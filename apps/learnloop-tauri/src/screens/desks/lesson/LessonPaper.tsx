// A Teacher lesson as a pad in a stack (spec §11.1): "a pad like any other", yours to keep. Above the lesson, its
// mode buttons (review, or "lesson" while it is open, and "your additions"); then the lesson itself, LessonView in
// its window frame (or, for a notebook lesson, RD9b's frame through the host's seam); then the learner's own notes
// under it, a `lesson_additions` pad written through RD4's pad ops (the stack renders those blocks, so every pad
// insert, edit and menu works there).
//
// A finished lesson reopened is its review: LessonView reads it with lesson.view only, so nothing is regenerated,
// no model is called and nothing new is written.
import { useCallback, useState, type ReactNode } from "react";
import type { LessonViewDto } from "../../../api/dto";
import { LessonView, type LessonEntry } from "../../LessonView";
import type { LessonsHost } from "./host";
import { lessonMedium, modeButtons, modeLine, type LessonMode } from "./model";

export interface LessonPaperProps {
  host: LessonsHost;
  /** The stack item's key (an opening's until its lesson exists). */
  itemKey: string;
  lessonId: string | null;
  entry: LessonEntry;
  /** The learner's notes under the lesson (the stack renders the additions pad's blocks and its "write here" line). */
  additions: ReactNode;
  /** Whether the additions pad has anything in it (shown under the lesson in review too, then). */
  hasAdditions: boolean;
}

export function LessonPaper({ host, itemKey, lessonId, entry, additions, hasAdditions }: LessonPaperProps) {
  const [mode, setMode] = useState<LessonMode>("lesson");
  const [view, setView] = useState<LessonViewDto | null>(null);
  const { desk } = host;
  const onView = useCallback((next: LessonViewDto) => {
    setView(next);
    if (!lessonId) desk.opened(itemKey, next.lessonId);
    else desk.noteView(lessonId, next);
  }, [desk, itemKey, lessonId]);
  const closed = Boolean(view?.closed ?? (lessonId ? desk.summary(lessonId)?.closed : false));
  const shownId = lessonId ?? view?.lessonId ?? null;
  const notebook = view && shownId && lessonMedium(view) === "notebook" && host.notebookFrame ? host.notebookFrame(shownId, view) : null;
  return (
    <div className="lessonnb" data-lesson-paper={shownId ?? itemKey}>
      <div className="lhead">
        <span className="lg">◇</span>
        <span className="lt">Teacher lesson <span className="faint">· yours to keep, like your other pads</span></span>
        {!shownId && !view ? (
          // An opening that failed outright has no lesson to show: the learner lets its tab go.
          <button type="button" className="lclose" onClick={() => desk.dropOpening(itemKey)}>let it go</button>
        ) : null}
      </div>
      <div className="lmodes" role="group" aria-label="lesson modes">
        {modeButtons(closed).map((button) => (
          <button key={button.mode} type="button" className={mode === button.mode ? "on" : ""} aria-pressed={mode === button.mode}
                  data-lmode={button.mode} onClick={() => setMode(button.mode)} disabled={button.mode === "additions" && !shownId}>
            {button.label}
          </button>
        ))}
        <span className="lmd">{modeLine(mode, closed)}</span>
      </div>
      {/* Folded, not unmounted, under "your additions": a reply being written or a turn in flight stays as it was. */}
      <div className="lframe" hidden={mode !== "lesson"}>
        {notebook ?? (
          <LessonView
            entry={entry}
            frame="window"
            onView={onView}
            onError={host.onError}
            {...(host.onQuickCheck ? { onQuickCheck: host.onQuickCheck } : {})}
            {...(host.onLookInLibrary ? { onLookInLibrary: host.onLookInLibrary } : {})}
            onStartFresh={(learningObjectIds) => host.openLesson({ kind: "open", entry: "learning_object", learningObjectIds })}
          />
        )}
      </div>
      {mode === "lesson" && !hasAdditions ? null : (
        <div className="laddl">
          <div className="lah">{mode === "additions" ? "your additions under this lesson · the lesson stays as the teacher made it" : "your additions under this lesson"}</div>
          {additions}
        </div>
      )}
    </div>
  );
}
