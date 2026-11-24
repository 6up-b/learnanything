---
title: "Desktop module · src/screens/desks/checks/CheckCard.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.checks.CheckCard"
language: "TypeScript"
area: "TypeScript/screens/desks/checks"
source_path: "apps/learnloop-tauri/src/screens/desks/checks/CheckCard.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/checks/CheckCard.tsx"
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

# `src/screens/desks/checks/CheckCard.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/checks/_area|TypeScript/screens/desks/checks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `CheckCard` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/checks/CheckCard.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/CheckCard.tsx) |
| Source lines | 197 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/checks/_area|TypeScript/screens/desks/checks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/checks/CheckCard|src/screens/desks/checks/CheckCard.tsx]]

## Public API

- `export function CheckMarker(` — function, line 18
- `export function CheckCardInline(` — function, line 94
- `export function CheckCardOverlay(` — function, line 133
- `export class CheckLenses` — class, line 176

## Internal implementation anchors

- `const SAFE =` — const, line 15
- `const check = checks[0]` — const, line 20
- `const held = desk.holding()` — const, line 22
- `function question(open: OpenCheck): string` — function, line 44
- `const prompt = open.card.prompt as` — const, line 45
- `function Question(` — function, line 51
- `const presentation = open.card.prompt?.presentation` — const, line 52
- `function opensCold(open: OpenCheck): boolean` — function, line 60
- `function feedback(open: OpenCheck): string` — function, line 64
- `const reply = open.reply as` — const, line 65
- `function answerKeys(desk: CheckDesk)` — function, line 69
- `function ReasonLine(` — function, line 81
- `const reason = (open.reply?.reason ?? null) as CheckReason | null` — const, line 82
- `const primedBy = typeof open.reply?.primedBy === "string" ? open.reply.primedBy : null` — const, line 84
- `const byNote = reason === "primed" && primedBy === "unmeasured_note"` — const, line 85
- `const unmeasured = reason === "primed" && primedBy !== null && !byNote` — const, line 86
- `const eligibility = typeof open.reply?.eligibility === "string" ? open.reply.eligibility : null` — const, line 87
- `const words = byNote ? PRIMED_BY_NOTE_WORDS : unmeasured ? PRIMED_UNMEASURED_WORDS : reason === "practice" && eligibility ? `counts as practice · $` — const, line 88
- `const open = desk.open()` — const, line 96
- `const veiled = open.veiled` — const, line 98
- `const looked = lookedLine(open.looked, open.coldNow)` — const, line 99
- `const cold = Boolean(open.reply?.cold)` — const, line 101
- `const open = desk.open()` — const, line 135
- `const veiled = open.veiled` — const, line 137
- `const looked = lookedLine(open.looked, open.coldNow)` — const, line 138
- `const version = desk.getVersion()` — const, line 180
- `const known = this.made.get(windowId)` — const, line 181
- `const lens: ReaderLens =` — const, line 183
- `const own = base?.before?.(spanId) ?? null` — const, line 186
- `const open = desk.open()` — const, line 187
- `const here = Boolean(open && open.host?.extractionId === extractionId && open.host?.spanId === spanId)` — const, line 188
- `const due = desk.dueAt(extractionId, spanId).filter((check)` — const, line 189

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `CheckCardOverlay`, `CheckLenses`; references `CheckCardOverlay`, `CheckLenses`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/components/ItemPresentation|src/components/ItemPresentation.tsx]] — import-or-re-export; imports `ItemPresentation`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export; imports `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/checks/controller|src/screens/desks/checks/controller.ts]] — import-or-re-export; imports `CheckDesk`, `DueCheck`, `OpenCheck`
- [[Reference/Desktop/TypeScript/screens/desks/checks/hold|src/screens/desks/checks/hold.ts]] — import-or-re-export; imports `SAFE_ATTR`
- [[Reference/Desktop/TypeScript/screens/desks/checks/model|src/screens/desks/checks/model.ts]] — import-or-re-export; imports `CheckReason`, `PRIMED_BY_NOTE_WORDS`, `PRIMED_UNMEASURED_WORDS`, `REASON_WORDS`, `answeredHead`, `eligibilityWords`, `groupsLine`, `lookedLine`
- [[Reference/Desktop/TypeScript/screens/desks/fitMath|src/screens/desks/fitMath.tsx]] — import-or-re-export; imports `FitMath`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/checks/contract.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/contract.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/checks/checks.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/checks.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/checks/CheckCard.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/CheckCard.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
