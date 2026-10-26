# Credits: Motorola 6800 family module (MC6800, MC6801, HD6301/6303, MC68HC11)

This module is a community SLEIGH module that Ghidra-Rare imported, tested and fixed. The original
processor specifications, tests and build were written by the authors below; Ghidra-Rare's changes
are listed after them.

## Upstream

| | |
|---|---|
| Source | [sigurasg/GhidraMC6800](https://github.com/sigurasg/GhidraMC6800), commit `713ae0232f6e2f67b67d6ea0cf9b4e7f6864a6b2` (2026-10-23, "Build with Ghidra 12.2 (#55)") |
| Ghidra-Rare fork | [aleph-void/GhidraMC6800](https://github.com/aleph-void/GhidraMC6800), branch `ghidra-rare` |
| License | Apache-2.0 (`LICENSE`, unchanged); the Ghidra-Rare additions are under the same license |
| Original authors | Sigurdur Asgeirsson ([@sigurasg](https://github.com/sigurasg), commits "Sigurdur Asgeirsson" and "Sigurður Ásgeirsson"): the MC6800, MC6801, HD6301 and MC68HC11 SLEIGH specifications, the JSR analyzer, the JUnit disassembly and emulator tests, the build (2022-2026; the MC68HC11 language was added in December 2025, #31). Antonio Vázquez Blanco ([@antoniovazquezblanco](https://github.com/antoniovazquezblanco)): CI setup (2024) |

Ghidra-Rare's changes are kept as separate commits on branch `ghidra-rare` of a fork of the
upstream repository, on top of its full history, so the original license and authorship are
preserved.

Alternative implementations were read for comparison and not copied: GaryOderNichts/ghidra-hc11-lang
(the text of Ghidra pull request #5068 plus a one-line `oprx8_Y` typo fix; Apache-2.0), used only to compare the depth of the
HC11 specification (it has no 6800, 6801 or HD6301 and models DAA and STOP as pcodeops). The HC11
interrupt vector names and register symbols in `mc68hc11.pspec` are taken from the NXP M68HC11
Reference Manual's tables, not from that repository.

## Ghidra-Rare changes

All of them were found by the differential, model-checked and real-code tests in `test/`
(see `GHIDRA-RARE.md`).

1. **Semantics fixed in `mc6800.sinc`, `mc6801.sinc`, `mc68hc11.sinc`:**
   - ROR shifted arithmetically (sign bit replicated); all shifts and rotates, ASLD and LSRD now set
     V = N xor C; LSRD shifted left.
   - BRN is a two-byte instruction (the pattern was one byte); found by the decode differential.
   - TST clears C; MUL sets C from bit 7 of the result; ABA sets H.
   - DAA follows the manuals' correction table (C was wrongly kept or recomputed).
   - TAP cleared H (`A & 0x1F`); CC bits 7 and 6 read as 1 on the MC6800/6801/HD6301 (TPA, pushed
     CC byte); the HC11's S and X bits exist, X can only be cleared by TAP/RTI.
   - On the HC11, SWI/WAI/RTI push and pull Y; SWI jumps through the vector (it called the
     vector's address; the upstream TODO) and uses the HC11 vector 0xFFF6.
   - HC11 BRSET branched when any masked bit was set instead of all; BSET/BCLR set N, Z and V.
2. **Spec files.** A processor spec for the HC11 (the 21 vectors and the control registers at
   0x1000; before, it shared the 6801's), a GCC-ABI compiler spec for the HC11 (derived from GCC
   3.4.6 output), the 6800-family spec gained the return address slot and stack parameters, a DWARF
   register map, an ELF opinion (EM_68HC11 = 70), the HD6301 TRAP vector, a manual index
   (`mc68hc11.idx`, page numbers of the NXP M68HC11 Reference Manual).
3. **ELF relocation handler** for the MC68HC11 (`MC68HC11_ElfRelocationHandler`).
4. **Tests.** Two upstream expectations that encoded the old flags were corrected
   (`EmulatorMC68HC11Test.ASL_Y`, `LSR_Y`); `EmulatorMC6800FixesTest`, `EmulatorMC6801FixesTest`,
   `EmulatorMC68HC11FixesTest` (25 regression tests, including the BRSET/BRCLR, BSET/BCLR and Y
   instruction tests upstream listed as TODO); the whole of `test/`.
5. **README.md:** the MC68HC11 was missing from the list of supported processors; install pointer
   and limitations section. Upstream's text is otherwise unchanged.
6. **build.gradle:** `copyDependencies` disabled and `test/`, `tools/` excluded from the zip.

Ghidra-Rare additions (not upstream): `GHIDRA-RARE.md`, `CREDITS.md`, `test/`,
`data/languages/mc68hc11.{pspec,cspec,dwarf,opinion}`, `data/languages/hd6301.pspec`,
`data/manuals/mc68hc11.idx`, `src/main/java/ghidra/app/util/bin/format/elf/relocation/MC68HC11_*`,
`src/test/java/is/sort/mc6800/Emulator*FixesTest.java`, and the release workflow added by the
repository owner.

Test inputs used by `test/` and not part of this repository (fetched by pinned URL and SHA-256 by
`test/fetch-real-samples.sh`): Brad Conte's crypto-algorithms (public domain), kokke's tiny-AES-c and
tiny-regex-c (Unlicense), compiled with GNU binutils 2.45 and GCC 3.4.6 (GPL), which
`test/build-toolchain.sh` builds.
