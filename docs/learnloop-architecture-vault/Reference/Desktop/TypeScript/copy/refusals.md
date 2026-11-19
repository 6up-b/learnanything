---
title: "Desktop module · src/copy/refusals.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.copy.refusals"
language: "TypeScript"
area: "TypeScript/copy"
source_path: "apps/learnloop-tauri/src/copy/refusals.ts"
source_paths:
  - "apps/learnloop-tauri/src/copy/refusals.ts"
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

# `src/copy/refusals.ts`

Area: [[Reference/Desktop/TypeScript/copy/_area|TypeScript/copy]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `NO_HINTS_ON_YOUR_OWN`, `NO_HINTS_SHORT_CHECK`, `NO_ASK_SHORT_CHECK`, `NO_ASK_TEACH_BACK` and related exports within the desktop's TypeScript/copy ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/copy/refusals.ts](../../../../../../apps/learnloop-tauri/src/copy/refusals.ts) |
| Source lines | 24 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/copy/_area|TypeScript/copy]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/copy/refusals|src/copy/refusals.ts]]

## Public API

- `export const NO_HINTS_ON_YOUR_OWN = "No hints on this one: it's a check on your own."` — const, line 9
- `export const NO_HINTS_SHORT_CHECK = `No hints during this short check. Answer with what you know, or choose “$` — const, line 12
- `export const NO_ASK_SHORT_CHECK = `Ask is paused during this short check. To be taught instead, choose “$` — const, line 15
- `export const NO_ASK_TEACH_BACK = "Ask is paused while you teach this one back, so the tutor can't give the answer away."` — const, line 18
- `export const NO_ASK_NOT_YET = "Ask opens once this question has loaded, and stays paused during a short check."` — const, line 21
- `export const NOTE_NO_SUBJECT = "This note can't be saved here: the question isn't filed under a subject yet. Your words are still here."` — const, line 24

## Internal implementation anchors

No non-exported declaration anchor was detected by the static extractor.

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `NO_ASK_NOT_YET`, `NO_ASK_TEACH_BACK`; references `NO_ASK_NOT_YET`, `NO_ASK_TEACH_BACK`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `NOTE_NO_SUBJECT`; references `NOTE_NO_SUBJECT`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `NO_ASK_SHORT_CHECK`, `NO_ASK_TEACH_BACK`, `NO_HINTS_ON_YOUR_OWN`, `NO_HINTS_SHORT_CHECK`; references `NO_ASK_SHORT_CHECK`, `NO_ASK_TEACH_BACK`, `NO_HINTS_ON_YOUR_OWN`, `NO_HINTS_SHORT_CHECK`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/app/checkHandoff|src/app/checkHandoff.ts]] — import-or-re-export; imports `STOP_AND_TEACH_LABEL`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/copy/denyList.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/copy/refusals.ts](../../../../../../apps/learnloop-tauri/src/copy/refusals.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
