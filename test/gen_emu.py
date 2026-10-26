#!/usr/bin/env python3
"""Generate emulator test files for EmuCheck.java.

  gen_emu.py <outdir> [--per-op N] [--break]

For each variant (6800, 6801, 6301, hc11), emu_sweep_<variant>.txt: N random one-instruction cases
per opcode (edge-biased operands and flags), expected results from model6800.py (written from the
manuals).  emu_hand_<variant>.txt: the hand-computed sequences of hand_tests.py.
--break writes emu_break.txt: one hand-computed case with a deliberately wrong expectation.
"""
import os, random, sys
import model6800 as M

out = sys.argv[1]
per_op = int(sys.argv[sys.argv.index("--per-op") + 1]) if "--per-op" in sys.argv else 24
os.makedirs(out, exist_ok=True)
rnd = random.Random(0x68C11)
E8 = [0, 1, 2, 0x0F, 0x10, 0x7E, 0x7F, 0x80, 0x81, 0x99, 0xFE, 0xFF, 0x09, 0x0A, 0x60, 0x66]
E16 = [0, 1, 0x7FFF, 0x8000, 0xFFFF, 0x00FF, 0x0100, 0x8001, 0x7FFE, 0x1234]
PC0 = 0x1000   # per-test addresses are 0x4000 + 0x20 * (k % 400), see EmuCheck.BATCH


def pat(a, seed):
    return ((a * 131 + seed * 29 + 7) ^ (a >> 3)) & 0xFF


def r8():
    return rnd.choice(E8) if rnd.random() < 0.55 else rnd.randrange(256)


def r16():
    return rnd.choice(E16) if rnd.random() < 0.4 else rnd.randrange(65536)


def make_case(variant, prefix, op, mnem, mode, size, k):
    hc11 = variant == "hc11"
    regs = {"A": r8(), "B": r8(), "X": r16(), "Y": r16() if hc11 else 0, "S": rnd.randrange(0x30EA, 0x30F5)}
    ccmax = 0xFF if hc11 else 0x3F
    cc = rnd.randrange(ccmax + 1)
    seed = rnd.randrange(256)
    code = bytes([prefix]) if prefix else b""
    code += bytes([op])
    ix = "Y" if mode in ("idy", "by", "bry") else "X"
    # operand address selection
    def idx_operand():
        if rnd.random() < 0.15:
            base, off = 0xFFE8 + rnd.randrange(8), rnd.randrange(8)
        else:
            base, off = 0x2000 + rnd.randrange(16), rnd.randrange(15)
        regs[ix] = base
        return off
    if mode == "imm":
        code += (r8() if size == 1 else r16()).to_bytes(size, "big")
    elif mode == "dir":
        code += bytes([0x40 + rnd.randrange(0x1E)])
    elif mode == "ext":
        code += (0x2000 + rnd.randrange(0x1E)).to_bytes(2, "big")
    elif mode in ("idx", "idy"):
        code += bytes([idx_operand()])
    elif mode == "rel":
        code += bytes([rnd.randrange(256)])
    elif mode in ("bd",):
        code += bytes([0x40 + rnd.randrange(0x1E), r8()])
    elif mode in ("bx", "by"):
        code += bytes([idx_operand(), r8()])
    elif mode == "brd":
        code += bytes([0x40 + rnd.randrange(0x1E), r8(), rnd.randrange(256)])
    elif mode in ("brx", "bry"):
        code += bytes([idx_operand(), r8(), rnd.randrange(256)])
    elif mode == "imd":
        code += bytes([r8(), 0x40 + rnd.randrange(0x1E)])
    elif mode == "imx":
        code += bytes([r8(), idx_operand()])
    # branch-style bit tests: make mask relate to memory so both outcomes occur
    return regs, cc, seed, code


def expected(variant, regs, cc, seed, code, pc=PC0):
    flags = {n: (cc >> i) & 1 for i, n in enumerate(M.FLAGS)}
    if variant == "hc11":
        flags["X"] = (cc >> 6) & 1; flags["S"] = (cc >> 7) & 1
    ins = M.decode(variant, code)
    assert ins is not None, code.hex()
    cpu = M.CPU(variant, {k: regs[k] for k in "ABXYS"}, flags, lambda a: pat(a, seed) if
                (0x40 <= a < 0x60 or 0x2000 <= a < 0x2020 or 0x30E0 <= a < 0x3100 or 0xFFE0 <= a) else 0, pc)
    M.execute(variant, cpu, ins)
    return ins, cpu


def fmt(variant, name, regs, cc, seed, code, ins, cpu, pc=PC0):
    init = [f"A={regs['A']:02x}", f"B={regs['B']:02x}", f"CC={cc:02x}", f"X={regs['X']:04x}", f"S={regs['S']:04x}"]
    if variant == "hc11":
        init.append(f"Y={regs['Y']:04x}")
    init.append(f"seed={seed}")
    ex = []
    if not cpu.dundef:
        ex += [f"A={cpu.r['A']:02x}", f"B={cpu.r['B']:02x}"]
    ex += [f"X={cpu.r['X']:04x}", f"S={cpu.r['S']:04x}"]
    if variant == "hc11":
        ex.append(f"Y={cpu.r['Y']:04x}")
    mask = "ff" if variant == "hc11" else "3f"
    ex.append(f"CC/{mask}={cpu.ccbyte():02x}")
    ex.append(f"PC={cpu.pc:04x}")
    for a, v in sorted(cpu.writes.items()):
        ex.append(f"m{a:04x}={v:02x}")
    ex.append("win")
    return f"{name} {pc:x} n1 {code.hex()} {','.join(init)} {','.join(ex)}"


import hand_tests

for variant in ("6800", "6801", "6301", "hc11"):
    table = M.build(variant)
    lines = []
    n = 0
    for (prefix, op), (mnem, mode, size) in sorted(table.items()):
        for k in range(per_op):
            regs, cc, seed, code = make_case(variant, prefix, op, mnem, mode, size, k)
            pc = 0x4000 + 0x20 * (n % 400); n += 1
            ins, cpu = expected(variant, regs, cc, seed, code, pc)
            lines.append(fmt(variant, f"{variant}_{prefix:02x}{op:02x}_{mnem}_{k}", regs, cc, seed, code, ins, cpu, pc))
    open(f"{out}/emu_sweep_{variant}.txt", "w").write("\n".join(lines) + "\n")
    hl = hand_tests.lines(variant)
    open(f"{out}/emu_hand_{variant}.txt", "w").write("\n".join(hl) + "\n")
    print(f"{variant}: {len(table)} opcodes, {len(lines)} sweep cases, {len(hl)} hand-computed sequences")
open(f"{out}/emu_break.txt", "w").write("\n".join(hand_tests.broken()) + "\n")
