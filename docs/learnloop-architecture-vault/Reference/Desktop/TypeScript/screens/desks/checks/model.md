---
title: "Desktop module · src/screens/desks/checks/model.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.checks.model"
language: "TypeScript"
area: "TypeScript/screens/desks/checks"
source_path: "apps/learnloop-tauri/src/screens/desks/checks/model.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/checks/model.ts"
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

# `src/screens/desks/checks/model.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/checks/_area|TypeScript/screens/desks/checks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `VEIL_LABEL`, `SHOW_ANYWAY_COST`, `SHOW_NOTE_COST`, `SHOW_UNMEASURED_COST` and related exports within the desktop's TypeScript/screens/desks/checks ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/checks/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/model.ts) |
| Source lines | 207 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/checks/_area|TypeScript/screens/desks/checks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/checks/model|src/screens/desks/checks/model.ts]]

## Public API

- `export const VEIL_LABEL = "hidden during this check · back when you answer"` — const, line 11
- `export const SHOW_ANYWAY_COST = "If it shows what the answer says, this answer counts as practice and the check stays due. If it doesn't, nothing changes."` — const, line 13
- `export const SHOW_NOTE_COST = "This is one of your notes. LearnLoop doesn't read your notes, so it can't tell whether this one gives the answer away: opening it makes this answer count as practice, and the check stays due."` — const, line 16
- `export const SHOW_UNMEASURED_COST = "LearnLoop can't tell what this shows against the answer, so opening it makes this answer count as practice, and the check stays due."` — const, line 20
- `export function costOf(ref: CheckVeilRefDto | null): string` — function, line 24
- `export const WINDOW_VEIL_DECISIONS: Record<DeskWindowKind, "passages" | "whole"> =` — const, line 34
- `export function passagesCanShow(kind: string): boolean` — function, line 50
- `export const PRIMED_BY_NOTE_WORDS = "counts as practice · you opened one of your notes during this check` — const, line 55
- `export function veilIsNote(ref: CheckVeilRefDto): boolean` — function, line 60
- `export function refKey(ref: Record<string, unknown>): string` — function, line 67
- `export function veilSelector(ref: CheckVeilRefDto): string | null` — function, line 78
- `export function groupsLine(veiled: readonly CheckVeilRefDto[]): string` — function, line 108
- `export type CheckReason = "on_your_own" | "primed" | "with_help" | "seen_before" | "already_answered" | "practice"` — type, line 114
- `export const REASON_WORDS: Record<CheckReason, string> =` — const, line 117
- `export const PRIMED_UNMEASURED_WORDS = "counts as practice · you opened something during this check that LearnLoop can't measure against the answer, so this one counts as practice"` — const, line 127
- `export function eligibilityWords(eligibility: string | null): string` — function, line 137
- `export function answeredHead(cold: boolean): string` — function, line 142
- `export function lookedLine(groups: readonly string[], coldNow: boolean | null): string | null` — function, line 147
- `export function windowKind(window:` — function, line 155
- `export function visibleNow(stage: ParentNode | null, windows: ReadonlyArray<` — function, line 167
- `export function visibleKey(visible: CheckVisibleDto): string` — function, line 205

## Internal implementation anchors

- `const keys = Object.keys(ref).filter((key)` — const, line 68
- `function quoted(value: string): string` — function, line 72
- `const window = typeof ref.window_id === "string" ? `[data-desk-window="$` — const, line 79
- `const counts = new Map<string, number>()` — const, line 109
- `const ELIGIBILITY_WORDS: Record<string, string> =` — const, line 131
- `const what = [...new Set(groups)].join(" · ")` — const, line 149
- `const content = window.content?.kind` — const, line 156
- `const unique = (values: Iterable<string | null | undefined>): string[]` — const, line 163
- `const out: CheckVisibleDto["windows"] = []` — const, line 169
- `const kind = windowKind(window)` — const, line 171
- `const host = stage?.querySelector(`[data-desk-window="$` — const, line 172
- `const entry: CheckVisibleDto["windows"][number] =` — const, line 173
- `const extractionId = window.content?.extractionId` — const, line 175
- `const spans = [...host.querySelectorAll("[data-span-id], [data-transcript-span]")]` — const, line 180
- `const blocks = unique([...host.querySelectorAll("[data-block]")].map((element)` — const, line 191

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `visibleNow`, `windowKind`; references `visibleNow`, `windowKind`
- [[Reference/Desktop/TypeScript/screens/desks/checks/CheckCard|src/screens/desks/checks/CheckCard.tsx]] — import-or-re-export: `CheckReason`, `PRIMED_BY_NOTE_WORDS`, `PRIMED_UNMEASURED_WORDS`, `REASON_WORDS`, `answeredHead`, `eligibilityWords`, `groupsLine`, `lookedLine`; references `CheckReason`, `PRIMED_BY_NOTE_WORDS`, `PRIMED_UNMEASURED_WORDS`, `REASON_WORDS`, `answeredHead`, `eligibilityWords`, `groupsLine`, `lookedLine`
- [[Reference/Desktop/TypeScript/screens/desks/checks/VeilLayer|src/screens/desks/checks/VeilLayer.tsx]] — import-or-re-export: `VEIL_LABEL`, `costOf`, `refKey`, `veilSelector`; references `VEIL_LABEL`, `costOf`, `refKey`, `veilSelector`
- [[Reference/Desktop/TypeScript/screens/desks/checks/controller|src/screens/desks/checks/controller.ts]] — import-or-re-export: `CheckReason`, `refKey`, `visibleKey`; references `CheckReason`, `refKey`, `visibleKey`
- [[Reference/Desktop/TypeScript/screens/desks/checks/hold|src/screens/desks/checks/hold.ts]] — import-or-re-export: `VEIL_LABEL`, `passagesCanShow`, `refKey`, `veilSelector`; references `VEIL_LABEL`, `passagesCanShow`, `refKey`, `veilSelector`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CheckVeilRefDto`, `CheckVisibleDto`, `DeskWindowKind`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/checks/windowKinds.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/windowKinds.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/checks/contract.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/contract.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/checks/checks.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/checks.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_ih_lesson_candidate_after_cold_miss.py](../../../../../../../../tests/test_ih_lesson_candidate_after_cold_miss.py) — cross-boundary name contract: references uniquely owned exported name `REASON_WORDS`; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/checks/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/model.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
