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
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
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
| Source lines | 1248 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]]

## Public API

- `export function GoldenPathScreen(` — function, line 138

## Internal implementation anchors

- `type Checkpoint, } from "../components/goldenpath/shared"` — type, line 43
- `const RUN_STAGES: Array<` — const, line 51
- `function runCheckpoints(run: RunStateDto): Checkpoint[]` — function, line 63
- `const visited = new Set<string>(run.history.map((h)` — const, line 64
- `const currentIdx = RUN_STAGES.findIndex((s)` — const, line 65
- `let state: Checkpoint["state"] = "pending"` — let, line 67
- `function ServedFreshness(` — function, line 78
- `const INSTRUCTION_STATES = new Set(["instructing", "completing", "practicing", "integrating"])` — const, line 86
- `interface RunBundle` — interface, line 88
- `interface RunSurfaceResult<T>` — interface, line 103
- `async function readRunSurface<T>( label: string, request: Promise<T>, absentCodes: string[] = [], ): Promise<RunSurfaceResult<T>>` — function, line 108
- `const command = getCommandError(error)` — const, line 116
- `function fixtureBundle(): RunBundle` — function, line 122
- `const offline = !runId` — const, line 152
- `const load = useCallback(async ()` — const, line 158
- `const restore = await readRunSurface( "restoration", api.goldenPathRestore(runId), ["restore_unavailable"] )` — const, line 170
- `const message = errorMessage(error, "Could not load this Golden Path run.")` — const, line 206
- `const advance = useCallback(async ()` — const, line 216
- `const next = bundle.run.nextAction` — const, line 220
- `const acceptEdge = useCallback(async ()` — const, line 239
- `const declineEdge = useCallback(async ()` — const, line 252
- `const onKey = (e: KeyboardEvent)` — const, line 266
- `const tag = (e.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 267
- `const checkpoints = useMemo(()` — const, line 276
- `const invitation = depth?.invitation ?? restore?.invitation ?? null` — const, line 297
- `const workspaceOwnsTransition = !offline && (run.currentState === "triaging" || INSTRUCTION_STATES.has(run.currentState))` — const, line 300
- `const committedReason = triageStatus?.latest?.selectedReason ?? null` — const, line 302
- `const currentRung = ladderStatus?.currentStage ?? null` — const, line 303
- `const isCurrent = currentRung === s.stageKey` — const, line 386
- `function AssessmentWorkspace(` — function, line 608
- `const openAssessment = async ()` — const, line 624
- `const lockAnswer = async ()` — const, line 635
- `const item = await api.getPracticeItem(opened.practiceItemId)` — const, line 639
- `const submit = async ()` — const, line 646
- `const maxPoints = opened?.maxPoints ?? 4` — const, line 667
- `const TRIAGE_COARSE_OPTIONS = [` — const, line 748
- `const TRIAGE_SIGNATURE_OPTIONS = [` — const, line 753
- `const TRIAGE_EXPOSURE_OPTIONS = [` — const, line 762
- `const TRIAGE_TRACE_OPTIONS = [` — const, line 766
- `const TRIAGE_CONFIDENCE_OPTIONS = [` — const, line 770
- `function snakeReason(reason: string): string` — function, line 778
- `function TriageWorkspace(` — function, line 782
- `const committed = triageStatus?.latest ?? null` — const, line 805
- `const runTriage = async ()` — const, line 807
- `const res = await api.diagnosticTriage(` — const, line 810
- `const commitReason = async (reason: string)` — const, line 830
- `const res = await api.diagnosticTriageDecide(` — const, line 834
- `const needsDecision = result.tier === "two" && !result.autoCommitted && !result.routed` — const, line 849
- `const SCAFFOLD_OPTIONS = [` — const, line 930
- `function LadderWorkspace(` — function, line 936
- `const enter = async ()` — const, line 957
- `const res = await api.ladderEnter(` — const, line 960
- `const logOutcome = async (outcome: "pass" | "incorrect" | "gave_up")` — const, line 972
- `const res = await api.ladderAdvance(` — const, line 976
- `const disabled = busy || parentBusy` — const, line 992
- `function PoolWorkspace(` — function, line 1065
- `const pool = poolForRun.pool?.pool ?? null` — const, line 1081
- `const anchorsInVault = poolForRun.anchors.filter((a)` — const, line 1082
- `const requestAnchorVariant = async (ref: string, direction: "easier" | "harder")` — const, line 1087
- `const result = await api.requestRungVariant(` — const, line 1090
- `const run = async (fn: ()` — const, line 1101
- `const serve = async ()` — const, line 1113
- `const allAdmitted = pool != null && pool.surfaces.length > 0 && pool.surfaces.every((s)` — const, line 1125
- `const servable = pool != null && (pool.status === "reviewed" || pool.status === "active")` — const, line 1126
- `const anchor = poolForRun.anchors.find((a)` — const, line 1184

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `GoldenPathScreen`; references `GoldenPathScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AssessOpenDto`, `AssessResultDto`, `DepthInvitationResultDto`, `LadderAdvanceResultDto`, `LadderPolicyDto`, `LadderStatusDto`, `PoolDto`, `PoolForRunDto`, `PoolNextSurfaceDto`, `RestoreDto`, `RunStateDto`, `ServedSurfaceDto`, `TriageResultDto`, `TriageStatusDto`
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

- [tests/test_sidecar_golden_path.py](../../../../../../tests/test_sidecar_golden_path.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_golden_path_assessment.py](../../../../../../tests/test_sidecar_golden_path_assessment.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_golden_path_fixture.py](../../../../../../tests/test_golden_path_fixture.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/GoldenPathScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/GoldenPathScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
