---
title: "Desktop module · src/components/QuickAddDialog.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.QuickAddDialog"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/QuickAddDialog.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/QuickAddDialog.tsx"
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

# `src/components/QuickAddDialog.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `QuickAddDialog` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/QuickAddDialog.tsx](../../../../../../apps/learnloop-tauri/src/components/QuickAddDialog.tsx) |
| Source lines | 636 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]]

## Public API

- `export function QuickAddDialog(` — function, line 21

## Internal implementation anchors

- `const ROLES = ["primary_textbook", "lecture", "paper", "reference", "alternate_explanation"]` — const, line 16
- `const RECOMMENDED_INVENTORY_OUTPUT_TOKENS = 12_000` — const, line 17
- `const NARROW_ADJUNCT_SCOPE = "Treat this source as a narrow enrichment adjunct. Make only additive changes: attach it to existing curriculum when it fits` — const, line 18
- `const mountedRef = useRef(true)` — const, line 63
- `const fileDragging = useSourceFileDrop(` — const, line 64
- `async function browseForSource()` — function, line 83
- `const picked = await pickSourceFile()` — const, line 85
- `const handler = (e: KeyboardEvent)` — const, line 96
- `const effectiveBrief = (): StudyMapBriefDto` — const, line 106
- `const enrichmentActive = brief?.authoringPreset === "narrow_adjunct"` — const, line 110
- `const applyEnrichmentPreset = ()` — const, line 112
- `const clearEnrichmentPreset = ()` — const, line 124
- `const next =` — const, line 127
- `const runPlan = async (rangeIsCurrent = false)` — const, line 137
- `const res = await api.planQuickAdd(` — const, line 147
- `const command = getCommandError(err)` — const, line 153
- `const importThenPlan = async ()` — const, line 164
- `const batch = await api.startImportBatch(` — const, line 169
- `const current = await api.getIngestBatch(batch.id)` — const, line 175
- `const activeJob = current.jobs.find((job)` — const, line 177
- `const progressStatus = current.status === "running" ? "running" : "queued"` — const, line 179
- `const failed = current.jobs.find((job)` — const, line 187
- `const confirmBuild = async ()` — const, line 212
- `const res = await api.confirmQuickAdd(` — const, line 217
- `const allConsented = consentTicked.every(Boolean)` — const, line 234
- `const budgetValid = unlimitedTokenBudget || (inventoryOutputTokens >= 1_000 && inventoryOutputTokens <= 100_000)` — const, line 235
- `function Label(` — function, line 568
- `const backdropStyle: CSSProperties =` — const, line 576
- `const modalStyle: CSSProperties =` — const, line 588
- `const headerStyle: CSSProperties =` — const, line 600
- `const footerStyle: CSSProperties =` — const, line 609
- `const primaryBtn: CSSProperties =` — const, line 618
- `const ghostBtn: CSSProperties =` — const, line 628

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `QuickAddDialog`; references `QuickAddDialog`
- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export: `QuickAddDialog`; references `QuickAddDialog`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `QuickAddPlanDto`, `StudyMapBriefDto`
- [[Reference/Desktop/TypeScript/components/AsciiLoadingBar|src/components/AsciiLoadingBar.tsx]] — import-or-re-export; imports `AsciiLoadingBar`
- [[Reference/Desktop/TypeScript/components/PageRangeSelector|src/components/PageRangeSelector.tsx]] — import-or-re-export; imports `PageRangeSelector`, `pageSelectionError`
- [[Reference/Desktop/TypeScript/components/StudyMapBriefWizard|src/components/StudyMapBriefWizard.tsx]] — import-or-re-export; imports `StudyMapBriefWizard`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `TermCheckbox`, `TermSelect`
- [[Reference/Desktop/TypeScript/components/useSourceFileDrop|src/components/useSourceFileDrop.ts]] — import-or-re-export; imports `pickSourceFile`, `useSourceFileDrop`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`

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

1. Modify [apps/learnloop-tauri/src/components/QuickAddDialog.tsx](../../../../../../apps/learnloop-tauri/src/components/QuickAddDialog.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
