---
title: "Desktop module · src/components/GoalWizard.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.GoalWizard"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/GoalWizard.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/GoalWizard.tsx"
source_commit: "101474c3087317e780021b2cb665b3ffac136da7"
source_commit_timestamp: "2026-07-26T11:25:26-04:00"
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

# `src/components/GoalWizard.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `GoalWizard` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/GoalWizard.tsx](../../../../../../apps/learnloop-tauri/src/components/GoalWizard.tsx) |
| Source lines | 683 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `101474c3087317e780021b2cb665b3ffac136da7` |
| Commit timestamp | `2026-07-26T11:25:26-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] → [[Reference/Desktop/TypeScript/components/GoalWizard|src/components/GoalWizard.tsx]]

## Public API

- `export function GoalWizard(` — function, line 17

## Internal implementation anchors

- `const STEP_LABELS = ["what", "how well", "by when", "exam"]` — const, line 15
- `const facetIds = useMemo( ()` — const, line 51
- `const conceptIds = useMemo(()` — const, line 55
- `const dueAt = openEnded || !dueDate ? null : new Date(`$` — const, line 56
- `const stepValid = useMemo(()` — const, line 58
- `let cancelled = false` — let, line 66
- `let cancelled = false` — let, line 86
- `const handle = window.setTimeout(()` — const, line 88
- `const advance = ()` — const, line 116
- `async function generateStarterPractice()` — function, line 124
- `const gaps = feasibility?.materialGaps ?? []` — const, line 125
- `const result = await api.generateStarterPractice( gaps.map((gap)` — const, line 130
- `async function create()` — function, line 142
- `const created = await api.createGoal(` — const, line 147
- `const filteredConcepts = useMemo(()` — const, line 167
- `const q = filter.trim().toLowerCase()` — const, line 169
- `const examQuestionsRoughly = Math.round(targetRecall * 20)` — const, line 174
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 186
- `const ownsEnter = tag === "input" || tag === "textarea" || tag === "select" || tag === "button"` — const, line 187
- `const next = new Set(prev)` — const, line 254
- `function StepWhat(` — function, line 304
- `const on = selected.has(c.id)` — const, line 365
- `const measurable = c.learningObjects.length > 0` — const, line 371
- `function StepHowWell(` — function, line 412
- `function StepByWhen(` — function, line 430
- `const gaps = feasibility?.materialGaps ?? []` — const, line 455
- `function StepExam(` — function, line 543
- `function SummaryRow(` — function, line 637
- `function Label(` — function, line 646
- `const inputStyle: CSSProperties =` — const, line 654
- `const primaryBtn: CSSProperties =` — const, line 665
- `const ghostBtn: CSSProperties =` — const, line 675

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export: `GoalWizard`; references `GoalWizard`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `GoalWizard`; references `GoalWizard`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ConceptGraphNode`, `CreateGoalResult`, `GoalFeasibilityResult`
- [[Reference/Desktop/TypeScript/components/CommandOverlayFrame|src/components/CommandOverlayFrame.tsx]] — import-or-re-export; imports `CommandOverlayFrame`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Goals Exams and Certification Workflow|Goals, Exams, and Certification Workflow]] — owns the end-to-end goal path.
- [[Concepts/Goals and Certification|Goals and Certification]] — owns goal and certification semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_goal_projection.py](../../../../../../tests/test_goal_projection.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_exam_session.py](../../../../../../tests/test_exam_session.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/GoalWizard.tsx](../../../../../../apps/learnloop-tauri/src/components/GoalWizard.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
