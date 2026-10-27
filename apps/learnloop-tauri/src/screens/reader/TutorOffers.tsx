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
//   worked example (RW1b's next-step question at that line), and RW5b's
//   "make this explorable" on a cited equation or figure the tutor's own
//   answer judged explorable (the press builds the figure under its passage;
//   the button itself calls nothing).
//
// Fetch early, show on press. The practice and passage lookups start when the
// answer lands, so a press shows the result at once; pressed sooner, the
// button says "◐ looking in your books…" in place. Nothing a lookup fetched is
// shown, and no impression or exposure is recorded, until the press. A
// comparison is one heavier model call and runs only when pressed. A lookup
// that found nothing turns its button into a quiet line; one that failed, or
// whose books could not be checked (the verification unavailable, over its
// budget, cancelled), keeps its button, says so, and runs again on the press.
// "Practise" on a proposal is the only thing that serves it (the Reader's
// working posture, D40).
//
// The lookups and presses belong to the exchange, not to this component
// (Codex review F6): collapsing an answer and opening it again shows what was
// fetched and pressed, and runs nothing again. The impression names exactly
// the proposals rendered (F4).
//
// RW4b's hook (docs/reviews/reader-workbench-RW4b.md §5): with `exercises`
// (library_exercises on), a practice offer's textbook exercises show after its
// items through the same ProposalExercises block as RW4a's "practice this
// question", and a lookup whose only proposals are exercises is ready (so
// "nothing … fits" shows only when the block has nothing either). Without
// `exercises` the offers are RW1c's, unchanged.
//
// RW4d: a shown comparison can be kept (CompareKeep, under the table), only
// while the Reader provides its compareKeep context; without it nothing more
// renders.
//
// Reader CA3 (`onCompare`, present only while compare from anywhere is on and
// the comparing posture can open): "how do your books treat this?" is one more
// door of the one comparison request: the press opens the comparing posture's
// table beside the book (anchored on the passage the question was asked on),
// and the offer says so; nothing runs here. Absent: today's inline table.
import { useEffect, useReducer } from "react";
import { api } from "../../api/client";
import type {
  CompareTableDto,
  FindPracticeResultDto,
  PracticeRequestDto,
  ReaderTutorButtonDto,
  SourcePassageDto,
  SourceToolRequestDto,
  SourceToolRunDto,
} from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { logReaderAction } from "./activity";
import { practiceFromToolRun } from "./exerciseCandidates";
import { CompareKeep } from "./CompareKeep";
import { CompareTable } from "./LibraryAnswer";
import { ProposalExercises, type LibraryExercisesProps } from "./ProposalExercises";
import { clip } from "./readerShared";
import { MeaningLabel, ModelVoice, SourceVoice } from "./voices";

export const OFFER_COPY = {
  practice: "practice this",
  passages: "from your books",
  compare: "how do your books treat this?",
  nextStep: "try the next step first",
  makeExplorable: "make this explorable",
  explorableBuilding: "building an interactive version under the passage",
  /** RW5d P1: the tutor's figure goal (AI-written), a button the learner presses (D28). */
  showMe: "show me:",
  showMeAiWritten: "(AI-written)",
  looking: "looking in your books",
  comparing: "comparing",
  /** CA3: the comparison opened beside the book. */
  compareOpened: "compared beside the book ▸",
  nothing: "nothing in your practice or books fits this yet",
  failed: "Couldn't look that up — press to try again.",
  unchecked: "Your books couldn't be checked just now",
  tryAgain: "press to try again.",
  practise: "practise",
  reasonLabel: "LearnLoop's reason",
  notCovered: "not covered by your books",
} as const;

/** The proposals a practice offer shows (and the impression names). */
export const MAX_SHOWN = 3;

export type OfferKind = "practice" | "passages" | "compare" | "try_next_step" | "make_explorable" | "show_me";

