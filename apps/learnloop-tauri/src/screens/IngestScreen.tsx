import { useCallback, useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import { api } from "../api/client";
import type { AcquisitionPreviewItem, CommandError, IngestJobDto, IngestJobPhase, IngestMode, PdfEngine, SourceLibraryCard, StartingLevel } from "../api/dto";
import { COLOR, Dim, Faint, FONT_MONO, KeyBar, Pill, SectionHeader, TermSelect, type PillColor } from "../components/term";
import { STARTING_LEVELS } from "../components/StudyMapBriefWizard";
import { IngestActivityStack } from "../components/IngestActivity";
import { SourceLibrarySidebar } from "../components/SourceLibrarySidebar";
import { OutlinePlanFlow } from "../components/OutlineAndPlan";
import { PageRangeSelector, pageSelectionError } from "../components/PageRangeSelector";
import { useSourceFileDrop } from "../components/useSourceFileDrop";
import { AsciiLoadingBar } from "../components/AsciiLoadingBar";

// Ingest screen — single merged surface over durable ingest v2 (§5.7/§6).
// One entry point: paste a source, canonical imports go through the durable
// batch queue (`start_import_batch` → fetch → extract → library card), then a
// manual "outline & select →" launches the authoring batch. Exam seeding still
// rides the legacy one-shot pipeline (`start_ingest`) until a v2 exam workflow
// exists. Left column is the source library; batch progress renders inline as
// Activity cards — there are no sub-tabs.

type Kind = "web" | "arxiv" | "pdf" | "youtube" | "local" | "audio";

// ── Source-kind detection (mirrors src/learnloop/services/source_ingestion.py) ──
function detectKind(source: string): Kind | null {
  const s = (source || "").trim();
  if (!s) return null;
  if (/^https?:\/\/([\w-]+\.)?arxiv\.org\//i.test(s) || /^arxiv:/i.test(s)) return "arxiv";
  if (/^\d{4}\.\d{4,5}(v\d+)?$/.test(s)) return "arxiv"; // bare id
  // Mirror resolution._YOUTUBE_HOSTS: youtube.com, www./m. subdomains, youtu.be.
  if (/^https?:\/\/([\w-]+\.)?(youtube\.com|youtu\.be)\//i.test(s)) return "youtube";
  if (/\.pdf(\?|$)/i.test(s)) return "pdf";
  if (/^https?:\/\//i.test(s)) return "web";
  if (/\.(mp3|wav|m4a|flac|ogg|oga|opus|aac)$/i.test(s)) return "audio";
  if (/\.(md|markdown|txt|vtt|srt)$/i.test(s)) return "local";
  return null;
}

type KindMeta = { color: PillColor; label: string; icon: string };

const KIND_META: Record<Kind, KindMeta> = {
  web: { color: "cyan", label: "web page", icon: "🌐" },
  arxiv: { color: "green", label: "arXiv paper", icon: "📄" },
  pdf: { color: "amber", label: "PDF", icon: "📕" },
  youtube: { color: "red", label: "YouTube transcript", icon: "▶" },
  local: { color: "purple", label: "local file", icon: "📁" },
  audio: { color: "pink", label: "audio file", icon: "🎙" }
};

type Mode = IngestMode;

function kebabCase(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

// ── Bordered card — thin border, matching the handoff design's Card ─────
function Card({ children, style = {} }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div
      style={{
        border: `1px solid ${COLOR.border}`,
        borderRadius: 2,
        padding: "14px 18px",
        background: "transparent",
        position: "relative",
        ...style
      }}
    >
      {children}
    </div>
  );
}

// ── Kind chips above input ──────────────────────────────────────────────
function KindChips({ active }: { active: Kind | null }) {
  const order: Kind[] = ["web", "arxiv", "pdf", "youtube", "local", "audio"];
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {order.map((k) => {
        const sel = k === active;
        const meta = KIND_META[k];
        return (
          <span
            key={k}
            style={{
              padding: "3px 10px",
              fontSize: 11,
              fontFamily: FONT_MONO,
              border: `1px solid ${sel ? COLOR.amber : COLOR.border}`,
              background: sel ? "#241d12" : "transparent",
              color: sel ? COLOR.amber : COLOR.textDim
            }}
          >
            <span style={{ marginRight: 6, opacity: 0.7 }}>{meta.icon}</span>
            {meta.label}
          </span>
        );
      })}
    </div>
  );
}

// ── Subject picker with inline "+ new subject" creation ─────────────────
// Persisted vault learner level (profile/learner.yaml). All synthesis inherits
// it as the brief's startingLevel; editing here replaces the global learner
// claim (existing mastery states are not retro-seeded).
function LearnerLevelChip() {
  const [level, setLevel] = useState<StartingLevel | null>(null);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let alive = true;
    api
      .getLearnerProfile()
      .then((profile) => {
        if (alive) setLevel(profile.startingLevel);
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, []);

  const pick = async (next: StartingLevel) => {
    if (saving) return;
    setSaving(true);
    try {
      const profile = await api.setLearnerProfile({ startingLevel: next });
      setLevel(profile.startingLevel);
      setOpen(false);
    } catch {
      // non-fatal; chip keeps its previous value
    } finally {
      setSaving(false);
    }
  };

  const label = STARTING_LEVELS.find((s) => s.id === level)?.label;
  return (
    <span style={{ position: "relative", display: "inline-flex" }}>
      <span
        onClick={() => setOpen((v) => !v)}
        title="your declared starting level for this vault — new study maps and generated questions calibrate to it"
        style={{
          padding: "4px 12px",
          fontSize: 12,
          fontFamily: FONT_MONO,
          border: `1px solid ${level ? COLOR.border : COLOR.borderStrong}`,
          color: level ? COLOR.textDim : COLOR.textFaint,
          cursor: "pointer",
          whiteSpace: "nowrap"
        }}
      >
        {label ? `level: ${label}` : "set your level"}
      </span>
      {open ? (
        <span
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            zIndex: 40,
            display: "flex",
            flexDirection: "column",
            background: COLOR.bg,
            border: `1px solid ${COLOR.borderStrong}`,
            boxShadow: "0 8px 30px rgba(0,0,0,0.5)"
          }}
        >
          {STARTING_LEVELS.map((s) => (
            <span
              key={s.id}
              onClick={() => void pick(s.id)}
              style={{
                padding: "6px 14px",
                fontSize: 12,
                fontFamily: FONT_MONO,
                whiteSpace: "nowrap",
                color: s.id === level ? COLOR.amber : COLOR.textDim,
                background: s.id === level ? "#241d12" : "transparent",
                cursor: "pointer"
              }}
            >
              {s.label}
            </span>
          ))}
        </span>
      ) : null}
    </span>
  );
}

function SubjectPicker({
  subjects,
  value,
  onChange,
  onCreate,
  creating
}: {
  subjects: string[];
  value: string | null;
  onChange: (subject: string | null) => void;
  onCreate: (title: string) => Promise<boolean>;
  creating: boolean;
}) {
  const [adding, setAdding] = useState(false);
  const [title, setTitle] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (adding) inputRef.current?.focus();
  }, [adding]);

  async function submit() {
    const trimmed = title.trim();
    if (!trimmed || creating) return;
    const created = await onCreate(trimmed);
    if (!created) return;
    setTitle("");
    setAdding(false);
  }

  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
      {subjects.map((s) => {
        const sel = s === value;
        return (
          <span
            key={s}
            onClick={() => onChange(sel ? null : s)}
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
      {adding ? (
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            padding: "3px 8px",
            border: `1px dashed ${COLOR.amber}`,
            background: COLOR.bgInput
          }}
        >
          <input
            ref={inputRef}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={(e) => {
              e.stopPropagation();
              if (e.key === "Enter") void submit();
              if (e.key === "Escape") {
                setTitle("");
                setAdding(false);
              }
            }}
            placeholder="subject title"
            style={{
              width: 140,
              background: "transparent",
              color: COLOR.text,
              border: "none",
              outline: "none",
              fontFamily: FONT_MONO,
              fontSize: 12
            }}
          />
          {title.trim() && <Faint style={{ fontSize: 10 }}>→ {kebabCase(title)}</Faint>}
          <span
            onClick={() => void submit()}
            style={{ color: creating ? COLOR.textFaint : COLOR.green, cursor: creating ? "default" : "pointer", fontSize: 12 }}
          >
            {creating ? "…" : "✓"}
          </span>
          <span
            onClick={() => {
              setTitle("");
              setAdding(false);
            }}
            style={{ color: COLOR.textFaint, cursor: "pointer", fontSize: 12 }}
          >
            ✕
          </span>
        </span>
      ) : (
        <span
          onClick={() => setAdding(true)}
          style={{
            padding: "4px 12px",
            fontSize: 12,
            fontFamily: FONT_MONO,
            border: `1px dashed ${COLOR.border}`,
            color: COLOR.textFaint,
            cursor: "pointer"
          }}
        >
          + new subject
        </span>
      )}
    </div>
  );
}

// ── Indeterminate progress bar + spinner while the legacy exam job runs ──
const SPINNER_FRAMES = ["◐", "◓", "◑", "◒"];

const INGEST_PHASES: Array<{ phase: IngestJobPhase; label: string }> = [
  { phase: "preparing", label: "prepare" },
  { phase: "fetching", label: "fetch" },
  { phase: "extracting", label: "extract" },
  { phase: "staging", label: "stage" },
  { phase: "authoring", label: "author" }
];

function RunningCard({ job, elapsed, onCancel }: { job: IngestJobDto; elapsed: number; onCancel: () => void }) {
  const frame = SPINNER_FRAMES[Math.floor(elapsed * 2) % SPINNER_FRAMES.length];
  const minutes = Math.floor(elapsed / 60);
  const seconds = Math.floor(elapsed % 60);
  const clock = minutes > 0 ? `${minutes}m ${String(seconds).padStart(2, "0")}s` : `${seconds}s`;
  const activeIndex = INGEST_PHASES.findIndex((item) => item.phase === job.phase);
  const cancelling = job.phase === "cancelling";
  return (
    <Card style={{ marginTop: 4, borderLeft: `3px solid ${COLOR.cyan}` }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 10 }}>
        <span style={{ color: COLOR.cyan, fontSize: 13, fontWeight: 600 }}>
          {frame} {cancelling ? "cancelling ingest…" : job.message}
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 12 }}>
          <span style={{ color: COLOR.textDim, fontSize: 12, fontFamily: FONT_MONO }}>{clock}</span>
          <span
            onClick={onCancel}
            style={{ color: COLOR.red, cursor: cancelling ? "default" : "pointer", fontSize: 11, opacity: cancelling ? 0.5 : 1 }}
          >
            {cancelling ? "stopping…" : "cancel"}
          </span>
        </span>
      </div>
      <AsciiLoadingBar />
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 11, fontFamily: FONT_MONO, fontSize: 10 }}>
        {INGEST_PHASES.map((item, index) => {
          const complete = activeIndex > index;
          const active = activeIndex === index;
          return (
            <span key={item.phase} style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
              {index > 0 && <span style={{ color: complete || active ? COLOR.green : COLOR.border }}>→</span>}
              <span style={{ color: active ? COLOR.cyan : complete ? COLOR.green : COLOR.textFaint }}>
                {complete ? "✓ " : active ? `${frame} ` : "· "}{item.label}
              </span>
            </span>
          );
        })}
      </div>
      <div style={{ marginTop: 10, fontSize: 11, color: COLOR.textDim, lineHeight: 1.6 }}>
        <div>
          <Faint>source</Faint>{" "}
          <span
            style={{
              fontFamily: FONT_MONO,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              display: "inline-block",
              maxWidth: 420,
              verticalAlign: "bottom"
            }}
          >
            {job.source}
          </span>
        </div>
        {job.phase === "authoring" && job.totalWindows != null && (
          <div style={{ marginTop: 4 }}>
            <Faint>model window</Faint>{" "}
            <span style={{ color: COLOR.cyan }}>{job.currentWindow ?? 1}</span>
            <Faint> / {job.totalWindows}</Faint>
          </div>
        )}
        <div style={{ marginTop: 4 }}>
          <Faint>
            job {job.id} · exam seeding · subject {job.subjectId}
          </Faint>
        </div>
      </div>
    </Card>
  );
}

