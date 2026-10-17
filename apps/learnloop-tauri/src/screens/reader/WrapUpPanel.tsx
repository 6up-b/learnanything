// Wrap up (reader workbench RW6a; spec §9.1, D16, D34; UX §4.8): an optional
// session-ending synthesis under a minute. Three short lists from the typed
// session summary -- resolved, still open, worth reinforcing -- each line with
// one action the same chip takes elsewhere (resolve, keep open, revisit once,
// undo). Keep open writes nothing. One key (Esc) closes it. Not a modal: it
// sits in the rail, or in place where the learner landed, and takes no focus.
import { useEffect, useState, type CSSProperties } from "react";
import type { ReaderWrapUpActionDto, ReaderWrapUpDto, ReaderWrapUpInquiryLineDto, ReaderWrapUpReinforceLineDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { Quoted, RecapLink } from "./RecapCard";
import { RECAP_COPY, observationLine } from "./recapCopy";
import { MeaningLabel } from "./voices";

export interface WrapUpPanelProps {
  wrapUp: ReaderWrapUpDto;
  /** "destination": Today or the library, where only status chips can run. */
  where: "reader" | "destination";
  onAction: (line: ReaderWrapUpInquiryLineDto, action: ReaderWrapUpActionDto) => Promise<void> | void;
  onClose: () => void;
}

const ACTION_LABELS: Record<ReaderWrapUpActionDto["action"], string> = {
  undo: "undo",
  resolve: "resolve",
  revisit_once: "revisit once",
  keep_open: "keep open",
};

const headingStyle: CSSProperties = { fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, margin: "8px 0 2px", fontWeight: 400 };
const listStyle: CSSProperties = { listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 4 };
const lineStyle: CSSProperties = { fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text, lineHeight: 1.5 };

function reinforceLine(line: ReaderWrapUpReinforceLineDto): string {
  if (line.kind === "with_help") return `${line.marker} ${line.title || "a problem"} · with help · ${line.helpLine ?? ""}`.trim();
  if (line.kind === "claim") return `${line.marker} worked with help — not yet checked on your own`;
  return `${line.marker} ${observationLine(line.kind)}`;
}

export function WrapUpPanel({ wrapUp, where, onAction, onClose }: WrapUpPanelProps) {
  const [kept, setKept] = useState<Set<string>>(new Set());
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const actionsFor = (line: ReaderWrapUpInquiryLineDto) =>
    line.actions.filter((action) => !(where === "destination" && action.where === "reader"));
  // A claim from a problem already listed "with help" says nothing new.
  const withHelp = wrapUp.worthReinforcing.filter((line) => line.kind === "with_help");
  const reinforce = wrapUp.worthReinforcing.filter((line) => line.kind !== "claim" || withHelp.length === 0);
  const empty = wrapUp.resolved.length === 0 && wrapUp.stillOpen.length === 0 && reinforce.length === 0;

  const renderInquiry = (line: ReaderWrapUpInquiryLineDto, glyph: string) => (
    <li key={line.rootExchangeId} style={lineStyle}>
      <span aria-hidden="true">{glyph} </span><Quoted text={line.questionMd} />{" "}
      <span style={{ display: "inline-flex", gap: 6, flexWrap: "wrap" }}>
        {kept.has(line.rootExchangeId) ? <MeaningLabel>kept open</MeaningLabel> : actionsFor(line).map((action) => (
          <RecapLink
            key={action.action}
            onClick={() => {
              if (action.action === "keep_open") {
                setKept((current) => new Set(current).add(line.rootExchangeId));
                return;
              }
              void onAction(line, action);
            }}
          >
            {ACTION_LABELS[action.action]}
          </RecapLink>
        ))}
      </span>
    </li>
  );

  return (
    <section aria-label={RECAP_COPY.wrapUp} data-wrap-up="" style={{ border: `1px solid ${COLOR.border}`, padding: "8px 10px", marginBottom: 12 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim, letterSpacing: "0.08em", textTransform: "uppercase", flex: 1 }}>
          {RECAP_COPY.wrapUp} · under a minute
        </span>
        <RecapLink onClick={onClose} label="close wrap up">close · esc</RecapLink>
      </div>
      {empty ? <MeaningLabel>{RECAP_COPY.nothingToWrap}</MeaningLabel> : null}
      {wrapUp.resolved.length > 0 ? (
        <div>
          <h4 style={headingStyle}>{RECAP_COPY.resolved}</h4>
          <ul style={listStyle}>{wrapUp.resolved.map((line) => renderInquiry(line, "✓"))}</ul>
        </div>
      ) : null}
      {wrapUp.stillOpen.length > 0 ? (
        <div>
          <h4 style={headingStyle}>{RECAP_COPY.stillOpen}</h4>
          <ul style={listStyle}>{wrapUp.stillOpen.map((line) => renderInquiry(line, "?"))}</ul>
        </div>
      ) : null}
      {reinforce.length > 0 ? (
        <div>
          <h4 style={headingStyle}>{RECAP_COPY.worthReinforcing}</h4>
          <ul style={listStyle}>
            {reinforce.map((line, index) => (
              <li key={`${line.kind}:${line.sessionId ?? line.facetId ?? index}`} style={lineStyle}>{reinforceLine(line)}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
