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
import { COLOR, Dim, Faint, FONT_MONO, Pill, PlainEnglishPanel, SectionHeader } from "./term";
import { RepairTraceBlocks } from "./RepairTrace";

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

/** Panel-internal field label. Tracking matches the app-wide uppercase
 * micro-label idiom (0.10em — ItemPresentation, SqliteBrowser, TrackRecordView);
 * `tone` lets a label inside a toned Panel agree with its border instead of
 * staying faint while a block nested below it renders louder. */
function SmallLabel({ children, tone = COLOR.textFaint }: { children: ReactNode; tone?: string }) {
  return (
    <div
      style={{
        color: tone,
        fontFamily: FONT_MONO,
        fontSize: 10,
        letterSpacing: "0.1em",
        marginBottom: 5,
        textTransform: "uppercase",
      }}
    >
      {children}
    </div>
  );
}

// One rank above SmallLabel. The receipt is a three-level document — section
// header, group, panel label — but the group tier used to render in the same
// 10px faint style as the panel tier, so the before/after diff nested inside
// `repair decision` read as its peer rather than its child. Amber at 0.12em is
// the app's heading eyebrow (ClaimSurface, RepairScreen, QuickAddDialog);
// SmallLabel keeps the faint field-label role it shares with the rest of the app.
function GroupHeader({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        color: COLOR.amber,
        fontFamily: FONT_MONO,
        fontSize: 11,
        letterSpacing: "0.12em",
        marginBottom: 8,
        textTransform: "uppercase",
      }}
    >
      {children}
    </div>
  );
}

/** A group inside the inspector receipt. The hairline carries the break that
 * whitespace could not: a 14px group gap against an 8px intra-group gap did not
 * read as a boundary across a section this long. */
function AuditGroup({ label, children }: { label: ReactNode; children: ReactNode }) {
  return (
    <div style={{ marginTop: 20, borderTop: `1px solid ${COLOR.border}`, paddingTop: 12 }}>
      <GroupHeader>{label}</GroupHeader>
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
      <SmallLabel tone={COLOR.green}>{label}</SmallLabel>
      <RepairTraceBlocks trace={trace} preservedLabel="preserved learner work" repairLabel="the repair" />
    </Panel>
  );
}

/** Where the two traces stop agreeing. The cut snaps back to a line break (or a
 * word boundary) so each side stays independently parseable as markdown —
 * splitting mid-list or mid-`$…$` would render as garbage rather than as a diff.
 * Backing up to the start of the line also means the whole changed line lights
 * up on both sides, which is what a line-based diff shows anyway. `shared` is
 * identical in both traces by construction, so either may supply it. */
function splitDivergence(
  before: string,
  after: string,
): { shared: string; removed: string; added: string } {
  const limit = Math.min(before.length, after.length);
  let common = 0;
  while (common < limit && before[common] === after[common]) common += 1;
  if (common === before.length && common === after.length) {
    return { shared: before, removed: "", added: "" };
  }
  const newline = after.lastIndexOf("\n", common);
  const space = after.lastIndexOf(" ", common);
  // Clamped to `common`: when the traces diverge exactly at a line break the
  // snap-back would otherwise land one past it and eat the newline, silently
  // fusing the last preserved line onto the first repaired one.
  const cut = Math.min(newline >= 0 ? newline + 1 : space > 0 ? space + 1 : 0, common);
  return { shared: before.slice(0, cut), removed: before.slice(cut), added: after.slice(cut) };
}

/** Label/value row *inside* a Panel. AuditRow's 148px column and rules are the
 * group-level idiom and read as a table; within a panel the same relationship
 * needs to stay subordinate to the panel's own prose. Faint label against a dim
 * value gives a scan column, which four consecutive `·`-joined dim runs did not. */
function PanelRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "108px minmax(0, 1fr)",
        gap: 8,
        fontSize: 11,
        lineHeight: 1.5,
        marginTop: 3,
      }}
    >
      <Faint>{label}</Faint>
      <Dim style={{ minWidth: 0, overflowWrap: "anywhere" }}>{children}</Dim>
    </div>
  );
}

/** Provenance footer for a panel: identifiers, versions, supersession — true but
 * never the point, so it sits below a rule rather than between the claim and the
 * analysis of it. */
