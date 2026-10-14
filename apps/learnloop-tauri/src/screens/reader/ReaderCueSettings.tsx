// Reader workbench RW3a: margin marks in Settings ("cues off everywhere also
// from Settings", spec §6.1). The same density the Guide's footer sets, kept
// in the vault's [cues] config; absent when cues are switched off (W11: no
// disabled control) or the sidecar does not know them.
import { useEffect, useState, type CSSProperties } from "react";
import { api } from "../../api/client";
import type { CueDensity, ReaderCuePreferencesDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { SectionHeader } from "../../components/ui";
import { errorMessage } from "../../errors";
import { CUE_COPY, CUE_DENSITIES } from "./cues";
import { MeaningLabel } from "./voices";

export function ReaderCueSettings({
  rowStyle,
  labelStyle,
  onToast,
}: {
  rowStyle: CSSProperties;
  labelStyle: CSSProperties;
  onToast: (message: string) => void;
}) {
  const [prefs, setPrefs] = useState<ReaderCuePreferencesDto | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let alive = true;
    Promise.resolve()
      .then(() => api.readerCuePreferences({}))
      .then((next) => {
        if (alive) setPrefs(next);
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, []);
  if (!prefs?.enabled) return null;
  const choose = async (density: CueDensity) => {
    if (density === prefs.density || busy) return;
    setBusy(true);
    try {
      setPrefs(await api.readerSetCuePreferences({ density, via: "settings" }));
      onToast(`${CUE_COPY.receiptDensity} ${density}`);
    } catch (error) {
      onToast(errorMessage(error));
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <SectionHeader>Reader</SectionHeader>
      <div style={{ ...rowStyle, borderBottom: "none", flexWrap: "wrap" }}>
        <span style={labelStyle}>{CUE_COPY.footerLabel}</span>
        <span role="group" aria-label={CUE_COPY.footerLabel} style={{ display: "inline-flex", gap: 8 }}>
          {CUE_DENSITIES.map((density) => (
            <button
              key={density}
              type="button"
              aria-pressed={prefs.density === density}
              disabled={busy}
              onClick={() => void choose(density)}
              style={{
                border: `1px solid ${prefs.density === density ? COLOR.borderFocus : COLOR.border}`,
                background: prefs.density === density ? COLOR.washAmber : "transparent",
                color: prefs.density === density ? COLOR.amberLink : COLOR.textDim,
                fontFamily: FONT_MONO,
                fontSize: 11,
                padding: "3px 8px",
                cursor: "pointer",
              }}
            >
              {density}
            </button>
          ))}
        </span>
        <MeaningLabel>{CUE_COPY.footerLimit}</MeaningLabel>
      </div>
    </>
  );
}
