---
title: "Desktop module · src/screens/IngestScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.IngestScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/IngestScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/IngestScreen.tsx"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
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

# `src/screens/IngestScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `IngestScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/IngestScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/IngestScreen.tsx) |
| Source lines | 1559 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]]

## Public API

- `export function IngestScreen(` — function, line 431

## Internal implementation anchors

- `type Kind = "web" | "arxiv" | "pdf" | "youtube" | "local" | "audio"` — type, line 23
- `function detectKind(source: string): Kind | null` — function, line 26
- `const s = (source || "").trim()` — const, line 27
- `type KindMeta =` — type, line 40
- `const KIND_META: Record<Kind, KindMeta> =` — const, line 42
- `type Mode = IngestMode` — type, line 51
- `function kebabCase(value: string): string` — function, line 53
- `function Card(` — function, line 61
- `function KindChips(` — function, line 79
- `const order: Kind[] = ["web", "arxiv", "pdf", "youtube", "local", "audio"]` — const, line 80
- `const sel = k === active` — const, line 84
- `const meta = KIND_META[k]` — const, line 85
- `function LearnerLevelChip()` — function, line 111
- `let alive = true` — let, line 119
- `const pick = async (next: StartingLevel)` — const, line 136
- `const profile = await api.setLearnerProfile(` — const, line 141
- `const label = STARTING_LEVELS.find((s)` — const, line 152
- `function SubjectPicker(` — function, line 225
- `const inputRef = useRef<HTMLInputElement>(null)` — const, line 240
- `async function submit()` — function, line 246
- `const trimmed = title.trim()` — const, line 247
- `const created = await onCreate(trimmed)` — const, line 249
- `const sel = s === value` — const, line 258
- `const SPINNER_FRAMES = ["◐", "◓", "◑", "◒"]` — const, line 348
- `const INGEST_PHASES: Array<` — const, line 350
- `function RunningCard(` — function, line 358
- `const frame = SPINNER_FRAMES[Math.floor(elapsed * 2) % SPINNER_FRAMES.length]` — const, line 359
- `const minutes = Math.floor(elapsed / 60)` — const, line 360
- `const seconds = Math.floor(elapsed % 60)` — const, line 361
- `const clock = minutes > 0 ? `$` — const, line 362
- `const activeIndex = INGEST_PHASES.findIndex((item)` — const, line 363
- `const cancelling = job.phase === "cancelling"` — const, line 364
- `const complete = activeIndex > index` — const, line 384
- `const active = activeIndex === index` — const, line 385
- `const overlayActive = outlineTarget !== null` — const, line 454
- `const card = lib.sources.find((c)` — const, line 482
- `function IngestHome(` — function, line 538
- `const inputRef = useRef<HTMLInputElement>(null)` — const, line 584
- `const activityRef = useRef<HTMLDivElement>(null)` — const, line 585
- `const runningRef = useRef(false)` — const, line 586
- `const kind = authoritativeKind ?? detectKind(source)` — const, line 588
- `const running = job?.status === "queued" || job?.status === "running"` — const, line 589
- `const result = job?.status === "completed" ? job.result : null` — const, line 590
- `const error = localError ?? (job?.status === "failed" || job?.status === "cancelled" ? job.error?.message ?? job.message : null)` — const, line 591
- `const stagingVisible = mode === "canonical"` — const, line 595
- `const hasStaged = staged.length > 0` — const, line 596
- `const canRun = (source.trim().length > 0 || (stagingVisible && hasStaged)) && !running && !importing && (mode === "canonical" || subject !== null) && (mode !== "canonical" || pageSelectionError(pageSelection) === null) && Object.values(stagedPageRanges).every…` — const, line 597
- `const importCount = staged.length + (source.trim() ? 1 : 0)` — const, line 604
- `const subjectTooltip = mode === "canonical" ? "imports land in the vault-global source library — no subject needed. A subject chosen here just pre-tags the import batch` — const, line 605
- `const refreshSubjects = useCallback(async ()` — const, line 610
- `const snapshot = await api.loadVault()` — const, line 612
- `const list = snapshot.vault?.subjects ?? []` — const, line 613
- `let cancelled = false` — let, line 633
- `const active = snapshot.jobs.find((candidate)` — const, line 636
- `let cancelled = false` — let, line 647
- `let timer: number | undefined` — let, line 648
- `const poll = async ()` — const, line 649
- `const next = await api.getIngestJob(jobId)` — const, line 651
- `const commandError = e as CommandError` — const, line 663
- `const candidate = source.trim()` — const, line 682
- `let cancelled = false` — let, line 688
- `const timer = window.setTimeout(()` — const, line 690
- `const mapped: Record<string, Kind> =` — const, line 694
- `let cancelled = false` — let, line 724
- `const timer = window.setTimeout(()` — const, line 725
- `const next: Record<string, AcquisitionPreviewItem> =` — const, line 729
- `const parsed = Date.parse(job.startedAt ?? job.createdAt)` — const, line 746
- `const started = Number.isNaN(parsed) ? Date.now() : parsed` — const, line 747
- `const id = window.setInterval(()` — const, line 749
- `async function createSubject(title: string): Promise<boolean>` — function, line 753
- `const id = kebabCase(title)` — const, line 754
- `const res = await api.runCliCommand(["add-subject", id, title])` — const, line 759
- `function clearFinishedJob()` — function, line 776
- `function stageCurrent()` — function, line 782
- `const src = source.trim()` — const, line 783
- `const next =` — const, line 787
- `function stageDropped(paths: string[])` — function, line 797
- `const unique = paths.filter((path, index)` — const, line 800
- `const next =` — const, line 807
- `const fileDragging = useSourceFileDrop(` — const, line 813
- `function removeStaged(src: string)` — function, line 819
- `const next =` — const, line 822
- `const next =` — const, line 827
- `async function startCanonicalImport(entries: Array<` — function, line 833
- `const batch = await api.startImportBatch(` — const, line 836
- `async function startExamSeeding(src: string)` — function, line 865
- `const started = await api.startIngest(` — const, line 870
- `const commandError = e as CommandError` — const, line 874
- `const activeJobId = (commandError.details as` — const, line 875
- `async function startRun()` — function, line 886
- `const trimmed = source.trim()` — const, line 888
- `const entries = [ ...staged.map((stagedSource)` — const, line 891
- `async function cancelIngest()` — function, line 916
- `async function chooseLocalSource()` — function, line 925
- `const selected = await openDialog(` — const, line 927
- `function onKey(event: KeyboardEvent)` — function, line 943
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 947
- `const isInput = tag === "input" || tag === "textarea"` — const, line 948
- `const modeChip = (m: Mode, icon: string, label: string)` — const, line 976
- `const sel = mode === m` — const, line 977
- `const rowKind = detectKind(src)` — const, line 1274
- `const meta = rowKind ? KIND_META[rowKind] : null` — const, line 1275
- `const preview = previews[src]` — const, line 1276
- `const stagedRange = stagedPageRanges[src] ?? ""` — const, line 1277

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `IngestScreen`; references `IngestScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AcquisitionPreviewItem`, `CommandError`, `IngestBatchDto`, `IngestJobDto`, `IngestJobPhase`, `IngestMode`, `PdfEngine`, `SourceLibraryCard`, `StartingLevel`
- [[Reference/Desktop/TypeScript/components/AsciiLoadingBar|src/components/AsciiLoadingBar.tsx]] — import-or-re-export; imports `AsciiLoadingBar`
- [[Reference/Desktop/TypeScript/components/IngestActivity|src/components/IngestActivity.tsx]] — import-or-re-export; imports `IngestActivityStack`
- [[Reference/Desktop/TypeScript/components/OutlineAndPlan|src/components/OutlineAndPlan.tsx]] — import-or-re-export; imports `OutlinePlanFlow`
- [[Reference/Desktop/TypeScript/components/PageRangeSelector|src/components/PageRangeSelector.tsx]] — import-or-re-export; imports `PageRangeSelector`, `pageSelectionError`
- [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]] — import-or-re-export; imports `SourceLibrarySidebar`
- [[Reference/Desktop/TypeScript/components/StudyMapBriefWizard|src/components/StudyMapBriefWizard.tsx]] — import-or-re-export; imports `STARTING_LEVELS`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Pill`, `PillColor`, `SectionHeader`, `TermSelect`
- [[Reference/Desktop/TypeScript/components/useSourceFileDrop|src/components/useSourceFileDrop.ts]] — import-or-re-export; imports `useSourceFileDrop`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/plugin-dialog`, `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_ingest_m3.py](../../../../../../tests/test_sidecar_ingest_m3.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_source_ingestion.py](../../../../../../tests/test_source_ingestion.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_init.py](../../../../../../tests/test_init.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/IngestScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/IngestScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
