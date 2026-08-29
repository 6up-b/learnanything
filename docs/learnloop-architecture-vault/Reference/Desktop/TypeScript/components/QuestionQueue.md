---
title: "Desktop module · src/components/QuestionQueue.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.QuestionQueue"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/QuestionQueue.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/QuestionQueue.tsx"
source_commit: "971d7c274e09873d726d43578cd080e4d8865571"
source_commit_timestamp: "2026-07-27T06:01:19-04:00"
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

# `src/components/QuestionQueue.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `QuestionQueue` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/QuestionQueue.tsx](../../../../../../apps/learnloop-tauri/src/components/QuestionQueue.tsx) |
| Source lines | 354 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `971d7c274e09873d726d43578cd080e4d8865571` |
| Commit timestamp | `2026-07-27T06:01:19-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] → [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]]

## Public API

- `export function QuestionQueuePanel(` — function, line 29

## Internal implementation anchors

- `const CONTEXT_PILL: Record<string, PillColor> =` — const, line 15
- `interface SourceLaunch` — interface, line 22
- `const refresh = useCallback(()` — const, line 44
- `const resolve = useCallback( async (id: string, resolution: "resolved" | "dismissed")` — const, line 56
- `const promote = useCallback( async (row: QuestionQueueRowDto)` — const, line 72
- `const targetId = selectedTargetById[row.id] ?? (row.promotionTargetIds.length === 1 ? row.promotionTargetIds[0] : undefined)` — const, line 74
- `const result = await api.promoteTutorQuestion( row.id, "practice", targetId ?` — const, line 87
- `const expanded = expandedId === row.id` — const, line 125
- `const busy = busyId === row.id` — const, line 126
- `const dialogueTarget = targetForDialogue(row)` — const, line 127
- `const primedItemId = readyPracticeItemId(row)` — const, line 128
- `const primedItemId = sourceLaunch.primedItemId` — const, line 290
- `function targetForDialogue(row: QuestionQueueRowDto): AskTarget | null` — function, line 300
- `function readyPracticeItemId(row: QuestionQueueRowDto): string | null` — function, line 330
- `function QueueAction(` — function, line 338

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `QuestionQueuePanel`; references `QuestionQueuePanel`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `QuestionQueueRowDto`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export; imports `AskTarget`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export; imports `OpenInSource`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`, `SectionHeader`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`, `subscribeQueueChanged`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_diagnostic.py](../../../../../../tests/test_sidecar_diagnostic.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/QuestionQueue.tsx](../../../../../../apps/learnloop-tauri/src/components/QuestionQueue.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
