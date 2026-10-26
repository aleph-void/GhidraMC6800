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

/** Regression tests added by Ghidra-Rare (see GHIDRA-RARE.md). */
public class EmulatorMC6801FixesTest extends AbstractEmulatorTest {
	public EmulatorMC6801FixesTest() {
		super("MC6801:BE:16:default");
	}

	@Test
	public void BRN_isTwoBytes() {
		assemble(0x0000, "BRN 0x0010");
		byte[] code = read(0x0000, 2);
		assertEquals(0x21, code[0]);
		stepFrom(0x0000);
		assertEquals(0x0002, getPC());
	}

	@Test
	public void LSRD_shiftsRight() {
		assemble(0x0000, "LSRD");
		setD(0x1235);
		setCC(0x00);
		stepFrom(0x0000);
		assertEquals(0x091A, getD());
		// C = old bit 0, N = 0, V = C.
		assertEquals(CC.C | CC.V, getCC() & (CC.N | CC.Z | CC.V | CC.C));
	}

	@Test
	public void ASLD_setsV() {
		assemble(0x0000, "ASLD");
		setD(0x4000);
		setCC(0x00);
		stepFrom(0x0000);
		assertEquals(0x8000, getD());
		// N = 1, C = 0, V = N xor C = 1.
		assertEquals(CC.N | CC.V, getCC() & (CC.N | CC.Z | CC.V | CC.C));
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
		setA(0xFF);
		setB(0xFF);
		stepFrom(0x0000);
		assertEquals(0xFE01, getD());
		assertEquals(0, getCC() & CC.C);
	}

	@Test
	public void SWI_usesVector() {
		assemble(0x0000, "SWI");
		write(0xFFFA, 0x04, 0x00);
		setS(0x07FF);
		stepFrom(0x0000);
		assertEquals(0x0400, getPC());
	}
}
