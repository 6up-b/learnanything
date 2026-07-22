// New-vault creation is intentionally short. Once the vault exists, onboarding
// continues in the real Ingest/Quick Add surface so setup and everyday source
// ingestion cannot drift into two subtly different workflows.
//
// Steps: 1 Vault (dir + optional first subject → create) · 2 First source
// (classify + hand off to the ingest study-map build via QuickAddDialog) ·
// 3 Proposals (nothing enters the vault without review) · 4 Goal (optional,
// embeds GoalWizard) · 5 The loop (orientation reference card).
//
// The wizard owns its own state across steps. It never reimplements ingestion:
// the bootstrap reuses QuickAddDialog (durable v2 build → proposals); the
// proposals/goal steps route into the real tabs.

import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import { api } from "../api/client";
import type { CommandError, StartingLevel } from "../api/dto";
import type { TopTab } from "./ui";
import { COLOR, Faint, FONT_MONO } from "./term";
import { GoalWizard } from "./GoalWizard";
import { QuickAddDialog } from "./QuickAddDialog";
import { STARTING_LEVELS } from "./StudyMapBriefWizard";
import { PageRangeSelector, pageSelectionError } from "./PageRangeSelector";
import { useSourceFileDrop } from "./useSourceFileDrop";

const STEP_LABELS = ["vault"];

