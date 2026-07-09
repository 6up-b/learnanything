import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type {
  ProposalBatchDto,
  ProposalItemDto,
  ProposalReviewRoute,
  ProposalSourceRefDto,
  ProposalsSnapshot
} from "../api/dto";
import { EntityLink } from "../components/ui";
import {
  COLOR,
  Dim,
  Faint,
  FONT_MONO,
  KeyBar,
  Meta,
  Pill,
  SectionHeader,
  type PillColor
} from "../components/term";

// ── Pills ──────────────────────────────────────────────────────────────
function RoutePill({ route }: { route: ProposalReviewRoute }) {
  if (route === "auto_apply") return <Pill color="green">auto_apply</Pill>;
  if (route === "review_required") return <Pill color="amber">review_required</Pill>;
  return <Pill color="red">reject</Pill>;
}

function DecisionPill({ decision }: { decision: string }) {
  if (decision === "accepted") return <Pill color="green">accepted</Pill>;
  if (decision === "rejected") return <Pill color="red">rejected</Pill>;
  if (decision === "pending") return <Pill color="amber">pending</Pill>;
  return <Pill color="slate">{decision}</Pill>;
}

const ITEM_TYPE_COLOR: Record<string, PillColor> = {
  learning_object: "purple",
  practice_item: "cyan",
  concept: "amber",
  concept_edge: "green",
  rubric: "slate",
  error_type: "red"
};

function ItemTypePill({ itemType }: { itemType: string }) {
  return <Pill color={ITEM_TYPE_COLOR[itemType] ?? "slate"}>{itemType.replace(/_/g, " ")}</Pill>;
}

function SourceRefPill({ source, onInspect }: { source: ProposalSourceRefDto; onInspect: (id: string) => void }) {
  const color: PillColor =
    source.kind === "note"
      ? "cyan"
      : source.kind === "canonical_source"
        ? "amber"
        : source.kind === "existing_entity"
          ? "green"
          : source.kind === "session"
          ? "purple"
          : "slate";
  if (!source.refId) {
    return <Pill color={color}>{source.label}</Pill>;
  }
  const targetId = source.refId;
  return (
    <span
      role="button"
      tabIndex={0}
      title={`learnloop show ${targetId}`}
      onClick={(event) => {
        event.stopPropagation();
        onInspect(targetId);
      }}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          event.stopPropagation();
          onInspect(targetId);
        }
      }}
      style={{ display: "inline-flex", cursor: "pointer" }}
    >
      <Pill color={color} style={{ textDecoration: "underline", textUnderlineOffset: 2 }}>{source.label}</Pill>
    </span>
  );
}

