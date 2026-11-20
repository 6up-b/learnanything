// One-line snippets of passages that hold math: the Ask chip's quote (rendered, so it is clipped whole formulas at a
// time) and the plain lines of Today's threads and citation labels (text, so their formulas become readable words).
// A snippet cut inside a formula leaves an unclosed "\(" that no renderer reads as math, and a plain line that keeps
// TeX shows "\(\uvec\)" to the learner.

/** A closed formula: \( \), \[ \], $$ $$ or $ $ (the delimiters MarkdownMath reads). */
const MATH = /\\\(([\s\S]*?)\\\)|\\\[([\s\S]*?)\\\]|\$\$([\s\S]*?)\$\$|\$([^$\n]+?)\$/g;

/**
 * `text` clipped to about `max` characters with "…", never inside a formula: a formula the cut would split is left
 * out whole (or kept whole when it starts the snippet and is short enough), and an unclosed opener before the cut is
 * dropped with what follows it.
 */
export function clipMath(text: string, max: number): string {
  if (text.length <= max) return text;
  let cut = max;
  for (const match of text.matchAll(MATH)) {
    const start = match.index ?? 0;
    const end = start + match[0].length;
    if (start >= cut) break;
    if (end > cut) {
      // Keep a leading formula that fits in twice the room; otherwise stop before it.
      cut = start < max / 3 && end <= max * 2 ? end : start;
      break;
    }
  }
  return `${dropUnclosedOpener(text.slice(0, cut)).trimEnd()}…`;
}

/** `head` without an unclosed formula at its end (a label the sidecar already cut, or a cut mid-formula). */
function dropUnclosedOpener(head: string): string {
  const closed = head.replace(MATH, (whole) => " ".repeat(whole.length));
  const opener = Math.max(closed.lastIndexOf("\\("), closed.lastIndexOf("\\["), closed.lastIndexOf("$"));
  return opener >= 0 ? head.slice(0, opener) : head;
}

const GREEK: Record<string, string> = {
  alpha: "α", beta: "β", gamma: "γ", delta: "δ", epsilon: "ε", varepsilon: "ε", zeta: "ζ", eta: "η", theta: "θ",
  vartheta: "ϑ", iota: "ι", kappa: "κ", lambda: "λ", mu: "μ", nu: "ν", xi: "ξ", pi: "π", rho: "ρ", sigma: "σ",
  tau: "τ", upsilon: "υ", phi: "φ", varphi: "φ", chi: "χ", psi: "ψ", omega: "ω", Gamma: "Γ", Delta: "Δ",
  Theta: "Θ", Lambda: "Λ", Xi: "Ξ", Pi: "Π", Sigma: "Σ", Phi: "Φ", Psi: "Ψ", Omega: "Ω"
};

const SYMBOLS: Record<string, string> = {
  cdot: "·", times: "×", div: "÷", pm: "±", mp: "∓", le: "≤", leq: "≤", ge: "≥", geq: "≥", ne: "≠", neq: "≠",
  approx: "≈", sim: "∼", equiv: "≡", in: "∈", notin: "∉", subset: "⊂", subseteq: "⊆", supset: "⊃", cup: "∪",
  cap: "∩", to: "→", rightarrow: "→", leftarrow: "←", Rightarrow: "⇒", Leftrightarrow: "⇔", mapsto: "↦",
  infty: "∞", sum: " ∑", prod: " ∏", int: " ∫", partial: "∂", nabla: "∇", perp: "⊥", parallel: "∥", ldots: "…",
  cdots: "⋯", dots: "…", forall: "∀", exists: "∃", emptyset: "∅", circ: "∘", langle: "⟨", rangle: "⟩",
  vert: "|", lvert: "|", rvert: "|", mid: "|", prime: "′", quad: " ", qquad: " "
};

/** Commands that only style or size what follows: dropped, their argument kept. */
const STYLE = new Set([
  "text", "textbf", "textit", "emph", "mathrm", "mathbf", "mathbb", "mathcal", "mathfrak", "mathit", "mathsf", "mathtt",
  "boldsymbol", "bm", "operatorname", "hat", "widehat", "bar", "overline", "underline", "vec", "tilde", "widetilde",
  "left", "right", "big", "Big", "bigl", "bigr", "Bigl", "Bigr", "displaystyle", "textstyle", "limits", "nolimits"
]);

/** A formula's TeX as readable text: symbols as characters (a big operator after a space, so "1/N ∑"), styling
 *  dropped, any other command as its name. */
function plainTex(tex: string): string {
  let text = tex;
  for (let round = 0; round < 3; round++) {
    text = text
      .replace(/\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}/g, "$1/$2")
      .replace(/\\sqrt\s*\{([^{}]*)\}/g, "√$1");
  }
  return text
    .replace(/\\\\/g, " ")
    .replace(/\\([{}%&_#$])/g, "$1")
    .replace(/\\[,;:! ]/g, " ")
    .replace(/\\([A-Za-z]+)/g, (_whole, name: string) => GREEK[name] ?? SYMBOLS[name] ?? (STYLE.has(name) ? "" : name))
    .replace(/\\/g, "")
    .replace(/[{}]/g, "")
    .replace(/&/g, " ");
}

/** Markdown outside formulas, as the one-line snippets always showed it: emphasis and heading marks dropped. */
function plainMarkdown(text: string): string {
  return text.replace(/[*_`#>]/g, "");
}

/**
 * A passage's markdown as one line of plain text with no TeX in it: each formula as readable text (`\(\lambda\)`
 * is λ), an unclosed formula's rest too, and a source's own command that the line cannot render as its name
 * (`\uvec` is "uvec"). For lines that are text, never rendered (Today's threads, citation labels).
 */
export function plainMathLine(markdown: string): string {
  let out = "";
  let at = 0;
  for (const match of markdown.matchAll(MATH)) {
    const start = match.index ?? 0;
    out += plainMarkdown(markdown.slice(at, start));
    out += plainTex(match[1] ?? match[2] ?? match[3] ?? match[4] ?? "");
    at = start + match[0].length;
  }
  const rest = markdown.slice(at);
  const opener = rest.search(/\\\(|\\\[|\$/);
  out += opener >= 0 ? plainMarkdown(rest.slice(0, opener)) + plainTex(rest.slice(opener).replace(/^(\\\(|\\\[|\$\$?)/, "")) : plainMarkdown(rest);
  return out.replace(/\s+/g, " ").trim();
}
