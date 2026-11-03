// The attempt type of a phone answer: the desktop's `chooseAttemptType` (PracticeScreen.tsx). The
// phone reveals no hint of its own, but a draft it adopted may carry some, and they still count.
import type { AttemptType } from "@desktop/api/dto";

const NON_RECORDING: ReadonlySet<string> = new Set(["guided_walkthrough", "skip"]);

export function phoneAttemptType(allowed: readonly AttemptType[], hints = 0): AttemptType {
  if (hints > 0 && (allowed.length === 0 || allowed.includes("hinted_attempt"))) return "hinted_attempt";
  if (allowed.length === 0 || allowed.includes("independent_attempt")) return "independent_attempt";
  return allowed.find((candidate) => !NON_RECORDING.has(candidate)) ?? "independent_attempt";
}
