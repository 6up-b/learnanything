// F2 — learner-model review, presented as the GUI mirror of `learnloop diff`.
// The current state (working hypotheses) is primary; the append-only changelog
// remains visible as the quieter ledger beside it. Non-monotone events always
// use a glyph + label + color, never color alone (§4.13).

import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type {
  ClaimCandidateDto,
  KnowledgeHistoryAttempt,
  ReviewChangelogEntryDto,
  ReviewLogDto,
  WorkingHypothesisDto
} from "../api/dto";
import { ClaimSurface, mintVisitId } from "../components/ClaimSurface";
import { CommandOverlayFrame } from "../components/CommandOverlayFrame";
import { FacetEvidenceDrawer } from "../components/KnowledgeModel";
import { COLOR, Dim, Faint, FONT_MONO, Pill } from "../components/term";

const shortFacet = (facetId: string): string => facetId.replace(/^facet_/, "");

// Visual trial: flip this off to restore the original amber-only attempt links.
const ATTEMPT_OUTCOME_HUES_ENABLED = true;
const ATTEMPT_OUTCOME_HUE_MIX = 0.6;

// COLOR tokens are var() references now, so hue blending happens in CSS via
// color-mix instead of hex arithmetic.
function attemptOutcomeTone(attempt: KnowledgeHistoryAttempt): string {
  if (!ATTEMPT_OUTCOME_HUES_ENABLED) return COLOR.amberLink;
  const mix = (to: string) =>
    `color-mix(in srgb, ${to} ${ATTEMPT_OUTCOME_HUE_MIX * 100}%, ${COLOR.amberLink})`;
  if (attempt.correctness != null && attempt.correctness >= 1) {
    return mix(COLOR.green);
  }
  if (attempt.correctness != null && attempt.correctness <= 0) {
    return mix(COLOR.red);
  }
  // Older history rows may omit normalized correctness while retaining a zero score.
  if (attempt.correctness == null && attempt.rubricScore === 0) {
    return mix(COLOR.red);
  }
  return COLOR.amberLink;
}

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function EventBadge({ glyph, label, color }: { glyph: string; label: string; color: string }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, color, fontSize: 11 }}>
      <span aria-hidden>{glyph}</span>
      {label}
    </span>
  );
}

function FacetRef({
  facetId,
  onOpen,
  tone = COLOR.amberLink,
  underlined = false
}: {
  facetId: string;
  onOpen: (facetId: string) => void;
  tone?: string;
  underlined?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={() => onOpen(facetId)}
      title="Open facet evidence"
      style={{ ...facetLinkStyle, color: tone }}
    >
      <span aria-hidden style={{ marginRight: 4 }}>↗</span>
      <span
        style={{
          textDecorationLine: underlined ? "underline" : "none",
          textDecorationThickness: "1px",
          textUnderlineOffset: 3
        }}
      >
        {shortFacet(facetId)}
      </span>
    </button>
  );
}

function changelogFacetToneLabel(entry: ReviewChangelogEntryDto): string {
  return entry.kind === "regrade"
    ? "item facets · direction not apportioned"
    : "touched facets · movement is aggregate";
}

function attemptsBySession(
  changelog: ReviewChangelogEntryDto[],
  attempts: KnowledgeHistoryAttempt[]
): Record<string, KnowledgeHistoryAttempt[]> {
  const sessions = changelog
    .filter((entry) => entry.kind === "session")
    .slice()
    .sort((left, right) => new Date(left.at).getTime() - new Date(right.at).getTime());
  const orderedAttempts = attempts
    .slice()
    .sort((left, right) => new Date(left.t).getTime() - new Date(right.t).getTime());
  const grouped: Record<string, KnowledgeHistoryAttempt[]> = {};
  let previousEnd = Number.NEGATIVE_INFINITY;

  for (const session of sessions) {
    const end = new Date(session.at).getTime();
    const candidates = orderedAttempts.filter((attempt) => {
      const at = new Date(attempt.t).getTime();
      return Number.isFinite(at) && at > previousEnd && at <= end;
    });
    grouped[session.id] = session.attemptsRecorded > 0
      ? candidates.slice(-session.attemptsRecorded)
      : [];
    previousEnd = end;
  }
  return grouped;
}

