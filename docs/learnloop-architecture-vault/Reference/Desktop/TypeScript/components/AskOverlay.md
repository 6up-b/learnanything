---
title: "Desktop module · src/components/AskOverlay.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.AskOverlay"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/AskOverlay.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/AskOverlay.tsx"
source_commit: "971d7c274e09873d726d43578cd080e4d8865571"
source_commit_timestamp: "2026-07-27T06:01:19-04:00"
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

# `src/components/AskOverlay.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `AskOverlay` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/AskOverlay.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.tsx) |
| Source lines | 768 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `971d7c274e09873d726d43578cd080e4d8865571` |
| Commit timestamp | `2026-07-27T06:01:19-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]]

## Public API

- `export interface AskTarget` — interface, line 18
- `export function AskOverlay(` — function, line 96

## Internal implementation anchors

- `const CONTEXT_PILL: Record<TutorQuestionContext, PillColor> =` — const, line 34
- `interface ThreadEntry` — interface, line 41
- `interface SaveNotice` — interface, line 61
- `function promotionChipLabel(promotion: QuestionPromotionDto): string` — function, line 67
- `function promotionRequestLabel(request: QuestionPromotionRequestDto): string` — function, line 84
- `function entityIdOf(target: AskTarget): string` — function, line 92
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 118
- `const inputRef = useRef<HTMLInputElement | null>(null)` — const, line 119
- `const saveNoticeTimerRef = useRef<number | null>(null)` — const, line 120
- `const promoteNoticeTimerRef = useRef<number | null>(null)` — const, line 121
- `const open = target !== null` — const, line 123
- `function clearSaveNoticeTimer()` — function, line 125
- `function showSaveNotice(notice: SaveNotice)` — function, line 132
- `function clearPromoteNoticeTimer()` — function, line 141
- `function showPromoteNotice(notice: SaveNotice)` — function, line 148
- `function saveNoteLabel(entry: ThreadEntry)` — function, line 157
- `function canSaveNote(entry: ThreadEntry)` — function, line 163
- `let cancelled = false` — let, line 169
- `const entries: ThreadEntry[] = snapshot.events.map((event: TutorQuestionEventDto)` — const, line 190
- `const onKey = (event: KeyboardEvent)` — const, line 259
- `const node = bodyRef.current` — const, line 275
- `async function send()` — function, line 281
- `const text = question.trim()` — const, line 283
- `let answer:` — let, line 303
- `const readerAnswer = await api.readerAsk(` — const, line 315
- `const input: AskTutorQuestionInput =` — const, line 329
- `const tutorAnswer = await api.askTutorQuestion(input)` — const, line 340
- `const commandError = error as CommandError` — const, line 371
- `async function rate(eventId: string, useful: boolean)` — function, line 386
- `async function saveAsNote(eventId: string)` — function, line 397
- `const result = await api.saveTutorAnswerNote(eventId)` — const, line 400
- `const noteName = result.noteId ? ` $` — const, line 406
- `async function promote(eventId: string, intent: PromotionIntent)` — function, line 418
- `const result = await api.promoteTutorQuestion(eventId, intent)` — const, line 422
- `const backdropStyle: CSSProperties =` — const, line 704
- `const modalStyle: CSSProperties =` — const, line 716
- `const headerStyle: CSSProperties =` — const, line 729
- `const inputStyle: CSSProperties =` — const, line 738
- `const footerStyle: CSSProperties =` — const, line 749
- `const saveNoticeStyle: CSSProperties =` — const, line 760

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `AskOverlay`, `AskTarget`; references `AskOverlay`, `AskTarget`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export: `AskTarget`; references `AskTarget`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `AskTarget`; references `AskTarget`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AskTutorQuestionInput`, `CommandError`, `PromotionIntent`, `QuestionPromotionDto`, `QuestionPromotionRequestDto`, `TutorCitationDto`, `TutorQuestionContext`, `TutorQuestionEventDto`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export; imports `OpenInSource`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/AskOverlay.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
