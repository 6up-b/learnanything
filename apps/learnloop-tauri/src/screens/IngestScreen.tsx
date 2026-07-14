import { useCallback, useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import { api } from "../api/client";
import type { CommandError, IngestJobDto, IngestJobPhase, IngestMode, RecentIngestEntry } from "../api/dto";
import { COLOR, Dim, Faint, FONT_MONO, KeyBar, Pill, SectionHeader, type PillColor } from "../components/term";
import {
  BatchProgressView,
  IngestViewTabs,
  SourceLibraryView,
  type IngestView
} from "../components/BatchProgress";

// Ingest screen — `learnloop ingest <source> --subject <id>` mirror.
// Spec_mvp §15.2: turn external reference material (URL / arXiv id / PDF /
// YouTube / local .md|.txt) into a `source_type: canonical_source` note under
// `subjects/<id>/notes/`, then run the canonical-ingestor proposal against it.
//
// Runs the real pipeline as a cancellable sidecar job; the screen polls typed
// phase/progress snapshots while recent ingests come from `get_recent_ingests`.

type Kind = "web" | "arxiv" | "pdf" | "youtube" | "local";

// ── Source-kind detection (mirrors src/learnloop/services/source_ingestion.py) ──
function detectKind(source: string): Kind | null {
  const s = (source || "").trim();
  if (!s) return null;
  if (/^https?:\/\/(www\.)?arxiv\.org\//i.test(s) || /^arxiv:/i.test(s)) return "arxiv";
  if (/^\d{4}\.\d{4,5}(v\d+)?$/.test(s)) return "arxiv"; // bare id
  if (/^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\//i.test(s)) return "youtube";
  if (/\.pdf(\?|$)/i.test(s)) return "pdf";
  if (/^https?:\/\//i.test(s)) return "web";
  if (/\.(md|markdown|txt)$/i.test(s)) return "local";
  return null;
}

type KindMeta = { color: PillColor; label: string; icon: string };

const KIND_META: Record<Kind, KindMeta> = {
  web: { color: "cyan", label: "web page", icon: "🌐" },
  arxiv: { color: "green", label: "arXiv paper", icon: "📄" },
  pdf: { color: "amber", label: "PDF", icon: "📕" },
  youtube: { color: "red", label: "YouTube transcript", icon: "▶" },
  local: { color: "purple", label: "local file", icon: "📁" }
};

// Backend `canonical_source.kind` values → display pill.
const BACKEND_KIND: Record<string, { color: PillColor; label: string }> = {
  website_page: { color: "cyan", label: "web" },
  arxiv_html: { color: "green", label: "arxiv" },
  textbook_chapter: { color: "amber", label: "pdf" },
  youtube_video: { color: "red", label: "youtube" }
};

function backendKindPill(kind: string | null, canonicalUri?: string | null): { color: PillColor; label: string } {
  if (kind === "website_page" && canonicalUri && /\.pdf(?:$|[?#])/i.test(canonicalUri)) {
    return { color: "amber", label: "pdf" };
  }
  if (kind && BACKEND_KIND[kind]) return BACKEND_KIND[kind];
  return { color: "slate", label: kind ?? "source" };
}

type Mode = IngestMode;

function relativeWhen(iso: string | null): string {
  if (!iso) return "";
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return "";
  const seconds = Math.max(0, (Date.now() - then) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

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

// ── Markdown preview highlighter — light reuse of library's style ──────
function previewMD(src: string): ReactNode[] {
  const out: ReactNode[] = [];
  src.split("\n").forEach((line, i) => {
    if (line.startsWith("# ")) {
      out.push(
        <div key={i} style={{ color: COLOR.amber, fontWeight: 700 }}>
          {line}
        </div>
      );
    } else if (line.startsWith("## ")) {
      out.push(
        <div key={i} style={{ color: COLOR.amberLink, fontWeight: 600 }}>
          {line}
        </div>
      );
    } else if (line.startsWith("> ")) {
      out.push(
        <div key={i} style={{ color: COLOR.cyan, fontStyle: "italic" }}>
          {line}
        </div>
      );
    } else if (line.startsWith("    ")) {
      out.push(
        <div key={i} style={{ color: COLOR.green }}>
          {line}
        </div>
      );
    } else if (/^\d+\.\s/.test(line) || /^- /.test(line)) {
      const marker = line.match(/^\S+/)?.[0] ?? "";
      out.push(
        <div key={i}>
          <span style={{ color: COLOR.amber }}>{marker} </span>
          <span>{line.slice(line.indexOf(" ") + 1)}</span>
        </div>
      );
    } else if (line.startsWith("[")) {
      const tag = line.match(/^\[[^\]]+\]/)?.[0] ?? "";
      out.push(
        <div key={i}>
          <span style={{ color: COLOR.textFaint }}>{tag}</span>
          <span>{line.slice(tag.length)}</span>
        </div>
      );
    } else {
      // inline backticks
      const parts = line.split(/(`[^`]+`)/);
      out.push(
        <div key={i}>
          {parts.map((p, j) =>
            p.startsWith("`") ? (
              <span key={j} style={{ color: COLOR.green, background: COLOR.bgElev, padding: "0 4px" }}>
                {p.slice(1, -1)}
              </span>
            ) : (
              <span key={j}>{p}</span>
            )
          )}
        </div>
      );
    }
  });
  return out;
}

// ── Recent ingest row ──────────────────────────────────────────────────
function RecentIngestRow({
  row,
  selected,
  onSelect
}: {
  row: RecentIngestEntry;
  selected: boolean;
  onSelect: () => void;
}) {
  const pill = row.purpose === "exam_ingest"
    ? { color: "pink" as PillColor, label: "exam" }
    : backendKindPill(row.kind, row.canonicalUri);
  return (
    <div
      onClick={onSelect}
      style={{
        padding: "8px 12px",
        borderBottom: `1px solid ${COLOR.border}`,
        borderLeft: `2px solid ${selected ? COLOR.amber : "transparent"}`,
        background: selected ? COLOR.bgElev : "transparent",
        display: "flex",
        flexDirection: "column",
        gap: 3,
        cursor: "pointer"
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <Pill color={pill.color}>{pill.label}</Pill>
        <span
          style={{
            flex: 1,
            minWidth: 0,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            color: COLOR.text,
            fontSize: 12
          }}
        >
          {row.title}
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11 }}>
        <Faint style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{row.subjectId ?? "—"}</Faint>
        <span style={{ flex: 1 }} />
        <Faint>{relativeWhen(row.createdAt ?? row.retrievedAt)}</Faint>
      </div>
    </div>
  );
}

// ── Kind chips above input ──────────────────────────────────────────────
function KindChips({ active }: { active: Kind | null }) {
  const order: Kind[] = ["web", "arxiv", "pdf", "youtube", "local"];
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
function SubjectPicker({
  subjects,
  value,
  onChange,
  onCreate,
  creating
}: {
  subjects: string[];
  value: string | null;
  onChange: (subject: string) => void;
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
            onClick={() => onChange(s)}
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

// ── Indeterminate progress bar + spinner while the pipeline runs ────────
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
      <div className="ll-ingest-bar" />
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
            job {job.id} · {job.mode === "exam" ? "practice exam" : "canonical source"} · subject {job.subjectId}
          </Faint>
        </div>
      </div>
    </Card>
  );
}

// ── Selected recent-ingest preview state ─────────────────────────────────
type NotePreview = {
  entry: RecentIngestEntry;
  loading: boolean;
  frontmatter: string | null;
  body: string | null;
  error: string | null;
};

function splitFrontmatter(raw: string): { frontmatter: string | null; body: string } {
  if (raw.startsWith("---")) {
    const end = raw.indexOf("\n---", 3);
    if (end !== -1) {
      return {
        frontmatter: raw.slice(0, end + 4),
        body: raw.slice(end + 4).replace(/^\s*\n/, "")
      };
    }
  }
  return { frontmatter: null, body: raw };
}

// ── Ingest tab shell: view switch over library / add / batch progress ───
export function IngestScreen({
  jobId,
  onJobIdChange,
  onProceedToPropose
}: {
  jobId: string | null;
  onJobIdChange: (jobId: string | null) => void;
  onProceedToPropose: (patchId: string) => void;
}) {
  // A running legacy job forces the Add-source view so its progress stays visible.
  const [view, setView] = useState<IngestView>(jobId ? "add" : "library");
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <IngestViewTabs view={view} onChange={setView} />
      {view === "add" && (
        <AddSourceView jobId={jobId} onJobIdChange={onJobIdChange} onProceedToPropose={onProceedToPropose} />
      )}
      {view === "library" && (
        <SourceLibraryView
          onOpenBatch={(batchId) => {
            setSelectedBatchId(batchId);
            setView("batches");
          }}
        />
      )}
      {view === "batches" && <BatchProgressView selectedBatchId={selectedBatchId} onSelect={setSelectedBatchId} />}
    </div>
  );
}

// ── Single-source ingest form (legacy Quick-add path, still durable) ─────
function AddSourceView({
  jobId,
  onJobIdChange,
  onProceedToPropose
}: {
  jobId: string | null;
  onJobIdChange: (jobId: string | null) => void;
  onProceedToPropose: (patchId: string) => void;
}) {
  const [source, setSource] = useState("");
  const [mode, setMode] = useState<Mode>("canonical");
  const [subjects, setSubjects] = useState<string[]>([]);
  const [subject, setSubject] = useState<string | null>(null);
  const [creatingSubject, setCreatingSubject] = useState(false);
  const [recent, setRecent] = useState<RecentIngestEntry[]>([]);
  const [recentLoading, setRecentLoading] = useState(true);
  const [preview, setPreview] = useState<NotePreview | null>(null);
  const [job, setJob] = useState<IngestJobDto | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [localError, setLocalError] = useState<string | null>(null);
  const [authoritativeKind, setAuthoritativeKind] = useState<Kind | null>(null);
  const [classifying, setClassifying] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const runningRef = useRef(false);
  const completedJobRef = useRef<string | null>(null);

  const kind = authoritativeKind ?? detectKind(source);
  const running = job?.status === "queued" || job?.status === "running";
  const result = job?.status === "completed" ? job.result : null;
  const error = localError ?? (job?.status === "failed" || job?.status === "cancelled" ? job.error?.message ?? job.message : null);
  const canRun = source.trim().length > 0 && subject !== null && !running;

  const refreshSubjects = useCallback(async () => {
    try {
      const snapshot = await api.loadVault();
      const list = snapshot.vault?.subjects ?? [];
      setSubjects(list);
      setSubject((current) => (current && list.includes(current) ? current : (list[0] ?? null)));
    } catch {
      // vault not loaded yet — the shell surfaces that state
    }
  }, []);

  const refreshRecent = useCallback(async () => {
    try {
      const snapshot = await api.getRecentIngests();
      setRecent(snapshot.ingests);
    } catch {
      setRecent([]);
    } finally {
      setRecentLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshSubjects();
    void refreshRecent();
  }, [refreshSubjects, refreshRecent]);

  useEffect(() => {
    runningRef.current = running;
  }, [running]);

  // Recover an ingest that is still running if this screen was unmounted while
  // the learner visited another tab.
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
        if (next.status === "completed" && completedJobRef.current !== next.id) {
          completedJobRef.current = next.id;
          await refreshRecent();
        }
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
  }, [jobId, onJobIdChange, refreshRecent]);

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
            textfile: "local"
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

  // Elapsed-time ticker while the background job runs.
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
    completedJobRef.current = null;
  }

  async function startIngest() {
    const src = source.trim();
    if (!src || !subject || runningRef.current) return;
    runningRef.current = true;
    setJob(null);
    onJobIdChange(null);
    setLocalError(null);
    setPreview(null);
    try {
      const started = await api.startIngest({ source: src, subjectId: subject, mode });
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
        filters: [{ name: "Ingest sources", extensions: ["pdf", "md", "markdown", "txt", "html", "htm"] }]
      });
      if (typeof selected !== "string") return;
      clearFinishedJob();
      setSource(selected);
      setLocalError(null);
      setPreview(null);
      window.requestAnimationFrame(() => inputRef.current?.focus());
    } catch (e) {
      setLocalError((e as Error).message || "Could not open the source picker.");
    }
  }

  async function openRecent(entry: RecentIngestEntry) {
    clearFinishedJob();
    setLocalError(null);
    setPreview({ entry, loading: true, frontmatter: null, body: null, error: null });
    if (!entry.path) {
      setPreview({ entry, loading: false, frontmatter: null, body: null, error: "note path unknown" });
      return;
    }
    try {
      const file = await api.readVaultFile(entry.path);
      if (file.body == null) {
        setPreview({ entry, loading: false, frontmatter: null, body: null, error: "file is binary or too large to preview" });
        return;
      }
      const { frontmatter, body } = splitFrontmatter(file.body);
      setPreview({ entry, loading: false, frontmatter, body, error: null });
    } catch (e) {
      setPreview({ entry, loading: false, frontmatter: null, body: null, error: (e as CommandError).message });
    }
  }

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      const isInput = tag === "input" || tag === "textarea";
      if (event.key === "Enter" && isInput && event.target === inputRef.current && canRun) {
        void startIngest();
      } else if (event.key === "Escape" && !running) {
        setSource("");
        clearFinishedJob();
        setLocalError(null);
        setPreview(null);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source, subject, mode, running, canRun, jobId]);

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
          ingest · canonical source staging
        </div>
        <div style={{ marginTop: 10, fontSize: 13, color: COLOR.textDim, lineHeight: 1.65 }}>
          stages external references as <span style={{ color: COLOR.green }}>source_type: canonical_source</span> notes, then
          proposes learning objects &amp; practice items for review
          {subject && (
            <>
              {"  ·  "}
              subject{" "}
              <span style={{ color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 3 }}>{subject}</span>
            </>
          )}
        </div>
      </div>

      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "300px 1fr", minHeight: 0 }}>
        {/* ── LEFT: recent ingests ── */}
        <div style={{ borderRight: `1px solid ${COLOR.border}`, display: "flex", flexDirection: "column", minHeight: 0 }}>
          <div
            style={{
              padding: "10px 14px",
              fontSize: 12,
              color: COLOR.amber,
              textDecoration: "underline",
              textUnderlineOffset: 3,
              background: COLOR.bgElev,
              borderBottom: `1px solid ${COLOR.border}`,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "baseline"
            }}
          >
            <span>recent ingests</span>
            {recent.length > 0 && <Faint style={{ fontSize: 11, textDecoration: "none" }}>{recent.length}</Faint>}
          </div>
          <div className="ll-scroll" style={{ flex: 1, overflowY: "auto" }}>
            {recentLoading ? (
              <div style={{ padding: "14px 12px", fontSize: 12, color: COLOR.textFaint }}>◐ loading…</div>
            ) : recent.length === 0 ? (
              <div style={{ padding: "14px 12px", fontSize: 12, color: COLOR.textFaint, lineHeight: 1.6 }}>
                nothing ingested yet — staged sources will show up here.
              </div>
            ) : (
              recent.map((r) => (
                <RecentIngestRow
                  key={r.noteId}
                  row={r}
                  selected={preview?.entry.noteId === r.noteId}
                  onSelect={() => void openRecent(r)}
                />
              ))
            )}
          </div>
        </div>

        {/* ── RIGHT: input + status + preview ── */}
        <div className="ll-scroll" style={{ padding: "18px 24px", overflowY: "auto", display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
            <SectionHeader style={{ marginTop: 0 }}>Source</SectionHeader>
            <span style={{ flex: 1 }} />
            <div style={{ display: "flex", gap: 6 }}>
              {modeChip("canonical", "📚", "canonical source")}
              {modeChip("exam", "📝", "practice exam")}
            </div>
          </div>

          {/* input */}
          <div
            style={{
              border: `1px solid ${source.trim() ? COLOR.amber : COLOR.border}`,
              background: COLOR.bgInput,
              padding: "10px 92px 10px 36px",
              position: "relative"
            }}
          >
            <span style={{ position: "absolute", left: 14, top: 12, color: COLOR.amber, fontWeight: 700 }}>❯</span>
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
                  : "paste a URL, arXiv id, PDF path, YouTube link, or local .md / .txt path"
              }
              style={{
                width: "100%",
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
                position: "absolute",
                right: 12,
                top: 10,
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

          {/* subject + run button */}
          <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 4, flexWrap: "wrap" }}>
            <Faint>subject</Faint>
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
            <span style={{ flex: 1 }} />
            <span
              onClick={() => {
                if (canRun) void startIngest();
              }}
              style={{
                padding: "8px 16px",
                border: `1px solid ${running ? COLOR.cyan : canRun ? COLOR.amber : COLOR.border}`,
                background: running ? "#10212a" : canRun ? "#241d12" : "transparent",
                color: running ? COLOR.cyan : canRun ? COLOR.amber : COLOR.textFaint,
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
              {running
                ? "◐ ingesting…"
                : job?.status === "failed" || job?.status === "cancelled"
                  ? "↻ retry ingest"
                  : mode === "exam"
                    ? "▶ ingest exam"
                    : "▶ run ingest"}
              {!running && canRun && <Faint style={{ color: COLOR.amber }}>↵</Faint>}
            </span>
          </div>

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

          {/* running state */}
          {running && job && <RunningCard job={job} elapsed={elapsed} onCancel={() => void cancelIngest()} />}

          {/* error card */}
          {error && !running && (
            <Card style={{ borderLeft: `3px solid ${COLOR.red}`, marginTop: 4 }}>
              <div style={{ color: COLOR.red, fontWeight: 600, fontSize: 13 }}>
                {job?.status === "cancelled" ? "ingest cancelled" : "ingest failed"}
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
                  The source note may already be staged. Check recent ingests before retrying; content-addressed reuse prevents duplicate proposals.
                </div>
              )}
            </Card>
          )}

          {/* completion card */}
          {result && !running && (
            <Card style={{ borderLeft: `3px solid ${COLOR.green}`, marginTop: 4 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 14 }}>
                <div>
                  <div style={{ color: COLOR.green, fontWeight: 600, fontSize: 13 }}>
                    {result.reusedExisting ? "ingest complete · reused existing proposal" : "ingest complete · proposal ready"}
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
                    {job?.mode === "exam" && (
                      <span style={{ marginLeft: 8 }}>
                        <Faint>then</Faint> <Dim>learnloop seed-exam-attempts --outcomes &lt;file&gt;</Dim>
                      </span>
                    )}
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

          {/* recent-ingest note preview */}
          {preview && (
            <>
              <SectionHeader>
                Staged note · {preview.entry.path ?? preview.entry.noteId}
              </SectionHeader>
              <div
                style={{
                  border: `1px solid ${COLOR.border}`,
                  background: COLOR.bg,
                  display: "flex",
                  flexDirection: "column",
                  maxHeight: 420,
                  overflow: "hidden"
                }}
              >
                <div
                  style={{
                    padding: "8px 14px",
                    background: COLOR.bgElev,
                    borderBottom: `1px solid ${COLOR.border}`,
                    fontSize: 12,
                    color: COLOR.textDim,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 10
                  }}
                >
                  <span
                    style={{
                      fontFamily: FONT_MONO,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      minWidth: 0
                    }}
                  >
                    <span style={{ color: COLOR.green }}>{preview.entry.title}</span>
                  </span>
                  <span style={{ display: "inline-flex", gap: 6, flexShrink: 0, alignItems: "center" }}>
                    {preview.entry.purpose === "exam_ingest" && <Pill color="pink">exam</Pill>}
                    <Pill color="green">canonical_source</Pill>
                    <Pill color={backendKindPill(preview.entry.kind, preview.entry.canonicalUri).color}>
                      {backendKindPill(preview.entry.kind, preview.entry.canonicalUri).label}
                    </Pill>
                    {preview.entry.patchId && (
                      <span
                        onClick={() => {
                          if (preview.entry.patchId) onProceedToPropose(preview.entry.patchId);
                        }}
                        style={{
                          color: COLOR.amberLink,
                          cursor: "pointer",
                          textDecoration: "underline",
                          textUnderlineOffset: 2,
                          fontSize: 11
                        }}
                      >
                        proposal →
                      </span>
                    )}
                    <span
                      onClick={() => setPreview(null)}
                      style={{ color: COLOR.textFaint, cursor: "pointer", fontSize: 12, marginLeft: 4 }}
                    >
                      ✕
                    </span>
                  </span>
                </div>
                <div
                  className="ll-scroll"
                  style={{
                    flex: 1,
                    overflowY: "auto",
                    padding: "12px 16px",
                    fontFamily: FONT_MONO,
                    fontSize: 12.5,
                    lineHeight: 1.6,
                    color: COLOR.text,
                    whiteSpace: "pre-wrap"
                  }}
                >
                  {preview.loading ? (
                    <Faint>◐ loading note…</Faint>
                  ) : preview.error ? (
                    <span style={{ color: COLOR.red }}>{preview.error}</span>
                  ) : (
                    <>
                      {preview.frontmatter && (
                        <div style={{ color: COLOR.textFaint, marginBottom: 10 }}>{preview.frontmatter}</div>
                      )}
                      <div>{previewMD(preview.body ?? "")}</div>
                    </>
                  )}
                </div>
              </div>
            </>
          )}

          {!source && !preview && !running && !result && !error && (
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
              <span style={{ color: COLOR.amber }}>what does ingest do</span>
              {"  "}
              <Faint>·</Faint>
              {"  "}
              fetches the source, extracts clean Markdown, stages it as a{" "}
              <span style={{ color: COLOR.green }}>source_type: canonical_source</span> note, and runs the canonical ingestor to
              propose learning objects, concepts, and practice items — reviewed on the Proposals screen.{" "}
              <Faint>select a recent ingest on the left to view its staged note.</Faint>
            </div>
          )}
        </div>
      </div>

      <KeyBar
        keys={[
          { key: "↵", label: running ? "running…" : "Run ingest" },
          { key: "^v", label: "Paste source" },
          { key: "esc", label: "Reset" }
        ]}
        right={{ key: "^p", label: "palette" }}
      />
    </div>
  );
}
