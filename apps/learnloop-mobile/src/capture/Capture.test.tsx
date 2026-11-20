// Capture and the desktop being away (§7), and pairing (§4.2)
// Split out of App.test.tsx (mobile v2 V2, V1's carried item): the cases are unchanged.
import {
  act, answers, App, beforeEach, beginSession, cacheSessionId, called, calls, cleanup, describe, expect, fakeFetch, feedback, fireEvent,
  getAnswers, gets, installFakeHost, it, item, listOutbox, PLAN_OFF, queue, rememberPendingSubmit, render, respond, row, saveCredential,
  screen, session, vi, waitFor, type Call, type RpcAnswer
} from "../test/fakeHost";

import { findJargon } from "@desktop/copy/denyList";
import { CAPTURE_COPY } from "./CaptureScreen";

installFakeHost();

/** UX fix stage 4 (F13): the sent line now says when; a capture sent in the test's moment was sent just now. */
const SENT_NOW = "Sent to your desktop · just now.";

describe("capture and the desktop being away (§7)", () => {
  it("a capture is saved while the desktop is asleep and sent when it wakes", async () => {
    let awake = false;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (!awake) return Promise.reject(new TypeError("asleep"));
      if (String(input) === "/api/v1/capture") return Promise.resolve(new Response("{}", { status: 201 }));
      return fakeFetch(input, init);
    }));
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Capture" }));
    fireEvent.change(screen.getByLabelText("A thought, a problem or a link"), { target: { value: "An idea" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByText(CAPTURE_COPY.savedHere)).toBeTruthy();
    await waitFor(async () => expect(await listOutbox()).toHaveLength(1));
    expect(await screen.findByText(/Desktop offline/)).toBeTruthy();
    awake = true;
    await act(async () => {
      window.dispatchEvent(new Event("focus"));
      await new Promise((resolve) => setTimeout(resolve, 10));
    });
    await waitFor(async () => expect(await listOutbox()).toEqual([]));
  });

  // UX journey audit UX-9 (phone-2 #31-48): "1 waiting to send." stayed after the desktop had
  // accepted the capture (201), then went with no word; nothing ever said it arrived.
  it("UX-9: a capture the desktop accepts says it was sent, and nothing is left waiting", async () => {
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input) === "/api/v1/capture") return Promise.resolve(new Response("{}", { status: 201 }));
      return fakeFetch(input, init);
    }));
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Capture" }));
    fireEvent.change(screen.getByLabelText("A thought, a problem or a link"), { target: { value: "An idea" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect((await screen.findByText(SENT_NOW)).getAttribute("role")).toBe("status");
    expect(screen.queryByText(/waiting to send/)).toBeNull();
    // It stays while the learner types the next one, until the next capture.
    fireEvent.change(screen.getByLabelText("A thought, a problem or a link"), { target: { value: "Another" } });
    expect(screen.getByText(SENT_NOW)).toBeTruthy();
  });

  it("UX-9: while the desktop is away it says the capture waits on the phone; when it wakes, that it was sent", async () => {
    let awake = false;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (!awake) return Promise.reject(new TypeError("asleep"));
      if (String(input) === "/api/v1/capture") return Promise.resolve(new Response("{}", { status: 201 }));
      return fakeFetch(input, init);
    }));
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Capture" }));
    fireEvent.change(screen.getByLabelText("A thought, a problem or a link"), { target: { value: "An idea" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByText(CAPTURE_COPY.savedHere)).toBeTruthy();
    expect(await screen.findByText("1 waiting to send.")).toBeTruthy();
    expect(screen.queryByText(SENT_NOW)).toBeNull();
    awake = true;
    await act(async () => {
      window.dispatchEvent(new Event("focus"));
      await new Promise((resolve) => setTimeout(resolve, 10));
    });
    expect(await screen.findByText(SENT_NOW)).toBeTruthy();
    expect(screen.queryByText(/waiting to send/)).toBeNull();
  });

  // UX fix stage 4 (audit F13, P9; phone-2 #31-53): "Sent to your desktop." said nothing of when, and the line
  // went with the screen: leaving Capture and coming back showed no word of the last capture.
  it("F13: the sent line says when, from the capture's own time, and is still there after leaving Capture and coming back", async () => {
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input) === "/api/v1/capture") return Promise.resolve(new Response("{}", { status: 201 }));
      return fakeFetch(input, init);
    }));
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Capture" }));
    fireEvent.change(screen.getByLabelText("A thought, a problem or a link"), { target: { value: "An idea" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    const line = await screen.findByText("Sent to your desktop · just now.");
    expect(line.getAttribute("role")).toBe("status");
    const realNow = Date.now.bind(Date);
    const later = vi.spyOn(Date, "now").mockImplementation(() => realNow() + 2 * 60_000 + 5_000);
    try {
      fireEvent.click(screen.getByRole("button", { name: "Today" }));
      await waitFor(() => expect(screen.queryByLabelText("A thought, a problem or a link")).toBeNull());
      fireEvent.click(screen.getByRole("button", { name: "Capture" }));
      const again = await screen.findByText("Sent to your desktop · 2 min ago.");
      expect(again.getAttribute("role")).toBe("status");
      expect(findJargon(again.textContent ?? "")).toEqual([]);
    } finally {
      later.mockRestore();
    }
  });

  it("F13: a capture that waited on the phone says it was sent when the desktop took it, not when it was saved", async () => {
    let awake = false;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (!awake) return Promise.reject(new TypeError("asleep"));
      if (String(input) === "/api/v1/capture") return Promise.resolve(new Response("{}", { status: 201 }));
      return fakeFetch(input, init);
    }));
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Capture" }));
    fireEvent.change(screen.getByLabelText("A thought, a problem or a link"), { target: { value: "An idea" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByText(CAPTURE_COPY.savedHere)).toBeTruthy();
    // Away from Capture for an hour; the desktop wakes meanwhile and the app's own flush sends it.
    fireEvent.click(screen.getByRole("button", { name: "Today" }));
    const realNow = Date.now.bind(Date);
    const later = vi.spyOn(Date, "now").mockImplementation(() => realNow() + 60 * 60_000);
    try {
      awake = true;
      await act(async () => {
        window.dispatchEvent(new Event("focus"));
        await new Promise((resolve) => setTimeout(resolve, 10));
      });
      await waitFor(async () => expect(await listOutbox()).toEqual([]));
      fireEvent.click(screen.getByRole("button", { name: "Capture" }));
      expect(await screen.findByText("Sent to your desktop · just now.")).toBeTruthy();
    } finally {
      later.mockRestore();
    }
  });

  it("a URL is a url capture", async () => {
    const captured: unknown[] = [];
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input) === "/api/v1/capture") {
        captured.push(JSON.parse(init?.body as string));
        return Promise.resolve(new Response("{}", { status: 201 }));
      }
      return fakeFetch(input, init);
    }));
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Capture" }));
    fireEvent.change(screen.getByLabelText("A thought, a problem or a link"), { target: { value: "https://arxiv.org/abs/2401.00001" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(captured).toHaveLength(1));
    expect(captured[0]).toMatchObject({ kind: "url", url: "https://arxiv.org/abs/2401.00001" });
  });
});

