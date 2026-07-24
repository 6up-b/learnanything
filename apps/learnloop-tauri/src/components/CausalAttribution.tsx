import type { CSSProperties, ReactNode } from "react";
import type {
  CausalDivergenceAnchorDto,
  CausalEpisodeDto,
  CausalFeedbackDto,
  CausalHypothesisDto,
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

export function CausalFeedbackPanel({
  feedback,
  onContest,
  contestPending = false,
}: {
  feedback: CausalFeedbackDto;
  onContest?: (
    reason: UnresolvedCauseSelfReportResponse,
    factorId: string | null,
  ) => void;
  contestPending?: boolean;
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
        <AuditRow label="probe decision">
          <span style={{ color: COLOR.amber }}>{humanize(receipt.probeDecision.decision)}</span>
          <Dim> · {receipt.probeDecision.reason}</Dim>
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
