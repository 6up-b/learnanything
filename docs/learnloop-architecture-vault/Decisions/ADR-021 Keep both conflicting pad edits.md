---
title: ADR-021 Keep both conflicting pad edits
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
decision_date: 2026-11-23
decision_status: accepted
last_reviewed: 2026-11-23
source_commit: 9038b096e7446d5f433f95d881de7e7c1bd0da15
source_commit_timestamp: "2026-11-23T19:57:34-05:00"
source_paths:
  - src/learnloop/pads/blocks.py
  - src/learnloop/desks/protocol.py
  - apps/learnloop-tauri/src/screens/desks/pads/model.ts
  - apps/learnloop-tauri/src/screens/desks/store.ts
  - tests/test_pad_stale_edits_stacks_and_passage_reads.py
tags:
  - learnloop/decision
  - learnloop/reader
  - learnloop/persistence
---

# ADR-021 Keep both conflicting pad edits

## Context

A pad editor can type against a version another client has edited, moved or removed. Reapplying the incoming words to the latest head can overwrite the other client's work or attach the stale edit to a block the learner did not see.

## Decision

The editor sends its expected head and a keep-both target with the edit. If the head is stale and the edit can be kept, the server keeps the current head and places the incoming words in a marked block beside it. The new block records the original block and both head identities. The receipt names the sibling, so the client can redirect edits typed on top of that wording. A stale edit without keep-both gets a conflict. Stale removes, moves and lifts do not get rebased onto a newer head.

## Consequences

- The learner can find both wordings after a reload and decide what to keep.
- A keep-both block has its own version history. Its words go through the ordinary emission rules.
- Keep-both is a successful op with a redirect. Debug it from the receipt and the pad heads. See [[Debug a workbench write]] and [[Reader workbench#Writing and saved state]].

## Enforcement

`tests/test_pad_stale_edits_stacks_and_passage_reads.py` covers the server's stale edits and destructive ops. Desktop `pads/model.test.ts` and `store.test.ts` cover optimistic application and redirecting the queued edits.

## What would reverse it

A successor merge protocol would need to preserve both wordings and the observed heads through retry, reconnect and concurrent removal or lift. It would also need to give the learner a way to inspect and recover both edits.
