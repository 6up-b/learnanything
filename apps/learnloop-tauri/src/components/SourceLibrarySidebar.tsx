import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type {
  CommandError,
  SourceLibraryCard,
  SourceReadiness,
  SourceSetDto,
  SourceSetSummaryDto
} from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill } from "./term";
import { AddToCollectionPanel } from "./AddToCollection";
import { youtubeVideoId } from "./sourceTail";

// Left-sidebar successor to the legacy "recent ingests" column: the v2
// source-library cards in compact row form. Mirrors RecentIngestRow's header
// strip / row / ll-scroll structure (see IngestScreen), replacing the old
// SourceLibraryView card grid. Below the source list is the collections
// (source-set) section — each set expands to its members, and "synthesize →"
// enqueues a study-map build batch (§4.3/§8).

// ── Readiness palette (ready→green, processing→cyan, needs_extraction→amber) ──
const READINESS_META: Record<SourceReadiness, { color: string; label: string }> = {
  ready: { color: COLOR.green, label: "ready" },
  processing: { color: COLOR.cyan, label: "processing…" },
  needs_extraction: { color: COLOR.amber, label: "needs extraction" }
};

// Backend titles for local files are raw file:// URIs — show a readable tail
// (basename) instead; the full title stays available in the hover tooltip.
function readableTitle(title: string): string {
  // YouTube watch URLs hide the id in the ?v= query — the plain query-strip below
  // would yield just "watch"; surface "youtube · <id>" instead.
  const vid = youtubeVideoId(title);
  if (vid) return `youtube · ${vid}`;
  if (!/^[a-z][a-z0-9+.-]*:\/\//i.test(title) && !title.includes("/")) return title;
  const trimmed = title.replace(/[/\\]+$/, "");
  const tail = trimmed.split(/[?#]/)[0].split(/[/\\]/).filter(Boolean).pop();
  return tail || title;
}

export function SourceLibrarySidebar({
  onOpenOutline,
  onFocusSource,
  onCreateStudyMap,
  onOpenBatch,
  refreshToken
}: {
  onOpenOutline: (card: SourceLibraryCard) => void;
  onFocusSource: (card: SourceLibraryCard) => void;
  onCreateStudyMap?: () => void;
  onOpenBatch?: (batchId: string) => void;
  refreshToken?: number;
}): JSX.Element {
  const [sources, setSources] = useState<SourceLibraryCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Which ready row has its "add to collection" panel open (sourceId), and a
  // token that bumps to re-fetch the collections list after a membership change.
  const [addTarget, setAddTarget] = useState<string | null>(null);
  const [collectionsRefresh, setCollectionsRefresh] = useState(0);
  const firstLoad = useRef(true);

  // ── Data load — keep last data on error, surface only first-load failures ──
  const refresh = useCallback(async () => {
    try {
      const snapshot = await api.getSourceLibrary();
      setSources(snapshot.sources);
      setError(null);
    } catch (e) {
      if (firstLoad.current) setError((e as CommandError).message);
    } finally {
      firstLoad.current = false;
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh, refreshToken]);

  // ── Poll while any source is still processing ──
  const anyProcessing = sources.some((card) => card.readiness === "processing");
  useEffect(() => {
    if (!anyProcessing) return;
    const id = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(id);
  }, [anyProcessing, refresh]);

  function selectCard(card: SourceLibraryCard) {
    setSelected(card.sourceId);
    if (card.readiness === "ready") onOpenOutline(card);
    else onFocusSource(card);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      {/* ── header strip ── */}
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
        <span>source library</span>
        {sources.length > 0 && <Faint style={{ fontSize: 11, textDecoration: "none" }}>{sources.length}</Faint>}
      </div>

      {/* ── create study map ── */}
      {onCreateStudyMap && (
        <span
          onClick={onCreateStudyMap}
          title="Turn one source into a complete study map: paste a URL or file, LearnLoop imports and outlines it, plans subjects, learning objects, and practice items, and asks for a single confirmation before building. Use this when starting a new topic from scratch; use the source input on the right to add material to an existing library."
          style={{
            margin: 8,
            border: `1px solid ${COLOR.amber}`,
            background: "#241d12",
            color: COLOR.amber,
            fontFamily: FONT_MONO,
            fontSize: 11,
            padding: "6px 12px",
            cursor: "pointer",
            textAlign: "center"
          }}
        >
          ＋ create study map
        </span>
      )}

      {/* ── scrollable body ── */}
      <div className="ll-scroll" style={{ flex: 1, overflowY: "auto" }}>
        {error && <div style={{ padding: "10px 12px", fontSize: 11, color: COLOR.red }}>{error}</div>}
        {loading ? (
          <div style={{ padding: "14px 12px", fontSize: 12, color: COLOR.textFaint }}>◐ loading…</div>
        ) : sources.length === 0 ? (
          <div style={{ padding: "14px 12px", fontSize: 12, color: COLOR.textFaint, lineHeight: 1.6 }}>
            no sources yet — paste a URL or file in the source input to import your first source.
          </div>
        ) : (
          sources.map((card) => (
            <div key={card.sourceId}>
              <SourceRow
                card={card}
                selected={selected === card.sourceId}
                onSelect={() => selectCard(card)}
                onAddToCollection={() => setAddTarget((cur) => (cur === card.sourceId ? null : card.sourceId))}
              />
              {addTarget === card.sourceId && (
                <div style={{ padding: "0 10px 10px" }}>
                  <AddToCollectionPanel
                    sourceId={card.sourceId}
                    revisionId={card.currentRevisionId}
                    scopeUnitIds={[]}
                    seedRole={card.suggestedRole}
                    onClose={() => setAddTarget(null)}
                    onAdded={() => {
                      setAddTarget(null);
                      setCollectionsRefresh((n) => n + 1);
                    }}
                  />
                </div>
              )}
            </div>
          ))
        )}

        <CollectionsSection
          sources={sources}
          refreshToken={collectionsRefresh}
          onSynthesize={(batchId) => {
            setCollectionsRefresh((n) => n + 1);
            onOpenBatch?.(batchId);
          }}
        />
      </div>
    </div>
  );
}

// ── Row — mirrors RecentIngestRow ──
function SourceRow({
  card,
  selected,
  onSelect,
  onAddToCollection
}: {
  card: SourceLibraryCard;
  selected: boolean;
  onSelect: () => void;
  onAddToCollection: () => void;
}) {
  const readiness = READINESS_META[card.readiness];
  const isReady = card.readiness === "ready";
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
      {/* line 1: readiness dot + title */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ color: readiness.color }} title={readiness.label}>
          ●
        </span>
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
          title={card.title}
        >
          {readableTitle(card.title)}
        </span>
      </div>

      {/* line 2: counts, pills */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11 }}>
        <Faint style={{ fontFamily: FONT_MONO }}>
          {card.unitCount} units · {card.blockCount} blocks
        </Faint>
        {card.suggestedRole && (
          <span
            title="suggested role — authority is decided per collection membership, not on the source; auto-suggestions are always explanatory (never exam or problem_set)"
            style={{ color: COLOR.textFaint, fontSize: 11, cursor: "help" }}
          >
            role {card.suggestedRole}
          </span>
        )}
        <span style={{ flex: 1 }} />
        {card.acquisitionKind && <Pill color="slate">{card.acquisitionKind}</Pill>}
        {card.updateAvailable && <Pill color="amber">update</Pill>}
      </div>

      {/* line 3: readiness label, or the outline + add-to-collection affordances */}
      {isReady ? (
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span
            style={{
              fontSize: 11,
              fontFamily: FONT_MONO,
              color: COLOR.amberLink,
              textDecoration: "underline",
              textUnderlineOffset: 2
            }}
          >
            outline &amp; select →
          </span>
          <span
            onClick={(e) => {
              e.stopPropagation();
              onAddToCollection();
            }}
            title="pin this source (at its current revision) into a collection with a role — the unit that synthesis groups and reads"
            style={{ fontSize: 11, fontFamily: FONT_MONO, color: COLOR.textFaint, cursor: "pointer" }}
          >
            ＋ collection
          </span>
        </div>
      ) : (
        <Faint style={{ fontSize: 11 }}>{readiness.label}</Faint>
      )}
    </div>
  );
}

// ── Collections (source sets, §4.3) ──────────────────────────────────────
// Compact rows below the source list; click expands members inline. "synthesize →"
// enqueues the mode-aware study-map build batch, surfaced in the Activity stack via
// onSynthesize(batchId): with no map yet it bootstraps (inventory members →
// bootstrap_synthesis); once one exists it appends the collection's new material via
// the bounded neighborhood (inventory new members → append_synthesis) — never rebuilds.
function CollectionsSection({
  sources,
  refreshToken,
  onSynthesize
}: {
  sources: SourceLibraryCard[];
  refreshToken: number;
  onSynthesize?: (batchId: string) => void;
}) {
  const [sets, setSets] = useState<SourceSetSummaryDto[]>([]);
  const [expanded, setExpanded] = useState<Record<string, SourceSetDto | "loading">>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const titleFor = useCallback(
    (sourceId: string): string => {
      const card = sources.find((c) => c.sourceId === sourceId);
      return card ? readableTitle(card.title) : sourceId.split(/[/\\]/).filter(Boolean).pop() ?? sourceId;
    },
    [sources]
  );

  const refresh = useCallback(async () => {
    try {
      const snap = await api.listSourceSets();
      setSets(snap.sourceSets ?? []);
    } catch {
      // keep last on transient error
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh, refreshToken]);

  async function toggle(id: string) {
    if (expanded[id] && expanded[id] !== "loading") {
      setExpanded((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      return;
    }
    setExpanded((prev) => ({ ...prev, [id]: "loading" }));
    try {
      const { sourceSet } = await api.getSourceSet(id);
      setExpanded((prev) => ({ ...prev, [id]: sourceSet }));
    } catch (e) {
      setError((e as CommandError).message);
      setExpanded((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    }
  }

  async function synthesize(id: string) {
    setBusy(id);
    setError(null);
    setNotice(null);
    try {
      const batch = await api.buildStudyMap({ sourceSetId: id });
      setNotice(
        batch.mode === "append"
          ? "appending new material via the bounded neighborhood — the map is not rebuilt"
          : "creating the study map"
      );
      onSynthesize?.(batch.id);
    } catch (e) {
      setError((e as CommandError).message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div style={{ borderTop: `1px solid ${COLOR.border}`, marginTop: 4 }}>
      <div
        style={{
          padding: "8px 14px",
          fontSize: 11,
          fontFamily: FONT_MONO,
          color: COLOR.textDim,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          textTransform: "uppercase",
          letterSpacing: "0.1em"
        }}
      >
        <span>collections</span>
        {sets.length > 0 && <Faint style={{ fontSize: 11 }}>{sets.length}</Faint>}
      </div>

      {error && <div style={{ padding: "0 14px 8px", fontSize: 11, color: COLOR.red }}>{error}</div>}
      {notice && (
        <div style={{ padding: "0 14px 8px", fontSize: 11, fontFamily: FONT_MONO, color: COLOR.textDim }}>{notice}</div>
      )}

      {sets.length === 0 ? (
        <div style={{ padding: "0 14px 12px", fontSize: 11, color: COLOR.textFaint, lineHeight: 1.6 }}>
          no collections yet — use <span style={{ fontFamily: FONT_MONO }}>＋ collection</span> on a ready source to group
          material, then synthesize a study map.
        </div>
      ) : (
        sets.map((set) => {
          const detail = expanded[set.id];
          const open = detail !== undefined;
          const isBusy = busy === set.id;
          return (
            <div key={set.id} style={{ borderBottom: `1px solid ${COLOR.border}` }}>
              <div
                onClick={() => void toggle(set.id)}
                style={{ padding: "8px 12px", display: "flex", flexDirection: "column", gap: 3, cursor: "pointer" }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 11, width: 10 }}>
                    {open ? "▾" : "▸"}
                  </span>
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
                    title={set.title}
                  >
                    {set.title}
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, paddingLeft: 18 }}>
                  <Faint style={{ fontFamily: FONT_MONO }}>{set.subjectId}</Faint>
                  <Faint>· {set.memberCount} member{set.memberCount === 1 ? "" : "s"}</Faint>
                  <span style={{ flex: 1 }} />
                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      if (!isBusy) void synthesize(set.id);
                    }}
                    title="synthesize → creates the study map; when one already exists this appends the collection's new material via the bounded neighborhood — never rebuilds. surfaced as a build batch in Activity on the right"
                    style={{
                      fontFamily: FONT_MONO,
                      fontSize: 11,
                      color: isBusy ? COLOR.textFaint : COLOR.amberLink,
                      cursor: isBusy ? "default" : "pointer"
                    }}
                  >
                    {isBusy ? "queuing…" : "synthesize →"}
                  </span>
                </div>
              </div>

              {open && detail === "loading" && (
                <div style={{ padding: "0 14px 8px 30px", fontSize: 11, color: COLOR.textFaint }}>◐ loading members…</div>
              )}
              {open && detail !== "loading" && (
                <div style={{ padding: "0 12px 8px 30px", display: "flex", flexDirection: "column", gap: 4 }}>
                  {detail.members.length === 0 ? (
                    <Faint style={{ fontSize: 11 }}>no members</Faint>
                  ) : (
                    detail.members.map((m, i) => (
                      <div key={`${m.sourceId}-${i}`} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11 }}>
                        <span
                          style={{
                            flex: 1,
                            minWidth: 0,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            color: COLOR.textDim
                          }}
                          title={m.sourceId}
                        >
                          {titleFor(m.sourceId)}
                        </span>
                        {m.scope.length > 0 && <Faint style={{ fontFamily: FONT_MONO }}>{m.scope.length}u</Faint>}
                        <Pill color="slate">{m.defaultRole}</Pill>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}
