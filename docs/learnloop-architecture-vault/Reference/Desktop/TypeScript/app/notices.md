---
title: "Desktop module · src/app/notices.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.notices"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/notices.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/notices.ts"
source_commit: "719233b9e6a9f5c689fc3466bf87c6e4521b93bb"
source_commit_timestamp: "2026-10-21T13:40:43-04:00"
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

# `src/app/notices.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `NEEDS_SESSION`, `noticeAfterSessionBegins`, `NoticeCondition`, `ShellNotice` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/notices.ts](../../../../../../apps/learnloop-tauri/src/app/notices.ts) |
| Source lines | 207 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `719233b9e6a9f5c689fc3466bf87c6e4521b93bb` |
| Commit timestamp | `2026-10-21T13:40:43-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/notices|src/app/notices.ts]]

## Public API

- `export const NEEDS_SESSION =` — const, line 20
- `export function noticeAfterSessionBegins(current: string | null): string | null` — function, line 34
- `export type NoticeCondition = "session"` — type, line 41
- `export interface ShellNotice` — interface, line 43
- `export type NoticeInput = Omit<ShellNotice, "id" | "shownAt" | "retrying" | "retry" | "source"> & (` — type, line 72
- `export const NOTICE_TTL_MS = 5000` — const, line 76
- `export const MAX_VISIBLE_NOTICES = 3` — const, line 81
- `export function addNotice(list: ShellNotice[], input: NoticeInput): ShellNotice[]` — function, line 85
- `export function dismissSource(list: ShellNotice[], source: string): ShellNotice[]` — function, line 102
- `export function runNoticeRetry(notice: ShellNotice, onChange: Dispatch<SetStateAction<ShellNotice[]>>): void` — function, line 116
- `export function dismissNotice(list: ShellNotice[], id: string): ShellNotice[]` — function, line 150
- `export function resolveNotices(list: ShellNotice[], condition: NoticeCondition): ShellNotice[]` — function, line 155
- `export function visibleNotices(list: ShellNotice[], holding: boolean): ShellNotice[]` — function, line 163
- `export function restartHidden(list: ShellNotice[], visibleIds: string[]): ShellNotice[]` — function, line 176
- `export function markShown(list: ShellNotice[], ids: string[], now: number): ShellNotice[]` — function, line 187
- `export function expireNotices(list: ShellNotice[], now: number, ttlMs: number = NOTICE_TTL_MS): ShellNotice[]` — function, line 199
- `export function sessionNotice(need: keyof typeof NEEDS_SESSION): NoticeInput` — function, line 205

## Internal implementation anchors

- `const SESSION_NOTICES: ReadonlySet<string> = new Set(Object.values(NEEDS_SESSION))` — const, line 30
- `let nextId = 0` — let, line 83
- `const source = input.source ? input.source : null` — const, line 87
- `const notice: ShellNotice =` — const, line 88
- `const rest = list.filter((existing)` — const, line 93
- `const next = list.filter((notice)` — const, line 103
- `const retry = notice.retry` — const, line 117
- `const source = notice.source` — const, line 118
- `let outcome: Promise<unknown>` — let, line 121
- `function retryFailure(notice: ShellNotice, source: string, retry: NoticeRetry, error: unknown): NoticeInput` — function, line 138
- `const command = getCommandError(error)` — const, line 139
- `const base =` — const, line 140
- `const next = list.filter((notice)` — const, line 156
- `const errors = list.filter((notice)` — const, line 164
- `const room = MAX_VISIBLE_NOTICES - errors.length` — const, line 165
- `const notices = holding || room <= 0 ? [] : list.filter((notice)` — const, line 166
- `const chosen = new Set([...errors, ...notices].map((notice)` — const, line 167
- `let changed = false` — let, line 177
- `const next = list.map((notice)` — const, line 178
- `let changed = false` — let, line 188
- `const next = list.map((notice)` — const, line 189
- `const next = list.filter((notice)` — const, line 200

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `NEEDS_SESSION`, `NoticeInput`, `ShellNotice`, `addNotice`, `dismissNotice`, `noticeAfterSessionBegins`, `resolveNotices`, `sessionNotice`; references `NEEDS_SESSION`, `NoticeInput`, `ShellNotice`, `addNotice`, `dismissNotice`, `noticeAfterSessionBegins`, `resolveNotices`, `sessionNotice`
- [[Reference/Desktop/TypeScript/components/NoticeHost|src/components/NoticeHost.tsx]] — import-or-re-export: `NOTICE_TTL_MS`, `ShellNotice`, `dismissNotice`, `expireNotices`, `markShown`, `restartHidden`, `runNoticeRetry`, `visibleNotices`; references `NOTICE_TTL_MS`, `ShellNotice`, `dismissNotice`, `expireNotices`, `markShown`, `restartHidden`, `runNoticeRetry`, `visibleNotices`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `MessageKind`, `NoticeRetry`, `errorMessage`, `getCommandError`, `retryRan`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/NoticeHost.test.tsx](../../../../../../apps/learnloop-tauri/src/components/NoticeHost.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/notices.test.ts](../../../../../../apps/learnloop-tauri/src/app/notices.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/notices.shell.test.ts](../../../../../../apps/learnloop-tauri/src/app/notices.shell.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/notices.ts](../../../../../../apps/learnloop-tauri/src/app/notices.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
