// @vitest-environment node
// The selection model on real layout-model geometry (reader-pdf-selection):
// the GLM-OCR answer for pages 1-5 of Wei Tang, Kangning Cui, Raymond H.
// Chan, arXiv:2302.11517v2 (CC BY 4.0), as the extraction maps it (see the
// fixture's credit). The Reader has no text layer for it here, as for a scan:
// every word is placed by estimate inside GLM's boxes.
//
// It also writes down the selection contract with the sidecar
// (selection_contract.json): the nodes these selections send. The Python
// side (tests/test_reader_pdf_selection.py) anchors every one of them and
// requires an exact anchor with the same offsets. UPDATE_PDF_SELECTION_CONTRACT=1
// rewrites the file; otherwise the model must still produce it exactly.
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { beforeAll, describe, expect, it } from "vitest";
import type { ReaderPdfBlockDto } from "../../api/dto";
import { hitTest, rangeRects, selectionNodes, selectionText, SelectionModel, type Pos, type SelRange, type SpanNode } from "./model";
import { buildPdf, readPdf } from "./testing/syntheticPdf";
import { SYNTHETIC_BLOCKS, SYNTHETIC_PAGES } from "./testing/syntheticBook";

const here = __dirname;
const arxiv = JSON.parse(readFileSync(join(here, "fixtures", "arxiv_2302_11517_glm_blocks.json"), "utf8")) as {
  credit: string;
  blocks: ReaderPdfBlockDto[];
};

let model: SelectionModel;
let synthetic: SelectionModel;

beforeAll(async () => {
  model = new SelectionModel(arxiv.blocks);
  synthetic = new SelectionModel(SYNTHETIC_BLOCKS);
  for (const page of await readPdf(buildPdf(SYNTHETIC_PAGES))) synthetic.setPageText(page.page, page.items, page.transform, page.styles);
});

function find(on: SelectionModel, spanId: string, text: string, nth = 0): Pos {
  const block = on.blockIndex(spanId) as number;
  const source = on.blocks[block].text;
  const hits = on.units(block).flatMap((unit, index) => (source.slice(unit.start, unit.end) === text ? [index] : []));
  if (hits[nth] === undefined) throw new Error(`no ${text} in ${spanId}`);
  return { block, unit: hits[nth] };
}

function last(on: SelectionModel, spanId: string): Pos {
  const block = on.blockIndex(spanId) as number;
  return { block, unit: on.unitCount(block) - 1 };
}

function centre(on: SelectionModel, pos: Pos): [number, number, number] {
  const box = on.geometry(pos.block).boxes[pos.unit][0];
  return [on.blocks[pos.block].page, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2];
}

describe("GLM-OCR geometry with no text layer (arXiv:2302.11517v2, CC BY 4.0)", () => {
  it("lays every text block's words out inside its box, line by line", () => {
    const abstract = model.blockIndex("s4") as number;
    const geometry = model.geometry(abstract);
    expect(geometry.source).toBe("estimated");
    const box = model.blocks[abstract].bbox;
    expect(geometry.lines.length).toBeGreaterThan(10);
    for (const boxes of geometry.boxes) {
      for (const [x0, y0, x1, y1] of boxes) {
        expect(x0).toBeGreaterThanOrEqual(box[0] - 0.01);
        expect(x1).toBeLessThanOrEqual(box[2] + 0.01);
        expect(y0).toBeGreaterThanOrEqual(box[1] - 0.01);
        expect(y1).toBeLessThanOrEqual(box[3] + 0.01);
      }
    }
    // A click on any word lands on that word.
    const pos = find(model, "s4", "retinopathy");
    expect(hitTest(model, ...centre(model, pos))).toEqual(pos);
  });

  it("reads the left column, then the right one", () => {
    const ranges: SelRange[] = [{ anchor: last(model, "s4"), head: find(model, "s8", "learning") }];
    expect(selectionNodes(model, ranges).map((node) => node.spanId)).toEqual(["s4", "s5", "s6", "s7", "s8"]);
    expect(selectionText(model, ranges).split("\n\n").slice(1, 4)).toEqual(["1. INTRODUCTION", "2. RELATED WORKS", "2.1. Medical Image Segmentation"]);
  });

  it("takes the loss formula and the results table whole, as LaTeX and Markdown", () => {
    const formula = model.blocks[model.blockIndex("s12") as number];
    const [page, x, y] = [formula.page, (formula.bbox[0] + formula.bbox[2]) / 2, (formula.bbox[1] + formula.bbox[3]) / 2];
    const pos = hitTest(model, page, x, y) as Pos;
    expect(selectionText(model, [{ anchor: pos, head: pos }])).toBe(formula.text.trim());
    expect(formula.text.startsWith("$$\n\\mathcal {L}")).toBe(true);
    const table = model.blocks[model.blockIndex("s15") as number];
    const cell = hitTest(model, table.page, table.bbox[0] + 5, table.bbox[1] + 5) as Pos;
    expect(selectionText(model, [{ anchor: cell, head: cell }])).toBe(table.text.trim());
    expect(rangeRects(model, [{ anchor: cell, head: cell }], table.page)).toEqual([table.bbox]);
  });

  it("selects nothing on a figure with no text (never its caption)", () => {
    const figure = arxiv.blocks.find((block) => block.blockType === "Figure") as ReaderPdfBlockDto;
    expect(figure.text).toBe("");
    const [x0, y0, x1, y1] = figure.bbox;
    expect(hitTest(model, figure.page, (x0 + x1) / 2, (y0 + y1) / 2)).toBeNull();
  });

  it("drags over a page break past the figure into its caption", () => {
    const ranges: SelRange[] = [{ anchor: find(model, "s8", "segmentation"), head: find(model, "s10", "Illustration") }];
    expect(selectionNodes(model, ranges).map((node) => node.spanId)).toEqual(["s8", "s10"]);
  });
});

