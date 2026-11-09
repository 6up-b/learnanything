// Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): a lesson offer, a block of today's plan.
//
// "Learn X now? (about 15 min)", the topic in plain words and the planner's honest reason, with Start, up to two
// other topics and "Not now". Start opens the lesson (the plan goes on at its next block when the lesson closes);
// "Not now" goes straight on to the block the plan would have served. Only ever this block of the plan: never a
// modal or a notification, and never during a check (the sidecar offers it only at a block boundary). The answer
// goes through the TE1b response the Today card uses (`lesson.suggestion_respond`, on this block's own decision).
import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { LessonSuggestionEntryDto, PlanLessonOfferDto } from "../../api/dto";
import { getCommandError } from "../../errors";
import { COLOR, FONT_MONO } from "../../components/term";
import type { LessonEntry } from "../LessonScreen";

export type OfferResponse = "accepted" | "chose_alternative" | "declined";
export type OfferSurface = "today" | "offer_page";

/** Instruct hand-off IH1: the offer's card or page is on screen. One `offer_shown` event on the block, written once
 *  per block and surface (the sidecar keeps that count across remounts; the ref only spares a repeat call while this
 *  one stays mounted). A failure is dropped: the receipt never disturbs what it describes. Nothing is sent for an
 *  answered or id-less offer. */
export function useOfferShown(offer: PlanLessonOfferDto, surface: OfferSurface, sessionId: string | null) {
  const blockId = offer.blockId;
  const sent = useRef<string | null>(null);
  const live = Boolean(offer.decisionId) && !offer.answered && Boolean(blockId);
  useEffect(() => {
    if (!live || !blockId) return;
    const key = `${blockId}:${surface}`;
    if (sent.current === key) return;
    sent.current = key;
    try {
      void Promise.resolve(api.recordOfferShown?.({ blockId, surface, sessionId })).catch(() => undefined);
    } catch {
      /* the receipt never disturbs the page */
    }
  }, [live, blockId, surface, sessionId]);
}

/** The offer's answers, through the TE1b response the Today card has always used (`lesson.suggestion_respond`, on
 *  this block's own decision). Start answers `accepted` and opens the lesson at once; nothing else starts one. */
export function useLessonOfferActions({
  offer,
  sessionId,
  onStartLesson,
  onAnswered,
  onGone,
  onError
}: {
  offer: PlanLessonOfferDto;
  sessionId: string | null;
  /** Opens the lesson the learner started (a TE1 lesson whose origin is this block's decision). */
  onStartLesson?: (entry: LessonEntry) => void;
  /** The plan moves on (its next block is chosen): re-read it. */
  onAnswered: (response: OfferResponse) => void;
  /** IH2: this offer is no longer in the plan (a newer decision replaced it), so no answer can land. */
  onGone?: () => void;
  onError: (message: string) => void;
}) {
  const [busy, setBusy] = useState(false);

  async function respond(response: OfferResponse, chosen?: LessonSuggestionEntryDto) {
    if (!offer.decisionId) return;
    setBusy(true);
    try {
      const result = await api.lessonSuggestionRespond({
        decisionId: offer.decisionId, response, sessionId,
        ...(response === "chose_alternative" && chosen ? { candidateRef: chosen.ref } : {})
      });
      onAnswered(response);
      if (result.lesson && onStartLesson) {
        onStartLesson({
          kind: "open", entry: "learning_object", learningObjectIds: result.lesson.learningObjectIds,
          title: result.lesson.title,
          suggestion: { decisionId: result.lesson.decisionId, lessonId: result.lesson.lessonId }
        });
      }
    } catch (error) {
      const failure = getCommandError(error);
      if (failure?.code === "not_found" && onGone) onGone();
      else onError(failure?.message ?? String(error));
    } finally {
      setBusy(false);
    }
  }

  return { busy, respond };
}

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
  const { busy, respond } = useLessonOfferActions({ offer, sessionId, onStartLesson, onAnswered, onGone: onAnswered, onError });
  useOfferShown(offer, "today", sessionId);
  if (!offer.decisionId || offer.answered) return null;

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
