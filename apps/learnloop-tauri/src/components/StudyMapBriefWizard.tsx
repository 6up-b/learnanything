// Intent-first study-map brief wizard (§5.1). Outcome → depth → topics → (exam
// goal). Produces a StudyMapBriefDto; exam-prep reveals goal fields and signals
// createGoal so the same flow can mint the Goal. Feeds Quick add (default brief)
// and the full journey ("Create study map").

import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";
import type { StartingLevel, StudyMapBriefDto } from "../api/dto";
import { COLOR, Faint, FONT_MONO } from "./term";

export const STARTING_LEVELS: { id: StartingLevel; label: string }[] = [
  { id: "new_to_this", label: "new to this" },
  { id: "some_exposure", label: "some exposure" },
  { id: "comfortable", label: "comfortable" },
  { id: "strong_background", label: "strong background" }
];

type Outcome = "general_learning" | "reference_mastery" | "exam_prep";
const OUTCOMES: { id: Outcome; label: string; blurb: string }[] = [
  { id: "general_learning", label: "general learning", blurb: "build understanding across the material" },
  { id: "reference_mastery", label: "reference mastery", blurb: "look things up fast, retain the essentials" },
  { id: "exam_prep", label: "exam prep", blurb: "hit a recall target by a deadline" }
];
const DEPTHS = ["intro", "standard", "deep"];

