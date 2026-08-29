---
title: "Desktop module · src/components/sourceTail.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.sourceTail"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/sourceTail.ts"
source_paths:
  - "apps/learnloop-tauri/src/components/sourceTail.ts"
source_commit: "d79bacf5ced0cce4cbe2f323513fe63f752495fe"
source_commit_timestamp: "2026-07-14T17:14:28-04:00"
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

# `src/components/sourceTail.ts`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides shared `sourceTail` state or utility behavior for desktop components.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/sourceTail.ts](../../../../../../apps/learnloop-tauri/src/components/sourceTail.ts) |
| Source lines | 40 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `d79bacf5ced0cce4cbe2f323513fe63f752495fe` |
| Commit timestamp | `2026-07-14T17:14:28-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/components/sourceTail|src/components/sourceTail.ts]]

## Public API

- `export function youtubeVideoId(source: string): string | null` — function, line 9
- `export function readableSourceTail(source: string): string` — function, line 33

## Internal implementation anchors

- `const s = (source || "").trim()` — const, line 10
- `const url = new URL(s)` — const, line 13
- `const host = url.hostname.toLowerCase()` — const, line 14
- `const id = url.pathname.split("/").filter(Boolean)[0]` — const, line 16
- `const v = url.searchParams.get("v")` — const, line 19
- `const parts = url.pathname.split("/").filter(Boolean)` — const, line 22
- `const vid = youtubeVideoId(source)` — const, line 34
- `const trimmed = source.replace(/[/\\]+$/, "")` — const, line 36
- `const withoutQuery = trimmed.split(/[?#]/)[0]` — const, line 37
- `const tail = withoutQuery.split(/[/\\]/).filter(Boolean).pop()` — const, line 38

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/IngestActivity|src/components/IngestActivity.tsx]] — import-or-re-export: `readableSourceTail`; references `readableSourceTail`
- [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]] — import-or-re-export: `youtubeVideoId`; references `youtubeVideoId`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `youtubeVideoId`; references `youtubeVideoId`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_reader.py](../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_ingest_m3.py](../../../../../../tests/test_sidecar_ingest_m3.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_source_ingestion.py](../../../../../../tests/test_source_ingestion.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/sourceTail.ts](../../../../../../apps/learnloop-tauri/src/components/sourceTail.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
