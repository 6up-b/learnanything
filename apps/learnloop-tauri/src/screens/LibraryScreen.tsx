import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { api } from "../api/client";
import { useCachedQuery } from "../api/useCachedQuery";
import { TAG } from "../api/queryTags";
import type {
  CoverageRollupDto,
  ProposalBatchDto,
  ProposalItemDto,
  ProposalsSnapshot,
  SourceSetSummaryDto,
  VaultFileContent,
  VaultTreeNode,
  VaultTreeSnapshot
} from "../api/dto";
import { COLOR, Dim, Faint, FONT_MONO, KeyBar, Meta, Pill, type PillColor } from "../components/term";
import { highlightFor } from "../components/highlight";
import { ProvenancePanel } from "../components/ProvenancePanel";
import { LiveMarkdownEditor } from "../render/LiveMarkdownEditor";
import { SqliteBrowser } from "./SqliteBrowser";

// A vault selection is either an on-disk file or a (virtual) proposal payload doc.
type Selection =
  | { kind: "file"; path: string }
  | { kind: "proposal"; patchId: string; itemId: string }
  | null;

function sameSelection(a: Selection, b: Selection): boolean {
  if (a === null || b === null) return a === b;
  if (a.kind === "file" && b.kind === "file") return a.path === b.path;
  if (a.kind === "proposal" && b.kind === "proposal") return a.patchId === b.patchId && a.itemId === b.itemId;
  return false;
}

function kindColor(kind: string | undefined): PillColor {
  return (
    {
      yaml: "amber",
      md: "cyan",
      toml: "green",
      json: "purple",
      text: "slate",
      sqlite: "pink",
      binary: "slate"
    } as Record<string, PillColor>
  )[kind ?? ""] ?? "slate";
}

// Single-character typed file glyph, matching the handoff legend.
function FileGlyph({ name, kind }: { name: string; kind: string | undefined }) {
  if (name.startsWith("lo_")) return <span style={{ color: COLOR.purplePill }}>L</span>;
  if (name.startsWith("pi_") || name.startsWith("practice_")) return <span style={{ color: COLOR.cyan }}>P</span>;
  if (name.startsWith("concept_")) return <span style={{ color: COLOR.green }}>C</span>;
  if (kind === "md") return <span style={{ color: COLOR.green }}>m</span>;
  if (kind === "yaml") return <span style={{ color: COLOR.amber }}>y</span>;
  if (kind === "sqlite") return <span style={{ color: COLOR.pink }}>▦</span>;
  if (kind === "binary") return <span style={{ color: COLOR.textFaint }}>·</span>;
  return <span style={{ color: COLOR.textFaint }}>·</span>;
}

function entityPill(name: string): { color: PillColor; label: string } | null {
  if (name.startsWith("lo_")) return { color: "purple", label: "learning_object" };
  if (name.startsWith("pi_") || name.startsWith("practice_")) return { color: "cyan", label: "practice_item" };
  if (name.startsWith("concept_")) return { color: "green", label: "concept" };
  if (name.startsWith("error_")) return { color: "red", label: "error_taxonomy" };
  return null;
}

function inspectableTreeEntityId(node: VaultTreeNode): string | null {
  if (node.type !== "file") return null;
  const stem = node.name.replace(/\.(?:ya?ml|json|md|txt)$/i, "");
  return /^(?:lo_|pi_|practice_|concept_)/.test(stem) ? stem : null;
}

function firstFilePath(nodes: VaultTreeNode[]): string | null {
  for (const node of nodes) {
    if (node.type === "file") return node.path;
    if (node.children) {
      const nested = firstFilePath(node.children);
      if (nested) return nested;
    }
  }
  return null;
}

function dirPaths(nodes: VaultTreeNode[], acc: string[] = []): string[] {
  for (const node of nodes) {
    if (node.type === "dir") {
      acc.push(node.path);
      if (node.children) dirPaths(node.children, acc);
    }
  }
  return acc;
}

// Flatten files in display order, skipping the contents of collapsed dirs — used
// for j/k keyboard navigation.
function visibleFiles(nodes: VaultTreeNode[], collapsed: Set<string>, acc: string[] = []): string[] {
  for (const node of nodes) {
    if (node.type === "file") acc.push(node.path);
    else if (node.children && !collapsed.has(node.path)) visibleFiles(node.children, collapsed, acc);
  }
  return acc;
}

function findProposal(
  proposals: ProposalsSnapshot | null,
  patchId: string,
  itemId: string
): { batch: ProposalBatchDto; item: ProposalItemDto } | null {
  for (const batch of proposals?.batches ?? []) {
    if (batch.id !== patchId) continue;
    const item = batch.items.find((candidate) => candidate.id === itemId);
    if (item) return { batch, item };
  }
  return null;
}

function proposalLabel(item: ProposalItemDto): string {
  return item.proposedEntityId || item.id;
}

