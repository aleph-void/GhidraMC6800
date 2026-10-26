#!/usr/bin/env python3
"""Compare two slot listings ("<offset-hex> <len> <text>"): Ghidra (DumpSlots.java) vs a reference.

  slotcmp.py <ghidra.txt> <reference.txt> --ref objdump|unidasm [--max N] [--bytes FILE]

Reference text is normalised: objdump ".byte" / unidasm "illegal"/"???" lines count as "rejected".
Both texts are reduced to tokens (mnemonic, registers, numbers by value; "#", "*", "," and
0x-padding dropped), so display spelling differences are "semantic" agreement, identical
normalised spelling is "exact".  Length (bytes consumed) must agree for every accepted word.
Rejected-by-both counts as agreement ("both invalid").  Everything else is bucketed by
(class key) and checked against the explained-difference rules in test/explained.py.
"""
import argparse, collections, importlib.util, os, re, sys

ap = argparse.ArgumentParser()
ap.add_argument("g"); ap.add_argument("o")
ap.add_argument("--ref", default="objdump")
ap.add_argument("--max", type=int, default=4)
ap.add_argument("--bytes", help="raw image the slots came from (to print the instruction bytes)")
ap.add_argument("--slot", type=int, default=8)
ap.add_argument("--variant", default="hc11")
a = ap.parse_args()

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("explained", os.path.join(here, "explained.py"))
ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)
raw = open(a.bytes, "rb").read() if a.bytes else None


def load(p, is_ghidra):
    d = {}
    for line in open(p):
        parts = line.rstrip("\n").split(" ", 2)
        if len(parts) < 2:
            continue
        off = int(parts[0], 16); n = int(parts[1]); t = parts[2].strip() if len(parts) > 2 else ""
        if is_ghidra:
            if t == "BAD" or n == 0:
                t = None
        else:
            if t.startswith(".byte") or t.startswith("(bad)") or t == "" or n <= 0 \
               or re.match(r"(?i)(illegal|\?+$|\?\?\?|\.db|\.byte)", t):
                t = None
        d[off] = (n, t)
    return d


sys.path.insert(0, here)
from cmpnorm import norm, sem


g = load(a.g, True); o = load(a.o, False)
cnt = collections.Counter(); classes = collections.defaultdict(list); expl = collections.Counter()
for off in sorted(o):
    if off not in g:
        cnt["missing"] += 1; continue
    gn, gt = g[off]; on, ot = o[off]
    if gt is None and ot is None:
        cnt["both invalid"] += 1; continue
    b = raw[off:off + a.slot].hex() if raw else ""
    if gt is not None and ot is not None and gn == on:
        if norm(gt) == norm(ot):
            cnt["exact"] += 1; continue
        if sem(gt) == sem(ot):
            cnt["semantic"] += 1; continue
    # a difference: try the explained rules
    kind = "differ" if (gt is not None and ot is not None) else ("ghidra only" if ot is None else "reference only")
    rule = ex.explain(a.variant, a.ref, gt, gn, ot, on, b)
    if rule:
        expl[rule] += 1; cnt[kind + " (explained)"] += 1; continue
    cnt[kind] += 1
    mn = lambda t: (t.split()[0].lower() if t else "-")
    classes[f"{kind}: ref {mn(ot)} / ghidra {mn(gt)}"].append((off, b, gt, gn, ot, on))

total = sum(cnt.values())
agree = cnt["exact"] + cnt["semantic"] + cnt["both invalid"]
unexpl = cnt["differ"] + cnt["ghidra only"] + cnt["reference only"]
print(f"compared {total} slots: agree {agree} (exact {cnt['exact']}, semantic {cnt['semantic']}, "
      f"both invalid {cnt['both invalid']}), explained {sum(expl.values())}, unexplained {unexpl}")
for k, v in expl.most_common():
    print(f"   explained [{v}] {k}")
for k in ("differ", "ghidra only", "reference only", "missing"):
    if cnt[k]:
        print(f"   {k}: {cnt[k]}")
for key in sorted(classes, key=lambda k: -len(classes[k])):
    print(f"[{len(classes[key])}] {key}")
    for off, b, gt, gn, ot, on in classes[key][:a.max]:
        print(f"    {off:08x} {b[:a.slot*2]}  ghidra({gn}): {gt}   ref({on}): {ot}")
sys.exit(1 if unexpl else 0)
