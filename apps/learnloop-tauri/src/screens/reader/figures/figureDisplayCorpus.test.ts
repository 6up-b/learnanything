// RW5c (G22's extension): formatValue, String(v) and the derived bounds against the corpus
// the Python twins read too (tests/test_rw5c_display_twins.py).
import { expect, it } from "vitest";
import { formatValue } from "./FigurePanels";
import { compileSpec, defaults, derivedBounds, type FigureSpec } from "./figureSpec";
import corpus from "./figureDisplayCorpus.json";

it("formatValue and String(v) are the corpus's", () => {
  for (const item of corpus.values) {
    expect(formatValue(item.value)).toBe(item.number);
    expect(formatValue(item.value, "percent")).toBe(item.percent);
    expect(String(item.value)).toBe(item.string);
  }
});

it("the derived bounds are the Python evaluator's, case by case", () => {
  for (const item of corpus.bounds) {
    const compiled = compileSpec(item.spec as unknown as FigureSpec);
    const params = (item as { params?: Record<string, number> }).params ?? {};
    const found = derivedBounds(compiled, item.panel, item.kind as "shade" | "highlight" | "integral" | "sum", item.index, { ...defaults(compiled), ...params });
    expect(found, item.name).toEqual(item.expected);
  }
});
