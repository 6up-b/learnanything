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
import { useState, type CSSProperties } from "react";
import type { ReaderDigestNarrativeDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { ModelActionState } from "./ModelActionState";
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
} as const;

/** The well's markers are evidence's vocabulary, never model text's. */
function withoutMarkers(text: string): string {
  return text.replace(/[●◌○]/g, "").replace(/\s{2,}/g, " ").trim();
}

export function DigestNarrative({ narrative }: { narrative: ReaderDigestNarrativeDto | null | undefined }) {
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
