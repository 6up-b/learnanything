// Teacher TE1b (spec_teacher_v1 §15.1, §19): the router's lesson suggestion card in Today.
//
// "Learn X now? (about 15 min)", the topic in plain words and the planner's honest reason, with Start, up to
// two alternatives and "Not now". At most one a day (the sidecar draws the day's card once and reads it back),
// and only ever this card: never a modal or a notification. The card asks for nothing while the sidecar's
// `teacher.suggestions` key is absent (the parent renders it only then), so with the switch off Today is
// exactly what it was.
import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { LessonSuggestionDto, LessonSuggestionEntryDto } from "../../api/dto";
import { getCommandError } from "../../errors";
import { COLOR, FONT_MONO } from "../../components/term";
import type { LessonEntry } from "../LessonScreen";

export function LessonSuggestionCard({
  sessionId,
  onStartLesson,
  onError
}: {
  sessionId: string | null;
  /** Opens the lesson the learner started (a TE1 lesson whose origin is this card's decision). */
  onStartLesson: (entry: LessonEntry) => void;
  onError: (message: string) => void;
}) {
  const [card, setCard] = useState<LessonSuggestionDto | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api.lessonSuggestion({ sessionId })
      .then((result) => { if (!cancelled) setCard(result.suggestion ?? null); })
      // The card is optional: a failed read shows no card and never blocks Today.
      .catch(() => undefined);
    return () => { cancelled = true; };
  }, [sessionId]);

  if (!card) return null;

  async function respond(response: "accepted" | "chose_alternative" | "declined", chosen?: LessonSuggestionEntryDto) {
    if (!card) return;
    setBusy(true);
    try {
      const result = await api.lessonSuggestionRespond({
        decisionId: card.decisionId, response, sessionId,
        ...(response === "chose_alternative" && chosen ? { candidateRef: chosen.ref } : {})
      });
      setCard(null);
      if (result.lesson) {
        onStartLesson({
          kind: "open", entry: "learning_object", learningObjectIds: result.lesson.learningObjectIds,
          title: result.lesson.title,
          suggestion: { decisionId: result.lesson.decisionId, lessonId: result.lesson.lessonId }
        });
      }
    } catch (error) {
      onError(getCommandError(error)?.message ?? String(error));
    } finally {
      setBusy(false);
    }
  }

  const { suggestion, alternatives } = card;
  return (
    <section aria-label="Suggested lesson" data-testid="lesson-suggestion-card"
             style={{ margin: "0 18px 10px", padding: "10px 12px", border: `1px solid ${COLOR.border}`,
                      background: COLOR.bgElev, fontFamily: FONT_MONO, fontSize: 13 }}>
      <div style={{ color: COLOR.text }}>
        Learn <strong>{suggestion.title}</strong> now? (about {card.minutes} min)
      </div>
      <div style={{ color: COLOR.textDim, marginTop: 4 }}>
        {suggestion.why} <span style={{ fontSize: 11 }}>· {card.whyLabel}</span>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
        <button type="button" disabled={busy} onClick={() => void respond("accepted")}>Start</button>
        {alternatives.map((alternative) => (
          <button key={alternative.ref} type="button" disabled={busy} title={alternative.why}
                  onClick={() => void respond("chose_alternative", alternative)}>
            Or: {alternative.title}
          </button>
        ))}
        <button type="button" disabled={busy} onClick={() => void respond("declined")}>Not now</button>
      </div>
    </section>
  );
}
