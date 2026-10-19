// Reader workbench RW2b: "Check my work"'s verdict column and summary (UX
// §5.2, §5.4, W5; spec §5.2, G9, G38). Markers sit in a narrow column beside
// the steps, each labelled by method: "checked" only when the sandbox's
// symbolic check ran and its controls behaved, else "model's reading, not
// checked". Never the correction, never red, never a score. Editing a
// checked step dims its marker and says so.
import { COLOR, FONT_MONO } from "../../components/term";
import type { CheckStepVerdictDto, CheckViewDto } from "../../api/dto";
import { MeaningLabel } from "../reader/voices";
import { HELP_COPY, staleLine, verdictMark } from "./helpModel";
import { useSymbolicChecksLive } from "../../app/algoConfig";

export function VerdictCell({ verdict, symbolicEnabled }: { verdict: CheckStepVerdictDto | null;
  symbolicEnabled?: boolean }) {
  // Fix round 13: the app's CURRENT switch, AND the view's own.
  const live = useSymbolicChecksLive();
  if (!verdict) return <span style={{ width: 120, flexShrink: 0 }} />;
  const shown = verdictMark(verdict, symbolicEnabled === true && live);
  const words = verdict.first ? `${shown.mark} first` : `${shown.mark} ${shown.label}`;
  return (
    <span
      data-testid="workbench-verdict"
      data-verdict={verdict.verdict}
      data-method={verdict.method}
      title={shown.label === verdict.label && (verdict.method === "checked" || verdict.method === "checked_numerically")
        ? `${shown.label} (${HELP_COPY.methodLine})` : shown.label}
      style={{ width: 120, flexShrink: 0, paddingTop: 4, opacity: verdict.editedSinceCheck ? 0.5 : 1 }}
    >
      <MeaningLabel>{words}</MeaningLabel>
      {verdict.editedSinceCheck ? (
        <div><MeaningLabel>{HELP_COPY.editedSinceCheck}</MeaningLabel></div>
      ) : null}
    </span>
  );
}

/** The first questionable step's reason and the model's guess, under it. */
export function QuestionableNote({ check, chainId }: { check: CheckViewDto; chainId: string }) {
  const live = useSymbolicChecksLive();
  const verdict = check.verdicts.find((entry) => entry.chainId === chainId);
  if (!verdict || !verdict.first) return null;
  return (
    <div data-testid="workbench-first-questionable" style={{ display: "flex", flexDirection: "column", gap: 2, marginTop: 2 }}>
      <MeaningLabel style={{ fontSize: 11 }}>{`${verdictMark(verdict, check.symbolicEnabled === true && live).mark} ${verdict.reason || "this is where it stops holding"}`}</MeaningLabel>
      {check.errorKind ? <MeaningLabel style={{ fontSize: 11 }}>{check.errorKind.label}</MeaningLabel> : null}
    </div>
  );
}

/** The check's own lines: pending, stale, assumptions, the sandbox's absence. */
export function CheckSummary({ check, pending, notice }: { check: CheckViewDto | null; pending: boolean; notice: string | null }) {
  const stale = staleLine(check);
  if (!pending && !check && !notice) return null;
  return (
    <div data-testid="workbench-check-summary" role="status" aria-live="polite" style={{ display: "flex", flexDirection: "column", gap: 2, fontFamily: FONT_MONO }}>
      {pending ? <MeaningLabel style={{ fontSize: 11 }}><span aria-hidden="true">◐</span> {HELP_COPY.checking}…</MeaningLabel> : null}
      {stale ? <MeaningLabel style={{ fontSize: 11, color: COLOR.textDim }}>{stale}</MeaningLabel> : null}
      {check && check.assumptions.length ? (
        <MeaningLabel style={{ fontSize: 11 }}>{`${HELP_COPY.assumptions} ${check.assumptions.join("; ")}`}</MeaningLabel>
      ) : null}
      {check && !check.symbolicAvailable ? <MeaningLabel style={{ fontSize: 11 }}>{HELP_COPY.noSandbox}</MeaningLabel> : null}
      {notice ? <MeaningLabel style={{ fontSize: 11 }}>{notice}</MeaningLabel> : null}
    </div>
  );
}
