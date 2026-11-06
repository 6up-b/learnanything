// Teacher TE2 (spec_teacher_v1 §11.5, §11.8, §19): Today's lesson card.
//
// Each open lesson shows as "Continue your lesson on X", with "Close it" beside it (the lesson closes as
// stopped and its later checks are set, as any close does; nothing closes a lesson on a timer). Below, a quiet
// "Learn something new" opens the lesson start, where the learner types what they want to learn. Rendered only
// while the sidecar says TE2 serves (`teacher.te2`), so with the switch off Today is exactly what it was.
import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { OpenLessonDto } from "../../api/dto";
import { getCommandError } from "../../errors";
import { COLOR, FONT_MONO } from "../../components/term";
import type { LessonEntry } from "../LessonScreen";

export function ContinueLessonCard({
  onStartLesson,
  onError,
}: {
  onStartLesson: (entry: LessonEntry) => void;
  onError: (message: string) => void;
}) {
  const [lessons, setLessons] = useState<OpenLessonDto[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api.lessonOpenLessons()
      .then((result) => { if (!cancelled) setLessons(result.lessons ?? []); })
      // Optional: a failed read shows no card and never blocks Today.
      .catch(() => undefined);
    return () => { cancelled = true; };
  }, []);

  async function closeLesson(lesson: OpenLessonDto) {
    setBusy(true);
    try {
      await api.lessonTurn({ action: "close", lessonId: lesson.lessonId });
      setLessons((current) => current.filter((entry) => entry.lessonId !== lesson.lessonId));
    } catch (error) {
      onError(getCommandError(error)?.message ?? String(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-label="Your lessons" data-testid="continue-lesson-card"
             style={{ margin: "0 18px 10px", padding: "10px 12px", border: `1px solid ${COLOR.border}`,
                      background: COLOR.bgElev, fontFamily: FONT_MONO, fontSize: 13 }}>
      {lessons.map((lesson) => (
        <div key={lesson.lessonId} data-testid="continue-lesson" style={{ display: "flex", flexWrap: "wrap", gap: 8,
                                                                         alignItems: "center", marginBottom: 6 }}>
          <span style={{ color: COLOR.text }}>Continue your lesson on <strong>{lesson.title}</strong></span>
          <button type="button" disabled={busy} onClick={() => onStartLesson({ kind: "resume", lessonId: lesson.lessonId })}>
            Continue
          </button>
          <button type="button" disabled={busy} onClick={() => void closeLesson(lesson)}>Close it</button>
        </div>
      ))}
      <button type="button" data-testid="learn-something-new" disabled={busy}
              onClick={() => onStartLesson({ kind: "typed" })}>
        Learn something new
      </button>
    </section>
  );
}
