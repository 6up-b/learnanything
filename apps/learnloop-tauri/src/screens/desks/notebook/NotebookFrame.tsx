// A marimo notebook in a window (spec §11.2, §11.5; docs/reviews/notebook-runtime-b1-b3.md): the sidecar's
// sandboxed server, shown in a frame served by its per-session proxy on 127.0.0.1.
//
// - The session belongs to its owner (a pad or a lesson), never to the window: opening the same owner again
//   returns the same session, so a desk switch, a move or a remount keeps the kernel. Unmounting never closes it;
//   the sidecar stops it after its idle minutes with no frame attached.
// - Honest states: starting, ready, stopped (idle, with resume), crashed and restarting, failed, and the runtime
//   unavailable with the sidecar's reason. The frame is mounted only once the server answers.
// - The window lifecycle (spec §3.6): a paused window (offscreen, another desk) polls nothing and its frame takes
//   no input or focus, while the server keeps running; a preview (an overview card) shows a placeholder, never a
//   second live frame (§11.4).
// - The frame has no Tauri IPC: it is another origin, sandboxed, with the proxy's CSP. The bridge's four messages
//   are checked by `event.source` and `event.origin` (./bridge.ts) and handed on as untrusted notebook text.
import { createContext, useCallback, useContext, useEffect, useRef, useState, type CSSProperties } from "react";
import { api } from "../../../api/client";
import type { NotebookOpenInput, NotebookOwner, NotebookSessionDto } from "../../../api/dto";
import { useListenerHub, useWhenLive, useWindowLifecycle, isPaused } from "../lifecycle";
import { frameOrigin, fromFrame, parseBridgeMessage, toPage, type BridgeMessage } from "./bridge";
import "./notebook.css";

/** What the workbench does with a frame's bridge messages (the desks provide it; elsewhere nothing happens). */
export interface NotebookBridgeHost {
  /** A checked message, its geometry in page coordinates, with the frame element it came from. */
  onMessage(message: BridgeMessage, frame: HTMLIFrameElement, owner: NotebookOwner): void;
}

export const NotebookBridgeContext = createContext<NotebookBridgeHost | null>(null);

/** The calls the frame makes (the sidecar's RPCs; tests give their own). */
export interface NotebookApi {
  notebookOpen(input: NotebookOpenInput): Promise<NotebookSessionDto>;
  notebookStatus(input: { sessionId: string }): Promise<NotebookSessionDto>;
}

/** How often the frame asks the session's state: quickly while it starts or restarts, slowly while it runs (a
 * crash or an idle stop shows within this). keep: display polling, not a parameter. */
export const POLL_MS = { changing: 500, ready: 5000 } as const;

/** A failed open or reading is retried this many times, this far apart, before the failure is said (spec §11.2:
 * "It retries three times, 1.5 s apart"). keep: the spec's values. */
export const RETRY = { times: 3, everyMs: 1500 } as const;

export interface NotebookError {
  code: string;
  message: string;
  retryable: boolean;
}

export type FrameView =
  | { kind: "opening" }
  | { kind: "starting"; restarts: number }
  | { kind: "ready"; frameUrl: string }
  | { kind: "restarting"; restarts: number }
  | { kind: "retrying"; retry: number }
  | { kind: "stopped"; reason: string | null }
  | { kind: "failed"; message: string }
  | { kind: "unavailable"; message: string };

/** The view a session (or the error that stood in for one) shows. */
export function frameView(session: NotebookSessionDto | null, error: NotebookError | null, retry = 0): FrameView {
  if (retry > 0) return { kind: "retrying", retry };
  if (error) {
    return error.code === "notebook_runtime_unavailable" ? { kind: "unavailable", message: error.message } : { kind: "failed", message: error.message };
  }
  if (!session) return { kind: "opening" };
  switch (session.state) {
    case "ready":
      return { kind: "ready", frameUrl: session.frameUrl };
    case "starting":
      return { kind: "starting", restarts: session.restarts };
    case "restarting":
      return { kind: "restarting", restarts: session.restarts };
    case "stopping":
    case "stopped":
      return { kind: "stopped", reason: session.stopReason };
    case "failed":
      return { kind: "failed", message: "The notebook couldn’t keep running. Select Try again." };
  }
}

