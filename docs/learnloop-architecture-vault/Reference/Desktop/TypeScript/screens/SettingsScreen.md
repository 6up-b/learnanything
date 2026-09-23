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
source_commit: "7f37f7bef54c4dc6170182720840faf546d9f51b"
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
| Source lines | 899 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `7f37f7bef54c4dc6170182720840faf546d9f51b` |
| Commit timestamp | `2026-09-03T10:56:04-07:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]]

## Public API

- `export const PALETTE_STORAGE_KEY = "learnloop.palette"` — const, line 63
- `export function SettingsOverlay(` — function, line 92
- `export function SettingsScreen(` — function, line 135

## Internal implementation anchors

- `const USE_CASES: Array<` — const, line 21
- `const TRANSCRIPTION_PROVIDERS = [` — const, line 31
- `const OPENROUTER_TRANSCRIPTION_MODEL_SUGGESTION = "google/gemini-2.5-flash"` — const, line 35
- `const OPENROUTER_VIDEO_MODEL_SUGGESTION = "google/veo-3.1"` — const, line 37
- `function isNewInteger(draft: number | null, current: number): draft is number` — function, line 40
- `const ANIMATION_RENDERER_OPTIONS = [` — const, line 43
- `const ANIMATION_QUALITY_OPTIONS = [` — const, line 47
- `const BUDGET_ROWS: Array<` — const, line 55
- `const PALETTES = [` — const, line 64
- `function applyPalette(palette: string)` — function, line 72
- `type UseCaseDraft =` — type, line 82
- `type SettingsScreenProps =` — type, line 84
- `const settingsQuery = useCachedQuery(["get_settings"], ()` — const, line 145
- `const settings: SettingsDto | null = settingsQuery.data ?? null` — const, line 149
- `const acceptSettings = useCallback((next: SettingsDto)` — const, line 169
- `const providerByName = useMemo(()` — const, line 177
- `const map = new Map<string,` — const, line 178
- `const providerOptions = useMemo( ()` — const, line 185
- `const currentForUseCase = useCallback( (useCase: (typeof USE_CASES)[number]): UseCaseDraft` — const, line 193
- `const routed = settings?.ai.routing[useCase.primaryRoute] ?? settings?.ai.activeProvider ?? "codex"` — const, line 195
- `const model = providerByName.get(routed)?.model ?? providerByName.get("openrouter")?.model ?? ""` — const, line 197
- `const draftFor = (useCase: (typeof USE_CASES)[number]): UseCaseDraft` — const, line 205
- `const applyUseCase = async (useCase: (typeof USE_CASES)[number])` — const, line 208
- `const draft = draftFor(useCase)` — const, line 209
- `const choice: UseCaseChoiceInput =` — const, line 215
- `const result = await api.updateAiSettings(` — const, line 219
- `const next =` — const, line 222
- `const saveKey = async (value: string)` — const, line 234
- `const result = await api.setOpenrouterApiKey(value)` — const, line 239
- `const saveBudgets = async ()` — const, line 253
- `const budgets: Partial<IngestBudgetsDto> =` — const, line 255
- `const result = await api.updateIngestSettings(` — const, line 261
- `const rowStyle =` — const, line 278
- `const labelStyle =` — const, line 287
- `const hintStyle =` — const, line 288
- `const inputStyle =` — const, line 289
- `const buttonStyle = (enabled: boolean)` — const, line 298
- `const envOverride = settings.ai.envProviderOverride` — const, line 318
- `const budgetsDirty = BUDGET_ROWS.some((` — const, line 319
- `const draft = budgetDrafts[field]` — const, line 321
- `const budgetsInvalid = BUDGET_ROWS.some((` — const, line 326
- `const draft = budgetDrafts[field]` — const, line 328
- `const transcriptionProvider = transcriptionProviderDraft ?? settings.ingest.transcriptionProvider` — const, line 335
- `const transcriptionDirty = (transcriptionProviderDraft !== null && transcriptionProviderDraft !== settings.ingest.transcriptionProvider) || (transcriptionModelDraft !== null && transcriptionModelDraft !== settings.ingest.transcriptionModel) || (transcriptionU…` — const, line 336
- `const draft = draftFor(useCase)` — const, line 371
- `const current = currentForUseCase(useCase)` — const, line 372
- `const isManual = useCase.id === "grading" && manualGrading && !drafts[useCase.id]` — const, line 373
- `const dirty = !isManual && (draft.provider !== current.provider || (draft.provider === "openrouter" && draft.model !== current.model))` — const, line 374
- `const canApply = dirty && busy === null && (draft.provider !== "openrouter" || draft.model.trim().length > 0)` — const, line 376
- `const options = useCase.id === "grading" ? [...providerOptions, "manual"] : providerOptions` — const, line 378
- `const model = transcriptionModelDraft ?? settings.ingest.transcriptionModel` — const, line 498
- `const slug = videoModelDraft.trim()` — const, line 671
- `const saved = settings.ingest.budgets[field]` — const, line 797
- `const draft = budgetDrafts[field]` — const, line 799
- `const value = draft ?? saved` — const, line 800
- `const invalid = !Number.isFinite(value) || value < min || value > max` — const, line 801

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `SettingsOverlay`; references `SettingsOverlay`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AnimationRenderer`, `IngestBudgetField`, `IngestBudgetsDto`, `RuntimeHealth`, `SettingsDto`, `UseCaseChoiceInput`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/components/CommandOverlayFrame|src/components/CommandOverlayFrame.tsx]] — import-or-re-export; imports `CommandOverlayFrame`
- [[Reference/Desktop/TypeScript/components/NativeMediaSettings|src/components/NativeMediaSettings.tsx]] — import-or-re-export; imports `NativeMediaSettings`
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
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/SettingsScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/SettingsScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
