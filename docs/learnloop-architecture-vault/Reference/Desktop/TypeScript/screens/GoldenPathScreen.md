---
title: "Desktop module · src/screens/GoldenPathScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.GoldenPathScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/GoldenPathScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/GoldenPathScreen.tsx"
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

# `src/screens/GoldenPathScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `GoldenPathScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/GoldenPathScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/GoldenPathScreen.tsx) |
| Source lines | 1276 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]]

## Public API

- `export function GoldenPathScreen(` — function, line 140
- `export function triageCoarseOptions(stuckPrompt: boolean = algoConfig().stuckPrompt)` — function, line 773

## Internal implementation anchors

- `type Checkpoint, } from "../components/goldenpath/shared"` — type, line 44
- `const RUN_STAGES: Array<` — const, line 53
- `function runCheckpoints(run: RunStateDto): Checkpoint[]` — function, line 65
- `const visited = new Set<string>(run.history.map((h)` — const, line 66
- `const currentIdx = RUN_STAGES.findIndex((s)` — const, line 67
- `let state: Checkpoint["state"] = "pending"` — let, line 69
- `function ServedFreshness(` — function, line 80
- `const INSTRUCTION_STATES = new Set(["instructing", "completing", "practicing", "integrating"])` — const, line 88
- `interface RunBundle` — interface, line 90
- `interface RunSurfaceResult<T>` — interface, line 105
- `async function readRunSurface<T>( label: string, request: Promise<T>, absentCodes: string[] = [], ): Promise<RunSurfaceResult<T>>` — function, line 110
- `const command = getCommandError(error)` — const, line 118
- `function fixtureBundle(): RunBundle` — function, line 124
- `const offline = !runId` — const, line 154
- `const load = useCallback(async ()` — const, line 162
- `const restore = await readRunSurface( "restoration", api.goldenPathRestore(runId), ["restore_unavailable"] )` — const, line 174
- `const message = errorMessage(error, "Could not load this Golden Path run.")` — const, line 210
- `const advance = useCallback(async ()` — const, line 220
- `const next = bundle.run.nextAction` — const, line 224
- `const advanced = await api.goldenPathAdvance(` — const, line 228
- `const acceptEdge = useCallback(async ()` — const, line 244
- `const declineEdge = useCallback(async ()` — const, line 257
- `const onKey = (e: KeyboardEvent)` — const, line 271
- `const tag = (e.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 273
- `const checkpoints = useMemo(()` — const, line 282
- `const invitation = depth?.invitation ?? restore?.invitation ?? null` — const, line 303
- `const workspaceOwnsTransition = !offline && (run.currentState === "triaging" || INSTRUCTION_STATES.has(run.currentState))` — const, line 306
- `const committedReason = triageStatus?.latest?.selectedReason ?? null` — const, line 308
- `const currentRung = ladderStatus?.currentStage ?? null` — const, line 309
- `const isCurrent = currentRung === s.stageKey` — const, line 397
- `function AssessmentWorkspace(` — function, line 619
- `const openAssessment = async ()` — const, line 635
- `const lockAnswer = async ()` — const, line 646
- `const item = await api.getPracticeItem(opened.practiceItemId)` — const, line 650
- `const submit = async ()` — const, line 657
- `const maxPoints = opened?.maxPoints ?? 4` — const, line 678
- `const TRIAGE_COARSE_OPTIONS = [` — const, line 759
- `const TRIAGE_COARSE_OPTIONS_STUCK = TRIAGE_COARSE_OPTIONS.map((option)` — const, line 767
- `const TRIAGE_SIGNATURE_OPTIONS = [` — const, line 776
- `const TRIAGE_EXPOSURE_OPTIONS = [` — const, line 785
- `const TRIAGE_TRACE_OPTIONS = [` — const, line 789
- `const TRIAGE_CONFIDENCE_OPTIONS = [` — const, line 793
- `function snakeReason(reason: string): string` — function, line 801
- `function TriageWorkspace(` — function, line 805
- `const committed = triageStatus?.latest ?? null` — const, line 828
- `const runTriage = async ()` — const, line 830
- `const res = await api.diagnosticTriage(` — const, line 833
- `const commitReason = async (reason: string)` — const, line 853
- `const res = await api.diagnosticTriageDecide(` — const, line 857
- `const needsDecision = result.tier === "two" && !result.autoCommitted && !result.routed` — const, line 872
- `const SCAFFOLD_OPTIONS = [` — const, line 958
- `function LadderWorkspace(` — function, line 964
- `const enter = async ()` — const, line 985
- `const res = await api.ladderEnter(` — const, line 988
- `const logOutcome = async (outcome: "pass" | "incorrect" | "gave_up")` — const, line 1000
- `const res = await api.ladderAdvance(` — const, line 1004
- `const disabled = busy || parentBusy` — const, line 1020
- `function PoolWorkspace(` — function, line 1093
- `const pool = poolForRun.pool?.pool ?? null` — const, line 1109
- `const anchorsInVault = poolForRun.anchors.filter((a)` — const, line 1110
- `const requestAnchorVariant = async (ref: string, direction: "easier" | "harder")` — const, line 1115
- `const result = await api.requestRungVariant(` — const, line 1118
- `const run = async (fn: ()` — const, line 1129
- `const serve = async ()` — const, line 1141
- `const allAdmitted = pool != null && pool.surfaces.length > 0 && pool.surfaces.every((s)` — const, line 1153
- `const servable = pool != null && (pool.status === "reviewed" || pool.status === "active")` — const, line 1154
- `const anchor = poolForRun.anchors.find((a)` — const, line 1212

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: dynamic import; no named call claim

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AssessOpenDto`, `AssessResultDto`, `DepthInvitationResultDto`, `LadderAdvanceResultDto`, `LadderPolicyDto`, `LadderStatusDto`, `PoolDto`, `PoolForRunDto`, `PoolNextSurfaceDto`, `RestoreDto`, `RunStateDto`, `ServedSurfaceDto`, `TriageResultDto`, `TriageStatusDto`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/ItemPresentation|src/components/ItemPresentation.tsx]] — import-or-re-export; imports `ItemPresentation`
- [[Reference/Desktop/TypeScript/components/goldenpath/TriageDecisionAid|src/components/goldenpath/TriageDecisionAid.tsx]] — import-or-re-export; imports `TriageDecisionAid`
- [[Reference/Desktop/TypeScript/components/goldenpath/shared|src/components/goldenpath/shared.tsx]] — import-or-re-export; imports `AffectTap`, `BoundaryView`, `CalibrationBadge`, `Checkpoint`, `CheckpointLadder`, `ClaimBadge`, `DepthEnvelopeCard`, `IntervalBar`, `PrimaryButton`, `SecondaryButton`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`, `TermSelect`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/fixtures/goldenpath/index|src/fixtures/goldenpath/index.ts]] — import-or-re-export; imports `goldenPathFixtures`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — places the staged journey in the user-facing session path.
- [[Concepts/Learning System#The feedback loop|learning feedback loop]] — owns the learning intent behind the fixture or surface.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/GoldenPathScreen.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/GoldenPathScreen.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_golden_path.py](../../../../../../tests/test_sidecar_golden_path.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_golden_path_assessment.py](../../../../../../tests/test_sidecar_golden_path_assessment.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_golden_path_fixture.py](../../../../../../tests/test_golden_path_fixture.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/GoldenPathScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/GoldenPathScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
