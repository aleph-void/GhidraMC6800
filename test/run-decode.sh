#!/usr/bin/env bash
# Decode differentials for the four languages: binutils libopcodes (HC11 only, via slotdis) and MAME unidasm.
#   test/run-decode.sh <workdir> [fuzz-slots]
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=$(readlink -m "$1"); mkdir -p "$W"
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
# SLOTDIS: test/slotdis.c built against a libopcodes with the m68hc11 target (run-tests.sh builds it)
: "${SLOTDIS:?set SLOTDIS to the slotdis binary}"
NFUZZ=${2:-40000}; NF=$(( (NFUZZ + 8191) / 8192 ))
python3 "$HERE/gen_corpus.py" "$W" "$NFUZZ"
rc=0
# language, corpus tag, reference kind, reference arch
run() {
	local lang=$1 tag=$2 ref=$3 arch=$4 var=$5
	for c in enum $(for ((k=0;k<NF;k++)); do echo fuzz$k; done); do
		local base=$W/${c}_$tag
		"$HERE/ghidra-slots.sh" "$lang" $base.bin 8 $W/g_${c}_${tag}_${ref}_${arch}.txt
		if [[ $ref == objdump ]]; then
			"$SLOTDIS" "$arch" 8 $base.bin >$W/o_${c}_${tag}_${ref}_${arch}.txt
		else
			[[ -s $W/o_${c}_${tag}_${ref}_${arch}.txt ]] || python3 "$HERE/unislot.py" "$arch" 8 $base.bin $W/o_${c}_${tag}_${ref}_${arch}.txt
		fi
		echo "-- $lang $c vs $ref $arch: $(python3 "$HERE/slotcmp.py" $W/g_${c}_${tag}_${ref}_${arch}.txt $W/o_${c}_${tag}_${ref}_${arch}.txt \
			--ref $ref --variant $var --bytes $base.bin >$W/cmp_${c}_${tag}_${ref}_${arch}.txt && echo OK || { rc=1; echo FAIL; }) $(head -1 $W/cmp_${c}_${tag}_${ref}_${arch}.txt)"
	done
}
run MC68HC11:BE:16:default hc11 objdump m68hc11 hc11
run MC68HC11:BE:16:default hc11 unidasm hc11 hc11
run MC6801:BE:16:default 6801 unidasm m6803 6801
run HD6301:BE:16:default 6301 unidasm hd6301 6301
run HD6301:BE:16:default 6301 unidasm hd63701 6301
run MC6800:BE:16:default 6800 unidasm m6800 6800
exit $rc
