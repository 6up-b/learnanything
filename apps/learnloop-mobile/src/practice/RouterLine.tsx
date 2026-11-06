// Mobile v2 J4: the router's visible decisions on the phone. The plain line sits on the surface
// (FG1 §6.4, the stated exception to "the glass box on demand", governed by the server's
// `ui.show_router_decisions`: absent there, absent here); `details` and "how was this chosen?" open
// in a bottom sheet (§4.1), so the primary button never moves. Display only.
import { useState } from "react";
import type { RouterDecisionDto } from "@desktop/api/dto";
import { phone } from "../api/phone";
import { Sheet } from "../shell/Sheet";

export function RouterLine({ decision, explainId }: { decision: RouterDecisionDto | null | undefined; explainId?: string | null }) {
  const [open, setOpen] = useState(false);
  if (!decision) return null;
  return (
    <div className="dim" data-testid="router-line">
      <span>{decision.line}</span>{" "}
      <button type="button" className="link" onClick={() => setOpen(true)}>details</button>
      {open ? <RouterDetails decision={decision} explainId={explainId ?? null} onClose={() => setOpen(false)} /> : null}
    </div>
  );
}

/** The block's own reason, behind `why?` (ux §4.1: collapsed, on the object). */
export function WhyLink({ why, details, explainId }: { why: string | null; details: string | null; explainId: string | null }) {
  const [open, setOpen] = useState(false);
  if (!why && !details && !explainId) return null;
  return (
    <>
      <button type="button" className="link" aria-expanded={open} onClick={() => setOpen(true)}>why?</button>
      {open ? (
        <Sheet title="Why this" onClose={() => setOpen(false)}>
          {why ? <p>{why}</p> : null}
          {details ? <p className="dim">{details}</p> : null}
          {explainId ? <Explain decisionId={explainId} /> : null}
        </Sheet>
      ) : null}
    </>
  );
}

function RouterDetails({ decision, explainId, onClose }: { decision: RouterDecisionDto; explainId: string | null; onClose: () => void }) {
  const details = decision.details;
  return (
    <Sheet title="How this was chosen" onClose={onClose}>
      {details.held ? <p>The rest of this comes after the question.</p> : null}
      {details.cardSummary ? <p style={{ whiteSpace: "pre-wrap" }}>{details.cardSummary}</p> : null}
      {details.models.map((model) => (
        <p key={model.name} className="dim">
          {model.name}: {model.status ?? ""} {model.answer != null ? JSON.stringify(model.answer) : ""}
        </p>
      ))}
      {details.rationale ? <p>Why: {details.rationale}</p> : null}
      {details.fallback ? <p className="dim">Fell back: {details.fallback}</p> : null}
      <p className="dim">Decision {decision.decisionId}</p>
      {explainId ? <Explain decisionId={explainId} /> : null}
    </Sheet>
  );
}

/** "How was this chosen?": the objective's own account of one decision, read when asked. */
function Explain({ decisionId }: { decisionId: string }) {
  const [lines, setLines] = useState<string[] | null>(null);
  const [asked, setAsked] = useState(false);
  if (!asked) {
    return (
      <button
        type="button"
        className="link"
        onClick={() => {
          setAsked(true);
          void phone.routerObjectiveExplain(decisionId).then(
            (reply) => setLines(reply.lines?.length ? reply.lines : ["Nothing more is recorded for this one."]),
            () => setLines(["That couldn't be read just now."])
          );
        }}
      >
        how was this chosen?
      </button>
    );
  }
  if (lines === null) return <p className="dim" role="status">Reading…</p>;
  return (
    <div>
      {lines.map((line, index) => (
        <p key={index} className="dim">{line}</p>
      ))}
    </div>
  );
}
