// RW1a's inquiry components on their own: the detour strip, the reconnect
// line, the passage quick check, the inquiry keys, and the activity logger.
import { useState } from "react";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { DetourStrip } from "./DetourStrip";
import { InquiryQuickCheck } from "./InquiryQuickCheck";
import { ReconnectLine } from "./ReconnectLine";
import { ReaderAskBranches, type ReaderExchange } from "./ReaderAskBranches";
import { EMPTY_STACK, pushDetour, type ReturnEntry } from "./returnStack";
import type { ReaderInquiryQuestionDto } from "../../api/dto";

const api = vi.hoisted(() => ({ readerLogActivity: vi.fn() }));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

import {
  activitySince,
  flushReaderActivity,
  learnerActivitySnapshot,
  logReaderActivity,
  noteLearnerActivity,
  resetReaderActivityForTests,
  setReaderActivityEnabled,
} from "./activity";

beforeEach(() => {
  vi.resetAllMocks();
  resetReaderActivityForTests();
});
afterEach(cleanup);

const entry = (id: string, label: string): ReturnEntry => ({
  id, kind: "peek", sourceId: "src", sourceTitle: "Book", extractionId: "ext", spanId: id, selection: null,
  railTab: "ask", exchangeId: null, label, openedAt: 0,
});

it("the detour strip is absent without a detour and a navigation landmark with one", () => {
  const onGoTo = vi.fn();
  const { rerender } = render(<DetourStrip stack={EMPTY_STACK} onGoTo={onGoTo} />);
  expect(screen.queryByRole("navigation", { name: "Detour" })).toBeNull();
  const stack = pushDetour(EMPTY_STACK, { ...entry("o", "Mixtures ¶3"), kind: "origin" }, entry("a", "why weighted by p?"));
  rerender(<DetourStrip stack={stack} onGoTo={onGoTo} />);
  const nav = screen.getByRole("navigation", { name: "Detour" });
  expect(nav.textContent).toContain("alt+← back");
  fireEvent.click(within(nav).getByRole("button", { name: "Mixtures ¶3" }));
  expect(onGoTo).toHaveBeenCalledWith(0);
});

it("the reconnect line quotes the learner's words and offers yes, still unclear and quick check", () => {
  const onYes = vi.fn();
  const onStillUnclear = vi.fn();
  const onQuickCheck = vi.fn();
  render(<ReconnectLine question="why weighted by p?" placement="inline" onYes={onYes} onStillUnclear={onStillUnclear} onQuickCheck={onQuickCheck} />);
  const line = screen.getByRole("group", { name: "Does this make sense now?" });
  expect(line.textContent).toContain("why weighted by p?");
  expect(line.textContent).toContain("does this make sense now?");
  fireEvent.click(screen.getByRole("button", { name: "yes" }));
  expect(onYes).toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "quick check" }));
  expect(onQuickCheck).toHaveBeenCalled();
  // Not "check me": that always means an attempt on your own (D43).
  expect(line.textContent).not.toMatch(/check me/i);
  fireEvent.click(screen.getByRole("button", { name: "still unclear…" }));
  expect(screen.getByText(/where this goes/)).toBeTruthy();
  fireEvent.change(screen.getByLabelText("What's still unclear?"), { target: { value: "the bounds" } });
  fireEvent.click(screen.getByRole("button", { name: "ask this ^↵" }));
  expect(onStillUnclear).toHaveBeenCalledWith("the bounds");
});

const question: ReaderInquiryQuestionDto = {
  id: "raq", extractionId: "ext", sectionId: "u1", status: "proposed", questionMd: "Why?", expectedAnswerMd: "Because.",
  spanIds: ["s1"], practiceItemId: null, answeredAt: null, scopeKind: "inquiry", questionStyle: "recall",
  anchorSpanIds: ["s1"], inquiryRootEventId: "root", responseMd: null, selfCheck: null, escalationLearningObjectId: "lo",
};

