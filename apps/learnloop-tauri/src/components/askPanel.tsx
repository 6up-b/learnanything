// Reader CA2 (docs/specs/ux_reader_compare_ask_v1.md §7): the one Ask panel's
// shared vocabulary and its help-style control. The panel itself is
// AskOverlay in its "docked" (practice, feedback) and "inline" (the workbench,
// under a step) variants; the library and capture contexts keep the modal.
// Everything here renders only while the sidecar sends `ask` (ask.panel_enabled).
import { useState, useSyncExternalStore } from "react";
import { api } from "../api/client";
import type { AnswerMode, HelpStyle } from "../api/dto";
import { algoConfig, setAdaptiveHelpStyle, storedHelpStyle, subscribeAlgoConfig } from "../app/algoConfig";
import { errorMessage } from "../errors";
import { COLOR, FONT_MONO } from "./term";

/** §7.4: the help style IS Ask's answer mode (mirrors tutor_qa.HELP_STYLE_ANSWER_MODES). */
export const STYLE_ANSWER_MODE: Record<HelpStyle, AnswerMode> = {
  let_me_struggle: "ask_me_first",
  balanced: "help_me_reason",
  guide_me: "answer_directly"
};

/** The label an answer carries for the mode it was written in (§7.4). */
export const ANSWER_MODE_LABEL: Record<AnswerMode, string> = {
  ask_me_first: "asking you first",
  help_me_reason: "helping you reason",
  answer_directly: "answering directly"
};

/** "change" under the box: another mode for this one question. */
export const ONE_QUESTION_MODES: ReadonlyArray<{ value: AnswerMode; label: string }> = [
  { value: "ask_me_first", label: "ask me first this time" },
  { value: "help_me_reason", label: "help me reason this time" },
  { value: "answer_directly", label: "answer directly this time" }
];

const STYLE_LABELS: ReadonlyArray<{ value: HelpStyle; label: string }> = [
  { value: "let_me_struggle", label: "let me struggle" },
  { value: "balanced", label: "balanced" },
  { value: "guide_me", label: "guide me" }
];

export const ASK_COPY = {
  /** §7.1 item 4: the cost, said before sending (the existing rule, plainly). */
  cost: "a question about the maths counts as a hint · asking what the question means doesn't",
  costFeedback: "a question about the maths counts as a hint on your next try",
  /** §7.7: a check on your own. */
  coldPlaceholder:
    "ask in your words — a question about the maths makes this practice with help ◌; asking what the question means doesn't",
  placeholder: "ask in your words",
  keepOnMyOwn: "esc keep it on my own",
  empty: "(nothing asked yet on this attempt)",
  /** K11: book first, and honest when the books have nothing kept. */
  fromBooks: "§ from your books",
  explanation: "◇ LearnLoop's explanation",
  noBooks: "Your books don't cover this directly — this is LearnLoop's model's explanation",
  earlier: "earlier on this question ▸",
  earlierCost: "opening one counts as a hint",
  earlierFree: "your earlier attempts ▸",
  earlierHeader: (date: string) => `from your attempt on ${date} — not part of this one`,
  whatsSent: "ⓘ what's sent",
  convertedBanner: "Practice with help ◌ — you asked about the maths"
} as const;

/** What an answer did to the attempt, in plain words (§7.5, §7.7). */
export function answerCountLabel(
  { hintEquivalent, context, cold }: { hintEquivalent: boolean; context: string; cold: boolean }
): string {
  if (context === "feedback") return hintEquivalent ? "counts as a hint on your next try" : "a clarification · free";
  if (cold) return hintEquivalent ? "counts as help" : "a clarification · still on your own";
  return hintEquivalent ? "counts as a hint" : "a clarification · free";
}

/** The stored help style, live (one preference: Settings, the hint panel, Ask). */
export function useStoredHelpStyle(): HelpStyle {
  return useSyncExternalStore(subscribeAlgoConfig, storedHelpStyle);
}

/** §7.4: "help style: let me struggle · [balanced] · guide me", the stored
 *  preference, on every help surface. Changing it changes what both doors
 *  serve; it never blocks anything. */
export function StoredHelpStyle({ onError, compact = false }: { onError?: (message: string) => void; compact?: boolean }) {
  const style = useStoredHelpStyle();
  const [busy, setBusy] = useState(false);
  if (algoConfig().ask === null && algoConfig().adaptiveHints === null) return null;
  const choose = async (next: HelpStyle) => {
    if (next === style || busy) return;
    setBusy(true);
    try {
      const saved = await api.setHelpStyle(next);
      setAdaptiveHelpStyle(saved.helpStyle);
    } catch (error) {
      onError?.(errorMessage(error));
    } finally {
      setBusy(false);
    }
  };
  return (
    <span role="radiogroup" aria-label="help style" data-testid="ask-help-style"
      style={{ display: "inline-flex", gap: 4, alignItems: "baseline", flexWrap: "wrap", fontFamily: FONT_MONO,
        fontSize: compact ? 10 : 11, color: COLOR.textDim }}>
      <span>help style:</span>
      {STYLE_LABELS.map((option, index) => {
        const checked = style === option.value;
        return (
          <span key={option.value}>
            {index > 0 ? <span aria-hidden="true"> · </span> : null}
            <button type="button" role="radio" aria-checked={checked} aria-disabled={busy}
              onClick={() => void choose(option.value)}
              style={{ border: 0, background: "transparent", padding: 0, cursor: "pointer", fontFamily: FONT_MONO,
                fontSize: compact ? 10 : 11, color: checked ? COLOR.text : COLOR.textDim }}>
              {checked ? `[${option.label}]` : option.label}
            </button>
          </span>
        );
      })}
    </span>
  );
}

/** A short date in the learner's words: "Tue 14 Oct". */
export function shortDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
}
