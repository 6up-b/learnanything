// RW5c (spec §7, option B; G23a, G23e): every label slot of a checked figure reads from its elements.
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import katex from "katex";
import { afterEach, expect, it, vi } from "vitest";
import type { FigureElementDto, FigureViewDto } from "../../../api/dto";
import { FIGURE_FRAME, FigureInline, frameBadge, SOURCE_CHECK_COPY, sourceCheckReasons } from "./FigureInline";
import { derivedWords } from "./figureLabels";
import type { FiguresCtl } from "./useFigures";

vi.mock("../activity", () => ({ logReaderAction: vi.fn() }));
vi.mock("../../../api/client", () => ({ api: {} }));

const CLAIM = "matches the book's equation (checked)";

/** The delivered spec of a checked figure: its labels are element ids (the sidecar's rewrite). */
const SPEC = {
  spec_version: "ifs-v1", kind: "reconstructed", demonstrates: "the model's free text",
  parameters: [
    { name: "a", label: "parameters.0", min: 0.5, max: 1, step: 0.25, default: 1 },
    { name: "b", label: "parameters.1", min: 0, max: 1, step: 0.25, default: 0.5 },
  ],
  definitions: [{ name: "f", expr: "a*x + 0.25" }, { name: "h", expr: "b*x" }],
  panels: [
    { kind: "function_plot", x: { var: "x", min: 0, max: 1 },
      series: [{ expr: "f", label: "panels.0.series.0" }, { expr: "h", label: "panels.0.series.1" }],
      markers: [{ x: "b", label: "panels.0.markers.0" }],
      shade: [{ series: "panels.0.series.0", from: "-1", to: "2", label: "panels.0.shade.0" }] },
    { kind: "readout", label: "panels.1", expr: "integral(f, x, 0, 0.5)", format: "number" },
    { kind: "pmf_bars", k: { var: "k", min: 0, max: 3 }, series: [{ expr: "1/(k+1)", label: "panels.2.series.0" }],
      highlight: { from: "1.5", to: "4.2", label: "panels.2.highlight" } },
  ],
  annotations: [{ target: "panels.0.series.0", text: "the model's note" }],
};
const shadeTemplate = { kind: "shade", panel: 0, index: 0, bodyTex: "f(x)", bodyPlain: "f(x)", variable: "x" } as const;
const ELEMENTS: FigureElementDto[] = [
  { id: "parameters.0", path: "parameters.0", role: "symbol", tex: "a", plain: "a", voice: "source" },
  { id: "parameters.1", path: "parameters.1", role: "ai", tex: "b", plain: "b", voice: "model" },
  { id: "panels.0.series.0", path: "panels.0.series.0", role: "book", tex: "f(x)", plain: "f(x)", voice: "source", definition: "f",
    equation: "f(x)=ax+\\frac{1}{4}", source: { extractionId: "ext", spanId: "s1", page: 87 } },
  { id: "panels.0.series.1", path: "panels.0.series.1", role: "ai", tex: "\\mathrm{h}(x)", plain: "h(x)", voice: "model", definition: "h", tag: "ai_defined" },
  { id: "panels.0.markers.0", path: "panels.0.markers.0", role: "ai", tex: "x = b", plain: "x = b", voice: "model" },
  { id: "panels.0.shade.0", path: "panels.0.shade.0", role: "derived", tex: "stale", plain: "stale", voice: "frame", definition: "f", template: shadeTemplate },
  { id: "panels.1", path: "panels.1", role: "derived", tex: "stale", plain: "stale", voice: "frame", definition: "f",
    template: { kind: "integral", panel: 1, index: 0, bodyTex: "f(x)", bodyPlain: "f(x)", variable: "x" } },
  { id: "panels.2.series.0", path: "panels.2.series.0", role: "ai", tex: "\\frac{1}{k + 1}", plain: "1/(k + 1)", voice: "model" },
  { id: "panels.2.highlight", path: "panels.2.highlight", role: "ai", tex: "stale", plain: "stale", voice: "model",
    template: { kind: "highlight", panel: 2, index: 0, bodyTex: "\\frac{1}{k + 1}", bodyPlain: "1/(k + 1)", variable: "k" } },
];

