// The phone Reader (mobile v2 §3; owner decision D4): the book's extracted text, one section at a time, in the
// book's face, with KaTeX math; the original page as the host's image on demand; progress, activity and the
// end of a section recorded exactly as the desktop's Reader records them, through the outbox (§5.4), so a
// section read on the train counts when the phone is back in reach.
//
// What the host withholds never reaches this screen (a held-out passage arrives with no text and says so),
// and a selection on it offers no Ask, by the desktop's own rule.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { CommandError, ReaderDoseOfferDto, ReaderGuidePlanDto, ReaderProgressListDto } from "@desktop/api/dto";
import { accrueVisit, visitSeconds, type VisitClock } from "@desktop/screens/reader/visitClock";
import { phone, type PhoneReaderBlock, type PhoneSectionDto } from "../api/phone";
import { addReaderIntent, flushOutbox } from "../store/outbox";
import { newUlid } from "../util/ulid";
import { PageImage, PhoneMarkdown } from "./PageImage";
import { cachedGuide, cachedSection, loadGuide, loadProgress, loadSection, prefetchSection, rememberPlace } from "./readerCache";
import { nextSectionId, resumeSection, selectionProtected } from "./readerModel";
import { SectionList } from "./SectionList";
import { SelectionSheet, type PhoneSelection } from "./SelectionSheet";

/** How long the Reader waits after the last span came into view before it reports progress (a `keep` bound:
 *  a report per pause in scrolling, not per span). */
export const PROGRESS_DEBOUNCE_MS = 1500;

export interface ReaderTarget {
  readonly extractionId: string;
  readonly sourceId: string | null;
  readonly title: string;
  /** A section to open (the plan's reading block, a section picked from the list); else *Continue reading*. */
  readonly sectionId?: string | null;
  /** Opened by the plan's reading block (DL1 §6.10): *Back to today's plan* ends it as the desktop's banner does. */
  readonly plan?: { readonly sessionId: string | null; readonly sectionTitle: string | null } | null;
}

