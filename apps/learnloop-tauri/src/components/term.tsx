// Terminal-style primitives ported from the handoff design (learnloop-handoff2).
// Inline-styled, monospace, dark-slate palette — used by the screens that follow
// the handoff layout language (Today, Graph, Library). The desktop shell/nav in
// ui.tsx keeps its own CSS-class styling; these primitives style screen *bodies*.

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
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
  scrollbarTrack: "#181818",
  // Wash backgrounds — promoted from the raw hex copied across screens (§1.4).
  washAmber: "#241d12",
  washCyan: "#10212a",
  washCyanBanner: "#101d22",
  washRed: "#241315",
  washGreen: "#122117",
  washPurple: "#1a162a"
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

// Terminal-style checkbox used where a native platform checkbox would break the
// app's monospace control language. It remains a real keyboard-focusable button
// and exposes checkbox semantics to assistive technology.
export function TermCheckbox({
  checked,
  onChange,
  label,
  disabled = false,
  compact = false,
  style = {}
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: ReactNode;
  disabled?: boolean;
  compact?: boolean;
  style?: CSSProperties;
}) {
  const [focused, setFocused] = useState(false);
  return (
    <button
      className={`term-checkbox${checked ? " checked" : ""}${compact ? " compact" : ""}`}
      type="button"
      role="checkbox"
      aria-checked={checked}
      disabled={disabled}
      onClick={(event) => {
        event.stopPropagation();
        onChange(!checked);
      }}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: compact ? 5 : 7,
        padding: compact ? "2px 6px" : "4px 8px",
        border: `1px solid ${focused ? COLOR.borderFocus : checked ? COLOR.amber : COLOR.border}`,
        borderRadius: 2,
        background: checked ? COLOR.washAmber : COLOR.bgInput,
        color: checked ? COLOR.amber : COLOR.textDim,
        fontFamily: FONT_MONO,
        fontSize: compact ? 9 : 11,
        lineHeight: 1.35,
        letterSpacing: "0.01em",
        cursor: disabled ? "default" : "pointer",
        opacity: disabled ? 0.45 : 1,
        outline: "none",
        boxShadow: focused ? `0 0 0 1px ${COLOR.bg}, 0 0 0 2px ${COLOR.borderFocus}` : "none",
        ...style
      }}
    >
      <span aria-hidden="true" style={{ color: checked ? COLOR.amber : COLOR.textFaint }}>
        {checked ? "▣" : "▢"}
      </span>
      <span>{label}</span>
    </button>
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
  ariaLabel,
  disabled = false,
  width,
  style = {}
}: {
  value: string;
  options: Array<TermSelectOption> | Array<string>;
  onChange: (value: string) => void;
  placeholder?: string;
  ariaLabel?: string;
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
  const listboxId = useId();
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
    <div id={listboxId} ref={listRef} className="term-select-list ll-scroll" style={listStyle} role="listbox">
      {opts.map((o, i) => {
        const isSel = o.value === value;
        const isHi = i === highlight;
        return (
          <div
            key={o.value}
            id={`${listboxId}-option-${i}`}
            className={`term-select-option${isSel ? " selected" : ""}${isHi ? " highlighted" : ""}`}
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
    <div ref={wrapRef} className="term-select" style={{ position: "relative", display: "inline-block", width, ...style }}>
      <div
        ref={controlRef}
        className={`term-select-control${open ? " open" : ""}${disabled ? " disabled" : ""}`}
        tabIndex={disabled ? -1 : 0}
        role="combobox"
        aria-label={ariaLabel}
        aria-controls={listboxId}
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-activedescendant={open && highlight >= 0 ? `${listboxId}-option-${highlight}` : undefined}
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

export function DisclosureHeader({
  open,
  onToggle,
  children,
  eyebrow,
  description,
  meta,
  tooltip,
  tone = COLOR.amber,
  style = {}
}: {
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
  eyebrow?: ReactNode;
  description?: ReactNode;
  meta?: ReactNode;
  tooltip?: ReactNode;
  tone?: string;
  style?: CSSProperties;
}) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: 8, width: "100%", marginTop: 22, marginBottom: open ? 14 : 0, ...style }}>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        style={{
          flex: 1,
          minWidth: 0,
          padding: 0,
          border: "none",
          background: "transparent",
          display: "flex",
          alignItems: "baseline",
          gap: 8,
          color: tone,
          fontFamily: FONT_MONO,
          textAlign: "left",
          cursor: "pointer"
        }}
      >
        <span style={{ flex: 1, minWidth: 0 }}>
          {eyebrow ? (
            <span style={{ display: "block", color: COLOR.textFaint, fontSize: 11, marginBottom: 3 }}>
              {eyebrow}
            </span>
          ) : null}
          <span style={{ color: tone, fontSize: 14, fontWeight: 400, textDecoration: "underline", textDecorationThickness: "1px", textUnderlineOffset: 3 }}>
            {children}
          </span>
          {description ? (
            <span style={{ display: "block", color: COLOR.textDim, fontSize: 11, fontWeight: 400, lineHeight: 1.5, marginTop: 6, maxWidth: 720 }}>
              {description}
            </span>
          ) : null}
        </span>
        <span style={{ color: COLOR.textFaint, fontSize: 11, fontWeight: 400, whiteSpace: "nowrap" }}>
          {meta ? <span style={{ marginRight: 12 }}>{meta}</span> : null}
          {open ? "▾ collapse" : "▸ expand"}
        </span>
      </button>
      {tooltip ? <HelpTooltip label={`About ${String(children)}`}>{tooltip}</HelpTooltip> : null}
    </div>
  );
}

export function HelpTooltip({ label, children }: { label: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<{ left: number; width: number; top?: number; bottom?: number } | null>(null);
  const tooltipId = useId();
  const anchorRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (!open) {
      setPosition(null);
      return;
    }
    const updatePosition = () => {
      const rect = anchorRef.current?.getBoundingClientRect();
      if (!rect) return;
      const viewportPadding = 8;
      const width = Math.min(320, window.innerWidth - viewportPadding * 2);
      const left = Math.max(viewportPadding, Math.min(rect.right - width, window.innerWidth - width - viewportPadding));
      const roomBelow = window.innerHeight - rect.bottom;
      setPosition(
        roomBelow >= 150
          ? { left, width, top: rect.bottom + 6 }
          : { left, width, bottom: window.innerHeight - rect.top + 6 }
      );
    };
    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [open]);

  return (
    <span style={{ display: "inline-flex", flexShrink: 0 }}>
      <button
        ref={anchorRef}
        type="button"
        aria-label={label}
        aria-describedby={open ? tooltipId : undefined}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        style={{
          width: 17,
          height: 17,
          padding: 0,
          border: `1px solid ${COLOR.borderStrong}`,
          borderRadius: "50%",
          background: "transparent",
          color: open ? COLOR.amber : COLOR.textFaint,
          fontFamily: FONT_MONO,
          fontSize: 10,
          lineHeight: "15px",
          textAlign: "center",
          cursor: "help"
        }}
      >
        ?
      </button>
      {open && position ? createPortal(
          <span
            id={tooltipId}
            role="tooltip"
            style={{
              position: "fixed",
              zIndex: 1000,
              left: position.left,
              width: position.width,
              top: position.top,
              bottom: position.bottom,
              maxHeight: "min(280px, calc(100vh - 16px))",
              overflowY: "auto",
              padding: "9px 10px",
              border: `1px solid ${COLOR.borderStrong}`,
              background: COLOR.bgElev,
              boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
              color: COLOR.textDim,
              fontFamily: FONT_MONO,
              fontSize: 11,
              fontWeight: 400,
              lineHeight: 1.5,
              textAlign: "left"
            }}
          >
            {children}
          </span>,
          document.body
        ) : null}
    </span>
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

// Promoted Card (§1.4 — ends the triplication across ui.tsx / IngestScreen /
// IngestActivity). Transparent bg, 1px border, 2px radius; state shows as a 3px
// left border in the semantic palette (rule 6/8). New screens use this one.
export type CardStatus = "running" | "done" | "error" | "attention" | "probe" | "neutral";

const CARD_STATUS_COLOR: Record<CardStatus, string | null> = {
  running: COLOR.cyan,
  done: COLOR.green,
  error: COLOR.red,
  attention: COLOR.amber,
  probe: COLOR.pink,
  neutral: null
};

export function Card({
  children,
  status = "neutral",
  selected = false,
  onClick,
  style = {}
}: {
  children: ReactNode;
  status?: CardStatus;
  selected?: boolean;
  onClick?: () => void;
  style?: CSSProperties;
}) {
  const statusColor = CARD_STATUS_COLOR[status];
  const leftColor = selected ? COLOR.amber : statusColor;
  return (
    <div
      onClick={onClick}
      style={{
        fontFamily: FONT_MONO,
        border: `1px solid ${selected ? COLOR.amber : COLOR.border}`,
        borderLeft: leftColor ? `3px solid ${leftColor}` : `1px solid ${selected ? COLOR.amber : COLOR.border}`,
        borderRadius: 2,
        padding: "14px 18px",
        background: "transparent",
        cursor: onClick ? "pointer" : "default",
        ...style
      }}
    >
      {children}
    </div>
  );
}
