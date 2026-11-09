// Instruct hand-off IH6 (spec_instruct_handoff_v1 §7b): the plan view while a read holds its boundary for an open workbench.
// The learner can always get out of it from here: resume the problem, set it aside, or go on with the plan's own Begin or
// Continue, which decides at once and leaves the problem open.
import { useState, type CSSProperties } from "react";
import { api } from "../../api/client";
import type { PlanQuestionInProgressDto } from "../../api/dto";
import { rereadPlanAfterWorkbenchClosed } from "../../app/dailyPlan";
import { errorMessage } from "../../errors";
import { COLOR, FONT_MONO } from "../../components/term";

const link: CSSProperties = {
  border: 0,
  background: "transparent",
  color: COLOR.amberLink,
  cursor: "pointer",
  fontFamily: FONT_MONO,
  fontSize: 12,
  padding: 0
};

export function QuestionInProgress({
  question,
  onResume,
  onError
}: {
  question: PlanQuestionInProgressDto;
  /** Absent: this surface has no way to open it (a Reader problem from the classic Today). */
  onResume?: () => void;
  onError: (message: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  async function setAside() {
    setBusy(true);
    try {
      await api.workbenchAbandon({ sessionId: question.workbenchSessionId });
      rereadPlanAfterWorkbenchClosed();
    } catch (error) {
      onError(errorMessage(error, "Couldn't set this problem aside."));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div data-testid="question-in-progress-actions" style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
      {onResume ? (
        <button type="button" style={link} disabled={busy} onClick={onResume}>
          resume ▸
        </button>
      ) : null}
      <button type="button" style={{ ...link, color: COLOR.textDim }} disabled={busy} onClick={() => void setAside()}>
        set it aside
      </button>
    </div>
  );
}
