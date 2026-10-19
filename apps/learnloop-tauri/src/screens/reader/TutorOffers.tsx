// RW1c's offers under a Reader tutor answer (spec §4.6, D44, G59; UX §4.2).
//
// Offers, not actions: every button here is something the learner presses;
// LearnLoop shows, serves, schedules, imports and opens nothing on its own.
//
// * The sources spec's requests: "practice this" (S0's deterministic request,
//   or the tutor's own find_practice), "from your books: …" (a passage
//   request) and "how do your books treat this?" (a comparison), each with
//   the tutor's one-line reason, labelled as LearnLoop's.
// * The Reader's own: "try the next step first" on a cited derivation or
//   worked example (RW1b's next-step question at that line).
//
// Fetch early, show on press. The practice and passage lookups start when the
// answer lands, so a press shows the result at once; pressed sooner, the
// button says "◐ looking in your books…" in place. Nothing a lookup fetched is
// shown, and no impression or exposure is recorded, until the press. A
// comparison is one heavier model call and runs only when pressed. A lookup
// that found nothing turns its button into a quiet line; one that failed
// keeps its button and runs again on the press. "Practise" on a proposal is
// the only thing that serves it (the Reader's working posture, D40).
import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type {
  FindPracticeResultDto,
  PracticeRequestDto,
  ReaderTutorButtonDto,
  SourcePassageDto,
  SourceToolRequestDto,
  SourceToolRunDto,
} from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { logReaderAction } from "./activity";
import { clip } from "./readerShared";
import { MeaningLabel, ModelVoice, SourceVoice } from "./voices";

export const OFFER_COPY = {
  practice: "practice this",
  passages: "from your books",
  compare: "how do your books treat this?",
  nextStep: "try the next step first",
  looking: "looking in your books",
  comparing: "comparing",
  nothing: "nothing in your practice or books fits this yet",
  failed: "Couldn't look that up — press to try again.",
  practise: "practise",
  reasonLabel: "LearnLoop's reason",
} as const;

export type OfferKind = "practice" | "passages" | "compare" | "try_next_step";

/** One proposal the practice offer shows. */
export interface OfferItem {
  practiceItemId: string;
  prompt: string;
}

interface Lookup {
  phase: "loading" | "ready" | "empty" | "failed";
  items?: OfferItem[];
  proposalId?: string | null;
  passages?: SourcePassageDto[];
  run?: SourceToolRunDto;
}

interface Offer {
  key: string;
  kind: OfferKind;
  label: string;
  reason: string | null;
  toolCallId: string | null;
  request?: SourceToolRequestDto;
  practice?: PracticeRequestDto;
  button?: ReaderTutorButtonDto;
}

export interface TutorOffersProps {
  exchangeId: string;
  extractionId: string;
  practiceRequest?: PracticeRequestDto | null;
  toolRequests?: SourceToolRequestDto[];
  buttons?: ReaderTutorButtonDto[];
  /** Serve a proposal (the Reader's working posture); absent: no "practise". */
  onPracticePick?: ((item: OfferItem, proposalId: string | null) => void) | null;
  /** RW1b's next-step question at a cited line; absent: no such button. */
  onTryNextStep?: ((spanId: string) => void) | null;
}

function offersFor(props: TutorOffersProps): Offer[] {
  const requests = props.toolRequests ?? [];
  const offers: Offer[] = [];
  const practiceRequests = requests.filter((request) => request.tool === "find_practice");
  for (const request of practiceRequests) {
    offers.push({ key: request.toolCallId, kind: "practice", label: OFFER_COPY.practice, reason: request.reason,
      toolCallId: request.toolCallId, request });
  }
  if (practiceRequests.length === 0 && props.practiceRequest) {
    offers.push({ key: `practice:${props.exchangeId}`, kind: "practice", label: OFFER_COPY.practice, reason: null,
      toolCallId: null, practice: props.practiceRequest });
  }
  for (const request of requests.filter((entry) => entry.tool === "find_sources")) {
    offers.push({ key: request.toolCallId, kind: "passages", label: `${OFFER_COPY.passages}:`, reason: request.reason,
      toolCallId: request.toolCallId, request });
  }
  for (const request of requests.filter((entry) => entry.tool === "compare_sources")) {
    offers.push({ key: request.toolCallId, kind: "compare", label: OFFER_COPY.compare, reason: request.reason,
      toolCallId: request.toolCallId, request });
  }
  if (props.onTryNextStep) {
    for (const button of props.buttons ?? []) {
      if (button.kind !== "try_next_step" || button.extractionId !== props.extractionId) continue;
      offers.push({ key: `next:${button.spanId}`, kind: "try_next_step", label: OFFER_COPY.nextStep, reason: null,
        toolCallId: null, button });
    }
  }
  return offers;
}

