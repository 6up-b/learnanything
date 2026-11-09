// Instruct hand-off IH1 (spec_instruct_handoff_v1 §4): the full page feedback's Next opens when the plan's next step
// is a lesson offer. Before this the step fell through to Today, where the card was one element among others and the
// learner may never have seen it.
//
// The sentence is fixed: "This looks like something to learn. Start a {minutes} minute lesson on {topic}?" with the
// offer's own duration (already rounded for display by the sidecar) and its topic's title. Under it, the router's own
// words, but only a model's rationale when its guard let it through (`whyKind === "model_written"`); otherwise the
// plain reason for the lesson. Start answers the offer's own decision and opens the lesson at once, in one tap;
// nothing else ever starts a lesson. Never a modal, and nothing on it starts anything by itself.
import type { PlanLessonOfferStepDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import type { LessonEntry } from "../LessonScreen";
import { useLessonOfferActions, useOfferShown, type OfferResponse } from "./LessonOfferBlock";

/** The page's one sentence, kept in one place so the wording is pinned by a test. */
export function offerSentence(minutes: number, topic: string): string {
  return `This looks like something to learn. Start a ${minutes} minute lesson on ${topic}?`;
}

export function LessonOfferPage({
  step,
  sessionId,
  onStartLesson,
  onAnswered,
  onError
}: {
  step: PlanLessonOfferStepDto;
  sessionId: string | null;
  /** Opens the lesson the learner started (a TE1 lesson whose origin is this block's decision). */
  onStartLesson?: (entry: LessonEntry) => void;
  /** The offer was answered: the plan goes on (or, after Start, the lesson has opened). */
  onAnswered: (response: OfferResponse) => void;
  onError: (message: string) => void;
}) {
  const offer = step.offer;
  const { busy, respond } = useLessonOfferActions({ offer, sessionId, onStartLesson, onAnswered, onError });
  useOfferShown(offer, "offer_page", sessionId);

  const { suggestion, alternatives } = offer;
  const rationale = step.whyKind === "model_written" && step.why ? step.why : null;
  return (
    <section aria-label="A lesson you could take now" data-testid="lesson-offer-page"
             style={{ display: "flex", flexDirection: "column", gap: 14, maxWidth: 640, margin: "48px auto",
                      padding: "0 16px", fontFamily: FONT_MONO, color: COLOR.text }}>
      <div data-testid="lesson-offer-sentence" style={{ fontSize: 18, lineHeight: 1.5 }}>
        {offerSentence(offer.minutes, suggestion.title)}
      </div>
      <div data-testid="lesson-offer-reason" style={{ fontSize: 13, color: COLOR.textDim, lineHeight: 1.5 }}>
        {rationale ?? suggestion.why} <span style={{ fontSize: 11 }}>· {offer.whyLabel}</span>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        <button type="button" disabled={busy} onClick={() => void respond("accepted")}>Start</button>
        <button type="button" disabled={busy} onClick={() => void respond("declined")}>Not now</button>
        {alternatives.map((alternative) => (
          <button key={alternative.ref} type="button" disabled={busy} title={alternative.why}
                  onClick={() => void respond("chose_alternative", alternative)}>
            Or: {alternative.title}
          </button>
        ))}
      </div>
      {/* IH3 (spec §6): the quiet "Something else would help" link goes here, under the actions. */}
      <div data-testid="lesson-offer-something-else-slot" />
    </section>
  );
}
