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
| Source lines | 1419 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]]

## Public API

- `export function MaintenanceScreen(` — function, line 73
- `export function TranscriptionReportCard(` — function, line 1329

## Internal implementation anchors

- `function spanIdFromLocator(locator: string | null): string | null` — function, line 37
- `const SEVERITY_PILL: Record<MaintenanceSeverity, PillColor> =` — const, line 41
- `const RESOLUTION_KINDS:` — const, line 47
- `const panel: CSSProperties =` — const, line 54
- `const btn: CSSProperties =` — const, line 62
- `const feedQuery = useCachedQuery(["maintenance_feed", subjectId], ()` — const, line 92
- `const conflictsQuery = useCachedQuery(["list_source_conflicts", "open"], ()` — const, line 95
- `const readinessQuery = useCachedQuery(["exam_readiness", subjectId], ()` — const, line 98
- `const sourceSetsQuery = useCachedQuery(["list_source_sets"], ()` — const, line 101
- `const healthQuery = useCachedQuery(["get_measurement_health"], ()` — const, line 102
- `const adjudicationQuery = useCachedQuery(["adjudication_queue",` — const, line 105
- `const notices: MaintenanceNoticeDto[] = feedQuery.data?.notices ?? []` — const, line 108
- `const conflicts: SourceConflictDto[] = conflictsQuery.data?.conflicts ?? []` — const, line 109
- `const readiness: ExamReadinessReportDto | null = readinessQuery.data?.report ?? null` — const, line 110
- `const sourceSets: SourceSetSummaryDto[] = sourceSetsQuery.data?.sourceSets ?? []` — const, line 111
- `const measurementHealth: MeasurementHealthDto | null = healthQuery.data ?? null` — const, line 112
- `const adjudicationOwed: number | null = adjudicationQuery.data?.total ?? null` — const, line 114
- `const reportError = useCallback( (err: unknown)` — const, line 126
- `const reload = ()` — const, line 132
- `const loadError = feedQuery.error ?? conflictsQuery.error ?? readinessQuery.error ?? sourceSetsQuery.error ?? healthQuery.error` — const, line 143
- `const noticeAction = async (notice: MaintenanceNoticeDto, action: "dismiss" | "snooze")` — const, line 149
- `const resolveDirection = async ( edgeId: string, resolution: EdgeDirectionResolution, rationale: string )` — const, line 157
- `const runAppend = async (sourceSetId: string)` — const, line 169
- `const res = await api.appendSource(` — const, line 173
- `const resolve = async (conflict: SourceConflictDto, kind: ConflictResolutionKind)` — const, line 182
- `let resolution: Record<string, unknown> =` — let, line 184
- `const canonical = window.prompt("Canonical notation?") ?? ""` — const, line 186
- `const alternate = window.prompt("Alternate notation?") ?? ""` — const, line 187
- `const bySeverity = (sev: MaintenanceSeverity)` — const, line 197
- `const scheduleColdProbes = async ()` — const, line 199
- `const transitionProbe = async (candidateId: string, toStatus: string)` — const, line 210
- `const needsReviewer = toStatus === "reviewed" || toStatus === "rejected"` — const, line 211
- `const reviewer = needsReviewer ? window.prompt("Reviewer name?")?.trim() : null` — const, line 212
- `const reason = needsReviewer ? window.prompt("Review reason (optional)?")?.trim() || null : null` — const, line 214
- `const generateCommissioningPractice = async ()` — const, line 226
- `const result = await api.generateCommissioningPractice(` — const, line 234
- `const applyIntegrationBackfill = async ()` — const, line 243
- `const confirmed = window.confirm( "Apply the reviewed D3 coordination backfill? This rewrites authored learning-object YAML, rebuilds affected state, and records one learner-visible recalibration boundary." )` — const, line 244
- `function metricValue(metric: MeasurementHealthDto["scoreboard"]["metrics"][number]): string` — function, line 466
- `function MeasurementHealthPanel(` — function, line 472
- `const reach = health.reachability.summary` — const, line 499
- `const inference = health.inferencePrecheck.summary` — const, line 500
- `const cold = health.coldProbes.coverage` — const, line 501
- `const backfill = health.integrationBackfill.summary` — const, line 502
- `const backfillChanges = (backfill.dispositions.DROP ?? 0) + (backfill.dispositions.LOWER ?? 0)` — const, line 503
- `const queue = health.reachability.cells.filter((cell)` — const, line 505
- `const nextStatus = (status: string): string | null` — const, line 506
- `const next = nextStatus(candidate.status)` — const, line 743
- `function TraceEvidenceBlock(` — function, line 775
- `const t = traceEvidence` — const, line 780
- `function InstrumentAuditBlock(` — function, line 835
- `const hunts = audit.errorHuntOutcomes` — const, line 836
- `const coverage = audit.discriminationProfileCoverage` — const, line 837
- `const ladders = audit.ladderedStems.filter((stem)` — const, line 838
- `const commissioning = audit.contrastPairCommissioning.summary` — const, line 839
- `function ClarificationRateBlock(` — function, line 987
- `const c = clarificationRate` — const, line 992
- `function ConflictSide(` — function, line 1030
- `const spanId = resolvedSpanId !== undefined ? resolvedSpanId : spanIdFromLocator(locator)` — const, line 1049
- `const openable = extractionId != null && spanId != null` — const, line 1050
- `function StudyMapDiffView(` — function, line 1067
- `const diff = append.studyMapDiff` — const, line 1068
- `const th: CSSProperties =` — const, line 1114
- `const td: CSSProperties =` — const, line 1115
- `const DIRECTION_ACTIONS:` — const, line 1119
- `const REASON_COPY: Record<AmbiguousEdgeDirectionDetail["reason"], string> =` — const, line 1126
- `function AmbiguousEdgeCard(` — function, line 1132
- `const detail = notice.detail as unknown as AmbiguousEdgeDirectionDetail | null` — const, line 1141
- `const edgeId = detail?.edgeId ?? (notice.action.edgeId as string | null | undefined) ?? null` — const, line 1144
- `const evidence = detail?.evidence ?? null` — const, line 1145
- `const src = detail.sourceConcept` — const, line 1149
- `const tgt = detail.targetConcept` — const, line 1150
- `function ConceptRef(` — function, line 1251
- `function RestructureRequestCard(` — function, line 1272
- `const detail = notice.detail as unknown as RestructureRequestDetail | null` — const, line 1279
- `interface TranscriptionReportDetail` — interface, line 1319
- `const detail = (notice.detail ??` — const, line 1340
- `const itemId = detail.practiceItemId ?? notice.entityId ?? (notice.action.practiceItemId as string | undefined) ?? null` — const, line 1341
- `const reports = detail.reports ?? 1` — const, line 1346
- `const notes = detail.notes ?? []` — const, line 1347
- `const printed = useAsPrinted(itemId)` — const, line 1348
- `const save = async ()` — const, line 1349
- `const prompt = draft.trim()` — const, line 1351

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
- [[Reference/Desktop/TypeScript/components/AsPrinted|src/components/AsPrinted.tsx]] — import-or-re-export; imports `AsPrinted`, `useAsPrinted`
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

- [apps/learnloop-tauri/src/screens/MaintenanceScreen.transcription.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/MaintenanceScreen.transcription.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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
