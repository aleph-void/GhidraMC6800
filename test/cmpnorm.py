"""Text normalisation shared by slotcmp.py and real_compare.py: reduces a 6800-family disassembly line
to tokens so that spelling differences (#, *, commas, $/0x, padding, aliases) do not count."""
import re

ALIAS = {"lda": "ldaa", "ldb": "ldab", "sta": "staa", "stb": "stab", "ora": "oraa", "orb": "orab",
         "bhs": "bcc", "blo": "bcs", "lsl": "asl", "lsla": "asla", "lslb": "aslb", "lsld": "asld", "cmpx": "cpx"}


def norm(t):
    t = t.lower().strip()
    t = re.sub(r"<[^>]*>", " ", t)                                  # objdump: <symbol+off> annotations
    t = t.replace("0x0x", "0x")
    t = re.sub(r"\$([0-9a-f]+)", r"0x\1", t)                      # unidasm: $12
    t = re.sub(r"\((x|y)\+(0x[0-9a-f]+)\)", r"\2 \1", t)           # unidasm: (X+0x12)
    t = re.sub(r"\b(\w+),([xy])\b", r"\1 \2", t)
    t = re.sub(r"[#*,\$]", " ", t)
    t = re.sub(r"[\[\]()]", " ", t)
    return t.split()


def num(tok):
    tok = ALIAS.get(tok, tok)
    if re.fullmatch(r"-?0x[0-9a-f]+", tok):
        return str(int(tok, 16))
    return tok


def sem(t):
    return [num(x) for x in norm(t)]
