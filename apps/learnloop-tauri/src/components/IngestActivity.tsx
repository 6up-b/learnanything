import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { api } from "../api/client";
import type {
  CommandError,
  DurableIngestStatus,
  IngestBatchDto,
  IngestJobView
} from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill, type PillColor } from "./term";
import { readableSourceTail } from "./sourceTail";

// Ingest activity stack — durable batches rendered inline on the merged Ingest
// screen (replacing the legacy full-screen BatchProgressView). Active batches
// sit at the top expanded; finished batches collapse to one-line rows. One
// list_ingest_batches poll (snapshot carries full jobs) drives everything.

// ── Status → colour maps (moved verbatim from BatchProgress) ─────────────
const STATUS_PILL: Record<DurableIngestStatus, PillColor> = {
  queued: "slate",
  running: "cyan",
  waiting_for_input: "amber",
  completed: "green",
  failed: "red",
  blocked: "purple",
  cancelled: "slate"
};

const STATUS_COLOR: Record<DurableIngestStatus, string> = {
  queued: COLOR.textFaint,
  running: COLOR.cyan,
  waiting_for_input: COLOR.amber,
  completed: COLOR.green,
  failed: COLOR.red,
  blocked: COLOR.purplePill,
  cancelled: COLOR.textFaint
};

function statusLabel(status: DurableIngestStatus): string {
  return status.replace(/_/g, " ");
}

function isActive(status: DurableIngestStatus): boolean {
  return status === "queued" || status === "running" || status === "waiting_for_input";
}

// relativeWhen — copied from IngestScreen; batches carry ISO timestamps.
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

// ── Bordered card (moved verbatim from BatchProgress) ────────────────────
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

// ── Batch title — the imported source's real title, else a readable tail ─
// Prefer the human-readable title an import job captured (e.g. a YouTube
// "<title> — <author>"); otherwise keep the last meaningful segment of the
// source URL/path and let CSS ellipsize. Fallback to the workflow type when no
// source is attached.
function batchTitle(batch: IngestBatchDto): string {
  for (const job of batch.jobs) {
    const title = job.result?.title;
    if (typeof title === "string" && title.trim()) return title;
  }
  const source = batch.jobs.find((job) => job.source)?.source ?? null;
  if (!source) return batch.workflowType;
  return readableSourceTail(source);
}

// Import-completion source id — the outline CTA target. Only import workflows
// carry it, under either casing depending on the emitting job.
function importedSourceId(batch: IngestBatchDto): string | null {
  if (batch.status !== "completed") return null;
  const isImport = (job: IngestJobView) =>
    job.jobType === "import_source" || /import/i.test(batch.workflowType);
  for (const job of batch.jobs) {
    if (!isImport(job) || !job.result) continue;
    const id = job.result.sourceId ?? job.result.source_id;
    if (typeof id === "string" && id) return id;
  }
  return null;
}

// ── IngestActivityStack ──────────────────────────────────────────────────
export function IngestActivityStack({
  focusBatchId,
  onOpenOutline,
  onError
}: {
  focusBatchId: string | null;
  onOpenOutline: (sourceId: string) => void;
  onError?: (message: string) => void;
}): JSX.Element {
  const [batches, setBatches] = useState<IngestBatchDto[]>([]);
  const [loaded, setLoaded] = useState(false);
  // Finished rows the learner clicked open (active rows are always expanded).
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const reportedError = useRef(false);
  const onErrorRef = useRef(onError);
  onErrorRef.current = onError;

  // ── Single poll: fast while anything is active, idle otherwise ──────────
  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;
    const poll = async () => {
      try {
        const snapshot = await api.listIngestBatches(30);
        if (cancelled) return;
        setBatches(snapshot.batches);
        setLoaded(true);
        reportedError.current = false;
        const active = snapshot.batches.some((batch) => isActive(batch.status));
        timer = window.setTimeout(() => void poll(), active ? 1500 : 5000);
      } catch (e) {
        if (cancelled) return;
        // Report once, keep the last good data, retry on the idle cadence.
        if (!reportedError.current) {
          reportedError.current = true;
          onErrorRef.current?.((e as CommandError).message);
        }
        timer = window.setTimeout(() => void poll(), 5000);
      }
    };
    void poll();
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, []);

  // Optimistically replace one batch from a mutation's returned DTO.
  const patchBatch = useCallback((next: IngestBatchDto) => {
    setBatches((prev) => prev.map((batch) => (batch.id === next.id ? next : batch)));
  }, []);

  const reportError = useCallback((message: string) => {
    onErrorRef.current?.(message);
  }, []);

  // ── Partition: active (newest first), then latest 5 finished ────────────
  const { active, finished } = useMemo(() => {
    const byNewest = (a: IngestBatchDto, b: IngestBatchDto) =>
      Date.parse(b.createdAt ?? "") - Date.parse(a.createdAt ?? "");
    const act = batches.filter((batch) => isActive(batch.status)).sort(byNewest);
    const fin = batches
      .filter((batch) => !isActive(batch.status))
      .sort((a, b) => Date.parse(b.finishedAt ?? b.createdAt ?? "") - Date.parse(a.finishedAt ?? a.createdAt ?? ""))
      .slice(0, 5);
    return { active: act, finished: fin };
  }, [batches]);

  function toggle(batchId: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(batchId)) next.delete(batchId);
      else next.add(batchId);
      return next;
    });
  }

  if (loaded && batches.length === 0) {
    return (
      <Faint style={{ display: "block", padding: "4px 0", fontSize: 12 }}>
        no ingest activity yet — imports will appear here.
      </Faint>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {active.map((batch) => (
        <BatchCard
          key={batch.id}
          batch={batch}
          focused={batch.id === focusBatchId}
          onPatch={patchBatch}
          onError={reportError}
          onOpenOutline={onOpenOutline}
        />
      ))}
      {finished.map((batch) => {
        const open = expanded.has(batch.id) || batch.id === focusBatchId;
        return open ? (
          <BatchCard
            key={batch.id}
            batch={batch}
            focused={batch.id === focusBatchId}
            onPatch={patchBatch}
            onError={reportError}
            onOpenOutline={onOpenOutline}
            onCollapse={() => toggle(batch.id)}
          />
        ) : (
          <CollapsedRow key={batch.id} batch={batch} onExpand={() => toggle(batch.id)} />
        );
      })}
    </div>
  );
}

