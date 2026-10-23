// UX Phase 2 fix round 6 (the orchestrator's verify of fcb9e4beb): round 5
// gave the simple frame body tabIndex -1 and moved the focus there after a
// pointer click on a chrome control. A focusable `main` also took the focus on
// every click on plain content, and the Reader's intent box then ignored the
// next key (its target was `main`: neither the body nor inside its host), and
// keyboard scrolling stopped. Now the frame body is not focusable, and a
// pointer click on a chrome control only lets go of the focus, which returns
// to the body as in base. Here the real Reader, inside the real simple frame
// and chrome root: after a pointer click on a place the focus is on the body,
// and the intent box takes the first printable key.
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerInvokePreset: vi.fn(), readerCapture: vi.fn(), readerActiveQuestion: vi.fn(), readerActiveQuestionStatus: vi.fn(),
    readerSetMode: vi.fn(),
  },
  contract: { value: {} as Record<string, unknown> },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({
  getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn(), isMaximized: async () => false, onResized: async () => () => undefined })
}));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? contract.value : { sources: [source.card] }, error: null }) }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const BOX = "What do you want to do with this?";

function routed(action: string, extra: Record<string, unknown> = {}) {
  const found = intent.palette.flatMap((g) => g.actions).find((a) => a.id === action)!;
  return {
    state: "done", routingId: `r_${action}`, speculative: false, action, status: "routed", reason: null,
    intention: found.intention, group: found.group, label: found.label, effect: found.effect, latencyMs: 900, ...extra,
  };
}

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

async function openBox() {
  const result = render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  const box = await screen.findByRole("textbox", { name: BOX });
  return { result, block, box: box as HTMLInputElement };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 } };
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerIntentOutcome.mockResolvedValue({ routingId: "r", recorded: true });
  api.readerSetMode.mockResolvedValue({ mode: "skim" });
  api.readerInvokePreset.mockResolvedValue({ annotationId: "ann_1", anchorStatus: "exact", arc: null });
  api.readerAsk.mockResolvedValue({ eventId: "q", readerAnswerEventId: "a", parentExchangeId: null, answerMd: "Landed answer", answerMode: "help_me_reason", citations: [], manifest: {} });
});
afterEach(() => { cleanup(); vi.useRealTimers(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));

import { TerminalFrame } from "../../components/ui";
import { ShellChromeRoot } from "../../app/ShellChromeRoot";

function inSimpleFrame(children: ReactNode) {
  return (
    <ShellChromeRoot>
      <TerminalFrame
        shell="simple"
        active="reader"
        onTab={() => undefined}
        aiReady={false}
        vaultRoot="/vault"
        onSelectVault={() => undefined}
        simpleNav={{
          active: "reader",
          onPlace: () => undefined,
          onPalette: () => undefined,
          onSettings: () => undefined,
          onUnderTheHood: () => undefined,
          onKeyboardHelp: () => undefined
        }}
      >
        {children}
      </TerminalFrame>
    </ShellChromeRoot>
  );
}

function place(name: string): HTMLElement {
  return within(screen.getByRole("navigation", { name: "Places" })).getByRole("button", { name });
}

it("the simple frame body is not focusable", () => {
  render(inSimpleFrame(<div>body</div>));
  const main = document.querySelector("main.frame-body") as HTMLElement;
  expect(main.hasAttribute("tabindex")).toBe(false);
  expect(main.tabIndex).toBe(-1); // jsdom's default for a non-focusable element
});

it("a pointer click on a place lets go of the focus: it returns to the body", async () => {
  render(inSimpleFrame(<div>body</div>));
  const today = place("Today");
  await act(async () => {
    today.focus();
    fireEvent.click(today, { detail: 1 });
  });
  expect(document.activeElement).toBe(document.body);
  // A keyboard activation (detail 0) keeps the focus on the control.
  await act(async () => {
    today.focus();
    fireEvent.click(today, { detail: 0 });
  });
  expect(document.activeElement).toBe(today);
});

it("after a pointer click on a place, the intent box takes the first printable key", async () => {
  render(inSimpleFrame(<ReaderScreen initialSource={source} onError={vi.fn()} />));
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  const box = (await screen.findByRole("textbox", { name: BOX })) as HTMLInputElement;
  const reader = place("Reader");
  await act(async () => {
    reader.focus();
    fireEvent.click(reader, { detail: 1 });
  });
  expect(document.activeElement).toBe(document.body);
  await act(async () => {
    fireEvent.keyDown(document.activeElement as HTMLElement, { key: "w" });
  });
  expect(document.activeElement).toBe(box);
  expect(box.value).toBe("w");
});
