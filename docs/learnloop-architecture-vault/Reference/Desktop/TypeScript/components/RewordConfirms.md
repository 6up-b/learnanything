---
title: "Desktop module · src/components/RewordConfirms.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.RewordConfirms"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/RewordConfirms.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/RewordConfirms.tsx"
source_commit: "b3dca2b0505d83cf07dd82ea6d2065b34dbde343"
source_commit_timestamp: "2026-10-13T16:45:00-04:00"
source_worktree_state: "staged-or-mixed"
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

# `src/components/RewordConfirms.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `RewordConfirms` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/RewordConfirms.tsx](../../../../../../apps/learnloop-tauri/src/components/RewordConfirms.tsx) |
| Source lines | 211 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `staged-or-mixed` |
| Source commit | `b3dca2b0505d83cf07dd82ea6d2065b34dbde343` |
| Commit timestamp | `2026-10-13T16:45:00-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] → [[Reference/Desktop/TypeScript/components/RewordConfirms|src/components/RewordConfirms.tsx]]

## Public API

- `export function fieldLabel(field: string): string` — function, line 43
- `export function roleLabel(role: string): string` — function, line 47
- `export function valueText(value: unknown): string` — function, line 52
- `export function supportLine(confirm: FacetRewordConfirmDto): string` — function, line 66
- `export function RewordConfirmList(` — function, line 154

## Internal implementation anchors

- `const FIELD_LABEL: Record<string, string> =` — const, line 18
- `const ROLE_LABEL: Record<string, string> =` — const, line 31
- `const SPAN_SUPPORT_LINE: Record<string, string> =` — const, line 59
- `const check = confirm.spanSupport` — const, line 67
- `const roles = Array.from(new Set(confirm.sources.map((source)` — const, line 77
- `function SourceLine(` — function, line 81
- `function RewordConfirmCard(` — function, line 96
- `const changed = confirm.fields.map(fieldLabel).join(", ")` — const, line 105
- `const visible = confirms.filter((confirm)` — const, line 165
- `async function decide(confirm: FacetRewordConfirmDto, decision: "confirm" | "keep")` — function, line 168
- `const wordingStyle: CSSProperties =` — const, line 201
- `const button: CSSProperties =` — const, line 203

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/FacetInspector|src/components/FacetInspector.tsx]] — import-or-re-export: `roleLabel`; references `roleLabel`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — import-or-re-export: `RewordConfirmList`; references `RewordConfirmList`
- [[Reference/Desktop/TypeScript/screens/RegistryReviewScreen|src/screens/RegistryReviewScreen.tsx]] — import-or-re-export: `RewordConfirmList`; references `RewordConfirmList`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `FacetChangeSourceDto`, `FacetRewordConfirmDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `SectionHeader`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/syllabusRole.test.tsx](../../../../../../apps/learnloop-tauri/src/components/syllabusRole.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/RewordConfirms.test.tsx](../../../../../../apps/learnloop-tauri/src/components/RewordConfirms.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/RewordConfirms.tsx](../../../../../../apps/learnloop-tauri/src/components/RewordConfirms.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