// ---- the contract with the sidecar --------------------------------------------------

interface ContractSelection {
  name: string;
  extraction: "synthetic" | "arxiv";
  nodes: SpanNode[];
}

function contractSelections(): ContractSelection[] {
  const s = (on: SelectionModel, ranges: SelRange[]) => selectionNodes(on, ranges);
  const range = (anchor: Pos, head: Pos): SelRange[] => [{ anchor, head }];
  return [
    { name: "two columns in reading order", extraction: "synthetic", nodes: s(synthetic, range(find(synthetic, "s2", "quietly."), find(synthetic, "s3", "begins"))) },
    { name: "a hyphenated word", extraction: "synthetic", nodes: s(synthetic, range(find(synthetic, "s2", "long"), find(synthetic, "s2", "of"))) },
    { name: "over a page break and its footnote", extraction: "synthetic", nodes: s(synthetic, range(find(synthetic, "s3", "column."), find(synthetic, "s5", "on"))) },
    { name: "a display formula", extraction: "synthetic", nodes: s(synthetic, range(last(synthetic, "s6"), last(synthetic, "s6"))) },
    { name: "a table", extraction: "synthetic", nodes: s(synthetic, range(last(synthetic, "s8"), last(synthetic, "s8"))) },
    { name: "inline maths", extraction: "synthetic", nodes: s(synthetic, range(find(synthetic, "s9", "positive;"), find(synthetic, "s9", "holds"))) },
    { name: "letters outside the BMP on a scan", extraction: "synthetic", nodes: s(synthetic, range(find(synthetic, "s11", "Vectors"), find(synthetic, "s11", "𝐂²"))) },
    { name: "arxiv: across the columns", extraction: "arxiv", nodes: s(model, range(find(model, "s4", "retinopathy"), find(model, "s8", "learning"))) },
    { name: "arxiv: authors with superscripts", extraction: "arxiv", nodes: s(model, range(find(model, "s2", "Tang"), find(model, "s2", "Cui"))) },
    { name: "arxiv: the loss formula", extraction: "arxiv", nodes: s(model, range(last(model, "s12"), last(model, "s12"))) },
    { name: "arxiv: the results table", extraction: "arxiv", nodes: s(model, range(last(model, "s15"), last(model, "s15"))) },
    { name: "arxiv: a reference", extraction: "arxiv", nodes: s(model, range(find(model, "s19", "W."), find(model, "s19", "Abulkhair,"))) },
  ];
}

describe("the selection contract with the sidecar", () => {
  it("sends, for every selection, each block's exact slice with code-point offsets", () => {
    const selections = contractSelections();
    for (const selection of selections) {
      const blocks = selection.extraction === "arxiv" ? arxiv.blocks : SYNTHETIC_BLOCKS;
      for (const node of selection.nodes) {
        const block = blocks.find((candidate) => candidate.spanId === node.spanId) as ReaderPdfBlockDto;
        expect(Array.from(block.text ?? "").slice(node.start, node.end).join("")).toBe(node.quote);
      }
    }
    const contract = {
      about:
        "The nodes the Reader's PDF selection model sends for these selections (written by arxiv.test.ts). " +
        "tests/test_reader_pdf_selection.py anchors each and requires an exact anchor with these offsets.",
      blocks: { synthetic: SYNTHETIC_BLOCKS },
      selections,
    };
    const path = join(here, "fixtures", "selection_contract.json");
    if (process.env.UPDATE_PDF_SELECTION_CONTRACT === "1") writeFileSync(path, JSON.stringify(contract, null, 1) + "\n", "utf8");
    expect(JSON.parse(readFileSync(path, "utf8"))).toEqual(JSON.parse(JSON.stringify(contract)));
  });
});
