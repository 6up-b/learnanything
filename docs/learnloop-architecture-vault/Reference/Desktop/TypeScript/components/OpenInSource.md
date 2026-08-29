---
title: "Desktop module · src/components/OpenInSource.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.OpenInSource"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/OpenInSource.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/OpenInSource.tsx"
source_commit: "a29853775f09f6b504620b1a8b6d5e890161f912"
source_commit_timestamp: "2026-07-14T17:11:30-04:00"
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

# `src/components/OpenInSource.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `OpenInSource` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/OpenInSource.tsx](../../../../../../apps/learnloop-tauri/src/components/OpenInSource.tsx) |
| Source lines | 361 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `a29853775f09f6b504620b1a8b6d5e890161f912` |
| Commit timestamp | `2026-07-14T17:11:30-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]]

## Public API

- `export function OpenInSource(` — function, line 11

## Internal implementation anchors

- `const handler = (e: KeyboardEvent)` — const, line 32
- `let cancelled = false` — let, line 40
- `const heading = view ? view.sectionPath.length > 0 ? view.sectionPath.join(" › ") : view.blockType : "Open in source"` — const, line 62
- `const prev = view.previousSpans[view.previousSpans.length - 1]` — const, line 139
- `const next = view.nextSpans[0]` — const, line 149
- `function PdfRegion(` — function, line 167
- `const left = Math.max(0, Math.min(100, (x0 / pageSize[0]) * 100))` — const, line 170
- `const top = Math.max(0, Math.min(100, (y0 / pageSize[1]) * 100))` — const, line 171
- `const width = Math.max(0.5, Math.min(100 - left, ((x1 - x0) / pageSize[0]) * 100))` — const, line 172
- `const height = Math.max(0.5, Math.min(100 - top, ((y1 - y0) / pageSize[1]) * 100))` — const, line 173
- `function youtubeVideoId(uri: string): string | null` — function, line 198
- `const url = new URL(uri)` — const, line 200
- `const host = url.hostname.replace(/^www\./, "")` — const, line 201
- `const v = url.searchParams.get("v")` — const, line 204
- `const parts = url.pathname.split("/").filter(Boolean)` — const, line 206
- `const marker = parts.findIndex((p)` — const, line 207
- `function timeRange(view: SpanViewDto):` — function, line 218
- `const raw = (view.locator || "").replace(/^span:(?:[^/]+\/)?/, "")` — const, line 219
- `const match = /^t=([0-9]+(?:\.[0-9]+)?)-([0-9]+(?:\.[0-9]+)?)$/.exec(raw)` — const, line 220
- `function fmtTime(seconds: number): string` — function, line 225
- `const s = Math.max(0, Math.floor(seconds))` — const, line 226
- `const m = Math.floor(s / 60)` — const, line 227
- `function YouTubeEmbed(` — function, line 231
- `const uri = view.canonicalUri as string` — const, line 232
- `const videoId = youtubeVideoId(uri)` — const, line 233
- `const src = `https://www.youtube-nocookie.com/embed/$` — const, line 247
- `function NeighborList(` — function, line 282
- `const backdropStyle: CSSProperties =` — const, line 303
- `const panelStyle: CSSProperties =` — const, line 315
- `const headerStyle: CSSProperties =` — const, line 327
- `const pageBoxStyle: CSSProperties =` — const, line 336
- `const highlightBlockStyle: CSSProperties =` — const, line 344
- `const navBtn: CSSProperties =` — const, line 354

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `OpenInSource`; references `OpenInSource`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `OpenInSource`; references `OpenInSource`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export: `OpenInSource`; references `OpenInSource`
- [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]] — import-or-re-export: `OpenInSource`; references `OpenInSource`
- [[Reference/Desktop/TypeScript/screens/RepairScreen|src/screens/RepairScreen.tsx]] — import-or-re-export: `OpenInSource`; references `OpenInSource`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SpanNeighborDto`, `SpanViewDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Pill`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.
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

1. Modify [apps/learnloop-tauri/src/components/OpenInSource.tsx](../../../../../../apps/learnloop-tauri/src/components/OpenInSource.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
