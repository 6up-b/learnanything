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
source_commit: "bf930ea08e1644f3acecb9d331a6fcedbf0fec19"
source_commit_timestamp: "2026-10-23T18:05:56-04:00"
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
| Source lines | 1677 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `bf930ea08e1644f3acecb9d331a6fcedbf0fec19` |
| Commit timestamp | `2026-10-23T18:05:56-04:00` |

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
- `const loadedIdRef = useRef<string | null>(null)` — const, line 87
- `const backNavRef = useRef(false)` — const, line 88
- `function go(id: string)` — function, line 92
- `const trimmed = id.trim()` — const, line 93
- `function back()` — function, line 97
- `const prev = loadedIdRef.current` — const, line 114
- `const onKey = (event: KeyboardEvent)` — const, line 126
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 128
- `const isInput = tag === "input" || tag === "textarea"` — const, line 129
- `async function fetchEntity(id: string)` — function, line 156
- `const previous = entity` — const, line 158
- `const result = await api.inspectEntity(id)` — const, line 159
- `const pill = entity && entity.kind in KIND_PILL ? KIND_PILL[entity.kind] : null` — const, line 174
- `function InspectorEntityView(` — function, line 246
- `const title = entity.kind === "practice_item" ? entity.detail.learningObjectTitle : entity.kind === "learning_object" ? entity.detail.title : entity.kind === "concept" ? entity.detail.title : entity.kind === "error_event" ? entity.detail.errorTitle ?? entity.…` — const, line 268
- `function ProbeEpisodeBody(` — function, line 326
- `function PracticeItemBody(` — function, line 354
- `const state = detail.state` — const, line 368
- `const mastery = detail.mastery` — const, line 369
- `const answered = detail.attempts.some((attempt)` — const, line 374
- `const withholdAnswer = simplePracticeFeedback() && (answering || !answered)` — const, line 375
- `function LearningObjectBody(` — function, line 579
- `function ConceptBody(` — function, line 672
- `const presentation = conceptRelationPresentation(relation)` — const, line 725
- `function conceptRelationPresentation( relation: ConceptInspectorDetail["relations"][number] ):` — function, line 763
- `function LoCapabilitySection(` — function, line 785
- `let alive = true` — let, line 792
- `function ErrorEventBody(` — function, line 821
- `function P0AttributionInspector(` — function, line 857
- `const text = (key: string): string | null` — const, line 858
- `const number = (key: string): number | null` — const, line 860
- `const object = (key: string): Record<string, unknown> | null` — const, line 862
- `const list = (key: string): unknown[]` — const, line 866
- `const target = object("targetRef") as Parameters<typeof formatCausalTarget>[0]` — const, line 867
- `const divergence = object("firstDivergence") as Parameters<typeof formatDivergenceAnchor>[0]` — const, line 868
- `const resolution = text("resolutionStatus")` — const, line 869
- `const causeScope = text("causeScope")` — const, line 870
- `const operation = text("operation")` — const, line 871
- `const localization = number("modelReportedLocalizationConfidence")` — const, line 872
- `const causal = number("modelReportedCausalConfidence")` — const, line 873
- `const contrast = object("facetContrast")` — const, line 874
- `const candidates = list("candidateCauses")` — const, line 875
- `const claims = list("postdictiveClaims")` — const, line 876
- `const candidate = raw && typeof raw === "object" && !Array.isArray(raw) ? raw as Record<string, unknown> :` — const, line 925
- `const candidateTarget = candidate.targetRef && typeof candidate.targetRef === "object" && !Array.isArray(candidate.targetRef) ? candidate.targetRef as Parameters<typeof formatCausalTarget>[0] : null` — const, line 929
- `const claim = raw && typeof raw === "object" && !Array.isArray(raw) ? raw as Record<string, unknown> :` — const, line 957
- `function NoteBody(` — function, line 976
- `function AttemptBody(` — function, line 1046
- `const feedback = detail.feedback ?? null` — const, line 1047
- `const surprise = feedback?.surprise ?? null` — const, line 1048
- `const evidence = feedback?.criterionEvidence ?? []` — const, line 1049
- `const attributions = feedback?.errorAttributions ?? []` — const, line 1050
- `const repairs = feedback?.repairSuggestions ?? []` — const, line 1051
- `const assessed = criterionAssessed(row)` — const, line 1121
- `const earned = row.pointsAwarded > 0` — const, line 1122
- `const tone = !assessed ? COLOR.textDim : earned ? COLOR.green : COLOR.red` — const, line 1123
- `function AttemptAttributionRow(` — function, line 1219
- `const plan = event.repairPlan` — const, line 1226
- `const resolution = typeof plan?.resolutionStatus === "string" ? plan.resolutionStatus : null` — const, line 1227
- `const scope = typeof plan?.causeScope === "string" ? plan.causeScope : null` — const, line 1229
- `const operation = typeof plan?.operation === "string" ? plan.operation : null` — const, line 1230
- `const abstention = typeof plan?.abstentionReason === "string" ? plan.abstentionReason : null` — const, line 1231
- `const target = plan?.targetRef && typeof plan.targetRef === "object" && !Array.isArray(plan.targetRef) ? plan.targetRef as Parameters<typeof formatCausalTarget>[0] : null` — const, line 1233
- `const divergence = plan?.firstDivergence && typeof plan.firstDivergence === "object" && !Array.isArray(plan.firstDivergence) ? plan.firstDivergence as Parameters<typeof formatDivergenceAnchor>[0] : null` — const, line 1237
- `function NotFoundBody(` — function, line 1284
- `const WHY_ROWS: Array<` — const, line 1334
- `function SchedulerWhy(` — function, line 1342
- `const comps = scheduler.components` — const, line 1343
- `const normalizedComps =` — const, line 1344
- `const rows = WHY_ROWS.filter((row)` — const, line 1348
- `const maxVal = Math.max(0.001, ...rows.map((row)` — const, line 1349
- `const value = normalizedComps[row.key] ?? 0` — const, line 1363
- `const pct = (value / maxVal) * 100` — const, line 1364
- `function MasteryPosteriorBar(` — function, line 1414
- `const mean = Math.max(0, Math.min(1, mastery.mean))` — const, line 1415
- `const fallbackSd = Math.sqrt(Math.max(0, mastery.variance))` — const, line 1416
- `const lower = Math.max(0, Math.min(mean, mastery.plausibleLower ?? mean - fallbackSd))` — const, line 1417
- `const upper = Math.min(1, Math.max(mean, mastery.plausibleUpper ?? mean + fallbackSd))` — const, line 1418
- `const mass = mastery.plausibleMass ?? 0.8` — const, line 1419
- `const tone = masteryColor(mean)` — const, line 1420
- `const intervalLabel = `$` — const, line 1421
- `function InspectorRow(` — function, line 1463
- `function Stat(` — function, line 1474
- `function LearningObjectRelations(` — function, line 1483
- `function ConceptReferenceLinks(` — function, line 1537
- `function fallbackConceptRefs(values: string[]): ConceptReferenceDto[]` — function, line 1564
- `function IdLink(` — function, line 1568
- `function attemptTypePillColor(attemptType: string): PillColor` — function, line 1598
- `function attemptRowStyle(index: number): CSSProperties` — function, line 1613
- `function rubricRowStyle(index: number): CSSProperties` — function, line 1625
- `function relTime(iso: string | null | undefined): string` — function, line 1637
- `const then = Date.parse(iso)` — const, line 1639
- `const diff = Date.now() - then` — const, line 1641
- `const abs = Math.abs(diff)` — const, line 1642
- `const minute = 60_000` — const, line 1643
- `const hour = 3_600_000` — const, line 1644
- `const day = 86_400_000` — const, line 1645
- `const label = abs < hour ? `$` — const, line 1647
- `function formatUnknown(value: unknown): string` — function, line 1651
- `const searchInputStyle: CSSProperties =` — const, line 1659
- `const panelStyle: CSSProperties =` — const, line 1670

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
