// Reader RW5b: the renderer's heat maps, vector fields, trajectories and iterated maps
// (spec §8.7; UX §4.7, §7.2), and "make this explorable" on an offer.
//
// Drawn from evaluateFigure's data only (the panels corpus): a heat map's cells and
// contour lines, a field's arrows over its heat map, a path from its marked start that
// says in words where it stopped, a values table for every panel; the tutor's offer is
// a button that calls nothing until pressed and then builds with origin "tutor"; the
// library's appears only on a passage the organizer judged explorable.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FigureViewDto, LibraryHitDto, LibraryNoteDto } from "../../../api/dto";
import corpus from "./figurePanelsCorpus.json";
import { ADVANCED_COPY, contourSegments } from "./AdvancedPanels";
import { FigurePanel } from "./FigurePanels";
import { compileSpec, evaluateFigure, type FigureSpec, type HeatmapData } from "./figureSpec";
import { FiguresUnder } from "./FigureInline";
import { useFigures, type FiguresContract } from "./useFigures";
import { OFFER_COPY, TutorOffers, defaultTutorOfferStore } from "../TutorOffers";
import { LIBRARY_EXPLORABLE_COPY, LibraryAnswer } from "../LibraryAnswer";
import type { LibraryAskController } from "../useLibraryAsk";

const api = vi.hoisted(() => ({
  readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
  readerFigureRevise: vi.fn(), readerFigurePredict: vi.fn(), readerFigureExplain: vi.fn(), readerLogActivity: vi.fn(),
  findPractice: vi.fn(), runSourceTool: vi.fn(), recordProposalImpressions: vi.fn(), recordSourceOfferShown: vi.fn(),
}));
vi.mock("../../../api/client", () => ({ api }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

beforeEach(() => {
  vi.resetAllMocks();
  defaultTutorOfferStore.clear();
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
});
afterEach(cleanup);

function specOf(id: string): FigureSpec {
  return corpus.figures.find((item) => item.id === id)!.spec as unknown as FigureSpec;
}

function draw(id: string, showTable = false) {
  const compiled = compileSpec(specOf(id));
  const data = evaluateFigure(compiled);
  return render(<div>{data.panels.map((panel, index) => <FigurePanel key={index} data={panel} model={compiled.spec.panels[index]} showTable={showTable} />)}</div>);
}

it("draws a heat map's cells and contour lines, labelled for a screen reader", () => {
  const { container } = draw("heatmap_quadratic_landscape");
  const panel = container.querySelector('[data-figure-panel="heatmap_2d"]')!;
  expect(panel.querySelectorAll("[data-figure-heat] rect").length).toBe(17 * 13);
  expect(panel.querySelectorAll("[data-figure-contour]").length).toBe(2);
  expect(screen.getByRole("img", { name: /heat map of loss with 2 contour lines/ })).toBeTruthy();
  expect(panel.textContent).toContain("contours at 1, 3");
});

it("traces a contour by marching squares over the computed grid only", () => {
  const data = evaluateFigure(compileSpec(specOf("heatmap_quadratic_landscape"))).panels[0] as HeatmapData;
  const segments = contourSegments(data, 1);
  expect(segments.length).toBeGreaterThan(8);
  // Every endpoint lies inside the grid (nothing is drawn past the computed data).
  for (const [[x0, y0], [x1, y1]] of segments) {
    for (const [px, py] of [[x0, y0], [x1, y1]]) {
      expect(px >= -2 && px <= 2 && py >= -2 && py <= 2).toBe(true);
    }
  }
});

it("draws a vector field's arrows over its heat map", () => {
  const { container } = draw("vector_field_gradient_over_heatmap");
  const panel = container.querySelector('[data-figure-panel="vector_field_2d"]')!;
  // 9 x 9 grid points; the one at the minimum is a dot, the rest arrows.
  expect(panel.querySelectorAll("[data-figure-arrows] line").length).toBe(80);
  expect(panel.querySelectorAll("[data-figure-arrows] circle").length).toBe(1);
  expect(panel.querySelectorAll("[data-figure-heat] rect").length).toBe(11 * 11);
  expect(screen.getByRole("img", { name: /vector field of negative gradient, over a heat map of loss/ })).toBeTruthy();
});

it("draws a trajectory from its start and says where it left the plot", () => {
  const { container } = draw("trajectory_leaves_plot");
  const panel = container.querySelector('[data-figure-panel="trajectory_2d"]')!;
  expect(panel.querySelector("[data-figure-start]")).toBeTruthy();
  expect(panel.querySelector('[data-figure-stop="left_plot"]')).toBeTruthy();
  expect(panel.textContent).toContain(ADVANCED_COPY.leftPlot);
  expect(panel.textContent).toContain("fixed-step RK4");
});

it("draws an iterated map's points and a path that never ran says so", () => {
  const { container } = draw("iterate_gradient_descent");
  const panel = container.querySelector('[data-figure-panel="iterate_2d"]')!;
  expect(panel.querySelectorAll("[data-figure-iterate]").length).toBe(41);
  expect(panel.textContent).toContain("40 iterations");
  cleanup();
  const compiled = compileSpec(specOf("trajectory_starts_outside"));
  const data = evaluateFigure(compiled);
  const outside = render(<FigurePanel data={data.panels[0]} model={compiled.spec.panels[0]} showTable={false} />);
  expect(outside.container.textContent).toContain(ADVANCED_COPY.startsOutside);
  expect(outside.container.querySelector("[data-figure-path]")).toBeNull();
});

it("gives every new panel a values table", () => {
  for (const id of ["heatmap_gaussian_density", "vector_field_rotation_default_cells", "trajectory_damped_oscillator", "iterate_henon_map"]) {
    const { container } = draw(id, true);
    const table = within(container as HTMLElement).getByRole("table", { name: "values as a table" });
    expect(table.querySelectorAll("tr").length).toBeGreaterThan(3);
    expect(table.querySelectorAll("tr").length).toBeLessThan(30);
    cleanup();
  }
});

function viewOf(id: string): FigureViewDto {
  return {
    figureId: "fig_adv", extractionId: "ext_prob", spanIds: ["p3"], anchorSpanId: "p3", region: null, origin: "tutor",
    verification: "illustrative", kind: "illustrative", label: "AI-built illustration of an interpretation · not checked against the book",
    reason: null, unsupportedKind: null, supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-10-23T00:00:00",
    specJson: JSON.stringify(specOf(id)), demonstrates: "how gradient descent moves", assumptions: [], predictions: [], propertyChecks: ["values_finite"],
  } as unknown as FigureViewDto;
}

const CONTRACT: FiguresContract = { predictions: true, region: true, revisions: true, offers: true };

function Harness({ contract = CONTRACT }: { contract?: FiguresContract }) {
  const ctl = useFigures({ extractionId: "ext_prob", contract });
  return (
    <div>
      <div data-span="p3"><FiguresUnder ctl={ctl} spanId="p3" /></div>
      <TutorOffers exchangeId="qe_1" extractionId="ext_prob" toolRequests={[]}
        buttons={[{ kind: "make_explorable", extractionId: "ext_prob", spanId: "p3", label: "make this explorable", role: "equation" },
          { kind: "make_explorable", extractionId: "ext_other", spanId: "x1", label: "make this explorable", role: "figure" }]}
        onMakeExplorable={(spanId, offerRef) => ctl.request({ spanIds: [spanId], origin: "tutor", offerRef })} />
    </div>
  );
}

it("an RW5b figure under its passage opens to its panels", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [viewOf("iterate_gradient_descent")] });
  const { container } = render(<Harness />);
  const line = await screen.findByRole("button", { name: /interactive version/ });
  fireEvent.click(line);
  await waitFor(() => expect(container.querySelector('[data-figure-panel="iterate_2d"]')).toBeTruthy());
});

