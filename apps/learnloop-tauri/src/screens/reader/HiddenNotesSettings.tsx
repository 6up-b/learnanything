// followups-nov1c C (curriculum C2 ruling R5): Settings lists the note links the learner
// hid (one tap, "hide", beside a › mark or on a path line), so one can be brought back
// after the reading changed, when the reading's own undo is long gone. One row per hidden
// link: the note's title and heading, its date, where it was linked and who linked it,
// with "show again" (notes.decide keep: the learner's own word again). The note's text and
// where it lives are never shown here. Absent while nothing is hidden, or with the notes
// switched off or tend absent (the RPC refuses; W11: no disabled control).
import { useEffect, useState, type CSSProperties } from "react";
import { api } from "../../api/client";
import type { HiddenNoteDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { errorMessage } from "../../errors";
import { MeaningLabel } from "./voices";

export const HIDDEN_NOTES_COPY = {
  label: "hidden notes",
  hiddenFrom: "hidden from",
  showAgain: "show again",
  // Honest: a link the learner made shows again at once; a model's link only where the
  // topic's current proposals still name that note (a keep is the learner's decision).
  shownByYou: "your note is shown again beside that passage",
  shownByModel: "shown again wherever LearnLoop's model still links that note",
} as const;

function noteName(entry: HiddenNoteDto): string {
  return [entry.note.title, entry.note.heading].filter(Boolean).join(" › ");
}

export function HiddenNotesSettings({
  rowStyle,
  labelStyle,
  onToast,
}: {
  rowStyle: CSSProperties;
  labelStyle: CSSProperties;
  onToast: (message: string) => void;
}) {
  const [hidden, setHidden] = useState<HiddenNoteDto[] | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let alive = true;
    Promise.resolve()
      .then(() => api.notesHidden())
      .then((out) => {
        if (alive) setHidden(out.hidden);
      })
      .catch(() => undefined); // notes off or tend absent: nothing to list
    return () => {
      alive = false;
    };
  }, []);
  if (!hidden || hidden.length === 0) return null;
  const showAgain = async (entry: HiddenNoteDto) => {
    if (busy) return;
    setBusy(true);
    try {
      await api.notesDecide({ linkId: entry.linkId, choice: "keep" });
      setHidden((current) => (current ?? []).filter((other) => other.linkId !== entry.linkId));
      // Who made the link, by its origin (the server's rule: a model's link keeps its topic,
      // learningObjectId), never by its target: a model can link a note to a passage too
      // (Codex review F4), and keeping that only lifts the hide.
      onToast(entry.learningObjectId ? HIDDEN_NOTES_COPY.shownByModel : HIDDEN_NOTES_COPY.shownByYou);
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
    <div data-hidden-notes-settings="" style={{ ...rowStyle, borderBottom: "none", flexDirection: "column", alignItems: "flex-start", gap: 4 }}>
      <span style={labelStyle}>{HIDDEN_NOTES_COPY.label}</span>
      {hidden.map((entry) => (
        <span key={entry.linkId} data-hidden-note={entry.linkId} style={{ display: "inline-flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}>
          <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
            <span aria-hidden="true" style={{ color: COLOR.amber }}>› </span>{noteName(entry)}
            {entry.note.dateLabel ? ` · ${entry.note.dateLabel}` : ""}
          </span>
          <MeaningLabel>
            {HIDDEN_NOTES_COPY.hiddenFrom} {entry.where} · {entry.byLabel}
            {entry.note.originLabel ? ` · ${entry.note.originLabel}` : ""}
          </MeaningLabel>
          <button
            type="button"
            disabled={busy}
            aria-label={`${HIDDEN_NOTES_COPY.showAgain}: ${noteName(entry)}`}
            onClick={() => void showAgain(entry)}
            style={link}
          >
            {HIDDEN_NOTES_COPY.showAgain}
          </button>
        </span>
      ))}
    </div>
  );
}
