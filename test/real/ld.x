OUTPUT_FORMAT("elf32-m68hc11")
ENTRY(_start)
MEMORY { zp (rw) : ORIGIN = 0x0000, LENGTH = 0x100
         ram (rw) : ORIGIN = 0x0100, LENGTH = 0x0e00
         rom (rx) : ORIGIN = 0x2000, LENGTH = 0xdfc0
         vec (r)  : ORIGIN = 0xffc0, LENGTH = 0x40 }
SECTIONS {
  .softregs (NOLOAD) : { *(.softregs) } > zp
  .text : { *(.text) *(.text.*) } > rom
  .rodata : { *(.rodata) *(.rodata.*) } > rom
  .data : { *(.data) *(.data.*) } > ram AT > rom
  .bss (NOLOAD) : { *(.bss) *(COMMON) } > ram
  .vectors 0xfffe : { *(.vectors) } > vec
}
