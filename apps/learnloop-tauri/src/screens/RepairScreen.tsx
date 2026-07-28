// F6 — Repair flow (§4.10). NOT a tab: a detail overlay launched with a
// misconceptionId from Review's working hypotheses (and, later, Feedback's
// "repair this" and Today cards). The learner sees ONE compact sequence; the
// four backend stages (diagnosis → prescription → treatment → follow-up) are the
// recorded structure, never shown as a pipeline:
//
//   a. Compare the two ideas — the §4.7 statement pair (misconception +
//      authored correction, one visual unit) and the mechanism.
//   b. Open the source — side-by-side spans for BOTH the target and the
//      confused-with facet (a misconception is a confusion between two things).
//      prescribeRemediation returns the passage text and records a
//      `remediation_delivery` exposure for it (migration 150) — that is the
//      claim this screen supports, since we render the returned text inline
//      with no further action. The stronger `remediation` exposure is written
//      only when the learner actually clicks "open in source" below.
//   c. Try a related item now — one tap into the primed attempt the treatment
//      RPC returns, handed off to the normal primed practice loop.
//   d. Confirmation that an unassisted cold retry is scheduled (tomorrow or
//      later) — required for remediation to ever convert to Demonstrated credit.
//
// Status chips come from misconception transition events, including "returned"
// (relapse) — rendered plainly, never hidden. All actions are keyboard-reachable
// and state is never encoded by color alone (§4.13).

