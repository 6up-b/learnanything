// The desks' context menu in jsdom (spec §0 item 7, §9.1): one listener and one menu on a passage or a window header,
// the promoted rows asked per object, `.` on the hovered object, and the verbs that open windows or write a pad. Also
// the two layouts carried with it from the mockup: the shelf's TODAY · RUNNING PAD and a pad stack's title bar.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MenuObjectInput, PadOpDto, PassagePromotedDto, PromotedRowDto } from "../../api/dto";
import { FixtureDeskServer } from "../../fixtures/desks/workspace";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../fixtures/desks/sources";
import { Poller } from "../../api/poller";
import { useSyncExternalStore } from "react";
import { DeskShell, type MenuTransport, type PaneRenderInput } from "./DeskShell";
import { usePadsHost } from "./pads/host";
import { PadStackWindow } from "./pads/PadStackWindow";
import { openNotebookMenu } from "./notebook/menuBridge";

vi.mock("../../api/client", () => ({ api: {} }));
vi.mock("./windows/SourceWindow", () => ({ SourceWindow: () => null }));
vi.mock("./windows/PanelWindow", () => ({ PANEL_TITLES: { guide: "Guide", notes: "Notes", path: "Reading path", library: "Library" }, LibraryPanel: () => null, PathPanel: () => null, RailHostPanel: () => null }));

const paneMenus: string[] = [];

/** A pane with passages, and a right-click handler of its own standing for the Reader's old tag menu. */
function PassagePane({ input }: { input: PaneRenderInput }) {
  const id = input.window.windowId;
  // The lesson openings shown in this window (a stack's tabs in flight), read as a stack window would.
  const lessons = usePadsHost()?.lessons?.desk;
  useSyncExternalStore(lessons?.subscribe ?? (() => () => undefined), lessons?.getVersion ?? (() => 0));
  return (
    <div data-testid={`pane-${id}`} data-kind={input.window.content?.kind ?? input.window.kind} data-openings={lessons?.openingsFor(id).length ?? 0} onContextMenu={() => paneMenus.push(id)}>
      <p data-span-id={`${id}_s1`}>{`the first passage of ${id}`}</p>
      <p data-span-id={`${id}_s2`}>{`the second passage of ${id}`}</p>
    </div>
  );
}

const row = (rowId: string, label: string): PromotedRowDto => ({
  rowId, kind: "question", glyph: "?", label, reason: "you asked about this here", action: { verb: "open", ref: { kind: "thread", rootExchangeId: `q_${rowId}` } },
  learnerAt: null, checked: true, judgeRank: 0, basis: "union", extra: {},
} as unknown as PromotedRowDto);

function menuFakes() {
  const asked: MenuObjectInput[] = [];
  const labels: unknown[] = [];
  const transport: MenuTransport = {
    // Rows that differ by passage: the object's own union read.
    passagePromoted: vi.fn(async (input: MenuObjectInput) => {
      asked.push(input);
      const rows = input.spanId?.endsWith("_s1") ? [row("r1", "your question on the first passage")] : input.spanId?.endsWith("_s2") ? [row("r2", "your question on the second passage")] : [];
      return { version: 1, objectKey: JSON.stringify(input), rows, cap: 4, pendingJob: null, paid: false } as unknown as PassagePromotedDto;
    }),
    passagePromotedJob: vi.fn(async () => ({}) as never),
    passagePromotedCancel: vi.fn(async () => ({}) as never),
    proposalLabel: vi.fn(async (input) => {
      labels.push(input);
      return {};
    }),
    passageKnows: vi.fn(async () => ({ objectKey: "k", sourceIds: [], places: [] }) as never),
    readerCorrespondents: vi.fn(),
    readingIdentity: vi.fn(async () => ({ sourceId: FIXTURE_SOURCES.book.sourceId, revisionId: "rev1", renderViewId: "rv1" })),
    readerCapture: vi.fn(async () => ({ annotationId: "ann_new" }) as never),
    readerImportExercise: vi.fn(),
    readerAuthorSectionQuestion: vi.fn(),
  };
  return { transport, asked, labels };
}

