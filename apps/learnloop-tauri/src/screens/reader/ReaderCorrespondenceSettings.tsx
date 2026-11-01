// Reader CA5: Settings brings "also in your books" back (ux_reader_compare_ask_v1
// §6.2: "Hidden leaves nothing behind. Settings brings it back."). One row per
// thing the learner hid from the line's ⋯ (everywhere, or for a book, by
// name), each with "show again". Absent when nothing is hidden or the feature
// is switched off (W11: no disabled control).
import { useEffect, useState, type CSSProperties } from "react";
import { api } from "../../api/client";
import type { CorrespondencePreferencesDto } from "../../api/dto";
import { invalidate } from "../../api/queryCache";
import { COLOR, FONT_MONO } from "../../components/term";
import { errorMessage } from "../../errors";
import { MeaningLabel } from "./voices";

export const CORRESPONDENCE_SETTINGS_COPY = {
  label: "also in your books",
  everywhere: "hidden everywhere",
  forBook: "hidden for",
  showAgain: "show again",
  shown: "also in your books is shown again",
} as const;

export function ReaderCorrespondenceSettings({
  rowStyle,
  labelStyle,
  onToast,
}: {
  rowStyle: CSSProperties;
  labelStyle: CSSProperties;
  onToast: (message: string) => void;
}) {
  const [prefs, setPrefs] = useState<CorrespondencePreferencesDto | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let alive = true;
    Promise.resolve()
      .then(() => api.readerCorrespondencePreferences())
      .then((next) => {
        if (alive) setPrefs(next);
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, []);
  if (!prefs?.enabled || (!prefs.hideEverywhere && prefs.hiddenSources.length === 0)) return null;
  const show = async (input: { sourceId?: string; hideSource?: boolean; hideEverywhere?: boolean }) => {
    if (busy) return;
    setBusy(true);
    try {
      setPrefs(await api.readerSetCorrespondencePreferences(input));
      // The Reader reads the line's preferences from its prompt contract.
      invalidate({ key: ["reader_prompt_contract"] });
      onToast(CORRESPONDENCE_SETTINGS_COPY.shown);
    } catch (error) {
      onToast(errorMessage(error));
    } finally {
      setBusy(false);
    }
  };
  const link: CSSProperties = {
    border: 0, background: "transparent", padding: 0, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11,
    color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2,
  };
  return (
    <div data-correspondence-settings="" style={{ ...rowStyle, borderBottom: "none", flexDirection: "column", alignItems: "flex-start", gap: 4 }}>
      <span style={labelStyle}>{CORRESPONDENCE_SETTINGS_COPY.label}</span>
      {prefs.hideEverywhere ? (
        <span style={{ display: "inline-flex", gap: 8, alignItems: "baseline" }}>
          <MeaningLabel>{CORRESPONDENCE_SETTINGS_COPY.everywhere}</MeaningLabel>
          <button type="button" disabled={busy} onClick={() => void show({ hideEverywhere: false })} style={link}>{CORRESPONDENCE_SETTINGS_COPY.showAgain}</button>
        </span>
      ) : null}
      {prefs.hiddenSources.map((source) => (
        <span key={source.sourceId} style={{ display: "inline-flex", gap: 8, alignItems: "baseline" }}>
          <MeaningLabel>{CORRESPONDENCE_SETTINGS_COPY.forBook} {source.title}</MeaningLabel>
          <button
            type="button"
            disabled={busy}
            aria-label={`${CORRESPONDENCE_SETTINGS_COPY.showAgain}: ${source.title}`}
            onClick={() => void show({ sourceId: source.sourceId, hideSource: false })}
            style={link}
          >
            {CORRESPONDENCE_SETTINGS_COPY.showAgain}
          </button>
        </span>
      ))}
    </div>
  );
}
