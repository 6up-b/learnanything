---
title: "Desktop module · src/screens/ProposalsScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.ProposalsScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/ProposalsScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/ProposalsScreen.tsx"
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

# `src/screens/ProposalsScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ProposalsScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/ProposalsScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/ProposalsScreen.tsx) |
| Source lines | 946 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]]

## Public API

- `export interface ProposalRepeat` — interface, line 276
- `export function repeatedPendingProposals(batches: ProposalBatchDto[]): Map<string, ProposalRepeat>` — function, line 285
- `export function ProposalsScreen(` — function, line 619

## Internal implementation anchors

- `type PillColor } from "../components/term"` — type, line 26
- `function RoutePill(` — function, line 30
- `function DecisionPill(` — function, line 36
- `const ITEM_TYPE_COLOR: Record<string, PillColor> =` — const, line 43
- `function ItemTypePill(` — function, line 52
- `function SourceRefPill(` — function, line 56
- `const color: PillColor = source.kind === "note" ? "cyan" : source.kind === "canonical_source" ? "amber" : source.kind === "existing_entity" ? "green" : source.kind === "session" ? "purple" : "slate"` — const, line 57
- `const targetId = source.refId` — const, line 70
- `function ProposalsHero(` — function, line 95
- `const resolved = totals.accepted + totals.rejected` — const, line 110
- `const stats = [` — const, line 111
- `const Stat = (` — const, line 117
- `const sep = <span style=` — const, line 123
- `function BatchHeader(` — function, line 219
- `const run = batch.agentRun` — const, line 229
- `const lineage = [batch.id, batch.purpose, run.durationS != null ? `$` — const, line 230
- `const groups = new Map<string, string[]>()` — const, line 286
- `const key = `$` — const, line 290
- `const repeats = new Map<string, ProposalRepeat>()` — const, line 294
- `function RepeatPill(` — function, line 302
- `function ProposalItemRow(` — function, line 311
- `function PayloadPreview(` — function, line 376
- `function ActionButton(` — function, line 403
- `function ProposalDetail(` — function, line 441
- `const run = batch.agentRun` — const, line 465
- `const isPending = item.decision === "pending"` — const, line 466
- `const isAccepted = item.decision === "accepted"` — const, line 467
- `const canAccept = item.validationStatus !== "invalid"` — const, line 468
- `const canUndo = item.decision === "rejected" && !item.applied` — const, line 469
- `const canRefreshValidation = isPending && item.validationStatus === "invalid"` — const, line 470
- `const proposalsQuery = useCachedQuery(["get_proposals"], ()` — const, line 642
- `const snapshot: ProposalsSnapshot | null = proposalsQuery.data ?? null` — const, line 643
- `const all = snapshot.batches.flatMap((batch)` — const, line 653
- `const batch = snapshot.batches.find((candidate)` — const, line 665
- `const next = new Set(current)` — const, line 669
- `const first = batch.items.find((item)` — const, line 673
- `const items = snapshot?.batches.flatMap((batch)` — const, line 683
- `const inspectIds = uniqueIds( items.flatMap((item)` — const, line 684
- `const practiceItemIds = uniqueIds( items .filter((item)` — const, line 691
- `const visibleItems = useMemo(()` — const, line 701
- `const repeats = useMemo( ()` — const, line 707
- `const focusedItem = useMemo( ()` — const, line 712
- `const focusedBatch = useMemo( ()` — const, line 716
- `const runMutation = useCallback( async (action: ()` — const, line 721
- `const accept = useCallback(()` — const, line 738
- `const reject = useCallback(()` — const, line 743
- `const undo = useCallback(()` — const, line 748
- `const refreshValidation = useCallback(()` — const, line 753
- `const bulkAcceptAutoApply = useCallback(()` — const, line 759
- `const byBatch = snapshot.batches .map((batch)` — const, line 761
- `let latest = snapshot` — let, line 771
- `const onKey = (event: KeyboardEvent)` — const, line 780
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 783
- `const index = focusedItemId ? visibleItems.findIndex((item)` — const, line 785
- `const next = visibleItems[Math.min(visibleItems.length - 1, index + 1)]` — const, line 787
- `const prev = visibleItems[Math.max(0, index - 1)]` — const, line 791
- `function toggleBatch(id: string)` — function, line 812
- `const next = new Set(current)` — const, line 814
- `const codexRevision = useMemo(()` — const, line 821
- `const expanded = !collapsed.has(batch.id)` — const, line 865
- `function uniqueIds(values: Array<string | null | undefined>): string[]` — function, line 944

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: dynamic import; no named call claim

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ProposalBatchDto`, `ProposalItemDto`, `ProposalReviewRoute`, `ProposalSourceRefDto`, `ProposalsSnapshot`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/shell|src/app/shell.ts]] — import-or-re-export; imports `simpleShell`
- [[Reference/Desktop/TypeScript/components/RewordConfirms|src/components/RewordConfirms.tsx]] — import-or-re-export; imports `RewordConfirmList`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `PillColor`, `SectionHeader`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EntityLink`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/ProposalsScreen.repeats.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/ProposalsScreen.repeats.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/ProposalsScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/ProposalsScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
