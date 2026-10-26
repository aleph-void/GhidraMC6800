#!/usr/bin/env bash
# Fetch the real C sources the real-code test compiles (never committed; URL and SHA-256 pinned).
#   test/fetch-real-samples.sh <dir>
#
#   B-Con/crypto-algorithms  public domain ("released into the public domain free of any restrictions")
#   kokke/tiny-AES-c         Unlicense
#   kokke/tiny-regex-c       Unlicense
set -euo pipefail
D=$(readlink -m "${1:-real-samples}")
mkdir -p "$D"/bcon "$D"/tinyaes "$D"/tinyregex
BCON=cfbde48414baacf51fc7c74f275190881f037d32
TAES=23856752fbd139da0b8ca6e471a13d5bcc99a08d
TRE=f2632c6d9ed25272987471cdb8b70395c2460bdb
fetch() { # path url sha256
	local f=$D/$1
	if [[ -s $f ]] && echo "$3  $f" | sha256sum -c --status; then return; fi
	curl -fsSL "$2" -o "$f"
	echo "$3  $f" | sha256sum -c --status || { echo "SHA-256 mismatch: $1" >&2; exit 1; }
}
fetch bcon/aes.c https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/aes.c f59be01f535478a16264a82f304802a627362ca27328c35efd9af816ea0e0d45
fetch bcon/aes.h https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/aes.h 295eca4ebe89419c2d3fbd78e975aa800972986248989b6757f0a2211e21174a
fetch bcon/arcfour.c https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/arcfour.c 1ff12d57f47ea299ccdb51bec9b23166593866895e74ac3b17db328ff46ddeb8
fetch bcon/arcfour.h https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/arcfour.h 560dadb506ef6e388dccd282919c67c8ef06428d6474b8329168347a0b575776
fetch bcon/base64.c https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/base64.c 2c6c1eb346ec85ec7e21e1eeba1ed1a349e53692408ab6cdf6644c37c4daabd6
fetch bcon/base64.h https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/base64.h f18434438b25705fd8dce08320b47dec2b7522855ba327c691accf7e0884a0f7
fetch bcon/blowfish.c https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/blowfish.c a096d3338a43b390f801516e1461bcbcdce434188176a3c138136826989c6de6
fetch bcon/blowfish.h https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/blowfish.h 44b4f981562d13a1f67600402285d81a1c0e63d0a82c8efa4279eb391aa1545d
fetch bcon/des.c https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/des.c a19af365968d4b5f4f99958b05ab50c8127e11b05e1d804a356be5a39dd1a29f
fetch bcon/des.h https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/des.h f5c76b3d45b2083d48040270cc2f94c07dada6caabf6d6836f958e3b134ead9f
fetch bcon/md2.c https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/md2.c b1c31c3fe5d28a65de8e33549956dfeba7dbd74eb265b8e3b25460a1457ca9a8
fetch bcon/md2.h https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/md2.h e35ba4d34832ff54d0570e4262f6e3679978dbc9b6b48609df956e3a576adb0c
fetch bcon/md5.c https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/md5.c c97df0fa155b7b421a9ea8815f0e6ff9c64b2a2096a3cfd445b7e288a126aa84
fetch bcon/md5.h https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/md5.h 374c758fcc838bb4c23f591e284be41bb67d059cfa0dbd65997d65fee81c3e07
fetch bcon/rot-13.c https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/rot-13.c 5e5846d76e35d6db61d18226253868a13c2855842cc8e576b99790458bb47130
fetch bcon/rot-13.h https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/rot-13.h e424db1f39490d8e120ca566018d49e321ce6fabb096799904e9f6277270f63d
fetch bcon/sha1.c https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/sha1.c 7e5965e83bcafc361e31aff99136ba5ebae338448d4d33496e11e071ec437029
fetch bcon/sha1.h https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/sha1.h b76cc80cfc7a760150f2d0047ad39673d472d09900115bf8361b4e30f398f5b8
fetch bcon/sha256.c https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/sha256.c 4cbc93d30c28cee2a056d6f52cbce6e66ff9450f1d712ee4f59761b9b4486fad
fetch bcon/sha256.h https://raw.githubusercontent.com/B-Con/crypto-algorithms/$BCON/sha256.h a946e621775fd8251624e77d19f25407c4b6074ab780027e5797b77c7acf79b5
fetch tinyaes/aes.c https://raw.githubusercontent.com/kokke/tiny-AES-c/$TAES/aes.c f7f78b44654efd3542b6886923dd05194286807ebcfeb078ea05d21fe901ee9e
fetch tinyaes/aes.h https://raw.githubusercontent.com/kokke/tiny-AES-c/$TAES/aes.h 9f74a4de3bd11621ff6e8fb9b352b060f699e6c1c67f81a22d104aacad61a23b
fetch tinyregex/re.c https://raw.githubusercontent.com/kokke/tiny-regex-c/$TRE/re.c 846f87cd2527d7e1cdacddbcfed973cf953e50ba5d3ef50b69f592ed8622a34e
fetch tinyregex/re.h https://raw.githubusercontent.com/kokke/tiny-regex-c/$TRE/re.h 8ba52081ac279e7e8cf9a60165e5ca9ff84f417f49c921dda7dd8635c2f720bd