it("the tutor's offer calls nothing until pressed, then builds with origin tutor under the passage", async () => {
  api.readerFigureRequest.mockResolvedValue({ jobId: "j1", kind: "figure_build", askId: null, state: "pending", result: null });
  api.readerFigureJob.mockResolvedValue({ jobId: "j1", kind: "figure_build", askId: null, state: "pending", result: null });
  render(<Harness />);
  await act(async () => { await Promise.resolve(); });
  // Only this book's block is offered.
  const buttons = screen.getAllByRole("button", { name: OFFER_COPY.makeExplorable });
  expect(buttons).toHaveLength(1);
  expect(api.readerFigureRequest).not.toHaveBeenCalled();
  fireEvent.click(buttons[0]);
  await waitFor(() => expect(api.readerFigureRequest).toHaveBeenCalledTimes(1));
  expect(api.readerFigureRequest).toHaveBeenCalledWith({ extractionId: "ext_prob", spanIds: ["p3"], origin: "tutor", offerRef: "qe_1" });
  expect(screen.queryByRole("button", { name: OFFER_COPY.makeExplorable })).toBeNull();
  expect(screen.getByText(OFFER_COPY.explorableBuilding)).toBeTruthy();
  await waitFor(() => expect(document.querySelector('[data-span="p3"]')!.textContent).toMatch(/building an interactive version/));
});

it("with offers off in the contract an offered press builds nothing", async () => {
  render(<Harness contract={{ predictions: true, region: true, revisions: true }} />);
  fireEvent.click(screen.getAllByRole("button", { name: OFFER_COPY.makeExplorable })[0]);
  await act(async () => { await Promise.resolve(); });
  expect(api.readerFigureRequest).not.toHaveBeenCalled();
});

