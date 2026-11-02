---
title: "Desktop module · src/screens/LessonScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.LessonScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/LessonScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/LessonScreen.tsx"
source_commit: "47c892762f2845348a5efaa4d16192161094013f"
source_commit_timestamp: "2026-11-02T05:28:14-05:00"
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

# `src/screens/LessonScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `LessonScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/LessonScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/LessonScreen.tsx) |
| Source lines | 417 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `47c892762f2845348a5efaa4d16192161094013f` |
| Commit timestamp | `2026-11-02T05:28:14-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]]

## Public API

- `export type LessonEntry = |` — type, line 36
- `export function LessonScreen(` — function, line 58
- `export const LESSON_FIGURE_COPY: Readonly<Record<Exclude<LessonFigureStatus, "shown">, string>> = Object.freeze(` — const, line 294
- `export const LESSON_FIGURE_CONTRACT: FiguresContract = Object.freeze(` — const, line 301

## Internal implementation anchors

- `const TAP_LABELS = ["1", "2", "3", "4", "5"]` — const, line 41
- `const CLOSE_WORDS: Record<string, string> =` — const, line 42
- `function dueWords(due: string): string` — function, line 51
- `const day = new Date(`$` — const, line 52
- `const days = Math.max(0, Math.round((day.getTime() - Date.now()) / 86_400_000))` — const, line 54
- `const run = useCallback(async (input: LessonTurnInput)` — const, line 82
- `const next = await api.lessonTurn(input)` — const, line 87
- `const err = getCommandError(error)` — const, line 91
- `const code = err?.code ?? ""` — const, line 92
- `const message = err?.message ?? String(error)` — const, line 93
- `const details = (err?.details ??` — const, line 96
- `const saved = details.lesson_id ?? details.lessonId` — const, line 97
- `const lessonId = typeof saved === "string" && saved ? saved : input.lessonId` — const, line 98
- `let cancelled = false` — let, line 117
- `const lessonId = view?.lessonId` — const, line 129
- `const openCheck = view?.openCheck ?? null` — const, line 130
- `const send = useCallback(async ()` — const, line 138
- `const text = reply.trim()` — const, line 140
- `const submitCheck = useCallback(async ()` — const, line 145
- `const submitPrediction = useCallback(async ()` — const, line 151
- `const value = predictionAnswer.trim()` — const, line 153
- `const stop = useCallback(async ()` — const, line 158
- `const startFresh = useCallback(async ()` — const, line 164
- `const learningObjectIds = view?.learningObjectIds ?? []` — const, line 165
- `const feed = useMemo(()` — const, line 170
- `const title = entry.kind === "open" ? entry.title : undefined` — const, line 171
- `function useLessonFigureCtl(figure: FigureViewDto): FiguresCtl` — function, line 304
- `function LessonFigure(` — function, line 329
- `const shown = useMemo(()` — const, line 331
- `const ctl = useLessonFigureCtl(shown)` — const, line 332
- `function FeedEntry(` — function, line 336
- `const open = item.checkRef === openCheckRef` — const, line 355

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: `LessonEntry`; references `LessonEntry`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FigureViewDto`, `LessonFeedEntryDto`, `LessonFigureStatus`, `LessonTurnInput`, `LessonViewDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `getCommandError`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export; imports `FigureInline`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export; imports `FiguresContract`, `FiguresCtl`, `figurePlacementKey`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/LessonScreen.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/LessonScreen.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/LessonScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/LessonScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
