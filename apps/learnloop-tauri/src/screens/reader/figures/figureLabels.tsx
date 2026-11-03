// Reader RW5c: code-owned, element-scoped labels (spec_reader_rw5c_checked_labels_v1 §7, option B; G23e).
//
// On a figure with a checked element every label in specJson is an element id, and every label
// slot (legend, SVG text, values-table header, aria-label, readout, slider) is drawn from here: the
// book's own left-hand side in source voice, a derived label's closed template over the bounds the
// evaluator used, or LearnLoop's rendering of the element's expression behind the model's glyph. So
// no model string can reach a slot of a figure that carries the claim, whatever the model wrote. A
// figure with no checked element has no provider value, and every slot draws its label as before.
import katex from "katex";
import "katex/dist/katex.min.css";
import { createContext, useContext, useMemo, useState, type CSSProperties, type ReactNode } from "react";
import type { FigureElementDto, FigureViewDto } from "../../../api/dto";
import { COLOR, FONT_MONO } from "../../../components/term";
import { MeaningLabel } from "../voices";
import { derivedBounds, defaults, type CompiledFigure, type DerivedBounds } from "./figureSpec";
import { FIGURE_FRAME, linkStyle, sourceCheckReasons } from "./FigureInline";
import type { FiguresCtl } from "./useFigures";

/** A legend line's length past which it names the curve and the table header keeps the full rendering (a layout fallback, §8.2). */
const LEGEND_CHARS = 48;

export interface FigureLabels {
  elements: ReadonlyMap<string, FigureElementDto>;
  /** A label as plain text, for aria-labels and SVG text. */
  plain: (id: string) => string;
  bounds: (element: FigureElementDto) => DerivedBounds | null;
}

const FigureLabelsContext = createContext<FigureLabels | null>(null);

export function useFigureLabels(): FigureLabels | null {
  return useContext(FigureLabelsContext);
}

/** The element map a figure is drawn from: empty unless it carries a checked element. */
export function labelElements(figure: FigureViewDto): FigureElementDto[] {
  const elements = figure.elements ?? [];
  return figure.sourceCheck?.status === "checked" && elements.some((element) => element.role === "book") ? elements : [];
}

export function Tex({ tex, style }: { tex: string; style?: CSSProperties }) {
  const html = useMemo(() => katex.renderToString(tex, { throwOnError: false, strict: "ignore", trust: false, output: "html" }), [tex]);
  return <span data-figure-tex={tex} style={style} dangerouslySetInnerHTML={{ __html: html }} />;
}

/** A derived label's words at this evaluation: the bounds the evaluator used, never by formatValue (F9). */
export function derivedWords(element: FigureElementDto, bounds: DerivedBounds | null): { tex: string; plain: string; empty: boolean; clipped: boolean } {
  const template = element.template;
  if (!template || !bounds || bounds.from === null || bounds.to === null) return { tex: element.tex, plain: element.plain, empty: false, clipped: false };
  // The operand as the check wrote it: a compound left-hand side arrives grouped, read from KaTeX's tree (elements.BookLabel.operand; Astra A2).
  const { bodyTex, bodyPlain, variable } = template;
  if (bounds.integers && bounds.integers[1] < bounds.integers[0]) {
    return { tex: bodyTex, plain: `${bodyPlain}: ${FIGURE_FRAME.noTerms}`, empty: true, clipped: bounds.clipped };
  }
  const low = bounds.integers ? String(bounds.integers[0]) : String(bounds.from);
  const high = bounds.integers ? String(bounds.integers[1]) : String(bounds.to);
  const lowTex = numberTex(low);
  const highTex = numberTex(high);
  const limited = bounds.clipped ? ` · ${FIGURE_FRAME.limitedToPlot}` : "";
  if (template.kind === "shade") {
    return { tex: `\\text{area under } ${bodyTex} \\text{ from } ${lowTex} \\text{ to } ${highTex}`,
      plain: `area under ${bodyPlain} from ${low} to ${high}${limited}`, empty: false, clipped: bounds.clipped };
  }
  const symbol = variableTex(variable);
  if (template.kind === "integral") {
    return { tex: `\\int_{${lowTex}}^{${highTex}} ${bodyTex}\\,d${symbol}`, plain: `integral from ${low} to ${high} of ${bodyPlain} d${variable}`, empty: false, clipped: false };
  }
  return { tex: `\\sum_{${symbol}=${lowTex}}^{${highTex}} ${bodyTex}`, plain: `sum for ${variable} from ${low} to ${high} of ${bodyPlain}${limited}`, empty: false, clipped: bounds.clipped };
}

