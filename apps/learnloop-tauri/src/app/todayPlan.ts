// UX Phase 3: Today in the simple shell (docs/specs/ux_learnloop_v1.md §7.1,
// §4.2 rules 9 and 10, §10 3.1-3.4).
//
// Today is one sentence and Enter: "25 minutes today: finish §5.4 Mixtures,
// then 6 short questions from earlier days." These helpers turn the plan DTO
// into the learner's words. They format; they decide nothing and estimate
// nothing (the daily loop's gate G3: every number shown is one the plan DTO
// carries). The lanes (maintain, repair, new, push) are never named on the
// surface: each is described by what it does, and the split is behind why?.
// No count of waiting things appears anywhere (rule 10): a plan is minutes,
// and the threads are things to pick up, never totals.

import { api } from "../api/client";
import type {
  DailyPlanBodyDto,
  DailyPlanDto,
  PlanBlockDto,
  PlanItemDto,
  PlanLane,
  PlanProjectedBlockDto,
  QuestionQueueRowDto,
  ScheduledItemDto,
  StreakSummary,
  WorkbenchOpenProblemDto
} from "../api/dto";
import { aboutMinutes, wholeMinutes } from "./dailyPlan";

type Plan = DailyPlanBodyDto;

/** "Tuesday evening": the day and the part of it, in the learner's clock. */
export function dayPhrase(now: Date = new Date()): string {
  const weekday = now.toLocaleDateString(undefined, { weekday: "long" });
  const hour = now.getHours();
  // The ordinary parts of a day (a calendar convention, not a parameter).
  const part = hour < 5 ? "night" : hour < 12 ? "morning" : hour < 17 ? "afternoon" : hour < 22 ? "evening" : "night";
  return `${weekday} ${part}`;
}

function titles(list: readonly string[]): string {
  const unique = [...new Set(list.filter(Boolean))];
  if (unique.length <= 2) return unique.join(" and ");
  return `${unique.slice(0, 2).join(", ")} and more`;
}

function questions(count: number): string {
  return count === 1 ? "1 short question" : `${count} short questions`;
}

/** What a lane does, in words, for the plan sentence (never the lane's name). */
function lanePhrase(lane: PlanLane | null, itemCount: number, loTitles: readonly string[]): string {
  const about = titles(loTitles);
  switch (lane) {
    case "maintain":
      return `${questions(itemCount)} from earlier days`;
    case "repair":
      return "a fix for a mix-up";
    case "new":
      return about ? `new: ${about}` : "something new";
    case "push":
      return about ? `a step further on ${about}` : "a step further";
    default:
      return about ? about : questions(itemCount);
  }
}

/** The block's row on the surface: what it is, in words. */
function laneRow(lane: PlanLane | null, itemCount: number, loTitles: readonly string[]): string {
  const about = titles(loTitles);
  switch (lane) {
    case "maintain":
      return about ? `${questions(itemCount)} · ${about}` : questions(itemCount);
    case "repair":
      return about ? `Fix a mix-up · ${about}` : "Fix a mix-up";
    case "new":
      return about ? `New: ${about}` : "Something new";
    case "push":
      return about ? `A step further · ${about}` : "A step further";
    default:
      return about || questions(itemCount);
  }
}

function readingStarted(block: PlanBlockDto): boolean {
  return Boolean(block.startedAt) || (block.reading?.spansSeen ?? 0) > 0;
}

function readingTitle(title: string | null | undefined): string {
  return title && title.trim() ? title.trim() : "the next section";
}

/** One block of today's plan as the surface shows it. */
export interface TodayRow {
  key: string;
  /** The block being worked now (or the one Begin opens). */
  current: boolean;
  text: string;
  /** "about 12 min": an estimate, always labelled as one. */
  minutes: string;
  /** The plan's own reason for the block (why? only). */
  why: string | null;
  /** The receipts behind that reason (details ▸ inside why?). */
  whyDetails: string | null;
  /** Items to answer on your own (a check whether a fix held). */
  onYourOwn: boolean;
}

function chosenRow(block: PlanBlockDto, current: boolean): TodayRow {
  let text: string;
  if (block.reading) {
    text = `${readingStarted(block) ? "Continue" : "Read"} ${readingTitle(block.reading.sectionTitle)}`;
  } else if (block.chosenBy === "learner_pick") {
    text = `Your pick · ${titles(block.learningObjectTitles) || "a question"}`;
  } else {
    const items = block.items.filter((item) => item.state === "planned" || item.state === "served").length || block.items.length;
    text = laneRow(block.lane, items, block.learningObjectTitles);
  }
  return {
    key: block.id,
    current,
    text,
    minutes: aboutMinutes(block.estMinutes),
    why: block.why || null,
    whyDetails: block.whyDetails ?? null,
    onYourOwn: block.items.some(onYourOwnItem)
  };
}

