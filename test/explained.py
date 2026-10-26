"""Explained difference classes for slotcmp.py.

explain(variant, ref, ghidra_text, ghidra_len, ref_text, ref_len, hexbytes) -> class name or None.
Every class here has been checked against the manuals (or is a confirmed reference-tool bug);
see GHIDRA-RARE.md "Decode" for the evidence behind each one.
"""
import re

STORE_IMM = {0x87, 0x8F, 0xC7, 0xCD, 0xCF}


def explain(variant, ref, gt, gn, ot, on, hexbytes):
    b = bytes.fromhex(hexbytes) if hexbytes else b""
    op = b[0] if b else -1
    # --- objdump -m m68hc11 ---
    if ref == "objdump" and op == 0x00 and ot and ot.startswith("bgnd") and gt and gt.startswith("TEST"):
        return "objdump prints opcode 0x00 as the HC12 'bgnd'; HC11 has TEST (reference quirk, MAME agrees with Ghidra)"
    # --- MAME unidasm ---
    if ref == "unidasm":
        if ot and ot.startswith("brlcr") and gt and gt.startswith("BRCLR"):
            return "MAME unidasm misspells BRCLR (18 1F, Y-indexed) as 'brlcr' (reference bug)"
        if gt is None and ot and op in STORE_IMM and re.match(r"st[abdxs]\s+#", ot) and variant != "hc11":
            return "MAME decodes the undefined store-immediate opcodes (87 8F C7 CD CF) as 'sta/stb/sts/std/stx #imm'; the manuals leave them undefined"
        if gt is None and ot and variant == "6800" and op == 0x21 and ot.startswith("brn"):
            return "0x21 BRN is a 6801 addition; unused on the MC6800 (MAME decodes it)"
        if gt is None and ot and variant == "6800" and op == 0x9D and ot.startswith("jsr"):
            return "0x9D direct JSR is a 6801 addition; unused on the MC6800 (MAME decodes it)"
        if variant == "6301" and gt is None and ot and op in (0x12, 0x13) and ot.startswith("asx"):
            return "MAME decodes 0x12/0x13 as 'asx1/asx2 1,s' (HD6301 hardware-specific); not in the HD6301 instruction set"
    # --- branch targets outside 0..0xFFFF: the reference prints the unwrapped address, Ghidra wraps ---
    if gt and ot and gn == on and re.match(r"b[a-z]+\s", ot.lower()):
        def nums(t):
            return [int(h, 16) & 0xFFFF for h in re.findall(r"(?:0x|\$)([0-9a-f]+)", t.lower().replace("0x0x", "0x"))]
        if nums(gt) and nums(gt) == nums(ot):
            return "relative branch whose target wraps outside 0..0xFFFF: reference prints the unwrapped address, Ghidra wraps (16-bit PC)"
    return None
