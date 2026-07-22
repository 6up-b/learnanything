// Shared P2 golden-path primitives (spec_tauri_ui §1.5 new shared components).
// Every one follows the fifteen-rule contract: mono only, term.tsx tokens, glyph
// + label + color for non-monotone state, one continuous quantity per channel,
// real buttons with keyboard affordances.

import { useState, type CSSProperties, type ReactNode } from "react";
import {
  BlockBar,
  COLOR,
  Card,
  Dim,
  Faint,
  FONT_MONO,
  Pill,
  type PillColor,
} from "../term";
import type {
  BoundaryCellDto,
  BoundaryCellState,
  DepthEdgeDto,
  GpCalibrationStatus,
  GpClaimLanguage,
  GpInterval,
  LadderStageDto,
  ReaderDisposition,
} from "../../api/dto";

// ── CalibrationBadge (umbrella §1; P0 §6) ────────────────────────────────────
// Fixed slate/cyan/green mapping — a visible label on every model-derived claim.
const CALIBRATION_MAP: Record<GpCalibrationStatus, { color: PillColor; label: string }> = {
  heuristic: { color: "slate", label: "heuristic" },
  simulation_validated: { color: "cyan", label: "sim-validated" },
  live_calibrated: { color: "green", label: "live-calibrated" },
};

export function CalibrationBadge({ status, style }: { status: GpCalibrationStatus; style?: CSSProperties }) {
  const m = CALIBRATION_MAP[status] ?? CALIBRATION_MAP.heuristic;
  return (
    <Pill color={m.color} style={style}>
      ◆ {m.label}
    </Pill>
  );
}

// ── ClaimBadge — the §8.2 reliability-aware claim language (glyph+label+color) ─
const CLAIM_MAP: Record<GpClaimLanguage, { color: PillColor; glyph: string; label: string }> = {
  provisional: { color: "amber", glyph: "◐", label: "provisional" },
  calibrated: { color: "green", glyph: "✓", label: "certified for sample" },
  insufficient: { color: "red", glyph: "·", label: "insufficient" },
};

export function ClaimBadge({ claim, style }: { claim: GpClaimLanguage; style?: CSSProperties }) {
  const m = CLAIM_MAP[claim] ?? CLAIM_MAP.provisional;
  return (
    <Pill color={m.color} style={style}>
      {m.glyph} {m.label}
    </Pill>
  );
}

// ── IntervalBar — one continuous quantity (point) with an interval band ───────
// Renders the point estimate as the filled block bar; the [low, high] band is
// stated numerically (never blended onto the same continuous channel, §1.1).
export function IntervalBar({ interval }: { interval: GpInterval }) {
  return (
    <span style={{ display: "inline-flex", gap: 8, alignItems: "center", fontFamily: FONT_MONO, fontSize: 12 }}>
      <BlockBar value={interval.point} max={1} width={10} />
      <span style={{ color: COLOR.text }}>{interval.point.toFixed(2)}</span>
      <Faint>
        [{interval.low.toFixed(2)}–{interval.high.toFixed(2)}]
      </Faint>
    </span>
  );
}

// ── CheckpointLadder — the ✓ → ◐ → · multi-phase stage strip (rule 10) ────────
export type CheckpointState = "done" | "current" | "pending";
export interface Checkpoint {
  key: string;
  label: string;
  state: CheckpointState;
}
const CHECK_GLYPH: Record<CheckpointState, { glyph: string; color: string }> = {
  done: { glyph: "✓", color: COLOR.green },
  current: { glyph: "◐", color: COLOR.cyan },
  pending: { glyph: "·", color: COLOR.textFaint },
};

export function CheckpointLadder({ steps }: { steps: Checkpoint[] }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 6, fontFamily: FONT_MONO, fontSize: 12 }}>
      {steps.map((s, i) => {
        const g = CHECK_GLYPH[s.state];
        return (
          <span key={s.key} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <span style={{ color: g.color }}>{g.glyph}</span>
            <span style={{ color: s.state === "current" ? COLOR.cyan : s.state === "done" ? COLOR.text : COLOR.textFaint }}>
              {s.label}
            </span>
            {i < steps.length - 1 ? <span style={{ color: COLOR.textFaint }}>→</span> : null}
          </span>
        );
      })}
    </div>
  );
}

