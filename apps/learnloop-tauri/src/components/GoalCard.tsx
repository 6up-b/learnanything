// UX Phase 3 (docs/specs/ux_learnloop_v1.md §7.1 "Goals", §10 3.4): a goal
// as one card under Today's plan, in plain words --
// "Probability midterm · 14 Nov · on track" -- with Practise for this goal and,
// when its held-out exam is ready, Practice exam. GoalBanner's numbers, the
// track record and the forecasts are behind details ▸ (the banner itself,
// unchanged). The standing reads the banner's own rule (statusOf), so the
// card and the banner can never disagree.
import { useEffect, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type { ExamStatusSnapshot, GoalDto } from "../api/dto";
import { GoalBanner, statusOf } from "./GoalBanner";
import { COLOR, FONT_MONO } from "./term";

const STANDING_WORDS: Record<string, string> = {
  "ON TRACK": "on track",
  "CLOSING IN": "getting there",
  BEHIND: "needs more practice"
};

/** "on track", "getting there" or "needs more practice"; null with no report. */
export function goalStanding(goal: GoalDto): string | null {
  const report = goal.report;
  if (!report || report.total <= 0) return null;
  const attainment = report.attainmentFraction ?? report.onTrackFraction ?? null;
  if (attainment === null) return null;
  return STANDING_WORDS[statusOf(attainment).label] ?? null;
}

/** "14 Nov", or null for an open-ended goal. */
export function goalDate(goal: GoalDto): string | null {
  if (!goal.dueAt) return null;
  const at = Date.parse(goal.dueAt);
  if (Number.isNaN(at)) return null;
  return new Date(at).toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

const link: CSSProperties = {
  border: 0,
  background: "transparent",
  color: COLOR.amberLink,
  cursor: "pointer",
  fontFamily: FONT_MONO,
  fontSize: 12,
  padding: 0
};

const action: CSSProperties = {
  padding: "4px 12px",
  border: `1px solid ${COLOR.border}`,
  background: "transparent",
  color: COLOR.text,
  cursor: "pointer",
  fontFamily: FONT_MONO,
  fontSize: 12
};

export function GoalCard({
  goal,
  onPractise,
  onTakeExam,
  onGoalChanged,
  onNewGoal,
  onError
}: {
  goal: GoalDto;
  onPractise: (goal: GoalDto) => void;
  onTakeExam?: (goalId: string) => void;
  onGoalChanged: () => void;
  onNewGoal: () => void;
  onError: (message: string) => void;
}) {
  const [details, setDetails] = useState(false);
  const [exam, setExam] = useState<ExamStatusSnapshot | null>(null);
  useEffect(() => {
    if (!onTakeExam || !goal.exam.enabled) {
      setExam(null);
      return;
    }
    let cancelled = false;
    Promise.resolve()
      .then(() => api.getExamStatus(goal.id))
      .then((snapshot) => {
        if (!cancelled) setExam(snapshot ?? null);
      })
      .catch(() => {
        // The exam is offered only when its status reads ready.
        if (!cancelled) setExam(null);
      });
    return () => {
      cancelled = true;
    };
  }, [goal.id, goal.exam.enabled, onTakeExam]);

  const parts = [goal.title, goalDate(goal), goalStanding(goal)].filter(Boolean);
  const examReady = Boolean(onTakeExam && exam && exam.poolItemCount > 0);
  return (
    <div data-testid="goal-card" style={{ border: `1px solid ${COLOR.border}`, padding: "10px 14px", display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ fontSize: 13, color: COLOR.text }}>{parts.join(" · ")}</div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <button type="button" style={action} onClick={() => onPractise(goal)}>
          Practise for this goal
        </button>
        {examReady && onTakeExam ? (
          <button type="button" style={action} onClick={() => onTakeExam(goal.id)}>
            Practice exam
          </button>
        ) : null}
        <button type="button" style={link} aria-expanded={details} onClick={() => setDetails((open) => !open)}>
          details {details ? "▾" : "▸"}
        </button>
      </div>
      {details ? (
        <div data-testid="goal-card-details">
          <GoalBanner
            goals={[goal]}
            onError={onError}
            onPracticeAtRisk={() => onPractise(goal)}
            onTakeExam={onTakeExam}
            onNewGoal={onNewGoal}
            onGoalChanged={onGoalChanged}
          />
        </div>
      ) : null}
    </div>
  );
}
