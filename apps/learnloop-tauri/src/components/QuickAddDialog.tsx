// Quick add (§1): paste one source → auto-selected units, suggested role, default
// brief, and ONE confirmation (token estimate + external-AI consent), then a
// priority build batch. compose → confirm. The confirm phase is the single
// consent checkpoint; import/inventory/synthesis run after it.

import { useEffect, useRef, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type { CommandError, QuickAddPlanDto, StudyMapBriefDto } from "../api/dto";
import { StudyMapBriefWizard } from "./StudyMapBriefWizard";
import { COLOR, Faint, FONT_MONO, Pill, TermCheckbox, TermSelect } from "./term";
import { PageRangeSelector, pageSelectionError } from "./PageRangeSelector";
import { useSourceFileDrop } from "./useSourceFileDrop";
import { AsciiLoadingBar } from "./AsciiLoadingBar";

const ROLES = ["primary_textbook", "lecture", "paper", "reference", "alternate_explanation"];
const RECOMMENDED_INVENTORY_OUTPUT_TOKENS = 12_000;

export function QuickAddDialog({
  subjects,
  defaultSubjectId,
  defaultSource,
  defaultPageSelection,
  defaultBrief,
  guided = false,
  onClose,
  onEnqueued
}: {
  subjects: { id: string; title: string }[];
  defaultSubjectId?: string | null;
  // Optional prefilled source (URL / path). The NewVault wizard passes the
  // learner's first source so the bootstrap opens ready to analyze.
  defaultSource?: string | null;
  defaultPageSelection?: string | null;
  // Optional starting brief (e.g. the NewVault wizard's startingLevel) shown in
  // the brief wizard and sent with the plan/confirm calls until edited.
  defaultBrief?: StudyMapBriefDto | null;
  guided?: boolean;
  onClose: () => void;
  onEnqueued: (batchId: string) => void;
}) {
  const [phase, setPhase] = useState<"compose" | "confirm">("compose");
  const [source, setSource] = useState(defaultSource ?? "");
  const [subjectId, setSubjectId] = useState(defaultSubjectId ?? subjects[0]?.id ?? "");
  const [brief, setBrief] = useState<StudyMapBriefDto | undefined>(defaultBrief ?? undefined);
  const [briefOpen, setBriefOpen] = useState(false);
  const [plan, setPlan] = useState<QuickAddPlanDto | null>(null);
  const [roleOverride, setRoleOverride] = useState<string>("");
  const [consentTicked, setConsentTicked] = useState<boolean[]>([]);
  const [busy, setBusy] = useState(false);
  const [needsImport, setNeedsImport] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pageSelection, setPageSelection] = useState(defaultPageSelection ?? "");
  const [inventoryOutputTokens, setInventoryOutputTokens] = useState(RECOMMENDED_INVENTORY_OUTPUT_TOKENS);
  const [unlimitedTokenBudget, setUnlimitedTokenBudget] = useState(false);
  const [rangeImported, setRangeImported] = useState(false);
  // Per-source reader participation (owner choice at ingest setup). Practice
  // exams and similar assessment material opt out of the question/ask loop.
  const [readerEnabled, setReaderEnabled] = useState(true);
  const [importProgress, setImportProgress] = useState<{ status: "queued" | "running" | "completed"; message: string } | null>(null);
  const mountedRef = useRef(true);
  const fileDragging = useSourceFileDrop({
    enabled: phase === "compose" && !briefOpen && !busy,
    priority: 110,
    onDrop: (paths) => {
      setSource(paths[0]);
      setRangeImported(false);
      setError(paths.length > 1 ? "Quick add accepts one source at a time; using the first dropped file." : null);
    }
  });

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !briefOpen) onClose();
    };
    window.addEventListener("keydown", handler, true);
    return () => window.removeEventListener("keydown", handler, true);
  }, [onClose, briefOpen]);

  const asCommandError = (err: unknown): CommandError | null =>
    err && typeof err === "object" && "code" in err ? (err as CommandError) : null;

  // Reader-first seeding: when this source joins the reading loop, bootstrap
  // authors the study map WITHOUT practice items — they accrue as sections are
  // read. Reader-off sources keep upfront authoring (no reader to seed from).
  const effectiveBrief = (): StudyMapBriefDto => ({
    ...(brief ?? {}),
    practiceItems: brief?.practiceItems ?? (readerEnabled ? "as_you_read" : "upfront")
  });

  const runPlan = async (rangeIsCurrent = false) => {
    setBusy(true);
    setError(null);
    setNeedsImport(false);
    if (pageSelection.trim() && !rangeImported && !rangeIsCurrent) {
      setNeedsImport(true);
      setBusy(false);
      return;
    }
    try {
      const res = await api.planQuickAdd({ source: source.trim(), subjectId, brief: effectiveBrief() });
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
    setImportProgress({ status: "queued", message: "Import accepted; assigning the extraction worker…" });
    try {
      const batch = await api.startImportBatch({
        sources: [source.trim()],
        subjectId,
        pages: pageSelection.trim() || undefined
      });
      while (mountedRef.current) {
        const current = await api.getIngestBatch(batch.id);
        if (!mountedRef.current) return;
        const activeJob = current.jobs.find((job) => job.status === "running")
          ?? current.jobs.find((job) => job.status === "queued" || job.status === "waiting_for_input");
        const progressStatus = current.status === "running" ? "running" : "queued";
        setImportProgress({
          status: progressStatus,
          message: progressStatus === "running"
            ? activeJob?.message || activeJob?.phase || "Extraction worker is processing the source."
            : "Import queued; assigning the extraction worker…"
        });
        if (current.status === "failed" || current.status === "blocked" || current.status === "cancelled") {
          const failed = current.jobs.find((job) => job.error);
          setError(failed?.error?.message ?? "The selected pages could not be imported.");
          setImportProgress(null);
          setBusy(false);
          return;
        }
        if (current.status === "completed") {
          setNeedsImport(false);
          setRangeImported(true);
          setImportProgress({ status: "completed", message: "Import complete; preparing the study-map plan…" });
          await runPlan(true);
          if (mountedRef.current) setImportProgress(null);
          return;
        }
        await new Promise((resolve) => window.setTimeout(resolve, 1000));
      }
    } catch (err: unknown) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : String(err));
        setImportProgress(null);
        setBusy(false);
      }
    }
  };

  const confirmBuild = async () => {
    if (!plan) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.confirmQuickAdd({
        source: source.trim(),
        subjectId,
        brief: effectiveBrief(),
        roleOverride,
        inventoryOutputTokens,
        unlimitedTokenBudget,
        readerEnabled
      });
      onEnqueued(res.quickAdd.batchId);
      onClose();
    } catch (err: unknown) {
      const command = asCommandError(err);
      setError(command?.message ?? (err instanceof Error ? err.message : String(err)));
      setBusy(false);
    }
  };

  const allConsented = consentTicked.every(Boolean);
  const budgetValid = unlimitedTokenBudget || (inventoryOutputTokens >= 1_000 && inventoryOutputTokens <= 100_000);

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
          {guided ? (
            <div style={{ marginBottom: 16, border: `1px solid ${COLOR.cyan}`, background: "#101d22", padding: "11px 13px", fontSize: 11, lineHeight: 1.65 }}>
              <div style={{ color: COLOR.cyan, fontFamily: FONT_MONO, marginBottom: 3 }}>NEW VAULT SETUP · GUIDED INGEST</div>
              <span style={{ color: phase === "compose" ? COLOR.amber : COLOR.green }}>01 source + pages</span>
              <Faint> → </Faint>
              <span style={{ color: phase === "compose" ? COLOR.amber : COLOR.green }}>02 inventory budget</span>
              <Faint> → </Faint>
              <span style={{ color: phase === "confirm" ? COLOR.amber : COLOR.textFaint }}>03 review + build</span>
              <div style={{ color: COLOR.textDim, marginTop: 4 }}>
                Choose the exact source scope and enough output room for detailed textbook inventories. You can adjust the budget without editing the vault configuration.
              </div>
            </div>
          ) : null}
          {phase === "compose" ? (
            <div>
              <Label>source</Label>
              <div style={{ border: `1px solid ${source.trim() ? COLOR.amber : COLOR.border}`, background: COLOR.bgInput, padding: "9px 12px 9px 30px", position: "relative" }}>
                <span style={{ position: "absolute", left: 12, top: 9, color: COLOR.amber, fontWeight: 700 }}>❯</span>
                <input
                  value={source}
                  onChange={(e) => {
                    setSource(e.target.value);
                    setRangeImported(false);
                  }}
                  onKeyDown={(e) => e.stopPropagation()}
                  placeholder="paste a URL, arXiv id, PDF path, or .md/.txt/.vtt/.srt"
                  style={{ width: "100%", background: "transparent", color: COLOR.text, border: "none", outline: "none", fontFamily: FONT_MONO, fontSize: 13 }}
                />
              </div>

              <div style={{
                marginTop: 10,
                padding: "8px 10px",
                border: `1px dashed ${fileDragging ? COLOR.amber : COLOR.border}`,
                background: fileDragging ? "#241d12" : "transparent",
                color: fileDragging ? COLOR.amber : COLOR.textFaint,
                fontSize: 11
              }}>
                {fileDragging ? "drop to use this source" : "or drop a PDF, Markdown, text, HTML, or transcript (.vtt/.srt) file"}
              </div>

              <div style={{ marginTop: 14 }}>
                <PageRangeSelector
                  value={pageSelection}
                  onChange={(value) => {
                    setPageSelection(value);
                    setRangeImported(false);
                  }}
                  disabled={busy}
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

              <Label style={{ marginTop: 18 }}>inventory output budget · per unit</Label>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <input
                  type="number"
                  min={1000}
                  max={100000}
                  step={1000}
                  value={inventoryOutputTokens}
                  onChange={(e) => setInventoryOutputTokens(Number(e.target.value))}
                  disabled={busy || unlimitedTokenBudget}
                  style={{ width: 130, background: COLOR.bgInput, color: unlimitedTokenBudget ? COLOR.textFaint : budgetValid ? COLOR.text : COLOR.red, border: `1px solid ${budgetValid ? COLOR.border : COLOR.red}`, padding: "7px 9px", fontFamily: FONT_MONO, fontSize: 12, opacity: unlimitedTokenBudget ? 0.55 : 1 }}
                />
                <Faint style={{ fontSize: 11 }}>tokens · 12,000 recommended for large textbook sections</Faint>
              </div>
              <TermCheckbox
                checked={unlimitedTokenBudget}
                onChange={setUnlimitedTokenBudget}
                disabled={busy}
                label="no LearnLoop token ceiling"
                style={{ marginTop: 7 }}
              />
              {unlimitedTokenBudget ? (
                <Faint style={{ display: "block", marginTop: 4, fontSize: 10 }}>provider limits and context-window sharding still apply</Faint>
              ) : !budgetValid ? (
                <div style={{ marginTop: 5, color: COLOR.red, fontSize: 11 }}>Use 1,000–100,000 tokens per selected unit.</div>
              ) : null}

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
                {brief ? (
                  <Faint style={{ fontSize: 12 }}>
                    brief: {brief.outcome ?? "general_learning"} · {brief.depth ?? "standard"}
                    {brief.startingLevel ? ` · ${brief.startingLevel.replace(/_/g, " ")}` : ""}
                  </Faint>
                ) : (
                  <Faint style={{ fontSize: 12 }}>default brief will be used</Faint>
                )}
              </div>

              <div style={{ marginTop: 14, display: "flex", alignItems: "center", gap: 10 }}>
                <span
                  onClick={() => setReaderEnabled((v) => !v)}
                  style={{
                    cursor: "pointer",
                    fontFamily: FONT_MONO,
                    fontSize: 11,
                    padding: "3px 10px",
                    border: `1px solid ${readerEnabled ? COLOR.green : COLOR.border}`,
                    color: readerEnabled ? COLOR.green : COLOR.textFaint
                  }}
                >
                  {readerEnabled ? "▣ reader on" : "▢ reader off"}
                </span>
                <Faint style={{ fontSize: 11 }}>
                  {readerEnabled
                    ? "this source joins the reading loop (highlights, span-grounded Ask)"
                    : "kept out of the reader — right for practice exams and other assessment material"}
                </Faint>
              </div>

              {needsImport ? (
                <div style={{ marginTop: 16, border: `1px solid ${COLOR.borderStrong}`, background: COLOR.bgInput, padding: "10px 14px" }}>
                  <Faint style={{ fontSize: 12 }}>
                    {pageSelection.trim()
                      ? "Import + extract the selected PDF pages first, then quick-add continues."
                      : "This source has not been imported yet. Import + extract first, then quick-add continues."}
                  </Faint>
                  {busy && importProgress ? (
                    <div style={{ marginTop: 10 }}>
                      {importProgress.status === "running" ? <AsciiLoadingBar /> : null}
                      <div style={{ fontFamily: FONT_MONO, fontSize: 11, marginTop: 6 }}>
                        <span style={{ color: importProgress.status === "completed" ? COLOR.green : importProgress.status === "running" ? COLOR.cyan : COLOR.amber }}>
                          {importProgress.status.toUpperCase()}
                        </span>
                        <Faint> · {importProgress.message}</Faint>
                      </div>
                    </div>
                  ) : null}
                  <div style={{ marginTop: 8 }}>
                    <button style={{ ...primaryBtn, opacity: busy ? 0.5 : 1 }} disabled={busy} onClick={() => void importThenPlan()}>
                      {busy ? "importing…" : pageSelection.trim() ? "Import selected pages" : "Import first"}
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
              <div style={{ marginTop: 4, fontSize: 12, color: COLOR.textDim }}>
                inventory output ceiling: <span style={{ color: COLOR.amber }}>{unlimitedTokenBudget ? "none" : inventoryOutputTokens.toLocaleString()}</span>{unlimitedTokenBudget ? "" : " tokens per unit"}
              </div>

              {effectiveBrief().practiceItems === "as_you_read" ? (
                <div style={{ marginTop: 14, border: `1px solid ${COLOR.border}`, padding: "9px 12px", fontSize: 12, color: COLOR.textDim, lineHeight: 1.6 }}>
                  <span style={{ color: COLOR.amber }}>reader-first:</span> this build creates the study map
                  (concepts, facets, learning objects) with <b>no upfront practice items</b> — questions appear
                  in the reader per section, and practice items build themselves as you complete sections.
                </div>
              ) : null}

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
              style={{
                ...primaryBtn,
                opacity: busy || !source.trim() || !subjectId || !budgetValid || pageSelectionError(pageSelection) !== null ? 0.5 : 1,
                cursor: busy || pageSelectionError(pageSelection) !== null ? "default" : "pointer"
              }}
              disabled={busy || !source.trim() || !subjectId || !budgetValid || pageSelectionError(pageSelection) !== null}
              onClick={() => void runPlan()}
            >
              {busy ? "…" : "Analyze →"}
            </button>
          ) : (
            <button
              style={{ ...primaryBtn, opacity: busy || !allConsented || !budgetValid ? 0.5 : 1, cursor: busy || !allConsented || !budgetValid ? "default" : "pointer" }}
              disabled={busy || !allConsented || !budgetValid}
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
