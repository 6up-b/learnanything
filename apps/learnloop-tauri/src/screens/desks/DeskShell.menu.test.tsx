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
import { api } from "../../api/client";
import { COMPANION_FIGURE_COPY, resetCompanionFiguresForTests } from "./companion/companionFigures";

// No inline check is open (the desks read it before showing anything).
vi.mock("../../api/client", () => ({ api: { checkOpenInline: async () => ({ administration: null }) } }));
vi.mock("./windows/SourceWindow", () => ({ SourceWindow: () => null }));
vi.mock("./windows/PanelWindow", () => ({ PANEL_TITLES: { guide: "Guide", notes: "Notes", path: "Reading path", library: "Library" }, LibraryPanel: () => null, PathPanel: () => null, RailHostPanel: () => null }));

const paneMenus: string[] = [];

/** A pane with passages, and a right-click handler of its own standing for the Reader's old tag menu. */
function PassagePane({ input }: { input: PaneRenderInput }) {
  const id = input.window.windowId;
  // The lesson openings shown in this window (a stack's tabs in flight), read as a stack window would.
  const host = usePadsHost();
  const lessons = host?.lessons?.desk;
  useSyncExternalStore(lessons?.subscribe ?? (() => () => undefined), lessons?.getVersion ?? (() => 0));
  return (
    <div data-testid={`pane-${id}`} data-kind={input.window.content?.kind ?? input.window.kind} data-openings={lessons?.openingsFor(id).length ?? 0} onContextMenu={() => paneMenus.push(id)}>
      {host?.teachMe ? <button type="button" data-testid={`teach-${id}`} onClick={() => host.teachMe?.(FIXTURE_SOURCES.book.extractionId, [`${id}_s1`])}>teach</button> : null}
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
      return { version: 1, objectKey: JSON.stringify(input), rows, cap: 4, pendingJob: null, paid: false, withheld: false } as unknown as PassagePromotedDto;
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
    readerExerciseImportStatus: vi.fn(async () => ({ status: "running" }) as never),
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
function mount(options: { stacks?: boolean; pads?: (pads: ReturnType<typeof padsFakes>) => void } = {}) {
  const server = new FixtureDeskServer();
  const menu = menuFakes();
  const pads = padsFakes(server);
  options.pads?.(pads);
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
  return { server, again, poller, ...menu };
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
  resetCompanionFiguresForTests();
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
    expect(await screen.findByText("a passage · “the first passage of fx_w_book”")).toBeTruthy();
    await screen.findByText("your question on the first passage");
    expect(asked[0]).toEqual({ objectKind: "passage", extractionId: FIXTURE_SOURCES.book.extractionId, spanId: "fx_w_book_s1", windowId: "fx_w_book", deskId: "fx_desk_softmax",
      requestId: expect.stringMatching(/^prom_/) });
    const verbs = [...menus()[0].querySelectorAll(":scope > .mi .t")].map((each) => each.firstChild?.textContent);
    expect(verbs).toEqual(["Ask", "Note in margin", expect.stringMatching(/^Append to “/), "Save for later", "Open beside", "Find in my sources", "Compare", "Show me", "Make it practice", "Teach me this", "What this knows"]);
  });

  it("the menu asks its rows once and keeps its judged job while the desks re-render around it", async () => {
    const { transport, again } = mount();
    (transport.passagePromoted as ReturnType<typeof vi.fn>).mockImplementation(async (input: MenuObjectInput) =>
      ({ version: 1, objectKey: JSON.stringify(input), rows: [row("r1", "a cheap row")], cap: 4, pendingJob: { jobId: "job1" }, paid: false, withheld: false }) as unknown as PassagePromotedDto);
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
    fireEvent.click(within(promoted).getByLabelText("hide this suggestion"));
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
    await waitFor(() => expect(menus()[0].querySelector(".mh")?.textContent).toMatch(/^a window · “/));
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
    await waitFor(() => expect(menus()).toHaveLength(0));
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

  it("a pad stack's title bar reads Pads ⓘ yours, its ⓘ opening where your words go", async () => {
    mount();
    await screen.findByTestId("pane-fx_w_book");
    const head = await waitFor(() => {
      const found = document.querySelector('[data-desk-window="fx_w_pads"] .desk-pane-head') as HTMLElement | null;
      expect(found).toBeTruthy();
      return found as HTMLElement;
    });
    expect(head.querySelector(".t")?.textContent).toBe("Pads");
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
    expect(within(menu).getByText("your pad")).toBeTruthy();
    expect(menu.textContent).not.toContain("x = 1");
    expect(within(menu).getByText("Python cell")).toBeTruthy();
  });
});

describe("RD5 fix round: the menu's rows and actions", () => {
  const corr = (rowId: string, source: { sourceId: string; extractionId: string }): PromotedRowDto => ({
    rowId, kind: "correspondent", glyph: "§", label: `elsewhere ${rowId}`, reason: "treats it too", learnerAt: null, checked: true, judgeRank: 1, basis: "judged", extra: {},
    action: { verb: "open", ref: { kind: "source", sourceId: source.sourceId, extractionId: source.extractionId }, target: {} },
  } as unknown as PromotedRowDto);

  it("a closed menu's late answer never reaches the next menu: Open beside opens the open menu's correspondent", async () => {
    const { transport, server } = mount();
    let answerA: (found: PassagePromotedDto) => void = () => undefined;
    (transport.passagePromoted as ReturnType<typeof vi.fn>).mockImplementation((input: MenuObjectInput) => (input.spanId?.endsWith("_s1")
      ? new Promise<PassagePromotedDto>((resolve) => { answerA = resolve; })
      : Promise.resolve({ version: 1, objectKey: "b", rows: [corr("rb", FIXTURE_SOURCES.paper)], cap: 4, pendingJob: null, paid: false, withheld: false } as unknown as PassagePromotedDto)));
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    fireEvent.keyDown(window, { key: "Escape" });
    fireEvent.contextMenu(passage("fx_w_book_s2"));
    await screen.findByText("elsewhere rb");
    await act(async () => {
      answerA({ version: 1, objectKey: "a", rows: [corr("ra", FIXTURE_SOURCES.video2)], cap: 4, pendingJob: null, paid: false, withheld: false } as unknown as PassagePromotedDto);
      await Promise.resolve();
    });
    fireEvent.keyDown(window, { key: "b" });
    await flush();
    const desk = server.state().desks.find((each) => each.deskId === "fx_desk_softmax");
    expect(desk?.focusWindowId).toBe("fx_w_paper");
    expect(desk?.slots.flatMap((slot) => slot.windows).some((window) => window.content?.kind === "video" && (window.content as { sourceId: string }).sourceId === FIXTURE_SOURCES.video2.sourceId)).toBe(false);
  });

  it("a pad row opens its pad at its line (the line flashes), a note's row opens its passage, and a pad line's gap row opens What this knows of that line", async () => {
    const { transport } = mount({ stacks: true });
    const flashed: string[] = [];
    const onFlash = (event: Event) => flashed.push((event as CustomEvent<{ blockId: string }>).detail.blockId);
    window.addEventListener("learnloop:pad-flash", onFlash);
    const rowOf = (rowId: string, label: string, action: Record<string, unknown>): PromotedRowDto => ({ rowId, kind: "your_words", glyph: "›", label, reason: "r", action, learnerAt: null, checked: null, judgeRank: 0, basis: "union", extra: {} } as unknown as PromotedRowDto);
    (transport.passagePromoted as ReturnType<typeof vi.fn>).mockImplementation(async (input: MenuObjectInput) => ({ version: 1, objectKey: "k", cap: 4, pendingJob: null, paid: false, withheld: false,
      rows: input.objectKind === "pad_line"
        ? [rowOf("rg", "a gap row", { verb: "knows", gapId: "g1" })]
        : [rowOf("rp", "your pad line", { verb: "open", ref: { kind: "pad", padId: "fx_pad_running" }, target: { blockId: "fx_b_r2" } }), rowOf("rn", "your margin note", { verb: "annotation", annotationId: "a1" })] }) as unknown as PassagePromotedDto);
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    fireEvent.click(await screen.findByText("your pad line"));
    await flush();
    expect(flashed).toEqual(["fx_b_r2"]);
    expect(document.querySelector(".desk-window.focus [data-desk-window]")?.getAttribute("data-desk-window")).toBe("fx_w_pads");
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    fireEvent.click(await screen.findByText("your margin note"));
    await flush();
    expect(document.querySelector(".desk-window.focus [data-desk-window]")?.getAttribute("data-desk-window")).toBe("fx_w_book");
    // A pad line's own menu: its gap row opens What this knows of the line (the source menu is not open).
    await waitFor(() => expect(document.querySelector('[data-desk-window="fx_w_pads"] [data-block="fx_b_r1"]')).toBeTruthy());
    // A right-click's press focuses the window first (the pad menu belongs to the active window).
    const line = document.querySelector('[data-desk-window="fx_w_pads"] [data-block="fx_b_r1"]') as HTMLElement;
    fireEvent.mouseDown(line, { button: 2 });
    await flush();
    fireEvent.contextMenu(line);
    await flush();
    fireEvent.click(await screen.findByText("a gap row"));
    await waitFor(() => expect(transport.passageKnows).toHaveBeenCalledWith(expect.objectContaining({ objectKind: "pad_line", blockId: "fx_b_r1" })));
    expect(screen.getByRole("dialog", { name: "passage details" })).toBeTruthy();
    window.removeEventListener("learnloop:pad-flash", onFlash);
  });
});

describe("RD5 fix round: a selection across passages", () => {
  it("Append links the line to every passage the selection touches, each highlighted with its own words", async () => {
    const { transport, server } = mount();
    await screen.findByTestId("pane-fx_w_book");
    const first = passage("fx_w_book_s1").firstChild as Node;
    const second = passage("fx_w_book_s2").firstChild as Node;
    const range = document.createRange();
    range.setStart(first, 4);
    range.setEnd(second, 10);
    const selection = window.getSelection() as Selection;
    selection.removeAllRanges();
    selection.addRange(range);
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    fireEvent.click(screen.getByText(/^Append to “/));
    fireEvent.click(within(screen.getByRole("menu", { name: "append to" })).getAllByRole("menuitem")[0]);
    await waitFor(() => expect(transport.readerCapture).toHaveBeenCalled());
    const capture = (transport.readerCapture as ReturnType<typeof vi.fn>).mock.calls[0][0] as { rawSelection: { nodes: Array<{ spanId: string; quote?: string }> } };
    expect(transport.passagePromoted).toHaveBeenCalledWith(expect.objectContaining({
      spanId: "fx_w_book_s1", spanIds: ["fx_w_book_s1", "fx_w_book_s2"],
    }));
    expect(capture.rawSelection.nodes).toEqual([{ spanId: "fx_w_book_s1", quote: "first passage of fx_w_book" }, { spanId: "fx_w_book_s2", quote: "the second" }]);
    await flush();
    await flush();
    const ops = server.padBatches.flatMap((batch) => batch.ops as PadOpDto[]);
    const links = ops.filter((op) => op.op === "link_anchor") as Array<Extract<PadOpDto, { op: "link_anchor" }>>;
    expect(links.map((op) => op.spanId)).toEqual(["fx_w_book_s1", "fx_w_book_s2"]);
    selection.removeAllRanges();
  });
});

describe("RD5 fix round: a window header's menu", () => {
  it("a reading's header asks about the passage in view; a window with no passage offers its moves only", async () => {
    const { asked, transport } = mount();
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(document.querySelector('[data-desk-window="fx_w_book"] .desk-pane-head') as HTMLElement);
    await waitFor(() => expect(asked).toHaveLength(1));
    expect(asked[0]).toMatchObject({ objectKind: "window", windowId: "fx_w_book", extractionId: FIXTURE_SOURCES.book.extractionId, spanId: "fx_w_book_s1" });
    fireEvent.keyDown(window, { key: "i" });
    await waitFor(() => expect(transport.passageKnows).toHaveBeenCalledWith(expect.objectContaining({ objectKind: "window", spanId: "fx_w_book_s1" })));
    // Escape lets What this knows go (it owns the focus while open).
    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "passage details" })).toBeNull());
    // The pad stack's header: no passage, so no rows asked and no What this knows.
    await waitFor(() => expect(document.querySelector('[data-desk-window="fx_w_pads"] .desk-pane-head')).toBeTruthy());
    fireEvent.contextMenu(document.querySelector('[data-desk-window="fx_w_pads"] .desk-pane-head') as HTMLElement);
    const verbs = [...menus()[0].querySelectorAll(":scope > .mi .t")].map((each) => each.firstChild?.textContent);
    expect(verbs).toEqual(["New desk from these", "Gather linked sources", "Share a slot with the next", "Own slot"]);
    expect(asked).toHaveLength(1);
  });
});

