---
title: "Desktop module · src/components/goldenpath/GoldenPathSetup.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.goldenpath.GoldenPathSetup"
language: "TypeScript"
area: "TypeScript/components/goldenpath"
source_path: "apps/learnloop-tauri/src/components/goldenpath/GoldenPathSetup.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/goldenpath/GoldenPathSetup.tsx"
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

# `src/components/goldenpath/GoldenPathSetup.tsx`

Area: [[Reference/Desktop/TypeScript/components/goldenpath/_area|TypeScript/components/goldenpath]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `GoldenPathSetup` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/goldenpath/GoldenPathSetup.tsx](../../../../../../../apps/learnloop-tauri/src/components/goldenpath/GoldenPathSetup.tsx) |
| Source lines | 380 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/goldenpath/_area|TypeScript/components/goldenpath]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/goldenpath/GoldenPathSetup|src/components/goldenpath/GoldenPathSetup.tsx]]

## Public API

- `export function GoldenPathSetup(` — function, line 29

## Internal implementation anchors

- `const REVIEW_CHECKS = [` — const, line 21
- `const EMPTY_ANCHORS: Set<string> = new Set()` — const, line 27
- `let cancelled = false` — let, line 56
- `const activeGoals = useMemo(()` — const, line 82
- `const entry = useMemo(()` — const, line 83
- `const anchors = (loId ? picks.get(loId)?.anchors : undefined) ?? EMPTY_ANCHORS` — const, line 84
- `const heldOut = (loId ? picks.get(loId)?.heldOut : undefined) ?? null` — const, line 85
- `const resetDraft = useCallback(()` — const, line 88
- `const updatePick = ( mutate: (prev:` — const, line 94
- `const next = new Map(prev)` — const, line 100
- `const toggleAnchor = (id: string)` — const, line 106
- `const anchors = new Set(pick.anchors)` — const, line 108
- `const chooseHeldOut = (id: string)` — const, line 114
- `const anchors = new Set(pick.anchors)` — const, line 116
- `const compose = async ()` — const, line 121
- `const result = await api.blueprintComposeDraft(` — const, line 125
- `const review = async ()` — const, line 138
- `const confirmInput: Omit<ConfirmInput, "depthPreset"> | null = useMemo(()` — const, line 154
- `const done = run.currentState === "complete"` — const, line 204
- `const isAnchor = anchors.has(item.practiceItemId)` — const, line 285
- `const isHeldOut = heldOut === item.practiceItemId` — const, line 286
- `const next = new Set(prev)` — const, line 331

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `GoldenPathSetup`; references `GoldenPathSetup`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ComposeDraftResult`, `ExemplarPoolEntryDto`, `GoalDto`, `RunListEntryDto`
- [[Reference/Desktop/TypeScript/components/ExemplarConfirmDialog|src/components/ExemplarConfirmDialog.tsx]] — import-or-re-export; imports `ConfirmInput`, `ExemplarConfirmDialog`
- [[Reference/Desktop/TypeScript/components/goldenpath/shared|src/components/goldenpath/shared.tsx]] — import-or-re-export; imports `PrimaryButton`, `SecondaryButton`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`, `TermCheckbox`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — places the staged journey in the user-facing session path.
- [[Concepts/Learning System#The feedback loop|learning feedback loop]] — owns the learning intent behind the fixture or surface.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_golden_path.py](../../../../../../../tests/test_sidecar_golden_path.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_golden_path_assessment.py](../../../../../../../tests/test_sidecar_golden_path_assessment.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_golden_path_fixture.py](../../../../../../../tests/test_golden_path_fixture.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/goldenpath/GoldenPathSetup.tsx](../../../../../../../apps/learnloop-tauri/src/components/goldenpath/GoldenPathSetup.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
