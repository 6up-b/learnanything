// An honest wait (docs/reviews/first-evening-step-6.md): while a book is got ready and while
// a section's questions are written, a few short lines say what is happening, in facts the sidecar recorded when they
// happened (wait_detail.py): the step, its parts, when the request was sent, when its reply last moved, whether this is
// a second try, and a time this library measured, with how many it rests on. The details stay collapsed.
//
// Never said: a percentage, a time left, an estimate this library has not measured, a count of topics before a whole
// plan was read, or that something "stalled" (no threshold is invented). "Still writing" is said only when the reply
// grew since the previous read; otherwise the time its last part came. A connection that does not stream says nothing
// about a reply until it is received.
//
// Pure apart from one hook (the previous read, to tell the reply grew); the phone imports it (`@desktop/app/waitDetail`).

import { useRef } from "react";
import type { BuildDetailDto, WaitDeliveryDto, WaitMeasuredDto, WritingDetailDto } from "../api/dto";
import type { TodayCause } from "./todayCause";

/** The detail a wait carries: a book being got ready, or a section's questions being written; null for any other cause
 *  or where the sidecar sent none. */
export type WaitDetail = { kind: "build"; value: BuildDetailDto; firstTimeSaid?: boolean } | { kind: "writing"; value: WritingDetailDto };

/** `where`: the desktop shows a first build's "The first time, this can take several minutes." under the waiting
 *  indicator; the phone says it only in the block for a book read to its end. Where it is said, the details do not
 *  repeat it as "no time is given", and with nothing else to add the details control is not shown at all. */
export function waitDetailOf(cause: TodayCause | null, where: "desktop" | "phone" = "desktop"): WaitDetail | null {
  if (cause?.kind === "on_the_way" && cause.detail) {
    const firstTimeSaid = cause.firstBuild === true && (where === "desktop" || cause.allRead === true);
    return { kind: "build", value: cause.detail, ...(firstTimeSaid ? { firstTimeSaid } : {}) };
  }
  if (cause?.kind === "section_writing" && cause.detail) return { kind: "writing", value: cause.detail };
  return null;
}

/** The words a wait shows: its lines, and what its collapsed details hold. */
export interface WaitDetailWords {
  lines: string[];
  details: string[];
}

/** How times are said: counted back from the read on the desktop, which reads again every few seconds; as clock times
 *  on the phone, whose Today is not read again on its own (an age would grow false as it sat). */
export type WaitClock = "ago" | "at";

/** The label of the collapsed details. */
export const WAIT_DETAILS_LABEL = "details";

/** Said for a library's first topics, which have no measured time yet. */
export const FIRST_QUESTIONS_TIME = "The first questions can take a few minutes.";

function parse(value: string | null | undefined): number | null {
  if (!value) return null;
  const at = Date.parse(value);
  return Number.isNaN(at) ? null : at;
}

/** A whole number of seconds or minutes, counted down to (never rounded up). */
function span(seconds: number): string {
  if (seconds < 60) {
    const whole = Math.max(0, Math.floor(seconds));
    return `${whole} ${whole === 1 ? "second" : "seconds"}`;
  }
  const minutes = Math.floor(seconds / 60);
  return `${minutes} ${minutes === 1 ? "minute" : "minutes"}`;
}

