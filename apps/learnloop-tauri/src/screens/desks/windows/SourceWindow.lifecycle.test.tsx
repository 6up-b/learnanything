// A source window is the Reader's source pane as one scoped instance (spec §3.6, §7.1): a preview logs
// no reading activity, an active window opens a visit, a window that leaves the view closes it, and the
// window shows the pane alone, its rail in the panel window it is given.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { readerRenderViewFixture as view } from "../../../fixtures/readerRenderView";
import type { ReaderActivityEvent, SourceLibraryCard } from "../../../api/dto";
import { flushReaderActivity, resetReaderActivityForTests } from "../../reader/activity";
import { DIRECT_HUB, WindowScope, type WindowState } from "../lifecycle";
import { SourceWindow } from "./SourceWindow";
import type { ReaderWindowing } from "../source/types";
import type { ListenerHub } from "../lifecycle";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerLogActivity: vi.fn(),
  readerNoteReadingProgress: vi.fn(), readerMarkSectionProgress: vi.fn(),
}));
vi.mock("../../../api/client", () => ({ api }));
vi.mock("../../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [card] }, error: null }) }));
vi.mock("../../reader/readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("../../reader/guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("../../reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const card = { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const noop = () => undefined;

function Window({ state, railHost = null }: { state: WindowState; railHost?: ReaderWindowing["railHost"] }) {
  return (
    <WindowScope lifecycle={{ windowId: "w1", state }} hub={DIRECT_HUB}>
      <SourceWindow
        content={{ kind: "source", sourceId: view.sourceId, extractionId: view.extractionId }}
        card={card}
        libraryLoaded
        startSpan={null}
        railHost={railHost}
        onStatus={noop}
        onJumpReady={noop}
        onMediaReady={noop}
        onError={noop}
      />
    </WindowScope>
  );
}

function logged(): ReaderActivityEvent[] {
  act(() => flushReaderActivity());
  return api.readerLogActivity.mock.calls.flatMap(([input]) => (input as { events: ReaderActivityEvent[] }).events);
}

beforeEach(() => {
  vi.resetAllMocks();
  resetReaderActivityForTests();
  Element.prototype.scrollIntoView = vi.fn();
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
});
afterEach(cleanup);

it("a preview opens no reading visit and logs nothing", async () => {
  render(<Window state="preview" />);
  await screen.findByText(view.blocks[1].markdown);
  expect(logged().map((event) => event.kind)).toEqual([]);
});

it("the same window, active, opens a visit; leaving the view closes it, and an offscreen window opens none", async () => {
  const { rerender } = render(<Window state="active" />);
  await screen.findByText(view.blocks[1].markdown);
  expect(logged().map((event) => event.kind)).toEqual(["reader_view_opened"]);
  rerender(<Window state="hidden" />);
  expect(logged().map((event) => event.kind)).toEqual(["reader_view_opened", "reader_view_closed"]);
  rerender(<Window state="offscreen" />);
  expect(logged().map((event) => event.kind)).toEqual(["reader_view_opened", "reader_view_closed"]);
});

it("shows the source pane alone: no Reader header, no key bar, no rail without a panel window", async () => {
  render(<Window state="active" />);
  await screen.findByText(view.blocks[1].markdown);
  expect(screen.queryByText("READER")).toBeNull();
  expect(screen.queryByText("← Library")).toBeNull();
  expect(screen.queryByRole("complementary")).toBeNull();
});

it("renders its rail into the panel window it is given, on that window's tab", async () => {
  const host = document.createElement("div");
  document.body.appendChild(host);
  render(<Window state="active" railHost={{ node: host, tab: "notes", lifecycle: { windowId: "p1", state: "visible" }, hub: DIRECT_HUB }} />);
  await screen.findByText(view.blocks[1].markdown);
  // Opening the source resets the rail to the Guide and the panel's tab is applied after, in an effect: under load
  // the first look can land between the two, so the check waits for the panel's tab.
  await waitFor(() => expect(host.querySelector('[role="complementary"]')?.getAttribute("aria-label")).toBe("Notes"));
  host.remove();
});

it("a tag menu portaled over the desks closes when its window stops being the active one", async () => {
  const { rerender } = render(<Window state="active" />);
  const block = await screen.findByText(view.blocks[1].markdown);
  act(() => {
    fireEvent.contextMenu(block, { clientX: 40, clientY: 40 });
  });
  expect(screen.getByText(/^tag .* as$/, { selector: "div" })).toBeTruthy();
  rerender(<Window state="hidden" />);
  expect(screen.queryByText(/^tag .* as$/, { selector: "div" })).toBeNull();
  // Back on its desk it does not reappear: it was closed, not hidden.
  rerender(<Window state="active" />);
  expect(screen.queryByText(/^tag .* as$/, { selector: "div" })).toBeNull();
});

it("the rail in a panel window lives in that panel's window scope (its lifecycle, hub and claims), not the source's", async () => {
  const host = document.createElement("div");
  document.body.appendChild(host);
  const panelHub: ListenerHub = { listen: (target, type, handler, options) => DIRECT_HUB.listen(target, type, handler, options) };
  // The source is active; its panel is not: the Wrap up's esc, the rail's cues and its timers belong to
  // the panel the learner sees them in.
  render(<Window state="active" railHost={{ node: host, tab: "guide", lifecycle: { windowId: "p1", state: "visible" }, hub: panelHub }} />);
  await screen.findByText(view.blocks[1].markdown);
  const rail = host.querySelector('[role="complementary"]') as HTMLElement;
  expect(rail).not.toBeNull();
  expect(rail.closest("[data-rail-window]")?.getAttribute("data-rail-window")).toBe("p1");
  expect(rail.closest("[data-rail-window]")?.getAttribute("data-rail-state")).toBe("visible");
  host.remove();
});
