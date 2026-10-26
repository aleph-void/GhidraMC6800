#!/usr/bin/env python3
"""Reference model of the 6800 family (MC6800, MC6801, HD6301, MC68HC11), written from the
manuals' instruction descriptions and boolean formulae (Motorola M6800 Programming Reference
Manual, MC6801 Reference Manual, M68HC11 Reference Manual, Hitachi HD6301/6303 data book).
It does not look at the SLEIGH files.  Used by gen_emu.py to produce expected results for the
Ghidra emulator (EmuCheck.java).

  decode(variant, code)  -> Insn(prefix, op, mnem, mode, size, length, fields)  or None
  execute(variant, cpu, insn)  runs one instruction on cpu (see CPU)
variants: "6800", "6801", "6301", "hc11"
"""
M8, M16 = 0xFF, 0xFFFF
FLAGS = "CVZNIH"          # bit 0..5 of CC
HC11_FLAGS = FLAGS + "XS"  # bits 6, 7 (HC11 only)


class Insn:
    def __init__(self, prefix, op, mnem, mode, size=1, length=1, f=None):
        self.prefix, self.op, self.mnem, self.mode, self.size, self.length = prefix, op, mnem, mode, size, length
        self.f = f or {}

    def __repr__(self):
        return f"<{self.prefix:02x} {self.op:02x} {self.mnem} {self.mode}>"


