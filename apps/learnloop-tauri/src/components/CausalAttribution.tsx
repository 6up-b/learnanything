import { useCallback, useState, type CSSProperties, type ReactNode } from "react";
import { api } from "../api/client";
import type {
  CausalDivergenceAnchorDto,
  CausalEpisodeDto,
  CausalFeedbackDto,
  CausalHypothesisDto,
  CausalProbeOfferDto,
  CausalRepairActionId,
  CausalRepairStatusDto,
  CausalRepairStatusState,
  CausalTargetRefDto,
  RepairedTraceDto,
  UnresolvedCauseSelfReportResponse,
} from "../api/dto";
import { MarkdownMath } from "../render/MarkdownMath";
import { COLOR, Dim, Faint, FONT_MONO, Pill, SectionHeader } from "./term";

const CONTEST_LABELS: Partial<Record<UnresolvedCauseSelfReportResponse, string>> = {
  diagnosis_wrong: "The diagnosis is wrong",
  item_unclear: "The item was unclear",
  notation_confused: "The notation confused me",
  other_valid_approach: "I used another valid approach",
  slipped: "I knew it and slipped",
};

const ANCHOR_LABELS: Record<string, string> = {
  first_observable_divergence: "first observable divergence",
  earliest_supported_faulty_commitment: "earliest supported commitment",
  repair_insertion_point: "repair insertion point",
};

function humanize(value: string | null | undefined): string {
  return value ? value.replace(/_/g, " ") : "unknown";
}

export function formatCausalTarget(ref: CausalTargetRefDto | null | undefined): string {
  if (!ref) return "no typed target";
  if (ref.kind === "facet_capability") {
    return [ref.facetId, ref.capability].filter(Boolean).join(" · ") || "facet capability";
  }
  if (ref.kind === "criterion") return ref.criterionId ? `criterion · ${ref.criterionId}` : "criterion";
  if (ref.kind === "item_step") {
    return [ref.recipeId, ref.checkpointId].filter(Boolean).join(" · ") || "item step";
  }
  if (ref.kind === "answer_span") {
    return ref.quote ? `answer span · “${ref.quote}”` : "answer span";
  }
  return humanize(ref.kind);
}

export function formatDivergenceAnchor(
  anchor: CausalDivergenceAnchorDto | null | undefined,
): string {
  if (!anchor) return "not localized";
  const kind = humanize(typeof anchor.anchorKind === "string" ? anchor.anchorKind : null);
  const quote = typeof anchor.quote === "string" && anchor.quote.trim() ? `“${anchor.quote}”` : null;
  const checkpoint =
    typeof anchor.checkpointId === "string" && anchor.checkpointId
      ? `checkpoint ${anchor.checkpointId}`
      : null;
  const criterion =
    typeof anchor.criterionId === "string" && anchor.criterionId
      ? `criterion ${anchor.criterionId}`
      : null;
  return [kind, quote ?? checkpoint, criterion].filter(Boolean).join(" · ");
}