it("no onMakeExplorable, no button (the Reader passes none while offers are off)", () => {
  render(<TutorOffers exchangeId="qe_2" extractionId="ext_prob" toolRequests={[]}
    buttons={[{ kind: "make_explorable", extractionId: "ext_prob", spanId: "p3", label: "make this explorable", role: "equation" }]} />);
  expect(screen.queryByRole("button", { name: OFFER_COPY.makeExplorable })).toBeNull();
});

const LIBRARY_HIT: LibraryHitDto = {
  key: "ext_prob:p3", extractionId: "ext_prob", spanId: "p3", sourceId: "src_prob", sourceTitle: "Introduction to Probability",
  section: "5.4", page: 1, text: "f_X(x) = p λ e^{λx} for x < 0", role: "equation", group: "Explanation", expansion: null,
  learningObjectIds: [], authorship: "source", label: "source-authored",
} as unknown as LibraryHitDto;
const LIBRARY_NOTE: LibraryNoteDto = {
  key: "ext_prob:p3", verdict: "contributes", ledgerId: "lac_1", line: "the density itself", roles: [], speaksTo: null,
  label: "LearnLoop's model", explorable: true,
};

function libraryCtl(notes: LibraryNoteDto[]): LibraryAskController {
  const idle = { phase: "idle" as const, value: null, failure: null };
  const prose = { ...LIBRARY_HIT, key: "ext_prob:p2", spanId: "p2", role: "ordinary_prose", text: "The two-sided exponential has density" };
  const ask = {
    askId: "la_1", query: "what is the two-sided exponential?", entry: "reader", status: "ok", policy: "reading", personalized: false,
    basis: "keyword", hits: [LIBRARY_HIT, prose], learningObjectIds: [], extractionId: "ext_prob", anchorSpanIds: [],
    groups: { sources: [{ sourceId: "src_prob", sourceTitle: "Introduction to Probability", groups: [{ group: "Explanation", keys: [LIBRARY_HIT.key, prose.key] }] }], expansions: [] },
    expansions: [], expandGraph: false, sourceCount: 1, passageCount: 2,
  };
  return {
    enabled: true, settings: { expandGraph: false, personalizedDefault: false, compare: false }, keep: null, open: true,
    state: {
      key: 1, request: { query: ask.query }, personalized: false, pinned: [], peek: null,
      ask: { phase: "landed", value: ask, failure: null },
      notes: { phase: "landed", value: { askId: "la_1", status: "judged", notes, order: [] }, failure: null },
      compare: idle, tutor: idle, practice: idle,
    },
    ask: vi.fn(), retry: vi.fn(), setPersonalized: vi.fn(), retryNotes: vi.fn(), togglePin: vi.fn(), canCompare: false,
    compare: vi.fn(), askTutor: vi.fn(), practice: vi.fn(), peek: vi.fn(), closePeek: vi.fn(), close: vi.fn(),
    cancelNotes: vi.fn(), cancelCompare: vi.fn(), cancelTutor: vi.fn(),
  } as unknown as LibraryAskController;
}

it("the library answer offers 'make this explorable' only where the organizer judged it, and the press names the question", () => {
  const pressed = vi.fn();
  const prose: LibraryNoteDto = { ...LIBRARY_NOTE, key: "ext_prob:p2", explorable: false };
  render(<LibraryAnswer ctl={libraryCtl([LIBRARY_NOTE, prose])} onOpenHit={null} onPracticePick={null} onClose={vi.fn()} onMakeExplorable={pressed} />);
  const buttons = screen.getAllByRole("button", { name: LIBRARY_EXPLORABLE_COPY.make });
  expect(buttons).toHaveLength(1);
  expect(buttons[0].getAttribute("data-library-explorable")).toBe("ext_prob:p3");
  fireEvent.click(buttons[0]);
  expect(pressed).toHaveBeenCalledWith(expect.objectContaining({ key: "ext_prob:p3" }), "la_1");
  expect(screen.queryByRole("button", { name: LIBRARY_EXPLORABLE_COPY.make })).toBeNull();
  expect(screen.getByText(LIBRARY_EXPLORABLE_COPY.building)).toBeTruthy();
});

it("with offers off (no explorable field, no handler) the library answer has no offer", () => {
  const { explorable: _dropped, ...rw4a } = LIBRARY_NOTE;
  render(<LibraryAnswer ctl={libraryCtl([rw4a])} onOpenHit={null} onPracticePick={null} onClose={vi.fn()} />);
  expect(screen.queryByRole("button", { name: LIBRARY_EXPLORABLE_COPY.make })).toBeNull();
  cleanup();
  render(<LibraryAnswer ctl={libraryCtl([LIBRARY_NOTE])} onOpenHit={null} onPracticePick={null} onClose={vi.fn()} />);
  expect(screen.queryByRole("button", { name: LIBRARY_EXPLORABLE_COPY.make })).toBeNull();
});
