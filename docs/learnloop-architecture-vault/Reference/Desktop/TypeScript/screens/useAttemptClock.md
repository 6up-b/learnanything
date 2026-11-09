---
title: "Desktop module · src/screens/useAttemptClock.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.useAttemptClock"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/useAttemptClock.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/useAttemptClock.ts"
source_commit: "3d6205a33e36c3014eb4b9a48382ee128a8fc5b1"
source_commit_timestamp: "2026-11-09T01:32:24-05:00"
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

# `src/screens/useAttemptClock.ts`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `AttemptClock`, `useAttemptClock` within the desktop's TypeScript/screens ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/useAttemptClock.ts](../../../../../../apps/learnloop-tauri/src/screens/useAttemptClock.ts) |
| Source lines | 82 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `3d6205a33e36c3014eb4b9a48382ee128a8fc5b1` |
| Commit timestamp | `2026-11-09T01:32:24-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/useAttemptClock|src/screens/useAttemptClock.ts]]

## Public API

- `export interface AttemptClock` — interface, line 21
- `export function useAttemptClock(storage: ActiveStorage | null = defaultActiveStorage()): AttemptClock` — function, line 30

## Internal implementation anchors

- `type ActiveStorage } from "./attemptClock"` — type, line 12
- `const TOUCH_EVENTS = ["keydown", "pointerdown", "wheel", "scroll", "input"] as const` — const, line 17
- `const SAVE_EVERY_MS = 5000` — const, line 19
- `const clock = useRef<VisitClock | null>(null)` — const, line 31
- `const keyRef = useRef<string | null>(null)` — const, line 32
- `const savedAt = useRef(0)` — const, line 33
- `const save = useCallback(()` — const, line 35
- `const now = Date.now()` — const, line 37
- `const open = useCallback((key: string | null)` — const, line 44
- `const onTouch = ()` — const, line 52
- `const current = clock.current` — const, line 53
- `const now = Date.now()` — const, line 55
- `const seconds = useCallback(()` — const, line 71
- `const forget = useCallback((key?: string | null)` — const, line 73
- `const target = key ?? keyRef.current` — const, line 74

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]] — import-or-re-export: `useAttemptClock`; references `useAttemptClock`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `useAttemptClock`; references `useAttemptClock`
- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export: `useAttemptClock`; references `useAttemptClock`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/attemptClock|src/screens/attemptClock.ts]] — import-or-re-export; imports `ActiveStorage`, `attemptActiveSeconds`, `carriedActiveMs`, `defaultActiveStorage`, `forgetActiveMs`, `keepActiveMs`, `openAttemptClock`, `touchAttempt`
- [[Reference/Desktop/TypeScript/screens/reader/visitClock|src/screens/reader/visitClock.ts]] — import-or-re-export; imports `VisitClock`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/attemptClock.test.ts](../../../../../../apps/learnloop-tauri/src/screens/attemptClock.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/useAttemptClock.ts](../../../../../../apps/learnloop-tauri/src/screens/useAttemptClock.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