function ChangelogEntry({
  entry,
  attempts,
  onOpenFacet,
  onInspectAttempt
}: {
  entry: ReviewChangelogEntryDto;
  attempts: KnowledgeHistoryAttempt[] | null;
  onOpenFacet: (facetId: string) => void;
  onInspectAttempt: (attemptId: string) => void;
}) {
  const isRecalibration = entry.kind === "recalibration";
  const isRegrade = entry.kind === "regrade";
  const moved = entry.predictionsMoved;
  const touched = entry.misconceptionsTouched;
  const badges: Array<{ glyph: string; label: string; color: string }> = [];

  if (entry.facetsDemonstrated > 0) {
    badges.push({ glyph: "+", label: `${entry.facetsDemonstrated} demonstrated`, color: COLOR.green });
  }
  if (moved.up > 0) badges.push({
    glyph: "▲",
    label: `${moved.up} prediction${moved.up === 1 ? "" : "s"} up`,
    color: COLOR.green
  });
  if (moved.down > 0) badges.push({
    glyph: "▼",
    label: `${moved.down} prediction${moved.down === 1 ? "" : "s"} down`,
    color: COLOR.red
  });
  if (entry.corrections > 0) {
    badges.push({ glyph: "⟲", label: `${entry.corrections} corrected`, color: COLOR.amber });
  }
  if (touched.resolved > 0) {
    badges.push({ glyph: "✓", label: `${touched.resolved} resolved`, color: COLOR.green });
  }
  if (touched.returned > 0) {
    badges.push({ glyph: "↩", label: `${touched.returned} returned`, color: COLOR.red });
  }

  if (isRegrade) {
    const direction = entry.direction ?? "same";
    badges.push({
      glyph: direction === "down" ? "▼" : direction === "up" ? "▲" : "＝",
      label:
        entry.oldScore !== undefined && entry.newScore !== undefined
          ? `credit ${entry.oldScore} → ${entry.newScore}`
          : `credit ${direction}`,
      color: direction === "down" ? COLOR.red : direction === "up" ? COLOR.green : COLOR.textDim
    });
  }

  const markerColor = isRecalibration ? COLOR.textFaint : isRegrade ? COLOR.amber : COLOR.cyan;
  const facetTone = COLOR.textDim;

  return (
    <article style={timelineEntryStyle}>
      <span aria-hidden style={{ ...timelineMarkerStyle, borderColor: markerColor }} />
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <Pill color={isRecalibration ? "slate" : isRegrade ? "amber" : "cyan"}>{entry.kind}</Pill>
        <time dateTime={entry.at} style={{ color: COLOR.textFaint, fontSize: 11 }}>{fmtDate(entry.at)}</time>
      </div>

      {isRecalibration ? (
        <div style={{ marginTop: 7, color: COLOR.textDim, fontSize: 12, lineHeight: 1.55 }}>
          Estimates recomputed; your underlying evidence did not change.
          {entry.previousAlgorithmVersion && entry.algorithmVersion ? (
            <div style={{ marginTop: 3, color: COLOR.textFaint, fontSize: 10 }}>
              {entry.previousAlgorithmVersion} → {entry.algorithmVersion}
            </div>
          ) : null}
        </div>
      ) : (
        <>
          {!isRegrade ? (
            <>
              <div style={{ marginTop: 7, color: COLOR.textDim, fontSize: 11 }}>
                {entry.attemptsRecorded} attempt{entry.attemptsRecorded === 1 ? "" : "s"}
                <Faint> · </Faint>
                {entry.itemsReviewed} item{entry.itemsReviewed === 1 ? "" : "s"} reviewed
              </div>
              {entry.attemptsRecorded > 0 ? (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 8px", marginTop: 7, alignItems: "center" }}>
                  <Faint style={{ fontSize: 10 }}>attempts</Faint>
                  {attempts == null ? (
                    <Faint style={{ fontSize: 10 }}>resolving…</Faint>
                  ) : attempts.length > 0 ? attempts.map((attempt) => (
                    <button
                      key={attempt.id}
                      type="button"
                      onClick={() => onInspectAttempt(attempt.id)}
                      title={`learnloop show ${attempt.id}`}
                      style={{ ...attemptLinkStyle, color: attemptOutcomeTone(attempt) }}
                    >
                      ↗ {attempt.id}
                    </button>
                  )) : (
                    <Faint style={{ fontSize: 10 }}>references unavailable</Faint>
                  )}
                </div>
              ) : null}
            </>
          ) : null}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "5px 12px", marginTop: 7 }}>
            {badges.length > 0 ? badges.map((badge) => (
              <EventBadge key={`${badge.glyph}:${badge.label}`} {...badge} />
            )) : <Faint style={{ fontSize: 11 }}>＝ no belief change</Faint>}
          </div>
        </>
      )}

      {entry.facetIds.length > 0 ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 8px", marginTop: 8, alignItems: "center" }}>
          <span style={{ color: facetTone, fontSize: 9, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            {changelogFacetToneLabel(entry)}
          </span>
          {entry.facetIds.slice(0, 8).map((facetId) => (
            <FacetRef key={facetId} facetId={facetId} onOpen={onOpenFacet} tone={facetTone} underlined />
          ))}
          {entry.facetIds.length > 8 ? <Faint style={{ fontSize: 10 }}>+{entry.facetIds.length - 8} more</Faint> : null}
        </div>
      ) : null}
    </article>
  );
}

