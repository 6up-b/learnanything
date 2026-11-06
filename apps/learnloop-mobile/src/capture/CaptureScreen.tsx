import { useEffect, useRef, useState } from "react";
import { encodeImageToJpeg } from "../util/encodeImage";
import { newUlid } from "../util/ulid";
import { addToOutbox, listOutbox, removeFromOutbox, type OutboxRecord } from "../store/outbox";

const URLISH = /^(https?:\/\/\S+|(arxiv:)?\d{4}\.\d{4,5}(v\d+)?)$/i;

/** Saving makes a reference; no practice begins (T6). Saved to the outbox first, so a sleeping
 *  desktop loses nothing (§7), and sent whenever one is in reach. */
export function CaptureScreen({ onSaved }: { onSaved: () => void }) {
  const [text, setText] = useState("");
  const [note, setNote] = useState("");
  const [records, setRecords] = useState<OutboxRecord[]>([]);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const photo = useRef<HTMLInputElement>(null);

  const refresh = () => listOutbox().then(setRecords).catch(() => undefined);
  useEffect(() => {
    void refresh();
  }, []);

  async function save(record: Pick<OutboxRecord, "kind" | "text" | "url" | "note" | "media">) {
    setError(null);
    try {
      await addToOutbox({ clientCaptureId: newUlid(), capturedAt: new Date().toISOString(), ...record });
      setText("");
      setNote("");
      setSaved(true);
      onSaved();
      await refresh();
    } catch (failure) {
      // §7: a quota error is surfaced, never swallowed.
      setError(failure instanceof Error ? failure.message : "This phone couldn't save that.");
    }
  }

  async function saveText() {
    const value = text.trim();
    if (!value) return;
    const trimmedNote = note.trim() || undefined;
    await save(URLISH.test(value) ? { kind: "url", url: value, note: trimmedNote } : { kind: "text", text: value, note: trimmedNote });
  }

  async function savePhoto(file: File | undefined) {
    if (!file) return;
    try {
      await save({ kind: "image", media: await encodeImageToJpeg(file), note: note.trim() || undefined });
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "This phone couldn't prepare that photo.");
    }
  }

  const stuck = records.filter((record) => record.problem);
  const waiting = records.length - stuck.length;
  return (
    <div className="screen">
      <h1>Capture</h1>
      <label htmlFor="capture-text">A thought, a problem or a link</label>
      <textarea id="capture-text" rows={5} value={text} onChange={(event) => { setText(event.target.value); setSaved(false); }} />
      <label htmlFor="capture-note">Note (optional)</label>
      <input id="capture-note" value={note} onChange={(event) => setNote(event.target.value)} />
      {saved ? <p className="dim" role="status">Saved.</p> : null}
      {error ? <p className="bad" role="alert">{error}</p> : null}
      {waiting > 0 ? <p className="dim">{waiting} waiting to send.</p> : null}
      {stuck.map((record) => (
        <div className="banner" key={record.clientCaptureId}>
          <div>{record.text ?? record.url ?? "Photo"}</div>
          <div className="bad">{record.problem?.message}</div>
          <div className="row">
            <button className="plain" type="button" onClick={() => void removeFromOutbox(record.clientCaptureId).then(refresh)}>Dismiss</button>
          </div>
        </div>
      ))}
      <div className="actions">
        <button className="primary block" type="button" disabled={!text.trim()} onClick={() => void saveText()}>Save</button>
        <div className="row">
          <button className="plain" type="button" onClick={() => photo.current?.click()}>Photo</button>
          <input ref={photo} type="file" accept="image/*" hidden aria-label="Photo" onChange={(event) => void savePhoto(event.target.files?.[0])} />
        </div>
      </div>
    </div>
  );
}