function kebabCase(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

export function NewVaultWizard({
  onClose,
  onActivateVault,
  onContinueInIngest,
  onGotoTab,
  onToast,
  onError
}: {
  onClose: () => void;
  // Re-select + re-load the vault at `path` so the whole app rebinds to it
  // (App.changeVault). Resolves once the switch is complete.
  onActivateVault: (path: string) => Promise<void>;
  onContinueInIngest: (subjectId: string | null) => void;
  onGotoTab: (tab: TopTab) => void;
  onToast: (message: string) => void;
  onError: (message: string) => void;
}) {
  const [step, setStep] = useState(0);

  // step 1 — vault
  const [path, setPath] = useState("");
  const [subjectTitle, setSubjectTitle] = useState("");
  const [startingLevel, setStartingLevel] = useState<StartingLevel | null>(null);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [vaultReady, setVaultReady] = useState(false);
  const [vaultRoot, setVaultRoot] = useState<string | null>(null);

  // subjects known to the (now active) vault — used by the bootstrap handoff
  const [subjects, setSubjects] = useState<string[]>([]);
  const [firstSubjectId, setFirstSubjectId] = useState<string | null>(null);

  // step 2 — first source
  const [source, setSource] = useState("");
  const [pageSelection, setPageSelection] = useState("");
  const [dropNote, setDropNote] = useState<string | null>(null);
  const [kind, setKind] = useState<string | null>(null);
  const [classifying, setClassifying] = useState(false);
  const [bootstrapSubject, setBootstrapSubject] = useState<string | null>(null);
  const [newSubjectTitle, setNewSubjectTitle] = useState("");
  const [addingSubject, setAddingSubject] = useState(false);
  const [quickAddOpen, setQuickAddOpen] = useState(false);
  const [bootstrapBatchId, setBootstrapBatchId] = useState<string | null>(null);
  const [buildRunning, setBuildRunning] = useState(false);

  // step 4 — goal (declared before the drop hook because nested overlays pause it)
  const [goalWizardOpen, setGoalWizardOpen] = useState(false);
  const [goalCreated, setGoalCreated] = useState(false);

  const fileDragging = useSourceFileDrop({
    enabled: step === 1 && !quickAddOpen && !goalWizardOpen,
    priority: 100,
    onDrop: (paths) => {
      setSource(paths[0]);
      setDropNote(paths.length > 1 ? `Using ${paths[0]}; the first-source wizard accepts one file at a time.` : null);
    }
  });

  // step 3 — proposals
  const [pendingCount, setPendingCount] = useState<number | null>(null);

  const asCommandError = (err: unknown): string =>
    err && typeof err === "object" && "message" in err
      ? String((err as CommandError).message)
      : err instanceof Error
        ? err.message
        : String(err);

  // Load the fresh vault's subjects once it is active.
  async function refreshSubjects() {
    try {
      const snap = await api.loadVault();
      const list = snap.vault?.subjects ?? [];
      setSubjects(list);
      setBootstrapSubject((current) => current ?? firstSubjectId ?? list[0] ?? null);
    } catch {
      // vault still switching — the shell surfaces load errors
    }
  }

  async function createVault() {
    if (creating) return;
    const trimmed = path.trim();
    if (!trimmed) {
      setCreateError("Choose a directory for the vault.");
      return;
    }
    setCreating(true);
    setCreateError(null);
    try {
      const result = await api.createVault({
        path: trimmed,
        subject: subjectTitle.trim() || null,
        startingLevel
      });
      setVaultRoot(result.vaultRoot);
      setFirstSubjectId(result.subjectId);
      // Rebind the whole app to the new vault before running any further RPCs.
      await onActivateVault(result.vaultRoot);
      await refreshSubjects();
      setVaultReady(true);
      onContinueInIngest(result.subjectId);
      onClose();
    } catch (err) {
      setCreateError(asCommandError(err));
    } finally {
      setCreating(false);
    }
  }

  async function browseForDirectory() {
    try {
      const selected = await openDialog({ directory: true, multiple: false });
      if (typeof selected === "string") {
        setPath(selected);
        setCreateError(null);
      }
    } catch (err) {
      setCreateError(asCommandError(err));
    }
  }

  async function addSubject() {
    const title = newSubjectTitle.trim();
    if (!title || addingSubject) return;
    const id = kebabCase(title);
    if (!id) return;
    setAddingSubject(true);
    try {
      const res = await api.runCliCommand(["add-subject", id, title]);
      if (res.exitCode !== 0) {
        onError(res.stderr.trim() || `add-subject failed (exit ${res.exitCode})`);
        return;
      }
      await refreshSubjects();
      setBootstrapSubject(id);
      setNewSubjectTitle("");
    } catch (err) {
      onError(asCommandError(err));
    } finally {
      setAddingSubject(false);
    }
  }

  // Debounced source classification (reuses the real ingest classifier).
  useEffect(() => {
    const candidate = source.trim();
    if (!candidate) {
      setKind(null);
      setClassifying(false);
      return;
    }
    let cancelled = false;
    setClassifying(true);
    const handle = window.setTimeout(() => {
      api
        .classifyIngestSource(candidate)
        .then((res) => {
          if (!cancelled) setKind(res.kind);
        })
        .catch(() => {
          if (!cancelled) setKind(null);
        })
        .finally(() => {
          if (!cancelled) setClassifying(false);
        });
    }, 350);
    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, [source]);

  // Poll proposals + build status while the wizard sits on/after the bootstrap.
  useEffect(() => {
    if (!vaultReady || (step !== 1 && step !== 2)) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const snap = await api.getProposals();
        if (!cancelled) setPendingCount(snap.totals.pending);
      } catch {
        /* ignore transient */
      }
      if (bootstrapBatchId) {
        try {
          const batch = await api.getIngestBatch(bootstrapBatchId);
          if (!cancelled) setBuildRunning(batch.status === "running" || batch.status === "queued");
        } catch {
          /* ignore */
        }
      }
    };
    void tick();
    const id = window.setInterval(() => void tick(), 2500);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [vaultReady, step, bootstrapBatchId]);

  const stepValid = useMemo(() => {
    if (step === 0) return vaultReady || path.trim().length > 0;
    return true;
  }, [step, vaultReady, path]);

  const advance = () => {
    if (goalWizardOpen || quickAddOpen) return;
    if (step === 0) {
      if (!vaultReady) void createVault();
      else setStep(1);
      return;
    }
    if (step < STEP_LABELS.length - 1) {
      setStep((s) => s + 1);
    } else {
      finish();
    }
  };

  function finish() {
    onToast(
      buildRunning
        ? "Vault ready — your study map is still building in Ingest."
        : "Vault ready. Begin a session from Start when you are."
    );
    onGotoTab(buildRunning ? "ingest" : "today");
    onClose();
  }

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (goalWizardOpen || quickAddOpen) return; // nested overlays own the keyboard
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
  }, [step, vaultReady, goalWizardOpen, quickAddOpen, buildRunning, path, subjectTitle, creating]);

  const primaryLabel = (() => {
    if (step === 0) return vaultReady ? "next →" : creating ? "creating…" : "create vault ↵";
    if (step === STEP_LABELS.length - 1) return "finish ↵";
    return "next →";
  })();

  return (
    <div style={backdropStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        <div style={headerStyle}>
          <span style={{ color: COLOR.amber, fontWeight: 700 }}>❯</span>
          <span style={{ color: COLOR.text, fontSize: 13 }}>
            new <span style={{ color: COLOR.amber }}>vault</span>
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
            <StepVault
              path={path}
              onPath={setPath}
              onBrowse={browseForDirectory}
              subjectTitle={subjectTitle}
              onSubjectTitle={setSubjectTitle}
              startingLevel={startingLevel}
              onStartingLevel={setStartingLevel}
              vaultReady={vaultReady}
              vaultRoot={vaultRoot}
              createError={createError}
            />
          ) : step === 1 ? (
            <StepFirstSource
              source={source}
              onSource={(value) => {
                setSource(value);
                setDropNote(null);
              }}
              pageSelection={pageSelection}
              onPageSelection={setPageSelection}
              fileDragging={fileDragging}
              dropNote={dropNote}
              kind={kind}
              classifying={classifying}
              subjects={subjects}
              bootstrapSubject={bootstrapSubject}
              onBootstrapSubject={setBootstrapSubject}
              newSubjectTitle={newSubjectTitle}
              onNewSubjectTitle={setNewSubjectTitle}
              addingSubject={addingSubject}
              onAddSubject={addSubject}
              bootstrapBatchId={bootstrapBatchId}
              buildRunning={buildRunning}
              onOpenBootstrap={() => setQuickAddOpen(true)}
            />
          ) : step === 2 ? (
            <StepProposals
              pendingCount={pendingCount}
              bootstrapStarted={bootstrapBatchId !== null}
              buildRunning={buildRunning}
              onGoToProposals={() => {
                onGotoTab("proposals");
                onClose();
              }}
            />
          ) : step === 3 ? (
            <StepGoal goalCreated={goalCreated} onOpenGoalWizard={() => setGoalWizardOpen(true)} />
          ) : (
            <StepLoop />
          )}
        </div>

        <div style={footerStyle}>
          {step > 0 ? (
            <button type="button" onClick={() => setStep((s) => s - 1)} style={ghostBtn}>
              ← back
            </button>
          ) : (
            <span />
          )}
          <span style={{ flex: 1 }} />
          <Faint style={{ fontSize: 11 }}>
            {step === STEP_LABELS.length - 1 ? "enter finish · esc cancel" : "enter next · esc cancel"}
          </Faint>
          <button
            type="button"
            onClick={advance}
            disabled={!stepValid || creating}
            style={{
              ...primaryBtn,
              opacity: !stepValid || creating ? 0.4 : 1,
              cursor: !stepValid || creating ? "default" : "pointer"
            }}
          >
            {primaryLabel}
          </button>
        </div>
      </div>

      {quickAddOpen ? (
        <QuickAddDialog
          subjects={subjects.map((s) => ({ id: s, title: s }))}
          defaultSubjectId={bootstrapSubject}
          defaultSource={source}
          defaultPageSelection={pageSelection}
          defaultBrief={startingLevel ? { startingLevel } : null}
          onClose={() => setQuickAddOpen(false)}
          onEnqueued={(batchId) => {
            setBootstrapBatchId(batchId);
            setBuildRunning(true);
            setQuickAddOpen(false);
            setStep(2);
          }}
        />
      ) : null}

      {goalWizardOpen ? (
        <GoalWizard
          onClose={() => setGoalWizardOpen(false)}
          onCreated={() => {
            setGoalCreated(true);
            setGoalWizardOpen(false);
          }}
          onError={onError}
        />
      ) : null}
    </div>
  );
}

