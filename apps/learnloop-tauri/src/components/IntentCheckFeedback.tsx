// Daily-loop DL2: after a check on your own (Reader §9.3 items 9 and 10).
// Feedback says it was the check, and, only when the check's provenance
// carries inquiry roots or anchor spans (RW6b's follow-ups), offers a link
// back to where it was studied. A link, never an automatic jump.
import type { IntentCheckDto, IntentRestorationDto } from "../api/dto";
import { quietLine, quietLink } from "./PlainParts";

export function IntentCheckFeedback({
  check,
  onOpenStudied
}: {
  check: IntentCheckDto | undefined | null;
  onOpenStudied?: (restoration: IntentRestorationDto) => void;
}) {
  if (!check) return null;
  const back = check.restoration;
  return (
    <div style={{ ...quietLine, marginBottom: 10 }} data-testid="intent-check-feedback">
      Your check on your own.
      {back && onOpenStudied ? (
        <>
          {" "}
          <button type="button" style={quietLink} onClick={() => onOpenStudied(back)}>
            {back.detail ? `${back.label}: ${back.detail}` : back.label}
          </button>
        </>
      ) : null}
    </div>
  );
}
