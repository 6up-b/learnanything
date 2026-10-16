import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { CommandError, GuidedRedoDto, ProbeBlockEndDto } from "../api/dto";
import { FIX_MIX_UP_LABEL, simplePracticeFeedback, VERDICT_TEXT, verdictOf } from "../app/practiceFeedback";
import { DetailsToggle, PrimaryAction, quietLine } from "../components/PlainParts";
import { ProbeBlockResult } from "../components/ProbeBlockResult";
import { COLOR, KeyBar } from "../components/term";
import { Card, SectionHeader } from "../components/ui";
import { MarkdownMath } from "../render/MarkdownMath";

// §5.7/§12 unified Diagnostic Check review: replaces the single-attempt
// FeedbackScreen when an attempt just closed a diagnostic block — releases
// feedback for every attempt in the block (not just the last one) and routes
// the learner on, adaptively continuing the same episode when there's more to
// measure instead of dropping back to the general queue.

const CONTINUE_LABEL: Record<string, string> = {
  tutoring: "Start tutoring session",
  next_block: "Continue diagnostic check",
  ordinary_practice: "Back to practice"
};

/** UX Phase 4.3: the route's next step in plain words. */
const PLAIN_CONTINUE_LABEL: Record<string, string> = {
  tutoring: "Learn it with the tutor",
  next_block: "A few more questions",
  ordinary_practice: "Back to practice"
};

