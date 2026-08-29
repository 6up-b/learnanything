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
| Source lines | 1576 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]]

## Public API

- `export function InspectorOverlay(` — function, line 58

## Internal implementation anchors

- `const KIND_PILL: Record<string,` — const, line 44
- `function masteryColor(mastery: number): string` — function, line 54
- `const loadedIdRef = useRef<string | null>(null)` — const, line 73
- `const backNavRef = useRef(false)` — const, line 74
- `function go(id: string)` — function, line 78
- `const trimmed = id.trim()` — const, line 79
- `function back()` — function, line 83
- `const prev = loadedIdRef.current` — const, line 100
- `const onKey = (event: KeyboardEvent)` — const, line 112
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 113
- `const isInput = tag === "input" || tag === "textarea"` — const, line 114
- `async function fetchEntity(id: string)` — function, line 141
- `const previous = entity` — const, line 143
- `const result = await api.inspectEntity(id)` — const, line 144
- `const pill = entity && entity.kind in KIND_PILL ? KIND_PILL[entity.kind] : null` — const, line 159
- `function InspectorEntityView(` — function, line 229
- `const title = entity.kind === "practice_item" ? entity.detail.learningObjectTitle : entity.kind === "learning_object" ? entity.detail.title : entity.kind === "concept" ? entity.detail.title : entity.kind === "error_event" ? entity.detail.errorTitle ?? entity.…` — const, line 247
- `function ProbeEpisodeBody(` — function, line 292
- `function PracticeItemBody(` — function, line 320
- `const state = detail.state` — const, line 331
- `const mastery = detail.mastery` — const, line 332
- `function LearningObjectBody(` — function, line 515
- `function ConceptBody(` — function, line 578
- `const presentation = conceptRelationPresentation(relation)` — const, line 631
- `function conceptRelationPresentation( relation: ConceptInspectorDetail["relations"][number] ):` — function, line 669
- `function LoCapabilitySection(` — function, line 691
- `let alive = true` — let, line 698
- `function ErrorEventBody(` — function, line 727
- `function P0AttributionInspector(` — function, line 763
- `const text = (key: string): string | null` — const, line 764
- `const number = (key: string): number | null` — const, line 766
- `const object = (key: string): Record<string, unknown> | null` — const, line 768
- `const list = (key: string): unknown[]` — const, line 772
- `const target = object("targetRef") as Parameters<typeof formatCausalTarget>[0]` — const, line 773
- `const divergence = object("firstDivergence") as Parameters<typeof formatDivergenceAnchor>[0]` — const, line 774
- `const resolution = text("resolutionStatus")` — const, line 775
- `const causeScope = text("causeScope")` — const, line 776
- `const operation = text("operation")` — const, line 777
- `const localization = number("modelReportedLocalizationConfidence")` — const, line 778
- `const causal = number("modelReportedCausalConfidence")` — const, line 779
- `const contrast = object("facetContrast")` — const, line 780
- `const candidates = list("candidateCauses")` — const, line 781
- `const claims = list("postdictiveClaims")` — const, line 782
- `const candidate = raw && typeof raw === "object" && !Array.isArray(raw) ? raw as Record<string, unknown> :` — const, line 831
- `const candidateTarget = candidate.targetRef && typeof candidate.targetRef === "object" && !Array.isArray(candidate.targetRef) ? candidate.targetRef as Parameters<typeof formatCausalTarget>[0] : null` — const, line 835
- `const claim = raw && typeof raw === "object" && !Array.isArray(raw) ? raw as Record<string, unknown> :` — const, line 863
- `function NoteBody(` — function, line 882
- `function AttemptBody(` — function, line 952
- `const feedback = detail.feedback ?? null` — const, line 953
- `const surprise = feedback?.surprise ?? null` — const, line 954
- `const evidence = feedback?.criterionEvidence ?? []` — const, line 955
- `const attributions = feedback?.errorAttributions ?? []` — const, line 956
- `const repairs = feedback?.repairSuggestions ?? []` — const, line 957
- `const earned = row.pointsAwarded > 0` — const, line 1022
- `function AttemptAttributionRow(` — function, line 1118
- `const plan = event.repairPlan` — const, line 1125
- `const resolution = typeof plan?.resolutionStatus === "string" ? plan.resolutionStatus : null` — const, line 1126
- `const scope = typeof plan?.causeScope === "string" ? plan.causeScope : null` — const, line 1128
- `const operation = typeof plan?.operation === "string" ? plan.operation : null` — const, line 1129
- `const abstention = typeof plan?.abstentionReason === "string" ? plan.abstentionReason : null` — const, line 1130
- `const target = plan?.targetRef && typeof plan.targetRef === "object" && !Array.isArray(plan.targetRef) ? plan.targetRef as Parameters<typeof formatCausalTarget>[0] : null` — const, line 1132
- `const divergence = plan?.firstDivergence && typeof plan.firstDivergence === "object" && !Array.isArray(plan.firstDivergence) ? plan.firstDivergence as Parameters<typeof formatDivergenceAnchor>[0] : null` — const, line 1136
- `function NotFoundBody(` — function, line 1183
- `const WHY_ROWS: Array<` — const, line 1233
- `function SchedulerWhy(` — function, line 1241
- `const comps = scheduler.components` — const, line 1242
- `const normalizedComps =` — const, line 1243
- `const rows = WHY_ROWS.filter((row)` — const, line 1247
- `const maxVal = Math.max(0.001, ...rows.map((row)` — const, line 1248
- `const value = normalizedComps[row.key] ?? 0` — const, line 1262
- `const pct = (value / maxVal) * 100` — const, line 1263
- `function MasteryPosteriorBar(` — function, line 1313
- `const mean = Math.max(0, Math.min(1, mastery.mean))` — const, line 1314
- `const fallbackSd = Math.sqrt(Math.max(0, mastery.variance))` — const, line 1315
- `const lower = Math.max(0, Math.min(mean, mastery.plausibleLower ?? mean - fallbackSd))` — const, line 1316
- `const upper = Math.min(1, Math.max(mean, mastery.plausibleUpper ?? mean + fallbackSd))` — const, line 1317
- `const mass = mastery.plausibleMass ?? 0.8` — const, line 1318
- `const tone = masteryColor(mean)` — const, line 1319
- `const intervalLabel = `$` — const, line 1320
- `function InspectorRow(` — function, line 1362
- `function Stat(` — function, line 1373
- `function LearningObjectRelations(` — function, line 1382
- `function ConceptReferenceLinks(` — function, line 1436
- `function fallbackConceptRefs(values: string[]): ConceptReferenceDto[]` — function, line 1463
- `function IdLink(` — function, line 1467
- `function attemptTypePillColor(attemptType: string): PillColor` — function, line 1497
- `function attemptRowStyle(index: number): CSSProperties` — function, line 1512
- `function rubricRowStyle(index: number): CSSProperties` — function, line 1524
- `function relTime(iso: string | null | undefined): string` — function, line 1536
- `const then = Date.parse(iso)` — const, line 1538
- `const diff = Date.now() - then` — const, line 1540
- `const abs = Math.abs(diff)` — const, line 1541
- `const minute = 60_000` — const, line 1542
- `const hour = 3_600_000` — const, line 1543
- `const day = 86_400_000` — const, line 1544
- `const label = abs < hour ? `$` — const, line 1546
- `function formatUnknown(value: unknown): string` — function, line 1550
- `const searchInputStyle: CSSProperties =` — const, line 1558
- `const panelStyle: CSSProperties =` — const, line 1569

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `InspectorOverlay`; references `InspectorOverlay`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AttemptInspectorDetail`, `CapabilityGridResult`, `ConceptInspectorDetail`, `ConceptReferenceDto`, `ErrorEventDto`, `InspectorEntity`, `InspectorSearchResult`, `LearningObjectDetail`, `MasteryDto`, `NoteInspectorDetail`, `PracticeItemDetail`, `ProbeEpisodeInspectorDetail`, `SchedulerComponents`, `SchedulerExplanationDto`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `masteryTone`
- [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]] — import-or-re-export; imports `RungVariantActions`
- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export; imports `CausalEpisodeInspector`, `formatCausalTarget`, `formatDivergenceAnchor`
- [[Reference/Desktop/TypeScript/components/CommandOverlayFrame|src/components/CommandOverlayFrame.tsx]] — import-or-re-export; imports `CommandOverlayFrame`, `commandOverlayActionStyle`, `learnloopShowOverlayWidth`
- [[Reference/Desktop/TypeScript/components/ConceptAnimationSection|src/components/ConceptAnimationSection.tsx]] — import-or-re-export; imports `ConceptAnimationSection`
- [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]] — import-or-re-export; imports `CapabilityGridView`
- [[Reference/Desktop/TypeScript/components/recipeedit/RecipeTreeEditor|src/components/recipeedit/RecipeTreeEditor.tsx]] — import-or-re-export; imports `RecipeTreeEditor`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `Dim`, `DisclosureHeader`, `Divider`, `FONT_MONO`, `Faint`, `HelpTooltip`, `Meta`, `Pill`, `PillColor`, `PlainEnglishPanel`, `SectionHeader`, `modePillColor`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/InspectorOverlay.tsx](../../../../../../apps/learnloop-tauri/src/components/InspectorOverlay.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
