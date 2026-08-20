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
source_commit: "d0f25b2598a77dcc5236118dad9e1af2422d8682"
source_commit_timestamp: "2026-08-16T20:45:34-04:00"
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
| Source lines | 434 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `d0f25b2598a77dcc5236118dad9e1af2422d8682` |
| Commit timestamp | `2026-08-16T20:45:34-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/SessionFinishHud|src/components/SessionFinishHud.tsx]]

## Public API

- `export function SessionFinishHud(` — function, line 61

## Internal implementation anchors

- `const EXIT_MS = 520` — const, line 15
- `const CHAR_W = 7` — const, line 16
- `const CHAR_H = 12` — const, line 17
- `const ACTIVE_FRAME_MS = 33` — const, line 18
- `const COMPLETE_FRAME_MS = 66` — const, line 19
- `const GLYPHS: Record<string, string[]> =` — const, line 22
- `const C =` — const, line 35
- `type ColorId = (typeof C)[keyof typeof C]` — type, line 46
- `const COLOR_CLASS: Record<ColorId, string> =` — const, line 48
- `const NEEDS_ESCAPE_RE = /[&<>]/` — const, line 58
- `const HTML_ESCAPE_RE = /[&<>]/g` — const, line 59
- `const active = summary !== null` — const, line 68
- `const closingRef = useRef(false)` — const, line 70
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 71
- `const preRef = useRef<HTMLPreElement>(null)` — const, line 72
- `const requestClose = useCallback(()` — const, line 80
- `const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches` — const, line 83
- `const onKey = (event: KeyboardEvent)` — const, line 94
- `const container = containerRef.current` — const, line 107
- `const pre = preRef.current` — const, line 108
- `const aspect = CHAR_W / CHAR_H` — const, line 111
- `const code = summary.sessionId.slice(-6).toUpperCase()` — const, line 112
- `const logNo = (parseInt(summary.sessionId.slice(-5), 36) % 9000) + 1000` — const, line 113
- `const elapsed = formatElapsed(summary.startedAt, summary.endedAt)` — const, line 114
- `const attempts = String(summary.attemptsRecorded)` — const, line 115
- `const items = String(summary.itemsReviewed)` — const, line 116
- `const followups = summary.followupsQueued != null ? String(summary.followupsQueued) : "—"` — const, line 117
- `const streakDays = `$` — const, line 118
- `const streakActive = summary.streak.activeToday` — const, line 119
- `const bestStreak = `BEST STREAK $` — const, line 120
- `const facetsDemonstrated = summary.facetsDemonstrated ?? 0` — const, line 125
- `const movedUp = summary.predictionsMoved?.up ?? 0` — const, line 126
- `const movedDown = summary.predictionsMoved?.down ?? 0` — const, line 127
- `const corrections = summary.corrections ?? 0` — const, line 128
- `const mscResolved = summary.misconceptionsTouched?.resolved ?? 0` — const, line 129
- `const mscReturned = summary.misconceptionsTouched?.returned ?? 0` — const, line 130
- `const coldDone = summary.coldChecksCompleted ?? 0` — const, line 134
- `const coldPassed = summary.coldChecksPassed ?? 0` — const, line 135
- `type DiffLine =` — type, line 139
- `const candidates: DiffLine[] = []` — const, line 140
- `const forced = candidates.filter((c)` — const, line 164
- `const optional = candidates.filter((c)` — const, line 165
- `const diffLines = [...forced, ...optional].slice(0, 3)` — const, line 166
- `const hasMoreDiff = candidates.length > diffLines.length` — const, line 167
- `let cols = 0` — let, line 169
- `let rows = 0` — let, line 170
- `let grid: string[] = []` — let, line 171
- `let cgrid = new Uint8Array(0)` — let, line 172
- `const resize = ()` — const, line 173
- `const rect = container.getBoundingClientRect()` — const, line 174
- `const nextCols = Math.max(40, Math.floor(rect.width / CHAR_W))` — const, line 175
- `const nextRows = Math.max(24, Math.floor(rect.height / CHAR_H))` — const, line 176
- `const ro = new ResizeObserver(resize)` — const, line 184
- `const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches` — const, line 187
- `let raf = 0` — let, line 188
- `let startTs = 0` — let, line 189
- `let lastDrawTs = 0` — let, line 190
- `const draw = (ts: number)` — const, line 192
- `const sinceStart = ts - startTs` — const, line 195
- `const pt = Math.min(1, Math.max(0, (sinceStart - 300) / 2050))` — const, line 197
- `const pct = reduce ? 100 : Math.round((1 - Math.pow(1 - pt, 3)) * 100)` — const, line 198
- `const f = pct / 100` — const, line 199
- `const done = pct >= 100` — const, line 200
- `const phase = reduce ? 0 : ts / 1000` — const, line 201
- `const frameMs = done ? COMPLETE_FRAME_MS : ACTIVE_FRAME_MS` — const, line 203
- `const set = (r: number, c: number, ch: string, color: ColorId)` — const, line 212
- `const i = r * cols + c` — const, line 214
- `const put = (r: number, c: number, str: string, color: ColorId)` — const, line 218
- `const putCenter = (r: number, str: string, color: ColorId)` — const, line 221
- `const cx = (cols - 1) / 2` — const, line 225
- `const cy = (rows - 1) / 2` — const, line 226
- `const maxR = Math.min(cx - 2, (cy - 2) / aspect)` — const, line 227
- `const rMeter = maxR * 0.82` — const, line 228
- `const rOuter = maxR * 0.99` — const, line 229
- `const rClaw = maxR * 0.9` — const, line 230
- `const rInner = maxR * 0.6` — const, line 231
- `const place = (rad: number, ang: number, ch: string, color: ColorId)` — const, line 233
- `const ringSteps = (rad: number)` — const, line 236
- `const steps = ringSteps(rad)` — const, line 240
- `const prog = ((phase / 3.4) + off) % 1` — const, line 250
- `const rad = maxR * (0.14 + prog * 0.72)` — const, line 251
- `const shade = prog < 0.7 ? C.amberLow : C.faintDot` — const, line 252
- `const steps = ringSteps(rad)` — const, line 253
- `const base = phase * 0.18 + k * 0.25` — const, line 263
- `const steps = ringSteps(rMeter)` — const, line 271
- `const t = s / steps` — const, line 273
- `const ang = -Math.PI / 2 + t * 2 * Math.PI` — const, line 274
- `const lit = t <= f` — const, line 275
- `const head = !done && lit && f - t < 2.5 / steps` — const, line 276
- `const teleRows = Math.min(10, Math.floor(rows * 0.34))` — const, line 295
- `const teleTop = Math.round(cy - teleRows / 2)` — const, line 296
- `const onL = !reduce && Math.sin(phase * 3 - i * 0.6) > 0.2` — const, line 298
- `const onR = !reduce && Math.sin(phase * 3 - i * 0.6 + 1.5) > 0.2` — const, line 299
- `const xr = Math.round(cy - rInner * aspect)` — const, line 305
- `const logStr = `LOG #$` — const, line 316
- `const status = done ? "● STATUS OK" : "○ FINALIZING"` — const, line 319
- `const digits = String(pct)` — const, line 326
- `const blockW = digits.length * 5 - 1` — const, line 327
- `const startCol = Math.round(cx - (blockW - 1) / 2)` — const, line 328
- `const topRow = Math.round(cy) - 2` — const, line 329
- `const glyph = GLYPHS[digits[di]]` — const, line 331
- `const segs: Array<[string, ColorId]> = [ ["ATTEMPTS ", C.faint], [attempts, C.amber], [" ", C.faint], ["ITEMS ", C.faint], [items, C.amber], [" ", C.faint], ["FOLLOW-UPS ", C.faint], [followups, C.green], [" ", C.faint], ["STREAK ", C.faint], [streakDays, str…` — const, line 344
- `const total = segs.reduce((n, [s])` — const, line 350
- `let col = Math.round(cx - total / 2)` — let, line 351
- `let diffRow = Math.round(cy) + 7` — let, line 358
- `let html = ""` — let, line 372
- `let run = ""` — let, line 374
- `let cur = 0` — let, line 375
- `const flush = ()` — const, line 376
- `const i = r * cols + c` — const, line 382
- `const color = cgrid[i]` — const, line 383
- `function esc(s: string): string` — function, line 421
- `function formatElapsed(startedAt: string, endedAt: string): string` — function, line 427
- `const ms = new Date(endedAt).getTime() - new Date(startedAt).getTime()` — const, line 428
- `const totalSeconds = Math.round(ms / 1000)` — const, line 430
- `const minutes = Math.floor(totalSeconds / 60)` — const, line 431
- `const seconds = totalSeconds % 60` — const, line 432

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `SessionFinishHud`; references `SessionFinishHud`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SessionEndSummary`

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

1. Modify [apps/learnloop-tauri/src/components/SessionFinishHud.tsx](../../../../../../apps/learnloop-tauri/src/components/SessionFinishHud.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
