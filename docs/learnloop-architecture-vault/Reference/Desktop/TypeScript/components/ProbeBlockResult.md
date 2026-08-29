---
title: "Desktop module · src/components/ProbeBlockResult.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.ProbeBlockResult"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/ProbeBlockResult.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/ProbeBlockResult.tsx"
source_commit: "61ea8d0d1aa6bc4241581ec16263f6514df44332"
source_commit_timestamp: "2026-08-03T22:04:53-04:00"
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

# `src/components/ProbeBlockResult.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `ProbeBlockResult` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/ProbeBlockResult.tsx](../../../../../../apps/learnloop-tauri/src/components/ProbeBlockResult.tsx) |
| Source lines | 198 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `61ea8d0d1aa6bc4241581ec16263f6514df44332` |
| Commit timestamp | `2026-08-03T22:04:53-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] → [[Reference/Desktop/TypeScript/components/ProbeBlockResult|src/components/ProbeBlockResult.tsx]]

## Public API

- `export function ProbeBlockResult(` — function, line 27

## Internal implementation anchors

- `const ROUTE_LABEL: Record<string, string> =` — const, line 21
- `const startGuidedRedo = async (attemptId: string)` — const, line 58
- `const redo = await api.startGuidedRedo(attemptId)` — const, line 62
- `const reportContest = async ( attemptId: string, factorId: string | null, reason: UnresolvedCauseSelfReportResponse, )` — const, line 71
- `const refreshed = await api.getFeedback(attemptId)` — const, line 87

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]] — import-or-re-export: `ProbeBlockResult`; references `ProbeBlockResult`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export: `ProbeBlockResult`; references `ProbeBlockResult`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `GuidedRedoDto`, `ProbeBlockEndDto`, `UnresolvedCauseSelfReportResponse`
- [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]] — import-or-re-export; imports `ProbeRemintAction`
- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export; imports `CausalFeedbackPanel`
- [[Reference/Desktop/TypeScript/components/RepairAffordances|src/components/RepairAffordances.tsx]] — import-or-re-export; imports `CommonRepairCard`, `GuidedRedoAffordance`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `Pill`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.
- [[Concepts/Diagnosis and Remediation#Episode lifecycle|diagnosis episode lifecycle]] — owns diagnostic and repair policy.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_diagnostic.py](../../../../../../tests/test_sidecar_diagnostic.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/ProbeBlockResult.tsx](../../../../../../apps/learnloop-tauri/src/components/ProbeBlockResult.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