/** One proposal the practice offer shows. */
export interface OfferItem {
  practiceItemId: string;
  prompt: string;
}

interface Lookup {
  /** `unchecked`: the call answered, but its books (or proposals) were not
   *  checked (unavailable, over budget, cancelled, timed out): never "nothing fits". */
  phase: "loading" | "ready" | "empty" | "failed" | "unchecked";
  items?: OfferItem[];
  proposalId?: string | null;
  /** RW4b: the landed proposal (its textbook exercises), for ProposalExercises. */
  practice?: FindPracticeResultDto;
  passages?: SourcePassageDto[];
  run?: SourceToolRunDto;
  table?: CompareTableDto;
  missingPerspectives?: string[];
  because?: string | null;
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

/** What one exchange's offers have fetched and the learner has pressed. */
interface ExchangeOffersState {
  lookups: Record<string, Lookup>;
  pressed: Set<string>;
  recorded: Set<string>;
  /** Lookups started (a key leaves only when its run failed or went unchecked). */
  started: Set<string>;
  shownLogged: boolean;
  listeners: Set<() => void>;
}

/** Exchange-scoped offer state: it outlives the component that renders it
 *  (a collapse unmounts it), so nothing is fetched, impressed or logged twice. */
export interface TutorOfferStore {
  get: (exchangeId: string) => ExchangeOffersState;
  clear: () => void;
}

const STORE_CAP = 200;

export function createTutorOfferStore(): TutorOfferStore {
  const states = new Map<string, ExchangeOffersState>();
  return {
    get(exchangeId) {
      let state = states.get(exchangeId);
      if (!state) {
        state = { lookups: {}, pressed: new Set(), recorded: new Set(), started: new Set(), shownLogged: false, listeners: new Set() };
        states.set(exchangeId, state);
        if (states.size > STORE_CAP) {
          const oldest = states.keys().next().value;
          if (oldest !== undefined && oldest !== exchangeId) states.delete(oldest);
        }
      }
      return state;
    },
    clear() {
      states.clear();
    },
  };
}

/** The store a TutorOffers uses when the screen gives it none. */
export const defaultTutorOfferStore = createTutorOfferStore();

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
  /** RW5b: build the figure of a cited block the tutor judged explorable;
   *  absent: no such button. */
  onMakeExplorable?: ((spanId: string, offerRef: string) => void) | null;
  /** RW5d P1: build the tutor's figure goal (the press is the grant; the server
   *  checks the goal against the stored answer). Absent: no such button. */
  onShowMe?: ((goal: string, offerRef: string) => void) | null;
  /** RW5b (Codex review F1): the judgment an explorable press names, the
   *  answer's QUESTION event (where the tutor's view is stored), never
   *  `exchangeId` (its reader_answer_submitted interaction event, which the
   *  server cannot resolve to the judgment). Absent: no such button. */
  offerRef?: string | null;
  /** Where the exchange's offer state lives (the screen's; else a module default). */
  store?: TutorOfferStore;
  /** RW4b: the textbook-exercise view (absent while library_exercises is off). */
  exercises?: LibraryExercisesProps | null;
  /** Reader CA3: open the comparison beside the book (the one request); absent: today's inline table. */
  onCompare?: ((request: { question: string; toolCallId: string | null }) => void) | null;
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
  if (props.onMakeExplorable && props.offerRef) {
    for (const button of props.buttons ?? []) {
      if (button.kind !== "make_explorable" || button.extractionId !== props.extractionId) continue;
      offers.push({ key: `explorable:${button.spanId}`, kind: "make_explorable", label: OFFER_COPY.makeExplorable, reason: null,
        toolCallId: null, button });
    }
  }
  if (props.onShowMe && props.offerRef) {
    // RW5d P1: at most one figure goal per answer (its label is the goal).
    const goal = (props.buttons ?? []).find((button) => button.kind === "show_me" && button.label.trim());
    if (goal) {
      offers.push({ key: `show_me:${props.exchangeId}`, kind: "show_me", label: OFFER_COPY.showMe, reason: null,
        toolCallId: null, button: goal });
    }
  }
  return offers;
}

