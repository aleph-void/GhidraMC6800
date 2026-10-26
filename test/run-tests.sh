#!/usr/bin/env bash
# Test suite of the 6800-family module (MC6800, MC6801, HD6301/6303, MC68HC11); everything that
# needs no downloads, then (--real) the real-code checks:
#   1. compile the four .slaspec files, check the .sla sizes, build lib/GhidraMC6800.jar
#   2. decode corpora vs binutils (HC11) and MAME unidasm (all four): every opcode of every page
#      x 4 operand patterns, and 40,000 random 8-byte slots per language, 0 unexplained differences
#   3. every-entry test: every opcode-table entry decodes (reached/total), nothing else does
#   4. p-code: hand-computed sequences and ~22,000 model-checked one-instruction cases in
#      Ghidra's emulator, plus one deliberately wrong expectation that must be reported
#   5. with --real <workdir>: build the m68hc11-elf toolchain and real C programs, import them
#      headless (ELF opinion), compare with objdump, check the ELF relocation handler against ld
#
#   test/run-tests.sh [--real] [workdir]
#
# Environment:
#   GHIDRA_INSTALL_DIR  Ghidra 12.1.x/12.2 scratch install; the module is symlinked into its
#                       Ghidra/Processors/GhidraMC6800 (use a copy, not your real install)
#   JAVA_HOME           a JDK with javac (17 or newer; Ghidra 12.2 needs 25)
#   SLOTDIS             slotdis binary, or BU_SRC + BU_LIB (+ BU_LIBIBERTY): a binutils 2.45 source
#                       tree and a directory with libopcodes.a libbfd.a libsframe.a of a build
#                       configured --enable-targets=all (or at least m68hc11), to build test/slotdis.c
#   UNIDASM             MAME's unidasm (default: on PATH)
#   FUZZ_SLOTS, EMU_PER_OP   random slots per language (default 40000) and model-checked cases per
#                       opcode (default 24); smaller values for a quick check
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
MOD=$(cd "$HERE/.." && pwd)
REAL=0
[[ ${1:-} == --real ]] && { REAL=1; shift; }
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR to a scratch Ghidra 12.1.x / 12.2}"
W=$(readlink -m "${1:-${TMPDIR:-/tmp}/hc11-tests}")
mkdir -p "$W"
export UNIDASM=${UNIDASM:-unidasm}
fail=0

P="$GHIDRA_INSTALL_DIR/Ghidra/Processors/GhidraMC6800"
if [[ ! -e $P ]]; then ln -s "$MOD" "$P"; elif [[ $(readlink -f "$P") != "$MOD" ]]; then
	echo "warning: $P exists and is not this module" >&2; fi

echo "== compiling SLEIGH"
for s in "$MOD"/data/languages/*.slaspec; do
	"$GHIDRA_INSTALL_DIR/support/sleigh" "$s" 2>&1 | grep -E "^ERROR" && exit 1 || true
	python3 - "${s%.slaspec}.sla" <<'EOF'
import sys, zlib
d = open(sys.argv[1], "rb").read()
n = len(zlib.decompress(d[4:]))
print(f"   {sys.argv[1].split('/')[-1]}: {len(d)} bytes, {n} decoded ({100 * n / (1 << 24):.2f}% of the 16 MiB limit)")
sys.exit(n >= 1 << 24)
EOF
done
"$HERE/build-jar.sh"

if [[ -z ${SLOTDIS:-} ]]; then
	: "${BU_SRC:?set SLOTDIS, or BU_SRC and BU_LIB}" "${BU_LIB:?set BU_LIB}"
	SLOTDIS=$W/slotdis
	gcc -O2 -w -DPACKAGE=1 -DPACKAGE_VERSION=1 -o "$SLOTDIS" "$HERE/slotdis.c" -I"$BU_SRC/include" \
		-I"$BU_SRC/bfd" -I"$BU_LIB/../include" "$BU_LIB/libopcodes.a" "$BU_LIB/libbfd.a" \
		"$BU_LIB/libsframe.a" "${BU_LIBIBERTY:-$BU_LIB/libiberty.a}" -lz -lzstd
fi
export SLOTDIS

echo "== decode: opcode-page enumeration and random slots vs binutils / MAME unidasm"
"$HERE/run-decode.sh" "$W/decode" "${FUZZ_SLOTS:-40000}" | tee "$W/decode.log"
grep -q FAIL "$W/decode.log" && fail=1

echo "== every-entry decode test"
for v in 6800:MC6800 6801:MC6801 6301:HD6301 hc11:MC68HC11; do
	f=$(ls "$W"/decode/g_enum_"${v%%:*}"_*.txt | head -1)
	python3 "$HERE/entry_check.py" "${v%%:*}" "$f" || fail=1
done

echo "== p-code: hand-computed sequences and model-checked one-instruction cases"
python3 "$HERE/gen_emu.py" "$W/emu" --per-op "${EMU_PER_OP:-24}"
for v in 6800:MC6800 6801:MC6801 6301:HD6301 hc11:MC68HC11; do
	t=${v%%:*} l=${v##*:}:BE:16:default
	"$HERE/run-emu.sh" "$l" "$W/emu/emu_hand_$t.txt" "$W/emu/hand_$t.out" fresh
	"$HERE/run-emu.sh" "$l" "$W/emu/emu_sweep_$t.txt" "$W/emu/sweep_$t.out"
	echo "-- $l: hand-computed: $(tail -n 1 "$W/emu/hand_$t.out"); model-checked: $(tail -n 1 "$W/emu/sweep_$t.out")"
	grep -h FAIL "$W/emu/hand_$t.out" "$W/emu/sweep_$t.out" | head -10 && fail=1 || true
done
"$HERE/run-emu.sh" MC6800:BE:16:default "$W/emu/emu_break.txt" "$W/emu/break.out" fresh
if [[ $(grep -c '^FAIL' "$W/emu/break.out") == 1 ]]; then
	echo "-- deliberately wrong expectation reported: $(grep '^FAIL' "$W/emu/break.out")"
else
	echo "-- FAIL: the deliberately wrong expectation was not reported"; fail=1
fi

if ((REAL)); then
	echo "== real code"
	R=$W/real
	TC=${HC11_TOOLCHAIN:-$R/toolchain}
	[[ -x $TC/inst/bin/m68hc11-elf-gcc ]] || "$HERE/build-toolchain.sh" "$TC"
	"$HERE/fetch-real-samples.sh" "$R/samples"
	"$HERE/build-real.sh" "$TC" "$R/samples" "$R/elf"
	"$HERE/real-binaries.sh" "$R/elf" "$R/work" "$TC/inst/bin/m68hc11-elf-objdump" || fail=1
	echo "-- ELF relocation handler vs ld"
	"$TC/inst/bin/m68hc11-elf-as" "$HERE/elf/relocs.s" -o "$R/relocs.o"
	"$HERE/reloc-check.sh" "$TC/inst/bin/m68hc11-elf-ld" "$TC/inst/bin/m68hc11-elf-objdump" "$R/reloc" \
		"$R/relocs.o" "$R/elf/t-aes-O1.o" "$R/elf/c-sha256-O1.o" "$R/elf/c-md5-O0.o" | tee "$R/reloc.log"
	if grep "^--" "$R/reloc.log" | grep -qv ": 0 differ$"; then fail=1; fi
fi

((fail)) && { echo "FAILED"; exit 1; }
echo "all tests passed"
