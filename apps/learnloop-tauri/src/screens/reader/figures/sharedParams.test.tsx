// Shared parameters (spec §13.1): every instance of one figure shares its parameters, so dragging one (the book's
// inset, the companion's widget) moves the others; another figure keeps its own.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FigureViewDto } from "../../../api/dto";
import corpus from "./figureGoldenCorpus.json";
import { FigureInline } from "./FigureInline";
import { resetSharedParamsForTests } from "./sharedParams";
import { figurePlacementKey, type FiguresCtl } from "./useFigures";

vi.mock("../../../api/client", () => ({ api: { readerLogActivity: vi.fn(async () => ({ recorded: 0 })) } }));

const SPEC = corpus.figures.find((item) => item.id === "two_sided_exponential")!.spec;

function figure(figureId: string, anchorSpanId: string): FigureViewDto {
  return {
    figureId, extractionId: "ext", spanIds: [anchorSpanId], anchorSpanId, region: null, origin: "selection", verification: "verified", shown: true,
    labelCode: "illustrative", kind: "reconstructed", label: "", reason: null, unsupportedKind: null, supersedesId: null, revisionNote: null,
    versions: 1, createdAt: "2026-11-23T00:00:00", specJson: JSON.stringify(SPEC), demonstrates: "", assumptions: [], predictions: [],
  } as FigureViewDto;
}

function ctl(shown: FigureViewDto): FiguresCtl {
  return {
    enabled: true, contract: { predictions: false, region: false, revisions: false }, figures: [shown], pending: [], expandedKey: figurePlacementKey(shown),
    setExpanded: () => undefined, request: async () => "skipped", revise: () => undefined, predict: async () => null, explain: async () => null,
    under: () => ({ figures: [], pending: [], richPending: [], followed: [] }), followed: [], follow: async () => false, richPending: [],
    cancelRich: () => undefined, retryRich: () => undefined, manimOptIn: null, optInSpanId: null, answerManimOptIn: () => undefined,
  };
}

beforeEach(() => resetSharedParamsForTests());
afterEach(cleanup);

it("two instances of one figure move together; another figure keeps its own values", () => {
  const inset = figure("fig_shared", "p1");
  const companion = figure("fig_shared", "p9");
  const other = figure("fig_other", "p1");
  render(
    <div>
      <div data-testid="inset"><FigureInline figure={inset} ctl={ctl(inset)} /></div>
      <div data-testid="companion"><FigureInline figure={companion} ctl={ctl(companion)} /></div>
      <div data-testid="other"><FigureInline figure={other} ctl={ctl(other)} /></div>
    </div>,
  );
  const sliderIn = (id: string) => screen.getByTestId(id).querySelector<HTMLInputElement>('input[type="range"]')!;
  const before = sliderIn("other").value;
  const max = sliderIn("inset").max;
  fireEvent.change(sliderIn("inset"), { target: { value: max } });
  expect(sliderIn("companion").value).toBe(sliderIn("inset").value);
  expect(sliderIn("inset").value).not.toBe(before);
  expect(sliderIn("other").value).toBe(before);
});
