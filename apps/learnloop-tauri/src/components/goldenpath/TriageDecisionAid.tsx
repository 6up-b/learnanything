// Triage decision aid (spec_p2 §6, U-027; spec_tauri_ui §3 P2 row).
//
// Deterministic route (tier one): stated plainly. Provisional distribution
// (tier two): alternatives listed glyph+label+color with an override affordance;
// NEVER silently applied to a consequential transition. Overrides log as anchors.

import { COLOR, Card, Dim, Faint, FONT_MONO, Pill, SectionHeader } from "../term";
import { CalibrationBadge, SecondaryButton } from "./shared";
import type { TriageResultDto, TriageRouteDto } from "../../api/dto";

function humanReason(reason: string): string {
  return reason.replace(/_/g, " ");
}

function RouteBody({ route }: { route: TriageRouteDto }) {
  return (
    <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim, lineHeight: 1.7 }}>
      <div>
        <Faint>ladder entry</Faint> <Dim>{route.ladderEntryStage}</Dim>
      </div>
      <div>
        <Faint>first intervention</Faint> {humanReason(route.firstIntervention)}
      </div>
      <div>
        <Faint>cold follow-up</Faint> {humanReason(route.coldFollowUp)}
      </div>
      <div>
        <Faint>reopens diagnostic</Faint> {route.reopensDiagnostic ? "yes" : "no"}
      </div>
    </div>
  );
}

export function TriageDecisionAid({
  triage,
  onOverride,
}: {
  triage: TriageResultDto;
  onOverride?: (reason: string) => void;
}) {
  const decisive = triage.decisive;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <SectionHeader style={{ marginTop: 0 }}>Failure Triage</SectionHeader>
      {decisive ? (
        // Tier one — a deterministic route, stated plainly.
        <Card status="attention" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
            <Pill color="amber">tier one · deterministic route</Pill>
            <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.amber }}>
              {humanReason(triage.reason ?? "—")}
            </span>
          </div>
          <Faint style={{ fontSize: 11 }}>evidence is decisive — this route is applied automatically.</Faint>
          {triage.route ? <RouteBody route={triage.route} /> : null}
        </Card>
      ) : (
        // Tier two — a provisional distribution presented as a decision aid.
        <Card status="probe" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
            <Pill color="pink">tier two · decision aid</Pill>
            <CalibrationBadge status="heuristic" />
          </div>
          <Faint style={{ fontSize: 11 }}>
            provisional — not applied to any consequential transition without your confirmation.
          </Faint>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {(triage.alternatives.length > 0
              ? triage.alternatives
              : Object.entries(triage.distribution ?? {}).map(([reason, weight]) => ({
                  reason,
                  weight,
                  route: null as TriageRouteDto | null,
                }))
            )
              .slice()
              .sort((a, b) => b.weight - a.weight)
              .map((alt, idx) => {
                const recommended = idx === 0;
                return (
                  <div
                    key={alt.reason}
                    style={{
                      border: `1px solid ${recommended ? COLOR.pink : COLOR.border}`,
                      borderRadius: 2,
                      padding: "8px 12px",
                      display: "flex",
                      flexDirection: "column",
                      gap: 6,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                      <span style={{ color: recommended ? COLOR.pink : COLOR.textFaint }}>
                        {recommended ? "▸" : "·"}
                      </span>
                      <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
                        {humanReason(alt.reason)}
                      </span>
                      <Faint>{(alt.weight * 100).toFixed(0)}%</Faint>
                      {recommended ? <Pill color="pink">recommended</Pill> : null}
                      {onOverride ? (
                        <span style={{ marginLeft: "auto" }}>
                          <SecondaryButton onClick={() => onOverride(alt.reason)}>choose this →</SecondaryButton>
                        </span>
                      ) : null}
                    </div>
                    {alt.route ? <RouteBody route={alt.route} /> : null}
                  </div>
                );
              })}
          </div>
        </Card>
      )}
    </div>
  );
}
