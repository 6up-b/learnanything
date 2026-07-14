// Terminal-style primitives ported from the handoff design (learnloop-handoff2).
// Inline-styled, monospace, dark-slate palette — used by the screens that follow
// the handoff layout language (Today, Graph, Library). The desktop shell/nav in
// ui.tsx keeps its own CSS-class styling; these primitives style screen *bodies*.

import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";

export const COLOR = {
  bg: "#0e0e0e",
  bgElev: "#181818",
  bgInput: "#080808",
  border: "#2a2a2a",
  borderStrong: "#3a3a3a",
  borderFocus: "#e3a063",
  text: "#d8d8e0",
  textDim: "#9090a0",
  textItalic: "#8088a0",
  textFaint: "#666778",
  amber: "#e3a063",
  amberLink: "#f0b878",
  purplePill: "#5a4d8a",
  purpleText: "#dccdf2",
  green: "#7fd28f",
  greenSoft: "#5fa672",
  cyan: "#6ad0e0",
  red: "#e07e7e",
  pink: "#dc7fb8",
  yellow: "#dccd5a",
  scrollbar: "#5a4d8a",
  scrollbarTrack: "#181818"
} as const;

export const FONT_MONO =
  '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace';

export type PillColor = "purple" | "green" | "cyan" | "amber" | "red" | "pink" | "slate";

const PILL_PALETTE: Record<PillColor, { bg: string; fg: string }> = {
  purple: { bg: COLOR.purplePill, fg: COLOR.purpleText },
  green: { bg: "#3a6b4d", fg: "#b8e8c8" },
  cyan: { bg: "#2e5d6a", fg: "#a8e0ed" },
  amber: { bg: "#6e5025", fg: "#f0c890" },
  red: { bg: "#6b3838", fg: "#f0b8b8" },
  pink: { bg: "#5d3252", fg: "#f0c0e0" },
  slate: { bg: "#363850", fg: "#b0b0c8" }
};

export function Pill({
  children,
  color = "purple",
  style = {}
}: {
  children: ReactNode;
  color?: PillColor;
  style?: CSSProperties;
}) {
  const palette = PILL_PALETTE[color] ?? PILL_PALETTE.purple;
  return (
    <span
      style={{
        fontFamily: FONT_MONO,
        fontSize: 12,
        color: palette.fg,
        background: palette.bg,
        padding: "1px 8px",
        borderRadius: 2,
        whiteSpace: "nowrap",
        ...style
      }}
    >
      {children}
    </span>
  );
}

// Practice/probe `practice_mode` is an open vocabulary — the authoring model
// emits free-text mode labels (short_answer, proof_explanation,
// worked_calculation, multiple_choice_with_explanation, diagnostic_probe, …),
// so an exact-match table would send every new label to the fallback. Instead we
// classify by keyword into semantic families, each anchored to one pill color
// (the original handoff palette: short_answer→purple, explanation→cyan,
// proof→amber, worked→green, transfer/probe/teach→pink, recall→slate).
// First matching rule wins; anything unrecognized falls back to purple.
const MODE_COLOR_RULES: Array<[RegExp, PillColor]> = [
  [/teach/, "pink"], // teach-back (learner teaches the AI naive student)
  [/transfer/, "pink"], // near/far transfer
  [/probe|diagnostic/, "pink"], // diagnostic probes
  [/proof|derivation|theorem|justif/, "amber"], // formal argument
  [/numeric|calculat|worked|algebra|comput|quantit|arithmetic/, "green"], // computation
  [/explan|explain|compare|contrast|diagram|classif|feature|conceptual/, "cyan"], // conceptual / explanatory
  [/recall|ordering|ordered|sequence|multiple_choice|match|recogni/, "slate"], // recall / recognition / sequencing
  [/short_answer|open_response|open_text|constructed|scenario|free_response|application/, "purple"] // short/open constructed answer
];

export function modePillColor(mode: string | null | undefined): PillColor {
  const m = (mode ?? "").toLowerCase();
  for (const [pattern, color] of MODE_COLOR_RULES) {
    if (pattern.test(m)) return color;
  }
  return "purple";
}

// Terminal-styled dropdown that replaces native <select>. Closed state is a
// bordered chip (amber border/text when open); the open list is an absolutely
// positioned panel below the control. Keyboard: ↑/↓ move highlight, Enter picks,
// Home/End jump, Esc closes WITHOUT bubbling (so screen-level esc handlers do not
// also fire). Click-outside closes. If a parent with overflow:hidden clips the
// list (e.g. a scrollable dialog body), the list is positioned with fixed
// coordinates from getBoundingClientRect so it escapes the clip.
export type TermSelectOption = { value: string; label: string };

