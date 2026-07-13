import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { CalibrationSessionProgressDto, CommandError } from "../api/dto";
import { DialogueProbePanel } from "../components/DialogueProbe";
import { BlockBar, COLOR, FONT_MONO, Faint, KeyBar } from "../components/term";
import { Card, Pill, SectionHeader } from "../components/ui";

// Calibration session progress (probe redesign §5.9): a learner-initiated
// wrapper that batches diagnostic episode blocks in one sitting. This screen
// shows the plan (blocks completed of planned, elapsed vs the time budget,
// per-episode observation counts) and hands off to the ordinary practice
// screen for the adaptively-selected next target item. It pre-empts the tab
// body like the exam overlay, and remounts (→ refreshes) whenever the learner
// returns from a practice/feedback round.

const SESSION_TONE: Record<string, string> = {
  active: "green",
  completed: "cyan",
  stopped: "amber",
  expired: "red"
};

const EPISODE_TONE: Record<string, string> = {
  in_progress: "green",
  complete: "cyan",
  converted_to_tutoring: "amber",
  abandoned: "red"
};

function minutes(value: number): string {
  return `${value.toFixed(1)}m`;
}

export function CalibrationScreen({
  calibrationSessionId,
  onPractice,
  onExit,
  onError
}: {
  calibrationSessionId: string;
  onPractice: (practiceItemId: string) => void;
  onExit: () => void;
  onError: (message: string) => void;
}) {
  const [progress, setProgress] = useState<CalibrationSessionProgressDto | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [stopping, setStopping] = useState(false);
  // §8.1: an in-flight dialogue microprobe block on the next target's LO.
  const [dialogueLo, setDialogueLo] = useState<string | null>(null);

  const refresh = useCallback(() => {
    api
      .getCalibrationSession(calibrationSessionId)
      .then((snap) => {
        setProgress(snap);
        setErrorMessage(null);
      })
      .catch((error) => setErrorMessage((error as CommandError).message));
  }, [calibrationSessionId]);

  // Refresh on mount and whenever the window regains focus. Returning from a
  // practice round remounts this screen, so progress is always current.
  useEffect(() => {
    refresh();
    const onFocus = () => refresh();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [refresh]);

  const nextTarget = progress?.status === "active" ? progress.nextTarget : null;

  const stop = useCallback(async () => {
    if (stopping || !progress || progress.status !== "active") return;
    setStopping(true);
    try {
      setProgress(await api.stopCalibrationSession(calibrationSessionId));
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setStopping(false);
    }
  }, [stopping, progress, calibrationSessionId, onError]);

  useEffect(() => {
    if (dialogueLo != null) return; // the dialogue panel owns the keyboard
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;
      if (event.key === "Escape") {
        event.preventDefault();
        onExit();
      } else if (event.key === "Enter" && nextTarget) {
        event.preventDefault();
        onPractice(nextTarget.practiceItemId);
      } else if (event.key.toLowerCase() === "d" && !event.ctrlKey && !event.metaKey && !event.altKey && nextTarget) {
        event.preventDefault();
        setDialogueLo(nextTarget.learningObjectId);
      } else if (event.key.toLowerCase() === "s" && !event.ctrlKey && !event.metaKey && !event.altKey) {
        event.preventDefault();
        void stop();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [dialogueLo, nextTarget, onExit, onPractice, stop]);

  if (errorMessage) {
    return (
      <div className="screen">
        <div className="screen-scroll">
          <SectionHeader>Calibration session</SectionHeader>
          <Card>
            <div style={{ color: COLOR.red, marginBottom: 10 }}>{errorMessage}</div>
            <button className="queue-row focused" type="button" onClick={onExit}>
              <span className="queue-hotkey">esc</span>
              <span className="queue-title">Back to today</span>
            </button>
          </Card>
        </div>
        <KeyBar keys={[{ key: "esc", label: "today" }]} />
      </div>
    );
  }

  if (!progress) {
    return (
      <div className="screen">
        <div className="screen-scroll">
          <Card>Loading calibration progress…</Card>
        </div>
        <KeyBar keys={[{ key: "esc", label: "today" }]} />
      </div>
    );
  }

  if (dialogueLo != null) {
    return (
      <div className="screen">
        <div className="screen-scroll">
          <DialogueProbePanel
            learningObjectId={dialogueLo}
            sessionId={progress.sessionId}
            onDone={() => {
              setDialogueLo(null);
              refresh();
            }}
            onError={onError}
          />
        </div>
        <KeyBar
          keys={[
            { key: "⌃↵", label: "commit answer" },
            { key: "esc", label: "end dialogue" }
          ]}
        />
      </div>
    );
  }

  const budgetFraction =
    progress.timeBudgetMinutes > 0
      ? Math.min(progress.elapsedMinutes / progress.timeBudgetMinutes, 1)
      : 0;

  return (
    <div className="screen">
      <div className="screen-scroll">
        <SectionHeader>Calibration session</SectionHeader>
        <Card focused>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <Pill tone={SESSION_TONE[progress.status] ?? "slate"}>{progress.status}</Pill>
            <span style={{ fontFamily: FONT_MONO, color: COLOR.amber }}>
              {progress.blocksCompleted}/{progress.blocksPlanned} blocks
            </span>
            {progress.goalId ? <Faint>goal {progress.goalId}</Faint> : <Faint>open episodes</Faint>}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 10, fontFamily: FONT_MONO, fontSize: 12 }}>
            <BlockBar value={budgetFraction} width={16} />
            <span style={{ color: COLOR.textDim }}>
              {minutes(progress.elapsedMinutes)} of {minutes(progress.timeBudgetMinutes)}
            </span>
            <Faint>{minutes(progress.remainingMinutes)} left</Faint>
          </div>
          {progress.status === "active" ? (
            nextTarget ? (
              <div className="form-row" style={{ marginTop: 16, display: "grid", gap: 4 }}>
                <button
                  className="queue-row focused"
                  type="button"
                  onClick={() => onPractice(nextTarget.practiceItemId)}
                >
                  <span className="queue-hotkey">↵</span>
                  <span className="queue-title">Practice next target · {nextTarget.practiceItemId}</span>
                  <span className="queue-score" />
                </button>
                <button
                  className="queue-row"
                  type="button"
                  onClick={() => setDialogueLo(nextTarget.learningObjectId)}
                >
                  <span className="queue-hotkey">d</span>
                  <span className="queue-title">Diagnostic dialogue · {nextTarget.learningObjectId}</span>
                  <span className="queue-score" />
                </button>
              </div>
            ) : (
              <div style={{ marginTop: 14 }}>
                <Faint>no runnable target right now — all planned blocks are done or parked</Faint>
              </div>
            )
          ) : (
            <div style={{ marginTop: 14, fontFamily: FONT_MONO, fontSize: 13, color: COLOR.textDim }}>
              {progress.status === "completed"
                ? "All planned blocks completed."
                : progress.status === "expired"
                  ? "Time budget exhausted — the session expired."
                  : "Calibration stopped."}
            </div>
          )}
          {nextTarget ? (
            <div className="queue-meta" style={{ marginTop: 8 }}>
              <Faint>
                {nextTarget.learningObjectId} · {nextTarget.selectionObjective}
                {nextTarget.entropy != null ? ` · entropy ${nextTarget.entropy.toFixed(2)} nats` : ""}
              </Faint>
            </div>
          ) : null}
        </Card>

        <SectionHeader>Episodes</SectionHeader>
        <Card>
          {progress.episodes.length === 0 ? (
            <Faint>no episodes planned</Faint>
          ) : (
            <div style={{ display: "grid", gap: 2 }}>
              {progress.episodes.map((episode) => (
                <div
                  key={episode.episodeId}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr auto auto",
                    gap: 10,
                    alignItems: "center",
                    fontSize: 12,
                    fontFamily: FONT_MONO,
                    padding: "4px 0",
                    borderTop: `1px solid ${COLOR.border}`
                  }}
                >
                  <span style={{ overflowWrap: "anywhere", color: COLOR.text }}>
                    {episode.learningObjectId}
                    {nextTarget?.episodeId === episode.episodeId ? (
                      <span style={{ color: COLOR.amber }}> ◀ next</span>
                    ) : null}
                  </span>
                  <span style={{ color: COLOR.textDim, textAlign: "right" }}>
                    {episode.qualifyingObservations}/{episode.maximumObservations} obs
                  </span>
                  <Pill tone={EPISODE_TONE[episode.status] ?? "slate"}>{episode.status}</Pill>
                </div>
              ))}
            </div>
          )}
        </Card>

        <div className="form-row" style={{ marginTop: 18, display: "flex", gap: 10 }}>
          {progress.status === "active" ? (
            <button className="queue-row" type="button" onClick={() => void stop()} disabled={stopping}>
              <span className="queue-hotkey">s</span>
              <span className="queue-title">{stopping ? "Stopping…" : "Stop calibrating"}</span>
            </button>
          ) : null}
          <button className="queue-row" type="button" onClick={onExit}>
            <span className="queue-hotkey">esc</span>
            <span className="queue-title">Back to today</span>
          </button>
        </div>
      </div>
      <KeyBar
        keys={[
          ...(nextTarget
            ? [
                { key: "↵", label: "practice next target" },
                { key: "d", label: "diagnostic dialogue" }
              ]
            : []),
          { key: "esc", label: "today" }
        ]}
      />
    </div>
  );
}
