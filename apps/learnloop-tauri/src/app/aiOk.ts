// The learner's one OK before LearnLoop uses AI (the sidecar's `learnloop.ai.model_use`).
//
// A store with no import of the API client, because the client reports here: a request the sidecar refused with
// `waiting_for_ok` (nothing was sent) asks for the sheet and waits for the learner's answer. OK sends that same
// request again, once; "Not now" leaves it refused, and what waits in the background waits on. Several requests
// refused together share one sheet and one answer. An Add whose questions wait for the OK asks too, with nothing
// to send again (its book's questions resume on the sidecar).
import { useSyncExternalStore } from "react";

type Answer = (accepted: boolean) => void;

let asking = false;
const waiting: Answer[] = [];
const listeners = new Set<() => void>();

function notify(): void {
  for (const listener of listeners) listener();
}

function setAsking(next: boolean): void {
  if (asking === next) return;
  asking = next;
  notify();
}

/** A refused request waits here: true once the learner said OK (send it again), false when they closed the sheet. */
export function waitForAiOk(): Promise<boolean> {
  return new Promise((resolve) => {
    waiting.push(resolve);
    setAsking(true);
  });
}

/** Show the sheet with nothing to send again (an Add whose questions wait for the OK). */
export function askForAiOk(): void {
  setAsking(true);
}

/** The sheet's answer: every waiting request learns it at once, and the sheet goes. */
export function answerAiOk(accepted: boolean): void {
  const answers = waiting.splice(0, waiting.length);
  setAsking(false);
  for (const answer of answers) answer(accepted);
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** Whether something is waiting for the learner's OK now. */
export function useAiOkAsked(): boolean {
  return useSyncExternalStore(subscribe, () => asking);
}

/** A sidecar refusal that means "waiting for your OK": nothing was sent. */
export function isWaitingForOk(error: unknown): boolean {
  return (error as { code?: unknown } | null)?.code === "waiting_for_ok";
}
