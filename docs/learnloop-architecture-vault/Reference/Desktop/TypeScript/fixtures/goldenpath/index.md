---
title: "Desktop module · src/fixtures/goldenpath/index.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.fixtures.goldenpath.index"
language: "TypeScript"
area: "TypeScript/fixtures/goldenpath"
source_path: "apps/learnloop-tauri/src/fixtures/goldenpath/index.ts"
source_paths:
  - "apps/learnloop-tauri/src/fixtures/goldenpath/index.ts"
source_commit: "02c3e6e10f5ca37e16cef05657ee693b33502fb7"
source_commit_timestamp: "2026-07-21T13:26:14-04:00"
source_worktree_state: "clean"
activation_kind: "entry-reachable build graph"
activation_evidence: "Imported through a current Reader/GoldenPath screen reachable from src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/fixtures/goldenpath/index.ts`

Area: [[Reference/Desktop/TypeScript/fixtures/goldenpath/_area|TypeScript/fixtures/goldenpath]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Exposes deterministic `index` fixture data for a reproducible desktop scenario.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/fixtures/goldenpath/index.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/index.ts) |
| Source lines | 60 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/fixtures/goldenpath/_area|TypeScript/fixtures/goldenpath]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `02c3e6e10f5ca37e16cef05657ee693b33502fb7` |
| Commit timestamp | `2026-07-21T13:26:14-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> Imported through a current Reader/GoldenPath screen reachable from src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/ExemplarConfirmDialog|src/components/ExemplarConfirmDialog.tsx]] → [[Reference/Desktop/TypeScript/fixtures/goldenpath/index|src/fixtures/goldenpath/index.ts]]

## Public API

- `export const goldenPathFixtures =` — const, line 41
- `export type GoldenPathFixtures = typeof goldenPathFixtures` — type, line 60

## Internal implementation anchors

No non-exported declaration anchor was detected by the static extractor.

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/ExemplarConfirmDialog|src/components/ExemplarConfirmDialog.tsx]] — import-or-re-export: `goldenPathFixtures`; references `goldenPathFixtures`
- [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]] — import-or-re-export: `goldenPathFixtures`; references `goldenPathFixtures`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AssessOpenDto`, `AssessResultDto`, `BlueprintVersionDto`, `BoundaryDiffDto`, `ConfirmReceiptDto`, `DepthInvitationResultDto`, `LadderPolicyDto`, `PoolDto`, `PoolNextSurfaceDto`, `ReaderPromptContractDto`, `RestoreDto`, `RunStateDto`, `TriageResultDto`

### Assets, platform, and third-party dependencies

- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/assessOpen.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/assessOpen.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/assessResult.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/assessResult.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/blueprintVersion.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/blueprintVersion.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/boundaryDiff.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/boundaryDiff.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/confirmReceipt.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/confirmReceipt.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/depthInvitation.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/depthInvitation.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/ladderPolicy.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/ladderPolicy.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/poolAssembled.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/poolAssembled.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/poolNextSurface.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/poolNextSurface.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/readerPromptContract.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/readerPromptContract.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/restore.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/restore.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/runStatusAssessed.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/runStatusAssessed.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/runStatusReady.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/runStatusReady.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/runStatusReadyToAssess.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/runStatusReadyToAssess.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/triageDecisive.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/triageDecisive.json)
- Local asset: [apps/learnloop-tauri/src/fixtures/goldenpath/triageProvisional.json](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/triageProvisional.json)

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — places the staged journey in the user-facing session path.
- [[Concepts/Learning System#The feedback loop|learning feedback loop]] — owns the learning intent behind the fixture or surface.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_golden_path.py](../../../../../../../tests/test_sidecar_golden_path.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_golden_path_assessment.py](../../../../../../../tests/test_sidecar_golden_path_assessment.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_golden_path_fixture.py](../../../../../../../tests/test_golden_path_fixture.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/fixtures/goldenpath/index.ts](../../../../../../../apps/learnloop-tauri/src/fixtures/goldenpath/index.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
