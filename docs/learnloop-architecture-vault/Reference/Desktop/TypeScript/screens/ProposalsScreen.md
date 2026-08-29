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
source_commit: "388f3ce6b9e89c35532881182dabb2d08272d445"
source_commit_timestamp: "2026-07-24T09:24:46-04:00"
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
| Source lines | 874 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `388f3ce6b9e89c35532881182dabb2d08272d445` |
| Commit timestamp | `2026-07-24T09:24:46-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]]

## Public API

- `export function ProposalsScreen(` — function, line 562

## Internal implementation anchors

- `type PillColor } from "../components/term"` — type, line 21
- `function RoutePill(` — function, line 25
- `function DecisionPill(` — function, line 31
- `const ITEM_TYPE_COLOR: Record<string, PillColor> =` — const, line 38
- `function ItemTypePill(` — function, line 47
- `function SourceRefPill(` — function, line 51
- `const color: PillColor = source.kind === "note" ? "cyan" : source.kind === "canonical_source" ? "amber" : source.kind === "existing_entity" ? "green" : source.kind === "session" ? "purple" : "slate"` — const, line 52
- `const targetId = source.refId` — const, line 65
- `function ProposalsHero(` — function, line 90
- `const resolved = totals.accepted + totals.rejected` — const, line 105
- `const stats = [` — const, line 106
- `const Stat = (` — const, line 112
- `const sep = <span style=` — const, line 118
- `function BatchHeader(` — function, line 214
- `const run = batch.agentRun` — const, line 224
- `const lineage = [batch.id, batch.purpose, run.durationS != null ? `$` — const, line 225
- `function ProposalItemRow(` — function, line 260
- `function PayloadPreview(` — function, line 319
- `function ActionButton(` — function, line 346
- `function ProposalDetail(` — function, line 384
- `const run = batch.agentRun` — const, line 408
- `const isPending = item.decision === "pending"` — const, line 409
- `const isAccepted = item.decision === "accepted"` — const, line 410
- `const canAccept = item.validationStatus !== "invalid"` — const, line 411
- `const canUndo = item.decision === "rejected" && !item.applied` — const, line 412
- `const canRefreshValidation = isPending && item.validationStatus === "invalid"` — const, line 413
- `const applySnapshot = useCallback((next: ProposalsSnapshot)` — const, line 586
- `const all = next.batches.flatMap((batch)` — const, line 589
- `let cancelled = false` — let, line 596
- `const batch = snapshot.batches.find((candidate)` — const, line 612
- `const next = new Set(current)` — const, line 616
- `const first = batch.items.find((item)` — const, line 620
- `const items = snapshot?.batches.flatMap((batch)` — const, line 630
- `const inspectIds = uniqueIds( items.flatMap((item)` — const, line 631
- `const practiceItemIds = uniqueIds( items .filter((item)` — const, line 638
- `const visibleItems = useMemo(()` — const, line 648
- `const focusedItem = useMemo( ()` — const, line 653
- `const focusedBatch = useMemo( ()` — const, line 657
- `const runMutation = useCallback( async (action: ()` — const, line 662
- `const accept = useCallback(()` — const, line 678
- `const reject = useCallback(()` — const, line 683
- `const undo = useCallback(()` — const, line 688
- `const refreshValidation = useCallback(()` — const, line 693
- `const bulkAcceptAutoApply = useCallback(()` — const, line 699
- `const byBatch = snapshot.batches .map((batch)` — const, line 701
- `let latest = snapshot` — let, line 711
- `const onKey = (event: KeyboardEvent)` — const, line 720
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 721
- `const index = focusedItemId ? visibleItems.findIndex((item)` — const, line 723
- `const next = visibleItems[Math.min(visibleItems.length - 1, index + 1)]` — const, line 725
- `const prev = visibleItems[Math.max(0, index - 1)]` — const, line 729
- `function toggleBatch(id: string)` — function, line 750
- `const next = new Set(current)` — const, line 752
- `const codexRevision = useMemo(()` — const, line 759
- `const expanded = !collapsed.has(batch.id)` — const, line 794
- `function uniqueIds(values: Array<string | null | undefined>): string[]` — function, line 872

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `ProposalsScreen`; references `ProposalsScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ProposalBatchDto`, `ProposalItemDto`, `ProposalReviewRoute`, `ProposalSourceRefDto`, `ProposalsSnapshot`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `PillColor`, `SectionHeader`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EntityLink`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

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

1. Modify [apps/learnloop-tauri/src/screens/ProposalsScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/ProposalsScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
