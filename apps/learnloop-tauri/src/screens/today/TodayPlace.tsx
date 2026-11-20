// UX Phase 3: Today in the simple shell (docs/specs/ux_learnloop_v1.md §7.1,
// wireframe W4, §10 3.1-3.4). Start and Today merged into one place:
//
//   Tuesday evening                              10m  15m [25m] 40m  60m
//   Up to 25 minutes today. Planned so far: finish §5.4 Mixtures, then 6
//   short questions from earlier days and a fix for a mix-up.     why? ▸
//   ▸ Continue §5.4 Mixtures                               about 12 min
//     6 short questions · Conditional probability           about 8 min
//                                                          [ Begin ↵ ]
//   Pick up a thread
//   4 days · best 9                              all of today's list (l)
//
// The plan is minutes; there is no count of waiting things anywhere (§4.2
// rule 10): no due, probe, later or follow-up tiles, no queue size, no
// overdue list. Re-entry after a break is a short plan with no debt screen.
// The lanes, the split, each block's reasons and the knowledge headline are
// behind why? (layer 2). Begin, the minutes and keep going call exactly the
// RPCs classic's Start and Today call: nothing about what is served changes.
// Classic keeps StartScreen and TodayScreen as they were; only the simple
// shell mounts this place (app/App.tsx).

import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { api } from "../../api/client";
import { TAG } from "../../api/queryTags";
import { useCachedQuery } from "../../api/useCachedQuery";
import type {
  AiConnectionDto,
  DailyPlanDto,
  GoalDto,
  OpenLessonDto,
  PlanLessonOfferStepDto,
  PlanReadingDto,
  PlanStepDto,
  QueueSnapshot,
  ScheduledItemDto,
  SessionEndSummary,
  SessionSnapshot,
  SomethingElseChosenDto,
  SourceLibraryCard,
  StreakSummary,
  WorkbenchOpenProblemDto
} from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { GoalCard } from "../../components/GoalCard";
import { GoalWizard } from "../../components/GoalWizard";
import { Waiting } from "../../components/Waiting";
import { WAITING_COPY } from "../../copy/waiting";
import { InboxStrip } from "../../components/InboxStrip";
import { targetForDialogue } from "../../components/QuestionQueue";
import type { AskTarget } from "../../components/AskOverlay";
import { INTERACTIVE_SELECTOR, screenLeavesKey } from "../../app/keymap";
import { subscribeQueueChanged } from "../../queueEvents";
import { algoConfig } from "../../app/algoConfig";
import { LessonOfferBlock } from "./LessonOfferBlock";
import { lessonEntryFor, SomethingElse } from "./SomethingElse";
import { LessonSuggestionCard } from "./LessonSuggestionCard";
import { QuestionInProgress } from "./QuestionInProgress";
import type { LessonEntry } from "../LessonScreen";
import { todayQueueInput } from "../../app/autoAdvance";
import { aboutMinutes, planStepAction, questionInProgressLine, useDailyPlan, waitingLine } from "../../app/dailyPlan";
import {
  THREADS_SHOWN,
  dayPhrase,
  doneLine,
  fullListWhy,
  onYourOwnWhy,
  planSentence,
  GOAL_NOTHING_READY,
  planWasEmpty,
  reentrySentence,
  reentryWhy,
  splitWhy,
  streakLine,
  todayRows,
  todayThreads,
  type TodayThread
} from "../../app/todayPlan";
import { errorMessage, type ErrorReport } from "../../errors";
import {
  GOAL_NOT_UP_TODAY,
  KEEP_GOING_NOTHING_LEAD,
  PLAN_FINISHED,
  PLAN_STOPPED_WITH_MORE,
  WHATS_SENT,
  causeActionLabel,
  causeWait,
  causeSendsPassages,
  causeSentence,
  continueLessonLine,
  goalCauseSentence,
  todayCause,
  type TodayCause
} from "../../app/todayCause";

export interface TodayPlaceProps {
  session: SessionSnapshot | null;
  /** The streak as of vault load; the plan's fresher copy wins. */
  streak: StreakSummary | null;
  /** Begin started a session (and maybe served its first step). */
  onBeginSession: (session: SessionSnapshot, firstStep?: PlanStepDto | null) => void;
  /** Start a session for these minutes (fix round 2, F1/F7): the shell owns
   *  the start. It is the shell's session as soon as it answers, kept when
   *  Today is left on the same vault; null when it was not started, or a vault
   *  change made it obsolete. */
  onStartSession: (minutes: number) => Promise<SessionSnapshot | null>;
  onOpenPractice: (practiceItemId: string, schedulerCandidateId?: string | null, proposalOrigin?: null, planPresentationId?: string | null) => void;
  onOpenPlanReading: (reading: PlanReadingDto) => void;
  onEndSession: (summary: SessionEndSummary) => void;
  /** The shell's Add (first run: nothing to plan yet). */
  onAdd: () => void;
  /** Open a book at a passage (an open question's place), on the reading the
   *  passage was found on (fix round 1, F3). */
  onOpenPassage: (sourceId: string, spanId: string | null, reading: string | null) => void;
  /** Resume an unfinished problem in its book. */
  onResumeProblem: (problem: WorkbenchOpenProblemDto) => void;
  onAsk: (target: AskTarget) => void;
  onTakeExam?: (goalId: string) => void;
  subjects?: { id: string; title: string }[];
  /** RW6a's wrap-up offer, when the shell armed it for this view. */
  wrapUp?: ReactNode;
  /** Teacher TE1b: Start on Today's lesson suggestion card opens this lesson (absent: no card). */
  onStartLesson?: (entry: LessonEntry) => void;
  /** Begin served a lesson offer as the plan's first step: the shell opens the offer's own page (the one feedback's
   *  Next opens), so the press shows something. Without it the press only turned Begin into Continue. */
  onLessonOffer?: (step: PlanLessonOfferStepDto) => void;
  /** A lesson is on screen over Today. Its closing is when an open lesson may have been left, so Today reads them
   *  again then. */
  lessonOpen?: boolean;
  /** UX fix stage 3 (audit P1): what an empty Today's cause line acts with.
   *  The AI connection says which OK is missing and what is sent. */
  aiConnection?: AiConnectionDto | null;
  /** The one-time OK, or connecting an AI: the shelf's own sheet. */
  onConnectAi?: () => void;
  /** Open a book in the Reader, as its card's Continue does. */
  onOpenBook?: (card: SourceLibraryCard) => void;
  /** Go to the Library's books, where a card asks for something Today can't do. */
  onOpenLibrary?: () => void;
  onError: (message: string, report?: ErrorReport) => void;
}

/** An action's step after Today unmounted (fix round 1, F1), or a start the
 *  shell did not make (fix round 2): stop, quietly. */
const LEFT = Symbol("today-left");

const linkButton: CSSProperties = {
  border: 0,
  background: "transparent",
  color: COLOR.amberLink,
  cursor: "pointer",
  fontFamily: FONT_MONO,
  fontSize: 12,
  padding: "0 4px"
};

const dimLink: CSSProperties = { ...linkButton, color: COLOR.textDim };

