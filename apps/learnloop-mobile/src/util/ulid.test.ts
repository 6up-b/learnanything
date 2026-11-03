import { expect, it } from "vitest";
import { newUlid } from "./ulid";

it("is the canonical ULID the capture endpoint asks for", () => {
  // The server's rule: src/learnloop/capture/inbox.py _ULID.
  expect(newUlid()).toMatch(/^[0-7][0-9A-HJKMNP-TV-Z]{25}$/);
  expect(newUlid()).not.toBe(newUlid());
});
