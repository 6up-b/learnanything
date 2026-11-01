// RW6b part 1's "Coming up" (spec §9.3; UX §4.8-4.9, S15, D36; W12): a dated
// timeline with purpose, why (LearnLoop's estimate) and undo; undo takes an
// optional reason; undo all; the next three then "later ▸" with no number;
// retirements read as good news with undo; no counts, nothing "overdue", no
// "error" or "mistake" about the learner's work.
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { ReaderComingUpDto, ReaderFollowupLineDto, ReaderRecapCardDto } from "../../api/dto";
import { ComingUp } from "./ComingUp";
import { RecapCard } from "./RecapCard";
import { upcomingDay } from "./recapCopy";

afterEach(cleanup);

const NOW = new Date(2026, 9, 12, 9, 0, 0); // Mon 12 Oct, local

function line(id: string, date: string, overrides: Partial<ReaderFollowupLineDto> = {}): ReaderFollowupLineDto {
  return {
    commitmentId: id, digestId: "rsd_1", extractionId: "ext1", purpose: "retention", novelty: "new_problem",
    noveltyLabel: "a new problem", purposeText: "a new problem on Mixtures, on your own", expectedMinutes: 6.2,
    why: "expected to show whether this holds without help · about 6 min · LearnLoop's estimate; its scale is not yet calibrated",
    date, actions: ["why", "undo"], ...overrides,
  };
}

function timeline(count: number): ReaderComingUpDto {
  const days = ["2026-10-14", "2026-10-15", "2026-10-19", "2026-10-21", "2026-11-09"];
  const lines = days.slice(0, count).map((day, index) => line(`c${index + 1}`, day));
  return { next: lines.slice(0, 3), later: lines.slice(3), undoAll: [{ digestId: "rsd_1" }],
           scale: "LearnLoop's estimate; its scale is not yet calibrated", enabled: true };
}

it("shows each check as a dated line with its purpose and minutes, never a count", () => {
  render(<ComingUp comingUp={timeline(2)} now={NOW} onUndo={vi.fn()} onUndoAll={vi.fn()} />);
  const region = screen.getByText("Coming up · checks on your own").parentElement as HTMLElement;
  expect(region.textContent).toContain("Wed");
  expect(region.textContent).toContain("a new problem on Mixtures, on your own · about 6 min");
  expect(region.textContent?.toLowerCase()).not.toMatch(/overdue|\bdue\b|error|mistake|\d+ checks?/);
  expect(within(region).getAllByRole("button", { name: "why" })).toHaveLength(2);
});

it("why expands to the purpose and the valuation, labelled as LearnLoop's estimate", () => {
  const { container } = render(<ComingUp comingUp={timeline(1)} now={NOW} onUndo={vi.fn()} onUndoAll={vi.fn()} />);
  expect(container.querySelector("[data-followup-why]")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "why" }));
  const why = container.querySelector("[data-followup-why]");
  expect(why?.textContent).toContain("LearnLoop's estimate");
});

it("undo takes an optional reason and says the check is undone, with a way to keep it", () => {
  const onUndo = vi.fn().mockResolvedValue(undefined);
  const onRestore = vi.fn().mockResolvedValue(undefined);
  render(<ComingUp comingUp={timeline(1)} now={NOW} onUndo={onUndo} onUndoAll={vi.fn()} onRestore={onRestore} />);
  fireEvent.click(screen.getByRole("button", { name: /^undo: / }));
  const box = screen.getByRole("textbox", { name: "why undo this check? (optional)" }) as HTMLInputElement;
  expect(box.placeholder).toBe("why? (optional)");
  expect(document.activeElement).not.toBe(box); // nothing takes focus
  fireEvent.change(box, { target: { value: "  I know this one  " } });
  fireEvent.keyDown(box, { key: "Enter" });
  expect(onUndo).toHaveBeenCalledWith("c1", "I know this one");
  expect(screen.getByText(/undone/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "keep it after all" }));
  expect(onRestore).toHaveBeenCalledWith("c1");
});

it("an undo with no reason sends none", () => {
  const onUndo = vi.fn().mockResolvedValue(undefined);
  render(<ComingUp comingUp={timeline(1)} now={NOW} onUndo={onUndo} onUndoAll={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: /^undo: / }));
  fireEvent.click(screen.getByRole("button", { name: /^undo: / }));
  expect(onUndo).toHaveBeenCalledWith("c1", null);
});

it("undo all retires every check of the session, with its optional reason", () => {
  const onUndoAll = vi.fn().mockResolvedValue(undefined);
  render(<ComingUp comingUp={timeline(2)} now={NOW} onUndo={vi.fn()} onUndoAll={onUndoAll} />);
  fireEvent.click(screen.getByRole("button", { name: "undo all" }));
  fireEvent.change(screen.getByRole("textbox"), { target: { value: "too many this week" } });
  fireEvent.click(screen.getByRole("button", { name: "undo all" }));
  expect(onUndoAll).toHaveBeenCalledWith("rsd_1", "too many this week");
  expect(screen.getAllByText(/undone/)).toHaveLength(2);
});