def build(variant):
    """(prefix, opcode) -> (mnem, mode, size); modes: inh imm dir ext idx idy rel bd bx by brd brx bry imd imx"""
    t = {}
    v6801 = variant in ("6801", "6301", "hc11")
    hc11 = variant == "hc11"
    h6301 = variant == "6301"

    def add(op, m, mode, size=1, prefix=0):
        t[(prefix, op)] = (m, mode, size)

    for op, m in {0x01: "NOP", 0x06: "TAP", 0x07: "TPA", 0x08: "INX", 0x09: "DEX", 0x0A: "CLV", 0x0B: "SEV",
                  0x0C: "CLC", 0x0D: "SEC", 0x0E: "CLI", 0x0F: "SEI", 0x10: "SBA", 0x11: "CBA", 0x16: "TAB",
                  0x17: "TBA", 0x19: "DAA", 0x1B: "ABA", 0x30: "TSX", 0x31: "INS", 0x32: "PULA", 0x33: "PULB",
                  0x34: "DES", 0x35: "TXS", 0x36: "PSHA", 0x37: "PSHB", 0x39: "RTS", 0x3B: "RTI", 0x3E: "WAI",
                  0x3F: "SWI"}.items():
        add(op, m, "inh")
    if v6801:
        for op, m in {0x04: "LSRD", 0x05: "ASLD", 0x38: "PULX", 0x3A: "ABX", 0x3C: "PSHX", 0x3D: "MUL"}.items():
            add(op, m, "inh")
        add(0x21, "BRN", "rel")
    if hc11:
        for op, m in {0x00: "TEST", 0x02: "IDIV", 0x03: "FDIV", 0x8F: "XGDX", 0xCF: "STOP"}.items():
            add(op, m, "inh")
        add(0x12, "BRSET", "brd"); add(0x13, "BRCLR", "brd"); add(0x14, "BSET", "bd"); add(0x15, "BCLR", "bd")
        add(0x1C, "BSET", "bx"); add(0x1D, "BCLR", "bx"); add(0x1E, "BRSET", "brx"); add(0x1F, "BRCLR", "brx")
    if h6301:
        add(0x18, "XGDX", "inh"); add(0x1A, "SLP", "inh")
        for opx, opd, m in ((0x61, 0x71, "AIM"), (0x62, 0x72, "OIM"), (0x65, 0x75, "EIM"), (0x6B, 0x7B, "TIM")):
            add(opx, m, "imx"); add(opd, m, "imd")
    for i, m in enumerate(["BRA", "BRN", "BHI", "BLS", "BCC", "BCS", "BNE", "BEQ", "BVC", "BVS", "BPL", "BMI",
                           "BGE", "BLT", "BGT", "BLE"]):
        if m != "BRN":
            add(0x20 + i, m, "rel")
    for base, r in ((0x40, "A"), (0x50, "B")):
        for off, m in {0: "NEG", 3: "COM", 4: "LSR", 6: "ROR", 7: "ASR", 8: "ASL", 9: "ROL", 10: "DEC",
                       12: "INC", 13: "TST", 15: "CLR"}.items():
            add(base + off, m + r, "inh")
    for off, m in {0: "NEG", 3: "COM", 4: "LSR", 6: "ROR", 7: "ASR", 8: "ASL", 9: "ROL", 10: "DEC", 12: "INC",
                   13: "TST", 14: "JMP", 15: "CLR"}.items():
        add(0x60 + off, m, "idx"); add(0x70 + off, m, "ext")
    # accumulator / index groups
    for hi, mode in ((0x8, "imm"), (0x9, "dir"), (0xA, "idx"), (0xB, "ext")):
        for lo, m in {0: "SUBA", 1: "CMPA", 2: "SBCA", 4: "ANDA", 5: "BITA", 6: "LDAA", 8: "EORA", 9: "ADCA",
                      10: "ORAA", 11: "ADDA"}.items():
            add(hi * 16 + lo, m, mode)
        if mode != "imm":
            add(hi * 16 + 7, "STAA", mode)
            add(hi * 16 + 15, "STS", mode, 2)
        add(hi * 16 + 12, "CPX", mode, 2)
        add(hi * 16 + 14, "LDS", mode, 2)
        if v6801:
            add(hi * 16 + 3, "SUBD", mode, 2)
    for hi, mode in ((0xC, "imm"), (0xD, "dir"), (0xE, "idx"), (0xF, "ext")):
        for lo, m in {0: "SUBB", 1: "CMPB", 2: "SBCB", 4: "ANDB", 5: "BITB", 6: "LDAB", 8: "EORB", 9: "ADCB",
                      10: "ORAB", 11: "ADDB"}.items():
            add(hi * 16 + lo, m, mode)
        add(hi * 16 + 14, "LDX", mode, 2)
        if mode != "imm":
            add(hi * 16 + 7, "STAB", mode)
            add(hi * 16 + 15, "STX", mode, 2)
        if v6801:
            add(hi * 16 + 3, "ADDD", mode, 2)
            add(hi * 16 + 12, "LDD", mode, 2)
            if mode != "imm":
                add(hi * 16 + 13, "STD", mode, 2)
    add(0x8D, "BSR", "rel")
    add(0xAD, "JSR", "idx"); add(0xBD, "JSR", "ext")
    if v6801:
        add(0x9D, "JSR", "dir")
    if hc11:
        # page 0x18: the Y-indexed forms
        for op in list(t):
            if op[0] == 0 and t[op][1] in ("idx", "bx", "brx") and t[op][0] != "CPX":
                m, mode, size = t[op]
                add(op[1], m, {"idx": "idy", "bx": "by", "brx": "bry"}[mode], size, 0x18)
        add(0xAC, "CPY", "idy", 2, 0x18); add(0xEE, "LDY", "idy", 2, 0x18); add(0xEF, "STY", "idy", 2, 0x18)
        for op, m in {0x08: "INY", 0x09: "DEY", 0x30: "TSY", 0x35: "TYS", 0x38: "PULY", 0x3A: "ABY",
                      0x3C: "PSHY", 0x8F: "XGDY"}.items():
            add(op, m, "inh", 1, 0x18)
        for op, mode in ((0x8C, "imm"), (0x9C, "dir"), (0xBC, "ext")):
            add(op, "CPY", mode, 2, 0x18)
        for op, mode in ((0xCE, "imm"), (0xDE, "dir"), (0xFE, "ext")):
            add(op, "LDY", mode, 2, 0x18)
        for op, mode in ((0xDF, "dir"), (0xFF, "ext")):
            add(op, "STY", mode, 2, 0x18)
        # page 0x1A
        for op, mode in ((0x83, "imm"), (0x93, "dir"), (0xB3, "ext"), (0xA3, "idx")):
            add(op, "CPD", mode, 2, 0x1A)
        add(0xAC, "CPY", "idx", 2, 0x1A); add(0xEE, "LDY", "idx", 2, 0x1A); add(0xEF, "STY", "idx", 2, 0x1A)
        # page 0xCD
        add(0xA3, "CPD", "idy", 2, 0xCD); add(0xAC, "CPX", "idy", 2, 0xCD)
        add(0xEE, "LDX", "idy", 2, 0xCD); add(0xEF, "STX", "idy", 2, 0xCD)
    return t


_tables = {}