export function ReaderScreen({
  target,
  onSection,
  onPlanBack,
  onError
}: {
  target: ReaderTarget;
  /** The open section, for the URL fragment (§4.2). */
  onSection?: (sectionId: string | null) => void;
  /** The plan's reading was left (`left_reader`), skipped or finished: Today takes over. */
  onPlanBack: () => void;
  onError: (error: unknown) => void;
}) {
  const { extractionId } = target;
  const [guide, setGuide] = useState<ReaderGuidePlanDto | null>(null);
  const [progress, setProgress] = useState<ReaderProgressListDto | null>(null);
  const [sectionId, setSectionId] = useState<string | null>(target.sectionId ?? null);
  const [section, setSection] = useState<PhoneSectionDto | null>(null);
  const [stale, setStale] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [listOpen, setListOpen] = useState(false);
  const [selection, setSelection] = useState<PhoneSelection | null>(null);
  const [pageOf, setPageOf] = useState<string | null>(null);
  const [dose, setDose] = useState<ReaderDoseOfferDto["offer"] | null>(null);
  const [leaving, setLeaving] = useState(false);
  const visitId = useMemo(() => newUlid(), [extractionId]);
  const seen = useRef<Set<string>>(new Set());
  const reported = useRef<Record<string, number>>({});
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const body = useRef<HTMLDivElement>(null);

  // §3.4: activity carries its own `occurredAt`, so the outbox keeps its time (RO0 row 5).
  const activity = useCallback((kind: string, payload: Record<string, unknown>) => {
    void addReaderIntent({
      id: newUlid(), method: "reader.log_activity",
      params: { events: [{ kind, occurredAt: new Date().toISOString(), payload: { visitId, extractionId, ...payload } }] }
    }).then(() => flushOutbox()).catch(() => undefined);
  }, [extractionId, visitId]);

  // The visit, as the desktop's Reader records it (`useReaderVisit`; Codex review F8): opened with its surface, its
  // book, whether Ask is there and who sent the learner here (RO0 rows 3, 4), and closed with its active and idle
  // seconds on the desktop's own clock (`visitClock`), which the router's activity clock reads.
  const clock = useRef<VisitClock | null>(null);
  const touch = useCallback(() => {
    if (clock.current) accrueVisit(clock.current, Date.now());
  }, []);
  const initiator = target.plan ? "plan" : "learner";
  useEffect(() => {
    const visit: VisitClock = { lastActive: Date.now(), active: 0, idle: 0 };
    clock.current = visit;
    activity("reader_view_opened", {
      surface: "text", sourceId: target.sourceId, initiator,
      askAvailable: typeof navigator === "undefined" || navigator.onLine !== false
    });
    return () => {
      accrueVisit(visit, Date.now());
      const seconds = visitSeconds(visit);
      activity("reader_view_closed", { activeSeconds: seconds.active_seconds, idleSeconds: seconds.idle_seconds });
      if (clock.current === visit) clock.current = null;
    };
    // One visit per opened book (its visit id); the book's source and who opened it don't start another.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activity]);

  // The section list and the shared reading history: where *Continue reading* lands.
  useEffect(() => {
    let cancelled = false;
    void cachedGuide(extractionId).then((cached) => {
      if (cancelled || !cached.guide) return;
      const kept = cached.guide;
      setGuide((current) => current ?? kept);
      setProgress((current) => current ?? cached.progress);
      setSectionId((current) => current ?? resumeSection(kept.sections, cached.progress));
    });
    (async () => {
      try {
        const [loaded, history] = await Promise.all([loadGuide(extractionId), loadProgress(extractionId)]);
        if (cancelled) return;
        setGuide(loaded.guide);
        setProgress(history);
        setSectionId((current) => current ?? resumeSection(loaded.guide.sections, history));
      } catch (error) {
        if (cancelled) return;
        const command = error as CommandError;
        if (command?.code === "desktop_offline") {
          // The list kept on this phone stays; with none, say when the book opens.
          setGuide((current) => {
            if (!current) setProblem("This book isn't on this phone yet. It opens when the desktop is reachable.");
            return current;
          });
        } else {
          setGuide(null);
          setProblem(command?.code === "held_out_material" ? command.message : "This book couldn't be opened.");
        }
        onError(error);
      }
    })();
    return () => {
      cancelled = true;
    };
    // Once per book.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [extractionId]);

  const sections = guide?.sections ?? [];
  const current = sections.find((one) => one.id === sectionId) ?? null;
  const following = sectionId ? nextSectionId(sections, sectionId) : null;

  useEffect(() => {
    onSection?.(sectionId);
  }, [onSection, sectionId]);

  // §3.2: the open section, from the host or the display cache, and the next one prefetched.
  useEffect(() => {
    if (!sectionId) return undefined;
    let cancelled = false;
    setSection(null);
    setProblem(null);
    seen.current = new Set();
    setDose(null);
    // §4.5: the copy on this phone at once, then the host's (which replaces it, and drops it if a mark changed).
    void cachedSection(extractionId, sectionId).then((cached) => {
      if (cancelled || !cached) return;
      setSection((current) => current ?? cached);
      setStale((current) => current || true);
    });
    loadSection(extractionId, sectionId).then(
      (loaded) => {
        if (cancelled) return;
        setSection(loaded.section);
        setStale(loaded.stale);
        rememberPlace({ extractionId, sectionId, spanId: null, title: target.title, sourceId: target.sourceId });
        body.current?.scrollTo?.({ top: 0 });
      },
      (error) => {
        if (cancelled) return;
        const command = error as CommandError;
        if (command?.code === "desktop_offline") {
          // The copy on this phone, if there is one, stays on screen and says so.
          setSection((current) => {
            if (!current) setProblem("This section isn't on this phone yet. It opens when the desktop is reachable.");
            return current;
          });
          return;
        }
        // Refused now (a new mark, say): nothing kept of it is shown.
        setSection(null);
        setProblem(command?.code === "held_out_material" ? command.message : "This section couldn't be opened.");
      }
    );
    return () => {
      cancelled = true;
    };
  }, [extractionId, sectionId, target.title, target.sourceId]);

  // One section ahead, into the display cache, once the open one is here (never the whole book, §5.4).
  const loadedId = section ? sectionId : null;
  useEffect(() => {
    if (loadedId && following) void prefetchSection(extractionId, following);
  }, [extractionId, loadedId, following]);

  const readable = useMemo(() => new Set(current?.spanIds ?? []), [current]);

  /** §3.4: progress as the desktop reports it: how many of the section's spans were seen, debounced, monotonic. */
  const report = useCallback((completed: boolean) => {
    if (!current) return;
    const spansSeen = completed ? current.spanIds.length : Math.min(seen.current.size, current.spanIds.length);
    const before = reported.current[current.id] ?? 0;
    if (!completed && spansSeen <= before) return;
    reported.current[current.id] = Math.max(before, spansSeen);
    void addReaderIntent({
      id: newUlid(), method: "reader.mark_section_progress", coalesce: `${extractionId}:${current.id}`,
      params: { extractionId, sectionId: current.id, spansSeen, spanCount: current.spanIds.length, ...(completed ? { completed: true } : {}) }
    }).then(() => flushOutbox()).catch(() => undefined);
    setProgress((list) => {
      const rows = list?.sections ?? [];
      const row = rows.find((one) => one.sectionId === current.id);
      const next = { extractionId, sectionId: current.id, spansSeen: Math.max(row?.spansSeen ?? 0, spansSeen),
        spanCount: current.spanIds.length, revealedAt: row?.revealedAt ?? null,
        completedAt: row?.completedAt ?? (completed ? new Date().toISOString() : null), generationBatchId: row?.generationBatchId ?? null };
      return { extractionId, sections: [...rows.filter((one) => one.sectionId !== current.id), next] };
    });
  }, [current, extractionId]);

  // A span is seen when it scrolls into view.
  useEffect(() => {
    const root = body.current;
    if (!root || !section || typeof IntersectionObserver === "undefined") return undefined;
    const observer = new IntersectionObserver((entries) => {
      touch();
      for (const entry of entries) {
        const span = (entry.target as HTMLElement).dataset.span;
        if (entry.isIntersecting && span && readable.has(span)) seen.current.add(span);
      }
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => report(false), PROGRESS_DEBOUNCE_MS);
    });
    for (const node of root.querySelectorAll<HTMLElement>("[data-span]")) observer.observe(node);
    return () => {
      observer.disconnect();
      if (timer.current) clearTimeout(timer.current);
    };
  }, [section, readable, report, touch]);

  /** The foot of a section: it is finished, the dose arm draws (the server's, before anything shows), then on. */
  async function finishSection() {
    if (!current) return;
    report(true);
    let offer: ReaderDoseOfferDto["offer"] | null = null;
    try {
      offer = (await phone.doseOffer(extractionId, current.id, visitId)).offer ?? null;
    } catch {
      offer = null; // Offline: no dose is drawn (§3.4); the section's progress waits in the outbox.
    }
    if (offer) {
      setDose(offer);
      doseEvent(offer.drawId, "delivered");
      return;
    }
    goOn();
  }

  function doseEvent(drawId: string, event: "delivered" | "taken" | "dismissed" | "not_delivered") {
    void addReaderIntent({ id: newUlid(), method: "reader.dose_offer_event", params: { drawId, event } })
      .then(() => flushOutbox()).catch(() => undefined);
  }

  function goOn() {
    setDose(null);
    if (target.plan) {
      // The plan's reading ended with the section (the host records `section_completed` from the progress).
      onPlanBack();
      return;
    }
    if (following) setSectionId(following);
  }

  /** The desktop's banner (`left_reader`) and its skip (`skipped`): the block ends, its estimate counts as used. */
  async function backToPlan(outcome: "left_reader" | "skipped" = "left_reader") {
    if (leaving) return;
    setLeaving(true);
    try {
      await phone.planReadingEnded(outcome, target.plan?.sessionId ?? null);
    } catch (error) {
      onError(error);
    } finally {
      setLeaving(false);
      onPlanBack();
    }
  }

  /** The extra was taken: a worked example opens where it is; a question stays on screen to try. */
  function takeDose(offer: NonNullable<ReaderDoseOfferDto["offer"]>) {
    doseEvent(offer.drawId, "taken");
    if (offer.variant !== "extra_worked_example") return;
    const span = offer.content.spanId;
    const holder = span ? sections.find((one) => one.spanIds.includes(span)) : null;
    setDose(null);
    if (holder && holder.id !== sectionId) setSectionId(holder.id);
    else if (!holder) goOn();
  }

  function onSelectEnd() {
    touch();
    const picked = readSelection(body.current);
    if (picked) setSelection(picked);
  }

  const askOff = selection ? selectionProtected(section?.protection, selection.spanIds) : false;

  return (
    <div className="screen reader">
      {target.plan ? (
        <div className="banner" role="status">
          <div>Reading for today's plan · {target.plan.sectionTitle ?? current?.label ?? "this section"}</div>
          <div className="row">
            <button className="plain" type="button" disabled={leaving} onClick={() => void backToPlan()}>Back to today's plan</button>
            <button className="plain" type="button" disabled={leaving} onClick={() => void backToPlan("skipped")}>Skip this reading</button>
          </div>
        </div>
      ) : null}
      <div className="reader-head">
        <button className="link" type="button" onClick={() => setListOpen(true)} aria-label="Sections">
          {current?.label ?? target.title}
        </button>
        {stale ? <span className="dim">· the copy on this phone</span> : null}
      </div>
      {problem ? <p className="dim" role="status">{problem}</p> : null}
      {!section && !problem ? <p className="dim" role="status">Opening the section…</p> : null}
      {section ? (
        <div className="book" ref={body} onMouseUp={onSelectEnd} onTouchEnd={onSelectEnd} onScroll={touch}>
          {section.blocks.map((block) => (
            <Block key={block.displayNodeId} block={block} extractionId={extractionId}
              pageOpen={pageOf === block.displayNodeId} onPage={() => setPageOf((open) => open === block.displayNodeId ? null : block.displayNodeId)} />
          ))}
        </div>
      ) : null}
      {dose ? (
        <DoseOffer offer={dose} onTake={() => takeDose(dose)} onDismiss={() => { doseEvent(dose.drawId, "dismissed"); goOn(); }}
          onDone={goOn} onError={onError} />
      ) : section ? (
        <div className="actions">
          <button className="primary block" type="button" onClick={() => void finishSection()}>
            {target.plan ? "Done with this section" : following ? "Next section" : "Finish the book's last section"}
          </button>
        </div>
      ) : null}
      {listOpen && guide ? (
        <SectionList sections={sections} progress={progress} current={sectionId}
          onPick={(id) => { setListOpen(false); setSectionId(id); }} onClose={() => setListOpen(false)} />
      ) : null}
      {selection && section ? (
        <SelectionSheet selection={selection} section={section} askOff={askOff}
          protectionMessage={section.protection?.message ?? null} onClose={() => setSelection(null)} onError={onError} />
      ) : null}
    </div>
  );
}

type DoseOfferContent = NonNullable<ReaderDoseOfferDto["offer"]>;
type OfferedQuestion = NonNullable<DoseOfferContent["question"]>;

/** §3.4: the dose arm's offer, as the desktop words it, with its glass-box line. Help, never evidence. The offer
 *  comes first and shows nothing of the extra; a taken question is then the desktop's quick check (Codex review F9:
 *  `DoseOffer` opens `AuthoredQuestionCard`), answered in the learner's words before the intended answer shows. */
function DoseOffer({ offer, onTake, onDismiss, onDone, onError }: {
  offer: DoseOfferContent;
  onTake: () => void;
  onDismiss: () => void;
  onDone: () => void;
  onError: (error: unknown) => void;
}) {
  const [taken, setTaken] = useState(false);
  const question = offer.variant === "extra_question" ? offer.question ?? null : null;
  if (taken && question) return <ExtraQuestion question={question} onDone={onDone} onError={onError} />;
  return (
    <div className="banner dose" role="status">
      <p>{offer.text}</p>
      <p className="dim">{offer.why}</p>
      <div className="row">
        <button className="primary" type="button" onClick={() => { onTake(); if (question) setTaken(true); }}>
          {question ? "Try it" : "Show me"}
        </button>
        <button className="plain" type="button" onClick={onDismiss}>Not now</button>
      </div>
    </div>
  );
}

/** The desktop's quick-check card for the extra question the draw chose: optional, a self-check, never a grade.
 *  *Compare with the source* records the learner's answer on the question (`reader.authored_question_action`,
 *  `answered`) and only then shows the intended one beside it; *Skip* records nothing, as the desktop's does. */
function ExtraQuestion({ question, onDone, onError }: {
  question: OfferedQuestion;
  onDone: () => void;
  onError: (error: unknown) => void;
}) {
  const [response, setResponse] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [busy, setBusy] = useState(false);
  async function compare() {
    const words = response.trim();
    if (!words || busy) return;
    setBusy(true);
    try {
      await phone.authoredQuestionAction(question.questionId, words);
      setSubmitted(true);
    } catch (error) {
      onError(error);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="banner dose" role="group" aria-label="Quick check">
      <p className="dim">Quick check · optional, a self-check, never a grade</p>
      <p className="dim">One more question on this section, offered at random.</p>
      <div className="markdown"><PhoneMarkdown value={question.prompt} /></div>
      {!submitted ? (
        <>
          <textarea aria-label="Your answer" value={response} placeholder="Answer in your own words…"
            onChange={(event) => setResponse(event.target.value)} />
          <div className="row">
            <button className="primary" type="button" disabled={busy || !response.trim()} onClick={() => void compare()}>
              Compare with the source
            </button>
            <button className="plain" type="button" disabled={busy} onClick={onDone}>Skip</button>
          </div>
        </>
      ) : (
        <>
          <p className="dim">› your answer</p>
          <p className="learner-words">{response.trim()}</p>
          <p className="dim">◇ the intended answer · compare, don't grade</p>
          <div className="markdown"><PhoneMarkdown value={question.expectedAnswer} /></div>
          <div className="actions"><button className="primary block" type="button" onClick={onDone}>Done for now</button></div>
        </>
      )}
    </div>
  );
}

function Block({ block, extractionId, pageOpen, onPage }: {
  block: PhoneReaderBlock & { page?: number | null };
  extractionId: string;
  pageOpen: boolean;
  onPage: () => void;
}) {
  const page = typeof block.page === "number" ? block.page : null;
  if (block.withheld) {
    return <p className="dim withheld" data-span={block.spanId ?? undefined}>A passage held out for your exam. It isn't shown here.</p>;
  }
  const view = block.health?.recommendedView ?? "derived";
  // §3.1: a block whose text doesn't read well shows its page instead, and says so; never garbled text silently.
  if (view === "crop_default" && page !== null) {
    return (
      <figure className="as-printed" data-span={block.spanId ?? undefined}>
        <PageImage ref_={extractionId} page={page} />
        <figcaption className="dim">as printed</figcaption>
      </figure>
    );
  }
  return (
    <div className="block" data-span={block.spanId ?? undefined}>
      <div className="markdown book-text"><PhoneMarkdown value={block.markdown} /></div>
      {page !== null ? (
        <button className="link quiet" type="button" aria-expanded={pageOpen} onClick={onPage}>
          {view === "warn_link" ? "This text may not read well · View the page" : "View the page"}
        </button>
      ) : null}
      {pageOpen && page !== null ? <PageImage ref_={extractionId} page={page} alt={view === "derived" ? block.markdown : null} /> : null}
    </div>
  );
}

/** The selected passages, by their blocks' spans (the server checks they are this reading's, §3.5). */
function readSelection(root: HTMLElement | null): PhoneSelection | null {
  if (!root || typeof window.getSelection !== "function") return null;
  const picked = window.getSelection();
  const quote = picked?.toString().trim() ?? "";
  if (!picked || !quote || picked.rangeCount === 0) return null;
  const range = picked.getRangeAt(0);
  const spans: string[] = [];
  for (const node of root.querySelectorAll<HTMLElement>("[data-span]")) {
    if (range.intersectsNode(node) && node.dataset.span) spans.push(node.dataset.span);
  }
  return spans.length ? { spanIds: spans, quote } : null;
}
