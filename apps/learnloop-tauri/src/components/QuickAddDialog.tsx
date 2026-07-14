// Quick add (§1): paste one source → auto-selected units, suggested role, default
// brief, and ONE confirmation (token estimate + external-AI consent), then a
// priority build batch. compose → confirm. The confirm phase is the single
// consent checkpoint; import/inventory/synthesis run after it.

import { useEffect, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type { CommandError, QuickAddPlanDto, StudyMapBriefDto } from "../api/dto";
import { StudyMapBriefWizard } from "./StudyMapBriefWizard";
import { COLOR, Faint, FONT_MONO, Pill, TermSelect } from "./term";

const ROLES = ["primary_textbook", "lecture", "paper", "reference", "alternate_explanation"];

export function QuickAddDialog({
  subjects,
  defaultSubjectId,
  onClose,
  onEnqueued
}: {
  subjects: { id: string; title: string }[];
  defaultSubjectId?: string | null;
  onClose: () => void;
  onEnqueued: (batchId: string) => void;
}) {
  const [phase, setPhase] = useState<"compose" | "confirm">("compose");
  const [source, setSource] = useState("");
  const [subjectId, setSubjectId] = useState(defaultSubjectId ?? subjects[0]?.id ?? "");
  const [brief, setBrief] = useState<StudyMapBriefDto | undefined>(undefined);
  const [briefOpen, setBriefOpen] = useState(false);
  const [plan, setPlan] = useState<QuickAddPlanDto | null>(null);
  const [roleOverride, setRoleOverride] = useState<string>("");
  const [consentTicked, setConsentTicked] = useState<boolean[]>([]);
  const [busy, setBusy] = useState(false);
  const [needsImport, setNeedsImport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !briefOpen) onClose();
    };
    window.addEventListener("keydown", handler, true);
    return () => window.removeEventListener("keydown", handler, true);
  }, [onClose, briefOpen]);

  const asCommandError = (err: unknown): CommandError | null =>
    err && typeof err === "object" && "code" in err ? (err as CommandError) : null;

  const runPlan = async () => {
    setBusy(true);
    setError(null);
    setNeedsImport(false);
    try {
      const res = await api.planQuickAdd({ source: source.trim(), subjectId, brief });
      setPlan(res.plan);
      setRoleOverride(res.plan.suggestedRole);
      setConsentTicked(res.plan.confirmation.externalAiConsent.map(() => false));
      setPhase("confirm");
    } catch (err: unknown) {
      const command = asCommandError(err);
      if (command?.code === "quick_add_requires_import") {
        setNeedsImport(true);
      } else {
        setError(command?.message ?? (err instanceof Error ? err.message : String(err)));
      }
    } finally {
      setBusy(false);
    }
  };

  const importThenPlan = async () => {
    setBusy(true);
    setError(null);
    try {
      const batch = await api.startImportBatch({ sources: [source.trim()], subjectId });
      let tries = 0;
      const poll = async () => {
        tries += 1;
        const current = await api.getIngestBatch(batch.id);
        const done = current.status === "completed" || current.status === "failed" || current.status === "blocked";
        if (done || tries > 60) {
          setNeedsImport(false);
          await runPlan();
          return;
        }
        setTimeout(() => void poll(), 1000);
      };
      await poll();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  };

  const confirmBuild = async () => {
    if (!plan) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.confirmQuickAdd({ source: source.trim(), subjectId, brief, roleOverride });
      onEnqueued(res.quickAdd.batchId);
      onClose();
    } catch (err: unknown) {
      const command = asCommandError(err);
      setError(command?.message ?? (err instanceof Error ? err.message : String(err)));
      setBusy(false);
    }
  };

  const allConsented = consentTicked.every(Boolean);

  return (
    <div style={backdropStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        <div style={headerStyle}>
          <span style={{ color: COLOR.amber, fontWeight: 700 }}>❯</span>
          <span style={{ fontSize: 13, color: COLOR.text }}>Quick add → study map</span>
          <Pill color={phase === "confirm" ? "amber" : "slate"}>{phase}</Pill>
          <span style={{ marginLeft: "auto", cursor: "pointer", color: COLOR.textFaint, fontSize: 12 }} onClick={onClose}>
            esc ✕
          </span>
        </div>

        <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: "16px 18px" }}>
          {phase === "compose" ? (
            <div>
              <Label>source</Label>
              <div style={{ border: `1px solid ${source.trim() ? COLOR.amber : COLOR.border}`, background: COLOR.bgInput, padding: "9px 12px 9px 30px", position: "relative" }}>
                <span style={{ position: "absolute", left: 12, top: 9, color: COLOR.amber, fontWeight: 700 }}>❯</span>
                <input
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  onKeyDown={(e) => e.stopPropagation()}
                  placeholder="paste a URL, arXiv id, PDF path, or .md/.txt"
                  style={{ width: "100%", background: "transparent", color: COLOR.text, border: "none", outline: "none", fontFamily: FONT_MONO, fontSize: 13 }}
                />
              </div>

              <Label style={{ marginTop: 18 }}>subject</Label>
              <TermSelect
                value={subjectId}
                options={subjects.map((s) => ({ value: s.id, label: s.title }))}
                onChange={setSubjectId}
                placeholder="pick a subject"
                width={280}
              />

              <div style={{ marginTop: 18, display: "flex", alignItems: "center", gap: 10 }}>
                <span
                  onClick={() => setBriefOpen(true)}
                  title="the brief is where your intent lives — your level, target depth, exam-prep vs general learning, notation preferences. The same source becomes an intro course or an advanced treatment depending on it; the synthesis model reads it when proposing the study map."
                  style={{
                    cursor: "help",
                    color: COLOR.amberLink,
                    fontSize: 12,
                    textDecoration: "underline dotted",
                    textUnderlineOffset: 3
                  }}
                >
                  {brief ? "edit brief" : "customize brief"}
                </span>
                {brief ? <Faint style={{ fontSize: 12 }}>brief: {brief.outcome ?? "general_learning"} · {brief.depth ?? "standard"}</Faint> : <Faint style={{ fontSize: 12 }}>default brief will be used</Faint>}
              </div>

              {needsImport ? (
                <div style={{ marginTop: 16, border: `1px solid ${COLOR.borderStrong}`, background: COLOR.bgInput, padding: "10px 14px" }}>
                  <Faint style={{ fontSize: 12 }}>This source has not been imported yet. Import + extract first, then quick-add continues.</Faint>
                  <div style={{ marginTop: 8 }}>
                    <button style={{ ...primaryBtn, opacity: busy ? 0.5 : 1 }} disabled={busy} onClick={() => void importThenPlan()}>
                      {busy ? "importing…" : "Import first"}
                    </button>
                  </div>
                </div>
              ) : null}

              {error ? <div style={{ marginTop: 12, color: COLOR.red, fontSize: 12 }}>{error}</div> : null}
            </div>
          ) : null}

          {phase === "confirm" && plan ? (
            <div>
              <div style={{ fontSize: 14, color: COLOR.text, marginBottom: 4 }}>{plan.title}</div>
              <Faint style={{ fontSize: 12 }}>{plan.normalizedUri}</Faint>

              <Label style={{ marginTop: 18 }}>scope</Label>
              <div style={{ fontSize: 13, color: COLOR.text }}>
                {plan.wholeSource ? "whole source" : `${plan.selectedUnitIds.length} of the most relevant units`}
              </div>
              <div style={{ marginTop: 6, maxHeight: 140, overflowY: "auto" }} className="ll-scroll">
                {plan.selectedUnitLabels.slice(0, 40).map((label, i) => (
                  <div key={i} style={{ fontSize: 12, color: COLOR.textDim, padding: "2px 0" }}>
                    · {label}
                  </div>
                ))}
              </div>

              <Label style={{ marginTop: 18 }}>role</Label>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <TermSelect value={roleOverride} options={ROLES} onChange={setRoleOverride} width={280} />
                {plan.roleAmbiguous ? <Pill color="amber">role ambiguous — flagged</Pill> : null}
              </div>

              <Label style={{ marginTop: 18 }}>estimate</Label>
              <div style={{ fontSize: 13, color: COLOR.text }}>~{plan.confirmation.estimatedInputTokens.toLocaleString()} input tokens</div>

              <Label style={{ marginTop: 18 }}>external AI consent</Label>
              {plan.confirmation.externalAiConsent.map((consent, i) => (
                <label key={i} style={{ display: "flex", alignItems: "flex-start", gap: 10, marginTop: 6, cursor: "pointer" }}>
                  <span
                    style={{ fontFamily: FONT_MONO, color: consentTicked[i] ? COLOR.amber : COLOR.textFaint, fontSize: 15 }}
                    onClick={() => setConsentTicked((prev) => prev.map((v, j) => (j === i ? !v : v)))}
                  >
                    {consentTicked[i] ? "▣" : "▢"}
                  </span>
                  <span style={{ fontSize: 12, color: COLOR.text }} onClick={() => setConsentTicked((prev) => prev.map((v, j) => (j === i ? !v : v)))}>
                    <b>{consent.stage}</b> — {consent.reason ?? consent.kind}
                    {consent.provider ? <Faint style={{ fontSize: 11 }}> ({consent.provider})</Faint> : null}
                  </span>
                </label>
              ))}

              {error ? <div style={{ marginTop: 12, color: COLOR.red, fontSize: 12 }}>{error}</div> : null}
            </div>
          ) : null}
        </div>

        <div style={footerStyle}>
          {phase === "confirm" ? (
            <button style={ghostBtn} onClick={() => setPhase("compose")}>
              ← back
            </button>
          ) : null}
          <span style={{ flex: 1 }} />
          <Faint style={{ fontSize: 11 }}>one confirmation — import + inventory + synthesis run after this</Faint>
          {phase === "compose" ? (
            <button
              style={{ ...primaryBtn, opacity: busy || !source.trim() || !subjectId ? 0.5 : 1, cursor: busy ? "default" : "pointer" }}
              disabled={busy || !source.trim() || !subjectId}
              onClick={() => void runPlan()}
            >
              {busy ? "…" : "Analyze →"}
            </button>
          ) : (
            <button
              style={{ ...primaryBtn, opacity: busy || !allConsented ? 0.5 : 1, cursor: busy || !allConsented ? "default" : "pointer" }}
              disabled={busy || !allConsented}
              onClick={() => void confirmBuild()}
            >
              {busy ? "building…" : "Confirm & build"}
            </button>
          )}
        </div>
      </div>

      {briefOpen ? (
        <StudyMapBriefWizard
          initialBrief={brief}
          submitLabel="Use brief"
          onClose={() => setBriefOpen(false)}
          onSubmit={(b) => {
            setBrief(b);
            setBriefOpen(false);
          }}
        />
      ) : null}
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
