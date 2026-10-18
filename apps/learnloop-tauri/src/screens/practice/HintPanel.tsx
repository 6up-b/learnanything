// Adaptive hints H2b: the practice screen's hint panel (spec_adaptive_hints_v1
// §4.8; the Reader's words, UX §5.6-§5.8, §5.11). It appears only once the
// learner asked for a hint (D13: nothing else is added to the screen), keeps
// every hint in the order shown, labels each one honestly (where it came
// from, its kind in plain words, how far ahead a goal is, worked help ◌), and
// carries a hint's own quiet lines, the feedback box, the worked-help picks
// (their consequence stated before they are taken), a discriminating
// question's own answer box and the "⋯" help-style menu. Static: nothing
// steals focus, animates or opens a modal.
import { useState, type KeyboardEvent } from "react";
import type { HelpStyle, HintShortcut } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { quietLine, quietLink } from "../../components/PlainParts";
import { MarkdownMath } from "../../render/MarkdownMath";
import { HELP_STYLE_COPY, HINT_COPY, SHORTCUT_COPY } from "./hintCopy";
import type { AdaptiveHints, HintEntry } from "./useAdaptiveHints";

const chip = (on: boolean) => ({
  border: `1px solid ${on ? COLOR.borderFocus : COLOR.border}`,
  background: on ? COLOR.washAmber : "transparent",
  color: on ? COLOR.amberLink : COLOR.textDim,
  fontFamily: FONT_MONO,
  fontSize: 11,
  padding: "3px 8px",
  cursor: "pointer",
  textAlign: "left" as const
});

/** The label line of a hint: origin, kind in plain words, horizon, worked help. */
export function hintLabelLine(entry: HintEntry): string {
  const labels = entry.result.labels ?? {};
  const parts: string[] = [];
  if (labels.origin) parts.push(labels.origin);
  if (labels.kind && labels.kind !== labels.origin) parts.push(labels.kind);
  if (labels.horizon) parts.push(labels.horizon);
  if (entry.result.kind === "discriminating") parts.push(HINT_COPY.notGraded);
  if (labels.workedHelp) parts.push(labels.workedHelp);
  return parts.join(" · ");
}

function draftLines(answer: string): string[] {
  return answer.split("\n").map((line) => line.trim()).filter(Boolean);
}

function FeedbackBox({
  answer,
  disabled,
  onSend
}: {
  answer: string;
  disabled: boolean;
  onSend: (reply: { shortcut?: HintShortcut; text?: string; selection?: string }) => void;
}) {
  const [shortcut, setShortcut] = useState<HintShortcut | null>(null);
  const [text, setText] = useState("");
  const [picked, setPicked] = useState<number[]>([]);
  const lines = draftLines(answer);
  const send = () => {
    const selection = shortcut === "not_where_stuck" ? picked.sort((a, b) => a - b).map((i) => lines[i]).join("\n") : "";
    // An empty reply is allowed: it still asks for the next hint at once.
    onSend({ shortcut: shortcut ?? undefined, text, selection });
  };
  const onKey = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      if (!disabled) send();
    }
  };
  return (
    <div data-testid="hint-feedback" style={{ display: "grid", gap: 6, marginTop: 6 }}>
      <div role="group" aria-label="what didn't connect" style={{ display: "grid", gap: 4 }}>
        {SHORTCUT_COPY.map((entry) => (
          <button
            key={entry.value}
            type="button"
            aria-pressed={shortcut === entry.value}
            onClick={() => setShortcut((current) => (current === entry.value ? null : entry.value))}
            style={chip(shortcut === entry.value)}
          >
            {entry.label} <span style={{ color: COLOR.textDim }}>— {entry.does}</span>
          </button>
        ))}
      </div>
      {shortcut === "not_where_stuck" && lines.length > 0 ? (
        <div data-testid="hint-feedback-lines" style={{ display: "grid", gap: 3 }}>
          <span style={quietLine}>{HINT_COPY.pickLines}</span>
          {lines.map((line, index) => (
            <button
              key={`${index}:${line}`}
              type="button"
              aria-pressed={picked.includes(index)}
              onClick={() => setPicked((current) => current.includes(index)
                ? current.filter((value) => value !== index)
                : [...current, index])}
              style={chip(picked.includes(index))}
            >
              {line}
            </button>
          ))}
        </div>
      ) : null}
      <input
        type="text"
        className="text-input"
        aria-label={HINT_COPY.sayMore}
        placeholder={HINT_COPY.sayMore}
        value={text}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={onKey}
        style={{ width: "100%", fontSize: 12 }}
      />
      <div>
        <button type="button" style={quietLink} disabled={disabled} onClick={send}>{HINT_COPY.nextHint}</button>
      </div>
    </div>
  );
}

