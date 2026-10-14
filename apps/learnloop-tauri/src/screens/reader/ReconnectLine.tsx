// The reconnect line (reader workbench RW1a; spec §4.1; UX §4.2, W4).
//
// After a branch is marked done, or when the learner returns to the root
// passage through the detour strip or Alt+←, one quiet line asks about the
// inquiry in the learner's own words:
//   ↳ your question "why weighted by p?" — does this make sense now?
//     yes · still unclear… · quick check
// Inline under the root passage only on a return the learner started (the
// one inline line LearnLoop ever adds to the text column), and at the top of
// the inquiry in the rail. Ignoring it does nothing; it goes away after a
// screen of scrolling.
import { useState } from "react";
import { COLOR, FONT_MONO } from "../../components/term";
import { clip } from "./readerShared";
import { LearnerQuote, MeaningLabel } from "./voices";

const linkStyle = {
  border: 0,
  background: "transparent",
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 11,
  padding: 0,
  cursor: "pointer",
  textDecoration: "underline",
  textUnderlineOffset: 2,
} as const;

export interface ReconnectLineProps {
  question: string;
  placement: "inline" | "rail";
  busy?: boolean;
  onYes: () => void;
  /** Empty text opens a follow-up on the root in the Ask rail; text asks it. */
  onStillUnclear: (text: string) => void;
  /** The passage-scoped quick check, when the Reader's one check-offer rule
   *  offers it (reading-hardening, part 2); absent, the line has no button. */
  onQuickCheck?: () => void;
}

export function ReconnectLine({ question, placement, busy = false, onYes, onStillUnclear, onQuickCheck }: ReconnectLineProps) {
  const [unclearOpen, setUnclearOpen] = useState(false);
  const [text, setText] = useState("");
  return (
    <div
      role="group"
      aria-label="Does this make sense now?"
      data-reconnect={placement}
      style={{
        fontFamily: FONT_MONO,
        fontSize: 11,
        color: COLOR.textDim,
        padding: placement === "inline" ? "2px 0 6px 15px" : "6px 0",
        display: "flex",
        flexDirection: "column",
        gap: 4,
      }}
    >
      <span>
        <span aria-hidden="true">↳ </span>your question <LearnerQuote>{clip(question, 90)}</LearnerQuote> — does this make sense now?
      </span>
      <span style={{ display: "flex", gap: 8, flexWrap: "wrap", paddingLeft: placement === "inline" ? 15 : 0 }}>
        <button type="button" disabled={busy} onClick={onYes} style={linkStyle}>yes</button>
        <span aria-hidden="true">·</span>
        <button type="button" disabled={busy} onClick={() => setUnclearOpen((open) => !open)} aria-expanded={unclearOpen} style={linkStyle}>
          still unclear…
        </button>
        {onQuickCheck ? (
          <>
            <span aria-hidden="true">·</span>
            <button type="button" disabled={busy} onClick={onQuickCheck} style={linkStyle}>quick check</button>
          </>
        ) : null}
      </span>
      {unclearOpen ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 4, paddingLeft: placement === "inline" ? 15 : 0 }}>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="What's still unclear?"
            aria-label="What's still unclear?"
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                onStillUnclear(text.trim());
                setUnclearOpen(false);
                setText("");
              }
            }}
            style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 6, minHeight: 50, resize: "vertical" }}
          />
          <MeaningLabel>
            where this goes: it becomes a follow-up question to your first one; LearnLoop's model may read it to name
            what's missing. It never grades you.
          </MeaningLabel>
          <span>
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                onStillUnclear(text.trim());
                setUnclearOpen(false);
                setText("");
              }}
              style={linkStyle}
            >
              {text.trim() ? "ask this ^↵" : "ask a follow-up"}
            </button>
          </span>
        </div>
      ) : null}
    </div>
  );
}
