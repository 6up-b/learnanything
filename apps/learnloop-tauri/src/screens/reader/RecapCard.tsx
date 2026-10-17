// "Last time here" (reader workbench RW6a; spec §9.1; UX §4.8, W1, W12, S10):
// the compact card at the head of the Guide when a source is opened again.
// Continue at, Still open, Unfinished, Worth a second look, Since last time.
// Threads to pick up, never debt: headings carry no counts, nothing is
// "overdue", evidence uses the well's markers (◌ ●), never a percentage.
// Nothing here takes focus, animates or opens a modal; every line acts
// through a chip the Reader already has.
import { useState, type CSSProperties, type ReactNode } from "react";
import type { ReaderRecapCardDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { RECAP_COPY, aboutMinutes, fullDay, observationLine, shortDay, stepsLabel } from "./recapCopy";
import { MeaningLabel } from "./voices";

export { shortDay } from "./recapCopy";

export interface RecapCardProps {
  recap: ReaderRecapCardDto;
  collapsed: boolean;
  /** For "(Mon)" against today (tests pin it). */
  now?: Date;
  onExpand: () => void;
  onContinue: () => void;
  onDismiss: () => void;
  /** An inquiry's passage, with a way back (its crumb). */
  onOpenInquiry: (rootExchangeId: string, spanId: string) => void;
  onSetStatus: (rootExchangeId: string, resolution: "resolved") => void;
  /** "revisit once": the RW1a test_me_later chip (absent where it can't run). */
  onRevisit?: (rootExchangeId: string) => void;
  /** The inquiry already has its revisit (the Ask chip's state, shared). */
  revisited?: (rootExchangeId: string) => boolean;
  onResume: (sessionId: string) => void;
}

export const recapLinkStyle: CSSProperties = {
  border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11, padding: 0,
  cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2,
};

const headingStyle: CSSProperties = {
  fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, margin: "8px 0 2px", fontWeight: 400,
};
const listStyle: CSSProperties = { listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 4 };
const lineStyle: CSSProperties = { fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text, lineHeight: 1.5 };

export function RecapLink({ children, onClick, label }: { children: ReactNode; onClick: () => void; label?: string }) {
  return (
    <button type="button" onClick={onClick} aria-label={label} style={recapLinkStyle}>
      {children}
    </button>
  );
}

/** The learner's own words, in their voice (UX §3.4: amber quote marks). */
export function Quoted({ text }: { text: string }) {
  return (
    <span data-voice="learner">
      <span style={{ color: COLOR.amber }}>“</span>{text}<span style={{ color: COLOR.amber }}>”</span>
    </span>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <h4 style={headingStyle}>{title}</h4>
      <ul style={listStyle}>{children}</ul>
    </div>
  );
}

export function RecapCard({
  recap, collapsed, now, onExpand, onContinue, onDismiss, onOpenInquiry, onSetStatus, onRevisit, revisited, onResume,
}: RecapCardProps) {
  const [kept, setKept] = useState<Set<string>>(new Set());
  const continueLabel = recap.continueAt?.label ? `continue at ${recap.continueAt.label}` : "continue where you left off";
  if (collapsed) {
    return (
      <div style={{ ...lineStyle, color: COLOR.textDim, marginBottom: 10 }}>
        <RecapLink onClick={onExpand}>{RECAP_COPY.lastTime}</RecapLink>
        <span> · {continueLabel}</span>
      </div>
    );
  }
  const minutes = aboutMinutes(recap.session.minutes);
  const { stillOpen, unfinished, worthASecondLook: secondLook, sinceLastTime } = recap;
  const gains = sinceLastTime.demonstrated.length > 0 || sinceLastTime.checksRetired.length > 0;
  return (
    <section
      aria-label={RECAP_COPY.title}
      data-recap-card=""
      style={{ border: `1px solid ${COLOR.border}`, padding: "8px 10px", marginBottom: 12, display: "flex", flexDirection: "column", gap: 2 }}
    >
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim, letterSpacing: "0.08em", textTransform: "uppercase", flex: 1 }}>
          {RECAP_COPY.title} · {fullDay(recap.session.startedAt)}{minutes ? ` · ${minutes}` : ""}
        </span>
        <RecapLink onClick={onDismiss}>dismiss</RecapLink>
      </div>
      <div style={lineStyle}>
        ↳ {continueLabel}{" "}
        <RecapLink onClick={onContinue}>continue</RecapLink>
      </div>
      {stillOpen.length > 0 ? (
        <Section title={RECAP_COPY.stillOpen}>
          {stillOpen.map((line) => {
            const isKept = kept.has(line.rootExchangeId);
            return (
              <li key={line.rootExchangeId} style={lineStyle}>
                <span aria-hidden="true">? </span><Quoted text={line.questionMd} />{" "}
                <span style={{ display: "inline-flex", gap: 6, flexWrap: "wrap" }}>
                  <RecapLink onClick={() => onOpenInquiry(line.rootExchangeId, line.spanId)}>open</RecapLink>
                  {isKept ? <MeaningLabel>kept open</MeaningLabel> : (
                    <>
                      <RecapLink onClick={() => onSetStatus(line.rootExchangeId, "resolved")}>resolved</RecapLink>
                      {onRevisit ? (revisited?.(line.rootExchangeId)
                        ? <MeaningLabel>revisit once ✓</MeaningLabel>
                        : <RecapLink onClick={() => onRevisit(line.rootExchangeId)}>revisit once</RecapLink>) : null}
                      <RecapLink onClick={() => setKept((current) => new Set(current).add(line.rootExchangeId))}>keep open</RecapLink>
                    </>
                  )}
                </span>
              </li>
            );
          })}
        </Section>
      ) : null}
      {unfinished.length > 0 ? (
        <Section title={RECAP_COPY.unfinished}>
          {unfinished.map((line) => {
            // An abandoned problem keeps its steps (spec §5.4): it says it was
            // set aside, and its link reopens it through the same resume.
            const abandoned = line.status === "abandoned";
            return (
              <li key={line.sessionId} style={lineStyle}>
                <span aria-hidden="true">✎ </span>
                <span>{line.title} · {stepsLabel(line.stepCount)} · {line.helpLine}{abandoned ? ` · ${RECAP_COPY.setAside}` : ""}</span>{" "}
                <RecapLink onClick={() => onResume(line.sessionId)}>{abandoned ? RECAP_COPY.reopen : RECAP_COPY.resume}</RecapLink>
              </li>
            );
          })}
        </Section>
      ) : null}
      {secondLook.length > 0 ? (
        <Section title={RECAP_COPY.secondLook}>
          {secondLook.map((line) => (
            <li key={`${line.kind}:${line.sourceEventIds.join(",")}`} style={lineStyle}>
              <span aria-hidden="true">◌ </span>
              <span>{observationLine(line.kind, line.questionMd, line.observed)}</span>{" "}
              {line.rootExchangeId && line.spanId ? (
                <RecapLink onClick={() => onOpenInquiry(line.rootExchangeId as string, line.spanId as string)}>open ▸</RecapLink>
              ) : null}
            </li>
          ))}
        </Section>
      ) : null}
      {gains ? (
        <Section title={RECAP_COPY.sinceLastTime}>
          {sinceLastTime.demonstrated.map((line) => (
            <li key={line.learningObjectId} style={lineStyle}>
              <span>● {line.title} — demonstrated on your own ({shortDay(line.demonstratedOn, now)})</span>
            </li>
          ))}
          {sinceLastTime.checksRetired.map((line) => (
            <li key={line.commitmentId} style={lineStyle}>
              <span>No longer needed: you solved one like it on {shortDay(line.retiredAt, now)}</span>
            </li>
          ))}
        </Section>
      ) : null}
    </section>
  );
}
