// Instruct hand-off IH3 (spec_instruct_handoff_v1 §6): "Something else would help".
//
// One quiet link where the router's next action is about to be served (feedback, a plan boundary on Today, the lesson
// offer page). It opens a short section in place, never a modal: what the plan could do right now in plain words
// (another question, review something earlier, something new, read the source, learn this, stop), the router's own
// candidates and not a fixed list, and an optional note. Choosing one serves it and keeps the choice, with the options
// then, as the learner's own statement. A preference is what the learner would take, never evidence they know it.
import { useRef, useState } from "react";
import { api } from "../../api/client";
import type { SomethingElseChosenDto, SomethingElseOptionDto, SomethingElseOptionsDto } from "../../api/dto";
import { useDailyPlan } from "../../app/dailyPlan";
import { getCommandError } from "../../errors";
import { COLOR, FONT_MONO } from "../../components/term";
import type { LessonEntry } from "../LessonScreen";

export type SomethingElseSurface = "feedback" | "offer_page" | "today";

/** The one place the link's wording lives, so a test pins it. */
export const SOMETHING_ELSE_LINK = "Something else would help";

/** Whether the quiet link may show: the sidecar says so on the plan (absent with the switch off or below the tag). */
export function useSomethingElseOn(sessionId: string | null, enabled?: boolean): boolean {
  const plan = useDailyPlan(sessionId, enabled === undefined && Boolean(sessionId));
  return enabled ?? Boolean(plan.data?.somethingElse);
}

/** The lesson a chosen "learn this" opens (a learner-started lesson on the topic: nothing is pre-answered for them). */
export function lessonEntryFor(result: SomethingElseChosenDto): LessonEntry | null {
  const lesson = result.preference?.outcome === "lesson" ? result.preference.lesson : null;
  return lesson
    ? { kind: "open", entry: "learning_object", learningObjectIds: lesson.learningObjectIds, title: lesson.title }
    : null;
}

function newKey(): string {
  const c = (globalThis as { crypto?: { randomUUID?: () => string } }).crypto;
  return c?.randomUUID ? c.randomUUID() : `pref_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

const linkStyle = {
  background: "none", border: "none", padding: 0, cursor: "pointer", color: COLOR.textDim,
  fontFamily: FONT_MONO, fontSize: 12, textDecoration: "underline"
} as const;

export function SomethingElse({
  sessionId,
  surface,
  attemptId = null,
  enabled,
  canStartLesson = true,
  hidePlansPick = false,
  onChosen,
  onError
}: {
  sessionId: string | null;
  surface: SomethingElseSurface;
  /** The answer whose feedback the learner is on (feedback only). */
  attemptId?: string | null;
  /** Known to the caller (a plan it already read); otherwise read from today's plan. */
  enabled?: boolean;
  /** False where lessons can't open (the desktop's lessons off): "learn this" is then not offered. */
  canStartLesson?: boolean;
  /** The offer page is the plan's own pick already: that option is left off it. */
  hidePlansPick?: boolean;
  /** The choice was served and kept: the host moves on (opens the step or the lesson, or serves Next on agreement). */
  onChosen: (result: SomethingElseChosenDto) => void;
  onError: (message: string) => void;
}) {
  const on = useSomethingElseOn(sessionId, enabled);
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState<SomethingElseOptionsDto | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  // The act's own key, kept across a failed send so a retry writes once; a new panel is a new act.
  const key = useRef<string | null>(null);
  if (!on || !sessionId) return null;

  async function show() {
    setOpen(true);
    key.current = null;
    setLoading(true);
    try {
      setOptions(await api.planSomethingElseOptions(sessionId));
    } catch (error) {
      setOptions(null);
      onError(getCommandError(error)?.message ?? String(error));
    } finally {
      setLoading(false);
    }
  }

  async function choose(option: SomethingElseOptionDto) {
    if (busy) return;
    setBusy(true);
    key.current = key.current ?? newKey();
    try {
      const result = await api.planSomethingElse({
        kind: option.kind, ref: option.ref, surface, attemptId, sessionId,
        noteMd: note.trim() ? note.trim() : null, preferenceId: key.current
      });
      key.current = null;
      setOpen(false);
      setNote("");
      onChosen(result);
    } catch (error) {
      onError(getCommandError(error)?.message ?? String(error));
    } finally {
      setBusy(false);
    }
  }

  const shown = (options?.options ?? []).filter(
    (option) => (canStartLesson || option.kind !== "lesson") && !(hidePlansPick && option.plansPick)
  );
  return (
    <div data-testid="something-else" style={{ fontFamily: FONT_MONO, color: COLOR.text }}>
      {!open ? (
        <button type="button" data-testid="something-else-link" style={linkStyle} onClick={() => void show()}>
          {SOMETHING_ELSE_LINK}
        </button>
      ) : (
        <section aria-label="What would help" data-testid="something-else-panel"
                 style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 13, maxWidth: 560 }}>
          <div>What would help right now?</div>
          {loading ? <div style={{ color: COLOR.textDim }}>Looking at what the plan could do…</div> : null}
          {!loading && shown.length === 0 ? (
            <div data-testid="something-else-none" style={{ color: COLOR.textDim }}>
              Nothing else is available right now.
            </div>
          ) : null}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {shown.map((option) => (
              <button key={option.kind} type="button" data-testid={`something-else-option-${option.kind}`}
                      disabled={busy} onClick={() => void choose(option)}>
                {option.label}
                {option.minutes ? ` (about ${Math.max(1, Math.round(option.minutes))} min)` : ""}
              </button>
            ))}
          </div>
          <label style={{ display: "flex", flexDirection: "column", gap: 4, color: COLOR.textDim, fontSize: 12 }}>
            Anything you'd like us to know? (optional)
            <textarea data-testid="something-else-note" rows={2} value={note} maxLength={4000}
                      onChange={(event) => setNote(event.target.value)}
                      style={{ fontFamily: FONT_MONO, fontSize: 12 }} />
          </label>
          <div style={{ fontSize: 11, color: COLOR.textDim }}>
            This is only what you'd like to do next. It isn't counted as knowing something.
          </div>
          <div>
            <button type="button" style={linkStyle} disabled={busy} onClick={() => setOpen(false)}>Never mind</button>
          </div>
        </section>
      )}
    </div>
  );
}
