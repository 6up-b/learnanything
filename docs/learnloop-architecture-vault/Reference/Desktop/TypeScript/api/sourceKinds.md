---
title: "Desktop module · src/api/sourceKinds.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.api.sourceKinds"
language: "TypeScript"
area: "TypeScript/api"
source_path: "apps/learnloop-tauri/src/api/sourceKinds.ts"
source_paths:
  - "apps/learnloop-tauri/src/api/sourceKinds.ts"
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

# `src/api/sourceKinds.ts`

Area: [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SOURCE_KINDS`, `SourceCategory`, `SourceKindRow`, `SOURCE_FILE_EXTENSIONS` and related exports within the desktop's TypeScript/api ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/api/sourceKinds.ts](../../../../../../apps/learnloop-tauri/src/api/sourceKinds.ts) |
| Source lines | 23 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] → [[Reference/Desktop/TypeScript/api/sourceKinds|src/api/sourceKinds.ts]]

## Public API

- `export const SOURCE_KINDS = [` — const, line 4
- `export type SourceCategory = (typeof SOURCE_KINDS)[number]["category"]` — type, line 14
- `export type SourceKindRow = (typeof SOURCE_KINDS)[number]` — type, line 16
- `export const SOURCE_FILE_EXTENSIONS: readonly string[] = SOURCE_KINDS.flatMap((kind)` — const, line 19
- `export function sourceKindRow(category: string | null | undefined): SourceKindRow | null` — function, line 21

## Internal implementation anchors

No non-exported declaration anchor was detected by the static extractor.

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export: `IsoTimestamp`, `SourceCategory`, `version: number;
  codex: {
    ready: boolean;
    status: string;
    model: string | null;
    actualRevision: string | null;
    baseUrl: string;
    checkedAt: IsoTimestamp;`; references `IsoTimestamp`, `SourceCategory`
- [[Reference/Desktop/TypeScript/app/useGlobalAdd|src/app/useGlobalAdd.ts]] — import-or-re-export: `SOURCE_FILE_EXTENSIONS`; references `SOURCE_FILE_EXTENSIONS`
- [[Reference/Desktop/TypeScript/components/useSourceFileDrop|src/components/useSourceFileDrop.ts]] — import-or-re-export: `SOURCE_FILE_EXTENSIONS`; references `SOURCE_FILE_EXTENSIONS`
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `SOURCE_KINDS`, `SourceCategory`, `sourceKindRow`; references `SOURCE_KINDS`, `SourceCategory`, `sourceKindRow`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/IngestScreen.eligibility.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/IngestScreen.eligibility.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/api/sourceKinds.test.ts](../../../../../../apps/learnloop-tauri/src/api/sourceKinds.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_hint_feedback_texts.py](../../../../../../tests/test_hint_feedback_texts.py) — cross-boundary name contract: references uniquely owned exported name `SOURCE_KINDS`; it does **not** directly execute this source module.
- [tests/test_notes_as_learner_text.py](../../../../../../tests/test_notes_as_learner_text.py) — cross-boundary name contract: references uniquely owned exported name `SOURCE_KINDS`; it does **not** directly execute this source module.
- [tests/test_reader_formative_texts.py](../../../../../../tests/test_reader_formative_texts.py) — cross-boundary name contract: references uniquely owned exported name `SOURCE_KINDS`; it does **not** directly execute this source module.
- [tests/test_source_kinds.py](../../../../../../tests/test_source_kinds.py) — direct source contract: references the exact source path.
- [tests/test_sidecar_ingest_m3.py](../../../../../../tests/test_sidecar_ingest_m3.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_source_ingestion.py](../../../../../../tests/test_source_ingestion.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_init.py](../../../../../../tests/test_init.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Add or change an RPC in all four layers: DTO, client facade, Rust command/registration, and Python sidecar handler/registry.
- Preserve camelCase wire names and typed error behavior; exercise `tests/test_desktop_rpc_contract.py` plus the feature's sidecar tests.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/api/sourceKinds.ts](../../../../../../apps/learnloop-tauri/src/api/sourceKinds.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
