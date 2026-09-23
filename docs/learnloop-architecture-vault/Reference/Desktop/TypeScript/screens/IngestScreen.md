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
| Source lines | 1588 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]]

## Public API

- `export function IngestScreen(` — function, line 423

## Internal implementation anchors

- `type Kind = "web" | "arxiv" | "pdf" | "youtube" | "local" | "audio"` — type, line 25
- `function detectKind(source: string): Kind | null` — function, line 28
- `const s = (source || "").trim()` — const, line 29
- `type KindMeta =` — type, line 42
- `const KIND_META: Record<Kind, KindMeta> =` — const, line 44
- `type Mode = IngestMode` — type, line 53
- `function kebabCase(value: string): string` — function, line 55
- `function Card(` — function, line 63
- `function KindChips(` — function, line 81
- `const order: Kind[] = ["web", "arxiv", "pdf", "youtube", "local", "audio"]` — const, line 82
- `const sel = k === active` — const, line 86
- `const meta = KIND_META[k]` — const, line 87
- `function LearnerLevelChip()` — function, line 113
- `const profileQuery = useCachedQuery(["get_learner_profile"], ()` — const, line 119
- `const profileError = saveError ?? (profileQuery.error ? errorMessage(profileQuery.error, "Could not load your learner level.") : null)` — const, line 125
- `const pick = async (next: StartingLevel)` — const, line 128
- `const profile = await api.setLearnerProfile(` — const, line 133
- `const label = STARTING_LEVELS.find((s)` — const, line 144
- `function SubjectPicker(` — function, line 217
- `const inputRef = useRef<HTMLInputElement>(null)` — const, line 232
- `async function submit()` — function, line 238
- `const trimmed = title.trim()` — const, line 239
- `const created = await onCreate(trimmed)` — const, line 241
- `const sel = s === value` — const, line 250
- `const SPINNER_FRAMES = ["◐", "◓", "◑", "◒"]` — const, line 340
- `const INGEST_PHASES: Array<` — const, line 342
- `function RunningCard(` — function, line 350
- `const frame = SPINNER_FRAMES[Math.floor(elapsed * 2) % SPINNER_FRAMES.length]` — const, line 351
- `const minutes = Math.floor(elapsed / 60)` — const, line 352
- `const seconds = Math.floor(elapsed % 60)` — const, line 353
- `const clock = minutes > 0 ? `$` — const, line 354
- `const activeIndex = INGEST_PHASES.findIndex((item)` — const, line 355
- `const cancelling = job.phase === "cancelling"` — const, line 356
- `const complete = activeIndex > index` — const, line 376
- `const active = activeIndex === index` — const, line 377
- `const overlayActive = outlineTarget !== null` — const, line 446
- `const card = lib.sources.find((c)` — const, line 474
- `function IngestHome(` — function, line 530
- `const vaultQuery = useCachedQuery(["load_vault"], ()` — const, line 562
- `const subjects: string[] = useMemo(()` — const, line 563
- `const effectivePdfEngine: PdfEngine = pdfEngine === "auto" ? vaultPdfEngine : pdfEngine` — const, line 587
- `const nativePdf = effectivePdfEngine === "native"` — const, line 588
- `let cancelled = false` — let, line 590
- `const inputRef = useRef<HTMLInputElement>(null)` — const, line 601
- `const activityRef = useRef<HTMLDivElement>(null)` — const, line 602
- `const runningRef = useRef(false)` — const, line 603
- `const kind = authoritativeKind ?? detectKind(source)` — const, line 605
- `const running = job?.status === "queued" || job?.status === "running"` — const, line 606
- `const result = job?.status === "completed" ? job.result : null` — const, line 607
- `const error = localError ?? (job?.status === "failed" || job?.status === "cancelled" ? job.error?.message ?? job.message : null)` — const, line 608
- `const stagingVisible = mode === "canonical"` — const, line 612
- `const hasStaged = staged.length > 0` — const, line 613
- `const canRun = (source.trim().length > 0 || (stagingVisible && hasStaged)) && !running && !importing && (mode === "canonical" || subject !== null) && (mode !== "canonical" || pageSelectionError(pageSelection) === null) && Object.values(stagedPageRanges).every…` — const, line 614
- `const importCount = staged.length + (source.trim() ? 1 : 0)` — const, line 621
- `const subjectTooltip = mode === "canonical" ? "imports land in the vault-global source library — no subject needed. A subject chosen here just pre-tags the import batch` — const, line 622
- `const refreshVault = vaultQuery.refetch` — const, line 627
- `const refreshSubjects = useCallback(async ()` — const, line 628
- `let cancelled = false` — let, line 644
- `const active = snapshot.jobs.find((candidate)` — const, line 647
- `let cancelled = false` — let, line 658
- `let timer: number | undefined` — let, line 659
- `const poll = async ()` — const, line 660
- `const next = await api.getIngestJob(jobId)` — const, line 662
- `const commandError = e as CommandError` — const, line 674
- `const candidate = source.trim()` — const, line 693
- `let cancelled = false` — let, line 699
- `const timer = window.setTimeout(()` — const, line 701
- `const mapped: Record<string, Kind> =` — const, line 705
- `let cancelled = false` — let, line 735
- `const timer = window.setTimeout(()` — const, line 736
- `const next: Record<string, AcquisitionPreviewItem> =` — const, line 740
- `const parsed = Date.parse(job.startedAt ?? job.createdAt)` — const, line 757
- `const started = Number.isNaN(parsed) ? Date.now() : parsed` — const, line 758
- `const id = window.setInterval(()` — const, line 760
- `async function createSubject(title: string): Promise<boolean>` — function, line 764
- `const id = kebabCase(title)` — const, line 765
- `const res = await api.runCliCommand(["add-subject", id, title])` — const, line 770
- `function clearFinishedJob()` — function, line 787
- `function stageCurrent()` — function, line 793
- `const src = source.trim()` — const, line 794
- `const next =` — const, line 798
- `function stageDropped(paths: string[])` — function, line 808
- `const unique = paths.filter((path, index)` — const, line 811
- `const next =` — const, line 818
- `const fileDragging = useSourceFileDrop(` — const, line 824
- `function removeStaged(src: string)` — function, line 830
- `const next =` — const, line 833
- `const next =` — const, line 838
- `async function startCanonicalImport(entries: Array<` — function, line 844
- `const batch = await api.startImportBatch(` — const, line 847
- `async function startExamSeeding(src: string)` — function, line 876
- `const started = await api.startIngest(` — const, line 881
- `const commandError = e as CommandError` — const, line 885
- `const activeJobId = (commandError.details as` — const, line 886
- `async function startRun()` — function, line 897
- `const trimmed = source.trim()` — const, line 899
- `const entries = [ ...staged.map((stagedSource)` — const, line 902
- `async function cancelIngest()` — function, line 927
- `async function chooseLocalSource()` — function, line 936
- `const selected = await openDialog(` — const, line 938
- `function onKey(event: KeyboardEvent)` — function, line 954
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 958
- `const isInput = tag === "input" || tag === "textarea"` — const, line 959
- `const modeChip = (m: Mode, icon: string, label: string)` — const, line 987
- `const sel = mode === m` — const, line 988
- `const next = value as PdfEngine` — const, line 1192
- `const rowKind = detectKind(src)` — const, line 1303
- `const meta = rowKind ? KIND_META[rowKind] : null` — const, line 1304
- `const preview = previews[src]` — const, line 1305
- `const stagedRange = stagedPageRanges[src] ?? ""` — const, line 1306

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: dynamic import; no named call claim

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AcquisitionPreviewItem`, `CommandError`, `IngestBatchDto`, `IngestJobDto`, `IngestJobPhase`, `IngestMode`, `PdfEngine`, `SourceLibraryCard`, `StartingLevel`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
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
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/IngestScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/IngestScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