const STOPPED_WORDS: Record<string, string> = {
  idle: "paused while no window showed it",
  make_room: "paused to make room for another notebook",
  closed: "closed",
  replaced: "replaced by a newer version",
  vault_switch: "closed when you switched libraries",
};

/** The one line a view says (interface text, JetBrains Mono). */
export function statusLine(view: FrameView): string {
  switch (view.kind) {
    case "opening":
      return "opening the notebook…";
    case "starting":
      return "Starting the notebook on this device…";
    case "ready":
      return "";
    case "restarting":
      return "Restarting the notebook…";
    case "retrying":
      return "Waiting for the notebook. Trying again…";
    case "stopped":
      return `Notebook ${view.reason ? STOPPED_WORDS[view.reason] ?? "paused" : "paused"}. Select Resume.`;
    case "failed":
      return view.message;
    case "unavailable":
      return view.message;
  }
}

function errorOf(error: unknown): NotebookError {
  if (error && typeof error === "object") {
    const record = error as { code?: unknown; message?: unknown; retryable?: unknown };
    return { code: typeof record.code === "string" ? record.code : "error", message: typeof record.message === "string" ? record.message : String(error), retryable: record.retryable === true };
  }
  return { code: "error", message: String(error), retryable: false };
}

export interface NotebookFrameProps {
  owner: NotebookOwner;
  /** The notebook file, relative to the vault root; left out for a pad, whose notebook is its cells. */
  path?: string;
  view?: "app" | "edit";
  /** The notebook's name, for the frame's title and the overview's placeholder. */
  title?: string;
  /** Overrides the sidecar's calls (tests, the harness). */
  calls?: NotebookApi;
  style?: CSSProperties;
  /** Every session reading the frame takes (a pad's cells read their run states from it). */
  onSession?: (session: NotebookSessionDto) => void;
  /** How soon to read a ready session again, from the reading just taken, when its owner waits on something in
   * it (a lesson's commit point); undefined keeps POLL_MS.ready. */
  readyPoll?: (session: NotebookSessionDto) => number | undefined;
}

