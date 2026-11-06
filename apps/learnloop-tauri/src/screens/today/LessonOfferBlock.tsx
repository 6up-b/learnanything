// Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): a lesson offer, a block of today's plan.
//
// "Learn X now? (about 15 min)", the topic in plain words and the planner's honest reason, with Start, up to two
// other topics and "Not now". Start opens the lesson (the plan goes on at its next block when the lesson closes);
// "Not now" goes straight on to the block the plan would have served. Only ever this block of the plan: never a
// modal or a notification, and never during a check (the sidecar offers it only at a block boundary). The answer
// goes through the TE1b response the Today card uses (`lesson.suggestion_respond`, on this block's own decision).
import { useState } from "react";
import { api } from "../../api/client";
import type { LessonSuggestionEntryDto, PlanLessonOfferDto } from "../../api/dto";
import { getCommandError } from "../../errors";
import { COLOR, FONT_MONO } from "../../components/term";
import type { LessonEntry } from "../LessonScreen";

export function LessonOfferBlock({
  offer,
  sessionId,
  onStartLesson,
  onAnswered,
  onError
}: {
  offer: PlanLessonOfferDto;
  sessionId: string | null;
  /** Opens the lesson the learner started (a TE1 lesson whose origin is this block's decision). */
  onStartLesson?: (entry: LessonEntry) => void;
  /** The plan moves on (its next block is chosen): re-read it. */
  onAnswered: () => void;
  onError: (message: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  if (!offer.decisionId || offer.answered) return null;

  async function respond(response: "accepted" | "chose_alternative" | "declined", chosen?: LessonSuggestionEntryDto) {
    if (!offer.decisionId) return;
    setBusy(true);
    try {
      const result = await api.lessonSuggestionRespond({
        decisionId: offer.decisionId, response, sessionId,
        ...(response === "chose_alternative" && chosen ? { candidateRef: chosen.ref } : {})
      });
      onAnswered();
      if (result.lesson && onStartLesson) {
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

  const { suggestion, alternatives } = offer;
  return (
    <section aria-label="A lesson you could take now" data-testid="lesson-offer-block"
             style={{ padding: "10px 12px", border: `1px solid ${COLOR.border}`, background: COLOR.bgElev,
                      fontFamily: FONT_MONO, fontSize: 13 }}>
      <div style={{ color: COLOR.text }}>
        Learn <strong>{suggestion.title}</strong> now? (about {offer.minutes} min)
      </div>
      <div style={{ color: COLOR.textDim, marginTop: 4 }}>
        {suggestion.why} <span style={{ fontSize: 11 }}>· {offer.whyLabel}</span>
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
