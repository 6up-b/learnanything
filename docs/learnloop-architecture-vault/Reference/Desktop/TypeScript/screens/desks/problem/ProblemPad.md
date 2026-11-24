---
title: "Desktop module · src/screens/desks/problem/ProblemPad.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.problem.ProblemPad"
language: "TypeScript"
area: "TypeScript/screens/desks/problem"
source_path: "apps/learnloop-tauri/src/screens/desks/problem/ProblemPad.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/problem/ProblemPad.tsx"
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

# `src/screens/desks/problem/ProblemPad.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/problem/_area|TypeScript/screens/desks/problem]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ProblemPad` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/problem/ProblemPad.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/problem/ProblemPad.tsx) |
| Source lines | 154 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/problem/_area|TypeScript/screens/desks/problem]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/problem/ProblemPad|src/screens/desks/problem/ProblemPad.tsx]]

## Public API

- `export interface ProblemHost` — interface, line 15
- `export interface ProblemInk` — interface, line 28
- `export function ProblemPad(` — function, line 58

## Internal implementation anchors

- `function ReadingNote(` — function, line 47
- `const gone = useRef(onGone)` — const, line 48
- `const problem = useSyncExternalStore(subscribeProblems, ()` — const, line 59
- `const told = useRef(new Set<string>())` — const, line 61
- `const handwritten: HandwrittenWork | undefined = ink && ink.lines.length ?` — const, line 62
- `const unseen = ink.lines.map((line, index)` — const, line 68
- `const here = lineId ? ink.lines.find((line)` — const, line 69
- `const resume = async ()` — const, line 85
- `const result = await api.workbenchOpen(` — const, line 89
- `const card = problem?.card ?? host.cardFor(result.session.sourceId ?? null)` — const, line 90
- `const reopen = async ()` — const, line 99
- `const result = await api.workbenchReopen(` — const, line 102
- `const line = !problem ? "✎ a problem from your reading" : problem.away === "abandoned" ? "abandoned · your steps are kept" : "set aside · your steps are kept"` — const, line 112
- `const readOnly = problem.readOnly || session.status === "submitted"` — const, line 127
- `const card = problem.card ?? host.cardFor(result.session.sourceId ?? null)` — const, line 144
- `const spanId = problem.spanId ?? result.session.spanIds[0] ?? null` — const, line 145

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `ProblemHost`; references `ProblemHost`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export: `ProblemInk`, `ProblemPad`; references `ProblemInk`, `ProblemPad`
- [[Reference/Desktop/TypeScript/screens/desks/pads/host|src/screens/desks/pads/host.ts]] — import-or-re-export: `ProblemHost`; references `ProblemHost`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SourceLibraryCard`, `WorkbenchSessionDto`, `WorkbenchSubmitDto`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/desks/problem/problemPads|src/screens/desks/problem/problemPads.ts]] — import-or-re-export; imports `handOver`, `noteProblem`, `problemOf`, `subscribeProblems`
- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export; imports `HandwrittenWork`, `Workbench`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/problem/ProblemPad.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/problem/ProblemPad.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
