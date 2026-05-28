// Terminal-style primitives ported from the handoff design (learnloop-handoff2).
// Inline-styled, monospace, dark-slate palette — used by the screens that follow
// the handoff layout language (Today, Graph, Library). The desktop shell/nav in
// ui.tsx keeps its own CSS-class styling; these primitives style screen *bodies*.

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
