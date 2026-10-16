// Small shared pieces of UX Phase 4's plain surfaces (docs/specs/ux_learnloop_v1.md
// §4.3): the one disclosure pattern ("details ▸" on the object, collapsed by
// default, remembered for the visit only), the learner/model/book voices, and
// the primary and quiet actions.
import type { CSSProperties, ReactNode } from "react";
import { COLOR, FONT_MONO } from "./term";

export function DetailsToggle({
  open,
  onToggle,
  label = "details",
  style
}: {
  open: boolean;
  onToggle: () => void;
  label?: string;
  style?: CSSProperties;
}) {
  return (
    <button
      type="button"
      aria-expanded={open}
      onClick={onToggle}
      style={{ ...quietLink, ...style }}
    >
      {label} {open ? "▾" : "▸"}
    </button>
  );
}

/** One primary action on the surface (§4.2): at most one per screen. */
export function PrimaryAction({
  children,
  hotkey,
  onClick,
  disabled,
  ariaLabel
}: {
  children: ReactNode;
  hotkey?: string;
  onClick: () => void;
  disabled?: boolean;
  ariaLabel?: string;
}) {
  return (
    <button className="plain-action primary" type="button" onClick={onClick} disabled={disabled} aria-label={ariaLabel}>
      <span>{children}</span>
      {hotkey ? <span className="plain-key" aria-hidden="true">{hotkey}</span> : null}
    </button>
  );
}

/** A quiet action beside the primary one. */
export function QuietAction({
  children,
  onClick,
  disabled,
  ariaLabel
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
  ariaLabel?: string;
}) {
  return (
    <button className="plain-action" type="button" onClick={onClick} disabled={disabled} aria-label={ariaLabel}>
      <span>{children}</span>
    </button>
  );
}

/** "› You wrote" / "◇ A full answer" / "§ the book": the three voices (§7.5). */
export function VoicePanel({ mark, title, children }: { mark: string; title: string; children: ReactNode }) {
  return (
    <div
      style={{
        border: `1px solid ${COLOR.border}`,
        padding: "10px 14px",
        minWidth: 0,
        background: COLOR.bgElev
      }}
    >
      <div style={{ fontSize: 12, color: COLOR.textDim, marginBottom: 6 }}>
        <span aria-hidden="true" style={{ color: COLOR.amber, marginRight: 6, fontFamily: FONT_MONO }}>{mark}</span>
        <span>{title}</span>
      </div>
      <div style={{ fontSize: 13, lineHeight: 1.6, color: COLOR.text, overflowWrap: "anywhere" }}>{children}</div>
    </div>
  );
}

export const quietLink: CSSProperties = {
  background: "transparent",
  border: "none",
  padding: 0,
  color: COLOR.textDim,
  textDecoration: "underline",
  textUnderlineOffset: 3,
  cursor: "pointer",
  fontSize: 12,
  fontFamily: "inherit"
};

export const quietLine: CSSProperties = {
  color: COLOR.textDim,
  fontSize: 12,
  lineHeight: 1.6
};
