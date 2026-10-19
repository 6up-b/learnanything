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
import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { ReaderDoseOfferDto, ReaderGuideSectionDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";

type Offer = NonNullable<ReaderDoseOfferDto["offer"]>;

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
  showingQuestionId?: string | null;
  onShowExample?: (spanId: string) => void;
  onShowQuestion?: (questionId: string) => void;
}

export function DoseOffer(props: DoseOfferProps) {
  const { extractionId, sectionId, visitId, boundaryChecksAvailable, cueDensityOff, skim, restoredSpanId, sections,
    showingQuestionId, onShowExample, onShowQuestion } = props;
  const [offer, setOffer] = useState<Offer | null>(null);
  const [why, setWhy] = useState(false);
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

  if (!offer) return null;
  const close = (event: "taken" | "dismissed") => {
    void api.readerDoseOfferEvent({ drawId: offer.drawId, event }).catch(() => undefined);
    setOffer(null);
    setWhy(false);
  };
  const take = () => {
    close("taken");
    if (offer.variant === "extra_worked_example" && offer.content.spanId) onShowExample?.(offer.content.spanId);
    if (offer.variant === "extra_question" && offer.content.questionId) onShowQuestion?.(offer.content.questionId);
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
