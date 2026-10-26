# GhidraMC6800

A Ghidra extension for the Motorola MC6800 and related MCUs.

![Disassembly](screenshot.png)

## Features

* Contains language specs for Motorola MC6800 and related MPUs.

  The supported instruction sets include:

  - Motorola MC6800, which also covers Motorola MC6802 and MC6808.
  - Motorola MC6801, which also covers Motorola MC6803 as well as Hitachi HD6803.
  - Hitachi HD6301, which also covers Hitachi HD6303 (and the HD63701, whose instruction set is the same).
  - Motorola MC68HC11, with the four opcode pages (0x18, 0x1A, 0xCD prefixes), its interrupt
    vectors and control registers, a GCC calling convention and an ELF loader opinion
    (EM_68HC11).

  The [Ghidra-Rare notes](GHIDRA-RARE.md) list what was verified, how, and what was fixed.

## How to install
1. Download a prebuilt GhidraMC6800 release for your Ghidra version (this fork's
   [Releases page](https://github.com/aleph-void/GhidraMC6800/releases) has zips for the three newest Ghidra
   releases; the original author's are at
   [sigurasg/GhidraMC6800](https://github.com/sigurasg/GhidraMC6800/releases)), or build it yourself.
1. Start Ghidra
1. File -> Install Extensions
1. Press the plus icon ("Add extension")
1. Choose the built or downloaded GhidraMC6800 zip file
1. Restart Ghidra when prompted to load the extension properly

## How to build

### With VS Code and Docker

Open the directory in a VS Code instance and then reopen it in a devcontainer.

In a new terminal window type
```
./gradlew
```

### Otherwise

As a prerequisite, you need to have a Ghidra installation somewhere (an actual
installation, not a copy of Ghidra source code!).

```
export GHIDRA_INSTALL_DIR=/path/to/ghidra
./gradlew
```

or

```
./gradlew -Pghidra.dir=/path/to/ghidra
```

You can then find a built extension .zip in the `dist` directory.

`./gradlew test` (same `GHIDRA_INSTALL_DIR`) runs the JUnit disassembly and emulator tests;
`test/run-tests.sh` runs the Ghidra-Rare differential and emulator suite (see
[GHIDRA-RARE.md](GHIDRA-RARE.md)).

## Known limitations and issues

Status of what upstream listed, and what remains (details in [GHIDRA-RARE.md](GHIDRA-RARE.md)):

| Item | Status |
|---|---|
| Issue #23 "Add 68HC11" (open upstream, but the language existed) | Done and verified; the HC11 language now has its own processor spec (vectors, registers), calling convention, DWARF map and ELF opinion |
| `TODO` in `SWI` ("missing indirection") | Fixed: SWI jumps through its vector (0xFFFA; HC11 0xFFF6) |
| Issue #44 "how MC6800 CPX affects flags" | Resolved: N, Z, V from the 16-bit subtraction and C unaffected is exactly what the MC6800 manual says (and MAME does); the 6801 and later set C. Covered by tests |
| Issue #28 "test all MC6800 instructions in emulation" | Done: every opcode of all four languages is run in Ghidra's emulator against a reference model (about 22,900 cases) plus 183 hand-computed sequences |
| Test `TODO`s: Y instructions, BRSET/BRCLR, BSET/BCLR | Done (and BRSET/BSET/BCLR were wrong: fixed) |
| Issue #3 "More MPUs" (6801U4, 6803E, MC68120/121, HD6301X0/Y0, HD63701, HD6303R/X/Y) | Same instruction sets as the existing languages as far as tested (MAME's unidasm decodes `hd63701` exactly like `hd6301`): use MC6801 or HD6301. The on-chip register maps of the X/Y variants are not described |
| Issue #45 "bake the manuals into the release" | Not done: the manuals are not redistributable here; manual index files exist for the MC6800, MC6801 and MC68HC11 (no index for the HD6301) |
| `WAI`, `STOP`, `SLP` | `WAI` pushes the register frame and continues; `STOP` and `SLP` are no-ops (clock and interrupt state cannot be modelled) |
| Interrupt-vector based entry points | The MC6800/6801/HC11/HD6301 vector tables are entry points; an INIT-remapped HC11 register block is not followed |



## License

Licensed under the Apache License, Version 2.0.
