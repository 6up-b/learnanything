import { useCallback, useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { api } from "../api/client";
import type {
  CommandError,
  DurableIngestStatus,
  IngestBatchDto,
  IngestJobView,
  SourceLibraryCard,
  SourceReadiness
} from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill, SectionHeader, type PillColor } from "./term";

// Durable ingest surfaces (source-ingestion v2 §5.7): the Source library card
// grid and the Batch-progress checkpoint ladder. These sit alongside the legacy
// single-source form under the Ingest tab's view switch.

export type IngestView = "library" | "add" | "batches";

const STATUS_PILL: Record<DurableIngestStatus, PillColor> = {
  queued: "slate",
  running: "cyan",
  waiting_for_input: "amber",
  completed: "green",
  failed: "red",
  blocked: "purple",
  cancelled: "slate"
};

const READINESS_META: Record<SourceReadiness, { color: string; label: string }> = {
  ready: { color: COLOR.green, label: "ready" },
  processing: { color: COLOR.cyan, label: "processing" },
  needs_extraction: { color: COLOR.amber, label: "needs extraction" }
};

function statusLabel(status: DurableIngestStatus): string {
  return status.replace(/_/g, " ");
}

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

// ── View switcher (terminal segmented tabs) ─────────────────────────────
export function IngestViewTabs({ view, onChange }: { view: IngestView; onChange: (view: IngestView) => void }) {
  const tabs: Array<{ id: IngestView; label: string }> = [
    { id: "library", label: "▤ source library" },
    { id: "add", label: "＋ add source" },
    { id: "batches", label: "◲ batch progress" }
  ];
  return (
    <div
      style={{
        display: "flex",
        gap: 4,
        padding: "10px 24px",
        borderBottom: `1px solid ${COLOR.border}`,
        background: COLOR.bgElev,
        flexShrink: 0
      }}
    >
      {tabs.map((tab) => {
        const sel = tab.id === view;
        return (
          <span
            key={tab.id}
            onClick={() => onChange(tab.id)}
            style={{
              padding: "5px 14px",
              fontSize: 12,
              fontFamily: FONT_MONO,
              border: `1px solid ${sel ? COLOR.amber : COLOR.border}`,
              background: sel ? "#241d12" : "transparent",
              color: sel ? COLOR.amber : COLOR.textDim,
              cursor: "pointer"
            }}
          >
            {tab.label}
          </span>
        );
      })}
    </div>
  );
}

