---
title: "Desktop module · src/components/ui.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.ui"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/ui.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/ui.tsx"
source_commit: "971d7c274e09873d726d43578cd080e4d8865571"
source_commit_timestamp: "2026-07-27T06:01:19-04:00"
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

# `src/components/ui.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `ui` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/ui.tsx](../../../../../../apps/learnloop-tauri/src/components/ui.tsx) |
| Source lines | 389 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `971d7c274e09873d726d43578cd080e4d8865571` |
| Commit timestamp | `2026-07-27T06:01:19-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]]

## Public API

- `export const SHOW_GOLDEN_PATH = false` — const, line 11
- `export const navTabs = allNavTabs.filter((tab)` — const, line 30
- `export type TopTab = (typeof allNavTabs)[number]["id"] | "errors" | "settings"` — type, line 33
- `export function Titlebar()` — function, line 43
- `export type NavBadgeCounts = Partial<Record<TopTab, number>>` — type, line 237
- `export function TerminalFrame(` — function, line 239
- `export function SectionHeader(` — function, line 303
- `export function Pill(` — function, line 307
- `export function Card(` — function, line 311
- `export function EntityLink(` — function, line 327
- `export function EmptyPlaceholder(` — function, line 372
- `export function KeyBar(` — function, line 380

## Internal implementation anchors

- `const allNavTabs = [` — const, line 13
- `function getAppWindow(): ReturnType<typeof getCurrentWindow> | null` — function, line 35
- `const appWindow = useMemo(getAppWindow, [])` — const, line 44
- `let unlisten: (()` — let, line 49
- `const sync = ()` — const, line 50
- `function VaultPath(` — function, line 84
- `const wrapRef = useRef<HTMLSpanElement | null>(null)` — const, line 86
- `const chipRef = useRef<HTMLSpanElement | null>(null)` — const, line 87
- `const recents = useMemo(()` — const, line 91
- `const list = listRecentVaults()` — const, line 93
- `const labelFor = useMemo(()` — const, line 99
- `const counts = new Map<string, number>()` — const, line 100
- `const name = vaultName(p)` — const, line 102
- `const onDocMouseDown = (event: MouseEvent)` — const, line 111
- `const switchTo = (path: string)` — const, line 118
- `const addNew = async ()` — const, line 123
- `const selected = await openDialog(` — const, line 125
- `function SettingsChip(` — function, line 197
- `const NAV_BADGE_STYLE: CSSProperties =` — const, line 227
- `const count = badges?.[tab.id] ?? 0` — const, line 266
- `const SPINNER_FRAMES = "⣾⣽⣻⢿⡿⣟⣯⣷"` — const, line 361
- `function Spinner()` — function, line 363
- `const id = setInterval(()` — const, line 366

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `EmptyPlaceholder`, `NavBadgeCounts`, `SHOW_GOLDEN_PATH`, `TerminalFrame`, `TopTab`, `navTabs`; references `EmptyPlaceholder`, `NavBadgeCounts`, `SHOW_GOLDEN_PATH`, `TerminalFrame`, `TopTab`, `navTabs`
- [[Reference/Desktop/TypeScript/components/CommandPalette|src/components/CommandPalette.tsx]] — import-or-re-export: `Pill`, `TopTab`, `navTabs`; references `Pill`, `TopTab`, `navTabs`
- [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]] — import-or-re-export: `Card`, `Pill`, `SectionHeader`; references `Card`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/components/FacetInspector|src/components/FacetInspector.tsx]] — import-or-re-export: `EntityLink`; references `EntityLink`
- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export: `TopTab`; references `TopTab`
- [[Reference/Desktop/TypeScript/components/ProbeBlockResult|src/components/ProbeBlockResult.tsx]] — import-or-re-export: `Pill`; references `Pill`
- [[Reference/Desktop/TypeScript/components/RepairAffordances|src/components/RepairAffordances.tsx]] — import-or-re-export: `Pill`; references `Pill`
- [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]] — import-or-re-export: `Card`, `Pill`, `SectionHeader`; references `Card`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export: `Card`, `SectionHeader`; references `Card`, `SectionHeader`
- [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]] — import-or-re-export: `Card`, `SectionHeader`; references `Card`, `SectionHeader`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `EntityLink`, `KeyBar`, `Pill`; references `EntityLink`, `KeyBar`, `Pill`
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export: `EntityLink`; references `EntityLink`
- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `EntityLink`; references `EntityLink`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `Card`, `EntityLink`, `KeyBar`, `Pill`, `SectionHeader`; references `Card`, `EntityLink`, `KeyBar`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — import-or-re-export: `EntityLink`; references `EntityLink`
- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export: `SectionHeader`; references `SectionHeader`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `EmptyPlaceholder`, `KeyBar`, `SectionHeader`; references `EmptyPlaceholder`, `KeyBar`, `SectionHeader`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `EmptyPlaceholder`, `EntityLink`; references `EmptyPlaceholder`, `EntityLink`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/app/recentVaults|src/app/recentVaults.ts]] — import-or-re-export; imports `listRecentVaults`, `samePath`, `vaultName`, `vaultNameWithParent`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/api/window`, `@tauri-apps/plugin-dialog`, `react`

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

1. Modify [apps/learnloop-tauri/src/components/ui.tsx](../../../../../../apps/learnloop-tauri/src/components/ui.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
