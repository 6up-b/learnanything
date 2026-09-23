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
| Source lines | 873 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]]

## Public API

- `export function ProposalsScreen(` — function, line 564

## Internal implementation anchors

- `type PillColor } from "../components/term"` — type, line 23
- `function RoutePill(` — function, line 27
- `function DecisionPill(` — function, line 33
- `const ITEM_TYPE_COLOR: Record<string, PillColor> =` — const, line 40
- `function ItemTypePill(` — function, line 49
- `function SourceRefPill(` — function, line 53
- `const color: PillColor = source.kind === "note" ? "cyan" : source.kind === "canonical_source" ? "amber" : source.kind === "existing_entity" ? "green" : source.kind === "session" ? "purple" : "slate"` — const, line 54
- `const targetId = source.refId` — const, line 67
- `function ProposalsHero(` — function, line 92
- `const resolved = totals.accepted + totals.rejected` — const, line 107
- `const stats = [` — const, line 108
- `const Stat = (` — const, line 114
- `const sep = <span style=` — const, line 120
- `function BatchHeader(` — function, line 216
- `const run = batch.agentRun` — const, line 226
- `const lineage = [batch.id, batch.purpose, run.durationS != null ? `$` — const, line 227
- `function ProposalItemRow(` — function, line 262
- `function PayloadPreview(` — function, line 321
- `function ActionButton(` — function, line 348
- `function ProposalDetail(` — function, line 386
- `const run = batch.agentRun` — const, line 410
- `const isPending = item.decision === "pending"` — const, line 411
- `const isAccepted = item.decision === "accepted"` — const, line 412
- `const canAccept = item.validationStatus !== "invalid"` — const, line 413
- `const canUndo = item.decision === "rejected" && !item.applied` — const, line 414
- `const canRefreshValidation = isPending && item.validationStatus === "invalid"` — const, line 415
- `const proposalsQuery = useCachedQuery(["get_proposals"], ()` — const, line 587
- `const snapshot: ProposalsSnapshot | null = proposalsQuery.data ?? null` — const, line 588
- `const all = snapshot.batches.flatMap((batch)` — const, line 598
- `const batch = snapshot.batches.find((candidate)` — const, line 610
- `const next = new Set(current)` — const, line 614
- `const first = batch.items.find((item)` — const, line 618
- `const items = snapshot?.batches.flatMap((batch)` — const, line 628
- `const inspectIds = uniqueIds( items.flatMap((item)` — const, line 629
- `const practiceItemIds = uniqueIds( items .filter((item)` — const, line 636
- `const visibleItems = useMemo(()` — const, line 646
- `const focusedItem = useMemo( ()` — const, line 651
- `const focusedBatch = useMemo( ()` — const, line 655
- `const runMutation = useCallback( async (action: ()` — const, line 660
- `const accept = useCallback(()` — const, line 677
- `const reject = useCallback(()` — const, line 682
- `const undo = useCallback(()` — const, line 687
- `const refreshValidation = useCallback(()` — const, line 692
- `const bulkAcceptAutoApply = useCallback(()` — const, line 698
- `const byBatch = snapshot.batches .map((batch)` — const, line 700
- `let latest = snapshot` — let, line 710
- `const onKey = (event: KeyboardEvent)` — const, line 719
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 720
- `const index = focusedItemId ? visibleItems.findIndex((item)` — const, line 722
- `const next = visibleItems[Math.min(visibleItems.length - 1, index + 1)]` — const, line 724
- `const prev = visibleItems[Math.max(0, index - 1)]` — const, line 728
- `function toggleBatch(id: string)` — function, line 749
- `const next = new Set(current)` — const, line 751
- `const codexRevision = useMemo(()` — const, line 758
- `const expanded = !collapsed.has(batch.id)` — const, line 793
- `function uniqueIds(values: Array<string | null | undefined>): string[]` — function, line 871

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
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `PillColor`, `SectionHeader`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EntityLink`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/ProposalsScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/ProposalsScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