function projectedRow(block: PlanProjectedBlockDto): TodayRow {
  const text = block.readingTitle ? `Read ${readingTitle(block.readingTitle)}` : laneRow(block.lane, block.itemCount, block.learningObjectTitles);
  return {
    key: `projected:${block.ordinal}`,
    current: false,
    text,
    minutes: aboutMinutes(block.estMinutes),
    why: block.why || null,
    whyDetails: null,
    onYourOwn: false
  };
}

/** A plan item that checks, on your own, whether an earlier fix held. */
export function onYourOwnItem(item: PlanItemDto): boolean {
  return item.origin === "followup" && (item.state === "planned" || item.state === "served");
}

/** The blocks still ahead: the current one, the chosen ones after it, then
 *  the projection (if nothing changes). Finished blocks are not listed. */
export function todayRows(plan: Plan): TodayRow[] {
  const rows: TodayRow[] = [];
  for (const block of plan.blocks) {
    if (block.status === "done") continue;
    rows.push(chosenRow(block, block.id === plan.currentBlockId));
  }
  for (const block of plan.projected) rows.push(projectedRow(block));
  return rows;
}

function sentencePhrase(row: { reading: string | null; started: boolean; lane: PlanLane | null; items: number; titles: readonly string[]; pick: boolean }): string {
  if (row.reading !== null) return `${row.started ? "finish" : "read"} ${readingTitle(row.reading)}`;
  if (row.pick) return `your pick, ${titles(row.titles) || "a question"}`;
  return lanePhrase(row.lane, row.items, row.titles);
}

function joinPhrases(phrases: string[]): string {
  if (phrases.length <= 1) return phrases[0] ?? "";
  if (phrases.length === 2) return `${phrases[0]}, then ${phrases[1]}`;
  return `${phrases[0]}, then ${phrases.slice(1, -1).join(", ")} and ${phrases[phrases.length - 1]}`;
}

function minutesWord(minutes: number): string {
  return minutes === 1 ? "1 minute" : `${minutes} minutes`;
}

/** "25 minutes today: finish §5.4 Mixtures, then 6 short questions from
 *  earlier days and a fix for a mix-up." Null when nothing is planned. */
export function planSentence(plan: Plan): string | null {
  const phrases: string[] = [];
  for (const block of plan.blocks) {
    if (block.status === "done") continue;
    phrases.push(
      sentencePhrase({
        reading: block.reading ? block.reading.sectionTitle ?? "" : null,
        started: readingStarted(block),
        lane: block.lane,
        items: block.items.filter((item) => item.state === "planned" || item.state === "served").length || block.items.length,
        titles: block.learningObjectTitles,
        pick: block.chosenBy === "learner_pick"
      })
    );
  }
  for (const block of plan.projected) {
    phrases.push(
      sentencePhrase({ reading: block.readingTitle, started: false, lane: block.lane, items: block.itemCount, titles: block.learningObjectTitles, pick: false })
    );
  }
  if (phrases.length === 0) return null;
  const begun = plan.blocks.some((block) => block.status === "done" || Boolean(block.startedAt));
  const head = begun
    ? `About ${minutesWord(Math.max(1, Math.round(plan.minutesLeft)))} left today`
    : `${minutesWord(Math.max(1, Math.round(plan.minutesBudget)))} today`;
  return `${head}: ${joinPhrases(phrases)}.`;
}

/** Re-entry after a break (DL P6): a short plan, and no debt screen. What
 *  slipped is behind why?, never on the surface. */
export function reentrySentence(plan: Plan): string {
  const minutes = plan.reentry ? Math.max(1, Math.round(plan.reentry.planMinutes)) : Math.max(1, Math.round(plan.minutesBudget));
  return `Welcome back. A short catch-up today: ${minutesWord(minutes)} of the most useful questions. Nothing else is waiting on you.`;
}

/** The re-entry's why?: how long away, and what it chose to bring back. */
export function reentryWhy(plan: Plan): string | null {
  const reentry = plan.reentry;
  if (!reentry) return null;
  const away = `You were away ${reentry.gapDays} day${reentry.gapDays === 1 ? "" : "s"}.`;
  const named = reentry.slippedNames.length ? ` Today's catch-up starts with what faded most: ${reentry.slippedNames.join(", ")}.` : "";
  return `${away}${named} The rest comes back over the next days, a little at a time.`;
}

/** The split behind the plan, in words: what each part is for and its minutes. */
export function splitWhy(plan: Plan): string[] {
  const words: Record<PlanLane, string> = {
    maintain: "keeping what you know",
    repair: "fixing mix-ups",
    new: "new material",
    push: "going further toward your goals"
  };
  const lines = plan.split.lanes
    .filter((lane) => lane.displayMinutes > 0)
    .map((lane) => `${aboutMinutes(lane.displayMinutes)} for ${words[lane.lane]}${lane.reason ? ` (${lane.reason})` : ""}`);
  if (plan.split.requestedMinutes > 0) lines.unshift(`${aboutMinutes(plan.split.requestedMinutes)} for what you asked for, first`);
  return lines;
}