export function NotebookFrame({ owner, path, view = "app", title = "notebook", calls = api, style, onSession, readyPoll }: NotebookFrameProps) {
  const lifecycle = useWindowLifecycle();
  const paused = isPaused(lifecycle.state);
  const whenLive = useWhenLive();
  const hub = useListenerHub();
  const host = useContext(NotebookBridgeContext);
  const [session, setSession] = useState<NotebookSessionDto | null>(null);
  const [error, setError] = useState<NotebookError | null>(null);
  const [attempt, setAttempt] = useState(0);
  // Automatic retries of a failed open or reading (0: none pending); a success ends them.
  const [retrying, setRetrying] = useState(0);
  const retries = useRef(0);
  const frameRef = useRef<HTMLIFrameElement | null>(null);
  const preview = lifecycle.state === "preview";
  const onSessionRef = useRef(onSession);
  onSessionRef.current = onSession;
  const readyPollRef = useRef(readyPoll);
  readyPollRef.current = readyPoll;
  useEffect(() => {
    if (session) onSessionRef.current?.(session);
  }, [session]);

  // Open (or rejoin) the owner's session, then follow its state. A preview opens nothing.
  useEffect(() => {
    if (preview) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const failed = (reason: unknown) => {
      if (cancelled) return;
      const problem = errorOf(reason);
      if (problem.code !== "notebook_runtime_unavailable" && retries.current < RETRY.times) {
        retries.current += 1;
        setRetrying(retries.current);
        timer = setTimeout(() => setAttempt((value) => value + 1), RETRY.everyMs);
        return;
      }
      retries.current = 0;
      setRetrying(0);
      setError(problem);
    };
    const answered = () => {
      retries.current = 0;
      setRetrying(0);
      setError(null);
    };
    const follow = async (sessionId: string) => {
      await whenLive();
      if (cancelled) return;
      try {
        const next = await calls.notebookStatus({ sessionId });
        if (cancelled) return;
        setSession(next);
        answered();
        if (next.state === "stopped" || next.state === "failed") return;
        timer = setTimeout(() => void follow(sessionId), next.state === "ready" ? readyPollRef.current?.(next) ?? POLL_MS.ready : POLL_MS.changing);
      } catch (reason) {
        failed(reason);
      }
    };
    void (async () => {
      await whenLive();
      if (cancelled) return;
      try {
        const opened = await calls.notebookOpen(path === undefined ? { owner, view } : { owner, path, view });
        if (cancelled) return;
        setSession(opened);
        answered();
        timer = setTimeout(() => void follow(opened.sessionId), opened.state === "ready" ? readyPollRef.current?.(opened) ?? POLL_MS.ready : POLL_MS.changing);
      } catch (reason) {
        failed(reason);
      }
    })();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [owner, path, view, attempt, preview, calls, whenLive]);

  const current = frameView(session, error, retrying);
  // A frame already showing stays while its session restarts or a reading is retried (it reconnects by itself).
  const frameUrl = current.kind === "ready" ? current.frameUrl
    : session?.state === "restarting" || (current.kind === "retrying" && session?.state === "ready") ? session.frameUrl : null;
  const origin = frameUrl ? frameOrigin(frameUrl) : null;

  // The bridge: only this frame's own messages, of exactly the four shapes.
  useEffect(() => {
    if (!origin || preview) return;
    return hub.listen<MessageEvent>("window", "message", (event) => {
      const frame = frameRef.current;
      if (!frame || !fromFrame(event, { window: frame.contentWindow, origin })) return;
      const message = parseBridgeMessage(event.data);
      if (!message || paused) return;
      const box = frame.getBoundingClientRect();
      const placed = toPage(message, { left: box.left, top: box.top, width: box.width, height: box.height });
      if (placed.ll === "click") {
        // The workbench's menus close on a press outside them; a press inside the frame never reaches the page.
        frame.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
        frame.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true }));
      }
      host?.onMessage(placed, frame, owner);
    });
  }, [origin, preview, paused, hub, host, owner]);

  // A paused window's frame takes no focus or input (React 18 has no `inert` prop, so the attribute is set here).
  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;
    if (paused) frame.setAttribute("inert", "");
    else frame.removeAttribute("inert");
  }, [paused, frameUrl]);

  const retry = useCallback(() => {
    retries.current = 0;
    setRetrying(0);
    setSession(null);
    setError(null);
    setAttempt((value) => value + 1);
  }, []);

  if (preview) {
    return (
      <div className="ll-nb ll-nb-placeholder" data-notebook-placeholder="" style={style}>
        <span className="glyph">◆</span> notebook · {title}
      </div>
    );
  }
  const line = statusLine(current);
  const action =
    current.kind === "stopped" ? "resume" : current.kind === "failed" || current.kind === "unavailable" ? "try again" : null;
  return (
    <div className="ll-nb" data-notebook-state={current.kind} style={style}>
      {line ? (
        <div className="ll-nb-status" role="status">
          <span>{line}</span>
          {action ? (
            <button type="button" onClick={retry}>
              {action}
            </button>
          ) : null}
        </div>
      ) : null}
      {frameUrl ? (
        <iframe
          ref={frameRef}
          className="ll-nb-frame"
          title={`notebook · ${title}`}
          src={frameUrl}
          sandbox="allow-scripts allow-same-origin allow-forms allow-downloads"
          referrerPolicy="no-referrer"
          allow=""
          tabIndex={paused ? -1 : 0}
          aria-hidden={paused ? true : undefined}
          data-paused={paused ? "" : undefined}
        />
      ) : null}
    </div>
  );
}
