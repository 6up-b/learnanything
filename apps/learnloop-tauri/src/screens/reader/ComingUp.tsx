// "Coming up" (reader workbench RW6b part 1; spec §9.3; UX §4.8-4.9, S15,
// D36; wireframe W12): the scheduled checks on your own as a calm, dated
// timeline -- never a list of counts. Each line has its date, its purpose,
// about how long it takes, *why* (the purpose and LearnLoop's estimate, never
// a verified fact, W2) and *undo*; the section has *undo all*. Undo takes an
// optional reason ("why? (optional)", W5), which is calibration data about
// whether the check was worth its minutes. The next three by date show, then
// "later ▸" with no number. Nothing takes focus or opens a modal.
import { useState, type CSSProperties } from "react";
import type { ReaderComingUpDto, ReaderFollowupLineDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { COMING_UP_COPY, aboutCheckMinutes, upcomingDay } from "./recapCopy";

export interface ComingUpProps {
  comingUp: ReaderComingUpDto;
  /** For the day labels against today (tests pin it). */
  now?: Date;
  onUndo: (commitmentId: string, reason: string | null) => Promise<unknown> | void;
  onUndoAll: (digestId: string, reason: string | null) => Promise<unknown> | void;
  onRestore?: (commitmentId: string) => Promise<unknown> | void;
}

const headingStyle: CSSProperties = { fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, margin: "8px 0 2px", fontWeight: 400 };
const listStyle: CSSProperties = { listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 4 };
const lineStyle: CSSProperties = { fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text, lineHeight: 1.5 };
const dayStyle: CSSProperties = { display: "inline-block", minWidth: 44, color: COLOR.textDim };
const linkStyle: CSSProperties = {
  border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11, padding: 0,
  cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2,
};
const inputStyle: CSSProperties = {
  fontFamily: FONT_MONO, fontSize: 11, background: COLOR.bgInput, color: COLOR.text,
  border: `1px solid ${COLOR.border}`, padding: "1px 4px", minWidth: 160,
};

function Link({ children, onClick, label }: { children: string; onClick: () => void; label?: string }) {
  return (
    <button type="button" style={linkStyle} onClick={onClick} aria-label={label}>
      {children}
    </button>
  );
}

/** Undo with an optional reason: undo, then the reason box (Enter or "undo" takes it). */
function UndoWithReason({ text = COMING_UP_COPY.undo, label, onUndo }: {
  text?: string;
  label?: string;
  onUndo: (reason: string | null) => void;
}) {
  const [asking, setAsking] = useState(false);
  const [reason, setReason] = useState("");
  if (!asking) return <Link onClick={() => setAsking(true)} label={label}>{text}</Link>;
  const take = () => {
    setAsking(false);
    onUndo(reason.trim() ? reason.trim() : null);
  };
  return (
    <span style={{ display: "inline-flex", gap: 6, alignItems: "baseline" }}>
      <input
        type="text"
        aria-label={COMING_UP_COPY.reasonLabel}
        placeholder={COMING_UP_COPY.reasonPlaceholder}
        value={reason}
        style={inputStyle}
        onChange={(event) => setReason(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") take();
          if (event.key === "Escape") setAsking(false);
        }}
      />
      <Link onClick={take} label={label}>{text}</Link>
      <Link onClick={() => setAsking(false)}>{COMING_UP_COPY.keep}</Link>
    </span>
  );
}

function Line({ line, now, undone, onUndo, onRestore }: {
  line: ReaderFollowupLineDto;
  now?: Date;
  undone: boolean;
  onUndo: (reason: string | null) => void;
  onRestore?: () => void;
}) {
  const [why, setWhy] = useState(false);
  const minutes = aboutCheckMinutes(line.expectedMinutes);
  const parts = [line.purposeText, minutes].filter(Boolean).join(" · ");
  return (
    <li style={lineStyle} data-followup={line.commitmentId}>
      <span style={dayStyle}>{line.date ? upcomingDay(line.date, now) : ""}</span>
      <span>{parts}</span>{" "}
      {undone ? (
        <span style={{ color: COLOR.textDim }}>
          · {COMING_UP_COPY.undone}{onRestore ? <> · <Link onClick={onRestore}>{COMING_UP_COPY.restore}</Link></> : null}
        </span>
      ) : (
        <span style={{ display: "inline-flex", gap: 6, flexWrap: "wrap" }}>
          <span aria-hidden="true">·</span>
          <Link onClick={() => setWhy((open) => !open)}>{COMING_UP_COPY.why}</Link>
          <span aria-hidden="true">·</span>
          <UndoWithReason label={`undo: ${line.purposeText}`} onUndo={onUndo} />
        </span>
      )}
      {why && !undone ? (
        <div style={{ color: COLOR.textDim, paddingLeft: 44 }} data-followup-why="">
          {line.why}
        </div>
      ) : null}
    </li>
  );
}

export function ComingUp({ comingUp, now, onUndo, onUndoAll, onRestore }: ComingUpProps) {
  const [later, setLater] = useState(false);
  const [undone, setUndone] = useState<Set<string>>(new Set());
  const lines = later ? [...comingUp.next, ...comingUp.later] : comingUp.next;
  if (comingUp.next.length === 0 && comingUp.later.length === 0) return null;
  const mark = (ids: string[], on: boolean) =>
    setUndone((current) => {
      const next = new Set(current);
      for (const id of ids) {
        if (on) next.add(id);
        else next.delete(id);
      }
      return next;
    });
  const pending = [...comingUp.next, ...comingUp.later].filter((line) => !undone.has(line.commitmentId));
  return (
    <div data-coming-up="">
      <h4 style={headingStyle}>{COMING_UP_COPY.title}</h4>
      <ul style={listStyle}>
        {lines.map((line) => (
          <Line
            key={line.commitmentId}
            line={line}
            now={now}
            undone={undone.has(line.commitmentId)}
            onUndo={(reason) => {
              mark([line.commitmentId], true);
              void Promise.resolve(onUndo(line.commitmentId, reason)).catch(() => mark([line.commitmentId], false));
            }}
            onRestore={onRestore ? () => {
              mark([line.commitmentId], false);
              void Promise.resolve(onRestore(line.commitmentId)).catch(() => mark([line.commitmentId], true));
            } : undefined}
          />
        ))}
      </ul>
      <div style={{ ...lineStyle, display: "flex", gap: 12, justifyContent: "space-between" }}>
        {comingUp.later.length > 0 && !later ? <Link onClick={() => setLater(true)}>{COMING_UP_COPY.later}</Link> : <span />}
        {pending.length > 0 && comingUp.undoAll.length > 0 ? (
          <UndoWithReason
            text={COMING_UP_COPY.undoAll}
            onUndo={(reason) => {
              const ids = pending.map((line) => line.commitmentId);
              mark(ids, true);
              for (const { digestId } of comingUp.undoAll) {
                void Promise.resolve(onUndoAll(digestId, reason)).catch(() => mark(ids, false));
              }
            }}
          />
        ) : null}
      </div>
    </div>
  );
}
