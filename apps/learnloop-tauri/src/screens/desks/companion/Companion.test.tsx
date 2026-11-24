// The companion's body (spec §8.1, §8.4, §8.5): each job state said honestly, the history by day and desk with
// its anchors, a previewed diff with accept and "not this", and no asking without a passage to ask about.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CompanionHistoryDto } from "../../../api/dto";
import { REAL_TIMERS } from "../keys/router";
import type { CompanionExchange } from "./asks";
import { Companion, type CompanionProps } from "./Companion";
import { DiffProposal } from "./DiffProposal";
import { threadExchanges } from "../windows/ThreadWindow";

vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

afterEach(cleanup);

const HISTORY: CompanionHistoryDto = {
  version: 1,
  days: [
    { date: "2026-11-18", desks: [{ deskId: "d1", exchanges: [{ questionEventId: "q1", questionMd: "why the exponential?", answerFirstSentence: "Differences become ratios.", answerStatus: "answered", context: "reader", surface: "desk", where: "on a desk", origin: "live", goalId: null, padBlockIds: [], anchor: { extractionId: "ext", spanId: "s2", quality: "exact_selection" }, createdAt: "2026-11-18T10:00:00Z" }] }] },
    { date: "2026-11-14", desks: [{ deskId: null, exchanges: [{ questionEventId: "q0", questionMd: "an old question", answerFirstSentence: "", answerStatus: "answered", context: "reader", surface: "reader", where: "in the Reader", origin: "backfill", goalId: null, padBlockIds: [], anchor: null, createdAt: "2026-11-14T10:00:00Z" }] }] },
  ],
  cursor: null,
};

function exchange(over: Partial<CompanionExchange>): CompanionExchange {
  return { requestId: "r1", deskId: "d1", windowId: "w1", question: "why?", quote: null, extractionId: "ext", spanId: "s1", status: "asking", jobStatus: "running", streamedPieces: 0, answer: null, error: null, kept: false, stopping: false, sent: false, askedAt: 0,
    request: { surface: "desk", deskId: "d1", extractionId: "ext", spanId: "s1", question: "why?", parentExchangeId: null }, ...over };
}

function props(over: Partial<CompanionProps> = {}): CompanionProps {
  return {
    state: { mode: "docked", origin: "drawer", anchored: null, last: "none" },
    dock: "br",
    stage: { width: 1300, height: 900 },
    overview: false,
    reducedMotion: true,
    timers: REAL_TIMERS,
    context: { following: { glyph: "§", title: "A book" }, goalInContext: true },
    threadTitle: "why?",
    thread: [],
    chip: null,
    cannotAsk: null,
    avoid: 0,
    loadHistory: async () => HISTORY,
    deskTitle: (id) => (id === "d1" ? "softmax" : "no desk"),
    onAsk: vi.fn(),
    onCancel: vi.fn(),
    onRetry: vi.fn(),
    onClearChip: vi.fn(),
    onOpenClaim: vi.fn(),
    onOpenAnchor: vi.fn(),
    onOpenThread: vi.fn(),
    onHide: vi.fn(),
    onDock: vi.fn(),
    onSnap: vi.fn(),
    onPill: vi.fn(),
    ...over,
  };
}

describe("the thread's states", () => {
  it("asking can be stopped; a failure says why and offers a retry only when it may help; interrupted can be asked again", () => {
    const p = props({ thread: [
      exchange({ requestId: "a", status: "asking", streamedPieces: 4 }),
      exchange({ requestId: "b", status: "failed", error: { code: "provider_unavailable", message: "The tutor isn't reachable right now.", retryable: true } }),
      exchange({ requestId: "c", status: "failed", error: { code: "waiting_for_ok", message: "LearnLoop needs your OK to use AI.", retryable: false } }),
      exchange({ requestId: "d", status: "interrupted", error: { code: "job_not_found", message: "LearnLoop restarted since it was asked.", retryable: false } }),
      exchange({ requestId: "e", status: "cancelled", kept: true }),
    ] });
    render(<Companion {...p} />);
    expect(screen.getByText(/4 pieces so far/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "stop" }));
    expect(p.onCancel).toHaveBeenCalledWith("a");
    expect(screen.getByText("The tutor isn't reachable right now.")).toBeTruthy();
    expect(screen.getAllByRole("button", { name: "try again" })).toHaveLength(1);
    expect(screen.getByText("LearnLoop needs your OK to use AI.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "ask again" }));
    expect(p.onRetry).toHaveBeenCalledWith("d");
    expect(screen.getByText(/kept in your history/)).toBeTruthy();
  });

  it("with no passage to ask about, the input says so and asks nothing", () => {
    const p = props({ cannotAsk: "ask from a passage: focus a book or a video, or select a passage, then press c" });
    render(<Companion {...p} />);
    const input = screen.getByLabelText("ask about this") as HTMLInputElement;
    expect(input.disabled).toBe(true);
    expect(screen.getByText(/ask from a passage/)).toBeTruthy();
  });

  it("the context line follows the focused window and says the goal is in view, never that the tutor answers with it", () => {
    render(<Companion {...props()} />);
    expect(screen.getByText("following § A book")).toBeTruthy();
    // The tutor's prompt does not receive the goal (the desk context is recorded, not sent): the badge claims no more.
    const badge = screen.getByText("◎ goal in view");
    expect(badge.getAttribute("title")).toBe("your goal's lens is on this desk; the tutor's answers don't take it into account yet");
    expect(document.body.textContent).not.toContain("goal in context");
  });
});

describe("the history", () => {
  it("lists exchanges by day and desk, newest first, with where they happened; an anchor opens beside", async () => {
    const p = props();
    render(<Companion {...p} />);
    fireEvent.click(screen.getByRole("tab", { name: "history" }));
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });
    expect(screen.getByText("› why the exponential?")).toBeTruthy();
    expect(screen.getByText("◇ Differences become ratios.")).toBeTruthy();
    expect(screen.getByText("softmax")).toBeTruthy();
    expect(screen.getByText("before desks")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "§ the passage ↗" }));
    expect(p.onOpenAnchor).toHaveBeenCalledWith({ extractionId: "ext", spanId: "s2", quality: "exact_selection" });
  });
});

