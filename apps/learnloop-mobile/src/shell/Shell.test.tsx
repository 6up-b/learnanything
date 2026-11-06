// The shell of mobile v2 stage V1 around today's practice: places, stacks, sheets, the fragment,
// the connection line, the stale-app reload and the reconnect order. The practice journeys
// themselves are App.test.tsx's, unchanged.
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { clear as clearQueries } from "@desktop/api/queryCache";
import { App } from "../App";
import { ALLOWLIST_DIGEST } from "../api/phoneMethods";
import { saveCredential } from "../store/credential";
import { addToOutbox } from "../store/outbox";
import { cacheSessionId } from "../store/sessionCache";
import { BUSY_LINE, GRADING_LINE, UPDATED_LINE } from "./ConnectionLine";
import { reloader } from "./freshness";

interface Sent { readonly url: string; readonly method?: string }
type Answer = unknown | { status: number; body: unknown };

const session = { version: 1, sessionId: "s1", startedAt: "t", endedAt: null, availableMinutes: 15, checkpoint: null, ownerDeviceId: "dev", ownerLabel: "Phone", ownerGeneration: 0 };
const queue = { version: 1, sessionId: "s1", sections: [{ title: "Due", items: [{ practiceItemId: "i1", schedulerCandidateId: "c1", learningObjectTitle: "Topic i1" }] }], deviceDeferredCount: 0 };
const item = { id: "i1", learningObjectTitle: "Topic i1", attemptTypesAllowed: ["independent_attempt"], assessmentContractVersionId: "acv", presentation: { practiceItemId: "i1", blocks: [{ kind: "prompt", markdown: "Define it.", label: null }] } };

let sent: Sent[];
let answers: Record<string, Answer>;
let gets: Record<string, Answer>;
let reachable: boolean;

function respond(answer: Answer, wrap: boolean): Response {
  if (answer && typeof answer === "object" && "status" in answer && "body" in answer) {
    const shaped = answer as { status: number; body: unknown };
    return new Response(JSON.stringify(shaped.body), { status: shaped.status });
  }
  return new Response(JSON.stringify(wrap ? { ok: true, result: answer } : answer), { status: 200 });
}

async function fakeFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url = String(input);
  if (!reachable) {
    sent.push({ url: `offline ${url}` });
    throw new TypeError("asleep");
  }
  if (url === "/rpc") {
    const method = JSON.parse(init?.body as string).method as string;
    sent.push({ url, method });
    if (!(method in answers)) return new Response(JSON.stringify({ ok: false, error: { code: "not_found", message: "no fake", retryable: false } }), { status: 404 });
    return respond(answers[method], true);
  }
  sent.push({ url });
  if (url === "/api/v1/capture") return new Response("{}", { status: 201 });
  if (url in gets) return respond(gets[url], false);
  return new Response(JSON.stringify({ ok: false, error: { code: "not_found", message: "no fake", retryable: false } }), { status: 404 });
}

beforeEach(async () => {
  sent = [];
  reachable = true;
  clearQueries();
  answers = { start_session: session, get_session: session, get_today_queue: queue, get_practice_item: item, get_probe_contract: { active: false }, save_practice_draft: { ok: true } };
  gets = { "/api/v1/queue-revision": { revision: 1 }, "/api/v1/meta": { host_version: "0.1.0", api_version: 1, allowlist_digest: ALLOWLIST_DIGEST, schema_version: 250 } };
  vi.stubGlobal("fetch", vi.fn(fakeFetch));
  await saveCredential({ token: "tok", deviceId: "dev", scope: "app" });
});

const tabBar = () => screen.queryByRole("navigation", { name: "Places" });