it("shows the next three by date, then later ▸ with no number", () => {
  render(<ComingUp comingUp={timeline(5)} now={NOW} onUndo={vi.fn()} onUndoAll={vi.fn()} />);
  expect(document.querySelectorAll("[data-followup]")).toHaveLength(3);
  const later = screen.getByRole("button", { name: "later ▸" });
  expect(later.textContent).toBe("later ▸");
  fireEvent.click(later);
  expect(document.querySelectorAll("[data-followup]")).toHaveLength(5);
  expect(screen.getByText("9 Nov")).toBeTruthy();
});

it("renders nothing when nothing is coming up", () => {
  const { container } = render(<ComingUp comingUp={{ ...timeline(0) }} now={NOW} onUndo={vi.fn()} onUndoAll={vi.fn()} />);
  expect(container.textContent).toBe("");
});

it("labels plan days as weekdays this week, else a date", () => {
  expect(upcomingDay("2026-10-14", NOW)).toBe("Wed");
  expect(upcomingDay("2026-10-12", NOW)).toBe("Mon");
  expect(upcomingDay("2026-10-25", NOW)).toBe("25 Oct");
  expect(upcomingDay("not a day", NOW)).toBe("");
});

function card(overrides: Partial<ReaderRecapCardDto> = {}): ReaderRecapCardDto {
  return {
    recapVersion: "rw6a-recap-v1", extractionId: "ext1",
    session: { sessionId: "v1", extractionId: "ext1", visitIds: ["v1"], startedAt: "2026-10-09T20:00:00Z", endedAt: "2026-10-09T20:40:00Z", minutes: 40 },
    continueAt: null, stillOpen: [], unfinished: [], worthASecondLook: [],
    sinceLastTime: { demonstrated: [], checksRetired: [{ commitmentId: "cr1", retiredAt: "2026-10-11T08:00:00Z", solvedAttemptId: "a9" }] },
    comingUp: timeline(1),
    ...overrides,
  };
}

const handlers = () => ({ onExpand: vi.fn(), onContinue: vi.fn(), onDismiss: vi.fn(), onOpenInquiry: vi.fn(),
                         onSetStatus: vi.fn(), onResume: vi.fn() });

it("the card shows Coming up and a retirement as good news with undo", () => {
  const onRestore = vi.fn().mockResolvedValue(undefined);
  render(<RecapCard recap={card()} collapsed={false} now={NOW} {...handlers()} onUndoFollowup={vi.fn()}
                    onUndoAllFollowups={vi.fn()} onRestoreFollowup={onRestore} />);
  const region = screen.getByRole("region", { name: "Last time here" });
  expect(within(region).getByText("Coming up · checks on your own")).toBeTruthy();
  expect(region.textContent).toContain("No longer needed: you solved one like it on Sun");
  fireEvent.click(within(region).getByRole("button", { name: "undo: keep this check" }));
  expect(onRestore).toHaveBeenCalledWith("cr1");
  expect(region.textContent?.toLowerCase()).not.toMatch(/overdue|\bdue\b|error|mistake/);
});

it("the good news names the solve's own day, or the settled explanations", () => {
  const solved = { commitmentId: "cr1", retiredAt: "2026-10-13T08:00:00Z", answeredBy: "solved_on_your_own",
                   solvedAttemptId: "a9", solvedAt: "2026-10-11T08:00:00Z" };
  const rivals = { commitmentId: "cr2", retiredAt: "2026-10-13T08:00:00Z", answeredBy: "rivals_resolved",
                   solvedAttemptId: null, solvedAt: null };
  render(<RecapCard recap={card({ sinceLastTime: { demonstrated: [], checksRetired: [solved, rivals] } })}
                    collapsed={false} now={NOW} {...handlers()} />);
  const region = screen.getByRole("region", { name: "Last time here" });
  expect(region.textContent).toContain("No longer needed: you solved one like it on Sun");
  expect(region.textContent).toContain("No longer needed: the explanations it was to tell apart are settled");
  expect(region.textContent).not.toContain("you solved one like it on Tue");
});

it("the card leaves Coming up out without the follow-up actions (an older sidecar)", () => {
  render(<RecapCard recap={card({ comingUp: undefined })} collapsed={false} now={NOW} {...handlers()} />);
  expect(screen.queryByText("Coming up · checks on your own")).toBeNull();
  expect(screen.queryByRole("button", { name: "undo: keep this check" })).toBeNull();
});
