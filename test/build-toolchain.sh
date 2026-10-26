#!/usr/bin/env bash
# Build a m68hc11-elf cross toolchain for the real-code test: GNU binutils 2.45 (as, ld, objdump) and
# the C compiler of GCC 3.4.6, the last GCC series with an easy m68hc11 port (GCC 6 and later dropped it).
# GCC 3.4.6 needs old-C flags with a current host compiler; only cc1/xgcc are built (no libgcc, no libc).
#
#   test/build-toolchain.sh <dir>            -> <dir>/inst/bin/m68hc11-elf-{gcc,as,ld,objdump,...}
set -euo pipefail
D=$(readlink -m "${1:?usage: build-toolchain.sh <dir>}")
mkdir -p "$D"
cd "$D"
P=$D/inst
get() { # url sha256 file
	[[ -s $3 ]] && echo "$2  $3" | sha256sum -c --status && return
	curl -fsSL "$1" -o "$3"
	echo "$2  $3" | sha256sum -c --status
}
get https://ftp.gnu.org/gnu/binutils/binutils-2.45.tar.xz \
	c50c0e7f9cb188980e2cc97e4537626b1672441815587f1eab69d2a1bfbef5d2 binutils-2.45.tar.xz
get https://ftp.gnu.org/gnu/gcc/gcc-3.4.6/gcc-core-3.4.6.tar.bz2 \
	3aab171d86e5a6c14cb9de35467a0472a7d5ef1d5b79a1df72ca533f8e82a133 gcc-core-3.4.6.tar.bz2
[[ -d binutils-2.45 ]] || tar xf binutils-2.45.tar.xz
[[ -d gcc-3.4.6 ]] || tar xf gcc-core-3.4.6.tar.bz2

mkdir -p bu-build && cd bu-build
[[ -f Makefile ]] || ../binutils-2.45/configure --target=m68hc11-elf --prefix="$P" --disable-nls \
	--disable-gdb --disable-sim --disable-gprofng --disable-werror >conf.log 2>&1
make -j"$(nproc)" MAKEINFO=true >make.log 2>&1
make install MAKEINFO=true >inst.log 2>&1
cd "$D"

export PATH=$P/bin:$PATH
mkdir -p gcc-build && cd gcc-build
OLDC="-std=gnu89 -fcommon -w -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0 -fno-stack-protector"
[[ -f Makefile ]] || CC="gcc $OLDC" ../gcc-3.4.6/configure --target=m68hc11-elf --prefix="$P" \
	--enable-languages=c --disable-nls --disable-libssp --without-headers --with-newlib \
	--disable-shared --disable-threads >conf.log 2>&1
# libgcc does not build with a current assembler (.softregs); the compiler proper is all that is needed
make -k -j"$(nproc)" all-gcc CC="gcc $OLDC" CFLAGS="-O1 $OLDC" MAKEINFO=true >make.log 2>&1 || true
[[ -x gcc/xgcc && -x gcc/cc1 ]] || { echo "GCC 3.4.6 build failed, see $D/gcc-build/make.log" >&2; exit 1; }
mkdir -p "$P/gcc"
cp gcc/xgcc gcc/cc1 "$P/gcc/"
cp -r ../gcc-3.4.6/gcc/ginclude "$P/gcc/include"
cat >"$P/bin/m68hc11-elf-gcc" <<EOF
#!/bin/sh
exec "$P/gcc/xgcc" -B"$P/gcc/" -B"$P/m68hc11-elf/bin/" -nostdinc -isystem "$P/gcc/include" "\$@"
EOF
chmod +x "$P/bin/m68hc11-elf-gcc"
echo "OK: $P/bin/m68hc11-elf-gcc"
