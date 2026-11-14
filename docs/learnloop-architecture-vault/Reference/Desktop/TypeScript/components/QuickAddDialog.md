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
| Source lines | 667 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]]

## Public API

- `export function QuickAddDialog(` — function, line 24

## Internal implementation anchors

- `const ROLES = ["primary_textbook", "lecture", "paper", "reference", "alternate_explanation"]` — const, line 19
- `const RECOMMENDED_INVENTORY_OUTPUT_TOKENS = 12_000` — const, line 20
- `const NARROW_ADJUNCT_SCOPE = "Treat this source as a narrow enrichment adjunct. Make only additive changes: attach it to existing curriculum when it fits` — const, line 21
- `const subjectChoices = [...subjects, ...createdSubjects.filter((c)` — const, line 54
- `const mountedRef = useRef(true)` — const, line 73
- `const fileDragging = useSourceFileDrop(` — const, line 74
- `async function browseForSource()` — function, line 93
- `const picked = await pickSourceFile()` — const, line 95
- `const handler = (e: KeyboardEvent)` — const, line 106
- `const effectiveBrief = (): StudyMapBriefDto` — const, line 117
- `const enrichmentActive = brief?.authoringPreset === "narrow_adjunct"` — const, line 121
- `const applyEnrichmentPreset = ()` — const, line 123
- `const clearEnrichmentPreset = ()` — const, line 136
- `const next =` — const, line 139
- `const runPlan = async (rangeIsCurrent = false)` — const, line 149
- `const res = await api.planQuickAdd(` — const, line 159
- `const command = getCommandError(err)` — const, line 165
- `const importThenPlan = async ()` — const, line 176
- `const batch = await api.startImportBatch(` — const, line 181
- `const current = await api.getIngestBatch(batch.id)` — const, line 187
- `const activeJob = current.jobs.find((job)` — const, line 189
- `const progressStatus = current.status === "running" ? "running" : "queued"` — const, line 191
- `const failed = current.jobs.find((job)` — const, line 199
- `const confirmBuild = async ()` — const, line 224
- `const res = await api.confirmQuickAdd(` — const, line 229
- `const allConsented = consentTicked.every(Boolean)` — const, line 248
- `const budgetValid = unlimitedTokenBudget || (inventoryOutputTokens >= 1_000 && inventoryOutputTokens <= 100_000)` — const, line 249
- `function Label(` — function, line 599
- `const backdropStyle: CSSProperties =` — const, line 607
- `const modalStyle: CSSProperties =` — const, line 619
- `const headerStyle: CSSProperties =` — const, line 631
- `const footerStyle: CSSProperties =` — const, line 640
- `const primaryBtn: CSSProperties =` — const, line 649
- `const ghostBtn: CSSProperties =` — const, line 659

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `QuickAddDialog`; references `QuickAddDialog`
- [[Reference/Desktop/TypeScript/components/InboxStrip|src/components/InboxStrip.tsx]] — import-or-re-export: `QuickAddDialog`; references `QuickAddDialog`
- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export: `QuickAddDialog`; references `QuickAddDialog`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `QuickAddPlanDto`, `StudyMapBriefDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/AsciiLoadingBar|src/components/AsciiLoadingBar.tsx]] — import-or-re-export; imports `AsciiLoadingBar`
- [[Reference/Desktop/TypeScript/components/NewSubjectControl|src/components/NewSubjectControl.tsx]] — import-or-re-export; imports `NewSubjectControl`
- [[Reference/Desktop/TypeScript/components/PageRangeSelector|src/components/PageRangeSelector.tsx]] — import-or-re-export; imports `PageRangeSelector`, `pageSelectionError`
- [[Reference/Desktop/TypeScript/components/StudyMapBriefWizard|src/components/StudyMapBriefWizard.tsx]] — import-or-re-export; imports `StudyMapBriefWizard`
- [[Reference/Desktop/TypeScript/components/quickAddConsent|src/components/quickAddConsent.ts]] — import-or-re-export; imports `initialConsentTicks`
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

- [apps/learnloop-tauri/src/components/QuickAddDialog.test.tsx](../../../../../../apps/learnloop-tauri/src/components/QuickAddDialog.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/components/QuickAddDialog.tsx](../../../../../../apps/learnloop-tauri/src/components/QuickAddDialog.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
