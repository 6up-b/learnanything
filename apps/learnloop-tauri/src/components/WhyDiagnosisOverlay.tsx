// Why-this-diagnosis overlay (spec_p2 §6; spec_tauri_ui §3 P2 row).
//
// CommandOverlayFrame consumer, command="why" — the WhyPanel pattern: the locked
// hypothesis set (triage reasons), the probes/evidence used, per-response
// contributions, surviving alternatives, and a CalibrationBadge on the heuristic
// triage channel. Renders from a triage result (live or the fixture).

import { CommandOverlayFrame } from "./CommandOverlayFrame";
import { COLOR, Card, Dim, Faint, FONT_MONO, Pill, SectionHeader } from "./term";
import { BlockBar } from "./term";
import { CalibrationBadge } from "./goldenpath/shared";
import type { TriageResultDto } from "../api/dto";

function human(s: string): string {
  return s.replace(/_/g, " ");
}

export function WhyDiagnosisOverlay({
  triage,
  onClose,
}: {
  triage: TriageResultDto;
  onClose: () => void;
}) {
  const alts =
    triage.alternatives.length > 0
      ? triage.alternatives
      : Object.entries(triage.distribution ?? {}).map(([reason, weight]) => ({ reason, weight, route: null }));
  const sorted = [...alts].sort((a, b) => b.weight - a.weight);

  return (
    <CommandOverlayFrame
      command="why"
      context="this diagnosis"
      badge={<Pill color={triage.decisive ? "amber" : "pink"}>tier {triage.tier}</Pill>}
      onClose={onClose}
      footerKeys={<Faint style={{ fontFamily: FONT_MONO, fontSize: 12 }}>esc close</Faint>}
    >
      <div className="ll-scroll" style={{ padding: "16px 22px", overflowY: "auto", display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.text }}>
            recommended: <span style={{ color: COLOR.amber }}>{human(triage.reason ?? "—")}</span>
          </span>
          <CalibrationBadge status="heuristic" />
          {triage.decisive ? <Pill color="amber">decisive route</Pill> : <Pill color="pink">decision aid</Pill>}
        </div>

        <SectionHeader style={{ marginTop: 0 }}>Locked hypothesis set</SectionHeader>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {sorted.map((alt, i) => (
            <Card key={alt.reason} status={i === 0 ? "attention" : "neutral"} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>{human(alt.reason)}</span>
                <BlockBar value={alt.weight} max={1} width={10} />
                <Faint>{(alt.weight * 100).toFixed(0)}%</Faint>
                {i === 0 ? <Pill color="amber">surviving lead</Pill> : null}
              </div>
              {alt.route ? (
                <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
                  <Faint>route</Faint> {alt.route.routeId} <Faint>· ladder</Faint> <Dim>{alt.route.ladderEntryStage}</Dim>
                </div>
              ) : null}
            </Card>
          ))}
        </div>

        <SectionHeader>Grader assumptions</SectionHeader>
        <Faint style={{ fontFamily: FONT_MONO, fontSize: 12, lineHeight: 1.7 }}>
          the triage channel is registered <Dim>heuristic</Dim> so misroutes are discoverable. The route is snapshotted
          before any tutor prose is generated — prose can never change the action, target, scaffold, reveal budget, or
          follow-up contract. Overrides are logged as adjudication anchors into the calibration stream.
        </Faint>
      </div>
    </CommandOverlayFrame>
  );
}
