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
export function observationLine(kind: ReaderObservationKind | string, quoted?: string | null): string {
  switch (kind) {
    case "still_unclear":
      return quoted ? `your question “${quoted}” — still unclear when you came back to it` : "a question still unclear when you came back to it";
    case "next_step_missed":
      return "your next-step guess differed from the book's";
    case "why_step_missed":
      return "your answer to why a step holds differed from the book's";
    case "assumption_missed":
      return "your answer about the assumptions differed from the book's";
    case "prediction_missed":
      return "a figure prediction that turned out differently";
    default:
      return "worth a second look";
  }
}

export function stepsLabel(count: number): string {
  return `${count} step${count === 1 ? "" : "s"}`;
}