// ── step 1: vault ────────────────────────────────────────────────────────────
function StepVault({
  path,
  onPath,
  onBrowse,
  subjectTitle,
  onSubjectTitle,
  startingLevel,
  onStartingLevel,
  vaultReady,
  vaultRoot,
  createError
}: {
  path: string;
  onPath: (v: string) => void;
  onBrowse: () => void;
  subjectTitle: string;
  onSubjectTitle: (v: string) => void;
  startingLevel: StartingLevel | null;
  onStartingLevel: (v: StartingLevel | null) => void;
  vaultReady: boolean;
  vaultRoot: string | null;
  createError: string | null;
}) {
  return (
    <div>
      <Prose>
        A <b>vault</b> is a folder LearnLoop owns: your concepts, evidence, practice items, and the SQLite
        state behind them. Pick an empty directory (or an existing vault to reopen).
      </Prose>

      <Label style={{ marginTop: 18 }}>vault directory</Label>
      <div style={{ display: "flex", gap: 10 }}>
        <input
          value={path}
          onChange={(e) => onPath(e.target.value)}
          placeholder="/home/you/learnloop-vault"
          style={{ ...inputStyle, flex: 1 }}
          autoFocus
          disabled={vaultReady}
        />
        <button type="button" onClick={onBrowse} style={ghostBtn} disabled={vaultReady}>
          browse…
        </button>
      </div>

      <Label style={{ marginTop: 20 }}>first subject — optional</Label>
      <input
        value={subjectTitle}
        onChange={(e) => onSubjectTitle(e.target.value)}
        placeholder="e.g. Linear Algebra"
        style={inputStyle}
        disabled={vaultReady}
      />
      <div style={{ marginTop: 6, fontSize: 12, color: COLOR.textFaint, lineHeight: 1.5 }}>
        Seeds one subject so your first source has somewhere to land. You can add more later, or skip this
        and create a subject on the next step.
      </div>

      <Label style={{ marginTop: 20 }}>where are you starting from — optional</Label>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {STARTING_LEVELS.map((s) => (
          <button
            key={s.id}
            type="button"
            disabled={vaultReady}
            onClick={() => onStartingLevel(startingLevel === s.id ? null : s.id)}
            style={{
              padding: "6px 14px",
              fontFamily: FONT_MONO,
              fontSize: 12,
              cursor: vaultReady ? "default" : "pointer",
              border: `1px solid ${startingLevel === s.id ? COLOR.amber : COLOR.borderStrong}`,
              background: startingLevel === s.id ? "#241d12" : "transparent",
              color: startingLevel === s.id ? COLOR.amber : COLOR.textDim
            }}
          >
            {s.label}
          </button>
        ))}
      </div>
      <div style={{ marginTop: 6, fontSize: 12, color: COLOR.textFaint, lineHeight: 1.5 }}>
        Your honest starting point for this vault's material. It calibrates how hard the first questions
        are — practice adapts from your actual answers after that. Change it anytime from the ingest screen.
      </div>

      {vaultReady && vaultRoot ? (
        <div style={okBox}>
          <span style={{ color: COLOR.green }}>✓ vault created</span> at{" "}
          <span style={{ fontFamily: FONT_MONO, color: COLOR.text }}>{vaultRoot}</span> — it is now the active vault.
        </div>
      ) : null}
      {createError ? <div style={{ marginTop: 12, fontSize: 12, color: COLOR.red }}>{createError}</div> : null}
    </div>
  );
}

