---
title: "Desktop module · src/screens/desks/goal/model.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.goal.model"
language: "TypeScript"
area: "TypeScript/screens/desks/goal"
source_path: "apps/learnloop-tauri/src/screens/desks/goal/model.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/goal/model.ts"
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

# `src/screens/desks/goal/model.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/goal/_area|TypeScript/screens/desks/goal]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `LensLevel`, `LEVEL_LABEL`, `MarkKind`, `markKind` and related exports within the desktop's TypeScript/screens/desks/goal ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/goal/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/model.ts) |
| Source lines | 263 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/goal/_area|TypeScript/screens/desks/goal]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/goal/model|src/screens/desks/goal/model.ts]]

## Public API

- `export type LensLevel = GoalLensSectionDto["level"]` — type, line 6
- `export const LEVEL_LABEL: Record<LensLevel, string> =` — const, line 9
- `export type MarkKind = "core" | "sup" | "skip" | "later" | "shown" | "partial"` — type, line 20
- `export function markKind(level: LensLevel): MarkKind | null` — function, line 22
- `export interface LensIndex` — interface, line 35
- `export function indexLens(lens: GoalLensDto | null | undefined): LensIndex | null` — function, line 43
- `export function levelsInRange(index: LensIndex | null, spanIds: readonly string[]): GoalLensSectionDto[]` — function, line 58
- `export function mostNeededSpan(index: LensIndex, spanIds: readonly string[]): string | undefined` — function, line 77
- `export function noneNeeded(sections: readonly GoalLensSectionDto[]): boolean` — function, line 89
- `export function isDimmed(section: GoalLensSectionDto | undefined, dimOn: boolean): boolean` — function, line 96
- `export function deeperDepthLabel(band: GoalBandDto | null): string | null` — function, line 101
- `export function whyLevelLine(section: GoalLensSectionDto, band: GoalBandDto | null): string` — function, line 108
- `export function goalShort(band: GoalBandDto | null): string` — function, line 117
- `export function goalLabel(band: GoalBandDto): string` — function, line 123
- `export function formatDay(stamp: string): string` — function, line 128
- `export function countsLine(band: GoalBandDto): string` — function, line 135
- `export function nextLine(band: GoalBandDto):` — function, line 148
- `export function hereLine(index: LensIndex | null, readingSpan: string | null, where: string | null, band: GoalBandDto | null):` — function, line 157
- `export interface Callout` — interface, line 180
- `export function calloutFor(section: GoalLensSectionDto): Callout | null` — function, line 186
- `export function dotClasses(dot: GoalBandLoDto, here: string | null): string` — function, line 205
- `export function dotTitle(dot: GoalBandLoDto): string` — function, line 212
- `export function readOrNot(read: boolean): string` — function, line 217
- `export function truncate(text: string | null, limit: number): string | null` — function, line 222
- `export interface ShelfGoal` — interface, line 229
- `export function shelfGoal(index: LensIndex | null): ShelfGoal | null` — function, line 235

## Internal implementation anchors

- `const bySpan = new Map<string, GoalLensSectionDto>()` — const, line 45
- `const starts = new Map<string, GoalLensSectionDto>()` — const, line 46
- `const seen = new Set<string>()` — const, line 60
- `const out: GoalLensSectionDto[] = []` — const, line 61
- `const section = index.bySpan.get(span)` — const, line 63
- `const NEED_RANK: Record<string, number> =` — const, line 75
- `let best:` — let, line 78
- `const section = index.bySpan.get(spanId)` — const, line 80
- `const rank = section ? (section.dim ? 10 : 0) + (NEED_RANK[section.level] ?? NEED_RANK.unmapped) : NEED_RANK.unmapped` — const, line 81
- `const depths = band?.depths ?? []` — const, line 102
- `const at = depths.findIndex((depth)` — const, line 103
- `const deeper = deeperDepthLabel(band)` — const, line 110
- `const title = band?.goal.title?.trim()` — const, line 118
- `const due = band.goal.dueAt ? `due $` — const, line 124
- `const parsed = new Date(stamp)` — const, line 129
- `const counts = band.counts` — const, line 136
- `const parts = [ counts.demonstrated ? `$` — const, line 138
- `const n = counts.learningObjects` — const, line 143
- `const next = band.next` — const, line 149
- `const section = index.bySpan.get(readingSpan)` — const, line 160
- `const place = where || section?.title || ""` — const, line 161
- `const lo = section.learningObjects.find((entry)` — const, line 168
- `const dot = band?.learningObjects?.find((each)` — const, line 169
- `const tag = section.level === "later" ? "later" : section.level === "already_shown" ? "already shown" : section.reasonKey === "alternate" ? "another way" : lo?.kind === "prerequisite" ? "prerequisite" : section.level === "partial" ? "partly mapped" : null` — const, line 170
- `const lo = section.learningObjects.find((entry)` — const, line 188
- `const quoted = lo.title ? `“$` — const, line 191
- `const sections = index.sections` — const, line 237
- `const total = sections.reduce((sum, section)` — const, line 241
- `const ranges: Array<[number, number]> = []` — const, line 242
- `let at = 0` — let, line 243
- `const from = at / total` — const, line 245
- `const last = ranges[ranges.length - 1]` — const, line 248
- `const primaries = new Set(sections.filter((section)` — const, line 253

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/goal/GoalBand|src/screens/desks/goal/GoalBand.tsx]] — import-or-re-export: `countsLine`, `dotClasses`, `dotTitle`, `formatDay`, `goalLabel`, `nextLine`; references `countsLine`, `dotClasses`, `dotTitle`, `formatDay`, `goalLabel`, `nextLine`
- [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]] — import-or-re-export: `LensIndex`, `ShelfGoal`, `hereLine`, `markKind`, `shelfGoal`; references `LensIndex`, `ShelfGoal`, `hereLine`, `markKind`, `shelfGoal`
- [[Reference/Desktop/TypeScript/screens/desks/goal/PathView|src/screens/desks/goal/PathView.tsx]] — import-or-re-export: `formatDay`, `goalLabel`; references `formatDay`, `goalLabel`
- [[Reference/Desktop/TypeScript/screens/desks/goal/controller|src/screens/desks/goal/controller.ts]] — import-or-re-export: `LensIndex`, `indexLens`; references `LensIndex`, `indexLens`
- [[Reference/Desktop/TypeScript/screens/desks/goal/marks|src/screens/desks/goal/marks.tsx]] — import-or-re-export: `LensIndex`, `calloutFor`, `goalShort`, `isDimmed`, `markKind`, `mostNeededSpan`, `noneNeeded`, `whyLevelLine`; references `LensIndex`, `calloutFor`, `goalShort`, `isDimmed`, `markKind`, `mostNeededSpan`, `noneNeeded`, `whyLevelLine`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `GoalBandDto`, `GoalBandLoDto`, `GoalLensDto`, `GoalLensSectionDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Goals Exams and Certification Workflow|Goals, Exams, and Certification Workflow]] — owns the end-to-end goal path.
- [[Concepts/Goals and Certification|Goals and Certification]] — owns goal and certification semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/goal/watch.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/watch.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/shelf.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/shelf.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/protection.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/protection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/model.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/goal/components.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/components.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_goals.py](../../../../../../../../tests/test_sidecar_goals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_exams.py](../../../../../../../../tests/test_sidecar_exams.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_goal_projection.py](../../../../../../../../tests/test_goal_projection.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_exam_session.py](../../../../../../../../tests/test_exam_session.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/goal/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/model.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