// ── DepthEnvelopeCard (§1.5) — depth preset + envelope preview + burden ───────
export function DepthEnvelopeCard({
  preset,
  edge,
  policyRecommendation = "suggest_next",
  onConfirm,
  confirmLabel = "confirm depth ↵",
}: {
  preset: string;
  edge?: DepthEdgeDto | null;
  policyRecommendation?: string;
  onConfirm?: () => void;
  confirmLabel?: string;
}) {
  const minutes = edge?.burden?.minutes;
  return (
    <Card status="attention" style={{ background: COLOR.washAmber, display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
        <span style={{ color: COLOR.amber, fontFamily: FONT_MONO, fontSize: 13 }}>{preset}</span>
        <Pill color="amber">served as {policyRecommendation}</Pill>
      </div>
      {edge ? (
        <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim, lineHeight: 1.6 }}>
          <div>
            <Faint>edge</Faint> {edge.edgeId} <Faint>·</Faint> {edge.direction} → <Dim>{edge.milestoneSlug}</Dim>
          </div>
          <div>
            <Faint>evidence</Faint> {String((edge.exitEvidence as { kind?: string })?.kind ?? "—")}{" "}
            <Faint>· fresh-proof</Faint> {edge.freshProofRule}
          </div>
          {minutes != null ? (
            <div>
              <Faint>burden budget</Faint> ~{minutes} min
            </div>
          ) : null}
        </div>
      ) : (
        <Faint style={{ fontSize: 12 }}>no reviewed outgoing edge — hold at target</Faint>
      )}
      {onConfirm ? (
        <div>
          <PrimaryButton onClick={onConfirm}>{confirmLabel}</PrimaryButton>
        </div>
      ) : null}
    </Card>
  );
}

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

// ── BoundaryView (§5.3) — capability × facet cells, relationship-not-deficit ──
// well-view channel discipline: discrete state is a discrete marker (glyph +
// color), the continuous point estimate is the block bar — never blended.
const CELL_STATE: Record<BoundaryCellState, { glyph: string; color: string; label: string }> = {
  demonstrated: { glyph: "●", color: COLOR.green, label: "demonstrated" },
  developing: { glyph: "◐", color: COLOR.cyan, label: "developing" },
  untested: { glyph: "○", color: COLOR.textFaint, label: "untested" },
  weak: { glyph: "◔", color: COLOR.amber, label: "weak" },
  contested: { glyph: "◍", color: COLOR.pink, label: "contested" },
};

export function BoundaryCellMarker({ state }: { state: BoundaryCellState }) {
  const m = CELL_STATE[state] ?? CELL_STATE.untested;
  return (
    <span style={{ display: "inline-flex", gap: 5, alignItems: "center", fontFamily: FONT_MONO, fontSize: 12 }}>
      <span style={{ color: m.color }}>{m.glyph}</span>
      <span style={{ color: m.color }}>{m.label}</span>
    </span>
  );
}

export function BoundaryView({ cells, passed }: { cells: BoundaryCellDto[]; passed?: boolean }) {
  const deepened = cells.filter((c) => c.changed);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {/* relationship-not-deficit: lead with what deepened, directions not deficiencies */}
      <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim }}>
        {deepened.length > 0 ? (
          <span>
            <span style={{ color: COLOR.green }}>{deepened.length}</span> capabilit
            {deepened.length === 1 ? "y" : "ies"} deepened this run — directions to keep developing, not deficits.
          </span>
        ) : (
          <span>no cells changed since baseline.</span>
        )}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {cells.map((c) => (
          <Card
            key={`${c.facet}:${c.capability}`}
            status={c.changed ? "done" : "neutral"}
            style={{ display: "flex", flexDirection: "column", gap: 6 }}
          >
            <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
              <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.text }}>{c.facet}</span>
              <Faint>×</Faint>
              <Dim>{c.capability}</Dim>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
              <BoundaryCellMarker state={c.before} />
              <span style={{ color: COLOR.textFaint }}>→</span>
              <BoundaryCellMarker state={c.after} />
              <ClaimBadge claim={c.claimLanguage} />
              <CalibrationBadge status={c.calibrationStatus} />
            </div>
            <IntervalBar interval={c.interval} />
          </Card>
        ))}
      </div>
      {passed != null ? (
        <Faint style={{ fontSize: 11 }}>
          assessment {passed ? "passed" : "not passed"} — estimates recomputed; your underlying evidence did not change.
        </Faint>
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

// ── LadderStrip — the nine-stage pattern ladder rendered as checkpoints ───────
export function ladderCheckpoints(stages: LadderStageDto[], currentStageKey: string | null): Checkpoint[] {
  const ordered = [...stages].sort((a, b) => a.ordinal - b.ordinal || a.stageKey.localeCompare(b.stageKey));
  const currentIdx = ordered.findIndex((s) => s.stageKey === currentStageKey);
  return ordered.map((s, i) => ({
    key: s.id,
    label: s.stageKey,
    state: currentIdx < 0 ? "pending" : i < currentIdx ? "done" : i === currentIdx ? "current" : "pending",
  }));
}