describe("RD5 fix round: a pad line's Teach me", () => {
  it("opens a lesson tab in the desk's stack, as the source menu's does, with no app-level lesson hook needed", async () => {
    mount();
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.click(screen.getByTestId("teach-fx_w_book"));
    await waitFor(() => expect(screen.getByTestId("pane-fx_w_pads").getAttribute("data-openings")).toBe("1"));
  });
});

describe("RD5 fix round: Show me", () => {
  it("shows the figure in the companion; moved to the scratchpad it lands in the running pad of the desk it was asked on, even with another desk shown, and its poll ends", async () => {
    // Spec §13.1: Show me's figure appears in the companion (which reads its history when it shows).
    (api as unknown as Record<string, unknown>).companionHistory = async () => ({ version: 1, days: [], cursor: null });
    let answer: (read: unknown) => void = () => undefined;
    const { server, poller } = mount({ pads: (pads) => {
      pads.transport.figureRequest = (async () => ({ jobId: "fj1", kind: "figure_build", askId: null, state: "pending", result: null })) as never;
      pads.transport.readerFigureJob = (() => new Promise((resolve) => { answer = resolve; })) as never;
    } });
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    fireEvent.keyDown(window, { key: "v" });
    await flush();
    // The poll's read is in flight when another desk is shown; it answers there.
    let tick: Promise<void> = Promise.resolve();
    act(() => {
      tick = poller.tick();
    });
    fireEvent.click(screen.getByRole("button", { name: "attention", exact: true } as never));
    await flush();
    await act(async () => {
      answer({ jobId: "fj1", kind: "figure_build", askId: null, state: "done", result: { figure: { figureId: "fig9", shown: true, demonstrates: "a picture of it", goalText: "" }, reused: false } });
      await tick;
    });
    await flush();
    await flush();
    // Nothing lands in a pad by itself: the figure is in the companion, with "move to scratchpad".
    expect(server.padBatches.some((batch) => (batch.ops as PadOpDto[]).some((op) => op.op === "insert_block" && op.kind === "figure"))).toBe(false);
    const shown = await waitFor(() => {
      const found = document.querySelector<HTMLElement>('[data-companion-figure="fig9"]');
      if (!found) throw new Error("not yet");
      return found;
    });
    fireEvent.click(within(shown).getByRole("button", { name: COMPANION_FIGURE_COPY.move }));
    await flush();
    await flush();
    const inserts = server.padBatches.filter((batch) => (batch.ops as PadOpDto[]).some((op) => op.op === "insert_block" && op.kind === "figure"));
    expect(inserts.map((batch) => batch.padId)).toEqual(["fx_pad_running"]);
    expect(poller.size).toBe(0);
  });

  it("a figure job the sidecar no longer knows ends its poll (no registration left behind)", async () => {
    const { poller } = mount({ pads: (pads) => {
      pads.transport.figureRequest = (async () => ({ jobId: "fj2", kind: "figure_build", askId: null, state: "pending", result: null })) as never;
      pads.transport.readerFigureJob = (async () => {
        throw { code: "job_not_found", message: "gone" };
      }) as never;
    } });
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    fireEvent.keyDown(window, { key: "v" });
    await flush();
    await act(async () => {
      await poller.tick();
    });
    await flush();
    expect(poller.size).toBe(0);
  });
});

