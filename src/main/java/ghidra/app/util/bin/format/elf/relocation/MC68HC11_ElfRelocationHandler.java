/* SPDX-License-Identifier: Apache-2.0 */
// Added by Ghidra-Rare.
package ghidra.app.util.bin.format.elf.relocation;

import ghidra.app.util.bin.format.elf.*;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Program;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryAccessException;
import ghidra.program.model.reloc.Relocation.Status;
import ghidra.program.model.reloc.RelocationResult;

/**
 * ELF relocation handler for the Motorola 68HC11 (EM_68HC11 = 70), the relocations GNU as emits
 * for m68hc11-elf.  Semantics follow binutils bfd/elf32-m68hc11.c.  GNU as writes SHT_REL sections
 * (the addend is the value already in the field; an SHT_RELA section is honoured too).  S + A is stored as an 8, 16 or 32-bit big-endian value (HI8 and LO8
 * store the high and the low byte), and the PC-relative forms store S + A - P (GNU as puts the
 * -1 or -2 of the branch offset into the addend).
 * R_M68HC11_RL_JUMP and RL_GROUP only mark linker-relaxation groups and are skipped; 3B (a bit
 * number), 24 and PAGE (banked memory) have no meaning for an unbanked 64 KB program and are
 * reported as unhandled.
 */
public class MC68HC11_ElfRelocationHandler extends
		AbstractElfRelocationHandler<MC68HC11_ElfRelocationType, ElfRelocationContext<?>> {

	public static final int EM_68HC11 = 70;

	public MC68HC11_ElfRelocationHandler() {
		super(MC68HC11_ElfRelocationType.class);
	}

	@Override
	public boolean canRelocate(ElfHeader elf) {
		return elf.e_machine() == EM_68HC11;
	}

	/** GNU as writes REL relocations: the addend is the value already in the field. */
	private static long implicitAddend(Memory mem, MC68HC11_ElfRelocationType type, Address a)
			throws MemoryAccessException {
		switch (type) {
			case R_M68HC11_PCREL_8:
				return mem.getByte(a);
			case R_M68HC11_8:
			case R_M68HC11_HI8:
			case R_M68HC11_LO8:
				return mem.getByte(a) & 0xffL;
			case R_M68HC11_PCREL_16:
				return mem.getShort(a);
			case R_M68HC11_16:
			case R_M68HC11_LO16:
				return mem.getShort(a) & 0xffffL;
			case R_M68HC11_32:
				return mem.getInt(a);
			default:
				return 0;
		}
	}

	@Override
	protected RelocationResult relocate(ElfRelocationContext<?> ctx, ElfRelocation relocation,
			MC68HC11_ElfRelocationType type, Address relocationAddress, ElfSymbol elfSymbol,
			Address symbolAddr, long symbolValue, String symbolName) throws MemoryAccessException {

		Program program = ctx.getProgram();
		Memory mem = program.getMemory();
		long P = relocationAddress.getOffset();

		switch (type) {
			case R_M68HC11_NONE:
			case R_M68HC11_GNU_VTINHERIT:
			case R_M68HC11_GNU_VTENTRY:
			case R_M68HC11_RL_JUMP:
			case R_M68HC11_RL_GROUP:
				return RelocationResult.SKIPPED;
			default:
				break;
		}
		if (handleUnresolvedSymbol(ctx, relocation, relocationAddress)) {
			return RelocationResult.FAILURE;
		}
		long A = relocation.hasAddend() ? relocation.getAddend() : implicitAddend(mem, type, relocationAddress);
		long v = symbolValue + A;
		switch (type) {
			case R_M68HC11_8:
			case R_M68HC11_LO8:
				mem.setByte(relocationAddress, (byte) v);
				return new RelocationResult(Status.APPLIED, 1);
			case R_M68HC11_HI8:
				mem.setByte(relocationAddress, (byte) (v >> 8));
				return new RelocationResult(Status.APPLIED, 1);
			case R_M68HC11_PCREL_8:
				mem.setByte(relocationAddress, (byte) (v - P));
				return new RelocationResult(Status.APPLIED, 1);
			case R_M68HC11_16:
			case R_M68HC11_LO16:
				mem.setShort(relocationAddress, (short) v);
				return new RelocationResult(Status.APPLIED, 2);
			case R_M68HC11_PCREL_16:
				mem.setShort(relocationAddress, (short) (v - P));
				return new RelocationResult(Status.APPLIED, 2);
			case R_M68HC11_32:
				mem.setInt(relocationAddress, (int) v);
				return new RelocationResult(Status.APPLIED, 4);
			default:
				markAsUnhandled(program, relocationAddress, type, relocation.getSymbolIndex(),
					symbolName, ctx.getLog());
				return RelocationResult.UNSUPPORTED;
		}
	}
}