describe("pairing (§4.2)", () => {
  it("an app with no token pairs with the manual code", async () => {
    const { deleteCredential, readCredential } = await import("../store/credential");
    await deleteCredential();
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input) === "/pair") {
        expect(JSON.parse(init?.body as string)).toEqual({ code: "ABCDEFGHJK", device_label: "Phone" });
        return new Response(JSON.stringify({ device_id: "d9", scope: "app", token: "new" }), { status: 200 });
      }
      return fakeFetch(input, init);
    }));
    render(<App />);
    fireEvent.change(await screen.findByLabelText("Manual code"), { target: { value: "ABCDEFGHJK" } });
    fireEvent.click(screen.getByRole("button", { name: "Pair" }));
    expect(await screen.findByRole("button", { name: "15 min" })).toBeTruthy();
    await expect(readCredential()).resolves.toEqual({ token: "new", deviceId: "d9", scope: "app" });
  });

  it("a Shortcut's code is refused with what to do", async () => {
    const { deleteCredential } = await import("../store/credential");
    await deleteCredential();
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ device_id: "d9", scope: "capture", token: "narrow" }), { status: 200 })));
    render(<App />);
    fireEvent.change(await screen.findByLabelText("Manual code"), { target: { value: "ABCDEFGHJK" } });
    fireEvent.click(screen.getByRole("button", { name: "Pair" }));
    expect(await screen.findByText(/for the Shortcut/)).toBeTruthy();
  });

  it("unpaired with captures waiting says how many", async () => {
    const { deleteCredential } = await import("../store/credential");
    const { addToOutbox } = await import("../store/outbox");
    await deleteCredential();
    await addToOutbox({ clientCaptureId: "c", kind: "text", text: "x", capturedAt: "t" });
    render(<App />);
    // Mobile v2 §4.1's plain words: "token" is on the deny-list, so the line says what to do.
    expect(await screen.findByText("Pair again to send 1 waiting capture.")).toBeTruthy();
  });
});