function padsFakes(server: FixtureDeskServer) {
  return {
    transport: {
      padProposals: async (input: { padId: string }) => ({ version: 1, padId: input.padId, proposals: [] }),
      proposalLabel: async () => ({}),
      padSubmitBlock: async () => ({}) as never,
      carriedCarry: async () => ({ carried: {} as never, created: true }),
      requestTeachBack: async () => ({ practiceItemId: "tb" }),
      passageUnionRange: async () => ({ version: 1, extractionId: "", sections: [], spans: [] }) as never,
      authorPracticeItem: async () => ({ practiceItemId: "x" }),
      workbenchOpenProblems: async () => ({ problems: [] }),
      submitTeachBackTurn: async () => ({ done: true }) as never,
      getSession: async () => ({ checkpoint: null }) as never,
      passageContent: async () => ({ version: 1, extractionId: "", sourceId: null, title: null, withheld: false, spans: [] }) as never,
      padDrain: async ({ deskId }: { deskId: string }) => ({ version: 1, deskId, day: "2026-11-23", pads: [] }) as never,
      carriedList: async () => ({ carried: [], shelfLimit: 3 }),
      carriedMark: async () => ({}),
      figureRequest: async () => ({ jobId: "j", kind: "figure_build", askId: null, state: "done", result: { figure: null, reused: false } }) as never,
      readerFigureJob: async () => ({ jobId: "j", kind: "figure_build", askId: null, state: "done", result: null }) as never,
    },
    deskTransport: {
      state: async () => server.state(),
      apply: async (input: Parameters<FixtureDeskServer["apply"]>[0]) => server.apply(input),
      library: async () => FIXTURE_LIBRARY,
      resolveExtraction: async (sourceId: string) => Object.values(FIXTURE_SOURCES).find((source) => source.sourceId === sourceId)?.extractionId ?? sourceId,
      applyPad: async (input: Parameters<FixtureDeskServer["applyPad"]>[0]) => server.applyPad(input),
      padGet: async ({ padId }: { padId: string }) => server.padGet(padId),
    },
  };
}

let minted = 0;
function mount(options: { stacks?: boolean } = {}) {
  const server = new FixtureDeskServer();
  const menu = menuFakes();
  const pads = padsFakes(server);
  const vaultKey = `vault-${Math.random()}`;
  const poller = new Poller({ setInterval: () => 1, clearInterval: () => undefined });
  const onError = vi.fn();
  const ui = () => (
    <DeskShell
      vaultKey={vaultKey}
      onError={onError}
      transport={pads.deskTransport}
      padsTransport={pads.transport as never}
      menuTransport={menu.transport}
      poller={poller}
      renderPane={(input) => (options.stacks && input.window.kind === "pad_stack"
        ? <PadStackWindow windowId={input.window.windowId} stack={input.window.stack ?? []} view={input.window.view ?? {}} />
        : <PassagePane input={input} />)}
      initialViewport={{ width: 1600, height: 960 }}
      mintId={(prefix) => `${prefix}_${++minted}`}
    />
  );
  const view = render(ui());
  // The desks render again (their parent re-rendered): every inline prop is a new object.
  const again = () => view.rerender(ui());
  return { server, again, ...menu };
}

