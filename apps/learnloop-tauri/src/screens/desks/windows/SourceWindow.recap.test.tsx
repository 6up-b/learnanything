// A source window records recap_shown only when the card is on screen (spec §3.6): its rail is shown in a
// panel window that is itself visible. A preview, a window with no rail panel, or a hidden panel shows no
// card, so nothing is recorded as shown.
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { readerRenderViewFixture as view } from "../../../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../../../api/dto";
import { setAlgoConfig } from "../../../app/algoConfig";
import { resetReaderActivityForTests } from "../../reader/activity";
import { DIRECT_HUB, WindowScope, type WindowState } from "../lifecycle";
import { SourceWindow } from "./SourceWindow";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerLogActivity: vi.fn(),
  readerNoteReadingProgress: vi.fn(), readerMarkSectionProgress: vi.fn(), readerRecap: vi.fn(), readerRecapEvent: vi.fn(),
  readerWrapUp: vi.fn(),
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

const RECAP = {
  recapVersion: "rw6a-recap-v1", extractionId: view.extractionId,
  session: { sessionId: "v1", extractionId: view.extractionId, visitIds: ["v1"], startedAt: "2026-10-09T20:00:00Z", endedAt: "2026-10-09T20:40:00Z", minutes: 40 },
  continueAt: { sectionId: "u1", label: "Symmetric matrices" },
  stillOpen: [{ rootExchangeId: "r1", questionEventId: "q1", questionMd: "a project-authored open question", spanId: "span_symmetric_prose", anchorSpanIds: ["span_symmetric_prose"], openedAt: "2026-10-09T20:05:00Z" }],
  unfinished: [], worthASecondLook: [], sinceLastTime: { demonstrated: [], checksRetired: [] },
};

function Window({ state, panel }: { state: WindowState; panel: { host: HTMLElement; state: WindowState } | null }) {
  return (
    <WindowScope lifecycle={{ windowId: "w1", state }} hub={DIRECT_HUB}>
      <SourceWindow
        content={{ kind: "source", sourceId: view.sourceId, extractionId: view.extractionId }}
        card={card}
        libraryLoaded
        startSpan={null}
        railHost={panel ? { node: panel.host, tab: "guide", lifecycle: { windowId: "p1", state: panel.state }, hub: DIRECT_HUB } : null}
        onStatus={noop}
        onJumpReady={noop}
        onMediaReady={noop}
        onError={noop}
      />
    </WindowScope>
  );
}

function shownEvents(): number {
  return api.readerRecapEvent.mock.calls.filter(([input]) => (input as { event: string }).event === "recap_shown").length;
}

async function settle() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 20));
  });
}

let host: HTMLElement;

beforeEach(() => {
  vi.resetAllMocks();
  resetReaderActivityForTests();
  setAlgoConfig({ recap: { enabled: true, wrapUpEnabled: true } });
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerRecap.mockResolvedValue({ version: 1, recap: RECAP, dismissed: false });
  api.readerRecapEvent.mockResolvedValue({ version: 1, eventId: "ev", event: "recap_shown" });
  api.readerWrapUp.mockResolvedValue({ version: 1, wrapUpVersion: "rw6a-wrap-up-v1", available: false, extractionId: view.extractionId, session: null, resolved: [], stillOpen: [], worthReinforcing: [] });
  host = document.createElement("div");
  document.body.appendChild(host);
});
afterEach(() => {
  cleanup();
  host.remove();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

it("a preview with a recap records nothing as shown", async () => {
  render(<Window state="preview" panel={{ host, state: "preview" }} />);
  await screen.findByText(view.blocks[1].markdown);
  await settle();
  expect(api.readerRecap).toHaveBeenCalled();
  expect(shownEvents()).toBe(0);
});

it("an active window with no rail panel shows no card, so records none", async () => {
  render(<Window state="active" panel={null} />);
  await screen.findByText(view.blocks[1].markdown);
  await settle();
  expect(api.readerRecap).toHaveBeenCalled();
  expect(shownEvents()).toBe(0);
});

it("a rail panel that is hidden records none; once it is on screen the card is recorded once", async () => {
  const { rerender } = render(<Window state="active" panel={{ host, state: "hidden" }} />);
  await screen.findByText(view.blocks[1].markdown);
  await settle();
  expect(shownEvents()).toBe(0);
  rerender(<Window state="active" panel={{ host, state: "visible" }} />);
  await waitFor(() => expect(shownEvents()).toBe(1));
});
