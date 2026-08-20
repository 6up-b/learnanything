---
title: "Desktop module · src/components/KnowledgeModel.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.KnowledgeModel"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/KnowledgeModel.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/KnowledgeModel.tsx"
source_commit: "971d7c274e09873d726d43578cd080e4d8865571"
source_commit_timestamp: "2026-07-27T06:01:19-04:00"
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

# `src/components/KnowledgeModel.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `KnowledgeModel` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/KnowledgeModel.tsx](../../../../../../apps/learnloop-tauri/src/components/KnowledgeModel.tsx) |
| Source lines | 1000 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `971d7c274e09873d726d43578cd080e4d8865571` |
| Commit timestamp | `2026-07-27T06:01:19-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] → [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]]

## Public API

- `export function AttemptTraceView(` — function, line 83
- `export function UnresolvedCauseCard(` — function, line 101
- `export function RecipeTree(` — function, line 257
- `export function CapabilityGridView(` — function, line 375
- `export function FacetEvidenceReceipt(` — function, line 767
- `export function FacetEvidenceDrawer(` — function, line 903

## Internal implementation anchors

- `const pct = (value: number | null | undefined): string` — const, line 22
- `const demonstratedPct = (value: number | null | undefined): string` — const, line 29
- `const shortFacet = (facetId: string): string` — const, line 32
- `const facetTitle = (facetId: string): string` — const, line 33
- `const STATUS_META: Record<TraceCriterionDto["status"],` — const, line 40
- `function TraceCriterionRow(` — function, line 47
- `const meta = STATUS_META[row.status]` — const, line 48
- `const candidateLabel = (cause: UnresolvedCauseDto["candidateCauses"][number]): string` — const, line 117
- `const facet = cause.facet ?? cause.targetRef?.facetId` — const, line 119
- `const capability = cause.capability ?? cause.targetRef?.capability` — const, line 120
- `const buttonStyle = (disabled: boolean): CSSProperties` — const, line 125
- `const concreteCandidates = factor.candidateCauses .map((candidate, index)` — const, line 148
- `const pending = reportingFactorId === factor.id` — const, line 151
- `function ComponentRow(` — function, line 231
- `const marker = bottleneck ? "◆" : c.gating ? "●" : "○"` — const, line 232
- `const bottleneckKey = readiness.bottleneck ? `$` — const, line 259
- `const isBest = recipe.recipeId === bp.bestRecipeId` — const, line 294
- `function GridCell(` — function, line 337
- `const marker = demonstrated ? "●" : tested ? "◌" : "·"` — const, line 348
- `const label = demonstrated ? "demonstrated" : tested ? "tested" : "untested"` — const, line 349
- `const tone = demonstrated ? COLOR.green : tested ? COLOR.cyan : COLOR.textFaint` — const, line 350
- `const cellOf = new Map(grid.cells.map((c)` — const, line 380
- `const required = grid.cells.filter((cell)` — const, line 381
- `const demonstrated = required.filter((cell)` — const, line 382
- `const tested = required.filter((cell)` — const, line 383
- `const untested = required.length - demonstrated - tested` — const, line 384
- `const cell = cellOf.get(`$` — const, line 431
- `const CHANNEL_META: Record< "direct" | "embedded" | "assisted" | "pooled",` — const, line 487
- `function pointChannel(p: DemonstratedTimelinePointDto): "direct" | "embedded" | "assisted"` — function, line 497
- `const channels = (p.derivation ?? []).map((d)` — const, line 499
- `const round3 = (v: number): string` — const, line 504
- `function formatEvidenceTime(value: string): string` — function, line 506
- `const date = new Date(value)` — const, line 507
- `function ReceiptEntityLink(` — function, line 518
- `const BOUND_LABEL: Record<string, string> =` — const, line 535
- `function ReadyDerivationLine(` — function, line 541
- `const n = ready.directObservationCount` — const, line 542
- `const u = ready.unassistedObservationCount` — const, line 543
- `const slices = ready.pooledCapabilities.length` — const, line 544
- `const days = ready.daysSinceLastEvidence` — const, line 545
- `function ObservationDetail(` — function, line 585
- `const rows = point.derivation ?? []` — const, line 594
- `const channel = pointChannel(point)` — const, line 595
- `const channelMeta = CHANNEL_META[channel]` — const, line 596
- `const deltaTone = point.delta < 0 ? COLOR.red : point.delta > 0 ? COLOR.green : COLOR.textFaint` — const, line 597
- `const meta = CHANNEL_META[d.channel]` — const, line 628
- `function EvidenceScrubber(` — function, line 656
- `const channel = pointChannel(p)` — const, line 669
- `const meta = CHANNEL_META[channel]` — const, line 670
- `const isSel = selected === i` — const, line 671
- `const label = `$` — const, line 672
- `function ScrubberLegend()` — function, line 706
- `function DemonstratedCurve(` — function, line 723
- `const points = timeline.points` — const, line 724
- `const w = 560` — const, line 726
- `const h = 112` — const, line 727
- `const left = 28` — const, line 728
- `const right = 8` — const, line 729
- `const top = 8` — const, line 730
- `const bottom = 18` — const, line 731
- `const xs = (i: number)` — const, line 732
- `const ys = (value: number)` — const, line 733
- `const path = points.map((p, i)` — const, line 734
- `let alive = true` — let, line 773
- `const corrections = timeline?.points.filter((p)` — const, line 786
- `const latestCaps = timeline?.points.length ? timeline.points[timeline.points.length - 1].demonstratedCapabilities : []` — const, line 787
- `const latestPoint = timeline?.points.length ? timeline.points[timeline.points.length - 1] : null` — const, line 790
- `const latestTone = latestPoint && latestPoint.delta < 0 ? COLOR.red : latestPoint && latestPoint.delta > 0 ? COLOR.green : COLOR.textFaint` — const, line 791
- `const receiptHeroStyle =` — const, line 931
- `const receiptStatusLineStyle =` — const, line 937
- `const receiptContextStyle =` — const, line 946
- `const receiptSeparatorStyle =` — const, line 953
- `const receiptTitleStyle =` — const, line 958
- `const receiptBodyStyle =` — const, line 967
- `const receiptSectionLabelStyle =` — const, line 971
- `const observationEyebrowStyle =` — const, line 979
- `const receiptEntityLinkStyle =` — const, line 986
- `const receiptEntityLinkLabelStyle =` — const, line 996

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/FacetInspector|src/components/FacetInspector.tsx]] — import-or-re-export: `FacetEvidenceReceipt`; references `FacetEvidenceReceipt`
- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `CapabilityGridView`; references `CapabilityGridView`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `AttemptTraceView`, `UnresolvedCauseCard`; references `AttemptTraceView`, `UnresolvedCauseCard`
- [[Reference/Desktop/TypeScript/screens/ReviewScreen|src/screens/ReviewScreen.tsx]] — import-or-re-export: `FacetEvidenceDrawer`; references `FacetEvidenceDrawer`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `FacetEvidenceDrawer`; references `FacetEvidenceDrawer`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AttemptTraceDto`, `CapabilityGridResult`, `ComponentReadinessDto`, `DemonstratedTimelinePointDto`, `FacetEvidenceTimelineDto`, `LoReadinessDto`, `ObservationDerivationDto`, `ReadyDerivationDto`, `TraceCriterionDto`, `UnresolvedCauseDto`, `UnresolvedCauseSelfReportResponse`
- [[Reference/Desktop/TypeScript/components/CommandOverlayFrame|src/components/CommandOverlayFrame.tsx]] — import-or-re-export; imports `CommandOverlayFrame`, `learnloopShowOverlayWidth`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`, `SectionHeader`, `measurementStateColor`, `measurementStateLabel`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Build a Study Map|Build a Study Map]] — owns the map-building journey.
- [[Concepts/Canonical Knowledge Model#Core entities|canonical knowledge entities]] — owns graph meaning.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_knowledge_model.py](../../../../../../tests/test_sidecar_knowledge_model.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_graph_edit_proposals.py](../../../../../../tests/test_graph_edit_proposals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_build_study_map_routing.py](../../../../../../tests/test_build_study_map_routing.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/KnowledgeModel.tsx](../../../../../../apps/learnloop-tauri/src/components/KnowledgeModel.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
