import katex from "katex";
import { useCallback, useEffect, useLayoutEffect, useRef } from "react";
import "katex/dist/katex.min.css";

// A live "WYSIWYG" answer editor: the learner types Markdown + LaTeX into a
// contentEditable surface and every *completed* `$…$` / `$$…$$` span renders as
// KaTeX in place, the moment the closing delimiter is typed. The math segment
// the caret currently sits inside reverts to its raw source so it stays
// editable — click a rendered equation (or backspace into it) to edit it again.
//
// The plain string is the single source of truth (`value`/`onChange`). The DOM
// is only rebuilt when the *rendered-widget structure* changes (a span renders,
// un-renders, or the caret crosses a boundary); ordinary typing inside text or
// inside the active equation is left to the browser, so the caret never jumps.

interface Props {
  value: string;
  onChange: (next: string) => void;
  disabled?: boolean;
  placeholder?: string;
  maxHeight?: number;
  className?: string;
  ariaLabel?: string;
}

type Seg =
  | { kind: "text"; text: string; start: number; end: number }
  | { kind: "math"; src: string; tex: string; display: boolean; start: number; end: number };

// Zero-width spaces are sometimes left behind by the browser around atomic
// widgets; they must never reach the source model. Built from an escape so the
// pattern stays visible in source rather than being an invisible glyph.
const ZWSP = new RegExp("\\u200B", "g");

// Split the source into plain-text runs and complete math spans. An unterminated
// `$` (the learner is mid-equation) stays text, so the source is visible while
// being typed and only renders once it is closed.
function tokenize(value: string): Seg[] {
  const segs: Seg[] = [];
  let i = 0;
  let textStart = 0;
  const pushText = (end: number) => {
    if (end > textStart) segs.push({ kind: "text", text: value.slice(textStart, end), start: textStart, end });
  };
  while (i < value.length) {
    const ch = value[i];
    if (ch === "\\") {
      i += 2; // skip an escaped char (e.g. \$) so it can't open/close math
      continue;
    }
    if (ch === "$") {
      const display = value[i + 1] === "$";
      const delim = display ? 2 : 1;
      const contentStart = i + delim;
      let j = contentStart;
      let close = -1;
      while (j < value.length) {
        if (value[j] === "\\") { j += 2; continue; }
        if (display ? value[j] === "$" && value[j + 1] === "$" : value[j] === "$") { close = j; break; }
        j += 1;
      }
      if (close > contentStart) {
        pushText(i);
        const end = close + delim;
        segs.push({ kind: "math", src: value.slice(i, end), tex: value.slice(contentStart, close), display, start: i, end });
        i = end;
        textStart = end;
        continue;
      }
      i += 1; // no (non-empty) closing delimiter — treat this `$` as literal text
      continue;
    }
    i += 1;
  }
  pushText(value.length);
  return segs;
}

const isActiveMath = (seg: Seg, caret: number): boolean =>
  seg.kind === "math" && caret > seg.start && caret < seg.end;

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderMath(tex: string, display: boolean): string {
  try {
    return katex.renderToString(tex, { displayMode: display, throwOnError: false, output: "htmlAndMathml" });
  } catch {
    return escapeHtml(display ? `$$${tex}$$` : `$${tex}$`);
  }
}

// Build the editor's innerHTML from the segments. Text and the caret's active
// equation are emitted as editable raw spans; every other equation becomes an
// atomic (contenteditable=false) KaTeX widget carrying its source in data-src.
function buildHtml(segs: Seg[], caret: number): string {
  let html = "";
  for (const seg of segs) {
    if (seg.kind === "text") {
      if (seg.text) html += `<span data-raw="1">${escapeHtml(seg.text)}</span>`;
    } else if (isActiveMath(seg, caret)) {
      html += `<span data-raw="1">${escapeHtml(seg.src)}</span>`;
    } else {
      const cls = seg.display ? "mle-math mle-display" : "mle-math";
      html += `<span class="${cls}" contenteditable="false" data-src="${escapeHtml(seg.src).replace(/"/g, "&quot;")}">${renderMath(seg.tex, seg.display)}</span>`;
    }
  }
  return html;
}

// A signature of just the rendered widgets (their kind/source/active-ness, in
// order). When this is unchanged we leave the DOM alone, so typing inside text
// or inside the active equation never triggers a rebuild.
function widgetSig(segs: Seg[], caret: number): string {
  return segs
    .map((seg) => (seg.kind === "text" ? "T" : isActiveMath(seg, caret) ? "A" : (seg.display ? "D" : "I") + seg.src))
    .join("");
}

