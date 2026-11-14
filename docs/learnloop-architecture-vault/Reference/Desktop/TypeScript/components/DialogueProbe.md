---
title: "Desktop module · src/components/DialogueProbe.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.DialogueProbe"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/DialogueProbe.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/DialogueProbe.tsx"
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

# `src/components/DialogueProbe.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `DialogueProbe` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/DialogueProbe.tsx](../../../../../../apps/learnloop-tauri/src/components/DialogueProbe.tsx) |
| Source lines | 418 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]] → [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]]

## Public API

- `export function DialogueProbePanel(` — function, line 35

## Internal implementation anchors

- `const TURN_KIND_LABEL: Record<string, string> =` — const, line 20
- `interface SubmittedTurn` — interface, line 27
- `type Phase = "starting" | "asking" | "submitting" | "ending" | "done"` — type, line 33
- `const turnOpenedAtMs = useRef(Date.now())` — const, line 62
- `const activeClock = useAttemptClock()` — const, line 65
- `const elapsedSeconds = ()` — const, line 66
- `const stuckPrompt = algoConfig().stuckPrompt` — const, line 72
- `const dialogueState = useRef<string | null>(null)` — const, line 76
- `const textareaRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 77
- `const fail = useCallback( (error: unknown)` — const, line 79
- `const endBlock = useCallback(async ()` — const, line 87
- `const result = await api.endProbeDialogue(dialogueState.current)` — const, line 94
- `const advance = useCallback(async ()` — const, line 102
- `const next = await api.nextProbeDialogueTurn(dialogueState.current)` — const, line 105
- `const started = useRef(false)` — const, line 128
- `const submitTurn = useCallback( async (dontKnow: boolean)` — const, line 145
- `const recorded = await api.recordProbeDialogueTurn(dialogueState.current, turn.presentationId)` — const, line 177
- `const stopAndTeach = useCallback(async ()` — const, line 208
- `const practiceItemId = turn.practiceItemId` — const, line 213
- `let stopped: StopProbeResultDto | null = null` — let, line 214
- `let ended: ProbeBlockEndDto | null = null` — let, line 225
- `const onKey = (event: KeyboardEvent)` — const, line 243

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]] — import-or-re-export: `DialogueProbePanel`; references `DialogueProbePanel`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `DialogueTurnDto`, `GuidedRedoDto`, `ProbeBlockEndDto`, `StopProbeResultDto`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `STUCK_PROMPT_TEXT`, `algoConfig`
- [[Reference/Desktop/TypeScript/app/checkHandoff|src/app/checkHandoff.ts]] — import-or-re-export; imports `CheckHandoff`, `STOP_AND_TEACH_LABEL`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/ProbeBlockResult|src/components/ProbeBlockResult.tsx]] — import-or-re-export; imports `ProbeBlockResult`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `Card`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/useAttemptClock|src/screens/useAttemptClock.ts]] — import-or-re-export; imports `useAttemptClock`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.
- [[Concepts/Diagnosis and Remediation#Episode lifecycle|diagnosis episode lifecycle]] — owns diagnostic and repair policy.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/DialogueProbe.test.tsx](../../../../../../apps/learnloop-tauri/src/components/DialogueProbe.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/DialogueProbe.tsx](../../../../../../apps/learnloop-tauri/src/components/DialogueProbe.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