function Panel({
  children,
  tone = "cyan",
  style,
}: {
  children: ReactNode;
  tone?: "cyan" | "green" | "amber" | "red" | "slate";
  style?: CSSProperties;
}) {
  const border = {
    cyan: COLOR.cyan,
    green: COLOR.green,
    amber: COLOR.amber,
    red: COLOR.red,
    slate: COLOR.borderStrong,
  }[tone];
  return (
    <div
      style={{
        border: `1px solid ${COLOR.border}`,
        borderLeft: `3px solid ${border}`,
        background: COLOR.bgElev,
        padding: "12px 14px",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

function SmallLabel({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        color: COLOR.textFaint,
        fontFamily: FONT_MONO,
        fontSize: 10,
        letterSpacing: "0.04em",
        marginBottom: 5,
        textTransform: "uppercase",
      }}
    >
      {children}
    </div>
  );
}

function TraceView({
  trace,
  label = "authorized repaired trace",
}: {
  trace: RepairedTraceDto;
  label?: string;
}) {
  return (
    <Panel tone="green">
      <SmallLabel>{label}</SmallLabel>
      {trace.learnerWorkPrefix ? (
        <div style={{ marginBottom: 9 }}>
          <Faint>preserved learner work</Faint>
          <div
            style={{
              marginTop: 4,
              padding: "7px 9px",
              border: `1px solid ${COLOR.border}`,
              whiteSpace: "pre-wrap",
            }}
          >
            <MarkdownMath value={trace.learnerWorkPrefix} />
          </div>
        </div>
      ) : null}
      {trace.minimalEdit ? (
        <div style={{ color: COLOR.text, lineHeight: 1.55 }}>
          <span style={{ color: COLOR.green }}>minimal edit · </span>
          {trace.minimalEdit}
        </div>
      ) : null}
      {trace.repairedAnswerMd ? (
        <div style={{ marginTop: 9 }}>
          <Faint>repaired continuation</Faint>
          <div
            style={{
              marginTop: 4,
              padding: "7px 9px",
              border: `1px solid ${COLOR.border}`,
            }}
          >
            <MarkdownMath value={trace.repairedAnswerMd} />
          </div>
        </div>
      ) : null}
    </Panel>
  );
}

// ── P2 causal repair hold (spec_causal_attribution_v1 §6, §6.6) ──────────────
// The typed union `causal_repair_status` returns, rendered as the learner state
// it is. The message is authored server-side (`causal_orchestrator`) precisely
// so one copy exists; this component never re-words it — it only chooses tone,
// the section heading, and which actions are reachable.
//
// §6.6 places the hold in the "why we are NOT reviewing X" position of the typed
// feedback display, next to "why we are not reviewing demonstrated work". What
// is held is the BRANCH-SPECIFIC repair inside one divergent causal factor, not
// "unrelated remediation" — the old wording named the wrong thing.

const REPAIR_STATUS_TONE: Record<
  CausalRepairStatusState,
  "cyan" | "green" | "amber" | "red" | "slate"
> = {
  started: "green",
  safe_common_repair_available: "green",
  needs_disambiguation: "amber",
  deferred_machine_checks: "cyan",
  blocked_pending_review: "slate",
};

const REPAIR_STATUS_PILL: Record<CausalRepairStatusState, string> = {
  started: "repair started",
  safe_common_repair_available: "one repair covers it",
  needs_disambiguation: "holding this repair",
  deferred_machine_checks: "checking first",
  blocked_pending_review: "check not ready",
};

const REPAIR_STATUS_HEADING: Record<CausalRepairStatusState, string> = {
  started: "what happens next",
  safe_common_repair_available: "what happens next",
  needs_disambiguation: "why we are not reviewing this yet",
  deferred_machine_checks: "why we are not reviewing this yet",
  blocked_pending_review: "why we are not reviewing this yet",
};

/** Honest learner copy for a probe offer that could not be served. The typed
 *  reasons come from `causal_orchestrator.accept_probe_offer`. */
const PROBE_OFFER_COPY: Record<string, string> = {
  factor_not_open: "This one is already settled — there is nothing left to check.",
  no_reviewed_active_candidate: "The check that would tell these apart isn't ready yet.",
  probe_item_missing_from_vault: "The check that would tell these apart isn't ready yet.",
  probe_item_not_eligible: "The check that would tell these apart isn't ready yet.",
  another_probe_episode_is_open:
    "Another diagnostic is already open for this topic — finish that one first.",
};

function probeOfferCopy(reason: string): string {
  return PROBE_OFFER_COPY[reason] ?? "The quick check could not be started right now.";
}

export function CausalRepairStatusPanel({
  status,
  pendingActionId = null,
  note = null,
  onAction,
  style,
}: {
  status: CausalRepairStatusDto;
  pendingActionId?: CausalRepairActionId | null;
  /** Transient outcome copy (e.g. a probe offer that could not be served). */
  note?: string | null;
  onAction?: (actionId: CausalRepairActionId, status: CausalRepairStatusDto) => void;
  style?: CSSProperties;
}) {
  const tone = REPAIR_STATUS_TONE[status.status] ?? "slate";
  const busy = pendingActionId != null;
  const pendingChecks = status.pendingMachineCheckIds.length;
  return (
    <Panel tone={tone} style={style}>
      <SmallLabel>{REPAIR_STATUS_HEADING[status.status] ?? "repair status"}</SmallLabel>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <Pill color={tone}>{REPAIR_STATUS_PILL[status.status] ?? status.status}</Pill>
      </div>
      <div style={{ marginTop: 7, color: COLOR.text, lineHeight: 1.55 }}>{status.message}</div>

      {/* "Not now" means stop asking, not stop being ambiguous: the state is
          still needs_disambiguation, the offer is simply withdrawn. */}
      {status.status === "needs_disambiguation" && !status.probeOffered ? (
        <div style={{ marginTop: 6 }}>
          <Dim>You asked me not to check again for now — you can still ask to be taught.</Dim>
        </div>
      ) : null}

      {status.status === "deferred_machine_checks" && pendingChecks ? (
        <div style={{ marginTop: 6 }}>
          <Dim>
            {pendingChecks} machine-side check{pendingChecks === 1 ? "" : "s"} still to finish.
          </Dim>
        </div>
      ) : null}

      {note ? (
        <div style={{ marginTop: 7 }}>
          <Dim>{note}</Dim>
        </div>
      ) : null}

      {status.actions.length && onAction ? (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 10 }}>
          {status.actions.map((action) => {
            const primary = action.id === "take_quick_check";
            const color = primary ? COLOR.cyan : COLOR.amber;
            return (
              <button
                key={action.id}
                type="button"
                disabled={busy}
                onClick={() => onAction(action.id, status)}
                style={{
                  border: `1px solid ${busy ? COLOR.border : color}`,
                  background: "transparent",
                  color: busy ? COLOR.textFaint : color,
                  cursor: busy ? "default" : "pointer",
                  fontFamily: FONT_MONO,
                  fontSize: 11,
                  padding: "5px 9px",
                }}
              >
                {pendingActionId === action.id ? "…" : action.label}
              </button>
            );
          })}
        </div>
      ) : null}

      {status.probeDecision ? (
        <div style={{ marginTop: 8, fontFamily: FONT_MONO, fontSize: 10 }}>
          <Faint>
            decision · {humanize(status.probeDecision)} · {humanize(status.reason)}
            {status.decisionPolicyVersion ? ` · ${status.decisionPolicyVersion}` : ""}
          </Faint>
        </div>
      ) : null}
    </Panel>
  );
}

