#!/usr/bin/env bash
# Build the real-code test programs with the m68hc11-elf toolchain of test/build-toolchain.sh.
#   test/build-real.sh <toolchain-dir> <samples-dir> <out-dir>
# Programs (each at -O0 -O1 -O2 -Os, and -O1 -g): crypto = B-Con crypto-algorithms (arcfour base64 md2 md5 rot-13 sha1 sha256; 32-bit int), tiny = tiny-AES-c +
# tiny-regex-c (-mshort, 16-bit int).  Calls to runtime helpers that are not built (64-bit shifts,
# 32-bit divide) stay unresolved; the code around them is still real compiler output.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
TC=$(readlink -f "$1") S=$(readlink -f "$2") O=$(readlink -m "$3")
mkdir -p "$O"
export PATH=$TC/inst/bin:$PATH
GCC=m68hc11-elf-gcc
LARITH=$TC/gcc-3.4.6/gcc/config/m68hc11/larith.asm
R=$HERE/real
for flav in long short; do
	f=(); [[ $flav == short ]] && f=(-mshort)
	mkdir -p "$O/lg-$flav"
	for L in adddi3 subdi3 notdi2 negsi2 one_cmplsi2 ashlsi3 ashrsi3 lshrsi3 lshrhi3 lshlhi3 rotrhi3 rotlhi3 \
		ashrhi3 ashrqi3 lshlqi3 divmodhi4 mulqi3 mulhi3 mulhi32 mulsi3; do
		$GCC "${f[@]}" -c -x assembler-with-cpp -DL_$L "$LARITH" -o "$O/lg-$flav/$L.o"
	done
	m68hc11-elf-as "${f[@]:0:0}" "$R/crt0.s" -o "$O/crt0.o"
	$GCC "${f[@]}" -O1 -c "$R/rt.c" -o "$O/rt-$flav.o"
done
link() { # name objs...
	local n=$1; shift
	m68hc11-elf-ld -T "$R/ld.x" --unresolved-symbols=ignore-all -o "$O/$n.elf" "$@" 2>"$O/$n.ld.log"
}
# O1g = -O1 -g: the DWARF debug information exercises the register mapping (data/languages/mc68hc11.dwarf)
for opt in O0 O1 O2 Os O1g; do
	g=(); fo=$opt
	[[ $opt == O1g ]] && { g=(-g); fo=O1; }
	objs=()
	for a in arcfour base64 md2 md5 rot-13 sha1 sha256; do
		$GCC -$fo "${g[@]}" -I"$R/inc" -I"$S/bcon" -c "$S/bcon/$a.c" -o "$O/c-$a-$opt.o"
		objs+=("$O/c-$a-$opt.o")
	done
	$GCC -$fo "${g[@]}" -c "$R/main1.c" -o "$O/c-main-$opt.o"
	link crypto-$opt "$O/crt0.o" "$O/c-main-$opt.o" "$O/rt-long.o" "${objs[@]}" "$O"/lg-long/*.o
	$GCC -mshort -$fo "${g[@]}" -I"$R/inc" -I"$S/tinyaes" -c "$S/tinyaes/aes.c" -o "$O/t-aes-$opt.o"
	$GCC -mshort -$fo "${g[@]}" -I"$R/inc" -I"$S/tinyregex" -c "$S/tinyregex/re.c" -o "$O/t-re-$opt.o"
	$GCC -mshort -$fo "${g[@]}" -I"$R/inc" -I"$S/tinyaes" -I"$S/tinyregex" -c "$R/main2.c" -o "$O/t-main-$opt.o"
	link tiny-$opt "$O/crt0.o" "$O/t-main-$opt.o" "$O/rt-short.o" "$O/t-aes-$opt.o" "$O/t-re-$opt.o" "$O"/lg-short/*.o
done
ls -la "$O"/*.elf
