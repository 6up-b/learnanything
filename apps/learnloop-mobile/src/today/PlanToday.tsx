// Mobile v2 §2.2, J1/J4/J5: the phone's Today is the shared plan (owner decision D1), filtered at
// the step by the host. One sentence, the router's line, the one count that explains an absence,
// and one primary action in the thumb zone: Begin, Next, or (the plan done) Keep going. Everything
// shown is the plan DTO's; nothing here decides what comes next.
import { useEffect, useState } from "react";
import type { CommandError, SessionEndSummary, SessionSnapshot } from "@desktop/api/dto";
import { setQueryData } from "@desktop/api/queryCache";
import { TAG } from "@desktop/api/queryTags";
import { useCachedQuery } from "@desktop/api/useCachedQuery";
import { phone, type PhonePlanDto, type PhoneSomethingElseDto } from "../api/phone";
import { SomethingElse } from "../practice/SomethingElse";
import { WAITING_COPY } from "@desktop/copy/waiting";
import { Waiting } from "../components/Waiting";
import { RouterLine, WhyLink } from "../practice/RouterLine";
import { currentWhy, doneLine, planSentence, stepOf, waitingForDesktop } from "./planWords";
import { causeSentence, todayCause } from "@desktop/app/todayCause";
import { nextPracticeLines, useLatestNextPractice, useNextDayRefresh } from "@desktop/app/nextPractice";

/** A day whose plan has nothing in it: no question and no reading planned (the desktop's `planWasEmpty`). */
function emptyDay(data: PhonePlanDto | undefined): boolean {
  return Boolean(data?.plan) && (data?.day?.plannedItems ?? 0) === 0 && (data?.day?.readingBlocks ?? 0) === 0;
}

export function planKey(sessionId: string | null): readonly [string, string | null] {
  return ["get_daily_plan", sessionId];
}

/** The plan's off (a vault below its version, `plan.enabled` off) or the host's kill switch says so. */
export function planOff(reply: PhonePlanDto | null | undefined, error?: unknown): boolean {
  if ((error as CommandError | undefined)?.code === "phone_plan_off") return true;
  return reply !== null && reply !== undefined && reply.enabled === false;
}

