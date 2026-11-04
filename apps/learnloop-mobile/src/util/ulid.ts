// The ids the phone mints: capture ids (the server wants a canonical ULID) and submission keys.
const ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";

export function newUlid(now: number = Date.now()): string {
  let time = "";
  let remaining = now;
  for (let index = 0; index < 10; index += 1) {
    time = ALPHABET[remaining % 32] + time;
    remaining = Math.floor(remaining / 32);
  }
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  let random = "";
  for (const byte of bytes) random += ALPHABET[byte % 32];
  return time + random;
}
