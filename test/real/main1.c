/* driver: calls library routines with opaque, over-sized context buffers (written for Ghidra-Rare, CC0) */
typedef unsigned char BYTE;
void sha256_init(void *), sha256_update(void *, const BYTE *, unsigned), sha256_final(void *, BYTE *);
void md5_init(void *), md5_update(void *, const BYTE *, unsigned), md5_final(void *, BYTE *);
unsigned base64_encode(const BYTE *, BYTE *, unsigned, int);
void arcfour_key_setup(BYTE *, const BYTE *, int), arcfour_generate_stream(BYTE *, BYTE *, unsigned);
void rot13(char *);
BYTE out[64];
char text[80] = "hello world";
BYTE ctx[160];
int main(void)
{
	BYTE h[32], m[16], st[256];
	static const BYTE key[8] = { 1, 2, 3, 4, 5, 6, 7, 8 };
	sha256_init(ctx);
	sha256_update(ctx, (BYTE *)text, 11);
	sha256_final(ctx, h);
	md5_init(ctx);
	md5_update(ctx, (BYTE *)text, 11);
	md5_final(ctx, m);
	base64_encode(h, out, 32, 1);
	arcfour_key_setup(st, key, 8);
	arcfour_generate_stream(st, out, 16);
	rot13(text);
	return out[0] + m[0];
}