// ── Collapsed finished row — one line, bordered bottom like list rows ────
function CollapsedRow({ batch, onExpand }: { batch: IngestBatchDto; onExpand: () => void }) {
  const done = batch.jobs.filter((job) => job.status === "completed").length;
  return (
    <div
      onClick={onExpand}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "8px 2px",
        borderBottom: `1px solid ${COLOR.border}`,
        cursor: "pointer"
      }}
    >
      <Pill color={STATUS_PILL[batch.status]}>{statusLabel(batch.status)}</Pill>
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
        title={batchTitle(batch)}
      >
        {batchTitle(batch)}
      </span>
      <Faint style={{ fontSize: 11, fontFamily: FONT_MONO }}>
        {done}/{batch.jobs.length} jobs
      </Faint>
      <Faint style={{ fontSize: 11 }}>{relativeWhen(batch.finishedAt ?? batch.createdAt)}</Faint>
    </div>
  );
}

// ── Expanded batch card — header + job ladder + import CTA ────────────────
function BatchCard({
  batch,
  focused,
  onPatch,
  onError,
  onOpenOutline,
  onCollapse
}: {
  batch: IngestBatchDto;
  focused: boolean;
  onPatch: (batch: IngestBatchDto) => void;
  onError: (message: string) => void;
  onOpenOutline: (sourceId: string) => void;
  onCollapse?: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const active = isActive(batch.status);
  const resumable = batch.status === "failed" || batch.status === "cancelled";
  const sourceId = importedSourceId(batch);

  // Force-scroll the focused batch into view whenever the focus target changes.
  useEffect(() => {
    if (focused) ref.current?.scrollIntoView({ block: "nearest" });
  }, [focused]);

  async function cancel() {
    try {
      onPatch(await api.cancelIngestBatch(batch.id));
    } catch (e) {
      onError((e as CommandError).message);
    }
  }

  async function resume() {
    try {
      onPatch(await api.resumeIngestBatch(batch.id));
    } catch (e) {
      onError((e as CommandError).message);
    }
  }

  return (
    <Card style={{ borderLeft: `3px solid ${STATUS_COLOR[batch.status]}` }}>
      <div ref={ref} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
        <Pill color={STATUS_PILL[batch.status]}>{statusLabel(batch.status)}</Pill>
        <span
          onClick={onCollapse}
          style={{
            minWidth: 0,
            maxWidth: 360,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            color: COLOR.text,
            fontSize: 13,
            fontWeight: 600,
            cursor: onCollapse ? "pointer" : "default"
          }}
          title={batchTitle(batch)}
        >
          {batchTitle(batch)}
        </span>
        <Faint style={{ fontSize: 11, fontFamily: FONT_MONO }}>{batch.workflowType}</Faint>
        <Faint style={{ fontSize: 11 }}>{relativeWhen(active ? batch.createdAt : batch.finishedAt ?? batch.createdAt)}</Faint>
        <span style={{ flex: 1 }} />
        {active && (
          <span onClick={() => void cancel()} style={{ color: COLOR.red, cursor: "pointer", fontSize: 12, fontFamily: FONT_MONO }}>
            cancel
          </span>
        )}
        {resumable && (
          <span onClick={() => void resume()} style={{ color: COLOR.green, cursor: "pointer", fontSize: 12, fontFamily: FONT_MONO }}>
            ↻ resume
          </span>
        )}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {batch.jobs.map((job) => (
          <JobRow key={job.id} job={job} />
        ))}
      </div>

      {sourceId && (
        <div style={{ marginTop: 12, fontSize: 12 }}>
          <span style={{ color: COLOR.green }}>source ready</span>{" "}
          <Faint>·</Faint>{" "}
          <span
            onClick={() => onOpenOutline(sourceId)}
            style={{ color: COLOR.amberLink, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
          >
            outline &amp; select →
          </span>
        </div>
      )}
    </Card>
  );
}

// ── JobRow + ladder + token bars + waiting card (moved verbatim) ─────────
function JobRow({ job }: { job: IngestJobView }) {
  const borderColor = STATUS_COLOR[job.status];
  return (
    <Card style={{ borderLeft: `3px solid ${borderColor}` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
        <Faint style={{ fontFamily: FONT_MONO }}>#{job.ordinal}</Faint>
        <span style={{ color: COLOR.text, fontSize: 13, fontWeight: 600 }}>{job.jobType}</span>
        <Pill color={STATUS_PILL[job.status]}>{statusLabel(job.status)}</Pill>
        <span style={{ flex: 1 }} />
        {job.attemptCount > 1 && <Faint style={{ fontSize: 11 }}>attempt {job.attemptCount}</Faint>}
        {job.currentWindow != null && job.totalWindows != null && (
          <Faint style={{ fontSize: 11, fontFamily: FONT_MONO }}>
            window {job.currentWindow}/{job.totalWindows}
          </Faint>
        )}
      </div>

      <CheckpointLadder ladder={job.checkpointLadder} phase={job.phase} status={job.status} />

      {job.message && <div style={{ marginTop: 8, fontSize: 12, color: COLOR.textDim }}>{job.message}</div>}

      <TokenBars usage={job.usage} estimate={job.estimate} />

      {job.waitingForInput && <WaitingCard payload={job.waitingForInput} />}

      {job.error && (
        <div style={{ marginTop: 8, fontSize: 11, color: COLOR.red, fontFamily: FONT_MONO }}>
          {job.error.code}: {job.error.message}
        </div>
      )}
    </Card>
  );
}

function CheckpointLadder({
  ladder,
  phase,
  status
}: {
  ladder: string[];
  phase: string | null;
  status: DurableIngestStatus;
}) {
  const activeIndex = phase ? ladder.indexOf(phase) : -1;
  const allDone = status === "completed";
  return (
    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 6, fontFamily: FONT_MONO, fontSize: 10 }}>
      {ladder.map((step, index) => {
        const done = allDone || (activeIndex >= 0 && index < activeIndex);
        const current = !allDone && index === activeIndex;
        const failed = current && (status === "failed" || status === "blocked" || status === "cancelled");
        const color = failed ? COLOR.red : current ? COLOR.cyan : done ? COLOR.green : COLOR.textFaint;
        return (
          <span key={step} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            {index > 0 && <span style={{ color: done || current ? COLOR.green : COLOR.border }}>→</span>}
            <span style={{ color }}>
              {done ? "✓ " : current ? (failed ? "✕ " : "◐ ") : "· "}
              {step}
            </span>
          </span>
        );
      })}
    </div>
  );
}

function TokenBars({ usage, estimate }: { usage: Record<string, number>; estimate: Record<string, number> }) {
  const keys = Array.from(new Set([...Object.keys(usage || {}), ...Object.keys(estimate || {})]));
  if (keys.length === 0) return null;
  return (
    <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 6 }}>
      {keys.map((key) => {
        const actual = usage?.[key] ?? 0;
        const est = estimate?.[key] ?? 0;
        const denom = Math.max(actual, est, 1);
        const actualPct = Math.min(100, (actual / denom) * 100);
        return (
          <div key={key} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, fontFamily: FONT_MONO }}>
            <Faint style={{ width: 130, flexShrink: 0 }}>{key}</Faint>
            <div style={{ flex: 1, height: 6, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, position: "relative" }}>
              <div style={{ position: "absolute", inset: 0, width: `${actualPct}%`, background: COLOR.cyan }} />
            </div>
            <span style={{ color: COLOR.text, minWidth: 90, textAlign: "right" }}>
              {actual}
              {est > 0 && <Faint> / {est} est</Faint>}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function WaitingCard({ payload }: { payload: Record<string, unknown> }) {
  return (
    <div style={{ marginTop: 10, border: `1px solid ${COLOR.amber}`, background: "#241d12", padding: "10px 14px" }}>
      <div style={{ color: COLOR.amber, fontSize: 12, fontWeight: 600, marginBottom: 6 }}>waiting for input</div>
      <pre
        style={{
          margin: 0,
          fontFamily: FONT_MONO,
          fontSize: 11,
          color: COLOR.textDim,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word"
        }}
      >
        {JSON.stringify(payload, null, 2)}
      </pre>
      <span
        style={{
          display: "inline-block",
          marginTop: 8,
          padding: "4px 12px",
          border: `1px solid ${COLOR.amber}`,
          color: COLOR.amber,
          fontSize: 11,
          fontFamily: FONT_MONO,
          cursor: "pointer"
        }}
      >
        resolve →
      </span>
    </div>
  );
}