describe("RD5 fix round: New desk from these", () => {
  it("moves the window alone (no links needed) to a new desk titled from it, and focuses it there", async () => {
    const { server } = mount();
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(document.querySelector('[data-desk-window="fx_w_paper"] .desk-pane-head') as HTMLElement);
    fireEvent.keyDown(window, { key: "d" });
    await flush();
    await flush();
    const state = server.state();
    const fresh = state.desks.find((desk) => desk.title.startsWith("new desk · "));
    expect(fresh).toBeTruthy();
    // The window alone came over (the new desk's own running pad joins it on its first visit, as any desk's).
    const came = fresh?.slots.flatMap((slot) => slot.windows).map((window) => window.windowId).filter((windowId) => windowId.startsWith("fx_w_"));
    expect(came).toEqual(["fx_w_paper"]);
    expect(fresh?.focusWindowId).toBe("fx_w_paper");
    // The window's neighbours stayed.
    const old = state.desks.find((desk) => desk.deskId === "fx_desk_softmax");
    expect(old?.slots.flatMap((slot) => slot.windows).map((window) => window.windowId)).toContain("fx_w_book");
  });
});

describe("RD5 fix round: the menu's keys", () => {
  it("`n` writes a margin note on the hovered passage; `b` runs its first promoted action and labels it opened", async () => {
    const { transport, labels } = mount();
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.mouseOver(passage("fx_w_book_s2"));
    fireEvent.keyDown(window, { key: "n" });
    const sheet = await screen.findByRole("dialog", { name: "› note in margin" });
    fireEvent.change(within(sheet).getByRole("textbox", { name: "your note" }), { target: { value: "this is the temperature again" } });
    fireEvent.click(within(sheet).getByText("keep it"));
    await waitFor(() => expect(transport.readerCapture).toHaveBeenCalledWith(expect.objectContaining({ action: "annotate", learnerText: "this is the temperature again",
      rawSelection: { extractionId: FIXTURE_SOURCES.book.extractionId, nodes: [{ spanId: "fx_w_book_s2" }] } })));
    fireEvent.mouseOver(passage("fx_w_book_s1"));
    fireEvent.keyDown(window, { key: "b" });
    await waitFor(() => expect(labels).toEqual([expect.objectContaining({ proposalKind: "promoted_row", proposalId: "r1", label: "opened" })]));
  });

  it("`.` with a pad stack focused but no line hovered opens the menu on the hovered passage", async () => {
    const { asked } = mount({ stacks: true });
    await screen.findByTestId("pane-fx_w_book");
    await waitFor(() => expect(document.querySelector('[data-desk-window="fx_w_pads"] [data-block="fx_b_r1"]')).toBeTruthy());
    fireEvent.mouseDown(document.querySelector('[data-desk-window="fx_w_pads"] .desk-pane-head') as HTMLElement);
    await flush();
    expect(document.querySelector(".desk-window.focus [data-desk-window]")?.getAttribute("data-desk-window")).toBe("fx_w_pads");
    fireEvent.mouseOver(passage("fx_w_book_s2"));
    fireEvent.keyDown(window, { key: "." });
    await waitFor(() => expect(asked.some((input) => input.spanId === "fx_w_book_s2")).toBe(true));
    expect(menus()).toHaveLength(1);
  });
});