/** How often an empty day's cause is read again while a book's questions are
 *  on their way (the shelf reads its cards every 3 s while one works). */
const CAUSE_POLL_MS = 5000;

function actionButton(primary = false): CSSProperties {
  return {
    padding: "6px 16px",
    border: `1px solid ${primary ? COLOR.amber : COLOR.border}`,
    background: primary ? "var(--wash-amber)" : "transparent",
    color: primary ? COLOR.amber : COLOR.text,
    cursor: "pointer",
    fontFamily: FONT_MONO,
    fontSize: 12
  };
}

function MinuteChips({ value, choices, disabled, onChange }: { value: number | null; choices: number[]; disabled?: boolean; onChange: (minutes: number) => void }) {
  return (
    <div role="radiogroup" aria-label="minutes today" style={{ display: "flex", gap: 6, flexWrap: "wrap", opacity: disabled ? 0.5 : 1 }}>
      {choices.map((minutes) => {
        const selected = minutes === value;
        return (
          <span
            key={minutes}
            role="radio"
            aria-checked={selected}
            onClick={() => !selected && !disabled && onChange(minutes)}
            style={{
              padding: "3px 10px",
              border: `1px solid ${selected ? COLOR.amber : COLOR.border}`,
              background: selected ? "var(--wash-amber)" : "transparent",
              color: selected ? COLOR.amber : COLOR.text,
              cursor: "pointer",
              fontSize: 12,
              fontFamily: FONT_MONO
            }}
          >
            {minutes}m
          </span>
        );
      })}
    </div>
  );
}

/** Fix round 1 (F2): Enter aimed at a control (a button, a link, a field)
 *  is that control's own: it activates what has the focus (why?, skip, a
 *  thread's resume, Something new), never the page's Begin or the list's
 *  open. The page's Enter is for the page itself. */
function enterOnControl(event: KeyboardEvent): boolean {
  return event.target instanceof Element && event.target.closest(INTERACTIVE_SELECTOR) !== null;
}

function stepChoice(choices: number[], current: number | null, delta: number): number | undefined {
  if (current === null || choices.length === 0) return undefined;
  const index = choices.indexOf(current);
  return choices[Math.max(0, Math.min(choices.length - 1, (index < 0 ? 0 : index) + delta))];
}

/** The plan's why? (layer 2): the re-entry, the split in words, each block's reason. */
function PlanWhy({ data }: { data: DailyPlanDto }) {
  const plan = data.plan;
  const headline = useCachedQuery(data.headlineEnabled === false ? null : ["get_today_headline"], () => api.getTodayHeadline(), {
    tags: [TAG.queue, TAG.graph]
  });
  if (!plan) return null;
  const rows = todayRows(plan);
  const reentry = plan.kind === "reentry" ? reentryWhy(plan) : null;
  const split = splitWhy(plan);
  const line = headline.data?.enabled ? headline.data.line ?? null : null;
  return (
    <div data-testid="today-why" style={{ fontSize: 12, color: COLOR.textDim, lineHeight: 1.6, borderLeft: `2px solid ${COLOR.border}`, paddingLeft: 10 }}>
      {reentry ? <p style={{ margin: "0 0 6px" }}>{reentry}</p> : null}
      {split.length ? (
        <>
          <div>How today's minutes are split:</div>
          <ul style={{ margin: "2px 0 6px", paddingLeft: 18 }}>
            {split.map((entry) => (
              <li key={entry}>{entry}</li>
            ))}
          </ul>
        </>
      ) : null}
      {rows.some((row) => row.why) ? (
        <ul style={{ margin: "2px 0 6px", paddingLeft: 18 }}>
          {rows
            .filter((row) => row.why)
            .map((row) => (
              <li key={row.key}>
                {row.text}: {row.why}
                {row.whyDetails ? (
                  <details style={{ marginTop: 2 }}>
                    <summary style={{ cursor: "pointer" }}>details ▸</summary>
                    {row.whyDetails}
                  </details>
                ) : null}
              </li>
            ))}
        </ul>
      ) : null}
      {line ? (
        <details>
          <summary style={{ cursor: "pointer" }}>details ▸</summary>
          <span title={headline.data?.expectedRecallTooltip}>{line}</span>
        </details>
      ) : null}
    </div>
  );
}

/** "Pick up a thread": open questions, unfinished problems, the wrap-up. No counts. */
function Threads({
  wrapUp,
  onOpenPassage,
  onResumeProblem,
  onAsk
}: {
  wrapUp?: ReactNode;
  onOpenPassage: TodayPlaceProps["onOpenPassage"];
  onResumeProblem: TodayPlaceProps["onResumeProblem"];
  onAsk: TodayPlaceProps["onAsk"];
}) {
  const questions = useCachedQuery(["list_question_queue", "today-threads"], () => api.listQuestionQueue(), { tags: [TAG.queue] });
  const problems = useCachedQuery(["workbench_open_problems"], () => api.workbenchOpenProblems(), { tags: [TAG.queue] });
  const [more, setMore] = useState(false);
  // The threads are ambient: a failed read shows nothing, never an error.
  const threads = useMemo(
    () =>
      todayThreads(questions.data?.questions ?? [], problems.data?.problems ?? []).filter(
        (thread) => thread.kind === "problem" || threadAction(thread) !== null
      ),
    [questions.data, problems.data]
  );

  function threadAction(thread: TodayThread): { label: string; run: () => void } | null {
    if (thread.kind === "problem") return { label: "resume ▸", run: () => onResumeProblem(thread.problem) };
    const citation = thread.question.sourceCitation;
    if (citation?.sourceId) return { label: "open in book ▸", run: () => onOpenPassage(citation.sourceId as string, citation.spanId, citation.extractionId ?? null) };
    const target = targetForDialogue(thread.question);
    return target ? { label: "continue ▸", run: () => onAsk(target) } : null;
  }

  if (threads.length === 0) return <>{wrapUp ?? null}</>;
  const shown = more ? threads : threads.slice(0, THREADS_SHOWN);
  return (
    <section aria-label="Pick up a thread" data-testid="today-threads" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <div style={{ fontSize: 12, color: COLOR.textDim }}>Pick up a thread</div>
      {shown.map((thread) => {
        const act = threadAction(thread);
        return (
          <div key={thread.key} data-testid="today-thread" style={{ display: "flex", gap: 8, alignItems: "baseline", fontSize: 13 }}>
            <span style={{ color: COLOR.textFaint, fontFamily: FONT_MONO }}>{thread.kind === "question" ? "?" : "✎"}</span>
            <span style={{ flex: 1, minWidth: 0, color: COLOR.text, overflowWrap: "anywhere" }}>
              {thread.text}
              {thread.kind === "question" && thread.place ? <span style={{ color: COLOR.textFaint }}> · {thread.place}</span> : null}
              {thread.kind === "problem" ? <span style={{ color: COLOR.textFaint }}> — {thread.steps}</span> : null}
            </span>
            {act ? (
              <button type="button" style={linkButton} onClick={act.run}>
                {act.label}
              </button>
            ) : null}
          </div>
        );
      })}
      {wrapUp ?? null}
      {!more && threads.length > THREADS_SHOWN ? (
        <button type="button" style={{ ...dimLink, alignSelf: "flex-start", padding: 0 }} onClick={() => setMore(true)}>
          more ▸
        </button>
      ) : null}
    </section>
  );
}

