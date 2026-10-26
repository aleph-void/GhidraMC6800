#!/usr/bin/env python3
"""Disassemble the first instruction of every fixed-size slot of a raw image with MAME unidasm.

  unislot.py <arch> <slot> <image> <out.txt>      -> lines "<offset-hex> <len> <text>"
unidasm only sweeps linearly, so each slot is disassembled by its own process (-basepc = slot
offset, so branch targets are absolute), 16 at a time.
"""
import concurrent.futures, os, re, subprocess, sys, tempfile

arch, slot, img, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
data = open(img, "rb").read()
UNIDASM = os.environ.get("UNIDASM", "unidasm")
tmp = tempfile.mkdtemp(prefix="unislot.")


def run(args):
    lane, offs = args
    res = []
    p = os.path.join(tmp, "lane%d.bin" % lane)
    for off in offs:
        open(p, "wb").write(data[off:off + slot].ljust(slot, b"\0"))
        r = subprocess.run([UNIDASM, p, "-arch", arch, "-basepc", "%x" % off, "-count", "1"],
                           capture_output=True, text=True).stdout
        line = r.strip().splitlines()[0] if r.strip() else ""
        m = re.match(r"\s*([0-9a-fA-F]+):\s+((?:[0-9a-fA-F]{2,4} )+)\s*(.*)$", line)
        if not m:
            res.append((off, 0, "illegal"))
            continue
        n = len(m.group(2).replace(" ", "")) // 2
        res.append((off, n, m.group(3).strip() or "illegal"))
    return res


offs = list(range(0, len(data) - slot + 1, slot))
L = 16
chunks = [(i, offs[i::L]) for i in range(L)]
rows = []
with concurrent.futures.ThreadPoolExecutor(L) as ex:
    for r in ex.map(run, chunks):
        rows += r
rows.sort()
with open(out, "w") as f:
    for off, n, t in rows:
        f.write("%08x %d %s\n" % (off, n, t))
