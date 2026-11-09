---
title: "Desktop module · src/components/InspectorOverlay.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.InspectorOverlay"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/InspectorOverlay.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/InspectorOverlay.tsx"
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

# `src/components/InspectorOverlay.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `InspectorOverlay` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/InspectorOverlay.tsx](../../../../../../apps/learnloop-tauri/src/components/InspectorOverlay.tsx) |
| Source lines | 1699 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]]

## Public API

- `export function InspectorOverlay(` — function, line 65

## Internal implementation anchors

- `const KIND_PILL: Record<string,` — const, line 51
- `function masteryColor(mastery: number): string` — function, line 61
- `const loadedIdRef = useRef<string | null>(null)` — const, line 90
- `const backNavRef = useRef(false)` — const, line 91
- `function go(id: string)` — function, line 95
- `const trimmed = id.trim()` — const, line 96
- `function back()` — function, line 100
- `const prev = loadedIdRef.current` — const, line 117
- `const onKey = (event: KeyboardEvent)` — const, line 129
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 131
- `const isInput = tag === "input" || tag === "textarea"` — const, line 132
- `async function fetchEntity(id: string)` — function, line 159
- `const previous = entity` — const, line 161
- `const result = await api.inspectEntity(id)` — const, line 162
- `const pill = entity && entity.kind in KIND_PILL ? KIND_PILL[entity.kind] : null` — const, line 177
- `function InspectorEntityView(` — function, line 250
- `const title = entity.kind === "practice_item" ? entity.detail.learningObjectTitle : entity.kind === "learning_object" ? entity.detail.title : entity.kind === "concept" ? entity.detail.title : entity.kind === "error_event" ? entity.detail.errorTitle ?? entity.…` — const, line 274
- `function ProbeEpisodeBody(` — function, line 333
- `function PracticeItemBody(` — function, line 361
- `const state = detail.state` — const, line 375
- `const mastery = detail.mastery` — const, line 376
- `const answered = detail.attempts.some((attempt)` — const, line 381
- `const withholdAnswer = simplePracticeFeedback() && (answering || !answered)` — const, line 382
- `function LearningObjectBody(` — function, line 586
- `function ConceptBody(` — function, line 694
- `const presentation = conceptRelationPresentation(relation)` — const, line 747
- `function conceptRelationPresentation( relation: ConceptInspectorDetail["relations"][number] ):` — function, line 785
- `function LoCapabilitySection(` — function, line 807
- `let alive = true` — let, line 814
- `function ErrorEventBody(` — function, line 843
- `function P0AttributionInspector(` — function, line 879
- `const text = (key: string): string | null` — const, line 880
- `const number = (key: string): number | null` — const, line 882
- `const object = (key: string): Record<string, unknown> | null` — const, line 884
- `const list = (key: string): unknown[]` — const, line 888
- `const target = object("targetRef") as Parameters<typeof formatCausalTarget>[0]` — const, line 889
- `const divergence = object("firstDivergence") as Parameters<typeof formatDivergenceAnchor>[0]` — const, line 890
- `const resolution = text("resolutionStatus")` — const, line 891
- `const causeScope = text("causeScope")` — const, line 892
- `const operation = text("operation")` — const, line 893
- `const localization = number("modelReportedLocalizationConfidence")` — const, line 894
- `const causal = number("modelReportedCausalConfidence")` — const, line 895
- `const contrast = object("facetContrast")` — const, line 896
- `const candidates = list("candidateCauses")` — const, line 897
- `const claims = list("postdictiveClaims")` — const, line 898
- `const candidate = raw && typeof raw === "object" && !Array.isArray(raw) ? raw as Record<string, unknown> :` — const, line 947
- `const candidateTarget = candidate.targetRef && typeof candidate.targetRef === "object" && !Array.isArray(candidate.targetRef) ? candidate.targetRef as Parameters<typeof formatCausalTarget>[0] : null` — const, line 951
- `const claim = raw && typeof raw === "object" && !Array.isArray(raw) ? raw as Record<string, unknown> :` — const, line 979
- `function NoteBody(` — function, line 998
- `function AttemptBody(` — function, line 1068
- `const feedback = detail.feedback ?? null` — const, line 1069
- `const surprise = feedback?.surprise ?? null` — const, line 1070
- `const evidence = feedback?.criterionEvidence ?? []` — const, line 1071
- `const attributions = feedback?.errorAttributions ?? []` — const, line 1072
- `const repairs = feedback?.repairSuggestions ?? []` — const, line 1073
- `const assessed = criterionAssessed(row)` — const, line 1143
- `const earned = row.pointsAwarded > 0` — const, line 1144
- `const tone = !assessed ? COLOR.textDim : earned ? COLOR.green : COLOR.red` — const, line 1145
- `function AttemptAttributionRow(` — function, line 1241
- `const plan = event.repairPlan` — const, line 1248
- `const resolution = typeof plan?.resolutionStatus === "string" ? plan.resolutionStatus : null` — const, line 1249
- `const scope = typeof plan?.causeScope === "string" ? plan.causeScope : null` — const, line 1251
- `const operation = typeof plan?.operation === "string" ? plan.operation : null` — const, line 1252
- `const abstention = typeof plan?.abstentionReason === "string" ? plan.abstentionReason : null` — const, line 1253
- `const target = plan?.targetRef && typeof plan.targetRef === "object" && !Array.isArray(plan.targetRef) ? plan.targetRef as Parameters<typeof formatCausalTarget>[0] : null` — const, line 1255
- `const divergence = plan?.firstDivergence && typeof plan.firstDivergence === "object" && !Array.isArray(plan.firstDivergence) ? plan.firstDivergence as Parameters<typeof formatDivergenceAnchor>[0] : null` — const, line 1259
- `function NotFoundBody(` — function, line 1306
- `const WHY_ROWS: Array<` — const, line 1356
- `function SchedulerWhy(` — function, line 1364
- `const comps = scheduler.components` — const, line 1365
- `const normalizedComps =` — const, line 1366
- `const rows = WHY_ROWS.filter((row)` — const, line 1370
- `const maxVal = Math.max(0.001, ...rows.map((row)` — const, line 1371
- `const value = normalizedComps[row.key] ?? 0` — const, line 1385
- `const pct = (value / maxVal) * 100` — const, line 1386
- `function MasteryPosteriorBar(` — function, line 1436
- `const mean = Math.max(0, Math.min(1, mastery.mean))` — const, line 1437
- `const fallbackSd = Math.sqrt(Math.max(0, mastery.variance))` — const, line 1438
- `const lower = Math.max(0, Math.min(mean, mastery.plausibleLower ?? mean - fallbackSd))` — const, line 1439
- `const upper = Math.min(1, Math.max(mean, mastery.plausibleUpper ?? mean + fallbackSd))` — const, line 1440
- `const mass = mastery.plausibleMass ?? 0.8` — const, line 1441
- `const tone = masteryColor(mean)` — const, line 1442
- `const intervalLabel = `$` — const, line 1443
- `function InspectorRow(` — function, line 1485
- `function Stat(` — function, line 1496
- `function LearningObjectRelations(` — function, line 1505
- `function ConceptReferenceLinks(` — function, line 1559
- `function fallbackConceptRefs(values: string[]): ConceptReferenceDto[]` — function, line 1586
- `function IdLink(` — function, line 1590
- `function attemptTypePillColor(attemptType: string): PillColor` — function, line 1620
- `function attemptRowStyle(index: number): CSSProperties` — function, line 1635
- `function rubricRowStyle(index: number): CSSProperties` — function, line 1647
- `function relTime(iso: string | null | undefined): string` — function, line 1659
- `const then = Date.parse(iso)` — const, line 1661
- `const diff = Date.now() - then` — const, line 1663
- `const abs = Math.abs(diff)` — const, line 1664
- `const minute = 60_000` — const, line 1665
- `const hour = 3_600_000` — const, line 1666
- `const day = 86_400_000` — const, line 1667
- `const label = abs < hour ? `$` — const, line 1669
- `function formatUnknown(value: unknown): string` — function, line 1673
- `const searchInputStyle: CSSProperties =` — const, line 1681
- `const panelStyle: CSSProperties =` — const, line 1692

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `InspectorOverlay`; references `InspectorOverlay`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AttemptInspectorDetail`, `CapabilityGridResult`, `ConceptInspectorDetail`, `ConceptReferenceDto`, `ErrorEventDto`, `InspectorEntity`, `InspectorSearchResult`, `LearningObjectDetail`, `MasteryDto`, `NOT_ASSESSED_LABEL`, `NoteInspectorDetail`, `PracticeItemDetail`, `ProbeEpisodeInspectorDetail`, `SchedulerComponents`, `SchedulerExplanationDto`, `UNVERIFIED_ROUTE_REVIEW_REASON`, `criterionAssessed`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `masteryTone`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]] — import-or-re-export; imports `simplePracticeFeedback`
- [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]] — import-or-re-export; imports `RungVariantActions`
- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export; imports `CausalEpisodeInspector`, `formatCausalTarget`, `formatDivergenceAnchor`
- [[Reference/Desktop/TypeScript/components/CommandOverlayFrame|src/components/CommandOverlayFrame.tsx]] — import-or-re-export; imports `CommandOverlayFrame`, `commandOverlayActionStyle`, `learnloopShowOverlayWidth`
- [[Reference/Desktop/TypeScript/components/ConceptAnimationSection|src/components/ConceptAnimationSection.tsx]] — import-or-re-export; imports `ConceptAnimationSection`
- [[Reference/Desktop/TypeScript/components/IntentControl|src/components/IntentControl.tsx]] — import-or-re-export; imports `IntentControl`, `SubjectIntent`
- [[Reference/Desktop/TypeScript/components/ItemPresentation|src/components/ItemPresentation.tsx]] — import-or-re-export; imports `ItemPresentation`
- [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]] — import-or-re-export; imports `CapabilityGridView`
- [[Reference/Desktop/TypeScript/components/PlacementControls|src/components/PlacementControls.tsx]] — import-or-re-export; imports `PlacementSection`
- [[Reference/Desktop/TypeScript/components/ReadinessLine|src/components/ReadinessLine.tsx]] — import-or-re-export; imports `ReadinessLine`
- [[Reference/Desktop/TypeScript/components/recipeedit/RecipeTreeEditor|src/components/recipeedit/RecipeTreeEditor.tsx]] — import-or-re-export; imports `RecipeTreeEditor`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `Dim`, `DisclosureHeader`, `Divider`, `FONT_MONO`, `Faint`, `HelpTooltip`, `Meta`, `Pill`, `PillColor`, `PlainEnglishPanel`, `SectionHeader`, `modePillColor`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/InspectorOverlay.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/components/InspectorOverlay.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/InspectorOverlay.tsx](../../../../../../apps/learnloop-tauri/src/components/InspectorOverlay.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
