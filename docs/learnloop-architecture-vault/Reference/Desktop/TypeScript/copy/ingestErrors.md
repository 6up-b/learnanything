---
title: "Desktop module · src/copy/ingestErrors.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.copy.ingestErrors"
language: "TypeScript"
area: "TypeScript/copy"
source_path: "apps/learnloop-tauri/src/copy/ingestErrors.ts"
source_paths:
  - "apps/learnloop-tauri/src/copy/ingestErrors.ts"
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

# `src/copy/ingestErrors.ts`

Area: [[Reference/Desktop/TypeScript/copy/_area|TypeScript/copy]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `PlainError`, `plainError` within the desktop's TypeScript/copy ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/copy/ingestErrors.ts](../../../../../../apps/learnloop-tauri/src/copy/ingestErrors.ts) |
| Source lines | 52 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/copy/_area|TypeScript/copy]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AddSource|src/components/AddSource.tsx]] → [[Reference/Desktop/TypeScript/copy/ingestErrors|src/copy/ingestErrors.ts]]

## Public API

- `export interface PlainError` — interface, line 7
- `export function plainError(error: unknown, fallback = "Something went wrong."): PlainError` — function, line 38

## Internal implementation anchors

- `const LINES: Record<string, string> =` — const, line 14
- `const OWN_WORDS = new Set(["library_folder_in_use", "chatgpt_models_unavailable", "text_recognition_unavailable"])` — const, line 29
- `function asCommandError(error: unknown): CommandError | null` — function, line 31
- `const command = asCommandError(error)` — const, line 39
- `const raw = command?.message ?? (error instanceof Error ? error.message : typeof error === "string" ? error : null)` — const, line 40
- `const retryable = Boolean(command?.retryable)` — const, line 41
- `const known = command ? LINES[command.code] : undefined` — const, line 45
- `const line = command?.code === "invalid_page_range" && raw ? `$` — const, line 48

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/AddSource|src/components/AddSource.tsx]] — import-or-re-export: `plainError`; references `plainError`
- [[Reference/Desktop/TypeScript/components/ConnectAI|src/components/ConnectAI.tsx]] — import-or-re-export: `plainError`; references `plainError`
- [[Reference/Desktop/TypeScript/components/PlanFallbackOffer|src/components/PlanFallbackOffer.tsx]] — import-or-re-export: `plainError`; references `plainError`
- [[Reference/Desktop/TypeScript/screens/LibraryPlace|src/screens/LibraryPlace.tsx]] — import-or-re-export: `plainError`; references `plainError`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/copy/ingestErrors.test.ts](../../../../../../apps/learnloop-tauri/src/copy/ingestErrors.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_ingest_m3.py](../../../../../../tests/test_sidecar_ingest_m3.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_source_ingestion.py](../../../../../../tests/test_source_ingestion.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_init.py](../../../../../../tests/test_init.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/copy/ingestErrors.ts](../../../../../../apps/learnloop-tauri/src/copy/ingestErrors.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
