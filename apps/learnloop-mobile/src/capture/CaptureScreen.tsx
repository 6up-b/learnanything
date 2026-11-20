import { useEffect, useRef, useState } from "react";
import { encodeImageToJpeg } from "../util/encodeImage";
import { newUlid } from "../util/ulid";
import { useVisibleInterval } from "../util/useVisibleInterval";
import { addToOutbox, listOutbox, removeFromOutbox, type OutboxRecord } from "../store/outbox";

/** UX-9 (audit phone-2 #31-48): what happened to the last capture, in words. */
export const CAPTURE_COPY = {
  /** Sent: the desktop accepted it. Stays until the next capture. UX fix stage 4 (F13) adds when: `sentLine`. */
  sent: "Sent to your desktop",
  /** Saved on the phone and not sent yet (the desktop out of reach). */
  savedHere: "Saved on this phone. It goes to your desktop when it's in reach.",
  /** Saved, its first send under way. */
  sending: "Saved. Sending to your desktop…"
} as const;

/**
 * The last capture saved on this phone and what became of it. UX fix stage 4 (F13): the app holds it, not the
 * screen, so the line is still there when Capture is left and opened again while the app is open. It lives in
 * memory only: nothing new is stored on the record.
 */
export interface LastCapture {
  readonly id: string;
  /** The record's own time (`capturedAt`). */
  readonly capturedAt: string;
  readonly state: "sending" | "waiting" | "sent";
  /** When it was sent, in ms: the record's own time if its first send took it, else when this phone saw it leave. */
  readonly sentAt?: number;
}

/**
 * The last capture after a read of the outbox. Gone without a problem: the desktop took it (a record leaves only on
 * 201 or 200). A problem: its banner says so instead. Still there: waiting, once its first send has settled.
 */
export function settleLastCapture(current: LastCapture | null, list: readonly OutboxRecord[], settled: boolean, now: number): LastCapture | null {
  if (!current || current.state === "sent") return current;
  const record = list.find((one) => one.clientCaptureId === current.id);
  if (!record) {
    // Taken on its first send, the record's own time is when; after a wait, when this phone saw it go.
    const own = Date.parse(current.capturedAt);
    const sentAt = current.state === "sending" && Number.isFinite(own) ? own : now;
    return { ...current, state: "sent", sentAt };
  }
  if (record.problem) return null;
  if (settled || current.state !== "sending") return current.state === "waiting" ? current : { ...current, state: "waiting" };
  return current;
}

/** "just now", "2 min ago", "1 hour ago": how long since `at`. */
export function agoWords(at: number, now: number): string {
  const minutes = Math.floor(Math.max(0, now - at) / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  return hours === 1 ? "1 hour ago" : `${hours} hours ago`;
}

/** "Sent to your desktop · 2 min ago." */
export function sentLine(last: LastCapture, now: number): string {
  return `${CAPTURE_COPY.sent} · ${agoWords(last.sentAt ?? Date.parse(last.capturedAt), now)}.`;
}

/** How often the "· 2 min ago" is read again while Capture is on screen. */
const AGO_TICK_MS = 30_000;

const URLISH = /^(https?:\/\/\S+|(arxiv:)?\d{4}\.\d{4,5}(v\d+)?)$/i;

/** Saving makes a reference; no practice begins (T6). Saved to the outbox first, so a sleeping
 *  desktop loses nothing (§7), and sent whenever one is in reach.
 *
 *  UX-9 (audit phone-2 #31-48): the screen read the outbox only when it saved, before the send
 *  it started had settled, so "1 waiting to send." stayed after the desktop had taken the
 *  capture. It now reads the outbox again when that send settles and whenever the app's flush
 *  changes the count, and says what became of the last capture: sent, or saved here to go later.
 *
 *  UX fix stage 4 (F13, phone-2 #31-53): the sent line says when ("· 2 min ago"), and the app keeps
 *  the last capture, so leaving Capture and coming back still shows it. */
export function CaptureScreen({ onSaved, outboxWaiting, last, onLast }: {
  /** The app's flush; the screen reads the outbox again once it settles. */
  onSaved: () => Promise<void> | void;
  /** The app's count of captures waiting, after its latest flush (on open, focus, every minute). */
  outboxWaiting?: number;
  /** The last capture saved here (the app's, so it outlives this screen): sending, waiting, or sent. */
  last: LastCapture | null;
  onLast: (update: (current: LastCapture | null) => LastCapture | null) => void;
}) {
  const [text, setText] = useState("");
  const [note, setNote] = useState("");
  const [records, setRecords] = useState<OutboxRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  // "· 2 min ago" is read against the clock while the screen is on; this only re-renders.
  const [, setTick] = useState(0);
  useVisibleInterval(() => setTick((value) => value + 1), AGO_TICK_MS, last?.state === "sent");
  const photo = useRef<HTMLInputElement>(null);

  const refresh = (settled = false) =>
    listOutbox()
      .then((list) => {
        setRecords(list);
        onLast((current) => settleLastCapture(current, list, settled, Date.now()));
      })
      .catch(() => undefined);
  useEffect(() => {
    void refresh();
  }, [outboxWaiting]);

  async function save(record: Pick<OutboxRecord, "kind" | "text" | "url" | "note" | "media">) {
    setError(null);
    try {
      const id = newUlid();
      const capturedAt = new Date().toISOString();
      await addToOutbox({ clientCaptureId: id, capturedAt, ...record });
      setText("");
      setNote("");
      onLast(() => ({ id, capturedAt, state: "sending" }));
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
  // The app's flush can learn the last capture was sent a moment before this screen reads the outbox again: one
  // known sent is never also counted as waiting.
  const sentId = last?.state === "sent" ? last.id : null;
  const waiting = records.filter((record) => !record.problem && record.clientCaptureId !== sentId).length;
  return (
    <div className="screen">
      <h1>Capture</h1>
      <label htmlFor="capture-text">A thought, a problem or a link</label>
      <textarea id="capture-text" rows={5} value={text} onChange={(event) => setText(event.target.value)} />
      <label htmlFor="capture-note">Note (optional)</label>
      <input id="capture-note" value={note} onChange={(event) => setNote(event.target.value)} />
      {last ? (
        <p className="dim" role="status">
          {last.state === "sent" ? sentLine(last, Date.now()) : last.state === "waiting" ? CAPTURE_COPY.savedHere : CAPTURE_COPY.sending}
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