/** Fetch + act on one causal repair case. Shared by Feedback (where the hold is
 *  rendered inside the typed feedback display) and Repair (where the learner
 *  tapped "start repair"), so the three actions behave identically on both. */
export function useCausalRepairActions({
  sessionId,
  onStatus,
  onProbeAccepted,
  onError,
}: {
  sessionId?: string | null;
  onStatus: (status: CausalRepairStatusDto) => void;
  /** The probe was pinned into a factor-aware episode — serve the instrument. */
  onProbeAccepted?: (offer: CausalProbeOfferDto) => void;
  onError?: (message: string) => void;
}) {
  const [pendingActionId, setPendingActionId] = useState<CausalRepairActionId | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const runAction = useCallback(
    (actionId: CausalRepairActionId, status: CausalRepairStatusDto) => {
      const factorId = status.factorId;
      if (!factorId) return;
      setPendingActionId(actionId);
      setNote(null);
      const refresh = () =>
        api
          .causalRepairStatus(status.misconceptionId, sessionId)
          .then((result) => onStatus(result.repairStatus));
      const done = () => setPendingActionId(null);
      const fail = (error: unknown) => {
        onError?.(error instanceof Error ? error.message : String(error));
      };

      if (actionId === "take_quick_check") {
        api
          .causalProbeOfferAction({
            factorId,
            misconceptionId: status.misconceptionId,
            sessionId,
            decisionReceiptId: status.decisionReceiptId,
          })
          .then((result) => {
            const offer = result.offer;
            if (offer.accepted && offer.practiceItemId && onProbeAccepted) {
              onProbeAccepted(offer);
              return;
            }
            setNote(probeOfferCopy(offer.reason));
            return refresh();
          })
          .catch(fail)
          .finally(done);
        return;
      }

      if (actionId === "not_now") {
        // The decline persists; re-reading is what proves it — the factor stays
        // divergent and comes back with probeOffered: false.
        api
          .causalProbeDefer({ factorId, misconceptionId: status.misconceptionId, sessionId })
          .then(refresh)
          .catch(fail)
          .finally(done);
        return;
      }

      api
        .causalTeachMeNow({
          factorId,
          misconceptionId: status.misconceptionId,
          sessionId,
        })
        .then((result) => onStatus(result.repairStatus))
        .catch(fail)
        .finally(done);
    },
    [onError, onProbeAccepted, onStatus, sessionId],
  );

  return { pendingActionId, note, runAction };
}