/** One line, only when there are captures to look at; it opens the inbox. */
function CapturesLine({ subjects, onAsk }: { subjects: { id: string; title: string }[]; onAsk: (target: AskTarget) => void }) {
  const summary = useCachedQuery(["get_inbox_summary", "today"], () => api.getInboxSummary(), { tags: [TAG.queue] });
  const [open, setOpen] = useState(false);
  const data = summary.data;
  const something = Boolean(data && ((data.newCount ?? 0) > 0 || (data.deletePending?.length ?? 0) > 0 || data.vaultMismatch));
  if (!something && !open) return null;
  // Fix round 1 (F5): the learner's inbox, with no count of what is waiting
  // (§4.2 rule 10); classic's strip keeps its counts.
  if (open) return <InboxStrip subjects={subjects} onAsk={onAsk} countFree />;
  return (
    <button type="button" data-testid="today-captures" style={{ ...dimLink, alignSelf: "flex-start", padding: 0 }} onClick={() => setOpen(true)}>
      New captures ▸
    </button>
  );
}

/** The full list (`l`): titles, minutes where the plan estimates them, and
 *  why each is there in a few words. No ids, modes, mastery or priorities. */
function PlainList({
  queue,
  plan,
  busy,
  failed,
  onRetry,
  onOpen,
  onBack
}: {
  queue: QueueSnapshot | null;
  plan: DailyPlanDto["plan"] | null;
  busy: boolean;
  /** Fix round 1 (F6): the list's read failed (with `queue`, its refresh). */
  failed: boolean;
  /** Try the read again (the query's own self-contained retry). */
  onRetry: () => void;
  onOpen: (item: ScheduledItemDto) => void;
  onBack: () => void;
}) {
  const items = useMemo(() => queue?.sections.flatMap((section) => section.items) ?? [], [queue]);
  const minutesOf = useMemo(() => {
    const map = new Map<string, number>();
    for (const block of plan?.blocks ?? []) for (const item of block.items) map.set(item.practiceItemId, item.estMinutes);
    return map;
  }, [plan]);
  const [focus, setFocus] = useState(0);
  const [why, setWhy] = useState<string | null>(null);
  useEffect(() => {
    setFocus((index) => Math.min(index, Math.max(0, items.length - 1)));
  }, [items.length]);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (screenLeavesKey(event)) return;
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea" || event.defaultPrevented) return;
      if (event.key === "j" || event.key === "ArrowDown") {
        event.preventDefault();
        setFocus((index) => Math.min(items.length - 1, index + 1));
      } else if (event.key === "k" || event.key === "ArrowUp") {
        event.preventDefault();
        setFocus((index) => Math.max(0, index - 1));
      } else if (event.key === "Enter") {
        if (enterOnControl(event)) return;
        event.preventDefault();
        const item = items[focus];
        if (item && !busy) onOpen(item);
      } else if (event.key === "p" || event.key === "Escape") {
        event.preventDefault();
        onBack();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [busy, focus, items, onBack, onOpen]);

  return (
    <div data-testid="today-list" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <div style={{ fontSize: 12, color: COLOR.textDim }}>
        All of today's list{plan ? " · opening one adds it to today's plan" : ""} ·{" "}
        <button type="button" style={linkButton} onClick={onBack}>
          back to the plan (p)
        </button>
      </div>
      {failed ? (
        <div data-testid="today-list-error" role="alert" style={{ fontSize: 13, color: COLOR.text }}>
          {queue === null ? "Couldn't read today's list" : "Couldn't refresh today's list; what's below may be out of date"} ·{" "}
          <button type="button" style={linkButton} onClick={onRetry}>
            Try again
          </button>
        </div>
      ) : null}
      {queue === null ? (
        failed ? null : (
          <div data-testid="today-list-loading" aria-busy="true" style={{ minHeight: 32, opacity: 0.35, fontSize: 13, color: COLOR.textDim }}>
            …
          </div>
        )
      ) : items.length === 0 ? (
        <div style={{ fontSize: 13, color: COLOR.textDim }}>Nothing else for today.</div>
      ) : (
        items.map((item, index) => {
          const minutes = minutesOf.get(item.practiceItemId);
          const cold = onYourOwnWhy(item);
          return (
            <div
              key={item.practiceItemId}
              data-testid="today-list-row"
              aria-current={index === focus ? "true" : undefined}
              style={{ display: "flex", gap: 10, alignItems: "baseline", fontSize: 13, padding: "2px 0", color: index === focus ? COLOR.amber : COLOR.text }}
            >
              <button
                type="button"
                style={{ ...linkButton, color: "inherit", fontSize: 13, padding: 0, textAlign: "left", flex: 1 }}
                disabled={busy}
                onClick={() => onOpen(item)}
                onFocus={() => setFocus(index)}
              >
                {item.learningObjectTitle}
              </button>
              {minutes !== undefined ? <span style={{ color: COLOR.textFaint, fontSize: 12 }}>{aboutMinutes(minutes)}</span> : null}
              <span style={{ color: COLOR.textFaint, fontSize: 12 }}>{fullListWhy(item)}</span>
              {cold ? (
                <button type="button" style={dimLink} aria-expanded={why === item.practiceItemId} onClick={() => setWhy((open) => (open === item.practiceItemId ? null : item.practiceItemId))}>
                  why?
                </button>
              ) : null}
              {cold && why === item.practiceItemId ? <span style={{ color: COLOR.textDim, fontSize: 12 }}>{cold}</span> : null}
            </div>
          );
        })
      )}
    </div>
  );
}

