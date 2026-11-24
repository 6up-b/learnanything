// The desks' fixture figure (project-authored spec from the figure golden corpus): what Show me builds on a passage
// of the synthetic book, for the harness's Show me run and the companion's figure (spec §13.1).
import type { FigureViewDto } from "../../api/dto";
import corpus from "../../screens/reader/figures/figureGoldenCorpus.json";
import { FIXTURE_SOURCES } from "./sources";

const SPEC = corpus.figures.find((item) => item.id === "two_sided_exponential")!.spec;

export function fixtureFigure(spanId: string): FigureViewDto {
  const { book } = FIXTURE_SOURCES;
  return {
    figureId: "fx_figure_softmax", extractionId: book.extractionId, spanIds: [spanId], anchorSpanId: spanId, region: null, origin: "show_me",
    verification: "verified", shown: true, labelCode: "illustrative", kind: "reconstructed", label: "AI-built illustration",
    reason: null, unsupportedKind: null, supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-11-23T00:00:00",
    specJson: JSON.stringify(SPEC), demonstrates: "how a parameter moves the curve", assumptions: [], predictions: [],
    goalText: "show me this passage", grounding: "passages",
    passages: [{ extractionId: book.extractionId, spanId, sourceTitle: "Softmax, a short book", page: 2 }],
  } as unknown as FigureViewDto;
}