// ── Hero ───────────────────────────────────────────────────────────────
function ProposalsHero({
  totals,
  batchCount,
  codexRevision,
  authoringReady,
  authoringProvider,
  onPropose
}: {
  totals: { pending: number; accepted: number; rejected: number };
  batchCount: number;
  codexRevision: string | null;
  authoringReady: boolean;
  authoringProvider: string;
  onPropose?: () => void;
}) {
  const resolved = totals.accepted + totals.rejected;
  const stats = [
    { label: "PENDING", val: totals.pending, color: COLOR.amber },
    { label: "ACCEPTED", val: totals.accepted, color: COLOR.green },
    { label: "REJECTED", val: totals.rejected, color: COLOR.red },
    { label: "BATCHES", val: batchCount, color: COLOR.text }
  ];
  const Stat = ({ value, label, color }: { value: number; label: string; color: string }) => (
    <span style={{ whiteSpace: "nowrap" }}>
      <span style={{ color, fontWeight: 600 }}>{value}</span>{" "}
      <span style={{ color: COLOR.textDim }}>{label}</span>
    </span>
  );
  const sep = <span style={{ color: COLOR.textFaint, margin: "0 8px" }}>·</span>;
  return (
    <div
      style={{
        padding: "24px 32px 22px",
        background: COLOR.bg,
        borderBottom: `1px solid ${COLOR.border}`,
        display: "flex",
        gap: 32,
        alignItems: "flex-end",
        flexShrink: 0
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 13,
            color: COLOR.textFaint,
            letterSpacing: "0.02em",
            display: "flex",
            flexWrap: "wrap",
            alignItems: "baseline",
            rowGap: 4
          }}
        >
          <span style={{ textTransform: "uppercase", letterSpacing: "0.18em", color: COLOR.textFaint, fontSize: 11 }}>
            proposals · AI inbox
          </span>
          {sep}
          <Stat value={totals.pending} label="pending" color={COLOR.amber} />
          {sep}
          <Stat value={resolved} label="resolved" color={COLOR.green} />
          {sep}
          <Stat value={batchCount} label="batches" color={COLOR.text} />
        </div>

        <div style={{ marginTop: 12, fontSize: 13, color: COLOR.textDim, lineHeight: 1.65 }}>
          local app-server
          {codexRevision ? (
            <>
              {"  ·  "}revision{" "}
              <span style={{ color: COLOR.green, fontFamily: FONT_MONO }}>{codexRevision.slice(0, 7)}</span>
            </>
          ) : null}
          {"  ·  "}ai:{authoringProvider}{" "}
          <span style={{ color: authoringReady ? COLOR.green : COLOR.red }}>{authoringReady ? "● ready" : "● offline"}</span>
          {"  ·  "}every change routes through this inbox — providers never write files
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "row", alignItems: "stretch", gap: 10, flexShrink: 0 }}>
        {onPropose ? (
          <span
            onClick={onPropose}
            style={{
              padding: "0 14px",
              border: `1px solid ${COLOR.amber}`,
              background: "#241d12",
              color: COLOR.amber,
              fontSize: 12,
              fontWeight: 600,
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              fontFamily: FONT_MONO,
              whiteSpace: "nowrap"
            }}
          >
            + new proposal
          </span>
        ) : null}

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, auto)", gap: 0, border: `1px solid ${COLOR.border}` }}>
          {stats.map((s, i) => (
            <div
              key={s.label}
              style={{
                padding: "10px 16px",
                borderRight: i < stats.length - 1 ? `1px solid ${COLOR.border}` : "none",
                minWidth: 78,
                textAlign: "right",
                background: COLOR.bgElev
              }}
            >
              <div style={{ fontSize: 10, color: COLOR.textFaint, letterSpacing: "0.14em" }}>{s.label}</div>
              <div style={{ fontSize: 20, color: s.color, fontFamily: FONT_MONO, marginTop: 3, lineHeight: 1.1 }}>{s.val}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Batch header (collapsible) ─────────────────────────────────────────
function BatchHeader({
  batch,
  expanded,
  onToggle
}: {
  batch: ProposalBatchDto;
  expanded: boolean;
  onToggle: () => void;
}) {
  const { counts } = batch;
  const run = batch.agentRun;
  const lineage = [batch.id, batch.purpose, run.durationS != null ? `${run.durationS}s` : null, run.startedAt]
    .filter(Boolean)
    .join(" · ");
  return (
    <div
      onClick={onToggle}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 14,
        padding: "14px 24px",
        borderBottom: `1px solid ${COLOR.border}`,
        background: COLOR.bgElev,
        cursor: "pointer"
      }}
    >
      <span style={{ color: COLOR.amber, fontFamily: FONT_MONO, width: 14, fontSize: 13 }}>{expanded ? "▾" : "▸"}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ color: COLOR.text, fontWeight: 600, fontSize: 13, lineHeight: 1.4 }}>
          {batch.summary ?? "(no summary)"}
        </div>
        <div style={{ marginTop: 3 }}>
          <Meta style={{ fontSize: 11 }}>{lineage}</Meta>
        </div>
      </div>
      <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
        {counts.accepted > 0 ? <Pill color="green">{counts.accepted} accepted</Pill> : null}
        {counts.pending > 0 ? <Pill color="amber">{counts.pending} pending</Pill> : null}
        {counts.rejected > 0 ? <Pill color="red">{counts.rejected} rejected</Pill> : null}
      </div>
    </div>
  );
}