function statementPairText(hypothesis: WorkingHypothesisDto): string {
  const correction = hypothesis.correctionStatement.trim();
  if (hypothesis.targetFacet && hypothesis.confusedWithFacet) {
    return `Some answers here were consistent with confusing ${shortFacet(hypothesis.targetFacet)} and ${shortFacet(
      hypothesis.confusedWithFacet
    )}. The distinction to use here: ${correction}`;
  }
  return `${hypothesis.statement.trim()} — the distinction to use here: ${correction}`;
}

function WorkingHypothesis({
  hypothesis,
  visitId,
  onOpenFacet,
  onRepair,
  onError
}: {
  hypothesis: WorkingHypothesisDto;
  visitId: string;
  onOpenFacet: (facetId: string) => void;
  onRepair: (misconceptionId: string) => void;
  onError: (message: string) => void;
}) {
  const claim: ClaimCandidateDto = useMemo(() => ({
    claimClass: "diagnosis",
    claimType: "misconception",
    claimRef: hypothesis.id,
    claimVersion: "review-working-1",
    producerVersion: "learner_review_feed",
    surface: "review_working_hypotheses",
    temperature: "cold",
    coldReask: true,
    claimText: statementPairText(hypothesis)
  }), [hypothesis]);
  const lastTransition = hypothesis.history[hypothesis.history.length - 1] ?? null;
  const returned = hypothesis.history.some((item) => item.label === "returned" || item.toStatus === "returned");

  return (
    <article style={{ ...hypothesisStyle, borderLeftColor: returned ? COLOR.red : COLOR.pink }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <Pill color={returned ? "red" : "pink"}>{hypothesis.status}</Pill>
        {returned ? <EventBadge glyph="↩" label="returned" color={COLOR.red} /> : null}
        <Faint style={{ fontSize: 10 }}>priority {hypothesis.severity.toFixed(2)}</Faint>
        <span style={{ flex: 1 }} />
        <Faint style={{ fontSize: 10 }}>{hypothesis.learningObjectId}</Faint>
      </div>

      {lastTransition ? (
        <div style={{ margin: "7px 0 5px", color: COLOR.textFaint, fontSize: 10 }}>
          {lastTransition.label.replace(/_/g, " ")} · {fmtDate(lastTransition.at)}
        </div>
      ) : <div style={{ height: 8 }} />}

      <ClaimSurface claim={claim} visitId={visitId} onError={onError} />

      {hypothesis.mechanism ? (
        <div style={{ marginTop: 9, color: COLOR.textDim, fontSize: 11, lineHeight: 1.55 }}>
          <span style={eyebrowInlineStyle}>mechanism</span> {hypothesis.mechanism}
        </div>
      ) : null}

      <div style={{ display: "flex", alignItems: "center", gap: 9, marginTop: 10, flexWrap: "wrap" }}>
        <button type="button" onClick={() => onRepair(hypothesis.id)} style={repairButtonStyle}>
          repair this →
        </button>
        {hypothesis.targetFacet ? <FacetRef facetId={hypothesis.targetFacet} onOpen={onOpenFacet} tone={returned ? COLOR.red : COLOR.pink} /> : null}
        {hypothesis.confusedWithFacet ? <FacetRef facetId={hypothesis.confusedWithFacet} onOpen={onOpenFacet} tone={returned ? COLOR.red : COLOR.pink} /> : null}
      </div>
    </article>
  );
}

function InlineStat({ value, label, tone = COLOR.text }: { value: string | number; label: string; tone?: string }) {
  return (
    <span style={{ whiteSpace: "nowrap" }}>
      <span style={{ color: tone, fontWeight: 600 }}>{value}</span>{" "}
      <span style={{ color: COLOR.textDim }}>{label}</span>
    </span>
  );
}

function SectionIntro({ eyebrow, title, description, count }: { eyebrow: string; title: string; description: string; count: number }) {
  return (
    <div style={{ marginBottom: 12, padding: "18px 18px 0" }}>
      <div style={eyebrowStyle}>{eyebrow}</div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
        <h2 style={sectionTitleStyle}>{title}</h2>
        <Faint style={{ fontSize: 11 }}>{count}</Faint>
      </div>
      <div style={{ color: COLOR.textDim, fontSize: 11, lineHeight: 1.5 }}>{description}</div>
    </div>
  );
}

export function ReviewScreen({
  onClose,
  onError,
  onRepair,
  onInspect,
  inspectorOpen = false
}: {
  onClose: () => void;
  onError: (message: string) => void;
  onRepair: (misconceptionId: string) => void;
  onInspect: (entityId: string) => void;
  inspectorOpen?: boolean;
}) {
  const [log, setLog] = useState<ReviewLogDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [drawerFacetId, setDrawerFacetId] = useState<string | null>(null);
  const [historyExpanded, setHistoryExpanded] = useState(false);
  const [sessionAttempts, setSessionAttempts] = useState<Record<string, KnowledgeHistoryAttempt[]> | null>(null);
  const visitId = useRef<string>(mintVisitId());

  useEffect(() => {
    let alive = true;
    api.getReviewLog()
      .then((result) => {
        if (alive) setLog(result);
      })
      .catch((error: unknown) => {
        if (!alive) return;
        const message = error instanceof Error ? error.message : String(error);
        setLoadError(message);
        onError(message);
      });
    return () => {
      alive = false;
    };
  }, [onError]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      if (inspectorOpen) {
        return;
      }
      if (drawerFacetId) {
        setDrawerFacetId(null);
      } else {
        onClose();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [drawerFacetId, inspectorOpen, onClose]);

  useEffect(() => {
    if (!historyExpanded || !log || sessionAttempts) return;
    let alive = true;
    api.getKnowledgeMapHistory()
      .then((history) => {
        if (alive) setSessionAttempts(attemptsBySession(log.changelog, history.attempts));
      })
      .catch((error: unknown) => {
        if (!alive) return;
        onError(error instanceof Error ? error.message : String(error));
        setSessionAttempts({});
      });
    return () => {
      alive = false;
    };
  }, [historyExpanded, log, onError, sessionAttempts]);

  const hypotheses = (log?.workingHypotheses ?? []).filter(
    (hypothesis) => hypothesis.correctionStatement && hypothesis.correctionStatement.trim()
  );
  const changelog = log?.changelog ?? [];
  const movementUp = changelog.reduce((sum, entry) => sum + entry.predictionsMoved.up, 0);
  const movementDown = changelog.reduce((sum, entry) => sum + entry.predictionsMoved.down, 0);

  return (
    <>
      <CommandOverlayFrame
        command="diff"
        context="learner model"
        badge={log ? <Pill color={hypotheses.length > 0 ? "pink" : "green"}>{hypotheses.length} active</Pill> : <Pill color="slate">loading</Pill>}
        footerKeys={(
          <>
            <span><span style={{ color: COLOR.text }}>esc</span> close</span>
            <span><span style={{ color: COLOR.text }}>scroll</span> history</span>
          </>
        )}
        footerRight={<span>command palette · <Dim>learnloop diff</Dim></span>}
        onClose={onClose}
        ariaLabel="Knowledge change review"
      >
        <div
          className="ll-scroll"
          style={bodyStyle}
          onWheel={(event) => {
            if (event.deltaY > 0 && changelog.length > 0) setHistoryExpanded(true);
          }}
          onTouchMove={() => {
            if (changelog.length > 0) setHistoryExpanded(true);
          }}
          onScroll={(event) => {
            if (event.currentTarget.scrollTop > 4 && changelog.length > 0) setHistoryExpanded(true);
          }}
        >
          {!log ? (
            <div style={{ padding: "34px 28px", minHeight: 260 }}>
              <div style={eyebrowStyle}>knowledge ledger</div>
              <div style={{ marginTop: 8, color: loadError ? COLOR.red : COLOR.text, fontSize: 16 }}>
                {loadError ? "Could not load the learner-model diff." : "Reading learner-model changes…"}
              </div>
              {loadError ? <div style={{ marginTop: 8, color: COLOR.textDim, fontSize: 11 }}>{loadError}</div> : null}
            </div>
          ) : (
            <>
              <div style={heroStyle}>
                <div>
                  <div style={summaryLineStyle}>
                    <span style={summaryContextStyle}>knowledge ledger · current snapshot</span>
                    <span style={summarySeparatorStyle}>·</span>
                    <InlineStat value={changelog.length} label={changelog.length === 1 ? "entry" : "entries"} />
                    <span style={summarySeparatorStyle}>·</span>
                    <InlineStat
                      value={hypotheses.length}
                      label="active hypotheses"
                      tone={hypotheses.length ? COLOR.pink : COLOR.green}
                    />
                    <span style={summarySeparatorStyle}>·</span>
                    <InlineStat value={`▲ ${movementUp}`} label="predictions up" tone={COLOR.green} />
                    <span style={summarySeparatorStyle}>·</span>
                    <InlineStat value={`▼ ${movementDown}`} label="predictions down" tone={movementDown ? COLOR.red : COLOR.textFaint} />
                  </div>
                  <h1 style={heroTitleStyle}>What changed. What still needs repair.</h1>
                  <div style={heroCopyStyle}>
                    A literal account of model movement—improvements, downgrades, corrections, and the hypotheses still in play.
                  </div>
                </div>
              </div>

              <div style={contentGridStyle}>
                <section>
                  <SectionIntro
                    eyebrow="now"
                    title="Working hypotheses"
                    description="Current diagnostic claims, always paired with their authored correction. Repair is the next action."
                    count={hypotheses.length}
                  />
                  {hypotheses.length > 0 ? hypotheses.map((hypothesis) => (
                    <WorkingHypothesis
                      key={hypothesis.id}
                      hypothesis={hypothesis}
                      visitId={visitId.current}
                      onOpenFacet={setDrawerFacetId}
                      onRepair={onRepair}
                      onError={onError}
                    />
                  )) : (
                    <div style={emptyStateStyle}>
                      <span style={{ color: COLOR.green }}>✓ clear</span>
                      <div style={{ marginTop: 6 }}>
                        {changelog.length === 0
                          ? "Nothing yet. Standing misconceptions will appear here after your first session."
                          : "No active misconceptions are currently attached to the learner model."}
                      </div>
                    </div>
                  )}
                </section>

                <section style={ledgerSectionStyle}>
                  <SectionIntro
                    eyebrow="ledger"
                    title="Change history"
                    description="Reverse chronological and unsmoothed. System-authored recalculations remain visibly distinct."
                    count={changelog.length}
                  />
                  {changelog.length > 0 && historyExpanded ? (
                    <div style={timelineStyle}>
                      {changelog.map((entry) => (
                        <ChangelogEntry
                          key={entry.id}
                          entry={entry}
                          attempts={entry.kind === "session" ? sessionAttempts?.[entry.id] ?? null : []}
                          onOpenFacet={setDrawerFacetId}
                          onInspectAttempt={onInspect}
                        />
                      ))}
                    </div>
                  ) : changelog.length > 0 ? (
                    <button
                      type="button"
                      aria-expanded="false"
                      onClick={() => setHistoryExpanded(true)}
                      style={historyRevealStyle}
                    >
                      <span style={{ color: COLOR.amber }}>show change history →</span>
                      <span style={{ color: COLOR.textFaint, fontSize: 10 }}>
                        {changelog.length} {changelog.length === 1 ? "entry" : "entries"} · also opens when you scroll
                      </span>
                    </button>
                  ) : (
                    <div style={emptyStateStyle}>
                      The ledger begins after your first completed session.
                    </div>
                  )}
                </section>
              </div>
            </>
          )}
        </div>
      </CommandOverlayFrame>

      {drawerFacetId ? (
        <FacetEvidenceDrawer
          facetId={drawerFacetId}
          onClose={() => setDrawerFacetId(null)}
          onInspect={(entityId) => {
            setDrawerFacetId(null);
            onInspect(entityId);
          }}
        />
      ) : null}
    </>
  );
}

const bodyStyle: CSSProperties = {
  flex: 1,
  minHeight: 0,
  overflowY: "auto"
};

const heroStyle: CSSProperties = {
  padding: "14px 18px",
  borderBottom: `1px solid ${COLOR.border}`,
  background: `linear-gradient(110deg, ${COLOR.bgElev} 0%, ${COLOR.bg} 68%)`
};

const summaryLineStyle: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  alignItems: "baseline",
  rowGap: 4,
  color: COLOR.textFaint,
  fontSize: 11
};

const summaryContextStyle: CSSProperties = {
  color: COLOR.textFaint,
  fontSize: 10,
  letterSpacing: "0.16em",
  textTransform: "uppercase"
};

const summarySeparatorStyle: CSSProperties = {
  color: COLOR.textFaint,
  margin: "0 8px"
};

const heroTitleStyle: CSSProperties = {
  margin: "7px 0 0",
  color: COLOR.text,
  fontSize: 19,
  lineHeight: 1.3,
  fontWeight: 600,
  letterSpacing: "-0.02em"
};

const heroCopyStyle: CSSProperties = {
  marginTop: 7,
  maxWidth: 800,
  color: COLOR.textDim,
  fontSize: 11,
  lineHeight: 1.55
};

const contentGridStyle: CSSProperties = {
  display: "block"
};

const ledgerSectionStyle: CSSProperties = {
  minWidth: 0,
  borderTop: `1px solid ${COLOR.border}`
};

const eyebrowStyle: CSSProperties = {
  color: COLOR.amber,
  fontSize: 9,
  letterSpacing: "0.13em",
  textTransform: "uppercase"
};

const eyebrowInlineStyle: CSSProperties = {
  color: COLOR.textFaint,
  fontSize: 9,
  letterSpacing: "0.08em",
  textTransform: "uppercase"
};

const sectionTitleStyle: CSSProperties = {
  margin: "4px 0 3px",
  color: COLOR.text,
  fontSize: 14,
  lineHeight: 1.3,
  fontWeight: 600
};

const hypothesisStyle: CSSProperties = {
  margin: "0 18px 12px",
  padding: "12px 13px",
  border: `1px solid ${COLOR.border}`,
  borderLeft: `3px solid ${COLOR.pink}`,
  background: COLOR.bgElev
};

const repairButtonStyle: CSSProperties = {
  fontFamily: FONT_MONO,
  fontSize: 11,
  fontWeight: 600,
  color: COLOR.amber,
  background: "#241d12",
  border: `1px solid ${COLOR.amber}`,
  borderRadius: 2,
  padding: "5px 11px",
  cursor: "pointer"
};

const facetLinkStyle: CSSProperties = {
  fontFamily: FONT_MONO,
  fontSize: 10,
  color: COLOR.amberLink,
  background: "transparent",
  border: 0,
  padding: 0,
  cursor: "pointer"
};

const attemptLinkStyle: CSSProperties = {
  fontFamily: FONT_MONO,
  fontSize: 10,
  color: COLOR.amberLink,
  background: "transparent",
  border: 0,
  padding: 0,
  cursor: "pointer"
};

const timelineStyle: CSSProperties = {
  margin: "0 18px 18px 25px",
  borderLeft: `1px solid ${COLOR.borderStrong}`
};

const historyRevealStyle: CSSProperties = {
  width: "calc(100% - 36px)",
  margin: "0 18px 18px",
  padding: "13px 14px",
  display: "flex",
  flexDirection: "column",
  alignItems: "flex-start",
  gap: 5,
  border: `1px dashed ${COLOR.borderStrong}`,
  background: COLOR.bgInput,
  fontFamily: FONT_MONO,
  fontSize: 11,
  textAlign: "left",
  cursor: "pointer"
};

const timelineEntryStyle: CSSProperties = {
  position: "relative",
  padding: "0 0 18px 18px"
};

const timelineMarkerStyle: CSSProperties = {
  position: "absolute",
  left: -5,
  top: 4,
  width: 9,
  height: 9,
  border: `2px solid ${COLOR.cyan}`,
  background: COLOR.bg,
  borderRadius: "50%"
};

const emptyStateStyle: CSSProperties = {
  margin: "0 18px 18px",
  padding: "14px 15px",
  border: `1px dashed ${COLOR.borderStrong}`,
  color: COLOR.textDim,
  fontSize: 11,
  lineHeight: 1.55
};