function PanelFooter({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        marginTop: 9,
        paddingTop: 7,
        borderTop: `1px solid ${COLOR.border}`,
        fontFamily: FONT_MONO,
        fontSize: 10,
        color: COLOR.textFaint,
        overflowWrap: "anywhere",
      }}
    >
      {children}
    </div>
  );
}

/** The band bleeds into the Panel's own padding by exactly its border plus its
 * left padding, so highlighted text stays on the same left edge as the shared
 * text above it. Inset instead, the band shifted its content 10px right and a
 * single continuous numbered list visibly stepped sideways at the split — the
 * highlight has to mark the text without moving it. */
function DiffBlock({ accent, wash, children }: { accent: string; wash: string; children: ReactNode }) {
  return (
    <div
      className="md-tight"
      style={{
        background: wash,
        borderLeft: `2px solid ${accent}`,
        padding: "4px 8px",
        marginTop: 6,
        marginLeft: -10,
        marginRight: -10,
      }}
    >
      {children}
    </div>
  );
}

/** Side-by-side minimal repair. The repaired answer is composed server-side as
 * the learner's preserved prefix plus a regenerated continuation, so the point
 * where `after` stops matching `before` splits both traces at once: everything
 * past it in `before` is what the repair discarded, everything past it in
 * `after` is the repair itself. Washing the two tails red and green is the same
 * signal RepairTraceBlocks already uses for the regenerated half, rather than
 * leaving the reader to find the divergence in two walls of prose. */
