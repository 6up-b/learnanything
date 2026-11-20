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
| Source lines | 538 |
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
- `export function sessionTopicLine(topic: SessionTopicDto): string` — function, line 98

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
- `function SessionFinishCard(` — function, line 103
- `const onKey = (event: KeyboardEvent)` — const, line 107
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 110
- `const topics = summary.topics ?? []` — const, line 119
- `function ClassicSessionFinishHud(` — function, line 164
- `const active = summary !== null` — const, line 171
- `const closingRef = useRef(false)` — const, line 173
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 174
- `const preRef = useRef<HTMLPreElement>(null)` — const, line 175
- `const requestClose = useCallback(()` — const, line 183
- `const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches` — const, line 186
- `const onKey = (event: KeyboardEvent)` — const, line 197
- `const container = containerRef.current` — const, line 211
- `const pre = preRef.current` — const, line 212
- `const aspect = CHAR_W / CHAR_H` — const, line 215
- `const code = summary.sessionId.slice(-6).toUpperCase()` — const, line 216
- `const logNo = (parseInt(summary.sessionId.slice(-5), 36) % 9000) + 1000` — const, line 217
- `const elapsed = formatElapsed(summary.startedAt, summary.endedAt)` — const, line 218
- `const attempts = String(summary.attemptsRecorded)` — const, line 219
- `const items = String(summary.itemsReviewed)` — const, line 220
- `const followups = summary.followupsQueued != null ? String(summary.followupsQueued) : "—"` — const, line 221
- `const streakDays = `$` — const, line 222
- `const streakActive = summary.streak.activeToday` — const, line 223
- `const bestStreak = `BEST STREAK $` — const, line 224
- `const facetsDemonstrated = summary.facetsDemonstrated ?? 0` — const, line 229
- `const movedUp = summary.predictionsMoved?.up ?? 0` — const, line 230
- `const movedDown = summary.predictionsMoved?.down ?? 0` — const, line 231
- `const corrections = summary.corrections ?? 0` — const, line 232
- `const mscResolved = summary.misconceptionsTouched?.resolved ?? 0` — const, line 233
- `const mscReturned = summary.misconceptionsTouched?.returned ?? 0` — const, line 234
- `const coldDone = summary.coldChecksCompleted ?? 0` — const, line 238
- `const coldPassed = summary.coldChecksPassed ?? 0` — const, line 239
- `type DiffLine =` — type, line 243
- `const candidates: DiffLine[] = []` — const, line 244
- `const forced = candidates.filter((c)` — const, line 268
- `const optional = candidates.filter((c)` — const, line 269
- `const diffLines = [...forced, ...optional].slice(0, 3)` — const, line 270
- `const hasMoreDiff = candidates.length > diffLines.length` — const, line 271
- `let cols = 0` — let, line 273
- `let rows = 0` — let, line 274
- `let grid: string[] = []` — let, line 275
- `let cgrid = new Uint8Array(0)` — let, line 276
- `const resize = ()` — const, line 277
- `const rect = container.getBoundingClientRect()` — const, line 278
- `const nextCols = Math.max(40, Math.floor(rect.width / CHAR_W))` — const, line 279
- `const nextRows = Math.max(24, Math.floor(rect.height / CHAR_H))` — const, line 280
- `const ro = new ResizeObserver(resize)` — const, line 288
- `const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches` — const, line 291
- `let raf = 0` — let, line 292
- `let startTs = 0` — let, line 293
- `let lastDrawTs = 0` — let, line 294
- `const draw = (ts: number)` — const, line 296
- `const sinceStart = ts - startTs` — const, line 299
- `const pt = Math.min(1, Math.max(0, (sinceStart - 300) / 2050))` — const, line 301
- `const pct = reduce ? 100 : Math.round((1 - Math.pow(1 - pt, 3)) * 100)` — const, line 302
- `const f = pct / 100` — const, line 303
- `const done = pct >= 100` — const, line 304
- `const phase = reduce ? 0 : ts / 1000` — const, line 305
- `const frameMs = done ? COMPLETE_FRAME_MS : ACTIVE_FRAME_MS` — const, line 307
- `const set = (r: number, c: number, ch: string, color: ColorId)` — const, line 316
- `const i = r * cols + c` — const, line 318
- `const put = (r: number, c: number, str: string, color: ColorId)` — const, line 322
- `const putCenter = (r: number, str: string, color: ColorId)` — const, line 325
- `const cx = (cols - 1) / 2` — const, line 329
- `const cy = (rows - 1) / 2` — const, line 330
- `const maxR = Math.min(cx - 2, (cy - 2) / aspect)` — const, line 331
- `const rMeter = maxR * 0.82` — const, line 332
- `const rOuter = maxR * 0.99` — const, line 333
- `const rClaw = maxR * 0.9` — const, line 334
- `const rInner = maxR * 0.6` — const, line 335
- `const place = (rad: number, ang: number, ch: string, color: ColorId)` — const, line 337
- `const ringSteps = (rad: number)` — const, line 340
- `const steps = ringSteps(rad)` — const, line 344
- `const prog = ((phase / 3.4) + off) % 1` — const, line 354
- `const rad = maxR * (0.14 + prog * 0.72)` — const, line 355
- `const shade = prog < 0.7 ? C.amberLow : C.faintDot` — const, line 356
- `const steps = ringSteps(rad)` — const, line 357
- `const base = phase * 0.18 + k * 0.25` — const, line 367
- `const steps = ringSteps(rMeter)` — const, line 375
- `const t = s / steps` — const, line 377
- `const ang = -Math.PI / 2 + t * 2 * Math.PI` — const, line 378
- `const lit = t <= f` — const, line 379
- `const head = !done && lit && f - t < 2.5 / steps` — const, line 380
- `const teleRows = Math.min(10, Math.floor(rows * 0.34))` — const, line 399
- `const teleTop = Math.round(cy - teleRows / 2)` — const, line 400
- `const onL = !reduce && Math.sin(phase * 3 - i * 0.6) > 0.2` — const, line 402
- `const onR = !reduce && Math.sin(phase * 3 - i * 0.6 + 1.5) > 0.2` — const, line 403
- `const xr = Math.round(cy - rInner * aspect)` — const, line 409
- `const logStr = `LOG #$` — const, line 420
- `const status = done ? "● STATUS OK" : "○ FINALIZING"` — const, line 423
- `const digits = String(pct)` — const, line 430
- `const blockW = digits.length * 5 - 1` — const, line 431
- `const startCol = Math.round(cx - (blockW - 1) / 2)` — const, line 432
- `const topRow = Math.round(cy) - 2` — const, line 433
- `const glyph = GLYPHS[digits[di]]` — const, line 435
- `const segs: Array<[string, ColorId]> = [ ["ATTEMPTS ", C.faint], [attempts, C.amber], [" ", C.faint], ["ITEMS ", C.faint], [items, C.amber], [" ", C.faint], ["FOLLOW-UPS ", C.faint], [followups, C.green], [" ", C.faint], ["STREAK ", C.faint], [streakDays, str…` — const, line 448
- `const total = segs.reduce((n, [s])` — const, line 454
- `let col = Math.round(cx - total / 2)` — let, line 455
- `let diffRow = Math.round(cy) + 7` — let, line 462
- `let html = ""` — let, line 476
- `let run = ""` — let, line 478
- `let cur = 0` — let, line 479
- `const flush = ()` — const, line 480
- `const i = r * cols + c` — const, line 486
- `const color = cgrid[i]` — const, line 487
- `function esc(s: string): string` — function, line 525
- `function formatElapsed(startedAt: string, endedAt: string): string` — function, line 531
- `const ms = new Date(endedAt).getTime() - new Date(startedAt).getTime()` — const, line 532
- `const totalSeconds = Math.round(ms / 1000)` — const, line 534
- `const minutes = Math.floor(totalSeconds / 60)` — const, line 535
- `const seconds = totalSeconds % 60` — const, line 536

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `SessionFinishHud`; references `SessionFinishHud`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SessionEndSummary`, `SessionTopicDto`
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
