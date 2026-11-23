---
title: "Desktop module · src/fixtures/desks/companion.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.fixtures.desks.companion"
language: "TypeScript"
area: "TypeScript/fixtures/desks"
source_path: "apps/learnloop-tauri/src/fixtures/desks/companion.ts"
source_paths:
  - "apps/learnloop-tauri/src/fixtures/desks/companion.ts"
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

# `src/fixtures/desks/companion.ts`

Area: [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Exposes deterministic `companion` fixture data for a reproducible desktop scenario.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/fixtures/desks/companion.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/companion.ts) |
| Source lines | 190 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/fixtures/desks/_area|TypeScript/fixtures/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/fixtures/desks/fakeCore|src/fixtures/desks/fakeCore.ts]] → [[Reference/Desktop/TypeScript/fixtures/desks/companion|src/fixtures/desks/companion.ts]]

## Public API

- `export const FAKE_ANSWER_MS = 600` — const, line 23
- `export class FixtureCompanion` — class, line 25

## Internal implementation anchors

- `interface FakeJob` — interface, line 15
- `const known = this.jobs.get(input.requestId)` — const, line 36
- `const job = this.jobs.get(requestId)` — const, line 43
- `const done = job.status === "done" || job.status === "cancelled"` — const, line 63
- `const answerMd = `A synthetic answer from the fixture's tutor to “$` — const, line 64
- `const job = this.jobs.get(requestId)` — const, line 94
- `const earlier: CompanionExchangeDto[] = [` — const, line 100
- `const all = [...this.answered, ...earlier]` — const, line 110
- `const q = input.query?.toLowerCase().trim()` — const, line 111
- `const rows = q ? all.filter((exchange)` — const, line 112
- `const days = new Map<string, CompanionExchangeDto[]>()` — const, line 113
- `const date = row.createdAt.slice(0, 10)` — const, line 115
- `const q = input.query.toLowerCase().trim()` — const, line 126
- `const sources = FIXTURE_LIBRARY.filter((card)` — const, line 127
- `const passages = this.passages((text)` — const, line 137
- `const jobId = `fx_search_$` — const, line 138
- `const groups: SearchGroupDto[] = [` — const, line 140
- `const search = this.searches.get(jobId)` — const, line 165
- `const done = this.now() - search.at >= 300` — const, line 167
- `const rows = done ? this.passages((text)` — const, line 169
- `const card = FIXTURE_LIBRARY.find((entry)` — const, line 180
- `const video = view.extractionId === FIXTURE_SOURCES.video.extractionId || view.extractionId === FIXTURE_SOURCES.video2.extractionId` — const, line 181

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/fakeCore|src/fixtures/desks/fakeCore.ts]] — import-or-re-export: `FixtureCompanion`; references `FixtureCompanion`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CompanionAskInput`, `CompanionAskJobDto`, `CompanionExchangeDto`, `CompanionHistoryDto`, `SearchEverythingDto`, `SearchGroupDto`, `SearchJobDto`
- [[Reference/Desktop/TypeScript/fixtures/desks/sources|src/fixtures/desks/sources.ts]] — import-or-re-export; imports `FIXTURE_LIBRARY`, `FIXTURE_SOURCES`, `FIXTURE_VIEWS`

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

1. Modify [apps/learnloop-tauri/src/fixtures/desks/companion.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/desks/companion.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
