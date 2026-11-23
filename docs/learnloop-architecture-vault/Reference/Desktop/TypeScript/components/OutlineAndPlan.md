---
title: "Desktop module · src/components/OutlineAndPlan.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.OutlineAndPlan"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/OutlineAndPlan.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/OutlineAndPlan.tsx"
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

# `src/components/OutlineAndPlan.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `OutlineAndPlan` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/OutlineAndPlan.tsx](../../../../../../apps/learnloop-tauri/src/components/OutlineAndPlan.tsx) |
| Source lines | 1352 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] → [[Reference/Desktop/TypeScript/components/OutlineAndPlan|src/components/OutlineAndPlan.tsx]]

## Public API

- `export function OutlinePlanFlow(` — function, line 177

## Internal implementation anchors

- `function Card(` — function, line 28
- `const SIGNAL_ORDER = ["examples", "exercises", "equations", "figures", "definitions", "theorems", "tables"]` — const, line 34
- `const BUDGET_FIELDS: IngestBudgetField[] = [ "inventoryInputTokens", "inventoryOutputTokens", "synthesisShardInputTokens", "synthesisShardOutputTokens", "synthesisTotalInputCeiling" ]` — const, line 37
- `const BUDGET_LABELS: Record<IngestBudgetField, string> =` — const, line 44
- `type PinnedCollection =` — type, line 53
- `function ModelInputPreview(` — function, line 61
- `const firstFetch = useRef(true)` — const, line 76
- `let cancelled = false` — let, line 79
- `const isFirst = firstFetch.current` — const, line 80
- `const run = ()` — const, line 84
- `const timer = window.setTimeout(run, isFirst ? 0 : 500)` — const, line 102
- `function PreviewToggle(` — function, line 168
- `const load = useCallback(async ()` — const, line 200
- `const next = await api.getSourceOutline(sourceRef)` — const, line 203
- `const prior = next.selection.selectedUnitIds` — const, line 205
- `const priorOverrides: Record<string, string> =` — const, line 207
- `const unitId = ov["unitId"] as string | undefined` — const, line 209
- `const op = ov["op"] as string | undefined` — const, line 210
- `const escCloses = simpleShell()` — const, line 232
- `function onKeyDown(e: KeyboardEvent)` — function, line 234
- `const tag = (e.target as HTMLElement | null)?.tagName` — const, line 237
- `function toggleUnit(unitId: string)` — function, line 248
- `const next = new Set(current)` — const, line 250
- `function cycleOverride(unitId: string)` — function, line 257
- `const next =` — const, line 259
- `const now = next[unitId]` — const, line 260
- `async function persistSelection(roleValue: string = role)` — function, line 268
- `const boundaryOverrides = Object.entries(overrides).map(([unitId, op])` — const, line 270
- `async function onRoleChange(nextRole: string)` — function, line 280
- `async function toPlan()` — function, line 290
- `const active = step === s.id` — const, line 337
- `function kindGlyph(unit: EffectiveUnitDto):` — function, line 416
- `function ResultingShape(` — function, line 422
- `const overridesKey = JSON.stringify(overrides)` — const, line 432
- `let cancelled = false` — let, line 435
- `const boundaryOverrides = Object.entries(overrides).map(([unitId, op])` — const, line 437
- `const run = ()` — const, line 438
- `const timer = window.setTimeout(run, 400)` — const, line 454
- `const units = shape?.units ?? []` — const, line 463
- `function RoleControl(` — function, line 525
- `const effectiveRole = role || suggestedRole || ""` — const, line 534
- `const overridden = role !== "" && suggestedRole != null && role !== suggestedRole` — const, line 535
- `const roles = useSourceRoles()` — const, line 538
- `const authority = roles.find((row)` — const, line 539
- `const assessmentOnly = authority != null && !authority.semanticContract && !authority.scopeOnly` — const, line 540
- `function OutlineView(` — function, line 576
- `const selectedIds = outline.units.filter((u)` — const, line 604
- `const selectedCount = selectedIds.length` — const, line 605
- `const selectedTokens = outline.units.filter((u)` — const, line 606
- `async function save()` — function, line 608
- `function UnitRow(` — function, line 704
- `const pages = unit.pageStart != null ? `p$` — const, line 717
- `const signals = SIGNAL_ORDER.filter((k)` — const, line 719
- `function SingleUnitSummary(` — function, line 769
- `const label = unit.label || unit.unitId` — const, line 784
- `const scheme = typeof unit.locator?.scheme === "string" ? (unit.locator.scheme as string) : ""` — const, line 785
- `const isTimed = scheme === "time_range" || /transcript|caption|subtitle/i.test(label)` — const, line 786
- `const noun = isTimed ? "transcript" : "document"` — const, line 787
- `function BuildPlanView(` — function, line 815
- `const firstPlanFetch = useRef(true)` — const, line 849
- `let cancelled = false` — let, line 852
- `const invalidCeilings = useMemo(()` — const, line 869
- `const value = ceilings[field]` — const, line 872
- `const overrides = useMemo(()` — const, line 877
- `const diff: Partial<IngestBudgetsDto> =` — const, line 879
- `const overridesKey = JSON.stringify(overrides)` — const, line 886
- `const planSubjectId = pinned?.subjectId ?? subjectId` — const, line 889
- `let cancelled = false` — let, line 892
- `const isFirst = firstPlanFetch.current` — const, line 893
- `const run = ()` — const, line 895
- `const timer = window.setTimeout(run, isFirst ? 0 : 400)` — const, line 906
- `const canStart = pinned !== null && invalidCeilings.length === 0` — const, line 915
- `async function startBuild()` — function, line 916
- `const batch = await api.buildStudyMap(` — const, line 923
- `const routingColor = plan.routing === "create" ? COLOR.green : COLOR.cyan` — const, line 939
- `function StageRow(` — function, line 1075
- `const color = stage.exceedsCeiling ? COLOR.red : COLOR.cyan` — const, line 1076
- `const pct = Math.min(100, (stage.inputTokens / Math.max(stage.ceiling, 1)) * 100)` — const, line 1077
- `function ConsentSummary(` — function, line 1103
- `function CeilingControls(` — function, line 1120
- `const dirty = defaults != null && BUDGET_FIELDS.some((field)` — const, line 1141
- `const bad = invalid.includes(field)` — const, line 1166
- `function RepairDialog(` — function, line 1211
- `async function start()` — function, line 1229
- `const pageList = pages .split(",") .map((s)` — const, line 1238
- `const input: StartExtractionRepairInput =` — const, line 1246
- `function OptionChip(` — function, line 1330
- `const color = on ? (danger ? COLOR.red : COLOR.amber) : COLOR.textFaint` — const, line 1331
- `function buttonStyle(primary: boolean): CSSProperties` — function, line 1342

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `OutlinePlanFlow`; references `OutlinePlanFlow`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `BuildPlan`, `BuildPlanStage`, `CommandError`, `EffectiveOutlineDto`, `EffectiveUnitDto`, `IngestBudgetBoundsDto`, `IngestBudgetField`, `IngestBudgetsDto`, `OutlineUnit`, `SelectionPreviewDto`, `SourceOutline`, `StartExtractionRepairInput`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/shell|src/app/shell.ts]] — import-or-re-export; imports `simpleShell`
- [[Reference/Desktop/TypeScript/components/AddToCollection|src/components/AddToCollection.tsx]] — import-or-re-export; imports `AddToCollectionPanel`, `SYLLABUS_ROLE_HINT`, `roleOptions`, `useSourceRoles`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`, `TermCheckbox`, `TermSelect`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/sourceRoles.test.tsx](../../../../../../apps/learnloop-tauri/src/components/sourceRoles.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/OutlineAndPlan.escape.test.tsx](../../../../../../apps/learnloop-tauri/src/components/OutlineAndPlan.escape.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_ingest_m3.py](../../../../../../tests/test_sidecar_ingest_m3.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_source_ingestion.py](../../../../../../tests/test_source_ingestion.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_init.py](../../../../../../tests/test_init.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/OutlineAndPlan.tsx](../../../../../../apps/learnloop-tauri/src/components/OutlineAndPlan.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
