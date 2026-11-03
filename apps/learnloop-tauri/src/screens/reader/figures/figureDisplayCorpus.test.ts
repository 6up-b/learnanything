// RW5c (G22's extension): formatValue, String(v) and the derived bounds against the corpus
// the Python twins read too (tests/test_rw5c_display_twins.py).
import katex from "katex";
import { expect, it } from "vitest";
import type { FigureElementDto } from "../../../api/dto";
import { derivedWords } from "./figureLabels";
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

const mathmlChildren = (tex: string): Element[] => {
  const holder = document.createElement("div");
  holder.innerHTML = katex.renderToString(tex, { output: "mathml", strict: "ignore" });
  const semantics = holder.querySelector("semantics")!;
  return [...semantics.children].filter((child) => child.tagName.toLowerCase() !== "annotation");
};
const flat = (elements: Element[]): Element[] => elements.flatMap((element) => (element.tagName.toLowerCase() === "mrow" ? flat([...element.children]) : [element]));
const markup = (elements: Element[]): string[] => elements.map((element) => element.outerHTML);
const SIGNS = new Set(["+", "−", "±", "∓", "⋅", "×", "∗", "/", "∕", ",", "=", "<", ">"]);

/** All of the left-hand side is what the template applies to, in KaTeX's own output: one fence, or no sign outside its brackets (tests/katex_meaning.py's twin). */
function wholeInScope(tex: string, lhs: string, kind: string): boolean {
  const children = [...mathmlChildren(tex)[0].children];
  const tag = (element: Element) => element.tagName.toLowerCase();
  let start: number;
  let end = children.length;
  if (kind === "shade") {
    start = children.findIndex((child) => tag(child) === "mtext" && child.textContent?.includes("area")) + 1;
    end = children.findIndex((child, index) => index >= start && tag(child) === "mtext" && child.textContent?.includes("from"));
  } else {
    start = children.findIndex((child) => ["msubsup", "munderover", "msub", "munder"].includes(tag(child))) + 1;
    if (kind === "integral") end = children.length - 3;
  }
  const operand = children.slice(start, end);
  if (kind === "shade") {
    // KaTeX joins adjacent text: \\text{area under } \\text{Var}(k) is one mtext, then (k).
    const rest = (children[start - 1].textContent ?? "").replace(/\u00a0/g, " ").split("area under ")[1];
    if (rest) {
      const merged = children[start - 1].cloneNode() as Element;
      merged.textContent = rest;
      operand.unshift(merged);
    }
  }
  const expected = markup(flat(mathmlChildren(lhs)));
  if (operand.length === 1 && tag(operand[0]) === "mrow") {
    const inner = [...operand[0].children];
    const first = inner[0];
    const last = inner[inner.length - 1];
    if (first?.getAttribute("fence") === "true" && last?.getAttribute("fence") === "true" && first.textContent === "(" && last.textContent === ")"
      && JSON.stringify(markup(flat(inner.slice(1, -1)))) === JSON.stringify(expected)) return true;
  }
  const shown = flat(operand);
  if (JSON.stringify(markup(shown)) !== JSON.stringify(expected)) return false;
  let depth = 0;
  for (const element of shown) {
    if (tag(element) !== "mo") continue;
    const text = element.textContent ?? "";
    if ("([{⟨".includes(text)) depth += 1;
    else if (")]}⟩".includes(text)) depth -= 1;
    else if (depth === 0 && SIGNS.has(text)) return false;
  }
  return true;
}

it("the derived words are the Python writer's, and hold the whole left-hand side in KaTeX's own output (Astra A2)", () => {
  expect(corpus.templates.some((item) => item.compound)).toBe(true);
  for (const item of corpus.templates) {
    const element = { template: { kind: item.kind, panel: 0, index: 0, bodyTex: item.body_tex, bodyPlain: item.body_plain, variable: "k" }, tex: "", plain: "" } as unknown as FigureElementDto;
    const bounds = { ...item.bounds, integers: item.bounds.integers as [number, number] | null };
    const words = derivedWords(element, bounds);
    expect(words.tex, item.lhs).toBe(item.tex);
    expect(words.plain, item.lhs).toBe(item.plain);
    expect(wholeInScope(words.tex, item.lhs, item.kind), `${item.kind} ${item.tex}`).toBe(true);
  }
  // The reading has teeth: Astra's own label fails it.
  expect(wholeInScope("\\sum_{k=0}^{2} 1-F(k)", "1-F(k)", "sum")).toBe(false);
});
