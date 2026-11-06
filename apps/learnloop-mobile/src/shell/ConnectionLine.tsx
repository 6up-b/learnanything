// One quiet line under the title for the connection (mobile v2 §4.4), never a modal. Most
// important first: a stale app, then no desktop, then a busy one, then grading down.
import { useConnection } from "./connection";
import { reloadApp } from "./freshness";

export const UPDATED_LINE = "LearnLoop was updated.";
export const BUSY_LINE = "Desktop is busy — trying again.";
export const GRADING_LINE = "Grading isn't available right now. Your answer is saved.";

export function offlineLine(waiting: number): string {
  const queued = waiting > 0 ? ` ${waiting} ${waiting === 1 ? "capture" : "captures"} waiting to send.` : "";
  return `Desktop offline. Capture still works.${queued}`;
}

export function ConnectionLine({ outboxWaiting }: { outboxWaiting: number }) {
  const state = useConnection();
  if (state.stale) {
    return (
      <div className="line" role="status">
        <span>{UPDATED_LINE}</span>
        <button className="link" type="button" onClick={() => void reloadApp()}>Reload</button>
      </div>
    );
  }
  if (state.offline) return <div className="line" role="status">{offlineLine(outboxWaiting)}</div>;
  if (state.busy) return <div className="line" role="status">{BUSY_LINE}</div>;
  if (state.gradingDown) return <div className="line" role="status">{GRADING_LINE}</div>;
  return null;
}