// ── step 2: first source ─────────────────────────────────────────────────────
function StepFirstSource({
  source,
  onSource,
  pageSelection,
  onPageSelection,
  fileDragging,
  dropNote,
  kind,
  classifying,
  subjects,
  bootstrapSubject,
  onBootstrapSubject,
  newSubjectTitle,
  onNewSubjectTitle,
  addingSubject,
  onAddSubject,
  bootstrapBatchId,
  buildRunning,
  onOpenBootstrap
}: {
  source: string;
  onSource: (v: string) => void;
  pageSelection: string;
  onPageSelection: (v: string) => void;
  fileDragging: boolean;
  dropNote: string | null;
  kind: string | null;
  classifying: boolean;
  subjects: string[];
  bootstrapSubject: string | null;
  onBootstrapSubject: (v: string | null) => void;
  newSubjectTitle: string;
  onNewSubjectTitle: (v: string) => void;
  addingSubject: boolean;
  onAddSubject: () => void;
  bootstrapBatchId: string | null;
  buildRunning: boolean;
  onOpenBootstrap: () => void;
}) {
  const hasSubject = bootstrapSubject !== null && subjects.includes(bootstrapSubject);
  const canBootstrap = source.trim().length > 0 && hasSubject && pageSelectionError(pageSelection) === null;
  return (
    <div>
      <Prose>
        LearnLoop learns from <b>canonical sources</b> — a textbook chapter, lecture notes, an article, a
        YouTube lecture. Point it at your first one and it will extract the structure, then propose a study
        map: concepts, evidence facets, and practice items, each citing the exact passage it came from.
      </Prose>

      <Label style={{ marginTop: 18 }}>first source</Label>
      <div style={{ border: `1px solid ${source.trim() ? COLOR.amber : COLOR.border}`, background: COLOR.bgInput, padding: "9px 12px 9px 30px", position: "relative" }}>
        <span style={{ position: "absolute", left: 12, top: 9, color: COLOR.amber, fontWeight: 700 }}>❯</span>
        <input
          value={source}
          onChange={(e) => onSource(e.target.value)}
          placeholder="paste a URL, arXiv id, PDF path, YouTube link, or .md / .txt / .vtt / .srt path"
          style={{ width: "100%", background: "transparent", color: COLOR.text, border: "none", outline: "none", fontFamily: FONT_MONO, fontSize: 13 }}
          autoFocus
        />
      </div>
      <div style={{ marginTop: 6, fontSize: 12, color: COLOR.textFaint }}>
        {source.trim()
          ? classifying
            ? "checking with the ingest classifier…"
            : kind
              ? <>detected: <span style={{ color: COLOR.cyan }}>{kind}</span></>
              : "unsupported or unresolved source"
          : "paste a source above"}
      </div>

      <div
        style={{
          marginTop: 10,
          padding: "9px 12px",
          border: `1px dashed ${fileDragging ? COLOR.amber : COLOR.border}`,
          background: fileDragging ? "#241d12" : "transparent",
          color: fileDragging ? COLOR.amber : COLOR.textFaint,
          fontSize: 12
        }}
      >
        {fileDragging ? "drop to use this source" : "or drop a PDF, Markdown, text, HTML, or transcript (.vtt/.srt) file here"}
      </div>
      {dropNote ? <Faint style={{ display: "block", marginTop: 5, fontSize: 11 }}>{dropNote}</Faint> : null}

      <div style={{ marginTop: 14 }}>
        <PageRangeSelector
          value={pageSelection}
          onChange={onPageSelection}
        />
      </div>

      <Label style={{ marginTop: 20 }}>subject</Label>
      {subjects.length > 0 ? (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {subjects.map((s) => {
            const sel = s === bootstrapSubject;
            return (
              <span
                key={s}
                onClick={() => onBootstrapSubject(sel ? null : s)}
                style={{
                  padding: "4px 12px",
                  fontSize: 12,
                  fontFamily: FONT_MONO,
                  border: `1px solid ${sel ? COLOR.amber : COLOR.border}`,
                  background: sel ? "#241d12" : "transparent",
                  color: sel ? COLOR.amber : COLOR.text,
                  cursor: "pointer"
                }}
              >
                {s}
              </span>
            );
          })}
        </div>
      ) : (
        <Faint style={{ fontSize: 12 }}>no subjects yet — create one below.</Faint>
      )}
      <div style={{ display: "flex", gap: 8, marginTop: 8, alignItems: "center" }}>
        <input
          value={newSubjectTitle}
          onChange={(e) => onNewSubjectTitle(e.target.value)}
          placeholder="+ new subject title"
          style={{ ...inputStyle, width: 240 }}
        />
        <button
          type="button"
          onClick={onAddSubject}
          disabled={!newSubjectTitle.trim() || addingSubject}
          style={{ ...ghostBtn, opacity: !newSubjectTitle.trim() || addingSubject ? 0.4 : 1 }}
        >
          {addingSubject ? "adding…" : "add subject"}
        </button>
      </div>

      <div style={{ marginTop: 22 }}>
        <button
          type="button"
          onClick={onOpenBootstrap}
          disabled={!canBootstrap}
          style={{ ...primaryBtn, opacity: canBootstrap ? 1 : 0.4, cursor: canBootstrap ? "pointer" : "default" }}
        >
          build study map from this source →
        </button>
        {!hasSubject ? (
          <Faint style={{ fontSize: 11, marginLeft: 12 }}>pick or create a subject first</Faint>
        ) : null}
      </div>

      {bootstrapBatchId ? (
        <div style={okBox}>
          <span style={{ color: buildRunning ? COLOR.cyan : COLOR.green }}>
            {buildRunning ? "◐ study-map build running" : "✓ build enqueued"}
          </span>{" "}
          — extraction → outline → study-map build → proposals. You can move on; it continues in the
          background and lands on the Proposals screen for review.
        </div>
      ) : (
        <div style={{ marginTop: 18, padding: "12px 14px", border: `1px solid ${COLOR.border}`, background: COLOR.bgInput, fontSize: 12, color: COLOR.textDim, lineHeight: 1.6 }}>
          "Build study map" opens one confirmation (token estimate + external-AI consent), then runs the
          durable pipeline. Nothing enters the vault yet — everything it proposes is reviewed next.
        </div>
      )}
    </div>
  );
}

