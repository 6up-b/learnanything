---
title: "Desktop module · src/app/practiceFeedback.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.practiceFeedback"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/practiceFeedback.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/practiceFeedback.ts"
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

# `src/app/practiceFeedback.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `simplePracticeFeedback`, `Verdict`, `VERDICT_TEXT`, `verdictOf` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/practiceFeedback.ts](../../../../../../apps/learnloop-tauri/src/app/practiceFeedback.ts) |
| Source lines | 96 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]]

## Public API

- `export function simplePracticeFeedback(): boolean` — function, line 12
- `export type Verdict = "right" | "partly" | "not_yet" | "held"` — type, line 16
- `export const VERDICT_TEXT: Record<Verdict, string> =` — const, line 19
- `export function verdictOf(` — function, line 33
- `export const REPAIR_STEP_MINUTES = 4` — const, line 63
- `export const FIX_MIX_UP_LABEL = `Fix this mix-up · about $` — const, line 64
- `export type FeedbackOrigin = "plan" | "today" | "reader"` — type, line 67
- `export function feedbackOrigin(` — function, line 69
- `export const ORIGIN_LABEL: Record<FeedbackOrigin, string> =` — const, line 74
- `export function plainSlug(slug: string | null | undefined): string` — function, line 81
- `export function expectedAnswerText(value: unknown): string` — function, line 86

## Internal implementation anchors

- `const ratio = typeof correctness === "number" && Number.isFinite(correctness) ? correctness : typeof score === "number" && max > 0 ? score / max : 0` — const, line 45

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `feedbackOrigin`, `simplePracticeFeedback`; references `feedbackOrigin`, `simplePracticeFeedback`
- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `simplePracticeFeedback`; references `simplePracticeFeedback`
- [[Reference/Desktop/TypeScript/components/SessionFinishHud|src/components/SessionFinishHud.tsx]] — import-or-re-export: `simplePracticeFeedback`; references `simplePracticeFeedback`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export: `FIX_MIX_UP_LABEL`, `VERDICT_TEXT`, `simplePracticeFeedback`, `verdictOf`; references `FIX_MIX_UP_LABEL`, `VERDICT_TEXT`, `simplePracticeFeedback`, `verdictOf`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `FIX_MIX_UP_LABEL`, `FeedbackOrigin`, `VERDICT_TEXT`, `simplePracticeFeedback`, `verdictOf`; references `FIX_MIX_UP_LABEL`, `FeedbackOrigin`, `VERDICT_TEXT`, `simplePracticeFeedback`, `verdictOf`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `expectedAnswerText`, `simplePracticeFeedback`; references `expectedAnswerText`, `simplePracticeFeedback`
- [[Reference/Desktop/TypeScript/screens/RepairScreen|src/screens/RepairScreen.tsx]] — import-or-re-export: `FIX_MIX_UP_LABEL`, `simplePracticeFeedback`; references `FIX_MIX_UP_LABEL`, `simplePracticeFeedback`
- [[Reference/Desktop/TypeScript/screens/feedback/FeedbackSurface|src/screens/feedback/FeedbackSurface.tsx]] — import-or-re-export: `FeedbackOrigin`, `ORIGIN_LABEL`, `VERDICT_TEXT`, `Verdict`, `expectedAnswerText`; references `FeedbackOrigin`, `ORIGIN_LABEL`, `VERDICT_TEXT`, `Verdict`, `expectedAnswerText`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/app/practiceFeedback.test.ts](../../../../../../apps/learnloop-tauri/src/app/practiceFeedback.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_forecast_ledger.py](../../../../../../tests/test_forecast_ledger.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/practiceFeedback.ts](../../../../../../apps/learnloop-tauri/src/app/practiceFeedback.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
