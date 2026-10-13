// Daily-loop DL1 (spec_daily_loop_v1.md §6.10): the reader, opened by a plan's
// reading block. "Back to today's plan" ends the block (`left_reader`); its
// estimate counts as used either way. Completing the section in the reader ends
// it too (`section_completed`, recorded by the sidecar on the progress write).

import { useState } from "react";
import { api } from "../api/client";
import type { PlanReadingDto } from "../api/dto";
import { aboutMinutes } from "../app/dailyPlan";
import { COLOR, FONT_MONO } from "./term";

export function PlanReadingBanner({
  reading,
  estMinutes,
  sessionId,
  onBack,
  onError
}: {
  reading: PlanReadingDto;
  estMinutes: number | null;
  sessionId: string | null;
  onBack: () => void;
  onError: (message: string) => void;
}) {
  const [leaving, setLeaving] = useState(false);
  async function back() {
    if (leaving) return;
    setLeaving(true);
    try {
      await api.planReadingEnded("left_reader", sessionId);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setLeaving(false);
      onBack();
    }
  }
  return (
    <div
      data-testid="plan-reading-banner"
      role="status"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "6px 14px",
        borderBottom: `1px solid ${COLOR.border}`,
        background: COLOR.washCyan,
        fontFamily: FONT_MONO,
        fontSize: 12,
        color: COLOR.text,
        flexShrink: 0
      }}
    >
      <span>
        Reading for today's plan · {reading.sectionTitle}
        {estMinutes != null ? ` · ${aboutMinutes(estMinutes)}` : ""}
        {reading.partial && reading.fullMinutes ? ` (of ${aboutMinutes(reading.fullMinutes)})` : ""}
      </span>
      <span style={{ flex: 1 }} />
      <button
        type="button"
        onClick={() => void back()}
        disabled={leaving}
        style={{ border: `1px solid ${COLOR.amber}`, background: "transparent", color: COLOR.amber, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 12, padding: "3px 10px" }}
      >
        {leaving ? "leaving…" : "Back to today's plan"}
      </button>
    </div>
  );
}