function clockTime(at: number): string {
  return new Date(at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/** "2 minutes ago" or "at 18:04", for a time the sidecar recorded, as of its read. Null when either time is missing. */
function when(value: string | null | undefined, asOf: string | null, clock: WaitClock): string | null {
  const at = parse(value);
  if (at === null) return null;
  if (clock === "at") return `at ${clockTime(at)}`;
  const now = parse(asOf);
  return now === null ? null : `${span(Math.max(0, (now - at) / 1000))} ago`;
}

/** Whether the in-flight request's reply grew since the previous read: its last part came at another time, or more
 *  parts came. False on the first read, which has nothing to compare with. */
export function replyGrew(delivery: WaitDeliveryDto | null | undefined, previous: WaitDeliveryDto | null | undefined): boolean {
  if (!delivery || !previous || delivery.outputPieces <= 0 || !delivery.lastOutputAt) return false;
  return delivery.lastOutputAt !== previous.lastOutputAt || delivery.outputPieces > previous.outputPieces;
}

/** What the request waited on is doing: "still writing" only when its reply grew; else when its last part came; with
 *  no part yet, when it was sent; with none in flight, when the last reply came. Null with nothing recorded. */
function deliveryPhrase(delivery: WaitDeliveryDto | null, asOf: string | null, clock: WaitClock, grew: boolean): string | null {
  if (!delivery) return null;
  if (delivery.requestSentAt) {
    if (delivery.outputPieces > 0 && delivery.lastOutputAt) {
      if (grew) return "still writing";
      const last = when(delivery.lastOutputAt, asOf, clock);
      return last ? `reply arriving, last part ${last}` : "reply arriving";
    }
    const sent = when(delivery.requestSentAt, asOf, clock);
    return sent ? `asked ${sent}, no reply yet` : "asked, no reply yet";
  }
  const received = when(delivery.replyReceivedAt, asOf, clock);
  return received ? `reply received ${received}` : null;
}

function timeLine(started: string | null, asOf: string | null, delivery: WaitDeliveryDto | null, clock: WaitClock, grew: boolean): string | null {
  const since = when(started, asOf, clock);
  const parts = [since ? `Started ${since}` : null, deliveryPhrase(delivery, asOf, clock, grew)].filter(Boolean) as string[];
  if (parts.length === 0) return null;
  const line = parts.join(" · ");
  return line.charAt(0).toUpperCase() + line.slice(1);
}

function countWords(count: number, one: string, many: string): string {
  return `${count} ${count === 1 ? one : many}`;
}

function minutesWords(minutes: number): string {
  if (minutes < 1) return "under a minute";
  const whole = Math.round(minutes);
  return `about ${whole} ${whole === 1 ? "minute" : "minutes"}`;
}

function buildMeasured(measured: WaitMeasuredDto | null): string {
  return measured
    ? `Earlier builds in this library took ${minutesWords(measured.minutes)} for a book this size (from ${countWords(measured.samples, "build", "builds")}).`
    : "No book has finished getting ready in this library yet, so no time is given.";
}

/** The stage of a build, in a few words. */
function buildStage(detail: BuildDetailDto): string {
  switch (detail.stage) {
    case "queued":
      return "Waiting to start";
    case "reading": {
      const inventory = detail.inventory;
      return inventory && inventory.total !== null && inventory.total > 0
        ? `Reading the text · ${inventory.done} of ${countWords(inventory.total, "part", "parts")} read`
        : "Reading the text";
    }
    case "planning": {
      const part = detail.synthesis;
      const which = part && part.part !== null && part.parts !== null && part.parts > 0 ? ` · part ${part.part} of ${part.parts}` : "";
      const pass = part?.pass === "evidence" ? " · looking at the passages it asked for" : part?.pass === "plan_reused" ? " · kept from before" : "";
      return `Planning questions${which}${pass}`;
    }
    case "organizing":
      return "Organizing the topics";
    case "checking":
      return typeof detail.draftedTopics === "number"
        ? `${countWords(detail.draftedTopics, "topic", "topics")} drafted · checking ${detail.draftedTopics === 1 ? "it" : "them"}`
        : "Checking the plan";
    case "saving":
      return "Saving the plan";
  }
}

/** A book being got ready: its stage, then how long and what its request is doing; details hold what was reused, what
 *  a further pass is, and this library's measured time with its sample count (or that none was measured). */
export function buildWaitWords(detail: BuildDetailDto, options: { clock: WaitClock; grew: boolean; firstTimeSaid?: boolean }): WaitDetailWords {
  const stage = buildStage(detail);
  const lines = [detail.retry ? `Trying again · ${stage}` : stage];
  const time = timeLine(detail.startedAt, detail.asOf, detail.delivery, options.clock, options.grew);
  if (time) lines.push(time);
  const details: string[] = [];
  if (detail.retry) details.push("An earlier try stopped; this one picks up from what was kept.");
  const reused = detail.inventory?.reused ?? 0;
  if (detail.stage === "reading" && reused > 0) {
    details.push(`${countWords(reused, "part was", "parts were")} read before and ${reused === 1 ? "is" : "are"} not read again.`);
  }
  if (detail.stage === "planning" && detail.synthesis?.pass === "evidence") {
    details.push("A part can take a second look, with the passages it asked to see.");
  }
  if (detail.stage === "checking" && typeof detail.draftedTopics === "number") {
    details.push("The topics you get can differ once the checks are done.");
  }
  // Before any build was measured, the line on screen already says the first time takes several minutes: "no time is
  // given" under details would add nothing (the live walk opened it twice and found nothing new).
  if (detail.measured || !options.firstTimeSaid) details.push(buildMeasured(detail.measured));
  return { lines, details };
}

/** A section's questions being written: the topic being written, which of how many; how long and what its request is
 *  doing; and how long a topic has taken here (with how many), or, before any was timed, that the first can take a
 *  few minutes. */
export function writingWaitWords(detail: WritingDetailDto, options: { clock: WaitClock; grew: boolean }): WaitDetailWords {
  const lines: string[] = [];
  const details: string[] = [];
  if (detail.queued) {
    lines.push("Waiting to start");
  } else {
    const topic = detail.topic;
    const which = topic && topic.index !== null && topic.total !== null
      ? `Writing topic ${topic.index} of ${topic.total}${topic.title ? `: “${topic.title}”` : ""}`
      : topic?.title ? `Writing questions on “${topic.title}”` : null;
    if (detail.retry) lines.push(which ? `Trying again · ${which}` : "Trying again");
    else if (which) lines.push(which);
    const time = timeLine(detail.topicStartedAt ?? detail.startedAt, detail.asOf, detail.delivery, options.clock, options.grew);
    if (time) lines.push(time);
    if (detail.retry) details.push("An earlier try stopped; topics already written are kept and not written again.");
  }
  if (detail.measured) {
    lines.push(`Here a topic's questions have taken ${minutesWords(detail.measured.minutes)} to write.`);
    details.push(`Measured on the last ${countWords(detail.measured.samples, "topic", "topics")} written in this library.`);
  } else {
    lines.push(FIRST_QUESTIONS_TIME);
  }
  return { lines, details };
}

/** The wait's words for a detail, telling "still writing" from the previous read of the same wait (held across reads
 *  in a ref: no timer of its own; the screen's existing reads bring each new one). */
export function useWaitWords(detail: WaitDetail | null, clock: WaitClock): WaitDetailWords | null {
  const previous = useRef<{ kind: string; delivery: WaitDeliveryDto | null } | null>(null);
  const shown = useRef<{ key: WaitDeliveryDto | null; grew: boolean } | null>(null);
  if (!detail) {
    previous.current = null;
    shown.current = null;
    return null;
  }
  const delivery = detail.value.delivery;
  // One read is compared once: a re-render with the same read keeps what it said.
  if (!shown.current || shown.current.key !== delivery) {
    const before = previous.current && previous.current.kind === detail.kind ? previous.current.delivery : null;
    shown.current = { key: delivery, grew: replyGrew(delivery, before) };
    previous.current = { kind: detail.kind, delivery };
  }
  const grew = shown.current.grew;
  return detail.kind === "build"
    ? buildWaitWords(detail.value, { clock, grew, firstTimeSaid: detail.firstTimeSaid === true })
    : writingWaitWords(detail.value, { clock, grew });
}
