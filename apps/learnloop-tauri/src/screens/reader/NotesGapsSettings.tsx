// Curriculum C5 (spec_deliverable_curriculum_v1 §10.2, §12 C5; owner Q9): the opt-in for
// the learner's linked notes to steer suggestions. Off by default; on, LearnLoop's model reads a
// note they linked (never one they hid) for gaps in their understanding, as tier-2 learner text
// (C2b: like their other questions and answers): it only ever steers what to suggest, never
// grades. Shown only where the notes are (the Reader's prompt contract carries `notes`:
// notes.enabled on); absent otherwise (W11: no disabled control).
import { useEffect, useState, type CSSProperties } from "react";
import { api } from "../../api/client";
import type { NotesContractDto } from "../../api/dto";
import { invalidate } from "../../api/queryCache";
import { TermCheckbox } from "../../components/term";
import { errorMessage } from "../../errors";
import { MeaningLabel } from "./voices";

export const NOTES_GAPS_COPY = {
  label: "your notes",
  toggle: "let my linked notes steer suggestions",
  line: "Off unless you turn it on. LearnLoop's model reads the notes you've linked (never one you hid) for gaps in your understanding. It only ever steers what to suggest, never grades you.",
  on: "your linked notes now steer suggestions",
  off: "your notes no longer steer suggestions",
} as const;

export function NotesGapsSettings({
  rowStyle,
  labelStyle,
  onToast,
}: {
  rowStyle: CSSProperties;
  labelStyle: CSSProperties;
  onToast: (message: string) => void;
}) {
  const [notes, setNotes] = useState<NotesContractDto | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let alive = true;
    Promise.resolve()
      .then(() => api.readerPromptContract())
      .then((contract) => {
        if (alive) setNotes(contract?.notes ?? null);
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, []);
  if (!notes?.enabled) return null;
  const checked = Boolean(notes.gaps);
  const choose = async (next: boolean) => {
    if (busy || next === checked) return;
    setBusy(true);
    try {
      const saved = await api.notesSetGaps({ enabled: next });
      setNotes({ ...notes, gaps: saved.gapsEnabled || undefined });
      // The notes surfaces read the opt-in from the Reader's prompt contract.
      invalidate({ key: ["reader_prompt_contract"] });
      onToast(saved.gapsEnabled ? NOTES_GAPS_COPY.on : NOTES_GAPS_COPY.off);
    } catch (error) {
      onToast(errorMessage(error));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div data-notes-gaps-settings="" style={{ ...rowStyle, borderBottom: "none", flexDirection: "column", alignItems: "flex-start", gap: 4 }}>
      <span style={labelStyle}>{NOTES_GAPS_COPY.label}</span>
      <TermCheckbox checked={checked} disabled={busy} onChange={(next) => void choose(next)} label={NOTES_GAPS_COPY.toggle} compact />
      <MeaningLabel>{NOTES_GAPS_COPY.line}</MeaningLabel>
    </div>
  );
}