// ── Source library card grid ────────────────────────────────────────────
export function SourceLibraryView({ onOpenBatch }: { onOpenBatch: (batchId: string) => void }) {
  const [sources, setSources] = useState<SourceLibraryCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [quickSource, setQuickSource] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const snapshot = await api.getSourceLibrary();
      setSources(snapshot.sources);
    } catch {
      setSources([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function quickAdd() {
    const src = quickSource.trim();
    if (!src || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const batch = await api.startImportBatch({ sources: [src] });
      setQuickSource("");
      onOpenBatch(batch.id);
    } catch (e) {
      setError((e as CommandError).message);
    } finally {
      setSubmitting(false);
      void refresh();
    }
  }

  return (
    <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: "18px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
        <SectionHeader style={{ marginTop: 0 }}>Quick add</SectionHeader>
        <Faint>fetch → extract → durable queue, defaults auto-chosen</Faint>
      </div>
      <div
        style={{
          border: `1px solid ${quickSource.trim() ? COLOR.amber : COLOR.border}`,
          background: COLOR.bgInput,
          padding: "10px 92px 10px 36px",
          position: "relative"
        }}
      >
        <span style={{ position: "absolute", left: 14, top: 12, color: COLOR.amber, fontWeight: 700 }}>❯</span>
        <input
          value={quickSource}
          onChange={(e) => setQuickSource(e.target.value)}
          onKeyDown={(e) => {
            e.stopPropagation();
            if (e.key === "Enter") void quickAdd();
          }}
          placeholder="paste a URL, arXiv id, PDF path, or local .md / .txt file"
          style={{
            width: "100%",
            background: "transparent",
            color: COLOR.text,
            border: "none",
            outline: "none",
            fontFamily: FONT_MONO,
            fontSize: 13
          }}
        />
        <span
          onClick={() => void quickAdd()}
          style={{
            position: "absolute",
            right: 12,
            top: 10,
            color: submitting ? COLOR.textFaint : COLOR.amberLink,
            cursor: submitting ? "default" : "pointer",
            fontSize: 11,
            fontFamily: FONT_MONO
          }}
        >
          {submitting ? "…" : "import →"}
        </span>
      </div>
      {error && <div style={{ color: COLOR.red, fontSize: 12 }}>{error}</div>}

      <div style={{ display: "flex", alignItems: "baseline", gap: 14, marginTop: 4 }}>
        <SectionHeader style={{ marginTop: 0 }}>Source library</SectionHeader>
        {sources.length > 0 && <Faint>{sources.length} sources</Faint>}
      </div>
      {loading ? (
        <Faint>◐ loading…</Faint>
      ) : sources.length === 0 ? (
        <div style={{ padding: "14px 16px", border: `1px dashed ${COLOR.border}`, fontSize: 12, color: COLOR.textDim, lineHeight: 1.6 }}>
          <span style={{ color: COLOR.amber }}>no sources yet</span> — quick-add a file or URL above, or use{" "}
          <span style={{ color: COLOR.green }}>add source</span> for the full single-source flow. Imported sources register a
          revision + extraction run and show up here as cards.
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
          {sources.map((card) => (
            <SourceCard key={card.sourceId} card={card} />
          ))}
        </div>
      )}
    </div>
  );
}

function SourceCard({ card }: { card: SourceLibraryCard }) {
  const readiness = READINESS_META[card.readiness];
  return (
    <Card style={{ display: "flex", flexDirection: "column", gap: 8, borderLeft: `3px solid ${readiness.color}` }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
        <span
          style={{
            flex: 1,
            minWidth: 0,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            color: COLOR.text,
            fontSize: 13,
            fontWeight: 600
          }}
          title={card.title}
        >
          {card.title}
        </span>
        {card.acquisitionKind && <Pill color="slate">{card.acquisitionKind}</Pill>}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 11, fontFamily: FONT_MONO }}>
        <span style={{ color: readiness.color }}>● {readiness.label}</span>
        <Faint>
          {card.unitCount} units · {card.blockCount} blocks
        </Faint>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 11 }}>
        <Faint>role {card.suggestedRole ?? "—"}</Faint>
        <span style={{ flex: 1 }} />
        {card.updateAvailable && <Pill color="amber">update available</Pill>}
      </div>
    </Card>
  );
}

