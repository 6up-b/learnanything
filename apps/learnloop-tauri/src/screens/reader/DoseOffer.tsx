// Adaptive difficulty AD2+AD3 (spec_adaptive_difficulty_v1 §5.12, §12; D21):
// now and then, one more thing to try at the end of a section, the Reader's
// randomized dose arm. At a completed section the sidecar draws (its row with
// every exact chance is written before anything is shown) whether to offer
// one more worked example or one quick question; most sections show nothing.
//
// The offer is a quiet LearnLoop line in the Reader's usual style: it never
// gates the text, never animates, and is dismissed with one key (Escape) or a
// tap. A dismissal costs nothing and is never read as low ability. Its rows
// (`delivered`, `taken`, `dismissed`) append and never change the draw. The
// glass box says why it appeared: "Offered at random, to learn how much of
// this helps you". With `reading_dose_offers` off the sidecar offers nothing
// and the Reader is unchanged.
//
// A taken extra question is the exact question the draw chose (Codex review
// F6): the Reader tells the sidecar which check the section already shows
// (`showingQuestionId`, never in the draw's support), and on "yes" this shows
// the chosen question itself, answered like any quick check, so the answer is
// the extra the offer delivered (its reading opportunity names the offer).
import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { ReaderDoseOfferDto, ReaderGuideSectionDto, ReaderSectionQuestionDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { AuthoredQuestionCard } from "./GuideRail";

type Offer = NonNullable<ReaderDoseOfferDto["offer"]>;
type OfferedQuestion = NonNullable<Offer["question"]>;

/** The chosen extra question as the quick-check card reads a section's question. */
function extraSection(question: OfferedQuestion, sectionId: string | null): ReaderGuideSectionDto {
  const asked: ReaderSectionQuestionDto = {
    practiceItemId: null, learningObjectId: null, learningObjectTitle: null, prompt: question.prompt,
    reason: "One more question on this section, offered at random.", learnerSignal: "auto_authored", goalId: null,
    goalTitle: null, goldenPathRunId: null, targetContractVersionId: null, readingPhase: "after_section",
    pattern: null, placementEventId: null, blueprintVersionId: null, placement: "auto_authored",
    authoredQuestionId: question.questionId, expectedAnswer: question.expectedAnswer, spanIds: question.spanIds,
    escalationLearningObjectId: null,
  };
  const spans = question.spanIds;
  return { id: question.sectionId ?? sectionId ?? "", label: "", startSpanId: spans[0] ?? "",
    endSpanId: spans[spans.length - 1] ?? "", spanIds: spans, question: asked, suggestedPassages: [] };
}

export interface DoseOfferProps {
  extractionId: string;
  /** The section the learner just completed (its boundary), or null. */
  sectionId: string | null;
  visitId: () => string | null;
  boundaryChecksAvailable: boolean;
  cueDensityOff: boolean;
  skim: boolean;
  /** The passage the learner was restored to (its section is never a decision point). */
  restoredSpanId: string | null;
  sections: ReaderGuideSectionDto[];
  /** The section's ordinary quick check already on show (never offered again as the extra). */
  showingQuestionId?: string | null;
  onShowExample?: (spanId: string) => void;
  /** Told the id of the extra question shown (after the learner said yes). */
  onShowQuestion?: (questionId: string) => void;
  /** "show me the passage" on the extra question. */
  onJump?: (spanId: string) => void;
}

export function DoseOffer(props: DoseOfferProps) {
  const { extractionId, sectionId, visitId, boundaryChecksAvailable, cueDensityOff, skim, restoredSpanId, sections,
    showingQuestionId, onShowExample, onShowQuestion, onJump } = props;
  const [offer, setOffer] = useState<Offer | null>(null);
  const [why, setWhy] = useState(false);
  const [extra, setExtra] = useState<OfferedQuestion | null>(null);
  const decided = useRef(new Set<string>());

  useEffect(() => {
    if (!sectionId || decided.current.has(sectionId)) return;
    const visit = visitId();
    if (!visit) return;
    decided.current.add(sectionId);
    const section = sections.find((candidate) => candidate.id === sectionId);
    const restoredSection = !!restoredSpanId && !!section?.spanIds.includes(restoredSpanId);
    let alive = true;
    // A test double or an older client without the call: nothing shows.
    if (typeof api.readerDoseOffer !== "function") return;
    api
      .readerDoseOffer({ extractionId, sectionId, visitId: visit, boundaryChecksAvailable, cueDensityOff, skim,
        restoredSection, showingQuestionId: showingQuestionId ?? null })
      .then((result) => {
        if (!alive || !result?.offer) return;
        setOffer(result.offer);
        void api.readerDoseOfferEvent({ drawId: result.offer.drawId, event: "delivered" }).catch(() => undefined);
      })
      .catch(() => {
        // An older sidecar, or the draw refused: the Reader stays as it is.
      });
    return () => {
      alive = false;
    };
  }, [sectionId, extractionId, visitId, boundaryChecksAvailable, cueDensityOff, skim, restoredSpanId, sections,
    showingQuestionId]);

  if (extra) {
    return (
      <div data-testid="dose-extra-question">
        <AuthoredQuestionCard
          section={extraSection(extra, sectionId)}
          autoStart
          onJump={(spanId) => onJump?.(spanId)}
          onDismiss={() => setExtra(null)}
          onComplete={() => setExtra(null)}
          onError={() => undefined}
        />
      </div>
    );
  }
  if (!offer) return null;
  const close = (event: "taken" | "dismissed") => {
    void api.readerDoseOfferEvent({ drawId: offer.drawId, event }).catch(() => undefined);
    setOffer(null);
    setWhy(false);
  };
  const take = () => {
    close("taken");
    if (offer.variant === "extra_worked_example" && offer.content.spanId) onShowExample?.(offer.content.spanId);
    if (offer.variant === "extra_question" && offer.question) {
      setExtra(offer.question);
      onShowQuestion?.(offer.question.questionId);
    }
  };
  return (
    <div
      role="note"
      data-testid="dose-offer"
      tabIndex={-1}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.stopPropagation();
          close("dismissed");
        }
      }}
      style={{ fontSize: 11, color: COLOR.textDim, fontFamily: FONT_MONO, display: "flex", gap: 8, alignItems: "baseline",
        flexWrap: "wrap", padding: "4px 0" }}
    >
      <span>{offer.text}</span>
      <button type="button" onClick={take}
              style={{ border: 0, background: "transparent", padding: 0, color: COLOR.amberLink, fontFamily: FONT_MONO,
                fontSize: 11, cursor: "pointer" }}>
        yes
      </button>
      <button type="button" aria-label="dismiss (Esc)" onClick={() => close("dismissed")}
              style={{ border: 0, background: "transparent", padding: 0, color: COLOR.textFaint, fontFamily: FONT_MONO,
                fontSize: 11, cursor: "pointer" }}>
        no thanks
      </button>
      <button type="button" aria-expanded={why} onClick={() => setWhy((open) => !open)}
              style={{ border: 0, background: "transparent", padding: 0, color: COLOR.textFaint, fontFamily: FONT_MONO,
                fontSize: 11, cursor: "pointer" }}>
        why?
      </button>
      {why ? <span data-testid="dose-offer-why" style={{ color: COLOR.textFaint }}>{offer.why}</span> : null}
    </div>
  );
}