export function TodayPlace({
  session,
  streak: snapshotStreak,
  onBeginSession,
  onStartSession,
  onOpenPractice,
  onOpenPlanReading,
  onEndSession,
  onAdd,
  onOpenPassage,
  onResumeProblem,
  onAsk,
  onTakeExam,
  subjects = [],
  wrapUp,
  onStartLesson,
  onLessonOffer,
  lessonOpen = false,
  aiConnection = null,
  onConnectAi,
  onOpenBook,
  onOpenLibrary,
  onError
}: TodayPlaceProps) {
  const planQuery = useDailyPlan(session?.sessionId ?? null);
  const data: DailyPlanDto | null = planQuery.data ?? null;
  const planOn = data?.enabled === true && data.plan !== null;
  const plan = planOn ? data!.plan : null;
  const planOff = data !== null && !planOn;
  const [busy, setBusy] = useState(false);
  // What the press that set `busy` is waiting for, when it leads to a question (or more of the day): the
  // shared waiting line says it. Without it the only sign of a wait of up to 15 s was Begin's "opening…".
  const [waitLine, setWaitLine] = useState<string | null>(null);
  // Practise for this goal is two runs (read the list, then serve the pick): held, the line stays up between
  // them instead of vanishing and coming back after its delay.
  const lineHeld = useRef(false);
  const [why, setWhy] = useState(false);
  const [list, setList] = useState(false);
  const [wizard, setWizard] = useState(false);
  const [moreNew, setMoreNew] = useState<DailyPlanDto["preview"] | null>(null);
  // UX-4: Keep going came back with the day still done, so nothing was added.
  const [keptGoingToNothing, setKeptGoingToNothing] = useState(false);
  // UX-6: "Practise for this goal" found nothing ready: said on the card, never as an error.
  const [goalNothingReady, setGoalNothingReady] = useState(false);
  const now = new Date();

  // While the plan is off (its kill switch), the remembered minutes are the start summary's.
  const summary = useCachedQuery(planOff ? ["get_start_summary"] : null, () => api.getStartSummary(), { tags: [TAG.queue] });
  const [chosenMinutes, setChosenMinutes] = useState<number | null>(null);
  const offMinutes = session?.availableMinutes ?? chosenMinutes ?? summary.data?.rememberedMinutes ?? null;
  const minutes = plan ? plan.rememberedMinutes : offMinutes;
  const choices = plan ? plan.minuteChoices : summary.data?.minuteChoices ?? summary.data?.minutesPresets ?? [];

  // UX fix stage 3 (P1): a plan with nothing in it (closed empty, or open with
  // no block and nothing being chosen, waited on or held) says why, from the
  // book cards and today's list.
  const planDone = plan ? plan.status !== "open" : false;
  const emptyDay =
    data !== null &&
    plan !== null &&
    (planDone
      ? planWasEmpty(data)
      : todayRows(plan).length === 0 && plan.deciding !== true && !plan.waiting && !plan.questionInProgress);

  // The list is read only when it is shown, or while the plan is off (it
  // names Begin's first question), or to tell an empty day's cause. With a session, or under the plan, it is
  // Today's own queue read (classic Today's input); with the plan off and no
  // session, the minutes Begin will start (classic Start's preview).
  const queueInput = useMemo(
    () =>
      session || !planOff
        ? todayQueueInput(session)
        : offMinutes !== null
          ? { sessionId: null, availableMinutes: offMinutes, energy: null }
          : null,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [session?.sessionId, session?.availableMinutes, planOff, offMinutes]
  );
  const queueQuery = useCachedQuery(
    queueInput && (list || planOff || emptyDay || planDone || keptGoingToNothing) ? ["get_today_queue", queueInput] : null,
    () => api.getTodayQueue(queueInput!),
    { tags: [TAG.queue] }
  );
  const queue = queueQuery.data ?? null;
  // Fix round 1 (F6): a failed read of the full list says so and offers Try
  // again (the query's self-contained retry), whether nothing was read yet
  // or a refresh of what is shown failed.
  const retryQueue = useCallback(() => {
    const report = queueQuery.retryReport();
    if (report) void report.retry().catch(() => undefined);
  }, [queueQuery]);

  const library = useCachedQuery(["get_source_library"], () => api.getSourceLibrary(), { tags: [TAG.sources] });
  const noBooks = library.data !== undefined && library.data.sources.length === 0 && (library.data.pending?.length ?? 0) === 0;
  const listItems = queueQuery.error ? 0 : queue ? queue.sections.reduce((count, section) => count + section.items.length, 0) : null;
  const listItemIds = useMemo(() => queue?.sections.flatMap((section) => section.items.map((item) => item.practiceItemId)) ?? [], [queue]);
  // A closed plan with work left: a block of it not done, or questions still on today's list. The plan closes the
  // same way whether the router stopped with work feasible or nothing was left (its stopReason is free text), so
  // what is left is read from its rows and the list; null until the list is read, so neither line flashes.
  const moreLeft: boolean | null = !plan || !planDone
    ? null
    : plan.blocks.some((block) => block.status !== "done") || (listItems !== null && listItems > 0)
      ? true
      : listItems === null ? null : false;
  // Item 6: Keep going that came back with nothing open says the day's cause too.
  const cause: TodayCause | null = emptyDay || (keptGoingToNothing && planOn)
    ? todayCause({ cards: library.data?.sources, pending: library.data?.pending, ai: aiConnection, listItems, listItemIds })
    : null;
  // While a book's questions are on their way, the cause is read again as the
  // shelf reads it, so the line never outlives its state.
  const refetchLibrary = library.refetch;
  const refetchQueue = queueQuery.refetch;
  const onTheWay = cause?.kind === "on_the_way" || cause?.kind === "section_writing";
  useEffect(() => {
    if (!onTheWay) return;
    const timer = window.setInterval(() => {
      void refetchLibrary().catch(() => undefined);
      void refetchQueue().catch(() => undefined);
    }, CAUSE_POLL_MS);
    return () => window.clearInterval(timer);
  }, [onTheWay, refetchLibrary, refetchQueue]);
  // A build that ends, however it ends, bumps the revision the shell reads on
  // every screen; the shell then says the queue changed, here at once or on the
  // way back to Today. The books' lines are read with it, so a cause shown
  // follows a build that ended while the learner read elsewhere, with no press.
  const causeShown = cause !== null;
  useEffect(() => {
    if (!causeShown) return undefined;
    return subscribeQueueChanged(() => void refetchLibrary().catch(() => undefined));
  }, [causeShown, refetchLibrary]);

  const goals = useCachedQuery(["goals_list"], () => api.goalsList(), { tags: [TAG.goals] });
  const primaryGoal: GoalDto | null = useMemo(() => {
    const active = (goals.data?.goals ?? []).filter((goal) => goal.status === "active");
    active.sort((a, b) => {
      const da = a.dueAt ? Date.parse(a.dueAt) : Infinity;
      const db = b.dueAt ? Date.parse(b.dueAt) : Infinity;
      return da !== db ? da - db : b.priority - a.priority;
    });
    return active[0] ?? null;
  }, [goals.data]);

  // Router R2b: a block still being chosen is read again until it appears
  // (as Today's plan view does); a waiting plan is read again once it lifts.
  const deciding = plan?.deciding === true && !list;
  const refetchPlan = planQuery.refetch;
  useEffect(() => {
    if (!deciding) return;
    let reads = 0;
    const timer = window.setInterval(() => {
      reads += 1;
      if (reads > 40) {
        window.clearInterval(timer);
        return;
      }
      refetchPlan().catch(() => undefined);
    }, 1500);
    return () => window.clearInterval(timer);
  }, [deciding, refetchPlan]);
  const waitingUntil = plan?.waiting?.until ?? null;
  useEffect(() => {
    if (!waitingUntil) return;
    const at = Date.parse(waitingUntil);
    if (!Number.isFinite(at)) return;
    const timer = window.setTimeout(() => refetchPlan().catch(() => undefined), Math.max(at - Date.now(), 0) + 1000);
    return () => window.clearTimeout(timer);
  }, [waitingUntil, refetchPlan]);

  // Fix round 1 (F1): Today is keyed on its vault and unmounts when another
  // opens; an action still running then answers nothing, so its next step
  // (a request with the old vault's session, installing that session,
  // opening a question) never reaches the new vault. `stay` marks each step.
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  const stay = useCallback(<T,>(value: T): T => {
    if (!alive.current) throw LEFT;
    return value;
  }, []);
  // The shell's start (fix round 2): no session (a vault change) stops quietly.
  const startSession = useCallback(
    async (minutes: number): Promise<SessionSnapshot> => {
      const started = await onStartSession(minutes);
      if (!started) throw LEFT;
      return stay(started);
    },
    [onStartSession, stay]
  );
  const run = useCallback(
    async <T,>(work: () => Promise<T>): Promise<T | null> => {
      if (busy) return null;
      setBusy(true);
      try {
        return stay(await work());
      } catch (error) {
        if (error !== LEFT && alive.current) onError(errorMessage(error, "Couldn't do that just now."));
        return null;
      } finally {
        if (alive.current) setBusy(false);
      }
    },
    [busy, onError, stay]
  );
  // `run` that also says what it waits for. Only the press that wins `busy` sets the line, so a second
  // press during the wait (which `run` drops) cannot clear the first one's.
  const runSaying = useCallback(
    async <T,>(line: string, work: () => Promise<T>): Promise<T | null> => {
      if (busy) return null;
      setWaitLine(line);
      try {
        return await run(work);
      } finally {
        if (alive.current && !lineHeld.current) setWaitLine(null);
      }
    },
    [busy, run]
  );

  const done = plan ? plan.status !== "open" : false;
  const current = plan?.blocks.find((block) => block.id === plan.currentBlockId) ?? null;
  const waiting = plan && !done && !current && plan.waiting ? plan.waiting : null;
  // IH6: a read held the boundary for an open workbench. `deciding` is false, so nothing polls: closing the problem
  // invalidates the queue, and that refetch is the next read.
  const inProgress = plan && !done && !current ? plan.questionInProgress ?? null : null;
  const openProblems = useCachedQuery(inProgress ? ["workbench_open_problems"] : null, () => api.workbenchOpenProblems(), { tags: [TAG.queue] });
  const inProgressProblem = inProgress ? openProblems.data?.problems.find((problem) => problem.sessionId === inProgress.workbenchSessionId) ?? null : null;
  const inProgressItem = inProgress?.practiceItemId ?? null;
  const rows = plan && !done ? todayRows(plan) : [];

  // ── The plan's actions: exactly classic Start's and Today's RPCs ────────
  async function begin() {
    if (planOff) return beginWithoutPlan();
    if (!plan || done || waiting) return;
    if (!session) {
      const begun = await runSaying(WAITING_COPY.choosingNext, async () => {
        const started = await startSession(Math.round(plan.minutesBudget));
        const first = await api.nextPlanItem({ sessionId: started.sessionId, serve: true });
        return { started, step: first.step ?? null };
      });
      if (begun) onBeginSession(begun.started, begun.step);
      return;
    }
    const result = await runSaying(WAITING_COPY.choosingNext, () => api.nextPlanItem({ sessionId: session.sessionId, serve: true }));
    if (result?.step?.kind === "lesson_offer") {
      onLessonOffer?.(result.step);
      return;
    }
    const action = planStepAction(result?.step, { viaBlockLine: false });
    if (action.type === "practice") onOpenPractice(action.practiceItemId, action.schedulerCandidateId, null, action.planPresentationId);
    else if (action.type === "reader") onOpenPlanReading(action.reading);
  }

  // IH3: "Something else would help" was chosen at this plan boundary and served. A lesson opens as the learner's own start,
  // the plan's own pick (an agreement) is served as Begin serves it, and anything else is the step the choice placed.
  function afterSomethingElse(result: SomethingElseChosenDto) {
    const entry = lessonEntryFor(result);
    if (entry) {
      onStartLesson?.(entry);
      return;
    }
    if (result.preference?.outcome === "agreed") {
      void begin();
      return;
    }
    const action = planStepAction(result.step, { viaBlockLine: false });
    if (action.type === "practice") onOpenPractice(action.practiceItemId, action.schedulerCandidateId, null, action.planPresentationId);
    else if (action.type === "reader") onOpenPlanReading(action.reading);
    else void refetchPlan().catch(() => undefined);
  }

  // The plan's kill switch is off: Begin opens a session for these minutes
  // and its queue's first question, as classic Start then Today's Enter do.
  async function beginWithoutPlan() {
    if (minutes === null) return;
    const opened = await runSaying(WAITING_COPY.choosingNext, async () => {
      const started = session ?? (await startSession(minutes));
      const head = await api.getTodayQueue(todayQueueInput(started));
      return { started, item: head.sections.flatMap((section) => section.items)[0] ?? null };
    });
    if (!opened) return;
    if (!session) onBeginSession(opened.started);
    if (opened.item) onOpenPractice(opened.item.practiceItemId, opened.item.schedulerCandidateId ?? null);
  }

  function chooseMinutes(next: number) {
    if (planOff) {
      if (!session) setChosenMinutes(next);
      return;
    }
    if (!plan || next === plan.rememberedMinutes) return;
    void run(() => api.setPlanMinutes(next, session?.sessionId ?? null));
  }

  async function keepGoing() {
    setMoreNew(null);
    setKeptGoingToNothing(false);
    const result = await runSaying(WAITING_COPY.addingMore, () => api.planKeepGoing({ sessionId: session?.sessionId ?? null }));
    // UX-4 (audit student-1 #44): an extension with nothing in it comes back
    // closed, the same Today; say so rather than redraw it silently. Stage 3
    // (item 6): what follows the line is the day's cause, read from today's
    // list and the books, the same for every way a plan comes back closed.
    // The plan can't say which way it was (a stop the router chose with work
    // left, or nothing left to plan: its stopReason is free text), so the
    // list says whether there is more. Keep going never returns an abandoned
    // plan (only an earlier day's open plan is abandoned) nor a stopped one
    // (on a stopped plan it builds a new extension). With the plan off it
    // answers `enabled: false` and no plan, and Today becomes the plan-off
    // Begin: nothing to add there.
    if (result && result.enabled !== false && result.plan && result.plan.status !== "open") setKeptGoingToNothing(true);
  }

  async function somethingNew(confirm: boolean) {
    setKeptGoingToNothing(false);
    const result = await run(() => api.planMoreNew({ sessionId: session?.sessionId ?? null, confirm }));
    setMoreNew(confirm ? null : result?.preview ?? null);
  }

  async function finish() {
    await run(() => api.planKeepGoing({ sessionId: session?.sessionId ?? null, stop: true }));
    if (!session) return;
    const summaryResult = await run(() => api.endSession(session.sessionId));
    if (summaryResult) onEndSession(summaryResult);
  }

  async function skipCurrent() {
    if (!current) return;
    if (current.reading) {
      await run(() => api.planReadingEnded("skipped", session?.sessionId ?? null));
      return;
    }
    const next = current.items.find((item) => item.state === "served" || item.state === "planned");
    if (next) await run(() => api.nextPlanItem({ sessionId: session?.sessionId ?? null, skipPracticeItemId: next.practiceItemId }));
  }

  // A question from the full list: while the plan serves it is a learner
  // pick (a one-item block), served with the offer it was picked from; with
  // no session yet it begins today's plan with that pick (as Today's list).
  //
  // Fix round 1 (F4): with the plan off and no session, the session starts
  // with the minutes shown and chosen here (as Begin's), not the shell's
  // remembered ones.
  async function openFromList(item: ScheduledItemDto, line: string = WAITING_COPY.openingQuestion) {
    if (!plan) {
      if (!session && planOff && minutes !== null) {
        const started = await runSaying(line, () => startSession(minutes));
        if (!started) return;
        onBeginSession(started);
      }
      onOpenPractice(item.practiceItemId, item.schedulerCandidateId ?? null);
      return;
    }
    if (!session) {
      const begun = await runSaying(line, async () => {
        const started = await startSession(Math.round(plan.minutesBudget));
        const result = await api.planLearnerPick(item.practiceItemId, started.sessionId, item.schedulerCandidateId ?? null);
        return { started, step: result.step ?? null };
      });
      if (begun) onBeginSession(begun.started, begun.step);
      return;
    }
    const result = await runSaying(line, () => api.planLearnerPick(item.practiceItemId, session.sessionId, item.schedulerCandidateId ?? null));
    if (!result) return;
    const step = result.step;
    onOpenPractice(
      item.practiceItemId,
      step && step.kind === "item" ? step.schedulerCandidateId ?? item.schedulerCandidateId ?? null : item.schedulerCandidateId ?? null,
      null,
      step && step.kind === "item" ? step.presentationId ?? null : null
    );
  }

  // Practise for this goal: the first question on the goal's frontier in
  // today's list (as the goal banner's "practise at-risk" does).
  async function practiseGoal() {
    if (busy) return;
    lineHeld.current = true;
    try {
      await practiseGoalHeld();
    } finally {
      lineHeld.current = false;
      if (alive.current) setWaitLine(null);
    }
  }

  async function practiseGoalHeld() {
    setGoalNothingReady(false);
    const input = queueInput ?? todayQueueInput(session);
    const snapshot = await runSaying(WAITING_COPY.findingGoalQuestion, () => api.getTodayQueue(input));
    if (!snapshot) return;
    const target = snapshot.sections.flatMap((section) => section.items).find((item) => (item.components.goalFrontier ?? 0) > 0) ?? null;
    if (!target) {
      // UX-6 (audit beginner-1 #80-120): an empty state, not a failure.
      setGoalNothingReady(true);
      return;
    }
    await openFromList(target, WAITING_COPY.findingGoalQuestion);
  }

  // P1: the one step beside an empty day's cause. A retry the sidecar wants
  // confirmed (a re-read) is the Library's to ask.
  async function retryFromToday(target: { sourceId: string } | { batchId: string }) {
    const result = await run(() => api.sourceAction({ ...target, action: "retry" }));
    if (result?.needsConfirmation) onOpenLibrary?.();
  }

  // A finished section's questions that stopped: the same batch, asked again (what the Library's Activity does).
  async function resumeSection(resumeId: string) {
    const resumed = await run(() => api.resumeIngestBatch(resumeId));
    if (resumed) void refetchLibrary().catch(() => undefined);
  }

  function causeAction(shown: TodayCause): (() => void) | null {
    switch (shown.kind) {
      case "list_has_more":
        return () => setList(true);
      case "waiting_ok":
      case "needs_ai":
        return onConnectAi ?? null;
      case "questions_ready": {
        const item = shown.itemId ? queue?.sections.flatMap((section) => section.items).find((row) => row.practiceItemId === shown.itemId) : null;
        return item ? () => void openFromList(item) : null;
      }
      case "failed":
        return () => void retryFromToday(shown.target);
      case "section_failed":
        return () => void resumeSection(shown.resumeId);
      case "needs_look":
        return onOpenLibrary ?? null;
      case "on_the_way":
      case "section_writing":
      case "section_waiting":
      case "finish_section":
      case "none_up": {
        const card = shown.card;
        return card && onOpenBook ? () => onOpenBook(card) : null;
      }
      case "no_reading":
        return onAdd;
    }
  }

  const causeLine = cause ? (
    <CauseLine cause={cause} whatLeaves={aiConnection?.whatLeaves ?? null} busy={busy} onAction={causeAction(cause)} />
  ) : null;

  // Stage 3 (UX-6's line, now with its cause): "Practise for this goal" found
  // nothing on today's list. A goal with questions of its own says they are
  // not up today; one with none yet names the books' cause, as an empty Today
  // does (Today cannot tell which books a goal reads from, so the line names
  // the book it is about).
  const goalHasQuestions = (primaryGoal?.practicableItemCount ?? 0) > 0;
  const goalCause = goalNothingReady && !goalHasQuestions
    ? todayCause({ cards: library.data?.sources, pending: library.data?.pending, ai: aiConnection, listItems: 0 })
    : null;

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (screenLeavesKey(event)) return;
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea" || tag === "select" || event.defaultPrevented || busy || wizard) return;
      // The full list owns its keys while it is shown (and `p` leaves it).
      if (list) return;
      if (event.key === "Enter") {
        if (enterOnControl(event)) return;
        event.preventDefault();
        // A book's first questions on Today: Enter is their Begin, as the line says.
        const first = cause?.kind === "questions_ready" ? causeAction(cause) : null;
        if (first) first();
        else if (done) void keepGoing();
        else void begin();
      } else if (event.key === "l") {
        event.preventDefault();
        setList(true);
      } else if (event.key === "?") {
        event.preventDefault();
        setWhy((open) => !open);
      } else if (done && event.key === "d") {
        event.preventDefault();
        void finish();
      } else if (!done && (event.key === "ArrowLeft" || event.key === "ArrowRight")) {
        event.preventDefault();
        const next = stepChoice(choices, minutes, event.key === "ArrowLeft" ? -1 : 1);
        if (next !== undefined && next !== minutes) chooseMinutes(next);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const streak = data?.streak ?? snapshotStreak;
  const streakText = streakLine(streak);

  // ── States (§7.1) ───────────────────────────────────────────────────────
  let body: ReactNode;
  if (!data && planQuery.error) {
    body = (
      <div data-testid="today-error" role="alert" style={{ fontSize: 14, color: COLOR.text }}>
        Couldn't plan today ·{" "}
        <button type="button" style={linkButton} onClick={() => void refetchPlan().catch(() => undefined)}>
          Try again
        </button>
      </div>
    );
  } else if (!data) {
    // Loading: the frame, with nothing claimed yet (never "Loading today's queue").
    // App start and every return to Today: after the indicator's delay, what is being read (get_daily_plan took up to 19 s once in the walks).
    body = (
      <div data-testid="today-loading" aria-busy="true" style={{ minHeight: 64, fontSize: 14, color: COLOR.textDim }}>
        <Waiting testId="plan-wait" line={WAITING_COPY.readingPlan} />
      </div>
    );
  } else if (list) {
    body = (
      <PlainList
        queue={queue}
        plan={plan}
        busy={busy}
        failed={queueQuery.error !== null}
        onRetry={retryQueue}
        onOpen={(item) => void openFromList(item)}
        onBack={() => setList(false)}
      />
    );
  } else if (noBooks && (!plan || (rows.length === 0 && planWasEmpty(data)))) {
    body = (
      <div data-testid="today-first-run" style={{ display: "flex", flexDirection: "column", gap: 12, fontSize: 14, color: COLOR.text }}>
        <div>Nothing to plan yet. Add a book, paper or lecture and LearnLoop will plan your days around it.</div>
        <div>
          <button type="button" style={actionButton(true)} onClick={onAdd}>
            + Add
          </button>
        </div>
      </div>
    );
  } else if (planOff) {
    const head = queue?.sections.flatMap((section) => section.items)[0] ?? null;
    body = (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div data-testid="today-sentence" style={{ fontSize: 15, color: COLOR.text }}>
          {minutes !== null ? `${minutes} minutes today${head ? `: starting with ${head.learningObjectTitle}.` : "."}` : ""}
        </div>
        <div>
          <button type="button" style={actionButton(true)} disabled={busy || minutes === null} onClick={() => void begin()}>
            {busy ? "opening…" : "Begin ↵"}
          </button>
        </div>
      </div>
    );
  } else if (plan && done) {
    const empty = planWasEmpty(data);
    body = (
      <div data-testid="today-done" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <div data-testid="today-sentence" style={{ fontSize: 15, color: COLOR.text }}>
          {empty ? "Nothing planned for today." : plan.kind === "reentry" ? "Catch-up done." : doneLine(data)}
        </div>
        {empty ? causeLine : keptGoingToNothing ? null : moreLeft ? (
          <div data-testid="today-stopped-more" role="status" style={{ fontSize: 13, color: COLOR.textDim }}>
            {PLAN_STOPPED_WITH_MORE}
            {(listItems ?? 0) > 0 ? (
              <>
                {" "}
                <button type="button" style={linkButton} onClick={() => setList(true)}>
                  {causeActionLabel({ kind: "list_has_more" })}
                </button>
              </>
            ) : null}
          </div>
        ) : moreLeft === false ? (
          <div data-testid="today-finished" role="status" style={{ fontSize: 13, color: COLOR.textDim }}>
            {PLAN_FINISHED}
          </div>
        ) : null}
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button type="button" style={actionButton(true)} disabled={busy} onClick={() => void keepGoing()}>
            Keep going ↵
          </button>
          {plan.kind !== "reentry" ? (
            <button type="button" style={actionButton()} disabled={busy} onClick={() => void somethingNew(false)}>
              Something new
            </button>
          ) : null}
          {session ? (
            <button type="button" style={actionButton()} disabled={busy} onClick={() => void finish()}>
              Done for today
            </button>
          ) : null}
        </div>
        {keptGoingToNothing ? <KeepGoingNothing /> : null}
        {keptGoingToNothing && !empty ? causeLine : null}
        {moreNew ? (
          <div data-testid="today-more-new" style={{ fontSize: 12, color: COLOR.textDim }}>
            {moreNew.available ? (
              <>
                {aboutMinutes(moreNew.estMinutes)} of new material today, and a little more review on the days after.{" "}
                <button type="button" style={linkButton} disabled={busy} onClick={() => void somethingNew(true)}>
                  add it
                </button>
              </>
            ) : (
              "Nothing new is ready yet. Keep reading and LearnLoop will have more."
            )}
          </div>
        ) : null}
      </div>
    );
  } else if (plan) {
    const sentence = plan.kind === "reentry" ? reentrySentence(plan) : planSentence(plan);
    body = (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div data-testid="today-sentence" style={{ fontSize: 15, color: COLOR.text, lineHeight: 1.5 }}>
          {plan.kind === "keep_going" ? "Keep going. " : ""}
          {waiting ? waitingLine(waiting) : inProgress ? questionInProgressLine(inProgress) : sentence ?? (deciding ? "Choosing what's next…" : "Nothing planned for today.")}{" "}
          <button type="button" style={dimLink} aria-expanded={why} onClick={() => setWhy((open) => !open)}>
            why? {why ? "▾" : "▸"}
          </button>
        </div>
        {causeLine}
        {inProgress ? (
          <QuestionInProgress
            question={inProgress}
            onResume={inProgressProblem ? () => onResumeProblem(inProgressProblem) : inProgressItem ? () => onOpenPractice(inProgressItem) : undefined}
            onError={onError}
          />
        ) : null}
        {why ? <PlanWhy data={data} /> : null}
        {current?.lessonOffer ? (
          <LessonOfferBlock offer={current.lessonOffer} sessionId={session?.sessionId ?? null}
                            onStartLesson={onStartLesson} onAnswered={() => void refetchPlan().catch(() => undefined)}
                            onError={onError} />
        ) : null}
        {rows.length ? (
          <div data-testid="today-blocks" style={{ border: `1px solid ${COLOR.border}`, padding: "8px 14px", display: "flex", flexDirection: "column", gap: 4 }}>
            {rows.map((row) => (
              <div
                key={row.key}
                data-testid="today-block"
                aria-current={row.current ? "step" : undefined}
                style={{ display: "flex", gap: 10, alignItems: "baseline", fontSize: 13, color: row.current ? COLOR.text : COLOR.textDim }}
              >
                <span style={{ width: 12, color: COLOR.amber }}>{row.current ? "▸" : ""}</span>
                <span style={{ flex: 1, minWidth: 0 }}>
                  {row.text}
                  {row.onYourOwn ? <span style={{ color: COLOR.textFaint }}> · on your own</span> : null}
                </span>
                {row.current && current ? (
                  <button type="button" style={dimLink} disabled={busy} onClick={() => void skipCurrent()}>
                    skip
                  </button>
                ) : null}
                <span style={{ color: COLOR.textFaint, fontSize: 12, whiteSpace: "nowrap" }}>{row.minutes}</span>
              </div>
            ))}
          </div>
        ) : null}
        {!waiting && (rows.length > 0 || deciding || inProgress) ? (
          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button type="button" data-testid="today-begin" style={actionButton(true)} disabled={busy} onClick={() => void begin()}>
              {busy ? "opening…" : current?.startedAt ? "Continue ↵" : "Begin ↵"}
            </button>
          </div>
        ) : null}
        {!waiting && rows.length === 0 && !deciding && !inProgress ? (
          <div style={{ display: "flex", gap: 10 }}>
            <button type="button" style={actionButton(true)} disabled={busy} onClick={() => void keepGoing()}>
              Keep going
            </button>
          </div>
        ) : null}
        {!waiting && rows.length === 0 && !deciding && !inProgress && keptGoingToNothing ? <KeepGoingNothing /> : null}
        {/* IH3 (spec §6): the quiet link at any plan boundary, with a session (the choice is served into it). */}
        {session && data?.somethingElse && !waiting ? (
          <SomethingElse sessionId={session.sessionId} surface="today" enabled canStartLesson={Boolean(onStartLesson)}
                         hidePlansPick={Boolean(current?.lessonOffer)} onChosen={afterSomethingElse} onError={onError} />
        ) : null}
      </div>
    );
  }

  return (
    <div data-testid="today-place" className="screen" style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ flex: 1, overflowY: "auto", padding: "20px 28px", display: "flex", flexDirection: "column", gap: 18, maxWidth: 860, width: "100%", alignSelf: "center", boxSizing: "border-box" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <span style={{ flex: 1, fontSize: 13, color: COLOR.textDim }}>{dayPhrase(now)}</span>
          {choices.length && minutes !== null && !done && !list ? <MinuteChips value={minutes} choices={choices} disabled={busy || (planOff && session !== null)} onChange={chooseMinutes} /> : null}
        </div>
        {/* Teacher TE1b (codex review F1): the router's lesson suggestion card, at most one a day, only
            while the sidecar says Today may suggest one; otherwise nothing is asked. A section, never a dialog. */}
        {!list && onStartLesson && algoConfig().lessonSuggestions ? (
          <LessonSuggestionCard sessionId={session?.sessionId ?? null} onStartLesson={onStartLesson} onError={onError} />
        ) : null}
        {!list && onStartLesson ? <OpenLessons lessonOpen={lessonOpen} onStartLesson={onStartLesson} /> : null}
        {body}
        {waitLine ? <Waiting line={waitLine} /> : null}
        {!list && primaryGoal ? (
          <GoalCard goal={primaryGoal} onPractise={() => void practiseGoal()} onTakeExam={onTakeExam} onGoalChanged={() => void goals.refetch().catch(() => undefined)} onNewGoal={() => setWizard(true)} onError={onError} />
        ) : null}
        {!list && primaryGoal && goalNothingReady ? (
          goalCause ? (
            <CauseLine
              testId="goal-nothing-ready"
              sentence={goalCauseSentence(goalCause)}
              cause={goalCause}
              whatLeaves={aiConnection?.whatLeaves ?? null}
              busy={busy}
              onAction={causeAction(goalCause)}
              style={{ fontSize: 12, color: COLOR.textDim, marginTop: -10 }}
            />
          ) : (
            <div data-testid="goal-nothing-ready" role="status" style={{ fontSize: 12, color: COLOR.textDim, marginTop: -10 }}>
              {goalHasQuestions ? GOAL_NOT_UP_TODAY : GOAL_NOTHING_READY}
            </div>
          )
        ) : null}
        {!list ? <Threads wrapUp={wrapUp} onOpenPassage={onOpenPassage} onResumeProblem={onResumeProblem} onAsk={onAsk} /> : null}
        {!list ? <CapturesLine subjects={subjects} onAsk={onAsk} /> : null}
      </div>
      <div
        data-testid="today-footer"
        style={{ borderTop: `1px solid ${COLOR.border}`, padding: "6px 14px", display: "flex", alignItems: "center", gap: 12, fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim, flexShrink: 0 }}
      >
        <span data-testid="today-streak" style={{ color: COLOR.textDim }}>
          {streakText ?? ""}
        </span>
        <span style={{ flex: 1 }} />
        {list ? null : (
          <button type="button" style={dimLink} onClick={() => setList(true)}>
            all of today's list (l)
          </button>
        )}
      </div>
      {wizard ? <GoalWizard onClose={() => setWizard(false)} onCreated={() => void goals.refetch().catch(() => undefined)} onError={onError} /> : null}
    </div>
  );
}

/** P1: an empty day's cause in one line, with its one action beside it and,
 *  where that action sends passages to a model, what is sent on demand. A
 *  status line, never an error. */
function CauseLine({
  cause,
  whatLeaves,
  busy,
  onAction,
  sentence,
  testId = "today-cause",
  style
}: {
  cause: TodayCause;
  whatLeaves: string | null;
  busy: boolean;
  onAction: (() => void) | null;
  /** The line's own words where it is not Today's (the goal card's). */
  sentence?: string;
  testId?: string;
  style?: CSSProperties;
}) {
  const [sent, setSent] = useState(false);
  const label = causeActionLabel(cause);
  const wait = sentence === undefined ? causeWait(cause) : null;
  if (wait) {
    // A wait (a book being got ready, a finished section's questions being written): the shared waiting
    // indicator says what is happening and how far, the action beside it from the first moment; the line under it
    // says what to know meanwhile. The indicator is the status region, so this frame is not one too.
    return (
      <div data-testid={testId} style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 13, color: COLOR.text, lineHeight: 1.5, ...style }}>
        <Waiting testId={`${testId}-wait`} line={wait.line}>
          {label && onAction ? (
            <>
              {" "}
              <button type="button" style={linkButton} disabled={busy} onClick={onAction}>
                {label}
              </button>
            </>
          ) : null}
        </Waiting>
        <div>{wait.after}</div>
      </div>
    );
  }
  return (
    <div data-testid={testId} role="status" style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 13, color: COLOR.text, lineHeight: 1.5, ...style }}>
      <div>
        {sentence ?? causeSentence(cause)}{" "}
        {label && onAction ? (
          <button type="button" style={linkButton} disabled={busy} onClick={onAction}>
            {label}
          </button>
        ) : null}
        {whatLeaves && causeSendsPassages(cause) ? (
          <button type="button" style={dimLink} aria-expanded={sent} onClick={() => setSent((open) => !open)}>
            {WHATS_SENT} {sent ? "▾" : "▸"}
          </button>
        ) : null}
      </div>
      {sent && whatLeaves ? <div style={{ fontSize: 12, color: COLOR.textDim }}>{whatLeaves}</div> : null}
    </div>
  );
}

