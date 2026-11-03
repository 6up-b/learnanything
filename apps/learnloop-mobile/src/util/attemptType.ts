// The attempt type of a phone answer. The phone offers no hint, so this is the desktop's
// `defaultAttemptType` (PracticeScreen.tsx) without its hint branch.
import type { AttemptType } from "@desktop/api/dto";

const NON_RECORDING: ReadonlySet<string> = new Set(["guided_walkthrough", "skip"]);

export function phoneAttemptType(allowed: readonly AttemptType[]): AttemptType {
  if (allowed.length === 0 || allowed.includes("independent_attempt")) return "independent_attempt";
  return allowed.find((candidate) => !NON_RECORDING.has(candidate)) ?? "independent_attempt";
}