function figure(changes: Partial<FigureViewDto> = {}): FigureViewDto {
  return {
    figureId: "fig_1", extractionId: "ext", spanIds: ["s1"], anchorSpanId: "s1", region: null, origin: "selection",
    verification: "illustrative", kind: "reconstructed", label: "x", reason: null, unsupportedKind: null, supersedesId: null,
    revisionNote: null, versions: 1, createdAt: "2026-11-02T00:00:00", specJson: JSON.stringify(SPEC), demonstrates: "the model's free text",
    assumptions: [], predictions: [], propertyChecks: ["values_finite"], elements: ELEMENTS,
    sourceCheck: { status: "checked", certificationVersion: 1, reasons: [], recheckDue: false, rebuild: false }, ...changes,
  };
}

function ctl(changes: Partial<FiguresCtl> = {}): FiguresCtl {
  return {
    enabled: true, contract: { predictions: true, region: true, revisions: true } as FiguresCtl["contract"], figures: [], pending: [],
    expandedKey: "fig_1@s1", setExpanded: vi.fn(), request: vi.fn(), revise: vi.fn(), predict: vi.fn(), explain: vi.fn(),
    under: () => ({ figures: [], pending: [], richPending: [], followed: [] }), followed: [], follow: vi.fn(), richPending: [],
    cancelRich: vi.fn(), retryRich: vi.fn(), manimOptIn: null, optInSpanId: null, answerManimOptIn: vi.fn(), ...changes,
  } as FiguresCtl;
}

function open(view: FigureViewDto, control: FiguresCtl = ctl()): HTMLElement {
  const { container } = render(<FigureInline figure={view} ctl={control} />);
  return container;
}

afterEach(cleanup);

it("the collapsed line is code's: the book's left-hand side in source voice, the claim, and the rest", () => {
  const container = open(figure());
  const badge = container.querySelector("[data-figure-badge]") as HTMLElement;
  expect(badge.textContent).toContain(FIGURE_FRAME.aiBuilt);
  expect(badge.textContent).toContain(CLAIM);
  expect(badge.textContent).toContain(FIGURE_FRAME.restIllustration);
  expect(badge.querySelector('[data-figure-tex="f(x)"]')).not.toBeNull();
  expect(badge.textContent).toContain("§");
});