def decode(variant, code):
    t = _tables.setdefault(variant, build(variant))
    prefix = 0
    i = 0
    if variant == "hc11" and code[0] in (0x18, 0x1A, 0xCD):
        prefix = code[0]; i = 1
    e = t.get((prefix, code[i]))
    if e is None:
        return None
    m, mode, size = e
    n = i + 1
    f = {}
    if mode == "imm":
        f["imm"] = int.from_bytes(code[n:n + size], "big"); n += size
    elif mode in ("dir", "idx", "idy"):
        f["off"] = code[n]; n += 1
    elif mode == "ext":
        f["addr"] = int.from_bytes(code[n:n + 2], "big"); n += 2
    elif mode == "rel":
        f["rel"] = code[n]; n += 1
    elif mode in ("bd", "bx", "by"):
        f["off"] = code[n]; f["mask"] = code[n + 1]; n += 2
    elif mode in ("brd", "brx", "bry"):
        f["off"] = code[n]; f["mask"] = code[n + 1]; f["rel"] = code[n + 2]; n += 3
    elif mode in ("imd", "imx"):
        f["imm"] = code[n]; f["off"] = code[n + 1]; n += 2
    return Insn(prefix, code[i], m, mode, size, n, f)


class CPU:
    def __init__(self, variant, regs, flags, memget, pc):
        self.v = variant
        self.r = dict(regs)       # A B X Y S
        self.f = dict(flags)      # C V Z N I H (X S on hc11)
        self.pc = pc
        self.memget = memget
        self.writes = {}
        self.dundef = False       # D is indeterminate afterwards (divide by zero / overflow)

    # memory
    def rd8(self, a):
        a &= M16
        return self.writes.get(a, self.memget(a))

    def wr8(self, a, v):
        self.writes[a & M16] = v & M8

    def rd16(self, a):
        return (self.rd8(a) << 8) | self.rd8(a + 1)

    def wr16(self, a, v):
        self.wr8(a, v >> 8); self.wr8(a + 1, v)

    def ccbyte(self):
        b = sum(self.f[n] << i for i, n in enumerate(FLAGS))
        if self.v == "hc11":
            b |= self.f["X"] << 6 | self.f["S"] << 7
        else:
            b |= 0xC0
        return b

    def loadcc(self, b):
        for i, n in enumerate(FLAGS):
            self.f[n] = (b >> i) & 1
        if self.v == "hc11":
            self.f["X"] = self.f["X"] & (b >> 6) & 1   # X can be cleared, never set
            self.f["S"] = (b >> 7) & 1

    @property
    def D(self):
        return (self.r["A"] << 8) | self.r["B"]

    @D.setter
    def D(self, v):
        self.r["A"] = (v >> 8) & M8; self.r["B"] = v & M8


def sx8(v):
    return v - 256 if v & 0x80 else v


