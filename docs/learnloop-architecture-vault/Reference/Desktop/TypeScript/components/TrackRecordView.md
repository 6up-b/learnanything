---
title: "Desktop module · src/components/TrackRecordView.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.TrackRecordView"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/TrackRecordView.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/TrackRecordView.tsx"
source_commit: "a29853775f09f6b504620b1a8b6d5e890161f912"
source_commit_timestamp: "2026-07-14T17:11:30-04:00"
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

# `src/components/TrackRecordView.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `TrackRecordView` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/TrackRecordView.tsx](../../../../../../apps/learnloop-tauri/src/components/TrackRecordView.tsx) |
| Source lines | 231 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `a29853775f09f6b504620b1a8b6d5e890161f912` |
| Commit timestamp | `2026-07-14T17:11:30-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] → [[Reference/Desktop/TypeScript/components/GoalBanner|src/components/GoalBanner.tsx]] → [[Reference/Desktop/TypeScript/components/TrackRecordView|src/components/TrackRecordView.tsx]]

## Public API

- `export function TrackRecordView(` — function, line 159

## Internal implementation anchors

- `const pct = (v: number | null | undefined): string` — const, line 13
- `const num3 = (v: number | null | undefined): string` — const, line 14
- `function SectionHeader(` — function, line 16
- `function ReliabilityCurve(` — function, line 26
- `const pad = 18` — const, line 27
- `const plot = size - pad * 2` — const, line 28
- `const xy = (frac: number)` — const, line 29
- `const yOf = (frac: number)` — const, line 30
- `const minBinN = 3` — const, line 31
- `const solid = bins.filter((b)` — const, line 32
- `const sparse = b.count < minBinN` — const, line 44
- `function AnswerCalibrationSection(` — function, line 73
- `function ForecastTrackRecordSection(` — function, line 114
- `const kinds = Object.entries(record.trackRecord.byKind)` — const, line 115
- `const thStyle: React.CSSProperties =` — const, line 154
- `const thStyleR: React.CSSProperties =` — const, line 155
- `const tdStyle: React.CSSProperties =` — const, line 156
- `const tdStyleR: React.CSSProperties =` — const, line 157
- `let cancelled = false` — let, line 173

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/GoalBanner|src/components/GoalBanner.tsx]] — import-or-re-export: `TrackRecordView`; references `TrackRecordView`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AnswerCalibrationReportDto`, `CalibrationBinDto`, `ForecastTrackRecordDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_forecast_ledger.py](../../../../../../tests/test_forecast_ledger.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/TrackRecordView.tsx](../../../../../../apps/learnloop-tauri/src/components/TrackRecordView.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
