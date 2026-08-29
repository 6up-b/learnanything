---
title: "Desktop module · src/screens/MaintenanceScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.MaintenanceScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/MaintenanceScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/MaintenanceScreen.tsx"
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

# `src/screens/MaintenanceScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `MaintenanceScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/MaintenanceScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/MaintenanceScreen.tsx) |
| Source lines | 1279 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]]

## Public API

- `export function MaintenanceScreen(` — function, line 70

## Internal implementation anchors

- `function spanIdFromLocator(locator: string | null): string | null` — function, line 34
- `const SEVERITY_PILL: Record<MaintenanceSeverity, PillColor> =` — const, line 38
- `const RESOLUTION_KINDS:` — const, line 44
- `const panel: CSSProperties =` — const, line 51
- `const btn: CSSProperties =` — const, line 59
- `const reportError = useCallback( (err: unknown)` — const, line 102
- `const load = useCallback(()` — const, line 107
- `const noticeAction = async (notice: MaintenanceNoticeDto, action: "dismiss" | "snooze")` — const, line 123
- `const resolveDirection = async ( edgeId: string, resolution: EdgeDirectionResolution, rationale: string )` — const, line 132
- `const runAppend = async (sourceSetId: string)` — const, line 145
- `const res = await api.appendSource(` — const, line 149
- `const resolve = async (conflict: SourceConflictDto, kind: ConflictResolutionKind)` — const, line 159
- `let resolution: Record<string, unknown> =` — let, line 161
- `const canonical = window.prompt("Canonical notation?") ?? ""` — const, line 163
- `const alternate = window.prompt("Alternate notation?") ?? ""` — const, line 164
- `const bySeverity = (sev: MaintenanceSeverity)` — const, line 175
- `const scheduleColdProbes = async ()` — const, line 177
- `const transitionProbe = async (candidateId: string, toStatus: string)` — const, line 189
- `const needsReviewer = toStatus === "reviewed" || toStatus === "rejected"` — const, line 190
- `const reviewer = needsReviewer ? window.prompt("Reviewer name?")?.trim() : null` — const, line 191
- `const reason = needsReviewer ? window.prompt("Review reason (optional)?")?.trim() || null : null` — const, line 193
- `const generateCommissioningPractice = async ()` — const, line 206
- `const result = await api.generateCommissioningPractice(` — const, line 214
- `const applyIntegrationBackfill = async ()` — const, line 223
- `const confirmed = window.confirm( "Apply the reviewed D3 coordination backfill? This rewrites authored learning-object YAML, rebuilds affected state, and records one learner-visible recalibration boundary." )` — const, line 224
- `function metricValue(metric: MeasurementHealthDto["scoreboard"]["metrics"][number]): string` — function, line 441
- `function MeasurementHealthPanel(` — function, line 447
- `const reach = health.reachability.summary` — const, line 474
- `const inference = health.inferencePrecheck.summary` — const, line 475
- `const cold = health.coldProbes.coverage` — const, line 476
- `const backfill = health.integrationBackfill.summary` — const, line 477
- `const backfillChanges = (backfill.dispositions.DROP ?? 0) + (backfill.dispositions.LOWER ?? 0)` — const, line 478
- `const queue = health.reachability.cells.filter((cell)` — const, line 480
- `const nextStatus = (status: string): string | null` — const, line 481
- `const next = nextStatus(candidate.status)` — const, line 718
- `function TraceEvidenceBlock(` — function, line 750
- `const t = traceEvidence` — const, line 755
- `function InstrumentAuditBlock(` — function, line 810
- `const hunts = audit.errorHuntOutcomes` — const, line 811
- `const coverage = audit.discriminationProfileCoverage` — const, line 812
- `const ladders = audit.ladderedStems.filter((stem)` — const, line 813
- `const commissioning = audit.contrastPairCommissioning.summary` — const, line 814
- `function ClarificationRateBlock(` — function, line 962
- `const c = clarificationRate` — const, line 967
- `function ConflictSide(` — function, line 1005
- `const spanId = spanIdFromLocator(locator)` — const, line 1020
- `const openable = extractionId != null && spanId != null` — const, line 1021
- `function StudyMapDiffView(` — function, line 1038
- `const diff = append.studyMapDiff` — const, line 1039
- `const th: CSSProperties =` — const, line 1085
- `const td: CSSProperties =` — const, line 1086
- `const DIRECTION_ACTIONS:` — const, line 1090
- `const REASON_COPY: Record<AmbiguousEdgeDirectionDetail["reason"], string> =` — const, line 1097
- `function AmbiguousEdgeCard(` — function, line 1103
- `const detail = notice.detail as unknown as AmbiguousEdgeDirectionDetail | null` — const, line 1112
- `const edgeId = detail?.edgeId ?? (notice.action.edgeId as string | null | undefined) ?? null` — const, line 1115
- `const evidence = detail?.evidence ?? null` — const, line 1116
- `const src = detail.sourceConcept` — const, line 1120
- `const tgt = detail.targetConcept` — const, line 1121
- `function ConceptRef(` — function, line 1222
- `function RestructureRequestCard(` — function, line 1243
- `const detail = notice.detail as unknown as RestructureRequestDetail | null` — const, line 1250

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `MaintenanceScreen`; references `MaintenanceScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AmbiguousEdgeDirectionDetail`, `AppendResultDto`, `ConflictResolutionKind`, `EdgeDirectionResolution`, `ExamReadinessReportDto`, `GenerateCommissioningPracticeResult`, `MaintenanceNoticeDto`, `MaintenanceSeverity`, `MeasurementHealthDto`, `RestructureRequestDetail`, `SourceConflictDto`, `SourceSetSummaryDto`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export; imports `OpenInSource`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Dim`, `Divider`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`, `SectionHeader`, `TermSelect`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Inspect Persistent State|Inspect Persistent State]] — owns safe inspection.
- [[Architecture/State and Persistence#Open modes and migrations|state open modes]] — owns persistence safety.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_maintenance_feed.py](../../../../../../tests/test_maintenance_feed.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_doctor.py](../../../../../../tests/test_doctor.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/MaintenanceScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/MaintenanceScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
