// RW5d P4a: figures follow the section (spec_reader_show_me_figures_v1 §10.2).
//
// "Also in your books" offers a figure the learner kept in another book's
// corresponding section ("◇▸ interactive version from Lay §5.1"); pressing it
// shows the figure under the passage being read here, expanded, its home named
// ("from your reading of Lay § 5.1 …"), with no "not right?" (a new version
// belongs to its own book). Its own book's listing is read at the press, so a
// figure held out or switched off since is not shown. With no figures in the
// read (the switch off) or no onOpenFigure (figures off), nothing is offered.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { CorrespondentFigureDto, CorrespondentSectionDto, CorrespondentsDto, FigureViewDto } from "../../../api/dto";
import { ALSO_COPY, AlsoInBooks, figureOfferWords } from "../AlsoInBooks";
import corpus from "./figureGoldenCorpus.json";
import { FIGURE_COPY, FiguresUnder, figureHomeLine } from "./FigureInline";
import type { FigureSpec } from "./figureSpec";
import { useFigures, type FiguresContract, type FiguresCtl } from "./useFigures";

const { api, log } = vi.hoisted(() => ({
  api: {
    readerCorrespondents: vi.fn(), readerCorrespondentPeek: vi.fn(), readerCorrespondentDismiss: vi.fn(), curriculumAlsoAbout: vi.fn(),
    readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
    readerFigureRevise: vi.fn(), readerFigurePredict: vi.fn(), readerFigureExplain: vi.fn(), readerLogActivity: vi.fn(),
  },
  log: vi.fn(),
}));
vi.mock("../../../api/client", () => ({ api }));
vi.mock("../activity", () => ({ logReaderAction: log }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const FLAGSHIP = corpus.figures.find((item) => item.id === "two_sided_exponential")!.spec as unknown as FigureSpec;
const CONTRACT: FiguresContract = { predictions: true, region: true, revisions: true };
const SECTION = { id: "u61", label: "6.1 Introduction to eigenvalues", startSpanId: "s1" };

const REF: CorrespondentFigureDto = {
  figureId: "fig_lay", extractionId: "ext_lay", anchorSpanId: "l3", label: "AI-built illustration", kind: "illustrative",
  verification: "illustrative", createdAt: "2026-10-30T00:00:00Z",
};

function lay(over: Partial<CorrespondentSectionDto> = {}): CorrespondentSectionDto {
  return {
    extractionId: "ext_lay", sectionId: "lay51", title: "5.1 Eigenvectors and eigenvalues", sourceId: "src_lay", sourceTitle: "Lay",
    read: false, jump: { extractionId: "ext_lay", sectionId: "lay51", spanId: "l1" }, treatment: "introduces",
    treatmentWords: "introduces it", by: "judge", notation: null, notationLabel: null, roles: [], linkedByYou: false,
    kept: [], alsoLearningObjectIds: [], ...over,
  };
}

function judged(section: CorrespondentSectionDto): CorrespondentsDto {
  return {
    extractionId: "ext_strang", sectionId: SECTION.id, status: "judged", search: null,
    learningObjects: [{ learningObjectId: "lo_eigen", title: "eigenvalues", sources: [
      { sourceId: "src_lay", sourceTitle: "Lay", sections: [section] }] }],
    checkableLearningObjectIds: ["lo_eigen"],
  };
}

function layFigure(over: Partial<FigureViewDto> = {}): FigureViewDto {
  return {
    figureId: "fig_lay", extractionId: "ext_lay", spanIds: ["l3"], anchorSpanId: "l3", region: null, origin: "selection",
    verification: "illustrative", kind: "reconstructed", label: "AI-built illustration", reason: null, unsupportedKind: null,
    supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-10-30T00:00:00Z", specJson: JSON.stringify(FLAGSHIP),
    demonstrates: FLAGSHIP.demonstrates, assumptions: [], predictions: [], ...over,
  };
}

beforeEach(() => {
  vi.resetAllMocks();
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => { callback(0); return 0; });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

async function flush() {
  await act(async () => { for (let i = 0; i < 8; i += 1) await Promise.resolve(); });
}

async function mountAlso(section: CorrespondentSectionDto, onOpenFigure: ((figure: CorrespondentFigureDto, hit: CorrespondentSectionDto) => void) | null) {
  api.readerCorrespondents.mockResolvedValueOnce(judged(section));
  render(<AlsoInBooks extractionId="ext_strang" section={SECTION} hidden={false} onHide={vi.fn()} onGoThere={vi.fn()}
    onCompare={null} onError={vi.fn()} onOpenFigure={onOpenFigure} />);
  await flush();
  fireEvent.click(document.querySelector<HTMLButtonElement>("[data-also-collapsed]")!);
  await flush();
}

// -- the offer in "also in your books" ----------------------------------------------------------

it("offers a kept figure of the line's section, named by its home, and opens it on a press", async () => {
  const onOpenFigure = vi.fn();
  const section = lay({ figures: [REF] });
  await mountAlso(section, onOpenFigure);
  const offer = document.querySelector<HTMLButtonElement>(`[data-also-figure="fig_lay"]`)!;
  expect(offer.textContent).toBe("◇▸ interactive version from Lay §5.1");
  expect(offer.textContent).toBe(figureOfferWords(section));
  expect(offer.title).toContain(ALSO_COPY.figureFrom);
  fireEvent.click(offer);
  expect(onOpenFigure).toHaveBeenCalledWith(REF, section);
  // The collapsed line names books, never figures (it is unchanged).
  expect(api.readerFigures).not.toHaveBeenCalled();
});

it("offers nothing with no figure in the read or with figures off", async () => {
  await mountAlso(lay(), vi.fn());
  expect(document.querySelector("[data-also-figure]")).toBeNull();
  cleanup();
  await mountAlso(lay({ figures: [REF] }), null);
  expect(document.querySelector("[data-also-figure]")).toBeNull();
});

// -- the figure shown here --------------------------------------------------------------------------

let ctlRef: FiguresCtl | null = null;

function Harness({ spans, followOn = true }: { spans: string[]; followOn?: boolean }) {
  const ctl = useFigures({ extractionId: "ext_strang", contract: CONTRACT, followEnabled: followOn });
  ctlRef = ctl;
  return <div>{spans.map((span) => <div key={span} data-span={span}><FiguresUnder ctl={ctl} spanId={span} /></div>)}</div>;
}

it("shows a followed figure under the passage here, expanded, its home named, with no 'not right?'", async () => {
  api.readerFigures.mockImplementation(async ({ extractionId }: { extractionId: string }) => (
    extractionId === "ext_lay" ? { extractionId, figures: [layFigure()] } : { extractionId, figures: [] }));
  render(<Harness spans={["s4", "s5"]} />);
  await flush();
  let shown = false;
  await act(async () => {
    shown = await ctlRef!.follow(REF, { sourceTitle: "Lay", sectionTitle: "5.1 Eigenvectors and eigenvalues" }, "s5");
  });
  expect(shown).toBe(true);
  // Its own book's listing was read at the press (protection is checked there).
  expect(api.readerFigures).toHaveBeenCalledWith({ extractionId: "ext_lay" });
  const under = document.querySelector('[data-span="s5"] [data-figure="fig_lay"]')!;
  expect(under).not.toBeNull();
  expect(document.querySelector('[data-span="s4"] [data-figure]')).toBeNull();
  expect(under.querySelector("[data-figure-home]")!.textContent).toBe("from your reading of Lay § 5.1 Eigenvectors and eigenvalues");
  expect(figureHomeLine({ sourceTitle: "Lay", sectionTitle: "5.1 Eigenvectors and eigenvalues" }))
    .toBe(`${FIGURE_COPY.fromYourReading} Lay § 5.1 Eigenvectors and eigenvalues`);
  expect(under.querySelector("[data-figure-body]")).not.toBeNull(); // opened in place
  expect(screen.queryByRole("button", { name: FIGURE_COPY.notRight })).toBeNull();
  // Collapsed, it still says where it is from.
  fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.close }));
  expect(document.querySelector("[data-figure-body]")).toBeNull();
  expect(document.querySelector("[data-figure-home]")).not.toBeNull();
});

