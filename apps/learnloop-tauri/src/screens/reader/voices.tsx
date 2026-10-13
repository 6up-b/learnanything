// The Reader's visual grammar (reader workbench W2; UX §3.4), built once in
// RW1a for every later phase:
//
// * three voices -- the source (§, solid rule), LearnLoop's model (◇, dotted
//   purple rule) and the learner (›, solid amber rule) -- each with a glyph, a
//   rule style and a spoken prefix, so the author survives greyscale and a
//   screen reader (glyphs are aria-hidden; the prefix is visually hidden);
// * the knowledge well's evidence markers ○ ◌ ● and the check markers, never
//   a percentage and never colour alone;
// * MeaningLabel: copy that carries meaning ("model's reading", "not
//   checked", "never a grade") is --dim, never --faint (about 3.5:1 on the
//   default background, under WCAG's 4.5:1 for small text).
import type { CSSProperties, ReactNode } from "react";
import { COLOR, FONT_MONO } from "../../components/term";

export type ReaderVoice = "source" | "model" | "learner";

const VISUALLY_HIDDEN: CSSProperties = {
  position: "absolute",
  width: 1,
  height: 1,
  padding: 0,
  margin: -1,
  overflow: "hidden",
  clip: "rect(0, 0, 0, 0)",
  whiteSpace: "nowrap",
  border: 0,
};

/** Text only a screen reader hears (the voice's spoken prefix). */
export function SpokenOnly({ children }: { children: ReactNode }) {
  return <span style={VISUALLY_HIDDEN}>{children}</span>;
}

/** Copy that carries meaning. Always --dim (G55), never --faint. */
export function MeaningLabel({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <span data-meaning-label="" style={{ color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 10, ...style }}>
      {children}
    </span>
  );
}

const RULES: Record<ReaderVoice, CSSProperties> = {
  source: { borderLeft: `1px solid ${COLOR.borderStrong}` },
  model: { borderLeft: `1px dotted ${COLOR.purplePill}` },
  learner: { borderLeft: `2px solid var(--amber-mid)` },
};

const GLYPHS: Record<ReaderVoice, string> = { source: "§", model: "◇", learner: "›" };

function spokenPrefix(voice: ReaderVoice, locator?: string | null): string {
  if (voice === "source") return locator ? `From the book, ${locator}:` : "From the book:";
  if (voice === "model") return "LearnLoop's model:";
  return "You wrote:";
}

function VoiceBlock({
  voice,
  label,
  locator,
  children,
  style,
}: {
  voice: ReaderVoice;
  label: ReactNode;
  locator?: string | null;
  children: ReactNode;
  style?: CSSProperties;
}) {
  return (
    <div data-voice={voice} style={{ ...RULES[voice], paddingLeft: 8, display: "flex", flexDirection: "column", gap: 3, ...style }}>
      <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: voice === "model" ? COLOR.purpleText : COLOR.textDim }}>
        <span aria-hidden="true">{GLYPHS[voice]}</span> {label}
      </span>
      <SpokenOnly>{spokenPrefix(voice, locator)}</SpokenOnly>
      <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text, lineHeight: 1.6 }}>{children}</div>
    </div>
  );
}

/** The author, verbatim: § + source name and locator. */
export function SourceVoice({
  source,
  locator,
  children,
  style,
}: {
  source?: string | null;
  locator?: string | null;
  children: ReactNode;
  style?: CSSProperties;
}) {
  const label = [source || "from the book", locator].filter(Boolean).join(" · ");
  return <VoiceBlock voice="source" label={label} locator={locator} style={style}>{children}</VoiceBlock>;
}

/** LearnLoop's model. The first use in a panel says "LearnLoop's model". */
export function ModelVoice({
  first = false,
  note,
  children,
  style,
}: {
  first?: boolean;
  /** What kind of model text this is, said in the label ("connecting it to your question"). */
  note?: string | null;
  children: ReactNode;
  style?: CSSProperties;
}) {
  const label = `${first ? "LearnLoop's model" : "model"}${note ? ` · ${note}` : ""}`;
  return <VoiceBlock voice="model" label={label} style={style}>{children}</VoiceBlock>;
}

/** The learner's own words. */
export function LearnerVoice({ label = "you", children, style }: { label?: string; children: ReactNode; style?: CSSProperties }) {
  return <VoiceBlock voice="learner" label={label} style={style}>{children}</VoiceBlock>;
}

/** An inline quote of the learner's words inside model text (amber quote marks). */
export function LearnerQuote({ children }: { children: ReactNode }) {
  return (
    <span data-voice="learner-quote">
      <span aria-hidden="true" style={{ color: COLOR.amber }}>“</span>
      {children}
      <span aria-hidden="true" style={{ color: COLOR.amber }}>”</span>
    </span>
  );
}

// ── evidence and check markers ─────────────────────────────────────────────

export type EvidenceStatus = "untested" | "with_help" | "demonstrated";

const EVIDENCE: Record<EvidenceStatus, { glyph: string; words: string; color: string }> = {
  untested: { glyph: "○", words: "untested", color: COLOR.textDim },
  with_help: { glyph: "◌", words: "worked with help · a check on your own is pending", color: COLOR.amber },
  demonstrated: { glyph: "●", words: "demonstrated on your own", color: COLOR.green },
};

/** The knowledge well's discrete evidence markers (KnowledgeWellView): never a percentage. */
export function EvidenceMarker({ status, showWords = true }: { status: EvidenceStatus; showWords?: boolean }) {
  const marker = EVIDENCE[status];
  return (
    <span data-evidence={status} aria-label={marker.words} style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>
      <span aria-hidden="true" style={{ color: marker.color }}>{marker.glyph}</span>
      {showWords ? <span aria-hidden="true"> {marker.words}</span> : null}
    </span>
  );
}

export type CheckStatus = "checked" | "checked_not_following" | "model_reading" | "questionable" | "not_checked";

const CHECKS: Record<CheckStatus, { glyph: string; words: string }> = {
  checked: { glyph: "✓", words: "checked" },
  checked_not_following: { glyph: "≠", words: "checked: doesn't follow" },
  model_reading: { glyph: "≈", words: "model's reading" },
  questionable: { glyph: "?", words: "questionable (model's reading)" },
  not_checked: { glyph: "·", words: "not checked" },
};

/** One step's check status: "checked" only when a non-LLM check passed (W2). */
export function CheckMarker({ status }: { status: CheckStatus }) {
  const marker = CHECKS[status];
  return (
    <MeaningLabel>
      <span data-check={status} aria-label={marker.words}>
        <span aria-hidden="true">{marker.glyph} {marker.words}</span>
      </span>
    </MeaningLabel>
  );
}