it("with nothing checked the badge is RW5a's and no slot changes", () => {
  const plain = { ...SPEC, panels: [{ ...SPEC.panels[0], series: [{ expr: "f", label: "the model's name" }, { expr: "h", label: "other" }],
    shade: [{ series: "the model's name", from: "0", to: "1", label: "area" }], markers: [] }], annotations: [], parameters: SPEC.parameters };
  const container = open(figure({ specJson: JSON.stringify(plain), elements: [],
    sourceCheck: { status: "none", certificationVersion: 1, reasons: ["phi"], recheckDue: false, rebuild: false } }));
  expect((container.querySelector("[data-figure-badge]") as HTMLElement).textContent).toBe(frameBadge("illustrative"));
  expect(container.textContent).toContain("the model's name");
  expect(container.textContent).not.toContain(CLAIM);
  fireEvent.click(screen.getByRole("button", { name: /why this isn't checked/ }));
  expect(container.textContent).toContain(SOURCE_CHECK_COPY.phi);
});

it("the claim appears only on a book element, never from a status with no book element", () => {
  const container = open(figure({ elements: ELEMENTS.filter((element) => element.role !== "book") }));
  expect(container.textContent).not.toContain(CLAIM);
});

it("every label slot reads from the elements: legend, SVG text, table header, aria-label, readout and slider", () => {
  const container = open(figure());
  fireEvent.click(screen.getByText("t values table"));
  const legend = container.querySelector('[data-figure-role="book"]') as HTMLElement;
  expect(legend.textContent).toContain(CLAIM);
  expect(legend.getAttribute("data-figure-voice")).toBe("source");
  // No element id is ever drawn as words, and no slot shows anything but code's rendering.
  const text = container.textContent ?? "";
  for (const element of ELEMENTS) expect(text).not.toContain(element.id);
  const svg = container.querySelector('[data-figure-panel="function_plot"] svg') as SVGElement;
  expect(svg.getAttribute("aria-label")).toContain("plot of f(x), h(x)");
  expect(svg.getAttribute("aria-label")).toContain("area under f(x) from 0 to 1");
  expect(svg.textContent).toContain("x = b");
  const header = (container.querySelector('[data-figure-panel="function_plot"] thead') as HTMLElement);
  expect(within(header).getByText(CLAIM)).toBeTruthy();
  expect(header.querySelector('[data-figure-label="panels.0.series.1"]')).not.toBeNull();
  expect(screen.getByRole("slider", { name: "a" })).toBeTruthy();
  expect(screen.getByRole("slider", { name: "b" })).toBeTruthy();
});

it("an AI-defined reference is marked, in the model's voice", () => {
  const container = open(figure());
  const entry = container.querySelector('[data-figure-label="panels.0.series.1"]') as HTMLElement;
  expect(entry.getAttribute("data-figure-voice")).toBe("model");
  expect(entry.textContent).toContain("◇");
  expect(entry.textContent).toContain(FIGURE_FRAME.aiDefined);
  expect(entry.getAttribute("title")).toBe(FIGURE_FRAME.aiElement);
});

it("an id with no element draws the model's glyph alone, never a model string", () => {
  const worded = { ...SPEC, panels: [{ ...SPEC.panels[0], series: [{ expr: "f", label: "panels.0.series.0" }, { expr: "h", label: CLAIM }] }] };
  const container = open(figure({ specJson: JSON.stringify(worded) }));
  const bad = container.querySelector(`[data-figure-role="unmapped"]`) as HTMLElement;
  expect(bad.textContent).toBe("◇");
  expect(bad.closest("[data-figure-panel]")?.textContent?.split(CLAIM).length).toBe(2);
});

it("a shade states the clamped bounds it used, says so, and updates with the evaluation", () => {
  const container = open(figure());
  const readout = container.querySelector('[data-figure-readout="panels.0.shade.0"]') as HTMLElement;
  expect(readout.textContent).toContain(FIGURE_FRAME.limitedToPlot);
  expect(readout.textContent).toContain(FIGURE_FRAME.derivedFrom);
  expect(readout.querySelector("[data-figure-tex]")?.getAttribute("data-figure-tex")).toContain("\\text{ from } 0 \\text{ to } 1");
  expect(readout.textContent).not.toContain("from -1 to 2");
});

it("an integral readout states its evaluated bounds", () => {
  const container = open(figure());
  const readout = container.querySelector('[data-figure-readout="panels.1"]') as HTMLElement;
  expect(readout.querySelector("[data-figure-tex]")?.getAttribute("data-figure-tex")).toBe("\\int_{0}^{0.5} f(x)\\,dx");
});

it("a highlight states its integers", () => {
  const container = open(figure());
  const readout = container.querySelector('[data-figure-readout="panels.2.highlight"]') as HTMLElement;
  expect(readout.querySelector("[data-figure-tex]")?.getAttribute("data-figure-tex")).toBe("\\sum_{k=2}^{3} \\frac{1}{k + 1}");
  expect(readout.textContent).toContain(FIGURE_FRAME.limitedToPlot);
});

it("derived endpoints are lossless and an empty range says so", () => {
  const template: FigureElementDto = { id: "x", path: "x", role: "derived", tex: "", plain: "", voice: "frame",
    template: { kind: "sum", panel: 0, index: 0, bodyTex: "f(k)", bodyPlain: "f(k)", variable: "k" } };
  expect(derivedWords(template, { from: 100000, to: 100001, clipped: false, integers: [100000, 100001] }).tex).toBe("\\sum_{k=100000}^{100001} f(k)");
  const empty = derivedWords(template, { from: 2.2, to: 2.8, clipped: false, integers: [3, 2] });
  expect(empty.empty).toBe(true);
  expect(empty.plain).toContain(FIGURE_FRAME.noTerms);
  const shade: FigureElementDto = { ...template, template: { ...template.template!, kind: "shade", bodyTex: "f(x)", bodyPlain: "f(x)", variable: "x" } };
  expect(derivedWords(shade, { from: 0.123456, to: 0.123457, clipped: false, integers: null }).plain).toBe("area under f(x) from 0.123456 to 0.123457");
});

it("a scientific endpoint is written as the power it means, in every derived template (Codex review F3)", () => {
  const template = (kind: "shade" | "integral" | "sum"): FigureElementDto => ({ id: "x", path: "x", role: "derived", tex: "", plain: "", voice: "frame",
    template: { kind, panel: 0, index: 0, bodyTex: "f(x)", bodyPlain: "f(x)", variable: "x" } });
  const bounds = { from: 1e-7, to: 2e-7, clipped: false, integers: null };
  const integral = derivedWords(template("integral"), bounds);
  // The same words as the Python twin (test_rw5c_labels.py); the plain line keeps the round-trip digits.
  expect(integral.tex).toBe("\\int_{1 \\times 10^{-7}}^{2 \\times 10^{-7}} f(x)\\,dx");
  expect(integral.plain).toBe("integral from 1e-7 to 2e-7 of f(x) dx");
  expect(derivedWords(template("integral"), { ...bounds, from: -1.5e-7, to: 2.5e21 }).tex).toBe("\\int_{-1.5 \\times 10^{-7}}^{2.5 \\times 10^{21}} f(x)\\,dx");
  expect(derivedWords(template("integral"), { ...bounds, from: 0.5, to: 1 }).tex).toBe("\\int_{0.5}^{1} f(x)\\,dx");
  for (const kind of ["shade", "integral"] as const) {
    const shown = katex.renderToString(derivedWords(template(kind), bounds).tex, { output: "mathml", strict: "ignore" });
    expect(shown).toContain("<mn>1</mn><mo>×</mo><msup><mn>10</mn><mrow><mo>−</mo><mn>7</mn></mrow></msup>");
    expect(shown.replace(/<annotation[\s\S]*$/, "")).not.toContain("<mi>e</mi>");
  }
});

it("the annotation stays the model's line, its target code's name with no claim", () => {
  const container = open(figure());
  const line = screen.getByText(/the model's note/);
  expect(line.textContent?.startsWith("◇")).toBe(true);
  expect(line.textContent).not.toContain(CLAIM);
  expect(line.querySelector('[data-figure-tex="f(x)"]')).not.toBeNull();
  expect(container.textContent).toContain("the model's free text");
});

it("the ⓘ shows the book's equation as read, the page and opens it", () => {
  const openSource = vi.fn();
  const container = open(figure(), ctl({ openSource }));
  fireEvent.click(screen.getByRole("button", { name: /how this was checked/ }));
  const info = container.querySelector("[data-figure-source-equation]") as HTMLElement;
  expect(info.textContent).toContain("as LearnLoop read it from p. 87");
  expect(info.querySelector('[data-figure-tex="f(x)=ax+\\\\frac{1}{4}"]')).not.toBeNull();
  fireEvent.click(within(info).getByText("open the page"));
  expect(openSource).toHaveBeenCalledWith("ext", "s1");
  expect(container.querySelector("[data-figure-checked-line]")?.textContent).toContain("equals the book's equation on p. 87");
});

it("a rejected figure shows the frame's failed state, with rebuild only when it is offered", () => {
  const rejected = { verification: "failed" as const, specJson: null, reason: "its definition differs from the book's equation it quotes", elements: [] };
  const rebuild = vi.fn();
  const request = vi.fn();
  const { container, rerender } = render(<FigureInline figure={figure({ ...rejected, sourceCheck: { status: "differs", certificationVersion: 1, reasons: ["differs"], recheckDue: false, rebuild: true } })} ctl={ctl({ rebuild, request })} />);
  expect(container.textContent).toContain(FIGURE_FRAME.failed);
  expect(container.textContent).toContain("differs from the book's equation it quotes");
  fireEvent.click(screen.getByRole("button", { name: "rebuild" }));
  expect(rebuild).toHaveBeenCalledOnce();
  expect(screen.queryByText("try again")).toBeNull();
  rerender(<FigureInline figure={figure({ ...rejected, sourceCheck: { status: "differs", certificationVersion: 1, reasons: ["differs"], recheckDue: false, rebuild: false } })} ctl={ctl({ rebuild, request })} />);
  expect(screen.queryByRole("button", { name: "rebuild" })).toBeNull();
  expect(screen.queryByText("try again")).toBeNull();
});

it("opening a figure with no check yet asks for its recheck, by code", () => {
  const recheck = vi.fn();
  const view = figure({ elements: [], specJson: JSON.stringify({ ...SPEC, panels: [SPEC.panels[1]], annotations: [] }),
    sourceCheck: { status: "none", certificationVersion: 1, reasons: [], recheckDue: true, rebuild: false } });
  render(<FigureInline figure={view} ctl={ctl({ recheck, expandedKey: null })} />);
  fireEvent.click(screen.getByRole("button", { expanded: false }));
  expect(recheck).toHaveBeenCalledWith(view);
});

it("an unknown reason key is dropped", () => {
  expect(sourceCheckReasons(["phi", "made_up"])).toEqual([SOURCE_CHECK_COPY.phi]);
  expect(sourceCheckReasons(undefined)).toEqual([]);
});
