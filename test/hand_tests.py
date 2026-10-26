"""Hand-computed emulator sequences for the 6800 family (see gen_emu.py / EmuCheck.java).

Every expectation below was worked out by hand from the manuals, never copied from the module's
output.  Code is placed at 0x1000.  A test names the variants it applies to; an expectation may
be a dict {variant-group: text} where the groups are "all", "6800", "6801" (6801+6301+hc11
differences), "hc11".  Stack area: 0x30E0-0x30FF, data windows 0x0040/0x2000.
"""
PC = 0x1000
ALL = ("6800", "6801", "6301", "hc11")
F6801 = ("6801", "6301", "hc11")


def T(name, variants, code, init, expect, stop=None):
    return dict(name=name, variants=variants, code=code.replace(" ", ""), init=init, expect=expect, stop=stop)


def pad(code, at, blob):
    """place blob at address `at` inside a code string that starts at 0x1000"""
    b = bytes.fromhex(code.replace(" ", ""))
    off = at - PC
    b = b.ljust(off, b"\x01") + bytes.fromhex(blob.replace(" ", ""))
    return b.hex()


TESTS = [
    # ---- ALU, flags ----
    T("add_overflow_halfcarry", ALL, "86 7F 8B 01", "-", "A=80,CC/3f=2a"),                  # 7F+01: N V H
    T("sub_borrow", ALL, "86 10 80 20", "-", "A=f0,CC/3f=09"),                               # 10-20 = F0, N C
    T("adc_chain", ALL, "86 FF 8B 01 C6 00 C9 00", "-", "A=00,B=01,CC/3f=00"),               # FF+1 -> C; 0+0+C = 1
    T("sbc_borrow_in", ALL, "0D 86 05 82 05", "-", "A=ff,CC/3f=09"),                         # 5-5-1 = FF, N C
    T("logic_and_or_eor", ALL, "86 F0 84 3C 8A 05 88 FF", "-", "A=ca,CC/3f=08"),             # 30, 35, CA
    T("bit_test_zero", ALL, "86 0F 85 F0", "-", "A=0f,CC/3f=04"),
    T("neg_com", ALL, "86 80 40 C6 00 53", "-", "A=80,B=ff,CC/3f=09"),                        # NEGA(80)=80 V C N; COMB
    T("shift_rotate_chain", ALL, "86 81 48 44 46 49", "-", "A=01,CC/3f=00"),                 # 02(C V), 01, 00(C Z V), 01
    T("asr_keeps_sign", ALL, "86 81 47", "-", "A=c0,CC/3f=09"),                               # C0, C=1, N=1, V=N^C=0
    T("inc_dec_overflow", ALL, "86 7F 4C 4A", "-", "A=7f,CC/3f=02"),                          # 80 (V N), then 7F (V)
    T("tst_clears_carry", ALL, "0D 86 00 4D", "-", "A=00,CC/3f=04"),
    T("clr_clears_flags", ALL, "86 55 4F", "CC=0b", "A=00,CC/3f=04"),
    T("daa_19_plus_28", ALL, "86 19 8B 28 19", "-", "A=47,CC/3f=20"),                         # 41 H -> +06 = 47
    T("daa_99_plus_01", ALL, "86 99 8B 01 19", "-", "A=00,CC/3f=05"),                         # 9A -> +66 = 00, C Z
    T("aba_sba_tab_tba", ALL, "86 30 C6 40 1B 10 16 17", "-", "A=30,B=30,CC/3f=00"),
    # ---- addressing modes, memory ----
    T("indexed_store_load_inc", ALL, "CE 20 00 86 42 A7 05 E6 05 6C 05", "-", "X=2000,A=42,B=42,m2005=43,CC/3f=00"),
    T("direct_and_extended", ALL, "86 A5 97 50 B7 20 10 D6 50", "-", "A=a5,B=a5,m0050=a5,m2010=a5,CC/3f=08"),
    T("sixteen_bit_load_store", ALL, "CE 12 34 FF 20 00 8E 30 F0 BF 20 02 08 09 09", "-",
      "X=1233,S=30f0,m2000=12,m2001=34,m2002=30,m2003=f0,CC/3f=00"),
    # ---- stack, calls ----
    T("push_pull_order", ALL, "8E 30 F0 86 11 C6 22 36 37 4F 5F 32 33", "-",
      "A=22,B=11,S=30f0,m30f0=11,m30ef=22,CC/3f=04"),
    T("bsr_rts", ALL, pad("8E 30 F0 8D 0A 86 77", 0x100F, "C6 05 39"), "-",
      "A=77,B=05,S=30f0,m30f0=05,m30ef=10", stop=0x1007),
    T("jsr_ext_jsr_indexed", ALL, pad(pad("8E 30 F0 BD 10 10 CE 10 14 AD 00", 0x1010, "4C 39"), 0x1014, "5C 39"), "-",
      "A=01,B=01,X=1014,S=30f0,m30f0=0b,m30ef=10,CC/3f=00", stop=0x100B),
    # ---- branches ----
    T("loop_bne", ALL, "86 00 C6 05 8B 03 5A 26 FB", "-", "A=0f,B=00,CC/3f=04"),
    T("blt_taken_signed", ALL, "86 80 81 01 2D 02 C6 11", "-", "B=00,CC/3f=02", stop=0x1008),
    T("bhi_taken_unsigned", ALL, "86 80 81 01 22 02 C6 11", "-", "B=00,CC/3f=02", stop=0x1008),
    T("bgt_not_taken_on_equal", ALL, "86 05 81 05 2E 02 C6 11", "-", "B=11,CC/3f=00"),
    T("bcs_taken_on_borrow", ALL, "86 01 81 02 25 02 C6 11", "-", "B=00,CC/3f=09", stop=0x1008),
    # ---- CC register ----
    T("flag_instructions_set", ALL, "0D 0B 0F 0C", "-", "CC/3f=12"),                           # C V I, then C cleared
    T("flag_instructions_clear", ALL, "0D 0B 0F 0C 0A 0E", "-", "CC/3f=00"),
    T("tap_tpa_6800", ("6800", "6801", "6301"), "86 15 06 86 00 07", "-", "A=d5,CC/3f=15"),     # bits 7,6 read as 1
    T("tap_tpa_hc11", ("hc11",), "86 15 06 86 00 07", "-", "A=15,CC/ff=15"),
    T("tap_x_bit_cannot_be_set", ("hc11",), "86 00 06 86 40 06 07", "CC=40", "A=00,CC/ff=00"),
    T("tap_s_bit_settable", ("hc11",), "86 80 06 07", "-", "A=80,CC/ff=80"),
    # ---- interrupts ----
    T("swi_rti_6800", ("6800", "6801", "6301"), pad("3F", 0x1020, "3B"),
      "A=12,B=34,X=abcd,CC=05,S=30f0,mfffa=1020",
      "A=12,B=34,X=abcd,CC/3f=05,S=30f0,m30f0=01,m30ef=10,m30ee=cd,m30ed=ab,m30ec=12,m30eb=34,m30ea=c5",
      stop=0x1001),
    T("swi_rti_hc11", ("hc11",), pad("3F", 0x1020, "3B"),
      "A=12,B=34,X=abcd,Y=beef,CC=85,S=30f0,mfff6=1020",
      "A=12,B=34,X=abcd,Y=beef,CC/ff=85,S=30f0,m30f0=01,m30ef=10,m30ee=ef,m30ed=be,m30ec=cd,m30eb=ab,m30ea=12,m30e9=34,m30e8=85",
      stop=0x1001),
    T("swi_enters_handler_6800", ("6800", "6801", "6301"), "3F", "S=30f0,CC=00,mfffa=1020", "PC=1020,S=30e9,CC/3f=10,m30f0=01,m30ef=10,m30ee=00,m30ed=00,m30ec=00,m30eb=00,m30ea=c0", stop="n1"),
    T("swi_enters_handler_hc11", ("hc11",), "3F", "S=30f0,CC=00,mfff6=1020", "PC=1020,S=30e7,CC/ff=10,m30f0=01,m30ef=10,m30ee=00,m30ed=00,m30ec=00,m30eb=00,m30ea=00,m30e9=00,m30e8=00", stop="n1"),
    T("wai_pushes_state_6800", ("6800", "6801", "6301"), "3E", "A=12,B=34,X=abcd,CC=05,S=30f0",
      "S=30e9,m30f0=01,m30ef=10,m30ee=cd,m30ed=ab,m30ec=12,m30eb=34,m30ea=c5", stop="n1"),
    # ---- 6801 and later ----
    T("mul_carry_is_bit7", F6801, "86 80 C6 03 3D", "-", "A=01,B=80,CC/3f=01"),
    T("abx_unsigned", F6801, "CE 00 FF C6 81 3A", "-", "X=0180,B=81,CC/3f=08"),
    T("addd_subd_std", F6801, "CC 12 34 C3 0F FF 83 30 00 FD 20 00", "-", "A=f2,B=33,m2000=f2,m2001=33,CC/3f=09"),
    T("asld_lsrd", F6801, "CC 80 01 05 04 04", "-", "A=00,B=00,CC/3f=07"),
    T("lsrd_shifts_right", F6801, "CC 12 34 04", "-", "A=09,B=1a,CC/3f=00"),                  # 1234 >> 1 = 091A
    T("pshx_pulx", F6801, "8E 30 F0 CE AB CD 3C CE 00 00 38", "-", "X=abcd,S=30f0,m30f0=cd,m30ef=ab,CC/3f=04"),
    T("cpx_carry_6800", ("6800",), "CE 00 01 8C 00 02", "-", "CC/3f=08"),                       # C not affected
    T("cpx_carry_6801", F6801, "CE 00 01 8C 00 02", "-", "CC/3f=09"),                          # C = borrow
    T("brn_is_two_bytes", F6801, "21 02 C6 11", "-", "B=11"),
    T("jsr_direct", F6801, pad("8E 30 F0 9D 50", 0x1005, "01"), "m0050=4c39", "A=01,S=30f0,m30f0=05,m30ef=10", stop=0x1005),
    # ---- HD6301 additions ----
    T("xgdx_18", ("6301",), "CC 11 22 CE 33 44 18", "-", "A=33,B=44,X=1122"),
    T("aim_oim_eim_tim", ("6301",), "71 0F 50 72 F0 50 75 FF 50 7B 04 50", "m0050=3c", "m0050=03,CC/3f=04"),
    T("aim_indexed", ("6301",), "CE 20 00 61 F0 02", "m2002=a5", "m2002=a0,CC/3f=08"),
    # ---- HC11 ----
    T("hc11_y_register_ops", ("hc11",), "18 CE 12 34 18 08 18 09 18 09 18 FF 20 00", "-", "Y=1233,m2000=12,m2001=33,CC/ff=00"),
    T("hc11_y_indexed", ("hc11",), "18 CE 20 00 86 5A 18 A7 03 18 E6 03 18 6C 03", "-", "Y=2000,A=5a,B=5a,m2003=5b,CC/ff=00"),
    T("hc11_cpd_prefix_1a", ("hc11",), "CC 10 00 1A 83 10 00", "-", "A=10,B=00,CC/ff=04"),
    T("hc11_cpx_y_prefix_cd", ("hc11",), "CE 12 34 18 CE 20 00 CD AC 02", "m2002=1234", "X=1234,Y=2000,CC/ff=04"),
    T("hc11_ldx_stx_y_prefix_cd", ("hc11",), "18 CE 20 00 CD EE 02 CD EF 04", "m2002=1234", "X=1234,m2004=12,m2005=34"),
    T("hc11_cpy_immediate", ("hc11",), "18 CE 00 10 18 8C 00 20", "-", "CC/ff=09"),
    T("hc11_ldy_sty_x_indexed_1a", ("hc11",), "CE 20 00 1A EE 02 1A EF 04", "m2002=1234", "Y=1234,m2004=12,m2005=34"),
    T("hc11_xgdx_xgdy", ("hc11",), "CC 11 22 CE 33 44 8F 18 CE 55 66 18 8F", "-", "A=55,B=66,X=1122,Y=3344,CC/ff=00"),
    T("hc11_aby", ("hc11",), "18 CE 00 FF C6 FF 18 3A", "-", "Y=01fe,B=ff,CC/ff=08"),
    T("hc11_pshy_puly", ("hc11",), "8E 30 F0 18 CE BE EF 18 3C 18 CE 00 00 18 38", "-", "Y=beef,S=30f0,m30f0=ef,m30ef=be,CC/ff=04"),
    T("hc11_tsy_tys", ("hc11",), "8E 30 00 18 30 18 CE 20 00 18 35", "-", "Y=2000,S=1fff"),
    T("hc11_idiv", ("hc11",), "CC 00 64 CE 00 07 02", "-", "X=000e,A=00,B=02,CC/ff=00"),
    T("hc11_idiv_zero_quotient", ("hc11",), "CC 00 05 CE 00 07 02", "-", "X=0000,A=00,B=05,CC/ff=04"),
    T("hc11_idiv_by_zero", ("hc11",), "CC 00 05 CE 00 00 02", "-", "X=ffff,CC/ff=01"),
    T("hc11_fdiv", ("hc11",), "CC 00 01 CE 00 04 03", "-", "X=4000,A=00,B=00,CC/ff=00"),
    T("hc11_fdiv_overflow", ("hc11",), "CC 00 04 CE 00 04 03", "-", "X=ffff,CC/ff=02"),
    T("hc11_bset_bclr", ("hc11",), "14 50 F0 15 50 0F", "m0050=0f", "m0050=f0,CC/ff=08"),
    T("hc11_brset_taken", ("hc11",), "14 50 F0 15 50 0F 12 50 F0 02 C6 11", "m0050=0f", "B=00,m0050=f0,CC/ff=08", stop=0x100C),
    T("hc11_brset_not_taken", ("hc11",), "12 50 FF 02 C6 11", "m0050=f0", "B=11,CC/ff=00"),
    T("hc11_brclr_taken", ("hc11",), "13 50 0F 02 C6 11", "m0050=f0", "B=00", stop=0x1006),
    T("hc11_bset_x_bclr_y", ("hc11",), "CE 20 00 1C 04 81 18 CE 20 00 18 1D 04 80", "m2004=00", "m2004=01,CC/ff=00"),
    T("hc11_brset_y_taken", ("hc11",), "18 CE 20 00 18 1E 04 81 02 C6 11", "m2004=ff", "B=00", stop=0x100D),
    T("hc11_stop_test_nops", ("hc11",), "CF 00 01", "A=12", "A=12", stop=0x1003),
]


