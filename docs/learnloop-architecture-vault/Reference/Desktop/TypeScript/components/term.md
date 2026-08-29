---
title: "Desktop module · src/components/term.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.term"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/term.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/term.tsx"
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

# `src/components/term.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `term` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/term.tsx](../../../../../../apps/learnloop-tauri/src/components/term.tsx) |
| Source lines | 810 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AdjudicationOverlay|src/components/AdjudicationOverlay.tsx]] → [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]]

## Public API

- `export const COLOR =` — const, line 14
- `export const FONT_MONO = '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace'` — const, line 46
- `export type PillColor = "purple" | "green" | "cyan" | "amber" | "red" | "pink" | "slate"` — type, line 49
- `export function Pill(` — function, line 61
- `export function TermCheckbox(` — function, line 92
- `export function modePillColor(mode: string | null | undefined): PillColor` — function, line 168
- `export function measurementStateLabel(state: string | null | undefined): string` — function, line 197
- `export function measurementStateColor(state: string | null | undefined): string` — function, line 201
- `export type TermSelectOption =` — type, line 212
- `export function TermSelect(` — function, line 214
- `export function SectionHeader(` — function, line 443
- `export function PlainEnglishPanel(` — function, line 465
- `export function DisclosureHeader(` — function, line 503
- `export function HelpTooltip(` — function, line 570
- `export function BlockBar(` — function, line 665
- `export function Meta(` — function, line 687
- `export function Dim(` — function, line 695
- `export function Faint(` — function, line 699
- `export function Divider(` — function, line 703
- `export function KeyBar(` — function, line 722
- `export type CardStatus = "running" | "done" | "error" | "attention" | "probe" | "neutral"` — type, line 767
- `export function Card(` — function, line 778

## Internal implementation anchors

