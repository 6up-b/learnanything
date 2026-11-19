import { useEffect, useRef, useState } from "react";
import { encodeImageToJpeg } from "../util/encodeImage";
import { newUlid } from "../util/ulid";
import { addToOutbox, listOutbox, removeFromOutbox, type OutboxRecord } from "../store/outbox";

/** UX-9 (audit phone-2 #31-48): what happened to the last capture, in words. */
export const CAPTURE_COPY = {
  /** Sent while the screen is open: the desktop accepted it. Stays until the next capture. */
  sent: "Sent to your desktop.",
  /** Saved on the phone and not sent yet (the desktop out of reach). */
  savedHere: "Saved on this phone. It goes to your desktop when it's in reach.",
  /** Saved, its first send under way. */
  sending: "Saved. Sending to your desktop…"
} as const;

const URLISH = /^(https?:\/\/\S+|(arxiv:)?\d{4}\.\d{4,5}(v\d+)?)$/i;

/** Saving makes a reference; no practice begins (T6). Saved to the outbox first, so a sleeping
 *  desktop loses nothing (§7), and sent whenever one is in reach.
 *
 *  UX-9 (audit phone-2 #31-48): the screen read the outbox only when it saved, before the send
 *  it started had settled, so "1 waiting to send." stayed after the desktop had taken the
 *  capture. It now reads the outbox again when that send settles and whenever the app's flush
 *  changes the count, and says what became of the last capture: sent, or saved here to go later. */
export function CaptureScreen({ onSaved, outboxWaiting }: {
  /** The app's flush; the screen reads the outbox again once it settles. */
  onSaved: () => Promise<void> | void;
  /** The app's count of captures waiting, after its latest flush (on open, focus, every minute). */
  outboxWaiting?: number;
}) {
  const [text, setText] = useState("");
  const [note, setNote] = useState("");
  const [records, setRecords] = useState<OutboxRecord[]>([]);
  // The last capture saved here: sending (its first send not settled), waiting, or sent.
  const [last, setLast] = useState<{ id: string; state: "sending" | "waiting" | "sent" } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const photo = useRef<HTMLInputElement>(null);
  const lastRef = useRef(last);
  lastRef.current = last;

  const refresh = (settled = false) =>
    listOutbox()
      .then((list) => {
        setRecords(list);
        const current = lastRef.current;
        if (!current) return;
        const record = list.find((one) => one.clientCaptureId === current.id);
        // Gone without a problem: the desktop took it (a record leaves only on 201 or 200).
        if (!record) setLast({ id: current.id, state: "sent" });
        else if (record.problem) setLast(null);
        else if (settled || current.state !== "sending") setLast({ id: current.id, state: "waiting" });
      })
      .catch(() => undefined);
  useEffect(() => {
    void refresh();
  }, [outboxWaiting]);

  async function save(record: Pick<OutboxRecord, "kind" | "text" | "url" | "note" | "media">) {
    setError(null);
    try {
      const id = newUlid();
      await addToOutbox({ clientCaptureId: id, capturedAt: new Date().toISOString(), ...record });
      setText("");
      setNote("");
      lastRef.current = { id, state: "sending" };
      setLast(lastRef.current);
      await refresh();
      await onSaved();
      await refresh(true);
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
      <textarea id="capture-text" rows={5} value={text} onChange={(event) => setText(event.target.value)} />
      <label htmlFor="capture-note">Note (optional)</label>
      <input id="capture-note" value={note} onChange={(event) => setNote(event.target.value)} />
      {last ? (
        <p className="dim" role="status">
          {last.state === "sent" ? CAPTURE_COPY.sent : last.state === "waiting" ? CAPTURE_COPY.savedHere : CAPTURE_COPY.sending}
        </p>
      ) : null}
      {error ? <p className="bad" role="alert">{error}</p> : null}
      {waiting > 0 ? <p className="dim">{waiting} waiting to send.</p> : null}
      {stuck.map((record) => (
        <div className="banner" key={record.clientCaptureId}>
          <div>{record.text ?? record.url ?? "Photo"}</div>
          <div className="bad">{record.problem?.message}</div>
          <div className="row">
            <button className="plain" type="button" onClick={() => void removeFromOutbox(record.clientCaptureId).then(() => refresh())}>Dismiss</button>
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
