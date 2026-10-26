#!/usr/bin/env python3
"""Compare Ghidra's listing of a real binary (RealCheck.java) with objdump -d at the same addresses.

  real_compare.py <ghidra.lst> <objdump.txt> [max-examples]

Counts agreement per instruction Ghidra disassembled; objdump instructions Ghidra did not reach
(data, or code only reached through unresolved jumps) are counted separately.
"""
import collections, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cmpnorm

g = {}
for line in open(sys.argv[1]):
    p = line.rstrip("\n").split(" ", 2)
    g[int(p[0], 16)] = (len(p[1]) // 2, p[2] if len(p) > 2 else "")
o = {}
for line in open(sys.argv[2]):
    m = re.match(r"\s*([0-9a-f]+):\t((?:[0-9a-f]{2} )+)\s*\t?(.*)$", line)
    if not m:
        continue
    t = m.group(3).strip()
    n = len(m.group(2).split())
    o[int(m.group(1), 16)] = (n, None if t.startswith(".byte") or t == "" or t.startswith("(bad)") else t)
maxex = int(sys.argv[3]) if len(sys.argv) > 3 else 6
cnt = collections.Counter(); ex = collections.defaultdict(list)
for a, (gn, gt) in sorted(g.items()):
    if a not in o:
        cnt["ghidra only (not in objdump)"] += 1; continue
    on, ot = o[a]
    if ot is None:
        cnt["objdump rejects"] += 1; ex["objdump rejects"].append((a, gt, ot)); continue
    if gn != on:
        cnt["length differs"] += 1; ex["length"].append((a, gt, ot)); continue
    if cmpnorm.norm(gt) == cmpnorm.norm(ot):
        cnt["exact"] += 1
    elif cmpnorm.sem(gt) == cmpnorm.sem(ot):
        cnt["semantic"] += 1
    else:
        cnt["differ"] += 1; ex["differ"].append((a, gt, ot))
notreached = sum(1 for a in o if a not in g and o[a][1] is not None)
total = sum(cnt.values())
agree = cnt["exact"] + cnt["semantic"]
print(f"compared {total} Ghidra instructions: agree {agree} (exact {cnt['exact']}, semantic {cnt['semantic']}), "
      f"differ {cnt['differ'] + cnt['length differs'] + cnt['objdump rejects']}; objdump instructions Ghidra "
      f"did not disassemble: {notreached}")
for k, v in ex.items():
    print(f"[{len(v)}] {k}")
    for a, gt, ot in v[:maxex]:
        print(f"    {a:04x}  ghidra: {gt}   objdump: {ot}")
sys.exit(1 if (cnt["differ"] + cnt["length differs"]) else 0)
