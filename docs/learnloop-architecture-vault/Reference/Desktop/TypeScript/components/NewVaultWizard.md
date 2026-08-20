---
title: "Desktop module · src/components/NewVaultWizard.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.NewVaultWizard"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/NewVaultWizard.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/NewVaultWizard.tsx"
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

# `src/components/NewVaultWizard.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `NewVaultWizard` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/NewVaultWizard.tsx](../../../../../../apps/learnloop-tauri/src/components/NewVaultWizard.tsx) |
| Source lines | 941 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]]

## Public API

- `export function NewVaultWizard(` — function, line 33

## Internal implementation anchors

- `const STEP_LABELS = ["vault"]` — const, line 27
- `function kebabCase(value: string): string` — function, line 29
- `const fileDragging = useSourceFileDrop(` — const, line 82
- `async function refreshSubjects()` — function, line 95
- `const snap = await api.loadVault()` — const, line 97
- `const list = snap.vault?.subjects ?? []` — const, line 98
- `async function createVault()` — function, line 106
- `const trimmed = path.trim()` — const, line 108
- `const result = await api.createVault(` — const, line 116
- `async function browseForDirectory()` — function, line 136
- `const selected = await openDialog(` — const, line 138
- `async function browseForSource()` — function, line 149
- `const picked = await pickSourceFile()` — const, line 151
- `async function addSubject()` — function, line 160
- `const title = newSubjectTitle.trim()` — const, line 161
- `const id = kebabCase(title)` — const, line 163
- `const res = await api.runCliCommand(["add-subject", id, title])` — const, line 167
- `const candidate = source.trim()` — const, line 184
- `let cancelled = false` — let, line 190
- `const handle = window.setTimeout(()` — const, line 192
- `let cancelled = false` — let, line 214
- `const tick = async ()` — const, line 215
- `const snap = await api.getProposals()` — const, line 217
- `const batch = await api.getIngestBatch(bootstrapBatchId)` — const, line 224
- `const id = window.setInterval(()` — const, line 232
- `const stepValid = useMemo(()` — const, line 239
- `const advance = ()` — const, line 244
- `function finish()` — function, line 258
- `const onKey = (event: KeyboardEvent)` — const, line 269
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 271
- `const isInput = tag === "input" || tag === "textarea"` — const, line 272
- `const primaryLabel = (()` — const, line 286
- `function StepVault(` — function, line 435
- `function StepFirstSource(` — function, line 532
- `const hasSubject = bootstrapSubject !== null && subjects.includes(bootstrapSubject)` — const, line 573
- `const canBootstrap = source.trim().length > 0 && hasSubject && pageSelectionError(pageSelection) === null` — const, line 574
- `const sel = s === bootstrapSubject` — const, line 636
- `function StepProposals(` — function, line 709
- `function StepGoal(` — function, line 761
- `function StepLoop()` — function, line 787
- `function TabRow(` — function, line 830
- `function CmdRow(` — function, line 839
- `function Prose(` — function, line 848
- `function Label(` — function, line 852
- `const okBox: CSSProperties =` — const, line 860
- `const backdropStyle: CSSProperties =` — const, line 870
- `const modalStyle: CSSProperties =` — const, line 882
- `const headerStyle: CSSProperties =` — const, line 894
- `const footerStyle: CSSProperties =` — const, line 903
- `const inputStyle: CSSProperties =` — const, line 912
- `const primaryBtn: CSSProperties =` — const, line 923
- `const ghostBtn: CSSProperties =` — const, line 933

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `NewVaultWizard`; references `NewVaultWizard`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `StartingLevel`
- [[Reference/Desktop/TypeScript/components/GoalWizard|src/components/GoalWizard.tsx]] — import-or-re-export; imports `GoalWizard`
- [[Reference/Desktop/TypeScript/components/PageRangeSelector|src/components/PageRangeSelector.tsx]] — import-or-re-export; imports `PageRangeSelector`, `pageSelectionError`
- [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] — import-or-re-export; imports `QuickAddDialog`
- [[Reference/Desktop/TypeScript/components/StudyMapBriefWizard|src/components/StudyMapBriefWizard.tsx]] — import-or-re-export; imports `STARTING_LEVELS`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `TopTab`
- [[Reference/Desktop/TypeScript/components/useSourceFileDrop|src/components/useSourceFileDrop.ts]] — import-or-re-export; imports `pickSourceFile`, `useSourceFileDrop`
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

1. Modify [apps/learnloop-tauri/src/components/NewVaultWizard.tsx](../../../../../../apps/learnloop-tauri/src/components/NewVaultWizard.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