import { useCallback, useEffect, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type { CausalRepairStatusDto, StartRemediationDto, SpanViewDto } from "../api/dto";
import {
  CausalRepairStatusPanel,
  useCausalRepairActions,
} from "../components/CausalAttribution";
import { OpenInSource } from "../components/OpenInSource";
import { COLOR, Divider, Faint, FONT_MONO, Pill } from "../components/term";

const shortFacet = (facetId: string): string => facetId.replace(/^facet_/, "");

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

const btn: CSSProperties = {
  fontFamily: FONT_MONO,
  fontSize: 13,
  color: COLOR.amber,
  background: COLOR.bgInput,
  border: `1px solid ${COLOR.amber}`,
  borderRadius: 2,
  padding: "5px 14px",
  cursor: "pointer"
};

const btnDim: CSSProperties = {
  ...btn,
  color: COLOR.textDim,
  border: `1px solid ${COLOR.border}`
};

const stageBox: CSSProperties = {
  border: `1px solid ${COLOR.border}`,
  borderRadius: 3,
  padding: "12px 14px",
  marginTop: 12,
  background: COLOR.bgElev
};

function PassageCard({
  passage,
  onOpen
}: {
  passage: { role: string; facetId: string; spanView: SpanViewDto };
  onOpen: (extractionId: string, spanId: string) => void;
}) {
  const sv = passage.spanView;
  const heading = sv.sectionPath.length > 0 ? sv.sectionPath.join(" › ") : sv.blockType;
  return (
    <div style={{ border: `1px solid ${COLOR.border}`, borderRadius: 2, padding: "8px 10px", background: COLOR.bgInput }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
        <Pill color={passage.role.includes("confused") ? "red" : "cyan"}>{passage.role.replace(/_/g, " ")}</Pill>
        <span style={{ color: COLOR.amberLink, fontSize: 12 }}>{shortFacet(passage.facetId)}</span>
      </div>
      <div style={{ fontSize: 11, color: COLOR.textFaint, marginTop: 4 }}>{heading}</div>
      <div
        style={{
          borderLeft: `3px solid ${COLOR.amber}`,
          background: COLOR.bg,
          padding: "8px 10px",
          marginTop: 6,
          fontSize: 12,
          lineHeight: 1.6,
          whiteSpace: "pre-wrap",
          maxHeight: 200,
          overflowY: "auto"
        }}
      >
        {sv.text}
      </div>
      <button
        type="button"
        style={{ ...btnDim, fontSize: 11, padding: "2px 10px", marginTop: 6 }}
        onClick={() => onOpen(sv.extractionId, sv.spanId)}
      >
        open in source ▸
      </button>
    </div>
  );
}

export function RepairScreen({
  misconceptionId,
  sessionId,
  onClose,
  onPractice,
  onProbe,
  onError
}: {
  misconceptionId: string;
  /** Active session, when known — scopes the causal probe preference. */
  sessionId?: string | null;
  onClose: () => void;
  // Hand off to the app's primed practice loop (App.openPrimedRetry). Also
  // closes this overlay.
  onPractice: (practiceItemId: string) => void;
  /** Open a causal disambiguation probe COLD. It must not route through
   *  `onPractice`: that path submits `primed: true`, which would contaminate a
   *  diagnostic measurement with the repair context it is meant to be free of. */
  onProbe?: (practiceItemId: string) => void;
  onError: (message: string) => void;
}) {
  const [remediation, setRemediation] = useState<StartRemediationDto | null>(null);
  // P2 §6: the causal state can hold this targeted repair. That is a state with
  // its own learner copy and actions, not an error — the previous build turned
  // it into an `invalid_request` toast in developer language and stopped there.
  const [repairStatus, setRepairStatus] = useState<CausalRepairStatusDto | null>(null);
  const [prescribed, setPrescribed] = useState(false);
  const [treated, setTreated] = useState(false);
  const [busy, setBusy] = useState(false);
  const [openSpan, setOpenSpan] = useState<{ extractionId: string; spanId: string } | null>(null);

  const report = useCallback(
    (e: unknown) => onError(e instanceof Error ? e.message : String(e)),
    [onError]
  );

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !openSpan) onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose, openSpan]);

  useEffect(() => {
    let alive = true;
    setRemediation(null);
    setRepairStatus(null);
    setPrescribed(false);
    setTreated(false);
    api
      .startRemediation(misconceptionId)
      .then((r) => {
        if (!alive) return;
        setRemediation(r);
        setRepairStatus(r.episode ? null : r.repairStatus ?? null);
      })
      .catch(report);
    return () => {
      alive = false;
    };
  }, [misconceptionId, report]);

  const {
    pendingActionId: repairPendingActionId,
    note: repairNote,
    runAction: runRepairAction,
  } = useCausalRepairActions({
    sessionId,
    onStatus: (next) => {
      setRepairStatus(next.episode ? null : next);
      // "Teach me now" lifts the hold and returns the episode it started — use
      // that one rather than re-asking, which would mint a second episode.
      if (next.episode) {
        setRemediation((current) =>
          current ? { ...current, episode: next.episode } : current
        );
      }
    },
    onProbeAccepted: (offer) => {
      // The probe is pinned into a factor-aware episode; serve the instrument
      // cold, never through the primed-retry path.
      if (offer.practiceItemId && onProbe) onProbe(offer.practiceItemId);
    },
    onError,
  });

  const episodeId = remediation?.episode?.id ?? null;

  const prescribe = async () => {
    if (!episodeId) return;
    setBusy(true);
    try {
      const r = await api.prescribeRemediation(episodeId);
      setRemediation(r);
      setPrescribed(true);
    } catch (e) {
      report(e);
    } finally {
      setBusy(false);
    }
  };

  const treat = async () => {
    if (!episodeId) return;
    setBusy(true);
    try {
      const r = await api.startRemediationTreatment(episodeId);
      setRemediation(r);
      setTreated(true);
    } catch (e) {
      report(e);
    } finally {
      setBusy(false);
    }
  };

  const kase = remediation?.case ?? null;
  const passages = remediation?.episode?.passagesShown ?? [];
  const primedItemId = remediation?.primedItemId ?? remediation?.episode?.primedItemId ?? null;
  const coldItemId = remediation?.coldItemId ?? remediation?.episode?.coldItemId ?? null;
  const coldUnmeasurableReason = remediation?.coldUnmeasurableReason ?? null;
  const returned = kase?.history.some((h) => h.label === "returned") ?? false;

  return (
    <div style={backdrop} onClick={onClose}>
      <div style={panel} onClick={(e) => e.stopPropagation()}>
        <div style={header}>
          <span style={{ color: COLOR.amber, fontWeight: 700 }}>❯</span>
          <span style={{ fontSize: 13, color: COLOR.text }}>repair</span>
          {kase ? <Pill color={returned ? "red" : "pink"}>{kase.status}</Pill> : null}
          <span style={{ marginLeft: "auto", cursor: "pointer", color: COLOR.textFaint, fontSize: 12 }} onClick={onClose}>
            esc ✕
          </span>
        </div>

        <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: "14px 18px" }}>
          {!remediation ? <Faint>starting repair…</Faint> : null}

          {/* P2 §6: the causal state holds the BRANCH-SPECIFIC repair inside a
              divergent factor (never "unrelated remediation" — that copy named
              the wrong thing). Show the hold and its three actions here, where
              the learner just asked for the repair. */}
          {repairStatus ? (
            <div style={{ marginBottom: 14 }}>
              <CausalRepairStatusPanel
                status={repairStatus}
                pendingActionId={repairPendingActionId}
                note={repairNote}
                onAction={runRepairAction}
              />
            </div>
          ) : null}

          {kase ? (
            <>
              {/* a. Compare the two ideas — §4.7 statement pair, one unit */}
              <div style={{ fontSize: 11, color: COLOR.amber, letterSpacing: "0.1em", textTransform: "uppercase" }}>
                compare the two ideas
              </div>
              <div
                style={{
                  borderLeft: `3px solid ${COLOR.amber}`,
                  background: COLOR.bgElev,
                  padding: "10px 14px",
                  marginTop: 6,
                  lineHeight: 1.6
                }}
              >
                {kase.targetFacet && kase.confusedWithFacet ? (
                  <div>
                    Some answers were consistent with confusing{" "}
                    <span style={{ color: COLOR.cyan }}>{shortFacet(kase.targetFacet)}</span> and{" "}
                    <span style={{ color: COLOR.red }}>{shortFacet(kase.confusedWithFacet)}</span>.
                  </div>
                ) : (
                  <div>{kase.statement}</div>
                )}
                {kase.correctionStatement ? (
                  <div style={{ marginTop: 6, color: COLOR.green }}>
                    <Faint>the distinction to use here:</Faint> {kase.correctionStatement}
                  </div>
                ) : null}
                {kase.mechanism ? (
                  <div style={{ marginTop: 6, color: COLOR.textDim, fontSize: 12 }}>
                    <Faint>mechanism:</Faint> {kase.mechanism}
                  </div>
                ) : null}
              </div>

              {/* transition history — relapse rendered plainly */}
              {kase.history.length > 0 ? (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
                  {kase.history.map((h) => (
                    <span
                      key={h.id}
                      style={{ display: "inline-flex", gap: 4, alignItems: "center", fontSize: 11, color: h.label === "returned" ? COLOR.red : COLOR.textDim }}
                    >
                      {h.label === "returned" ? <span aria-hidden>↩</span> : null}
                      {h.label} · {fmtDate(h.at)}
                    </span>
                  ))}
                </div>
              ) : null}
            </>
          ) : null}

          {/* Stages b–d belong to the episode, not to the case record: a repair
              on a provisional belief has a live episode and no `misconceptions`
              row, so gating them on `kase` would strand the flow. */}
          {episodeId ? (
            <>
              {/* b. Open the source — side-by-side spans for BOTH facets */}
              <div style={stageBox}>
                <div style={{ fontSize: 11, color: COLOR.amber, letterSpacing: "0.1em", textTransform: "uppercase" }}>
                  open the source
                </div>
                {!prescribed ? (
                  <>
                    <div style={{ color: COLOR.textDim, fontSize: 12, margin: "6px 0" }}>
                      Read the canonical passages for both ideas — reading is recorded as exposure, not proof.
                    </div>
                    <button type="button" style={btn} disabled={busy} onClick={() => void prescribe()}>
                      {busy ? "…" : "show me the sources"}
                    </button>
                  </>
                ) : passages.length === 0 ? (
                  <div style={{ color: COLOR.textDim, fontSize: 12, marginTop: 6 }}>No source passages resolved for this case.</div>
                ) : (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 8, marginTop: 8 }}>
                    {passages.map((p, i) => (
                      <PassageCard key={`${p.facetId}:${i}`} passage={p} onOpen={(extractionId, spanId) => setOpenSpan({ extractionId, spanId })} />
                    ))}
                  </div>
                )}
              </div>

              {/* c. Try a related item + d. cold-retry confirmation */}
              {prescribed ? (
                <div style={stageBox}>
                  <div style={{ fontSize: 11, color: COLOR.amber, letterSpacing: "0.1em", textTransform: "uppercase" }}>
                    try a related item
                  </div>
                  {!treated ? (
                    <>
                      <div style={{ color: COLOR.textDim, fontSize: 12, margin: "6px 0" }}>
                        A primed practice item on this idea — try it now while the distinction is fresh.
                      </div>
                      <button type="button" style={btn} disabled={busy} onClick={() => void treat()}>
                        {busy ? "…" : "prime a related item"}
                      </button>
                    </>
                  ) : (
                    <>
                      <Divider style={{ margin: "6px 0" }} />
                      {primedItemId ? (
                        <button
                          type="button"
                          style={btn}
                          onClick={() => onPractice(primedItemId)}
                        >
                          practice this ▸
                        </button>
                      ) : (
                        <div style={{ color: COLOR.textDim, fontSize: 12 }}>No primed item was available for this case.</div>
                      )}
                      {/* d. Cold-retry status — honest about unmeasurability.
                          Only a paired independent surface converts to
                          Demonstrated credit; promising "scheduled" while
                          cold_item_id is NULL claimed a measurement that can
                          never happen. */}
                      {coldItemId ? (
                        <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10 }}>
                          <Pill color="green">scheduled</Pill>
                          <span style={{ fontSize: 12, color: COLOR.textDim }}>
                            an unassisted cold retry is scheduled for a later session (tomorrow or later) — only that
                            converts to Demonstrated credit
                          </span>
                        </div>
                      ) : (
                        <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10 }}>
                          <Pill color="red">not measurable</Pill>
                          <span style={{ fontSize: 12, color: COLOR.textDim }}>
                            {coldUnmeasurableReason === "no_independent_surface"
                              ? "no independent question exists on this topic yet, so no unassisted cold retry can be scheduled — this repair cannot convert to Demonstrated credit until another surface is authored"
                              : "no unassisted cold retry could be scheduled for this repair, so it cannot convert to Demonstrated credit"}
                          </span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              ) : null}
            </>
          ) : null}
        </div>
      </div>

      {openSpan ? (
        <OpenInSource
          extractionId={openSpan.extractionId}
          spanId={openSpan.spanId}
          context="remediation"
          entityType="misconception"
          entityId={misconceptionId}
          onClose={() => setOpenSpan(null)}
        />
      ) : null}
    </div>
  );
}

const backdrop: CSSProperties = {
  position: "fixed",
  inset: 0,
  zIndex: 215,
  background: "rgba(8, 8, 13, 0.78)",
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "center",
  padding: "6vh 5vw",
  backdropFilter: "blur(2px)"
};

const panel: CSSProperties = {
  width: "min(760px, 100%)",
  maxHeight: "86vh",
  background: COLOR.bg,
  border: `1px solid ${COLOR.borderStrong}`,
  boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
  display: "flex",
  flexDirection: "column",
  fontFamily: FONT_MONO,
  color: COLOR.text
};

const header: CSSProperties = {
  padding: "12px 16px",
  borderBottom: `1px solid ${COLOR.border}`,
  display: "flex",
  alignItems: "center",
  gap: 12,
  flexShrink: 0
};
