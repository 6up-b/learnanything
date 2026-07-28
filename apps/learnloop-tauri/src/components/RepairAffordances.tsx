import type { CausalFeedbackDto } from "../api/dto";
import { COLOR, FONT_MONO, Faint } from "./term";
import { Pill } from "./ui";

// Repair affordances shared by the FeedbackScreen and the §5.7 block-review
// surface (ProbeBlockResult). Extracted verbatim from FeedbackScreen so the
// diagnostic review renders the exact same visual language; the COLOR tokens
// resolve to the same palette FeedbackScreen's local constants carried.

export type CommonRepairDto = NonNullable<CausalFeedbackDto["commonRepair"]>;

/** Journey B: every plausible cause shares one fix — deliver the repair
 *  instead of holding or interrogating. Rendering reads the recommendation
 *  off the payload (recorded post-attempt / at block end); "start the fix"
 *  is the same handoff "Teach me now" uses. */
export function CommonRepairCard({
  commonRepair,
  onStartFix,
  onDismiss,
}: {
  commonRepair: CommonRepairDto;
  onStartFix: (misconceptionId: string) => void;
  onDismiss: () => void;
}) {
  return (
    <div
      style={{
        marginTop: 14,
        padding: "10px 12px",
        background: COLOR.bgElev,
        borderLeft: `3px solid ${COLOR.greenSoft}`,
        fontFamily: FONT_MONO,
        fontSize: 12,
        lineHeight: 1.6,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <Pill tone="green">same fix</Pill>
        <Faint>these explanations point to the same fix</Faint>
      </div>
      <div style={{ color: COLOR.text }}>{commonRepair.message}</div>
      <div style={{ marginTop: 8, display: "flex", gap: 16, alignItems: "center" }}>
        <span
          style={{ color: COLOR.amberLink, textDecoration: "underline", cursor: "pointer" }}
          onClick={() => onStartFix(commonRepair.misconceptionId)}
        >start the fix</span>
        <span
          style={{ color: COLOR.textDim, textDecoration: "underline", cursor: "pointer" }}
          onClick={onDismiss}
        >not now</span>
      </div>
    </div>
  );
}

/** "Redo the part you missed" (Fix 3): gate visibility on the server-computed
 *  `guidedRedoAvailable` before rendering — a visible affordance must never
 *  fail with `guided_redo_unavailable`. */
export function GuidedRedoAffordance({
  starting,
  onStart,
}: {
  starting: boolean;
  onStart: () => void;
}) {
  return (
    <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim, marginTop: 8 }}>
      {starting ? (
        <span style={{ color: COLOR.amber }}>preparing the redo…</span>
      ) : (
        <>
          <span
            style={{ color: COLOR.amberLink, textDecoration: "underline", cursor: "pointer" }}
            onClick={onStart}
          >redo the part you missed</span>
          {"   "}
          <Faint>your correct work stays — you rewrite only the failed step (scored as primed evidence)</Faint>
        </>
      )}
    </div>
  );
}
