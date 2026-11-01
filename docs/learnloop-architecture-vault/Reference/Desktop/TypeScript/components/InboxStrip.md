---
title: "Desktop module · src/components/InboxStrip.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.InboxStrip"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/InboxStrip.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/InboxStrip.tsx"
source_commit: "b927425c4eef35a98dcd1758706fe5e722255d4f"
source_commit_timestamp: "2026-10-25T02:38:53-04:00"
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

# `src/components/InboxStrip.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `InboxStrip` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/InboxStrip.tsx](../../../../../../apps/learnloop-tauri/src/components/InboxStrip.tsx) |
| Source lines | 216 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `b927425c4eef35a98dcd1758706fe5e722255d4f` |
| Commit timestamp | `2026-10-25T02:38:53-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] → [[Reference/Desktop/TypeScript/components/InboxStrip|src/components/InboxStrip.tsx]]

## Public API

- `export function InboxStrip(` — function, line 23

## Internal implementation anchors

- `const PENDING_LABEL: Record<NonNullable<CaptureDto["pendingRoute"]>, string> =` — const, line 11
- `const PAGE = 100` — const, line 15
- `function label(capture: CaptureDto): string` — function, line 17
- `const alive = useRef(false)` — const, line 44
- `const request = useRef(0)` — const, line 45
- `const refresh = useCallback(async ()` — const, line 46
- `const revision = ++request.current` — const, line 47
- `const next = await api.getInboxSummary()` — const, line 49
- `let listed: CaptureDto[] | null = null` — let, line 51
- `let older = false` — let, line 52
- `const seen = new Set<string>()` — const, line 65
- `const timer = window.setInterval(()` — const, line 79
- `const focus = ()` — const, line 80
- `async function remove(captureId: string, purge: boolean)` — function, line 90
- `const result = await api.purgeCapture(captureId)` — const, line 94
- `async function resume(captureId: string)` — function, line 107
- `const pendingDeletes = summary?.deletePending ?? []` — const, line 121
- `const pendingIds = new Set(pendingDeletes.map((capture)` — const, line 122

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `InboxStrip`; references `InboxStrip`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `InboxStrip`; references `InboxStrip`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/capture|src/api/capture.ts]] — import-or-re-export; imports `CaptureDto`, `InboxSummary`
- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export; imports `AskTarget`
- [[Reference/Desktop/TypeScript/components/CapturePhoto|src/components/CapturePhoto.tsx]] — import-or-re-export; imports `CapturePhoto`
- [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] — import-or-re-export; imports `QuickAddDialog`
- [[Reference/Desktop/TypeScript/components/WriteCardDialog|src/components/WriteCardDialog.tsx]] — import-or-re-export; imports `WriteCardDialog`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/InboxStrip.test.tsx](../../../../../../apps/learnloop-tauri/src/components/InboxStrip.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/InboxStrip.tsx](../../../../../../apps/learnloop-tauri/src/components/InboxStrip.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