it("shows nothing when its own book no longer lists it (held out, switched off, gone)", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_lay", figures: [] });
  render(<Harness spans={["s5"]} />);
  await flush();
  let shown = true;
  await act(async () => {
    shown = await ctlRef!.follow(REF, { sourceTitle: "Lay", sectionTitle: "5.1" }, "s5");
  });
  expect(shown).toBe(false);
  expect(document.querySelector("[data-figure]")).toBeNull();
  // A listed figure that is not shown (a failed line) is not followed either.
  api.readerFigures.mockResolvedValue({ extractionId: "ext_lay", figures: [layFigure({ verification: "failed", specJson: null })] });
  await act(async () => {
    shown = await ctlRef!.follow(REF, { sourceTitle: "Lay", sectionTitle: "5.1" }, "s5");
  });
  expect(shown).toBe(false);
  expect(document.querySelector("[data-figure]")).toBeNull();
});

// -- revocation after display (Codex review F1, F2) ------------------------------------------------

const HOME = { sourceTitle: "Lay", sectionTitle: "5.1 Eigenvectors and eigenvalues" };

async function followNow(): Promise<boolean> {
  let shown = false;
  await act(async () => { shown = await ctlRef!.follow(REF, HOME, "s5"); });
  return shown;
}

it("a followed figure its own book stops listing leaves on the next press (held out after it was shown)", async () => {
  api.readerFigures.mockImplementation(async ({ extractionId }: { extractionId: string }) => (
    extractionId === "ext_lay" ? { extractionId, figures: [layFigure()] } : { extractionId, figures: [] }));
  render(<Harness spans={["s5"]} />);
  await flush();
  expect(await followNow()).toBe(true);
  expect(document.querySelector('[data-span="s5"] [data-figure="fig_lay"] [data-figure-body]')).not.toBeNull();
  // Its passage is held out now: the listing omits it, and the same offer pressed again removes it here.
  api.readerFigures.mockImplementation(async ({ extractionId }: { extractionId: string }) => ({ extractionId, figures: [] }));
  expect(await followNow()).toBe(false);
  expect(document.querySelector("[data-figure]")).toBeNull();
  expect(ctlRef!.followed).toEqual([]);
  expect(ctlRef!.expandedKey).toBeNull();
  // An unreadable listing after a success removes it too.
  api.readerFigures.mockImplementation(async ({ extractionId }: { extractionId: string }) => (
    extractionId === "ext_lay" ? { extractionId, figures: [layFigure()] } : { extractionId, figures: [] }));
  expect(await followNow()).toBe(true);
  api.readerFigures.mockRejectedValue(new Error("the sidecar went away"));
  expect(await followNow()).toBe(false);
  expect(document.querySelector("[data-figure]")).toBeNull();
  expect(ctlRef!.expandedKey).toBeNull();
});

