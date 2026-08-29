---
title: "Desktop module · src/components/GoalReviewCard.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.GoalReviewCard"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/GoalReviewCard.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/GoalReviewCard.tsx"
source_commit: "565100878e11bc9ac281139570040c118fbaf1a5"
source_commit_timestamp: "2026-07-08T11:43:16-04:00"
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

# `src/components/GoalReviewCard.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `GoalReviewCard` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/GoalReviewCard.tsx](../../../../../../apps/learnloop-tauri/src/components/GoalReviewCard.tsx) |
| Source lines | 118 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `565100878e11bc9ac281139570040c118fbaf1a5` |
| Commit timestamp | `2026-07-08T11:43:16-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] → [[Reference/Desktop/TypeScript/components/GoalReviewCard|src/components/GoalReviewCard.tsx]]

## Public API

- `export type ReviewReason = "frontier_clear" | "due_passed" | "stale"` — type, line 12
- `export function GoalReviewCard(` — function, line 32

## Internal implementation anchors

- `const REASON_COPY: Record<ReviewReason,` — const, line 14
- `const copy = REASON_COPY[reason]` — const, line 46
- `const atRisk = goal.report?.atRiskCount ?? 0` — const, line 47
- `async function setStatus(status: GoalDto["status"])` — function, line 49
- `const ok = window.confirm(`$` — const, line 52
- `function ActionBtn(` — function, line 96

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `GoalReviewCard`, `ReviewReason`; references `GoalReviewCard`, `ReviewReason`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `GoalDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.
- [[Workflows/Goals Exams and Certification Workflow|Goals, Exams, and Certification Workflow]] — owns the end-to-end goal path.
- [[Concepts/Goals and Certification|Goals and Certification]] — owns goal and certification semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_goal_projection.py](../../../../../../tests/test_goal_projection.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_exam_session.py](../../../../../../tests/test_exam_session.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/GoalReviewCard.tsx](../../../../../../apps/learnloop-tauri/src/components/GoalReviewCard.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
