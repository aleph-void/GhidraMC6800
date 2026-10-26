#!/usr/bin/env python3
"""Every-entry test: every opcode-table entry of model6800.py decodes (reached/total), and no opcode
outside the table decodes.  Input: Ghidra's slot listing of gen_corpus.py's enum_<variant>.bin.

  entry_check.py <variant> <g_enum_<variant>.txt>
"""
import sys
import model6800 as M

variant, path = sys.argv[1], sys.argv[2]
table = M.build(variant)
prefixes = [0, 0x18, 0x1A, 0xCD] if variant == "hc11" else [0]
dec = {}
for line in open(path):
    off, n, text = line.rstrip("\n").split(" ", 2)
    k = int(off, 16) // 8
    pre, rest = divmod(k, 256 * 4)
    op = rest // 4
    key = (prefixes[pre], op)
    if int(n) > 0 and text != "BAD":
        dec.setdefault(key, []).append(text)
missing = [k for k in table if k not in dec]
# the prefix bytes themselves start (prefixed) instructions of the other pages
extra = [k for k in dec if k not in table and not (variant == "hc11" and k[0] == 0 and k[1] in (0x18, 0x1A, 0xCD))]
print(f"{variant}: opcode entries reached {len(table) - len(missing)}/{len(table)}; "
      f"opcodes outside the table that decode: {len(extra)}")
for k in missing:
    print(f"  NOT REACHED  {k[0]:02x} {k[1]:02x} {table[k][0]}")
for k in extra:
    print(f"  EXTRA        {k[0]:02x} {k[1]:02x} {dec[k][0]}")
sys.exit(1 if missing or extra else 0)
