// What a selection in a desk window asks about (spec §8.3, §8.6): its passages and its text, with rendered math
// read back as its TeX source rather than repeated symbols.
import { afterEach, describe, expect, it } from "vitest";
import { clipQuote, quoteOf, readWindowSelection } from "./selection";

const added: HTMLElement[] = [];

afterEach(() => {
  for (const element of added.splice(0)) element.remove();
  window.getSelection()?.removeAllRanges();
});

function windowWith(id: string, html: string): HTMLElement {
  const host = document.createElement("div");
  host.setAttribute("data-desk-window", id);
  host.innerHTML = html;
  document.body.append(host);
  added.push(host);
  return host;
}

describe("a selection in a window", () => {
  it("names every passage it touches and its text", () => {
    const host = windowWith("w1", '<p data-span-id="s1">first passage</p><p data-span-id="s2">second passage</p><p data-span-id="s3">third</p>');
    const range = document.createRange();
    range.setStart(host.querySelector('[data-span-id="s1"]')!.firstChild!, 6);
    range.setEnd(host.querySelector('[data-span-id="s2"]')!.firstChild!, 6);
    window.getSelection()!.addRange(range);
    const selected = readWindowSelection("w1", null);
    expect(selected?.spanIds).toEqual(["s1", "s2"]);
    expect(selected?.quote).toBe("passagesecond");
  });

  it("is null when the selection lies in another window", () => {
    windowWith("w1", '<p data-span-id="s1">text</p>');
    const other = windowWith("w2", '<p data-span-id="t1">other</p>');
    const range = document.createRange();
    range.selectNodeContents(other.querySelector("p")!);
    window.getSelection()!.addRange(range);
    expect(readWindowSelection("w1", null)).toBeNull();
  });

  it("reads rendered math by its TeX source, once", () => {
    const host = windowWith("w1", '<p data-span-id="s1">so <span class="katex"><span class="katex-mathml"><math><semantics><mrow><mi>e</mi></mrow><annotation encoding="application/x-tex">e^{c}</annotation></semantics></math></span><span class="katex-html">ec</span></span> cancels</p>');
    const range = document.createRange();
    range.selectNodeContents(host.querySelector("p")!);
    expect(quoteOf(range)).toBe("so $e^{c}$ cancels");
  });
});

describe("formula selections (RD3 review)", () => {
  const MATH = '<span class="katex"><span class="katex-mathml"><math><semantics><mrow><mi>e</mi></mrow><annotation encoding="application/x-tex">e^{c}</annotation></semantics></math></span><span class="katex-html"><span class="base">ec</span></span></span>';

  it("a selection that starts inside a formula's drawn copy takes the whole formula by its TeX", () => {
    const host = windowWith("w1", `<p data-span-id="s1">so ${MATH} cancels here</p>`);
    const drawn = host.querySelector(".katex-html .base")!.firstChild!;
    const range = document.createRange();
    range.setStart(drawn, 1);
    range.setEnd(host.querySelector("p")!.lastChild!, 8);
    expect(quoteOf(range)).toBe("$e^{c}$ cancels");
  });

  it("a displayed formula keeps display delimiters", () => {
    const host = windowWith("w1", `<div data-span-id="s1"><span class="katex-display">${MATH}</span></div>`);
    const range = document.createRange();
    range.selectNodeContents(host.querySelector("div")!);
    expect(quoteOf(range)).toBe("$$e^{c}$$");
  });

  it("a long quote is cut before a formula, never inside one", () => {
    const quote = `${"word ".repeat(10)}$\\frac{a}{b} + \\sum_{k} c_k$ after`;
    const cut = clipQuote(quote, 60);
    expect(cut.length).toBeLessThanOrEqual(60);
    expect((cut.match(/\$/g) ?? []).length % 2).toBe(0);
    expect(clipQuote("short", 60)).toBe("short");
    expect(clipQuote(`$$${"x".repeat(80)}$$ tail`, 40)).toBe("");
  });
});