async function flush() {
  await act(async () => {
    vi.advanceTimersByTime(300);
    await Promise.resolve();
  });
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

const passage = (id: string) => document.querySelector(`[data-span-id="${id}"]`) as HTMLElement;
const menus = () => document.querySelectorAll(".desk-menu:not(.submenu)");

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  paneMenus.length = 0;
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
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("the desks' context menu", () => {
  it("a right-click on a passage opens one menu for it (the window's own menu stays shut) and asks its promoted rows", async () => {
    const { asked } = mount();
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(passage("fx_w_book_s1"), { clientX: 400, clientY: 300 });
    expect(menus()).toHaveLength(1);
    expect(paneMenus).toEqual([]);
    expect(screen.getByText("a passage · “the first passage of fx_w_book”")).toBeTruthy();
    await screen.findByText("your question on the first passage");
    expect(asked[0]).toEqual({ objectKind: "passage", extractionId: FIXTURE_SOURCES.book.extractionId, spanId: "fx_w_book_s1", windowId: "fx_w_book", deskId: "fx_desk_softmax" });
    const verbs = [...menus()[0].querySelectorAll(":scope > .mi .t")].map((each) => each.firstChild?.textContent);
    expect(verbs).toEqual(["Ask", "Note in margin", expect.stringMatching(/^Append to “/), "Carry", "Open beside", "Find in my sources", "Compare", "Show me", "Make it practice", "Teach me this", "What this knows"]);
  });

  it("the menu asks its rows once and keeps its judged job while the desks re-render around it", async () => {
    const { transport, again } = mount();
    (transport.passagePromoted as ReturnType<typeof vi.fn>).mockImplementation(async (input: MenuObjectInput) =>
      ({ version: 1, objectKey: JSON.stringify(input), rows: [row("r1", "a cheap row")], cap: 4, pendingJob: { jobId: "job1" }, paid: false }) as unknown as PassagePromotedDto);
    (transport.passagePromotedJob as ReturnType<typeof vi.fn>).mockImplementation(async () => ({ version: 1, jobId: "job1", status: "running", done: false, rows: [], error: null }));
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    await screen.findByText("a cheap row");
    // The desks re-render (their parent, a toast, the outbox): the open menu is the same menu.
    for (let i = 0; i < 3; i += 1) {
      again();
      await flush();
    }
    expect(transport.passagePromoted).toHaveBeenCalledTimes(1);
    expect(transport.passagePromotedCancel).not.toHaveBeenCalled();
    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() => expect(transport.passagePromotedCancel).toHaveBeenCalledWith({ jobId: "job1" }));
  });

  it("the promoted rows differ by passage", async () => {
    mount();
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    await screen.findByText("your question on the first passage");
    fireEvent.keyDown(window, { key: "Escape" });
    expect(menus()).toHaveLength(0);
    fireEvent.contextMenu(passage("fx_w_book_s2"));
    await screen.findByText("your question on the second passage");
    expect(screen.queryByText("your question on the first passage")).toBeNull();
  });

  it("a dismissed row is labelled on its row id as a promoted row", async () => {
    const { labels } = mount();
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    const promoted = (await screen.findByText("your question on the first passage")).closest("button") as HTMLElement;
    fireEvent.click(within(promoted).getByLabelText("dismiss"));
    await waitFor(() => expect(labels).toEqual([expect.objectContaining({ proposalKind: "promoted_row", proposalId: "r1", label: "dismiss" })]));
    expect(screen.queryByText("your question on the first passage")).toBeNull();
  });

  it("a right-click on a window header opens the window's menu", async () => {
    mount();
    await screen.findByTestId("pane-fx_w_book");
    const head = document.querySelector('[data-desk-window="fx_w_book"] .desk-pane-head') as HTMLElement;
    fireEvent.contextMenu(head);
    expect(menus()).toHaveLength(1);
    const verbs = [...menus()[0].querySelectorAll(":scope > .mi .t")].map((each) => each.firstChild?.textContent);
    expect(verbs).toEqual(["New desk from these", "Gather linked sources", "Share a slot with the next", "Own slot", "What this knows"]);
    expect(menus()[0].querySelector(".mh")?.textContent).toMatch(/^a window · “/);
  });

  it("`.` opens the menu on the hovered passage, through the key router", async () => {
    const { asked } = mount();
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.mouseOver(passage("fx_w_book_s2"));
    fireEvent.keyDown(window, { key: "." });
    expect(menus()).toHaveLength(1);
    await screen.findByText("your question on the second passage");
    expect(asked[0]).toMatchObject({ spanId: "fx_w_book_s2" });
    // The open menu owns the keyboard: `.` again does not open a second one.
    fireEvent.keyDown(window, { key: "." });
    expect(menus()).toHaveLength(1);
  });

  it("Teach me opens a lesson as a tab of the desk's stack (its opening shows there and the stack takes the focus)", async () => {
    mount();
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    fireEvent.keyDown(window, { key: "t" });
    expect(menus()).toHaveLength(0);
    await waitFor(() => expect(screen.getByTestId("pane-fx_w_pads").getAttribute("data-openings")).toBe("1"));
    await flush();
    expect(document.querySelector(".desk-window.focus [data-desk-window]")?.getAttribute("data-desk-window")).toBe("fx_w_pads");
  });

  it("Append writes the passage as a quote in the running pad, linked both ways (the passage highlighted)", async () => {
    const { transport, server } = mount();
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    fireEvent.click(screen.getByText(/^Append to “/));
    const submenu = screen.getByRole("menu", { name: "append to" });
    fireEvent.click(within(submenu).getAllByRole("menuitem")[0]);
    await waitFor(() => expect(transport.readerCapture).toHaveBeenCalledWith(expect.objectContaining({ action: "highlight", extractionId: FIXTURE_SOURCES.book.extractionId })));
    await flush();
    await flush();
    const ops = server.padBatches.flatMap((batch) => batch.ops as PadOpDto[]);
    const quote = ops.find((op) => op.op === "insert_block") as Extract<PadOpDto, { op: "insert_block" }> | undefined;
    expect(quote).toMatchObject({ kind: "source_quote", provenance: "source", bodyMd: "the first passage of fx_w_book" });
    expect(ops.find((op) => op.op === "link_anchor")).toMatchObject({ blockId: quote?.blockId, spanId: "fx_w_book_s1", annotationId: "ann_new" });
    expect(server.padBatches.find((batch) => (batch.ops as PadOpDto[]).some((op) => op.op === "insert_block"))?.padId).toBe("fx_pad_running");
  });
});

