---
title: "Desktop module · src/components/SourceLibrarySidebar.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.SourceLibrarySidebar"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/SourceLibrarySidebar.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/SourceLibrarySidebar.tsx"
source_commit: "0e91c7ba1b7ff32d5d093dd62826890b70445d3f"
source_commit_timestamp: "2026-08-03T22:04:38-04:00"
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

# `src/components/SourceLibrarySidebar.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `SourceLibrarySidebar` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/SourceLibrarySidebar.tsx](../../../../../../apps/learnloop-tauri/src/components/SourceLibrarySidebar.tsx) |
| Source lines | 770 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `0e91c7ba1b7ff32d5d093dd62826890b70445d3f` |
| Commit timestamp | `2026-08-03T22:04:38-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] → [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]]

## Public API

- `export function SourceLibrarySidebar(` — function, line 45

## Internal implementation anchors

- `const READINESS_META: Record<SourceReadiness,` — const, line 25
- `const DEFAULT_INVENTORY_OUTPUT_TOKENS = 12_000` — const, line 30
- `function readableTitle(title: string): string` — function, line 34
- `const vid = youtubeVideoId(title)` — const, line 37
- `const trimmed = title.replace(/[/\\]+$/, "")` — const, line 40
- `const tail = trimmed.split(/[?#]/)[0].split(/[/\\]/).filter(Boolean).pop()` — const, line 41
- `const firstLoad = useRef(true)` — const, line 68
- `const refresh = useCallback(async ()` — const, line 71
- `const snapshot = await api.getSourceLibrary()` — const, line 73
- `const anyProcessing = sources.some((card)` — const, line 89
- `const id = window.setInterval(()` — const, line 92
- `function selectCard(card: SourceLibraryCard)` — function, line 96
- `function DeleteSourceDialog(` — function, line 215
- `let cancelled = false` — let, line 229
- `function onKeyDown(e: KeyboardEvent)` — function, line 244
- `async function confirm()` — function, line 251
- `const canDelete = plan !== null && plan.deletable && !busy` — const, line 263
- `function SourceRow(` — function, line 390
- `const readiness = READINESS_META[card.readiness]` — const, line 403
- `const isReady = card.readiness === "ready"` — const, line 404
- `function CollectionsSection(` — function, line 511
- `const titleFor = useCallback( (sourceId: string): string` — const, line 532
- `const card = sources.find((c)` — const, line 534
- `const refresh = useCallback(async ()` — const, line 540
- `const snap = await api.listSourceSets()` — const, line 542
- `async function toggle(id: string)` — function, line 553
- `const next =` — const, line 556
- `const next =` — const, line 569
- `async function synthesize(id: string)` — function, line 576
- `const inventoryOutputTokens = inventoryBudgets[id] ?? DEFAULT_INVENTORY_OUTPUT_TOKENS` — const, line 577
- `const unlimitedTokenBudget = Boolean(unlimitedBudgets[id])` — const, line 578
- `const batch = await api.buildStudyMap(` — const, line 587
- `const detail = expanded[set.id]` — const, line 632
- `const open = detail !== undefined` — const, line 633
- `const isBusy = busy === set.id` — const, line 634

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `SourceLibrarySidebar`; references `SourceLibrarySidebar`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `SourceDeletionPlanDto`, `SourceLibraryCard`, `SourceReadiness`, `SourceSetDto`, `SourceSetSummaryDto`, `StudyMapBriefDto`
- [[Reference/Desktop/TypeScript/components/AddToCollection|src/components/AddToCollection.tsx]] — import-or-re-export; imports `AddToCollectionPanel`
- [[Reference/Desktop/TypeScript/components/StudyMapBriefWizard|src/components/StudyMapBriefWizard.tsx]] — import-or-re-export; imports `StudyMapBriefWizard`
- [[Reference/Desktop/TypeScript/components/sourceTail|src/components/sourceTail.ts]] — import-or-re-export; imports `youtubeVideoId`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `TermCheckbox`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

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

1. Modify [apps/learnloop-tauri/src/components/SourceLibrarySidebar.tsx](../../../../../../apps/learnloop-tauri/src/components/SourceLibrarySidebar.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
