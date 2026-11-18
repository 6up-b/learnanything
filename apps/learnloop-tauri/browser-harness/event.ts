// Stands in for @tauri-apps/api/event. The bridge pushes the events the Rust
// shell emits (the vault watcher's learnloop://vault-files-changed) as
// server-sent events on one stream.
import { BRIDGE } from "./bridge";

export type UnlistenFn = () => void;
export type EventName = string;
export interface Event<T> {
  event: EventName;
  id: number;
  payload: T;
}
export type EventCallback<T> = (event: Event<T>) => void;

type Handler = { event: string; callback: EventCallback<unknown> };

const handlers = new Map<number, Handler>();
let nextId = 1;
let stream: EventSource | null = null;

function ensureStream() {
  if (stream) return;
  stream = new EventSource(`${BRIDGE}/events`);
  stream.onmessage = (message) => {
    let parsed: { event: string; payload: unknown };
    try {
      parsed = JSON.parse(message.data);
    } catch {
      return;
    }
    for (const [id, handler] of handlers) {
      if (handler.event === parsed.event) handler.callback({ event: parsed.event, id, payload: parsed.payload });
    }
  };
}

export async function listen<T>(event: EventName, handler: EventCallback<T>): Promise<UnlistenFn> {
  ensureStream();
  const id = nextId++;
  handlers.set(id, { event, callback: handler as EventCallback<unknown> });
  return () => {
    handlers.delete(id);
  };
}

export async function once<T>(event: EventName, handler: EventCallback<T>): Promise<UnlistenFn> {
  const unlisten = await listen<T>(event, (received) => {
    unlisten();
    handler(received);
  });
  return unlisten;
}

export async function emit(): Promise<void> {
  // Nothing in the frontend emits to the shell today.
}
