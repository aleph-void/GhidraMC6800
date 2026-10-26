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
 * Regression tests added by Ghidra-Rare for behaviour that was wrong before differential testing
 * against the manuals (see GHIDRA-RARE.md).
 */
public class EmulatorMC6800FixesTest extends AbstractEmulatorTest {
	public EmulatorMC6800FixesTest() {
		super("MC6800:BE:16:default");
	}

	@Test
	public void ROR_keepsSignBitClear() {
		assemble(0x0000, "RORA");
		setA(0x80);
		setCC(0x00);
		stepFrom(0x0000);
		// Carry in was 0: 0x80 >> 1 = 0x40 (it was 0xC0 when the shift was arithmetic).
		assertEquals(0x40, getA());
		assertEquals(0x00, getCC() & (CC.N | CC.Z | CC.V | CC.C));
	}

	@Test
	public void ROR_carryComesIn() {
		assemble(0x0000, "RORA");
		setA(0x01);
		setCC(CC.C);
		stepFrom(0x0000);
		assertEquals(0x80, getA());
		// C = old bit 0 = 1, N = 1, V = N xor C = 0.
		assertEquals(CC.N | CC.C, getCC() & (CC.N | CC.Z | CC.V | CC.C));
	}

	@Test
	public void shiftsSetV() {
		assemble(0x0000, "ASLA", "LSRA", "ASRA");
		setA(0xC0);
		setCC(0x00);
		stepFrom(0x0000);
		// ASL: 0xC0 -> 0x80, C = 1, N = 1, V = 0.
		assertEquals(0x80, getA());
		assertEquals(CC.N | CC.C, getCC() & (CC.N | CC.Z | CC.V | CC.C));
		step();
		// LSR: 0x80 -> 0x40, C = 0, N = 0, V = 0.
		assertEquals(0x40, getA());
		assertEquals(0x00, getCC() & (CC.N | CC.Z | CC.V | CC.C));
		setA(0x03);
		step();
		// ASR: 0x03 -> 0x01, C = 1, N = 0, V = N xor C = 1.
		assertEquals(0x01, getA());
		assertEquals(CC.C | CC.V, getCC() & (CC.N | CC.Z | CC.V | CC.C));
	}

	@Test
	public void TST_clearsCarry() {
		assemble(0x0000, "TSTA");
		setA(0x00);
		setCC(CC.C | CC.V | CC.N);
		stepFrom(0x0000);
		assertEquals(CC.Z, getCC() & (CC.N | CC.Z | CC.V | CC.C));
	}

	@Test
	public void ABA_setsHalfCarry() {
		assemble(0x0000, "ABA");
		setA(0x0F);
		setB(0x01);
		setCC(0x00);
		stepFrom(0x0000);
		assertEquals(0x10, getA());
		assertEquals(CC.H, getCC() & (CC.H | CC.N | CC.Z | CC.V | CC.C));
	}

	@Test
	public void DAA_table() {
		assemble(0x0000, "DAA");
		// {A, C before, H before, A after, C after}, from the correction table of the manual.
		int[][] cases = {
			{ 0x47, 0, 0, 0x47, 0 }, { 0x4A, 0, 0, 0x50, 0 }, { 0x43, 0, 1, 0x49, 0 },
			{ 0xA3, 0, 0, 0x03, 1 }, { 0x9A, 0, 0, 0x00, 1 }, { 0xB1, 0, 1, 0x17, 1 },
			{ 0x23, 1, 0, 0x83, 1 }, { 0x2A, 1, 0, 0x90, 1 }, { 0x13, 1, 1, 0x79, 1 },
		};
		for (int[] c : cases) {
			setA(c[0]);
			setCC((c[1] != 0 ? CC.C : 0) | (c[2] != 0 ? CC.H : 0));
			stepFrom(0x0000);
			assertEquals(c[3], getA(), String.format("A=%02x C=%d H=%d", c[0], c[1], c[2]));
			assertEquals(c[4] != 0 ? CC.C : 0, getCC() & CC.C,
				String.format("carry for A=%02x C=%d H=%d", c[0], c[1], c[2]));
		}
	}

	@Test
	public void TAP_TPA_bits76ReadAsOne() {
		assemble(0x0000, "TAP", "TPA");
		setA(0xFF);
		stepFrom(0x0000);
		// TAP keeps the six flags; TPA reads bits 7 and 6 as 1.
		assertEquals(0x3F, getCC() & 0xFF);
		setA(0x00);
		step();
		assertEquals(0xFF, getA());
	}

	@Test
	public void CPX_leavesCarryAlone() {
		// The 6800 manual: C is not affected by CPX (it is on the 6801 and later).
		assemble(0x0000, "CPX #0x0002");
		setX(0x0001);
		setCC(0x00);
		stepFrom(0x0000);
		assertEquals(CC.N, getCC() & (CC.N | CC.Z | CC.V | CC.C));
		setCC(CC.C);
		stepFrom(0x0000);
		assertEquals(CC.N | CC.C, getCC() & (CC.N | CC.Z | CC.V | CC.C));
	}

	@Test
	public void SWI_RTI() {
		// SWI jumps to the address stored at the vector (0xFFFA), not to the vector itself.
		assemble(0x0000, "SWI");
		assemble(0x0300, "RTI");
		write(0xFFFA, 0x03, 0x00);
		setS(0x07FF);
		setA(0x12);
		setB(0x34);
		setX(0xABCD);
		setCC(CC.C);
		stepFrom(0x0000);
		assertEquals(0x0300, getPC());
		assertEquals(0x07F8, getS());
		assertEquals(CC.I | CC.C, getCC() & 0x3F);
		// Pushed: PC (low, high), X (low, high), A, B, CC with bits 7 and 6 set.
		assertEquals(0x01, readByte(0x07FF));
		assertEquals(0x00, readByte(0x07FE));
		assertEquals((byte) 0xCD, readByte(0x07FD));
		assertEquals((byte) 0xAB, readByte(0x07FC));
		assertEquals(0x12, readByte(0x07FB));
		assertEquals(0x34, readByte(0x07FA));
		assertEquals((byte) 0xC1, readByte(0x07F9));
		step();
		assertEquals(0x0001, getPC());
		assertEquals(0x07FF, getS());
		assertEquals(CC.C, getCC() & 0x3F);
		assertEquals(0xABCD, getX());
	}
}
