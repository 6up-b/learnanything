// RW2b fix round 5, item 3 (docs/reviews/reader-rw2b-h3-codex-review.md): the
// "edited since check" comparison uses a fingerprint of the FULL step text,
// the same as the sidecar's snapshot (learnloop.hints.workbench.text_fingerprint).
import { expect, it } from "vitest";
import { CHECKED_TEXT_CHARS, textFingerprint, withLocalEdits } from "./helpModel";
import type { CheckViewDto } from "../../api/dto";

it("matches the sidecar's FNV-1a 64 reference values", () => {
  expect(textFingerprint("")).toBe("fnv1a64:cbf29ce484222325");
  expect(textFingerprint("a")).toBe("fnv1a64:af63dc4c8601ec8c");
  expect(textFingerprint("∫ x dx")).toMatch(/^fnv1a64:[0-9a-f]{16}$/);
});

const CHECKED = "1=1" + " ".repeat(1997) + "+0";
const EDITED = "1=1" + " ".repeat(1997) + "+1";

function checkOf(text: string, fingerprint: string | null): CheckViewDto {
  return {
    assistId: "ha_1", checkedAt: "2026-10-18T19:00:00Z", firstQuestionableStepId: null, errorKind: null,
    assumptions: [], symbolicAvailable: true, stale: false, changedSteps: [],
    verdicts: [{ chainId: "c1", number: 1, verdict: "valid", method: "checked", mark: "✓", label: "checked",
      reason: "", dependsOn: [], assumption: "", first: false, editedSinceCheck: false, deletedSinceCheck: false,
      checkedText: text.slice(0, CHECKED_TEXT_CHARS), checkedFingerprint: fingerprint }],
  } as CheckViewDto;
}

it("a long step edited past the bounded text shows its verdict as stale at once", () => {
  expect(CHECKED.slice(0, CHECKED_TEXT_CHARS)).toBe(EDITED.slice(0, CHECKED_TEXT_CHARS));
  const check = checkOf(CHECKED, textFingerprint(CHECKED));
  expect(withLocalEdits(check, [{ chainId: "c1", body: CHECKED }])).toBe(check);
  const edited = withLocalEdits(check, [{ chainId: "c1", body: EDITED }]);
  expect(edited?.stale).toBe(true);
  expect(edited?.verdicts[0].editedSinceCheck).toBe(true);
  expect(edited?.changedSteps).toEqual([1]);
});

it("a check without a fingerprint never vouches for text past its bound", () => {
  const check = checkOf(CHECKED, null);
  expect(withLocalEdits(check, [{ chainId: "c1", body: CHECKED }])?.verdicts[0].editedSinceCheck).toBe(true);
  const short = checkOf("x = 1", null);
  expect(withLocalEdits(short, [{ chainId: "c1", body: "x = 1" }])).toBe(short);
});
