---
title: "Desktop module · src/components/recipeedit/RecipeTreeEditor.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.recipeedit.RecipeTreeEditor"
language: "TypeScript"
area: "TypeScript/components/recipeedit"
source_path: "apps/learnloop-tauri/src/components/recipeedit/RecipeTreeEditor.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/recipeedit/RecipeTreeEditor.tsx"
source_commit: "324e21708f4ec712cc669086f5a261efa70f57ff"
source_commit_timestamp: "2026-07-15T11:03:42-04:00"
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

# `src/components/recipeedit/RecipeTreeEditor.tsx`

Area: [[Reference/Desktop/TypeScript/components/recipeedit/_area|TypeScript/components/recipeedit]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `RecipeTreeEditor` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/recipeedit/RecipeTreeEditor.tsx](../../../../../../../apps/learnloop-tauri/src/components/recipeedit/RecipeTreeEditor.tsx) |
| Source lines | 775 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/recipeedit/_area|TypeScript/components/recipeedit]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `324e21708f4ec712cc669086f5a261efa70f57ff` |
| Commit timestamp | `2026-07-15T11:03:42-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] → [[Reference/Desktop/TypeScript/components/recipeedit/RecipeTreeEditor|src/components/recipeedit/RecipeTreeEditor.tsx]]

## Public API

- `export function RecipeTreeEditor(` — function, line 94

## Internal implementation anchors

- `const CAPABILITIES = [ "retrieval", "schema_interpretation", "procedure_execution", "method_selection", "coordination", ] as const` — const, line 22
- `const MODALITIES = ["hard", "path_specific", "facilitating", "instructional_order"] as const` — const, line 30
- `type Role = "all_of" | "any_of"` — type, line 32
- `interface EditComponent` — interface, line 36
- `interface EditRecipe` — interface, line 41
- `interface EditBlueprint` — interface, line 48
- `function cloneComponent(c: RecipeComponentDto): EditComponent` — function, line 54
- `function seed(blueprints: LoBlueprintDto[]): EditBlueprint[]` — function, line 57
- `function snakeComponent(c: EditComponent): Record<string, unknown>` — function, line 73
- `function snakeRecipe(r: EditRecipe): Record<string, unknown>` — function, line 76
- `function snakeBlueprint(bp: EditBlueprint): Record<string, unknown>` — function, line 85
- `const shortFacet = (f: string): string` — const, line 89
- `const pct = (v: number | null | undefined): string` — const, line 90
- `const fresh = seed(blueprints ?? [])` — const, line 114
- `let alive = true` — let, line 126
- `const mutate = useCallback((fn: (bps: EditBlueprint[])` — const, line 138
- `const next = structuredClone(prev) as EditBlueprint[]` — const, line 140
- `const changedIds = useMemo(()` — const, line 147
- `const origById = new Map(original.map((b)` — const, line 148
- `const ids: string[] = []` — const, line 149
- `const hasBlueprints = (blueprints ?? []).length > 0` — const, line 156
- `async function file()` — function, line 158
- `const edits = draft .filter((bp)` — const, line 163
- `const result = await api.proposeGraphEdits(` — const, line 171
- `const invalid = result.items.filter((it)` — const, line 172
- `function BlueprintEditor(` — function, line 292
- `function RecipeEditor(` — function, line 342
- `const move = (role: Role, idx: number)` — const, line 353
- `const from = role === "all_of" ? r.allOf : r.anyOf` — const, line 355
- `const to = role === "all_of" ? r.anyOf : r.allOf` — const, line 356
- `const remove = (role: Role, idx: number)` — const, line 360
- `const setModality = (role: Role, idx: number, modality: string)` — const, line 362
- `const add = (role: Role, c: EditComponent)` — const, line 364
- `function RoleGroup(` — function, line 427
- `const arr = Array.isArray(children) ? children.flat() : [children]` — const, line 428
- `const hasContent = arr.some((c)` — const, line 429
- `function ComponentRow(` — function, line 438
- `function AddComponent(` — function, line 480
- `const matches = useMemo(()` — const, line 495
- `const needle = q.trim().toLowerCase()` — const, line 496
- `const ready = facet.trim().length > 0` — const, line 503
- `function BlastRadiusPanel(` — function, line 561
- `const timer = useRef<ReturnType<typeof setTimeout> | null>(null)` — const, line 573
- `const signature = useMemo(()` — const, line 575
- `let alive = true` — let, line 581
- `const cur = preview?.current.readiness ?? null` — const, line 604
- `const prop = preview?.proposed.readiness ?? null` — const, line 605
- `const delta = cur != null && prop != null ? prop - cur : null` — const, line 606
- `const bnChanged = preview && (preview.current.bottleneck?.facet !== preview.proposed.bottleneck?.facet || preview.current.bottleneck?.capability !== preview.proposed.bottleneck?.capability)` — const, line 607
- `const toggleBtn: CSSProperties =` — const, line 703
- `const linkBtn: CSSProperties =` — const, line 713
- `const numInput: CSSProperties =` — const, line 723
- `const rationaleInput: CSSProperties =` — const, line 733
- `const fileBar: CSSProperties =` — const, line 738
- `const ruleLegendStyle: CSSProperties =` — const, line 747
- `const suggestBox: CSSProperties =` — const, line 756
- `const suggestRow: CSSProperties =` — const, line 769

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `RecipeTreeEditor`; references `RecipeTreeEditor`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `BlueprintReadinessPreviewDto`, `FacetSummaryDto`, `LoBlueprintDto`, `RecipeComponentDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `HelpTooltip`, `Pill`, `SectionHeader`, `TermSelect`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Build a Study Map|Build a Study Map]] — owns the map-building journey.
- [[Concepts/Canonical Knowledge Model#Core entities|canonical knowledge entities]] — owns graph meaning.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_knowledge_model.py](../../../../../../../tests/test_sidecar_knowledge_model.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_graph_editor_reads.py](../../../../../../../tests/test_graph_editor_reads.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_graph_edit_proposals.py](../../../../../../../tests/test_graph_edit_proposals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_build_study_map_routing.py](../../../../../../../tests/test_build_study_map_routing.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/recipeedit/RecipeTreeEditor.tsx](../../../../../../../apps/learnloop-tauri/src/components/recipeedit/RecipeTreeEditor.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
