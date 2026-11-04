// FG1 (docs/specs/spec_followup_generate_serve_v1.md §6): what the follow-up workflow says,
// on the feedback screen: the line while a question is prepared, why the answer is held,
// the way out of a wait, and the router's decision. Everything here is the server's read.
import { useState } from "react";
import type { FollowupDto, RouterDecisionDto } from "../../api/dto";
import { QuietAction, quietLine, quietLink } from "../../components/PlainParts";
import { COLOR } from "../../components/term";

export function RouterDecisionLine({ decision }: { decision: RouterDecisionDto }) {
  const [open, setOpen] = useState(false);
  return (
    <div data-testid="router-decision" style={{ ...quietLine, marginTop: 8 }}>
      <span>{decision.line}</span>{" "}
      <button type="button" style={quietLink} onClick={() => setOpen((value) => !value)}>details</button>
      {open ? (
        <div data-testid="router-decision-details" style={{ marginTop: 6, display: "grid", gap: 4 }}>
          {decision.details.cardSummary ? <div style={{ whiteSpace: "pre-wrap" }}>{decision.details.cardSummary}</div> : null}
          {decision.details.models.map((model) => (
            <div key={model.name}>{model.name}: {model.status ?? ""} {model.answer != null ? JSON.stringify(model.answer) : ""}</div>
          ))}
          {decision.details.rationale ? <div>Why: {decision.details.rationale}</div> : null}
          {decision.details.fallback ? <div>Fell back: {decision.details.fallback}</div> : null}
          <div>Decision {decision.decisionId}</div>
        </div>
      ) : null}
    </div>
  );
}

export function FollowupPanel({
  followup,
  nextWaiting,
  onContinueWithout,
  onShowAnyway,
}: {
  followup: FollowupDto;
  /** Next was pressed and is waiting for the question. */
  nextWaiting: boolean;
  onContinueWithout: () => void;
  onShowAnyway: () => void;
}) {
  return (
    <div data-testid="followup-panel" style={{ marginBottom: 14, maxWidth: 900 }}>
      {followup.line ? (
        <div data-testid="followup-line" style={{ fontSize: 14, color: COLOR.text }}>{followup.line}</div>
      ) : null}
      {followup.held ? (
        <div data-testid="followup-held" style={{ ...quietLine, marginTop: 4 }}>
          The answer and the possible causes come after the question, so your answer can tell them apart.{" "}
          <button type="button" style={quietLink} onClick={onShowAnyway}>Show anyway</button>
        </div>
      ) : null}
      {nextWaiting && followup.canContinueWithout ? (
        <div style={{ marginTop: 8 }}>
          <QuietAction onClick={onContinueWithout}>Continue without it</QuietAction>
        </div>
      ) : null}
      {followup.routerDecision ? <RouterDecisionLine decision={followup.routerDecision} /> : null}
    </div>
  );
}
