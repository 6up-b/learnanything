---
title: "Desktop module · src/components/BookCard.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.BookCard"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/BookCard.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/BookCard.tsx"
source_commit: "462f02eaf8f6af6eb47ce6b7a895e21b04be309a"
source_commit_timestamp: "2026-10-19T23:41:22-04:00"
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

# `src/components/BookCard.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `BookCard` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/BookCard.tsx](../../../../../../apps/learnloop-tauri/src/components/BookCard.tsx) |
| Source lines | 193 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `462f02eaf8f6af6eb47ce6b7a895e21b04be309a` |
| Commit timestamp | `2026-10-19T23:41:22-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LibraryPlace|src/screens/LibraryPlace.tsx]] → [[Reference/Desktop/TypeScript/components/BookShelf|src/components/BookShelf.tsx]] → [[Reference/Desktop/TypeScript/components/BookCard|src/components/BookCard.tsx]]

## Public API

- `export function readableTitle(title: string): string` — function, line 35
- `export function StatusLine(` — function, line 51
- `export function BookCard(` — function, line 73
- `export function PendingCard(` — function, line 168

## Internal implementation anchors

- `const linkButton: CSSProperties =` — const, line 10
- `const primaryButton: CSSProperties =` — const, line 22
- `const trimmed = (title || "").trim()` — const, line 36
- `const name = decodeURIComponent(trimmed.split("/").pop() ?? trimmed).replace(/\.[A-Za-z0-9]` — const, line 38
- `const words = name.split(/[_\-.\s]+/).filter(Boolean)` — const, line 39
- `const lower = words.every((word)` — const, line 41
- `function toneColor(tone: SourceStatusLineDto["tone"]): string` — function, line 45
- `const ready = card.readiness === "ready"` — const, line 91
- `const readable = card.readerEnabled !== false` — const, line 92
- `const line = (aiReady === false ? card.statusLine?.withoutAi : null) ?? card.statusLine ?? null` — const, line 93
- `const noun = card.kindNoun ?? "book"` — const, line 94
- `const failed = entry.statusLine?.tone === "problem"` — const, line 178

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/BookShelf|src/components/BookShelf.tsx]] — import-or-re-export: `BookCard`, `PendingCard`; references `BookCard`, `PendingCard`
- [[Reference/Desktop/TypeScript/screens/reader/PreparingView|src/screens/reader/PreparingView.tsx]] — import-or-re-export: `StatusLine`, `readableTitle`; references `StatusLine`, `readableTitle`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `PendingAddDto`, `SourceActionKind`, `SourceLibraryCard`, `SourceStatusLineDto`
- [[Reference/Desktop/TypeScript/components/IntentControl|src/components/IntentControl.tsx]] — import-or-re-export; imports `IntentControl`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/copy/denyList.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/BookShelf.test.tsx](../../../../../../apps/learnloop-tauri/src/components/BookShelf.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/BookCard.tsx](../../../../../../apps/learnloop-tauri/src/components/BookCard.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
