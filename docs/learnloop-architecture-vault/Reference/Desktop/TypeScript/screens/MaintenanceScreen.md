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
source_commit: "8afe46254010114346f91d8643dc3ff29d8d8fe2"
source_commit_timestamp: "2026-09-03T10:56:04-07:00"
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
| Source lines | 1297 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `8afe46254010114346f91d8643dc3ff29d8d8fe2` |
| Commit timestamp | `2026-09-03T10:56:04-07:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]]

## Public API

- `export function MaintenanceScreen(` — function, line 72

## Internal implementation anchors

- `function spanIdFromLocator(locator: string | null): string | null` — function, line 36
- `const SEVERITY_PILL: Record<MaintenanceSeverity, PillColor> =` — const, line 40
- `const RESOLUTION_KINDS:` — const, line 46
- `const panel: CSSProperties =` — const, line 53
- `const btn: CSSProperties =` — const, line 61
- `const feedQuery = useCachedQuery(["maintenance_feed", subjectId], ()` — const, line 91
- `const conflictsQuery = useCachedQuery(["list_source_conflicts", "open"], ()` — const, line 94
- `const readinessQuery = useCachedQuery(["exam_readiness", subjectId], ()` — const, line 97
- `const sourceSetsQuery = useCachedQuery(["list_source_sets"], ()` — const, line 100
- `const healthQuery = useCachedQuery(["get_measurement_health"], ()` — const, line 101
- `const adjudicationQuery = useCachedQuery(["adjudication_queue",` — const, line 104
- `const notices: MaintenanceNoticeDto[] = feedQuery.data?.notices ?? []` — const, line 107
- `const conflicts: SourceConflictDto[] = conflictsQuery.data?.conflicts ?? []` — const, line 108
- `const readiness: ExamReadinessReportDto | null = readinessQuery.data?.report ?? null` — const, line 109
- `const sourceSets: SourceSetSummaryDto[] = sourceSetsQuery.data?.sourceSets ?? []` — const, line 110
- `const measurementHealth: MeasurementHealthDto | null = healthQuery.data ?? null` — const, line 111
- `const adjudicationOwed: number | null = adjudicationQuery.data?.total ?? null` — const, line 113
- `const reportError = useCallback( (err: unknown)` — const, line 125
- `const reload = ()` — const, line 131
- `const loadError = feedQuery.error ?? conflictsQuery.error ?? readinessQuery.error ?? sourceSetsQuery.error ?? healthQuery.error` — const, line 142
- `const noticeAction = async (notice: MaintenanceNoticeDto, action: "dismiss" | "snooze")` — const, line 148
- `const resolveDirection = async ( edgeId: string, resolution: EdgeDirectionResolution, rationale: string )` — const, line 156
- `const runAppend = async (sourceSetId: string)` — const, line 168
- `const res = await api.appendSource(` — const, line 172
- `const resolve = async (conflict: SourceConflictDto, kind: ConflictResolutionKind)` — const, line 181
- `let resolution: Record<string, unknown> =` — let, line 183
- `const canonical = window.prompt("Canonical notation?") ?? ""` — const, line 185
- `const alternate = window.prompt("Alternate notation?") ?? ""` — const, line 186
- `const bySeverity = (sev: MaintenanceSeverity)` — const, line 196
- `const scheduleColdProbes = async ()` — const, line 198
- `const transitionProbe = async (candidateId: string, toStatus: string)` — const, line 209
- `const needsReviewer = toStatus === "reviewed" || toStatus === "rejected"` — const, line 210
- `const reviewer = needsReviewer ? window.prompt("Reviewer name?")?.trim() : null` — const, line 211
- `const reason = needsReviewer ? window.prompt("Review reason (optional)?")?.trim() || null : null` — const, line 213
- `const generateCommissioningPractice = async ()` — const, line 225
- `const result = await api.generateCommissioningPractice(` — const, line 233
- `const applyIntegrationBackfill = async ()` — const, line 242
- `const confirmed = window.confirm( "Apply the reviewed D3 coordination backfill? This rewrites authored learning-object YAML, rebuilds affected state, and records one learner-visible recalibration boundary." )` — const, line 243
- `function metricValue(metric: MeasurementHealthDto["scoreboard"]["metrics"][number]): string` — function, line 459
- `function MeasurementHealthPanel(` — function, line 465
- `const reach = health.reachability.summary` — const, line 492
- `const inference = health.inferencePrecheck.summary` — const, line 493
- `const cold = health.coldProbes.coverage` — const, line 494
- `const backfill = health.integrationBackfill.summary` — const, line 495
- `const backfillChanges = (backfill.dispositions.DROP ?? 0) + (backfill.dispositions.LOWER ?? 0)` — const, line 496
- `const queue = health.reachability.cells.filter((cell)` — const, line 498
- `const nextStatus = (status: string): string | null` — const, line 499
- `const next = nextStatus(candidate.status)` — const, line 736
- `function TraceEvidenceBlock(` — function, line 768
- `const t = traceEvidence` — const, line 773
- `function InstrumentAuditBlock(` — function, line 828
- `const hunts = audit.errorHuntOutcomes` — const, line 829
- `const coverage = audit.discriminationProfileCoverage` — const, line 830
- `const ladders = audit.ladderedStems.filter((stem)` — const, line 831
- `const commissioning = audit.contrastPairCommissioning.summary` — const, line 832
- `function ClarificationRateBlock(` — function, line 980
- `const c = clarificationRate` — const, line 985
- `function ConflictSide(` — function, line 1023
- `const spanId = spanIdFromLocator(locator)` — const, line 1038
- `const openable = extractionId != null && spanId != null` — const, line 1039
- `function StudyMapDiffView(` — function, line 1056
- `const diff = append.studyMapDiff` — const, line 1057
- `const th: CSSProperties =` — const, line 1103
- `const td: CSSProperties =` — const, line 1104
- `const DIRECTION_ACTIONS:` — const, line 1108
- `const REASON_COPY: Record<AmbiguousEdgeDirectionDetail["reason"], string> =` — const, line 1115
- `function AmbiguousEdgeCard(` — function, line 1121
- `const detail = notice.detail as unknown as AmbiguousEdgeDirectionDetail | null` — const, line 1130
- `const edgeId = detail?.edgeId ?? (notice.action.edgeId as string | null | undefined) ?? null` — const, line 1133
- `const evidence = detail?.evidence ?? null` — const, line 1134
- `const src = detail.sourceConcept` — const, line 1138
- `const tgt = detail.targetConcept` — const, line 1139
- `function ConceptRef(` — function, line 1240
- `function RestructureRequestCard(` — function, line 1261
- `const detail = notice.detail as unknown as RestructureRequestDetail | null` — const, line 1268

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `MaintenanceScreen`; references `MaintenanceScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AmbiguousEdgeDirectionDetail`, `AppendResultDto`, `ConflictResolutionKind`, `EdgeDirectionResolution`, `ExamReadinessReportDto`, `GenerateCommissioningPracticeResult`, `MaintenanceNoticeDto`, `MaintenanceSeverity`, `MeasurementHealthDto`, `RestructureRequestDetail`, `SourceConflictDto`, `SourceSetSummaryDto`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
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
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/MaintenanceScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/MaintenanceScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
