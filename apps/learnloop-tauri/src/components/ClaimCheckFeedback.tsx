// LP-min (a), LPQ9 (spec_learned_parameters_v1 §3.0b item 7): the review that
// resolves a topic you marked as known says so, in one quiet line. Accuracy
// feedback on the claim, never a score, a calibration figure or a label about
// you; the sidecar sends it only on the resolving review.
import type { ClaimCheckDto } from "../api/dto";
import { quietLine } from "./PlainParts";

export function ClaimCheckFeedback({ check }: { check: ClaimCheckDto | undefined | null }) {
  if (!check) return null;
  return (
    <div style={{ ...quietLine, marginBottom: 10 }} data-testid="claim-check-feedback">
      {check.line}
    </div>
  );
}