// ── step 3: proposals ────────────────────────────────────────────────────────
function StepProposals({
  pendingCount,
  bootstrapStarted,
  buildRunning,
  onGoToProposals
}: {
  pendingCount: number | null;
  bootstrapStarted: boolean;
  buildRunning: boolean;
  onGoToProposals: () => void;
}) {
  return (
    <div>
      <Prose>
        Nothing a model writes enters your vault directly. Every concept, facet, and practice item arrives as
        a <b>proposal</b> — you accept, edit, or reject it on the Proposals screen. This keeps the vault
        yours: the AI drafts, you decide.
      </Prose>

      <div style={{ marginTop: 18, padding: "14px 16px", border: `1px solid ${COLOR.border}`, background: COLOR.bgInput }}>
        {!bootstrapStarted ? (
          <Faint style={{ fontSize: 13 }}>
            No bootstrap build was started. You can import a source anytime from the Ingest tab, then review
            what it proposes here.
          </Faint>
        ) : pendingCount === null ? (
          <Faint style={{ fontSize: 13 }}>checking for proposals…</Faint>
        ) : pendingCount > 0 ? (
          <div style={{ fontSize: 13, color: COLOR.text }}>
            <span style={{ color: COLOR.amber, fontFamily: FONT_MONO, fontSize: 20 }}>{pendingCount}</span> item
            {pendingCount === 1 ? "" : "s"} awaiting review.
          </div>
        ) : buildRunning ? (
          <Faint style={{ fontSize: 13 }}>
            The build is still running — proposals will appear here as it finishes.
          </Faint>
        ) : (
          <Faint style={{ fontSize: 13 }}>No pending proposals yet.</Faint>
        )}
      </div>

      <div style={{ marginTop: 18 }}>
        <button type="button" onClick={onGoToProposals} style={primaryBtn}>
          go to proposals →
        </button>
        <Faint style={{ fontSize: 11, marginLeft: 12 }}>opens the Proposals tab (closes this wizard)</Faint>
      </div>
    </div>
  );
}

