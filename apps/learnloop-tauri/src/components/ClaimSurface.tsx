import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { ClaimCandidateDto, PresentedClaimDto } from "../api/dto";
import { COLOR, FONT_MONO } from "./term";

export function mintVisitId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `visit-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function ClaimSurface({
  claim,
  sessionId,
  visitId,
  onReceipt,
  onResponded,
  onError
}: {
  claim: ClaimCandidateDto;
  sessionId?: string | null;
  visitId?: string | null;
  onReceipt?: (ref: string) => void;
  onResponded?: (payload: Record<string, unknown>) => void;
  onError: (message: string) => void;
}) {
  const root = useRef<HTMLDivElement | null>(null);
  const exposureStarted = useRef(false);
  const [presentation, setPresentation] = useState<PresentedClaimDto | null>(null);
  const [responded, setResponded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [interpretation, setInterpretation] = useState("");

  useEffect(() => {
    const node = root.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting) || exposureStarted.current) return;
        exposureStarted.current = true;
        api.presentClaims([{ ...claim, visibleAt: new Date().toISOString() }], { sessionId, visitId })
          .then((result) => setPresentation(result.claims[0] ?? null))
          .catch((error) => onError((error as Error).message));
      },
      { threshold: 0.35 }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [claim, onError, sessionId, visitId]);

  async function respond(payload: Record<string, unknown>) {
    if (!presentation || responded) return;
    try {
      await api.respondClaim(presentation.presentationId, payload);
      setResponded(true);
      onResponded?.(payload);
    } catch (error) {
      onError((error as Error).message);
    }
  }

  async function dismiss() {
    if (!presentation || responded) return;
    try {
      await api.dismissClaim(presentation.presentationId);
      setResponded(true);
    } catch (error) {
      onError((error as Error).message);
    }
  }

  const enabled = Boolean(presentation?.affordancesEnabled && !responded);
  return (
    <div
      ref={root}
      style={{ border: `1px solid ${COLOR.border}`, borderLeft: `3px solid ${COLOR.amber}`, padding: "12px 14px", background: COLOR.bgElev }}
    >
      <div style={{ color: COLOR.text, lineHeight: 1.55 }}>{claim.claimText}</div>
      {claim.provenance ? <div style={{ marginTop: 5, color: COLOR.textFaint, fontSize: 11, fontFamily: FONT_MONO }}>{claim.provenance}</div> : null}
      {claim.receiptRef && onReceipt ? (
        <button type="button" className="queue-row" style={{ marginTop: 8 }} onClick={() => onReceipt(claim.receiptRef!)}>
          show receipt
        </button>
      ) : null}
      {presentation?.suppressionReason ? (
        <div style={{ marginTop: 8, color: COLOR.textFaint, fontSize: 11 }}>annotated claim · responses paused ({presentation.suppressionReason.replace(/_/g, " ")})</div>
      ) : null}
      {responded ? <div style={{ marginTop: 8, color: COLOR.textDim, fontSize: 11 }}>response saved locally</div> : null}
      {enabled ? (
        <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 6 }}>
          <ClaimResponses
            claim={claim}
            editing={editing}
            setEditing={setEditing}
            interpretation={interpretation}
            setInterpretation={setInterpretation}
            respond={respond}
          />
          <button type="button" className="queue-row" onClick={() => void dismiss()}>dismiss</button>
        </div>
      ) : null}
    </div>
  );
}

function ClaimResponses({ claim, editing, setEditing, interpretation, setInterpretation, respond }: {
  claim: ClaimCandidateDto;
  editing: boolean;
  setEditing: (value: boolean) => void;
  interpretation: string;
  setInterpretation: (value: string) => void;
  respond: (payload: Record<string, unknown>) => Promise<void>;
}) {
  const button = (label: string, response: string, extra: Record<string, unknown> = {}) => (
    <button key={response} type="button" className="queue-row" onClick={() => void respond({ response, ...extra })}>{label}</button>
  );
  if (claim.claimClass === "estimate" && claim.claimType === "ready_estimate") {
    return <>{button("seems high", "high")}{button("about right", "about_right")}{button("seems low", "low")}{button("not sure", "not_sure")}</>;
  }
  if (claim.claimClass === "estimate") {
    return <>{button("pace is typical", "pace_typical")}{button("pace is atypical", "pace_atypical")}</>;
  }
  if (claim.claimClass === "policy") {
    return <>{button("useful", "useful")}{button("too easy", "choose_something_else", { reason: "too_easy" })}{button("too hard", "choose_something_else", { reason: "too_hard" })}{button("irrelevant", "choose_something_else", { reason: "irrelevant" })}{button("recently done", "choose_something_else", { reason: "recently_done" })}{button("bad item", "choose_something_else", { reason: "bad_item" })}</>;
  }
  if (claim.claimClass === "diagnosis") {
    return <>
      {button("fits", "fits")}{button("doesn't fit", "doesnt_fit")}{button("partly", "partly")}
      <button type="button" className="queue-row" onClick={() => setEditing(!editing)}>edit interpretation</button>
      {editing ? <span style={{ display: "flex", gap: 6, flexBasis: "100%" }}><input value={interpretation} onChange={(event) => setInterpretation(event.target.value)} aria-label="edit the interpretation" /><button type="button" className="queue-row" disabled={!interpretation.trim()} onClick={() => void respond({ response: "edit", interpretation })}>save edit</button></span> : null}
    </>;
  }
  if (claim.claimType === "regrade") {
    return <>{button("request review", "request_review")}</>;
  }
  return null;
}
