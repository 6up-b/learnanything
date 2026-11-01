---
title: "Desktop module · src/components/ConceptAnimationSection.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.ConceptAnimationSection"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/ConceptAnimationSection.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/ConceptAnimationSection.tsx"
source_commit: "73e04e71c69fef5371cef306d228eedd8bf67836"
source_commit_timestamp: "2026-11-01T08:37:27-05:00"
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

# `src/components/ConceptAnimationSection.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `ConceptAnimationSection` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/ConceptAnimationSection.tsx](../../../../../../apps/learnloop-tauri/src/components/ConceptAnimationSection.tsx) |
| Source lines | 309 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `73e04e71c69fef5371cef306d228eedd8bf67836` |
| Commit timestamp | `2026-11-01T08:37:27-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] → [[Reference/Desktop/TypeScript/components/ConceptAnimationSection|src/components/ConceptAnimationSection.tsx]]

## Public API

- `export function ConceptAnimationSection(` — function, line 56

## Internal implementation anchors

- `const PENDING_STATUSES = new Set(["queued", "generating", "validating", "rendering"])` — const, line 8
- `const PHASE_LABEL: Record<string, Record<string, string>> =` — const, line 10
- `function phaseLabel(status: string, renderer: string): string` — function, line 25
- `const LINK_STYLE =` — const, line 29
- `function StoryboardList(` — function, line 39
- `const pollRef = useRef<number | null>(null)` — const, line 64
- `const stopPolling = ()` — const, line 66
- `const pollStatus = (animationId: string, renderer: string = "manim")` — const, line 73
- `const interval = renderer === "video_model" ? 5000 : 2000` — const, line 77
- `let cancelled = false` — let, line 90
- `const rows = result.animations ?? []` — const, line 100
- `const preferred = rows.find((row)` — const, line 101
- `const generate = async ()` — const, line 117
- `const requested = await api.requestConceptAnimation(` — const, line 121
- `const videoRenderer = runtime?.renderer === "video_model"` — const, line 152

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `ConceptAnimationSection`; references `ConceptAnimationSection`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AnimationRuntimeDto`, `ConceptAnimationDto`, `StoryboardDto`
- [[Reference/Desktop/TypeScript/components/AnimationPlayer|src/components/AnimationPlayer.tsx]] — import-or-re-export; imports `AnimationPlayer`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Configure AI Providers|Configure AI Providers]] — owns provider setup.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/ConceptAnimationSection.tsx](../../../../../../apps/learnloop-tauri/src/components/ConceptAnimationSection.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