export function CausalFeedbackPanel({
  feedback,
  onContest,
  contestPending = false,
  repairStatus = null,
  repairPendingActionId = null,
  repairNote = null,
  onRepairAction,
}: {
  feedback: CausalFeedbackDto;
  onContest?: (
    reason: UnresolvedCauseSelfReportResponse,
    factorId: string | null,
  ) => void;
  contestPending?: boolean;
  /** §6.6: the typed P2 repair hold, rendered in the "why we are NOT reviewing
   *  X" position rather than raised as a modal error. */
  repairStatus?: CausalRepairStatusDto | null;
  repairPendingActionId?: CausalRepairActionId | null;
  repairNote?: string | null;
  onRepairAction?: (actionId: CausalRepairActionId, status: CausalRepairStatusDto) => void;
}) {
  const nonHypothesisUnverified = feedback.unverified.filter(
    (claim) => claim.kind !== "causal_hypothesis",
  );
  const canContest = Boolean(feedback.contestAction.available && onContest);
  return (
    <div style={{ fontSize: 13, color: COLOR.text }}>
      <div
        style={{
          display: "flex",
          gap: 8,
          alignItems: "center",
          flexWrap: "wrap",
          marginBottom: 10,
        }}
      >
        <Pill color="cyan">claim checked</Pill>
        <Dim>We separate what the attempt showed from what might explain it.</Dim>
      </div>

      {feedback.demonstratedCriteria.length ? (
        <Panel tone="green">
          <SmallLabel>what you already demonstrated</SmallLabel>
          <div style={{ display: "grid", gap: 5 }}>
            {feedback.demonstratedCriteria.map((criterion) => (
              <div
                key={criterion.criterionId}
                style={{ display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}
              >
                <span style={{ color: COLOR.green, fontFamily: FONT_MONO }}>✓</span>
                <span style={{ color: COLOR.text }}>
                  {criterion.criterionLabel || humanize(criterion.criterionId)}
                </span>
                <Faint>
                  {criterion.pointsAwarded}/{criterion.pointsPossible}
                </Faint>
              </div>
            ))}
          </div>
        </Panel>
      ) : null}

      {feedback.firstDivergence ? (
        <Panel tone="red" style={{ marginTop: 8 }}>
          <SmallLabel>first divergence in your work</SmallLabel>
          <div style={{ color: COLOR.text, lineHeight: 1.55 }}>
            {formatDivergenceAnchor(feedback.firstDivergence)}
          </div>
        </Panel>
      ) : null}

      {feedback.verifiedCorrection ? (
        <Panel tone="green" style={{ marginTop: 8 }}>
          <div
            style={{
              display: "flex",
              gap: 8,
              alignItems: "center",
              marginBottom: feedback.verifiedCorrection.rationale ? 7 : 0,
            }}
          >
            <Pill color="green">verified</Pill>
            <span style={{ color: COLOR.green, fontWeight: 600 }}>
              {feedback.verifiedCorrection.label}
            </span>
          </div>
          {feedback.verifiedCorrection.rationale ? (
            <MarkdownMath value={feedback.verifiedCorrection.rationale} />
          ) : null}
          <div style={{ marginTop: 6, color: COLOR.textDim, lineHeight: 1.5 }}>
            {feedback.verifiedCorrection.verificationScope}
          </div>
        </Panel>
      ) : null}

      {feedback.causalHypotheses.length ? (
        <div style={{ marginTop: 12 }}>
          <SmallLabel>possible explanations · not yet confirmed</SmallLabel>
          <div style={{ display: "grid", gap: 7 }}>
            {feedback.causalHypotheses.map((hypothesis) => (
              <Panel key={hypothesis.hypothesisId} tone="amber">
                <div
                  style={{
                    display: "flex",
                    gap: 7,
                    alignItems: "center",
                    flexWrap: "wrap",
                    marginBottom: 6,
                  }}
                >
                  <Pill color="amber">uncertain</Pill>
                </div>
                <div style={{ lineHeight: 1.55 }}>
                  <MarkdownMath value={hypothesis.statement} />
                </div>
              </Panel>
            ))}
          </div>
        </div>
      ) : null}

      {nonHypothesisUnverified.length || feedback.causalHypotheses.length ? (
        <Panel tone="slate" style={{ marginTop: 8 }}>
          <SmallLabel>what remains unverified</SmallLabel>
          {nonHypothesisUnverified.length ? (
            nonHypothesisUnverified.map((claim, index) => (
              <div
                key={`${claim.kind}:${claim.hypothesisId ?? index}`}
                style={{ marginTop: index ? 8 : 0, lineHeight: 1.55 }}
              >
                <Pill color="slate">{humanize(claim.kind)}</Pill>
                <div style={{ marginTop: 5 }}>
                  <MarkdownMath value={claim.statement} />
                </div>
              </div>
            ))
          ) : (
            <Dim>Why this happened remains a hypothesis, not a confirmed learner belief.</Dim>
          )}
        </Panel>
      ) : null}

      {feedback.proposedNextAction ? (
        <Panel tone="cyan" style={{ marginTop: 8 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <Pill color="cyan">suggested next step</Pill>
          </div>
          {feedback.proposedNextAction.rationale ? (
            <div style={{ marginTop: 7, lineHeight: 1.55 }}>
              <MarkdownMath value={feedback.proposedNextAction.rationale} />
            </div>
          ) : null}
        </Panel>
      ) : null}

      {feedback.protectedTargets.length ? (
        <Panel tone="green" style={{ marginTop: 8 }}>
          <SmallLabel>why we are not reviewing demonstrated work</SmallLabel>
          {feedback.protectedTargets.map((target, index) => (
            <div key={`${target.target ?? "target"}:${index}`} style={{ marginTop: index ? 7 : 0 }}>
              <div style={{ color: COLOR.textDim, lineHeight: 1.5 }}>
                {target.reason}
              </div>
            </div>
          ))}
        </Panel>
      ) : null}

      {/* §6.6: the "why we are NOT reviewing X" slot. A held targeted repair
          belongs here — next to the demonstrated work we are also not
          reviewing — not behind a modal error. */}
      {repairStatus ? (
        <CausalRepairStatusPanel
          status={repairStatus}
          pendingActionId={repairPendingActionId}
          note={repairNote}
          onAction={onRepairAction}
          style={{ marginTop: 8 }}
        />
      ) : null}

      {feedback.repairedTrace ? (
        <div style={{ marginTop: 8 }}>
          <TraceView trace={feedback.repairedTrace} />
        </div>
      ) : feedback.repairedTraceWithheldReason ? (
        <Panel tone="slate" style={{ marginTop: 8 }}>
          <SmallLabel>repaired trace withheld</SmallLabel>
          <Dim>
            The repair could reveal the answer before a permitted repair or verification activity.
          </Dim>
        </Panel>
      ) : null}

      {feedback.contestAction.available ? (
        <Panel tone="amber" style={{ marginTop: 8 }}>
          <SmallLabel>does this diagnosis fit?</SmallLabel>
          <Dim>
            Your report is evidence toward resolving the cause; it does not silently rewrite the record.
          </Dim>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
            {feedback.contestAction.reasons.map((reason) => (
              <button
                key={reason}
                type="button"
                disabled={!canContest || contestPending}
                onClick={() => {
                  if (canContest) {
                    onContest?.(reason, feedback.contestAction.factorId ?? null);
                  }
                }}
                style={{
                  border: `1px solid ${canContest ? COLOR.amber : COLOR.border}`,
                  background: "transparent",
                  color: canContest ? COLOR.amber : COLOR.textFaint,
                  cursor: canContest && !contestPending ? "pointer" : "default",
                  fontFamily: FONT_MONO,
                  fontSize: 11,
                  padding: "5px 8px",
                }}
              >
                {CONTEST_LABELS[reason] ?? humanize(reason)}
              </button>
            ))}
          </div>
        </Panel>
      ) : null}
    </div>
  );
}

function AuditRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "148px minmax(0, 1fr)",
        gap: 10,
        padding: "5px 0",
        borderBottom: `1px solid ${COLOR.border}`,
        fontSize: 12,
      }}
    >
      <Faint>{label}</Faint>
      <div style={{ minWidth: 0, overflowWrap: "anywhere" }}>{children}</div>
    </div>
  );
}

