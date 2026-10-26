/* driver for tiny-AES-c and tiny-regex-c (written for Ghidra-Rare, CC0) */
#include <stdint.h>
#include "aes.h"
#include "re.h"
struct AES_ctx ctx;
uint8_t buf[32];
static const uint8_t key[16] = { 0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6, 0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c };
static const uint8_t iv[16] = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 };
char line[40] = "abc 123 def";
int main(void)
{
	int len, pos;
	AES_init_ctx_iv(&ctx, key, iv);
	AES_ECB_encrypt(&ctx, buf);
	AES_CBC_encrypt_buffer(&ctx, buf, 32);
	AES_CBC_decrypt_buffer(&ctx, buf, 32);
	AES_CTR_xcrypt_buffer(&ctx, buf, 32);
	pos = re_match("[a-z]+ [0-9]+", line, &len);
	return pos + len + buf[0];
}
