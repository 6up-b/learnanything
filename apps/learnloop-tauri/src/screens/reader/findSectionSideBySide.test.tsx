// Reader CA6 on CA5a's find-section list (ux_reader_compare_ask_v1 §6.2-6.4,
// X7, §6.5 Records): `s` on a line, *side by side* on a line and *read side by
// side* in a peek's header open the hit side by side while the Reader passes
// onSideBySide; without it nothing new shows. Peeks and go there record CA5a's
// deferred salience-only events.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { CorrespondentPeekDto, CorrespondentSectionDto, CorrespondentsDto } from "../../api/dto";
import { FIND_COPY, FindSection, type FindSectionProps } from "./FindSection";
import { flushReaderActivity, resetReaderActivityForTests, setReaderActivityEnabled } from "./activity";

const { api } = vi.hoisted(() => ({ api: {
  readerCorrespondents: vi.fn(), readerCorrespondentPeek: vi.fn(), readerCorrespondentDismiss: vi.fn(), readerLogActivity: vi.fn(),
} }));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const SECTION = { id: "u61", label: "6.1 Introduction to eigenvalues", startSpanId: "s1" };

function hit(over: Partial<CorrespondentSectionDto> = {}): CorrespondentSectionDto {
  return {
    extractionId: "ext_axler", sectionId: "ax5a", title: "5.A Invariant subspaces", sourceId: "src_axler", sourceTitle: "Axler",
    read: false, jump: { extractionId: "ext_axler", sectionId: "ax5a", spanId: "a7" }, treatment: null,
    label: "found by search, not checked", by: "search", ...over,
  };
}

const LAY_51 = hit({ extractionId: "ext_lay", sectionId: "lay51", title: "5.1 Eigenvectors and eigenvalues", sourceId: "src_lay", sourceTitle: "Lay",
  jump: { extractionId: "ext_lay", sectionId: "lay51", spanId: "l3" }, read: true });
const LAY_52 = hit({ extractionId: "ext_lay", sectionId: "lay52", title: "5.2 The characteristic equation", sourceId: "src_lay", sourceTitle: "Lay",
  jump: { extractionId: "ext_lay", sectionId: "lay52", spanId: "l9" } });

function view(over: Partial<CorrespondentsDto> = {}): CorrespondentsDto {
  return {
    extractionId: "ext_strang", sectionId: SECTION.id, status: "unchecked", learningObjects: [],
    search: {
      label: "found by search, not checked", correctableLearningObjectIds: ["lo_eigen", "lo_charpoly"],
      sources: [
        { sourceId: "src_axler", sourceTitle: "Axler", sections: [hit()] },
        { sourceId: "src_lay", sourceTitle: "Lay", sections: [LAY_51, LAY_52] },
      ],
    },
    checkableLearningObjectIds: ["lo_eigen", "lo_charpoly"],
    ...over,
  };
}

const QUIET_NONE = view({ status: "none", search: null });

function peekOf(target: CorrespondentSectionDto, texts: string[], page: number | null = null): { peek: CorrespondentPeekDto } {
  return { peek: {
    extractionId: target.extractionId, sectionId: target.sectionId, sourceId: target.sourceId, sourceTitle: target.sourceTitle,
    title: target.title, jumpSpanId: target.jump.spanId!, page,
    blocks: texts.map((text, index) => ({ spanId: index === 0 ? target.jump.spanId! : `${target.jump.spanId}_${index}`, blockType: "Text", page, text })),
    exposureEventIds: texts.map((_text, index) => `see_${index}`),
  } };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => { callback(0); return 0; });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

async function flush() {
  await act(async () => { await Promise.resolve(); await Promise.resolve(); });
}

async function mount(props: Partial<FindSectionProps> = {}) {
  const handlers = { onGoThere: vi.fn(), onCompare: vi.fn(), onError: vi.fn() };
  const utils = render(<FindSection extractionId="ext_strang" section={SECTION} {...handlers} {...props} />);
  await flush();
  return { ...utils, ...handlers };
}

async function pressFind(pressed: CorrespondentsDto = view()) {
  api.readerCorrespondents.mockResolvedValueOnce(pressed);
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.action }));
  await flush();
}

it("`s` on a focused line, the line's button and the peek's header open side by side", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  api.readerCorrespondentPeek.mockResolvedValue(peekOf(LAY_51, ["An eigenvector…"]));
  const onSideBySide = vi.fn();
  await mount({ onSideBySide });
  await pressFind();
  expect(screen.getByText(FIND_COPY.keysSideBySide)).toBeTruthy();
  const first = screen.getByText("§ 5.A Invariant subspaces");
  first.focus();
  fireEvent.keyDown(first, { key: "s" });
  expect(onSideBySide).toHaveBeenLastCalledWith(hit());
  fireEvent.click(screen.getByRole("button", { name: "side by side with Lay 5.2 The characteristic equation" }));
  expect(onSideBySide).toHaveBeenLastCalledWith(LAY_52);
  fireEvent.click(screen.getByRole("button", { name: "peek at Lay 5.1 Eigenvectors and eigenvalues" }));
  await flush();
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.readSideBySide }));
  expect(onSideBySide).toHaveBeenLastCalledWith(LAY_51);
  // `s` on another button keeps that button's own press (no side by side).
  onSideBySide.mockClear();
  fireEvent.keyDown(screen.getByRole("button", { name: "go there: Axler 5.A Invariant subspaces" }), { key: "s" });
  expect(onSideBySide).not.toHaveBeenCalled();
});

it("without onSideBySide (switch off) the list is CA5a's exactly", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  api.readerCorrespondentPeek.mockResolvedValue(peekOf(LAY_51, ["An eigenvector…"]));
  await mount();
  await pressFind();
  expect(screen.getByText(FIND_COPY.keys)).toBeTruthy();
  expect(screen.queryByRole("button", { name: /^side by side with/ })).toBeNull();
  const first = screen.getByText("§ 5.A Invariant subspaces");
  first.focus();
  fireEvent.keyDown(first, { key: "s" });
  fireEvent.click(screen.getByRole("button", { name: "peek at Lay 5.1 Eigenvectors and eigenvalues" }));
  await flush();
  expect(screen.queryByRole("button", { name: FIND_COPY.readSideBySide })).toBeNull();
});

it("a peek and go there record CA5a's deferred events (salience only, ids only)", async () => {
  resetReaderActivityForTests();
  setReaderActivityEnabled(true);
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  api.readerCorrespondentPeek.mockResolvedValue(peekOf(LAY_51, ["An eigenvector…"]));
  await mount();
  await pressFind();
  fireEvent.click(screen.getByRole("button", { name: "peek at Lay 5.1 Eigenvectors and eigenvalues" }));
  await flush();
  fireEvent.click(screen.getByRole("button", { name: "go there: Axler 5.A Invariant subspaces" }));
  flushReaderActivity();
  const events = api.readerLogActivity.mock.calls.flatMap((call) => call[0].events);
  expect(events).toEqual([
    { kind: "reader_action_invoked", event: "corresponding_section_peeked", payload: {
      extraction_id: "ext_strang", section_id: SECTION.id, target_source_id: "src_lay", target_extraction_id: "ext_lay",
      target_section_id: "lay51", target_span_id: "l3", by: "search", via: "find_list" } },
    { kind: "reader_action_invoked", event: "corresponding_section_opened", payload: {
      extraction_id: "ext_strang", section_id: SECTION.id, target_source_id: "src_axler", target_extraction_id: "ext_axler",
      target_section_id: "ax5a", target_span_id: "a7", by: "search", via: "find_list" } },
  ]);
  resetReaderActivityForTests();
});