describe("RD5 fix round: the menu's sheets own the focus", () => {
  it("Note in margin's sheet takes the focus in its field and escape lets it go, writing nothing", async () => {
    const { transport } = mount();
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    fireEvent.keyDown(window, { key: "n" });
    const sheet = await screen.findByRole("dialog", { name: "› note in margin" });
    expect(document.activeElement).toBe(within(sheet).getByRole("textbox", { name: "your note" }));
    fireEvent.keyDown(document.body, { key: "Escape" });
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "› note in margin" })).toBeNull());
    expect(transport.readerCapture).not.toHaveBeenCalled();
  });
});

describe("RD5 fix round: labels are kept until stored", () => {
  it("a label whose send failed is sent again under the same id on the poller; one refused outright says so", async () => {
    const { transport, poller } = mount();
    const sent: Array<{ labelId: string; label: string }> = [];
    let failures = 1;
    (transport.proposalLabel as ReturnType<typeof vi.fn>).mockImplementation(async (input: { labelId: string; label: string; proposalId: string }) => {
      sent.push(input);
      if (input.proposalId === "r2") throw { code: "validation_error", message: "no such row", retryable: false };
      if (failures > 0) {
        failures -= 1;
        throw { code: "database_busy", message: "busy", retryable: true };
      }
      return {};
    });
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    const promoted = (await screen.findByText("your question on the first passage")).closest("button") as HTMLElement;
    fireEvent.click(within(promoted).getByLabelText("hide this suggestion"));
    await flush();
    await act(async () => {
      await poller.tick();
    });
    expect(sent).toHaveLength(2);
    expect(sent[1].labelId).toBe(sent[0].labelId);
    expect(poller.size).toBe(0);
    fireEvent.keyDown(window, { key: "Escape" });
    fireEvent.contextMenu(passage("fx_w_book_s2"));
    const second = (await screen.findByText("your question on the second passage")).closest("button") as HTMLElement;
    fireEvent.click(within(second).getByLabelText("hide this suggestion"));
    await flush();
    expect(await screen.findByText(/couldn't keep that you set it aside/)).toBeTruthy();
  });
});

describe("RD5 fix round: exam or held-out material in the menu", () => {
  it("names the material without quoting it, says nothing is searched, leaves out the verbs that would send its words, and a key pressed before the answer sends nothing", async () => {
    const { transport } = mount();
    let answer: (found: PassagePromotedDto) => void = () => undefined;
    (transport.passagePromoted as ReturnType<typeof vi.fn>).mockImplementation(() => new Promise<PassagePromotedDto>((resolve) => { answer = resolve; }));
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    // `/` (Find) before the menu's first answer: it waits for the protection.
    fireEvent.keyDown(window, { key: "/" });
    await act(async () => {
      answer({ version: 1, objectKey: "k", rows: [], cap: 4, pendingJob: null, paid: { searchedByMeaning: false, verified: false, reason: "exam or held-out material: nothing is searched for it" }, withheld: true } as unknown as PassagePromotedDto);
      await Promise.resolve();
    });
    await flush();
    expect(document.querySelector(".desk-search, [data-desk-search]")).toBeNull();
    expect(await screen.findByText("this is exam or held-out material: its words are not sent anywhere from here")).toBeTruthy();
    // Opened again on it: the plain line, the material named, the quoting verbs left out.
    (transport.passagePromoted as ReturnType<typeof vi.fn>).mockImplementation(async () => ({ version: 1, objectKey: "k", rows: [], cap: 4, pendingJob: null,
      paid: { searchedByMeaning: false, verified: false, reason: null }, withheld: true }) as unknown as PassagePromotedDto);
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    await screen.findByText("exam or held-out material: nothing is searched for it");
    expect(menus()[0].querySelector(".mh")?.textContent).toBe("a passage · exam or held-out material");
    const verbs = [...menus()[0].querySelectorAll(":scope > .mi .t")].map((each) => each.firstChild?.textContent);
    expect(verbs).toEqual(["Note in margin", "Open beside", "What this knows"]);
    expect(menus()[0].textContent).not.toContain("the first passage of fx_w_book");
  });

  it("on a practice exam that is not held out, offers what the classic Reader offers: Ask and Make it practice go, the rest wait; held out, none", async () => {
    const { transport } = mount();
    await screen.findByTestId("pane-fx_w_book");
    const reply = (withheldVerbs: string[]) => ({ version: 1, objectKey: "k", rows: [], cap: 4, pendingJob: null,
      paid: { searchedByMeaning: false, verified: false, reason: "exam or held-out material: nothing is searched for it" },
      withheld: true, withheldVerbs }) as unknown as PassagePromotedDto;
    // The server's per-verb verdict for exam material not held out: each verb by its destination's set.
    (transport.passagePromoted as ReturnType<typeof vi.fn>).mockImplementation(async () => reply(["append", "carry", "compare", "find", "show_me", "teach_me"]));
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    await screen.findByText("exam or held-out material: nothing is searched for it");
    const verbsNow = () => [...menus()[0].querySelectorAll(":scope > .mi .t")].map((each) => each.firstChild?.textContent);
    expect(verbsNow()).toEqual(["Ask", "Note in margin", "Open beside", "Make it practice", "What this knows"]);
    // The Reader's own Ask may read it, so the header quotes it as the Reader's composer does.
    expect(menus()[0].querySelector(".mh")?.textContent).toContain("“");
    fireEvent.keyDown(window, { key: "Escape" });
    await flush();
    // Held out: every verb that sends or copies it is left out, and the header names the material.
    (transport.passagePromoted as ReturnType<typeof vi.fn>).mockImplementation(async () => reply(["append", "ask", "carry", "compare", "find", "make_practice", "show_me", "teach_me"]));
    fireEvent.contextMenu(passage("fx_w_book_s1"));
    await screen.findByText("exam or held-out material: nothing is searched for it");
    expect(verbsNow()).toEqual(["Note in margin", "Open beside", "What this knows"]);
    expect(menus()[0].querySelector(".mh")?.textContent).toBe("a passage · exam or held-out material");
  });
});

it("keeps the header neutral while pending and offers retry after a failed protection read", async () => {
  const carry = vi.fn(async () => ({ carried: {} as never, created: true }));
  const { transport } = mount({ pads: (pads) => { pads.transport.carriedCarry = carry; } });
  let fail!: () => void;
  vi.mocked(transport.passagePromoted).mockImplementationOnce(() => new Promise((_resolve, reject) => { fail = reject; }));
  await screen.findByTestId("pane-fx_w_book");
  fireEvent.contextMenu(passage("fx_w_book_s1"));
  expect(menus()[0].textContent).not.toContain("the first passage of fx_w_book");
  fireEvent.keyDown(window, { key: "c" });
  await act(async () => fail());
  expect(carry).not.toHaveBeenCalled();
  expect(menus()[0].querySelector(".mh")?.textContent).toBe("a passage");
  expect(menus()[0].textContent).not.toContain("the first passage of fx_w_book");
  expect(within(menus()[0] as HTMLElement).queryByText("Carry")).toBeNull();
  fireEvent.click(await screen.findByRole("button", { name: /retry/i }));
  await screen.findByText("your question on the first passage");
  expect(menus()[0].textContent).toContain("the first passage of fx_w_book");
});

it("a pending Append destination cannot write after its menu is replaced", async () => {
  const { server, transport } = mount();
  let answer!: (found: PassagePromotedDto) => void;
  vi.mocked(transport.passagePromoted).mockImplementationOnce(() => new Promise((resolve) => { answer = resolve; }));
  await screen.findByTestId("pane-fx_w_book");
  fireEvent.contextMenu(passage("fx_w_book_s1"));
  fireEvent.click(screen.getByText(/^Append to “/));
  fireEvent.click(within(screen.getByRole("menu", { name: "append to" })).getByText("a new pad"));
  expect(transport.readerCapture).not.toHaveBeenCalled();
  expect(server.padBatches).toHaveLength(0);
  fireEvent.contextMenu(passage("fx_w_book_s2"));
  await screen.findByText("your question on the second passage");
  await act(async () => answer({ rows: [], withheld: false, pendingJob: null } as unknown as PassagePromotedDto));
  await flush();
  expect(transport.readerCapture).not.toHaveBeenCalled();
  expect(server.padBatches).toHaveLength(0);
  expect(menus()[0].textContent).toContain("the second passage");
});


it("refuses a new-pad Append chosen before a protected answer", async () => {
  const { server, transport } = mount();
  let answer!: (found: PassagePromotedDto) => void;
  vi.mocked(transport.passagePromoted).mockImplementationOnce(() => new Promise((resolve) => { answer = resolve; }));
  await screen.findByTestId("pane-fx_w_book");
  fireEvent.contextMenu(passage("fx_w_book_s1"));
  fireEvent.click(screen.getByText(/^Append to “/));
  fireEvent.click(within(screen.getByRole("menu", { name: "append to" })).getByText("a new pad"));
  expect(server.padBatches).toHaveLength(0);
  await act(async () => answer({ rows: [], withheld: true, pendingJob: null } as unknown as PassagePromotedDto));
  await screen.findByText("exam or held-out material: nothing is searched for it");
  expect(transport.readerCapture).not.toHaveBeenCalled();
  expect(server.padBatches).toHaveLength(0);
});
