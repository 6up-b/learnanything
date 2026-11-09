---
title: "Desktop module · src/components/ChatGPTPlanSettings.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.ChatGPTPlanSettings"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/ChatGPTPlanSettings.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/ChatGPTPlanSettings.tsx"
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

# `src/components/ChatGPTPlanSettings.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `ChatGPTPlanSettings` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/ChatGPTPlanSettings.tsx](../../../../../../apps/learnloop-tauri/src/components/ChatGPTPlanSettings.tsx) |
| Source lines | 328 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] → [[Reference/Desktop/TypeScript/components/ChatGPTPlanSettings|src/components/ChatGPTPlanSettings.tsx]]

## Public API

- `export function ChatGPTPlanSettings(` — function, line 42

## Internal implementation anchors

- `const POLL_MS = 1000` — const, line 18
- `async function openExternal(url: string)` — function, line 20
- `function stateLine(plan: ChatGPTPlanDto):` — function, line 25
- `const notify = useRef(` — const, line 56
- `const watched = useRef<string | null>(null)` — const, line 61
- `const attemptId = plan.attempt?.id ?? null` — const, line 65
- `const waiting = plan.attempt?.status === "waiting"` — const, line 66
- `let active = true` — let, line 71
- `let reported = false` — let, line 72
- `const timer = setInterval(()` — const, line 73
- `const attempt = plan.attempt` — const, line 90
- `const run = async (label: string, action: ()` — const, line 100
- `const next = await action()` — const, line 103
- `const signIn = async ()` — const, line 114
- `const next = await run("signin", ()` — const, line 115
- `const manageUsage = ()` — const, line 125
- `const granted = plan.openrouterGrantedTasks ?? []` — const, line 131
- `const stopOpenRouter = ()` — const, line 132
- `const line = stateLine(plan)` — const, line 138
- `const needsSignIn = plan.state === "signed_out" || plan.state === "plan_usage_disabled" || plan.state === "store_error"` — const, line 139
- `const continueStyle =` — const, line 140
- `const linkStyle =` — const, line 150
- `const uses = [ ...profile.routes, ...(profile.activeProvider ? ["active provider"] : []), ...(profile.fallbackProvider ? ["fallback"] : []) ]` — const, line 258

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export: `ChatGPTPlanSettings`; references `ChatGPTPlanSettings`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ChatGPTPlanDto`
- [[Reference/Desktop/TypeScript/components/NativeMediaSettings|src/components/NativeMediaSettings.tsx]] — import-or-re-export; imports `SettingsStyles`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/plugin-opener`, `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Configure AI Providers|Configure AI Providers]] — owns provider setup.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/ChatGPTPlanSettings.test.tsx](../../../../../../apps/learnloop-tauri/src/components/ChatGPTPlanSettings.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_maintenance_feed.py](../../../../../../tests/test_maintenance_feed.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_doctor.py](../../../../../../tests/test_doctor.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/ChatGPTPlanSettings.tsx](../../../../../../apps/learnloop-tauri/src/components/ChatGPTPlanSettings.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
