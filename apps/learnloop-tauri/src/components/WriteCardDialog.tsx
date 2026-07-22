// Learner card authoring (Matuschak reader-control slice): the learner writes a
// card in their own words against a learning object they already own. No review
// gate — author_practice_item writes straight to vault YAML and the sidecar
// reloads scheduler state before responding, so the card is schedulable on close.

import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type { CommandError } from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill, TermSelect } from "./term";

const PRACTICE_MODES = [
  { value: "short_answer", label: "short answer" },
  { value: "free_recall", label: "free recall" },
  { value: "explanation", label: "explanation" },
  { value: "worked_problem", label: "worked problem" }
];

export function WriteCardDialog({
  defaultLearningObjectId,
  defaultLearningObjectTitle,
  onClose,
  onCreated
}: {
  defaultLearningObjectId?: string | null;
  defaultLearningObjectTitle?: string | null;
  onClose: () => void;
  onCreated: (practiceItemId: string) => void;
}) {
  const [loOptions, setLoOptions] = useState<{ value: string; label: string }[] | null>(null);
  const [learningObjectId, setLearningObjectId] = useState(defaultLearningObjectId ?? "");
  const [prompt, setPrompt] = useState("");
  const [expectedAnswer, setExpectedAnswer] = useState("");
  const [hintsText, setHintsText] = useState("");
  const [practiceMode, setPracticeMode] = useState("short_answer");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .getFacetMastery()
      .then((snap) => {
        if (!alive) return;
        const seen = new Map<string, string>();
        for (const facet of snap.facets) {
          for (const lo of facet.learningObjects) {
            if (!seen.has(lo.id)) seen.set(lo.id, lo.title);
          }
        }
        const options = Array.from(seen, ([value, label]) => ({ value, label })).sort((a, b) =>
          a.label.localeCompare(b.label)
        );
        setLoOptions(options);
      })
      .catch(() => {
        // Fall back to the focused item's LO; the picker just stays fixed.
        if (alive) setLoOptions([]);
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler, true);
    return () => window.removeEventListener("keydown", handler, true);
  }, [onClose]);

  const options = useMemo(() => {
    const base = loOptions ?? [];
    if (defaultLearningObjectId && !base.some((o) => o.value === defaultLearningObjectId)) {
      return [{ value: defaultLearningObjectId, label: defaultLearningObjectTitle ?? defaultLearningObjectId }, ...base];
    }
    return base;
  }, [loOptions, defaultLearningObjectId, defaultLearningObjectTitle]);

  const canSubmit = !busy && learningObjectId !== "" && prompt.trim() !== "" && expectedAnswer.trim() !== "";

  const submit = async () => {
    if (!canSubmit) return;
    setBusy(true);
    setError(null);
    try {
      const hints = hintsText
        .split("\n")
        .map((h) => h.trim())
        .filter(Boolean);
      const res = await api.authorPracticeItem({
        learningObjectId,
        prompt: prompt.trim(),
        expectedAnswer: expectedAnswer.trim(),
        practiceMode,
        hints: hints.length > 0 ? hints : undefined
      });
      onCreated(res.practiceItemId);
      onClose();
    } catch (err: unknown) {
      const command = err && typeof err === "object" && "code" in err ? (err as CommandError) : null;
      setError(command?.message ?? (err instanceof Error ? err.message : String(err)));
      setBusy(false);
    }
  };

  return (
    <div style={backdropStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        <div style={headerStyle}>
          <span style={{ color: COLOR.amber, fontWeight: 700 }}>❯</span>
          <span style={{ fontSize: 13, color: COLOR.text }}>Write a card</span>
          <Pill color="amber">yours</Pill>
          <span style={{ marginLeft: "auto", cursor: "pointer", color: COLOR.textFaint, fontSize: 12 }} onClick={onClose}>
            esc ✕
          </span>
        </div>

        <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: "16px 18px" }}>
          <Label>learning object</Label>
          <TermSelect
            value={learningObjectId}
            options={options}
            onChange={setLearningObjectId}
            placeholder={loOptions == null ? "loading…" : "pick a learning object"}
            width={420}
          />

          <Label style={{ marginTop: 18 }}>prompt · the question you want to be asked</Label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.stopPropagation()}
            placeholder="e.g. Why does the determinant vanish exactly when the columns are dependent?"
            rows={3}
            style={textareaStyle}
            autoFocus
          />

          <Label style={{ marginTop: 16 }}>expected answer · in your own words</Label>
          <textarea
            value={expectedAnswer}
            onChange={(e) => setExpectedAnswer(e.target.value)}
            onKeyDown={(e) => e.stopPropagation()}
            placeholder="what a good answer should contain"
            rows={4}
            style={textareaStyle}
          />

          <div style={{ marginTop: 16, display: "flex", gap: 24, alignItems: "flex-start", flexWrap: "wrap" }}>
            <div>
              <Label>mode</Label>
              <TermSelect value={practiceMode} options={PRACTICE_MODES} onChange={setPracticeMode} width={200} />
            </div>
            <div style={{ flex: 1, minWidth: 220 }}>
              <Label>hints · optional, one per line</Label>
              <textarea
                value={hintsText}
                onChange={(e) => setHintsText(e.target.value)}
                onKeyDown={(e) => e.stopPropagation()}
                placeholder="a nudge to show before revealing the answer"
                rows={2}
                style={textareaStyle}
              />
            </div>
          </div>

          {error ? <div style={{ marginTop: 12, color: COLOR.red, fontSize: 12 }}>{error}</div> : null}
        </div>

        <div style={footerStyle}>
          <Faint style={{ fontSize: 11 }}>saved to your vault as a human-authored card — no review step</Faint>
          <span style={{ flex: 1 }} />
          <button style={ghostBtn} onClick={onClose}>
            cancel
          </button>
          <button
            style={{ ...primaryBtn, opacity: canSubmit ? 1 : 0.5, cursor: canSubmit ? "pointer" : "default" }}
            disabled={!canSubmit}
            onClick={() => void submit()}
          >
            {busy ? "saving…" : "Create card"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Label({ children, style = {} }: { children: React.ReactNode; style?: CSSProperties }) {
  return (
    <div style={{ fontSize: 11, color: COLOR.amber, textTransform: "uppercase", letterSpacing: "0.12em", fontFamily: FONT_MONO, marginBottom: 6, ...style }}>
      {children}
    </div>
  );
}

const textareaStyle: CSSProperties = {
  width: "100%",
  background: COLOR.bgInput,
  color: COLOR.text,
  border: `1px solid ${COLOR.border}`,
  padding: "9px 12px",
  fontFamily: FONT_MONO,
  fontSize: 13,
  lineHeight: 1.55,
  outline: "none",
  resize: "vertical"
};

const backdropStyle: CSSProperties = {
  position: "fixed",
  inset: 0,
  zIndex: 210,
  background: "rgba(8, 8, 13, 0.78)",
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "center",
  padding: "8vh 5vw",
  backdropFilter: "blur(2px)"
};

const modalStyle: CSSProperties = {
  width: "min(640px, 100%)",
  maxHeight: "80vh",
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
