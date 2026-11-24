// An open inline check holds everything on the desks it does not list as safe (spec §12.6.3; the RD7 review's class
// of misses: an allowlist of known attributes missed a surface each time). DeskShell end to end, with a book window
// standing in as a page of every kind of surface a source window can show: a passage the check covers and one it does
// not, a "your note" mark and its open panel, the original PDF's canvas, the side-by-side pane, a tooltip no one
// listed. The other direction too: the question stays readable and the answer box typeable.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { CheckCardDto, CheckVeilRefDto } from "../../../api/dto";
import { FixtureDeskServer } from "../../../fixtures/desks/workspace";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { DeskShell, type CompanionTransport, type DeskTransport, type PadsTransport } from "../DeskShell";
import type { GoalTransport } from "../goal/controller";
import type { CheckTransport } from "./controller";

vi.mock("../../../api/client", () => ({ api: {} }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

const { book } = FIXTURE_SOURCES;
const COVERED = `${book.extractionId}_s5_1`;
const PLAIN = `${book.extractionId}_s1_1`;
const LATE = `${book.extractionId}_s2_1`;
const ANSWER = "the gradient is p minus one-hot";

// The book window's page: whatever a source window can render, in the shapes the Reader renders them.
let late = false;
vi.mock("../windows/SourceWindow", () => ({
  SourceWindow: (props: { content: { kind: string; extractionId: string }; lens?: { before?: (span: string) => unknown } | null }) => {
    if (props.content.kind !== "source" || props.content.extractionId !== book.extractionId) return <div />;
    return (
      <div data-testid="book">
        {props.lens?.before?.(COVERED) as never}
        <div data-span-id={COVERED}><div data-passage-text="">{ANSWER}</div></div>
        <div data-span-id={PLAIN} title={`a tooltip quoting ${ANSWER}`}>
          <button type="button" data-note-mark={PLAIN} aria-label={`your note: ${ANSWER}`}>›</button>
          <div data-note-mark-panel={PLAIN}>my note says {ANSWER}</div>
          <div data-passage-text="">softmax turns scores into probabilities</div>
        </div>
        {late ? <div data-span-id={LATE}><div data-passage-text="">a passage that arrived later</div></div> : null}
        <div data-pdf-page=""><canvas data-testid="pdf-canvas" width={10} height={10} /></div>
        <div data-sbs-pane=""><p data-sbs-span="x_1">{ANSWER} in the second book</p></div>
        <div className="some-new-panel" aria-label={ANSWER}>a panel nobody listed: {ANSWER}</div>
      </div>
    );
  },
}));
vi.mock("../windows/PanelWindow", () => ({ PANEL_TITLES: { guide: "Guide", notes: "Notes", path: "Reading path", library: "Library" }, LibraryPanel: () => null, PathPanel: () => null, RailHostPanel: () => null }));

function deskTransport(server: FixtureDeskServer): DeskTransport {
  return {
    state: async () => server.state(),
    apply: async (input) => server.apply(input),
    applyPad: async (input) => server.applyPad(input),
    padGet: async ({ padId }) => server.padGet(padId),
    library: async () => FIXTURE_LIBRARY,
    resolveExtraction: async (sourceId: string) => Object.values(FIXTURE_SOURCES).find((source) => source.sourceId === sourceId)?.extractionId ?? sourceId,
  } as DeskTransport;
}

const quietGoal = { goals: async () => ({ version: 1, goals: [] }) } as unknown as GoalTransport;
const quietCompanion = { companionHistory: async () => ({ version: 1, days: [], cursor: null }) } as unknown as CompanionTransport;
const quietPads = {
  padProposals: async (input: { padId: string }) => ({ version: 1, padId: input.padId, proposals: [] }),
  padDrain: async () => ({ version: 1, pads: [] }),
  carriedList: async () => ({ carried: [], shelfLimit: 3 }),
  carriedMark: async () => ({}),
  passageUnionRange: async () => ({ version: 1, extractionId: "", spans: [], sections: [] }),
} as unknown as PadsTransport;

const SPAN_VEIL: CheckVeilRefDto = { group: "source passages", kind: "span", window_id: "fx_w_book", extraction_id: book.extractionId, span_id: COVERED, measured: true };

function openCard(): CheckCardDto {
  return {
    administrationToken: "cad_open", commitmentId: "cm_1", itemRef: "pi_1", contractHash: "h", cold: true, state: "open",
    protection: { veilSetId: "v1", method: "structural", groups: ["source passages"], opened: [], veiled: [SPAN_VEIL] },
    prompt: { prompt: "What is the gradient of the loss?" }, submissionId: null, eligibility: null, revision: 1,
    host: { extractionId: book.extractionId, sectionId: "s5", spanId: COVERED },
  };
}

let mintCount = 0;
const mint = (prefix: string) => `${prefix}_${++mintCount}`;

function mount(over: Partial<CheckTransport> = {}) {
  const server = new FixtureDeskServer();
  const checkTransport: CheckTransport = {
    dueFor: vi.fn(async () => ({ version: 1, checks: [{ handle: "chk_due_1" }] })),
    begin: vi.fn(async () => openCard()),
    protectMore: vi.fn(async () => ({ veilAdditions: [], standing: [SPAN_VEIL], revision: 1 })),
    expose: vi.fn(async () => ({ protectionStatus: { exposure: [], coldNow: false, measured: false } })),
    submit: vi.fn(async () => ({ administrationToken: "cad_open", attemptId: "at_1", cold: true, reason: "on_your_own" as const })),
    abandon: vi.fn(async () => ({})),
    openInline: vi.fn(async () => ({ administration: openCard() })),
    ...over,
  };
  const view = render(
    <DeskShell vaultKey={`vault-hold-${Math.random()}`} onError={vi.fn()} transport={deskTransport(server)} initialViewport={{ width: 1600, height: 960 }}
      mintId={mint} goalTransport={quietGoal} companion={quietCompanion} padsTransport={quietPads} checkTransport={checkTransport}
      reader={{ workbench: { practiceSessionId: "s_1", onPracticeSession: vi.fn() } } as never} />,
  );
  return { server, checkTransport, view };
}

/** Whether nothing of this element can be read, reached or announced: it, or something around it, is held. */
function held(element: Element | null): boolean {
  if (!element) return false;
  const around = element.closest(".ck-held, .ck-veiled");
  return Boolean(around && around.hasAttribute("inert") && around.getAttribute("aria-hidden") === "true");
}

/** The words a reader or a screen reader could find outside what is held: text, titles and labels. */
function exposedWords(): string {
  const words: string[] = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const element = node as Element;
    if (element.closest("[inert], [aria-hidden='true']")) continue;
    for (const name of ["title", "aria-label", "alt", "placeholder"]) {
      const value = element.getAttribute(name);
      if (value) words.push(value);
    }
    for (const child of element.childNodes) if (child.nodeType === Node.TEXT_NODE) words.push(child.textContent ?? "");
  }
  return words.join(" ");
}

beforeEach(() => {
  late = false;
  vi.useFakeTimers({ shouldAdvanceTime: true });
  const values = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => void values.set(key, value),
    removeItem: (key: string) => void values.delete(key),
    clear: () => values.clear(),
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function openedAfterRestart() {
  const mounted = mount();
  await waitFor(() => expect(document.querySelector('[data-check-card]')).toBeTruthy());
  await screen.findByTestId("book");
  // The protect request for what the restart's page shows has been answered.
  await waitFor(() => expect(mounted.checkTransport.protectMore).toHaveBeenCalled());
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 20)); });
  return mounted;
}

