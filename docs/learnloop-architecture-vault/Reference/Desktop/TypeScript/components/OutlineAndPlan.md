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
| Source lines | 1365 |
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

- `export function OutlinePlanFlow(` — function, line 194

## Internal implementation anchors

- `const SOURCE_ROLES = [ "primary_textbook", "lecture", "paper", "reference", "alternate_explanation", "problem_set", "exam", "notes", "syllabus" ] as const` — const, line 26
- `const ASSESSMENT_ONLY_ROLES = new Set(["exam", "problem_set"])` — const, line 38
- `function Card(` — function, line 45
- `const SIGNAL_ORDER = ["examples", "exercises", "equations", "figures", "definitions", "theorems", "tables"]` — const, line 51
- `const BUDGET_FIELDS: IngestBudgetField[] = [ "inventoryInputTokens", "inventoryOutputTokens", "synthesisShardInputTokens", "synthesisShardOutputTokens", "synthesisTotalInputCeiling" ]` — const, line 54
- `const BUDGET_LABELS: Record<IngestBudgetField, string> =` — const, line 61
- `type PinnedCollection =` — type, line 70
- `function ModelInputPreview(` — function, line 78
- `const firstFetch = useRef(true)` — const, line 93
- `let cancelled = false` — let, line 96
- `const isFirst = firstFetch.current` — const, line 97
- `const run = ()` — const, line 101
- `const timer = window.setTimeout(run, isFirst ? 0 : 500)` — const, line 119
- `function PreviewToggle(` — function, line 185
- `const load = useCallback(async ()` — const, line 217
- `const next = await api.getSourceOutline(sourceRef)` — const, line 220
- `const prior = next.selection.selectedUnitIds` — const, line 222
- `const priorOverrides: Record<string, string> =` — const, line 224
- `const unitId = ov["unitId"] as string | undefined` — const, line 226
- `const op = ov["op"] as string | undefined` — const, line 227
- `const escCloses = simpleShell()` — const, line 249
- `function onKeyDown(e: KeyboardEvent)` — function, line 251
- `const tag = (e.target as HTMLElement | null)?.tagName` — const, line 254
- `function toggleUnit(unitId: string)` — function, line 265
- `const next = new Set(current)` — const, line 267
- `function cycleOverride(unitId: string)` — function, line 274
- `const next =` — const, line 276
- `const now = next[unitId]` — const, line 277
- `async function persistSelection(roleValue: string = role)` — function, line 285
- `const boundaryOverrides = Object.entries(overrides).map(([unitId, op])` — const, line 287
- `async function onRoleChange(nextRole: string)` — function, line 297
- `async function toPlan()` — function, line 307
- `const active = step === s.id` — const, line 354
- `function kindGlyph(unit: EffectiveUnitDto):` — function, line 433
- `function ResultingShape(` — function, line 439
- `const overridesKey = JSON.stringify(overrides)` — const, line 449
- `let cancelled = false` — let, line 452
- `const boundaryOverrides = Object.entries(overrides).map(([unitId, op])` — const, line 454
- `const run = ()` — const, line 455
- `const timer = window.setTimeout(run, 400)` — const, line 471
- `const units = shape?.units ?? []` — const, line 480
- `function RoleControl(` — function, line 542
- `const effectiveRole = role || suggestedRole || ""` — const, line 551
- `const overridden = role !== "" && suggestedRole != null && role !== suggestedRole` — const, line 552
- `const assessmentOnly = ASSESSMENT_ONLY_ROLES.has(effectiveRole)` — const, line 553
- `function OutlineView(` — function, line 589
- `const selectedIds = outline.units.filter((u)` — const, line 617
- `const selectedCount = selectedIds.length` — const, line 618
- `const selectedTokens = outline.units.filter((u)` — const, line 619
- `async function save()` — function, line 621
- `function UnitRow(` — function, line 717
- `const pages = unit.pageStart != null ? `p$` — const, line 730
- `const signals = SIGNAL_ORDER.filter((k)` — const, line 732
- `function SingleUnitSummary(` — function, line 782
- `const label = unit.label || unit.unitId` — const, line 797
- `const scheme = typeof unit.locator?.scheme === "string" ? (unit.locator.scheme as string) : ""` — const, line 798
- `const isTimed = scheme === "time_range" || /transcript|caption|subtitle/i.test(label)` — const, line 799
- `const noun = isTimed ? "transcript" : "document"` — const, line 800
- `function BuildPlanView(` — function, line 828
- `const firstPlanFetch = useRef(true)` — const, line 862
- `let cancelled = false` — let, line 865
- `const invalidCeilings = useMemo(()` — const, line 882
- `const value = ceilings[field]` — const, line 885
- `const overrides = useMemo(()` — const, line 890
- `const diff: Partial<IngestBudgetsDto> =` — const, line 892
- `const overridesKey = JSON.stringify(overrides)` — const, line 899
- `const planSubjectId = pinned?.subjectId ?? subjectId` — const, line 902
- `let cancelled = false` — let, line 905
- `const isFirst = firstPlanFetch.current` — const, line 906
- `const run = ()` — const, line 908
- `const timer = window.setTimeout(run, isFirst ? 0 : 400)` — const, line 919
- `const canStart = pinned !== null && invalidCeilings.length === 0` — const, line 928
- `async function startBuild()` — function, line 929
- `const batch = await api.buildStudyMap(` — const, line 936
- `const routingColor = plan.routing === "create" ? COLOR.green : COLOR.cyan` — const, line 952
- `function StageRow(` — function, line 1088
- `const color = stage.exceedsCeiling ? COLOR.red : COLOR.cyan` — const, line 1089
- `const pct = Math.min(100, (stage.inputTokens / Math.max(stage.ceiling, 1)) * 100)` — const, line 1090
- `function ConsentSummary(` — function, line 1116
- `function CeilingControls(` — function, line 1133
- `const dirty = defaults != null && BUDGET_FIELDS.some((field)` — const, line 1154
- `const bad = invalid.includes(field)` — const, line 1179
- `function RepairDialog(` — function, line 1224
- `async function start()` — function, line 1242
- `const pageList = pages .split(",") .map((s)` — const, line 1251
- `const input: StartExtractionRepairInput =` — const, line 1259
- `function OptionChip(` — function, line 1343
- `const color = on ? (danger ? COLOR.red : COLOR.amber) : COLOR.textFaint` — const, line 1344
- `function buttonStyle(primary: boolean): CSSProperties` — function, line 1355

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
- [[Reference/Desktop/TypeScript/components/AddToCollection|src/components/AddToCollection.tsx]] — import-or-re-export; imports `AddToCollectionPanel`, `SYLLABUS_ROLE_HINT`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`, `TermCheckbox`, `TermSelect`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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
