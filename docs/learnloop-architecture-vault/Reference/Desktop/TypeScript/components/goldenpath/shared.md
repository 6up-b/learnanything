---
title: "Desktop module · src/components/goldenpath/shared.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.goldenpath.shared"
language: "TypeScript"
area: "TypeScript/components/goldenpath"
source_path: "apps/learnloop-tauri/src/components/goldenpath/shared.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/goldenpath/shared.tsx"
source_commit: "02c3e6e10f5ca37e16cef05657ee693b33502fb7"
source_commit_timestamp: "2026-07-21T13:26:14-04:00"
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

# `src/components/goldenpath/shared.tsx`

Area: [[Reference/Desktop/TypeScript/components/goldenpath/_area|TypeScript/components/goldenpath]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `shared` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/goldenpath/shared.tsx](../../../../../../../apps/learnloop-tauri/src/components/goldenpath/shared.tsx) |
| Source lines | 399 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/goldenpath/_area|TypeScript/components/goldenpath]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `02c3e6e10f5ca37e16cef05657ee693b33502fb7` |
| Commit timestamp | `2026-07-21T13:26:14-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/ExemplarConfirmDialog|src/components/ExemplarConfirmDialog.tsx]] → [[Reference/Desktop/TypeScript/components/goldenpath/shared|src/components/goldenpath/shared.tsx]]

## Public API

- `export function CalibrationBadge(` — function, line 36
- `export function ClaimBadge(` — function, line 52
- `export function IntervalBar(` — function, line 64
- `export type CheckpointState = "done" | "current" | "pending"` — type, line 77
- `export interface Checkpoint` — interface, line 78
- `export function CheckpointLadder(` — function, line 89
- `export function DepthEnvelopeCard(` — function, line 109
- `export function DispositionPicker(` — function, line 164
- `export function AffectTap(` — function, line 216
- `export function BoundaryCellMarker(` — function, line 269
- `export function BoundaryView(` — function, line 279
- `export function PrimaryButton(` — function, line 327
- `export function SecondaryButton(` — function, line 357
- `export function ladderCheckpoints(stages: LadderStageDto[], currentStageKey: string | null): Checkpoint[]` — function, line 391

## Internal implementation anchors

- `type PillColor, } from "../term"` — type, line 15
- `const CALIBRATION_MAP: Record<GpCalibrationStatus,` — const, line 30
- `const m = CALIBRATION_MAP[status] ?? CALIBRATION_MAP.heuristic` — const, line 37
- `const CLAIM_MAP: Record<GpClaimLanguage,` — const, line 46
- `const m = CLAIM_MAP[claim] ?? CLAIM_MAP.provisional` — const, line 53
- `const CHECK_GLYPH: Record<CheckpointState,` — const, line 83
- `const g = CHECK_GLYPH[s.state]` — const, line 93
- `const minutes = edge?.burden?.minutes` — const, line 122
- `const DISPOSITIONS: Array<` — const, line 157
- `const active = value === d.id` — const, line 178
- `const AFFECT_SIGNALS: Array<` — const, line 207
- `const CELL_STATE: Record<BoundaryCellState,` — const, line 261
- `const m = CELL_STATE[state] ?? CELL_STATE.untested` — const, line 270
- `const deepened = cells.filter((c)` — const, line 280
- `const ordered = [...stages].sort((a, b)` — const, line 392
- `const currentIdx = ordered.findIndex((s)` — const, line 393

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/ExemplarConfirmDialog|src/components/ExemplarConfirmDialog.tsx]] — import-or-re-export: `DepthEnvelopeCard`, `PrimaryButton`, `SecondaryButton`; references `DepthEnvelopeCard`, `PrimaryButton`, `SecondaryButton`
- [[Reference/Desktop/TypeScript/components/WhyDiagnosisOverlay|src/components/WhyDiagnosisOverlay.tsx]] — import-or-re-export: `CalibrationBadge`; references `CalibrationBadge`
- [[Reference/Desktop/TypeScript/components/goldenpath/GoldenPathSetup|src/components/goldenpath/GoldenPathSetup.tsx]] — import-or-re-export: `PrimaryButton`, `SecondaryButton`; references `PrimaryButton`, `SecondaryButton`
- [[Reference/Desktop/TypeScript/components/goldenpath/TriageDecisionAid|src/components/goldenpath/TriageDecisionAid.tsx]] — import-or-re-export: `CalibrationBadge`, `SecondaryButton`; references `CalibrationBadge`, `SecondaryButton`
- [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]] — import-or-re-export: `AffectTap`, `BoundaryView`, `CalibrationBadge`, `Checkpoint`, `CheckpointLadder`, `ClaimBadge`, `DepthEnvelopeCard`, `IntervalBar`, `PrimaryButton`, `SecondaryButton`; references `AffectTap`, `BoundaryView`, `CalibrationBadge`, `Checkpoint`, `CheckpointLadder`, `ClaimBadge`, `DepthEnvelopeCard`, `IntervalBar`, `PrimaryButton`, `SecondaryButton`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `AffectTap`, `DispositionPicker`, `PrimaryButton`, `SecondaryButton`; references `AffectTap`, `DispositionPicker`, `PrimaryButton`, `SecondaryButton`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `BoundaryCellDto`, `BoundaryCellState`, `DepthEdgeDto`, `GpCalibrationStatus`, `GpClaimLanguage`, `GpInterval`, `LadderStageDto`, `ReaderDisposition`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — places the staged journey in the user-facing session path.
- [[Concepts/Learning System#The feedback loop|learning feedback loop]] — owns the learning intent behind the fixture or surface.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — cross-boundary name contract: references uniquely owned exported name `Checkpoint`; it does **not** directly execute this source module.
- [tests/test_irt_end_to_end.py](../../../../../../../tests/test_irt_end_to_end.py) — cross-boundary name contract: references uniquely owned exported name `Checkpoint`; it does **not** directly execute this source module.
- [tests/test_offline_benchmark.py](../../../../../../../tests/test_offline_benchmark.py) — cross-boundary name contract: references uniquely owned exported name `Checkpoint`; it does **not** directly execute this source module.
- [tests/test_probe_attempt_updates.py](../../../../../../../tests/test_probe_attempt_updates.py) — cross-boundary name contract: references uniquely owned exported name `Checkpoint`; it does **not** directly execute this source module.
- [tests/test_probe_audit.py](../../../../../../../tests/test_probe_audit.py) — cross-boundary name contract: references uniquely owned exported name `Checkpoint`; it does **not** directly execute this source module.
- [tests/test_probe_belief_posterior.py](../../../../../../../tests/test_probe_belief_posterior.py) — cross-boundary name contract: references uniquely owned exported name `Checkpoint`; it does **not** directly execute this source module.
- [tests/test_probe_coverage.py](../../../../../../../tests/test_probe_coverage.py) — cross-boundary name contract: references uniquely owned exported name `Checkpoint`; it does **not** directly execute this source module.
- [tests/test_probe_lifecycle.py](../../../../../../../tests/test_probe_lifecycle.py) — cross-boundary name contract: references uniquely owned exported name `Checkpoint`; it does **not** directly execute this source module.
- [tests/test_sidecar_golden_path.py](../../../../../../../tests/test_sidecar_golden_path.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_golden_path_assessment.py](../../../../../../../tests/test_sidecar_golden_path_assessment.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_golden_path_fixture.py](../../../../../../../tests/test_golden_path_fixture.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/goldenpath/shared.tsx](../../../../../../../apps/learnloop-tauri/src/components/goldenpath/shared.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