function MinimalRepairDiff({ before, after }: { before: string; after: string }) {
  const { shared, removed, added } = splitDivergence(before, after);
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)",
        gap: 8,
        marginTop: 12,
      }}
    >
      <Panel tone="slate">
        <SmallLabel>observed trace · before</SmallLabel>
        <div
          className="md-tight"
          // `pre-wrap` also preserves runs of spaces, so any indented source
          // line rendered indented on top of markdown's own block layout —
          // whitespace handled twice. `pre-line` keeps the intentional line
          // breaks and drops the phantom indent.
          style={{ fontSize: 12, lineHeight: 1.5, whiteSpace: "pre-line", overflowWrap: "anywhere" }}
        >
          {shared ? <MarkdownMath value={shared} /> : null}
          {removed ? (
            <DiffBlock accent={COLOR.red} wash={COLOR.washRed}>
              <MarkdownMath value={removed} />
            </DiffBlock>
          ) : null}
        </div>
      </Panel>
      <Panel tone="green">
        <SmallLabel tone={COLOR.green}>minimal repair · after</SmallLabel>
        <div
          className="md-tight"
          // `pre-wrap` also preserves runs of spaces, so any indented source
          // line rendered indented on top of markdown's own block layout —
          // whitespace handled twice. `pre-line` keeps the intentional line
          // breaks and drops the phantom indent.
          style={{ fontSize: 12, lineHeight: 1.5, whiteSpace: "pre-line", overflowWrap: "anywhere" }}
        >
          {shared ? <MarkdownMath value={shared} /> : null}
          {added ? (
            <DiffBlock accent={COLOR.green} wash={COLOR.washGreen}>
              <MarkdownMath value={added} />
            </DiffBlock>
          ) : null}
        </div>
      </Panel>
    </div>
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
  const graderFeedback = feedback.unverified.filter(
    (claim) => claim.kind === "grader_feedback",
  );
  const nonHypothesisUnverified = feedback.unverified.filter(
    (claim) => claim.kind !== "causal_hypothesis" && claim.kind !== "grader_feedback",
  );
  const correctionRemainsUnverified =
    graderFeedback.length > 0 && feedback.verifiedCorrection === null;
  const hasUnverifiedClaims =
    nonHypothesisUnverified.length > 0 ||
    feedback.causalHypotheses.length > 0 ||
    correctionRemainsUnverified;
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

      {graderFeedback.length ? (
        <PlainEnglishPanel label="grader feedback" style={{ marginBottom: 8 }}>
          {graderFeedback.map((claim, index) => {
            const statement = claim.statement?.trim();
            return (
              <div
                key={`${statement ?? "no-written-feedback"}:${index}`}
                style={{
                  borderTop: index ? `1px solid ${COLOR.border}` : "none",
                  marginTop: index ? 7 : 0,
                  paddingTop: index ? 7 : 0,
                }}
              >
                {statement ? (
                  <MarkdownMath value={statement} />
                ) : (
                  <Dim>The grader did not provide additional written feedback for this submission.</Dim>
                )}
              </div>
            );
          })}
        </PlainEnglishPanel>
      ) : null}

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

      <Panel tone="slate" style={{ marginTop: 8 }}>
        <SmallLabel>what remains unverified after this submission</SmallLabel>
        {nonHypothesisUnverified.map((claim, index) => {
          const statement = claim.statement?.trim();
          return (
            <div
              key={`${claim.kind}:${claim.hypothesisId ?? index}`}
              style={{ marginTop: index ? 8 : 0, lineHeight: 1.55 }}
            >
              <Pill color="slate">{humanize(claim.kind)}</Pill>
              <div style={{ marginTop: 5 }}>
                {statement ? (
                  <MarkdownMath value={statement} />
                ) : (
                  <Dim>
                    The grader marked this part of your submitted answer as unverified,
                    but did not provide any further detail.
                  </Dim>
                )}
              </div>
            </div>
          );
        })}
        {feedback.causalHypotheses.length ? (
          <div style={{ marginTop: nonHypothesisUnverified.length ? 8 : 0 }}>
            <Dim>
              This attempt showed where your answer first diverged, but it did not
              establish why. The possible explanations above remain unconfirmed.
            </Dim>
          </div>
        ) : null}
        {correctionRemainsUnverified ? (
          <div
            style={{
              marginTop:
                nonHypothesisUnverified.length || feedback.causalHypotheses.length ? 8 : 0,
            }}
          >
            <Dim>
              The grader identified what to revisit, but this submission did not
              verify a corrected answer. A later checked attempt is needed to
              confirm the repair.
            </Dim>
          </div>
        ) : null}
        {!hasUnverifiedClaims ? (
          <Dim>No additional claims from this submission are still marked as unverified.</Dim>
        ) : null}
      </Panel>

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

      <AuditGroup label="criterion outcomes">
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
      </AuditGroup>

      <AuditGroup label="three divergence anchors">
        {([
          ["first_observable_divergence", receipt.divergenceAnchors.firstObservableDivergence],
          ["earliest_supported_faulty_commitment", receipt.divergenceAnchors.earliestSupportedFaultyCommitment],
          ["repair_insertion_point", receipt.divergenceAnchors.repairInsertionPoint],
        ] as const).map(([name, anchor]) => (
          <AuditRow key={name} label={ANCHOR_LABELS[name] ?? humanize(name)}>
            <Dim>{formatDivergenceAnchor(anchor)}</Dim>
          </AuditRow>
        ))}
      </AuditGroup>

      <AuditGroup label="candidate causes and evidence">
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
                {/* The claim is what the panel is for; everything under it is
                    apparatus. It was previously set at the same weight as its
                    own metadata. */}
                <div style={{ marginTop: 7, fontSize: 13, color: COLOR.text, lineHeight: 1.55 }}>
                  <MarkdownMath value={hypothesis.statement} />
                </div>
                <div style={{ marginTop: 8 }}>
                  <PanelRow label="resolution">{humanize(axis?.resolutionStatus)}</PanelRow>
                  <PanelRow label="target">
                    {formatCausalTarget(axis?.targetRef ?? hypothesis.targetRef)}
                  </PanelRow>
                  {hypothesis.operation ? (
                    <PanelRow label="operation">{humanize(hypothesis.operation)}</PanelRow>
                  ) : null}
                  {hypothesis.mechanism ? (
                    <PanelRow label="mechanism">{humanize(hypothesis.mechanism)}</PanelRow>
                  ) : null}
                  {evidence ? <PanelRow label="evidence">{evidence}</PanelRow> : null}
                  {errorType ? <PanelRow label="error">{humanize(errorType)}</PanelRow> : null}
                  {severity != null ? (
                    <PanelRow label="severity">
                      <span style={{ fontFamily: FONT_MONO }}>{severity.toFixed(2)}</span>
                    </PanelRow>
                  ) : null}
                  {applicabilitySurface ? (
                    <PanelRow label="surface">{humanize(applicabilitySurface)}</PanelRow>
                  ) : null}
                  {observedSignature ? (
                    <PanelRow label="observed sig">{observedSignature}</PanelRow>
                  ) : null}
                  {preregisteredSignature ? (
                    <PanelRow label="pre-registered">{preregisteredSignature}</PanelRow>
                  ) : null}
                  {hypothesis.postdictiveClaims.length ? (
                    <PanelRow label="postdictive">
                      {hypothesis.postdictiveClaims
                        .map((claim) => {
                          const criterion =
                            typeof claim.criterionId === "string" ? claim.criterionId : null;
                          const must = typeof claim.must === "string" ? humanize(claim.must) : null;
                          return [criterion, must].filter(Boolean).join(" must ");
                        })
                        .filter(Boolean)
                        .join(" · ")}
                    </PanelRow>
                  ) : null}
                </div>
                <PanelFooter>
                  {hypothesis.id} · v{hypothesis.version}
                  {hypothesis.supersedesId ? ` · supersedes ${hypothesis.supersedesId}` : ""}
                </PanelFooter>
              </Panel>
            );
          })}
        </div>
      </AuditGroup>

      <AuditGroup label="repair decision">
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
              <div style={{ marginTop: 7, fontSize: 13, color: COLOR.text, lineHeight: 1.55 }}>
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
            <div style={{ marginTop: 9 }}>
              <PanelRow label="targets">
                {selected.repairClass.targetRefs.map(formatCausalTarget).join(" · ") || "none"}
              </PanelRow>
              <PanelRow label="preserves">
                {selected.repairClass.preserveRefs.map(formatCausalTarget).join(" · ") || "none"}
              </PanelRow>
              {selected.minimality.preservedCriteria.length ? (
                <PanelRow label="preserved">
                  {selected.minimality.preservedCriteria.join(" · ")}
                </PanelRow>
              ) : null}
              {selected.minimality.changedLatentClaims.length ? (
                <PanelRow label="changed claims">
                  {selected.minimality.changedLatentClaims.join(" · ")}
                </PanelRow>
              ) : null}
              {selected.minimality.changedTraceSteps.length ? (
                <PanelRow label="changed steps">
                  {selected.minimality.changedTraceSteps.join(" · ")}
                </PanelRow>
              ) : null}
            </div>
            <PanelFooter>{selected.repairClass.id}</PanelFooter>
          </Panel>
        ) : (
          <Panel tone="red">
            <Dim>No safe structural repair was selected.</Dim>
          </Panel>
        )}
        {/* The group is four distinct things — the decision, the alternatives it
            beat, the coverage verdict, and the trace evidence. Under one group
            header they ran together as an undifferentiated column. */}
        {receipt.repairSelection.rejected.length ? (
          <div style={{ marginTop: 12 }}>
            <SmallLabel>rejected alternatives</SmallLabel>
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
          </div>
        ) : null}
        <div style={{ marginTop: 12 }}>
          <SmallLabel>coverage and probe need</SmallLabel>
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
        </div>
        {selected?.suggestion.repairedTrace || selected?.minimality.textDiff ? (
          <div style={{ marginTop: 12 }}>
            {/* "inspector only" is an answer-reveal boundary, not a caption — it
                does not belong at the faintest size on the screen, and it scopes
                the whole sub-block rather than the trace panel alone. */}
            <div style={{ display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}>
              <SmallLabel>trace evidence</SmallLabel>
              <Pill color="amber">inspector only</Pill>
            </div>
            {selected.suggestion.repairedTrace ? (
              <TraceView trace={selected.suggestion.repairedTrace} label="repaired trace audit" />
            ) : null}
            {selected.minimality.textDiff ? (
              <MinimalRepairDiff
                before={selected.minimality.textDiff.before}
                after={selected.minimality.textDiff.after}
              />
            ) : null}
          </div>
        ) : null}
      </AuditGroup>

      <AuditGroup label="mechanism taxonomy snapshot">
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
      </AuditGroup>
    </>
  );
}

/** Stat tile, one rank below InspectorOverlay's `Stat` (11px label / 14px value)
 * because it sits two panels deeper. Both parts previously inherited the 13px
 * body size, so the tile had no internal hierarchy at all — the label read as
 * loud as the number it captions, and the pair read louder than the panel prose
 * above it. Faint 10 against mono 12 puts the measurement on top where it
 * belongs and pulls the whole grid back under the rationale. */
function AuditMetric({ label, value }: { label: string; value: string | number }) {
  return (
    <div style={{ border: `1px solid ${COLOR.border}`, padding: "5px 7px" }}>
      <Faint style={{ fontSize: 10, display: "block", lineHeight: 1.3 }}>{label}</Faint>
      <div style={{ marginTop: 2, fontSize: 12, color: COLOR.text, fontFamily: FONT_MONO }}>{value}</div>
    </div>
  );
}
