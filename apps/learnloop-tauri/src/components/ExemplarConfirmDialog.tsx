// Atomic confirmation dialog (spec_p2 §3.1, §1.2 inv 2; spec_tauri_ui §3 row).
//
// The one atomic confirmation: goal contract v1 + commitment + DepthEnvelopeCard
// preset + assessment reservation, minted in ONE ↵ (QuickAddDialog composition
// pattern incl. consent/token checkpoint). Four owner-review artifacts are shown
// before the single confirm: the selected exemplars, the depth preset/envelope,
// the fresh held-out assessment reservation, and the goal-contract summary.
//
// Offline render (no confirmInput): the blueprint fixture is previewed with the
// confirm disabled — the review surface renders with no live sidecar.

import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { BlueprintVersionDto, CommandError, DepthEdgeDto } from "../api/dto";
import { COLOR, Faint, FONT_MONO, Meta, Pill, SectionHeader } from "./term";
import { DepthEnvelopeCard, PrimaryButton, SecondaryButton } from "./goldenpath/shared";
import { goldenPathFixtures } from "../fixtures/goldenpath";

const DEPTH_PRESETS = ["master_tasks_like_these", "one_solid_pass", "deep_transfer"];

export type ConfirmInput = Parameters<typeof api.goldenPathConfirm>[0];

export function ExemplarConfirmDialog({
  blueprintVersionId,
  confirmInput,
  onConfirmed,
  onClose,
  onError,
}: {
  // Live: fetch the blueprint version by id. Offline: use the fixture.
  blueprintVersionId?: string | null;
  // When present, the single ↵ mints the run atomically.
  confirmInput?: Omit<ConfirmInput, "depthPreset"> | null;
  onConfirmed?: (runId: string) => void;
  onClose: () => void;
  onError: (message: string) => void;
}) {
  const [blueprint, setBlueprint] = useState<BlueprintVersionDto | null>(
    blueprintVersionId ? null : goldenPathFixtures.blueprintVersion,
  );
  const [depthPreset, setDepthPreset] = useState(DEPTH_PRESETS[0]);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!blueprintVersionId) return;
    api
      .blueprintGetVersion(blueprintVersionId)
      .then(setBlueprint)
      .catch((error) => onError((error as CommandError).message));
  }, [blueprintVersionId, onError]);

  const edge = goldenPathFixtures.depthInvitation.invitation?.edge as DepthEdgeDto | undefined;
  // "reviewed" is confirmable: the atomic confirmation activates the blueprint
  // inside its own transaction (task_blueprints.activate docstring).
  const canConfirm =
    Boolean(confirmInput) && consent && !busy &&
    (blueprint?.status === "active" || blueprint?.status === "reviewed");

  const confirm = async () => {
    if (!confirmInput) return;
    setBusy(true);
    try {
      const receipt = await api.goldenPathConfirm({ ...confirmInput, depthPreset });
      onConfirmed?.(receipt.runId);
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  const exemplars = blueprint?.exemplars ?? [];
  const selected = exemplars.filter((e) => e.weight > 0);
  const heldOut = exemplars.filter((e) => e.heldOutWeight > 0);

  return (
    <div
      onClick={onClose}
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 500, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ width: 560, maxHeight: "88vh", overflowY: "auto", background: COLOR.bg, border: `1px solid ${COLOR.borderStrong}`, borderRadius: 2, padding: "22px 26px", display: "flex", flexDirection: "column", gap: 12 }}
        className="ll-scroll"
      >
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <span style={{ fontFamily: FONT_MONO, fontSize: 11, letterSpacing: "0.18em", color: COLOR.textFaint }}>
            CONFIRM EXEMPLAR &amp; START
          </span>
          {blueprint ? <Pill color={blueprint.status === "active" ? "green" : "amber"}>{blueprint.status}</Pill> : null}
        </div>
        <Faint style={{ fontSize: 12 }}>
          one ↵ mints goal-contract v1 + commitment + depth envelope + a fresh held-out reserve. If any part fails, none
          becomes active.
        </Faint>

        <SectionHeader style={{ marginTop: 6 }}>Selected exemplars</SectionHeader>
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {selected.map((e) => (
            <div key={e.id} style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: FONT_MONO, fontSize: 12 }}>
              <span style={{ color: COLOR.text }}>{e.exemplarRef}</span>
              <Pill color="cyan">{e.exposureStatus}</Pill>
              <Faint>weight {e.weight.toFixed(1)}</Faint>
            </div>
          ))}
          {selected.length > 1 ? <Faint style={{ fontSize: 11 }}>multiple exercises → a target distribution.</Faint> : null}
        </div>

        <SectionHeader>Fresh assessment reservation</SectionHeader>
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {heldOut.map((e) => (
            <div key={e.id} style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: FONT_MONO, fontSize: 12 }}>
              <span style={{ color: COLOR.text }}>{e.exemplarRef}</span>
              <Pill color="pink">{e.exposureStatus}</Pill>
              <Faint>held out · weight 0</Faint>
            </div>
          ))}
          <Faint style={{ fontSize: 11 }}>the unseen sibling — a selected exemplar can never be labeled held out.</Faint>
        </div>

        <SectionHeader>Depth</SectionHeader>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {DEPTH_PRESETS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setDepthPreset(p)}
              style={{
                fontFamily: FONT_MONO,
                fontSize: 12,
                padding: "4px 12px",
                borderRadius: 2,
                cursor: "pointer",
                background: depthPreset === p ? COLOR.washAmber : "transparent",
                border: `1px solid ${depthPreset === p ? COLOR.amber : COLOR.border}`,
                color: depthPreset === p ? COLOR.amber : COLOR.textDim,
              }}
            >
              {p}
            </button>
          ))}
        </div>
        <DepthEnvelopeCard preset={depthPreset} edge={edge} policyRecommendation="suggest_next" />
        <Faint style={{ fontSize: 11 }}>
          depth policy is chosen once here — <Meta>suggest_next</Meta> is recommended (U-018: no unprompted activation).
        </Faint>

        {/* consent / token checkpoint */}
        <label style={{ display: "flex", alignItems: "flex-start", gap: 8, fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim, cursor: "pointer" }}>
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} style={{ marginTop: 2 }} />
          <span>I confirm this reserves a fresh cold assessment and starts a certifying run.</span>
        </label>

        <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
          <PrimaryButton onClick={confirm} disabled={!canConfirm}>
            confirm &amp; start ↵
          </PrimaryButton>
          <SecondaryButton onClick={onClose}>cancel</SecondaryButton>
        </div>
        {!confirmInput ? <Faint style={{ fontSize: 11 }}>offline preview — confirm requires a live blueprint + goal.</Faint> : null}
      </div>
    </div>
  );
}
