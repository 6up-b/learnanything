// Instruct hand-off IH3 (spec_instruct_handoff_v1 §6): "Something else would help", on the phone.
//
// One quiet link; it opens in place, never a modal: what the plan could do now in plain words and an optional note.
// What the phone can serve is served (another question, a review, something new, stop). A lesson or a reading it can't
// serve is still kept as the learner's own pick, and the phone says so plainly: it waits on the desktop. The note and
// the choice are what the learner would take, never counted as knowing something.
import { useRef, useState } from "react";
import type { SomethingElseOptionDto } from "@desktop/api/dto";
import { TAG } from "@desktop/api/queryTags";
import { useCachedQuery } from "@desktop/api/useCachedQuery";
import { phone, type PhonePlanDto, type PhoneSomethingElseDto } from "../api/phone";
import { newUlid } from "../util/ulid";

export const SOMETHING_ELSE_LINK = "Something else would help";

/** What the phone says when a choice was kept but only the desktop serves it. */
export function waitsOnDesktop(kind: string, label: string): string {
  if (kind === "lesson") return `${label} is a lesson, and lessons wait on the desktop. Your choice is saved.`;
  if (kind === "read") return `${label} waits on the desktop. Your choice is saved.`;
  return `${label} waits on the desktop. Your choice is saved.`;
}

export function SomethingElse({
  sessionId,
  surface,
  attemptId = null,
  onServed,
  onAgreed,
  onError
}: {
  sessionId: string | null;
  surface: "phone_feedback" | "phone_today";
  attemptId?: string | null;
  /** The choice was served: the plan's reply (an item opens, or Today shows it). */
  onServed: (reply: PhoneSomethingElseDto) => void;
  /** The plan had already drawn this kind: nothing new was served, so the phone goes on as Next does. */
  onAgreed: () => void;
  onError: (error: unknown) => void;
}) {
  // The plan read says whether the link may show (absent with the switch off or below the tag).
  const plan = useCachedQuery<PhonePlanDto>(sessionId ? ["get_daily_plan", sessionId] : null, () => phone.getDailyPlan(sessionId), {
    tags: [TAG.queue]
  });
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState<SomethingElseOptionDto[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  const [saved, setSaved] = useState<string | null>(null);
  const key = useRef<string | null>(null);
  if (!sessionId || !plan.data?.somethingElse) return null;

  async function show() {
    setOpen(true);
    setSaved(null);
    key.current = null;
    setOptions(null);
    try {
      const reply = await phone.planSomethingElseOptions(sessionId);
      setOptions(reply.options ?? []);
    } catch (error) {
      setOpen(false);
      onError(error);
    }
  }

  async function choose(option: SomethingElseOptionDto) {
    if (busy) return;
    setBusy(true);
    key.current = key.current ?? newUlid();
    try {
      const reply = await phone.planSomethingElse({
        sessionId, kind: option.kind, ref: option.ref, surface, attemptId,
        noteMd: note.trim() ? note.trim() : null, preferenceId: key.current
      });
      key.current = null;
      setOpen(false);
      setNote("");
      const outcome = reply.preference?.outcome;
      if (outcome === "waits_on_desktop") setSaved(waitsOnDesktop(option.kind, option.label));
      else if (outcome === "agreed") onAgreed();
      else onServed(reply);
    } catch (error) {
      onError(error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div data-testid="something-else">
      {saved ? <p className="dim" role="status" data-testid="something-else-saved">{saved}</p> : null}
      {!open ? (
        <div className="row">
          <button className="plain" type="button" data-testid="something-else-link" onClick={() => void show()}>
            {SOMETHING_ELSE_LINK}
          </button>
        </div>
      ) : (
        <section aria-label="What would help" data-testid="something-else-panel">
          <p>What would help right now?</p>
          {options === null ? <p className="dim" role="status">Looking at what the plan could do…</p> : null}
          {options !== null && options.length === 0 ? (
            <p className="dim" data-testid="something-else-none">Nothing else is available right now.</p>
          ) : null}
          <div className="chips">
            {(options ?? []).map((option) => (
              <button key={option.kind} className="plain" type="button" data-testid={`something-else-option-${option.kind}`}
                      disabled={busy} onClick={() => void choose(option)}>
                {option.label}
                {option.servable ? "" : " (on the desktop)"}
              </button>
            ))}
          </div>
          <label htmlFor="something-else-note">Anything you'd like us to know? (optional)</label>
          <textarea id="something-else-note" rows={2} value={note} maxLength={4000} onChange={(event) => setNote(event.target.value)} />
          <p className="dim">This is only what you'd like to do next. It isn't counted as knowing something.</p>
          <div className="row">
            <button className="plain" type="button" disabled={busy} onClick={() => setOpen(false)}>Never mind</button>
          </div>
        </section>
      )}
    </div>
  );
}
