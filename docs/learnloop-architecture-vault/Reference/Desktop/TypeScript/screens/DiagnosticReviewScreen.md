---
title: "Desktop module · src/screens/DiagnosticReviewScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.DiagnosticReviewScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/DiagnosticReviewScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/DiagnosticReviewScreen.tsx"
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

# `src/screens/DiagnosticReviewScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `DiagnosticReviewScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/DiagnosticReviewScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/DiagnosticReviewScreen.tsx) |
| Source lines | 251 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]]

## Public API

- `export function DiagnosticReviewScreen(` — function, line 32

## Internal implementation anchors

- `const CONTINUE_LABEL: Record<string, string> =` — const, line 21
- `const PLAIN_CONTINUE_LABEL: Record<string, string> =` — const, line 27
- `const simple = simplePracticeFeedback()` — const, line 73
- `const sharedFix = onOpenRepair ? blockEnd.releasedFeedback.find((entry)` — const, line 76
- `const handleContinue = useCallback(async ()` — const, line 80
- `const anchorItemId = blockEnd.releasedFeedback[0]?.practiceItemId ?? undefined` — const, line 85
- `const askTutor = ()` — const, line 86
- `const next = await api.getNextProbeItem(learningObjectId)` — const, line 103
- `const tutoringLabel = handoffOpensLesson(onTeachFromCheck) ? TEACH_AFTER_CHECK_LABEL : TUTOR_AFTER_CHECK_LABEL` — const, line 116
- `const routeLabel = (labels: Record<string, string>)` — const, line 117
- `const runNextStep = useCallback(()` — const, line 120
- `const onKey = (event: KeyboardEvent)` — const, line 129
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 132
- `const stepLabel = sharedFix ? FIX_MIX_UP_LABEL : routeLabel(PLAIN_CONTINUE_LABEL)` — const, line 158
- `const verdict = verdictOf(` — const, line 168

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `DiagnosticReviewScreen`; references `DiagnosticReviewScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `GuidedRedoDto`, `ProbeBlockEndDto`
- [[Reference/Desktop/TypeScript/app/checkHandoff|src/app/checkHandoff.ts]] — import-or-re-export; imports `CheckHandoff`, `TEACH_AFTER_CHECK_LABEL`, `TUTOR_AFTER_CHECK_LABEL`, `handoffOpensLesson`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]] — import-or-re-export; imports `FIX_MIX_UP_LABEL`, `VERDICT_TEXT`, `simplePracticeFeedback`, `verdictOf`
- [[Reference/Desktop/TypeScript/components/PlainParts|src/components/PlainParts.tsx]] — import-or-re-export; imports `DetailsToggle`, `PrimaryAction`, `quietLine`
- [[Reference/Desktop/TypeScript/components/ProbeBlockResult|src/components/ProbeBlockResult.tsx]] — import-or-re-export; imports `ProbeBlockResult`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `KeyBar`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `Card`, `SectionHeader`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.
- [[Concepts/Diagnosis and Remediation#Episode lifecycle|diagnosis episode lifecycle]] — owns diagnostic and repair policy.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/RepairOverFeedback.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/RepairOverFeedback.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/DiagnosticReviewScreen.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/DiagnosticReviewScreen.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/checkHandoff.test.tsx](../../../../../../apps/learnloop-tauri/src/app/checkHandoff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_diagnosis_adjudication.py](../../../../../../tests/test_diagnosis_adjudication.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_diagnostic_review_policy.py](../../../../../../tests/test_diagnostic_review_policy.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/DiagnosticReviewScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/DiagnosticReviewScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
