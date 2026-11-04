// Mobile M2a (spec_mobile_tailnet_v1 §6.5): starting a session while a phone holds one.
//
// Every desktop start goes through `startSessionOrAsk`. `start_session` refuses with
// `session_open_elsewhere`, never ending the phone's session silently. The learner then
// chooses, in `SessionElsewherePrompt`: continue it here (adopt, which keeps its id, its caps
// and its draft), start fresh (the replaced draft is kept in `session_handoffs`), or cancel.
import { useSyncExternalStore } from "react";
import { api } from "../api/client";
import type { SessionElsewhereDetails, SessionSnapshot, SessionStartInput } from "../api/dto";
import { getCommandError } from "../errors";
import type { SessionMoved } from "./sessionMoved";

export type ElsewhereChoice = "adopt" | "fresh" | "cancel";

export interface ElsewhereQuestion {
  readonly details: SessionElsewhereDetails;
  readonly answer: (choice: ElsewhereChoice) => void;
}

let question: ElsewhereQuestion | null = null;
const listeners = new Set<() => void>();

function setQuestion(next: ElsewhereQuestion | null): void {
  question = next;
  for (const listener of listeners) listener();
}

export function useElsewhereQuestion(): ElsewhereQuestion | null {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    () => question
  );
}

function ask(details: SessionElsewhereDetails): Promise<ElsewhereChoice> {
  return new Promise((resolve) => {
    // A second start while one is asking joins the same answer's outcome by being asked again.
    question?.answer("cancel");
    setQuestion({
      details,
      answer: (choice) => {
        setQuestion(null);
        resolve(choice);
      }
    });
  });
}

/** What the session reads as after an adopt: the operation's reply is an owner snapshot, not a session. */
async function adopted(sessionId: string, expectedGeneration: number): Promise<SessionSnapshot> {
  await api.adoptSession({ sessionId, expectedGeneration });
  return api.getSession(sessionId);
}

export function adoptMovedSession(moved: SessionMoved): Promise<SessionSnapshot> {
  return adopted(moved.sessionId, moved.ownerGeneration ?? 0);
}

/**
 * `start_session`, asking when another device holds the open session. Null is Cancel: no
 * session was started and nothing changed. A stale choice comes back as the question again
 * with the session's current state, so the learner never acts on what they did not see.
 */
export async function startSessionOrAsk(input: SessionStartInput): Promise<SessionSnapshot | null> {
  let replace = input.replace ?? null;
  for (;;) {
    try {
      return await api.startSession(replace ? { ...input, replace } : input);
    } catch (error) {
      const command = getCommandError(error);
      if (command?.code !== "session_open_elsewhere") throw error;
      const details = command.details as unknown as SessionElsewhereDetails;
      const choice = await ask(details);
      if (choice === "cancel") return null;
      if (choice === "adopt") return adopted(details.session_id, details.owner_generation ?? 0);
      replace = details.session_id;
    }
  }
}