it("switching correspondence off clears a followed figure, and a follow still in flight never lands", async () => {
  api.readerFigures.mockImplementation(async ({ extractionId }: { extractionId: string }) => (
    extractionId === "ext_lay" ? { extractionId, figures: [layFigure()] } : { extractionId, figures: [] }));
  const view = render(<Harness spans={["s5"]} />);
  await flush();
  expect(await followNow()).toBe(true);
  expect(document.querySelector('[data-figure="fig_lay"]')).not.toBeNull();
  // reader.correspondence.enabled off (the contract refreshed, the same book open).
  view.rerender(<Harness spans={["s5"]} followOn={false} />);
  await flush();
  expect(document.querySelector("[data-figure]")).toBeNull();
  expect(ctlRef!.followed).toEqual([]);
  expect(ctlRef!.expandedKey).toBeNull();
  // Off, a press does nothing (no read of the other book).
  api.readerFigures.mockClear();
  expect(await followNow()).toBe(false);
  expect(api.readerFigures).not.toHaveBeenCalled();
  // Back on, nothing returns by itself (it was cleared, not hidden).
  view.rerender(<Harness spans={["s5"]} />);
  await flush();
  expect(document.querySelector("[data-figure]")).toBeNull();
  // A follow whose listing is still in flight when the switch goes off never lands.
  let release: (value: unknown) => void = () => undefined;
  api.readerFigures.mockImplementation(({ extractionId }: { extractionId: string }) => (
    extractionId === "ext_lay" ? new Promise((resolve) => { release = resolve; }) : Promise.resolve({ extractionId, figures: [] })));
  let pending: Promise<boolean> = Promise.resolve(true);
  act(() => { pending = ctlRef!.follow(REF, HOME, "s5"); });
  view.rerender(<Harness spans={["s5"]} followOn={false} />);
  await flush();
  let shown = true;
  await act(async () => {
    release({ extractionId: "ext_lay", figures: [layFigure()] });
    shown = await pending;
  });
  expect(shown).toBe(false);
  view.rerender(<Harness spans={["s5"]} />);
  await flush();
  expect(document.querySelector("[data-figure]")).toBeNull();
  expect(ctlRef!.followed).toEqual([]);
});
