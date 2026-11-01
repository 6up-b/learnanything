---
title: "Desktop module · src/screens/reader/ReaderNotes.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.ReaderNotes"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/ReaderNotes.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/ReaderNotes.tsx"
source_commit: "517a3eec6bdd10976bb35ca9c5f2506fabfb9aec"
source_commit_timestamp: "2026-11-01T08:51:49-05:00"
source_worktree_state: "staged-or-mixed"
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

# `src/screens/reader/ReaderNotes.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ReaderNotes` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/ReaderNotes.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ReaderNotes.tsx) |
| Source lines | 381 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `staged-or-mixed` |
| Source commit | `517a3eec6bdd10976bb35ca9c5f2506fabfb9aec` |
| Commit timestamp | `2026-11-01T08:51:49-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/ReaderNotes|src/screens/reader/ReaderNotes.tsx]]

## Public API

- `export const NOTES_COPY =` — const, line 25
- `export function noteLabel(link: NoteLinkDto): string` — function, line 53
- `export function NoteCard(` — function, line 87
- `export type NoteMark = NoteMarksDto["marks"][number]` — type, line 134
- `export function NoteMarkButton(` — function, line 136
- `export function useNoteMarks(` — function, line 182
- `export function PathLineNotes(` — function, line 213
- `export function usePathNotes(goalId: string | null, ready: boolean)` — function, line 231
- `export function passagesOfKeys(keys: string[]): Array<` — function, line 251
- `export function NotesTakeBand(` — function, line 260
- `export function NoteLinkPicker(` — function, line 294

## Internal implementation anchors

- `const linkStyle =` — const, line 45
- `const quietStyle =` — const, line 49
- `const headStyle =` — const, line 50
- `const where = [link.note.title, link.note.heading].filter(Boolean).join(" › ")` — const, line 54
- `function useDecide(onChanged: (()` — function, line 59
- `const decide = async (link: NoteLinkDto, choice: "hide" | "keep")` — const, line 62
- `const out = await api.notesDecide(` — const, line 66
- `const hiddenId = hidden[link.linkId]` — const, line 69
- `const next =` — const, line 73
- `function NoteList(` — function, line 119
- `const ctx = useNotes()` — const, line 137
- `const onPage = surface === "pdf"` — const, line 139
- `const count = mark.notes.length` — const, line 140
- `const label = count > 1 ? `$` — const, line 141
- `const body = open ? ( <div data-note-mark-panel=` — const, line 143
- `const button = ( <button type="button" data-note-mark=` — const, line 156
- `const NO_MARKS: ReadonlyMap<string, NoteMark> = new Map()` — const, line 179
- `const enabled = Boolean(settings?.enabled)` — const, line 187
- `let cancelled = false` — let, line 195
- `const onChanged = useCallback(()` — const, line 202
- `const settingsKey = settings ? JSON.stringify(settings) : ""` — const, line 203
- `const context = useMemo<NotesContextValue | null>( // eslint-disable-next-line react-hooks/exhaustive-deps ()` — const, line 204
- `const ctx = useNotes()` — const, line 214
- `const first = notes[0]` — const, line 217
- `const ctx = useNotes()` — const, line 232
- `const enabled = Boolean(ctx?.settings.enabled) && Boolean(goalId) && ready` — const, line 234
- `const revision = ctx?.revision ?? 0` — const, line 235
- `let cancelled = false` — let, line 238
- `const out: Array<` — const, line 252
- `const at = key.indexOf(":")` — const, line 254
- `const ctx = useNotes()` — const, line 261
- `const passages = useMemo(()` — const, line 264
- `const enabled = Boolean(ctx?.settings.enabled) && passages.length > 0` — const, line 265
- `const revision = ctx?.revision ?? 0` — const, line 266
- `let cancelled = false` — let, line 269
- `const ctx = useNotes()` — const, line 300
- `const search = useCallback(async (words: string)` — const, line 308
- `const out = await api.notesSearch(words ?` — const, line 311
- `const on = ctx !== null` — const, line 322
- `const link = async (hit: NoteHitDto)` — const, line 325

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `NOTES_COPY`, `NoteLinkPicker`, `NoteMarkButton`, `useNoteMarks`; references `NOTES_COPY`, `NoteLinkPicker`, `NoteMarkButton`, `useNoteMarks`
- [[Reference/Desktop/TypeScript/screens/reader/CompareKeep|src/screens/reader/CompareKeep.tsx]] — import-or-re-export: `NotesTakeBand`; references `NotesTakeBand`
- [[Reference/Desktop/TypeScript/screens/reader/ComparePointTable|src/screens/reader/ComparePointTable.tsx]] — import-or-re-export: `NotesTakeBand`; references `NotesTakeBand`
- [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]] — import-or-re-export: `PathLineNotes`, `usePathNotes`; references `PathLineNotes`, `usePathNotes`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `NoteHitDto`, `NoteLinkDto`, `NoteMarksDto`, `NotesContractDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/notesContext|src/screens/reader/notesContext.ts]] — import-or-re-export; imports `NotesContextValue`, `useNotes`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `LearnerVoice`, `MeaningLabel`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/readerNotes.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerNotes.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/ReaderNotes.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ReaderNotes.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
