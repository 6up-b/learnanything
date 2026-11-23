---
title: "Desktop module · src/screens/desks/menu/verbs.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.menu.verbs"
language: "TypeScript"
area: "TypeScript/screens/desks/menu"
source_path: "apps/learnloop-tauri/src/screens/desks/menu/verbs.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/menu/verbs.ts"
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

# `src/screens/desks/menu/verbs.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/menu/_area|TypeScript/screens/desks/menu]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `MenuApi`, `MenuContext`, `promotedRef`, `runVerb` and related exports within the desktop's TypeScript/screens/desks/menu ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/menu/verbs.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/verbs.ts) |
| Source lines | 215 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/menu/_area|TypeScript/screens/desks/menu]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/menu/verbs|src/screens/desks/menu/verbs.ts]]

## Public API

- `export interface MenuApi` — interface, line 20
- `export interface MenuContext` — interface, line 32
- `export function promotedRef(row: PromotedRowDto):` — function, line 68
- `export async function runVerb(id: VerbId, object: MenuObject, ctx: MenuContext): Promise<void>` — function, line 86
- `export function sourceMenuRows(object: MenuObject, ctx: MenuContext, appendTarget: string): MenuRow[]` — function, line 204

## Internal implementation anchors

- `function errorText(error: unknown): string` — function, line 59
- `function anchorOf(object: MenuObject):` — function, line 63
- `const ref = row.action.ref as Record<string, unknown> | undefined` — const, line 69
- `const camel: Record<string, unknown> =` — const, line 71
- `const target = row.action.target ??` — const, line 73
- `async function sectionOf(object: MenuObject, ctx: MenuContext): Promise<` — function, line 79
- `const knows = await ctx.api.passageKnows(objectInput(object, ctx.deskId))` — const, line 80
- `const place = knows.places.find((each)` — const, line 81
- `const anchor = anchorOf(object)` — const, line 87
- `const words = (object.selection || object.text).trim()` — const, line 88
- `const note = await ctx.askNote(object)` — const, line 105
- `const who = await ctx.api.readingIdentity(anchor.extractionId)` — const, line 107
- `const row = ctx.promotedRows().find((each)` — const, line 118
- `const place = row ? promotedRef(row) : null` — const, line 119
- `const found = await ctx.api.readerCorrespondents(` — const, line 130
- `const section = found.learningObjects.flatMap((lo)` — const, line 131
- `const figure = await ctx.showMe(words.slice(0, 300), anchor, object.windowId)` — const, line 149
- `const who = await ctx.api.readingIdentity(anchor.extractionId)` — const, line 162
- `const drafted = await ctx.api.readerAuthorSectionQuestion(` — const, line 175
- `const lesson = await ctx.api.lessonTurn(anchor ?` — const, line 180

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `MenuApi`, `MenuContext`, `promotedRef`, `sourceMenuRows`; references `MenuApi`, `MenuContext`, `promotedRef`, `sourceMenuRows`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ContentRefDto`, `CorrespondentsDto`, `LessonTurnInput`, `LessonViewDto`, `MenuObjectInput`, `PassageKnowsDto`, `PromotedRowDto`, `ReaderAuthorSectionQuestionDto`, `ReaderCaptureInput`, `ReaderCaptureReceiptDto`, `ReaderExerciseImportReceiptDto`, `ReaderImportExerciseInput`
- [[Reference/Desktop/TypeScript/screens/desks/menu/model|src/screens/desks/menu/model.ts]] — import-or-re-export; imports `MenuObject`, `MenuRow`, `VerbId`, `objectInput`, `verbsFor`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/menu/verbs.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/verbs.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/menu/verbs.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/verbs.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