/** Why a lookup's results went unchecked, in plain words (null: not said). */
function uncheckedBecause(status: string): string | null {
  if (/over_budget|capped|budget|cap\b/.test(status)) return "today's checking budget is used";
  if (/unavailable|skipped|unpriced|no_route|disabled/.test(status)) return "LearnLoop's model couldn't be reached";
  if (/timed_out|timeout/.test(status)) return "checking ran out of time";
  if (/cancel/.test(status)) return "the check was cancelled";
  return null;
}

/** A practice or passage result counts as found-or-nothing only when its call
 *  succeeded; any other status is an unchecked result (Codex review F5). */
function succeeded(status: string | undefined): boolean {
  return status === undefined || status === "" || status === "ok" || status === "cached";
}

function practiceLookup(items: OfferItem[], proposalId: string | null, status: string | undefined,
                        run?: SourceToolRunDto, practice?: FindPracticeResultDto): Lookup {
  const visible = items.slice(0, MAX_SHOWN);
  const kept = practice ? { practice } : {};
  if (visible.length) return { phase: "ready", items: visible, proposalId, run, ...kept };
  if (!succeeded(status)) return { phase: "unchecked", because: uncheckedBecause(status ?? ""), run };
  // RW4b: exercises only (the view on) is a result; the block says what it shows.
  if (practice?.sourceExercises?.length) return { phase: "ready", items: [], proposalId, run, practice };
  return { phase: "empty", items: [], proposalId, run };
}

/** The tutor's comparison in the Reader's own table (the compare_table
 *  mapping, `source_retrieval.library_ask.compare_table`): contributes,
 *  assumes (its `different_assumptions` relations), differs from the others
 *  (its other relations), and the sources that could not be checked. */
export function compareTableFromRun(run: SourceToolRunDto): CompareTableDto {
  const result = run.result;
  const sources = result.sources ?? [];
  const byRef = new Map(sources.map((source) => [source.ref, source]));
  const relations = (result.relations ?? []) as Array<Record<string, unknown>>;
  const text = (value: unknown) => (value == null ? null : String(value));
  const rows = sources.map((source) => {
    const assumes: CompareTableDto["rows"][number]["assumes"] = [];
    const differs: CompareTableDto["rows"][number]["differs"] = [];
    for (const relation of relations) {
      const left = text(relation.leftRef);
      const right = text(relation.rightRef);
      if (source.ref !== left && source.ref !== right) continue;
      const otherRef = left === source.ref ? right : left;
      const cell = {
        line: text(relation.statement),
        quote: text(left === source.ref ? relation.leftQuote : relation.rightQuote),
        relation: text(relation.relation),
        otherSourceTitle: (otherRef ? byRef.get(otherRef)?.sourceTitle : null) ?? null,
        authorship: "ai" as const,
      };
      (relation.relation === "different_assumptions" ? assumes : differs).push(cell);
    }
    return {
      sourceId: source.sourceId ?? null,
      sourceTitle: source.sourceTitle ?? null,
      key: `${source.extractionId}:${source.spanId}`,
      page: source.page ?? null,
      isOpenSource: false,
      contributes: (source.contributions ?? []).map((line) => ({
        line: line.contribution, quote: line.quote, perspective: line.perspective ?? null, authorship: "ai" as const,
      })),
      assumes,
      differs,
    };
  });
  const status = result.status ?? "ok";
  return {
    askId: run.toolCallId,
    status,
    comparisonId: result.comparisonId ?? null,
    header: "differences kept · each line quotes its own source",
    rows,
    alsoDiscussedIn: (result.alsoDiscussedIn ?? []) as Array<Record<string, unknown>>,
    unverifiedSources: (result.unverifiedSources ?? []) as CompareTableDto["unverifiedSources"],
    droppedPins: [],
    droppedLineCount: 0,
    verification: { status, stopped: null },
  };
}

