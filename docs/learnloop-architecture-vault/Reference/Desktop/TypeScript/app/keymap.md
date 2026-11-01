---
title: "Desktop module · src/app/keymap.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.keymap"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/keymap.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/keymap.ts"
source_commit: "725ef0e14d3ada9d88baaebc51a3273fc88226d0"
source_commit_timestamp: "2026-10-22T17:25:40-04:00"
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

# `src/app/keymap.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `KeyAction`, `KeyBinding`, `ADD_FILES_CHORD`, `shellBindings` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/keymap.ts](../../../../../../apps/learnloop-tauri/src/app/keymap.ts) |
| Source lines | 253 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `725ef0e14d3ada9d88baaebc51a3273fc88226d0` |
| Commit timestamp | `2026-10-22T17:25:40-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]]

## Public API

- `export type KeyAction = |` — type, line 17
- `export interface KeyBinding` — interface, line 34
- `export const ADD_FILES_CHORD: Chord =` — const, line 61
- `export function shellBindings(shell: ShellMode): KeyBinding[]` — function, line 113
- `export const CLASSIC_REPLACEMENTS: Readonly<Record<string, string>> =` — const, line 119
- `export const SCOPED_OVERRIDES: ReadonlyArray<` — const, line 135
- `export function screenLeavesKey(event: KeyboardEvent, options: ScreenKeyOptions =` — function, line 174
- `export interface ScreenKeyOptions` — interface, line 182
- `export const INTERACTIVE_SELECTOR = [ "button", "a[href]", "input", "select", "textarea", '[contenteditable]:not([contenteditable="false"])', '[role="button"]', '[role="link"]', '[role="menuitem"]', '[role="option"]', '[role="tab"]', '[role="checkbox"]', '[ro…` — const, line 201
- `export function controlOwner(control: Element): string` — function, line 219
- `export function matchesChord(chord: Chord, event: KeyboardEvent): boolean` — function, line 234
- `export function matchShellKey(event: KeyboardEvent, shell: ShellMode, typing: boolean): KeyBinding | null` — function, line 243

## Internal implementation anchors

- `interface Chord` — interface, line 26
- `function binding( id: string, keys: string, label: string, action: KeyAction, chord: Chord, options:` — function, line 48
- `function addBindings(): KeyBinding[]` — function, line 63
- `function classicBindings(): KeyBinding[]` — function, line 70
- `function simpleBindings(): KeyBinding[]` — function, line 84
- `const scoped = control.closest("[data-key-scope]")` — const, line 221
- `function onForeignControl(target: EventTarget | null, scopes: string[]): boolean` — function, line 225
- `const control = target.closest(INTERACTIVE_SELECTOR)` — const, line 227

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `KeyAction`, `matchShellKey`; references `KeyAction`, `matchShellKey`
- [[Reference/Desktop/TypeScript/app/ShellChromeRoot|src/app/ShellChromeRoot.tsx]] — import-or-re-export: `matchShellKey`; references `matchShellKey`
- [[Reference/Desktop/TypeScript/app/useGlobalAdd|src/app/useGlobalAdd.ts]] — import-or-re-export: `ADD_FILES_CHORD`, `matchesChord`; references `ADD_FILES_CHORD`, `matchesChord`
- [[Reference/Desktop/TypeScript/components/AddSource|src/components/AddSource.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/ConnectAI|src/components/ConnectAI.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/FacetInspector|src/components/FacetInspector.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/KeyboardHelp|src/components/KeyboardHelp.tsx]] — import-or-re-export: `CLASSIC_REPLACEMENTS`, `SCOPED_OVERRIDES`, `shellBindings`; references `CLASSIC_REPLACEMENTS`, `SCOPED_OVERRIDES`, `shellBindings`
- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/OutlineAndPlan|src/components/OutlineAndPlan.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/SessionFinishHud|src/components/SessionFinishHud.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/StudyMapBriefWizard|src/components/StudyMapBriefWizard.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/WriteCardDialog|src/components/WriteCardDialog.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/pdfSelection/usePdfSelection|src/components/pdfSelection/usePdfSelection.ts]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/RepairScreen|src/screens/RepairScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/ReviewScreen|src/screens/ReviewScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryPane|src/screens/reader/LibraryPane.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/reader/WrapUpPanel|src/screens/reader/WrapUpPanel.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/reader/bareAlt|src/screens/reader/bareAlt.ts]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/reader/useIntentBox|src/screens/reader/useIntentBox.ts]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRecap|src/screens/reader/useReaderRecap.ts]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/today/DailyPlanView|src/screens/today/DailyPlanView.tsx]] — import-or-re-export: `screenLeavesKey`; references `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `INTERACTIVE_SELECTOR`, `screenLeavesKey`; references `INTERACTIVE_SELECTOR`, `screenLeavesKey`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `activeShell`
- [[Reference/Desktop/TypeScript/app/shell|src/app/shell.ts]] — import-or-re-export; imports `Place`, `ShellMode`, `UthToolId`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `SHOW_GOLDEN_PATH`, `TopTab`, `navTabs`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/SqliteBrowser.readOnly.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/SqliteBrowser.readOnly.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/keymap.test.ts](../../../../../../apps/learnloop-tauri/src/app/keymap.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.fixRound3.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.fixRound3.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/keymap.ts](../../../../../../apps/learnloop-tauri/src/app/keymap.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
