// UX Phase 3: Today in the simple shell (docs/specs/ux_learnloop_v1.md §7.1,
// wireframe W4, §10 3.1-3.4). Start and Today merged into one place:
//
//   Tuesday evening                              10m  15m [25m] 40m  60m
//   25 minutes today: finish §5.4 Mixtures, then 6 short questions from
//   earlier days and a fix for a mix-up.                          why? ▸
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

import { useCallback, useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";
import { api } from "../../api/client";
import { TAG } from "../../api/queryTags";
import { useCachedQuery } from "../../api/useCachedQuery";
import type {
  DailyPlanDto,
  GoalDto,
  PlanReadingDto,
  PlanStepDto,
  QueueSnapshot,
  ScheduledItemDto,
  SessionEndSummary,
  SessionSnapshot,
  StreakSummary,
  WorkbenchOpenProblemDto
} from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { GoalCard } from "../../components/GoalCard";
import { GoalWizard } from "../../components/GoalWizard";
import { InboxStrip } from "../../components/InboxStrip";
import { targetForDialogue } from "../../components/QuestionQueue";
import type { AskTarget } from "../../components/AskOverlay";
import { screenLeavesKey } from "../../app/keymap";
import { todayQueueInput } from "../../app/autoAdvance";
import { aboutMinutes, planStepAction, useDailyPlan, waitingLine } from "../../app/dailyPlan";
import {
  THREADS_SHOWN,
  dayPhrase,
  doneLine,
  fullListWhy,
  onYourOwnWhy,
  planSentence,
  planWasEmpty,
  reentrySentence,
  reentryWhy,
  splitWhy,
  streakLine,
  todayRows,
  todayThreads,
  type TodayThread
} from "../../app/todayPlan";
import { errorMessage } from "../../errors";

export interface TodayPlaceProps {
  session: SessionSnapshot | null;
  /** The streak as of vault load; the plan's fresher copy wins. */
  streak: StreakSummary | null;
  /** Begin started a session (and maybe served its first step). */
  onBeginSession: (session: SessionSnapshot, firstStep?: PlanStepDto | null) => void;
  onOpenPractice: (practiceItemId: string, schedulerCandidateId?: string | null, proposalOrigin?: null, planPresentationId?: string | null) => void;
  onOpenPlanReading: (reading: PlanReadingDto) => void;
  onEndSession: (summary: SessionEndSummary) => void;
  /** The shell's Add (first run: nothing to plan yet). */
  onAdd: () => void;
  /** Open a book at a passage (an open question's place). */
  onOpenPassage: (sourceId: string, spanId: string | null) => void;
  /** Resume an unfinished problem in its book. */
  onResumeProblem: (problem: WorkbenchOpenProblemDto) => void;
  onAsk: (target: AskTarget) => void;
  onTakeExam?: (goalId: string) => void;
  subjects?: { id: string; title: string }[];
  /** RW6a's wrap-up offer, when the shell armed it for this view. */
  wrapUp?: ReactNode;
  onError: (message: string) => void;
}

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
    if (citation?.sourceId) return { label: "open in book ▸", run: () => onOpenPassage(citation.sourceId as string, citation.spanId) };
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
  if (open) return <InboxStrip subjects={subjects} onAsk={onAsk} />;
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
  onOpen,
  onBack
}: {
  queue: QueueSnapshot | null;
  plan: DailyPlanDto["plan"] | null;
  busy: boolean;
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
      {queue === null ? null : items.length === 0 ? (
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
  onError
}: TodayPlaceProps) {
  const planQuery = useDailyPlan(session?.sessionId ?? null);
  const data: DailyPlanDto | null = planQuery.data ?? null;
  const planOn = data?.enabled === true && data.plan !== null;
  const plan = planOn ? data!.plan : null;
  const planOff = data !== null && !planOn;
  const [busy, setBusy] = useState(false);
  const [why, setWhy] = useState(false);
  const [list, setList] = useState(false);
  const [wizard, setWizard] = useState(false);
  const [moreNew, setMoreNew] = useState<DailyPlanDto["preview"] | null>(null);
  const now = new Date();

  // While the plan is off (its kill switch), the remembered minutes are the start summary's.
  const summary = useCachedQuery(planOff ? ["get_start_summary"] : null, () => api.getStartSummary(), { tags: [TAG.queue] });
  const [chosenMinutes, setChosenMinutes] = useState<number | null>(null);
  const offMinutes = session?.availableMinutes ?? chosenMinutes ?? summary.data?.rememberedMinutes ?? null;
  const minutes = plan ? plan.rememberedMinutes : offMinutes;
  const choices = plan ? plan.minuteChoices : summary.data?.minuteChoices ?? summary.data?.minutesPresets ?? [];

  // The list is read only when it is shown, or while the plan is off (it is
  // then Today's content); keyed as Today's own queue read.
  const queueInput = useMemo(
    () => (session ? todayQueueInput(session) : offMinutes !== null ? { sessionId: null, availableMinutes: offMinutes, energy: null } : null),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [session?.sessionId, session?.availableMinutes, offMinutes]
  );
  const queueQuery = useCachedQuery(
    queueInput && (list || planOff) ? ["get_today_queue", queueInput] : null,
    () => api.getTodayQueue(queueInput!),
    { tags: [TAG.queue] }
  );
  const queue = queueQuery.data ?? null;

  const library = useCachedQuery(["get_source_library"], () => api.getSourceLibrary(), { tags: [TAG.sources] });
  const noBooks = library.data !== undefined && library.data.sources.length === 0 && (library.data.pending?.length ?? 0) === 0;

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

  const run = useCallback(
    async <T,>(work: () => Promise<T>): Promise<T | null> => {
      if (busy) return null;
      setBusy(true);
      try {
        return await work();
      } catch (error) {
        onError(errorMessage(error, "Couldn't do that just now."));
        return null;
      } finally {
        setBusy(false);
      }
    },
    [busy, onError]
  );

  const done = plan ? plan.status !== "open" : false;
  const current = plan?.blocks.find((block) => block.id === plan.currentBlockId) ?? null;
  const waiting = plan && !done && !current && plan.waiting ? plan.waiting : null;
  const rows = plan && !done ? todayRows(plan) : [];

  // ── The plan's actions: exactly classic Start's and Today's RPCs ────────
  async function begin() {
    if (planOff) return beginWithoutPlan();
    if (!plan || done || waiting) return;
    if (!session) {
      const begun = await run(async () => {
        const started = await api.startSession({ availableMinutes: Math.round(plan.minutesBudget) });
        const first = await api.nextPlanItem({ sessionId: started.sessionId, serve: true });
        return { started, step: first.step ?? null };
      });
      if (begun) onBeginSession(begun.started, begun.step);
      return;
    }
    const result = await run(() => api.nextPlanItem({ sessionId: session.sessionId, serve: true }));
    const action = planStepAction(result?.step, { viaBlockLine: false });
    if (action.type === "practice") onOpenPractice(action.practiceItemId, action.schedulerCandidateId, null, action.planPresentationId);
    else if (action.type === "reader") onOpenPlanReading(action.reading);
  }

  // The plan's kill switch is off: Begin opens a session for these minutes
  // and its queue's first question, as classic Start then Today's Enter do.
  async function beginWithoutPlan() {
    if (minutes === null) return;
    const opened = await run(async () => {
      const started = session ?? (await api.startSession({ availableMinutes: minutes }));
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
    await run(() => api.planKeepGoing({ sessionId: session?.sessionId ?? null }));
  }

  async function somethingNew(confirm: boolean) {
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
  async function openFromList(item: ScheduledItemDto) {
    if (!plan) {
      onOpenPractice(item.practiceItemId, item.schedulerCandidateId ?? null);
      return;
    }
    if (!session) {
      const begun = await run(async () => {
        const started = await api.startSession({ availableMinutes: Math.round(plan.minutesBudget) });
        const result = await api.planLearnerPick(item.practiceItemId, started.sessionId, item.schedulerCandidateId ?? null);
        return { started, step: result.step ?? null };
      });
      if (begun) onBeginSession(begun.started, begun.step);
      return;
    }
    const result = await run(() => api.planLearnerPick(item.practiceItemId, session.sessionId, item.schedulerCandidateId ?? null));
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
    const input = queueInput ?? todayQueueInput(session);
    const snapshot = await run(() => api.getTodayQueue(input));
    const target = snapshot?.sections.flatMap((section) => section.items).find((item) => (item.components.goalFrontier ?? 0) > 0) ?? null;
    if (!target) {
      onError("Nothing for this goal is ready to practise yet.");
      return;
    }
    await openFromList(target);
  }

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (screenLeavesKey(event)) return;
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea" || tag === "select" || event.defaultPrevented || busy || wizard) return;
      // The full list owns its keys while it is shown (and `p` leaves it).
      if (list) return;
      if (event.key === "Enter") {
        event.preventDefault();
        if (done) void keepGoing();
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
    body = <div data-testid="today-loading" aria-busy="true" style={{ minHeight: 64, opacity: 0.35, fontSize: 14, color: COLOR.textDim }}>…</div>;
  } else if (list) {
    body = <PlainList queue={queue} plan={plan} busy={busy} onOpen={(item) => void openFromList(item)} onBack={() => setList(false)} />;
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
          {waiting ? waitingLine(waiting) : sentence ?? (deciding ? "Choosing what's next…" : "Nothing planned for today.")}{" "}
          <button type="button" style={dimLink} aria-expanded={why} onClick={() => setWhy((open) => !open)}>
            why? {why ? "▾" : "▸"}
          </button>
        </div>
        {why ? <PlanWhy data={data} /> : null}
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
        {!waiting && (rows.length > 0 || deciding) ? (
          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button type="button" data-testid="today-begin" style={actionButton(true)} disabled={busy} onClick={() => void begin()}>
              {busy ? "opening…" : current?.startedAt ? "Continue ↵" : "Begin ↵"}
            </button>
          </div>
        ) : null}
        {!waiting && rows.length === 0 && !deciding ? (
          <div style={{ display: "flex", gap: 10 }}>
            <button type="button" style={actionButton(true)} disabled={busy} onClick={() => void keepGoing()}>
              Keep going
            </button>
          </div>
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
        {body}
        {!list && primaryGoal ? (
          <GoalCard goal={primaryGoal} onPractise={() => void practiseGoal()} onTakeExam={onTakeExam} onGoalChanged={() => void goals.refetch().catch(() => undefined)} onNewGoal={() => setWizard(true)} onError={onError} />
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