// ── step 4: goal (optional) ──────────────────────────────────────────────────
function StepGoal({ goalCreated, onOpenGoalWizard }: { goalCreated: boolean; onOpenGoalWizard: () => void }) {
  return (
    <div>
      <Prose>
        A <b>goal</b> is a target — a scope of concepts, a recall level, and (optionally) a deadline. It
        focuses the scheduler on what matters for an exam or milestone and unlocks a held-out practice exam.
        Entirely optional; you can create one anytime later.
      </Prose>

      <div style={{ marginTop: 20 }}>
        {goalCreated ? (
          <div style={okBox}>
            <span style={{ color: COLOR.green }}>✓ goal created</span> — it will appear on Today and drive the queue.
          </div>
        ) : (
          <button type="button" onClick={onOpenGoalWizard} style={primaryBtn}>
            create a goal →
          </button>
        )}
        <Faint style={{ fontSize: 11, marginLeft: 12 }}>or press next to skip</Faint>
      </div>
    </div>
  );
}

// ── step 5: the loop (orientation) ───────────────────────────────────────────
function StepLoop() {
  return (
    <div>
      <Prose>
        The average session is a short loop. Everything else is here when you need it.
      </Prose>

      <Label style={{ marginTop: 18 }}>the loop</Label>
      <div style={{ padding: "12px 14px", border: `1px solid ${COLOR.border}`, background: COLOR.bgInput, fontSize: 13, color: COLOR.textDim, lineHeight: 1.7 }}>
        <span style={{ color: COLOR.amber }}>Start</span> → set today's energy/time, begin a session ·{" "}
        <span style={{ color: COLOR.amber }}>Today</span> → work the queue: practice → feedback → next ·{" "}
        finish the session for a summary · <span style={{ color: COLOR.amber }}>Review</span> → the
        changelog of what you got wrong and working misconception hypotheses.
      </div>

      <Label style={{ marginTop: 18 }}>the tabs</Label>
      <div style={{ border: `1px solid ${COLOR.border}`, background: COLOR.bgInput, padding: "10px 14px" }}>
        <TabRow k="Today" v="the practice queue and your active session" />
        <TabRow k="Ingest" v="import canonical sources → build/extend the study map" />
        <TabRow k="Proposals" v="accept / edit / reject everything before it enters the vault" />
        <TabRow k="Library" v="the vault files, source library, and coverage" />
        <TabRow k="Graph" v="the concept graph and knowledge map" />
        <TabRow k="Registry" v="per-subject learning objects, facets, provenance" />
        <TabRow k="Review" v="mistakes, misconceptions, and repairs" />
        <TabRow k="Maintain" v="revision refresh, source conflicts, exam readiness" />
      </div>

      <Label style={{ marginTop: 18 }}>power commands · ^p palette or the learnloop CLI</Label>
      <div style={{ border: `1px solid ${COLOR.border}`, background: COLOR.bgInput, padding: "10px 14px" }}>
        <CmdRow k="show <id>" v="universal inspector — open any concept / item / attempt / error" />
        <CmdRow k="generate-practice" v="author practice items for thinly-covered learning objects" />
        <CmdRow k="populate-goal <goal>" v="fill a goal's scope with practice so day one isn't empty" />
        <CmdRow k="generate-diagnostics" v="seed diagnostic probes to locate misconceptions" />
        <CmdRow k="calibrate <goal>" v="batched diagnostic blocks over a goal's scope" />
        <CmdRow k="doctor" v="validate the vault, schemas, and runtime health" />
      </div>
      <Faint style={{ fontSize: 11, display: "block", marginTop: 10 }}>
        Open the palette anywhere with <b>^p</b> (or <b>:</b>). Type <b>help</b> for the full command list.
      </Faint>
    </div>
  );
}