describe("places (§4.2)", () => {
  it("four tabs in the thumb zone, Today current, and the + reads as Capture", async () => {
    render(<App />);
    await screen.findByRole("button", { name: "15 min" });
    const buttons = [...(tabBar() as HTMLElement).querySelectorAll("button")];
    expect(buttons.map((button) => button.textContent)).toEqual(["Today", "Read", "+", "Progress"]);
    expect(screen.getByRole("button", { name: "Capture" }).textContent).toBe("+");
    expect(screen.getByRole("button", { name: "Today" }).getAttribute("aria-current")).toBe("page");
  });

  it("each place is mirrored in the fragment, and a cold start opens it again", async () => {
    const { unmount } = render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Read" }));
    expect(await screen.findByText("Reading on the phone is coming in a later update.")).toBeTruthy();
    expect(window.location.hash).toBe("#/read");
    fireEvent.click(screen.getByRole("button", { name: "Progress" }));
    expect(window.location.hash).toBe("#/progress");
    unmount();
    render(<App />);
    expect(await screen.findByText(/Your goals and past answers/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Progress" }).getAttribute("aria-current")).toBe("page");
  });

  it("a question covers the tab bar, with Back to Today and Capture in the top bar, and is never reopened from the fragment", async () => {
    const { unmount } = render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
    fireEvent.click(await screen.findByRole("button", { name: /^Next: Topic i1/ }));
    await screen.findByText("Define it.");
    expect(tabBar()).toBeNull();
    expect(window.location.hash).toBe("#/today/question/i1");
    fireEvent.click(screen.getByRole("button", { name: "Capture" }));
    expect(await screen.findByLabelText("A thought, a problem or a link")).toBeTruthy();
    expect(tabBar()).not.toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Today" }));
    fireEvent.click(screen.getByRole("button", { name: "Back to Today" }));
    await screen.findByRole("button", { name: /^Next: Topic i1/ });
    expect(tabBar()).not.toBeNull();
    // A reload on a question's fragment: the serve is not repeated from the address.
    window.history.replaceState(null, "", "/app/#/today/question/i1");
    unmount();
    const serves = sent.filter((one) => one.method === "get_practice_item").length;
    render(<App />);
    await screen.findByRole("button", { name: /^Next: Topic i1/ });
    await waitFor(() => expect(sent.filter((one) => one.method === "get_session").length).toBeGreaterThan(0));
    expect(sent.filter((one) => one.method === "get_practice_item")).toHaveLength(serves);
    expect(window.location.hash).toBe("#/today");
  });

  it("a new screen's title is announced", async () => {
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
    fireEvent.click(await screen.findByRole("button", { name: /^Next: Topic i1/ }));
    await screen.findByText("Define it.");
    await waitFor(() => expect(document.querySelector("[aria-live='polite']")?.textContent).toBe("Question"));
  });
});

describe("the Display sheet (§4.6)", () => {
  it("picks light or dark over the system's choice, and Done closes it", async () => {
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Display" }));
    expect(screen.getByRole("dialog", { name: "Display" })).toBeTruthy();
    fireEvent.click(screen.getByRole("radio", { name: "Light" }));
    expect(document.documentElement.dataset.theme).toBe("light");
    fireEvent.click(screen.getByRole("radio", { name: "Match the phone" }));
    expect(document.documentElement.dataset.theme).toBeUndefined();
    fireEvent.click(screen.getByRole("button", { name: "Done" }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

describe("the connection line (§4.4)", () => {
  it("offline says what still works, and clears when the desktop answers", async () => {
    reachable = false;
    await addToOutbox({ clientCaptureId: "01A", kind: "text", text: "x", capturedAt: "t" });
    render(<App />);
    expect(await screen.findByText("Desktop offline. Capture still works. 1 capture waiting to send.")).toBeTruthy();
    reachable = true;
    await act(async () => {
      window.dispatchEvent(new Event("online"));
      await new Promise((resolve) => setTimeout(resolve, 20));
    });
    await waitFor(() => expect(screen.queryByText(/Desktop offline/)).toBeNull());
  });

  it("busy, then grading down, one quiet line each", async () => {
    answers.start_session = { status: 503, body: { ok: false, error: { code: "host_busy", message: "The desktop is busy; try again in a moment.", retryable: true } } };
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
    expect(await screen.findByText(BUSY_LINE)).toBeTruthy();
    answers.start_session = session;
    fireEvent.click(screen.getByRole("button", { name: "15 min" }));
    await screen.findByRole("button", { name: /^Next: Topic i1/ });
    expect(screen.queryByText(BUSY_LINE)).toBeNull();
    answers.submit_attempt = { status: 409, body: { ok: false, error: { code: "grading_fallback_required", message: "m", retryable: true } } };
    fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
    await screen.findByText("Define it.");
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "x";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    expect(await screen.findByText(GRADING_LINE)).toBeTruthy();
  });

  it("back from offline: the outbox first, then the session, then the token (§4.4's order)", async () => {
    cacheSessionId("s1");
    render(<App />);
    await screen.findByRole("button", { name: /^Next: Topic i1/ });
    reachable = false;
    await act(async () => {
      window.dispatchEvent(new Event("focus"));
      await new Promise((resolve) => setTimeout(resolve, 20));
    });
    await screen.findByText(/Desktop offline/);
    await addToOutbox({ clientCaptureId: "01B", kind: "text", text: "while away", capturedAt: "t" });
    reachable = true;
    sent = [];
    await act(async () => {
      window.dispatchEvent(new Event("online"));
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
    const order = sent.map((one) => one.method ?? one.url);
    const capture = order.indexOf("/api/v1/capture");
    const sessionRead = order.indexOf("get_session");
    const token = order.lastIndexOf("/api/v1/queue-revision");
    expect(capture).toBeGreaterThanOrEqual(0);
    expect(sessionRead).toBeGreaterThan(capture);
    expect(token).toBeGreaterThan(sessionRead);
  });
});

describe("a stale cached app (§5.2)", () => {
  it("a host on another allowlist offers one tap to reload", async () => {
    gets["/api/v1/meta"] = { host_version: "0.1.0", api_version: 1, allowlist_digest: "0".repeat(64), schema_version: 250 };
    const reload = vi.spyOn(reloader, "reload").mockImplementation(() => undefined);
    render(<App />);
    expect(await screen.findByText(UPDATED_LINE)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await waitFor(() => expect(reload).toHaveBeenCalledTimes(1));
  });

  it("the same host answers no line", async () => {
    render(<App />);
    await screen.findByRole("button", { name: "15 min" });
    await waitFor(() => expect(sent.some((one) => one.url === "/api/v1/meta")).toBe(true));
    expect(screen.queryByText(UPDATED_LINE)).toBeNull();
  });

  it("it is asked again on every return to the app", async () => {
    render(<App />);
    await screen.findByRole("button", { name: "15 min" });
    const before = sent.filter((one) => one.url === "/api/v1/meta").length;
    gets["/api/v1/meta"] = { host_version: "0.1.0", api_version: 1, allowlist_digest: "f".repeat(64), schema_version: 251 };
    await act(async () => {
      document.dispatchEvent(new Event("visibilitychange"));
      await new Promise((resolve) => setTimeout(resolve, 10));
    });
    expect(sent.filter((one) => one.url === "/api/v1/meta").length).toBe(before + 1);
    expect(await screen.findByText(UPDATED_LINE)).toBeTruthy();
  });

  it("a method the host no longer allows shows that line, never the raw refusal", async () => {
    answers.start_session = { status: 403, body: { ok: false, error: { code: "method_not_allowed", message: "method_not_allowed", retryable: false } } };
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
    expect(await screen.findByText(UPDATED_LINE)).toBeTruthy();
    expect(screen.queryByText("method_not_allowed")).toBeNull();
  });
});