/** "Done for today · 26 minutes." The time spent, never a count of items. */
export function doneLine(data: DailyPlanDto): string {
  const minutes = wholeMinutes(data.day?.actualMinutes);
  return minutes > 0 ? `Done for today · ${minutesWord(minutes)}.` : "Done for today.";
}

/** Whether the day's plan had anything in it. */
export function planWasEmpty(data: DailyPlanDto): boolean {
  return (data.day?.plannedItems ?? 0) === 0 && (data.day?.readingBlocks ?? 0) === 0;
}

/** The footer's streak: "4 days · best 9". Never red, never a loss. */
export function streakLine(streak: StreakSummary | null | undefined): string | null {
  if (!streak || streak.current <= 0) return null;
  const days = `${streak.current} day${streak.current === 1 ? "" : "s"}`;
  return streak.longest > streak.current ? `${days} · best ${streak.longest}` : days;
}

// ── Threads (§7.1 "Pick up a thread", Reader doc U12) ───────────────────────

export const THREADS_SHOWN = 3; // the spec's "at most three, then more ▸" (a layout bound)

export type TodayThread =
  | { kind: "question"; key: string; text: string; place: string | null; question: QuestionQueueRowDto }
  | { kind: "problem"; key: string; text: string; steps: string; problem: WorkbenchOpenProblemDto };

function oneLine(markdown: string, limit = 80): string {
  const text = markdown.replace(/\s+/g, " ").replace(/[*_`#>]/g, "").trim();
  return text.length > limit ? `${text.slice(0, limit - 1).trimEnd()}…` : text;
}

/** An open question to pick up: its words and, when it has one, its passage. */
export function questionThread(row: QuestionQueueRowDto): TodayThread {
  return {
    kind: "question",
    key: `q:${row.id}`,
    text: `“${oneLine(row.questionMd)}”`,
    place: row.sourceCitation?.label ?? null,
    question: row
  };
}

/** An unfinished problem: its statement and how far the learner got. */
export function problemThread(problem: WorkbenchOpenProblemDto): TodayThread {
  const steps = problem.stepCount === 1 ? "1 step written" : problem.stepCount > 1 ? `${problem.stepCount} steps written` : "not started";
  return { kind: "problem", key: `p:${problem.sessionId}`, text: oneLine(problem.stemMd), steps, problem };
}

/** Threads, newest first: open questions and unfinished problems. */
export function todayThreads(questionRows: readonly QuestionQueueRowDto[], problems: readonly WorkbenchOpenProblemDto[]): TodayThread[] {
  const open = questionRows.filter((row) => row.resolution === "open");
  const dated: Array<{ at: string; thread: TodayThread }> = [
    ...open.map((row) => ({ at: row.createdAt, thread: questionThread(row) })),
    ...problems.map((problem) => ({ at: problem.updatedAt, thread: problemThread(problem) }))
  ];
  dated.sort((a, b) => (a.at < b.at ? 1 : a.at > b.at ? -1 : 0));
  return dated.map((entry) => entry.thread);
}

// ── The full list (`l`): a plain list ───────────────────────────────────────

/** Why an item is on today's list, in about five words. */
export function fullListWhy(item: ScheduledItemDto): string {
  if (item.isFollowup) {
    switch (item.followupKind) {
      case "certification_cold_probe":
        return "on your own · no hints";
      case "cold_retry":
        return "on your own · no hints";
      case "intervention_followup":
        return "after a fix, once more";
      case "negative_surprise_followup":
        return "a second look";
      default:
        return "a second look";
    }
  }
  if (item.isProbe) return "to see what you know";
  if (item.dueStatus === "due") return "time to bring it back";
  if (item.dueStatus === "later") return "coming back later today";
  return "next up for you";
}

/** The why? behind a check on your own (the Reader doc's cold wording). */
export function onYourOwnWhy(item: ScheduledItemDto): string | null {
  if (!item.isFollowup) return null;
  if (item.followupKind === "cold_retry") return "To see whether last week's fix held. Help is still here — using it makes this practice with help.";
  if (item.followupKind === "certification_cold_probe") return "To see whether it has held, on your own. Help is still here — using it makes this practice with help.";
  return null;
}

// ── Implicit sessions (§7.1, §10 3.2) ───────────────────────────────────────

/**
 * The minutes an implicit session opens with: the plan's minutes while the
 * plan serves (as Today's Begin does), else the remembered minutes (the last
 * session's, or the first-run default the sidecar names). Null when neither
 * can be read: the caller says it couldn't start, and starts nothing.
 */
export async function implicitSessionMinutes(): Promise<number | null> {
  try {
    const plan = await api.getDailyPlan(null);
    if (plan?.enabled && plan.plan) return Math.max(1, Math.round(plan.plan.minutesBudget));
  } catch {
    /* fall through to the remembered minutes */
  }
  try {
    const summary = await api.getStartSummary();
    if (summary && Number.isFinite(summary.rememberedMinutes)) return summary.rememberedMinutes;
  } catch {
    /* nothing to start with */
  }
  return null;
}
