---
title: "Desktop module · src/components/ClaimSurface.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.ClaimSurface"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/ClaimSurface.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/ClaimSurface.tsx"
source_commit: "96eb5c906aa28df898ce8a4485b0817efcf154bd"
source_commit_timestamp: "2026-07-14T23:16:00-04:00"
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

# `src/components/ClaimSurface.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `ClaimSurface` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/ClaimSurface.tsx](../../../../../../apps/learnloop-tauri/src/components/ClaimSurface.tsx) |
| Source lines | 273 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `96eb5c906aa28df898ce8a4485b0817efcf154bd` |
| Commit timestamp | `2026-07-14T23:16:00-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] → [[Reference/Desktop/TypeScript/components/ClaimSurface|src/components/ClaimSurface.tsx]]

## Public API

- `export function mintVisitId(): string` — function, line 6
- `export function ClaimSurface(` — function, line 12

## Internal implementation anchors

- `const root = useRef<HTMLDivElement | null>(null)` — const, line 29
- `const exposureStarted = useRef(false)` — const, line 30
- `const node = root.current` — const, line 37
- `const observer = new IntersectionObserver( (entries)` — const, line 39
- `async function respond(payload: Record<string, unknown>)` — function, line 53
- `async function dismiss()` — function, line 64
- `const enabled = Boolean(presentation?.affordancesEnabled && !responded)` — const, line 74
- `const inDetailPanel = variant === "detail-panel"` — const, line 75
- `function ClaimResponses(` — function, line 191
- `const inDetailPanel = variant === "detail-panel"` — const, line 208
- `const button = (label: string, response: string, extra: Record<string, unknown> =` — const, line 209
- `const panelButtonStyle: CSSProperties =` — const, line 242
- `const panelPrimaryButtonStyle: CSSProperties =` — const, line 255
- `const panelDismissStyle: CSSProperties =` — const, line 262

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/GoalBanner|src/components/GoalBanner.tsx]] — import-or-re-export: `mintVisitId`; references `mintVisitId`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `ClaimSurface`, `mintVisitId`; references `ClaimSurface`, `mintVisitId`
- [[Reference/Desktop/TypeScript/screens/ReviewScreen|src/screens/ReviewScreen.tsx]] — import-or-re-export: `ClaimSurface`, `mintVisitId`; references `ClaimSurface`, `mintVisitId`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `ClaimSurface`, `mintVisitId`; references `ClaimSurface`, `mintVisitId`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ClaimCandidateDto`, `PresentedClaimDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_surfaced_belief_corrections.py](../../../../../../tests/test_surfaced_belief_corrections.py) — cross-boundary name contract: references uniquely owned exported name `ClaimSurface`; it does **not** directly execute this source module.
- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_forecast_ledger.py](../../../../../../tests/test_forecast_ledger.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/ClaimSurface.tsx](../../../../../../apps/learnloop-tauri/src/components/ClaimSurface.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
