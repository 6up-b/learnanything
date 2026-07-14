// F2 — Review tab (§4.9 Log / Review). Two sections:
//   1. Changelog (spine): reverse-chronological per-session diffs plus any
//      system-authored entries (recalibration / regrade). Non-monotone events
//      (downgrades, corrections, returned misconceptions) are annotated with a
//      glyph + label + color — never smoothed, never color alone (§4.13).
//   2. Working hypotheses (standing state): active misconception statements as
//      cold `diagnosis` claims via ClaimSurface. Each statement is ALWAYS paired
//      with its authored correction in the same visual unit (§4.7 rule); the
//      backend feed already drops rows lacking a correction, and we guard again
//      here. Each hypothesis carries a "repair this" action (→ F6 flow).
//
// Every facet reference opens FacetEvidenceDrawer (§4.9 / §5). The visit_id is
// minted once per tab mount and handed to every claim presentation so the
// backend dispatcher can enforce its ≤1 cold re-ask per visit budget.

import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type {
  ClaimCandidateDto,
  ReviewChangelogEntryDto,
  ReviewLogDto,
  WorkingHypothesisDto
} from "../api/dto";
import { ClaimSurface, mintVisitId } from "../components/ClaimSurface";
import { FacetEvidenceDrawer } from "../components/KnowledgeModel";
import { COLOR, Divider, Faint, FONT_MONO, Pill, SectionHeader } from "../components/term";

const shortFacet = (facetId: string): string => facetId.replace(/^facet_/, "");

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

// A non-monotone / notable event badge: glyph + label + color together, so
// state is never carried by color alone (§4.13).
function EventBadge({ glyph, label, color }: { glyph: string; label: string; color: string }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        color,
        fontSize: 12,
        fontFamily: FONT_MONO
      }}
    >
      <span aria-hidden>{glyph}</span>
      {label}
    </span>
  );
}

function FacetRef({ facetId, onOpen }: { facetId: string; onOpen: (facetId: string) => void }) {
  return (
    <button
      type="button"
      onClick={() => onOpen(facetId)}
      title="open evidence drawer"
      style={{
        fontFamily: FONT_MONO,
        fontSize: 12,
        color: COLOR.amberLink,
        background: "transparent",
        border: `1px solid ${COLOR.border}`,
        borderRadius: 2,
        padding: "0 6px",
        cursor: "pointer"
      }}
    >
      {shortFacet(facetId)}
    </button>
  );
}

const panel: CSSProperties = {
  border: `1px solid ${COLOR.border}`,
  borderRadius: 3,
  padding: "12px 14px",
  marginBottom: 14,
  background: COLOR.bgElev
};

