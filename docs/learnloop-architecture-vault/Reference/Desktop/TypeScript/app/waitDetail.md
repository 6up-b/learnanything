---
title: "Desktop module · src/app/waitDetail.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.waitDetail"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/waitDetail.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/waitDetail.ts"
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

# `src/app/waitDetail.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `WaitDetail`, `waitDetailOf`, `WaitDetailWords`, `WaitClock` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/waitDetail.ts](../../../../../../apps/learnloop-tauri/src/app/waitDetail.ts) |
| Source lines | 218 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] → [[Reference/Desktop/TypeScript/app/waitDetail|src/app/waitDetail.ts]]

## Public API

- `export type WaitDetail =` — type, line 19
- `export function waitDetailOf(cause: TodayCause | null): WaitDetail | null` — function, line 21
- `export interface WaitDetailWords` — interface, line 28
- `export type WaitClock = "ago" | "at"` — type, line 35
- `export const WAIT_DETAILS_LABEL = "details"` — const, line 38
- `export const FIRST_QUESTIONS_TIME = "The first questions can take a few minutes."` — const, line 41
- `export function replyGrew(delivery: WaitDeliveryDto | null | undefined, previous: WaitDeliveryDto | null | undefined): boolean` — function, line 74
- `export function buildWaitWords(detail: BuildDetailDto, options:` — function, line 150
- `export function writingWaitWords(detail: WritingDetailDto, options:` — function, line 174
- `export function useWaitWords(detail: WaitDetail | null, clock: WaitClock): WaitDetailWords | null` — function, line 201

## Internal implementation anchors

- `function parse(value: string | null | undefined): number | null` — function, line 43
- `const at = Date.parse(value)` — const, line 45
- `function span(seconds: number): string` — function, line 50
- `const whole = Math.max(0, Math.floor(seconds))` — const, line 52
- `const minutes = Math.floor(seconds / 60)` — const, line 55
- `function clockTime(at: number): string` — function, line 59
- `function when(value: string | null | undefined, asOf: string | null, clock: WaitClock): string | null` — function, line 64
- `const at = parse(value)` — const, line 65
- `const now = parse(asOf)` — const, line 68
- `function deliveryPhrase(delivery: WaitDeliveryDto | null, asOf: string | null, clock: WaitClock, grew: boolean): string | null` — function, line 81
- `const last = when(delivery.lastOutputAt, asOf, clock)` — const, line 86
- `const sent = when(delivery.requestSentAt, asOf, clock)` — const, line 89
- `const received = when(delivery.replyReceivedAt, asOf, clock)` — const, line 92
- `function timeLine(started: string | null, asOf: string | null, delivery: WaitDeliveryDto | null, clock: WaitClock, grew: boolean): string | null` — function, line 96
- `const since = when(started, asOf, clock)` — const, line 97
- `const parts = [since ? `Started $` — const, line 98
- `const line = parts.join(" · ")` — const, line 100
- `function countWords(count: number, one: string, many: string): string` — function, line 104
- `function minutesWords(minutes: number): string` — function, line 108
- `const whole = Math.round(minutes)` — const, line 110
- `function buildMeasured(measured: WaitMeasuredDto | null): string` — function, line 114
- `function buildStage(detail: BuildDetailDto): string` — function, line 121
- `const inventory = detail.inventory` — const, line 126
- `const part = detail.synthesis` — const, line 132
- `const which = part && part.part !== null && part.parts !== null && part.parts > 0 ? ` · part $` — const, line 133
- `const pass = part?.pass === "evidence" ? " · looking at the passages it asked for" : part?.pass === "plan_reused" ? " · kept from before" : ""` — const, line 134
- `const stage = buildStage(detail)` — const, line 151
- `const lines = [detail.retry ? `Trying again · $` — const, line 152
- `const time = timeLine(detail.startedAt, detail.asOf, detail.delivery, options.clock, options.grew)` — const, line 153
- `const details: string[] = []` — const, line 155
- `const reused = detail.inventory?.reused ?? 0` — const, line 157
- `const lines: string[] = []` — const, line 175
- `const details: string[] = []` — const, line 176
- `const topic = detail.topic` — const, line 180
- `const which = topic && topic.index !== null && topic.total !== null ? `Writing topic $` — const, line 181
- `const time = timeLine(detail.topicStartedAt ?? detail.startedAt, detail.asOf, detail.delivery, options.clock, options.grew)` — const, line 186
- `const previous = useRef<` — const, line 202
- `const shown = useRef<` — const, line 203
- `const delivery = detail.value.delivery` — const, line 209
- `const before = previous.current && previous.current.kind === detail.kind ? previous.current.delivery : null` — const, line 212
- `const grew = shown.current.grew` — const, line 216

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `WAIT_DETAILS_LABEL`, `useWaitWords`, `waitDetailOf`; references `WAIT_DETAILS_LABEL`, `useWaitWords`, `waitDetailOf`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `BuildDetailDto`, `WaitDeliveryDto`, `WaitMeasuredDto`, `WritingDetailDto`
- [[Reference/Desktop/TypeScript/app/todayCause|src/app/todayCause.ts]] — import-or-re-export; imports `TodayCause`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/copy/denyList.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/waitDetail.test.ts](../../../../../../apps/learnloop-tauri/src/app/waitDetail.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/waitDetail.ts](../../../../../../apps/learnloop-tauri/src/app/waitDetail.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
