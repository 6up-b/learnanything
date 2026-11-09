// "Show me the book's way" off the Reader (owner, 2026-11-08): the passage
// shows under the hint, says it counts, and a press that finds none says so.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ComponentProps } from "react";
import { HintCard } from "./StepHints";
import { HELP_COPY } from "./helpModel";
import type { WorkbenchHintViewDto } from "../../api/dto";

const api = vi.hoisted(() => ({ getSpanView: vi.fn() }));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../components/OpenInSource", () => ({
  OpenInSource: (p: { spanId: string; context?: string }) => <div data-testid="page-view">{p.spanId} {p.context}</div>,
}));

const HINT = {
  assistId: "ha_1", kind: "next_step", level: 3, hintMd: "the hint", labels: {}, aboutStepId: null,
  continueFromStepId: null, stepLine: "", replies: ["book_way"], discriminatingAnswer: null, bridge: null, claims: [],
  symbolicEnabled: false,
} as unknown as WorkbenchHintViewDto;

function card(overrides: Partial<ComponentProps<typeof HintCard>>) {
  return render(<HintCard hint={HINT} steps={[]} pending={false} bridge={undefined} onReply={vi.fn()} onBookWay={vi.fn()}
    onSmallerStep={vi.fn()} onAnswer={vi.fn()} onSkip={vi.fn()} {...overrides} />);
}

const READY = { status: "ready", line: "§ compare with the book: §3.4 ▸", spanId: "s9", extractionId: "ext" } as const;

beforeEach(() => {
  api.getSpanView.mockReset();
  api.getSpanView.mockResolvedValue({ version: 1, spanView: { text: "the passage", sectionPath: ["Ch 3", "§3.4"], page: 41 } });
});
afterEach(cleanup);

it("shows the passage itself under the hint, says it counts, and offers the page", async () => {
  card({ bridge: READY, bookInline: { practiceItemId: "pi_1" } });
  expect((await screen.findByText("the passage"))).toBeTruthy();
  expect(api.getSpanView).toHaveBeenCalledWith({ extractionId: "ext", spanId: "s9", context: "reader",
    entityType: "practice_item", entityId: "pi_1" });
  expect(screen.getByText(/counts as a hint · Ch 3 › §3.4 · p\. 41/)).toBeTruthy();
  expect(screen.queryByTestId("workbench-bridge")).toBeNull();
  fireEvent.click(screen.getByText(HELP_COPY.bookWayPage));
  expect(screen.getByTestId("page-view").textContent).toBe("s9 reader");
});

it("says so when the books have no passage, or couldn't be searched", () => {
  const { unmount } = card({ bridge: { status: "none", reason: "none" }, bookInline: { practiceItemId: "pi_1" } });
  expect(screen.getByText(HELP_COPY.bookWayNone)).toBeTruthy();
  unmount();
  card({ bridge: { status: "none", reason: "unavailable" }, bookInline: { practiceItemId: "pi_1" } });
  expect(screen.getByText(HELP_COPY.bookWayUnavailable)).toBeTruthy();
  expect(api.getSpanView).not.toHaveBeenCalled();
});

it("says so when the passage can't be read", async () => {
  api.getSpanView.mockRejectedValue(new Error("gone"));
  card({ bridge: READY, bookInline: { practiceItemId: null } });
  await waitFor(() => expect(screen.getByText(HELP_COPY.bookWayUnavailable)).toBeTruthy());
});

it("keeps the Reader's link: no passage is fetched beside the book", () => {
  const onPeek = vi.fn();
  card({ bridge: READY, onPeek });
  fireEvent.click(screen.getByTestId("workbench-bridge"));
  expect(onPeek).toHaveBeenCalledWith("s9");
  expect(api.getSpanView).not.toHaveBeenCalled();
});
