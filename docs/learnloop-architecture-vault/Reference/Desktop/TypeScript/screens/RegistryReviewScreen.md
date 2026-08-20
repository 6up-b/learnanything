---
title: "Desktop module · src/screens/RegistryReviewScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.RegistryReviewScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/RegistryReviewScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/RegistryReviewScreen.tsx"
source_commit: "6fd60ddcf8feb8dd53c30194b9a24de4b94720dc"
source_commit_timestamp: "2026-07-26T17:17:50-04:00"
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

# `src/screens/RegistryReviewScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `RegistryReviewScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/RegistryReviewScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/RegistryReviewScreen.tsx) |
| Source lines | 276 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `6fd60ddcf8feb8dd53c30194b9a24de4b94720dc` |
| Commit timestamp | `2026-07-26T17:17:50-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/RegistryReviewScreen|src/screens/RegistryReviewScreen.tsx]]

## Public API

- `export function RegistryReviewScreen(` — function, line 12

## Internal implementation anchors

- `const load = useCallback(()` — const, line 28
- `let cancelled = false` — let, line 33
- `const cleanup = load()` — const, line 56
- `const proposeMerge = async (retiredFacetId: string, survivingFacetId: string, needId?: string | null)` — const, line 60
- `const facetOptions = useMemo(()` — const, line 72
- `function MeasurementRankRow(` — function, line 124
- `const ratio = rank.rankRatio == null ? "—" : rank.rankRatio.toFixed(2)` — const, line 125
- `function WarningRow(` — function, line 160
- `const canCoarsen = warning.kind === "coarsen_distinction" && warning.facetIds.length === 2` — const, line 161
- `function FacetCard(` — function, line 179
- `const others = facetOptions.filter((id)` — const, line 182
- `const accent = card.status === "reviewed" ? COLOR.greenSoft : card.status === "proposed" ? COLOR.amber : COLOR.textFaint` — const, line 185
- `const lockDetail = card.lockReasons[0]?.detail` — const, line 186
- `function ListBlock(` — function, line 254
- `const smallBtn: CSSProperties =` — const, line 268

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `RegistryReviewScreen`; references `RegistryReviewScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FacetContractCardDto`, `IdentifiabilityWarningDto`, `MeasurementRankDto`, `SubjectRegistryDto`
- [[Reference/Desktop/TypeScript/components/ProvenancePanel|src/components/ProvenancePanel.tsx]] — import-or-re-export; imports `ProvenancePanel`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`, `TermSelect`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

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

1. Modify [apps/learnloop-tauri/src/screens/RegistryReviewScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/RegistryReviewScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
