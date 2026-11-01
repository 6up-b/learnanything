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
source_commit: "b23e92d402b0bbc32e00f4c6e1d3121b79bed9e5"
source_commit_timestamp: "2026-11-01T09:39:06-05:00"
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
| Source lines | 487 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `b23e92d402b0bbc32e00f4c6e1d3121b79bed9e5` |
| Commit timestamp | `2026-11-01T09:39:06-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/ReaderNotes|src/screens/reader/ReaderNotes.tsx]]

## Public API

- `export const NOTES_COPY =` — const, line 25
- `export function noteLabel(link: NoteLinkDto): string` — function, line 53
- `export const NOTES_POLL_MS =` — const, line 60
- `export function retainHidden(previous: readonly NoteLinkDto[], next: readonly NoteLinkDto[], hidden: ReadonlyMap<string, HiddenNote>): NoteLinkDto[]` — function, line 64
- `export function NoteCard(` — function, line 107
- `export type NoteMark = NoteMarksDto["marks"][number]` — type, line 154
- `export function NoteMarkButton(` — function, line 156
- `export function mergeMarks(previous: ReadonlyMap<string, NoteMark>, next: readonly NoteMark[], hidden: ReadonlyMap<string, HiddenNote>): Map<string, NoteMark>` — function, line 204
- `export function useNoteMarks(` — function, line 216
- `export function PathLineNotes(` — function, line 270
- `export function usePathNotes(goalId: string | null, ready: boolean)` — function, line 291
- `export function passagesOfKeys(keys: string[]): Array<` — function, line 335
- `export type NoteTakeOutcome = "kept" | "drafted" | "failed"` — type, line 346
- `export function NotesTakeBand(` — function, line 348
- `export function NoteLinkPicker(` — function, line 400

## Internal implementation anchors

- `const linkStyle =` — const, line 45
- `const quietStyle =` — const, line 49
- `const headStyle =` — const, line 50
- `const where = [link.note.title, link.note.heading].filter(Boolean).join(" › ")` — const, line 54
- `const listed = new Set(next.map((link)` — const, line 66
- `const out = [...next]` — const, line 67
- `function useDecide(ctx: NotesContextValue | null)` — function, line 76
- `const hiddenId = (link: NoteLinkDto)` — const, line 79
- `const decide = async (link: NoteLinkDto, choice: "hide" | "keep")` — const, line 80
- `const out = await api.notesDecide(` — const, line 84
- `const id = hiddenId(link)` — const, line 88
- `const next =` — const, line 93
- `function NoteList(` — function, line 139
- `const ctx = useNotes()` — const, line 157
- `const onPage = surface === "pdf"` — const, line 159
- `const count = mark.notes.length` — const, line 160
- `const label = count > 1 ? `$` — const, line 161
- `const body = open ? ( <div data-note-mark-panel=` — const, line 163
- `const button = ( <button type="button" data-note-mark=` — const, line 176
- `const NO_MARKS: ReadonlyMap<string, NoteMark> = new Map()` — const, line 199
- `const NO_HIDDEN: ReadonlyMap<string, HiddenNote> = new Map()` — const, line 200
- `const out = new Map(next.map((mark)` — const, line 206
- `const merged = retainHidden(mark.notes, out.get(spanId)?.notes ?? [], hidden)` — const, line 209
- `const enabled = Boolean(settings?.enabled)` — const, line 221
- `const hiddenRef = useRef(hidden)` — const, line 225
- `const marksFor = useRef<string | null>(null)` — const, line 227
- `let cancelled = false` — let, line 234
- `const same = marksFor.current === extractionId` — const, line 239
- `const onChanged = useCallback(()` — const, line 247
- `const remember = useCallback((link: NoteLinkDto, hiddenId: string)` — const, line 248
- `const forget = useCallback((linkId: string)` — const, line 251
- `const next = new Map(current)` — const, line 254
- `const settingsKey = settings ? JSON.stringify(settings) : ""` — const, line 259
- `const context = useMemo<NotesContextValue | null>( ()` — const, line 260
- `const ctx = useNotes()` — const, line 271
- `const first = notes[0]` — const, line 274
- `const ctx = useNotes()` — const, line 292
- `const enabled = Boolean(ctx?.settings.enabled) && Boolean(goalId) && ready` — const, line 295
- `const revision = ctx?.revision ?? 0` — const, line 296
- `const ctxRef = useRef(ctx)` — const, line 297
- `const linking = useRef<` — const, line 299
- `let cancelled = false` — let, line 302
- `let timer: ReturnType<typeof setTimeout> | undefined` — let, line 303
- `const hidden = ctxRef.current?.hidden ?? NO_HIDDEN` — const, line 307
- `const same = linking.current.goalId === goalId` — const, line 308
- `const before = same ? linking.current.state : null` — const, line 309
- `const next = new Map(out.lines.map((line)` — const, line 312
- `const merged = retainHidden(list, next.get(lo) ?? [], hidden)` — const, line 315
- `const wait = out.linking === "running" ? NOTES_POLL_MS.running : out.linking === "waiting" ? NOTES_POLL_MS.waiting : null` — const, line 322
- `const out: Array<` — const, line 336
- `const at = key.indexOf(":")` — const, line 338
- `const ctx = useNotes()` — const, line 353
- `const keysKey = keys.join("|")` — const, line 357
- `const passages = useMemo(()` — const, line 358
- `const enabled = Boolean(ctx?.settings.enabled) && passages.length > 0` — const, line 359
- `const revision = ctx?.revision ?? 0` — const, line 360
- `const use = async (link: NoteLinkDto)` — const, line 363
- `let cancelled = false` — let, line 375
- `const ctx = useNotes()` — const, line 406
- `const search = useCallback(async (words: string)` — const, line 414
- `const out = await api.notesSearch(words ?` — const, line 417
- `const on = ctx !== null` — const, line 428
- `const link = async (hit: NoteHitDto)` — const, line 431

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `NOTES_COPY`, `NoteLinkPicker`, `NoteMarkButton`, `useNoteMarks`; references `NOTES_COPY`, `NoteLinkPicker`, `NoteMarkButton`, `useNoteMarks`
- [[Reference/Desktop/TypeScript/screens/reader/CompareKeep|src/screens/reader/CompareKeep.tsx]] — import-or-re-export: `NotesTakeBand`; references `NotesTakeBand`
- [[Reference/Desktop/TypeScript/screens/reader/ComparePointTable|src/screens/reader/ComparePointTable.tsx]] — import-or-re-export: `NoteTakeOutcome`, `NotesTakeBand`; references `NoteTakeOutcome`, `NotesTakeBand`
- [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]] — import-or-re-export: `PathLineNotes`, `usePathNotes`; references `PathLineNotes`, `usePathNotes`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `NoteHitDto`, `NoteLinkDto`, `NoteMarksDto`, `NotesContractDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/notesContext|src/screens/reader/notesContext.ts]] — import-or-re-export; imports `HiddenNote`, `NotesContextValue`, `useNotes`
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
