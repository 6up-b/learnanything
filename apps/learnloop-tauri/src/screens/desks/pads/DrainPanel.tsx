// The desk drain (spec §10.12; alt+shift+q): "Closing “<desk>”" with today's pads, each with what it holds
// (its first and last lines) before anything is asked. One key each: Nk keep, Nl leave, Nc carry “<last line>”
// when the last line is a question. Skipping costs nothing; leave keeps a pad in the desk's history.
import { useEffect, useRef, useState } from "react";
import type { PadDrainDto } from "../../../api/dto";
import { screenLeavesKey } from "../../../app/keymap";
import { padName } from "./model";

/** Each settles once the server has it, and rejects (with why) when it does not. */
export interface DrainActions {
  keep: (padId: string, version: number) => Promise<void>;
  leave: (padId: string, version: number) => Promise<void>;
  carry: (text: string, padId: string) => Promise<void>;
}

export function DrainPanel({ deskTitle, load, actions, onClose, wrapUpHost }: {
  deskTitle: string;
  load: () => Promise<PadDrainDto>;
  actions: DrainActions;
  onClose: () => void;
  /** Where the desk's readings put their Wrap up, after the pads (the drain gives before it asks). */
  wrapUpHost?: (node: HTMLDivElement | null) => void;
}) {
  const [drain, setDrain] = useState<PadDrainDto | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [done, setDone] = useState<Record<string, string>>({});
  // A choice on its way (said as such, its row's keys waiting) and the last one that failed (its controls kept).
  const [pendingPad, setPendingPad] = useState<Record<string, string>>({});
  const [failed, setFailed] = useState<Record<string, string>>({});
  // The pad a number key named, waiting for its k, l or c.
  const pending = useRef<number | null>(null);
  useEffect(() => {
    let live = true;
    load().then((found) => live && setDrain(found), (error: unknown) => live && setFailure(error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error)));
    return () => {
      live = false;
    };
  }, [load]);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      // A modal panel: it owns the keyboard while it is open. Its keys are bare letters and digits: a chord
      // (alt+l moving the focus) is not "l, leave".
      if (screenLeavesKey(event, { modal: true }) || event.altKey || event.ctrlKey || event.metaKey) return;
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      const match = /^([1-9])$/.exec(event.key);
      if (match) {
        pending.current = Number(match[1]) - 1;
        event.preventDefault();
        return;
      }
      const index = pending.current;
      const pad = index !== null ? drain?.pads[index] : drain?.pads.length === 1 ? drain.pads[0] : undefined;
      if (!pad) return;
      if (event.key === "k") act(pad.padId, "kept", () => actions.keep(pad.padId, pad.version));
      else if (event.key === "l") act(pad.padId, "left in the library", () => actions.leave(pad.padId, pad.version));
      else if (event.key === "c" && pad.carryCandidate) act(pad.padId, "saved for later", () => actions.carry(pad.carryCandidate as string, pad.padId));
      else return;
      pending.current = null;
      event.preventDefault();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });
  // Done is said only once the save is acknowledged; a failure says why and keeps the row's controls.
  const act = (padId: string, said: string, run: () => Promise<void>) => {
    if (done[padId] || pendingPad[padId]) return;
    setPendingPad((now) => ({ ...now, [padId]: said }));
    setFailed((now) => {
      const next = { ...now };
      delete next[padId];
      return next;
    });
    void run().then(
      () => setDone((now) => ({ ...now, [padId]: said })),
      (error: unknown) => setFailed((now) => ({ ...now, [padId]: error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error) })),
    ).finally(() => setPendingPad((now) => {
      const next = { ...now };
      delete next[padId];
      return next;
    }));
  };
  return (
    <div className="desk-drain" role="dialog" aria-label={`closing ${deskTitle}`}>
      <div className="head">Closing “{deskTitle}”</div>
      <div className="sub">One key each · skipping costs nothing · leave keeps a pad in the desk’s history.</div>
      {failure ? <div className="note">Couldn’t load today’s pads. Close this panel and reopen it to try again.</div> : null}
      {drain && drain.pads.length === 0 ? <div className="note">nothing written on this desk today</div> : null}
      {drain?.pads.map((pad, index) => (
        <div key={pad.padId} className="pad" data-drain-pad={pad.padId}>
          <div className="title" title={pad.kept ? "Pinned" : undefined}>{pad.kept ? "⚲ " : ""}{padName(pad)}</div>
          <div className="lines"><span>{pad.firstLine}</span>{pad.lastLine && pad.lastLine !== pad.firstLine ? <span> … {pad.lastLine}</span> : null}</div>
          {failed[pad.padId] ? <div className="note err">{failed[pad.padId]} Check the pad before trying again.</div> : null}
          {done[pad.padId] ? <div className="done">{done[pad.padId]}</div> : pendingPad[pad.padId] ? <div className="note">◐ Saving your choice…</div> : (
            <div className="acts">
              <button type="button" onClick={() => act(pad.padId, "kept", () => actions.keep(pad.padId, pad.version))}><kbd title={`Press ${index + 1}, then K`}>{index + 1}k</kbd> keep</button>
              <button type="button" onClick={() => act(pad.padId, "left in the library", () => actions.leave(pad.padId, pad.version))}><kbd title={`Press ${index + 1}, then L`}>{index + 1}l</kbd> leave</button>
              {pad.carryCandidate ? <button type="button" onClick={() => act(pad.padId, "saved for later", () => actions.carry(pad.carryCandidate as string, pad.padId))}><kbd title={`Press ${index + 1}, then C`}>{index + 1}c</kbd> save for later “{pad.carryCandidate.slice(0, 60)}”</button> : null}
            </div>
          )}
        </div>
      ))}
      {wrapUpHost ? <div className="wrapups" data-drain-wrap-ups="" ref={wrapUpHost} /> : null}
      <div className="acts"><button type="button" onClick={onClose}>esc · done</button></div>
    </div>
  );
}
