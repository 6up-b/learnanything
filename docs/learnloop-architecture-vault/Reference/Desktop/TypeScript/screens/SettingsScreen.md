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
| Source lines | 1029 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]]

## Public API

- `export const PALETTE_STORAGE_KEY = "learnloop.palette"` — const, line 72
- `export function SettingsOverlay(` — function, line 101
- `export function SettingsScreen(` — function, line 144

## Internal implementation anchors

- `const USE_CASES: Array<` — const, line 27
- `const TRANSCRIPTION_PROVIDERS = [` — const, line 40
- `const OPENROUTER_TRANSCRIPTION_MODEL_SUGGESTION = "google/gemini-2.5-flash"` — const, line 44
- `const OPENROUTER_VIDEO_MODEL_SUGGESTION = "google/veo-3.1"` — const, line 46
- `function isNewInteger(draft: number | null, current: number): draft is number` — function, line 49
- `const ANIMATION_RENDERER_OPTIONS = [` — const, line 52
- `const ANIMATION_QUALITY_OPTIONS = [` — const, line 56
- `const BUDGET_ROWS: Array<` — const, line 64
- `const PALETTES = [` — const, line 73
- `function applyPalette(palette: string)` — function, line 81
- `type UseCaseDraft =` — type, line 91
- `type SettingsScreenProps =` — type, line 93
- `const settingsQuery = useCachedQuery(["get_settings"], ()` — const, line 154
- `const settings: SettingsDto | null = settingsQuery.data ?? null` — const, line 158
- `const acceptSettings = useCallback((next: SettingsDto)` — const, line 179
- `const providerByName = useMemo(()` — const, line 187
- `const map = new Map<string,` — const, line 188
- `const providerOptions = useMemo( ()` — const, line 195
- `const currentForUseCase = useCallback( (useCase: (typeof USE_CASES)[number]): UseCaseDraft` — const, line 205
- `const routed = settings?.ai.routing[useCase.primaryRoute] ?? (useCase.fallbackRoute ? settings?.ai.routing[useCase.fallbackRoute] : undefined) ?? settings?.ai.activeProvider ?? "codex"` — const, line 207
- `const model = providerByName.get(routed)?.model ?? providerByName.get("openrouter")?.model ?? ""` — const, line 213
- `const draftFor = (useCase: (typeof USE_CASES)[number]): UseCaseDraft` — const, line 221
- `const applyUseCase = async (useCase: (typeof USE_CASES)[number])` — const, line 224
- `const draft = draftFor(useCase)` — const, line 225
- `const choice: UseCaseChoiceInput =` — const, line 231
- `const result = await api.updateAiSettings(` — const, line 235
- `const next =` — const, line 238
- `const saveKey = async (value: string)` — const, line 250
- `const result = await api.setOpenrouterApiKey(value)` — const, line 255
- `const saveBudgets = async ()` — const, line 269
- `const budgets: Partial<IngestBudgetsDto> =` — const, line 271
- `const result = await api.updateIngestSettings(` — const, line 277
- `const rowStyle =` — const, line 294
- `const labelStyle =` — const, line 303
- `const hintStyle =` — const, line 304
- `const inputStyle =` — const, line 305
- `const buttonStyle = (enabled: boolean)` — const, line 314
- `const envOverride = settings.ai.envProviderOverride` — const, line 334
- `const budgetsDirty = BUDGET_ROWS.some((` — const, line 335
- `const draft = budgetDrafts[field]` — const, line 337
- `const budgetsInvalid = BUDGET_ROWS.some((` — const, line 342
- `const draft = budgetDrafts[field]` — const, line 344
- `const transcriptionProvider = transcriptionProviderDraft ?? settings.ingest.transcriptionProvider` — const, line 351
- `const transcriptionDirty = (transcriptionProviderDraft !== null && transcriptionProviderDraft !== settings.ingest.transcriptionProvider) || (transcriptionModelDraft !== null && transcriptionModelDraft !== settings.ingest.transcriptionModel) || (transcriptionU…` — const, line 352
- `const draft = draftFor(useCase)` — const, line 387
- `const current = currentForUseCase(useCase)` — const, line 388
- `const isManual = useCase.id === "grading" && manualGrading && !drafts[useCase.id]` — const, line 389
- `const dirty = !isManual && (draft.provider !== current.provider || (draft.provider === "openrouter" && draft.model !== current.model))` — const, line 390
- `const canApply = dirty && busy === null && (draft.provider !== "openrouter" || draft.model.trim().length > 0)` — const, line 392
- `const options = useCase.id === "grading" ? [...providerOptions, "manual"] : providerOptions` — const, line 394
- `const model = transcriptionModelDraft ?? settings.ingest.transcriptionModel` — const, line 621
- `const slug = videoModelDraft.trim()` — const, line 794
- `const saved = settings.ingest.budgets[field]` — const, line 920
- `const draft = budgetDrafts[field]` — const, line 922
- `const value = draft ?? saved` — const, line 923
- `const invalid = !Number.isFinite(value) || value < min || value > max` — const, line 924

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
- [[Reference/Desktop/TypeScript/components/ChatGPTPlanSettings|src/components/ChatGPTPlanSettings.tsx]] — import-or-re-export; imports `ChatGPTPlanSettings`
- [[Reference/Desktop/TypeScript/components/CommandOverlayFrame|src/components/CommandOverlayFrame.tsx]] — import-or-re-export; imports `CommandOverlayFrame`
- [[Reference/Desktop/TypeScript/components/NativeMediaSettings|src/components/NativeMediaSettings.tsx]] — import-or-re-export; imports `NativeMediaSettings`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `TermCheckbox`, `TermSelect`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `SectionHeader`
- [[Reference/Desktop/TypeScript/screens/practice/HelpStyleSettings|src/screens/practice/HelpStyleSettings.tsx]] — import-or-re-export; imports `HelpStyleSettings`
- [[Reference/Desktop/TypeScript/screens/reader/HiddenNotesSettings|src/screens/reader/HiddenNotesSettings.tsx]] — import-or-re-export; imports `HiddenNotesSettings`
- [[Reference/Desktop/TypeScript/screens/reader/NotesGapsSettings|src/screens/reader/NotesGapsSettings.tsx]] — import-or-re-export; imports `NotesGapsSettings`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderCorrespondenceSettings|src/screens/reader/ReaderCorrespondenceSettings.tsx]] — import-or-re-export; imports `ReaderCorrespondenceSettings`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderCueSettings|src/screens/reader/ReaderCueSettings.tsx]] — import-or-re-export; imports `ReaderCueSettings`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Configure AI Providers|Configure AI Providers]] — owns provider setup.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/SettingsScreen.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/SettingsScreen.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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
