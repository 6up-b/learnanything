// Reader RW5d P2b: rich figures in the Reader, the Manim half (spec §6.8, §9b.3; G-SM21).
//
// Fast then fuller: the quick figure shows at once with one dim line inside
// its frame ("◌ a fuller animation is being written"); when the rich one is
// ready the line reads "◇ a fuller animation is ready · open ▸", open swaps the
// frame's content and "◂ the quick version" swaps back: one figure line, two
// versions. The collapsed line says "a fuller animation is ready". A rich-only
// build is a pending line naming its phase. No toast, no count, no focus move.
// The Manim figure: its video through the shared player, its transcript, the
// code-written check lines and "the video itself is not checked frame by frame".
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FigureFullerDto, FigureRichPendingDto, FigureViewDto } from "../../../api/dto";
import corpus from "./figureGoldenCorpus.json";
import { FiguresUnder } from "./FigureInline";
import { manimCheckLine, RICH_FRAME, RICH_PHASES } from "./RichFigure";
import type { FigureSpec } from "./figureSpec";
import { RICH_POLL_MS, useFigures, type FiguresContract } from "./useFigures";

const api = vi.hoisted(() => ({
  readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
  readerFigureRevise: vi.fn(), readerFigurePredict: vi.fn(), readerFigureExplain: vi.fn(), readerLogActivity: vi.fn(),
  figureRichCancel: vi.fn(), figureRichRetry: vi.fn(), figureManimOptIn: vi.fn(), figureRequest: vi.fn(),
}));
vi.mock("../../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/core", () => ({ convertFileSrc: (name: string) => `llmedia://localhost/${name}` }));

const FLAGSHIP = corpus.figures.find((item) => item.id === "two_sided_exponential")!.spec as unknown as FigureSpec;
const CONTRACT: FiguresContract = { predictions: true, region: true, revisions: true, showMe: true,
  rich: { manimOptIn: "standing" } };

function manimView(overrides: Partial<FigureViewDto> = {}): FigureViewDto {
  return {
    figureId: "fig_rich", extractionId: "ext_prob", spanIds: ["p3"], anchorSpanId: "p3", region: null,
    origin: "selection", verification: "illustrative", kind: "illustrative", label: RICH_FRAME.manim, reason: null,
    unsupportedKind: null, supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-11-01T00:00:00",
    specJson: null, demonstrates: "why the trajectory spirals", assumptions: [], predictions: [], tier: "manim",
    fuller: null, manim: {
      mediaFileName: "sha256-abc.mp4", title: "Why it spirals", narrationMd: "It turns as it decays.",
      durationSeconds: 48, notCovered: ["the video itself is not checked frame by frame"], notCheckable: [],
      checks: [{ kind: "equals", function: "x", expr: "exp(a*t)*cos(b*t)", settings: 27, plotted: true },
               { kind: "invariant", function: "x", property: "bounded", bound: 2, settings: 27, plotted: true }],
    },
    ...overrides,
  };
}

function quickView(fuller: FigureFullerDto | null): FigureViewDto {
  return {
    figureId: "fig_quick", extractionId: "ext_prob", spanIds: ["p3"], anchorSpanId: "p3", region: null,
    origin: "selection", verification: "illustrative", kind: "illustrative",
    label: "AI-built illustration of an interpretation · not checked against the book", reason: null,
    unsupportedKind: null, supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-11-01T00:00:00",
    specJson: JSON.stringify(FLAGSHIP), demonstrates: FLAGSHIP.demonstrates, assumptions: [], predictions: [],
    tier: "grammar", manim: null, fuller,
  };
}

const PENDING: FigureFullerDto = { state: "pending", tier: "manim", phase: "rendering", reason: null,
  richJobId: "ijob_1", figure: null };

function Harness({ contract = CONTRACT }: { contract?: FiguresContract }) {
  const ctl = useFigures({ extractionId: "ext_prob", contract });
  return (
    <div>
      <button type="button">elsewhere</button>
      <div data-span="p3"><FiguresUnder ctl={ctl} spanId="p3" /></div>
      <button type="button" onClick={() => ctl.request({ spanIds: ["p3"], goalText: "the spiral", origin: "show_me" })}>
        show me
      </button>
    </div>
  );
}

beforeEach(() => {
  vi.resetAllMocks();
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, blob: async () => new Blob(["mp4"]) }) as unknown as typeof fetch;
  URL.createObjectURL = vi.fn(() => "blob:video") as unknown as typeof URL.createObjectURL;
  URL.revokeObjectURL = vi.fn();
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

