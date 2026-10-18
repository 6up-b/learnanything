// Adaptive hints H2b (spec D5): the one stored help-style preference in
// Settings, the same three settings the hint panel's "⋯" menu edits
// ([hints] help_style). Absent while adaptive hints are off (no disabled
// control), so Settings is then exactly as before.
import { useState, type CSSProperties } from "react";
import { api } from "../../api/client";
import type { HelpStyle } from "../../api/dto";
import { algoConfig, setAdaptiveHelpStyle } from "../../app/algoConfig";
import { COLOR, FONT_MONO } from "../../components/term";
import { SectionHeader } from "../../components/ui";
import { errorMessage } from "../../errors";
import { HELP_STYLE_COPY, HINT_COPY } from "./hintCopy";

export function HelpStyleSettings({
  rowStyle,
  labelStyle,
  onToast
}: {
  rowStyle: CSSProperties;
  labelStyle: CSSProperties;
  onToast: (message: string) => void;
}) {
  const adaptive = algoConfig().adaptiveHints;
  const [style, setStyle] = useState<HelpStyle>(adaptive?.helpStyle ?? "balanced");
  const [busy, setBusy] = useState(false);
  if (!adaptive) return null;
  const choose = async (next: HelpStyle) => {
    if (next === style || busy) return;
    setBusy(true);
    try {
      const saved = await api.setHelpStyle(next);
      setAdaptiveHelpStyle(saved.helpStyle);
      setStyle(saved.helpStyle);
      onToast(`${HINT_COPY.menuLabel} → ${HELP_STYLE_COPY.find((entry) => entry.value === saved.helpStyle)?.label ?? saved.helpStyle}`);
    } catch (error) {
      onToast(errorMessage(error));
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <SectionHeader>Hints</SectionHeader>
      <div style={{ ...rowStyle, borderBottom: "none", flexWrap: "wrap" }}>
        <span style={labelStyle}>{HINT_COPY.menuLabel}</span>
        <span role="group" aria-label={HINT_COPY.menuLabel} style={{ display: "inline-flex", gap: 8, flexWrap: "wrap" }}>
          {HELP_STYLE_COPY.map((entry) => (
            <button
              key={entry.value}
              type="button"
              aria-pressed={style === entry.value}
              title={entry.line}
              disabled={busy}
              onClick={() => void choose(entry.value)}
              style={{
                border: `1px solid ${style === entry.value ? COLOR.borderFocus : COLOR.border}`,
                background: style === entry.value ? COLOR.washAmber : "transparent",
                color: style === entry.value ? COLOR.amberLink : COLOR.textDim,
                fontFamily: FONT_MONO,
                fontSize: 11,
                padding: "3px 8px",
                cursor: "pointer"
              }}
            >
              {entry.label}
            </button>
          ))}
        </span>
        <span style={{ color: COLOR.textDim, fontSize: 12 }}>
          {HELP_STYLE_COPY.find((entry) => entry.value === style)?.line} · {HINT_COPY.menuNote}
        </span>
      </div>
    </>
  );
}
