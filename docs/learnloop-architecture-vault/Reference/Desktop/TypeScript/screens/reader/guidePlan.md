---
title: "Desktop module · src/screens/reader/guidePlan.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.guidePlan"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/guidePlan.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/guidePlan.ts"
source_commit: "807cf0540938f14375d3656d69a37071fa0d7396"
source_commit_timestamp: "2026-10-12T23:30:44-04:00"
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

# `src/screens/reader/guidePlan.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `GUIDE_DIAGNOSIS_POLL_MS`, `GUIDE_DIAGNOSIS_POLL_MAX_MS`, `guidePlanKey`, `pendingDiagnoses` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/guidePlan.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/guidePlan.ts) |
| Source lines | 100 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `807cf0540938f14375d3656d69a37071fa0d7396` |
| Commit timestamp | `2026-10-12T23:30:44-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/guidePlan|src/screens/reader/guidePlan.ts]]

## Public API

- `export const GUIDE_DIAGNOSIS_POLL_MS = 4_000` — const, line 19
- `export const GUIDE_DIAGNOSIS_POLL_MAX_MS = 60_000` — const, line 21
- `export function guidePlanKey(extractionId: string): QueryKey` — function, line 31
- `export function pendingDiagnoses(plan: ReaderGuidePlanDto | null | undefined): readonly string[]` — function, line 36
- `export function readGuidePlan( sourceId: string, extractionId: string, options:` — function, line 45
- `export function useGuideDiagnosisRefresh( source:` — function, line 65

## Internal implementation anchors

- `const GUIDE_PLAN_STATE_TAGS = [TAG.graph, TAG.goals, TAG.errors] as const` — const, line 29
- `const key = guidePlanKey(extractionId)` — const, line 50
- `const waiting = pendingDiagnoses(peek<ReaderGuidePlanDto>(key).data).length > 0` — const, line 51
- `const sourceId = source?.sourceId ?? null` — const, line 70
- `const extractionId = source?.extractionId ?? null` — const, line 71
- `const waitingOn = plan !== null && plan.extractionId === extractionId ? pendingDiagnoses(plan).join("\n") : ""` — const, line 72
- `const onPlanRef = useRef(onPlan)` — const, line 73
- `let cancelled = false` — let, line 78
- `let delay = GUIDE_DIAGNOSIS_POLL_MS` — let, line 79
- `let timer: ReturnType<typeof setTimeout> | null = null` — let, line 80
- `const poll = ()` — const, line 81

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `readGuidePlan`; references `readGuidePlan`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export: `useGuideDiagnosisRefresh`; references `useGuideDiagnosisRefresh`
- [[Reference/Desktop/TypeScript/screens/reader/useSidePane|src/screens/reader/useSidePane.ts]] — import-or-re-export: `readGuidePlan`; references `readGuidePlan`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderGuidePlanDto`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `QueryKey`, `peek`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/screens/reader/readerCache|src/screens/reader/readerCache.ts]] — import-or-re-export; imports `cachedSourceRead`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/guidePlan.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/guidePlan.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/ReaderScreen.marginMarksReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/ReaderScreen.marginMarksReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/guidePlan.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/guidePlan.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
