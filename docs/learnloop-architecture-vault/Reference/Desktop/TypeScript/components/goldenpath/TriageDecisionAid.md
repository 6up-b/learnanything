---
title: "Desktop module · src/components/goldenpath/TriageDecisionAid.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.goldenpath.TriageDecisionAid"
language: "TypeScript"
area: "TypeScript/components/goldenpath"
source_path: "apps/learnloop-tauri/src/components/goldenpath/TriageDecisionAid.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/goldenpath/TriageDecisionAid.tsx"
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

# `src/components/goldenpath/TriageDecisionAid.tsx`

Area: [[Reference/Desktop/TypeScript/components/goldenpath/_area|TypeScript/components/goldenpath]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `TriageDecisionAid` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/goldenpath/TriageDecisionAid.tsx](../../../../../../../apps/learnloop-tauri/src/components/goldenpath/TriageDecisionAid.tsx) |
| Source lines | 116 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]] → [[Reference/Desktop/TypeScript/components/goldenpath/TriageDecisionAid|src/components/goldenpath/TriageDecisionAid.tsx]]

## Public API

- `export function TriageDecisionAid(` — function, line 34

## Internal implementation anchors

- `function humanReason(reason: string): string` — function, line 11
- `function RouteBody(` — function, line 15
- `const decisive = triage.decisive` — const, line 41
- `const recommended = idx === 0` — const, line 79

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]] — import-or-re-export: `TriageDecisionAid`; references `TriageDecisionAid`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `TriageResultDto`, `TriageRouteDto`
- [[Reference/Desktop/TypeScript/components/goldenpath/shared|src/components/goldenpath/shared.tsx]] — import-or-re-export; imports `CalibrationBadge`, `SecondaryButton`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

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

1. Modify [apps/learnloop-tauri/src/components/goldenpath/TriageDecisionAid.tsx](../../../../../../../apps/learnloop-tauri/src/components/goldenpath/TriageDecisionAid.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