describe("an open check holds every surface it does not list as safe", () => {
  it("holds a note's mark and its open panel, the PDF's canvas, the side-by-side pane and a panel no one listed, with their labels off", async () => {
    await openedAfterRestart();
    await waitFor(() => expect(held(document.querySelector("[data-note-mark]"))).toBe(true));
    expect(held(document.querySelector("[data-note-mark-panel]"))).toBe(true);
    expect(held(screen.getByTestId("pdf-canvas"))).toBe(true);
    expect(held(document.querySelector("[data-sbs-span]"))).toBe(true);
    expect(held(document.querySelector(".some-new-panel"))).toBe(true);
    expect(held(document.querySelector(`[data-span-id="${COVERED}"]`))).toBe(true);
    // Nothing a reader or a screen reader can reach says the answer: not a text, a title or a label.
    expect(exposedWords()).not.toContain(ANSWER);
  });

  it("leaves the question readable, the answer box typeable, an uncovered passage's own words and the window's head", async () => {
    await openedAfterRestart();
    await waitFor(() => expect(held(document.querySelector("[data-note-mark]"))).toBe(true));
    const plain = document.querySelector(`[data-span-id="${PLAIN}"] [data-passage-text]`)!;
    expect(held(plain)).toBe(false);
    expect(exposedWords()).toContain("softmax turns scores into probabilities");
    const card = document.querySelector("[data-check-card]")!;
    expect(held(card)).toBe(false);
    expect(card.textContent).toContain("What is the gradient of the loss?");
    const box = screen.getByLabelText("your answer") as HTMLTextAreaElement;
    expect(box.disabled).toBe(false);
    expect(box.closest("[inert]")).toBeNull();
    fireEvent.change(box, { target: { value: "p - y" } });
    expect(box.value).toBe("p - y");
    // A pad's head says only what the window is.
    const head = document.querySelector('[data-desk-window="fx_w_pads"] .desk-pane-head')!;
    expect(held(head)).toBe(false);
    expect(head.querySelector(".t")!.textContent).toBe("Pads");
  });

  it("holds a passage the server has not judged (after a restart, or newly arrived) until a reply covers it", async () => {
    let answer!: (value: { veilAdditions: CheckVeilRefDto[]; standing: CheckVeilRefDto[]; revision: number }) => void;
    const pending = new Promise<{ veilAdditions: CheckVeilRefDto[]; standing: CheckVeilRefDto[]; revision: number }>((resolve) => { answer = resolve; });
    late = true;
    const { checkTransport } = mount({ protectMore: vi.fn(() => pending) });
    await screen.findByTestId("book");
    await waitFor(() => expect(checkTransport.protectMore).toHaveBeenCalled());
    const arrived = document.querySelector(`[data-span-id="${LATE}"] [data-passage-text]`)!;
    await waitFor(() => expect(held(arrived)).toBe(true));
    expect(exposedWords()).not.toContain("a passage that arrived later");
    await act(async () => { answer({ veilAdditions: [], standing: [SPAN_VEIL], revision: 2 }); await pending; });
    await waitFor(() => expect(held(arrived)).toBe(false));
    expect(held(document.querySelector(`[data-span-id="${COVERED}"]`))).toBe(true);
  });

  it("nothing of the desks shows before the restart read answers, and a failed read offers to read again", async () => {
    let fail = true;
    const { checkTransport } = mount({ openInline: vi.fn(async () => {
      if (fail) throw { code: "internal", message: "sidecar down" };
      return { administration: openCard() };
    }) });
    await waitFor(() => expect(document.querySelector('[data-check-recovery="failed"]')).toBeTruthy());
    expect(screen.queryByTestId("book")).toBeNull();
    expect(document.body.textContent).toContain("couldn't tell whether a check is open on your desks");
    fail = false;
    fireEvent.click(screen.getByRole("button", { name: "try again" }));
    await waitFor(() => expect(document.querySelector('[data-check-card]')).toBeTruthy());
    expect(checkTransport.openInline).toHaveBeenCalledTimes(2);
  });

  it("the menu waits, says why, and shows nothing of its target", async () => {
    await openedAfterRestart();
    await waitFor(() => expect(held(document.querySelector("[data-note-mark]"))).toBe(true));
    fireEvent.contextMenu(document.querySelector(`[data-span-id="${PLAIN}"] [data-passage-text]`)!);
    await waitFor(() => expect(document.querySelector(".desk-toast")?.textContent).toBe("the menu waits · after your check · it is open on this desk"));
    expect(held(document.querySelector(".desk-toast"))).toBe(false);
    expect(document.querySelector(".desk-menu, [role='menu']")).toBeNull();
  });

  it("show it anyway on a region no one described says it counts as practice, then records it before the hold lifts", async () => {
    const { checkTransport } = await openedAfterRestart();
    await waitFor(() => expect(document.querySelector('[data-veil-region="window:fx_w_book"]')).toBeTruthy());
    fireEvent.click(document.querySelector('[data-veil-region="window:fx_w_book"]')!);
    expect(screen.getByRole("dialog", { name: "show it anyway?" }).textContent).toContain("opening it makes this answer count as practice");
    expect(checkTransport.expose).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("show it"));
    await waitFor(() => expect(checkTransport.expose).toHaveBeenCalledWith(expect.objectContaining({ kind: "left", ref: expect.objectContaining({ kind: "surface", window_id: "fx_w_book" }) })));
    await waitFor(() => expect(held(document.querySelector(".some-new-panel"))).toBe(false));
    // The passage the server veils stays veiled.
    expect(held(document.querySelector(`[data-span-id="${COVERED}"]`))).toBe(true);
  });
});