it("writes a Manim figure's check lines from closed fields, scoped to the function", () => {
  expect(manimCheckLine({ kind: "equals", function: "x", expr: "exp(a*t)", settings: 27, plotted: true }))
    .toBe("the curve is drawn from x, which matches exp(a*t) at 27 tested settings");
  expect(manimCheckLine({ kind: "equals", function: "x", expr: "exp(a*t)", settings: 1, plotted: false }))
    .toBe("x matches exp(a*t) at 1 tested setting");
  expect(manimCheckLine({ kind: "invariant", function: "x", property: "bounded", bound: 2, settings: 9, plotted: false }))
    .toBe("x stays within ±2 at 9 tested settings");
});

it("plays a Manim figure with its transcript, checks and the frame-by-frame line", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [manimView()], richPending: [] });
  render(<Harness />);
  const line = await screen.findByRole("button", { name: /animation/ });
  expect(line.textContent).toContain(RICH_FRAME.manim);
  expect(line.textContent).not.toContain("matches the book");
  fireEvent.click(line);
  expect(await screen.findByLabelText("Why it spirals")).toBeTruthy();  // the shared player's video
  expect(screen.getByText(/the curve is drawn from x, which matches exp\(a\*t\)\*cos\(b\*t\)/)).toBeTruthy();
  expect(screen.getByText(/the video itself is not checked frame by frame/)).toBeTruthy();
  expect(screen.queryByText("It turns as it decays.")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: RICH_FRAME.transcript }));
  expect(screen.getByText("It turns as it decays.")).toBeTruthy();
});

it("shows the quick figure with its fuller line, then one line with two versions (G-SM21)", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  api.readerFigures.mockResolvedValueOnce({ extractionId: "ext_prob", figures: [quickView(PENDING)], richPending: [] });
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", richPending: [], figures: [quickView({
    state: "ready", tier: "manim", phase: null, reason: null, richJobId: null, figure: manimView() })] });
  render(<Harness />);
  const line = await screen.findByRole("button", { name: /interactive version/ });
  fireEvent.click(line);
  expect(document.querySelector("[data-figure-body]")).not.toBeNull();
  expect(screen.getByText(RICH_FRAME.fullerPending)).toBeTruthy();
  const focused = screen.getByRole("button", { name: "elsewhere" });
  focused.focus();
  await act(async () => { await vi.advanceTimersByTimeAsync(RICH_POLL_MS + 10); });
  expect(await screen.findByText(RICH_FRAME.fullerReady)).toBeTruthy();
  expect(document.activeElement).toBe(focused);  // the cue never moves focus
  expect(document.querySelectorAll("[data-figure]").length).toBe(1);  // one figure line
  expect(document.querySelector("[role=alert], [role=status]")).toBeNull();  // no toast
  fireEvent.click(screen.getByRole("button", { name: RICH_FRAME.open }));
  expect(document.querySelector("[data-manim-figure]")).not.toBeNull();
  expect(document.querySelector("[data-figure-body]")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: RICH_FRAME.quick }));
  expect(document.querySelector("[data-figure-body]")).not.toBeNull();
  // Collapsed: the cue sits on the figure's own line, nowhere else.
  fireEvent.click(screen.getByRole("button", { name: /interactive version/ }));
  expect(document.querySelector("[data-fuller-collapsed]")?.textContent).toContain(RICH_FRAME.collapsedReady);
});

it("a failed fuller version keeps the quick one and says why on request", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", richPending: [], figures: [quickView({
    state: "failed", tier: "manim", phase: null, reason: "x(0, -1, 1) = 1, but sin(t) = 0 there", richJobId: null,
    figure: null })] });
  render(<Harness />);
  fireEvent.click(await screen.findByRole("button", { name: /interactive version/ }));
  expect(screen.getByText(RICH_FRAME.fullerFailed)).toBeTruthy();
  expect(document.querySelector("[data-figure-body]")).not.toBeNull();
  fireEvent.click(screen.getByRole("button", { name: RICH_FRAME.why }));
  expect(screen.getByText(/but sin\(t\) = 0 there/)).toBeTruthy();
});

it("cancel on the fuller line cancels only the rich job", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [quickView(PENDING)], richPending: [] });
  api.figureRichCancel.mockResolvedValue({ richJobId: "ijob_1", state: "cancelled" });
  render(<Harness />);
  fireEvent.click(await screen.findByRole("button", { name: /interactive version/ }));
  fireEvent.click(screen.getByRole("button", { name: RICH_FRAME.cancel }));
  expect(api.figureRichCancel).toHaveBeenCalledWith({ richJobId: "ijob_1" });
  expect(document.querySelector("[data-figure-body]")).not.toBeNull();
});