def execute(variant, c, i):
    """Execute instruction i on cpu c (c.pc = address of the instruction)."""
    f, r = c.f, c.r
    nxt = (c.pc + i.length) & M16
    c.pc = nxt
    m, mode, size = i.mnem, i.mode, i.size
    ix = "Y" if mode in ("idy", "by", "bry") else "X"

    def ea():
        if mode in ("dir",):
            return i.f["off"]
        if mode == "ext":
            return i.f["addr"]
        if mode in ("idx", "idy", "bx", "by", "brx", "bry", "imx"):
            return (r[ix] + i.f["off"]) & M16
        if mode in ("bd", "brd", "imd"):
            return i.f["off"]
        raise AssertionError(mode)

    def rd(sz=None):
        sz = sz or size
        if mode == "imm":
            return i.f["imm"]
        a = ea()
        return c.rd8(a) if sz == 1 else c.rd16(a)

    def wr(v, sz=None):
        sz = sz or size
        a = ea()
        c.wr8(a, v) if sz == 1 else c.wr16(a, v)

    def nz(v, bits):
        f["N"] = (v >> (bits - 1)) & 1
        f["Z"] = int(v & ((1 << bits) - 1) == 0)

    def push8(v):
        c.wr8(r["S"], v); r["S"] = (r["S"] - 1) & M16

    def push16(v):
        c.wr8(r["S"], v & M8); c.wr8(r["S"] - 1, v >> 8); r["S"] = (r["S"] - 2) & M16

    def pull8():
        r["S"] = (r["S"] + 1) & M16
        return c.rd8(r["S"])

    def pull16():
        h = c.rd8(r["S"] + 1); l = c.rd8(r["S"] + 2); r["S"] = (r["S"] + 2) & M16
        return (h << 8) | l

    def add8(a, b, cin=0, setH=True):
        s = a + b + cin; res = s & M8
        if setH:
            f["H"] = int(((a & 15) + (b & 15) + cin) > 15)
        f["C"] = int(s > M8)
        f["V"] = int(((a ^ res) & (b ^ res) & 0x80) != 0)
        nz(res, 8)
        return res

    def sub8(a, b, cin=0):
        s = a - b - cin; res = s & M8
        f["C"] = int(s < 0)
        f["V"] = int(((a ^ b) & (a ^ res) & 0x80) != 0)
        nz(res, 8)
        return res

    def add16(a, b):
        s = a + b; res = s & M16
        f["C"] = int(s > M16)
        f["V"] = int(((a ^ res) & (b ^ res) & 0x8000) != 0)
        nz(res, 16)
        return res

    def sub16(a, b, setC=True):
        s = a - b; res = s & M16
        if setC:
            f["C"] = int(s < 0)
        f["V"] = int(((a ^ b) & (a ^ res) & 0x8000) != 0)
        nz(res, 16)
        return res

    def ld(reg, bits):
        v = rd(bits // 8)
        if reg == "D":
            c.D = v
        else:
            r[reg] = v
        nz(v, bits); f["V"] = 0

    def st(val, bits):
        wr(val, bits // 8); nz(val, bits); f["V"] = 0

    # read-modify-write operand access (accumulator forms or memory)
    def rmw(fn):
        if m[-1] in "AB" and mode == "inh" and m[:-1] in ("NEG", "COM", "LSR", "ROR", "ASR", "ASL", "ROL", "DEC", "INC", "TST", "CLR"):
            reg = m[-1]
            res = fn(r[reg])
            if res is not None:
                r[reg] = res
        else:
            res = fn(c.rd8(ea()))
            if res is not None:
                c.wr8(ea(), res)

    base = m[:-1] if (m[-1] in "AB" and mode == "inh" and m[:-1] in ("NEG", "COM", "LSR", "ROR", "ASR", "ASL", "ROL", "DEC", "INC", "TST", "CLR")) else m

    if base == "NEG":
        def fn(v):
            res = (-v) & M8; f["V"] = int(res == 0x80); f["C"] = int(res != 0); nz(res, 8); return res
        rmw(fn)
    elif base == "COM":
        def fn(v):
            res = (~v) & M8; f["V"] = 0; f["C"] = 1; nz(res, 8); return res
        rmw(fn)
    elif base == "LSR":
        def fn(v):
            f["C"] = v & 1; res = v >> 1; f["N"] = 0; f["Z"] = int(res == 0); f["V"] = f["N"] ^ f["C"]; return res
        rmw(fn)
    elif base == "ROR":
        def fn(v):
            res = (v >> 1) | (f["C"] << 7); f["C"] = v & 1; nz(res, 8); f["V"] = f["N"] ^ f["C"]; return res
        rmw(fn)
    elif base == "ASR":
        def fn(v):
            res = (v >> 1) | (v & 0x80); f["C"] = v & 1; nz(res, 8); f["V"] = f["N"] ^ f["C"]; return res
        rmw(fn)
    elif base == "ASL":
        def fn(v):
            res = (v << 1) & M8; f["C"] = v >> 7; nz(res, 8); f["V"] = f["N"] ^ f["C"]; return res
        rmw(fn)
    elif base == "ROL":
        def fn(v):
            res = ((v << 1) | f["C"]) & M8; f["C"] = v >> 7; nz(res, 8); f["V"] = f["N"] ^ f["C"]; return res
        rmw(fn)
    elif base == "DEC":
        def fn(v):
            res = (v - 1) & M8; f["V"] = int(v == 0x80); nz(res, 8); return res
        rmw(fn)
    elif base == "INC":
        def fn(v):
            res = (v + 1) & M8; f["V"] = int(v == 0x7F); nz(res, 8); return res
        rmw(fn)
    elif base == "TST":
        def fn(v):
            nz(v, 8); f["V"] = 0; f["C"] = 0
        rmw(fn)
    elif base == "CLR":
        def fn(v):
            f["N"] = 0; f["Z"] = 1; f["V"] = 0; f["C"] = 0; return 0
        rmw(fn)
    elif m == "JMP":
        c.pc = ea()
    elif m == "JSR":
        push16(nxt); c.pc = ea()
    elif m == "BSR":
        push16(nxt); c.pc = (nxt + sx8(i.f["rel"])) & M16
    elif m in ("SUBA", "SUBB"):
        reg = m[-1]; r[reg] = sub8(r[reg], rd())
    elif m in ("CMPA", "CMPB"):
        sub8(r[m[-1]], rd())
    elif m in ("SBCA", "SBCB"):
        reg = m[-1]; r[reg] = sub8(r[reg], rd(), f["C"])
    elif m in ("ANDA", "ANDB", "ORAA", "ORAB", "EORA", "EORB"):
        reg = m[-1]; v = rd()
        r[reg] = {"AND": r[reg] & v, "ORA": r[reg] | v, "EOR": r[reg] ^ v}[m[:3]]
        nz(r[reg], 8); f["V"] = 0
    elif m in ("BITA", "BITB"):
        nz(r[m[-1]] & rd(), 8); f["V"] = 0
    elif m in ("LDAA", "LDAB"):
        ld(m[-1], 8)
    elif m in ("STAA", "STAB"):
        st(r[m[-1]], 8)
    elif m in ("ADDA", "ADDB"):
        reg = m[-1]; r[reg] = add8(r[reg], rd())
    elif m in ("ADCA", "ADCB"):
        reg = m[-1]; r[reg] = add8(r[reg], rd(), f["C"])
    elif m == "CPX" or m == "CPY":
        reg = m[-1]
        sub16(r[reg], rd(), setC=(variant != "6800"))
    elif m == "CPD":
        sub16(c.D, rd())
    elif m in ("LDS", "LDX", "LDY"):
        ld(m[-1], 16)
    elif m == "LDD":
        ld("D", 16)
    elif m in ("STS", "STX", "STY"):
        st(r[m[-1]], 16)
    elif m == "STD":
        st(c.D, 16)
    elif m == "SUBD":
        c.D = sub16(c.D, rd())
    elif m == "ADDD":
        c.D = add16(c.D, rd())
    elif m == "ASLD":
        d = c.D; f["C"] = d >> 15; c.D = (d << 1) & M16; nz(c.D, 16); f["V"] = f["N"] ^ f["C"]
    elif m == "LSRD":
        d = c.D; f["C"] = d & 1; c.D = d >> 1; f["N"] = 0; f["Z"] = int(c.D == 0); f["V"] = f["C"]
    elif m == "MUL":
        c.D = r["A"] * r["B"]; f["C"] = (c.D >> 7) & 1
    elif m in ("ABX", "ABY"):
        reg = "X" if m == "ABX" else "Y"; r[reg] = (r[reg] + r["B"]) & M16
    elif m in ("INX", "INY"):
        reg = m[-1]; r[reg] = (r[reg] + 1) & M16; f["Z"] = int(r[reg] == 0)
    elif m in ("DEX", "DEY"):
        reg = m[-1]; r[reg] = (r[reg] - 1) & M16; f["Z"] = int(r[reg] == 0)
    elif m in ("TSX", "TSY"):
        r[m[-1]] = (r["S"] + 1) & M16
    elif m in ("TXS", "TYS"):
        r["S"] = (r[m[1]] - 1) & M16
    elif m == "INS":
        r["S"] = (r["S"] + 1) & M16
    elif m == "DES":
        r["S"] = (r["S"] - 1) & M16
    elif m in ("PSHA", "PSHB"):
        push8(r[m[-1]])
    elif m in ("PULA", "PULB"):
        r[m[-1]] = pull8()
    elif m in ("PSHX", "PSHY"):
        push16(r[m[-1]])
    elif m in ("PULX", "PULY"):
        r[m[-1]] = pull16()
    elif m == "RTS":
        c.pc = pull16()
    elif m in ("SWI", "WAI"):
        push16(nxt)
        if variant == "hc11":
            push16(r["Y"])
        push16(r["X"]); push8(r["A"]); push8(r["B"]); push8(c.ccbyte())
        if m == "SWI":
            f["I"] = 1
            c.pc = c.rd16(0xFFF6 if variant == "hc11" else 0xFFFA)
    elif m == "RTI":
        c.loadcc(pull8()); r["B"] = pull8(); r["A"] = pull8(); r["X"] = pull16()
        if variant == "hc11":
            r["Y"] = pull16()
        c.pc = pull16()
    elif m == "TAP":
        c.loadcc(r["A"])
    elif m == "TPA":
        r["A"] = c.ccbyte()
    elif m == "CLV": f["V"] = 0
    elif m == "SEV": f["V"] = 1
    elif m == "CLC": f["C"] = 0
    elif m == "SEC": f["C"] = 1
    elif m == "CLI": f["I"] = 0
    elif m == "SEI": f["I"] = 1
    elif m == "SBA":
        r["A"] = sub8(r["A"], r["B"])
    elif m == "CBA":
        sub8(r["A"], r["B"])
    elif m == "ABA":
        r["A"] = add8(r["A"], r["B"])
    elif m == "TAB":
        r["B"] = r["A"]; nz(r["B"], 8); f["V"] = 0
    elif m == "TBA":
        r["A"] = r["B"]; nz(r["A"], 8); f["V"] = 0
    elif m == "DAA":
        a = r["A"]; hi, lo = a >> 4, a & 15
        up = f["C"] == 1 or hi > 9 or (hi > 8 and lo > 9)
        low = f["H"] == 1 or lo > 9
        r["A"] = (a + (6 if low else 0) + (0x60 if up else 0)) & M8
        f["C"] = int(up); nz(r["A"], 8)
    elif m in ("NOP", "TEST", "STOP", "SLP", "BRN"):
        pass
    elif m in ("XGDX", "XGDY"):
        reg = m[-1]; d = c.D; c.D = r[reg]; r[reg] = d
    elif m == "IDIV":
        d, x = c.D, r["X"]
        f["V"] = 0; f["C"] = int(x == 0)
        if x == 0:
            r["X"] = 0xFFFF; c.dundef = True
        else:
            r["X"] = d // x; c.D = d % x
        f["Z"] = int(r["X"] == 0)
    elif m == "FDIV":
        d, x = c.D, r["X"]
        f["C"] = int(x == 0)
        if x == 0 or x <= d:
            f["V"] = int(x <= d)
            r["X"] = 0xFFFF; c.dundef = True
        else:
            f["V"] = 0
            n = d << 16
            r["X"] = n // x; c.D = n % x
        f["Z"] = int(r["X"] == 0)
    elif m == "BSET":
        v = c.rd8(ea()) | i.f["mask"]; c.wr8(ea(), v); nz(v, 8); f["V"] = 0
    elif m == "BCLR":
        v = c.rd8(ea()) & ~i.f["mask"] & M8; c.wr8(ea(), v); nz(v, 8); f["V"] = 0
    elif m == "BRSET":
        if (~c.rd8(ea()) & i.f["mask"]) & M8 == 0:
            c.pc = (nxt + sx8(i.f["rel"])) & M16
    elif m == "BRCLR":
        if (c.rd8(ea()) & i.f["mask"]) == 0:
            c.pc = (nxt + sx8(i.f["rel"])) & M16
    elif m in ("AIM", "OIM", "EIM", "TIM"):
        mv = c.rd8(ea()); imm = i.f["imm"]
        if m == "TIM":
            res = mv & imm
        else:
            res = {"AIM": mv & imm, "OIM": mv | imm, "EIM": mv ^ imm}[m]
            c.wr8(ea(), res)
        nz(res, 8); f["V"] = 0
    elif m in ("BRA", "BHI", "BLS", "BCC", "BCS", "BNE", "BEQ", "BVC", "BVS", "BPL", "BMI", "BGE", "BLT", "BGT", "BLE"):
        cond = {"BRA": True, "BHI": not (f["C"] or f["Z"]), "BLS": bool(f["C"] or f["Z"]), "BCC": not f["C"],
                "BCS": bool(f["C"]), "BNE": not f["Z"], "BEQ": bool(f["Z"]), "BVC": not f["V"], "BVS": bool(f["V"]),
                "BPL": not f["N"], "BMI": bool(f["N"]), "BGE": f["N"] == f["V"], "BLT": f["N"] != f["V"],
                "BGT": (not f["Z"]) and f["N"] == f["V"], "BLE": bool(f["Z"]) or f["N"] != f["V"]}[m]
        if cond:
            c.pc = (nxt + sx8(i.f["rel"])) & M16
    else:
        raise AssertionError("model: unhandled " + m)