// ── Compact item row ───────────────────────────────────────────────────
function ProposalItemRow({
  item,
  focused,
  onSelect
}: {
  item: ProposalItemDto;
  focused: boolean;
  onSelect: () => void;
}) {
  return (
    <div
      onClick={onSelect}
      style={{
        padding: "12px 24px 12px 38px",
        background: focused ? COLOR.bgElev : "transparent",
        borderLeft: `3px solid ${focused ? COLOR.amber : "transparent"}`,
        cursor: "pointer",
        borderBottom: `1px solid ${COLOR.border}`,
        display: "grid",
        gridTemplateColumns: "1fr auto auto",
        gap: 14,
        alignItems: "center",
        transition: "background 100ms ease"
      }}
    >
      <div style={{ minWidth: 0 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", rowGap: 4, minWidth: 0 }}>
          <ItemTypePill itemType={item.itemType} />
          <span style={{ color: COLOR.textFaint }}>·</span>
          <span style={{ color: COLOR.amber, fontFamily: FONT_MONO, fontSize: 12 }}>{item.operation}</span>
          <span
            style={{
              color: COLOR.text,
              fontFamily: FONT_MONO,
              fontSize: 13,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              minWidth: 0
            }}
          >
            {item.proposedEntityId}
          </span>
        </div>
        <div style={{ marginTop: 4 }}>
          <Meta style={{ fontSize: 11 }}>{item.id}</Meta>
        </div>
      </div>
      <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
        <RoutePill route={item.reviewRoute} />
      </div>
      <div style={{ display: "flex", gap: 6, flexShrink: 0, minWidth: 92, justifyContent: "flex-end" }}>
        <DecisionPill decision={item.decision} />
      </div>
    </div>
  );
}

// ── Payload preview ────────────────────────────────────────────────────
function PayloadPreview({ lines }: { lines: Array<[string, string]> }) {
  if (lines.length === 0) {
    return <Faint style={{ fontSize: 12 }}>empty payload</Faint>;
  }
  return (
    <div
      style={{
        padding: "12px 14px",
        background: COLOR.bgInput,
        border: `1px solid ${COLOR.border}`,
        borderLeft: `3px solid ${COLOR.purplePill}`,
        fontFamily: FONT_MONO,
        fontSize: 12,
        lineHeight: 1.75
      }}
    >
      {lines.map(([key, value], index) => (
        <div key={index} style={{ display: "grid", gridTemplateColumns: "170px 1fr", gap: 8 }}>
          <span style={{ color: COLOR.cyan }}>{key}</span>
          <span style={{ color: COLOR.green, overflowWrap: "anywhere" }}>{value}</span>
        </div>
      ))}
    </div>
  );
}

// ── Action button ──────────────────────────────────────────────────────
function ActionButton({
  hotkey,
  label,
  color,
  background,
  disabled,
  onClick
}: {
  hotkey: string;
  label: string;
  color: string;
  background: string;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <span
      onClick={disabled ? undefined : onClick}
      style={{
        padding: "8px 16px",
        border: `1px solid ${color}`,
        background,
        color,
        fontSize: 13,
        fontWeight: 600,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.4 : 1,
        display: "inline-flex",
        gap: 8,
        alignItems: "center"
      }}
    >
      <span style={{ fontWeight: 700 }}>[{hotkey}]</span> {label}
    </span>
  );
}

// ── Detail pane (right) ────────────────────────────────────────────────
function ProposalDetail({
  item,
  batch,
  busy,
  onAccept,
  onReject,
  onUndo,
  onRefreshValidation,
  onInspect,
  onHandoff
}: {
  item: ProposalItemDto | undefined;
  batch: ProposalBatchDto | undefined;
  busy: boolean;
  onAccept: () => void;
  onReject: () => void;
  onUndo: () => void;
  onRefreshValidation: () => void;
  onInspect: (id: string) => void;
  onHandoff?: (patchId: string, itemId: string) => void;
}) {
  if (!item || !batch) {
    return <div style={{ padding: 30, color: COLOR.textFaint, fontSize: 13 }}>no item selected</div>;
  }
  const run = batch.agentRun;
  const isPending = item.decision === "pending";
  const isAccepted = item.decision === "accepted";
  const canAccept = item.validationStatus !== "invalid";
  const canUndo = item.decision === "rejected" && !item.applied;
  const canRefreshValidation = isPending && item.validationStatus === "invalid";

  return (
    <div style={{ padding: "20px 22px" }}>
      <div style={{ fontSize: 11, color: COLOR.textFaint, marginBottom: 4, fontFamily: FONT_MONO }}>
        {item.id}
        {item.clientItemId ? <> · client {item.clientItemId}</> : null}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap", rowGap: 4 }}>
        <span style={{ color: COLOR.amber, fontFamily: FONT_MONO, fontSize: 13 }}>{item.operation}</span>
        <span style={{ fontFamily: FONT_MONO, fontSize: 17, color: COLOR.text, fontWeight: 600, overflowWrap: "anywhere" }}>
          <EntityLink id={item.proposedEntityId} onInspect={onInspect} />
        </span>
      </div>
      <div style={{ marginTop: 8, display: "flex", gap: 6, flexWrap: "wrap" }}>
        <ItemTypePill itemType={item.itemType} />
        <RoutePill route={item.reviewRoute} />
        <DecisionPill decision={item.decision} />
        {item.edited ? <Pill color="amber">edited</Pill> : null}
        {item.applied ? <Pill color="slate">applied</Pill> : null}
      </div>

      <SectionHeader>Rationale</SectionHeader>
      <div style={{ fontSize: 13, lineHeight: 1.6, color: COLOR.text }}>{item.rationale || <Faint>—</Faint>}</div>

      <SectionHeader>Source refs</SectionHeader>
      {item.sourceRefs.length ? (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {item.sourceRefs.map((source, index) => (
            <SourceRefPill key={index} source={source} onInspect={onInspect} />
          ))}
        </div>
      ) : (
        <Faint style={{ fontSize: 12 }}>no source refs</Faint>
      )}

      <SectionHeader>Payload</SectionHeader>
      <div style={{ position: "relative" }}>
        <PayloadPreview lines={item.payloadLines} />
        {onHandoff ? (
          <span
            onClick={() => onHandoff(batch.id, item.id)}
            title="open in Library editor"
            style={{
              position: "absolute",
              right: 6,
              bottom: 6,
              cursor: "pointer",
              color: COLOR.purpleText,
              background: COLOR.bgElev,
              border: `1px solid ${COLOR.borderStrong}`,
              borderRadius: 2,
              padding: "0 7px",
              fontSize: 13,
              lineHeight: "20px",
              fontFamily: FONT_MONO
            }}
          >
            ⤢
          </span>
        ) : null}
      </div>

      <div style={{ marginTop: 22, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
        <SectionHeader style={{ marginTop: 0, marginBottom: 0, flex: 1 }}>Validation</SectionHeader>
        {canRefreshValidation ? (
          <span
            onClick={busy ? undefined : onRefreshValidation}
            title="rerun validation"
            style={{
              width: 22,
              height: 22,
              border: `1px solid ${COLOR.borderStrong}`,
              background: COLOR.bgElev,
              color: busy ? COLOR.textFaint : COLOR.amber,
              cursor: busy ? "not-allowed" : "pointer",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: FONT_MONO,
              fontSize: 12,
              lineHeight: 1,
              opacity: busy ? 0.5 : 1
            }}
          >
            {busy ? "..." : "↻"}
          </span>
        ) : null}
      </div>
      {item.validationStatus === "valid" ? (
        <div style={{ fontSize: 12, color: COLOR.green }}>✓ schema · refs resolve · no id collision</div>
      ) : (
        <div style={{ fontSize: 12, color: item.validationStatus === "invalid" ? COLOR.red : COLOR.amber }}>
          {item.validationStatus === "invalid" ? "✗ " : "⚠ "}
          {item.validationErrors.length ? item.validationErrors.join(" · ") : `failed ${item.validationStatus} check`}
        </div>
      )}

      <SectionHeader>Origin</SectionHeader>
      <div style={{ display: "grid", gridTemplateColumns: "130px 1fr", rowGap: 4, fontSize: 12 }}>
        <Faint>batch</Faint>
        <Dim style={{ fontFamily: FONT_MONO }}>{batch.id}</Dim>
        <Faint>agent_run</Faint>
        <Dim style={{ fontFamily: FONT_MONO }}>{run.id}</Dim>
        <Faint>purpose</Faint>
        <span style={{ color: COLOR.text }}>{run.purpose ?? "—"}</span>
        <Faint>model</Faint>
        <Dim>{run.model ?? "—"}</Dim>
        <Faint>codex revision</Faint>
        <Dim style={{ fontFamily: FONT_MONO }}>{run.codexRevision ? run.codexRevision.slice(0, 7) : "—"}</Dim>
        <Faint>started</Faint>
        <Dim>{run.startedAt ?? "—"}</Dim>
        <Faint>duration</Faint>
        <Dim>{run.durationS != null ? `${run.durationS}s` : run.status === "running" ? "running…" : "—"}</Dim>
      </div>

      <div style={{ marginTop: 22, display: "flex", gap: 8, flexWrap: "wrap" }}>
        {isPending ? (
          <>
            <ActionButton
              hotkey="a"
              label="Accept"
              color={COLOR.green}
              background="#13251a"
              disabled={busy || !canAccept}
              onClick={onAccept}
            />
            <ActionButton hotkey="r" label="Reject" color={COLOR.red} background="#251313" disabled={busy} onClick={onReject} />
          </>
        ) : isAccepted ? (
          <ActionButton
            hotkey="r"
            label={item.applied ? "Reject (revert)" : "Reject"}
            color={COLOR.red}
            background="#251313"
            disabled={busy}
            onClick={onReject}
          />
        ) : canUndo ? (
          <ActionButton hotkey="u" label="Undo decision" color={COLOR.amber} background={COLOR.bgElev} disabled={busy} onClick={onUndo} />
        ) : (
          <Faint style={{ fontSize: 12 }}>reverted — applied change rolled back; this decision is final</Faint>
        )}
      </div>
    </div>
  );
}

// ── Main screen ────────────────────────────────────────────────────────
export function ProposalsScreen({
  authoringReady,
  authoringProvider,
  onInspect,
  onPaletteEntities,
  onError,
  onHandoff
}: {
  authoringReady: boolean;
  authoringProvider: string;
  onInspect: (id: string) => void;
  onPaletteEntities?: (ids: { inspectIds: string[]; practiceItemIds: string[] }) => void;
  onError: (message: string) => void;
  onHandoff?: (patchId: string, itemId: string) => void;
}) {
  const [snapshot, setSnapshot] = useState<ProposalsSnapshot | null>(null);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [focusedItemId, setFocusedItemId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const applySnapshot = useCallback((next: ProposalsSnapshot) => {
    setSnapshot(next);
    setFocusedItemId((current) => {
      const all = next.batches.flatMap((batch) => batch.items.map((item) => item.id));
      if (current && all.includes(current)) return current;
      return all[0] ?? null;
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .getProposals()
      .then((next) => {
        if (!cancelled) applySnapshot(next);
      })
      .catch((error) => {
        if (!cancelled) onError(error.message);
      });
    return () => {
      cancelled = true;
    };
  }, [applySnapshot, onError]);

  useEffect(() => {
    if (!onPaletteEntities) return;
    const items = snapshot?.batches.flatMap((batch) => batch.items) ?? [];
    const inspectIds = uniqueIds(
      items.flatMap((item) => [
        item.proposedEntityId,
        item.targetEntityId,
        ...item.sourceRefs.map((source) => source.refId),
      ])
    );
    const practiceItemIds = uniqueIds(
      items
        .filter((item) => item.itemType === "practice_item")
        .map((item) => item.proposedEntityId)
    );
    onPaletteEntities({ inspectIds, practiceItemIds });
    return () => onPaletteEntities({ inspectIds: [], practiceItemIds: [] });
  }, [snapshot, onPaletteEntities]);

  // Items in display order, skipping collapsed batches — drives j/k navigation.
  const visibleItems = useMemo(() => {
    if (!snapshot) return [] as ProposalItemDto[];
    return snapshot.batches.flatMap((batch) => (collapsed.has(batch.id) ? [] : batch.items));
  }, [snapshot, collapsed]);

  const focusedItem = useMemo(
    () => (snapshot ? snapshot.batches.flatMap((batch) => batch.items).find((item) => item.id === focusedItemId) : undefined),
    [snapshot, focusedItemId]
  );
  const focusedBatch = useMemo(
    () => snapshot?.batches.find((batch) => batch.items.some((item) => item.id === focusedItemId)),
    [snapshot, focusedItemId]
  );

  const runMutation = useCallback(
    async (action: () => Promise<ProposalsSnapshot>) => {
      if (busy) return;
      setBusy(true);
      try {
        applySnapshot(await action());
      } catch (error) {
        onError((error as Error).message);
      } finally {
        setBusy(false);
      }
    },
    [busy, applySnapshot, onError]
  );

  const accept = useCallback(() => {
    if (!focusedBatch || !focusedItem || focusedItem.validationStatus === "invalid" || focusedItem.decision !== "pending") return;
    void runMutation(() => api.acceptProposalItems(focusedBatch.id, [focusedItem.id]));
  }, [focusedBatch, focusedItem, runMutation]);

  const reject = useCallback(() => {
    if (!focusedBatch || !focusedItem || focusedItem.decision === "rejected") return;
    void runMutation(() => api.rejectProposalItems(focusedBatch.id, [focusedItem.id]));
  }, [focusedBatch, focusedItem, runMutation]);

  const undo = useCallback(() => {
    if (!focusedBatch || !focusedItem || focusedItem.decision !== "rejected" || focusedItem.applied) return;
    void runMutation(() => api.resetProposalItems(focusedBatch.id, [focusedItem.id]));
  }, [focusedBatch, focusedItem, runMutation]);

  const refreshValidation = useCallback(() => {
    if (!focusedBatch || !focusedItem || focusedItem.decision !== "pending") return;
    void runMutation(() => api.refreshProposalItemValidation(focusedBatch.id, focusedItem.id));
  }, [focusedBatch, focusedItem, runMutation]);

  // Bulk-accept every still-pending auto_apply item, batch by batch.
  const bulkAcceptAutoApply = useCallback(() => {
    if (!snapshot) return;
    const byBatch = snapshot.batches
      .map((batch) => ({
        id: batch.id,
        itemIds: batch.items
          .filter((item) => item.decision === "pending" && item.reviewRoute === "auto_apply" && item.validationStatus !== "invalid")
          .map((item) => item.id)
      }))
      .filter((entry) => entry.itemIds.length > 0);
    if (byBatch.length === 0) return;
    void runMutation(async () => {
      let latest = snapshot;
      for (const entry of byBatch) {
        latest = await api.acceptProposalItems(entry.id, entry.itemIds);
      }
      return latest;
    });
  }, [snapshot, runMutation]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;
      const index = focusedItemId ? visibleItems.findIndex((item) => item.id === focusedItemId) : -1;
      if (["j", "ArrowDown"].includes(event.key)) {
        const next = visibleItems[Math.min(visibleItems.length - 1, index + 1)];
        if (next) setFocusedItemId(next.id);
        event.preventDefault();
      } else if (["k", "ArrowUp"].includes(event.key)) {
        const prev = visibleItems[Math.max(0, index - 1)];
        if (prev) setFocusedItemId(prev.id);
        event.preventDefault();
      } else if (event.key === "a") {
        accept();
        event.preventDefault();
      } else if (event.key === "r") {
        reject();
        event.preventDefault();
      } else if (event.key === "u") {
        undo();
        event.preventDefault();
      } else if (event.key === "A") {
        bulkAcceptAutoApply();
        event.preventDefault();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [visibleItems, focusedItemId, accept, reject, undo, bulkAcceptAutoApply]);

  function toggleBatch(id: string) {
    setCollapsed((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const codexRevision = useMemo(() => {
    if (!snapshot) return null;
    for (const batch of snapshot.batches) {
      if (batch.agentRun.codexRevision) return batch.agentRun.codexRevision;
    }
    return null;
  }, [snapshot]);

  if (!snapshot) {
    return (
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: COLOR.textFaint, fontSize: 13 }}>
        loading proposals…
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <ProposalsHero
        totals={snapshot.totals}
        batchCount={snapshot.batchCount}
        codexRevision={codexRevision}
        authoringReady={authoringReady}
        authoringProvider={authoringProvider}
      />

      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        {/* Master list */}
        <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", minHeight: 0 }}>
          {snapshot.batches.length === 0 ? (
            <div style={{ padding: 40, color: COLOR.textFaint, fontSize: 13 }}>
              No proposals yet. AI authoring runs land here for review before anything touches the vault.
            </div>
          ) : (
            snapshot.batches.map((batch) => {
              const expanded = !collapsed.has(batch.id);
              return (
                <div key={batch.id}>
                  <BatchHeader batch={batch} expanded={expanded} onToggle={() => toggleBatch(batch.id)} />
                  {expanded
                    ? batch.items.map((item) => (
                        <ProposalItemRow
                          key={item.id}
                          item={item}
                          focused={focusedItemId === item.id}
                          onSelect={() => setFocusedItemId(item.id)}
                        />
                      ))
                    : null}
                </div>
              );
            })
          )}

          {/* policy note at bottom */}
          <div
            style={{
              margin: "28px 24px",
              padding: "14px 18px",
              border: `1px dashed ${COLOR.border}`,
              fontSize: 12,
              color: COLOR.textDim,
              lineHeight: 1.7
            }}
          >
            <span style={{ color: COLOR.amber, fontSize: 10, textTransform: "uppercase", letterSpacing: "0.14em", fontWeight: 700 }}>
              review policy · spec §7
            </span>
            <div style={{ marginTop: 6 }}>
              <span style={{ color: COLOR.green }}>auto_apply</span> · direct source-grounded extractions that pass schema + ref resolution.
            </div>
            <div>
              <span style={{ color: COLOR.amber }}>review_required</span> · existing-entity modifications, transfers, misconceptions, weak grounding.
            </div>
            <div>
              <span style={{ color: COLOR.red }}>reject</span> · unresolved refs, duplicate ids, invalid edges, schema failures.
            </div>
          </div>
        </div>

        {/* Detail pane */}
        <div
          className="ll-scroll"
          style={{ width: 420, flexShrink: 0, borderLeft: `1px solid ${COLOR.border}`, background: COLOR.bg, overflowY: "auto" }}
        >
          <ProposalDetail
            item={focusedItem}
            batch={focusedBatch}
            busy={busy}
            onAccept={accept}
            onReject={reject}
            onUndo={undo}
            onRefreshValidation={refreshValidation}
            onInspect={onInspect}
            onHandoff={onHandoff}
          />
        </div>
      </div>

      <KeyBar
        keys={[
          { key: "j/k", label: "Move" },
          { key: "a", label: "Accept" },
          { key: "r", label: "Reject" },
          { key: "u", label: "Undo" },
          { key: "A", label: "Bulk accept auto_apply" }
        ]}
        right={{ key: "^p", label: "palette" }}
      />
    </div>
  );
}

function uniqueIds(values: Array<string | null | undefined>): string[] {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value))));
}