async function runLookup(offer: Offer): Promise<Lookup> {
  if (offer.kind === "practice" && offer.practice) {
    const result: FindPracticeResultDto = await api.findPractice({ ...offer.practice.request, caller: offer.practice.caller });
    const items = result.items.map((item) => ({ practiceItemId: item.practiceItemId, prompt: item.prompt }));
    return { phase: items.length ? "ready" : "empty", items, proposalId: result.proposalId ?? null };
  }
  const run = await api.runSourceTool(offer.toolCallId ?? "");
  if (offer.kind === "practice") {
    const items = (run.result.items ?? []).map((item) => ({ practiceItemId: item.practiceItemId, prompt: item.prompt }));
    return { phase: items.length ? "ready" : "empty", items, proposalId: run.result.proposalId ?? null, run };
  }
  if (offer.kind === "passages") {
    const passages = run.result.passages ?? [];
    return { phase: passages.length ? "ready" : "empty", passages, run };
  }
  return { phase: (run.result.sources ?? []).length ? "ready" : "empty", run };
}

const buttonStyle = {
  border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11,
  cursor: "pointer", padding: 0, textAlign: "left" as const,
};

export function TutorOffers(props: TutorOffersProps) {
  const [offers] = useState(() => offersFor(props));
  const [lookups, setLookups] = useState<Record<string, Lookup>>({});
  const [pressed, setPressed] = useState<Set<string>>(new Set());
  const recorded = useRef<Set<string>>(new Set());
  const unmounted = useRef(false);

  const settle = (key: string, lookup: Lookup) => {
    if (!unmounted.current) setLookups((current) => ({ ...current, [key]: lookup }));
  };
  const start = (offer: Offer) => {
    settle(offer.key, { phase: "loading" });
    void runLookup(offer).then((lookup) => settle(offer.key, lookup), () => settle(offer.key, { phase: "failed" }));
  };

  useEffect(() => {
    unmounted.current = false;
    // Eager: the practice and passage lookups start as the answer lands; the
    // comparison waits for its press. Nothing is shown until a press.
    for (const offer of offers) {
      if (offer.kind === "practice" || offer.kind === "passages") start(offer);
      logReaderAction("tutor_offer_shown", {
        extraction_id: props.extractionId, exchange_id: props.exchangeId, offer_kind: offer.kind,
        tool_call_id: offer.toolCallId,
      });
    }
    return () => {
      unmounted.current = true;
    };
    // The answer is immutable once shown: its offers are built and run once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // What a press shows is recorded once, when it is shown (never on the eager fetch).
  useEffect(() => {
    for (const offer of offers) {
      const lookup = lookups[offer.key];
      if (!pressed.has(offer.key) || lookup?.phase !== "ready" || recorded.current.has(offer.key)) continue;
      recorded.current.add(offer.key);
      if (offer.kind === "practice" && lookup.proposalId && lookup.items?.length) {
        void api.recordProposalImpressions({
          proposalId: lookup.proposalId, surface: "reader",
          keys: lookup.items.map((item) => ({ kind: "item" as const, practiceItemId: item.practiceItemId })),
        }).catch(() => undefined);
      } else if ((offer.kind === "passages" || offer.kind === "compare") && offer.toolCallId) {
        void api.recordSourceOfferShown({
          toolCallId: offer.toolCallId,
          ...(offer.kind === "passages" ? { spanKeys: (lookup.passages ?? []).map((passage) => passage.spanKey) } : {}),
        }).catch(() => undefined);
      }
    }
  }, [lookups, pressed, offers]);

  if (offers.length === 0) return null;

  const press = (offer: Offer) => {
    const lookup = lookups[offer.key];
    logReaderAction("tutor_offer_pressed", {
      extraction_id: props.extractionId, exchange_id: props.exchangeId, offer_kind: offer.kind,
      tool_call_id: offer.toolCallId,
      offer_result: offer.kind === "try_next_step" ? "opened" : lookup?.phase === "ready" ? "shown"
        : lookup?.phase === "loading" ? "looking" : lookup?.phase === "empty" ? "empty" : "run",
    });
    if (offer.kind === "try_next_step" && offer.button) {
      props.onTryNextStep?.(offer.button.spanId);
      return;
    }
    setPressed((current) => new Set(current).add(offer.key));
    // A comparison runs now; a failed lookup runs again.
    if (offer.kind === "compare" ? lookup === undefined || lookup.phase === "failed" : lookup?.phase === "failed") start(offer);
  };

  return (
    <div data-tutor-offers="" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {offers.map((offer) => {
        const lookup = lookups[offer.key];
        const isPressed = pressed.has(offer.key);
        if (lookup?.phase === "empty") {
          return (
            <span key={offer.key} data-offer-empty={offer.kind}>
              <MeaningLabel>{OFFER_COPY.nothing}</MeaningLabel>
            </span>
          );
        }
        return (
          <div key={offer.key} data-offer={offer.kind} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {!isPressed || lookup?.phase === "failed" ? (
              <span style={{ display: "flex", gap: 6, alignItems: "baseline", flexWrap: "wrap" }}>
                <button type="button" onClick={() => press(offer)} style={buttonStyle}>
                  {offer.label}{offer.kind === "passages" ? ` ${clip(offer.reason ?? "", 80)}` : ""}
                </button>
                {offer.reason && offer.kind !== "passages" ? (
                  <MeaningLabel>{OFFER_COPY.reasonLabel}: {clip(offer.reason, 120)}</MeaningLabel>
                ) : null}
                {offer.reason && offer.kind === "passages" ? <MeaningLabel>({OFFER_COPY.reasonLabel})</MeaningLabel> : null}
                {isPressed && lookup?.phase === "failed" ? <MeaningLabel>{OFFER_COPY.failed}</MeaningLabel> : null}
              </span>
            ) : lookup === undefined || lookup.phase === "loading" ? (
              <MeaningLabel>
                <span aria-hidden="true">◐</span> {offer.kind === "compare" ? OFFER_COPY.comparing : OFFER_COPY.looking}…
              </MeaningLabel>
            ) : (
              <OfferResult offer={offer} lookup={lookup} onPracticePick={props.onPracticePick ?? null} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function OfferResult({ offer, lookup, onPracticePick }: {
  offer: Offer; lookup: Lookup; onPracticePick: TutorOffersProps["onPracticePick"];
}) {
  if (offer.kind === "practice") {
    return (
      <ModelVoice note={`${OFFER_COPY.practice}${offer.reason ? ` · ${clip(offer.reason, 80)}` : ""}`}>
        <ul aria-label="practice for this question" style={{ margin: 0, paddingLeft: 16 }}>
          {(lookup.items ?? []).slice(0, 3).map((item) => (
            <li key={item.practiceItemId}>
              {clip(item.prompt, 160)}{" "}
              {onPracticePick ? (
                <button type="button" onClick={() => onPracticePick(item, lookup.proposalId ?? null)} style={buttonStyle}>
                  {OFFER_COPY.practise} ▸
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      </ModelVoice>
    );
  }
  if (offer.kind === "passages") {
    return (
      <>
        {(lookup.passages ?? []).map((passage) => (
          <SourceVoice key={passage.spanKey} source={passage.sourceTitle}
            locator={[passage.section, passage.page != null ? `p.${passage.page}` : null].filter(Boolean).join(" · ") || null}>
            {clip(passage.text, 700)}
          </SourceVoice>
        ))}
      </>
    );
  }
  const sources = lookup.run?.result.sources ?? [];
  return (
    <ModelVoice note="how your books treat this · LearnLoop's comparison">
      {sources.map((source) => (
        <div key={source.ref} style={{ marginTop: 4 }}>
          <MeaningLabel>{source.sourceTitle ?? source.sourceId}{source.page != null ? ` · p.${source.page}` : ""}</MeaningLabel>
          {(source.contributions ?? []).map((line, index) => (
            <div key={index}>{line.contribution} <span style={{ color: COLOR.textDim }}>“{line.quote}”</span></div>
          ))}
        </div>
      ))}
    </ModelVoice>
  );
}
