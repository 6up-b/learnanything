---
title: "Desktop module · src/screens/LibraryScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.LibraryScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/LibraryScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/LibraryScreen.tsx"
source_commit: "7f37f7bef54c4dc6170182720840faf546d9f51b"
source_commit_timestamp: "2026-09-03T10:56:04-07:00"
source_worktree_state: "clean"
activation_kind: "entry-reachable build graph"
activation_evidence: "A static TypeScript import path reaches this file from the Vite entry src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/screens/LibraryScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `LibraryScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/LibraryScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/LibraryScreen.tsx) |
| Source lines | 1548 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `7f37f7bef54c4dc6170182720840faf546d9f51b` |
| Commit timestamp | `2026-09-03T10:56:04-07:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]]

## Public API

- `export function LibraryScreen(` — function, line 122

## Internal implementation anchors

- `type Selection = |` — type, line 22
- `function sameSelection(a: Selection, b: Selection): boolean` — function, line 27
- `function kindColor(kind: string | undefined): PillColor` — function, line 34
- `function FileGlyph(` — function, line 49
- `function entityPill(name: string):` — function, line 60
- `function inspectableTreeEntityId(node: VaultTreeNode): string | null` — function, line 68
- `const stem = node.name.replace(/\.(?:ya?ml|json|md|txt)$/i, "")` — const, line 70
- `function firstFilePath(nodes: VaultTreeNode[]): string | null` — function, line 74
- `const nested = firstFilePath(node.children)` — const, line 78
- `function dirPaths(nodes: VaultTreeNode[], acc: string[] = []): string[]` — function, line 85
- `function visibleFiles(nodes: VaultTreeNode[], collapsed: Set<string>, acc: string[] = []): string[]` — function, line 97
- `function findProposal( proposals: ProposalsSnapshot | null, patchId: string, itemId: string ):` — function, line 105
- `const item = batch.items.find((candidate)` — const, line 112
- `function proposalLabel(item: ProposalItemDto): string` — function, line 118
- `const treeQuery = useCachedQuery(["get_vault_tree"], ()` — const, line 146
- `const snapshot: VaultTreeSnapshot | null = treeQuery.data ?? null` — const, line 147
- `const proposalsQuery = useCachedQuery(["get_proposals"], ()` — const, line 148
- `const proposals: ProposalsSnapshot | null = proposalsQuery.data ?? null` — const, line 149
- `const sourceSetsQuery = useCachedQuery(["list_source_sets"], ()` — const, line 150
- `const sourceSets: SourceSetSummaryDto[] | null = sourceSetsQuery.data?.sourceSets ?? null` — const, line 151
- `const newInputRef = useRef<HTMLInputElement>(null)` — const, line 165
- `const seenTreeRef = useRef<VaultTreeSnapshot | null>(null)` — const, line 173
- `const firstTree = seenTreeRef.current === null` — const, line 176
- `const deep = dirPaths(snapshot.tree).filter((path)` — const, line 179
- `const loadError = treeQuery.error ?? proposalsQuery.error ?? sourceSetsQuery.error` — const, line 185
- `const reloadProposals = ()` — const, line 190
- `const cachedFilePath = selected?.kind === "file" ? selected.path : null` — const, line 216
- `const fileQuery = useCachedQuery( cachedFilePath ? ["read_vault_file", cachedFilePath] : null, ()` — const, line 217
- `const loadingFile = fileQuery.loading` — const, line 222
- `const draftUntouchedRef = useRef(true)` — const, line 235
- `const file = fileQuery.data` — const, line 238
- `const focusedProposal = useMemo( ()` — const, line 249
- `const selectedFilePath = selected?.kind === "file" ? selected.path : null` — const, line 258
- `const selectedContent = content && selectedFilePath === content.path ? content : null` — const, line 259
- `const entityProvenanceTarget = useMemo<` — const, line 263
- `const name = selectedContent?.name` — const, line 264
- `const stem = name.replace(/\.(md|ya?ml|json|toml)$/i, "")` — const, line 266
- `const isMd = Boolean(selectedContent && selectedContent.kind === "md" && selectedContent.editable && !selectedContent.binary && !selectedContent.truncated)` — const, line 271
- `const isDatabase = Boolean(selectedContent?.database)` — const, line 272
- `const canEditRaw = Boolean(selectedContent && selectedContent.editable && !selectedContent.binary && !selectedContent.truncated && selectedContent.kind !== "md")` — const, line 273
- `const dirty = selected?.kind === "proposal" ? focusedProposal != null && draft !== focusedProposal.item.payloadJson : (isMd && selectedContent?.body != null && draft !== selectedContent.body) || (editing && selectedContent?.body != null && draft !== selectedC…` — const, line 274
- `function beginEdit()` — function, line 279
- `async function saveFile()` — function, line 285
- `const saved = await api.writeVaultFile(selected.path, draft)` — const, line 289
- `async function saveProposal()` — function, line 300
- `const next = await api.editProposalItem(focusedProposal.batch.id, focusedProposal.item.id, draft)` — const, line 305
- `const refreshed = findProposal(next, focusedProposal.batch.id, focusedProposal.item.id)` — const, line 306
- `async function rejectProposal()` — function, line 315
- `async function deleteProposal()` — function, line 327
- `async function submitNewFile()` — function, line 340
- `const path = newPath?.trim()` — const, line 341
- `const created = await api.createVaultFile(path)` — const, line 347
- `const pendingByBatch = useMemo(()` — const, line 361
- `const navEntries = useMemo<Selection[]>(()` — const, line 362
- `const files: Selection[] = snapshot ? visibleFiles(snapshot.tree, collapsed).map((path)` — const, line 363
- `const props: Selection[] = proposalsOpen ? pendingByBatch.flatMap((batch)` — const, line 364
- `const selectedNoteId = useMemo(()` — const, line 372
- `const match = /(?:^|[\\/])notes[\\/]([^\\/]+)\.md$/.exec(selected.path)` — const, line 374
- `const onKey = (event: KeyboardEvent)` — const, line 384
- `const target = event.target as HTMLElement | null` — const, line 385
- `const tag = target?.tagName?.toLowerCase()` — const, line 386
- `const inField = tag === "textarea" || tag === "input"` — const, line 387
- `const inSqliteBrowser = Boolean(target?.closest?.("[data-sqlite-browser]"))` — const, line 388
- `const ctrl = event.ctrlKey || event.metaKey` — const, line 389
- `const index = navEntries.findIndex((entry)` — const, line 427
- `const rootName = useMemo(()` — const, line 441
- `const parts = snapshot.root.split(/[\\/]+/).filter(Boolean)` — const, line 443
- `function toggleDir(path: string)` — function, line 447
- `const next = new Set(current)` — const, line 449
- `const keyBar = (()` — const, line 456
- `function TreeLevel(` — function, line 626
- `const indent = 8 + depth * 14` — const, line 646
- `const isCollapsed = collapsed.has(node.path)` — const, line 648
- `const isSelected = selected?.kind === "file" && node.path === selected.path` — const, line 672
- `const inspectableId = inspectableTreeEntityId(node)` — const, line 673
- `function ProposalsTree(` — function, line 708
- `const total = proposals?.batches.reduce((sum, batch)` — const, line 721
- `const isSelected = selected?.kind === "proposal" && selected.patchId === batch.id && selected.itemId === item.id` — const, line 732
- `function DecisionDot(` — function, line 763
- `const color = decision === "accepted" ? COLOR.green : decision === "rejected" ? COLOR.red : COLOR.amber` — const, line 764
- `function allocCells(counts: number[], cells: number): number[]` — function, line 770
- `const total = counts.reduce((a, b)` — const, line 771
- `const exact = counts.map((c)` — const, line 773
- `const out = exact.map((e)` — const, line 774
- `let used = out.reduce((a, b)` — let, line 778
- `const byRemainder = exact.map((e, i)` — const, line 779
- `let k = 0` — let, line 780
- `let best = -1` — let, line 787
- `const floor = counts[i] > 0 ? 1 : 0` — const, line 789
- `function CoverageBucketBar(` — function, line 803
- `const dem = rollup.buckets.demonstrated.count` — const, line 804
- `const ass = rollup.buckets.assessed.count` — const, line 805
- `const debt = rollup.buckets.noPracticeSupply.count` — const, line 806
- `const total = rollup.total` — const, line 807
- `const cells = Math.min(width, Math.max(total, 3))` — const, line 811
- `const label = `coverage: $` — const, line 813
- `function CoverageLegendRow(` — function, line 824
- `function SourceSetCoverageRow(` — function, line 835
- `const fetched = useRef(false)` — const, line 849
- `const load = ()` — const, line 851
- `const toggle = ()` — const, line 865
- `const generate = async ()` — const, line 872
- `const res = await api.createStudyMap(` — const, line 878
- `const n = Object.values(res.studyMap.itemCounts ??` — const, line 879
- `const debt = rollup && rollup !== "unavailable" ? rollup.buckets.noPracticeSupply.count : 0` — const, line 891
- `function CoverageSection(` — function, line 961
- `function ViewerHeader(` — function, line 986
- `const pill = content ? entityPill(content.name) : null` — const, line 997
- `function FileViewer(` — function, line 1011
- `const actions = isMd ? ( <ActionButton label=` — const, line 1046
- `const RAW_EDITOR_FONT_SIZE = 12.5` — const, line 1102
- `const RAW_EDITOR_LINE_HEIGHT = RAW_EDITOR_FONT_SIZE * 1.65` — const, line 1103
- `const RAW_EDITOR_PADDING_TOP = 12` — const, line 1104
- `type EditorTextMatch =` — type, line 1106
- `type ValidationErrorAnchor =` — type, line 1112
- `function lineIndexForOffset(text: string, offset: number): number` — function, line 1117
- `let lineIndex = 0` — let, line 1118
- `const boundedOffset = Math.max(0, Math.min(offset, text.length))` — const, line 1119
- `function textMatches(text: string, needle: string): EditorTextMatch[]` — function, line 1126
- `const haystack = text.toLowerCase()` — const, line 1128
- `const matches: EditorTextMatch[] = []` — const, line 1129
- `let offset = 0` — let, line 1130
- `const start = haystack.indexOf(needle, offset)` — const, line 1132
- `function validationFieldHint(error: string): string | null` — function, line 1144
- `function validationErrorAnchors(text: string, errors: string[]): ValidationErrorAnchor[]` — function, line 1161
- `const lines = text.split("\n")` — const, line 1162
- `const lastContentLine = Math.max( 0, lines.reduce((last, line, index)` — const, line 1163
- `const fieldHint = validationFieldHint(error)` — const, line 1169
- `const fieldLine = fieldHint ? lines.findIndex((line)` — const, line 1170
- `const detailLine = error .split(":") .slice(1) .reverse() .map((detail)` — const, line 1177
- `const lineIndex = detailLine >= 0 ? detailLine : fieldLine >= 0 ? fieldLine : lastContentLine` — const, line 1193
- `function jsonParseIssue(text: string):` — function, line 1198
- `const message = (error as Error).message` — const, line 1203
- `const explicitLine = /\bline\s+(\d+)\b/i.exec(message)` — const, line 1204
- `const position = /\bposition\s+(\d+)\b/i.exec(message)` — const, line 1208
- `function EditorLineHighlights(` — function, line 1216
- `const validationSet = new Set(validationLines)` — const, line 1227
- `const findSet = new Set(findLines)` — const, line 1228
- `const lines = [...new Set([...validationLines, ...findLines])].sort((left, right)` — const, line 1229
- `const validation = validationSet.has(lineIndex)` — const, line 1234
- `const find = findSet.has(lineIndex)` — const, line 1235
- `const current = currentFindLine === lineIndex` — const, line 1236
- `function ProposalEditor(` — function, line 1265
- `const textareaRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 1284
- `const findInputRef = useRef<HTMLInputElement | null>(null)` — const, line 1285
- `const item = found?.item ?? null` — const, line 1290
- `const validationAnchors = useMemo( ()` — const, line 1291
- `const findNeedle = findQuery.trim().toLowerCase()` — const, line 1295
- `const findMatches = useMemo( ()` — const, line 1296
- `const parseIssue = useMemo(()` — const, line 1300
- `const scrollToLine = useCallback((lineIndex: number, behavior: ScrollBehavior = "smooth")` — const, line 1302
- `const textarea = textareaRef.current` — const, line 1303
- `const top = RAW_EDITOR_PADDING_TOP + lineIndex * RAW_EDITOR_LINE_HEIGHT - (textarea.clientHeight - RAW_EDITOR_LINE_HEIGHT) / 2` — const, line 1305
- `const openFind = useCallback(()` — const, line 1312
- `const closeFind = useCallback(()` — const, line 1317
- `const gotoFindMatch = useCallback((delta: number)` — const, line 1323
- `const boundedIndex = Math.min(matchIdx, findMatches.length - 1)` — const, line 1334
- `const match = findMatches[boundedIndex]` — const, line 1339
- `const timer = window.setTimeout( ()` — const, line 1351
- `const handler = (event: KeyboardEvent)` — const, line 1362
- `const pending = foundItem.decision === "pending"` — const, line 1377
- `const parseError = parseIssue?.message ?? null` — const, line 1378
- `function ActionButton(` — function, line 1497
- `const accent = danger ? COLOR.red : COLOR.amber` — const, line 1498
- `const preStyle: CSSProperties =` — const, line 1519
- `const rawEditorStyle: CSSProperties =` — const, line 1530
- `function formatBytes(bytes: number): string` — function, line 1544

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: dynamic import; no named call claim

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CoverageRollupDto`, `ProposalBatchDto`, `ProposalItemDto`, `ProposalsSnapshot`, `SourceSetSummaryDto`, `VaultFileContent`, `VaultTreeNode`, `VaultTreeSnapshot`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/components/ProvenancePanel|src/components/ProvenancePanel.tsx]] — import-or-re-export; imports `ProvenancePanel`
- [[Reference/Desktop/TypeScript/components/highlight|src/components/highlight.tsx]] — import-or-re-export; imports `highlightFor`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `PillColor`
- [[Reference/Desktop/TypeScript/render/LiveMarkdownEditor|src/render/LiveMarkdownEditor.tsx]] — import-or-re-export; imports `LiveMarkdownEditor`
- [[Reference/Desktop/TypeScript/screens/SqliteBrowser|src/screens/SqliteBrowser.tsx]] — import-or-re-export; imports `SqliteBrowser`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/LibraryScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/LibraryScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
