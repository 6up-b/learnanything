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
source_commit: "388f3ce6b9e89c35532881182dabb2d08272d445"
source_commit_timestamp: "2026-07-24T09:24:46-04:00"
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
| Source lines | 1563 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `388f3ce6b9e89c35532881182dabb2d08272d445` |
| Commit timestamp | `2026-07-24T09:24:46-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]]

## Public API

- `export function LibraryScreen(` — function, line 120

## Internal implementation anchors

- `type Selection = |` — type, line 20
- `function sameSelection(a: Selection, b: Selection): boolean` — function, line 25
- `function kindColor(kind: string | undefined): PillColor` — function, line 32
- `function FileGlyph(` — function, line 47
- `function entityPill(name: string):` — function, line 58
- `function inspectableTreeEntityId(node: VaultTreeNode): string | null` — function, line 66
- `const stem = node.name.replace(/\.(?:ya?ml|json|md|txt)$/i, "")` — const, line 68
- `function firstFilePath(nodes: VaultTreeNode[]): string | null` — function, line 72
- `const nested = firstFilePath(node.children)` — const, line 76
- `function dirPaths(nodes: VaultTreeNode[], acc: string[] = []): string[]` — function, line 83
- `function visibleFiles(nodes: VaultTreeNode[], collapsed: Set<string>, acc: string[] = []): string[]` — function, line 95
- `function findProposal( proposals: ProposalsSnapshot | null, patchId: string, itemId: string ):` — function, line 103
- `const item = batch.items.find((candidate)` — const, line 110
- `function proposalLabel(item: ProposalItemDto): string` — function, line 116
- `const newInputRef = useRef<HTMLInputElement>(null)` — const, line 157
- `const loadTree = ()` — const, line 162
- `let cancelled = false` — let, line 169
- `const deep = dirPaths(tree.tree).filter((path)` — const, line 173
- `const reloadProposals = ()` — const, line 205
- `let cancelled = false` — let, line 240
- `const focusedProposal = useMemo( ()` — const, line 263
- `const selectedFilePath = selected?.kind === "file" ? selected.path : null` — const, line 272
- `const selectedContent = content && selectedFilePath === content.path ? content : null` — const, line 273
- `const entityProvenanceTarget = useMemo<` — const, line 277
- `const name = selectedContent?.name` — const, line 278
- `const stem = name.replace(/\.(md|ya?ml|json|toml)$/i, "")` — const, line 280
- `const isMd = Boolean(selectedContent && selectedContent.kind === "md" && selectedContent.editable && !selectedContent.binary && !selectedContent.truncated)` — const, line 285
- `const isDatabase = Boolean(selectedContent?.database)` — const, line 286
- `const canEditRaw = Boolean(selectedContent && selectedContent.editable && !selectedContent.binary && !selectedContent.truncated && selectedContent.kind !== "md")` — const, line 287
- `const dirty = selected?.kind === "proposal" ? focusedProposal != null && draft !== focusedProposal.item.payloadJson : (isMd && selectedContent?.body != null && draft !== selectedContent.body) || (editing && selectedContent?.body != null && draft !== selectedC…` — const, line 288
- `function beginEdit()` — function, line 293
- `async function saveFile()` — function, line 299
- `const saved = await api.writeVaultFile(selected.path, draft)` — const, line 303
- `async function saveProposal()` — function, line 314
- `const next = await api.editProposalItem(focusedProposal.batch.id, focusedProposal.item.id, draft)` — const, line 318
- `const refreshed = findProposal(next, focusedProposal.batch.id, focusedProposal.item.id)` — const, line 320
- `async function rejectProposal()` — function, line 329
- `async function deleteProposal()` — function, line 341
- `const next = await api.deleteProposalItem(focusedProposal.batch.id, focusedProposal.item.id)` — const, line 345
- `async function submitNewFile()` — function, line 355
- `const path = newPath?.trim()` — const, line 356
- `const created = await api.createVaultFile(path)` — const, line 362
- `const pendingByBatch = useMemo(()` — const, line 376
- `const navEntries = useMemo<Selection[]>(()` — const, line 377
- `const files: Selection[] = snapshot ? visibleFiles(snapshot.tree, collapsed).map((path)` — const, line 378
- `const props: Selection[] = proposalsOpen ? pendingByBatch.flatMap((batch)` — const, line 379
- `const selectedNoteId = useMemo(()` — const, line 387
- `const match = /(?:^|[\\/])notes[\\/]([^\\/]+)\.md$/.exec(selected.path)` — const, line 389
- `const onKey = (event: KeyboardEvent)` — const, line 399
- `const target = event.target as HTMLElement | null` — const, line 400
- `const tag = target?.tagName?.toLowerCase()` — const, line 401
- `const inField = tag === "textarea" || tag === "input"` — const, line 402
- `const inSqliteBrowser = Boolean(target?.closest?.("[data-sqlite-browser]"))` — const, line 403
- `const ctrl = event.ctrlKey || event.metaKey` — const, line 404
- `const index = navEntries.findIndex((entry)` — const, line 442
- `const rootName = useMemo(()` — const, line 456
- `const parts = snapshot.root.split(/[\\/]+/).filter(Boolean)` — const, line 458
- `function toggleDir(path: string)` — function, line 462
- `const next = new Set(current)` — const, line 464
- `const keyBar = (()` — const, line 471
- `function TreeLevel(` — function, line 641
- `const indent = 8 + depth * 14` — const, line 661
- `const isCollapsed = collapsed.has(node.path)` — const, line 663
- `const isSelected = selected?.kind === "file" && node.path === selected.path` — const, line 687
- `const inspectableId = inspectableTreeEntityId(node)` — const, line 688
- `function ProposalsTree(` — function, line 723
- `const total = proposals?.batches.reduce((sum, batch)` — const, line 736
- `const isSelected = selected?.kind === "proposal" && selected.patchId === batch.id && selected.itemId === item.id` — const, line 747
- `function DecisionDot(` — function, line 778
- `const color = decision === "accepted" ? COLOR.green : decision === "rejected" ? COLOR.red : COLOR.amber` — const, line 779
- `function allocCells(counts: number[], cells: number): number[]` — function, line 785
- `const total = counts.reduce((a, b)` — const, line 786
- `const exact = counts.map((c)` — const, line 788
- `const out = exact.map((e)` — const, line 789
- `let used = out.reduce((a, b)` — let, line 793
- `const byRemainder = exact.map((e, i)` — const, line 794
- `let k = 0` — let, line 795
- `let best = -1` — let, line 802
- `const floor = counts[i] > 0 ? 1 : 0` — const, line 804
- `function CoverageBucketBar(` — function, line 818
- `const dem = rollup.buckets.demonstrated.count` — const, line 819
- `const ass = rollup.buckets.assessed.count` — const, line 820
- `const debt = rollup.buckets.noPracticeSupply.count` — const, line 821
- `const total = rollup.total` — const, line 822
- `const cells = Math.min(width, Math.max(total, 3))` — const, line 826
- `const label = `coverage: $` — const, line 828
- `function CoverageLegendRow(` — function, line 839
- `function SourceSetCoverageRow(` — function, line 850
- `const fetched = useRef(false)` — const, line 864
- `const load = ()` — const, line 866
- `const toggle = ()` — const, line 880
- `const generate = async ()` — const, line 887
- `const res = await api.createStudyMap(` — const, line 893
- `const n = Object.values(res.studyMap.itemCounts ??` — const, line 894
- `const debt = rollup && rollup !== "unavailable" ? rollup.buckets.noPracticeSupply.count : 0` — const, line 906
- `function CoverageSection(` — function, line 976
- `function ViewerHeader(` — function, line 1001
- `const pill = content ? entityPill(content.name) : null` — const, line 1012
- `function FileViewer(` — function, line 1026
- `const actions = isMd ? ( <ActionButton label=` — const, line 1061
- `const RAW_EDITOR_FONT_SIZE = 12.5` — const, line 1117
- `const RAW_EDITOR_LINE_HEIGHT = RAW_EDITOR_FONT_SIZE * 1.65` — const, line 1118
- `const RAW_EDITOR_PADDING_TOP = 12` — const, line 1119
- `type EditorTextMatch =` — type, line 1121
- `type ValidationErrorAnchor =` — type, line 1127
- `function lineIndexForOffset(text: string, offset: number): number` — function, line 1132
- `let lineIndex = 0` — let, line 1133
- `const boundedOffset = Math.max(0, Math.min(offset, text.length))` — const, line 1134
- `function textMatches(text: string, needle: string): EditorTextMatch[]` — function, line 1141
- `const haystack = text.toLowerCase()` — const, line 1143
- `const matches: EditorTextMatch[] = []` — const, line 1144
- `let offset = 0` — let, line 1145
- `const start = haystack.indexOf(needle, offset)` — const, line 1147
- `function validationFieldHint(error: string): string | null` — function, line 1159
- `function validationErrorAnchors(text: string, errors: string[]): ValidationErrorAnchor[]` — function, line 1176
- `const lines = text.split("\n")` — const, line 1177
- `const lastContentLine = Math.max( 0, lines.reduce((last, line, index)` — const, line 1178
- `const fieldHint = validationFieldHint(error)` — const, line 1184
- `const fieldLine = fieldHint ? lines.findIndex((line)` — const, line 1185
- `const detailLine = error .split(":") .slice(1) .reverse() .map((detail)` — const, line 1192
- `const lineIndex = detailLine >= 0 ? detailLine : fieldLine >= 0 ? fieldLine : lastContentLine` — const, line 1208
- `function jsonParseIssue(text: string):` — function, line 1213
- `const message = (error as Error).message` — const, line 1218
- `const explicitLine = /\bline\s+(\d+)\b/i.exec(message)` — const, line 1219
- `const position = /\bposition\s+(\d+)\b/i.exec(message)` — const, line 1223
- `function EditorLineHighlights(` — function, line 1231
- `const validationSet = new Set(validationLines)` — const, line 1242
- `const findSet = new Set(findLines)` — const, line 1243
- `const lines = [...new Set([...validationLines, ...findLines])].sort((left, right)` — const, line 1244
- `const validation = validationSet.has(lineIndex)` — const, line 1249
- `const find = findSet.has(lineIndex)` — const, line 1250
- `const current = currentFindLine === lineIndex` — const, line 1251
- `function ProposalEditor(` — function, line 1280
- `const textareaRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 1299
- `const findInputRef = useRef<HTMLInputElement | null>(null)` — const, line 1300
- `const item = found?.item ?? null` — const, line 1305
- `const validationAnchors = useMemo( ()` — const, line 1306
- `const findNeedle = findQuery.trim().toLowerCase()` — const, line 1310
- `const findMatches = useMemo( ()` — const, line 1311
- `const parseIssue = useMemo(()` — const, line 1315
- `const scrollToLine = useCallback((lineIndex: number, behavior: ScrollBehavior = "smooth")` — const, line 1317
- `const textarea = textareaRef.current` — const, line 1318
- `const top = RAW_EDITOR_PADDING_TOP + lineIndex * RAW_EDITOR_LINE_HEIGHT - (textarea.clientHeight - RAW_EDITOR_LINE_HEIGHT) / 2` — const, line 1320
- `const openFind = useCallback(()` — const, line 1327
- `const closeFind = useCallback(()` — const, line 1332
- `const gotoFindMatch = useCallback((delta: number)` — const, line 1338
- `const boundedIndex = Math.min(matchIdx, findMatches.length - 1)` — const, line 1349
- `const match = findMatches[boundedIndex]` — const, line 1354
- `const timer = window.setTimeout( ()` — const, line 1366
- `const handler = (event: KeyboardEvent)` — const, line 1377
- `const pending = foundItem.decision === "pending"` — const, line 1392
- `const parseError = parseIssue?.message ?? null` — const, line 1393
- `function ActionButton(` — function, line 1512
- `const accent = danger ? COLOR.red : COLOR.amber` — const, line 1513
- `const preStyle: CSSProperties =` — const, line 1534
- `const rawEditorStyle: CSSProperties =` — const, line 1545
- `function formatBytes(bytes: number): string` — function, line 1559

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `LibraryScreen`; references `LibraryScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CoverageRollupDto`, `ProposalBatchDto`, `ProposalItemDto`, `ProposalsSnapshot`, `SourceSetSummaryDto`, `VaultFileContent`, `VaultTreeNode`, `VaultTreeSnapshot`
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

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/LibraryScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/LibraryScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