it("the quick check is pending until it lands, then shows the intended answer beside the learner's", () => {
  const handlers = { onAnswer: vi.fn(), onSelfCheck: vi.fn(), onDismiss: vi.fn(), onEscalate: vi.fn() };
  const { rerender } = render(<InquiryQuickCheck phase="pending" question={null} {...handlers} />);
  expect(screen.getByRole("status").textContent).toContain("writing a quick check on this passage…");
  rerender(<InquiryQuickCheck phase="landed" question={question} {...handlers} />);
  const card = screen.getByRole("region", { name: "Quick check" });
  expect(card.textContent).toContain("never a grade");
  expect(card.querySelector('[data-voice="model"]')?.textContent).toContain("Why?");
  fireEvent.change(screen.getByLabelText("Your answer"), { target: { value: "Since." } });
  fireEvent.click(screen.getByRole("button", { name: /compare with the source/ }));
  expect(handlers.onAnswer).toHaveBeenCalledWith("Since.");
  rerender(<InquiryQuickCheck phase="landed" question={{ ...question, status: "answered", responseMd: "Since." }} {...handlers} />);
  expect(screen.getByText("Because.")).toBeTruthy();
  expect(screen.getByText("Since.").closest("[data-voice]")?.getAttribute("data-voice")).toBe("learner");
  fireEvent.click(screen.getByRole("button", { name: "no" }));
  expect(handlers.onSelfCheck).toHaveBeenCalledWith("no");
  fireEvent.click(screen.getByRole("button", { name: "add to practice →" }));
  expect(handlers.onEscalate).toHaveBeenCalled();
  rerender(<InquiryQuickCheck phase="landed" question={{ ...question, status: "dismissed" }} {...handlers} />);
  expect(screen.getByText(/You set this quick check aside/)).toBeTruthy();
});

const exchange = (id: string, parent: string | null, resolution: "open" | "resolved" = "open"): ReaderExchange => ({
  id, parentExchangeId: parent, extractionId: "ext", spanId: "s1", selectionSpanIds: [], selectionQuoteMd: null,
  question: `Question ${id}`, answerMd: `Answer ${id}`, answerMode: "answer_directly", citations: [], createdAt: null,
  questionEventId: `q_${id}`, resolution,
});

it("the inquiry keys: f follow-up, p passage, r resolved on a root and done on a branch, o reopen, arrows move", () => {
  const props = {
    onFollowUp: vi.fn(), onShowPassage: vi.fn(), onSetStatus: vi.fn(), onBranchDone: vi.fn(),
  };
  function Harness({ rootResolution }: { rootResolution: "open" | "resolved" }) {
    const [collapsed] = useState(new Set<string>());
    return <ReaderAskBranches exchanges={[exchange("child", "root"), exchange("root", null, rootResolution)]} collapsedIds={collapsed}
      query="" busy={false} onToggle={() => undefined} {...props} />;
  }
  const { rerender } = render(<Harness rootResolution="open" />);
  const [rootHeader, childHeader] = screen.getAllByRole("button", { name: /^▾ Question/ });
  fireEvent.keyDown(rootHeader, { key: "f" });
  expect(props.onFollowUp).toHaveBeenCalledWith(expect.objectContaining({ id: "root" }));
  fireEvent.keyDown(rootHeader, { key: "p" });
  expect(props.onShowPassage).toHaveBeenCalledWith("s1");
  fireEvent.keyDown(rootHeader, { key: "r" });
  expect(props.onSetStatus).toHaveBeenCalledWith(expect.objectContaining({ id: "root" }), "resolved");
  fireEvent.keyDown(childHeader, { key: "r" });
  expect(props.onBranchDone).toHaveBeenCalledWith(expect.objectContaining({ id: "child" }));
  rootHeader.focus();
  fireEvent.keyDown(rootHeader, { key: "ArrowDown" });
  expect(document.activeElement).toBe(childHeader);
  rerender(<Harness rootResolution="resolved" />);
  fireEvent.keyDown(screen.getAllByRole("button", { name: /^▾ Question/ })[0], { key: "o" });
  expect(props.onSetStatus).toHaveBeenLastCalledWith(expect.objectContaining({ id: "root" }), "open");
  expect(screen.getByRole("button", { name: "reopen" })).toBeTruthy();
});

it("activity is batched, off while switched off, and never surfaces a failure", async () => {
  api.readerLogActivity.mockRejectedValue(new Error("sidecar down"));
  logReaderActivity({ kind: "reader_selection", payload: { span_count: 1 } });
  flushReaderActivity();
  expect(api.readerLogActivity).not.toHaveBeenCalled();
  setReaderActivityEnabled(true);
  logReaderActivity({ kind: "reader_selection", payload: { span_count: 1 } });
  logReaderActivity({ kind: "reader_view_opened", payload: { visit_id: "v" } });
  flushReaderActivity();
  expect(api.readerLogActivity).toHaveBeenCalledTimes(1);
  expect(api.readerLogActivity.mock.calls[0][0].events).toHaveLength(2);
  await Promise.resolve();
  const before = learnerActivitySnapshot();
  noteLearnerActivity("typed");
  expect(activitySince(before)).toEqual({ typed: true });
});