export function DiagnosticReviewScreen({
  blockEnd,
  learningObjectId,
  learningObjectTitle,
  sessionId,
  onContinueDiagnostic,
  onAsk,
  onOpenRepair,
  onGuidedRedo,
  onBack,
  onError,
  keysSuspended = false
}: {
  blockEnd: ProbeBlockEndDto;
  learningObjectId: string;
  learningObjectTitle: string;
  sessionId: string;
  onContinueDiagnostic: (practiceItemId: string) => void;
  onAsk: (target: {
    context: "practice";
    practiceItemId: string;
    sessionId: string;
    proactiveOpen?: boolean;
  }) => void;
  /** Repair-journey entrances on released failures — App's openRepair /
   *  openGuidedRedo (both stash-and-resume the session). */
  onOpenRepair?: (misconceptionId: string) => void;
  onGuidedRedo?: (redo: GuidedRedoDto) => void;
  onBack: () => void;
  onError: (message: string) => void;
  /** An overlay over the results (the repair step) owns the keyboard (Codex
   *  review F2): ↵ and Esc never reach this screen underneath it. */
  keysSuspended?: boolean;
}) {
  const [continuing, setContinuing] = useState(false);
  // UX Phase 4.3 (§7.5): the short check's results fold into the feedback
  // flow, unless `[ui] practice_feedback = "classic"` restores the screen.
  const simple = simplePracticeFeedback();
  const [detailsOpen, setDetailsOpen] = useState(false);
  // A mix-up every released failure shares one fix for is the one next step.
  const sharedFix = onOpenRepair
    ? blockEnd.releasedFeedback.find((entry) => entry.causalFeedback?.commonRepair)?.causalFeedback?.commonRepair ?? null
    : null;

  const handleContinue = useCallback(async () => {
    if (continuing) return;
    if (blockEnd.route === "tutoring") {
      // §12.1: the typed transition decision is already persisted — the
      // tutor opens with it proactively rather than waiting on a question.
      const anchorItemId = blockEnd.releasedFeedback[0]?.practiceItemId ?? undefined;
      if (anchorItemId) {
        onAsk({ context: "practice", practiceItemId: anchorItemId, sessionId, proactiveOpen: true });
      }
      onBack();
      return;
    }
    setContinuing(true);
    try {
      // route === "next_block" (same episode continues) or "ordinary_practice"
      // (it doesn't) both resolve the same way: ask whether the episode still
      // has something to serve, and jump straight in if so.
      const next = await api.getNextProbeItem(learningObjectId);
      if (next.active && next.practiceItemId) {
        onContinueDiagnostic(next.practiceItemId);
        return;
      }
    } catch (error) {
      onError((error as CommandError).message ?? String(error));
    } finally {
      setContinuing(false);
    }
    onBack();
  }, [blockEnd, continuing, learningObjectId, onAsk, onBack, onContinueDiagnostic, onError, sessionId]);

  const runNextStep = useCallback(() => {
    if (sharedFix && onOpenRepair) {
      onOpenRepair(sharedFix.misconceptionId);
      return;
    }
    void handleContinue();
  }, [handleContinue, onOpenRepair, sharedFix]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (keysSuspended) return;
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;
      if (simple) {
        // One next step on ↵; Esc leaves; `.` toggles details.
        if (event.key === "Enter") {
          event.preventDefault();
          runNextStep();
        } else if (event.key === "Escape") {
          event.preventDefault();
          onBack();
        } else if (event.key === ".") {
          event.preventDefault();
          setDetailsOpen((open) => !open);
        }
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        void handleContinue();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handleContinue, onBack, keysSuspended, runNextStep, simple]);

  if (simple) {
    const stepLabel = sharedFix ? FIX_MIX_UP_LABEL : PLAIN_CONTINUE_LABEL[blockEnd.route ?? ""] ?? "Continue";
    return (
      <div className="screen">
        <div className="screen-scroll">
          <Card focused>
            <div style={{ fontSize: 15, color: COLOR.text }}>That's the short check done. Here's what it showed.</div>
            <div style={{ ...quietLine, marginTop: 2 }}>{learningObjectTitle}</div>
            {blockEnd.releasedFeedback.length > 0 ? (
              <div style={{ marginTop: 12, display: "grid", gap: 8 }}>
                {blockEnd.releasedFeedback.map((entry, index) => {
                  const verdict = verdictOf({
                    score: entry.rubricScore,
                    max: entry.maxPoints,
                    held: entry.heldForReview === true
                  });
                  return (
                    <div key={entry.attemptId} data-testid="check-verdict" style={{ fontSize: 13, lineHeight: 1.6 }}>
                      <span style={{ color: COLOR.textDim }}>Question {index + 1} · </span>
                      <span style={{ color: verdict === "right" ? COLOR.green : verdict === "partly" ? COLOR.amber : COLOR.text }}>
                        {VERDICT_TEXT[verdict]}
                      </span>
                      {entry.feedbackMd?.trim() && verdict !== "held" ? (
                        <div style={{ color: COLOR.textDim, fontSize: 12 }}>
                          <MarkdownMath value={entry.feedbackMd} />
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            ) : null}
            <div className="form-row" style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 10 }}>
              <PrimaryAction hotkey="↵" onClick={runNextStep} disabled={continuing}>
                {continuing ? "One moment…" : stepLabel}
              </PrimaryAction>
              <span style={{ flex: 1 }} />
              <DetailsToggle open={detailsOpen} onToggle={() => setDetailsOpen((open) => !open)} />
            </div>
            {detailsOpen ? (
              <div style={{ marginTop: 14 }}>
                <ProbeBlockResult
                  status={blockEnd.status}
                  completionReason={blockEnd.completionReason}
                  route={blockEnd.route}
                  releasedFeedback={blockEnd.releasedFeedback}
                  onOpenRepair={onOpenRepair}
                  onGuidedRedo={onGuidedRedo}
                  onError={onError}
                  simple
                />
              </div>
            ) : null}
          </Card>
        </div>
        <KeyBar keys={[
          { key: "↵", label: stepLabel.toLowerCase() },
          { key: ".", label: "details" },
          { key: "esc", label: "back" }
        ]} />
      </div>
    );
  }

  return (
    <div className="screen">
      <div className="screen-scroll">
        <SectionHeader>Diagnostic check complete</SectionHeader>
        <Card focused>
          <div style={{ fontSize: 13, marginBottom: 4 }}>
            Here's what we found for <b>{learningObjectTitle}</b> — nice work.
          </div>
          <ProbeBlockResult
            status={blockEnd.status}
            completionReason={blockEnd.completionReason}
            route={blockEnd.route}
            releasedFeedback={blockEnd.releasedFeedback}
            onOpenRepair={onOpenRepair}
            onGuidedRedo={onGuidedRedo}
            onError={onError}
          />
          <div className="form-row" style={{ marginTop: 14 }}>
            <button className="queue-row focused" type="button" disabled={continuing} onClick={() => void handleContinue()}>
              <span className="queue-hotkey">esc</span>
              <span className="queue-title">
                {continuing ? "One moment…" : CONTINUE_LABEL[blockEnd.route ?? ""] ?? "Continue"}
              </span>
            </button>
          </div>
        </Card>
      </div>
      <KeyBar keys={[{ key: "esc", label: "continue" }]} />
    </div>
  );
}
