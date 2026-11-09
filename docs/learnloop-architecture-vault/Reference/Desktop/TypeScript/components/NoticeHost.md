---
title: "Desktop module · src/components/NoticeHost.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.NoticeHost"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/NoticeHost.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/NoticeHost.tsx"
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

# `src/components/NoticeHost.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `NoticeHost` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/NoticeHost.tsx](../../../../../../apps/learnloop-tauri/src/components/NoticeHost.tsx) |
| Source lines | 106 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/NoticeHost|src/components/NoticeHost.tsx]]

## Public API

- `export function NoticeHost(` — function, line 19

## Internal implementation anchors

- `type ShellNotice } from "../app/notices"` — type, line 16
- `const visible = useMemo(()` — const, line 29
- `const unstamped = visible.filter((notice)` — const, line 30
- `const visibleIds = visible.map((notice)` — const, line 31
- `const offScreenStamped = notices.some( (notice)` — const, line 32
- `const ids = visibleIds ? visibleIds.split(" ") : []` — const, line 40
- `const ids = unstamped.split(" ")` — const, line 47
- `const nextExpiry = visible.reduce<number | null>((soonest, notice)` — const, line 52
- `const at = notice.shownAt + NOTICE_TTL_MS` — const, line 54
- `const timer = window.setTimeout(()` — const, line 59
- `function NoticeRow(` — function, line 78
- `const error = notice.kind === "error"` — const, line 80

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `NoticeHost`; references `NoticeHost`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/app/notices|src/app/notices.ts]] — import-or-re-export; imports `NOTICE_TTL_MS`, `ShellNotice`, `dismissNotice`, `expireNotices`, `markShown`, `restartHidden`, `runNoticeRetry`, `visibleNotices`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/NoticeHost.test.tsx](../../../../../../apps/learnloop-tauri/src/components/NoticeHost.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/NoticeHost.tsx](../../../../../../apps/learnloop-tauri/src/components/NoticeHost.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