/** `withExercises`: RW4b's view is on, so the lookup keeps its proposal. */
async function runLookup(offer: Offer, withExercises: boolean): Promise<Lookup> {
  if (offer.kind === "practice" && offer.practice) {
    const result: FindPracticeResultDto = await api.findPractice({ ...offer.practice.request, caller: offer.practice.caller });
    const items = result.items.map((item) => ({ practiceItemId: item.practiceItemId, prompt: item.prompt }));
    return practiceLookup(items, result.proposalId ?? null, result.status, undefined, withExercises ? result : undefined);
  }
  const run = await api.runSourceTool(offer.toolCallId ?? "");
  const status = run.result.status;
  if (offer.kind === "practice") {
    const items = (run.result.items ?? []).map((item) => ({ practiceItemId: item.practiceItemId, prompt: item.prompt }));
    return practiceLookup(items, run.result.proposalId ?? null, status, run,
      withExercises ? practiceFromToolRun(run) : undefined);
  }
  if (offer.kind === "passages") {
    const passages = run.result.passages ?? [];
    if (!succeeded(status)) return { phase: "unchecked", because: uncheckedBecause(status ?? ""), run };
    return { phase: passages.length ? "ready" : "empty", passages, run };
  }
  // A comparison: shown when it compared, or when too few checked sources
  // remain (the table says so, and lists what was not checked); anything else
  // (unavailable, over budget, cancelled, failed) is not a comparison.
  if (status && status !== "ok" && status !== "too_few_sources") {
    return { phase: "unchecked", because: uncheckedBecause(status), run };
  }
  const table = compareTableFromRun(run);
  const missing = run.result.missingPerspectives ?? [];
  if (!table.rows.length && !table.unverifiedSources.length && !missing.length) return { phase: "empty", run };
  return { phase: "ready", run, table, missingPerspectives: missing };
}

const buttonStyle = {
  border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11,
  cursor: "pointer", padding: 0, textAlign: "left" as const,
};

function notify(state: ExchangeOffersState) {
  for (const listener of [...state.listeners]) listener();
}

