---
title: "Desktop module · src/components/DiagnosisCard.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.DiagnosisCard"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/DiagnosisCard.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/DiagnosisCard.tsx"
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

# `src/components/DiagnosisCard.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `DiagnosisCard` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/DiagnosisCard.tsx](../../../../../../apps/learnloop-tauri/src/components/DiagnosisCard.tsx) |
| Source lines | 366 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] → [[Reference/Desktop/TypeScript/components/DiagnosisCard|src/components/DiagnosisCard.tsx]]

## Public API

- `export const DIAGNOSIS_POLL_MS = 2500` — const, line 15
- `export interface DiagnosisCardState` — interface, line 54
- `export function useDiagnosisCard( attemptId: string, initialStatus: DiagnosisStatusValue | null | undefined, onDiagnosisReady: (()` — function, line 71
- `export function DiagnosisCard(` — function, line 170

## Internal implementation anchors

- `function fmtDay(iso: string | null | undefined): string` — function, line 17
- `const date = new Date(iso)` — const, line 19
- `const box =` — const, line 24
- `const link =` — const, line 34
- `const shownAt = useRef<string | null>(null)` — const, line 80
- `const readyFired = useRef(false)` — const, line 81
- `let cancelled = false` — let, line 91
- `let timer: ReturnType<typeof setTimeout> | null = null` — let, line 92
- `const poll = ()` — const, line 93
- `const record = useCallback( async ( response: DiagnosisCardResponse | EscalationResponse | "not_same_mistake", citedAttemptId: string | null = null, )` — const, line 128
- `const own = useDiagnosisCard(attemptId, state ? null : initialStatus, onDiagnosisReady, onError)` — const, line 194
- `const escalation = card.escalation ?? null` — const, line 213
- `const escalatedRepair = escalation?.repair ?? null` — const, line 214
- `const repairs = (card.repairSuggestions ?? []).filter( (repair)` — const, line 216
- `const madeBefore = card.madeBefore ?? []` — const, line 219
- `const disowned = new Set(card.notSameMistakeAttemptIds ?? [])` — const, line 220
- `const chosen = escalation.recordedResponse === option.response` — const, line 274
- `const done = escalation.recordedResponse != null` — const, line 275
- `const chosen = card.recordedResponse === option.response` — const, line 345
- `const done = card.recordedResponse != null` — const, line 346

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `DiagnosisCard`, `useDiagnosisCard`; references `DiagnosisCard`, `useDiagnosisCard`
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export: `DIAGNOSIS_POLL_MS`; references `DIAGNOSIS_POLL_MS`
- [[Reference/Desktop/TypeScript/screens/feedback/FeedbackSurface|src/screens/feedback/FeedbackSurface.tsx]] — import-or-re-export: `DiagnosisCardState`; references `DiagnosisCardState`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DiagnosisCardDto`, `DiagnosisCardResponse`, `DiagnosisStatusValue`, `EscalationResponse`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `invalidate`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `Pill`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/guidePlan.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/guidePlan.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/DiagnosisCard.test.tsx](../../../../../../apps/learnloop-tauri/src/components/DiagnosisCard.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/DiagnosisCard.tsx](../../../../../../apps/learnloop-tauri/src/components/DiagnosisCard.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
