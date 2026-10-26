// Runs p-code semantic tests for the 6800 family in Ghidra's emulator.
// The program is a zero-filled 64 KB image (any 6800-family language, imported raw at 0).
// Script args: <tests.txt> <outfile>
//   tests.txt lines (blank and #-lines ignored):
//     <name> <pc-hex> <stop> <code-hex> <init> <expect>
//   <stop>   "n<N>" = execute N instructions, or a stop address in hex
//   <init>   comma list or "-": REG=hex (A B CC X Y S), mADDR=hex-bytes (memory), seed=N (fill the
//            four check windows with the test pattern first)
//   script arg 3 "fresh": a new emulator for every test (needed when tests share addresses)
//   <expect> comma list: REG=hex or REG/mask=hex (compare under mask), mADDR=hex-bytes,
//            and "win": every window byte not named by an mADDR must still have the pattern
//   window pattern: byte(a) = ((a*131 + seed*29 + 7) ^ (a >> 3)) & 0xFF
// Output: PASS/FAIL line per test and a final summary line.
//@category Testing

import java.io.PrintStream;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

import ghidra.app.emulator.EmulatorHelper;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.lang.Register;

public class EmuCheck extends GhidraScript {
	static final int[] WIN = { 0x0040, 0x2000, 0x30E0, 0xFFE0 };
	static final int WINLEN = 32;
	// A fresh emulator every BATCH tests (arg 3 = "fresh": every test).  Each test of a batch runs at
	// its own address, because the emulator keeps decoded instructions per address.
	static int BATCH = 400;

	static int pat(int a, int seed) {
		return ((a * 131 + seed * 29 + 7) ^ (a >> 3)) & 0xFF;
	}