// ── Ingest screen shell: outline overlay over the single merged view ────
export function IngestScreen({
  jobId,
  onJobIdChange,
  onProceedToPropose,
  onCreateStudyMap,
  guideActive = false,
  onDismissGuide
}: {
  jobId: string | null;
  onJobIdChange: (jobId: string | null) => void;
  onProceedToPropose: (patchId: string) => void;
  onCreateStudyMap?: () => void;
  guideActive?: boolean;
  onDismissGuide?: () => void;
}) {
  // The outline → build-plan → start-batch flow opens as a large modal OVER the
  // ingest screen, which stays mounted underneath (§5.7).
  const [outlineTarget, setOutlineTarget] = useState<{
    sourceRef: string;
    sourceUri: string | null;
    suggestedRole: string | null;
  } | null>(null);
  const [focusBatchId, setFocusBatchId] = useState<string | null>(null);
  const [libraryRefresh, setLibraryRefresh] = useState(0);
  const overlayActive = outlineTarget !== null;

  return (
    <>
      <IngestHome
        jobId={jobId}
        onJobIdChange={onJobIdChange}
        onProceedToPropose={onProceedToPropose}
        onCreateStudyMap={onCreateStudyMap}
        guideActive={guideActive}
        onDismissGuide={onDismissGuide}
        focusBatchId={focusBatchId}
        onFocusBatch={setFocusBatchId}
        libraryRefresh={libraryRefresh}
        onLibraryRefresh={() => setLibraryRefresh((n) => n + 1)}
        overlayActive={overlayActive}
        onOpenOutline={(sourceRef, sourceUri, suggestedRole = null) => {
          // The plan step re-imports by canonical URI to start the authoring
          // batch — callers without one (the Activity CTA) resolve it from the
          // library card before the flow opens, or "start batch" dead-ends. The
          // suggested role rides along the same resolution so the modal can seed
          // its role control.
          if (sourceUri) {
            setOutlineTarget({ sourceRef, sourceUri, suggestedRole });
            return;
          }
          void api
            .getSourceLibrary()
            .then((lib) => {
              const card = lib.sources.find((c) => c.sourceId === sourceRef);
              setOutlineTarget({
                sourceRef,
                sourceUri: card?.canonicalUri ?? null,
                suggestedRole: card?.suggestedRole ?? suggestedRole
              });
            })
            .catch(() => setOutlineTarget({ sourceRef, sourceUri: null, suggestedRole }));
        }}
      />

      {outlineTarget && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 300,
            background: "rgba(0,0,0,0.6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "4vh 4vw"
          }}
          onClick={() => setOutlineTarget(null)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              width: "min(1100px, 92vw)",
              height: "85vh",
              maxHeight: "85vh",
              background: COLOR.bg,
              border: `1px solid ${COLOR.borderStrong}`,
              boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden"
            }}
          >
            <OutlinePlanFlow
              sourceRef={outlineTarget.sourceRef}
              sourceUri={outlineTarget.sourceUri}
              subjectId={null}
              suggestedRole={outlineTarget.suggestedRole}
              onClose={() => setOutlineTarget(null)}
              onOpenBatch={(batchId) => {
                // The authoring batch surfaces as an expanded Activity card in
                // the ingest screen underneath; close the modal and focus it.
                setOutlineTarget(null);
                setFocusBatchId(batchId);
                setLibraryRefresh((n) => n + 1);
              }}
            />
          </div>
        </div>
      )}
    </>
  );
}

