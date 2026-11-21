// What comes next, dated: the words the session's finish and Today say from the
// sidecar's one read-only summary (`next_practice`), on the desktop and the phone alike.
//
// Every day here is a date of the plan's own calendar (YYYY-MM-DD, as the sidecar read it), compared with that
// calendar's "today" as plain dates: no clock or zone of this device decides which day a question is due on.
// Nothing here forecasts: a day with nothing due says so, minutes appear only where the summary carries them, and
// questions still being written get no day.

import { useEffect, useRef } from "react";
import type { NextPracticeDto, NextPracticeGroupDto, ScheduledItemDto } from "../api/dto";

const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
/** A week: within it a day is named by its weekday, after it by its date. */
const WEEKDAY_SPAN = 6;

function dayNumber(date: string): number | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date);
  if (!match) return null;
  return Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])) / 86_400_000;
}

/** Whole calendar days from `today` to `date` (both plan-calendar dates); null for a malformed one. */
export function daysFrom(today: string, date: string): number | null {
  const a = dayNumber(today);
  const b = dayNumber(date);
  return a === null || b === null ? null : Math.round(b - a);
}

function dateWords(date: string, today: string): string {
  const day = new Date(dayNumber(date)! * 86_400_000);
  const year = day.getUTCFullYear();
  const sameYear = today.slice(0, 4) === String(year);
  return `${day.getUTCDate()} ${MONTHS[day.getUTCMonth()]}${sameYear ? "" : ` ${year}`}`;
}

/** A day as the words name it: "today", "tomorrow", a weekday within the week, a date after it. */
export function dayName(date: string, today: string): string {
  const days = daysFrom(today, date);
  if (days === null) return date;
  if (days <= 0) return "today";
  if (days === 1) return "tomorrow";
  if (days <= WEEKDAY_SPAN) return WEEKDAYS[new Date(dayNumber(date)! * 86_400_000).getUTCDay()];
  return dateWords(date, today);
}

/** "on 9 November" after the week, the bare name within it ("Monday", "tomorrow"). */
function onDay(date: string, today: string): string {
  const days = daysFrom(today, date);
  const name = dayName(date, today);
  return days !== null && days > WEEKDAY_SPAN ? `on ${name}` : name;
}

function count(n: number, one: string, many: string): string {
  return `${n} ${n === 1 ? one : many}`;
}

function aboutMinutes(minutes: number | null | undefined): string {
  if (minutes === null || minutes === undefined || !Number.isFinite(minutes)) return "";
  const whole = Math.max(1, Math.round(minutes));
  return ` · about ${count(whole, "minute", "minutes")}`;
}

export interface NextPracticeWordsOptions {
  /** The session's finish (a snapshot): it also says what is still due today and a check open now, which Today's
   *  own plan and list already say there. */
  finish?: boolean;
  /** Say the question work under way: questions still being written, and finished sections whose questions wait to
   *  be written (Today leaves both to its own line about a book's questions). */
  writing?: boolean;
  /** The questions written from the learner's reading (the books' `itemIds`: `todayCause.readingItemIds`). A check on
   *  your own that keeps one of them is said as that question kept, so a learner who was offered it knows where it
   *  went. */
  keptItemIds?: readonly string[] | null;
}

function groupOn(groups: readonly NextPracticeGroupDto[], date: string): NextPracticeGroupDto | undefined {
  return groups.find((group) => group.date === date && group.count > 0);
}

function laterChecks(next: NextPracticeDto): NextPracticeGroupDto[] {
  return next.checks.filter((group) => (daysFrom(next.calendar.today, group.date) ?? 0) > 0 && group.count > 0);
}

function keptIn(group: NextPracticeGroupDto, kept: ReadonlySet<string>): number {
  return group.itemIds.filter((id) => kept.has(id)).length;
}

function keptWords(kept: number, from: string): string {
  return kept === 1
    ? `1 question from your reading is kept for a check on your own, ${from}.`
    : `${kept} questions from your reading are kept for checks on your own, ${from}.`;
}

/** "1 question from your reading is kept for a check on your own, available from 5 December.": a question written
 *  from the reading (one Today offered) set aside after an answer for a later check on the learner's own, so it can no
 *  longer be asked now. The check chooses its question after an answer, so nothing can say so beforehand: this is
 *  said once it is kept. Null when no later check keeps one of `keptItemIds`. */
export function keptForCheckLine(next: NextPracticeDto | null | undefined, keptItemIds: readonly string[] | null | undefined): string | null {
  if (!next) return null;
  const kept = new Set(keptItemIds ?? []);
  const group = laterChecks(next).find((check) => keptIn(check, kept) > 0);
  return group ? keptWords(keptIn(group, kept), `available from ${dayName(group.date, next.calendar.today)}`) : null;
}

/** Questions answered that come back on a day. Only answered questions have a day (one never answered has none), and
 *  saying so keeps the line from reading as "nothing to do until then" beside questions that can be asked now. */
function comeBack(n: number, more: string): string {
  return `${n} ${more}${n === 1 ? "question you answered comes" : "questions you answered come"} back`;
}

