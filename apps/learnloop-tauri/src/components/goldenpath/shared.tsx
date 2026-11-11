// Shared primitives first built for the P2 golden path (spec_tauri_ui §1.5),
// now the Reader's: the disposition picker, the affect tap and the two buttons.
// Every one follows the fifteen-rule contract: mono only, term.tsx tokens, glyph + label + color for
// non-monotone state, real buttons with keyboard affordances.

import { useState, type ReactNode } from "react";
import { COLOR, Faint, FONT_MONO } from "../term";
import type { ReaderDisposition } from "../../api/dto";

// ── DispositionPicker (§1.5, U-033) — one-row inline choice, walking-past ok ──
const DISPOSITIONS: Array<{ id: ReaderDisposition; glyph: string; label: string; hint: string }> = [
  { id: "comprehension_only", glyph: "◦", label: "just understanding", hint: "logged, never resurfaces" },
  { id: "check_once_later", glyph: "◑", label: "check once later", hint: "one single-use cold check" },
  { id: "keep_developing", glyph: "●", label: "keep developing", hint: "commit-class → a new target" },
  { id: "reference_only", glyph: "⌂", label: "reference only", hint: "citation kept, no practice" },
];

export function DispositionPicker({
  value,
  onChoose,
  disabled = false,
}: {
  value?: ReaderDisposition | null;
  onChoose: (d: ReaderDisposition) => void;
  disabled?: boolean;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <Faint style={{ fontSize: 11 }}>walking past = just understanding (never an obligation)</Faint>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {DISPOSITIONS.map((d) => {
          const active = value === d.id;
          return (
            <button
              key={d.id}
              type="button"
              disabled={disabled}
              onClick={() => onChoose(d.id)}
              title={d.hint}
              style={{
                fontFamily: FONT_MONO,
                fontSize: 12,
                padding: "4px 12px",
                borderRadius: 2,
                cursor: disabled ? "default" : "pointer",
                background: active ? COLOR.washAmber : "transparent",
                border: `1px solid ${active ? COLOR.amber : COLOR.border}`,
                color: active ? COLOR.amber : COLOR.textDim,
              }}
            >
              {d.glyph} {d.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ── AffectTap (§1.5, P0 §4.6) — one optional touch, six typed signals ─────────
const AFFECT_SIGNALS: Array<{ id: string; label: string }> = [
  { id: "felt_rote", label: "felt rote" },
  { id: "productive_struggle", label: "productive struggle" },
  { id: "confused", label: "confused" },
  { id: "clicked", label: "it clicked" },
  { id: "not_worth_attention", label: "not worth my attention" },
  { id: "fatigued", label: "fatigued" },
];

export function AffectTap({ onTap }: { onTap?: (signal: string) => void }) {
  const [open, setOpen] = useState(false);
  const [chosen, setChosen] = useState<string | null>(null);
  return (
    <div style={{ fontFamily: FONT_MONO, fontSize: 12 }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        style={{ background: "transparent", border: "none", color: COLOR.textFaint, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 12, padding: 0 }}
      >
        {open ? "▾" : "▸"} how did that feel
      </button>
      {open ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 6 }}>
          {AFFECT_SIGNALS.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => {
                setChosen(s.id);
                onTap?.(s.id);
              }}
              style={{
                fontFamily: FONT_MONO,
                fontSize: 11,
                padding: "2px 10px",
                borderRadius: 2,
                cursor: "pointer",
                background: chosen === s.id ? COLOR.washCyan : "transparent",
                border: `1px solid ${chosen === s.id ? COLOR.cyan : COLOR.border}`,
                color: chosen === s.id ? COLOR.cyan : COLOR.textDim,
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

// ── PrimaryButton / SecondaryButton (rule 9) ─────────────────────────────────
export function PrimaryButton({
  children,
  onClick,
  disabled = false,
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      style={{
        fontFamily: FONT_MONO,
        fontSize: 13,
        padding: "6px 16px",
        borderRadius: 2,
        cursor: disabled ? "default" : "pointer",
        background: disabled ? "transparent" : COLOR.washAmber,
        border: `1px solid ${disabled ? COLOR.border : COLOR.amber}`,
        color: disabled ? COLOR.textFaint : COLOR.amber,
      }}
    >
      {children}
    </button>
  );
}

export function SecondaryButton({
  children,
  onClick,
  disabled = false,
  active = false,
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  /** Toggle-style highlight (picker selections). */
  active?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      style={{
        fontFamily: FONT_MONO,
        fontSize: 13,
        padding: "6px 16px",
        borderRadius: 2,
        cursor: disabled ? "default" : "pointer",
        background: active ? COLOR.washAmber : "transparent",
        border: active ? `1px solid ${COLOR.amber}` : "none",
        color: active ? COLOR.amber : COLOR.textDim,
      }}
    >
      {children}
    </button>
  );
}
