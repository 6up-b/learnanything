// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { PassageKnowsDto, PassageUnionSpanDto } from "../../../api/dto";
import { KnowsPanel } from "./KnowsPanel";

afterEach(cleanup);

const span = (extra: Partial<PassageUnionSpanDto> = {}): PassageUnionSpanDto => ({
  spanId: "s1", sectionId: "sec1", annotations: [], padBlocks: [], exchanges: [], adjustments: [], gaps: [], passageLinks: [], figures: [],
  checksDue: [], notes: [], authoredQuestions: [], carried: [], exposure: { timesShown: 2, lastShownAt: null, withheld: false }, ...extra,
});

describe("What this knows", () => {
  it("groups what the passage holds, says an alias needs re-anchoring, and opens a question's thread", async () => {
    const openThread = vi.fn();
    const read: PassageKnowsDto = { objectKey: "k", sourceIds: ["src"], places: [{ extractionId: "e", spanId: "s1", role: null, knows: span({
      exchanges: [{ questionEventId: "q1", role: "selection", quality: "exact_selection", alias: "needs_reanchor", context: "", questionMd: "why is it positive", createdAt: "2026-11-20T10:00:00Z" }],
      carried: [{ carriedId: "c1", text: "does it hold for n = 0", since: "2026-11-21T10:00:00Z", state: "carried", alias: "exact" }],
    }) }] } as unknown as PassageKnowsDto;
    render(<KnowsPanel object={{ objectKind: "passage", extractionId: "e", spanId: "s1" }} load={async () => read} actions={{ openThread, openPadBlock: vi.fn(), openPassage: vi.fn() }} onClose={() => undefined} />);
    const question = await screen.findByText(/why is it positive/);
    expect(question.textContent).toContain("may need re-anchoring");
    expect(screen.getByText("your questions to the tutor")).toBeTruthy();
    expect(screen.getByText(/does it hold for n = 0/)).toBeTruthy();
    expect(screen.getByText(/shown 2 times/)).toBeTruthy();
    fireEvent.click(question);
    expect(openThread).toHaveBeenCalledWith("q1");
  });

  it("says a check is due and shows nothing of it", async () => {
    const read = { objectKey: "k", sourceIds: [], places: [{ extractionId: "e", spanId: "s1", role: null, knows: span({ checksDue: [{ commitmentId: "secret_c" }] }) }] } as unknown as PassageKnowsDto;
    render(<KnowsPanel object={{ objectKind: "passage", extractionId: "e", spanId: "s1" }} load={async () => read} actions={{ openThread: vi.fn(), openPadBlock: vi.fn(), openPassage: vi.fn() }} onClose={() => undefined} />);
    await screen.findByText(/a check is due before this passage/);
    expect(document.body.textContent).not.toContain("secret_c");
  });

  it("says when nothing is held yet", async () => {
    render(<KnowsPanel object={{ objectKind: "window", windowId: "w" }} load={async () => ({ objectKey: "k", sourceIds: [], places: [] }) as unknown as PassageKnowsDto} actions={{ openThread: vi.fn(), openPadBlock: vi.fn(), openPassage: vi.fn() }} onClose={() => undefined} />);
    await screen.findByText("nothing here yet");
  });

  it("takes the focus when it opens, closes on escape wherever the key lands, and gives the focus back", async () => {
    const before = document.createElement("button");
    document.body.appendChild(before);
    before.focus();
    const onClose = vi.fn();
    const view = render(<KnowsPanel object={{ objectKind: "window", windowId: "w" }} load={async () => ({ objectKey: "k", sourceIds: [], places: [] }) as unknown as PassageKnowsDto} actions={{ openThread: vi.fn(), openPadBlock: vi.fn(), openPassage: vi.fn() }} onClose={onClose} />);
    await screen.findByText("nothing here yet");
    expect(screen.getByRole("dialog", { name: "what this knows" }).contains(document.activeElement)).toBe(true);
    fireEvent.keyDown(document.body, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
    view.unmount();
    expect(document.activeElement).toBe(before);
    before.remove();
  });
});
