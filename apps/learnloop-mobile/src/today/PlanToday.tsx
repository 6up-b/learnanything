// Mobile v2 §2.2, J1/J4/J5: the phone's Today is the shared plan (owner decision D1), filtered at
// the step by the host. One sentence, the router's line, the one count that explains an absence,
// and one primary action in the thumb zone: Begin, Next, or (the plan done) Keep going. Everything
// shown is the plan DTO's; nothing here decides what comes next.
import { useEffect, useState } from "react";
import type { CommandError, SessionEndSummary, SessionSnapshot } from "@desktop/api/dto";
import { setQueryData } from "@desktop/api/queryCache";
import { TAG } from "@desktop/api/queryTags";
import { useCachedQuery } from "@desktop/api/useCachedQuery";
import { phone, type PhonePlanDto } from "../api/phone";
import { RouterLine, WhyLink } from "../practice/RouterLine";
import { currentWhy, doneLine, planSentence, stepOf, waitingForDesktop } from "./planWords";

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
  onError: (error: unknown) => void;
}) {
  const sessionId = session?.sessionId ?? null;
  const query = useCachedQuery<PhonePlanDto>(planKey(sessionId), () => phone.getDailyPlan(sessionId), { tags: [TAG.queue] });
  const [minutesBusy, setMinutesBusy] = useState(false);
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

  const data = query.data;
  const plan = data?.plan ?? null;
  if (!data || !plan) {
    return (
      <div className="screen">
        <h1>Today</h1>
        <p className="dim" role="status">{query.error ? "Today's plan couldn't be read." : "Reading today's plan…"}</p>
        {query.error ? (
          <div className="actions">
            <button className="primary block" type="button" onClick={() => void query.refetch().catch(() => undefined)}>Try again</button>
          </div>
        ) : null}
      </div>
    );
  }

  const waiting = waitingForDesktop(data);
  const step = stepOf(data);
  const finishedLine = finished && !session ? (
    <p className="banner" role="status">
      Session finished: {finished.attemptsRecorded} {finished.attemptsRecorded === 1 ? "answer" : "answers"}.
    </p>
  ) : null;

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
        <p data-testid="today-sentence">{doneLine(data)}</p>
        {waiting ? <p className="dim" role="status">{waiting}</p> : null}
        <div className="actions">
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
        {held && !sentence ? "Nothing here for the phone right now." : sentence ?? "Nothing planned for today."}{" "}
        <WhyLink why={why.why} details={why.details} explainId={why.decisionId} />
      </p>
      <RouterLine decision={data.routerDecision} explainId={why.decisionId} />
      {waiting ? <p className="dim" role="status">{waiting}</p> : null}
      {choosing ? <p className="dim" role="status">Choosing what's next…</p> : null}
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
      </div>
    </div>
  );
}
