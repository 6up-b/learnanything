---
title: "Desktop module · src/app/useGlobalAdd.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.useGlobalAdd"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/useGlobalAdd.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/useGlobalAdd.ts"
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

# `src/app/useGlobalAdd.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `looksLikeSource`, `useGlobalAdd` within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/useGlobalAdd.ts](../../../../../../apps/learnloop-tauri/src/app/useGlobalAdd.ts) |
| Source lines | 55 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/useGlobalAdd|src/app/useGlobalAdd.ts]]

## Public API

- `export function looksLikeSource(text: string): boolean` — function, line 13
- `export function useGlobalAdd(` — function, line 19

## Internal implementation anchors

- `const ARXIV_ID = /^(arxiv:)?\d` — const, line 9
- `const LOCAL_FILE = /^(~|\/|[A-Za-z]:\\).+\.(pdf|md|markdown|txt|html?|vtt|srt|mp3|wav|m4a|flac|ogg|oga|opus|aac)$/i` — const, line 10
- `const value = (text || "").trim()` — const, line 14
- `const handlers = useRef(` — const, line 28
- `const onKey = (event: KeyboardEvent)` — const, line 33
- `const onPaste = (event: Event)` — const, line 40
- `const clipboard = (event as ClipboardEvent).clipboardData` — const, line 42
- `const text = clipboard?.getData("text") ?? clipboard?.getData("text/plain") ?? ""` — const, line 43

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `useGlobalAdd`; references `useGlobalAdd`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/app/keyboard|src/app/keyboard.ts]] — import-or-re-export; imports `isTypingTarget`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `ADD_FILES_CHORD`, `matchesChord`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/app/useGlobalAdd.test.tsx](../../../../../../apps/learnloop-tauri/src/app/useGlobalAdd.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/useGlobalAdd.ts](../../../../../../apps/learnloop-tauri/src/app/useGlobalAdd.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