// Walk the DOM back into the plain source, capturing the caret's character
// offset. Math widgets contribute their data-src (their KaTeX innards are
// ignored); <br>/<div> boundaries the browser may inject become newlines.
function serialize(root: HTMLElement, anchorNode: Node | null, anchorOffset: number): { text: string; caret: number } {
  let out = "";
  let caret = -1;
  const visit = (node: Node, isBlock: boolean) => {
    if (isBlock && out.length > 0) out += "\n"; // a nested <div> starts a new line
    const children = node.childNodes;
    for (let idx = 0; idx <= children.length; idx += 1) {
      if (node === anchorNode && idx === anchorOffset) caret = out.length;
      if (idx === children.length) break;
      const child = children[idx];
      if (child.nodeType === Node.TEXT_NODE) {
        const raw = child.nodeValue ?? "";
        if (child === anchorNode) caret = out.length + raw.slice(0, anchorOffset).replace(ZWSP, "").length;
        out += raw.replace(ZWSP, "");
      } else if (child.nodeType === Node.ELEMENT_NODE) {
        const el = child as HTMLElement;
        if (el.dataset.src != null) {
          if (el === anchorNode) caret = out.length + (anchorOffset > 0 ? el.dataset.src.length : 0);
          out += el.dataset.src;
        } else if (el.tagName === "BR") {
          if (el === anchorNode) caret = out.length;
          // A lone trailing <br> the browser keeps to make the last line
          // selectable is not real content; only count breaks before more text.
          if (idx < children.length - 1 || node !== root) out += "\n";
        } else {
          visit(el, el.tagName === "DIV");
        }
      }
    }
  };
  visit(root, false);
  if (caret < 0) caret = out.length;
  return { text: out, caret };
}

// Place a collapsed caret at the given character offset in the rebuilt DOM.
function placeCaret(root: HTMLElement, offset: number): void {
  let remaining = offset;
  const range = document.createRange();
  let placed = false;
  const visit = (node: Node) => {
    for (let idx = 0; idx < node.childNodes.length && !placed; idx += 1) {
      const child = node.childNodes[idx];
      if (child.nodeType === Node.TEXT_NODE) {
        const len = (child.nodeValue ?? "").length;
        if (remaining <= len) { range.setStart(child, remaining); placed = true; return; }
        remaining -= len;
      } else if (child.nodeType === Node.ELEMENT_NODE) {
        const el = child as HTMLElement;
        if (el.dataset.src != null) {
          const len = el.dataset.src.length;
          if (remaining <= 0) { range.setStartBefore(el); placed = true; return; }
          if (remaining <= len) { range.setStartAfter(el); placed = true; return; }
          remaining -= len;
        } else if (el.tagName === "BR") {
          if (remaining <= 0) { range.setStartBefore(el); placed = true; return; }
          remaining -= 1;
        } else {
          visit(el);
        }
      }
    }
  };
  visit(root);
  const sel = window.getSelection();
  if (!sel) return;
  if (!placed) { range.selectNodeContents(root); range.collapse(false); } else { range.collapse(true); }
  sel.removeAllRanges();
  sel.addRange(range);
}

// Character offset at which a given widget element begins in the source.
function offsetOfNode(root: HTMLElement, target: HTMLElement): number {
  let out = 0;
  let found = -1;
  const visit = (node: Node) => {
    for (let idx = 0; idx < node.childNodes.length && found < 0; idx += 1) {
      const child = node.childNodes[idx];
      if (child === target) { found = out; return; }
      if (child.nodeType === Node.TEXT_NODE) {
        out += (child.nodeValue ?? "").replace(ZWSP, "").length;
      } else if (child.nodeType === Node.ELEMENT_NODE) {
        const el = child as HTMLElement;
        if (el.dataset.src != null) out += el.dataset.src.length;
        else if (el.tagName === "BR") out += 1;
        else visit(el);
      }
    }
  };
  visit(root);
  return found < 0 ? out : found;
}

