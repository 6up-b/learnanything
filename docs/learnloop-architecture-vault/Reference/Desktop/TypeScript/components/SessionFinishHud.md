---
title: "Desktop module · src/components/SessionFinishHud.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.SessionFinishHud"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/SessionFinishHud.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/SessionFinishHud.tsx"
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

# `src/components/SessionFinishHud.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `SessionFinishHud` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/SessionFinishHud.tsx](../../../../../../apps/learnloop-tauri/src/components/SessionFinishHud.tsx) |
| Source lines | 546 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/SessionFinishHud|src/components/SessionFinishHud.tsx]]

## Public API

- `export function SessionFinishHud(` — function, line 72
- `export function sessionLengthLine(summary: SessionEndSummary): string` — function, line 90
- `export function sessionTopicLine(topic: SessionTopicDto): string` — function, line 99

## Internal implementation anchors

- `const EXIT_MS = 520` — const, line 20
- `const CHAR_W = 7` — const, line 21
- `const CHAR_H = 12` — const, line 22
- `const ACTIVE_FRAME_MS = 33` — const, line 23
- `const COMPLETE_FRAME_MS = 66` — const, line 24
- `const GLYPHS: Record<string, string[]> =` — const, line 27
- `const C =` — const, line 40
- `type ColorId = (typeof C)[keyof typeof C]` — type, line 51
- `const COLOR_CLASS: Record<ColorId, string> =` — const, line 53
- `const NEEDS_ESCAPE_RE = /[&<>]/` — const, line 63
- `const HTML_ESCAPE_RE = /[&<>]/g` — const, line 64
- `function plural(count: number, one: string, many: string): string` — function, line 83
- `const ms = new Date(summary.endedAt).getTime() - new Date(summary.startedAt).getTime()` — const, line 91
- `const minutes = Number.isFinite(ms) && ms > 0 ? Math.max(1, Math.round(ms / 60000)) : 1` — const, line 92
- `function SessionFinishCard(` — function, line 104
- `const onKey = (event: KeyboardEvent)` — const, line 108
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 111
- `const topics = summary.topics ?? []` — const, line 120
- `const nextLines = nextPracticeLines(summary.nextPractice,` — const, line 122
- `function ClassicSessionFinishHud(` — function, line 172
- `const active = summary !== null` — const, line 179
- `const closingRef = useRef(false)` — const, line 181
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 182
- `const preRef = useRef<HTMLPreElement>(null)` — const, line 183
- `const requestClose = useCallback(()` — const, line 191
- `const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches` — const, line 194
- `const onKey = (event: KeyboardEvent)` — const, line 205
- `const container = containerRef.current` — const, line 219
- `const pre = preRef.current` — const, line 220
- `const aspect = CHAR_W / CHAR_H` — const, line 223
- `const code = summary.sessionId.slice(-6).toUpperCase()` — const, line 224
- `const logNo = (parseInt(summary.sessionId.slice(-5), 36) % 9000) + 1000` — const, line 225
- `const elapsed = formatElapsed(summary.startedAt, summary.endedAt)` — const, line 226
- `const attempts = String(summary.attemptsRecorded)` — const, line 227
- `const items = String(summary.itemsReviewed)` — const, line 228
- `const followups = summary.followupsQueued != null ? String(summary.followupsQueued) : "—"` — const, line 229
- `const streakDays = `$` — const, line 230
- `const streakActive = summary.streak.activeToday` — const, line 231
- `const bestStreak = `BEST STREAK $` — const, line 232
- `const facetsDemonstrated = summary.facetsDemonstrated ?? 0` — const, line 237
- `const movedUp = summary.predictionsMoved?.up ?? 0` — const, line 238
- `const movedDown = summary.predictionsMoved?.down ?? 0` — const, line 239
- `const corrections = summary.corrections ?? 0` — const, line 240
- `const mscResolved = summary.misconceptionsTouched?.resolved ?? 0` — const, line 241
- `const mscReturned = summary.misconceptionsTouched?.returned ?? 0` — const, line 242
- `const coldDone = summary.coldChecksCompleted ?? 0` — const, line 246
- `const coldPassed = summary.coldChecksPassed ?? 0` — const, line 247
- `type DiffLine =` — type, line 251
- `const candidates: DiffLine[] = []` — const, line 252
- `const forced = candidates.filter((c)` — const, line 276
- `const optional = candidates.filter((c)` — const, line 277
- `const diffLines = [...forced, ...optional].slice(0, 3)` — const, line 278
- `const hasMoreDiff = candidates.length > diffLines.length` — const, line 279
- `let cols = 0` — let, line 281
- `let rows = 0` — let, line 282
- `let grid: string[] = []` — let, line 283
- `let cgrid = new Uint8Array(0)` — let, line 284
- `const resize = ()` — const, line 285
- `const rect = container.getBoundingClientRect()` — const, line 286
- `const nextCols = Math.max(40, Math.floor(rect.width / CHAR_W))` — const, line 287
- `const nextRows = Math.max(24, Math.floor(rect.height / CHAR_H))` — const, line 288
- `const ro = new ResizeObserver(resize)` — const, line 296
- `const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches` — const, line 299
- `let raf = 0` — let, line 300
- `let startTs = 0` — let, line 301
- `let lastDrawTs = 0` — let, line 302
- `const draw = (ts: number)` — const, line 304
- `const sinceStart = ts - startTs` — const, line 307
- `const pt = Math.min(1, Math.max(0, (sinceStart - 300) / 2050))` — const, line 309
- `const pct = reduce ? 100 : Math.round((1 - Math.pow(1 - pt, 3)) * 100)` — const, line 310
- `const f = pct / 100` — const, line 311
- `const done = pct >= 100` — const, line 312
- `const phase = reduce ? 0 : ts / 1000` — const, line 313
- `const frameMs = done ? COMPLETE_FRAME_MS : ACTIVE_FRAME_MS` — const, line 315
- `const set = (r: number, c: number, ch: string, color: ColorId)` — const, line 324
- `const i = r * cols + c` — const, line 326
- `const put = (r: number, c: number, str: string, color: ColorId)` — const, line 330
- `const putCenter = (r: number, str: string, color: ColorId)` — const, line 333
- `const cx = (cols - 1) / 2` — const, line 337
- `const cy = (rows - 1) / 2` — const, line 338
- `const maxR = Math.min(cx - 2, (cy - 2) / aspect)` — const, line 339
- `const rMeter = maxR * 0.82` — const, line 340
- `const rOuter = maxR * 0.99` — const, line 341
- `const rClaw = maxR * 0.9` — const, line 342
- `const rInner = maxR * 0.6` — const, line 343
- `const place = (rad: number, ang: number, ch: string, color: ColorId)` — const, line 345
- `const ringSteps = (rad: number)` — const, line 348
- `const steps = ringSteps(rad)` — const, line 352
- `const prog = ((phase / 3.4) + off) % 1` — const, line 362
- `const rad = maxR * (0.14 + prog * 0.72)` — const, line 363
- `const shade = prog < 0.7 ? C.amberLow : C.faintDot` — const, line 364
- `const steps = ringSteps(rad)` — const, line 365
- `const base = phase * 0.18 + k * 0.25` — const, line 375
- `const steps = ringSteps(rMeter)` — const, line 383
- `const t = s / steps` — const, line 385
- `const ang = -Math.PI / 2 + t * 2 * Math.PI` — const, line 386
- `const lit = t <= f` — const, line 387
- `const head = !done && lit && f - t < 2.5 / steps` — const, line 388
- `const teleRows = Math.min(10, Math.floor(rows * 0.34))` — const, line 407
- `const teleTop = Math.round(cy - teleRows / 2)` — const, line 408
- `const onL = !reduce && Math.sin(phase * 3 - i * 0.6) > 0.2` — const, line 410
- `const onR = !reduce && Math.sin(phase * 3 - i * 0.6 + 1.5) > 0.2` — const, line 411
- `const xr = Math.round(cy - rInner * aspect)` — const, line 417
- `const logStr = `LOG #$` — const, line 428
- `const status = done ? "● STATUS OK" : "○ FINALIZING"` — const, line 431
- `const digits = String(pct)` — const, line 438
- `const blockW = digits.length * 5 - 1` — const, line 439
- `const startCol = Math.round(cx - (blockW - 1) / 2)` — const, line 440
- `const topRow = Math.round(cy) - 2` — const, line 441
- `const glyph = GLYPHS[digits[di]]` — const, line 443
- `const segs: Array<[string, ColorId]> = [ ["ATTEMPTS ", C.faint], [attempts, C.amber], [" ", C.faint], ["ITEMS ", C.faint], [items, C.amber], [" ", C.faint], ["FOLLOW-UPS ", C.faint], [followups, C.green], [" ", C.faint], ["STREAK ", C.faint], [streakDays, str…` — const, line 456
- `const total = segs.reduce((n, [s])` — const, line 462
- `let col = Math.round(cx - total / 2)` — let, line 463
- `let diffRow = Math.round(cy) + 7` — let, line 470
- `let html = ""` — let, line 484
- `let run = ""` — let, line 486
- `let cur = 0` — let, line 487
- `const flush = ()` — const, line 488
- `const i = r * cols + c` — const, line 494
- `const color = cgrid[i]` — const, line 495
- `function esc(s: string): string` — function, line 533
- `function formatElapsed(startedAt: string, endedAt: string): string` — function, line 539
- `const ms = new Date(endedAt).getTime() - new Date(startedAt).getTime()` — const, line 540
- `const totalSeconds = Math.round(ms / 1000)` — const, line 542
- `const minutes = Math.floor(totalSeconds / 60)` — const, line 543
- `const seconds = totalSeconds % 60` — const, line 544

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `SessionFinishHud`; references `SessionFinishHud`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SessionEndSummary`, `SessionTopicDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/nextPractice|src/app/nextPractice.ts]] — import-or-re-export; imports `nextPracticeLines`
- [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]] — import-or-re-export; imports `simplePracticeFeedback`
- [[Reference/Desktop/TypeScript/components/PlainParts|src/components/PlainParts.tsx]] — import-or-re-export; imports `PrimaryAction`, `quietLine`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/copy/denyList.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/SessionFinishHud.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/components/SessionFinishHud.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/SessionFinishHud.tsx](../../../../../../apps/learnloop-tauri/src/components/SessionFinishHud.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
