// Diagnosis-adjudication overlay (spec_tauri_ui §3, `command="adjudicate"`;
// spec_diagnostic_augmentation_v1 §2 A4).
//
// The supply step for the adjudication store: one case at a time, judged
// against what the learner was actually shown. The verdict vocabulary is
// PARTITIONED — the four filled verdicts are recordable only against a
// diagnosis that named a cause, the two abstention verdicts only against an
// abstention — and this screen never derives that partition itself. Every case
// arrives carrying the `allowedVerdicts` the store will accept for it, so an
// impossible verdict is not rendered rather than rendered and refused.
//
// After a verdict, the line under the header is whatever §5.6 arm (d) reported
// through `outcome` — a promotion, a withdrawal, or "no belief change" with the
// reason. It is never inferred from the verdict: an affirming verdict on an
// ambiguous cause set promotes nothing, and saying otherwise would be a lie the
// backend never told.

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type {
  AdjudicationCaseDto,
  AdjudicationOutcomeDto,
  AdjudicationQueueDto,
  AdjudicationRecordInput,
  AdjudicationScoreboardDto,
  AdjudicationVerdict
} from "../api/dto";
import { CommandOverlayFrame, commandOverlayActionStyle } from "./CommandOverlayFrame";
import { isTypingTarget } from "../app/keyboard";
import { Card, COLOR, Dim, Divider, Faint, FONT_MONO, Pill, SectionHeader } from "./term";
import { errorMessage } from "../errors";

const STRATUM_LABEL: Record<string, string> = {
  learner_contest: "from a learner contest",
  system_abstention: "the system abstained",
  anchor_disagreement: "candidates disagreed on the anchor",
  incomplete_repair_mapping: "a named cause had no repair class",
  sampled: "unflagged sample",
  manual: "picked by hand"
};

const VERDICT_KEY: Record<AdjudicationVerdict, string> = {
  correct: "c",
  wrong_anchor: "a",
  wrong_repair: "r",
  should_have_abstained: "s",
  correctly_abstained: "c",
  should_not_have_abstained: "n"
};

const VERDICT_LABEL: Record<AdjudicationVerdict, string> = {
  correct: "correct",
  wrong_anchor: "wrong anchor",
  wrong_repair: "wrong repair",
  should_have_abstained: "should have abstained",
  correctly_abstained: "correctly abstained",
  should_not_have_abstained: "should not have abstained"
};

const VERDICT_GLOSS: Record<AdjudicationVerdict, string> = {
  correct: "the anchor and the repair were both right",
  wrong_anchor: "the divergence is somewhere else",
  wrong_repair: "right place, wrong fix",
  should_have_abstained: "no cause should have been named",
  correctly_abstained: "naming a cause here was not possible",
  should_not_have_abstained: "the cause was nameable and the system ducked it"
};

// Verdicts that carry their own evidence and therefore open a form instead of
// recording on the keystroke. `correct` and `wrong_repair` inherit the system's
// anchor (both assert it was right); `should_not_have_abstained` cannot inherit
// one, because a system that abstained produced none.
const ANCHOR_FORM_VERDICTS: AdjudicationVerdict[] = ["wrong_anchor", "should_not_have_abstained"];
const REPAIR_FORM_VERDICTS: AdjudicationVerdict[] = ["wrong_anchor", "wrong_repair"];

const ANCHOR_KINDS = ["span", "between_spans", "missing_required_step", "whole_answer", "none"] as const;

type Draft = {
  verdict: AdjudicationVerdict;
  anchorKind: string;
  criterionId: string;
  quote: string;
  checkpointId: string;
  repairMd: string;
  repairClassId: string;
  rationale: string;
};

function newDraft(verdict: AdjudicationVerdict, kase: AdjudicationCaseDto): Draft {
  return {
    verdict,
    anchorKind: "span",
    criterionId: String(kase.systemAnchor?.criterionId ?? ""),
    quote: "",
    checkpointId: "",
    repairMd: "",
    repairClassId: "",
    rationale: ""
  };
}

function rate(value: number | null | undefined): string {
  return value == null ? "—" : value.toFixed(2);
}

