---
title: "Desktop module · src/screens/reader/checkOffer.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.checkOffer"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/checkOffer.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/checkOffer.ts"
source_commit: "148f7427ba6ffb1fcea9545e865f923e07eeb48b"
source_commit_timestamp: "2026-10-13T17:25:15-04:00"
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

# `src/screens/reader/checkOffer.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `CheckSurface`, `ReadingPhase`, `SectionCheckOffer`, `PassageCheckOffer` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/checkOffer.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/checkOffer.ts) |
| Source lines | 132 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `148f7427ba6ffb1fcea9545e865f923e07eeb48b` |
| Commit timestamp | `2026-10-13T17:25:15-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] → [[Reference/Desktop/TypeScript/screens/reader/checkOffer|src/screens/reader/checkOffer.ts]]

## Public API

- `export type CheckSurface = "pdf" | "text" | "watch" | "loading"` — type, line 23
- `export type ReadingPhase = "before_section" | "during_section" | "after_section"` — type, line 25
- `export interface SectionCheckOffer` — interface, line 30
- `export interface PassageCheckOffer` — interface, line 62
- `export type CheckOfferInput = SectionCheckOffer | PassageCheckOffer` — type, line 70
- `export type CheckOfferReason = | "offered" | "pinned" | "no_check" | "unavailable" | "settled" | "surface_loading" | "ahead" | "not_read_this_visit" | "not_at_its_point" | "not_raised" | "inquiry_closed" | "muted"` — type, line 72
- `export interface CheckOfferDecision` — interface, line 86
- `export function checkOffer(input: CheckOfferInput): CheckOfferDecision` — function, line 100

## Internal implementation anchors

- `const DURING_SECTION_AT = 0.45` — const, line 91
- `const AFTER_SECTION_AT = 0.7` — const, line 92
- `const BEFORE_SECTION_UNTIL = 0.3` — const, line 93
- `function decide(offer: boolean, reason: CheckOfferReason): CheckOfferDecision` — function, line 95
- `const until = Math.max(BEFORE_SECTION_UNTIL, input.firstPassageShare)` — const, line 120
- `const reached = input.surface === "pdf" && input.atLastPage !== null ? input.atLastPage : input.progress >= AFTER_SECTION_AT` — const, line 128

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `checkOffer`; references `checkOffer`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export: `CheckSurface`, `checkOffer`; references `CheckSurface`, `checkOffer`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/checkOffer.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/checkOffer.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/checkOffer.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/checkOffer.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
