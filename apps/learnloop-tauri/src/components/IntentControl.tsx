// Daily-loop DL2: the single intent control (spec_daily_loop_v1.md §5.2).
// One segmented control on a topic, a subject, a source and an item. Every
// choice shows, before it is taken, what it does, what earlier settings it
// replaces ("replaces your earlier setting on 2 topics and 1 item") and its
// projected cost ("about N min/day of reviews"), all computed by the sidecar
// with the very rule the queue uses. Optional: no setting means today's
// behaviour. Static: nothing steals focus, nothing opens a modal.
import { useEffect, useState } from "react";
import { api } from "../api/client";
import type {
  CommandError,
  IntentChoice,
  IntentChoicePreviewDto,
  IntentScopeKind,
  IntentViewDto
} from "../api/dto";
import { quietLine, quietLink } from "./PlainParts";
import { COLOR, FONT_MONO, SectionHeader } from "./term";

/** The choices that keep material coming, then the ones that stop it. */
const GROUPS: IntentChoice[][] = [
  ["master", "learn", "keep", "light_touch"],
  ["check_once", "reference", "pause", "let_go"]
];

const segment = (on: boolean, previewing: boolean) =>
  ({
    border: `1px solid ${on ? COLOR.borderFocus : previewing ? COLOR.borderStrong : COLOR.border}`,
    background: on ? COLOR.washAmber : "transparent",
    color: on ? COLOR.amberLink : COLOR.textDim,
    fontFamily: FONT_MONO,
    fontSize: 11,
    padding: "3px 8px",
    cursor: "pointer"
  }) as const;

export function previewLine(preview: IntentChoicePreviewDto): string {
  return [preview.consequence, preview.costLabel].filter(Boolean).join(" · ");
}

export function IntentControl({
  scopeKind,
  scopeId,
  heading = "What you want here",
  onChanged,
  onError
}: {
  scopeKind: IntentScopeKind;
  scopeId: string;
  heading?: string;
  /** Called after a choice or a deadline is saved (the caller may refetch). */
  onChanged?: () => void;
  onError?: (message: string) => void;
}) {
  const [view, setView] = useState<IntentViewDto | null>(null);
  const [previewing, setPreviewing] = useState<IntentChoice | null>(null);
  const [busy, setBusy] = useState(false);
  const [deadline, setDeadline] = useState("");

  useEffect(() => {
    let live = true;
    setView(null);
    setPreviewing(null);
    // A read that fails (an older sidecar, a missing scope) hides the control;
    // only a sidecar error is reported.
    Promise.resolve()
      .then(() => api.getIntent(scopeKind, scopeId))
      .then((next) => {
        if (live) setView(next);
      })
      .catch((error) => {
        if (error && typeof error === "object" && "code" in error) onError?.((error as CommandError).message);
      });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scopeKind, scopeId]);

  if (!view || !view.enabled || !view.available || !view.choices || !view.current) return null;
  const current = view.current;
  const byChoice = new Map(view.choices.map((choice) => [choice.choice, choice]));
  const shown = previewing ? byChoice.get(previewing) : current.choice !== "uncommitted" ? byChoice.get(current.choice) : null;

  const choose = async (choice: IntentChoice) => {
    if (busy) return;
    setBusy(true);
    try {
      setView(await api.setIntent(scopeKind, scopeId, choice));
      setPreviewing(null);
      onChanged?.();
    } catch (error) {
      onError?.((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  const saveDeadline = async () => {
    if (busy || !deadline) return;
    setBusy(true);
    try {
      setView(await api.setIntentDeadline(scopeKind, scopeId, deadline));
      setDeadline("");
      onChanged?.();
    } catch (error) {
      onError?.((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-testid="intent-control">
      <SectionHeader>{heading}</SectionHeader>
      <div style={{ ...quietLine, marginBottom: 6 }} data-testid="intent-current">
        {current.choice === "uncommitted"
          ? "No setting: reviewed as usual."
          : `Set to ${current.label}${current.source && current.source !== "this control" ? ` (from ${current.source})` : ""}.`}
      </div>
      <div style={{ display: "grid", gap: 4 }}>
        {GROUPS.map((group, index) => (
          <div key={index} role="radiogroup" aria-label={index === 0 ? "keep it coming" : "stop or check"}
               style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
            {group.map((choice) => {
              const preview = byChoice.get(choice);
              if (!preview) return null;
              const on = current.choice === choice;
              return (
                <button
                  key={choice}
                  type="button"
                  role="radio"
                  aria-checked={on}
                  disabled={busy}
                  title={preview.does}
                  onMouseEnter={() => setPreviewing(choice)}
                  onMouseLeave={() => setPreviewing(null)}
                  onFocus={() => setPreviewing(choice)}
                  onBlur={() => setPreviewing(null)}
                  onClick={() => void choose(choice)}
                  style={segment(on, previewing === choice)}
                >
                  {preview.label}
                </button>
              );
            })}
          </div>
        ))}
      </div>
      {shown ? (
        <div style={{ ...quietLine, marginTop: 6 }} data-testid="intent-preview" aria-live="polite">
          <div style={{ color: COLOR.text }}>{previewLine(shown)}</div>
          <div>{shown.does}</div>
        </div>
      ) : null}
      {current.deadline ? (
        <div style={{ ...quietLine, marginTop: 6 }} data-testid="intent-deadline">
          deadline {current.deadline.dueAt.slice(0, 10)} (a goal)
        </div>
      ) : null}
      {current.canAddDeadline ? (
        <div style={{ display: "flex", gap: 6, alignItems: "center", marginTop: 6 }}>
          <label style={quietLine}>
            {current.deadline ? "move the deadline" : "add a deadline"}{" "}
            <input
              type="date"
              value={deadline}
              onChange={(event) => setDeadline(event.target.value)}
              aria-label="deadline"
              style={{ fontFamily: FONT_MONO, fontSize: 11, background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}` }}
            />
          </label>
          <button type="button" style={quietLink} disabled={busy || !deadline} onClick={() => void saveDeadline()}>
            save
          </button>
        </div>
      ) : null}
    </div>
  );
}

/** The subject-wide control, opened from a topic on demand (no read until then). */
export function SubjectIntent({
  subjects,
  onChanged,
  onError
}: {
  subjects: string[];
  onChanged?: () => void;
  onError?: (message: string) => void;
}) {
  const [open, setOpen] = useState<string | null>(null);
  if (!subjects.length) return null;
  return (
    <div style={{ ...quietLine, marginTop: 6 }} data-testid="subject-intent">
      {subjects.map((subject) => (
        <button
          key={subject}
          type="button"
          style={{ ...quietLink, marginRight: 10 }}
          aria-expanded={open === subject}
          onClick={() => setOpen((current) => (current === subject ? null : subject))}
        >
          {open === subject ? `close ${subject}` : `set for all of ${subject}`}
        </button>
      ))}
      {open ? (
        <IntentControl
          scopeKind="subject"
          scopeId={open}
          heading={`All of ${open}`}
          onChanged={onChanged}
          onError={onError}
        />
      ) : null}
    </div>
  );
}
