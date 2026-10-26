/* SPDX-License-Identifier: Apache-2.0 */
// Added by Ghidra-Rare.
package ghidra.app.util.bin.format.elf.relocation;

/**
 * Motorola 68HC11 ELF relocation types (binutils include/elf/m68hc11.h).
 */
public enum MC68HC11_ElfRelocationType implements ElfRelocationType {

	R_M68HC11_NONE(0),
	R_M68HC11_8(1),
	R_M68HC11_HI8(2),
	R_M68HC11_LO8(3),
	R_M68HC11_PCREL_8(4),
	R_M68HC11_16(5),
	R_M68HC11_32(6),
	R_M68HC11_3B(7),
	R_M68HC11_PCREL_16(8),
	R_M68HC11_GNU_VTINHERIT(9),
	R_M68HC11_GNU_VTENTRY(10),
	R_M68HC11_24(11),
	R_M68HC11_LO16(12),
	R_M68HC11_PAGE(13),
	R_M68HC11_RL_JUMP(20),
	R_M68HC11_RL_GROUP(21);

	public final int typeId;

	private MC68HC11_ElfRelocationType(int typeId) {
		this.typeId = typeId;
	}

	@Override
	public int typeId() {
		return typeId;
	}
}
