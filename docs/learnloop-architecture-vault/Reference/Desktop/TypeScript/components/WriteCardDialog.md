---
title: "Desktop module · src/components/WriteCardDialog.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.WriteCardDialog"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/WriteCardDialog.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/WriteCardDialog.tsx"
source_commit: "02c3e6e10f5ca37e16cef05657ee693b33502fb7"
source_commit_timestamp: "2026-07-21T13:26:14-04:00"
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

# `src/components/WriteCardDialog.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `WriteCardDialog` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/WriteCardDialog.tsx](../../../../../../apps/learnloop-tauri/src/components/WriteCardDialog.tsx) |
| Source lines | 271 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `02c3e6e10f5ca37e16cef05657ee693b33502fb7` |
| Commit timestamp | `2026-07-21T13:26:14-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] → [[Reference/Desktop/TypeScript/components/WriteCardDialog|src/components/WriteCardDialog.tsx]]

## Public API

- `export function WriteCardDialog(` — function, line 18

## Internal implementation anchors

- `const PRACTICE_MODES = [` — const, line 11
- `let alive = true` — let, line 39
- `const seen = new Map<string, string>()` — const, line 44
- `const options = Array.from(seen, ([value, label])` — const, line 50
- `const handler = (e: KeyboardEvent)` — const, line 65
- `const options = useMemo(()` — const, line 72
- `const base = loOptions ?? []` — const, line 73
- `const canSubmit = !busy && learningObjectId !== "" && prompt.trim() !== "" && expectedAnswer.trim() !== ""` — const, line 80
- `const submit = async ()` — const, line 82
- `const hints = hintsText .split("\n") .map((h)` — const, line 87
- `const res = await api.authorPracticeItem(` — const, line 91
- `const command = err && typeof err === "object" && "code" in err ? (err as CommandError) : null` — const, line 101
- `function Label(` — function, line 190
- `const textareaStyle: CSSProperties =` — const, line 198
- `const backdropStyle: CSSProperties =` — const, line 211
- `const modalStyle: CSSProperties =` — const, line 223
- `const headerStyle: CSSProperties =` — const, line 235
- `const footerStyle: CSSProperties =` — const, line 244
- `const primaryBtn: CSSProperties =` — const, line 253
- `const ghostBtn: CSSProperties =` — const, line 263

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `WriteCardDialog`; references `WriteCardDialog`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `TermSelect`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/WriteCardDialog.tsx](../../../../../../apps/learnloop-tauri/src/components/WriteCardDialog.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