function DiscriminatingBox({
  entry,
  disabled,
  onAnswer,
  onSkip
}: {
  entry: HintEntry;
  disabled: boolean;
  onAnswer: (text: string) => void;
  onSkip: () => void;
}) {
  const [text, setText] = useState("");
  if (entry.answered) {
    return <div style={{ ...quietLine, marginTop: 4 }} data-testid="hint-discriminating-settled">{entry.answered.message}</div>;
  }
  return (
    <div style={{ display: "grid", gap: 4, marginTop: 6 }}>
      <input
        type="text"
        className="text-input"
        aria-label={HINT_COPY.answerBox}
        value={text}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            if (text.trim()) onAnswer(text);
          }
        }}
        style={{ width: "100%", fontSize: 12 }}
      />
      <div style={quietLine}>
        <button type="button" style={quietLink} disabled={!text.trim()} onClick={() => onAnswer(text)}>{HINT_COPY.answer}</button>
        {" · "}
        <button type="button" style={quietLink} disabled={disabled} onClick={onSkip}>{HINT_COPY.skip}</button>
      </div>
    </div>
  );
}

function HintCard({ entry, hints, answer }: { entry: HintEntry; hints: AdaptiveHints; answer: string }) {
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const replies = entry.result.replies ?? [];
  const asking = entry.result.kind === "discriminating" && Boolean(entry.result.discriminating?.answerBox);
  return (
    <div className="hint-banner" data-testid="hint-entry" style={{ display: "grid", gap: 4 }}>
      <div style={{ ...quietLine, fontFamily: FONT_MONO, fontSize: 11 }} data-testid="hint-labels">{hintLabelLine(entry)}</div>
      <div><MarkdownMath value={entry.result.hintMd ?? ""} /></div>
      {entry.result.message ? <div style={quietLine}>{entry.result.message}</div> : null}
      {asking ? (
        <DiscriminatingBox
          entry={entry}
          disabled={hints.pending}
          onAnswer={(text) => void hints.answerDiscriminating(entry, text)}
          onSkip={() => void hints.press()}
        />
      ) : null}
      {entry.result.assistId && replies.length ? (
        <div style={quietLine} data-testid="hint-replies">
          {replies.includes("smaller_step") ? (
            <>
              <button type="button" style={quietLink} disabled={hints.pending} onClick={() => hints.smallerStep(entry)}>
                {HINT_COPY.smallerStep}
              </button>
              {" · "}
            </>
          ) : null}
          {replies.includes("doesnt_connect") ? (
            <button
              type="button"
              style={quietLink}
              aria-expanded={feedbackOpen}
              title={HINT_COPY.doesntConnectTitle}
              onClick={() => setFeedbackOpen((open) => !open)}
            >
              {HINT_COPY.doesntConnect}
            </button>
          ) : null}
          {replies.includes("book_way") ? (
            <>
              {" · "}
              <button type="button" style={quietLink} disabled={hints.pending} onClick={() => hints.bookWay(entry)}>
                {HINT_COPY.bookWay}
              </button>
            </>
          ) : null}
        </div>
      ) : null}
      {feedbackOpen ? (
        <FeedbackBox
          answer={answer}
          disabled={hints.pending}
          onSend={(reply) => {
            setFeedbackOpen(false);
            hints.reply(entry, reply);
          }}
        />
      ) : null}
    </div>
  );
}

export function HintPanel({
  hints,
  answer,
  helpStyle
}: {
  hints: AdaptiveHints;
  answer: string;
  helpStyle: HelpStyle;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  if (!hints.entries.length && !hints.pending && !hints.notice) return null;
  return (
    <div data-testid="hint-panel" aria-label={HINT_COPY.panelLabel} style={{ display: "grid", gap: 6, marginTop: 8 }}>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button
          type="button"
          style={quietLink}
          aria-label={HINT_COPY.menuLabel}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
        >
          {HINT_COPY.menu}
        </button>
      </div>
      {menuOpen ? (
        <div data-testid="hint-style-menu" role="group" aria-label={HINT_COPY.menuLabel} style={{ display: "grid", gap: 4 }}>
          {HELP_STYLE_COPY.map((style) => (
            <button
              key={style.value}
              type="button"
              aria-pressed={helpStyle === style.value}
              onClick={() => {
                setMenuOpen(false);
                if (style.value !== helpStyle) void hints.saveHelpStyle(style.value);
              }}
              style={chip(helpStyle === style.value)}
            >
              {style.label} <span style={{ color: COLOR.textDim }}>— {style.line}</span>
            </button>
          ))}
          <span style={quietLine}>{HINT_COPY.menuNote}</span>
        </div>
      ) : null}
      {hints.entries.map((entry) => <HintCard key={entry.key} entry={entry} hints={hints} answer={answer} />)}
      {hints.pending ? (
        <div role="status" style={quietLine} data-testid="hint-writing">
          {HINT_COPY.writing}
          {hints.offer ? (
            <>
              {" · "}
              <button type="button" style={quietLink} disabled={hints.offerBusy}
                onClick={() => void hints.takeAuthoredInstead()}>
                {HINT_COPY.authoredInstead}
              </button>
            </>
          ) : null}
        </div>
      ) : null}
      {hints.notice ? <div role="status" style={quietLine} data-testid="hint-notice">{hints.notice.message}</div> : null}
      {hints.picks.length ? (
        <div style={{ ...quietLine, display: "grid", gap: 2 }} data-testid="hint-picks">
          {hints.picks.map((pick) => (
            <div key={pick.level}>
              <button
                type="button"
                style={quietLink}
                disabled={hints.pending}
                onClick={() => void hints.takeWorked(pick.level === 5 ? 5 : 4)}
              >
                {pick.label} · {pick.workedHelp}
              </button>{" "}
              <span>— {pick.consequence}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
