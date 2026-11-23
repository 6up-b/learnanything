// A Teacher lesson whose medium is a marimo notebook, in its lesson window (spec §11.2). The notebook is the
// lesson's own, read-only as the teacher made it (marimo's app view), served by the lesson's sandboxed session
// (owner `lesson:<id>`, so a desk move or a remount rejoins the same kernel; a paused window polls nothing).
//
// Its commit points hold cells: when the learner answers one (a value on the commit point's own control, which the
// sidecar sees on its way to the kernel), this releases the cells it holds through `notebook.release`. The sidecar
// refuses any other release. A finished lesson's notebook is its review: nothing is committed or released, and
// nothing is recorded. The learner's additions go to the lesson's additions pad, never into the notebook: the
// frame's right-click opens the pad menu labelled "the lesson" (notebook/menuBridge).
import { useCallback, useRef, useState } from "react";
import { api } from "../../../api/client";
import type { LessonViewDto, NotebookSessionDto } from "../../../api/dto";
import { NotebookFrame, type NotebookApi } from "./NotebookFrame";

/** How often a ready lesson notebook is read while a commit point waits for the learner (its reveal follows the
 * answer within this). keep: display polling, not a parameter. */
export const COMMIT_POLL_MS = 750;

export interface LessonNotebookApi extends NotebookApi {
  notebookRelease(input: { sessionId: string; cells: string[] }): Promise<unknown>;
}

/** The held cells the learner's commits have unlocked and that are not released yet (none in a review). */
export function lessonReleases(session: NotebookSessionDto | null): string[] {
  const lesson = session?.lesson;
  if (!lesson || lesson.review || session.state !== "ready") return [];
  const released = new Set(lesson.released);
  return lesson.commitPoints.filter((point) => point.committed).flatMap((point) => point.held).filter((name) => !released.has(name));
}

/** Whether a commit point still holds cells for an answer (the frame then reads its session more often). */
export function waitingOnCommit(session: NotebookSessionDto | null): boolean {
  const lesson = session?.lesson;
  return Boolean(lesson && !lesson.review && lesson.commitPoints.some((point) => !point.committed && point.held.length > 0));
}

export interface LessonNotebookProps {
  lessonId: string;
  view: LessonViewDto;
  /** Overrides the sidecar's calls (tests). */
  calls?: LessonNotebookApi;
}

export function LessonNotebook({ lessonId, view, calls = api }: LessonNotebookProps) {
  const [problem, setProblem] = useState<string | null>(null);
  const inFlight = useRef(new Set<string>());

  const onSession = useCallback((next: NotebookSessionDto) => {
    const cells = lessonReleases(next).filter((name) => !inFlight.current.has(name));
    if (cells.length === 0) return;
    for (const name of cells) inFlight.current.add(name);
    calls.notebookRelease({ sessionId: next.sessionId, cells })
      .then(() => setProblem(null))
      .catch((reason: unknown) => {
        const message = reason && typeof reason === "object" && "message" in reason ? String((reason as { message: unknown }).message) : String(reason);
        setProblem(`the answer's reveal didn't show: ${message}`);
      })
      .finally(() => {
        for (const name of cells) inFlight.current.delete(name);
      });
  }, [calls]);

  const review = view.closed;
  return (
    <div className="ll-lesson-nb" data-lesson-notebook={lessonId} data-review={review ? "on" : "off"}>
      {review ? <div className="ll-lesson-nb-line">review · the notebook as the teacher made it · nothing new is revealed or recorded</div> : null}
      {problem ? <div className="ll-lesson-nb-line" role="status">{problem}</div> : null}
      <NotebookFrame
        owner={`lesson:${lessonId}`}
        view="app"
        title={view.goal ?? "Teacher lesson"}
        calls={calls}
        onSession={onSession}
        readyPoll={commitPoll}
      />
    </div>
  );
}

/** Read a lesson notebook more often while a commit point waits for the learner. */
function commitPoll(session: NotebookSessionDto): number | undefined {
  return waitingOnCommit(session) ? COMMIT_POLL_MS : undefined;
}

/** The desks' `lessons.notebookFrame`: a notebook lesson's frame in its lesson window. */
export function lessonNotebookFrame(lessonId: string, view: LessonViewDto) {
  return <LessonNotebook lessonId={lessonId} view={view} />;
}