function ChangelogEntry({
  entry,
  onOpenFacet
}: {
  entry: ReviewChangelogEntryDto;
  onOpenFacet: (facetId: string) => void;
}) {
  // System-authored recalibration collapses to ONE honest line, never a
  // per-facet flood the learner appears to have caused (§4.9).
  if (entry.kind === "recalibration") {
    return (
      <div style={{ marginTop: 10, borderTop: `1px solid ${COLOR.border}`, paddingTop: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Pill color="slate">recalibration</Pill>
          <Faint>{fmtDate(entry.at)}</Faint>
        </div>
        <div style={{ marginTop: 3, color: COLOR.textDim }}>
          recalibration: estimates recomputed — your evidence unchanged
        </div>
      </div>
    );
  }

  const moved = entry.predictionsMoved;
  const touched = entry.misconceptionsTouched;
  const badges: Array<{ glyph: string; label: string; color: string }> = [];
  if (entry.facetsDemonstrated > 0)
    badges.push({ glyph: "+", label: `${entry.facetsDemonstrated} demonstrated`, color: COLOR.green });
  if (moved.up > 0) badges.push({ glyph: "▲", label: `${moved.up} up`, color: COLOR.green });
  // Downgrades are annotated, never smoothed.
  if (moved.down > 0) badges.push({ glyph: "▼", label: `${moved.down} down`, color: COLOR.red });
  if (entry.corrections > 0)
    badges.push({ glyph: "⟲", label: `${entry.corrections} corrected`, color: COLOR.amber });
  if (touched.resolved > 0)
    badges.push({ glyph: "✓", label: `${touched.resolved} resolved`, color: COLOR.green });
  // A returned misconception is relapse — rendered plainly, not hidden.
  if (touched.returned > 0)
    badges.push({ glyph: "↩", label: `${touched.returned} returned`, color: COLOR.red });

  const isRegrade = entry.kind === "regrade";
  // A system-authored out-of-session regrade states its old→new ledger fact
  // directly; a downgrade is annotated, never smoothed (§4.9).
  const regradeDirection = entry.direction ?? "same";
  const regradeGlyph = regradeDirection === "down" ? "▼" : regradeDirection === "up" ? "▲" : "＝";
  const regradeColor =
    regradeDirection === "down" ? COLOR.red : regradeDirection === "up" ? COLOR.green : COLOR.textDim;
  return (
    <div style={{ marginTop: 10, borderTop: `1px solid ${COLOR.border}`, paddingTop: 8 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <Pill color={isRegrade ? "amber" : "cyan"}>{isRegrade ? "regrade" : "session"}</Pill>
        <Faint>{fmtDate(entry.at)}</Faint>
        {!isRegrade ? (
          <span style={{ color: COLOR.textDim, fontSize: 12 }}>
            {entry.attemptsRecorded} attempt{entry.attemptsRecorded === 1 ? "" : "s"} ·{" "}
            {entry.itemsReviewed} item{entry.itemsReviewed === 1 ? "" : "s"}
          </span>
        ) : null}
      </div>
      {isRegrade ? (
        <div style={{ marginTop: 5 }}>
          <EventBadge
            glyph={regradeGlyph}
            label={
              entry.oldScore !== undefined && entry.newScore !== undefined
                ? `credit regraded ${regradeDirection}: ${entry.oldScore} → ${entry.newScore}`
                : `credit regraded ${regradeDirection}`
            }
            color={regradeColor}
          />
        </div>
      ) : badges.length > 0 ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 5 }}>
          {badges.map((b) => (
            <EventBadge key={b.label} glyph={b.glyph} label={b.label} color={b.color} />
          ))}
        </div>
      ) : (
        <div style={{ marginTop: 5, color: COLOR.textFaint, fontSize: 12 }}>no belief change</div>
      )}
      {entry.facetIds.length > 0 ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 6, alignItems: "center" }}>
          <Faint>facets:</Faint>
          {entry.facetIds.slice(0, 12).map((f) => (
            <FacetRef key={f} facetId={f} onOpen={onOpenFacet} />
          ))}
          {entry.facetIds.length > 12 ? <Faint>+{entry.facetIds.length - 12} more</Faint> : null}
        </div>
      ) : null}
    </div>
  );
}

// §4.7 render: state the evidence relation, not a belief attribution, and NEVER
// show the misconception without its authored correction in the same unit.
function statementPairText(h: WorkingHypothesisDto): string {
  const correction = h.correctionStatement.trim();
  if (h.targetFacet && h.confusedWithFacet) {
    return `Some answers here were consistent with confusing ${shortFacet(h.targetFacet)} and ${shortFacet(
      h.confusedWithFacet
    )}. The distinction to use here: ${correction}`;
  }
  return `${h.statement.trim()} — the distinction to use here: ${correction}`;
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
  const claim: ClaimCandidateDto = useMemo(
    () => ({
      claimClass: "diagnosis",
      claimType: "misconception",
      claimRef: hypothesis.id,
      // The feed carries no claim/producer version for a standing hypothesis;
      // synthesize stable values so cooldown + per-visit dedup key correctly.
      claimVersion: "review-working-1",
      producerVersion: "learner_review_feed",
      surface: "review_working_hypotheses",
      temperature: "cold",
      coldReask: true,
      claimText: statementPairText(hypothesis)
    }),
    [hypothesis]
  );

  const lastTransition = hypothesis.history[hypothesis.history.length - 1] ?? null;
  const returned = hypothesis.history.some((h) => h.label === "returned" || h.toStatus === "returned");

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
        <Pill color={returned ? "red" : "pink"}>{hypothesis.status}</Pill>
        {returned ? <EventBadge glyph="↩" label="returned" color={COLOR.red} /> : null}
        {lastTransition ? <Faint>{lastTransition.label} · {fmtDate(lastTransition.at)}</Faint> : null}
      </div>
      <ClaimSurface
        claim={claim}
        visitId={visitId}
        onError={onError}
      />
      {hypothesis.mechanism ? (
        <div style={{ marginTop: 6, color: COLOR.textDim, fontSize: 12 }}>
          <Faint>mechanism:</Faint> {hypothesis.mechanism}
        </div>
      ) : null}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
        <button
          type="button"
          onClick={() => onRepair(hypothesis.id)}
          style={{
            fontFamily: FONT_MONO,
            fontSize: 12,
            color: COLOR.amber,
            background: COLOR.bgInput,
            border: `1px solid ${COLOR.amber}`,
            borderRadius: 2,
            padding: "3px 12px",
            cursor: "pointer"
          }}
        >
          repair this ▸
        </button>
        {hypothesis.targetFacet ? <FacetRef facetId={hypothesis.targetFacet} onOpen={onOpenFacet} /> : null}
        {hypothesis.confusedWithFacet ? (
          <FacetRef facetId={hypothesis.confusedWithFacet} onOpen={onOpenFacet} />
        ) : null}
      </div>
    </div>
  );
}

