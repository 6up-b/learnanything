// RW6a's words (spec §9.1; UX §4.0 microcopy, §4.8, U6, U12): the well's
// markers, never a percentage; headings with no counts; nothing "overdue";
// no trait words; the learner's own words quoted, in their voice.
import type { ReaderObservationKind } from "../../api/dto";

export const RECAP_COPY = {
  title: "Last time here",
  stillOpen: "Still open",
  unfinished: "Unfinished",
  secondLook: "Worth a second look",
  sinceLastTime: "Since last time",
  lastTime: "last time ▸",
  resume: "Resume this problem ▸",
  reopen: "Reopen this problem ▸",
  setAside: "set aside",
  wrapUp: "Wrap up",
  wrapUpOffer: "Wrap up (under a minute)",
  wrapUpReady: "Reading wrap-up ready — under a minute ▸",
  resolved: "Resolved",
  worthReinforcing: "Worth reinforcing",
  nothingToWrap: "Nothing to wrap up from this session.",
} as const;

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "Thu 9 Oct" (local time). */
export function fullDay(iso: string): string {
  const when = new Date(iso);
  if (Number.isNaN(when.getTime())) return "";
  return `${DAYS[when.getDay()]} ${when.getDate()} ${MONTHS[when.getMonth()]}`;
}

/** "Mon" within the last six days, else "9 Oct" (local time). */
export function shortDay(iso: string, now: Date = new Date()): string {
  const when = new Date(iso);
  if (Number.isNaN(when.getTime())) return "";
  const days = (now.getTime() - when.getTime()) / 86_400_000;
  if (days >= 0 && days < 6) return DAYS[when.getDay()];
  return `${when.getDate()} ${MONTHS[when.getMonth()]}`;
}

/** "about 40 min" for a session's length; nothing for a moment's visit. */
export function aboutMinutes(minutes: number): string | null {
  if (!Number.isFinite(minutes) || minutes < 1) return null;
  if (minutes < 90) return `about ${Math.round(minutes)} min`;
  return `about ${Math.round(minutes / 60)} h`;
}

/** A formative record in plain words (the learner's quoted words where it has them). */
export function observationLine(kind: ReaderObservationKind | string, quoted?: string | null, observed?: Record<string, unknown> | null): string {
  // RW1b: whose answer it was compared with -- the book's own lines, or
  // LearnLoop's model's when the book does not say it (answer_basis).
  const whose = observed?.answerBasis === "model" ? "LearnLoop's model's answer" : "the book's";
  switch (kind) {
    case "still_unclear":
      return quoted ? `your question “${quoted}” — still unclear when you came back to it` : "a question still unclear when you came back to it";
    case "next_step_missed":
      return `your next-step guess differed from ${whose}`;
    case "why_step_missed":
      return `your answer to why a step holds differed from ${whose}`;
    case "assumption_missed":
      return `your answer about the assumptions differed from ${whose}`;
    case "prediction_missed":
      return "a figure prediction that turned out differently";
    default:
      return "worth a second look";
  }
}

export function stepsLabel(count: number): string {
  return `${count} step${count === 1 ? "" : "s"}`;
}

// RW6b's "Coming up" (spec §9.3; UX §4.8-4.9, S15, D36): a dated timeline,
// never a count; retirements read as good news; never "overdue" or "due".
export const COMING_UP_COPY = {
  title: "Coming up · checks on your own",
  why: "why",
  undo: "undo",
  undoAll: "undo all",
  keep: "keep it",
  undone: "undone",
  restore: "keep it after all",
  later: "later ▸",
  reasonLabel: "why undo this check? (optional)",
  reasonPlaceholder: "why? (optional)",
  settled: "No longer needed: the explanations it was to tell apart are settled",
} as const;

/** The good news for a check retired as no longer needed: how its question
 *  was answered, on the solve's own day (never the retirement's). */
export function retiredCheckLine(
  line: { retiredAt: string; answeredBy?: string | null; solvedAt?: string | null },
  now: Date = new Date(),
): string {
  if (line.answeredBy === "rivals_resolved") return COMING_UP_COPY.settled;
  return `No longer needed: you solved one like it on ${shortDay(line.solvedAt ?? line.retiredAt, now)}`;
}

/** A plan day ("YYYY-MM-DD", local): "Wed" within the coming six days, else "9 Nov". */
export function upcomingDay(day: string, now: Date = new Date()): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(day);
  if (!match) return "";
  const when = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const days = Math.round((when.getTime() - today.getTime()) / 86_400_000);
  if (days >= 0 && days < 7) return DAYS[when.getDay()];
  return `${when.getDate()} ${MONTHS[when.getMonth()]}`;
}

/** "about 6 min" for a check; nothing when unknown. */
export function aboutCheckMinutes(minutes: number | null | undefined): string | null {
  if (minutes == null || !Number.isFinite(minutes)) return null;
  return `about ${Math.max(1, Math.round(minutes))} min`;
}
