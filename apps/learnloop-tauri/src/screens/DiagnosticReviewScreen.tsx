import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { CommandError, GuidedRedoDto, ProbeBlockEndDto } from "../api/dto";
import { ProbeBlockResult } from "../components/ProbeBlockResult";
import { KeyBar } from "../components/term";
import { Card, SectionHeader } from "../components/ui";

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
  onError
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
}) {
  const [continuing, setContinuing] = useState(false);

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

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        void handleContinue();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handleContinue]);

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