export function StudyMapBriefWizard({
  initialBrief,
  submitLabel,
  submitting,
  onSubmit,
  onClose
}: {
  initialBrief?: StudyMapBriefDto;
  submitLabel?: string;
  submitting?: boolean;
  onSubmit: (brief: StudyMapBriefDto, createGoal: boolean) => void;
  onClose: () => void;
}) {
  const [step, setStep] = useState(0);
  const [outcome, setOutcome] = useState<Outcome>((initialBrief?.outcome as Outcome) ?? "general_learning");
  const [startingLevel, setStartingLevel] = useState<StartingLevel | undefined>(initialBrief?.startingLevel);
  const [level, setLevel] = useState(initialBrief?.level ?? "");
  const [depth, setDepth] = useState(initialBrief?.depth ?? "standard");
  const [notation, setNotation] = useState(initialBrief?.notation ?? "");
  const [includeTopics, setIncludeTopics] = useState<string[]>(initialBrief?.includeTopics ?? []);
  const [excludeTopics, setExcludeTopics] = useState<string[]>(initialBrief?.excludeTopics ?? []);
  const [dueDate, setDueDate] = useState("");
  const [targetRecall, setTargetRecall] = useState(initialBrief?.targetRecall ?? 0.85);
  const [examItemCount, setExamItemCount] = useState(initialBrief?.examItemCount ?? 20);

  const steps = useMemo(
    () => (outcome === "exam_prep" ? ["outcome", "depth", "topics", "goal"] : ["outcome", "depth", "topics"]),
    [outcome]
  );
  const isLast = step === steps.length - 1;

  const build = (): StudyMapBriefDto => {
    const brief: StudyMapBriefDto = {
      outcome,
      startingLevel,
      level: level.trim() || undefined,
      depth,
      notation: notation.trim() || undefined,
      includeTopics,
      excludeTopics
    };
    if (outcome === "exam_prep") {
      brief.dueAt = dueDate ? new Date(`${dueDate}T23:59:59`).toISOString() : undefined;
      brief.targetRecall = targetRecall;
      brief.examItemCount = examItemCount;
    }
    return brief;
  };

  const advance = () => {
    if (isLast) {
      onSubmit(build(), outcome === "exam_prep");
      return;
    }
    setStep((s) => Math.min(s + 1, steps.length - 1));
  };

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      const tag = (e.target as HTMLElement)?.tagName;
      if (e.key === "Enter" && tag !== "INPUT" && tag !== "TEXTAREA" && !submitting) {
        e.preventDefault();
        advance();
      }
    };
    window.addEventListener("keydown", handler, true);
    return () => window.removeEventListener("keydown", handler, true);
  });

  const current = steps[step];

  return (
    <div style={backdropStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        <div style={headerStyle}>
          <span style={{ color: COLOR.amber, fontWeight: 700 }}>❯</span>
          {steps.map((label, i) => (
            <span
              key={label}
              style={{
                fontSize: 12,
                fontFamily: FONT_MONO,
                color: i === step ? COLOR.amber : i < step ? COLOR.textDim : COLOR.textFaint,
                borderBottom: i === step ? `1px solid ${COLOR.amber}` : "1px solid transparent",
                paddingBottom: 2
              }}
            >
              {i + 1}·{label}
            </span>
          ))}
        </div>

        <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: "16px 18px" }}>
          {current === "outcome" ? (
            <div>
              <Label>what is this for</Label>
              {OUTCOMES.map((o) => (
                <div
                  key={o.id}
                  onClick={() => setOutcome(o.id)}
                  style={{
                    border: `1px solid ${outcome === o.id ? COLOR.amber : COLOR.border}`,
                    background: outcome === o.id ? "#241d12" : COLOR.bgInput,
                    padding: "10px 14px",
                    marginTop: 8,
                    cursor: "pointer"
                  }}
                >
                  <div style={{ color: outcome === o.id ? COLOR.amber : COLOR.text, fontSize: 13 }}>{o.label}</div>
                  <Faint style={{ fontSize: 12 }}>{o.blurb}</Faint>
                </div>
              ))}
            </div>
          ) : null}

          {current === "depth" ? (
            <div>
              <Label>where are you starting from</Label>
              <div style={{ display: "flex", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
                {STARTING_LEVELS.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => setStartingLevel(startingLevel === s.id ? undefined : s.id)}
                    style={{
                      ...segBtn,
                      border: `1px solid ${startingLevel === s.id ? COLOR.amber : COLOR.borderStrong}`,
                      background: startingLevel === s.id ? "#241d12" : "transparent",
                      color: startingLevel === s.id ? COLOR.amber : COLOR.textDim
                    }}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
              <Faint style={{ fontSize: 11, display: "block", marginBottom: 14 }}>
                sets how hard your first questions are — practice adapts from there
              </Faint>
              <Label>level notes</Label>
              <input style={inputStyle} value={level} placeholder="e.g. undergraduate, graduate, refresher" onChange={(e) => setLevel(e.target.value)} onKeyDown={(e) => e.stopPropagation()} />
              <Label style={{ marginTop: 20 }}>depth</Label>
              <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                {DEPTHS.map((d) => (
                  <button
                    key={d}
                    onClick={() => setDepth(d)}
                    style={{
                      ...segBtn,
                      border: `1px solid ${depth === d ? COLOR.amber : COLOR.borderStrong}`,
                      background: depth === d ? "#241d12" : "transparent",
                      color: depth === d ? COLOR.amber : COLOR.textDim
                    }}
                  >
                    {d}
                  </button>
                ))}
              </div>
              <Label style={{ marginTop: 20 }}>notation preference</Label>
              <input style={inputStyle} value={notation} placeholder="e.g. Leibniz, bra-ket, index notation (optional)" onChange={(e) => setNotation(e.target.value)} onKeyDown={(e) => e.stopPropagation()} />
            </div>
          ) : null}

          {current === "topics" ? (
            <div>
              <ChipInput label="include topics" chips={includeTopics} onChange={setIncludeTopics} placeholder="add a topic to focus on, press enter" />
              <div style={{ marginTop: 20 }}>
                <ChipInput label="exclude topics" chips={excludeTopics} onChange={setExcludeTopics} placeholder="add a topic to skip, press enter" />
              </div>
            </div>
          ) : null}

          {current === "goal" ? (
            <div>
              <Label>due date</Label>
              <input type="date" style={inputStyle} value={dueDate} onChange={(e) => setDueDate(e.target.value)} onKeyDown={(e) => e.stopPropagation()} />
              <Label style={{ marginTop: 20 }}>target recall</Label>
              <input
                type="number"
                min={0.5}
                max={0.99}
                step={0.01}
                style={{ ...inputStyle, width: 120 }}
                value={targetRecall}
                onChange={(e) => setTargetRecall(Math.min(0.99, Math.max(0.5, Number(e.target.value) || 0)))}
                onKeyDown={(e) => e.stopPropagation()}
              />
              <Label style={{ marginTop: 20 }}>held-out exam items</Label>
              <input
                type="number"
                min={0}
                max={100}
                style={{ ...inputStyle, width: 120 }}
                value={examItemCount}
                onChange={(e) => setExamItemCount(Math.max(0, Number(e.target.value) || 0))}
                onKeyDown={(e) => e.stopPropagation()}
              />
              <div style={{ marginTop: 12 }}>
                <Faint style={{ fontSize: 12 }}>This creates the Goal in the same flow.</Faint>
              </div>
            </div>
          ) : null}
        </div>

        <div style={footerStyle}>
          <button style={{ ...ghostBtn, opacity: step === 0 ? 0.4 : 1 }} disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))}>
            ← back
          </button>
          <span style={{ flex: 1 }} />
          <Faint style={{ fontSize: 11 }}>enter next · esc cancel</Faint>
          <button style={{ ...primaryBtn, opacity: submitting ? 0.5 : 1, cursor: submitting ? "default" : "pointer" }} disabled={submitting} onClick={advance}>
            {isLast ? submitLabel ?? "Use brief" : "next →"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ChipInput({ label, chips, onChange, placeholder }: { label: string; chips: string[]; onChange: (c: string[]) => void; placeholder: string }) {
  const [draft, setDraft] = useState("");
  const add = () => {
    const value = draft.trim();
    if (value && !chips.includes(value)) onChange([...chips, value]);
    setDraft("");
  };
  return (
    <div>
      <Label>{label}</Label>
      <input
        style={inputStyle}
        value={draft}
        placeholder={placeholder}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          e.stopPropagation();
          if (e.key === "Enter") {
            e.preventDefault();
            add();
          }
        }}
      />
      {chips.length ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
          {chips.map((chip) => (
            <span
              key={chip}
              style={{
                border: `1px solid ${COLOR.amber}`,
                background: "#241d12",
                color: COLOR.amber,
                fontFamily: FONT_MONO,
                fontSize: 12,
                padding: "2px 8px",
                display: "inline-flex",
                gap: 6
              }}
            >
              {chip}
              <span style={{ cursor: "pointer", color: COLOR.textFaint }} onClick={() => onChange(chips.filter((c) => c !== chip))}>
                ×
              </span>
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function Label({ children, style = {} }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div style={{ fontSize: 11, color: COLOR.amber, textTransform: "uppercase", letterSpacing: "0.12em", fontFamily: FONT_MONO, marginBottom: 6, ...style }}>
      {children}
    </div>
  );
}

const backdropStyle: CSSProperties = {
  position: "fixed",
  inset: 0,
  zIndex: 210,
  background: "rgba(8, 8, 13, 0.78)",
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "center",
  padding: "6vh 5vw",
  backdropFilter: "blur(2px)"
};

const modalStyle: CSSProperties = {
  width: "min(680px, 100%)",
  maxHeight: "84vh",
  background: COLOR.bg,
  border: `1px solid ${COLOR.borderStrong}`,
  boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
  display: "flex",
  flexDirection: "column",
  fontFamily: FONT_MONO,
  color: COLOR.text
};

const headerStyle: CSSProperties = {
  padding: "12px 16px",
  borderBottom: `1px solid ${COLOR.border}`,
  display: "flex",
  alignItems: "center",
  gap: 12,
  flexShrink: 0
};

const footerStyle: CSSProperties = {
  borderTop: `1px solid ${COLOR.border}`,
  padding: "10px 16px",
  display: "flex",
  alignItems: "center",
  gap: 12,
  flexShrink: 0
};

const inputStyle: CSSProperties = {
  width: "100%",
  background: COLOR.bgInput,
  color: COLOR.text,
  border: `1px solid ${COLOR.border}`,
  padding: "8px 12px",
  fontSize: 13,
  fontFamily: FONT_MONO,
  outline: "none"
};

const primaryBtn: CSSProperties = {
  padding: "7px 16px",
  border: `1px solid ${COLOR.amber}`,
  background: "#241d12",
  color: COLOR.amber,
  fontFamily: FONT_MONO,
  fontSize: 12,
  fontWeight: 600
};

const ghostBtn: CSSProperties = {
  padding: "7px 14px",
  border: `1px solid ${COLOR.borderStrong}`,
  background: "transparent",
  color: COLOR.textDim,
  fontFamily: FONT_MONO,
  fontSize: 12,
  cursor: "pointer"
};

const segBtn: CSSProperties = {
  padding: "6px 16px",
  fontFamily: FONT_MONO,
  fontSize: 12,
  cursor: "pointer"
};
