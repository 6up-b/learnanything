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
