// Copyright 2024 Sigurdur Asgeirsson <siggi@sort.is>
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package is.sort.mc6800;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

/**
 * Tests added by Ghidra-Rare: the instructions upstream listed as untested (BRSET/BRCLR,
 * BSET/BCLR, Y forms) and the fixes found by differential testing (see GHIDRA-RARE.md).
 */
public class EmulatorMC68HC11FixesTest extends AbstractEmulatorTest {
	public EmulatorMC68HC11FixesTest() {
		super("MC68HC11:BE:16:default");
	}

	@Test
	public void BSET_direct() {
		assemble(0x0000, "BSET 0x50 0xF0");
		write(0x0050, 0x0F);
		setCC(CC.V | CC.Z);
		stepFrom(0x0000);
		assertEquals((byte) 0xFF, readByte(0x0050));
		// N and Z from the result, V cleared.
		assertEquals(CC.N, getCC() & (CC.N | CC.Z | CC.V));
	}

	@Test
	public void BCLR_indexedX() {
		assemble(0x0000, "BCLR 0x04,X 0xFF");
		write(0x1004, 0xA5);
		setX(0x1000);
		setCC(CC.N);
		stepFrom(0x0000);
		assertEquals(0x00, readByte(0x1004));
		assertEquals(CC.Z, getCC() & (CC.N | CC.Z | CC.V));
	}

	@Test
	public void BSET_BCLR_indexedY() {
		assemble(0x0000, "BSET 0x02,Y 0x81", "BCLR 0x02,Y 0x01");
		write(0x2002, 0x00);
		setY(0x2000);
		stepFrom(0x0000, 2);
		assertEquals((byte) 0x80, readByte(0x2002));
		assertEquals(CC.N, getCC() & (CC.N | CC.Z | CC.V));
	}

	@Test
	public void BRSET_branchesWhenAllMaskedBitsAreSet() {
		assemble(0x0000, "BRSET 0x50 0x30 0x0010");
		write(0x0050, 0x3F);
		stepFrom(0x0000);
		assertEquals(0x0010, getPC());
		// One masked bit clear: falls through (the instruction is 4 bytes).
		write(0x0050, 0x2F);
		stepFrom(0x0000);
		assertEquals(0x0004, getPC());
	}

	@Test
	public void BRCLR_branchesWhenAllMaskedBitsAreClear() {
		assemble(0x0000, "BRCLR 0x50 0x30 0x0010");
		write(0x0050, 0xCF);
		stepFrom(0x0000);
		assertEquals(0x0010, getPC());
		write(0x0050, 0xDF);
		stepFrom(0x0000);
		assertEquals(0x0004, getPC());
	}

	@Test
	public void BRSET_BRCLR_indexed() {
		assemble(0x0000, "BRSET 0x01,X 0x81 0x0020");
		write(0x3001, 0x81);
		setX(0x3000);
		stepFrom(0x0000);
		assertEquals(0x0020, getPC());
		assemble(0x0100, "BRCLR 0x01,Y 0x81 0x0120");
		write(0x3001, 0x7E);
		setY(0x3000);
		stepFrom(0x0100);
		assertEquals(0x0120, getPC());
	}

	@Test
	public void TAP_XBitCanBeClearedNotSet() {
		assemble(0x0000, "TAP");
		setCC(0x00);
		setA(0x40);
		stepFrom(0x0000);
		assertEquals(0x00, getCC());
		setCC(0x40);
		setA(0x00);
		stepFrom(0x0000);
		assertEquals(0x00, getCC());
		// S can be set.
		setA(0x80);
		stepFrom(0x0000);
		assertEquals(0x80, getCC());
	}

	@Test
	public void SWI_RTI_pushesY() {
		assemble(0x0000, "SWI");
		assemble(0x0300, "RTI");
		write(0xFFF6, 0x03, 0x00);
		setS(0x07FF);
		setY(0xBEEF);
		setX(0xABCD);
		setA(0x12);
		setB(0x34);
		setCC(0x00);
		stepFrom(0x0000);
		assertEquals(0x0300, getPC());
		assertEquals(0x07F6, getS());
		// PC, Y, X, A, B, CC.
		assertEquals((byte) 0xEF, readByte(0x07FD));
		assertEquals((byte) 0xBE, readByte(0x07FC));
		assertEquals((byte) 0xCD, readByte(0x07FB));
		step();
		assertEquals(0x0001, getPC());
		assertEquals(0x07FF, getS());
		assertEquals(0xBEEF, getY());
		assertEquals(0xABCD, getX());
	}

	@Test
	public void XGDY() {
		assemble(0x0000, "XGDY");
		setD(0x1122);
		setY(0x3344);
		stepFrom(0x0000);
		assertEquals(0x3344, getD());
		assertEquals(0x1122, getY());
	}

	@Test
	public void ABY_PSHY_PULY() {
		assemble(0x0000, "ABY", "PSHY", "LDY #0x0000", "PULY");
		setY(0x00FF);
		setB(0xFF);
		setS(0x07FF);
		stepFrom(0x0000, 4);
		assertEquals(0x01FE, getY());
		assertEquals(0x07FF, getS());
	}

	@Test
	public void MUL_carryIsBit7OfB() {
		assemble(0x0000, "MUL");
		setA(0x80);
		setB(0x03);
		setCC(0x00);
		stepFrom(0x0000);
		assertEquals(0x0180, getD());
		assertEquals(CC.C, getCC() & CC.C);
	}
}