export function AdjudicationOverlay({
  onClose,
  onError
}: {
  onClose: () => void;
  onError: (message: string) => void;
}) {
  const [queue, setQueue] = useState<AdjudicationQueueDto | null>(null);
  const [board, setBoard] = useState<AdjudicationScoreboardDto | null>(null);
  const [index, setIndex] = useState(0);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [result, setResult] = useState<
    { attemptId: string; verdict: AdjudicationVerdict; outcome: AdjudicationOutcomeDto } | null
  >(null);

  const refreshBoard = useCallback(() => {
    api
      .adjudicationScoreboard("none")
      .then(setBoard)
      .catch(() => setBoard(null));
  }, []);

  useEffect(() => {
    let alive = true;
    api
      .adjudicationQueue({ limit: 50 })
      .then((result) => {
        if (alive) setQueue(result);
      })
      .catch((error: unknown) => {
        if (!alive) return;
        const message = errorMessage(error, "Could not load the adjudication queue.");
        setLoadError(message);
        onError(message);
      });
    refreshBoard();
    return () => {
      alive = false;
    };
  }, [onError, refreshBoard]);

  const cases = queue?.cases ?? [];
  const kase: AdjudicationCaseDto | null = cases[index] ?? null;

  const strata = useMemo(
    () => (queue?.countsByReason ?? []).filter((row) => row.count > 0),
    [queue]
  );

  const advance = useCallback(
    (drop: boolean) => {
      setDraft(null);
      setFormError(null);
      if (drop) {
        setQueue((current) =>
          current === null
            ? current
            : {
                ...current,
                total: Math.max(0, current.total - 1),
                cases: current.cases.filter((_, position) => position !== index)
              }
        );
        setIndex((position) => Math.min(position, Math.max(0, cases.length - 2)));
        return;
      }
      setIndex((position) => (cases.length === 0 ? 0 : (position + 1) % cases.length));
    },
    [cases.length, index]
  );

  const submit = useCallback(
    (input: AdjudicationRecordInput) => {
      setBusy(true);
      setFormError(null);
      api
        .adjudicationRecord(input)
        .then((recorded) => {
          setResult({
            attemptId: input.attemptId,
            verdict: input.verdict,
            outcome: recorded.outcome
          });
          refreshBoard();
          advance(true);
        })
        .catch((error: unknown) => {
          const message = errorMessage(error, "Could not record this adjudication.");
          setFormError(message);
          onError(message);
        })
        .finally(() => setBusy(false));
    },
    [advance, onError, refreshBoard]
  );

  const chooseVerdict = useCallback(
    (verdict: AdjudicationVerdict) => {
      if (!kase || busy) return;
      if (ANCHOR_FORM_VERDICTS.includes(verdict) || verdict === "wrong_repair") {
        setDraft(newDraft(verdict, kase));
        setFormError(null);
        return;
      }
      // `correct`, `should_have_abstained`, `correctly_abstained`: the verdict
      // is the whole record. The store inherits the system's own anchor and
      // repair for `correct`, which is exactly what `correct` asserts.
      submit({ attemptId: kase.attemptId, verdict });
    },
    [busy, kase, submit]
  );

  function submitDraft() {
    if (!kase || draft === null) return;
    const anchorRequired = ANCHOR_FORM_VERDICTS.includes(draft.verdict);
    if (anchorRequired && draft.anchorKind === "missing_required_step" && !draft.checkpointId.trim()) {
      setFormError("A missing_required_step anchor needs the checkpoint it names.");
      return;
    }
    if (draft.verdict === "wrong_repair" && !draft.repairMd.trim() && !draft.repairClassId) {
      setFormError("‘wrong repair’ needs the repair that should have been chosen.");
      return;
    }
    submit({
      attemptId: kase.attemptId,
      verdict: draft.verdict,
      anchor: anchorRequired
        ? {
            anchorKind: draft.anchorKind,
            criterionId: draft.criterionId.trim(),
            quote: draft.quote.trim() || null,
            checkpointId: draft.checkpointId.trim() || null
          }
        : null,
      repairMd: draft.repairMd.trim() || null,
      repairClassId: draft.repairClassId || null,
      rationale: draft.rationale.trim() || null
    });
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLElement>) {
    if (event.key === "Escape") {
      if (draft !== null) {
        setDraft(null);
        setFormError(null);
        return;
      }
      onClose();
      return;
    }
    // Single-keystroke verdicts are live only while no form is open; once a
    // verdict needs typed evidence, the keyboard belongs to the form.
    if (draft !== null || busy || !kase) return;
    if (event.metaKey || event.ctrlKey || event.altKey || isTypingTarget(event.target)) return;
    const key = event.key.toLowerCase();
    if (key === "k") {
      advance(false);
      return;
    }
    const match = kase.allowedVerdicts.find((verdict) => VERDICT_KEY[verdict] === key);
    if (match) {
      event.preventDefault();
      chooseVerdict(match);
    }
  }

  const overall = board?.overall;
  const badge = overall ? (
    <Pill color={overall.records > 0 ? "amber" : "slate"}>{overall.records} verdicts</Pill>
  ) : (
    <Pill color="slate">loading</Pill>
  );

  return (
    <CommandOverlayFrame
      command="adjudicate"
      context={kase ? kase.attemptId : "diagnosis queue"}
      badge={badge}
      onClose={onClose}
      onKeyDown={onKeyDown}
      focusOnMount
      width="min(1040px, 100%)"
      ariaLabel="Diagnosis adjudication"
      footerKeys={
        kase && draft === null ? (
          <>
            {kase.allowedVerdicts.map((verdict) => (
              <span key={verdict}>
                <span style={{ color: COLOR.text }}>{VERDICT_KEY[verdict]}</span> {VERDICT_LABEL[verdict]}
              </span>
            ))}
            <span>
              <span style={{ color: COLOR.text }}>k</span> skip
            </span>
            <span>
              <span style={{ color: COLOR.text }}>esc</span> close
            </span>
          </>
        ) : (
          <span>
            <span style={{ color: COLOR.text }}>esc</span> {draft === null ? "close" : "cancel"}
          </span>
        )
      }
      footerRight={<span>command palette · <Dim>learnloop diagnosis adjudicate</Dim></span>}
    >
      <div
        className="ll-scroll"
        style={{
          padding: "14px 22px 18px",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 12,
          fontFamily: FONT_MONO,
          fontSize: 13
        }}
      >
        {/* Running tally. Rates read `—`, never a flattering 1.0, when the
            denominator is empty — the scoreboard refuses to invent one. */}
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "baseline" }}>
          <span style={{ color: COLOR.textDim, fontSize: 12 }}>
            anchor accuracy <span style={{ color: COLOR.text }}>{rate(overall?.firstDivergenceAnchorAccuracy)}</span>
          </span>
          <span style={{ color: COLOR.textDim, fontSize: 12 }}>
            abstention precision <span style={{ color: COLOR.text }}>{rate(overall?.abstentionPrecision)}</span>
          </span>
          <span style={{ color: COLOR.textDim, fontSize: 12 }}>
            abstention recall <span style={{ color: COLOR.text }}>{rate(overall?.abstentionRecall)}</span>
          </span>
          {overall && !overall.abstentionCasesPresent ? (
            <Faint style={{ fontSize: 12 }}>no abstention case adjudicated yet</Faint>
          ) : null}
          <span style={{ flex: 1 }} />
          <span style={{ color: COLOR.textDim, fontSize: 12 }}>
            {cases.length === 0 ? "queue empty" : `case ${index + 1} of ${cases.length}`}
            {queue && queue.total > cases.length ? ` · ${queue.total} owed` : ""}
          </span>
        </div>

        {strata.length > 0 ? (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {strata.map((row) => (
              <Pill key={row.reason} color={row.reason === kase?.queueReason ? "amber" : "slate"}>
                {row.reason.replace(/_/g, " ")} {row.count}
              </Pill>
            ))}
          </div>
        ) : null}

        {result ? (
          <Card
            status={result.outcome.status === "no_belief_change" ? "neutral" : "done"}
            style={{ display: "flex", gap: 10, alignItems: "baseline", flexWrap: "wrap" }}
          >
            <span style={{ color: COLOR.green }}>recorded</span>
            <Dim>{result.attemptId}</Dim>
            <span style={{ color: COLOR.amber }}>{VERDICT_LABEL[result.verdict]}</span>
            <span style={{ color: COLOR.text }}>{result.outcome.message}</span>
          </Card>
        ) : null}

        {loadError ? <Card status="error">{loadError}</Card> : null}

        {!loadError && queue === null ? <Faint>loading the queue…</Faint> : null}

        {queue !== null && kase === null ? (
          <Card status="neutral">
            <div style={{ color: COLOR.text }}>No attempts are awaiting a diagnosis verdict.</div>
            <Faint style={{ fontSize: 12 }}>
              Contested diagnoses and abstentions enter this queue first; an unflagged `sampled`
              stratum keeps the eval set from being purely adversarially selected.
            </Faint>
          </Card>
        ) : null}

        {kase ? (
          <>
            <div style={{ display: "flex", gap: 10, alignItems: "baseline", flexWrap: "wrap" }}>
              <Pill color={kase.queueReason === "learner_contest" ? "pink" : "purple"}>
                {STRATUM_LABEL[kase.queueReason] ?? kase.queueReason.replace(/_/g, " ")}
              </Pill>
              <Faint style={{ fontSize: 12 }}>{kase.detail}</Faint>
              {kase.systemAbstained ? <Pill color="cyan">abstained</Pill> : null}
              {kase.anchorDisagreement ? <Pill color="amber">anchor disagreement</Pill> : null}
              {kase.incompleteRepairMapping ? <Pill color="amber">no repair class</Pill> : null}
            </div>

            <SectionHeader style={{ marginTop: 4 }}>What the learner was told</SectionHeader>
            <Card status="neutral" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {kase.shownToLearner.feedbackMd ? (
                <div style={{ color: COLOR.text, whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
                  {kase.shownToLearner.feedbackMd}
                </div>
              ) : (
                <Faint>no feedback sentence was recorded for this attempt</Faint>
              )}
              {kase.shownToLearner.hypotheses.map((hypothesis, position) => (
                <div key={hypothesis.hypothesisId ?? position} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <Faint style={{ fontSize: 12 }}>{hypothesis.label ?? "possible explanation"}</Faint>
                  <span style={{ color: COLOR.text }}>{hypothesis.statement}</span>
                  {hypothesis.traceConsistency ? (
                    <Faint style={{ fontSize: 12 }}>trace {hypothesis.traceConsistency}</Faint>
                  ) : null}
                </div>
              ))}
              {kase.shownToLearner.proposedNextAction?.rationale ? (
                <div style={{ color: COLOR.textDim }}>
                  <Faint style={{ fontSize: 12 }}>proposed next action</Faint>{" "}
                  {kase.shownToLearner.proposedNextAction.rationale}
                </div>
              ) : null}
              {!kase.shownToLearner.rendered ? (
                <Faint style={{ fontSize: 12 }}>
                  the receipt did not permit a learner-facing causal overlay, so no diagnosis prose was shown
                </Faint>
              ) : null}
            </Card>

            <SectionHeader>The learner’s work</SectionHeader>
            <Card status="neutral" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {kase.prompt ? (
                <div style={{ color: COLOR.textDim, whiteSpace: "pre-wrap", lineHeight: 1.6 }}>{kase.prompt}</div>
              ) : null}
              <Divider />
              <div style={{ color: COLOR.text, whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
                {kase.learnerAnswerMd || <Faint>no answer text recorded</Faint>}
              </div>
              <Faint style={{ fontSize: 12 }}>
                {kase.learningObjectTitle ?? kase.learningObjectId ?? "—"} · {kase.practiceItemId ?? "—"} ·{" "}
                {kase.rubricScore == null ? "unscored" : `score ${kase.rubricScore}`}
              </Faint>
            </Card>

            <SectionHeader>What the system claimed</SectionHeader>
            <Card status="attention" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {kase.systemAbstained ? (
                <div style={{ color: COLOR.text }}>
                  named no cause · <Dim>{kase.abstentionBasis.replace(/_/g, " ")}</Dim>
                </div>
              ) : (
                <>
                  <div style={{ color: COLOR.text }}>
                    <Faint style={{ fontSize: 12 }}>first divergence</Faint>{" "}
                    {String(kase.systemAnchor?.anchorKind ?? "none")}
                    {kase.systemAnchor?.criterionId ? ` · ${String(kase.systemAnchor.criterionId)}` : ""}
                  </div>
                  {kase.systemAnchor?.quote ? (
                    <div style={{ color: COLOR.amber }}>“{String(kase.systemAnchor.quote)}”</div>
                  ) : null}
                  <div style={{ color: COLOR.text }}>
                    <Faint style={{ fontSize: 12 }}>repair class</Faint> {kase.systemRepairClassId ?? "—"}
                  </div>
                </>
              )}
              {kase.learnerReport ? (
                <Faint style={{ fontSize: 12 }}>
                  learner reported “{String(kase.learnerReport.response ?? "")}” — evidence, never the verdict
                </Faint>
              ) : null}
            </Card>

            {draft === null ? (
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 4 }}>
                {kase.allowedVerdicts.map((verdict) => (
                  <button
                    key={verdict}
                    type="button"
                    disabled={busy}
                    onClick={() => chooseVerdict(verdict)}
                    style={verdictButtonStyle}
                    title={VERDICT_GLOSS[verdict]}
                  >
                    <span style={{ color: COLOR.amber }}>{VERDICT_KEY[verdict]}</span> {VERDICT_LABEL[verdict]}
                  </button>
                ))}
                <button type="button" disabled={busy} onClick={() => advance(false)} style={verdictButtonStyle}>
                  <span style={{ color: COLOR.amber }}>k</span> skip
                </button>
              </div>
            ) : (
              <Card status="probe" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ color: COLOR.text }}>
                  {VERDICT_LABEL[draft.verdict]} — <Faint style={{ fontSize: 12 }}>{VERDICT_GLOSS[draft.verdict]}</Faint>
                </div>
                {ANCHOR_FORM_VERDICTS.includes(draft.verdict) ? (
                  <>
                    <Faint style={{ fontSize: 12 }}>where the answer first diverges</Faint>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {ANCHOR_KINDS.map((kind) => (
                        <button
                          key={kind}
                          type="button"
                          onClick={() => setDraft({ ...draft, anchorKind: kind })}
                          style={{
                            ...verdictButtonStyle,
                            borderColor: draft.anchorKind === kind ? COLOR.amber : COLOR.border,
                            color: draft.anchorKind === kind ? COLOR.text : COLOR.textDim
                          }}
                        >
                          {kind.replace(/_/g, " ")}
                        </button>
                      ))}
                    </div>
                    <input
                      value={draft.criterionId}
                      onChange={(event) => setDraft({ ...draft, criterionId: event.target.value })}
                      placeholder="criterion id"
                      style={inputStyle}
                    />
                    <input
                      value={draft.quote}
                      onChange={(event) => setDraft({ ...draft, quote: event.target.value })}
                      placeholder="verbatim span from the learner’s answer (optional)"
                      style={inputStyle}
                    />
                    {draft.anchorKind === "missing_required_step" ? (
                      <input
                        value={draft.checkpointId}
                        onChange={(event) => setDraft({ ...draft, checkpointId: event.target.value })}
                        placeholder="checkpoint id (required for a missing step)"
                        style={inputStyle}
                      />
                    ) : null}
                  </>
                ) : null}
                {REPAIR_FORM_VERDICTS.includes(draft.verdict) ? (
                  <>
                    <Faint style={{ fontSize: 12 }}>
                      the minimal repair — a class only if this episode offered it, otherwise prose
                    </Faint>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {kase.repairClassOptions.map((option) => (
                        <button
                          key={option.id}
                          type="button"
                          onClick={() =>
                            setDraft({
                              ...draft,
                              repairClassId: draft.repairClassId === option.id ? "" : option.id
                            })
                          }
                          style={{
                            ...verdictButtonStyle,
                            borderColor: draft.repairClassId === option.id ? COLOR.amber : COLOR.border,
                            color: draft.repairClassId === option.id ? COLOR.text : COLOR.textDim
                          }}
                        >
                          {option.operator ?? option.id}
                        </button>
                      ))}
                    </div>
                    <textarea
                      value={draft.repairMd}
                      onChange={(event) => setDraft({ ...draft, repairMd: event.target.value })}
                      placeholder="the repair that should have been chosen"
                      rows={2}
                      style={{ ...inputStyle, resize: "vertical" }}
                    />
                  </>
                ) : null}
                <textarea
                  value={draft.rationale}
                  onChange={(event) => setDraft({ ...draft, rationale: event.target.value })}
                  placeholder="rationale (optional)"
                  rows={2}
                  style={{ ...inputStyle, resize: "vertical" }}
                />
                {formError ? <div style={{ color: COLOR.red }}>{formError}</div> : null}
                <div style={{ display: "flex", gap: 12 }}>
                  <button type="button" disabled={busy} onClick={submitDraft} style={commandOverlayActionStyle}>
                    record verdict
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => {
                      setDraft(null);
                      setFormError(null);
                    }}
                    style={{ ...commandOverlayActionStyle, color: COLOR.textDim }}
                  >
                    cancel
                  </button>
                </div>
              </Card>
            )}

            {formError && draft === null ? <div style={{ color: COLOR.red }}>{formError}</div> : null}

            <Faint style={{ fontSize: 11, lineHeight: 1.7 }}>
              A verdict is full authority: it names the anchor and the repair, and it is appended, never
              overwritten. The learner’s ⚑ contest is bounded evidence linked as provenance — it never sets
              the verdict. Only the verdicts this case can take are shown; the store enforces the same
              partition.
            </Faint>
          </>
        ) : null}
      </div>
    </CommandOverlayFrame>
  );
}

const verdictButtonStyle: React.CSSProperties = {
  fontFamily: FONT_MONO,
  fontSize: 12,
  background: "transparent",
  color: COLOR.text,
  border: `1px solid ${COLOR.border}`,
  borderRadius: 2,
  padding: "5px 10px",
  cursor: "pointer"
};

const inputStyle: React.CSSProperties = {
  fontFamily: FONT_MONO,
  fontSize: 12,
  background: COLOR.bgInput,
  color: COLOR.text,
  border: `1px solid ${COLOR.border}`,
  borderRadius: 2,
  padding: "6px 8px",
  width: "100%"
};
