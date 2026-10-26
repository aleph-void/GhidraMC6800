# Motorola 6800 family: Ghidra-Rare notes

This directory is a Ghidra-Rare fork of [sigurasg/GhidraMC6800](https://github.com/sigurasg/GhidraMC6800)
(Apache-2.0, see `CREDITS.md`). It holds four SLEIGH languages: MC6800 (also MC6802, MC6808), MC6801
(also MC6803 and Hitachi HD6803), HD6301 (also HD6303 and, as far as MAME's disassembler shows, the
HD63701) and MC68HC11. `README.md` is the upstream one with the stale claims corrected; this file is
Ghidra-Rare's account of what was tested, what was found and what remains.

| Language ID | Processors | Notes |
|---|---|---|
| `MC6800:BE:16:default` | MC6800, MC6802, MC6808 | 197 opcodes |
| `MC6801:BE:16:default` | MC6801, MC6803, HD6803 | 220 opcodes: adds D, ASLD/LSRD, MUL, ABX, PSHX/PULX, BRN, JSR direct, full CPX flags |
| `HD6301:BE:16:default` | HD6301, HD6303 | 230 opcodes: adds AIM/OIM/EIM/TIM, XGDX, SLP; TRAP vector |
| `MC68HC11:BE:16:default` | MC68HC11 (A8, E9, ...) | 308 opcodes over four pages (0x18/0x1A/0xCD prefixes); vectors and registers; GCC ABI; ELF opinion EM_68HC11 (70) |

The language IDs are upstream's; none collides with Ghidra's own or with another module here.

## Testing

```
export GHIDRA_INSTALL_DIR=<scratch copy of Ghidra 12.1.x or 12.2>   # the module is symlinked into it
export SLOTDIS=<binary>   # or BU_SRC + BU_LIB: binutils 2.45 source and a libopcodes.a build with m68hc11
test/run-tests.sh [--real] <workdir>     # FUZZ_SLOTS and EMU_PER_OP shrink the random corpora for a quick check
```

Without `--real` the suite needs only Ghidra, a JDK, binutils' libopcodes and MAME's `unidasm`. With `--real` it builds an m68hc11-elf toolchain (GNU binutils 2.45 and the C
compiler of GCC 3.4.6, `test/build-toolchain.sh`), fetches three freely licensed C code bases by pinned
URL and SHA-256 (`test/fetch-real-samples.sh`), compiles and links them at five optimisation levels
(`test/build-real.sh`), and runs `test/real-binaries.sh` and `test/reloc-check.sh`. The JUnit tests
of upstream (and the 25 added here) run with `./gradlew test` (432 tests, all passing).

| Step | Files |
|---|---|
| Decode differential | `gen_corpus.py`, `run-decode.sh`, `ghidra-slots.sh`/`DumpSlots.java`, `slotdis.c`, `unislot.py`, `slotcmp.py`, `explained.py` |
| Every-entry test | `entry_check.py` |
| P-code checks | `model6800.py` (reference model from the manuals), `hand_tests.py`, `gen_emu.py`, `EmuCheck.java`, `run-emu.sh` |
| Real code | `build-toolchain.sh`, `fetch-real-samples.sh`, `build-real.sh`, `real-binaries.sh`, `RealCheck.java`, `real_compare.py` |
| Relocations | `reloc-check.sh`, `elf/relocs.s`, `DumpMem.java`, `rawcmp.py` |

## Results

| Area | State |
|---|---|
| Decode | 0 unexplained differences in 258,048 compared slots (every opcode of every page times four operand patterns, and 40,960 random 8-byte slots per language): see the table below. Every-entry: 197/197 (MC6800), 220/220 (MC6801), 230/230 (HD6301), 308/308 (MC68HC11) opcode-table entries decode, and no opcode outside the tables does |
| Semantics | Every opcode of all four languages runs in Ghidra's emulator (22,920 model-checked cases, 24 per opcode with edge-biased operands and flags, results and all four memory windows compared) plus 183 hand-computed sequences (ALU and flags, every addressing mode, stack, calls, branches, interrupt frames, HC11 prefix pages, divide, bit operations): 0 failures; one deliberately wrong expectation is reported (the suite fails when it is not). 432 JUnit tests pass |
| Real code | 10 m68hc11-elf programs (B-Con crypto-algorithms: arcfour, base64, md2, md5, rot-13, sha1, sha256; tiny-AES-c; tiny-regex-c; GCC 3.4.6 at -O0, -O1, -O2, -Os, -O1 -g), imported headless with no forced language (the ELF opinion selects MC68HC11): 87,662 instructions in 602 functions, 0 bad-instruction bookmarks, 602/602 functions decompile; every instruction Ghidra found is identical (exact or semantic) to `objdump -d` at the same address (87,662/87,662), and objdump has 0 instructions Ghidra did not reach. The ELF relocation handler matches GNU ld byte for byte on four relocatable objects |
| Doesn't work | See "Doesn't work" |
| Unverified | See "Unverified" |

### Decode differential

Each language is compared with the reference on 8-byte slots (the longest instruction is 5 bytes), the
first instruction of each slot. "Exact" is identical text after whitespace and case normalisation;
"semantic" is the same instruction spelled differently (`#`/`*` markers, `$12` vs `0x12`, `(X+0x12)`
vs `0x12,X`, `lda` vs `ldaa`, `cmpx` vs `cpx`, zero padding); "both invalid" means both reject the
bytes; every "explained" difference is in one of the classes listed under "Reference tool bugs and
quirks". Lengths must agree for every accepted slot.

| Comparison | Slots | Exact | Semantic | Both invalid | Explained | Unexplained |
|---|---|---|---|---|---|---|
| MC68HC11 vs GNU binutils 2.45 `objdump -m m68hc11` (libopcodes) | 45,056 | 19,621 | 3,881 | 21,479 | 75 | 0 |
| MC68HC11 vs MAME `unidasm -arch hc11` | 45,056 | 22,768 | 785 | 21,479 | 24 | 0 |
| MC6801 vs MAME `unidasm -arch m6803` | 41,984 | 27,240 | 8,856 | 5,091 | 797 | 0 |
| HD6301 vs MAME `unidasm -arch hd6301` | 41,984 | 28,177 | 9,576 | 3,053 | 1,178 | 0 |
| HD6301 vs MAME `unidasm -arch hd63701` | 41,984 | 28,177 | 9,576 | 3,053 | 1,178 | 0 |
| MC6800 vs MAME `unidasm -arch m6800` | 41,984 | 24,360 | 8,038 | 8,615 | 971 | 0 |

Ghidra prints some operands differently from Motorola assembler syntax (`BSET 0x50 0xF0`, not
`bset *0x50,#0xF0`; direct-page addresses are padded to 4 digits). That is upstream's display and
is not changed; the Ghidra assembler accepts the displayed form.

### Real code

| Program | Instructions | Functions | Bad-instr. bookmarks | Decompiled | Agree with objdump | Not reached |
|---|---|---|---|---|---|---|
| crypto-O0 | 17,387 | 55 | 0 | 55/55 | 17,387/17,387 | 0 |
| crypto-O1 | 12,573 | 55 | 0 | 55/55 | 12,573/12,573 | 0 |
| crypto-O1g | 12,577 | 55 | 0 | 55/55 | 12,577/12,577 | 0 |
| crypto-O2 | 13,513 | 55 | 0 | 55/55 | 13,513/13,513 | 0 |
| crypto-Os | 12,291 | 55 | 0 | 55/55 | 12,291/12,291 | 0 |
| tiny-O0 | 5,839 | 71 | 0 | 71/71 | 5,839/5,839 | 0 |
| tiny-O1 | 3,514 | 71 | 0 | 71/71 | 3,514/3,514 | 0 |
| tiny-O1g | 3,514 | 71 | 0 | 71/71 | 3,514/3,514 | 0 |
| tiny-O2 | 3,324 | 57 | 0 | 57/57 | 3,324/3,324 | 0 |
| tiny-Os | 3,130 | 57 | 0 | 57/57 | 3,130/3,130 | 0 |

The one "Bad instruction" message in each decompile is a function Ghidra makes at address 0 from an
absolute symbol of GCC's library assembly (`A_low`); it is not code. The `-g` programs also report
DWARF source-map errors (negative line numbers in GCC 3.4.6's line tables); nothing in them concerns
the module. The programs use GCC's memory-based soft registers (`_.frame`, `_.d1`, ...) for the frame
pointer, so the decompiler shows `B_high`, `__d2` and similar globals and cannot follow frame-pointer
loads (a property of GCC 3.4's code generation, not of the module).

Relocation check (`test/reloc-check.sh`: Ghidra's relocated bytes against the same object linked by
GNU ld at the addresses Ghidra chose; the first object is a hand-written one with every relocation
type GNU as emits):

```
    -- relocs.o: relocations: {APPLIED=16, SKIPPED=3}; compared 46 bytes with the ld-linked object: 0 differ
    -- t-aes-O1.o: relocations: {APPLIED=608, SKIPPED=68}; compared 3365 bytes with the ld-linked object: 0 differ
    -- c-sha256-O1.o: relocations: {APPLIED=474, SKIPPED=69}; compared 4049 bytes with the ld-linked object: 0 differ
    -- c-md5-O0.o: relocations: {APPLIED=2688, SKIPPED=93}; compared 17239 bytes with the ld-linked object: 0 differ
```

## What was found and fixed

Upstream's tests passed before these fixes: they checked a few instructions each and, for the
shifts, asserted the wrong flags.

- **BRN** (0x21, 6801/6301/HC11) was a one-byte instruction; it has an offset byte. Every BRN
  desynchronised the following disassembly. Found by the decode differential.
- **ROR** shifted arithmetically before OR-ing the carry in, replicating the sign bit; **all shifts
  and rotates, ASLD and LSRD never set V** (V = N xor C); **LSRD shifted left**.
- **TST** did not clear C; **MUL** took C from bit 15 instead of bit 7 of the result; **ABA** did not
  set H.
- **DAA** cleared C when it was already set and the +0x60 correction did not carry; it is now the
  manuals' correction table.
- **TAP** loaded `A & 0x1F` (clearing H); the **CC register** now has the HC11's S and X bits (X can only
  be cleared, by TAP and RTI) and reads bits 7 and 6 as 1 on the other three processors (TPA, and the
  CC byte SWI/WAI push).
- **HC11 interrupt frame**: SWI, WAI and RTI did not push/pull Y. **SWI** called the address of its
  vector instead of the handler stored there (upstream's `TODO`), and used the 6800 vector address
  (0xFFFA) on the HC11, whose SWI vector is 0xFFF6.
- **HC11 BRSET** branched when any masked bit was set (all, per the manual); **BSET/BCLR** did not set
  N, Z, V.
- **HC11 spec files**: the language used the MC6801's processor spec (wrong vectors, no HC11 registers).
  It now has its own vector table (21 vectors), control registers at 0x1000, a GCC-ABI compiler spec
  (derived from GCC 3.4.6 output: first argument in D or X:D, rest on the stack, results in D or X:D), a
  DWARF register map, an ELF opinion (EM_68HC11 = 70) and a manual index.
- **All four**: the compiler spec had no return-address slot and no stack parameters; the HD6301 pspec
  lacked its TRAP vector (0xFFEE, from the Hitachi data book).
- **ELF relocation handler** for EM_68HC11 (relocatable objects were imported with every reference to 0).

## Upstream's own known limitations

| Item | Status |
|---|---|
| `TODO(siggi)` in SWI | Fixed (above) |
| Issue #44, how MC6800 CPX affects flags | The code was already what the MC6800 Programming Reference Manual specifies (N from the high byte, Z from both bytes, V from the subtraction, C untouched) and what MAME does; tests added. The HC11 and 6801 set C |
| Issue #28, test all instructions in emulation | Done (22,920 model-checked cases and 183 hand-computed sequences) |
| Issue #23, add 68HC11 (open though implemented) | Verified and completed (above) |
| Test `TODO`s (Y instructions, BRSET/BRCLR, BSET/BCLR; JSR analyzer analysis) | The first three tested (and the bugs found). The JSR analyzer's own `TODO` (test the actual analysis) is not done: the analyzer is disabled by default and only re-marks the primary reference of computed JSRs |
| Issue #3, more MPUs (6801U4, 6803E, MC68120/121, HD6301X0/Y0, HD63701, HD6303R/X/Y) | Same instruction sets as MC6801/HD6301 as far as MAME's `unidasm` shows (`hd63701` decodes exactly like `hd6301`); use those languages. The on-chip register maps of the X/Y variants are not described (no manual tested) |
| Issue #45, bake the manuals into the release | Not done: the manuals are not redistributable by this project. Manual index files exist for MC6800, MC6801 and MC68HC11; none for HD6301 (the Hitachi data book covers many products in one scan; no per-instruction page map was made) |
| Closed issues #12/#17 (BGT/BLT), #18 (HD6803) | Re-checked: all branch conditions pass the model checks; the HD6803 is the MC6803 |

### Comparison with the alternative HC11 implementations

GaryOderNichts/ghidra-hc11-lang (and Ghidra PR #5068, same text plus a typo fix) is HC11 only. On the same
opcode corpus its decode agrees with objdump on 1,225 of the 1,233 slots objdump accepts; the differences are the same
BRN length bug, opcode 0x00 (`TEST`) rejected, and double-prefix sequences (`18 18 FF`) accepted. Its p-code
uses pcodeops for DAA, STOP and LDS (`SP = LoadStack(...)`), so SP is not modelled. For the HD6301/6303: PR #6314
(HD6303 only) compiles, but on the opcode corpus it accepts 12 opcodes (48 of the 1,024 enumerated slots) that
MAME and the manuals leave undefined (e.g. opcode 0x00 as `SUB A,#imm`) and misspells BHI and BMI as `BGI` and `BNI`; PR #1904 (HD6301 in the 6805 directory) does not compile with Ghidra 12.1.4
(inconsistent `OP1`/`OP2` export sizes). `gh search repos` also finds ajxs/ghidra-6303 (HD6303, no license, bundled with Psion ROM images), which could not be
used or imported. The HC11 comparison is the one that mattered: this module is the
only one of the four with MC6800, MC6801, HD6301 and MC68HC11 together, with tests.

## Doesn't work

- **WAI** pushes the register frame and continues with the next instruction (no interrupt source to
  wait for); **STOP**, **SLP** and the HC11 **TEST** opcode are no-ops. Clock and interrupt state cannot be
  modelled.
- Undefined opcodes decode as bad instructions; the HC11's illegal-opcode trap (vector 0xFFF8) and the
  HD6301's TRAP (0xFFEE) are not simulated.
- The HC11 register block is described at its reset address (0x1000); an INIT register remap is not followed.
- Debug information from GCC: its frame base (DWARF register 9) is a memory soft register, so
  frame-relative variable locations are not mapped; only D, X, Y, SP, PC, A, B and CC are.
- ELF relocations R_M68HC11_24, _3B and _PAGE (banked memory) are reported as unhandled; unbanked programs
  never use them.
- The MC6800/6801/HD6301 compiler spec is a heuristic (A, B, X, then the stack): those processors have no
  standard ABI.

## Unverified

- Real silicon: every semantic check is against the manuals' instruction descriptions (as the reference model
  implements them), not against hardware. Behaviour the manuals call indeterminate (IDIV by zero remainder,
  FDIV overflow remainder, DAA's V, shifts of reserved CC bits) is not compared.
- Real MC6800, MC6801 and HD6301/6303 firmware: no freely licensed binaries or compiler for them were found;
  these three are verified by the decode differential and by the emulator model only. The HD6301's
  AIM/OIM/EIM/TIM flags (N, Z, V cleared) are checked only against the instruction descriptions.
- MC6801/HD6301 on-chip peripherals: upstream's register symbols are unchanged.
- The DWARF register map was exercised on GCC 3.4.6 `-g` programs (the import runs, D is mapped for
  locals in D); no other compiler for the HC11 was available.

## Reference tool bugs and quirks

Each was checked against the manual of the processor it concerns.

- **objdump `-m m68hc11` prints opcode 0x00 as `bgnd`**, the HC12 instruction; the HC11 has `TEST` there
  (M68HC11 Reference Manual, opcode map; MAME agrees). 75 slots.
- **objdump prints branch targets as `0x0x422`** (a doubled prefix); display only.
- **MAME `unidasm` misspells BRCLR (18 1F, Y-indexed) as `brlcr`**, on the HC11.
- **MAME decodes the undefined store-immediate opcodes** (0x87, 0x8F, 0xC7, 0xCD, 0xCF) on the 6800, 6801 and
  HD6301 as `sta/sts/stb/std/stx #imm`; the Programming Reference Manual, MC6801 and HD6301 opcode maps leave
  them unassigned (the HC11 uses 0xCD as a prefix and 0xCF as STOP).
- **MAME decodes 0x12 and 0x13 on the HD6301 as `asx1`/`asx2 1,s`**; they are not in the HD6301/6303 data book.
- **MAME decodes 0x21 (BRN) and 0x9D (direct JSR) on the MC6800**, where they are 6801 additions.
- Both tools print the target of a relative branch near address 0 or 0xFFFF unwrapped; Ghidra wraps to 16 bits.
