// Adaptive difficulty AD1 (spec_adaptive_difficulty_v1 §12, D5): the optional
// one-tap rating beside Submit, "Felt: easy · about right · hard".
//
// Never preselected and never required: Submit works without it, and a tap
// can be taken back (tap it again). It rides the submit itself, so it is
// always given before feedback; once Submit is pressed it is locked. One tap
// hides it for the rest of the session, remembered per viewer in browser
// storage (a convenience only: if storage is unavailable it simply shows).
// Absent while the sidecar says the tap is off (`adaptive_difficulty.rating_tap`).
// Logged only: it changes nothing the learner is served or graded on.
import { useState } from "react";
import type { DifficultyRating } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";

export const RATING_COPY: { value: DifficultyRating; label: string }[] = [
  { value: "easy", label: "easy" },
  { value: "about_right", label: "about right" },
  { value: "hard", label: "hard" }
];

const HIDDEN_KEY_PREFIX = "learnloop.ratingTapHidden:";

function hiddenFor(sessionId: string): boolean {
  try {
    return window.localStorage.getItem(HIDDEN_KEY_PREFIX + sessionId) === "1";
  } catch {
    return false;
  }
}

function rememberHidden(sessionId: string): void {
  try {
    window.localStorage.setItem(HIDDEN_KEY_PREFIX + sessionId, "1");
  } catch {
    // Storage is a convenience: the tap stays hidden for this screen anyway.
  }
}

export function DifficultyRatingTap({
  sessionId,
  value,
  onChange,
  locked
}: {
  sessionId: string;
  value: DifficultyRating | null;
  onChange: (value: DifficultyRating | null) => void;
  locked: boolean;
}) {
  const [hidden, setHidden] = useState(() => hiddenFor(sessionId));
  if (hidden) return null;
  return (
    <span
      role="group"
      aria-label="How did this one feel? (optional)"
      data-testid="difficulty-rating"
      style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 11, color: COLOR.textDim }}
    >
      <span>Felt:</span>
      {RATING_COPY.map((entry, index) => {
        const on = value === entry.value;
        return (
          <span key={entry.value} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            {index > 0 ? <span aria-hidden="true">·</span> : null}
            <button
              type="button"
              aria-pressed={on}
              disabled={locked}
              onClick={() => onChange(on ? null : entry.value)}
              style={{
                border: "none",
                background: "transparent",
                padding: 0,
                fontFamily: FONT_MONO,
                fontSize: 11,
                cursor: locked ? "default" : "pointer",
                color: on ? COLOR.amberLink : COLOR.textDim,
                textDecoration: on ? "underline" : "none"
              }}
            >
              {entry.label}
            </button>
          </span>
        );
      })}
      {locked ? null : (
        <button
          type="button"
          aria-label="hide this for the session"
          title="hide this for the session"
          onClick={() => {
            rememberHidden(sessionId);
            setHidden(true);
            onChange(null);
          }}
          style={{ border: "none", background: "transparent", padding: 0, fontSize: 11, color: COLOR.textDim,
                   cursor: "pointer", opacity: 0.6 }}
        >
          ×
        </button>
      )}
    </span>
  );
}
