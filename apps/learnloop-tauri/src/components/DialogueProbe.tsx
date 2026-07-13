import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { CommandError, DialogueTurnDto, ProbeBlockEndDto } from "../api/dto";
import { MarkdownMath } from "../render/MarkdownMath";
import { COLOR, FONT_MONO, Faint } from "./term";
import { Card, Pill, SectionHeader } from "./ui";

// Dialogue microprobe UI (probe redesign §8.1/§12): a short block of committed
// turns — commit → decisive reason → minimally-changed case → counterexample —
// with the exam-like measurement contract: the attempt type is forced to
// diagnostic_probe, hints/ask-tutor are unavailable, and per-turn feedback is
// withheld until the block ends (§5.6). The opaque dialogueState blob is owned
// by this client and round-tripped through every sidecar call.

const TURN_KIND_LABEL: Record<string, string> = {
  commit: "commit to an answer",
  reason: "state the decisive reason",
  counterfactual: "minimally changed case",
  counterexample: "boundary / failure case"
};

const ROUTE_LABEL: Record<string, string> = {
  tutoring: "next: tutoring on the diagnosed gap",
  next_block: "next: another short diagnostic block",
  ordinary_practice: "next: ordinary practice"
};

interface SubmittedTurn {
  kind: string;
  promptMd: string;
  answerMd: string;
}

type Phase = "starting" | "asking" | "submitting" | "ending" | "done";

