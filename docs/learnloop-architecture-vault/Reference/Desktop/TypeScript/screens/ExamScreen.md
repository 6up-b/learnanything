---
title: "Desktop module · src/screens/ExamScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.ExamScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/ExamScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/ExamScreen.tsx"
source_commit: "513080252d4f7da7b6ddc69e4848ecb9f0014685"
source_commit_timestamp: "2026-07-27T14:08:25-04:00"
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

# `src/screens/ExamScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ExamScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/ExamScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/ExamScreen.tsx) |
| Source lines | 603 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `513080252d4f7da7b6ddc69e4848ecb9f0014685` |
| Commit timestamp | `2026-07-27T14:08:25-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]]

## Public API

- `export function ExamScreen(` — function, line 26

## Internal implementation anchors

- `type Phase = "loading" | "error" | "exam" | "finishing" | "report"` — type, line 19
- `const startedRef = useRef(false)` — const, line 44
- `const items = session?.items ?? []` — const, line 46
- `const currentIndex = useMemo( ()` — const, line 48
- `const current = currentIndex >= 0 ? items[currentIndex] : null` — const, line 52
- `const finish = useCallback( (sessionId: string)` — const, line 54
- `const command = error as CommandError` — const, line 64
- `const allAnswered = snap.items.every((it)` — const, line 87
- `const command = error as CommandError` — const, line 95
- `const submit = useCallback(async ()` — const, line 108
- `const trimmed = answer.trim()` — const, line 110
- `const nextAnswered = new Set(answered)` — const, line 119
- `const done = session.items.every((it)` — const, line 123
- `const onKey = (event: KeyboardEvent)` — const, line 139
- `const ctrl = event.ctrlKey || event.metaKey` — const, line 140
- `const answeredCount = answered.size` — const, line 189
- `function pct(value: number | null): string` — function, line 269
- `function ItemReview(` — function, line 278
- `const repair = outcome.repairSuggestions[0] ?? null` — const, line 289
- `const scoreLine = outcome.rubricScore != null && outcome.maxPoints != null ? `$` — const, line 290
- `function ExamReport(` — function, line 389
- `const itemsById = useMemo(()` — const, line 399
- `const map = new Map<string, ExamItemDto>()` — const, line 400
- `const predicted = report.predictedScoreFraction` — const, line 404
- `const scored = report.scoreFraction` — const, line 405
- `const facets = useMemo(()` — const, line 407
- `const sortKey = (f: ExamFacetOutcomeDto)` — const, line 408
- `const tone = f.observedCorrectness != null ? masteryTone(f.observedCorrectness, COLOR) : COLOR.textFaint` — const, line 463
- `const pred = it.predictedCorrectness` — const, line 496
- `const obs = it.observedCorrectness` — const, line 497
- `const obsTone = obs != null ? masteryTone(obs, COLOR) : COLOR.textFaint` — const, line 498
- `const open = openIndex === i` — const, line 499

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `ExamScreen`; references `ExamScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `ExamFacetOutcomeDto`, `ExamItemDto`, `ExamItemOutcomeDto`, `ExamReportSnapshot`, `ExamSessionSnapshot`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `masteryTone`
- [[Reference/Desktop/TypeScript/components/ItemPresentation|src/components/ItemPresentation.tsx]] — import-or-re-export; imports `ItemPresentation`
- [[Reference/Desktop/TypeScript/components/RepairTrace|src/components/RepairTrace.tsx]] — import-or-re-export; imports `RepairTraceBlocks`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `KeyBar`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `Card`, `SectionHeader`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/render/MathLiveEditor|src/render/MathLiveEditor.tsx]] — import-or-re-export; imports `MathLiveEditor`

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

1. Modify [apps/learnloop-tauri/src/screens/ExamScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/ExamScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
