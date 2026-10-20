// RW1c: a Reader tutor answer in its three modes (spec §4.6; UX §4.2, W3).
//
// In this order: "From your books" (a § excerpt, quote-verified on the
// server, when one directly answers), LearnLoop's explanation (◇, grounded,
// with citations) and "connecting it to your work" (◇, only when the learner
// had work or an open question there, personalized). When the books don't
// cover it, the answer opens with the server's line and claims nothing as
// theirs. Under it: "another way · that didn't help…" and the offers.
//
// With no `tutor` on the exchange (reader_tutor.retrieval_enabled off, or an
// exchange from before RW1c) and no offers, or with no RW1c controls from the
// contract (both switches off), this is exactly the answer of before: one
// model voice.
import { useState } from "react";
import type { PracticeRequestDto, ReaderTutorButtonDto, SourceToolRequestDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { MarkdownMath } from "../../render/MarkdownMath";
import type { ReaderExchange } from "./ReaderAskBranches";
import { TutorOffers, type OfferItem, type TutorOfferStore } from "./TutorOffers";
import { MeaningLabel, ModelVoice, SourceVoice } from "./voices";

export const TUTOR_COPY = {
  fromYourBooks: "from your books",
  explanation: "LearnLoop's explanation",
  bridge: "connecting it to your work",
  anotherWay: "another way",
  didntHelp: "that didn't help…",
  unclearPrompt: "What's still unclear?",
  unclearPlaceholder: "optional: what's still unclear…",
  send: "ask again",
  cancel: "cancel",
  didntHelpDefault: "That didn't help.",
  anotherWayQuestion: "Explain it another way",
  openPassage: "open in your book",
} as const;

/** A passage the tutor showed, wherever it is: this source or another one. */
export interface TutorPassageRef {
  extractionId: string;
  spanId: string;
  sourceId?: string | null;
}

/** The offers a freshly landed answer carries (never restored from history). */
export interface ExchangeOffers {
  practiceRequest?: PracticeRequestDto | null;
  toolRequests?: SourceToolRequestDto[];
  buttons?: ReaderTutorButtonDto[];
}

/** RW1c's controls, present only while the contract names them. */
export interface TutorRailProps {
  anotherWay: boolean;
  offers: boolean;
  busy: boolean;
  onAnotherWay?: (exchange: ReaderExchange) => void;
  onDidntHelp?: (exchange: ReaderExchange, text: string) => void;
  onPracticePick?: ((item: OfferItem, proposalId: string | null) => void) | null;
  onTryNextStep?: ((spanId: string) => void) | null;
  /** Open a passage the answer quotes or cites: this source peeks at it,
   *  another book opens as a detour (Alt+← comes back). Absent: not offered. */
  onOpenPassage?: ((passage: TutorPassageRef) => void) | null;
  /** The screen's exchange-scoped offer state (lookups survive a collapse). */
  offerStore?: TutorOfferStore;
}

const linkStyle = {
  border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11,
  cursor: "pointer", padding: 0,
};

export function TutorAnswer({ exchange, tutor }: { exchange: ReaderExchange; tutor?: TutorRailProps }) {
  // RW1c's parts render only while the contract supplies its controls (fix
  // round 5, R4): with both switches off a saved RW1c answer is the one model
  // voice of before, even if an exchange still carries its view.
  const view = tutor ? exchange.tutor ?? null : null;
  const [unclearOpen, setUnclearOpen] = useState(false);
  const [unclear, setUnclear] = useState("");
  if (!view && !(tutor?.offers && exchange.offers)) {
    return (
      <ModelVoice first>
        <MarkdownMath value={exchange.answerMd} />
      </ModelVoice>
    );
  }
  const excerpt = view?.excerpt ?? null;
  const label = view?.retrieval?.label ?? null;
  return (
    <div data-tutor-answer="" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {view?.abstained && view.abstentionLine ? (
        <span data-abstention="">
          <MeaningLabel style={{ fontSize: 11 }}>{view.abstentionLine}</MeaningLabel>
        </span>
      ) : null}
      {excerpt ? (
        <SourceVoice source={TUTOR_COPY.fromYourBooks} locator={excerpt.label}>
          <blockquote data-excerpt="" style={{ margin: 0 }}>
            <MarkdownMath value={excerpt.quote} />
          </blockquote>
          {tutor?.onOpenPassage ? (
            <button type="button" data-open-excerpt="" style={linkStyle} onClick={() => tutor.onOpenPassage?.({
              extractionId: excerpt.extractionId, spanId: excerpt.spanId, sourceId: excerpt.sourceId ?? null,
            })}>
              {TUTOR_COPY.openPassage} ▸
            </button>
          ) : null}
        </SourceVoice>
      ) : null}
      {label && !view?.abstained ? <MeaningLabel>{label}</MeaningLabel> : null}
      <ModelVoice first note={view && !view.abstained ? TUTOR_COPY.explanation : null}>
        <MarkdownMath value={exchange.answerMd} />
      </ModelVoice>
      {view?.bridgeMd ? (
        <ModelVoice note={TUTOR_COPY.bridge}>
          <MarkdownMath value={view.bridgeMd} />
        </ModelVoice>
      ) : null}
      {tutor?.anotherWay && view ? (
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "baseline" }}>
          <button type="button" disabled={tutor.busy} onClick={() => tutor.onAnotherWay?.(exchange)} style={linkStyle}>
            {TUTOR_COPY.anotherWay}
          </button>
          <button type="button" disabled={tutor.busy} aria-expanded={unclearOpen} onClick={() => setUnclearOpen((open) => !open)} style={linkStyle}>
            {TUTOR_COPY.didntHelp}
          </button>
        </div>
      ) : null}
      {unclearOpen && tutor ? (
        <div data-still-unclear="" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <MeaningLabel>{TUTOR_COPY.unclearPrompt}</MeaningLabel>
          <textarea
            value={unclear}
            onChange={(event) => setUnclear(event.target.value)}
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                event.preventDefault();
                tutor.onDidntHelp?.(exchange, unclear.trim());
                setUnclearOpen(false);
                setUnclear("");
              }
            }}
            placeholder={TUTOR_COPY.unclearPlaceholder}
            style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 6, minHeight: 48 }}
          />
          <div style={{ display: "flex", gap: 12 }}>
            <button type="button" disabled={tutor.busy} onClick={() => {
              tutor.onDidntHelp?.(exchange, unclear.trim());
              setUnclearOpen(false);
              setUnclear("");
            }} style={linkStyle}>{TUTOR_COPY.send} · ctrl+↵</button>
            <button type="button" onClick={() => { setUnclearOpen(false); setUnclear(""); }} style={linkStyle}>{TUTOR_COPY.cancel}</button>
          </div>
        </div>
      ) : null}
      {tutor?.offers && exchange.offers ? (
        <TutorOffers
          exchangeId={exchange.id}
          extractionId={exchange.extractionId}
          practiceRequest={exchange.offers.practiceRequest ?? null}
          toolRequests={exchange.offers.toolRequests ?? []}
          buttons={exchange.offers.buttons ?? []}
          onPracticePick={tutor.onPracticePick ?? null}
          onTryNextStep={tutor.onTryNextStep ?? null}
          {...(tutor.offerStore ? { store: tutor.offerStore } : {})}
        />
      ) : null}
    </div>
  );
}