// ── The merged view: library sidebar · source input · inline activity ───
function IngestHome({
  jobId,
  onJobIdChange,
  onProceedToPropose,
  onCreateStudyMap,
  guideActive,
  onDismissGuide,
  focusBatchId,
  onFocusBatch,
  libraryRefresh,
  onLibraryRefresh,
  overlayActive,
  onOpenOutline
}: {
  jobId: string | null;
  onJobIdChange: (jobId: string | null) => void;
  onProceedToPropose: (patchId: string) => void;
  onCreateStudyMap?: () => void;
  guideActive: boolean;
  onDismissGuide?: () => void;
  focusBatchId: string | null;
  onFocusBatch: (batchId: string | null) => void;
  libraryRefresh: number;
  onLibraryRefresh: () => void;
  overlayActive: boolean;
  onOpenOutline: (sourceRef: string, sourceUri: string | null, suggestedRole?: string | null) => void;
}) {
  const [source, setSource] = useState("");
  const [mode, setMode] = useState<Mode>("canonical");
  const [subjects, setSubjects] = useState<string[]>([]);
  const [subject, setSubject] = useState<string | null>(null);
  const [creatingSubject, setCreatingSubject] = useState(false);
  const [job, setJob] = useState<IngestJobDto | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [localError, setLocalError] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  const [authoritativeKind, setAuthoritativeKind] = useState<Kind | null>(null);
  const [classifying, setClassifying] = useState(false);
  const [staged, setStaged] = useState<string[]>([]);
  const [stagedPageRanges, setStagedPageRanges] = useState<Record<string, string>>({});
  // Per-source reader opt-out chosen at ingest setup (practice exams etc.).
  const [stagedReaderOff, setStagedReaderOff] = useState<Record<string, boolean>>({});
  const [previews, setPreviews] = useState<Record<string, AcquisitionPreviewItem>>({});
  const [pageSelection, setPageSelection] = useState("");
  const [pdfEngine, setPdfEngine] = useState<PdfEngine>("auto");
  const inputRef = useRef<HTMLInputElement>(null);
  const activityRef = useRef<HTMLDivElement>(null);
  const runningRef = useRef(false);

  const kind = authoritativeKind ?? detectKind(source);
  const running = job?.status === "queued" || job?.status === "running";
  const result = job?.status === "completed" ? job.result : null;
  const error = localError ?? (job?.status === "failed" || job?.status === "cancelled" ? job.error?.message ?? job.message : null);
  // Subject is optional for canonical imports (v2 accepts a null subject); exam
  // seeding replays into one subject's mastery state, so it stays required.
  // Multi-source staging is canonical-only; exam seeding stays single-source legacy.
  const stagingVisible = mode === "canonical";
  const hasStaged = staged.length > 0;
  const canRun =
    (source.trim().length > 0 || (stagingVisible && hasStaged)) &&
    !running &&
    !importing &&
    (mode === "canonical" || subject !== null) &&
    (mode !== "canonical" || pageSelectionError(pageSelection) === null) &&
    Object.values(stagedPageRanges).every((selection) => pageSelectionError(selection) === null);
  const importCount = staged.length + (source.trim() ? 1 : 0);
  const subjectTooltip =
    mode === "canonical"
      ? "imports land in the vault-global source library — no subject needed. A subject chosen here just pre-tags the import batch; sources are bound to subjects later, at outline & build-plan time."
      : "exam seeding replays outcomes into one subject's mastery state, so a subject is required.";

  const refreshSubjects = useCallback(async () => {
    try {
      const snapshot = await api.loadVault();
      const list = snapshot.vault?.subjects ?? [];
      setSubjects(list);
      setSubject((current) => (current && list.includes(current) ? current : null));
    } catch {
      // vault not loaded yet — the shell surfaces that state
    }
  }, []);

  useEffect(() => {
    void refreshSubjects();
  }, [refreshSubjects]);

  useEffect(() => {
    runningRef.current = running || importing;
  }, [running, importing]);

  // Recover a legacy exam job that is still running if this screen was
  // unmounted while the learner visited another tab.
  useEffect(() => {
    if (jobId) return;
    let cancelled = false;
    api.getIngestJobs().then((snapshot) => {
      if (cancelled) return;
      const active = snapshot.jobs.find((candidate) => candidate.status === "queued" || candidate.status === "running");
      if (active) {
        setJob(active);
        onJobIdChange(active.id);
      }
    }).catch(() => {});
    return () => { cancelled = true; };
  }, [jobId, onJobIdChange]);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;
    let timer: number | undefined;
    const poll = async () => {
      try {
        const next = await api.getIngestJob(jobId);
        if (cancelled) return;
        setJob(next);
        setSource(next.source);
        setMode(next.mode);
        setSubject(next.subjectId);
        setLocalError(null);
        if (next.status === "queued" || next.status === "running") {
          timer = window.setTimeout(() => void poll(), 750);
        }
      } catch (e) {
        if (cancelled) return;
        const commandError = e as CommandError;
        if (commandError.code === "ingest_job_not_found") {
          onJobIdChange(null);
          setJob(null);
          setLocalError(commandError.message);
          return;
        }
        setLocalError(commandError.message);
        timer = window.setTimeout(() => void poll(), 1500);
      }
    };
    void poll();
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [jobId, onJobIdChange]);

  useEffect(() => {
    const candidate = source.trim();
    if (!candidate) {
      setAuthoritativeKind(null);
      setClassifying(false);
      return;
    }
    let cancelled = false;
    setClassifying(true);
    const timer = window.setTimeout(() => {
      api.classifyIngestSource(candidate)
        .then((classification) => {
          if (cancelled) return;
          const mapped: Record<string, Kind> = {
            web: "web",
            arxiv: "arxiv",
            pdf: "pdf",
            youtube: "youtube",
            textfile: "local",
            audio: "audio"
          };
          setAuthoritativeKind(mapped[classification.kind] ?? null);
        })
        .catch(() => {
          if (!cancelled) setAuthoritativeKind(null);
        })
        .finally(() => {
          if (!cancelled) setClassifying(false);
        });
    }, 350);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [source]);

  // Annotate staged sources from an acquisition preview (debounced). Keep the
  // last annotations on transient errors — no error spam.
  useEffect(() => {
    if (staged.length === 0) {
      setPreviews({});
      return;
    }
    let cancelled = false;
    const timer = window.setTimeout(() => {
      api.getAcquisitionPreview([...staged])
        .then((preview) => {
          if (cancelled) return;
          const next: Record<string, AcquisitionPreviewItem> = {};
          for (const item of preview.items) next[item.input] = item;
          setPreviews(next);
        })
        .catch(() => {
          // keep last annotations
        });
    }, 400);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [staged]);

  // Elapsed-time ticker while the legacy exam job runs.
  useEffect(() => {
    if (!running || !job) return;
    const parsed = Date.parse(job.startedAt ?? job.createdAt);
    const started = Number.isNaN(parsed) ? Date.now() : parsed;
    setElapsed(Math.max(0, (Date.now() - started) / 1000));
    const id = window.setInterval(() => setElapsed((Date.now() - started) / 1000), 500);
    return () => window.clearInterval(id);
  }, [running, job?.id, job?.startedAt, job?.createdAt]);

  async function createSubject(title: string): Promise<boolean> {
    const id = kebabCase(title);
    if (!id) return false;
    clearFinishedJob();
    setCreatingSubject(true);
    try {
      const res = await api.runCliCommand(["add-subject", id, title]);
      if (res.exitCode !== 0) {
        setLocalError(res.stderr.trim() || `add-subject failed (exit ${res.exitCode})`);
        return false;
      }
      await refreshSubjects();
      setSubject(id);
      setLocalError(null);
      return true;
    } catch (e) {
      setLocalError((e as CommandError).message);
      return false;
    } finally {
      setCreatingSubject(false);
    }
  }

  function clearFinishedJob() {
    if (running) return;
    setJob(null);
    onJobIdChange(null);
  }

  function stageCurrent() {
    const src = source.trim();
    if (!src || pageSelectionError(pageSelection) !== null) return;
    setStaged((prev) => (prev.includes(src) ? prev : [...prev, src]));
    setStagedPageRanges((prev) => {
      const next = { ...prev };
      next[src] = pageSelection;
      return next;
    });
    setSource("");
    setPageSelection("");
    setLocalError(null);
    window.requestAnimationFrame(() => inputRef.current?.focus());
  }

  function stageDropped(paths: string[]) {
    clearFinishedJob();
    setLocalError(null);
    const unique = paths.filter((path, index) => paths.indexOf(path) === index);
    if (unique.length === 1 && staged.length === 0 && !source.trim()) {
      setSource(unique[0]);
      return;
    }
    setStaged((prev) => [...prev, ...unique.filter((path) => !prev.includes(path))]);
    setStagedPageRanges((prev) => {
      const next = { ...prev };
      for (const path of unique) next[path] ??= "";
      return next;
    });
  }

  const fileDragging = useSourceFileDrop({
    enabled: mode === "canonical" && !running && !importing && !overlayActive,
    priority: 10,
    onDrop: stageDropped
  });

  function removeStaged(src: string) {
    setStaged((prev) => prev.filter((s) => s !== src));
    setStagedPageRanges((prev) => {
      const next = { ...prev };
      delete next[src];
      return next;
    });
    setStagedReaderOff((prev) => {
      const next = { ...prev };
      delete next[src];
      return next;
    });
  }

  async function startCanonicalImport(entries: Array<{ source: string; pages?: string }>) {
    setImporting(true);
    try {
      const batch = await api.startImportBatch({
        sources: entries.map((entry) => entry.source),
        subjectId: subject,
        pageRanges: entries
          .filter((entry): entry is { source: string; pages: string } => Boolean(entry.pages?.trim()))
          .map((entry) => ({ source: entry.source, pages: entry.pages })),
        readerDisabledSources: entries.map((entry) => entry.source).filter((src) => stagedReaderOff[src]),
        pdfEngine
      });
      setSource("");
      setStaged([]);
      setStagedPageRanges({});
      setStagedReaderOff({});
      setPageSelection("");
      setLocalError(null);
      onFocusBatch(batch.id);
      onLibraryRefresh();
      activityRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
    } catch (e) {
      setLocalError((e as CommandError).message);
    } finally {
      setImporting(false);
    }
  }

  async function startExamSeeding(src: string) {
    if (!subject) return;
    setJob(null);
    onJobIdChange(null);
    try {
      const started = await api.startIngest({ source: src, subjectId: subject, mode: "exam", pdfEngine });
      setJob(started);
      onJobIdChange(started.id);
    } catch (e) {
      const commandError = e as CommandError;
      const activeJobId = (commandError.details as { jobId?: string; job_id?: string } | undefined)?.jobId
        ?? (commandError.details as { job_id?: string } | undefined)?.job_id;
      if (commandError.code === "ingest_in_progress" && activeJobId) {
        onJobIdChange(activeJobId);
      } else {
        setLocalError(commandError.message);
      }
      runningRef.current = false;
    }
  }

  async function startRun() {
    if (runningRef.current) return;
    const trimmed = source.trim();
    // Canonical multi-source: submit staged (+ current input, if any) as ONE batch.
    if (mode === "canonical" && staged.length > 0) {
      const entries = [
        ...staged.map((stagedSource) => ({
          source: stagedSource,
          pages: stagedPageRanges[stagedSource] || undefined
        })),
        ...(trimmed ? [{ source: trimmed, pages: pageSelection.trim() || undefined }] : [])
      ];
      if (entries.length === 0) return;
      setLocalError(null);
      runningRef.current = true;
      await startCanonicalImport(entries);
      runningRef.current = false;
      return;
    }
    if (!trimmed) return;
    setLocalError(null);
    runningRef.current = true;
    if (mode === "canonical") {
      await startCanonicalImport([{ source: trimmed, pages: pageSelection.trim() || undefined }]);
      runningRef.current = false;
    } else {
      await startExamSeeding(trimmed);
    }
  }

  async function cancelIngest() {
    if (!job || !running || job.phase === "cancelling") return;
    try {
      setJob(await api.cancelIngest(job.id));
    } catch (e) {
      setLocalError((e as CommandError).message);
    }
  }

  async function chooseLocalSource() {
    try {
      const selected = await openDialog({
        multiple: false,
        directory: false,
        filters: [{ name: "Ingest sources", extensions: ["pdf", "md", "markdown", "txt", "html", "htm", "vtt", "srt", "mp3", "wav", "m4a", "flac", "ogg", "oga", "opus", "aac"] }]
      });
      if (typeof selected !== "string") return;
      clearFinishedJob();
      setSource(selected);
      setLocalError(null);
      window.requestAnimationFrame(() => inputRef.current?.focus());
    } catch (e) {
      setLocalError((e as Error).message || "Could not open the source picker.");
    }
  }

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      // The outline modal owns the keyboard while it is open (its own esc steps
      // plan → outline → close); don't also run the ingest screen's shortcuts.
      if (overlayActive) return;
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      const isInput = tag === "input" || tag === "textarea";
      if (event.key === "Enter" && isInput && event.target === inputRef.current) {
        // With staged sources present, Enter stages the current input; the run
        // button becomes the explicit import action. Otherwise Enter imports.
        if (mode === "canonical" && staged.length > 0) {
          if (source.trim()) stageCurrent();
        } else if (canRun) {
          void startRun();
        }
      } else if (event.key === "Escape" && !running) {
        // Stepped reset: input → staged list → job.
        if (source) {
          setSource("");
          setPageSelection("");
        } else if (staged.length > 0) {
          setStaged([]);
          setStagedPageRanges({});
        } else {
          clearFinishedJob();
        }
        setLocalError(null);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source, subject, mode, running, canRun, jobId, staged, overlayActive]);

  const modeChip = (m: Mode, icon: string, label: string) => {
    const sel = mode === m;
    return (
      <span
        key={m}
        onClick={() => {
          if (running) return;
          clearFinishedJob();
          setMode(m);
        }}
        style={{
          padding: "4px 14px",
          fontSize: 12,
          fontFamily: FONT_MONO,
          border: `1px solid ${sel ? COLOR.amber : COLOR.border}`,
          background: sel ? "#241d12" : "transparent",
          color: sel ? COLOR.amber : COLOR.textDim,
          cursor: running ? "default" : "pointer"
        }}
      >
        <span style={{ marginRight: 6, opacity: 0.75 }}>{icon}</span>
        {label}
      </span>
    );
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      {/* ── hero (Today / Proposals style, slimmed) ── */}
      <div
        style={{
          padding: "22px 32px 18px",
          background: COLOR.bg,
          borderBottom: `1px solid ${COLOR.border}`,
          flexShrink: 0
        }}
      >
        <div style={{ textTransform: "uppercase", letterSpacing: "0.18em", color: COLOR.textFaint, fontSize: 11 }}>
          ingest · source library
        </div>
        <div style={{ marginTop: 10, fontSize: 13, color: COLOR.textDim, lineHeight: 1.65 }}>
          imports register a <span style={{ color: COLOR.green }}>source revision + extraction</span> in the library; ready
          sources are outlined &amp; selected into authoring batches, reviewed on the Proposals screen
          {subject && (
            <>
              {"  ·  "}
              subject{" "}
              <span style={{ color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 3 }}>{subject}</span>
            </>
          )}
        </div>
        {guideActive ? (
          <div style={{ marginTop: 14, border: `1px solid ${COLOR.cyan}`, background: "#101d22", padding: "10px 13px", display: "flex", alignItems: "flex-start", gap: 12 }}>
            <span style={{ color: COLOR.cyan, fontFamily: FONT_MONO, whiteSpace: "nowrap" }}>SETUP 03/03</span>
            <div style={{ flex: 1, color: COLOR.textDim, fontSize: 11, lineHeight: 1.6 }}>
              Your build appears in <span style={{ color: COLOR.amber }}>Activity</span>. Inventory runs once per selected unit, then study-map synthesis starts. If a job fails, expand it here for the exact stage and retry path; completed proposals move to <span style={{ color: COLOR.amber }}>Proposals</span> for review.
            </div>
            <button type="button" onClick={onDismissGuide} style={{ border: "none", background: "transparent", color: COLOR.textFaint, cursor: "pointer", fontFamily: FONT_MONO }}>
              got it ×
            </button>
          </div>
        ) : null}
      </div>

      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "300px 1fr", minHeight: 0 }}>
        {/* ── LEFT: source library ── */}
        <div style={{ borderRight: `1px solid ${COLOR.border}`, display: "flex", flexDirection: "column", minHeight: 0 }}>
          <SourceLibrarySidebar
            refreshToken={libraryRefresh}
            onCreateStudyMap={onCreateStudyMap}
            onOpenOutline={(card: SourceLibraryCard) => onOpenOutline(card.sourceId, card.canonicalUri, card.suggestedRole)}
            onFocusSource={() => {
              // No per-source batch mapping yet — bring the activity stack into view.
              activityRef.current?.scrollIntoView({ block: "start", behavior: "smooth" });
            }}
            onOpenBatch={(batchId) => {
              // "synthesize →" on a collection enqueues a build batch — focus it in
              // the Activity stack and bring it into view.
              onFocusBatch(batchId);
              onLibraryRefresh();
              activityRef.current?.scrollIntoView({ block: "start", behavior: "smooth" });
            }}
          />
        </div>

        {/* ── RIGHT: input + inline activity ── */}
        <div className="ll-scroll" style={{ padding: "18px 24px", overflowY: "auto", display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
            <SectionHeader style={{ marginTop: 0 }}>Source</SectionHeader>
            <span style={{ flex: 1 }} />
            <div style={{ display: "flex", gap: 6 }}>
              {modeChip("canonical", "📚", "canonical source")}
              {modeChip("exam", "📝", "exam seeding")}
            </div>
          </div>

          {/* input */}
          <div
            style={{
              border: `1px solid ${source.trim() ? COLOR.amber : COLOR.border}`,
              background: COLOR.bgInput,
              padding: "10px 12px",
              display: "flex",
              alignItems: "center",
              gap: 10
            }}
          >
            <span style={{ color: COLOR.amber, fontWeight: 700, flexShrink: 0 }}>❯</span>
            <input
              ref={inputRef}
              value={source}
              disabled={running}
              onChange={(e) => {
                clearFinishedJob();
                setSource(e.target.value);
                setLocalError(null);
              }}
              placeholder={
                mode === "exam"
                  ? "paste a past exam: URL, PDF path, or local .md / .txt path"
                  : "paste a URL, arXiv id, PDF path, YouTube link, or local .md / .txt / .vtt / .srt / .mp3 / .wav path"
              }
              style={{
                flex: 1,
                minWidth: 0,
                background: "transparent",
                color: COLOR.text,
                border: "none",
                outline: "none",
                fontFamily: FONT_MONO,
                fontSize: 13,
                opacity: running ? 0.6 : 1
              }}
            />
            <span
              onClick={() => {
                if (!running) void chooseLocalSource();
              }}
              style={{
                flexShrink: 0,
                color: running ? COLOR.textFaint : COLOR.amberLink,
                cursor: running ? "default" : "pointer",
                fontSize: 11,
                fontFamily: FONT_MONO
              }}
            >
              browse…
            </span>
          </div>

          {/* detected kind */}
          <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 4 }}>
            <Faint>detected:</Faint>
            <KindChips active={kind} />
            <span style={{ flex: 1 }} />
            {classifying && source.trim() && <Faint>checking with pipeline…</Faint>}
            {!classifying && !kind && source.trim() && <Faint>unsupported or unresolved source</Faint>}
            {!source.trim() && <Faint>paste a source above</Faint>}
          </div>

          <div
            style={{
              border: `1px dashed ${fileDragging ? COLOR.amber : COLOR.border}`,
              background: fileDragging ? "#241d12" : "transparent",
              color: fileDragging ? COLOR.amber : COLOR.textFaint,
              padding: "7px 10px",
              fontSize: 11,
              fontFamily: FONT_MONO,
              marginTop: 6
            }}
          >
            {fileDragging ? "drop to add source files" : "drop PDF, Markdown, text, or HTML files anywhere on this screen"}
          </div>

          {/* optional PDF extraction scope */}
          {mode === "canonical" ? (
            <div style={{ marginTop: 6 }}>
              <PageRangeSelector
                value={pageSelection}
                onChange={setPageSelection}
                disabled={running || importing}
                compact
              />
              {hasStaged ? (
                <Faint style={{ display: "block", fontSize: 11, marginTop: 3 }}>
                  This range belongs to the current source. Staging captures it independently for that PDF.
                </Faint>
              ) : null}
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 6 }}>
                <Faint style={{ fontSize: 11 }}>pdf engine</Faint>
                <TermSelect
                  value={pdfEngine}
                  options={[
                    { value: "auto", label: "auto (vault default)" },
                    { value: "marker", label: "marker — structured, math, OCR" },
                    { value: "pypdf", label: "pypdf — fast native text" }
                  ]}
                  onChange={(value) => setPdfEngine(value as PdfEngine)}
                  disabled={running || importing}
                  width={250}
                />
                {pdfEngine !== "auto" && (
                  <Faint style={{ fontSize: 10 }}>
                    {pdfEngine === "marker"
                      ? "structured extraction via local Marker, or hosted Datalab in the debug runtime"
                      : "no OCR, tables, or math — scanned PDFs will fail"}
                  </Faint>
                )}
              </div>
            </div>
          ) : null}

          {/* subject + run button */}
          <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 4, flexWrap: "wrap" }}>
            <span
              title={subjectTooltip}
              style={{
                color: COLOR.textFaint,
                cursor: "help",
                textDecoration: "underline dotted",
                textUnderlineOffset: 3
              }}
            >
              subject{mode === "canonical" ? " (optional)" : ""}
            </span>
            <SubjectPicker
              subjects={subjects}
              value={subject}
              onChange={(s) => {
                clearFinishedJob();
                setSubject(s);
              }}
              onCreate={createSubject}
              creating={creatingSubject}
            />
            <LearnerLevelChip />
            <span style={{ flex: 1 }} />
            {stagingVisible && (
              <span
                onClick={() => {
                  if (source.trim() && !running && !importing) stageCurrent();
                }}
                title="stage this source and keep adding more — they import together as one batch"
                style={{
                  padding: "8px 12px",
                  border: `1px solid ${COLOR.border}`,
                  background: "transparent",
                  color: source.trim() && !running && !importing ? COLOR.textDim : COLOR.textFaint,
                  fontSize: 12,
                  fontFamily: FONT_MONO,
                  cursor: source.trim() && !running && !importing ? "pointer" : "default",
                  whiteSpace: "nowrap",
                  opacity: source.trim() && !running && !importing ? 1 : 0.6
                }}
              >
                + stage
              </span>
            )}
            <span
              onClick={() => {
                if (canRun) void startRun();
              }}
              style={{
                padding: "8px 16px",
                border: `1px solid ${running || importing ? COLOR.cyan : canRun ? COLOR.amber : COLOR.border}`,
                background: running || importing ? "#10212a" : canRun ? "#241d12" : "transparent",
                color: running || importing ? COLOR.cyan : canRun ? COLOR.amber : COLOR.textFaint,
                fontSize: 13,
                fontWeight: 600,
                cursor: canRun ? "pointer" : "default",
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                fontFamily: FONT_MONO,
                whiteSpace: "nowrap"
              }}
            >
              {running || importing
                ? "◐ ingesting…"
                : job?.status === "failed" || job?.status === "cancelled"
                  ? "↻ retry ingest"
                  : stagingVisible && hasStaged
                    ? `▶ import ${importCount} sources`
                    : mode === "exam"
                      ? "▶ seed exam"
                      : "▶ import source"}
              {!running && !importing && canRun && <Faint style={{ color: COLOR.amber }}>↵</Faint>}
            </span>
          </div>

          {/* staged sources (canonical multi-source) */}
          {stagingVisible && hasStaged && (
            <Card style={{ marginTop: 4 }}>
              <Faint style={{ fontSize: 11, fontFamily: FONT_MONO }}>
                staged sources · {staged.length}
              </Faint>
              <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 8 }}>
                {staged.map((src) => {
                  const rowKind = detectKind(src);
                  const meta = rowKind ? KIND_META[rowKind] : null;
                  const preview = previews[src];
                  const stagedRange = stagedPageRanges[src] ?? "";
                  return (
                    <div key={src} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 6, flexShrink: 0, width: 150 }}>
                        {meta ? (
                          <>
                            <span style={{ opacity: 0.7 }}>{meta.icon}</span>
                            <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>{meta.label}</span>
                          </>
                        ) : (
                          <Faint style={{ fontFamily: FONT_MONO, fontSize: 11 }}>unknown</Faint>
                        )}
                      </span>
                      <span
                        style={{
                          flex: 1,
                          minWidth: 0,
                          fontFamily: FONT_MONO,
                          fontSize: 12,
                          color: COLOR.text,
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis"
                        }}
                        title={src}
                      >
                        {src}
                      </span>
                      {preview?.duplicateOfInput && (
                        <Pill color="amber" style={{ flexShrink: 0 }}>duplicate</Pill>
                      )}
                      {preview?.existingSourceId && (
                        <Pill color="slate" style={{ flexShrink: 0 }}>already in library</Pill>
                      )}
                      {preview && preview.recognized === false && (
                        <Pill color="red" style={{ flexShrink: 0 }}>unrecognized</Pill>
                      )}
                      {rowKind === "pdf" ? (
                        <div style={{ flexShrink: 0 }}>
                          <PageRangeSelector
                            value={stagedRange}
                            onChange={(value) => setStagedPageRanges((prev) => ({
                              ...prev,
                              [src]: value
                            }))}
                            disabled={running || importing}
                            compact
                          />
                        </div>
                      ) : null}
                      <span
                        onClick={() => setStagedReaderOff((prev) => ({ ...prev, [src]: !prev[src] }))}
                        title="whether this source joins the reader loop (reading, highlights, span-grounded Ask). Turn off for assessment material like practice exams."
                        style={{
                          flexShrink: 0,
                          cursor: "pointer",
                          fontFamily: FONT_MONO,
                          fontSize: 10,
                          padding: "2px 8px",
                          border: `1px solid ${stagedReaderOff[src] ? COLOR.border : COLOR.green}`,
                          color: stagedReaderOff[src] ? COLOR.textFaint : COLOR.green
                        }}
                      >
                        {stagedReaderOff[src] ? "reader off" : "reader on"}
                      </span>
                      <span
                        onClick={() => removeStaged(src)}
                        title="remove"
                        style={{ flexShrink: 0, color: COLOR.textFaint, cursor: "pointer", fontSize: 12, fontFamily: FONT_MONO }}
                      >
                        ✕
                      </span>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {mode === "exam" && !running && !result && (
            <div
              style={{
                padding: "10px 14px",
                border: `1px dashed ${COLOR.border}`,
                fontSize: 12,
                color: COLOR.textDim,
                lineHeight: 1.6
              }}
            >
              <span style={{ color: COLOR.pink }}>exam seeding</span>
              {"  "}
              <Faint>·</Faint>
              {"  "}
              creates one tagged practice item per exam question (<Dim>exam_q:&lt;n&gt;</Dim>), each with a rubric and evidence
              facets. After accepting the proposal, seed your per-question outcomes with{" "}
              <Dim>learnloop seed-exam-attempts --outcomes &lt;file&gt;</Dim> so mastery replays from the exam date.
            </div>
          )}

          {/* legacy exam job: running state */}
          {running && job && <RunningCard job={job} elapsed={elapsed} onCancel={() => void cancelIngest()} />}

          {/* error card */}
          {error && !running && (
            <Card style={{ borderLeft: `3px solid ${COLOR.red}`, marginTop: 4 }}>
              <div style={{ color: COLOR.red, fontWeight: 600, fontSize: 13 }}>
                {job?.status === "cancelled" ? "ingest cancelled" : job ? "ingest failed" : "import failed"}
                {job?.error?.code ? <Faint style={{ marginLeft: 8 }}>{job.error.code}</Faint> : null}
              </div>
              <div
                style={{
                  marginTop: 6,
                  color: COLOR.textDim,
                  fontSize: 12,
                  lineHeight: 1.6,
                  fontFamily: FONT_MONO,
                  whiteSpace: "pre-wrap",
                  maxHeight: 160,
                  overflowY: "auto"
                }}
                className="ll-scroll"
              >
                {error}
              </div>
              {job?.error?.details.partial && (
                <div style={{ marginTop: 8, color: COLOR.amber, fontSize: 11 }}>
                  The source note may already be staged. Check the source library before retrying; content-addressed reuse
                  prevents duplicate proposals.
                </div>
              )}
            </Card>
          )}

          {/* legacy exam job: completion card */}
          {result && !running && (
            <Card style={{ borderLeft: `3px solid ${COLOR.green}`, marginTop: 4 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 14 }}>
                <div>
                  <div style={{ color: COLOR.green, fontWeight: 600, fontSize: 13 }}>
                    {result.reusedExisting ? "exam ingest complete · reused existing proposal" : "exam ingest complete · proposal ready"}
                  </div>
                  <div style={{ marginTop: 6, color: COLOR.text, fontSize: 12, lineHeight: 1.6 }}>
                    <Faint>staged note</Faint> <span style={{ color: COLOR.amberLink }}>{result.sourceNoteId}</span>
                    {"  ·  "}
                    <Faint>kind</Faint> <Dim>{kind ? KIND_META[kind].label : result.sourceKind}</Dim>
                  </div>
                  <div style={{ marginTop: 6, color: COLOR.textDim, fontSize: 12 }}>
                    next: <Dim>review the authoring proposal.</Dim>{" "}
                    {result.proposalId ? (
                      <span
                        style={{ color: COLOR.amberLink, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                        onClick={() => onProceedToPropose(result.proposalId as string)}
                      >
                        open proposal →
                      </span>
                    ) : (
                      <Faint>proposal record unavailable</Faint>
                    )}
                    <span style={{ marginLeft: 8 }}>
                      <Faint>then</Faint> <Dim>learnloop seed-exam-attempts --outcomes &lt;file&gt;</Dim>
                    </span>
                  </div>
                </div>
                <div
                  style={{
                    padding: "6px 12px",
                    background: COLOR.bgInput,
                    border: `1px solid ${COLOR.border}`,
                    fontFamily: FONT_MONO,
                    fontSize: 11,
                    color: COLOR.textDim,
                    minWidth: 240,
                    flexShrink: 0
                  }}
                >
                  <div>
                    <Faint>proposal</Faint> <span style={{ color: COLOR.green }}>{result.proposalId ?? "—"}</span>
                  </div>
                  <div style={{ marginTop: 4 }}>
                    <span style={{ color: COLOR.green }}>{result.autoAppliedCount}</span> auto-applied
                    {"  "}
                    <span style={{ color: COLOR.amber }}>{result.reviewRequiredCount}</span> to review
                    {result.invalidCount > 0 && (
                      <>
                        {"  "}
                        <span style={{ color: COLOR.red }}>{result.invalidCount}</span> invalid
                      </>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* ── inline batch activity ── */}
          <div ref={activityRef}>
            <SectionHeader style={{ marginTop: 8 }}>Activity</SectionHeader>
            <Faint style={{ display: "block", fontSize: 12, lineHeight: 1.6, marginBottom: 10 }}>
              each import runs as a durable batch — the checkpoint ladder shows its phases, token bars compare actual vs
              estimated usage. running batches can be cancelled, failed ones resumed. when an import completes,{" "}
              <span style={{ color: COLOR.amber }}>outline &amp; select →</span> chooses what the authoring model sees.
            </Faint>
            <IngestActivityStack
              focusBatchId={focusBatchId}
              onOpenOutline={(sourceId) => {
                onLibraryRefresh();
                onOpenOutline(sourceId, null);
              }}
              onError={(message) => setLocalError(message)}
            />
          </div>

          {!source && !running && !result && !error && (
            <div
              style={{
                marginTop: 12,
                padding: "14px 16px",
                border: `1px dashed ${COLOR.border}`,
                fontSize: 12,
                color: COLOR.textDim,
                lineHeight: 1.6
              }}
            >
              <div>
                <span style={{ color: COLOR.amber }}>import</span>
                {"  "}
                <Faint>·</Faint>
                {"  "}
                downloads or reads the source, extracts its structure (chapters, sections, exercises), and files it in the{" "}
                <span style={{ color: COLOR.green }}>source library</span> on the left. Importing commits you to nothing —
                no subject, no role, no cost beyond extraction. Nothing is sent to a model.
              </div>
              <div style={{ marginTop: 8 }}>
                <span style={{ color: COLOR.amber }}>study map</span>
                {"  "}
                <Faint>·</Faint>
                {"  "}
                your working curriculum, built from the library: concepts, learning objects, evidence facets, and practice
                items, all citing the exact source passages they came from. <Dim>outline &amp; select →</Dim> on a ready
                source chooses which units (and how many tokens) feed the authoring run that proposes it — reviewed on the
                Proposals screen before anything is applied.
              </div>
              <div style={{ marginTop: 8 }}>
                <span style={{ color: COLOR.amber }}>starting a vault</span>
                {"  "}
                <Faint>·</Faint>
                {"  "}
                import everything first: <Dim>+ stage</Dim> each book, page, or video and run them as one batch, then use{" "}
                <Dim>＋ create study map</Dim> in the sidebar to bootstrap the curriculum from your library in a single
                confirmed run. Later sources merge into the existing map instead of rebuilding it. Reach for{" "}
                <Dim>create study map</Dim> when starting a topic from scratch (one confirmation); use the
                import → outline → collection pipeline when adding to an existing map (append routes automatically) or when
                you want manual control over units, role, and which sources synthesize together.
              </div>
              <div style={{ marginTop: 8 }}>
                <span style={{ color: COLOR.amber }}>roles</span>
                {"  "}
                <Faint>·</Faint>
                {"  "}
                a source's authority (<Dim>primary_textbook</Dim>, <Dim>alternate_explanation</Dim>, <Dim>problem_set</Dim>,{" "}
                <Dim>exam</Dim>, …) is never fixed at import — the library suggests one, and you pick or override it on the{" "}
                <Dim>outline &amp; select →</Dim> step (or in the study-map confirmation). Authority is finalized when the
                source joins a collection — use <Dim>add to collection…</Dim> on a ready library row or on the build-plan
                step to pin the role and revision.
              </div>
            </div>
          )}
        </div>
      </div>

      <KeyBar
        keys={[
          { key: "↵", label: running || importing ? "running…" : mode === "exam" ? "Seed exam" : "Import source" },
          { key: "^v", label: "Paste source" },
          { key: "esc", label: "Back/reset" }
        ]}
        right={{ key: "^p", label: "palette" }}
      />
    </div>
  );
}
