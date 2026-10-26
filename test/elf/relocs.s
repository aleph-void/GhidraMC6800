; Relocations GNU as emits for m68hc11-elf (written for Ghidra-Rare, CC0).
	.sect .text
	.globl _start
_start:
	ldx	#ext_data		; R_M68HC11_16
	ldaa	*ext_zp			; R_M68HC11_8 (direct page)
	jsr	ext_func		; R_M68HC11_16
	.byte	0x20, 0			; bra ext_near
	.reloc	.-1, R_M68HC11_PCREL_8, ext_near
	.byte	0x8d, 0			; bsr ext_near + 2
	.reloc	.-1, R_M68HC11_PCREL_8, ext_near+2
	ldaa	#%lo(ext_data)		; R_M68HC11_LO8
	ldab	#%hi(ext_data)		; R_M68HC11_HI8
	ldd	#ext_data+4		; R_M68HC11_16 with addend
	ldy	ext_data+1		; R_M68HC11_16, prefix opcode
	brset	*ext_zp,#0x81,_start	; R_M68HC11_8 + PCREL_8 (direct + relative)
	bset	3,x,#0x40
	jmp	_start			; local
local:	rts
	.word	0			; a 16-bit PC-relative and a LO16 field
	.reloc	.-2, R_M68HC11_PCREL_16, ext_func
	.word	0
	.reloc	.-2, R_M68HC11_LO16, ext_data+0x20
	.sect .data
	.globl ptr
ptr:	.word	ext_data+2		; R_M68HC11_16 in data
	.long	ext_data		; R_M68HC11_32
	.word	local
