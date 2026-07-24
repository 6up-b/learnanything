// 4-step goal-creation wizard, terminal aesthetic, keyboard-friendly. Each step is
// one screen. Esc closes; Enter advances when the step is valid (except inside
// text inputs / on the concept filter). Step 3 debounces goal_feasibility.
//
// Steps: 1 What (title + optional larger intent + concept picker + advanced facet ids) · 2 How well
// (target recall) · 3 By when (due date / open-ended, live feasibility) ·
// 4 Exam (held-out toggle + summary + create).

import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";
import { api } from "../api/client";
import type { ConceptGraphNode, GoalFeasibilityResult } from "../api/dto";
import { COLOR, Faint, FONT_MONO } from "./term";

const STEP_LABELS = ["what", "how well", "by when", "exam"];

export function GoalWizard({ onClose, onCreated, onError }: { onClose: () => void; onCreated: () => void; onError: (m: string) => void }) {
  const [step, setStep] = useState(0);

  // step 1
  const [title, setTitle] = useState("");
  const [intentSentence, setIntentSentence] = useState("");
  const [concepts, setConcepts] = useState<ConceptGraphNode[] | null>(null);
  const [conceptError, setConceptError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [facetIdsRaw, setFacetIdsRaw] = useState("");

  // step 2
  const [targetRecall, setTargetRecall] = useState(0.85);

  // step 3
  const [openEnded, setOpenEnded] = useState(false);
  const [dueDate, setDueDate] = useState("");
  const [feasibility, setFeasibility] = useState<GoalFeasibilityResult | null>(null);
  const [feasibilityLoading, setFeasibilityLoading] = useState(false);

  // step 4
  const [examEnabled, setExamEnabled] = useState(true);
  const [examItemCount, setExamItemCount] = useState(20);
  const [populatePractice, setPopulatePractice] = useState(true);

  const [submitting, setSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const facetIds = useMemo(
    () => facetIdsRaw.split(",").map((s) => s.trim()).filter(Boolean),
    [facetIdsRaw]
  );
  const conceptIds = useMemo(() => Array.from(selected), [selected]);
  const dueAt = openEnded || !dueDate ? null : new Date(`${dueDate}T23:59:59`).toISOString();

  const stepValid = useMemo(() => {
    if (step === 0) return title.trim().length > 0 && (conceptIds.length > 0 || facetIds.length > 0);
    if (step === 2) return openEnded || dueDate.length > 0;
    return true;
  }, [step, title, conceptIds.length, facetIds.length, openEnded, dueDate]);

  // Load concept graph once.
  useEffect(() => {
    let cancelled = false;
    api
      .getConceptGraph()
      .then((snap) => {
        if (!cancelled) setConcepts(snap.concepts);
      })
      .catch((e) => {
        if (!cancelled) setConceptError((e as Error).message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Debounced feasibility whenever the scope/target/due changes (step 3 focus).
  useEffect(() => {
    if (conceptIds.length === 0 && facetIds.length === 0) {
      setFeasibility(null);
      return;
    }
    let cancelled = false;
    setFeasibilityLoading(true);
    const handle = window.setTimeout(() => {
      api
        .goalFeasibility({ targetRecall, dueAt, concepts: conceptIds, facets: facetIds })
        .then((res) => {
          if (!cancelled) setFeasibility(res);
        })
        .catch(() => {
          if (!cancelled) setFeasibility(null);
        })
        .finally(() => {
          if (!cancelled) setFeasibilityLoading(false);
        });
    }, 350);
    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conceptIds.join(","), facetIds.join(","), targetRecall, dueAt]);

  const advance = () => {
    if (step < 3) {
      if (stepValid) setStep((s) => s + 1);
    } else {
      void create();
    }
  };

  async function create() {
    if (submitting) return;
    setSubmitting(true);
    setCreateError(null);
    try {
      const created = await api.createGoal({
        title: title.trim(),
        intentSentence: intentSentence.trim() || undefined,
        targetRecall,
        dueAt,
        concepts: conceptIds,
        facets: facetIds,
        examEnabled,
        examItemCount: examEnabled ? examItemCount : undefined
      });
      if (populatePractice) {
        // Fire-and-forget: the exam pool reserves never-attempted items on day
        // one, which can leave the goal with nothing practicable. Populate in
        // the background; failures surface through the shared error channel.
        void api
          .runCliCommand(["populate-goal", created.goal.id])
          .then((result) => {
            if (result.exitCode !== 0) {
              onError(`goal practice generation failed: ${result.stderr || result.stdout}`.trim());
            } else {
              onCreated();
            }
          })
          .catch((e) => onError(`goal practice generation failed: ${(e as Error).message}`));
      }
      onCreated();
      onClose();
    } catch (e) {
      setCreateError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      const isInput = tag === "input" || tag === "textarea";
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      } else if (event.key === "Enter" && !isInput) {
        event.preventDefault();
        advance();
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, stepValid, submitting, title, intentSentence, conceptIds, facetIds, targetRecall, dueAt, examEnabled, examItemCount]);

  const filteredConcepts = useMemo(() => {
    if (!concepts) return [];
    const q = filter.trim().toLowerCase();
    if (!q) return concepts;
    return concepts.filter((c) => c.title.toLowerCase().includes(q) || c.aliases.some((a) => a.toLowerCase().includes(q)));
  }, [concepts, filter]);

  const examQuestionsRoughly = Math.round(targetRecall * 20);

  return (
    <div style={backdropStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        {/* header + step indicator */}
        <div style={headerStyle}>
          <span style={{ color: COLOR.amber, fontWeight: 700 }}>❯</span>
          <span style={{ color: COLOR.text, fontSize: 13 }}>
            new <span style={{ color: COLOR.amber }}>goal</span>
          </span>
          <span style={{ flex: 1 }} />
          {STEP_LABELS.map((label, i) => (
            <span
              key={label}
              style={{
                fontSize: 11,
                fontFamily: FONT_MONO,
                color: i === step ? COLOR.amber : i < step ? COLOR.textDim : COLOR.textFaint,
                borderBottom: i === step ? `1px solid ${COLOR.amber}` : "1px solid transparent",
                paddingBottom: 2
              }}
            >
              {i + 1}·{label}
            </span>
          ))}
          <span onClick={onClose} style={{ color: COLOR.textDim, cursor: "pointer", fontSize: 12, marginLeft: 8 }}>
            esc
          </span>
        </div>

        <div style={{ flex: 1, overflowY: "auto", minHeight: 0, padding: "20px 22px" }}>
          {step === 0 ? (
            <StepWhat
              title={title}
              onTitle={setTitle}
              intentSentence={intentSentence}
              onIntentSentence={setIntentSentence}
              concepts={filteredConcepts}
              conceptError={conceptError}
              loading={concepts == null}
              filter={filter}
              onFilter={setFilter}
              selected={selected}
              onToggle={(id) =>
                setSelected((prev) => {
                  const next = new Set(prev);
                  if (next.has(id)) next.delete(id);
                  else next.add(id);
                  return next;
                })
              }
              totalSelected={conceptIds.length}
              facetIdsRaw={facetIdsRaw}
              onFacetIds={setFacetIdsRaw}
              facetCount={facetIds.length}
            />
          ) : step === 1 ? (
            <StepHowWell targetRecall={targetRecall} onChange={setTargetRecall} roughly={examQuestionsRoughly} />
          ) : step === 2 ? (
            <StepByWhen
              openEnded={openEnded}
              onOpenEnded={setOpenEnded}
              dueDate={dueDate}
              onDueDate={setDueDate}
              feasibility={feasibility}
              loading={feasibilityLoading}
            />
          ) : (
            <StepExam
              examEnabled={examEnabled}
              onExamEnabled={setExamEnabled}
              examItemCount={examItemCount}
              onExamItemCount={setExamItemCount}
              populatePractice={populatePractice}
              onPopulatePractice={setPopulatePractice}
              title={title}
              intentSentence={intentSentence}
              conceptCount={conceptIds.length}
              facetCount={facetIds.length}
              targetRecall={targetRecall}
              dueAt={dueAt}
              feasibility={feasibility}
              createError={createError}
            />
          )}
        </div>

        {/* footer */}
        <div style={footerStyle}>
          {step > 0 ? (
            <button type="button" onClick={() => setStep((s) => s - 1)} style={ghostBtn}>
              ← back
            </button>
          ) : (
            <span />
          )}
          <span style={{ flex: 1 }} />
          <Faint style={{ fontSize: 11 }}>enter {step < 3 ? "next" : "create"} · esc cancel</Faint>
          <button
            type="button"
            onClick={advance}
            disabled={!stepValid || submitting}
            style={{ ...primaryBtn, opacity: !stepValid || submitting ? 0.4 : 1, cursor: !stepValid || submitting ? "default" : "pointer" }}
          >
            {step < 3 ? "next →" : submitting ? "creating…" : "create goal ↵"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── step 1: what ────────────────────────────────────────────────────────────
function StepWhat({
  title,
  onTitle,
  intentSentence,
  onIntentSentence,
  concepts,
  conceptError,
  loading,
  filter,
  onFilter,
  selected,
  onToggle,
  totalSelected,
  facetIdsRaw,
  onFacetIds,
  facetCount
}: {
  title: string;
  onTitle: (v: string) => void;
  intentSentence: string;
  onIntentSentence: (v: string) => void;
  concepts: ConceptGraphNode[];
  conceptError: string | null;
  loading: boolean;
  filter: string;
  onFilter: (v: string) => void;
  selected: Set<string>;
  onToggle: (id: string) => void;
  totalSelected: number;
  facetIdsRaw: string;
  onFacetIds: (v: string) => void;
  facetCount: number;
}) {
  return (
    <div>
      <Label>goal title</Label>
      <input value={title} onChange={(e) => onTitle(e.target.value)} placeholder="e.g. Linear algebra midterm" style={inputStyle} autoFocus />

      <Label style={{ marginTop: 20 }}>quest / larger intent · optional</Label>
      <textarea
        value={intentSentence}
        onChange={(e) => onIntentSentence(e.target.value)}
        placeholder="e.g. I want to use complex numbers in signal processing."
        rows={2}
        style={{ ...inputStyle, resize: "vertical", lineHeight: 1.5 }}
      />
      <Faint style={{ display: "block", marginTop: 6, fontSize: 11, lineHeight: 1.5 }}>
        Used to connect transfer questions to why this matters. If blank, LearnLoop uses the exam or problem goal above.
      </Faint>

      <Label style={{ marginTop: 20 }}>concepts — {totalSelected} selected</Label>
      <input value={filter} onChange={(e) => onFilter(e.target.value)} placeholder="filter concepts…" style={inputStyle} />
      <div style={{ marginTop: 8, border: `1px solid ${COLOR.border}`, maxHeight: 240, overflowY: "auto", background: COLOR.bgInput }}>
        {conceptError ? (
          <div style={{ padding: 12, fontSize: 12, color: COLOR.red }}>{conceptError}</div>
        ) : loading ? (
          <div style={{ padding: 12, fontSize: 12, color: COLOR.textFaint }}>loading concepts…</div>
        ) : concepts.length === 0 ? (
          <div style={{ padding: 12, fontSize: 12, color: COLOR.textFaint }}>no concepts match</div>
        ) : (
          concepts.map((c) => {
            const on = selected.has(c.id);
            return (
              <div
                key={c.id}
                onClick={() => onToggle(c.id)}
                style={{ display: "flex", alignItems: "center", gap: 10, padding: "7px 12px", cursor: "pointer", background: on ? COLOR.bgElev : "transparent", borderBottom: `1px solid ${COLOR.border}` }}
              >
                <span style={{ fontFamily: FONT_MONO, color: on ? COLOR.amber : COLOR.textFaint }}>{on ? "▣" : "▢"}</span>
                <span style={{ fontSize: 13, color: COLOR.text, flex: 1 }}>{c.title}</span>
                <Faint style={{ fontSize: 11, fontFamily: FONT_MONO }}>{c.practiceItemCount} items</Faint>
              </div>
            );
          })
        )}
      </div>

      <Label style={{ marginTop: 20 }}>advanced · explicit facet ids (comma-separated){facetCount ? ` — ${facetCount}` : ""}</Label>
      <input value={facetIdsRaw} onChange={(e) => onFacetIds(e.target.value)} placeholder="facet_…, facet_…" style={inputStyle} />
    </div>
  );
}

// ── step 2: how well ────────────────────────────────────────────────────────
function StepHowWell({ targetRecall, onChange, roughly }: { targetRecall: number; onChange: (v: number) => void; roughly: number }) {
  return (
    <div>
      <Label>target recall</Label>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 6 }}>
        <input type="range" min={0.5} max={0.99} step={0.01} value={targetRecall} onChange={(e) => onChange(Number(e.target.value))} style={{ flex: 1, accentColor: COLOR.amber }} />
        <span style={{ fontFamily: FONT_MONO, fontSize: 22, color: COLOR.amber, minWidth: 62, textAlign: "right" }}>{Math.round(targetRecall * 100)}%</span>
      </div>
      <div style={{ marginTop: 18, padding: "12px 14px", border: `1px solid ${COLOR.border}`, background: COLOR.bgInput, fontSize: 13, color: COLOR.textDim, lineHeight: 1.6 }}>
        A facet counts as <span style={{ color: COLOR.green }}>on track</span> once its recall reaches {Math.round(targetRecall * 100)}%.
        <br />
        Roughly: able to answer <span style={{ color: COLOR.text }}>~{roughly} of 20</span> exam questions on each concept.
      </div>
    </div>
  );
}

// ── step 3: by when ─────────────────────────────────────────────────────────
function StepByWhen({
  openEnded,
  onOpenEnded,
  dueDate,
  onDueDate,
  feasibility,
  loading
}: {
  openEnded: boolean;
  onOpenEnded: (v: boolean) => void;
  dueDate: string;
  onDueDate: (v: string) => void;
  feasibility: GoalFeasibilityResult | null;
  loading: boolean;
}) {
  return (
    <div>
      <Label>due date</Label>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 6 }}>
        <input type="date" value={dueDate} disabled={openEnded} onChange={(e) => onDueDate(e.target.value)} style={{ ...inputStyle, width: "auto", opacity: openEnded ? 0.4 : 1 }} />
        <label style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: 13, color: COLOR.textDim, cursor: "pointer" }}>
          <span style={{ fontFamily: FONT_MONO, color: openEnded ? COLOR.amber : COLOR.textFaint }} onClick={() => onOpenEnded(!openEnded)}>
            {openEnded ? "▣" : "▢"}
          </span>
          <span onClick={() => onOpenEnded(!openEnded)}>open-ended (no deadline)</span>
        </label>
      </div>

      <div style={{ marginTop: 18, padding: "12px 14px", border: `1px solid ${COLOR.border}`, background: COLOR.bgInput, fontSize: 13, color: COLOR.textDim, lineHeight: 1.65 }}>
        {loading ? (
          <Faint>estimating feasibility…</Faint>
        ) : !feasibility ? (
          <Faint>pick concepts on step 1 to see a projection.</Faint>
        ) : (
          <>
            <div>
              At your current pace you'd have{" "}
              <span style={{ color: COLOR.amber }}>
                {feasibility.onTrackCount} of {feasibility.scopeFacetCount}
              </span>{" "}
              facets on track{openEnded ? "" : " by this date"}
              {feasibility.projectedOnTrackFraction != null ? ` (${Math.round(feasibility.projectedOnTrackFraction * 100)}%)` : ""}.
            </div>
            {feasibility.uncoveredConcepts.length > 0 ? (
              <div style={{ marginTop: 8, color: COLOR.pink }}>
                no practice material yet for: {feasibility.uncoveredConcepts.join(", ")}
              </div>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}

// ── step 4: exam + summary ──────────────────────────────────────────────────
function StepExam({
  examEnabled,
  onExamEnabled,
  examItemCount,
  onExamItemCount,
  populatePractice,
  onPopulatePractice,
  title,
  intentSentence,
  conceptCount,
  facetCount,
  targetRecall,
  dueAt,
  feasibility,
  createError
}: {
  examEnabled: boolean;
  onExamEnabled: (v: boolean) => void;
  examItemCount: number;
  onExamItemCount: (v: number) => void;
  populatePractice: boolean;
  onPopulatePractice: (v: boolean) => void;
  title: string;
  intentSentence: string;
  conceptCount: number;
  facetCount: number;
  targetRecall: number;
  dueAt: string | null;
  feasibility: GoalFeasibilityResult | null;
  createError: string | null;
}) {
  return (
    <div>
      <Label>practice exam</Label>
      <label style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 6, cursor: "pointer" }}>
        <span style={{ fontFamily: FONT_MONO, color: examEnabled ? COLOR.amber : COLOR.textFaint, fontSize: 15 }} onClick={() => onExamEnabled(!examEnabled)}>
          {examEnabled ? "▣" : "▢"}
        </span>
        <span style={{ fontSize: 13, color: COLOR.text }} onClick={() => onExamEnabled(!examEnabled)}>
          hold out a practice exam
        </span>
        {examEnabled ? (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6, marginLeft: 8 }}>
            <input
              type="number"
              min={5}
              max={100}
              value={examItemCount}
              onChange={(e) => onExamItemCount(Math.max(1, Number(e.target.value) || 0))}
              style={{ ...inputStyle, width: 70 }}
            />
            <Faint style={{ fontSize: 12 }}>items</Faint>
          </span>
        ) : null}
      </label>
      <div style={{ marginTop: 6, fontSize: 12, color: COLOR.textFaint, lineHeight: 1.5 }}>
        Held-out items are reserved from your practice pool so the exam measures real transfer, not memorized questions.
      </div>

      <Label style={{ marginTop: 22 }}>starter practice</Label>
      <label style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 6, cursor: "pointer" }}>
        <span style={{ fontFamily: FONT_MONO, color: populatePractice ? COLOR.amber : COLOR.textFaint, fontSize: 15 }} onClick={() => onPopulatePractice(!populatePractice)}>
          {populatePractice ? "▣" : "▢"}
        </span>
        <span style={{ fontSize: 13, color: COLOR.text }} onClick={() => onPopulatePractice(!populatePractice)}>
          generate practice questions for this goal (background)
        </span>
      </label>
      <div style={{ marginTop: 6, fontSize: 12, color: COLOR.textFaint, lineHeight: 1.5 }}>
        The held-out exam reserves questions you have never practiced, which can leave the goal with
        little to practice on day one. This fills the gap with newly generated items.
      </div>

      <Label style={{ marginTop: 22 }}>summary</Label>
      <div style={{ border: `1px solid ${COLOR.border}`, background: COLOR.bgInput, padding: "12px 14px", fontSize: 13, lineHeight: 1.8 }}>
        <SummaryRow k="title" v={title || "—"} />
        <SummaryRow
          k="quest"
          v={
            intentSentence.trim() ||
            (examEnabled
              ? `Do well on the exam goal “${title}”.`
              : `Be good at problems covered by the goal “${title}”.`)
          }
        />
        <SummaryRow k="scope" v={`${conceptCount} concepts${facetCount ? ` + ${facetCount} facets` : ""}`} />
        <SummaryRow k="target" v={`${Math.round(targetRecall * 100)}% recall`} />
        <SummaryRow k="due" v={dueAt ? new Date(dueAt).toLocaleDateString() : "open-ended"} />
        <SummaryRow k="exam" v={examEnabled ? `${examItemCount} held-out items` : "off"} />
        {feasibility ? (
          <SummaryRow k="projection" v={`${feasibility.onTrackCount}/${feasibility.scopeFacetCount} facets on track at current pace`} />
        ) : null}
      </div>
      {createError ? <div style={{ marginTop: 12, fontSize: 12, color: COLOR.red }}>{createError}</div> : null}
    </div>
  );
}

function SummaryRow({ k, v }: { k: string; v: string }) {
  return (
    <div style={{ display: "flex", gap: 12 }}>
      <span style={{ color: COLOR.textFaint, fontFamily: FONT_MONO, width: 90, flexShrink: 0 }}>{k}</span>
      <span style={{ color: COLOR.text }}>{v}</span>
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
