// Daily-loop DL1: Today as a finite plan (spec_daily_loop_v1.md §6.5, §6.7, §7).
//
// The split line, the current block, the next blocks ("about"), the block line
// at a boundary, the re-entry panel, the optional headline and the done screen.
// Every number shown is read from the plan DTO (gate G3); nothing here counts,
// estimates or sums on its own. No overdue count, no backlog, no capture debt.

import { useEffect, useState, type CSSProperties } from "react";
import type { DailyPlanDto, PlanBlockDto, PlanLane, TodayHeadlineDto } from "../../api/dto";
import { COLOR, FONT_MONO, KeyBar } from "../../components/term";
import { aboutMinutes, minutesPerDay, waitingLine, wholeMinutes } from "../../app/dailyPlan";

const LANE_COLOR: Record<PlanLane, string> = {
  repair: COLOR.red,
  maintain: COLOR.amber,
  new: COLOR.cyan,
  push: COLOR.green
};

function laneColor(lane: PlanLane | null | undefined): string {
  return lane ? LANE_COLOR[lane] : COLOR.textDim;
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

const actionButton = (primary = false): CSSProperties => ({
  padding: "6px 14px",
  border: `1px solid ${primary ? COLOR.amber : COLOR.border}`,
  background: primary ? "var(--wash-amber)" : "transparent",
  color: primary ? COLOR.amber : COLOR.text,
  cursor: "pointer",
  fontFamily: FONT_MONO,
  fontSize: 12
});

/** "25 min · maintain 13 · repair 4 · new 4 · push 4 (why)". */
export function PlanSplitLine({ plan }: { plan: NonNullable<DailyPlanDto["plan"]> }) {
  const [why, setWhy] = useState(false);
  return (
    <div style={{ fontFamily: FONT_MONO, fontSize: 13 }}>
      <span data-testid="plan-split-line" style={{ color: COLOR.text }}>
        {plan.split.line}
      </span>{" "}
      <button type="button" style={linkButton} onClick={() => setWhy((open) => !open)} aria-expanded={why}>
        (why)
      </button>
      {why ? (
        <ul data-testid="plan-split-why" style={{ margin: "6px 0 0", paddingLeft: 18, color: COLOR.textDim, fontSize: 12 }}>
          {plan.split.lanes.map((lane) => (
            <li key={lane.lane}>
              <span style={{ color: laneColor(lane.lane) }}>{lane.lane}</span> {lane.displayMinutes} min — {lane.reason}
            </li>
          ))}
          {plan.split.requestedMinutes > 0 ? (
            <li>your requests first: {aboutMinutes(plan.split.requestedMinutes)}, before the split</li>
          ) : null}
        </ul>
      ) : null}
    </div>
  );
}

/** "Block 2 of about 3 · maintain · about 8 min · why" (§6.5). */
export function PlanBlockLine({ plan, block }: { plan: NonNullable<DailyPlanDto["plan"]>; block: PlanBlockDto }) {
  const [why, setWhy] = useState(false);
  const total = Math.max(plan.blockCountEstimate, block.ordinal);
  const label = block.reading
    ? `reading ${block.reading.sectionTitle ?? ""}`.trim()
    : block.chosenBy === "learner_pick"
      ? "your pick"
      : block.lane ?? "block";
  return (
    <div data-testid="plan-block-line" style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.text }}>
      Block {block.ordinal} of about {total} · <span style={{ color: laneColor(block.lane) }}>{label}</span> ·{" "}
      {aboutMinutes(block.estMinutes)}
      {block.reading?.partial && block.reading.fullMinutes ? ` (of ${aboutMinutes(block.reading.fullMinutes)})` : ""} ·{" "}
      <button type="button" style={linkButton} onClick={() => setWhy((open) => !open)} aria-expanded={why}>
        why
      </button>
      {why ? (
        <div data-testid="plan-block-why" style={{ color: COLOR.textDim, fontSize: 12, marginTop: 4 }}>
          {block.why}
          {block.fallback ? " (the chooser's pick did not fit; the plan's own rule chose this)" : ""}
          {block.whyDetails ? (
            <details data-testid="plan-block-why-details" style={{ marginTop: 2 }}>
              <summary style={{ cursor: "pointer" }}>details</summary>
              {block.whyDetails}
            </details>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

/** "14 demonstrated · 3 assumed · 9 learning · 6 untested — expected recall today 87%". */
export function PlanHeadline({ headline }: { headline: TodayHeadlineDto | null }) {
  if (!headline?.enabled || !headline.line) return null;
  return (
    <div data-testid="plan-headline" style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim }} title={headline.expectedRecallTooltip}>
      {headline.line}
    </div>
  );
}

/** §7: survival-first. No overdue count, no streak, no debt. */
export function PlanReentryPanel({ reentry }: { reentry: NonNullable<NonNullable<DailyPlanDto["plan"]>["reentry"]> }) {
  const names = reentry.slippedNames.length ? ` (${reentry.slippedNames.join(", ")}${reentry.slippedCount > reentry.slippedNames.length ? ", …" : ""})` : "";
  return (
    <div
      data-testid="plan-reentry"
      role="status"
      style={{ padding: "10px 12px", borderLeft: `3px solid ${COLOR.cyan}`, background: COLOR.washCyan, fontSize: 13, color: COLOR.text }}
    >
      Welcome back — {reentry.gapDays} days. Still solid: {reentry.solidCount}. Slipped below target: {reentry.slippedCount}
      {names}. Today: a short re-entry, {aboutMinutes(reentry.planMinutes)}, {reentry.planItems} item
      {reentry.planItems === 1 ? "" : "s"}.
    </div>
  );
}

function BlockItems({ block }: { block: PlanBlockDto }) {
  const next = block.items.find((item) => item.state === "served") ?? block.items.find((item) => item.state === "planned");
  return (
    <ol style={{ margin: "6px 0 0", paddingLeft: 22, fontSize: 13 }}>
      {block.items.map((item) => {
        const current = item === next;
        const finished = item.state === "done" || item.state === "skipped";
        return (
          <li
            key={item.practiceItemId}
            data-testid="plan-item"
            data-state={item.state}
            aria-current={current ? "step" : undefined}
            style={{
              color: finished ? COLOR.textFaint : current ? COLOR.amber : COLOR.text,
              textDecoration: item.state === "skipped" ? "line-through" : undefined,
              padding: "1px 0"
            }}
          >
            {item.learningObjectTitle}
            <span style={{ color: COLOR.textFaint }}>
              {" "}· {aboutMinutes(item.estMinutes)}
              {item.origin === "followup" ? " · follow-up" : item.origin === "requested" ? " · your request" : ""}
              {item.state === "done" ? " · done" : item.state === "skipped" ? " · skipped" : ""}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

export interface DailyPlanViewProps {
  data: DailyPlanDto;
  headline: TodayHeadlineDto | null;
  busy?: boolean;
  /** Serve the next step (Enter / Continue). */
  onContinue: () => void;
  onSetMinutes: (minutes: number) => void;
  onKeepGoing: () => void;
  onDone: () => void;
  onMoreNew: (confirm: boolean) => void;
  moreNewPreview?: DailyPlanDto["preview"] | null;
  onShowList: () => void;
  onSkip?: (practiceItemId: string) => void;
  /** Skip a current reading block from the block line (§6.10). */
  onSkipReading?: () => void;
}

/** Today, during the plan and when it is done (§6.5, §6.7). */
export function DailyPlanView({
  data,
  headline,
  busy = false,
  onContinue,
  onSetMinutes,
  onKeepGoing,
  onDone,
  onMoreNew,
  moreNewPreview = null,
  onShowList,
  onSkip,
  onSkipReading
}: DailyPlanViewProps) {
  const plan = data.plan;
  const done = plan ? plan.status !== "open" : false;
  const current = plan?.blocks.find((block) => block.id === plan.currentBlockId) ?? null;

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea" || event.defaultPrevented || busy) return;
      if (event.key === "Enter") {
        event.preventDefault();
        if (done) onKeepGoing();
        else onContinue();
      } else if (event.key === "l") {
        event.preventDefault();
        onShowList();
      } else if (done && event.key === "d") {
        event.preventDefault();
        onDone();
      } else if (!done && plan && (event.key === "ArrowLeft" || event.key === "ArrowRight")) {
        event.preventDefault();
        const choices = plan.minuteChoices;
        const index = choices.indexOf(plan.rememberedMinutes);
        const next = choices[Math.max(0, Math.min(choices.length - 1, (index < 0 ? 0 : index) + (event.key === "ArrowLeft" ? -1 : 1)))];
        if (next !== undefined && next !== plan.rememberedMinutes) onSetMinutes(next);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [busy, done, onContinue, onDone, onKeepGoing, onSetMinutes, onShowList, plan]);

  if (!plan) return null;
  const day = data.day;
  const streak = data.streak;
  const upcoming = plan.projected[0] ?? null;

  return (
    <div data-testid="daily-plan" style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ padding: "16px 22px", display: "flex", flexDirection: "column", gap: 12, overflowY: "auto", flex: 1 }}>
        {plan.kind === "reentry" && plan.reentry && !done ? <PlanReentryPanel reentry={plan.reentry} /> : null}
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <span style={{ fontFamily: FONT_MONO, color: COLOR.amber, fontWeight: 600 }}>
            {plan.kind === "keep_going" ? "Keep going" : plan.kind === "reentry" ? "Re-entry" : "Today"}
          </span>
          <PlanSplitLine plan={plan} />
        </div>
        <div role="radiogroup" aria-label="minutes today" style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {plan.minuteChoices.map((minutes) => {
            const selected = minutes === plan.rememberedMinutes;
            return (
              <span
                key={minutes}
                role="radio"
                aria-checked={selected}
                onClick={() => !selected && onSetMinutes(minutes)}
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
        <PlanHeadline headline={data.headlineEnabled === false ? null : headline} />

        {done ? (
          <PlanDone
            data={data}
            day={day}
            streakDays={streak?.current ?? null}
            streakToday={streak?.activeToday ?? false}
            onKeepGoing={onKeepGoing}
            onDone={onDone}
            onMoreNew={onMoreNew}
            moreNewPreview={moreNewPreview}
            busy={busy}
          />
        ) : current ? (
          <div style={{ border: `1px solid ${COLOR.border}`, padding: "10px 14px" }}>
            <PlanBlockLine plan={plan} block={current} />
            {current.reading ? (
              <div style={{ fontSize: 13, marginTop: 6, color: COLOR.text }}>
                Continue {current.reading.sectionTitle} · {aboutMinutes(current.estMinutes)}
                {current.reading.partial && current.reading.fullMinutes ? ` (of ${aboutMinutes(current.reading.fullMinutes)})` : ""}
                {onSkipReading ? (
                  <button type="button" style={linkButton} onClick={onSkipReading}>
                    skip
                  </button>
                ) : null}
              </div>
            ) : (
              <BlockItems block={current} />
            )}
            <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
              <button type="button" style={actionButton(true)} onClick={onContinue} disabled={busy}>
                {busy ? "opening…" : current.startedAt ? "continue ↵" : "begin ↵"}
              </button>
              {onSkip && !current.reading ? (
                <button
                  type="button"
                  style={actionButton()}
                  disabled={busy}
                  onClick={() => {
                    const next = current.items.find((item) => item.state === "served" || item.state === "planned");
                    if (next) onSkip(next.practiceItemId);
                  }}
                >
                  skip this item
                </button>
              ) : null}
            </div>
          </div>
        ) : plan.waiting ? (
          <div data-testid="plan-waiting" style={{ fontSize: 13, color: COLOR.textDim }}>
            {waitingLine(plan.waiting)}
          </div>
        ) : (
          <div data-testid="plan-choosing" style={{ fontSize: 13, color: COLOR.textDim }}>
            Choosing the next block…
            {plan.deciding ? (
              <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
                <button type="button" style={actionButton(true)} onClick={onContinue} disabled={busy}>
                  {busy ? "opening…" : "begin ↵"}
                </button>
              </div>
            ) : null}
          </div>
        )}

        {!done && upcoming ? (
          <div data-testid="plan-next" style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim }}>
            next: {upcoming.readingTitle ? `reading ${upcoming.readingTitle}` : upcoming.lane} · {aboutMinutes(upcoming.estMinutes)}
            {plan.projected.length > 1 ? ` · then ${plan.projected.length - 1} more` : ""}
          </div>
        ) : null}
      </div>
      <KeyBar
        keys={
          done
            ? [
                { key: "↵", label: "keep going" },
                { key: "d", label: "done" },
                { key: "l", label: "full list" }
              ]
            : [
                { key: "↵", label: current?.startedAt ? "continue" : "begin" },
                { key: "←/→", label: "minutes" },
                { key: "l", label: "full list" }
              ]
        }
      />
    </div>
  );
}

/** "Today complete · 26 min · 9 items", the streak marked, keep going or done (§6.5). */
export function PlanDone({
  data,
  day,
  streakDays,
  streakToday,
  onKeepGoing,
  onDone,
  onMoreNew,
  moreNewPreview,
  busy
}: {
  data: DailyPlanDto;
  day: DailyPlanDto["day"];
  streakDays: number | null;
  streakToday: boolean;
  onKeepGoing: () => void;
  onDone: () => void;
  onMoreNew: (confirm: boolean) => void;
  moreNewPreview: DailyPlanDto["preview"] | null;
  busy: boolean;
}) {
  const plan = data.plan!;
  const empty = (day?.plannedItems ?? 0) === 0 && (day?.readingBlocks ?? 0) === 0;
  const reentry = plan.kind === "reentry";
  const title = empty
    ? "Nothing due today"
    : reentry
      ? "Re-entry done. Keep going?"
      : "Today complete";
  return (
    <div data-testid="plan-done" style={{ border: `1px solid ${COLOR.border}`, padding: "12px 14px", display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ fontSize: 15, color: COLOR.text }}>
        <span data-testid="plan-done-title">{title}</span>
        {!empty && day ? (
          <span data-testid="plan-done-figures" style={{ color: COLOR.textDim }}>
            {" "}· {wholeMinutes(day.actualMinutes)} min · {day.doneItems} item{day.doneItems === 1 ? "" : "s"}
          </span>
        ) : null}
        {streakDays && streakDays > 0 ? (
          <span style={{ color: COLOR.amber, fontFamily: FONT_MONO, fontSize: 12 }}>
            {" "}· ● {streakDays} day{streakDays === 1 ? "" : "s"} streak{streakToday ? " · today ✓" : ""}
          </span>
        ) : null}
      </div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button type="button" style={actionButton(true)} onClick={onKeepGoing} disabled={busy}>
          keep going ↵
        </button>
        <button type="button" style={actionButton()} onClick={onDone} disabled={busy}>
          done
        </button>
        {!reentry ? (
          <button type="button" style={actionButton()} onClick={() => onMoreNew(false)} disabled={busy}>
            more new material
          </button>
        ) : null}
      </div>
      {moreNewPreview ? (
        <div data-testid="plan-more-new" style={{ fontSize: 12, color: COLOR.textDim }}>
          {moreNewPreview.available ? (
            <>
              {moreNewPreview.items} new item{moreNewPreview.items === 1 ? "" : "s"}, {aboutMinutes(moreNewPreview.estMinutes)} today ·
              adds about {minutesPerDay(moreNewPreview.addsMinutesPerDay)} min/day of reviews for two weeks.{" "}
              <button type="button" style={linkButton} onClick={() => onMoreNew(true)} disabled={busy}>
                add them
              </button>
            </>
          ) : (
            "No new material is ready to add."
          )}
        </div>
      ) : null}
    </div>
  );
}
