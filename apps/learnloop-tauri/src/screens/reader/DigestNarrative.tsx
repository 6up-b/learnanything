// The session narrative (reader workbench RW6b part 2; spec §9.2; UX §4.8,
// W14): at most 120 words LearnLoop's model wrote once from what the learner
// did (the session's typed summary, never their words). Always collapsed at
// first -- "▸ summary written by LearnLoop's model from what you did" -- and
// never the first thing shown; it sits at the foot of "Last time here" and of
// Wrap up. In LearnLoop's model's voice, never a source of a filled mark (no
// ● or ◌ here). Its waiting and failure states are W14's, in place: pending,
// failed (no retry: one narrative per session), unreachable and capped (it is
// retried at the next Today build; the lists above are complete without it).
// Switched off it is absent: the sidecar sends nothing and nothing renders.
// While it is pending the surface showing it re-reads it; a re-read that
// fails (fix round 4) shows W14's offline state when the sidecar is down, or
// says the summary could not be checked, with "try again", until a read
// succeeds (the surface's other content stays as it was).
import { useState, type CSSProperties } from "react";
import type { ReaderDigestNarrativeDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { ModelActionState, type ModelActionPhase } from "./ModelActionState";
import { MeaningLabel, ModelVoice } from "./voices";

// The recap's link style (RecapCard imports this component, so it is not imported back).
const linkStyle: CSSProperties = {
  border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11, padding: 0,
  cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2,
};

export const NARRATIVE_COPY = {
  collapsed: "▸ summary written by LearnLoop's model from what you did",
  expanded: "▾ summary written by LearnLoop's model from what you did",
  writing: "writing a summary of this session",
  failed: "LearnLoop's model couldn't write a summary of this session that matched what you did.",
  kept: "The lists above are complete without it.",
  capRoute: "summary",
  fallback: "Everything above",
  pollFailed: "Couldn't check on the summary.",
} as const;

/** How the last re-read of a pending narrative failed (client-side only). */
export type NarrativePollFailure = Extract<ModelActionPhase, "offline" | "failed">;

/** The narrative as a surface shows it: the sidecar's DTO, plus, while it is
 *  pending and the last re-read failed, how it failed and a way to re-read now. */
export type NarrativeView = ReaderDigestNarrativeDto & {
  pollFailure?: NarrativePollFailure;
  onRetry?: () => void;
};

/** The well's markers are evidence's vocabulary, never model text's. */
function withoutMarkers(text: string): string {
  return text.replace(/[●◌○]/g, "").replace(/\s{2,}/g, " ").trim();
}

export function DigestNarrative({ narrative }: { narrative: NarrativeView | null | undefined }) {
  const [open, setOpen] = useState(false);
  if (!narrative) return null;
  if (narrative.state === "landed") {
    const text = withoutMarkers(narrative.text ?? "");
    if (!text) return null;
    return (
      <div data-digest-narrative="landed" style={{ marginTop: 8 }}>
        <button type="button" style={linkStyle} aria-expanded={open} onClick={() => setOpen((current) => !current)}>
          {open ? NARRATIVE_COPY.expanded : NARRATIVE_COPY.collapsed}
        </button>
        {open ? (
          <ModelVoice first note="a summary of what you did, not a grade" style={{ marginTop: 4 }}>
            <span data-narrative-text="">{text}</span>
          </ModelVoice>
        ) : null}
      </div>
    );
  }
  const capAmount = typeof narrative.capUsd === "number" ? `$${narrative.capUsd.toFixed(2)}` : undefined;
  if (narrative.state === "pending" && narrative.pollFailure) {
    return (
      <div data-digest-narrative={narrative.pollFailure} style={{ marginTop: 8 }}>
        <ModelActionState phase={narrative.pollFailure} verb={NARRATIVE_COPY.writing} failure={NARRATIVE_COPY.pollFailed}
          kept={NARRATIVE_COPY.kept} onRetry={narrative.onRetry} />
      </div>
    );
  }
  return (
    <div data-digest-narrative={narrative.state} style={{ marginTop: 8 }}>
      {narrative.state === "pending" ? (
        <ModelActionState phase="pending" verb={NARRATIVE_COPY.writing} />
      ) : narrative.state === "capped" ? (
        <ModelActionState phase="capped" verb={NARRATIVE_COPY.writing} capRoute={NARRATIVE_COPY.capRoute}
          capAmount={capAmount} fallback={NARRATIVE_COPY.fallback} />
      ) : narrative.state === "unreachable" ? (
        <ModelActionState phase="unreachable" verb={NARRATIVE_COPY.writing} kept={NARRATIVE_COPY.kept} />
      ) : narrative.state === "failed" ? (
        <ModelActionState phase="failed" verb={NARRATIVE_COPY.writing} failure={narrative.message ?? NARRATIVE_COPY.failed}
          kept={NARRATIVE_COPY.kept} />
      ) : (
        <MeaningLabel>{NARRATIVE_COPY.kept}</MeaningLabel>
      )}
    </div>
  );
}