export function TermSelect({
  value,
  options,
  onChange,
  placeholder,
  disabled = false,
  width,
  style = {}
}: {
  value: string;
  options: Array<TermSelectOption> | Array<string>;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  width?: number | string;
  style?: CSSProperties;
}) {
  const opts: TermSelectOption[] = useMemo(
    () =>
      (options as Array<TermSelectOption | string>).map((o) =>
        typeof o === "string" ? { value: o, label: o } : o
      ),
    [options]
  );
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(-1);
  const [fixedRect, setFixedRect] = useState<{ left: number; top: number; width: number } | null>(null);
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const controlRef = useRef<HTMLDivElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);

  const selected = opts.find((o) => o.value === value);
  const selectedIndex = opts.findIndex((o) => o.value === value);

  // Close when clicking anywhere outside the control or the (possibly fixed) list.
  useEffect(() => {
    if (!open) return;
    const onDocMouseDown = (e: MouseEvent) => {
      const target = e.target as Node;
      if (wrapRef.current?.contains(target)) return;
      if (listRef.current?.contains(target)) return;
      setOpen(false);
    };
    document.addEventListener("mousedown", onDocMouseDown, true);
    return () => document.removeEventListener("mousedown", onDocMouseDown, true);
  }, [open]);

  // Detect clipping: if any ancestor clips overflow, anchor the list with fixed
  // coordinates so it renders on top of the clip.
  useEffect(() => {
    if (!open) {
      setFixedRect(null);
      return;
    }
    setHighlight(selectedIndex >= 0 ? selectedIndex : 0);
    let clipped = false;
    let node = controlRef.current?.parentElement ?? null;
    while (node) {
      const overflow = getComputedStyle(node).overflow + getComputedStyle(node).overflowY + getComputedStyle(node).overflowX;
      if (/hidden|auto|scroll/.test(overflow)) {
        clipped = true;
        break;
      }
      node = node.parentElement;
    }
    if (clipped && controlRef.current) {
      const r = controlRef.current.getBoundingClientRect();
      setFixedRect({ left: r.left, top: r.bottom, width: r.width });
    } else {
      setFixedRect(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const commit = (idx: number) => {
    const opt = opts[idx];
    if (!opt) return;
    onChange(opt.value);
    setOpen(false);
    controlRef.current?.focus();
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;
    if (e.key === "Escape") {
      if (open) {
        e.preventDefault();
        e.stopPropagation();
        setOpen(false);
      }
      return;
    }
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (!open) {
        setOpen(true);
      } else if (highlight >= 0) {
        commit(highlight);
      }
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!open) {
        setOpen(true);
        return;
      }
      setHighlight((h) => Math.min(opts.length - 1, h + 1));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (!open) {
        setOpen(true);
        return;
      }
      setHighlight((h) => Math.max(0, h - 1));
      return;
    }
    if (e.key === "Home" && open) {
      e.preventDefault();
      setHighlight(0);
      return;
    }
    if (e.key === "End" && open) {
      e.preventDefault();
      setHighlight(opts.length - 1);
    }
  };

  const listStyle: CSSProperties = {
    background: COLOR.bgElev,
    border: `1px solid ${COLOR.borderStrong}`,
    maxHeight: 240,
    overflowY: "auto",
    zIndex: 400,
    boxShadow: "0 12px 40px rgba(0,0,0,0.55)",
    ...(fixedRect
      ? { position: "fixed", left: fixedRect.left, top: fixedRect.top, width: fixedRect.width }
      : { position: "absolute", left: 0, top: "calc(100% + 2px)", minWidth: "100%" })
  };

  const list = open ? (
    <div ref={listRef} className="ll-scroll" style={listStyle} role="listbox">
      {opts.map((o, i) => {
        const isSel = o.value === value;
        const isHi = i === highlight;
        return (
          <div
            key={o.value}
            role="option"
            aria-selected={isSel}
            onMouseEnter={() => setHighlight(i)}
            onMouseDown={(e) => {
              e.preventDefault();
              commit(i);
            }}
            style={{
              fontFamily: FONT_MONO,
              fontSize: 12,
              padding: "5px 12px",
              cursor: "pointer",
              whiteSpace: "nowrap",
              color: isSel ? COLOR.amber : COLOR.text,
              background: isSel ? "#241d12" : isHi ? COLOR.bgInput : "transparent",
              borderLeft: isSel ? `2px solid ${COLOR.amber}` : "2px solid transparent"
            }}
          >
            {o.label}
          </div>
        );
      })}
      {opts.length === 0 ? (
        <div style={{ fontFamily: FONT_MONO, fontSize: 12, padding: "5px 12px", color: COLOR.textFaint }}>no options</div>
      ) : null}
    </div>
  ) : null;

  return (
    <div ref={wrapRef} style={{ position: "relative", display: "inline-block", width, ...style }}>
      <div
        ref={controlRef}
        tabIndex={disabled ? -1 : 0}
        role="combobox"
        aria-expanded={open}
        onKeyDown={onKeyDown}
        onClick={() => {
          if (disabled) return;
          setOpen((v) => !v);
        }}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          boxSizing: "border-box",
          width: width != null ? "100%" : undefined,
          fontFamily: FONT_MONO,
          fontSize: 12,
          padding: "4px 12px",
          background: COLOR.bgInput,
          border: `1px solid ${open ? COLOR.amber : COLOR.border}`,
          color: open ? COLOR.amber : selected ? COLOR.text : COLOR.textFaint,
          cursor: disabled ? "default" : "pointer",
          opacity: disabled ? 0.6 : 1,
          pointerEvents: disabled ? "none" : "auto",
          outline: "none",
          userSelect: "none"
        }}
      >
        <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {selected ? selected.label : placeholder ?? ""}
        </span>
        <span style={{ color: open ? COLOR.amber : COLOR.textFaint, fontSize: 11 }}>{open ? "▴" : "▾"}</span>
      </div>
      {list}
    </div>
  );
}

