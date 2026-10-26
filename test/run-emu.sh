#!/usr/bin/env bash
# Run one generated emulator test file:  test/run-emu.sh <language-id> <tests.txt> <out.txt> [fresh]
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
LANG_ID=$1 TESTS=$(readlink -f "$2") OUT=$(readlink -m "$3")
Z=$(mktemp "${TMPDIR:-/tmp}/zero64k.XXXXXX.bin")
trap 'rm -f "$Z"' EXIT
head -c 65536 /dev/zero >"$Z"
"$HERE/ghidra-script.sh" raw "$LANG_ID" "$Z" EmuCheck.java "$TESTS" "$OUT" ${4:+$4}
