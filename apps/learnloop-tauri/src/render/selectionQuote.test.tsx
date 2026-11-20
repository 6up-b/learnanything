// UX-26 (walk student-2 #87): a selection over rendered math became its quote through the selection's text, which
// holds every KaTeX layer of each formula (its MathML, its TeX annotation in jsdom, its HTML), so Ask's "§ from the
// book" and what the tutor read showed each formula two or three times. `selectionQuote` takes each selected formula
// once, as its own TeX source (the <annotation encoding="application/x-tex"> KaTeX keeps beside its MathML).
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MarkdownMath } from "./MarkdownMath";
import { selectionQuote } from "./mathSnippet";

afterEach(cleanup);

// The sample chapter's sentence the walk quoted (samples/understanding-linear-algebra-symmetric-matrices-and-variance.html).
const PASSAGE =
  "orthonormal vectors into a matrix \\(Q\\) produces an orthogonal matrix, which means that \\(Q^T = Q^{-1}\\text{.}\\) We then have";

function shown(value: string): HTMLElement {
  return render(<MarkdownMath value={value} />).container;
}

/** The desktop Reader's quote: the function over the selection, whitespace squeezed as before. */
function quote(range: Range): string {
  const selection = window.getSelection()!;
  selection.removeAllRanges();
  selection.addRange(range);
  return selectionQuote(range, selection.toString()).replace(/\s+/g, " ").trim();
}

function textNodes(root: Node): Text[] {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const out: Text[] = [];
  for (let node = walker.nextNode(); node; node = walker.nextNode()) out.push(node as Text);
  return out;
}

describe("UX-26: a selection's quote takes each formula once, as its TeX", () => {
  it("the walk's passage: inline math in a sentence", () => {
    const page = shown(PASSAGE);
    const range = document.createRange();
    range.selectNodeContents(page);
    expect(quote(range)).toBe(
      "orthonormal vectors into a matrix $Q$ produces an orthogonal matrix, which means that $Q^T = Q^{-1}\\text{.}$ We then have"
    );
  });

  it("a selection that starts or ends inside a formula takes the formula whole", () => {
    const page = shown(PASSAGE);
    const words = textNodes(page);
    const start = words.find((node) => node.data.includes("into a matrix"))!;
    // The last text node of the second formula's HTML layer: the selection ends inside it.
    const inFormula = textNodes(page.querySelectorAll(".katex")[1]).filter((node) => !node.parentElement!.closest("annotation"));
    const range = document.createRange();
    range.setStart(start, start.data.indexOf("matrix"));
    range.setEnd(inFormula[1], 0);
    expect(quote(range)).toBe("matrix $Q$ produces an orthogonal matrix, which means that $Q^T = Q^{-1}\\text{.}$");
    // Starting inside the first formula's MathML.
    const firstFormula = textNodes(page.querySelectorAll(".katex")[0])[0];
    const from = document.createRange();
    from.setStart(firstFormula, 0);
    from.setEnd(words.find((node) => node.data.includes("produces"))!, " produces".length);
    expect(quote(from)).toBe("$Q$ produces");
  });

  it("display math is quoted as $$…$$", () => {
    const page = shown("We then have\n\n$$\nA = QDQ^{-1} = QDQ^T.\n$$\n\nIn this case, A is orthogonally diagonalizable.");
    const range = document.createRange();
    range.selectNodeContents(page);
    expect(quote(range)).toBe("We then have $$A = QDQ^{-1} = QDQ^T.$$ In this case, A is orthogonally diagonalizable.");
  });

  it("a selection with no math is the selection's text, byte for byte", () => {
    const page = shown("A plain  passage,\nwith no formula at all.");
    const range = document.createRange();
    range.selectNodeContents(page);
    const selection = window.getSelection()!;
    selection.removeAllRanges();
    selection.addRange(range);
    const asSelected = selection.toString();
    expect(selectionQuote(range, asSelected)).toBe(asSelected);
    expect(selectionQuote(range, "  as the browser gave it\n")).toBe("  as the browser gave it\n");
  });
});