def _expand(t, variant):
    code = bytes.fromhex(t["code"])
    stop = t["stop"] if t["stop"] is not None else None
    init = t["init"]
    ex = t["expect"]
    if stop is None:
        # tests without an explicit stop run to the end of the code, or one instruction when PC= is given
        stop = PC + len(code)
    stops = stop if isinstance(stop, str) else f"{stop:x}"
    # default registers/seed
    inits = [] if init == "-" else init.split(",")
    names = {kv.split("=")[0] for kv in inits}
    if "seed" not in names:
        inits.append("seed=77")
    cc_mask = "ff" if variant == "hc11" else "3f"
    exs = ex.split(",")
    exs.append("win" if not any(e.startswith("m") for e in exs) else "")
    # memory expectations also imply the window check, so mark it unless the test writes outside windows
    if "win" not in exs:
        exs.append("win")
    exs = [e for e in exs if e]
    if "PC=" not in ex and not stops.startswith("n"):
        pass
    return f"{variant}_hand_{t['name']} {PC:x} {stops} {code.hex()} {','.join(inits)} {','.join(exs)}"


def lines(variant):
    return [_expand(t, variant) for t in TESTS if variant in t["variants"]]


def broken():
    t = TESTS[0]
    ln = _expand(t, "6800")
    return [ln.replace("A=80", "A=81", 1).replace("6800_hand_", "6800_broken_", 1)]