function observedEvidence(hypothesis: CausalHypothesisDto): string | null {
  const value = hypothesis.evidence?.observedEvidence;
  return typeof value === "string" && value.trim() ? value : null;
}

function recordString(record: Record<string, unknown> | null, key: string): string | null {
  const value = record?.[key];
  return typeof value === "string" && value.trim() ? value : null;
}

function recordNumber(record: Record<string, unknown> | null, key: string): number | null {
  const value = record?.[key];
  return typeof value === "number" ? value : null;
}

export function CausalEpisodeInspector({ episode }: { episode: CausalEpisodeDto | null | undefined }) {
  const receipt = episode?.receipt;
  if (!receipt) {
    return (
      <>
        <SectionHeader>Causal episode</SectionHeader>
        <Faint>No P1 diagnosis receipt was recorded for this attempt.</Faint>
      </>
    );
  }
  const hypothesisById = new Map(
    (episode?.hypotheses ?? []).map((hypothesis) => [hypothesis.id, hypothesis]),
  );
  const axesById = new Map(receipt.attributionAxes.map((axis) => [axis.hypothesisId, axis]));
  const orderedRefs = [...receipt.hypotheses].sort((left, right) => {
    const leftRank = receipt.ordinalRanking.indexOf(left.id);
    const rightRank = receipt.ordinalRanking.indexOf(right.id);
    return (leftRank < 0 ? Number.MAX_SAFE_INTEGER : leftRank) -
      (rightRank < 0 ? Number.MAX_SAFE_INTEGER : rightRank);
  });
  const selected = receipt.repairSelection.selected;
  const legacyTaxonomy = receipt.mechanismTaxonomy ?? {};
  const taxonomyClusters = Array.isArray(legacyTaxonomy.clusters)
    ? legacyTaxonomy.clusters
    : [];
  const taxonomyAbstained = Array.isArray(legacyTaxonomy.abstained)
    ? legacyTaxonomy.abstained
    : [];

  return (
    <>
      <SectionHeader>Causal episode</SectionHeader>
      <AuditRow label="receipt">
        <span style={{ color: COLOR.cyan, fontFamily: FONT_MONO }}>{receipt.id}</span>
        <Faint> · schema v{receipt.schemaVersion} · immutable snapshot</Faint>
      </AuditRow>
      <AuditRow label="permitted uses">
        <span style={{ display: "inline-flex", gap: 5, flexWrap: "wrap" }}>
          {receipt.permittedUses.map((use) => (
            <Pill key={use} color="cyan">{humanize(use)}</Pill>
          ))}
        </span>
      </AuditRow>
      <AuditRow label="plausible set">
        <Dim>{receipt.plausibleSet.length} concrete hypothesis{receipt.plausibleSet.length === 1 ? "" : "es"}</Dim>
      </AuditRow>

      <div style={{ marginTop: 12 }}>
        <SmallLabel>criterion outcomes</SmallLabel>
        <div style={{ display: "grid", gap: 5 }}>
          {receipt.criterionOutcomes.map((criterion) => {
            const tone = criterion.fullCredit ? COLOR.green : criterion.assessable ? COLOR.red : COLOR.textFaint;
            const mark = criterion.fullCredit ? "✓" : criterion.assessable ? "✗" : "·";
            return (
              <div
                key={criterion.criterionId}
                style={{
                  display: "grid",
                  gridTemplateColumns: "18px minmax(0, 1fr) auto",
                  gap: 7,
                  color: tone,
                  fontSize: 12,
                }}
              >
                <span>{mark}</span>
                <span>{criterion.criterionId}</span>
                <span style={{ fontFamily: FONT_MONO }}>
                  {criterion.pointsAwarded}/{criterion.pointsPossible}
                  {!criterion.assessable ? " · unassessable" : ""}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ marginTop: 14 }}>
        <SmallLabel>three divergence anchors</SmallLabel>
        {([
          ["first_observable_divergence", receipt.divergenceAnchors.firstObservableDivergence],
          ["earliest_supported_faulty_commitment", receipt.divergenceAnchors.earliestSupportedFaultyCommitment],
          ["repair_insertion_point", receipt.divergenceAnchors.repairInsertionPoint],
        ] as const).map(([name, anchor]) => (
          <AuditRow key={name} label={ANCHOR_LABELS[name] ?? humanize(name)}>
            <Dim>{formatDivergenceAnchor(anchor)}</Dim>
          </AuditRow>
        ))}
      </div>

      <div style={{ marginTop: 14 }}>
        <SmallLabel>candidate causes and evidence</SmallLabel>
        <div style={{ display: "grid", gap: 8 }}>
          {orderedRefs.map((ref, index) => {
            const hypothesis = hypothesisById.get(ref.id);
            if (!hypothesis) return null;
            const axis = axesById.get(ref.id);
            const support = receipt.supportScores[ref.id];
            const evidence = observedEvidence(hypothesis);
            const errorType = recordString(hypothesis.evidence, "errorType");
            const severity = recordNumber(hypothesis.evidence, "severity");
            const observedSignature = recordString(hypothesis.evidence, "observedSignature");
            const preregisteredSignature = recordString(
              hypothesis.evidence,
              "preregisteredSignature",
            );
            const applicabilitySurface = recordString(hypothesis.applicability, "surfaceFamily");
            return (
              <Panel key={ref.id} tone={ref.status === "open_set" ? "slate" : "amber"}>
                <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                  <span style={{ color: COLOR.textFaint, fontFamily: FONT_MONO }}>#{index + 1}</span>
                  <Pill color={ref.status === "open_set" ? "slate" : "amber"}>{humanize(ref.status)}</Pill>
                  <Pill color="slate">{humanize(axis?.causeScope ?? hypothesis.causeScope)}</Pill>
                  <span style={{ marginLeft: "auto" }}>
                    <Faint>support </Faint>
                    <span style={{ color: COLOR.amber, fontFamily: FONT_MONO }}>
                      {typeof support === "number" ? support.toFixed(2) : "not established"}
                    </span>
                  </span>
                </div>
                <div style={{ marginTop: 6, lineHeight: 1.5 }}>
                  <MarkdownMath value={hypothesis.statement} />
                </div>
                <div style={{ marginTop: 7, fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textFaint }}>
                  {hypothesis.id} · v{hypothesis.version}
                  {hypothesis.supersedesId ? ` · supersedes ${hypothesis.supersedesId}` : ""}
                </div>
                <div style={{ marginTop: 6, fontSize: 11, color: COLOR.textDim, lineHeight: 1.5 }}>
                  resolution · {humanize(axis?.resolutionStatus)}
                  {" · "}target · {formatCausalTarget(axis?.targetRef ?? hypothesis.targetRef)}
                  {hypothesis.operation ? ` · operation · ${humanize(hypothesis.operation)}` : ""}
                  {hypothesis.mechanism ? ` · mechanism · ${humanize(hypothesis.mechanism)}` : ""}
                </div>
                {evidence ? (
                  <div style={{ marginTop: 6, fontSize: 11, color: COLOR.textDim }}>
                    evidence · {evidence}
                  </div>
                ) : null}
                {errorType || severity != null || applicabilitySurface ? (
                  <div style={{ marginTop: 4, fontSize: 11, color: COLOR.textDim }}>
                    {errorType ? `error · ${humanize(errorType)}` : ""}
                    {severity != null ? `${errorType ? " · " : ""}severity · ${severity.toFixed(2)}` : ""}
                    {applicabilitySurface
                      ? `${errorType || severity != null ? " · " : ""}surface · ${humanize(applicabilitySurface)}`
                      : ""}
                  </div>
                ) : null}
                {observedSignature || preregisteredSignature ? (
                  <div style={{ marginTop: 4, fontSize: 11, color: COLOR.textDim }}>
                    {observedSignature ? `observed signature · ${observedSignature}` : ""}
                    {preregisteredSignature
                      ? `${observedSignature ? " · " : ""}pre-registered · ${preregisteredSignature}`
                      : ""}
                  </div>
                ) : null}
                {hypothesis.postdictiveClaims.length ? (
                  <div style={{ marginTop: 6, fontSize: 11, lineHeight: 1.5 }}>
                    <Faint>deterministic postdictive claims · </Faint>
                    <Dim>
                      {hypothesis.postdictiveClaims
                        .map((claim) => {
                          const criterion =
                            typeof claim.criterionId === "string" ? claim.criterionId : null;
                          const must = typeof claim.must === "string" ? humanize(claim.must) : null;
                          return [criterion, must].filter(Boolean).join(" must ");
                        })
                        .filter(Boolean)
                        .join(" · ")}
                    </Dim>
                  </div>
                ) : null}
              </Panel>
            );
          })}
        </div>
      </div>

      <div style={{ marginTop: 14 }}>
        <SmallLabel>repair decision</SmallLabel>
        {selected ? (
          <Panel tone="cyan">
            <div style={{ display: "flex", gap: 7, alignItems: "center", flexWrap: "wrap" }}>
              <Pill color="cyan">selected</Pill>
              <span style={{ color: COLOR.cyan, fontFamily: FONT_MONO }}>
                {humanize(selected.repairClass.operator)}
              </span>
              <Faint>{selected.repairClass.id}</Faint>
            </div>
            {selected.suggestion.rationale ? (
              <div style={{ marginTop: 7, lineHeight: 1.5 }}>
                <MarkdownMath value={selected.suggestion.rationale} />
              </div>
            ) : null}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                gap: 8,
                marginTop: 9,
              }}
            >
              <AuditMetric label="latent changes" value={selected.minimality.latentChangeCost} />
              <AuditMetric label="checkpoint changes" value={selected.minimality.checkpointChangeCost} />
              <AuditMetric label="trace edit cost" value={selected.minimality.traceEditCost ?? "—"} />
              <AuditMetric label="backtracking depth" value={selected.minimality.backtrackingDepth ?? "—"} />
              <AuditMetric label="estimated minutes" value={selected.minimality.estimatedMinutes ?? "—"} />
              <AuditMetric
                label="answer reveal budget"
                value={selected.repairClass.answerRevealBudget}
              />
            </div>
            <div style={{ marginTop: 8, fontSize: 11, lineHeight: 1.55 }}>
              <Faint>targets · </Faint>
              <Dim>
                {selected.repairClass.targetRefs.map(formatCausalTarget).join(" · ") || "none"}
              </Dim>
              <br />
              <Faint>preserves · </Faint>
              <Dim>
                {selected.repairClass.preserveRefs.map(formatCausalTarget).join(" · ") || "none"}
              </Dim>
            </div>
            {selected.minimality.preservedCriteria.length ? (
              <div style={{ marginTop: 6, fontSize: 11 }}>
                <Faint>preserved criteria · </Faint>
                <Dim>{selected.minimality.preservedCriteria.join(" · ")}</Dim>
              </div>
            ) : null}
            {selected.minimality.changedLatentClaims.length ? (
              <div style={{ marginTop: 4, fontSize: 11 }}>
                <Faint>changed latent claims · </Faint>
                <Dim>{selected.minimality.changedLatentClaims.join(" · ")}</Dim>
              </div>
            ) : null}
            {selected.minimality.changedTraceSteps.length ? (
              <div style={{ marginTop: 4, fontSize: 11 }}>
                <Faint>changed trace steps · </Faint>
                <Dim>{selected.minimality.changedTraceSteps.join(" · ")}</Dim>
              </div>
            ) : null}
          </Panel>
        ) : (
          <Panel tone="red">
            <Dim>No safe structural repair was selected.</Dim>
          </Panel>
        )}
        {receipt.repairSelection.rejected.map((rejected) => (
          <div
            key={rejected.repairClassId}
            style={{
              borderBottom: `1px solid ${COLOR.border}`,
              padding: "7px 2px",
              fontSize: 11,
            }}
          >
            <span style={{ color: COLOR.red }}>rejected · </span>
            <span style={{ fontFamily: FONT_MONO }}>{rejected.repairClassId}</span>
            <Dim> · {rejected.reasons.map(humanize).join(", ")}</Dim>
          </div>
        ))}
        <AuditRow label="common repair cover">
          <Pill color={receipt.commonRepairCover.coversPlausibleSet ? "green" : "slate"}>
            {receipt.commonRepairCover.coversPlausibleSet ? "covers plausible set" : "no common cover"}
          </Pill>
        </AuditRow>
        <AuditRow label="probe need">
          {receipt.probeNeed ? (
            <>
              <Pill color={receipt.probeNeed.divergent ? "amber" : "slate"}>
                {receipt.probeNeed.divergent ? "divergent repairs" : "not divergent"}
              </Pill>
              {receipt.probeNeed.incompleteRepairMapping ? (
                <Pill color="red">incomplete repair mapping</Pill>
              ) : null}
              <Dim> · {receipt.probeNeed.reason}</Dim>
            </>
          ) : (
            <>
              <span style={{ color: COLOR.amber }}>
                {humanize(receipt.probeDecision.decision)}
              </span>
              <Dim> · {receipt.probeDecision.reason}</Dim>
            </>
          )}
        </AuditRow>
        {selected?.suggestion.repairedTrace ? (
          <div style={{ marginTop: 8 }}>
            <TraceView
              trace={selected.suggestion.repairedTrace}
              label="repaired trace audit · inspector only"
            />
          </div>
        ) : null}
        {selected?.minimality.textDiff ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)",
              gap: 8,
              marginTop: 8,
            }}
          >
            <Panel tone="slate">
              <SmallLabel>observed trace · before</SmallLabel>
              <div style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
                <MarkdownMath value={selected.minimality.textDiff.before} />
              </div>
            </Panel>
            <Panel tone="green">
              <SmallLabel>minimal repair · after</SmallLabel>
              <div style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
                <MarkdownMath value={selected.minimality.textDiff.after} />
              </div>
            </Panel>
          </div>
        ) : null}
      </div>

      <div style={{ marginTop: 14 }}>
        <SmallLabel>mechanism taxonomy snapshot</SmallLabel>
        <AuditRow label="version">
          <Dim>{receipt.mechanismTaxonomyVersionId ?? "none pinned"}</Dim>
        </AuditRow>
        {receipt.mechanismTaxonomyHash ? (
          <AuditRow label="source heads">
            <Dim>{receipt.mechanismTaxonomyHash}</Dim>
          </AuditRow>
        ) : null}
        {taxonomyClusters.length || taxonomyAbstained.length ? (
          <>
        <AuditRow label="clusters">
          {taxonomyClusters.length ? (
            <span style={{ display: "grid", gap: 4 }}>
              {taxonomyClusters.map((raw, index) => {
                const cluster =
                  raw && typeof raw === "object" && !Array.isArray(raw)
                    ? raw as Record<string, unknown>
                    : {};
                return (
                  <Dim key={`${String(cluster.id ?? "cluster")}:${index}`}>
                    {String(cluster.id ?? "unnamed cluster")}
                    {cluster.support != null ? ` · support ${String(cluster.support)}` : ""}
                    {cluster.operation ? ` · ${humanize(String(cluster.operation))}` : ""}
                  </Dim>
                );
              })}
            </span>
          ) : <Dim>none earned yet</Dim>}
        </AuditRow>
        <AuditRow label="abstained groups">
          {taxonomyAbstained.length ? (
            <span style={{ display: "grid", gap: 4 }}>
              {taxonomyAbstained.map((raw, index) => {
                const group =
                  raw && typeof raw === "object" && !Array.isArray(raw)
                    ? raw as Record<string, unknown>
                    : {};
                return (
                  <Dim key={`${String(group.operation ?? "group")}:${index}`}>
                    {humanize(String(group.operation ?? "unknown operation"))}
                    {group.support != null ? ` · support ${String(group.support)}` : ""}
                  </Dim>
                );
              })}
            </span>
          ) : <Dim>none</Dim>}
        </AuditRow>
          </>
        ) : null}
      </div>
    </>
  );
}

function AuditMetric({ label, value }: { label: string; value: string | number }) {
  return (
    <div style={{ border: `1px solid ${COLOR.border}`, padding: "6px 8px" }}>
      <Faint>{label}</Faint>
      <div style={{ marginTop: 3, color: COLOR.text, fontFamily: FONT_MONO }}>{value}</div>
    </div>
  );
}
