#!/usr/bin/env python3
"""Decode corpora for the 6800 family, as 8-byte slots (the longest instruction is 5 bytes).

  gen_corpus.py <outdir> [fuzz-slots]

enum_<v>.bin : every opcode of every opcode page x 4 operand patterns (v = hc11, 6801, 6301, 6800)
fuzz<k>_<v>.bin : random slots (8192 per image) (HC11: 45% start with a page prefix 0x18/0x1A/0xCD)
"""
import os, random, sys

out = sys.argv[1]; nfuzz = int(sys.argv[2]) if len(sys.argv) > 2 else 40000
os.makedirs(out, exist_ok=True)
pats = [b"\x00\x00\x00\x00", b"\x12\x34\x56\x78", b"\xff\x80\x7f\x01", b"\x9a\xfe\x00\xc3"]
pages = {"hc11": [b"", b"\x18", b"\x1a", b"\xcd"], "6801": [b""], "6301": [b""], "6800": [b""]}
rnd = random.Random(0x6811)
for v, pre in pages.items():
    e = bytearray()
    for p in pre:
        for op in range(256):
            for pt in pats:
                e += (p + bytes([op]) + pt).ljust(8, b"\0")
    open(os.path.join(out, f"enum_{v}.bin"), "wb").write(e)
    # the address space is 64 KB: one image holds 8192 slots
    for k in range((nfuzz + 8191) // 8192):
        f = bytearray()
        for i in range(8192):
            s = bytes(rnd.randrange(256) for _ in range(8))
            if v == "hc11" and rnd.random() < 0.45:
                s = bytes([rnd.choice((0x18, 0x1A, 0xCD))]) + s[:7]
            f += s
        open(os.path.join(out, f"fuzz{k}_{v}.bin"), "wb").write(f)