export function DialogueProbePanel({
  learningObjectId,
  sessionId,
  onDone,
  onError
}: {
  learningObjectId: string;
  sessionId: string;
  /** Block finished (or failed to start): blockEnd is the §5.7 payload when one ran. */
  onDone: (blockEnd: ProbeBlockEndDto | null) => void;
  onError: (message: string) => void;
}) {
  const [phase, setPhase] = useState<Phase>("starting");
  const [turn, setTurn] = useState<DialogueTurnDto | null>(null);
  const [answer, setAnswer] = useState("");
  const [confidence, setConfidence] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState<SubmittedTurn[]>([]);
  const [blockEnd, setBlockEnd] = useState<ProbeBlockEndDto | null>(null);
  const dialogueState = useRef<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const fail = useCallback(
    (error: unknown) => {
      onError((error as CommandError).message ?? String(error));
      onDone(null);
    },
    [onError, onDone]
  );

  const endBlock = useCallback(async () => {
    if (dialogueState.current == null) {
      onDone(null);
      return;
    }
    setPhase("ending");
    try {
      const result = await api.endProbeDialogue(dialogueState.current);
      setBlockEnd(result.blockEnd);
      setPhase("done");
    } catch (error) {
      fail(error);
    }
  }, [fail, onDone]);

  const advance = useCallback(async () => {
    if (dialogueState.current == null) return;
    try {
      const next = await api.nextProbeDialogueTurn(dialogueState.current);
      dialogueState.current = next.dialogueState;
      if (next.turn == null) {
        await endBlock();
        return;
      }
      setTurn(next.turn);
      setAnswer("");
      setConfidence(null);
      setPhase("asking");
    } catch (error) {
      fail(error);
    }
  }, [endBlock, fail]);

  // Begin the block on mount. React 18 StrictMode double-mounts effects in
  // dev; the ref guard keeps the second run from opening a second block.
  const started = useRef(false);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    api
      .beginProbeDialogue(learningObjectId)
      .then((begin) => {
        dialogueState.current = begin.dialogueState;
        void advance();
      })
      .catch(fail);
  }, [learningObjectId, advance, fail]);

  useEffect(() => {
    if (phase === "asking") textareaRef.current?.focus();
  }, [phase, turn]);

  const submitTurn = useCallback(
    async (dontKnow: boolean) => {
      if (phase !== "asking" || turn == null || dialogueState.current == null) return;
      if (!dontKnow && !answer.trim()) return;
      setPhase("submitting");
      try {
        // Each turn is one committed diagnostic_probe attempt consuming the
        // turn's presentation (§5.1); grading feedback stays withheld (§5.6).
        if (dontKnow) {
          await api.submitDontKnow({
            sessionId,
            practiceItemId: turn.practiceItemId,
            hintsUsed: 0,
            probePresentationId: turn.presentationId,
            answerConfidence: confidence
          });
        } else {
          await api.submitAttempt({
            sessionId,
            practiceItemId: turn.practiceItemId,
            answerMd: answer,
            attemptType: "diagnostic_probe",
            hintsUsed: 0,
            probePresentationId: turn.presentationId,
            answerConfidence: confidence
          });
        }
        const recorded = await api.recordProbeDialogueTurn(dialogueState.current, turn.presentationId);
        dialogueState.current = recorded.dialogueState;
        setSubmitted((prior) => [
          ...prior,
          { kind: turn.kind, promptMd: turn.promptMd, answerMd: dontKnow ? "_(don't know)_" : answer }
        ]);
        setTurn(null);
        if (recorded.blockComplete) {
          await endBlock();
        } else {
          await advance();
        }
      } catch (error) {
        // e.g. §5.8: diagnostic turns need an approved AI grading provider.
        onError((error as CommandError).message ?? String(error));
        setPhase("asking");
      }
    },
    [phase, turn, answer, confidence, sessionId, advance, endBlock, onError]
  );

  // §3: Stop diagnosing and teach me — convert the episode to tutoring, then
  // close the block so unsubmitted presentations are invalidated.
  const stopAndTeach = useCallback(async () => {
    if (turn == null) {
      void endBlock();
      return;
    }
    try {
      await api.stopProbeDiagnosing(turn.practiceItemId);
    } catch (error) {
      onError((error as CommandError).message ?? String(error));
    }
    void endBlock();
  }, [turn, endBlock, onError]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey) && phase === "asking") {
        event.preventDefault();
        void submitTurn(false);
      } else if (event.key === "Escape") {
        event.preventDefault();
        if (phase === "done") onDone(blockEnd);
        else if (phase === "asking") void endBlock();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [phase, submitTurn, endBlock, onDone, blockEnd]);

  if (phase === "done") {
    return (
      <div>
        <SectionHeader>Diagnostic dialogue · results</SectionHeader>
        <Card focused>
          {blockEnd == null ? (
            <Faint>The dialogue ended without a block result.</Faint>
          ) : (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <Pill tone={blockEnd.status === "complete" ? "cyan" : "slate"}>{blockEnd.status}</Pill>
                {blockEnd.completionReason ? <Faint>{blockEnd.completionReason}</Faint> : null}
                {blockEnd.route ? (
                  <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.amber }}>
                    {ROUTE_LABEL[blockEnd.route] ?? blockEnd.route}
                  </span>
                ) : null}
              </div>
              {blockEnd.releasedFeedback.length > 0 ? (
                <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
                  <Faint>Feedback withheld during the block, released now:</Faint>
                  {blockEnd.releasedFeedback.map((feedback, index) => (
                    <div
                      key={feedback.attemptId}
                      style={{ borderTop: `1px solid ${COLOR.border}`, paddingTop: 8, fontSize: 13 }}
                    >
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <Pill tone={(feedback.rubricScore ?? 0) >= 3 ? "green" : "amber"}>
                          {feedback.rubricScore ?? "—"}/4
                        </Pill>
                        <Faint>
                          turn {index + 1}
                          {submitted[index] ? ` · ${TURN_KIND_LABEL[submitted[index].kind] ?? submitted[index].kind}` : ""}
                        </Faint>
                        {feedback.fatalErrors.length > 0 ? (
                          <span style={{ color: COLOR.red, fontFamily: FONT_MONO, fontSize: 11 }}>
                            {feedback.fatalErrors.join(", ")}
                          </span>
                        ) : null}
                      </div>
                      {feedback.feedbackMd ? (
                        <div className="markdown" style={{ marginTop: 4, fontSize: 12, lineHeight: 1.5 }}>
                          <MarkdownMath value={feedback.feedbackMd} />
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ marginTop: 10 }}>
                  <Faint>No feedback to release for this block.</Faint>
                </div>
              )}
            </>
          )}
          <div className="form-row" style={{ marginTop: 14 }}>
            <button className="queue-row focused" type="button" onClick={() => onDone(blockEnd)}>
              <span className="queue-hotkey">esc</span>
              <span className="queue-title">Continue</span>
            </button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <SectionHeader>Diagnostic dialogue</SectionHeader>
      <Card focused>
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <Pill tone="cyan">
            Diagnostic · turn {turn?.turnNumber ?? submitted.length + 1} of {turn?.plannedTurns ?? "…"}
          </Pill>
          {turn ? <Pill tone="slate">{TURN_KIND_LABEL[turn.kind] ?? turn.kind}</Pill> : null}
          <span style={{ fontSize: 12, opacity: 0.75 }}>
            Short committed answers. Feedback is delayed for measurement integrity; hints and
            ask-tutor are unavailable.
          </span>
        </div>

        {submitted.length > 0 ? (
          <div style={{ marginTop: 12, display: "grid", gap: 8 }}>
            {submitted.map((entry, index) => (
              <div key={index} style={{ fontSize: 12, opacity: 0.65 }}>
                <div className="markdown">
                  <MarkdownMath value={entry.promptMd} />
                </div>
                <div style={{ fontFamily: FONT_MONO, marginTop: 2, color: COLOR.textDim }}>
                  ▸ {entry.answerMd}
                </div>
              </div>
            ))}
          </div>
        ) : null}

        {phase === "starting" ? (
          <div style={{ marginTop: 12 }}>
            <Faint>Opening the dialogue block…</Faint>
          </div>
        ) : null}
        {phase === "ending" ? (
          <div style={{ marginTop: 12 }}>
            <Faint>Closing the block and releasing feedback…</Faint>
          </div>
        ) : null}

        {turn && (phase === "asking" || phase === "submitting") ? (
          <>
            <div className="markdown" style={{ marginTop: 12 }}>
              <MarkdownMath value={turn.promptMd} />
            </div>
            <textarea
              ref={textareaRef}
              className="self-grade-notes"
              style={{ marginTop: 10 }}
              value={answer}
              onChange={(event) => setAnswer(event.target.value)}
              placeholder="Commit to a short answer…"
              disabled={phase === "submitting"}
            />
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 8, flexWrap: "wrap" }}>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11, opacity: 0.85 }}>
                <Faint>confidence</Faint>
                {[1, 2, 3, 4, 5].map((level) => (
                  <button
                    key={level}
                    type="button"
                    className="queue-row"
                    style={{ padding: "0 6px", fontFamily: FONT_MONO, opacity: confidence === level ? 1 : 0.45 }}
                    onClick={() => setConfidence(confidence === level ? null : level)}
                    title="how confident are you in your answer? (optional, 1 = guessing, 5 = certain)"
                  >
                    {level}
                  </button>
                ))}
              </span>
              <button
                className="queue-row focused"
                type="button"
                disabled={phase === "submitting" || !answer.trim()}
                onClick={() => void submitTurn(false)}
              >
                <span className="queue-hotkey">⌃↵</span>
                <span className="queue-title">{phase === "submitting" ? "Submitting…" : "Commit answer"}</span>
              </button>
              <button
                className="queue-row"
                type="button"
                disabled={phase === "submitting"}
                onClick={() => void submitTurn(true)}
              >
                <span className="queue-title">Don't know</span>
              </button>
              <button
                className="queue-row"
                type="button"
                style={{ marginLeft: "auto" }}
                disabled={phase === "submitting"}
                onClick={() => void stopAndTeach()}
              >
                <span className="queue-title">Stop diagnosing and teach me</span>
              </button>
            </div>
          </>
        ) : null}
      </Card>
    </div>
  );
}
