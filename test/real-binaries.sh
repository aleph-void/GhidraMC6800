#!/usr/bin/env bash
# Real-code check: import the ELF programs built by test/build-real.sh headless (no -processor: the
# ELF opinion picks MC68HC11), analyze, decompile every function, and compare every instruction
# Ghidra found with objdump -d at the same address.
#
#   test/real-binaries.sh <elf-dir> <workdir> [objdump]
# Environment: GHIDRA_INSTALL_DIR (with this module in Ghidra/Processors), DECOMP_TIMEOUT (default 60)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
E_DIR=$(readlink -f "$1") W=$(readlink -m "$2")
OBJDUMP=${3:-m68hc11-elf-objdump}
TMO=${DECOMP_TIMEOUT:-60}
mkdir -p "$W"
run_one() {
	local f=$1 n p
	n=$(basename "$f" .elf)
	p=$(mktemp -d "${TMPDIR:-/tmp}/hc11-real.XXXXXX")
	"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" "$p" p -import "$f" -scriptPath "$HERE" \
		-postScript RealCheck.java "$W/$n.sum" "$W/$n.lst" "$W/$n.c" "$TMO" \
		-deleteProject >"$W/$n.log" 2>&1 || tail -20 "$W/$n.log" >&2
	rm -rf "$p"
}
files=("$E_DIR"/*.elf)
for f in "${files[@]}"; do run_one "$f" & [[ $(jobs -r | wc -l) -ge 4 ]] && wait -n; done
wait
rc=0
for f in "${files[@]}"; do
	n=$(basename "$f" .elf)
	"$OBJDUMP" -d "$f" >"$W/$n.od"
	echo "-- $n"
	grep -E "^(language|functions|instructions|fallthrough|bad-instruction|error bookmarks|decompile|functions whose)" \
		"$W/$n.sum" | sed 's/^/   /'
	python3 "$HERE/real_compare.py" "$W/$n.lst" "$W/$n.od" >"$W/$n.cmp" || rc=1
	echo "   vs objdump: $(head -1 "$W/$n.cmp")"
done
exit $rc