	@Override
	protected void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length > 2 && args[2].equals("fresh")) {
			BATCH = 1;
		}
		PrintStream out = new PrintStream(args[1]);
		int pass = 0, fail = 0, n = 0;
		EmulatorHelper emu = null;
		for (String line : Files.readAllLines(Path.of(args[0]))) {
			line = line.trim();
			if (line.isEmpty() || line.startsWith("#")) {
				continue;
			}
			if (emu == null || n % BATCH == 0) {
				if (emu != null) {
					emu.dispose();
				}
				emu = new EmulatorHelper(currentProgram);
			}
			n++;
			String[] f = line.split("\\s+");
			String err;
			try {
				err = runOne(emu, f);
			}
			catch (Exception e) {
				err = "exception " + e;
			}
			if (err == null) {
				pass++;
				out.println("PASS " + f[0]);
			}
			else {
				fail++;
				out.println("FAIL " + f[0] + ": " + err);
			}
		}
		if (emu != null) {
			emu.dispose();
		}
		out.printf("emulator tests: %d passed, %d failed%n", pass, fail);
		out.close();
	}

	private static byte[] hex(String s) {
		byte[] b = new byte[s.length() / 2];
		for (int i = 0; i < b.length; i++) {
			b[i] = (byte) Integer.parseInt(s.substring(2 * i, 2 * i + 2), 16);
		}
		return b;
	}

	private String runOne(EmulatorHelper emu, String[] f) throws Exception {
		long pc = Long.parseLong(f[1], 16);
		byte[] code = hex(f[3]);
		int seed = -1;
		Map<Integer, Integer> over = new HashMap<>();
		Map<Integer, Integer> initmem = new HashMap<>();
		// registers: clear all, then apply init
		for (String r : new String[] { "A", "B", "CC", "X", "S" }) {
			emu.writeRegister(r, 0);
		}
		boolean hasY = currentProgram.getRegister("Y") != null;
		if (hasY) {
			emu.writeRegister("Y", 0);
		}
		if (!f[4].equals("-")) {
			for (String kv : f[4].split(",")) {
				String[] p = kv.split("=");
				if (p[0].equals("seed")) {
					seed = Integer.parseInt(p[1]);
				}
			}
		}
		if (seed >= 0) {
			for (int w : WIN) {
				byte[] b = new byte[WINLEN];
				for (int i = 0; i < WINLEN; i++) {
					b[i] = (byte) pat(w + i, seed);
				}
				emu.writeMemory(toAddr(w), b);
			}
		}
		if (!f[4].equals("-")) {
			for (String kv : f[4].split(",")) {
				String[] p = kv.split("=");
				if (p[0].equals("seed")) {
					continue;
				}
				if (p[0].startsWith("m")) {
					int a = Integer.parseInt(p[0].substring(1), 16);
					byte[] b = hex(p[1]);
					emu.writeMemory(toAddr(a), b);
					for (int i = 0; i < b.length; i++) {
						initmem.put(a + i, b[i] & 0xFF);
					}
				}
				else {
					emu.writeRegister(p[0], new BigInteger(p[1], 16));
				}
			}
		}
		emu.writeMemory(toAddr(pc), code);
		emu.writeRegister(emu.getPCRegister(), pc);
		int steps = 0, maxSteps = 5000;
		Address stop = null;
		if (f[2].startsWith("n")) {
			maxSteps = Integer.parseInt(f[2].substring(1));
		}
		else {
			stop = toAddr(Long.parseLong(f[2], 16));
		}
		while (steps < maxSteps && (stop == null || !emu.getExecutionAddress().equals(stop))) {
			if (!emu.step(monitor)) {
				return "emulation stopped at " + emu.getExecutionAddress() + ": " +
					emu.getLastError();
			}
			steps++;
		}
		if (stop != null && !emu.getExecutionAddress().equals(stop)) {
			return "did not reach " + stop + " in " + maxSteps + " steps (at " +
				emu.getExecutionAddress() + ")";
		}
		StringBuilder bad = new StringBuilder();
		boolean win = false;
		for (String kv : f[5].split(",")) {
			if (kv.equals("-")) {
				continue;
			}
			if (kv.equals("win")) {
				win = true;
				continue;
			}
			String[] p = kv.split("=");
			if (p[0].startsWith("m")) {
				int a = Integer.parseInt(p[0].substring(1), 16);
				byte[] want = hex(p[1]);
				byte[] got = emu.readMemory(toAddr(a), want.length);
				for (int i = 0; i < want.length; i++) {
					over.put(a + i, want[i] & 0xFF);
					if (want[i] != got[i]) {
						bad.append(String.format(" m%04x=%02x (want %02x)", a + i, got[i] & 0xFF,
							want[i] & 0xFF));
					}
				}
				continue;
			}
			String reg = p[0];
			BigInteger mask = null;
			if (reg.contains("/")) {
				String[] q = reg.split("/");
				reg = q[0];
				mask = new BigInteger(q[1], 16);
			}
			BigInteger got;
			if (reg.equals("PC")) {
				got = BigInteger.valueOf(emu.getExecutionAddress().getOffset());
			}
			else {
				Register r = currentProgram.getRegister(reg);
				got = emu.readRegister(r);
			}
			BigInteger want = new BigInteger(p[1], 16);
			if (mask != null) {
				got = got.and(mask);
				want = want.and(mask);
			}
			if (!want.equals(got)) {
				bad.append(String.format(" %s=%x (want %x)", p[0], got, want));
			}
		}
		if (win && seed >= 0) {
			for (int w : WIN) {
				byte[] got = emu.readMemory(toAddr(w), WINLEN);
				for (int i = 0; i < WINLEN; i++) {
					int a = w + i;
					if (over.containsKey(a)) {
						continue;
					}
					int want = initmem.containsKey(a) ? initmem.get(a) : pat(a, seed);
					if ((got[i] & 0xFF) != want) {
						bad.append(String.format(" m%04x=%02x (untouched, want %02x)", a,
							got[i] & 0xFF, want));
					}
				}
			}
		}
		return bad.length() == 0 ? null : bad.toString().trim();
	}
}
