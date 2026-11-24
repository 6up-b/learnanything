// The notebook frame's honest states, its lifecycle (a paused window polls nothing and its frame takes no input;
// a preview shows a placeholder), and its bridge refusing what is not the frame's own.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { NotebookSessionDto } from "../../../api/dto";
import { DIRECT_HUB, WindowScope, type WindowState } from "../lifecycle";
import { NotebookBridgeContext, NotebookFrame, POLL_MS, frameView, statusLine, type NotebookApi } from "./NotebookFrame";

vi.mock("../../../api/client", () => ({ api: {} }));

const URL_ = "http://127.0.0.1:40123/s/secret/?view-as=present&show-chrome=false";

function session(state: NotebookSessionDto["state"], extra: Partial<NotebookSessionDto> = {}): NotebookSessionDto {
  return { version: 1, sessionId: "nbs_1", owner: "lesson:l1", state, stopReason: null, error: null, restarts: 0, framesAttached: 0,
    cells: [], startSeconds: [], frameUrl: URL_, memoryBytes: null, ...extra };
}

function calls(open: () => Promise<NotebookSessionDto>, status?: () => Promise<NotebookSessionDto>): NotebookApi & { opens: number; statuses: number } {
  const made = { opens: 0, statuses: 0,
    notebookOpen: vi.fn(async () => { made.opens += 1; return open(); }),
    notebookStatus: vi.fn(async () => { made.statuses += 1; return (status ?? open)(); }) };
  return made;
}

function Frame({ api, state = "active", onMessage }: { api: NotebookApi; state?: WindowState; onMessage?: (m: unknown) => void }) {
  return (
    <NotebookBridgeContext.Provider value={onMessage ? { onMessage } : null}>
      <WindowScope lifecycle={{ windowId: "w1", state }} hub={DIRECT_HUB}>
        <NotebookFrame owner="lesson:l1" path="notebooks/a.py" title="A slope" calls={api} />
      </WindowScope>
    </NotebookBridgeContext.Provider>
  );
}

beforeEach(() => vi.useFakeTimers());
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

async function settle() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

it("starts, then mounts the frame at the session's URL once ready, sandboxed and without IPC", async () => {
  let state: NotebookSessionDto["state"] = "starting";
  const api = calls(async () => session(state));
  render(<Frame api={api} />);
  await settle();
  expect(screen.getByRole("status").textContent).toContain("starting the notebook");
  expect(document.querySelector("iframe")).toBeNull();
  state = "ready";
  await act(async () => vi.advanceTimersByTime(POLL_MS.changing));
  await settle();
  const frame = document.querySelector("iframe")!;
  expect(frame.getAttribute("src")).toBe(URL_);
  expect(frame.getAttribute("sandbox")).toBe("allow-scripts allow-same-origin allow-forms allow-downloads");
  expect(frame.getAttribute("referrerpolicy")).toBe("no-referrer");
  expect(screen.queryByRole("status")).toBeNull();
  expect(api.notebookOpen).toHaveBeenCalledWith({ owner: "lesson:l1", path: "notebooks/a.py", view: "app" });
});

it("keeps the frame while a crashed server restarts, and says so", async () => {
  const api = calls(async () => session("restarting", { restarts: 2 }));
  render(<Frame api={api} />);
  await settle();
  expect(screen.getByRole("status").textContent).toBe("the notebook stopped; starting it again (2 of 3)…");
  expect(document.querySelector("iframe")?.getAttribute("src")).toBe(URL_);
});

it("an idle stop offers resume, which opens the owner's session again", async () => {
  let state: NotebookSessionDto["state"] = "stopped";
  const api = calls(async () => session(state, { stopReason: state === "stopped" ? "idle" : null }));
  render(<Frame api={api} />);
  await settle();
  expect(screen.getByRole("status").textContent).toContain("paused while no window showed it");
  expect(document.querySelector("iframe")).toBeNull();
  state = "ready";
  fireEvent.click(screen.getByRole("button", { name: "resume" }));
  await settle();
  expect(api.opens).toBe(2);
  expect(document.querySelector("iframe")).not.toBeNull();
});

it("says why the runtime is unavailable, in the sidecar's words", async () => {
  const api = calls(async () => {
    throw { code: "notebook_runtime_unavailable", message: "Notebooks can't run here: bubblewrap (bwrap) is not installed.", retryable: false };
  });
  render(<Frame api={api} />);
  await settle();
  expect(screen.getByRole("status").textContent).toContain("bubblewrap (bwrap) is not installed");
  expect(screen.getByRole("button", { name: "try again" })).toBeTruthy();
});

it("a failed session says what failed, with try again", async () => {
  const api = calls(async () => session("failed", { error: "the notebook server stopped 4 times" }));
  render(<Frame api={api} />);
  await settle();
  expect(screen.getByRole("status").querySelector("span")?.textContent).toBe("the notebook couldn't run: the notebook server stopped 4 times");
  expect(screen.getByRole("button", { name: "try again" })).toBeTruthy();
});

it("a paused window opens and polls nothing until it is live again", async () => {
  const api = calls(async () => session("ready"));
  const { rerender } = render(<Frame api={api} state="offscreen" />);
  await settle();
  expect(api.opens).toBe(0);
  rerender(<Frame api={api} state="visible" />);
  await settle();
  expect(api.opens).toBe(1);
});

it("a frame whose window is paused keeps its frame but takes no input or focus", async () => {
  const api = calls(async () => session("ready"));
  const { rerender } = render(<Frame api={api} />);
  await settle();
  rerender(<Frame api={api} state="hidden" />);
  await settle();
  const frame = document.querySelector("iframe")!;
  expect(frame.hasAttribute("inert")).toBe(true);
  expect(frame.tabIndex).toBe(-1);
  expect(api.opens).toBe(1);
});

it("a preview shows a placeholder and opens nothing (one live frame per session)", async () => {
  const api = calls(async () => session("ready"));
  render(<Frame api={api} state="preview" />);
  await settle();
  expect(document.querySelector("iframe")).toBeNull();
  expect(screen.getByText(/notebook · A slope/)).toBeTruthy();
  expect(api.opens).toBe(0);
});

it("hands on only the frame's own, well-formed messages", async () => {
  const api = calls(async () => session("ready"));
  const received: unknown[] = [];
  render(<Frame api={api} onMessage={(message) => received.push(message)} />);
  await settle();
  const frame = document.querySelector("iframe")!;
  const own = frame.contentWindow;
  const post = (data: unknown, source: unknown, origin: string) =>
    act(() => {
      window.dispatchEvent(new MessageEvent("message", { data, source: source as Window, origin }));
    });
  await post({ ll: "escape" }, own, "http://127.0.0.1:40123");
  await post({ ll: "escape" }, own, "http://127.0.0.1:40124");
  await post({ ll: "escape" }, window, "http://127.0.0.1:40123");
  await post({ ll: "run", code: "x" }, own, "http://127.0.0.1:40123");
  await post({ ll: "companion", text: "<b>hi</b>", rect: null, shift: false }, own, "http://127.0.0.1:40123");
  expect(received).toEqual([{ ll: "escape" }, { ll: "companion", text: "<b>hi</b>", rect: null, shift: false }]);
});

it("names every state in one line", () => {
  expect(statusLine(frameView(null, null))).toBe("opening the notebook…");
  expect(statusLine(frameView(session("stopped", { stopReason: "vault_switch" }), null))).toBe("notebook closed when the vault changed");
  expect(statusLine(frameView(session("ready"), null))).toBe("");
});
