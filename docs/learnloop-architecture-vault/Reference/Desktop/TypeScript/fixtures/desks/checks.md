---
title: "Desktop module · src/fixtures/desks/checks.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.fixtures.desks.checks"
language: "TypeScript"
area: "TypeScript/fixtures/desks"
source_path: "apps/learnloop-tauri/src/fixtures/desks/checks.ts"
source_paths:
  - "apps/learnloop-tauri/src/fixtures/desks/checks.ts"
activation_kind: "vitest-support"
activation_evidence: "Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/fixtures/desks/checks.ts`

Area: [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Exposes deterministic `checks` fixture data for a reproducible desktop scenario.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/fixtures/desks/checks.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/checks.ts) |
| Source lines | 246 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/fixtures/desks/fakeCore|src/fixtures/desks/fakeCore.ts]] → [[Reference/Desktop/TypeScript/fixtures/desks/checks|src/fixtures/desks/checks.ts]]

## Public API

- `export class FixtureChecks` — class, line 64

## Internal implementation anchors

- `const BOOK_CHECK =` — const, line 14
- `const PAPER_CHECK =` — const, line 16
- `const PROMPTS: Record<string, string> =` — const, line 19
- `const FEEDBACK: Record<string, string> =` — const, line 23
- `function windowGroup(kind: string): string` — function, line 28
- `function measured(ref: CheckVeilRefDto): boolean` — function, line 37
- `function handleOf(commitmentId: string, generation: number): string` — function, line 45
- `let hash = 0x811c9dc5` — let, line 46
- `let second = hash` — let, line 48
- `interface Open` — interface, line 53
- `const rows = this.mode === "open" ? [BOOK_CHECK, PAPER_CHECK] : this.mode === "due-paper" ? [PAPER_CHECK] : [BOOK_CHECK]` — const, line 86
- `const rows = this.dueRows().map((row)` — const, line 99
- `const spent = (this.generations.get(row.commitmentId) ?? 0) - 1` — const, line 107
- `const check = commitmentId === PAPER_CHECK.commitmentId ? PAPER_CHECK : BOOK_CHECK` — const, line 115
- `const covered = this.covered(commitmentId)` — const, line 120
- `const veiled: CheckVeilRefDto[] = []` — const, line 121
- `const add = (ref: CheckVeilRefDto)` — const, line 122
- `const protectedSpan = (spanId: string | null | undefined)` — const, line 125
- `const opened = new Set(open.opened.map((ref)` — const, line 143
- `const done = input.requestId ? this.closed.get(input.requestId) : undefined` — const, line 165
- `const commitmentId = this.resolve(input.handle)` — const, line 167
- `const open = this.open` — const, line 184
- `const known = new Set(open.veiled.map((ref)` — const, line 186
- `const additions = this.protection(open.commitmentId, input.visible).filter((ref)` — const, line 187
- `const open = this.open` — const, line 194
- `const again = input.exposureId ? open.exposures.get(input.exposureId) : undefined` — const, line 197
- `const unmeasured = input.kind === "left" || input.ref.measured === false || input.ref.kind === "surface"` — const, line 199
- `const coldNow = !open.unmeasured && !open.opened.some((ref)` — const, line 204
- `const status = input.exposureId ? open.exposures.get(input.exposureId)! :` — const, line 207
- `const saved = this.outcomes.get(input.submissionId)` — const, line 212
- `const open = this.open` — const, line 214
- `const primedBySpan = open.opened.some((ref)` — const, line 219
- `const byNote = open.opened.some((ref)` — const, line 220
- `const cold = !primedBySpan && !open.unmeasured` — const, line 221
- `const commitmentId = open.commitmentId` — const, line 223
- `const outcome =` — const, line 226

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/fakeCore|src/fixtures/desks/fakeCore.ts]] — import-or-re-export: `FixtureChecks`; references `FixtureChecks`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CheckCardDto`, `CheckVeilRefDto`, `CheckVisibleDto`, `ChecksDueDto`
- [[Reference/Desktop/TypeScript/fixtures/desks/sources|src/fixtures/desks/sources.ts]] — import-or-re-export; imports `FIXTURE_SOURCES`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/fixtures/desks/checks.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/checks.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