describe("the shelf's running pad and the pad stack's title bar, as the mockup has them", () => {
  it("TODAY · RUNNING PAD shows the running pad's last three blocks of today, each marked by where it came from", async () => {
    vi.setSystemTime(new Date(2026, 10, 23, 12, 0, 0));
    mount();
    await screen.findByTestId("pane-fx_w_book");
    const today = await waitFor(() => {
      const found = document.querySelector("[data-shelf-today]") as HTMLElement | null;
      expect(found?.querySelectorAll(".runmini")).toHaveLength(3);
      return found as HTMLElement;
    });
    expect(today.querySelector("h4")?.textContent).toBe("today · running padopen");
    // Above CARRIED, in the shelf's lower part.
    expect(today.closest(".lower")).toBeTruthy();
    const marks = [...today.querySelectorAll(".runmini .rm")].map((each) => each.textContent);
    expect(marks).toEqual(["◇ fig", "§", "›"]);
    fireEvent.click(within(today).getByRole("button", { name: "open" }));
    await flush();
    expect(document.querySelector(".desk-window.focus [data-desk-window]")?.getAttribute("data-desk-window")).toBe("fx_w_pads");
  });

  it("a pad stack's title bar reads Scratchpads ⓘ yours, its ⓘ opening where your words go", async () => {
    mount();
    await screen.findByTestId("pane-fx_w_book");
    const head = await waitFor(() => {
      const found = document.querySelector('[data-desk-window="fx_w_pads"] .desk-pane-head') as HTMLElement | null;
      expect(found).toBeTruthy();
      return found as HTMLElement;
    });
    expect(head.querySelector(".t")?.textContent).toBe("Scratchpads");
    const info = within(head).getByRole("button", { name: "where your words go" });
    expect(info.textContent).toBe("ⓘ");
    expect(head.querySelector(".loc")?.textContent).toBe("yours");
    expect([...head.children].map((child) => child.className)).toEqual(expect.arrayContaining(["t", "emi pinfo", "loc"]));
    expect(info.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(info);
    expect(info.getAttribute("aria-expanded")).toBe("true");
  });

  it("a notebook frame's right-click opens the pad menu in the stack that shows the notebook's pad", async () => {
    mount({ stacks: true });
    await screen.findByTestId("pane-fx_w_book");
    await waitFor(() => expect(document.querySelector('[data-desk-window="fx_w_pads"] [data-pad="fx_pad_running"]')).toBeTruthy());
    let opened = false;
    act(() => {
      opened = openNotebookMenu({ owner: "pad:fx_pad_running", padId: "fx_pad_running", lessonId: null, text: "x = 1", x: 300, y: 300,
        label: "your pad", insertLabel: "insert at the end of this pad" });
    });
    expect(opened).toBe(true);
    await flush();
    // The stack that shows the pad took the focus (a press inside a frame never reaches the desks).
    expect(document.querySelector(".desk-window.focus [data-desk-window]")?.getAttribute("data-desk-window")).toBe("fx_w_pads");
    const menu = await screen.findByRole("menu", { name: "the pad menu" });
    expect(within(menu).getByText("your pad · “x = 1”")).toBeTruthy();
    expect(within(menu).getByText("marimo cell")).toBeTruthy();
  });
});
