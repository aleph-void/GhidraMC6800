	.sect .softregs
	.globl _.tmp, _.z, _.xy, _.frame, _.d1, _.d2, _.d3, _.d4, _.d5, _.d6, _.d7, _.d8
_.tmp:	.space 2
_.z:	.space 2
_.xy:	.space 2
_.frame: .space 2
_.d1:	.space 2
_.d2:	.space 2
_.d3:	.space 2
_.d4:	.space 2
_.d5:	.space 2
_.d6:	.space 2
_.d7:	.space 2
_.d8:	.space 2

	.sect .text
	.globl _start
_start:
	lds	#0x0fff
	jsr	main
halt:	bra	halt

	.sect .vectors
	.word	_start	; IRQ-style placeholder vectors