/** A number's lossless digits in TeX (the Python renderer's _number_tex): 1e-7 written bare would
 *  read as a coefficient, the variable e, and a subtraction (Codex review F3). */
function numberTex(text: string): string {
  const [mantissa, exponent] = text.toLowerCase().split("e");
  return exponent === undefined ? mantissa : `${mantissa || "1"} \\times 10^{${Number(exponent)}}`;
}

const GREEK = new Set(["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa", "lambda", "mu", "nu", "xi", "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega"]);

/** A variable's name as a symbol (the Python renderer's symbol_tex for a bound variable). */
function variableTex(name: string): string {
  if (GREEK.has(name)) return `\\${name}`;
  if (name.length === 1) return name;
  const head = name.replace(/[0-9]+$/, "");
  const tail = name.slice(head.length);
  if (tail && (GREEK.has(head) || head.length === 1)) return `${GREEK.has(head) ? `\\${head}` : head}_{${tail}}`;
  return `\\mathrm{${name}}`;
}

export function FigureLabelsProvider({ figure, compiled, params, children }: { figure: FigureViewDto; compiled: CompiledFigure; params: Record<string, number>; children: ReactNode }) {
  const value = useMemo<FigureLabels | null>(() => {
    const list = labelElements(figure);
    if (!list.length) return null;
    const elements = new Map(list.map((element) => [element.id, element]));
    const bounds = (element: FigureElementDto) => {
      const template = element.template;
      if (!template) return null;
      try {
        return derivedBounds(compiled, template.panel, template.kind, template.index, { ...defaults(compiled), ...params });
      } catch {
        return null;
      }
    };
    return {
      elements,
      bounds,
      plain: (id) => {
        const element = elements.get(id);
        if (!element) return "";
        return element.template ? derivedWords(element, bounds(element)).plain : element.plain;
      },
    };
  }, [figure, compiled, params]);
  return <FigureLabelsContext.Provider value={value}>{children}</FigureLabelsContext.Provider>;
}

const GLYPH: CSSProperties = { fontFamily: FONT_MONO };

/** One label slot. With no element map, the label as the spec gives it. An id with no element draws
 *  the model's glyph alone: a model string can never reach a slot by being unmapped. */
export function LabelText({ id, legendIndex, bare }: { id: string; legendIndex?: number; /** Just the name, with no glyph or claim: an annotation's target, in the model's line. */ bare?: boolean }) {
  const labels = useFigureLabels();
  if (!labels) return <>{id}</>;
  const element = labels.elements.get(id);
  if (!element) return <span data-figure-label={id} data-figure-role="unmapped" style={{ ...GLYPH, color: COLOR.purpleText }}>◇</span>;
  const words = element.template ? derivedWords(element, labels.bounds(element)) : { tex: element.tex, plain: element.plain, empty: false, clipped: false };
  if (bare) return <span data-figure-label={id} data-figure-role={element.role}><Tex tex={words.tex} /></span>;
  if (element.role === "book") {
    return (
      <span data-figure-label={id} data-figure-role="book" data-figure-voice="source" style={{ color: COLOR.text }}>
        <span aria-hidden="true" style={GLYPH}>§ </span><Tex tex={words.tex} /> <span data-figure-claim="">{FIGURE_FRAME.bookChecked}</span>
      </span>
    );
  }
  if (element.role === "symbol") {
    return <span data-figure-label={id} data-figure-role="symbol" data-figure-voice="source"><span aria-hidden="true" style={GLYPH}>§ </span><Tex tex={words.tex} /></span>;
  }
  const compact = element.role === "ai" && legendIndex !== undefined && words.plain.length > LEGEND_CHARS;
  const glyph = element.voice === "model" ? <span aria-hidden="true" style={{ ...GLYPH, color: COLOR.purpleText }}>◇ </span> : null;
  return (
    <span data-figure-label={id} data-figure-role={element.role} data-figure-voice={element.voice}
      title={element.voice === "model" ? FIGURE_FRAME.aiElement : undefined}>
      {glyph}{compact ? `curve ${(legendIndex ?? 0) + 1}` : words.tex ? <Tex tex={words.tex} /> : null}
      {element.tag === "ai_defined" ? <span data-figure-ai-defined=""> · {FIGURE_FRAME.aiDefined}</span> : null}
      {words.empty ? <> · {FIGURE_FRAME.noTerms}</> : null}
    </span>
  );
}