export function LibraryScreen({
  onError,
  focus = null,
  onFocusConsumed,
  focusFilePath = null,
  onFileFocusConsumed,
  onAsk,
  onNoteSelected,
  onInspect
}: {
  onError: (message: string) => void;
  focus?: { patchId: string; itemId: string } | null;
  onFocusConsumed?: () => void;
  /** Vault-relative file to select on open (feedback "View in Library" jump). */
  focusFilePath?: string | null;
  onFileFocusConsumed?: () => void;
  onAsk?: (target: { context: "library"; noteId: string }) => void;
  onNoteSelected?: (noteId: string | null) => void;
  onInspect: (entityId: string) => void;
}) {
  // The tree, the proposals, and the source-set list are cached: returning to
  // Library repaints them immediately and revalidates in the background.
  // Per-set coverage rollups stay lazy (CoverageSection) so a long library
  // does not fan out N heavy coverage calls on mount.
  const treeQuery = useCachedQuery(["get_vault_tree"], () => api.getVaultTree(), { tags: [TAG.library] });
  const snapshot: VaultTreeSnapshot | null = treeQuery.data ?? null;
  const proposalsQuery = useCachedQuery(["get_proposals"], () => api.getProposals(), { tags: [TAG.proposals] });
  const proposals: ProposalsSnapshot | null = proposalsQuery.data ?? null;
  const sourceSetsQuery = useCachedQuery(["list_source_sets"], () => api.listSourceSets(), { tags: [TAG.sources] });
  const sourceSets: SourceSetSummaryDto[] | null = sourceSetsQuery.data?.sourceSets ?? null;
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [proposalsOpen, setProposalsOpen] = useState(true);
  const [selected, setSelected] = useState<Selection>(null);
  const [content, setContent] = useState<VaultFileContent | null>(null);

  // Edit state. `editing` only gates the raw editor for non-markdown text files;
  // markdown opens straight into the live editor and `draft` always tracks it.
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);

  // New-file prompt.
  const [newPath, setNewPath] = useState<string | null>(null);
  const newInputRef = useRef<HTMLInputElement>(null);

  // Read-only source-provenance popover for the selected entity file.
  const [provenanceOpen, setProvenanceOpen] = useState(false);

  // Collapse deep directories once per mount (the first tree seen), pick a
  // first file when nothing is selected, and leave the learner's expansion
  // alone when a background revalidation delivers a changed tree.
  const seenTreeRef = useRef<VaultTreeSnapshot | null>(null);
  useEffect(() => {
    if (!snapshot || seenTreeRef.current === snapshot) return;
    const firstTree = seenTreeRef.current === null;
    seenTreeRef.current = snapshot;
    if (firstTree) {
      const deep = dirPaths(snapshot.tree).filter((path) => path.includes("/"));
      setCollapsed(new Set(deep));
    }
    setSelected((current) => current ?? (firstFilePath(snapshot.tree) ? { kind: "file", path: firstFilePath(snapshot.tree)! } : null));
  }, [snapshot]);

  const loadError = treeQuery.error ?? proposalsQuery.error ?? sourceSetsQuery.error;
  useEffect(() => {
    if (loadError) onError(loadError.message);
  }, [loadError, onError]);

  const reloadProposals = () => {
    proposalsQuery.refetch().catch((error) => onError((error as Error).message));
  };

  // Honor a handoff from the feedback source panel: select that vault file.
  useEffect(() => {
    if (!focusFilePath || !snapshot) return;
    setSelected({ kind: "file", path: focusFilePath });
    onFileFocusConsumed?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusFilePath, snapshot]);

  // Honor a handoff from the Proposals screen: select that payload doc.
  useEffect(() => {
    if (!focus || !proposals) return;
    if (findProposal(proposals, focus.patchId, focus.itemId)) {
      setProposalsOpen(true);
      setSelected({ kind: "proposal", patchId: focus.patchId, itemId: focus.itemId });
    }
    onFocusConsumed?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focus, proposals]);

  // File bodies are cached per path: re-selecting a file, or returning to
  // Library, shows it at once; a save invalidates the tag and the fresh body
  // arrives in the background.
  const cachedFilePath = selected?.kind === "file" ? selected.path : null;
  const fileQuery = useCachedQuery(
    cachedFilePath ? ["read_vault_file", cachedFilePath] : null,
    () => api.readVaultFile(cachedFilePath as string),
    { tags: [TAG.library] }
  );
  const loadingFile = fileQuery.loading;

  // Every selection change drops out of edit mode and resets the editor.
  useEffect(() => {
    setEditing(false);
    setProvenanceOpen(false);
    setContent(null);
    setDraft("");
  }, [selected]);

  // Mirror the cached body into the editor. A revalidation (watcher, save,
  // ingest) must never clobber unsaved text, so the draft is only replaced
  // while it still matches the body it was seeded from.
  const draftUntouchedRef = useRef(true);
  draftUntouchedRef.current = !editing && (content === null || draft === (content.body ?? ""));
  useEffect(() => {
    const file = fileQuery.data;
    if (!file || !cachedFilePath) return;
    setContent(file);
    if (draftUntouchedRef.current) setDraft(file.body ?? "");
  }, [fileQuery.data, cachedFilePath]);

  useEffect(() => {
    if (fileQuery.error) onError(fileQuery.error.message);
  }, [fileQuery.error, onError]);

  // Seed the payload editor when a proposal selection changes.
  const focusedProposal = useMemo(
    () => (selected?.kind === "proposal" ? findProposal(proposals, selected.patchId, selected.itemId) : null),
    [selected, proposals]
  );
  useEffect(() => {
    if (focusedProposal) setDraft(focusedProposal.item.payloadJson);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected]);

  const selectedFilePath = selected?.kind === "file" ? selected.path : null;
  const selectedContent = content && selectedFilePath === content.path ? content : null;

  // An lo_/pi_/practice_ vault file is an inspectable entity whose id is the file stem;
  // it can carry source provenance we surface in a read-only popover.
  const entityProvenanceTarget = useMemo<{ entityType: string; entityId: string } | null>(() => {
    const name = selectedContent?.name;
    if (!name) return null;
    const stem = name.replace(/\.(md|ya?ml|json|toml)$/i, "");
    if (name.startsWith("lo_")) return { entityType: "learning_object", entityId: stem };
    if (name.startsWith("pi_") || name.startsWith("practice_")) return { entityType: "practice_item", entityId: stem };
    return null;
  }, [selectedContent]);
  const isMd = Boolean(selectedContent && selectedContent.kind === "md" && selectedContent.editable && !selectedContent.binary && !selectedContent.truncated);
  const isDatabase = Boolean(selectedContent?.database);
  const canEditRaw = Boolean(selectedContent && selectedContent.editable && !selectedContent.binary && !selectedContent.truncated && selectedContent.kind !== "md");
  const dirty =
    selected?.kind === "proposal"
      ? focusedProposal != null && draft !== focusedProposal.item.payloadJson
      : (isMd && selectedContent?.body != null && draft !== selectedContent.body) || (editing && selectedContent?.body != null && draft !== selectedContent.body);

  function beginEdit() {
    if (!canEditRaw || !content) return;
    setDraft(content.body ?? "");
    setEditing(true);
  }

  async function saveFile() {
    if (!selected || selected.kind !== "file" || saving) return;
    setSaving(true);
    try {
      const saved = await api.writeVaultFile(selected.path, draft);
      setContent(saved);
      setDraft(saved.body ?? "");
      setEditing(false);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function saveProposal() {
    if (!focusedProposal || saving) return;
    setSaving(true);
    try {
      // The wrapper seeds get_proposals with the returned snapshot.
      const next = await api.editProposalItem(focusedProposal.batch.id, focusedProposal.item.id, draft);
      const refreshed = findProposal(next, focusedProposal.batch.id, focusedProposal.item.id);
      if (refreshed) setDraft(refreshed.item.payloadJson);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function rejectProposal() {
    if (!focusedProposal || saving) return;
    setSaving(true);
    try {
      await api.rejectProposalItems(focusedProposal.batch.id, [focusedProposal.item.id]);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function deleteProposal() {
    if (!focusedProposal || saving) return;
    setSaving(true);
    try {
      await api.deleteProposalItem(focusedProposal.batch.id, focusedProposal.item.id);
      setSelected(null);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function submitNewFile() {
    const path = newPath?.trim();
    if (!path) {
      setNewPath(null);
      return;
    }
    try {
      const created = await api.createVaultFile(path);
      await treeQuery.refetch();
      setNewPath(null);
      setSelected({ kind: "file", path: created.path });
    } catch (error) {
      onError((error as Error).message);
    }
  }

  useEffect(() => {
    if (newPath !== null) newInputRef.current?.focus();
  }, [newPath]);

  // Combined j/k order: files first, then (when open) proposal items.
  const pendingByBatch = useMemo(() => proposals?.batches ?? [], [proposals]);
  const navEntries = useMemo<Selection[]>(() => {
    const files: Selection[] = snapshot ? visibleFiles(snapshot.tree, collapsed).map((path) => ({ kind: "file", path })) : [];
    const props: Selection[] = proposalsOpen
      ? pendingByBatch.flatMap((batch) => batch.items.map((item) => ({ kind: "proposal" as const, patchId: batch.id, itemId: item.id })))
      : [];
    return [...files, ...props];
  }, [snapshot, collapsed, proposalsOpen, pendingByBatch]);

  // A selected vault file under notes/ is an askable note; its id is the file
  // stem (note frontmatter ids match the filename).
  const selectedNoteId = useMemo(() => {
    if (selected?.kind !== "file") return null;
    const match = /(?:^|[\\/])notes[\\/]([^\\/]+)\.md$/.exec(selected.path);
    return match ? match[1] : null;
  }, [selected]);

  useEffect(() => {
    onNoteSelected?.(selectedNoteId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedNoteId]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName?.toLowerCase();
      const inField = tag === "textarea" || tag === "input";
      const inSqliteBrowser = Boolean(target?.closest?.("[data-sqlite-browser]"));
      const ctrl = event.ctrlKey || event.metaKey;

      if (ctrl && event.key.toLowerCase() === "s") {
        if (selected?.kind === "proposal") {
          event.preventDefault();
          void saveProposal();
        } else if (isMd || editing) {
          event.preventDefault();
          void saveFile();
        }
        return;
      }
      if (event.key === "Escape" && editing) {
        event.preventDefault();
        setEditing(false);
        setDraft(content?.body ?? "");
        return;
      }
      if (inField) return;
      // SqliteBrowser owns its grid navigation while focus is inside it. Without
      // this boundary, j/k and the arrow keys would also move the Library tree.
      if (inSqliteBrowser) return;
      if (event.key === "n") {
        event.preventDefault();
        setNewPath("notes/");
        return;
      }
      if (event.key === "e" && canEditRaw && !editing) {
        event.preventDefault();
        beginEdit();
        return;
      }
      if (event.key === "?" && !editing && selectedNoteId && onAsk) {
        event.preventDefault();
        onAsk({ context: "library", noteId: selectedNoteId });
        return;
      }
      if (editing) return;
      const index = navEntries.findIndex((entry) => sameSelection(entry, selected));
      if (["j", "ArrowDown"].includes(event.key)) {
        if (navEntries[index + 1]) setSelected(navEntries[index + 1]);
        event.preventDefault();
      } else if (["k", "ArrowUp"].includes(event.key)) {
        if (index > 0 && navEntries[index - 1]) setSelected(navEntries[index - 1]);
        event.preventDefault();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navEntries, selected, editing, canEditRaw, isMd, content, draft, saving, focusedProposal, selectedNoteId, onAsk]);

  const rootName = useMemo(() => {
    if (!snapshot) return "vault";
    const parts = snapshot.root.split(/[\\/]+/).filter(Boolean);
    return parts[parts.length - 1] ?? snapshot.root;
  }, [snapshot]);

  function toggleDir(path: string) {
    setCollapsed((current) => {
      const next = new Set(current);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }

  const keyBar = (() => {
    if (selected?.kind === "proposal") {
      return [
        { key: "^s", label: "Save payload" },
        { key: "^f", label: "Find" },
        { key: "j/k", label: "Move" }
      ];
    }
    if (isDatabase) {
      return [
        { key: "hjkl / arrows", label: "Move cell" },
        { key: "enter / i", label: "Edit" },
        { key: "space", label: "Inspector" },
        { key: "esc", label: "Cancel / close" }
      ];
    }
    if (isMd) {
      return [
        { key: "^s", label: dirty ? "Save ●" : "Save" },
        { key: "j/k", label: "Move" },
        { key: "n", label: "New note" },
        ...(selectedNoteId ? [{ key: "?", label: "ask tutor" }] : [])
      ];
    }
    if (editing) {
      return [
        { key: "^s", label: "Save" },
        { key: "esc", label: "Cancel" }
      ];
    }
    return [
      { key: "j/k", label: "Move" },
      { key: "▸/▾", label: "Toggle folder" },
      { key: "e", label: "Edit" },
      { key: "n", label: "New note" }
    ];
  })();

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        {/* Tree */}
        <div className="library-tree" style={{ width: 320, flexShrink: 0, borderRight: `1px solid ${COLOR.border}`, background: COLOR.bg, overflowY: "auto", minHeight: 0 }}>
          <div style={{ padding: "10px 14px", borderBottom: `1px solid ${COLOR.border}`, fontSize: 12, color: COLOR.textDim, display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ color: COLOR.amber, fontFamily: FONT_MONO }}>▾</span>
            <span style={{ color: COLOR.text }}>{rootName}</span>
            <Meta style={{ fontSize: 11 }}>vault root</Meta>
            <span style={{ flex: 1 }} />
            <span
              onClick={() => setNewPath("notes/")}
              title="new note (n)"
              style={{ cursor: "pointer", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 13 }}
            >
              + new
            </span>
          </div>

          {newPath !== null ? (
            <div style={{ padding: "8px 12px", borderBottom: `1px solid ${COLOR.border}`, display: "flex", gap: 6, alignItems: "center" }}>
              <input
                ref={newInputRef}
                value={newPath}
                onChange={(event) => setNewPath(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") { event.preventDefault(); void submitNewFile(); }
                  else if (event.key === "Escape") { event.preventDefault(); setNewPath(null); }
                }}
                placeholder="notes/my-note.md"
                style={{ flex: 1, background: COLOR.bgInput, border: `1px solid ${COLOR.amber}`, color: COLOR.text, fontFamily: FONT_MONO, fontSize: 12, padding: "4px 8px", outline: "none" }}
              />
            </div>
          ) : null}

          <div style={{ padding: "8px 0" }}>
            {snapshot ? (
              <TreeLevel
                nodes={snapshot.tree}
                depth={0}
                collapsed={collapsed}
                selected={selected}
                onToggle={toggleDir}
                onSelect={(path) => setSelected({ kind: "file", path })}
                onInspect={onInspect}
              />
            ) : (
              <div style={{ padding: "8px 16px", color: COLOR.textFaint, fontSize: 13 }}>loading vault…</div>
            )}
          </div>

          <ProposalsTree
            proposals={proposals}
            open={proposalsOpen}
            onToggle={() => setProposalsOpen((value) => !value)}
            selected={selected}
            onSelect={(patchId, itemId) => setSelected({ kind: "proposal", patchId, itemId })}
          />

          <CoverageSection sourceSets={sourceSets} onError={onError} onGenerated={reloadProposals} />

          <div style={{ margin: "20px 12px", padding: "10px 12px", border: `1px dashed ${COLOR.border}`, fontSize: 11, color: COLOR.textDim }}>
            <Faint>legend</Faint>
            <div style={{ marginTop: 6, display: "grid", gap: 3 }}>
              <span><span style={{ color: COLOR.purplePill }}>L</span> learning_object</span>
              <span><span style={{ color: COLOR.cyan }}>P</span> practice_item</span>
              <span><span style={{ color: COLOR.amber }}>y</span> yaml</span>
              <span><span style={{ color: COLOR.green }}>m</span> markdown</span>
              <span><span style={{ color: COLOR.pink }}>▦</span> sqlite database</span>
            </div>
          </div>
        </div>

        {/* Viewer / editor */}
        <div className="ll-scroll" style={{ position: "relative", flex: 1, minWidth: 0, display: "flex", flexDirection: "column", background: COLOR.bg, minHeight: 0 }}>
          {entityProvenanceTarget && provenanceOpen ? (
            <div style={{ position: "absolute", top: 42, right: 16, zIndex: 5 }}>
              <ProvenancePanel
                entityType={entityProvenanceTarget.entityType}
                entityId={entityProvenanceTarget.entityId}
                onClose={() => setProvenanceOpen(false)}
              />
            </div>
          ) : null}
          {selected?.kind === "proposal" ? (
            <ProposalEditor
              found={focusedProposal}
              draft={draft}
              dirty={Boolean(dirty)}
              saving={saving}
              onChangeDraft={setDraft}
              onSave={saveProposal}
              onReject={rejectProposal}
              onDelete={deleteProposal}
            />
          ) : isDatabase && selected?.kind === "file" ? (
            <>
              <ViewerHeader path={selected.path} content={selectedContent} dirty={false} actions={null} />
              <SqliteBrowser path={selected.path} onError={onError} />
            </>
          ) : (
            <FileViewer
              path={selected?.kind === "file" ? selected.path : null}
              content={selectedContent}
              loading={loadingFile}
              isMd={isMd}
              editing={editing}
              draft={draft}
              dirty={Boolean(dirty)}
              saving={saving}
              canEditRaw={canEditRaw}
              headerActions={entityProvenanceTarget ? (
                <ActionButton
                  label="provenance"
                  active={provenanceOpen}
                  onClick={() => setProvenanceOpen((open) => !open)}
                />
              ) : null}
              onChangeDraft={setDraft}
              onBeginEdit={beginEdit}
              onCancelEdit={() => { setEditing(false); setDraft(content?.body ?? ""); }}
              onSave={saveFile}
            />
          )}
        </div>
      </div>

      <KeyBar keys={keyBar} right={{ key: "^p", label: "palette" }} />
    </div>
  );
}

function TreeLevel({
  nodes,
  depth,
  collapsed,
  selected,
  onToggle,
  onSelect,
  onInspect
}: {
  nodes: VaultTreeNode[];
  depth: number;
  collapsed: Set<string>;
  selected: Selection;
  onToggle: (path: string) => void;
  onSelect: (path: string) => void;
  onInspect: (entityId: string) => void;
}) {
  return (
    <div>
      {nodes.map((node) => {
        const indent = 8 + depth * 14;
        if (node.type === "dir") {
          const isCollapsed = collapsed.has(node.path);
          return (
            <div key={node.path}>
              <div
                onClick={() => onToggle(node.path)}
                style={{ padding: "2px 8px", paddingLeft: indent, cursor: "pointer", display: "flex", alignItems: "center", gap: 4, fontSize: 12 }}
              >
                <span style={{ color: COLOR.amber, width: 10, flexShrink: 0, fontFamily: FONT_MONO }}>{isCollapsed ? "▸" : "▾"}</span>
                <span style={{ color: COLOR.amberLink, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", minWidth: 0, flex: 1 }}>{node.name}/</span>
              </div>
              {!isCollapsed && node.children ? (
                <TreeLevel
                  nodes={node.children}
                  depth={depth + 1}
                  collapsed={collapsed}
                  selected={selected}
                  onToggle={onToggle}
                  onSelect={onSelect}
                  onInspect={onInspect}
                />
              ) : null}
            </div>
          );
        }
        const isSelected = selected?.kind === "file" && node.path === selected.path;
        const inspectableId = inspectableTreeEntityId(node);
        return (
          <div
            key={node.path}
            onClick={() => onSelect(node.path)}
            onContextMenu={inspectableId ? (event) => {
              event.preventDefault();
              onInspect(inspectableId);
            } : undefined}
            title={inspectableId ? `Right-click to learnloop show ${inspectableId}` : undefined}
            style={{
              padding: "2px 8px",
              paddingLeft: indent + 14,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 12,
              background: isSelected ? "#241d12" : "transparent",
              borderLeft: `2px solid ${isSelected ? COLOR.amber : "transparent"}`,
              color: isSelected ? COLOR.text : COLOR.textDim
            }}
          >
            <span style={{ width: 10, textAlign: "center", fontFamily: FONT_MONO, flexShrink: 0 }}>
              <FileGlyph name={node.name} kind={node.kind} />
            </span>
            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0, flex: 1, fontFamily: FONT_MONO }}>{node.name}</span>
          </div>
        );
      })}
    </div>
  );
}

// Virtual "proposals/" group: each Codex proposal item is an editable payload doc.
function ProposalsTree({
  proposals,
  open,
  onToggle,
  selected,
  onSelect
}: {
  proposals: ProposalsSnapshot | null;
  open: boolean;
  onToggle: () => void;
  selected: Selection;
  onSelect: (patchId: string, itemId: string) => void;
}) {
  const total = proposals?.batches.reduce((sum, batch) => sum + batch.items.length, 0) ?? 0;
  return (
    <div style={{ borderTop: `1px solid ${COLOR.border}` }}>
      <div onClick={onToggle} style={{ padding: "4px 8px", cursor: "pointer", display: "flex", alignItems: "center", gap: 4, fontSize: 12 }}>
        <span style={{ color: COLOR.purpleText, width: 10, flexShrink: 0, fontFamily: FONT_MONO }}>{open ? "▾" : "▸"}</span>
        <span style={{ color: COLOR.purpleText, flex: 1 }}>proposals/</span>
        <Faint style={{ fontSize: 11 }}>{total}</Faint>
      </div>
      {open
        ? (proposals?.batches ?? []).map((batch) =>
            batch.items.map((item) => {
              const isSelected = selected?.kind === "proposal" && selected.patchId === batch.id && selected.itemId === item.id;
              return (
                <div
                  key={item.id}
                  onClick={() => onSelect(batch.id, item.id)}
                  style={{
                    padding: "2px 8px 2px 32px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    fontSize: 12,
                    background: isSelected ? "#241d12" : "transparent",
                    borderLeft: `2px solid ${isSelected ? COLOR.amber : "transparent"}`,
                    color: isSelected ? COLOR.text : COLOR.textDim
                  }}
                >
                  <span style={{ color: COLOR.purplePill, fontFamily: FONT_MONO, flexShrink: 0 }}>L</span>
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0, flex: 1, fontFamily: FONT_MONO }}>
                    {proposalLabel(item)}
                  </span>
                  <DecisionDot decision={item.decision} />
                </div>
              );
            })
          )
        : null}
    </div>
  );
}

function DecisionDot({ decision }: { decision: string }) {
  const color = decision === "accepted" ? COLOR.green : decision === "rejected" ? COLOR.red : COLOR.amber;
  return <span style={{ color, fontSize: 9, flexShrink: 0 }} title={decision}>●</span>;
}

// Distribute `cells` bar segments across bucket counts, giving any nonzero
// bucket at least one cell so a small-but-real debt slice can never vanish.
function allocCells(counts: number[], cells: number): number[] {
  const total = counts.reduce((a, b) => a + b, 0);
  if (total <= 0) return counts.map(() => 0);
  const exact = counts.map((c) => (c / total) * cells);
  const out = exact.map((e) => Math.floor(e));
  counts.forEach((c, i) => {
    if (c > 0 && out[i] === 0) out[i] = 1;
  });
  let used = out.reduce((a, b) => a + b, 0);
  const byRemainder = exact.map((e, i) => ({ i, r: e - Math.floor(e) })).sort((a, b) => b.r - a.r);
  let k = 0;
  while (used < cells && byRemainder.length) {
    out[byRemainder[k % byRemainder.length].i]++;
    used++;
    k++;
  }
  while (used > cells) {
    let best = -1;
    for (let i = 0; i < out.length; i++) {
      const floor = counts[i] > 0 ? 1 : 0;
      if (out[i] > floor && (best < 0 || out[i] > out[best])) best = i;
    }
    if (best < 0) break;
    out[best]--;
    used--;
  }
  return out;
}

// Three-bucket coverage bar (spec §4.11) with explicit precedence:
// demonstrated ≻ assessed-but-not ≻ no-practice-supply. The third bucket is the
// SYSTEM's debt (missing practice supply), so it is distinguished by glyph AND
// color AND label — never color alone — and carries a text equivalent for AT.
function CoverageBucketBar({ rollup, width = 26 }: { rollup: CoverageRollupDto; width?: number }) {
  const dem = rollup.buckets.demonstrated.count;
  const ass = rollup.buckets.assessed.count;
  const debt = rollup.buckets.noPracticeSupply.count;
  const total = rollup.total;
  if (total <= 0) {
    return <Faint style={{ fontSize: 11 }}>no facets mapped yet</Faint>;
  }
  const cells = Math.min(width, Math.max(total, 3));
  const [demCells, assCells, debtCells] = allocCells([dem, ass, debt], cells);
  const label = `coverage: ${dem} demonstrated, ${ass} assessed but not demonstrated, ${debt} with no practice items yet (system debt), of ${total} facets`;
  return (
    <span role="img" aria-label={label} style={{ fontFamily: FONT_MONO, fontSize: 12, letterSpacing: 1, whiteSpace: "nowrap" }}>
      <span style={{ color: COLOR.green }}>{"▓".repeat(demCells)}</span>
      <span style={{ color: COLOR.amber }}>{"▒".repeat(assCells)}</span>
      {/* debt: hatched glyph + pink so it reads as debt with color OFF, too */}
      <span style={{ color: COLOR.pink }}>{"▚".repeat(debtCells)}</span>
    </span>
  );
}

function CoverageLegendRow({ glyph, color, count, label }: { glyph: string; color: string; count: number; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: 6, fontSize: 11 }}>
      <span style={{ color, fontFamily: FONT_MONO, width: 10, flexShrink: 0 }}>{glyph}</span>
      <span style={{ color: COLOR.text, fontFamily: FONT_MONO }}>{count}</span>
      <span style={{ color: COLOR.textDim }}>{label}</span>
    </div>
  );
}

// One expandable source-set row. Coverage is fetched lazily on first expand.
function SourceSetCoverageRow({
  set,
  onError,
  onGenerated
}: {
  set: SourceSetSummaryDto;
  onError: (message: string) => void;
  onGenerated: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [rollup, setRollup] = useState<CoverageRollupDto | "unavailable" | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const fetched = useRef(false);

  const load = () => {
    if (fetched.current) return;
    fetched.current = true;
    setLoading(true);
    api
      .getSourceCoverage(set.id)
      .then((r) => setRollup(r.coverage.rollup ?? "unavailable"))
      .catch((error) => {
        fetched.current = false;
        onError((error as Error).message);
      })
      .finally(() => setLoading(false));
  };

  const toggle = () => {
    setExpanded((open) => {
      if (!open) load();
      return !open;
    });
  };

  const generate = async () => {
    setGenerating(true);
    setNote(null);
    try {
      // The only practice-item generation flow reachable from Library: study-map
      // synthesis in propose-only mode, so items land in proposals/ for review.
      const res = await api.createStudyMap({ sourceSetId: set.id, apply: false });
      const n = Object.values(res.studyMap.itemCounts ?? {}).reduce((a, b) => a + (b || 0), 0);
      setNote(n > 0 ? `proposed ${n} item(s) — review in proposals/ above` : "no new practice items proposed");
      onGenerated();
      fetched.current = false;
      load();
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setGenerating(false);
    }
  };

  const debt = rollup && rollup !== "unavailable" ? rollup.buckets.noPracticeSupply.count : 0;

  return (
    <div style={{ borderTop: `1px solid ${COLOR.border}` }}>
      <div
        onClick={toggle}
        style={{ padding: "3px 8px 3px 20px", cursor: "pointer", display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}
      >
        <span style={{ color: COLOR.amber, width: 10, flexShrink: 0, fontFamily: FONT_MONO }}>{expanded ? "▾" : "▸"}</span>
        <span style={{ color: COLOR.textDim, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0, flex: 1, fontFamily: FONT_MONO }}>
          {set.title}
        </span>
        <Faint style={{ fontSize: 11 }}>{set.memberCount}</Faint>
      </div>
      {expanded ? (
        <div style={{ padding: "4px 12px 10px 30px", display: "grid", gap: 6 }}>
          {loading ? (
            <Faint style={{ fontSize: 11 }}>loading coverage…</Faint>
          ) : rollup === "unavailable" ? (
            <Faint style={{ fontSize: 11 }}>coverage rollup unavailable for this set</Faint>
          ) : rollup ? (
            <>
              <CoverageBucketBar rollup={rollup} />
              <div style={{ display: "grid", gap: 2 }}>
                <CoverageLegendRow glyph="▓" color={COLOR.green} count={rollup.buckets.demonstrated.count} label="demonstrated" />
                <CoverageLegendRow glyph="▒" color={COLOR.amber} count={rollup.buckets.assessed.count} label="assessed, not demonstrated" />
                <CoverageLegendRow
                  glyph="▚"
                  color={COLOR.pink}
                  count={rollup.buckets.noPracticeSupply.count}
                  label="no practice items yet — system debt"
                />
              </div>
              {debt > 0 ? (
                <span
                  role="button"
                  tabIndex={0}
                  onClick={generating ? undefined : generate}
                  onKeyDown={(event) => {
                    if (!generating && (event.key === "Enter" || event.key === " ")) {
                      event.preventDefault();
                      void generate();
                    }
                  }}
                  style={{
                    justifySelf: "start",
                    padding: "2px 10px",
                    border: `1px solid ${COLOR.pink}`,
                    color: generating ? COLOR.textFaint : COLOR.pink,
                    background: "transparent",
                    fontFamily: FONT_MONO,
                    fontSize: 11,
                    cursor: generating ? "wait" : "pointer",
                    borderRadius: 2
                  }}
                >
                  {generating ? "generating…" : "+ create practice items"}
                </span>
              ) : null}
              {note ? <Faint style={{ fontSize: 11 }}>{note}</Faint> : null}
            </>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

// Coverage section (spec §4.11) — one three-bucket bar per source set. The set
// list is loaded on mount; each set's coverage rollup loads lazily on expand.
function CoverageSection({
  sourceSets,
  onError,
  onGenerated
}: {
  sourceSets: SourceSetSummaryDto[] | null;
  onError: (message: string) => void;
  onGenerated: () => void;
}) {
  const [open, setOpen] = useState(false);
  if (!sourceSets || sourceSets.length === 0) return null;
  return (
    <div style={{ borderTop: `1px solid ${COLOR.border}` }}>
      <div onClick={() => setOpen((value) => !value)} style={{ padding: "4px 8px", cursor: "pointer", display: "flex", alignItems: "center", gap: 4, fontSize: 12 }}>
        <span style={{ color: COLOR.amber, width: 10, flexShrink: 0, fontFamily: FONT_MONO }}>{open ? "▾" : "▸"}</span>
        <span style={{ color: COLOR.amber, flex: 1 }}>coverage/</span>
        <Faint style={{ fontSize: 11 }}>{sourceSets.length}</Faint>
      </div>
      {open
        ? sourceSets.map((set) => <SourceSetCoverageRow key={set.id} set={set} onError={onError} onGenerated={onGenerated} />)
        : null}
    </div>
  );
}

function ViewerHeader({
  path,
  content,
  dirty,
  actions
}: {
  path: string | null;
  content: VaultFileContent | null;
  dirty: boolean;
  actions: ReactNode;
}) {
  const pill = content ? entityPill(content.name) : null;
  return (
    <div style={{ padding: "12px 18px", borderBottom: `1px solid ${COLOR.border}`, display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
      <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.amberLink, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{path}</span>
      {content ? <Pill color={kindColor(content.kind)}>{content.kind}</Pill> : null}
      {pill ? <Pill color={pill.color}>{pill.label}</Pill> : null}
      {dirty ? <Faint style={{ fontSize: 11 }}>● unsaved</Faint> : null}
      <span style={{ flex: 1 }} />
      {content ? <Faint style={{ fontSize: 11 }}>{formatBytes(content.size)}</Faint> : null}
      {actions}
    </div>
  );
}

function FileViewer({
  path,
  content,
  loading,
  isMd,
  editing,
  draft,
  dirty,
  saving,
  canEditRaw,
  headerActions,
  onChangeDraft,
  onBeginEdit,
  onCancelEdit,
  onSave
}: {
  path: string | null;
  content: VaultFileContent | null;
  loading: boolean;
  isMd: boolean;
  editing: boolean;
  draft: string;
  dirty: boolean;
  saving: boolean;
  canEditRaw: boolean;
  headerActions?: ReactNode;
  onChangeDraft: (value: string) => void;
  onBeginEdit: () => void;
  onCancelEdit: () => void;
  onSave: () => void;
}) {
  if (!path) {
    return <div style={{ padding: 30, color: COLOR.textFaint, fontSize: 13 }}>select a file</div>;
  }

  const actions = isMd ? (
    <ActionButton label={saving ? "saving…" : dirty ? "save" : "saved"} active={dirty} onClick={onSave} />
  ) : editing ? (
    <>
      <ActionButton label={saving ? "saving…" : "save"} active onClick={onSave} />
      <ActionButton label="cancel" onClick={onCancelEdit} />
    </>
  ) : canEditRaw ? (
    <ActionButton label="edit" onClick={onBeginEdit} />
  ) : null;

  return (
    <>
      <ViewerHeader
        path={path}
        content={content}
        dirty={dirty}
        actions={
          <>
            {headerActions}
            {actions}
          </>
        }
      />
      <div style={{ flex: 1, overflow: "hidden", minHeight: 0, display: "flex" }}>
        {loading ? (
          <div style={{ padding: 20, color: COLOR.textFaint, fontSize: 13 }}>loading…</div>
        ) : isMd && content ? (
          // Markdown is edited live: blocks render with KaTeX, the active block is raw.
          <LiveMarkdownEditor value={draft} onChange={onChangeDraft} />
        ) : editing && content ? (
          <textarea
            value={draft}
            onChange={(event) => onChangeDraft(event.target.value)}
            spellCheck={false}
            autoFocus
            style={rawEditorStyle}
          />
        ) : content?.binary ? (
          <div style={{ padding: 20, color: COLOR.textFaint, fontSize: 13 }}>
            <Dim>binary file</Dim> — {formatBytes(content.size)} not shown.
          </div>
        ) : content?.truncated ? (
          <div style={{ padding: 20, color: COLOR.textFaint, fontSize: 13 }}>
            <Dim>file too large to preview</Dim> ({formatBytes(content.size)}).
          </div>
        ) : (
          <div style={{ flex: 1, overflow: "auto", minHeight: 0 }}>
            <pre style={preStyle}>{highlightFor(content?.kind, content?.body ?? "")}</pre>
          </div>
        )}
      </div>
    </>
  );
}

const RAW_EDITOR_FONT_SIZE = 12.5;
const RAW_EDITOR_LINE_HEIGHT = RAW_EDITOR_FONT_SIZE * 1.65;
const RAW_EDITOR_PADDING_TOP = 12;

type EditorTextMatch = {
  start: number;
  end: number;
  lineIndex: number;
};

type ValidationErrorAnchor = {
  error: string;
  lineIndex: number;
};

function lineIndexForOffset(text: string, offset: number): number {
  let lineIndex = 0;
  const boundedOffset = Math.max(0, Math.min(offset, text.length));
  for (let index = 0; index < boundedOffset; index += 1) {
    if (text[index] === "\n") lineIndex += 1;
  }
  return lineIndex;
}

function textMatches(text: string, needle: string): EditorTextMatch[] {
  if (!needle) return [];
  const haystack = text.toLowerCase();
  const matches: EditorTextMatch[] = [];
  let offset = 0;
  while (offset <= haystack.length - needle.length) {
    const start = haystack.indexOf(needle, offset);
    if (start < 0) break;
    matches.push({
      start,
      end: start + needle.length,
      lineIndex: lineIndexForOffset(text, start)
    });
    offset = start + Math.max(needle.length, 1);
  }
  return matches;
}

function validationFieldHint(error: string): string | null {
  if (error.startsWith("missing_required:")) return error.slice("missing_required:".length);
  if (error.includes("grading_rubric") || error.startsWith("missing_rubric:")) return "grading_rubric";
  if (error.includes("criterion_facet")) return "criterion_facet_weights";
  if (error.includes("evidence_weight")) return "evidence_weights";
  if (error.includes("evidence_facet") || error.includes("diagnostic_footprint")) return "evidence_facets";
  if (error.includes("repair_target")) return "repair_targets";
  if (error.includes("retrieval_demand")) return "retrieval_demand";
  if (error.includes("transfer_distance")) return "transfer_distance";
  if (error.includes("scaffold_level")) return "scaffold_level";
  if (error.includes("surface_family")) return "surface_family";
  if (error.includes("misconception_consistent_answer")) return "misconception_consistent_answer";
  if (error.startsWith("invalid_concept_edge:")) return "source_concept_id";
  if (error.startsWith("duplicate_id:")) return "id";
  return null;
}

function validationErrorAnchors(text: string, errors: string[]): ValidationErrorAnchor[] {
  const lines = text.split("\n");
  const lastContentLine = Math.max(
    0,
    lines.reduce((last, line, index) => (line.trim() ? index : last), 0)
  );

  return errors.map((error) => {
    const fieldHint = validationFieldHint(error);
    const fieldLine = fieldHint
      ? lines.findIndex((line) => line.toLowerCase().includes(JSON.stringify(fieldHint).toLowerCase()))
      : -1;

    // Error suffixes generally carry the offending ref/id/facet. Search them
    // from most-specific to least-specific and require a JSON string match so
    // validation code words do not accidentally match property names.
    const detailLine = error
      .split(":")
      .slice(1)
      .reverse()
      .map((detail) => JSON.stringify(detail).toLowerCase())
      .reduce<number>(
        (foundLine, quotedDetail) =>
          foundLine >= 0
            ? foundLine
            : lines.findIndex((line) => line.toLowerCase().includes(quotedDetail)),
        -1
      );

    // Prefer the concrete invalid value. For an absent required field there is
    // no offending line, so the containing field or final object line is the
    // most useful insertion point.
    const lineIndex = detailLine >= 0 ? detailLine : fieldLine >= 0 ? fieldLine : lastContentLine;
    return { error, lineIndex };
  });
}

function jsonParseIssue(text: string): { message: string; lineIndex: number } | null {
  try {
    JSON.parse(text);
    return null;
  } catch (error) {
    const message = (error as Error).message;
    const explicitLine = /\bline\s+(\d+)\b/i.exec(message);
    if (explicitLine) {
      return { message, lineIndex: Math.max(0, Number(explicitLine[1]) - 1) };
    }
    const position = /\bposition\s+(\d+)\b/i.exec(message);
    return {
      message,
      lineIndex: position ? lineIndexForOffset(text, Number(position[1])) : Math.max(0, text.split("\n").length - 1)
    };
  }
}

function EditorLineHighlights({
  validationLines,
  findLines,
  currentFindLine,
  scrollTop
}: {
  validationLines: number[];
  findLines: number[];
  currentFindLine: number | null;
  scrollTop: number;
}) {
  const validationSet = new Set(validationLines);
  const findSet = new Set(findLines);
  const lines = [...new Set([...validationLines, ...findLines])].sort((left, right) => left - right);

  return (
    <div aria-hidden style={{ position: "absolute", inset: 0, zIndex: 0, pointerEvents: "none", overflow: "hidden" }}>
      {lines.map((lineIndex) => {
        const validation = validationSet.has(lineIndex);
        const find = findSet.has(lineIndex);
        const current = currentFindLine === lineIndex;
        return (
          <div
            key={lineIndex}
            style={{
              position: "absolute",
              top: RAW_EDITOR_PADDING_TOP + lineIndex * RAW_EDITOR_LINE_HEIGHT - scrollTop,
              left: 0,
              right: 0,
              height: RAW_EDITOR_LINE_HEIGHT,
              boxSizing: "border-box",
              background: current
                ? "rgba(255, 213, 79, 0.18)"
                : validation
                  ? COLOR.washRed
                  : find
                    ? "rgba(255, 213, 79, 0.10)"
                    : "transparent",
              borderLeft: validation ? `3px solid ${COLOR.red}` : undefined,
              outline: current ? `1px solid ${COLOR.amber}` : undefined,
              outlineOffset: current ? -1 : undefined
            }}
          />
        );
      })}
    </div>
  );
}

function ProposalEditor({
  found,
  draft,
  dirty,
  saving,
  onChangeDraft,
  onSave,
  onReject,
  onDelete
}: {
  found: { batch: ProposalBatchDto; item: ProposalItemDto } | null;
  draft: string;
  dirty: boolean;
  saving: boolean;
  onChangeDraft: (value: string) => void;
  onSave: () => void;
  onReject: () => void;
  onDelete: () => void;
}) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const findInputRef = useRef<HTMLInputElement | null>(null);
  const [findOpen, setFindOpen] = useState(false);
  const [findQuery, setFindQuery] = useState("");
  const [matchIdx, setMatchIdx] = useState(0);
  const [editorScrollTop, setEditorScrollTop] = useState(0);
  const item = found?.item ?? null;
  const validationAnchors = useMemo(
    () => validationErrorAnchors(draft, item?.validationErrors ?? []),
    [draft, item?.validationErrors]
  );
  const findNeedle = findQuery.trim().toLowerCase();
  const findMatches = useMemo(
    () => (findOpen && findNeedle.length >= 2 ? textMatches(draft, findNeedle) : []),
    [draft, findNeedle, findOpen]
  );
  const parseIssue = useMemo(() => jsonParseIssue(draft), [draft]);

  const scrollToLine = useCallback((lineIndex: number, behavior: ScrollBehavior = "smooth") => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    const top =
      RAW_EDITOR_PADDING_TOP
      + lineIndex * RAW_EDITOR_LINE_HEIGHT
      - (textarea.clientHeight - RAW_EDITOR_LINE_HEIGHT) / 2;
    textarea.scrollTo({ top: Math.max(0, top), behavior });
  }, []);

  const openFind = useCallback(() => {
    setFindOpen(true);
    window.setTimeout(() => findInputRef.current?.focus(), 0);
  }, []);

  const closeFind = useCallback(() => {
    setFindOpen(false);
    setFindQuery("");
    setMatchIdx(0);
  }, []);

  const gotoFindMatch = useCallback((delta: number) => {
    if (!findMatches.length) return;
    setMatchIdx((index) => (index + delta + findMatches.length) % findMatches.length);
  }, [findMatches.length]);

  useEffect(() => {
    setMatchIdx(0);
  }, [findNeedle]);

  useEffect(() => {
    if (!findOpen || !findMatches.length) return;
    const boundedIndex = Math.min(matchIdx, findMatches.length - 1);
    if (boundedIndex !== matchIdx) {
      setMatchIdx(boundedIndex);
      return;
    }
    const match = findMatches[boundedIndex];
    scrollToLine(match.lineIndex);
    textareaRef.current?.setSelectionRange(match.start, match.end);
  }, [findMatches, findOpen, matchIdx, scrollToLine]);

  useEffect(() => {
    closeFind();
    setEditorScrollTop(0);
  }, [item?.id, closeFind]);

  useEffect(() => {
    if (!item || validationAnchors.length === 0) return;
    const timer = window.setTimeout(
      () => scrollToLine(validationAnchors[0].lineIndex, "auto"),
      0
    );
    return () => window.clearTimeout(timer);
    // Scroll once when a proposal's persisted validation state changes. Draft
    // edits continuously remap highlights but must not keep stealing scroll.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item?.id, item?.validationErrors.join("|"), scrollToLine]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (!item) return;
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "f") {
        event.preventDefault();
        openFind();
      }
    };
    window.addEventListener("keydown", handler, { capture: true });
    return () => window.removeEventListener("keydown", handler, { capture: true });
  }, [item, openFind]);

  if (!found) {
    return <div style={{ padding: 30, color: COLOR.textFaint, fontSize: 13 }}>proposal not found — it may have been deleted.</div>;
  }
  const { item: foundItem } = found;
  const pending = foundItem.decision === "pending";
  const parseError = parseIssue?.message ?? null;

  return (
    <>
      <div style={{ padding: "12px 18px", borderBottom: `1px solid ${COLOR.border}`, display: "flex", alignItems: "center", gap: 10, flexShrink: 0, flexWrap: "wrap" }}>
        <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.purpleText }}>proposals/{proposalLabel(foundItem)}</span>
        <Pill color="purple">{foundItem.itemType.replace(/_/g, " ")}</Pill>
        <span style={{ color: COLOR.amber, fontFamily: FONT_MONO, fontSize: 12 }}>{foundItem.operation}</span>
        <Pill color={foundItem.decision === "accepted" ? "green" : foundItem.decision === "rejected" ? "red" : "amber"}>{foundItem.decision}</Pill>
        {foundItem.edited ? <Pill color="amber">edited</Pill> : null}
        {dirty ? <Faint style={{ fontSize: 11 }}>● unsaved</Faint> : null}
        <span style={{ flex: 1 }} />
        {findOpen ? (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <input
              ref={findInputRef}
              value={findQuery}
              onChange={(event) => setFindQuery(event.target.value)}
              placeholder="find in payload…"
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  gotoFindMatch(event.shiftKey ? -1 : 1);
                }
                if (event.key === "Escape") {
                  event.preventDefault();
                  event.stopPropagation();
                  closeFind();
                }
              }}
              style={{ fontFamily: FONT_MONO, fontSize: 11, width: 150, background: COLOR.bg, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "2px 6px" }}
            />
            <Faint style={{ fontSize: 10 }}>{findMatches.length ? `${matchIdx + 1}/${findMatches.length}` : "0/0"}</Faint>
            {([["↑", () => gotoFindMatch(-1)], ["↓", () => gotoFindMatch(1)], ["✕", closeFind]] as Array<[string, () => void]>).map(([label, onClick]) => (
              <button
                key={label}
                type="button"
                onClick={onClick}
                style={{ width: 20, height: 18, border: `1px solid ${COLOR.border}`, background: "transparent", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 10, cursor: "pointer", padding: 0 }}
              >
                {label}
              </button>
            ))}
          </div>
        ) : (
          <button
            type="button"
            onClick={openFind}
            title="find in payload (ctrl+f)"
            aria-label="find in proposal payload"
            style={{ width: 20, height: 18, border: `1px solid ${COLOR.border}`, background: "transparent", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11, cursor: "pointer", padding: 0 }}
          >
            ⌕
          </button>
        )}
        <ActionButton label={saving ? "saving…" : "save"} active={pending && dirty && !parseError} disabled={!pending || saving || Boolean(parseError)} onClick={onSave} />
        {foundItem.decision !== "rejected" ? <ActionButton label="reject" onClick={onReject} disabled={saving} /> : null}
        <ActionButton label="delete" danger onClick={onDelete} disabled={saving} />
      </div>
      {!pending ? (
        <div style={{ padding: "6px 18px", fontSize: 11, color: COLOR.amber, borderBottom: `1px solid ${COLOR.border}` }}>
          payload is read-only — only pending proposals can be edited (this one is {foundItem.decision}).
        </div>
      ) : null}
      {parseError ? (
        <div style={{ padding: "6px 18px", fontSize: 11, color: COLOR.red, borderBottom: `1px solid ${COLOR.border}`, display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
          <span>invalid JSON · {parseError}</span>
          <button
            type="button"
            onClick={() => scrollToLine(parseIssue?.lineIndex ?? 0)}
            title={`jump to line ${(parseIssue?.lineIndex ?? 0) + 1}`}
            style={{ border: `1px solid ${COLOR.red}`, background: COLOR.washRed, color: COLOR.red, fontFamily: FONT_MONO, fontSize: 10.5, cursor: "pointer", padding: "2px 6px" }}
          >
            L{(parseIssue?.lineIndex ?? 0) + 1}
          </button>
        </div>
      ) : null}
      {foundItem.validationStatus === "invalid" && validationAnchors.length ? (
        <div style={{ padding: "6px 18px", fontSize: 11, color: COLOR.red, borderBottom: `1px solid ${COLOR.border}`, display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
          <span>validation ·</span>
          {validationAnchors.map((anchor, index) => (
            <button
              key={`${anchor.error}-${index}`}
              type="button"
              onClick={() => scrollToLine(anchor.lineIndex)}
              title={`jump to line ${anchor.lineIndex + 1}`}
              style={{ border: `1px solid ${COLOR.red}`, background: COLOR.washRed, color: COLOR.red, fontFamily: FONT_MONO, fontSize: 10.5, cursor: "pointer", padding: "2px 6px" }}
            >
              {anchor.error} · L{anchor.lineIndex + 1}
            </button>
          ))}
        </div>
      ) : null}
      <div style={{ position: "relative", flex: 1, overflow: "hidden", minHeight: 0, display: "flex", background: COLOR.bgInput }}>
        <EditorLineHighlights
          validationLines={[
            ...validationAnchors.map((anchor) => anchor.lineIndex),
            ...(parseIssue ? [parseIssue.lineIndex] : [])
          ]}
          findLines={findMatches.map((match) => match.lineIndex)}
          currentFindLine={findMatches[matchIdx]?.lineIndex ?? null}
          scrollTop={editorScrollTop}
        />
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={(event) => onChangeDraft(event.target.value)}
          onScroll={(event) => setEditorScrollTop(event.currentTarget.scrollTop)}
          spellCheck={false}
          readOnly={!pending}
          wrap="off"
          aria-label="proposal payload JSON editor"
          style={{ ...rawEditorStyle, position: "relative", zIndex: 1, background: "transparent" }}
        />
      </div>
    </>
  );
}

function ActionButton({ label, onClick, active = false, disabled = false, danger = false }: { label: string; onClick: () => void; active?: boolean; disabled?: boolean; danger?: boolean }) {
  const accent = danger ? COLOR.red : COLOR.amber;
  return (
    <span
      onClick={disabled ? undefined : onClick}
      style={{
        padding: "4px 12px",
        border: `1px solid ${active ? accent : danger ? COLOR.red : COLOR.borderStrong}`,
        background: active ? (danger ? "#251313" : "#241d12") : "transparent",
        color: disabled ? COLOR.textFaint : active ? accent : danger ? COLOR.red : COLOR.textDim,
        fontFamily: FONT_MONO,
        fontSize: 11,
        fontWeight: 600,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1
      }}
    >
      {label}
    </span>
  );
}

const preStyle: CSSProperties = {
  margin: 0,
  padding: "16px 20px",
  fontFamily: FONT_MONO,
  fontSize: 12.5,
  lineHeight: 1.65,
  color: COLOR.text,
  whiteSpace: "pre-wrap",
  overflowWrap: "anywhere"
};

const rawEditorStyle: CSSProperties = {
  flex: 1,
  resize: "none",
  border: "none",
  outline: "none",
  background: COLOR.bgInput,
  color: COLOR.text,
  fontFamily: FONT_MONO,
  fontSize: RAW_EDITOR_FONT_SIZE,
  lineHeight: `${RAW_EDITOR_LINE_HEIGHT}px`,
  padding: "12px 16px",
  minHeight: 0
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}