export function TutorOffers(props: TutorOffersProps) {
  const store = props.store ?? defaultTutorOfferStore;
  const state = store.get(props.exchangeId);
  const offers = offersFor(props);
  const [, rerender] = useReducer((tick: number) => tick + 1, 0);

  const settle = (key: string, lookup: Lookup) => {
    state.lookups = { ...state.lookups, [key]: lookup };
    if (lookup.phase === "failed" || lookup.phase === "unchecked") state.started.delete(key);
    notify(state);
  };
  const start = (offer: Offer) => {
    if (state.started.has(offer.key)) return;
    state.started.add(offer.key);
    settle(offer.key, { phase: "loading" });
    void runLookup(offer, Boolean(props.exercises)).then((lookup) => settle(offer.key, lookup), () => settle(offer.key, { phase: "failed" }));
  };

  useEffect(() => {
    state.listeners.add(rerender);
    // Eager, once per exchange: the practice and passage lookups start as the
    // answer lands; the comparison waits for its press. Nothing is shown
    // until a press. A remount (the answer collapsed and opened) runs nothing.
    for (const offer of offers) {
      if ((offer.kind === "practice" || offer.kind === "passages") && state.lookups[offer.key] === undefined) start(offer);
    }
    if (!state.shownLogged) {
      state.shownLogged = true;
      for (const offer of offers) {
        logReaderAction("tutor_offer_shown", {
          extraction_id: props.extractionId, exchange_id: props.exchangeId, offer_kind: offer.kind,
          tool_call_id: offer.toolCallId,
        });
      }
    }
    return () => {
      state.listeners.delete(rerender);
    };
    // The answer is immutable once shown: its offers are built once per exchange.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state]);

  // What a press shows is recorded once per exchange, when it is shown (never
  // on the eager fetch), and names exactly what is rendered.
  useEffect(() => {
    for (const offer of offers) {
      const lookup = state.lookups[offer.key];
      if (!state.pressed.has(offer.key) || lookup?.phase !== "ready" || state.recorded.has(offer.key)) continue;
      state.recorded.add(offer.key);
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
  });

  if (offers.length === 0) return null;

  const press = (offer: Offer) => {
    const lookup = state.lookups[offer.key];
    const opensBeside = offer.kind === "compare" && Boolean(props.onCompare);
    logReaderAction("tutor_offer_pressed", {
      extraction_id: props.extractionId, exchange_id: props.exchangeId, offer_kind: offer.kind,
      tool_call_id: offer.toolCallId,
      offer_result: offer.kind === "try_next_step" || offer.kind === "make_explorable" || offer.kind === "show_me" || opensBeside ? "opened" : lookup?.phase === "ready" ? "shown"
        : lookup?.phase === "loading" ? "looking" : lookup?.phase === "empty" ? "empty" : "run",
    });
    if (offer.kind === "try_next_step" && offer.button) {
      props.onTryNextStep?.(offer.button.spanId);
      return;
    }
    if (offer.kind === "make_explorable" && offer.button && props.offerRef) {
      // The press is the learner's: it builds under the passage (one press, one build).
      state.pressed = new Set(state.pressed).add(offer.key);
      notify(state);
      props.onMakeExplorable?.(offer.button.spanId, props.offerRef);
      return;
    }
    if (opensBeside && offer.request) {
      // CA3: the same comparison as every other door, beside the book.
      state.pressed = new Set(state.pressed).add(offer.key);
      notify(state);
      const query = offer.request.arguments?.query;
      props.onCompare?.({ question: typeof query === "string" && query.trim() ? query : offer.reason ?? "", toolCallId: offer.toolCallId });
      return;
    }
    if (offer.kind === "show_me" && offer.button && props.offerRef) {
      state.pressed = new Set(state.pressed).add(offer.key);
      notify(state);
      props.onShowMe?.(offer.button.label, props.offerRef);
      return;
    }
    state.pressed = new Set(state.pressed).add(offer.key);
    notify(state);
    // A comparison runs now; a failed or unchecked lookup runs again.
    const retry = lookup?.phase === "failed" || lookup?.phase === "unchecked";
    if (offer.kind === "compare" ? lookup === undefined || retry : retry) start(offer);
  };

  return (
    <div data-tutor-offers="" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {offers.map((offer) => {
        const lookup = state.lookups[offer.key];
        const isPressed = state.pressed.has(offer.key);
        if (lookup?.phase === "empty") {
          return (
            <span key={offer.key} data-offer-empty={offer.kind}>
              <MeaningLabel>{OFFER_COPY.nothing}</MeaningLabel>
            </span>
          );
        }
        if (offer.kind === "compare" && props.onCompare && isPressed && !lookup) {
          // CA3: the comparison is beside the book; pressing again opens it again.
          return (
            <span key={offer.key} data-offer={offer.kind} data-offer-pressed="">
              <button type="button" onClick={() => press(offer)} style={buttonStyle}>{OFFER_COPY.compareOpened}</button>
            </span>
          );
        }
        if ((offer.kind === "make_explorable" || offer.kind === "show_me") && isPressed) {
          // RW5b: the build shows under its passage (RW5a's pending line), not here.
          return (
            <span key={offer.key} data-offer={offer.kind} data-offer-pressed="">
              <MeaningLabel>{OFFER_COPY.explorableBuilding}</MeaningLabel>
            </span>
          );
        }
        const retryable = lookup?.phase === "failed" || lookup?.phase === "unchecked";
        return (
          <div key={offer.key} data-offer={offer.kind} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {!isPressed || retryable ? (
              <span style={{ display: "flex", gap: 6, alignItems: "baseline", flexWrap: "wrap" }}>
                <button type="button" onClick={() => press(offer)} style={buttonStyle}>
                  {offer.kind === "show_me" ? "▸ " : ""}{offer.label}{offer.kind === "passages" ? ` ${clip(offer.reason ?? "", 80)}` : ""}
                  {offer.kind === "show_me" && offer.button ? <> ◇ “{clip(offer.button.label, 160)}”</> : null}
                </button>
                {offer.kind === "show_me" ? <MeaningLabel>{OFFER_COPY.showMeAiWritten}</MeaningLabel> : null}
                {offer.reason && offer.kind !== "passages" ? (
                  <MeaningLabel>{OFFER_COPY.reasonLabel}: {clip(offer.reason, 120)}</MeaningLabel>
                ) : null}
                {offer.reason && offer.kind === "passages" ? <MeaningLabel>({OFFER_COPY.reasonLabel})</MeaningLabel> : null}
                {isPressed && lookup?.phase === "failed" ? <MeaningLabel>{OFFER_COPY.failed}</MeaningLabel> : null}
                {isPressed && lookup?.phase === "unchecked" ? (
                  <span data-offer-unchecked="">
                    <MeaningLabel>
                      {OFFER_COPY.unchecked}{lookup.because ? ` (${lookup.because})` : ""} — {OFFER_COPY.tryAgain}
                    </MeaningLabel>
                  </span>
                ) : null}
              </span>
            ) : lookup === undefined || lookup.phase === "loading" ? (
              <MeaningLabel>
                <span aria-hidden="true">◐</span> {offer.kind === "compare" ? OFFER_COPY.comparing : OFFER_COPY.looking}…
              </MeaningLabel>
            ) : (
              <OfferResult offer={offer} lookup={lookup} onPracticePick={props.onPracticePick ?? null}
                exercises={props.exercises ?? null} extractionId={props.extractionId} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function OfferResult({ offer, lookup, onPracticePick, exercises, extractionId }: {
  offer: Offer; lookup: Lookup; onPracticePick: TutorOffersProps["onPracticePick"];
  exercises: LibraryExercisesProps | null; extractionId: string;
}) {
  if (offer.kind === "practice") {
    const withExercises = Boolean(exercises && lookup.practice);
    return (
      <ModelVoice note={`${OFFER_COPY.practice}${offer.reason ? ` · ${clip(offer.reason, 80)}` : ""}`}>
        {(lookup.items ?? []).length || !withExercises ? (
          <ul aria-label="practice for this question" style={{ margin: 0, paddingLeft: 16 }}>
            {(lookup.items ?? []).map((item) => (
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
        ) : null}
        {exercises && lookup.practice ? (
          <ProposalExercises
            practice={lookup.practice}
            itemsShown={(lookup.items ?? []).length}
            exercises={exercises}
            query={offer.practice?.request.query ?? ""}
            learningObjectIds={offer.practice?.request.learningObjectIds ?? []}
            extractionId={extractionId ?? null}
          />
        ) : null}
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
  return (
    <ModelVoice note="how your books treat this · LearnLoop's comparison">
      {lookup.table ? <CompareTable table={lookup.table} /> : null}
      {/* RW4d: keep the tutor's comparison (renders nothing while keep is off). */}
      {lookup.table && offer.toolCallId ? (
        <CompareKeep table={lookup.table} target={{ toolCallId: offer.toolCallId, extractionId }} />
      ) : null}
      {lookup.missingPerspectives?.length ? (
        <span data-missing-perspectives="">
          <MeaningLabel style={{ fontSize: 11 }}>
            {OFFER_COPY.notCovered}: {lookup.missingPerspectives.join(", ")}
          </MeaningLabel>
        </span>
      ) : null}
    </ModelVoice>
  );
}