it("a rich-only build is a pending line naming its phase, with cancel", async () => {
  const line: FigureRichPendingDto = { requestId: "frq_1", extractionId: "ext_prob", anchorSpanId: "p3",
    tier: "manim", goalText: "the spiral", state: "pending", phase: "checking", reason: null, richJobId: "ijob_2" };
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [], richPending: [line] });
  api.figureRichCancel.mockResolvedValue({ richJobId: "ijob_2", state: "cancelled" });
  render(<Harness />);
  expect(await screen.findByText(`${RICH_PHASES.checking} · keep reading`)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: RICH_FRAME.cancel }));
  expect(api.figureRichCancel).toHaveBeenCalledWith({ richJobId: "ijob_2" });
  expect(document.querySelector("[data-rich-pending]")).toBeNull();
});

it("asks the Manim opt-in once, inline, after a press (allow · not now)", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [], richPending: [] });
  api.figureRequest.mockResolvedValue({ jobId: "j1", kind: "figure_build", askId: null, state: "pending", result: null });
  api.readerFigureJob.mockReturnValue(new Promise(() => undefined));
  api.figureManimOptIn.mockResolvedValue({ manimOptIn: "standing" });
  render(<Harness contract={{ ...CONTRACT, rich: { manimOptIn: "ask" } }} />);
  expect(document.querySelector("[data-manim-opt-in]")).toBeNull();  // never before a press
  fireEvent.click(screen.getByRole("button", { name: "show me" }));
  expect(await screen.findByText(RICH_FRAME.optIn)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: RICH_FRAME.allow }));
  expect(api.figureManimOptIn).toHaveBeenCalledWith({ choice: "allow" });
  expect(document.querySelector("[data-manim-opt-in]")).toBeNull();
});

it("switched off (no rich contract) a stored animation shows as can't show this kind here", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [{
    ...manimView({ verification: "unsupported", label: RICH_FRAME.cantShow, unsupportedKind: "an animation" }),
    tier: undefined, manim: undefined, fuller: undefined }] });
  render(<Harness contract={{ predictions: true, region: true, revisions: true }} />);
  expect(await screen.findByText(RICH_FRAME.cantShow)).toBeTruthy();
  expect(screen.queryByText(/needs an animation/)).toBeNull();
});

it("a rich-only build that ended with no figure says why and tries again (Codex review F9)", async () => {
  const line: FigureRichPendingDto = { requestId: "frq_1", extractionId: "ext_prob", anchorSpanId: "p3",
    tier: "manim", goalText: "the spiral", state: "failed", phase: null, reason: "interrupted when LearnLoop stopped",
    richJobId: "ijob_3" };
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [], richPending: [line] });
  api.figureRichRetry.mockResolvedValue({ richJobId: "ijob_3", state: "pending" });
  render(<Harness />);
  expect(await screen.findByText(RICH_FRAME.richFailed)).toBeTruthy();
  expect(screen.queryByText("interrupted when LearnLoop stopped")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: RICH_FRAME.why }));
  expect(screen.getByText("interrupted when LearnLoop stopped")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: RICH_FRAME.tryAgain }));
  expect(api.figureRichRetry).toHaveBeenCalledWith({ richJobId: "ijob_3" });
  expect(await screen.findByText(`${RICH_PHASES.writing} · keep reading`)).toBeTruthy();
});

it("not right? on an animation sends the note, or asks for a different kind (Codex review F11)", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [manimView()], richPending: [] });
  api.readerFigureRevise.mockResolvedValue({ jobId: "j2", kind: "figure_build", askId: null, state: "pending", result: null });
  api.readerFigureJob.mockReturnValue(new Promise(() => undefined));
  render(<Harness />);
  fireEvent.click(await screen.findByRole("button", { name: /animation/ }));
  fireEvent.click(screen.getByRole("button", { name: RICH_FRAME.notRight }));
  fireEvent.change(screen.getByLabelText(RICH_FRAME.notRight), { target: { value: "the spiral should be red" } });
  fireEvent.click(screen.getByRole("button", { name: RICH_FRAME.askBetter }));
  expect(api.readerFigureRevise).toHaveBeenCalledWith({ figureId: "fig_rich", note: "the spiral should be red" });
  fireEvent.click(screen.getByRole("button", { name: RICH_FRAME.notRight }));
  fireEvent.change(screen.getByLabelText(RICH_FRAME.notRight), { target: { value: "a picture is enough" } });
  fireEvent.click(screen.getByLabelText(RICH_FRAME.differentKind, { exact: false }));
  fireEvent.click(screen.getByRole("button", { name: RICH_FRAME.askBetter }));
  expect(api.readerFigureRevise).toHaveBeenLastCalledWith({ figureId: "fig_rich", note: "a picture is enough",
    differentKind: true });
});

it("without revisions in the contract an animation has no not right?", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [manimView()], richPending: [] });
  render(<Harness contract={{ ...CONTRACT, revisions: false }} />);
  fireEvent.click(await screen.findByRole("button", { name: /animation/ }));
  expect(screen.queryByRole("button", { name: RICH_FRAME.notRight })).toBeNull();
});
