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
| Source lines | 532 |
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

- `export function SessionFinishHud(` — function, line 71
- `export function sessionLengthLine(summary: SessionEndSummary): string` — function, line 89

## Internal implementation anchors

- `const EXIT_MS = 520` — const, line 19
- `const CHAR_W = 7` — const, line 20
- `const CHAR_H = 12` — const, line 21
- `const ACTIVE_FRAME_MS = 33` — const, line 22
- `const COMPLETE_FRAME_MS = 66` — const, line 23
- `const GLYPHS: Record<string, string[]> =` — const, line 26
- `const C =` — const, line 39
- `type ColorId = (typeof C)[keyof typeof C]` — type, line 50
- `const COLOR_CLASS: Record<ColorId, string> =` — const, line 52
- `const NEEDS_ESCAPE_RE = /[&<>]/` — const, line 62
- `const HTML_ESCAPE_RE = /[&<>]/g` — const, line 63
- `function plural(count: number, one: string, many: string): string` — function, line 82
- `const ms = new Date(summary.endedAt).getTime() - new Date(summary.startedAt).getTime()` — const, line 90
- `const minutes = Number.isFinite(ms) && ms > 0 ? Math.max(1, Math.round(ms / 60000)) : 1` — const, line 91
- `function SessionFinishCard(` — function, line 95
- `const onKey = (event: KeyboardEvent)` — const, line 99
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 102
- `const topics = summary.topics ?? []` — const, line 111
- `function ClassicSessionFinishHud(` — function, line 158
- `const active = summary !== null` — const, line 165
- `const closingRef = useRef(false)` — const, line 167
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 168
- `const preRef = useRef<HTMLPreElement>(null)` — const, line 169
- `const requestClose = useCallback(()` — const, line 177
- `const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches` — const, line 180
- `const onKey = (event: KeyboardEvent)` — const, line 191
- `const container = containerRef.current` — const, line 205
- `const pre = preRef.current` — const, line 206
- `const aspect = CHAR_W / CHAR_H` — const, line 209
- `const code = summary.sessionId.slice(-6).toUpperCase()` — const, line 210
- `const logNo = (parseInt(summary.sessionId.slice(-5), 36) % 9000) + 1000` — const, line 211
- `const elapsed = formatElapsed(summary.startedAt, summary.endedAt)` — const, line 212
- `const attempts = String(summary.attemptsRecorded)` — const, line 213
- `const items = String(summary.itemsReviewed)` — const, line 214
- `const followups = summary.followupsQueued != null ? String(summary.followupsQueued) : "—"` — const, line 215
- `const streakDays = `$` — const, line 216
- `const streakActive = summary.streak.activeToday` — const, line 217
- `const bestStreak = `BEST STREAK $` — const, line 218
- `const facetsDemonstrated = summary.facetsDemonstrated ?? 0` — const, line 223
- `const movedUp = summary.predictionsMoved?.up ?? 0` — const, line 224
- `const movedDown = summary.predictionsMoved?.down ?? 0` — const, line 225
- `const corrections = summary.corrections ?? 0` — const, line 226
- `const mscResolved = summary.misconceptionsTouched?.resolved ?? 0` — const, line 227
- `const mscReturned = summary.misconceptionsTouched?.returned ?? 0` — const, line 228
- `const coldDone = summary.coldChecksCompleted ?? 0` — const, line 232
- `const coldPassed = summary.coldChecksPassed ?? 0` — const, line 233
- `type DiffLine =` — type, line 237
- `const candidates: DiffLine[] = []` — const, line 238
- `const forced = candidates.filter((c)` — const, line 262
- `const optional = candidates.filter((c)` — const, line 263
- `const diffLines = [...forced, ...optional].slice(0, 3)` — const, line 264
- `const hasMoreDiff = candidates.length > diffLines.length` — const, line 265
- `let cols = 0` — let, line 267
- `let rows = 0` — let, line 268
- `let grid: string[] = []` — let, line 269
- `let cgrid = new Uint8Array(0)` — let, line 270
- `const resize = ()` — const, line 271
- `const rect = container.getBoundingClientRect()` — const, line 272
- `const nextCols = Math.max(40, Math.floor(rect.width / CHAR_W))` — const, line 273
- `const nextRows = Math.max(24, Math.floor(rect.height / CHAR_H))` — const, line 274
- `const ro = new ResizeObserver(resize)` — const, line 282
- `const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches` — const, line 285
- `let raf = 0` — let, line 286
- `let startTs = 0` — let, line 287
- `let lastDrawTs = 0` — let, line 288
- `const draw = (ts: number)` — const, line 290
- `const sinceStart = ts - startTs` — const, line 293
- `const pt = Math.min(1, Math.max(0, (sinceStart - 300) / 2050))` — const, line 295
- `const pct = reduce ? 100 : Math.round((1 - Math.pow(1 - pt, 3)) * 100)` — const, line 296
- `const f = pct / 100` — const, line 297
- `const done = pct >= 100` — const, line 298
- `const phase = reduce ? 0 : ts / 1000` — const, line 299
- `const frameMs = done ? COMPLETE_FRAME_MS : ACTIVE_FRAME_MS` — const, line 301
- `const set = (r: number, c: number, ch: string, color: ColorId)` — const, line 310
- `const i = r * cols + c` — const, line 312
- `const put = (r: number, c: number, str: string, color: ColorId)` — const, line 316
- `const putCenter = (r: number, str: string, color: ColorId)` — const, line 319
- `const cx = (cols - 1) / 2` — const, line 323
- `const cy = (rows - 1) / 2` — const, line 324
- `const maxR = Math.min(cx - 2, (cy - 2) / aspect)` — const, line 325
- `const rMeter = maxR * 0.82` — const, line 326
- `const rOuter = maxR * 0.99` — const, line 327
- `const rClaw = maxR * 0.9` — const, line 328
- `const rInner = maxR * 0.6` — const, line 329
- `const place = (rad: number, ang: number, ch: string, color: ColorId)` — const, line 331
- `const ringSteps = (rad: number)` — const, line 334
- `const steps = ringSteps(rad)` — const, line 338
- `const prog = ((phase / 3.4) + off) % 1` — const, line 348
- `const rad = maxR * (0.14 + prog * 0.72)` — const, line 349
- `const shade = prog < 0.7 ? C.amberLow : C.faintDot` — const, line 350
- `const steps = ringSteps(rad)` — const, line 351
- `const base = phase * 0.18 + k * 0.25` — const, line 361
- `const steps = ringSteps(rMeter)` — const, line 369
- `const t = s / steps` — const, line 371
- `const ang = -Math.PI / 2 + t * 2 * Math.PI` — const, line 372
- `const lit = t <= f` — const, line 373
- `const head = !done && lit && f - t < 2.5 / steps` — const, line 374
- `const teleRows = Math.min(10, Math.floor(rows * 0.34))` — const, line 393
- `const teleTop = Math.round(cy - teleRows / 2)` — const, line 394
- `const onL = !reduce && Math.sin(phase * 3 - i * 0.6) > 0.2` — const, line 396
- `const onR = !reduce && Math.sin(phase * 3 - i * 0.6 + 1.5) > 0.2` — const, line 397
- `const xr = Math.round(cy - rInner * aspect)` — const, line 403
- `const logStr = `LOG #$` — const, line 414
- `const status = done ? "● STATUS OK" : "○ FINALIZING"` — const, line 417
- `const digits = String(pct)` — const, line 424
- `const blockW = digits.length * 5 - 1` — const, line 425
- `const startCol = Math.round(cx - (blockW - 1) / 2)` — const, line 426
- `const topRow = Math.round(cy) - 2` — const, line 427
- `const glyph = GLYPHS[digits[di]]` — const, line 429
- `const segs: Array<[string, ColorId]> = [ ["ATTEMPTS ", C.faint], [attempts, C.amber], [" ", C.faint], ["ITEMS ", C.faint], [items, C.amber], [" ", C.faint], ["FOLLOW-UPS ", C.faint], [followups, C.green], [" ", C.faint], ["STREAK ", C.faint], [streakDays, str…` — const, line 442
- `const total = segs.reduce((n, [s])` — const, line 448
- `let col = Math.round(cx - total / 2)` — let, line 449
- `let diffRow = Math.round(cy) + 7` — let, line 456
- `let html = ""` — let, line 470
- `let run = ""` — let, line 472
- `let cur = 0` — let, line 473
- `const flush = ()` — const, line 474
- `const i = r * cols + c` — const, line 480
- `const color = cgrid[i]` — const, line 481
- `function esc(s: string): string` — function, line 519
- `function formatElapsed(startedAt: string, endedAt: string): string` — function, line 525
- `const ms = new Date(endedAt).getTime() - new Date(startedAt).getTime()` — const, line 526
- `const totalSeconds = Math.round(ms / 1000)` — const, line 528
- `const minutes = Math.floor(totalSeconds / 60)` — const, line 529
- `const seconds = totalSeconds % 60` — const, line 530

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `SessionFinishHud`; references `SessionFinishHud`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SessionEndSummary`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]] — import-or-re-export; imports `simplePracticeFeedback`
- [[Reference/Desktop/TypeScript/components/PlainParts|src/components/PlainParts.tsx]] — import-or-re-export; imports `PrimaryAction`, `quietLine`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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