export function SectionHeader({ children, style = {} }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div
      style={{
        fontFamily: FONT_MONO,
        fontSize: 14,
        color: COLOR.amber,
        textDecoration: "underline",
        textUnderlineOffset: "3px",
        marginBottom: 14,
        marginTop: 22,
        ...style
      }}
    >
      {children}
    </div>
  );
}

// Unicode block bar for difficulty / mastery / progress.
export function BlockBar({
  value,
  max = 1,
  width = 8,
  color = COLOR.amber,
  dim = COLOR.borderStrong
}: {
  value: number;
  max?: number;
  width?: number;
  color?: string;
  dim?: string;
}) {
  const filled = Math.max(0, Math.min(width, Math.round((value / max) * width)));
  return (
    <span style={{ fontFamily: FONT_MONO, letterSpacing: 0 }}>
      <span style={{ color }}>{"▓".repeat(filled)}</span>
      <span style={{ color: dim }}>{"░".repeat(width - filled)}</span>
    </span>
  );
}

export function Meta({ children, style = {} }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <span style={{ fontFamily: FONT_MONO, fontStyle: "italic", color: COLOR.textItalic, ...style }}>
      {children}
    </span>
  );
}

export function Dim({ children, style = {} }: { children: ReactNode; style?: CSSProperties }) {
  return <span style={{ color: COLOR.textDim, ...style }}>{children}</span>;
}

export function Faint({ children, style = {} }: { children: ReactNode; style?: CSSProperties }) {
  return <span style={{ color: COLOR.textFaint, ...style }}>{children}</span>;
}

export function Divider({ char = "─", color = COLOR.border, style = {} }: { char?: string; color?: string; style?: CSSProperties }) {
  return (
    <div
      style={{
        color,
        fontFamily: FONT_MONO,
        lineHeight: 1,
        whiteSpace: "nowrap",
        overflow: "hidden",
        userSelect: "none",
        ...style
      }}
    >
      {char.repeat(400)}
    </div>
  );
}

// Footer hot-key bar. `right` pins a single key to the far edge (e.g. ^p palette).
export function KeyBar({
  keys = [],
  right = null
}: {
  keys?: Array<{ key: string; label: string }>;
  right?: { key: string; label: string } | null;
}) {
  return (
    <div
      style={{
        borderTop: `1px solid ${COLOR.border}`,
        padding: "6px 14px",
        display: "flex",
        alignItems: "center",
        flexWrap: "wrap",
        columnGap: 20,
        rowGap: 4,
        fontFamily: FONT_MONO,
        fontSize: 12,
        color: COLOR.textDim,
        background: COLOR.bg,
        flexShrink: 0,
        whiteSpace: "nowrap"
      }}
    >
      {keys.map((k) => (
        <span key={k.key} style={{ display: "inline-flex", gap: 6, flexShrink: 0 }}>
          <span style={{ color: COLOR.text, fontWeight: 600 }}>{k.key}</span>
          <span>{k.label}</span>
        </span>
      ))}
      <span style={{ flex: 1, minWidth: 8 }} />
      {right && (
        <span style={{ display: "inline-flex", gap: 6, flexShrink: 0 }}>
          <span style={{ color: COLOR.text, fontWeight: 600 }}>{right.key}</span>
          <span>{right.label}</span>
        </span>
      )}
    </div>
  );
}
