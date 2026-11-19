// UX journey audit UX-5 (student-1 #35-39): a past exam's card said "for
// practice only" and its details said nothing about what that means.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { SourceLibraryCard } from "../api/dto";
import { findJargon } from "../copy/denyList";
import { BookCard, PAST_EXAM_DETAILS } from "./BookCard";

vi.mock("./IntentControl", () => ({ IntentControl: () => null }));

afterEach(cleanup);

const EXAM: SourceLibraryCard = {
  sourceId: "src_exam", title: "18.06 Linear Algebra, Exam 1", acquisitionKind: "pdf", canonicalUri: "/exams/quiz1.pdf",
  workId: null, currentRevisionId: "rev_1", revisionCount: 1, readiness: "ready", unitCount: 1, blockCount: 4,
  extractionStatus: "completed", suggestedRole: null, readerEnabled: false, updateAvailable: false, kindNoun: "PDF",
  statusLine: null
};

it("UX-5: a past exam's details say where it is and what it does; it offers no Open", () => {
  render(<BookCard card={EXAM} onContinue={vi.fn()} onAction={vi.fn()} />);
  expect(screen.queryByRole("button", { name: /Continue|Open/ })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  const line = screen.getByText(PAST_EXAM_DETAILS);
  expect(line).toBeTruthy();
  expect(findJargon(PAST_EXAM_DETAILS)).toEqual([]);
});

it("a book that opens in the Reader has no such line", () => {
  render(<BookCard card={{ ...EXAM, readerEnabled: true }} onContinue={vi.fn()} onAction={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(screen.queryByText(PAST_EXAM_DETAILS)).toBeNull();
});

// UX fix stage 3 (audit F7, student-1 #101, beginner-1 #70-74, retainer-1 #70):
// "Questions wait for your OK · Review" opened the one-time OK, and the learner
// expected questions. The label now says what the press does at that moment.
it("F7: the card's OK action says it asks for the OK, and still opens the same sheet", () => {
  const onAction = vi.fn();
  const card = { ...EXAM, readerEnabled: true, statusLine: { text: "Questions wait for your OK", tone: "quiet" as const, action: { kind: "connect_ai" as const, label: "Review" }, details: null } };
  render(<BookCard card={card} onContinue={vi.fn()} onAction={onAction} />);
  expect(screen.queryByRole("button", { name: "Review" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Give your OK" }));
  expect(onAction).toHaveBeenCalledWith("connect_ai", card);
});

it("F7: other actions keep their own words (changes to look at are still Review; no AI is still Connect)", () => {
  const changes = { ...EXAM, readerEnabled: true, statusLine: { text: "2 changes need a look", tone: "quiet" as const, action: { kind: "open_changes" as const, label: "Review" }, details: null } };
  render(<BookCard card={changes} onContinue={vi.fn()} onAction={vi.fn()} />);
  expect(screen.getByRole("button", { name: "Review" })).toBeTruthy();
  cleanup();
  const connect = { ...EXAM, readerEnabled: true, statusLine: { text: "Questions need an AI connection", tone: "quiet" as const, action: { kind: "connect_ai" as const, label: "Connect" }, details: null } };
  render(<BookCard card={connect} onContinue={vi.fn()} onAction={vi.fn()} />);
  expect(screen.getByRole("button", { name: "Connect" })).toBeTruthy();
});