/** What follows a derived label's value: *computed by LearnLoop from it*, and that a clamp moved a bound. */
export function LabelSuffix({ id }: { id: string }) {
  const labels = useFigureLabels();
  const element = labels?.elements.get(id);
  if (!labels || !element?.template) return null;
  const words = derivedWords(element, labels.bounds(element));
  return (
    <span data-figure-derived-note="" style={{ color: COLOR.textDim }}>
      {element.role === "derived" ? <> · {FIGURE_FRAME.derivedFrom}</> : null}
      {words.clipped ? <> · {FIGURE_FRAME.limitedToPlot}</> : null}
    </span>
  );
}

function distinctBook(figure: FigureViewDto): FigureElementDto[] {
  const seen = new Set<string>();
  return labelElements(figure).filter((element) => {
    if (element.role !== "book" || seen.has(element.tex)) return false;
    seen.add(element.tex);
    return true;
  });
}

/** The collapsed line's code-written badge (§7.2): *the rest is an illustration* whenever any ai element is drawn. */
export function CheckedBadge({ figure }: { figure: FigureViewDto }) {
  const rest = labelElements(figure).some((element) => element.role === "ai");
  return (
    <span data-figure-checked-badge="">
      {FIGURE_FRAME.aiBuilt}
      {distinctBook(figure).map((element) => (
        <span key={element.id}> · <span aria-hidden="true">§ </span><Tex tex={element.tex} /> {FIGURE_FRAME.bookChecked}</span>
      ))}
      {rest ? <> · {FIGURE_FRAME.restIllustration}</> : null}
    </span>
  );
}

/** The open frame's *checked by LearnLoop:* entry for each checked element (§7.2). */
export function CheckedLines({ figure }: { figure: FigureViewDto }) {
  return (
    <>
      {distinctBook(figure).map((element, index) => (
        <span key={element.id} data-figure-checked-line="">
          {index ? "; " : ""}the {element.path.includes(".series.") ? "curve" : "value"} <span aria-hidden="true">§ </span><Tex tex={element.tex} /> equals the book's equation
          {element.source?.page !== null && element.source?.page !== undefined ? ` on p. ${element.source.page}` : ""}, symbolically, for every value it is defined at and every value the sliders reach
        </span>
      ))}
    </>
  );
}

/** ⓘ: the book's equation as LearnLoop read it, its page, and what was checked (§3, Q18); with nothing
 *  checked, why not, in the frame's closed words. */
export function FigureSourceInfo({ figure, ctl }: { figure: FigureViewDto; ctl: FiguresCtl }) {
  const [open, setOpen] = useState(false);
  const book = distinctBook(figure);
  const reasons = sourceCheckReasons(figure.sourceCheck?.reasons);
  if (!book.length && !reasons.length) return null;
  return (
    <div data-figure-source-info="" style={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <button type="button" style={{ ...linkStyle, alignSelf: "flex-start" }} aria-expanded={open} onClick={() => setOpen((value) => !value)}>ⓘ {book.length ? "how this was checked" : "why this isn't checked against the book"}</button>
      {open && !book.length ? <MeaningLabel>{reasons.join("; ")}</MeaningLabel> : null}
      {open && book.map((element) => (
        <div key={element.id} data-figure-source-equation="" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <MeaningLabel>the book's equation as LearnLoop read it{element.source?.page !== null && element.source?.page !== undefined ? ` from p. ${element.source.page}` : ""}:</MeaningLabel>
          {element.equation ? <span><span aria-hidden="true">§ </span><Tex tex={element.equation} /></span> : null}
          {element.source && ctl.openSource ? (
            <button type="button" style={{ ...linkStyle, alignSelf: "flex-start" }} data-figure-open-page=""
              onClick={() => { const source = element.source; if (source) ctl.openSource?.(source.extractionId, source.spanId); }}>open the page</button>
          ) : null}
          <MeaningLabel>
            checked by code, with no model: this definition equals that equation exactly, on the same domain, for every value the sliders reach; what's shown matches it to the digits shown at each slider's ends and default; the check's controls were refused. Not checked: that LearnLoop read the page right, values between the plotted points, numbers computed from it, or that the figure teaches the right idea.
          </MeaningLabel>
        </div>
      ))}
    </div>
  );
}