export function ReviewScreen({
  onError,
  onRepair
}: {
  onError: (message: string) => void;
  onRepair: (misconceptionId: string) => void;
}) {
  const [log, setLog] = useState<ReviewLogDto | null>(null);
  const [drawerFacetId, setDrawerFacetId] = useState<string | null>(null);
  // One visit id per tab mount — handed to every claim presentation so the
  // dispatcher enforces its per-visit cold re-ask budget.
  const visitId = useRef<string>(mintVisitId());

  useEffect(() => {
    let alive = true;
    api
      .getReviewLog()
      .then((r) => alive && setLog(r))
      .catch((e) => alive && onError(e instanceof Error ? e.message : String(e)));
    return () => {
      alive = false;
    };
  }, [onError]);

  if (!log) {
    return <div style={{ padding: 30, color: COLOR.textFaint, fontSize: 13, fontFamily: FONT_MONO }}>loading review log…</div>;
  }

  // Fresh vault: suppress the changelog entirely; working hypotheses render
  // alone with one line on what appears after the first session (§4.9).
  const emptyVault = log.changelog.length === 0;

  return (
    <div style={{ fontFamily: FONT_MONO, color: COLOR.text, padding: "8px 4px", overflowY: "auto" }}>
      <SectionHeader>Review</SectionHeader>
      <Faint>the changelog of your knowledge — what was demonstrated, moved, or corrected</Faint>

      {!emptyVault ? (
        <div style={panel}>
          <Faint>Changelog · {log.changelog.length} entr{log.changelog.length === 1 ? "y" : "ies"}</Faint>
          {log.changelog.map((entry) => (
            <ChangelogEntry key={entry.id} entry={entry} onOpenFacet={setDrawerFacetId} />
          ))}
        </div>
      ) : null}

      <div style={panel}>
        <Faint>Working hypotheses · what&apos;s shaky now, each with its correction attached</Faint>
        {log.workingHypotheses.length === 0 ? (
          <div style={{ marginTop: 8, color: COLOR.textDim }}>
            {emptyVault
              ? "Nothing yet. After your first session, this is where standing misconceptions and shaky facets appear — each with its correction and a way to repair it."
              : "No active misconceptions. Clear."}
          </div>
        ) : (
          <>
            <Divider style={{ marginTop: 6 }} />
            {/* §4.7 critical rule: a row without an authored correction never
                renders statement-pair copy. Feed already filters these; guard
                again here so the statement can never appear naked. */}
            {log.workingHypotheses
              .filter((h) => h.correctionStatement && h.correctionStatement.trim())
              .map((h) => (
              <WorkingHypothesis
                key={h.id}
                hypothesis={h}
                visitId={visitId.current}
                onOpenFacet={setDrawerFacetId}
                onRepair={onRepair}
                onError={onError}
              />
            ))}
          </>
        )}
      </div>

      {drawerFacetId ? (
        <div style={drawerBackdrop} onClick={() => setDrawerFacetId(null)}>
          <div style={drawerPanel} onClick={(e) => e.stopPropagation()}>
            <FacetEvidenceDrawer facetId={drawerFacetId} onClose={() => setDrawerFacetId(null)} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

const drawerBackdrop: CSSProperties = {
  position: "fixed",
  inset: 0,
  zIndex: 210,
  background: "rgba(8, 8, 13, 0.78)",
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "center",
  padding: "8vh 5vw",
  backdropFilter: "blur(2px)"
};

const drawerPanel: CSSProperties = {
  width: "min(680px, 100%)",
  maxHeight: "80vh",
  overflowY: "auto"
};
