---
title: "Desktop module · src/components/ExemplarConfirmDialog.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.ExemplarConfirmDialog"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/ExemplarConfirmDialog.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/ExemplarConfirmDialog.tsx"
source_commit: "1c72cbabade1a4be2d2f4d18b22d1cf0ac171657"
source_commit_timestamp: "2026-07-22T21:17:05-04:00"
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

# `src/components/ExemplarConfirmDialog.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `ExemplarConfirmDialog` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/ExemplarConfirmDialog.tsx](../../../../../../apps/learnloop-tauri/src/components/ExemplarConfirmDialog.tsx) |
| Source lines | 167 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `1c72cbabade1a4be2d2f4d18b22d1cf0ac171657` |
| Commit timestamp | `2026-07-22T21:17:05-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/ExemplarConfirmDialog|src/components/ExemplarConfirmDialog.tsx]]

## Public API

- `export type ConfirmInput = Parameters<typeof api.goldenPathConfirm>[0]` — type, line 21
- `export function ExemplarConfirmDialog(` — function, line 23

## Internal implementation anchors

- `const DEPTH_PRESETS = ["master_tasks_like_these", "one_solid_pass", "deep_transfer"]` — const, line 19
- `const edge = goldenPathFixtures.depthInvitation.invitation?.edge as DepthEdgeDto | undefined` — const, line 53
- `const canConfirm = Boolean(confirmInput) && consent && !busy && (blueprint?.status === "active" || blueprint?.status === "reviewed")` — const, line 56
- `const confirm = async ()` — const, line 60
- `const receipt = await api.goldenPathConfirm(` — const, line 64
- `const exemplars = blueprint?.exemplars ?? []` — const, line 73
- `const selected = exemplars.filter((e)` — const, line 74
- `const heldOut = exemplars.filter((e)` — const, line 75

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `ExemplarConfirmDialog`; references `ExemplarConfirmDialog`
- [[Reference/Desktop/TypeScript/components/goldenpath/GoldenPathSetup|src/components/goldenpath/GoldenPathSetup.tsx]] — import-or-re-export: `ConfirmInput`, `ExemplarConfirmDialog`; references `ConfirmInput`, `ExemplarConfirmDialog`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `BlueprintVersionDto`, `CommandError`, `DepthEdgeDto`
- [[Reference/Desktop/TypeScript/components/goldenpath/shared|src/components/goldenpath/shared.tsx]] — import-or-re-export; imports `DepthEnvelopeCard`, `PrimaryButton`, `SecondaryButton`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Meta`, `Pill`, `SectionHeader`, `TermCheckbox`
- [[Reference/Desktop/TypeScript/fixtures/goldenpath/index|src/fixtures/goldenpath/index.ts]] — import-or-re-export; imports `goldenPathFixtures`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/ExemplarConfirmDialog.tsx](../../../../../../apps/learnloop-tauri/src/components/ExemplarConfirmDialog.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