describe("a proposed diff (pads arrive next)", () => {
  it("shows the inserted lines; without a pad to write to it says where it will land; not this declines", () => {
    render(<DiffProposal proposal={{ id: "p1", target: "running", label: "Put a check in your scratchpad", lines: ["check: grad = p - onehot"] }} />);
    expect(screen.getByText("+ check: grad = p - onehot")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "accept" })).toBeNull();
    expect(screen.getByText(/pads arrive next/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "not this" }));
    expect(screen.getByText(/nothing was written/)).toBeTruthy();
  });

  it("with a pad, accept writes and says so", async () => {
    const onAccept = vi.fn(async () => undefined);
    render(<DiffProposal proposal={{ id: "p1", target: "running", label: "Add this", lines: ["a line"], onAccept }} />);
    fireEvent.click(screen.getByRole("button", { name: "accept" }));
    await act(async () => {
      await Promise.resolve();
    });
    expect(onAccept).toHaveBeenCalled();
    expect(screen.getByText(/accepted · written to/)).toBeTruthy();
  });
});

describe("a thread window's exchanges", () => {
  it("are the whole thread the named exchange belongs to, in order", () => {
    const base = { extractionId: "ext", spanId: "s", answerMode: "answer_directly" as const, citations: [], createdAt: null, answerMd: "" };
    const all = [
      { ...base, eventId: "a", questionMd: "root" },
      { ...base, eventId: "b", parentExchangeId: "a", questionMd: "follow-up" },
      { ...base, eventId: "c", questionMd: "another root" },
      { ...base, eventId: "d", parentExchangeId: "b", questionMd: "deeper" },
    ];
    expect(threadExchanges(all, "b").map((exchange) => exchange.eventId)).toEqual(["a", "b", "d"]);
    expect(threadExchanges(all, "c").map((exchange) => exchange.eventId)).toEqual(["c"]);
  });
});

describe("the fix round (RD3 review)", () => {
  it("a stop not yet resolved says stopping, with no stop button and no claim about what was sent", () => {
    render(<Companion {...props({ thread: [exchange({ requestId: "a", status: "asking", stopping: true, sent: true })] })} />);
    expect(screen.getByText(/stopping/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "stop" })).toBeNull();
    expect(screen.queryByText(/Nothing was sent/)).toBeNull();
  });

  it("a stopped question says whether it was sent from whether it reached the tutor, never from kept", () => {
    render(<Companion {...props({ thread: [
      exchange({ requestId: "a", status: "cancelled", kept: false, sent: true }),
      exchange({ requestId: "b", status: "cancelled", kept: false, sent: false }),
      exchange({ requestId: "c", status: "cancelled", kept: true, sent: true }),
    ] })} />);
    expect(screen.getByText(/was sent before it stopped/)).toBeTruthy();
    expect(screen.getByText(/Stopped before it was sent/)).toBeTruthy();
    expect(screen.getByText(/kept in your history/)).toBeTruthy();
    expect(screen.queryByText("Nothing was sent.")).toBeNull();
  });

  it("a question waiting for the desk's writes shows as waiting", () => {
    render(<Companion {...props({ thread: [exchange({ requestId: "a", status: "waiting" })] })} />);
    const waiting = document.querySelector('[data-exchange-status="waiting"]');
    expect(waiting?.textContent).toMatch(/saving your desk first/);
  });

  it("history pages through the cursor: older exchanges append, keeping days and desks", async () => {
    const pages: Array<string | undefined> = [];
    const loadHistory = vi.fn(async (_query: string, cursor?: string) => {
      pages.push(cursor);
      if (!cursor) return { ...HISTORY, days: [HISTORY.days[0]], cursor: "c1" };
      return { ...HISTORY, days: [HISTORY.days[1]], cursor: null };
    });
    render(<Companion {...props({ loadHistory })} />);
    fireEvent.click(screen.getByRole("tab", { name: "history" }));
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });
    expect(screen.queryByText("› an old question")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /older exchanges/ }));
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });
    expect(screen.getByText("› why the exponential?")).toBeTruthy();
    expect(screen.getByText("› an old question")).toBeTruthy();
    expect(pages.filter((page) => page === "c1")).toHaveLength(1);
    expect(screen.queryByRole("button", { name: /older exchanges/ })).toBeNull();
  });

  it("in the overview the panel is inert and the focus leaves it; back from the overview the focus returns", () => {
    const p = props({ state: { mode: "docked", origin: "drawer", anchored: null, last: "none" } });
    const { rerender } = render(<Companion {...p} />);
    const input = screen.getByLabelText("ask about this") as HTMLInputElement;
    input.focus();
    expect(document.activeElement).toBe(input);
    rerender(<Companion {...p} overview />);
    const panel = document.querySelector("[data-desk-companion]") as HTMLElement;
    expect(panel.hasAttribute("inert")).toBe(true);
    expect(panel.getAttribute("aria-hidden")).toBe("true");
    expect(panel.contains(document.activeElement)).toBe(false);
    rerender(<Companion {...p} overview={false} />);
    expect(panel.hasAttribute("inert")).toBe(false);
    expect(document.activeElement).toBe(input);
  });
});