function TabRow({ k, v }: { k: string; v: string }) {
  return (
    <div style={{ display: "flex", gap: 12, padding: "3px 0", fontSize: 13, lineHeight: 1.5 }}>
      <span style={{ color: COLOR.amber, fontFamily: FONT_MONO, width: 96, flexShrink: 0 }}>{k}</span>
      <span style={{ color: COLOR.textDim }}>{v}</span>
    </div>
  );
}

function CmdRow({ k, v }: { k: string; v: string }) {
  return (
    <div style={{ display: "flex", gap: 12, padding: "3px 0", fontSize: 13, lineHeight: 1.5 }}>
      <span style={{ color: COLOR.cyan, fontFamily: FONT_MONO, width: 168, flexShrink: 0 }}>{k}</span>
      <span style={{ color: COLOR.textDim }}>{v}</span>
    </div>
  );
}

function Prose({ children }: { children: ReactNode }) {
  return <div style={{ fontSize: 13, color: COLOR.textDim, lineHeight: 1.7 }}>{children}</div>;
}

function Label({ children, style = {} }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div style={{ fontSize: 11, color: COLOR.amber, textTransform: "uppercase", letterSpacing: "0.12em", fontFamily: FONT_MONO, marginBottom: 6, ...style }}>
      {children}
    </div>
  );
}

const okBox: CSSProperties = {
  marginTop: 18,
  padding: "12px 14px",
  border: `1px solid ${COLOR.borderStrong}`,
  background: COLOR.bgInput,
  fontSize: 13,
  color: COLOR.textDim,
  lineHeight: 1.6
};

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
  width: "min(720px, 100%)",
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