export function PlanToday({
  session,
  finished,
  busy,
  choosing,
  onBegin,
  onNext,
  onKeepGoing,
  onEnd,
  onMode,
  onSomethingElse,
  onResume,
  onError
}: {
  session: SessionSnapshot | null;
  finished: SessionEndSummary | null;
  busy: boolean;
  /** Next is with the host: a decision at a boundary can take a while (§2.2). */
  choosing: boolean;
  onBegin: (minutes: number) => void;
  /** The phone's Next; `skip` is the desktop's skip link, for what waits for the desktop. */
  onNext: (skip?: string | null) => void;
  onKeepGoing: (stop: boolean) => void;
  onEnd: () => void;
  /** What the read says Today is: the plan, or (the plan off) M2a's queue. */
  onMode: (mode: "plan" | "queue") => void;
  /** IH3: "Something else would help" was chosen and served (the plan's reply: an item opens, or Today shows it). */
  onSomethingElse?: (reply: PhoneSomethingElseDto) => void;
  /** UX fix stage 4 (F19): a question left for Today has a draft; this reopens it as it was. */
  onResume?: (() => void) | null;
  onError: (error: unknown) => void;
}) {
  const sessionId = session?.sessionId ?? null;
  const query = useCachedQuery<PhonePlanDto>(planKey(sessionId), () => phone.getDailyPlan(sessionId), { tags: [TAG.queue] });
  // A step's reply stored as the plan carries no summary: the last read's stands until Today is read again, which it
  // is when the plan's next day starts.
  const nextPractice = useLatestNextPractice(query.data?.nextPractice);
  useNextDayRefresh(nextPractice?.calendar.nextDayStartsAt, () => void query.refetch().catch(() => undefined));
  const [minutesBusy, setMinutesBusy] = useState(false);
  // First questions arrive (P11): an empty day says why, in the desktop's words for the same states (the shared
  // `todayCause`), read from the books' lines as the Read tab gets them. Today's list is not read here, so a book's
  // questions are named by how many were written, and the primary action stays the plan's. A failed read says nothing.
  const empty = emptyDay(query.data) && (query.data?.plan?.blocks.length ?? 0) === 0;
  const library = useCachedQuery(empty ? ["get_source_library", "phone_today"] : null, () => phone.library(), { tags: [TAG.sources] });
  const cause = empty && library.data ? todayCause({ cards: library.data.sources, ai: null, listItems: 0, listUnknown: true }) : null;
  const causeLine = cause ? <p className="dim" role="status" data-testid="today-cause">{causeSentence(cause)}</p> : null;
  // As on the desktop: a book's questions offered are the day's news, so no "Nothing planned for today." above them.
  const offersQuestions = cause?.kind === "questions_ready" || cause?.kind === "questions_ready_with_section_work";
  useEffect(() => {
    if (planOff(query.data, query.error)) {
      onMode("queue");
      return;
    }
    if (query.data) onMode("plan");
    if (query.error) onError(query.error);
    // Reported once per failure.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query.data, query.error]);

  // UX fix stage 4 (F19): a draft left for Today is offered in every state of the plan, a failed read included, so it is
  // never behind a screen that does not show it. In the thumb zone, above the primary action, which stays the same.
  const resumeEntry = onResume ? (
    <button className="plain block" type="button" disabled={busy || choosing} onClick={onResume}>
      Resume your answer <span aria-hidden="true">▸</span>
    </button>
  ) : null;

  const data = query.data;
  const plan = data?.plan ?? null;
  if (!data || !plan) {
    return (
      <div className="screen">
        <h1>Today</h1>
        {query.error
          ? <p className="dim" role="status">Today's plan couldn't be read.</p>
          : <Waiting testId="plan-wait" line={WAITING_COPY.readingPlan} />}
        {query.error || resumeEntry ? (
          <div className="actions">
            {resumeEntry}
            {query.error ? (
              <button className="primary block" type="button" onClick={() => void query.refetch().catch(() => undefined)}>Try again</button>
            ) : null}
          </div>
        ) : null}
      </div>
    );
  }

  const waiting = waitingForDesktop(data);
  const step = stepOf(data);
  // What comes next, dated. The finish says it as read at the session's end while that is
  // still today in the plan's calendar; otherwise (no finish, or the day has turned) Today says it as read now, once
  // the plan is done or holds nothing, leaving what is being written to a book's own line when one shows.
  const snapshot = finished && !session && finished.nextPractice
    && (!nextPractice || nextPractice.calendar.today === finished.nextPractice.calendar.today) ? finished.nextPractice : null;
  const snapshotLines = nextPracticeLines(snapshot, { finish: true });
  const finishedLine = finished && !session ? (
    <>
      <p className="banner" role="status">
        Session finished: {finished.attemptsRecorded} {finished.attemptsRecorded === 1 ? "answer" : "answers"}.
      </p>
      {snapshotLines.length ? (
        <div className="dim" data-testid="session-next">
          {snapshotLines.map((line) => <p key={line}>{line}</p>)}
        </div>
      ) : null}
    </>
  ) : null;
  const nextLines = (lines: string[]) => (!snapshot && lines.length ? (
    <div className="dim" role="status" data-testid="today-next">
      {lines.map((line) => <p key={line}>{line}</p>)}
    </div>
  ) : null);
  const todayNext = nextLines(nextPracticeLines(nextPractice, { writing: cause === null }));

  async function chooseMinutes(minutes: number) {
    setMinutesBusy(true);
    try {
      setQueryData(planKey(sessionId), await phone.setPlanMinutes(minutes, sessionId), [TAG.queue]);
    } catch (error) {
      onError(error);
    } finally {
      setMinutesBusy(false);
    }
  }

  const held = step?.kind === "held_for_desktop" ? step : null;
  if (plan.status !== "open" || held?.stopOffer) {
    // J5: the stop offer, in both directions. "Keep going" is the primary action; the stop is the engine's.
    // A stop drawn while work waits for the desktop is offered the same way: the plan stays open for
    // that work, and Keep going overrides the stop in place (Codex re-review of V2, F7).
    return (
      <div className="screen">
        <h1>Today</h1>
        {finishedLine}
        {offersQuestions ? null : <p data-testid="today-sentence">{causeLine ? "Nothing planned for today." : doneLine(data)}</p>}
        {causeLine}
        {todayNext}
        {waiting ? <p className="dim" role="status">{waiting}</p> : null}
        <div className="actions">
          {resumeEntry}
          <button className="primary block" type="button" disabled={busy} onClick={() => onKeepGoing(false)}>Keep going</button>
          <div className="row">
            {session ? <button className="plain" type="button" disabled={busy} onClick={() => onKeepGoing(true)}>Done for today</button> : null}
          </div>
        </div>
      </div>
    );
  }

  const why = currentWhy(plan);
  const sentence = planSentence(plan);
  return (
    <div className="screen">
      <h1>Today</h1>
      {finishedLine}
      <p data-testid="today-sentence">
        {held && !sentence ? "Nothing here for the phone right now." : sentence ?? (offersQuestions ? "" : "Nothing planned for today.")}{" "}
        <WhyLink why={why.why} details={why.details} explainId={why.decisionId} />
      </p>
      {!held && !sentence ? causeLine : null}
      {!held && !sentence && empty ? todayNext : null}
      <RouterLine decision={data.routerDecision} explainId={why.decisionId} />
      {waiting ? <p className="dim" role="status">{waiting}</p> : null}
      {/* IH6: the desktop's open workbench holds what a read would decide; the phone's Next is an explicit step and decides. */}
      {plan.questionInProgress && !choosing ? (
        <p className="dim" role="status" data-testid="today-in-progress">A question is in progress on the desktop. Next here goes on without it.</p>
      ) : null}
      {choosing ? <Waiting testId="choosing-wait" line={WAITING_COPY.choosingNext} /> : null}
      {!session && plan.minuteChoices.length ? (
        <div className="chips" aria-label="Minutes today">
          {plan.minuteChoices.map((minutes) => (
            <button
              key={minutes}
              className="plain"
              type="button"
              aria-pressed={minutes === plan.rememberedMinutes}
              disabled={busy || minutesBusy || minutes === plan.rememberedMinutes}
              onClick={() => void chooseMinutes(minutes)}
            >
              {minutes} min
            </button>
          ))}
        </div>
      ) : null}
      <div className="actions">
        {resumeEntry}
        {session ? (
          <button className="primary block" type="button" disabled={busy || choosing} onClick={() => onNext()}>Next</button>
        ) : (
          <button className="primary block" type="button" disabled={busy} onClick={() => onBegin(Math.max(1, Math.round(plan.minutesBudget)))}>Begin</button>
        )}
        <div className="row">
          {session && held?.firstHeldItemId ? (
            <button className="plain" type="button" disabled={busy || choosing} onClick={() => onNext(held.firstHeldItemId)}>Skip it</button>
          ) : null}
          {session ? <button className="plain" type="button" disabled={busy} onClick={onEnd}>End session</button> : null}
        </div>
        {session && onSomethingElse && query.data?.somethingElse ? (
          <SomethingElse sessionId={session.sessionId} surface="phone_today" onServed={onSomethingElse}
                         onAgreed={() => onNext()} onError={onError} />
        ) : null}
      </div>
    </div>
  );
}
