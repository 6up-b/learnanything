// The path view's Teacher lesson row (spec §12.5): under an LO, the newest lesson on it, if one exists; a click opens
// its window (its tab in the desk's stack). The lessons are read once per path opening (lesson.list, no model call).
import { useSyncExternalStore } from "react";
import type { LessonDesk } from "./host";
import { lessonTabMeta } from "./model";

export function PathLessonRow({ desk, learningObjectId, onOpen }: {
  desk: LessonDesk;
  learningObjectId: string;
  onOpen: (lessonId: string) => void;
}) {
  useSyncExternalStore(desk.subscribe, desk.getVersion);
  // Newest first, as the list comes.
  const lesson = desk.allLessons()?.find((each) => each.learningObjectIds.includes(learningObjectId)) ?? null;
  if (!lesson) return null;
  return (
    <button type="button" className="gp-alt gp-lesson" data-gp-lesson={lesson.lessonId} onClick={() => onOpen(lesson.lessonId)}>
      <span className="g">◇</span>
      <span className="gp-src">Teacher lesson</span>
      <span className="gp-at">{lesson.title}</span>
      <span className="gp-why">{lessonTabMeta(lesson)}</span>
      <span className="gp-st">{lesson.closed ? "review it" : "continue it"}</span>
    </button>
  );
}