export function MathLiveEditor({ value, onChange, disabled, placeholder, maxHeight, className, ariaLabel }: Props) {
  const editorRef = useRef<HTMLDivElement>(null);
  const lastModel = useRef<string | null>(null);
  const lastSig = useRef<string>("");
  const reconciling = useRef(false);
  const composing = useRef(false);

  // Reconcile the DOM with its own content after an edit or caret move. Reads
  // the model + caret out of the DOM, and only rewrites innerHTML when the set
  // of rendered widgets must change (or a caret override is forced).
  const reconcile = useCallback((forceCaret?: number) => {
    const el = editorRef.current;
    if (!el) return;
    const sel = window.getSelection();
    const useForced = forceCaret != null;
    const anchorNode = !useForced && sel && sel.rangeCount ? sel.anchorNode : null;
    const anchorOffset = !useForced && sel && sel.rangeCount ? sel.anchorOffset : 0;
    const read = serialize(el, anchorNode, anchorOffset);
    const model = read.text;
    const caret = useForced ? Math.max(0, Math.min(forceCaret, model.length)) : read.caret;
    const segs = tokenize(model);
    const sig = widgetSig(segs, caret);
    if (useForced || sig !== lastSig.current) {
      reconciling.current = true;
      el.innerHTML = buildHtml(segs, caret);
      placeCaret(el, caret);
      lastSig.current = sig;
      reconciling.current = false;
    }
    if (model !== lastModel.current) {
      lastModel.current = model;
      onChange(model);
    }
  }, [onChange]);

  // Render every equation (nothing active) — used when focus leaves the editor.
  const renderAll = useCallback(() => {
    const el = editorRef.current;
    if (!el) return;
    const model = serialize(el, null, 0).text;
    const segs = tokenize(model);
    reconciling.current = true;
    el.innerHTML = buildHtml(segs, -1);
    lastSig.current = widgetSig(segs, -1);
    reconciling.current = false;
  }, []);

  // Adopt an externally-driven value (item switch, restored draft, clear) — but
  // ignore the echo of our own onChange, which would needlessly reset the caret.
  useLayoutEffect(() => {
    const el = editorRef.current;
    if (!el || value === lastModel.current) return;
    const focused = document.activeElement === el;
    const segs = tokenize(value);
    const caret = focused ? value.length : -1;
    reconciling.current = true;
    el.innerHTML = buildHtml(segs, caret);
    if (focused) placeCaret(el, caret);
    reconciling.current = false;
    lastModel.current = value;
    lastSig.current = widgetSig(segs, caret);
  }, [value]);

  // Reveal/hide the equation under the caret as it moves (arrows, clicks).
  useEffect(() => {
    const onSelectionChange = () => {
      if (reconciling.current || composing.current) return;
      const el = editorRef.current;
      const sel = window.getSelection();
      if (!el || !sel || sel.rangeCount === 0 || !sel.isCollapsed) return;
      if (!el.contains(sel.anchorNode)) return;
      reconcile();
    };
    document.addEventListener("selectionchange", onSelectionChange);
    return () => document.removeEventListener("selectionchange", onSelectionChange);
  }, [reconcile]);

  const onKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    // Ctrl/Cmd combos (submit, hint, …) belong to the screen's global handler.
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.key === "Enter") {
      event.preventDefault();
      const sel = window.getSelection();
      if (!sel || sel.rangeCount === 0) return;
      const range = sel.getRangeAt(0);
      range.deleteContents();
      const node = document.createTextNode("\n");
      range.insertNode(node);
      range.setStartAfter(node);
      range.collapse(true);
      sel.removeAllRanges();
      sel.addRange(range);
      reconcile();
      return;
    }
    if (event.key === "Backspace" || event.key === "Delete") {
      const el = editorRef.current;
      const sel = window.getSelection();
      if (!el || !sel || sel.rangeCount === 0 || !sel.isCollapsed) return;
      const { text, caret } = serialize(el, sel.anchorNode, sel.anchorOffset);
      const segs = tokenize(text);
      // Stepping into a rendered equation should open it for editing rather than
      // deleting the whole thing in one stroke.
      if (event.key === "Backspace") {
        const seg = segs.find((s) => s.kind === "math" && s.end === caret);
        if (seg) { event.preventDefault(); reconcile(seg.end - 1); return; }
      } else {
        const seg = segs.find((s) => s.kind === "math" && s.start === caret) as Extract<Seg, { kind: "math" }> | undefined;
        if (seg) { event.preventDefault(); reconcile(seg.start + (seg.display ? 2 : 1)); return; }
      }
    }
  };

  const onMouseDown = (event: React.MouseEvent<HTMLDivElement>) => {
    const widget = (event.target as HTMLElement).closest<HTMLElement>(".mle-math");
    const el = editorRef.current;
    if (!widget || !el) return;
    event.preventDefault();
    el.focus();
    const start = offsetOfNode(el, widget);
    reconcile(start + (widget.classList.contains("mle-display") ? 2 : 1));
  };

  const onPaste = (event: React.ClipboardEvent<HTMLDivElement>) => {
    event.preventDefault();
    const textData = event.clipboardData.getData("text/plain");
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0) return;
    const range = sel.getRangeAt(0);
    range.deleteContents();
    const node = document.createTextNode(textData);
    range.insertNode(node);
    range.setStartAfter(node);
    range.collapse(true);
    sel.removeAllRanges();
    sel.addRange(range);
    reconcile();
  };

  return (
    <div
      ref={editorRef}
      className={`mle-editor${className ? ` ${className}` : ""}`}
      contentEditable={!disabled}
      suppressContentEditableWarning
      role="textbox"
      aria-multiline="true"
      aria-label={ariaLabel}
      spellCheck={false}
      data-placeholder={placeholder}
      style={maxHeight ? { maxHeight } : undefined}
      onInput={() => { if (!composing.current) reconcile(); }}
      onKeyDown={onKeyDown}
      onMouseDown={onMouseDown}
      onPaste={onPaste}
      onBlur={renderAll}
      onCompositionStart={() => { composing.current = true; }}
      onCompositionEnd={() => { composing.current = false; reconcile(); }}
    />
  );
}