/** A lesson the learner left open waits here with its one action, Continue (its stop is inside the lesson). Read
 *  when Today opens and again each time a lesson over Today closes: Close keeps a lesson open, and without this line
 *  nothing in this shell led back to it. A failed read shows nothing and never blocks Today. */
function OpenLessons({ lessonOpen, onStartLesson }: { lessonOpen: boolean; onStartLesson: (entry: LessonEntry) => void }) {
  const [lessons, setLessons] = useState<OpenLessonDto[]>([]);
  useEffect(() => {
    if (lessonOpen) return;
    let cancelled = false;
    api.lessonOpenLessons()
      .then((result) => { if (!cancelled) setLessons(result.lessons ?? []); })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [lessonOpen]);
  if (lessons.length === 0) return null;
  return (
    <section aria-label="Your lessons" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      {lessons.map((lesson) => (
        <div key={lesson.lessonId} data-testid="today-open-lesson" style={{ fontSize: 13, color: COLOR.text }}>
          {continueLessonLine(lesson.title)}{" "}
          <button type="button" style={linkButton} onClick={() => onStartLesson({ kind: "resume", lessonId: lesson.lessonId })}>
            Continue
          </button>
        </div>
      ))}
    </section>
  );
}

/** UX-4: said in place, where Keep going was pressed; a notice, never an error. */
function KeepGoingNothing() {
  return (
    <div data-testid="today-keep-going-nothing" role="status" style={{ fontSize: 12, color: COLOR.textDim }}>
      {KEEP_GOING_NOTHING_LEAD}
    </div>
  );
}
