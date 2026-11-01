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
source_commit: "c94882abe7a8f5a7cde491603d6abba8a4c0e2db"
source_commit_timestamp: "2026-10-22T16:58:30-04:00"
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
| Source lines | 1618 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `c94882abe7a8f5a7cde491603d6abba8a4c0e2db` |
| Commit timestamp | `2026-10-22T16:58:30-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]]

## Public API

- `export function learnerTree(nodes: VaultTreeNode[], shell: ShellMode): VaultTreeNode[]` — function, line 116
- `export function initialFilePath(nodes: VaultTreeNode[], shell: ShellMode): string | null` — function, line 125
- `export function LibraryScreen(` — function, line 170

## Internal implementation anchors

- `type Selection = |` — type, line 25
- `function sameSelection(a: Selection, b: Selection): boolean` — function, line 30
- `function kindColor(kind: string | undefined): PillColor` — function, line 37
- `function FileGlyph(` — function, line 52
- `function entityPill(name: string):` — function, line 63
- `function inspectableTreeEntityId(node: VaultTreeNode): string | null` — function, line 71
- `const stem = node.name.replace(/\.(?:ya?ml|json|md|txt)$/i, "")` — const, line 73
- `function firstFilePath(nodes: VaultTreeNode[]): string | null` — function, line 77
- `const nested = firstFilePath(node.children)` — const, line 81
- `function isMachineFile(node: VaultTreeNode): boolean` — function, line 93
- `function firstMatchingPath(nodes: VaultTreeNode[], test: (node: VaultTreeNode)` — function, line 97
- `const nested = firstMatchingPath(node.children, test)` — const, line 101
- `function isDatabaseFile(node: VaultTreeNode): boolean` — function, line 112
- `const prune = (list: VaultTreeNode[]): VaultTreeNode[]` — const, line 118
- `function dirPaths(nodes: VaultTreeNode[], acc: string[] = []): string[]` — function, line 133
- `function visibleFiles(nodes: VaultTreeNode[], collapsed: Set<string>, acc: string[] = []): string[]` — function, line 145
- `function findProposal( proposals: ProposalsSnapshot | null, patchId: string, itemId: string ):` — function, line 153
- `const item = batch.items.find((candidate)` — const, line 160
- `function proposalLabel(item: ProposalItemDto): string` — function, line 166
- `const treeQuery = useCachedQuery(["get_vault_tree"], ()` — const, line 194
- `const snapshot: VaultTreeSnapshot | null = useMemo(()` — const, line 196
- `const data = treeQuery.data ?? null` — const, line 197
- `const proposalsQuery = useCachedQuery(["get_proposals"], ()` — const, line 201
- `const proposals: ProposalsSnapshot | null = proposalsQuery.data ?? null` — const, line 202
- `const sourceSetsQuery = useCachedQuery(["list_source_sets"], ()` — const, line 203
- `const sourceSets: SourceSetSummaryDto[] | null = sourceSetsQuery.data?.sourceSets ?? null` — const, line 204
- `const newInputRef = useRef<HTMLInputElement>(null)` — const, line 218
- `const seenTreeRef = useRef<VaultTreeSnapshot | null>(null)` — const, line 226
- `const firstTree = seenTreeRef.current === null` — const, line 229
- `const deep = dirPaths(snapshot.tree).filter((path)` — const, line 232
- `const first = initialFilePath(snapshot.tree, shellMode())` — const, line 237
- `const simple = simpleShell()` — const, line 246
- `const loadError = treeQuery.error ?? proposalsQuery.error ?? sourceSetsQuery.error` — const, line 250
- `const reloadProposals = ()` — const, line 256
- `const cachedFilePath = selected?.kind === "file" ? selected.path : null` — const, line 282
- `const fileQuery = useCachedQuery( cachedFilePath ? ["read_vault_file", cachedFilePath] : null, ()` — const, line 283
- `const loadingFile = fileQuery.loading` — const, line 288
- `const draftUntouchedRef = useRef(true)` — const, line 301
- `const file = fileQuery.data` — const, line 304
- `const focusedProposal = useMemo( ()` — const, line 315
- `const selectedFilePath = selected?.kind === "file" ? selected.path : null` — const, line 324
- `const selectedContent = content && selectedFilePath === content.path ? content : null` — const, line 325
- `const entityProvenanceTarget = useMemo<` — const, line 329
- `const name = selectedContent?.name` — const, line 330
- `const stem = name.replace(/\.(md|ya?ml|json|toml)$/i, "")` — const, line 332
- `const isMd = Boolean(selectedContent && selectedContent.kind === "md" && selectedContent.editable && !selectedContent.binary && !selectedContent.truncated)` — const, line 337
- `const isDatabase = Boolean(selectedContent?.database)` — const, line 338
- `const canEditRaw = Boolean(selectedContent && selectedContent.editable && !selectedContent.binary && !selectedContent.truncated && selectedContent.kind !== "md")` — const, line 339
- `const dirty = selected?.kind === "proposal" ? focusedProposal != null && draft !== focusedProposal.item.payloadJson : (isMd && selectedContent?.body != null && draft !== selectedContent.body) || (editing && selectedContent?.body != null && draft !== selectedC…` — const, line 340
- `function beginEdit()` — function, line 345
- `async function saveFile()` — function, line 351
- `const saved = await api.writeVaultFile(selected.path, draft)` — const, line 355
- `async function saveProposal()` — function, line 366
- `const next = await api.editProposalItem(focusedProposal.batch.id, focusedProposal.item.id, draft)` — const, line 371
- `const refreshed = findProposal(next, focusedProposal.batch.id, focusedProposal.item.id)` — const, line 372
- `async function rejectProposal()` — function, line 381
- `async function deleteProposal()` — function, line 393
- `async function submitNewFile()` — function, line 406
- `const path = newPath?.trim()` — const, line 407
- `const created = await api.createVaultFile(path)` — const, line 413
- `const pendingByBatch = useMemo(()` — const, line 427
- `const navEntries = useMemo<Selection[]>(()` — const, line 428
- `const files: Selection[] = snapshot ? visibleFiles(snapshot.tree, collapsed).map((path)` — const, line 429
- `const props: Selection[] = proposalsOpen ? pendingByBatch.flatMap((batch)` — const, line 430
- `const selectedNoteId = useMemo(()` — const, line 438
- `const match = /(?:^|[\\/])notes[\\/]([^\\/]+)\.md$/.exec(selected.path)` — const, line 440
- `const onKey = (event: KeyboardEvent)` — const, line 450
- `const target = event.target as HTMLElement | null` — const, line 451
- `const tag = target?.tagName?.toLowerCase()` — const, line 452
- `const inField = tag === "textarea" || tag === "input"` — const, line 453
- `const inSqliteBrowser = Boolean(target?.closest?.("[data-sqlite-browser]"))` — const, line 454
- `const ctrl = event.ctrlKey || event.metaKey` — const, line 455
- `const index = navEntries.findIndex((entry)` — const, line 496
- `const rootName = useMemo(()` — const, line 510
- `const parts = snapshot.root.split(/[\\/]+/).filter(Boolean)` — const, line 512
- `function toggleDir(path: string)` — function, line 516
- `const next = new Set(current)` — const, line 518
- `const keyBar = (()` — const, line 525
- `function TreeLevel(` — function, line 695
- `const indent = 8 + depth * 14` — const, line 715
- `const isCollapsed = collapsed.has(node.path)` — const, line 717
- `const isSelected = selected?.kind === "file" && node.path === selected.path` — const, line 741
- `const inspectableId = inspectableTreeEntityId(node)` — const, line 742
- `function ProposalsTree(` — function, line 777
- `const total = proposals?.batches.reduce((sum, batch)` — const, line 790
- `const isSelected = selected?.kind === "proposal" && selected.patchId === batch.id && selected.itemId === item.id` — const, line 801
- `function DecisionDot(` — function, line 832
- `const color = decision === "accepted" ? COLOR.green : decision === "rejected" ? COLOR.red : COLOR.amber` — const, line 833
- `function allocCells(counts: number[], cells: number): number[]` — function, line 839
- `const total = counts.reduce((a, b)` — const, line 840
- `const exact = counts.map((c)` — const, line 842
- `const out = exact.map((e)` — const, line 843
- `let used = out.reduce((a, b)` — let, line 847
- `const byRemainder = exact.map((e, i)` — const, line 848
- `let k = 0` — let, line 849
- `let best = -1` — let, line 856
- `const floor = counts[i] > 0 ? 1 : 0` — const, line 858
- `function CoverageBucketBar(` — function, line 872
- `const dem = rollup.buckets.demonstrated.count` — const, line 873
- `const ass = rollup.buckets.assessed.count` — const, line 874
- `const debt = rollup.buckets.noPracticeSupply.count` — const, line 875
- `const total = rollup.total` — const, line 876
- `const cells = Math.min(width, Math.max(total, 3))` — const, line 880
- `const label = `coverage: $` — const, line 882
- `function CoverageLegendRow(` — function, line 893
- `function SourceSetCoverageRow(` — function, line 904
- `const fetched = useRef(false)` — const, line 918
- `const load = ()` — const, line 920
- `const toggle = ()` — const, line 934
- `const generate = async ()` — const, line 941
- `const res = await api.createStudyMap(` — const, line 947
- `const n = Object.values(res.studyMap.itemCounts ??` — const, line 948
- `const debt = rollup && rollup !== "unavailable" ? rollup.buckets.noPracticeSupply.count : 0` — const, line 960
- `function CoverageSection(` — function, line 1030
- `function ViewerHeader(` — function, line 1055
- `const pill = content ? entityPill(content.name) : null` — const, line 1066
- `function FileViewer(` — function, line 1080
- `const actions = isMd ? ( <ActionButton label=` — const, line 1115
- `const RAW_EDITOR_FONT_SIZE = 12.5` — const, line 1171
- `const RAW_EDITOR_LINE_HEIGHT = RAW_EDITOR_FONT_SIZE * 1.65` — const, line 1172
- `const RAW_EDITOR_PADDING_TOP = 12` — const, line 1173
- `type EditorTextMatch =` — type, line 1175
- `type ValidationErrorAnchor =` — type, line 1181
- `function lineIndexForOffset(text: string, offset: number): number` — function, line 1186
- `let lineIndex = 0` — let, line 1187
- `const boundedOffset = Math.max(0, Math.min(offset, text.length))` — const, line 1188
- `function textMatches(text: string, needle: string): EditorTextMatch[]` — function, line 1195
- `const haystack = text.toLowerCase()` — const, line 1197
- `const matches: EditorTextMatch[] = []` — const, line 1198
- `let offset = 0` — let, line 1199
- `const start = haystack.indexOf(needle, offset)` — const, line 1201
- `function validationFieldHint(error: string): string | null` — function, line 1213
- `function validationErrorAnchors(text: string, errors: string[]): ValidationErrorAnchor[]` — function, line 1230
- `const lines = text.split("\n")` — const, line 1231
- `const lastContentLine = Math.max( 0, lines.reduce((last, line, index)` — const, line 1232
- `const fieldHint = validationFieldHint(error)` — const, line 1238
- `const fieldLine = fieldHint ? lines.findIndex((line)` — const, line 1239
- `const detailLine = error .split(":") .slice(1) .reverse() .map((detail)` — const, line 1246
- `const lineIndex = detailLine >= 0 ? detailLine : fieldLine >= 0 ? fieldLine : lastContentLine` — const, line 1262
- `function jsonParseIssue(text: string):` — function, line 1267
- `const message = (error as Error).message` — const, line 1272
- `const explicitLine = /\bline\s+(\d+)\b/i.exec(message)` — const, line 1273
- `const position = /\bposition\s+(\d+)\b/i.exec(message)` — const, line 1277
- `function EditorLineHighlights(` — function, line 1285
- `const validationSet = new Set(validationLines)` — const, line 1296
- `const findSet = new Set(findLines)` — const, line 1297
- `const lines = [...new Set([...validationLines, ...findLines])].sort((left, right)` — const, line 1298
- `const validation = validationSet.has(lineIndex)` — const, line 1303
- `const find = findSet.has(lineIndex)` — const, line 1304
- `const current = currentFindLine === lineIndex` — const, line 1305
- `function ProposalEditor(` — function, line 1334
- `const textareaRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 1353
- `const findInputRef = useRef<HTMLInputElement | null>(null)` — const, line 1354
- `const item = found?.item ?? null` — const, line 1359
- `const validationAnchors = useMemo( ()` — const, line 1360
- `const findNeedle = findQuery.trim().toLowerCase()` — const, line 1364
- `const findMatches = useMemo( ()` — const, line 1365
- `const parseIssue = useMemo(()` — const, line 1369
- `const scrollToLine = useCallback((lineIndex: number, behavior: ScrollBehavior = "smooth")` — const, line 1371
- `const textarea = textareaRef.current` — const, line 1372
- `const top = RAW_EDITOR_PADDING_TOP + lineIndex * RAW_EDITOR_LINE_HEIGHT - (textarea.clientHeight - RAW_EDITOR_LINE_HEIGHT) / 2` — const, line 1374
- `const openFind = useCallback(()` — const, line 1381
- `const closeFind = useCallback(()` — const, line 1386
- `const gotoFindMatch = useCallback((delta: number)` — const, line 1392
- `const boundedIndex = Math.min(matchIdx, findMatches.length - 1)` — const, line 1403
- `const match = findMatches[boundedIndex]` — const, line 1408
- `const timer = window.setTimeout( ()` — const, line 1420
- `const handler = (event: KeyboardEvent)` — const, line 1431
- `const pending = foundItem.decision === "pending"` — const, line 1447
- `const parseError = parseIssue?.message ?? null` — const, line 1448
- `function ActionButton(` — function, line 1567
- `const accent = danger ? COLOR.red : COLOR.amber` — const, line 1568
- `const preStyle: CSSProperties =` — const, line 1589
- `const rawEditorStyle: CSSProperties =` — const, line 1600
- `function formatBytes(bytes: number): string` — function, line 1614

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: dynamic import; no named call claim
- [[Reference/Desktop/TypeScript/screens/LibraryPlace|src/screens/LibraryPlace.tsx]] — dynamic import: dynamic import; no named call claim

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CoverageRollupDto`, `ProposalBatchDto`, `ProposalItemDto`, `ProposalsSnapshot`, `SourceSetSummaryDto`, `VaultFileContent`, `VaultTreeNode`, `VaultTreeSnapshot`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`, `useReportQueryError`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/shell|src/app/shell.ts]] — import-or-re-export; imports `ShellMode`, `shellMode`, `simpleShell`
- [[Reference/Desktop/TypeScript/components/ProvenancePanel|src/components/ProvenancePanel.tsx]] — import-or-re-export; imports `ProvenancePanel`
- [[Reference/Desktop/TypeScript/components/highlight|src/components/highlight.tsx]] — import-or-re-export; imports `highlightFor`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `PillColor`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `ReportError`
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

- [apps/learnloop-tauri/src/screens/retryWiring.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/retryWiring.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/classicErrors.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/classicErrors.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/LibraryScreen.firstFile.test.ts](../../../../../../apps/learnloop-tauri/src/screens/LibraryScreen.firstFile.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/LibraryScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/LibraryScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
