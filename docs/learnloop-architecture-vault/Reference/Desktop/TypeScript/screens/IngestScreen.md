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
| Source lines | 1608 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]]

## Public API

- `export function IngestScreen(` — function, line 442

## Internal implementation anchors

- `type Kind = SourceCategory` — type, line 28
- `function recognitionCostLabel(estimate: NonNullable<AcquisitionPreviewItem["extractionEstimate"]>): string` — function, line 31
- `const usd = estimate.estimatedUsd` — const, line 34
- `function detectKind(source: string): Kind | null` — function, line 42
- `const s = (source || "").trim()` — const, line 43
- `const url = /^https?:\/\//i.test(s)` — const, line 48
- `const path = (url ? s.replace(/[?#].*$/, "") : s).toLowerCase()` — const, line 49
- `const kind = SOURCE_KINDS.find((row)` — const, line 50
- `const KIND_STYLE: Record<Kind,` — const, line 57
- `function kindLabel(kind: Kind): string` — function, line 67
- `type Mode = IngestMode` — type, line 71
- `function kebabCase(value: string): string` — function, line 73
- `function Card(` — function, line 81
- `function KindChips(` — function, line 99
- `const sel = k === active` — const, line 103
- `const meta =` — const, line 104
- `function LearnerLevelChip()` — function, line 132
- `const profileQuery = useCachedQuery(["get_learner_profile"], ()` — const, line 138
- `const profileError = saveError ?? (profileQuery.error ? errorMessage(profileQuery.error, "Could not load your learner level.") : null)` — const, line 144
- `const pick = async (next: StartingLevel)` — const, line 147
- `const profile = await api.setLearnerProfile(` — const, line 152
- `const label = STARTING_LEVELS.find((s)` — const, line 163
- `function SubjectPicker(` — function, line 236
- `const inputRef = useRef<HTMLInputElement>(null)` — const, line 251
- `async function submit()` — function, line 257
- `const trimmed = title.trim()` — const, line 258
- `const created = await onCreate(trimmed)` — const, line 260
- `const sel = s === value` — const, line 269
- `const SPINNER_FRAMES = ["◐", "◓", "◑", "◒"]` — const, line 359
- `const INGEST_PHASES: Array<` — const, line 361
- `function RunningCard(` — function, line 369
- `const frame = SPINNER_FRAMES[Math.floor(elapsed * 2) % SPINNER_FRAMES.length]` — const, line 370
- `const minutes = Math.floor(elapsed / 60)` — const, line 371
- `const seconds = Math.floor(elapsed % 60)` — const, line 372
- `const clock = minutes > 0 ? `$` — const, line 373
- `const activeIndex = INGEST_PHASES.findIndex((item)` — const, line 374
- `const cancelling = job.phase === "cancelling"` — const, line 375
- `const complete = activeIndex > index` — const, line 395
- `const active = activeIndex === index` — const, line 396
- `const overlayActive = outlineTarget !== null` — const, line 465
- `const card = lib.sources.find((c)` — const, line 493
- `function IngestHome(` — function, line 549
- `const vaultQuery = useCachedQuery(["load_vault"], ()` — const, line 581
- `const subjects: string[] = useMemo(()` — const, line 582
- `const nativePdf = enginesRefusingRanges.includes(pdfEngine)` — const, line 607
- `let cancelled = false` — let, line 609
- `const inputRef = useRef<HTMLInputElement>(null)` — const, line 622
- `const activityRef = useRef<HTMLDivElement>(null)` — const, line 623
- `const runningRef = useRef(false)` — const, line 624
- `const kind = authoritativeKind ?? detectKind(source)` — const, line 626
- `const running = job?.status === "queued" || job?.status === "running"` — const, line 627
- `const result = job?.status === "completed" ? job.result : null` — const, line 628
- `const error = localError ?? (job?.status === "failed" || job?.status === "cancelled" ? job.error?.message ?? job.message : null)` — const, line 629
- `const stagingVisible = mode === "canonical"` — const, line 633
- `const hasStaged = staged.length > 0` — const, line 634
- `const canRun = (source.trim().length > 0 || (stagingVisible && hasStaged)) && !running && !importing && (mode === "canonical" || subject !== null) && (mode !== "canonical" || pageSelectionError(pageSelection) === null) && Object.values(stagedPageRanges).every…` — const, line 635
- `const importCount = staged.length + (source.trim() ? 1 : 0)` — const, line 642
- `const subjectTooltip = mode === "canonical" ? "imports land in the vault-global source library — no subject needed. A subject chosen here just pre-tags the import batch` — const, line 643
- `const refreshVault = vaultQuery.refetch` — const, line 648
- `const refreshSubjects = useCallback(async ()` — const, line 649
- `let cancelled = false` — let, line 665
- `const active = snapshot.jobs.find((candidate)` — const, line 668
- `let cancelled = false` — let, line 679
- `let timer: number | undefined` — let, line 680
- `const poll = async ()` — const, line 681
- `const next = await api.getIngestJob(jobId)` — const, line 683
- `const commandError = e as CommandError` — const, line 695
- `const candidate = source.trim()` — const, line 714
- `let cancelled = false` — let, line 720
- `const timer = window.setTimeout(()` — const, line 722
- `let cancelled = false` — let, line 748
- `const timer = window.setTimeout(()` — const, line 749
- `const next: Record<string, AcquisitionPreviewItem> =` — const, line 753
- `const parsed = Date.parse(job.startedAt ?? job.createdAt)` — const, line 770
- `const started = Number.isNaN(parsed) ? Date.now() : parsed` — const, line 771
- `const id = window.setInterval(()` — const, line 773
- `async function createSubject(title: string): Promise<boolean>` — function, line 777
- `const id = kebabCase(title)` — const, line 778
- `const res = await api.runCliCommand(["add-subject", id, title])` — const, line 783
- `function clearFinishedJob()` — function, line 800
- `function stageCurrent()` — function, line 806
- `const src = source.trim()` — const, line 807
- `const next =` — const, line 811
- `function stageDropped(paths: string[])` — function, line 821
- `const unique = paths.filter((path, index)` — const, line 824
- `const next =` — const, line 831
- `const fileDragging = useSourceFileDrop(` — const, line 837
- `function removeStaged(src: string)` — function, line 843
- `const next =` — const, line 846
- `const next =` — const, line 851
- `async function startCanonicalImport(entries: Array<` — function, line 857
- `const batch = await api.startImportBatch(` — const, line 860
- `async function startExamSeeding(src: string)` — function, line 889
- `const started = await api.startIngest(` — const, line 894
- `const commandError = e as CommandError` — const, line 898
- `const activeJobId = (commandError.details as` — const, line 899
- `async function startRun()` — function, line 910
- `const trimmed = source.trim()` — const, line 912
- `const entries = [ ...staged.map((stagedSource)` — const, line 915
- `async function cancelIngest()` — function, line 940
- `async function chooseLocalSource()` — function, line 949
- `const selected = await openDialog(` — const, line 951
- `function onKey(event: KeyboardEvent)` — function, line 967
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 972
- `const isInput = tag === "input" || tag === "textarea"` — const, line 973
- `const modeChip = (m: Mode, icon: string, label: string)` — const, line 1001
- `const sel = mode === m` — const, line 1002
- `const next = value as PdfEngine` — const, line 1207
- `const rowKind = sourceKindRow(previews[src]?.category)?.category ?? detectKind(src)` — const, line 1318
- `const meta = rowKind ?` — const, line 1319
- `const preview = previews[src]` — const, line 1320
- `const stagedRange = stagedPageRanges[src] ?? ""` — const, line 1321

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: dynamic import; no named call claim

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AcquisitionPreviewItem`, `CommandError`, `IngestBatchDto`, `IngestJobDto`, `IngestJobPhase`, `IngestMode`, `PdfEngine`, `SourceLibraryCard`, `StartingLevel`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/sourceKinds|src/api/sourceKinds.ts]] — import-or-re-export; imports `SOURCE_KINDS`, `SourceCategory`, `sourceKindRow`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
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

- [apps/learnloop-tauri/src/screens/IngestScreen.eligibility.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/IngestScreen.eligibility.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_ingest_m3.py](../../../../../../tests/test_sidecar_ingest_m3.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_source_ingestion.py](../../../../../../tests/test_source_ingestion.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_init.py](../../../../../../tests/test_init.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/IngestScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/IngestScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