- `const PILL_PALETTE: Record<PillColor,` — const, line 51
- `const palette = PILL_PALETTE[color] ?? PILL_PALETTE.purple` — const, line 70
- `const MODE_COLOR_RULES: Array<[RegExp, PillColor]> = [` — const, line 157
- `const m = (mode ?? "").toLowerCase()` — const, line 169
- `const MEASUREMENT_STATE_WORDS: Record<string, string> =` — const, line 183
- `const MEASUREMENT_STATE_COLORS: Record<string, string> =` — const, line 190
- `const opts: TermSelectOption[] = useMemo( ()` — const, line 233
- `const listboxId = useId()` — const, line 242
- `const wrapRef = useRef<HTMLDivElement | null>(null)` — const, line 244
- `const controlRef = useRef<HTMLDivElement | null>(null)` — const, line 245
- `const listRef = useRef<HTMLDivElement | null>(null)` — const, line 246
- `const selected = opts.find((o)` — const, line 248
- `const selectedIndex = opts.findIndex((o)` — const, line 249
- `const onDocMouseDown = (e: MouseEvent)` — const, line 254
- `const target = e.target as Node` — const, line 255
- `let clipped = false` — let, line 272
- `let node = controlRef.current?.parentElement ?? null` — let, line 273
- `const overflow = getComputedStyle(node).overflow + getComputedStyle(node).overflowY + getComputedStyle(node).overflowX` — const, line 275
- `const r = controlRef.current.getBoundingClientRect()` — const, line 283
- `const commit = (idx: number)` — const, line 291
- `const opt = opts[idx]` — const, line 292
- `const onKeyDown = (e: React.KeyboardEvent)` — const, line 299
- `const listStyle: CSSProperties =` — const, line 347
- `const list = open ? ( <div id=` — const, line 359
- `const isSel = o.value === value` — const, line 362
- `const isHi = i === highlight` — const, line 363
- `const tooltipId = useId()` — const, line 573
- `const anchorRef = useRef<HTMLButtonElement | null>(null)` — const, line 574
- `const updatePosition = ()` — const, line 581
- `const rect = anchorRef.current?.getBoundingClientRect()` — const, line 582
- `const viewportPadding = 8` — const, line 584
- `const width = Math.min(320, window.innerWidth - viewportPadding * 2)` — const, line 585
- `const left = Math.max(viewportPadding, Math.min(rect.right - width, window.innerWidth - width - viewportPadding))` — const, line 586
- `const roomBelow = window.innerHeight - rect.bottom` — const, line 587
- `const filled = Math.max(0, Math.min(width, Math.round((value / max) * width)))` — const, line 678
- `const CARD_STATUS_COLOR: Record<CardStatus, string | null> =` — const, line 769
- `const statusColor = CARD_STATUS_COLOR[status]` — const, line 791
- `const leftColor = selected ? COLOR.amber : statusColor` — const, line 792

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/AddToCollection|src/components/AddToCollection.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `TermSelect`; references `COLOR`, `FONT_MONO`, `Faint`, `TermSelect`
- [[Reference/Desktop/TypeScript/components/AdjudicationOverlay|src/components/AdjudicationOverlay.tsx]] — import-or-re-export: `COLOR`, `Card`, `Dim`, `Divider`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`; references `COLOR`, `Card`, `Dim`, `Divider`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/components/AsciiLoadingBar|src/components/AsciiLoadingBar.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`; references `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`; references `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`
- [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `TermSelect`; references `COLOR`, `FONT_MONO`, `Faint`, `TermSelect`
- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export: `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `PlainEnglishPanel`, `SectionHeader`; references `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `PlainEnglishPanel`, `SectionHeader`
- [[Reference/Desktop/TypeScript/components/ClaimSurface|src/components/ClaimSurface.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`; references `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/components/CommandOverlayFrame|src/components/CommandOverlayFrame.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`; references `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/ConceptAnimationSection|src/components/ConceptAnimationSection.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`; references `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`; references `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/ExemplarConfirmDialog|src/components/ExemplarConfirmDialog.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `Meta`, `Pill`, `SectionHeader`, `TermCheckbox`; references `COLOR`, `FONT_MONO`, `Faint`, `Meta`, `Pill`, `SectionHeader`, `TermCheckbox`
- [[Reference/Desktop/TypeScript/components/FacetInspector|src/components/FacetInspector.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `Meta`, `Pill`, `SectionHeader`, `TermSelect`; references `COLOR`, `FONT_MONO`, `Faint`, `Meta`, `Pill`, `SectionHeader`, `TermSelect`
- [[Reference/Desktop/TypeScript/components/GoalBanner|src/components/GoalBanner.tsx]] — import-or-re-export: `BlockBar`, `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `measurementStateLabel`; references `BlockBar`, `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `measurementStateLabel`
- [[Reference/Desktop/TypeScript/components/GoalReviewCard|src/components/GoalReviewCard.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`; references `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/GoalTrajectoryChart|src/components/GoalTrajectoryChart.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`; references `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/components/GoalWizard|src/components/GoalWizard.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`; references `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/IngestActivity|src/components/IngestActivity.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`, `TermCheckbox`; references `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`, `TermCheckbox`
- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `BlockBar`, `COLOR`, `Dim`, `DisclosureHeader`, `Divider`, `FONT_MONO`, `Faint`, `HelpTooltip`, `Meta`, `Pill`, `PillColor`, `PlainEnglishPanel`, `SectionHeader`, `modePillColor`; references `BlockBar`, `COLOR`, `Dim`, `DisclosureHeader`, `Divider`, `FONT_MONO`, `Faint`, `HelpTooltip`, `Meta`, `Pill`, `PillColor`, `PlainEnglishPanel`, `SectionHeader`, `modePillColor`
- [[Reference/Desktop/TypeScript/components/ItemPresentation|src/components/ItemPresentation.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`; references `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]] — import-or-re-export: `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`, `SectionHeader`, `measurementStateColor`, `measurementStateLabel`; references `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`, `measurementStateColor`, `measurementStateLabel`
- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`; references `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `Pill`; references `COLOR`, `FONT_MONO`, `Faint`, `Pill`
- [[Reference/Desktop/TypeScript/components/OutlineAndPlan|src/components/OutlineAndPlan.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`, `TermCheckbox`, `TermSelect`; references `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`, `TermCheckbox`, `TermSelect`
- [[Reference/Desktop/TypeScript/components/PageRangeSelector|src/components/PageRangeSelector.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`; references `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`; references `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/ProbeBlockResult|src/components/ProbeBlockResult.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`; references `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/ProvenancePanel|src/components/ProvenancePanel.tsx]] — import-or-re-export: `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`; references `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`, `SectionHeader`; references `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`, `SectionHeader`
- [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `TermCheckbox`, `TermSelect`; references `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `TermCheckbox`, `TermSelect`
- [[Reference/Desktop/TypeScript/components/RepairAffordances|src/components/RepairAffordances.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`; references `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/RepairTrace|src/components/RepairTrace.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`; references `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `TermCheckbox`; references `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `TermCheckbox`
- [[Reference/Desktop/TypeScript/components/StudyMapBriefWizard|src/components/StudyMapBriefWizard.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`; references `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/components/TrackRecordView|src/components/TrackRecordView.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`; references `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/components/WhyDiagnosisOverlay|src/components/WhyDiagnosisOverlay.tsx]] — import-or-re-export: `BlockBar`, `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`; references `BlockBar`, `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/components/WriteCardDialog|src/components/WriteCardDialog.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `TermSelect`; references `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `TermSelect`
- [[Reference/Desktop/TypeScript/components/goldenpath/GoldenPathSetup|src/components/goldenpath/GoldenPathSetup.tsx]] — import-or-re-export: `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`, `TermCheckbox`; references `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`, `TermCheckbox`
- [[Reference/Desktop/TypeScript/components/goldenpath/TriageDecisionAid|src/components/goldenpath/TriageDecisionAid.tsx]] — import-or-re-export: `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`; references `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/components/goldenpath/shared|src/components/goldenpath/shared.tsx]] — import-or-re-export: `BlockBar`, `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`; references `BlockBar`, `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`
- [[Reference/Desktop/TypeScript/components/graphedit/EditPopovers|src/components/graphedit/EditPopovers.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`; references `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/components/graphedit/GeometryPreview|src/components/graphedit/GeometryPreview.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`; references `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/components/graphedit/PendingStrip|src/components/graphedit/PendingStrip.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`; references `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/components/graphedit/SyllabusColumn|src/components/graphedit/SyllabusColumn.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`; references `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/components/highlight|src/components/highlight.tsx]] — import-or-re-export: `COLOR`; references `COLOR`
- [[Reference/Desktop/TypeScript/components/recipeedit/RecipeTreeEditor|src/components/recipeedit/RecipeTreeEditor.tsx]] — import-or-re-export: `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `HelpTooltip`, `Pill`, `SectionHeader`, `TermSelect`; references `BlockBar`, `COLOR`, `FONT_MONO`, `Faint`, `HelpTooltip`, `Pill`, `SectionHeader`, `TermSelect`
- [[Reference/Desktop/TypeScript/render/LiveMarkdownEditor|src/render/LiveMarkdownEditor.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`; references `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]] — import-or-re-export: `BlockBar`, `COLOR`, `FONT_MONO`, `Faint`, `KeyBar`; references `BlockBar`, `COLOR`, `FONT_MONO`, `Faint`, `KeyBar`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export: `KeyBar`; references `KeyBar`
- [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `KeyBar`; references `COLOR`, `FONT_MONO`, `Faint`, `KeyBar`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `modePillColor`; references `modePillColor`
- [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]] — import-or-re-export: `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`, `TermSelect`; references `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`, `TermSelect`
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export: `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `PillColor`, `SectionHeader`; references `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `PillColor`, `SectionHeader`
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Pill`, `PillColor`, `SectionHeader`, `TermSelect`; references `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Pill`, `PillColor`, `SectionHeader`, `TermSelect`
- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`; references `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/screens/KnowledgeStrataView|src/screens/KnowledgeStrataView.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`; references `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/screens/KnowledgeTerrainView|src/screens/KnowledgeTerrainView.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`; references `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/KnowledgeWellView|src/screens/KnowledgeWellView.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`; references `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — import-or-re-export: `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `PillColor`; references `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `PillColor`
- [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]] — import-or-re-export: `COLOR`, `Dim`, `Divider`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`, `SectionHeader`, `TermSelect`; references `COLOR`, `Dim`, `Divider`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`, `SectionHeader`, `TermSelect`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `BlockBar`, `COLOR`, `FONT_MONO`, `Faint`, `TermSelect`, `modePillColor`; references `BlockBar`, `COLOR`, `FONT_MONO`, `Faint`, `TermSelect`, `modePillColor`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — import-or-re-export: `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `PillColor`, `SectionHeader`; references `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `PillColor`, `SectionHeader`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`, `TermSelect`; references `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`, `TermSelect`
- [[Reference/Desktop/TypeScript/screens/RegistryReviewScreen|src/screens/RegistryReviewScreen.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`, `TermSelect`; references `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`, `TermSelect`
- [[Reference/Desktop/TypeScript/screens/RepairScreen|src/screens/RepairScreen.tsx]] — import-or-re-export: `COLOR`, `Divider`, `FONT_MONO`, `Faint`, `Pill`; references `COLOR`, `Divider`, `FONT_MONO`, `Faint`, `Pill`
- [[Reference/Desktop/TypeScript/screens/ReviewScreen|src/screens/ReviewScreen.tsx]] — import-or-re-export: `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `Pill`; references `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `Pill`
- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `TermCheckbox`, `TermSelect`; references `COLOR`, `FONT_MONO`, `TermCheckbox`, `TermSelect`
- [[Reference/Desktop/TypeScript/screens/SqliteBrowser|src/screens/SqliteBrowser.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`, `Faint`, `Pill`; references `COLOR`, `FONT_MONO`, `Faint`, `Pill`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `COLOR`, `FONT_MONO`; references `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`, `modePillColor`; references `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`, `modePillColor`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/glyphAtlas|src/screens/startBackdrops/glyphAtlas.ts]] — import-or-re-export: `FONT_MONO`; references `FONT_MONO`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`, `react-dom`

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

1. Modify [apps/learnloop-tauri/src/components/term.tsx](../../../../../../apps/learnloop-tauri/src/components/term.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
