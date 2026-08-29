---
title: "Desktop module · src/screens/SettingsScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.SettingsScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/SettingsScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/SettingsScreen.tsx"
source_commit: "64d39668a1d275c2910f98388ac612ae5391d694"
source_commit_timestamp: "2026-07-27T19:00:47-05:00"
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

# `src/screens/SettingsScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `SettingsScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/SettingsScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/SettingsScreen.tsx) |
| Source lines | 714 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `64d39668a1d275c2910f98388ac612ae5391d694` |
| Commit timestamp | `2026-07-27T19:00:47-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]]

## Public API

- `export const PALETTE_STORAGE_KEY = "learnloop.palette"` — const, line 43
- `export function SettingsOverlay(` — function, line 72
- `export function SettingsScreen(` — function, line 115

## Internal implementation anchors

- `const USE_CASES: Array<` — const, line 17
- `const TRANSCRIPTION_PROVIDERS = [` — const, line 27
- `const OPENROUTER_TRANSCRIPTION_MODEL_SUGGESTION = "google/gemini-2.5-flash"` — const, line 31
- `const BUDGET_ROWS: Array<` — const, line 35
- `const PALETTES = [` — const, line 44
- `function applyPalette(palette: string)` — function, line 52
- `type UseCaseDraft =` — type, line 62
- `type SettingsScreenProps =` — type, line 64
- `const acceptSettings = useCallback((next: SettingsDto)` — const, line 137
- `const providerByName = useMemo(()` — const, line 149
- `const map = new Map<string,` — const, line 150
- `const providerOptions = useMemo( ()` — const, line 157
- `const currentForUseCase = useCallback( (useCase: (typeof USE_CASES)[number]): UseCaseDraft` — const, line 165
- `const routed = settings?.ai.routing[useCase.primaryRoute] ?? settings?.ai.activeProvider ?? "codex"` — const, line 167
- `const model = providerByName.get(routed)?.model ?? providerByName.get("openrouter")?.model ?? ""` — const, line 169
- `const draftFor = (useCase: (typeof USE_CASES)[number]): UseCaseDraft` — const, line 177
- `const applyUseCase = async (useCase: (typeof USE_CASES)[number])` — const, line 180
- `const draft = draftFor(useCase)` — const, line 181
- `const choice: UseCaseChoiceInput =` — const, line 187
- `const result = await api.updateAiSettings(` — const, line 191
- `const next =` — const, line 194
- `const saveKey = async (value: string)` — const, line 206
- `const result = await api.setOpenrouterApiKey(value)` — const, line 209
- `const saveBudgets = async ()` — const, line 235
- `const budgets: Partial<IngestBudgetsDto> =` — const, line 237
- `const result = await api.updateIngestSettings(` — const, line 243
- `const rowStyle =` — const, line 260
- `const labelStyle =` — const, line 269
- `const hintStyle =` — const, line 270
- `const inputStyle =` — const, line 271
- `const buttonStyle = (enabled: boolean)` — const, line 280
- `const envOverride = settings.ai.envProviderOverride` — const, line 300
- `const budgetsDirty = BUDGET_ROWS.some((` — const, line 301
- `const draft = budgetDrafts[field]` — const, line 303
- `const budgetsInvalid = BUDGET_ROWS.some((` — const, line 308
- `const draft = budgetDrafts[field]` — const, line 310
- `const transcriptionProvider = transcriptionProviderDraft ?? settings.ingest.transcriptionProvider` — const, line 317
- `const transcriptionDirty = (transcriptionProviderDraft !== null && transcriptionProviderDraft !== settings.ingest.transcriptionProvider) || (transcriptionModelDraft !== null && transcriptionModelDraft !== settings.ingest.transcriptionModel) || (transcriptionU…` — const, line 318
- `const draft = draftFor(useCase)` — const, line 353
- `const current = currentForUseCase(useCase)` — const, line 354
- `const isManual = useCase.id === "grading" && manualGrading && !drafts[useCase.id]` — const, line 355
- `const dirty = !isManual && (draft.provider !== current.provider || (draft.provider === "openrouter" && draft.model !== current.model))` — const, line 356
- `const canApply = dirty && busy === null && (draft.provider !== "openrouter" || draft.model.trim().length > 0)` — const, line 358
- `const options = useCase.id === "grading" ? [...providerOptions, "manual"] : providerOptions` — const, line 360
- `const model = transcriptionModelDraft ?? settings.ingest.transcriptionModel` — const, line 494
- `const saved = settings.ingest.budgets[field]` — const, line 612
- `const draft = budgetDrafts[field]` — const, line 614
- `const value = draft ?? saved` — const, line 615
- `const invalid = !Number.isFinite(value) || value < min || value > max` — const, line 616

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `SettingsOverlay`; references `SettingsOverlay`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `IngestBudgetField`, `IngestBudgetsDto`, `RuntimeHealth`, `SettingsDto`, `UseCaseChoiceInput`
- [[Reference/Desktop/TypeScript/components/CommandOverlayFrame|src/components/CommandOverlayFrame.tsx]] — import-or-re-export; imports `CommandOverlayFrame`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `TermCheckbox`, `TermSelect`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `SectionHeader`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Configure AI Providers|Configure AI Providers]] — owns provider setup.

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

1. Modify [apps/learnloop-tauri/src/screens/SettingsScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/SettingsScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