// ── Batch progress ──────────────────────────────────────────────────────
export function BatchProgressView({
  selectedBatchId,
  onSelect
}: {
  selectedBatchId: string | null;
  onSelect: (batchId: string | null) => void;
}) {
  const [batches, setBatches] = useState<IngestBatchDto[]>([]);
  const [detail, setDetail] = useState<IngestBatchDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const detailRef = useRef<string | null>(null);

  const refreshList = useCallback(async () => {
    try {
      const snapshot = await api.listIngestBatches();
      setBatches(snapshot.batches);
    } catch {
      setBatches([]);
    }
  }, []);

  useEffect(() => {
    void refreshList();
    const id = window.setInterval(() => void refreshList(), 2000);
    return () => window.clearInterval(id);
  }, [refreshList]);

  // Poll the selected batch while it is active.
  useEffect(() => {
    detailRef.current = selectedBatchId;
    if (!selectedBatchId) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    let timer: number | undefined;
    const poll = async () => {
      try {
        const batch = await api.getIngestBatch(selectedBatchId);
        if (cancelled) return;
        setDetail(batch);
        setError(null);
        if (isActive(batch.status)) timer = window.setTimeout(() => void poll(), 1000);
      } catch (e) {
        if (cancelled) return;
        setError((e as CommandError).message);
      }
    };
    void poll();
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [selectedBatchId]);

  async function cancel(batchId: string) {
    try {
      setDetail(await api.cancelIngestBatch(batchId));
      void refreshList();
    } catch (e) {
      setError((e as CommandError).message);
    }
  }

  async function resume(batchId: string) {
    try {
      setDetail(await api.resumeIngestBatch(batchId));
      void refreshList();
    } catch (e) {
      setError((e as CommandError).message);
    }
  }

  return (
    <div style={{ flex: 1, display: "grid", gridTemplateColumns: "280px 1fr", minHeight: 0 }}>
      <div style={{ borderRight: `1px solid ${COLOR.border}`, display: "flex", flexDirection: "column", minHeight: 0 }}>
        <div
          style={{
            padding: "10px 14px",
            fontSize: 12,
            color: COLOR.amber,
            textDecoration: "underline",
            textUnderlineOffset: 3,
            background: COLOR.bgElev,
            borderBottom: `1px solid ${COLOR.border}`
          }}
        >
          batches
        </div>
        <div className="ll-scroll" style={{ flex: 1, overflowY: "auto" }}>
          {batches.length === 0 ? (
            <div style={{ padding: "14px 12px", fontSize: 12, color: COLOR.textFaint }}>no batches yet.</div>
          ) : (
            batches.map((batch) => {
              const sel = batch.id === selectedBatchId;
              const done = batch.jobs.filter((job) => job.status === "completed").length;
              return (
                <div
                  key={batch.id}
                  onClick={() => onSelect(batch.id)}
                  style={{
                    padding: "8px 12px",
                    borderBottom: `1px solid ${COLOR.border}`,
                    borderLeft: `2px solid ${sel ? COLOR.amber : "transparent"}`,
                    background: sel ? COLOR.bgElev : "transparent",
                    cursor: "pointer",
                    display: "flex",
                    flexDirection: "column",
                    gap: 4
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <Pill color={STATUS_PILL[batch.status]}>{statusLabel(batch.status)}</Pill>
                    <Faint style={{ fontSize: 11 }}>{batch.workflowType}</Faint>
                  </div>
                  <Faint style={{ fontSize: 11, fontFamily: FONT_MONO }}>
                    {done}/{batch.jobs.length} jobs · {batch.id.slice(0, 16)}
                  </Faint>
                </div>
              );
            })
          )}
        </div>
      </div>

      <div className="ll-scroll" style={{ overflowY: "auto", padding: "18px 24px" }}>
        {error && <div style={{ color: COLOR.red, fontSize: 12, marginBottom: 12 }}>{error}</div>}
        {!detail ? (
          <Faint>select a batch to watch its checkpoint ladder.</Faint>
        ) : (
          <BatchDetail batch={detail} onCancel={() => void cancel(detail.id)} onResume={() => void resume(detail.id)} />
        )}
      </div>
    </div>
  );
}

function BatchDetail({ batch, onCancel, onResume }: { batch: IngestBatchDto; onCancel: () => void; onResume: () => void }) {
  const active = isActive(batch.status);
  const resumable = batch.status === "failed" || batch.status === "cancelled";
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <SectionHeader style={{ marginTop: 0 }}>Batch {batch.id.slice(0, 20)}</SectionHeader>
        <Pill color={STATUS_PILL[batch.status]}>{statusLabel(batch.status)}</Pill>
        <span style={{ flex: 1 }} />
        {active && (
          <span onClick={onCancel} style={{ color: COLOR.red, cursor: "pointer", fontSize: 12, fontFamily: FONT_MONO }}>
            cancel
          </span>
        )}
        {resumable && (
          <span onClick={onResume} style={{ color: COLOR.green, cursor: "pointer", fontSize: 12, fontFamily: FONT_MONO }}>
            ↻ resume
          </span>
        )}
      </div>
      {batch.jobs.map((job) => (
        <JobRow key={job.id} job={job} />
      ))}
    </div>
  );
}

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

      {job.message && (
        <div style={{ marginTop: 8, fontSize: 12, color: COLOR.textDim }}>{job.message}</div>
      )}

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

const STATUS_COLOR: Record<DurableIngestStatus, string> = {
  queued: COLOR.textFaint,
  running: COLOR.cyan,
  waiting_for_input: COLOR.amber,
  completed: COLOR.green,
  failed: COLOR.red,
  blocked: COLOR.purplePill,
  cancelled: COLOR.textFaint
};

function isActive(status: DurableIngestStatus): boolean {
  return status === "queued" || status === "running" || status === "waiting_for_input";
}
