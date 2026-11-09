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
| Source lines | 524 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/ReaderNotes|src/screens/reader/ReaderNotes.tsx]]

## Public API

- `export const NOTES_COPY =` — const, line 32
- `export function noteLabel(link: NoteLinkDto): string` — function, line 63
- `export const NOTES_POLL_MS =` — const, line 70
- `export function retainHidden(previous: readonly NoteLinkDto[], next: readonly NoteLinkDto[], hidden: ReadonlyMap<string, HiddenNote>): NoteLinkDto[]` — function, line 74
- `export function NoteCard(` — function, line 117
- `export function NotesWhereThisGoes(` — function, line 152
- `export type NoteMark = NoteMarksDto["marks"][number]` — type, line 184
- `export function NoteMarkButton(` — function, line 186
- `export function mergeMarks(previous: ReadonlyMap<string, NoteMark>, next: readonly NoteMark[], hidden: ReadonlyMap<string, HiddenNote>): Map<string, NoteMark>` — function, line 234
- `export function useNoteMarks(` — function, line 246
- `export function PathLineNotes(` — function, line 300
- `export function usePathNotes(goalId: string | null, ready: boolean)` — function, line 321
- `export function passagesOfKeys(keys: string[]): Array<` — function, line 365
- `export type NoteTakeOutcome = "kept" | "drafted" | "failed"` — type, line 376
- `export function NotesTakeBand(` — function, line 378
- `export function NoteLinkPicker(` — function, line 430

## Internal implementation anchors

- `const linkStyle =` — const, line 55
- `const quietStyle =` — const, line 59
- `const headStyle =` — const, line 60
- `const where = [link.note.title, link.note.heading].filter(Boolean).join(" › ")` — const, line 64
- `const listed = new Set(next.map((link)` — const, line 76
- `const out = [...next]` — const, line 77
- `function useDecide(ctx: NotesContextValue | null)` — function, line 86
- `const hiddenId = (link: NoteLinkDto)` — const, line 89
- `const decide = async (link: NoteLinkDto, choice: "hide" | "keep")` — const, line 90
- `const out = await api.notesDecide(` — const, line 94
- `const id = hiddenId(link)` — const, line 98
- `const next =` — const, line 103
- `const gaps = Boolean(ctx?.settings.gaps)` — const, line 154
- `function NoteList(` — function, line 168
- `const ctx = useNotes()` — const, line 187
- `const onPage = surface === "pdf"` — const, line 189
- `const count = mark.notes.length` — const, line 190
- `const label = count > 1 ? `$` — const, line 191
- `const body = open ? ( <div data-note-mark-panel=` — const, line 193
- `const button = ( <button type="button" data-note-mark=` — const, line 206
- `const NO_MARKS: ReadonlyMap<string, NoteMark> = new Map()` — const, line 229
- `const NO_HIDDEN: ReadonlyMap<string, HiddenNote> = new Map()` — const, line 230
- `const out = new Map(next.map((mark)` — const, line 236
- `const merged = retainHidden(mark.notes, out.get(spanId)?.notes ?? [], hidden)` — const, line 239
- `const enabled = Boolean(settings?.enabled)` — const, line 251
- `const hiddenRef = useRef(hidden)` — const, line 255
- `const marksFor = useRef<string | null>(null)` — const, line 257
- `let cancelled = false` — let, line 264
- `const same = marksFor.current === extractionId` — const, line 269
- `const onChanged = useCallback(()` — const, line 277
- `const remember = useCallback((link: NoteLinkDto, hiddenId: string)` — const, line 278
- `const forget = useCallback((linkId: string)` — const, line 281
- `const next = new Map(current)` — const, line 284
- `const settingsKey = settings ? JSON.stringify(settings) : ""` — const, line 289
- `const context = useMemo<NotesContextValue | null>( ()` — const, line 290
- `const ctx = useNotes()` — const, line 301
- `const first = notes[0]` — const, line 304
- `const ctx = useNotes()` — const, line 322
- `const enabled = Boolean(ctx?.settings.enabled) && Boolean(goalId) && ready` — const, line 325
- `const revision = ctx?.revision ?? 0` — const, line 326
- `const ctxRef = useRef(ctx)` — const, line 327
- `const linking = useRef<` — const, line 329
- `let cancelled = false` — let, line 332
- `let timer: ReturnType<typeof setTimeout> | undefined` — let, line 333
- `const hidden = ctxRef.current?.hidden ?? NO_HIDDEN` — const, line 337
- `const same = linking.current.goalId === goalId` — const, line 338
- `const before = same ? linking.current.state : null` — const, line 339
- `const next = new Map(out.lines.map((line)` — const, line 342
- `const merged = retainHidden(list, next.get(lo) ?? [], hidden)` — const, line 345
- `const wait = out.linking === "running" ? NOTES_POLL_MS.running : out.linking === "waiting" ? NOTES_POLL_MS.waiting : null` — const, line 352
- `const out: Array<` — const, line 366
- `const at = key.indexOf(":")` — const, line 368
- `const ctx = useNotes()` — const, line 383
- `const keysKey = keys.join("|")` — const, line 387
- `const passages = useMemo(()` — const, line 388
- `const enabled = Boolean(ctx?.settings.enabled) && passages.length > 0` — const, line 389
- `const revision = ctx?.revision ?? 0` — const, line 390
- `const use = async (link: NoteLinkDto)` — const, line 393
- `let cancelled = false` — let, line 405
- `const ctx = useNotes()` — const, line 436
- `const meaningOffered = Boolean(ctx?.settings.meaning)` — const, line 444
- `const mode: "words" | "meaning" = meaningOffered && byMeaning ? "meaning" : "words"` — const, line 446
- `const search = useCallback(async (words: string, how: "words" | "meaning" = "words")` — const, line 448
- `const where = words ?` — const, line 451
- `const out = await api.notesSearch(how === "meaning" ?` — const, line 452
- `const on = ctx !== null` — const, line 463
- `const link = async (hit: NoteHitDto)` — const, line 466

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
- [apps/learnloop-tauri/src/screens/reader/notesGaps.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/notesGaps.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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