/** The lines, in order: today (the finish only), tomorrow or the nearest later day, the next check on your own (and
 *  the one keeping a question from the reading), the questions still being written. Empty when there is nothing dated
 *  and nothing under way. No line says that nothing is due: beside questions ready now, "Nothing is due tomorrow"
 *  read as nothing to do until the date named. */
export function nextPracticeLines(next: NextPracticeDto | null | undefined, options: NextPracticeWordsOptions = {}): string[] {
  if (!next) return [];
  const { today, tomorrow } = next.calendar;
  const lines: string[] = [];
  const dueToday = groupOn(next.reviews, today);
  const dueTomorrow = groupOn(next.reviews, tomorrow);
  const writing = options.writing !== false && next.writing.topicCount > 0;
  // Finished sections whose writing waits for their book or the desktop. The topics held for a look (`next.held`) get
  // no words: Today's own line counts the held questions an OK would apply, from the books' facts.
  const waiting = options.writing !== false ? next.waiting?.sectionCount ?? 0 : 0;
  const checkNow = groupOn(next.checks, today);
  if (options.finish && dueToday) {
    lines.push(`Still due today: ${count(dueToday.count, "question", "questions")}${aboutMinutes(dueToday.minutes)}.`);
  }
  // With questions still due today, tomorrow's are those that come due then, on top of them.
  const more = dueToday ? "more " : "";
  if (dueTomorrow) {
    lines.push(`Tomorrow: ${comeBack(dueTomorrow.count, more)}${aboutMinutes(dueTomorrow.minutes)}.`);
  } else if (next.nextReviewDate) {
    lines.push(`${comeBack(groupOn(next.reviews, next.nextReviewDate)?.count ?? 1, more)} ${onDay(next.nextReviewDate, today)}.`);
  }
  if (options.finish && checkNow) {
    lines.push(checkNow.count === 1 ? "A check on your own is available now." : `${checkNow.count} checks on your own are available now.`);
  }
  // The next check on your own; and the one that keeps a question from the reading, named as that question (with any
  // other check of its day beside it).
  const kept = new Set(options.keptItemIds ?? []);
  const later = laterChecks(next);
  const keeping = later.find((group) => keptIn(group, kept) > 0);
  for (const group of later.filter((group, index) => index === 0 || group === keeping)) {
    const from = `available from ${dayName(group.date, today)}`;
    const own = group === keeping ? keptIn(group, kept) : 0;
    const rest = group.count - own;
    if (own > 0) lines.push(keptWords(own, from));
    if (rest === 1) lines.push(`${own > 0 ? "Another" : "A"} check on your own is ${from}.`);
    else if (rest > 1) lines.push(`${rest} ${own > 0 ? "other " : ""}checks on your own are ${from}.`);
  }
  if (writing) {
    lines.push(`Questions on ${next.writing.topicCount} more ${next.writing.topicCount === 1 ? "topic" : "topics"} are still being written.`);
  }
  if (waiting > 0) {
    lines.push(`Questions from ${waiting} finished ${waiting === 1 ? "section" : "sections"} are waiting to be written.`);
  }
  return lines;
}

/** The full list's words for a row the summary dates: when it comes back (its effective due) or, kept for a check on
 *  your own, from when that check is available. Null when the summary does not name the row. */
export function nextPracticeRowWhy(next: NextPracticeDto | null | undefined, item: Pick<ScheduledItemDto, "practiceItemId">): string | null {
  if (!next) return null;
  const today = next.calendar.today;
  const check = next.checks.find((group) => group.itemIds.includes(item.practiceItemId));
  if (check) {
    const days = daysFrom(today, check.date) ?? 0;
    return days <= 0 ? "on your own · no hints" : `a check on your own from ${dayName(check.date, today)}`;
  }
  const review = next.reviews.find((group) => group.itemIds.includes(item.practiceItemId));
  if (!review) return null;
  const days = daysFrom(today, review.date) ?? 0;
  if (days <= 0) return "coming back later today";
  return `comes back ${onDay(review.date, today)}`;
}

/** The summary a screen last read: a plan reply that does not carry one (a step's, the minutes') keeps the one read
 *  before, until the next read of Today brings a fresh one. */
export function useLatestNextPractice(next: NextPracticeDto | null | undefined): NextPracticeDto | null {
  const latest = useRef<NextPracticeDto | null>(null);
  if (next !== undefined) latest.current = next;
  return latest.current;
}

/** Read Today again when the plan's next day starts (the summary says when, in its own calendar), so "tomorrow" is
 *  never yesterday's. */
export function useNextDayRefresh(nextDayStartsAt: string | null | undefined, refresh: () => void): void {
  const refreshRef = useRef(refresh);
  refreshRef.current = refresh;
  useEffect(() => {
    if (!nextDayStartsAt) return undefined;
    const at = Date.parse(nextDayStartsAt);
    if (!Number.isFinite(at)) return undefined;
    // A timer holds at most about 24.8 days; a day is far less, and a day already begun refreshes at once.
    const delay = Math.min(Math.max(at - Date.now(), 0) + 1000, 2_000_000_000);
    const timer = window.setTimeout(() => refreshRef.current(), delay);
    return () => window.clearTimeout(timer);
  }, [nextDayStartsAt]);
}
