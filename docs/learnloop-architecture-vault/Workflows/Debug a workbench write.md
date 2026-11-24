---
title: Debug a workbench write
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
last_reviewed: 2026-11-23
source_commit: 9038b096e7446d5f433f95d881de7e7c1bd0da15
source_commit_timestamp: "2026-11-23T19:57:34-05:00"
source_paths:
  - src/learnloop/desks/protocol.py
  - src/learnloop/db/stores/workspace_batches.py
  - src/learnloop_sidecar/handlers/pads.py
  - src/learnloop_sidecar/handlers/ink.py
  - src/learnloop_sidecar/context.py
  - src/learnloop/pads/emission.py
  - apps/learnloop-tauri/src/screens/desks/store.ts
  - apps/learnloop-tauri/src/screens/desks/outbox.ts
tags:
  - learnloop/workflow
  - learnloop/reader
---

# Debug a workbench write

## Find the receipt

For “my edit vanished”, start with the vault, client id, batch sequence and pad or desk id. Use `desk.state` for the server's sequence head and open layout. Inspect both [[Reference/Database/Tables/desk_op_receipts|desk_op_receipts]] and [[Reference/Database/Tables/pad_op_receipts|pad_op_receipts]] by client id and sequence. `desk.apply` uses the desk receipt table. `pad.apply`, `ink.save` and `ink.erase` use the pad receipt table. The next number is one past the highest sequence across both tables.

Read the op at its index in the receipt's result. A receipt proves the batch committed, including any per-op refusals. An identical retry gives the stored reply. `seq_gap` means the server expected an earlier batch. `seq_reused` means that sequence already belongs to a different request. Neither consumes a new number. See [[Reference/Modules/learnloop/desks/protocol|Batch protocol]].

## Follow the head or the conflict

- For a desk conflict, compare `current` with the head in `desks` and the window's owner in `desk_windows`. A window may have moved after the op was queued. A transfer checks both desks.
- For a pad conflict, read `pad.get` and follow the head in `pad_block_versions` or the link's latest event in `pad_block_anchors`. A successful edit with `keptBoth` points to a new sibling block. The original head still stands. A stale remove, move or lift can write nothing and stays dropped on rebase. See [[ADR-021 Keep both conflicting pad edits]].
- An op with `refused` has its own code. Other ops in its batch can still have succeeded. For ink, compare `ink.list` with `ink_strokes` and `ink_transcriptions`. These distinguish the standing strokes and their reading from the block wording.

## Check the outbox and both reconciles

If there is no receipt, inspect the desktop's vault-and-transport store and its `MemoryOutboxStore`. A transport failure keeps a batch available for retry while the app stays open. There is no disk outbox for unsent writes. Request validation errors and stale sidecar schema errors drop the rejected batch and move later ones up. A sequence gap or reuse clears the pending queue and reloads from the server head.

For an op conflict or keep-both reply, the desktop waits for any in-flight write, rereads `desk.state` and the affected pads with `pad.get`, then rebases queued intent, including edits made during those reads. It restamps applicable ops, redirects dependent edits into a keep-both sibling and reports dropped intent. Ink refresh merges the server's saved strokes with local strokes still waiting for acknowledgement. See [[Reference/Desktop/TypeScript/screens/desks/store|Desk store]] and [[Reference/Desktop/TypeScript/screens/desks/outbox|Write outbox]].

If the pad words are saved but their learner-text reading is missing, check the `pad_text` version gate, the learner-text gaps switch and the eligible kind and provenance. Follow the wording version id through `learner_text_gap_jobs`, `learner_text_gaps` and `learner_text_gap_reversals`. Pad emission runs after the write commits. The sidecar reconciles emission on vault open and after the gap worker drains. It can queue committed words and set aside a reading that finished after replacement. A missing gap does not establish a missing pad write. For an explicit submission use its own `pad_block_submissions` row and the recorded attempt or teach-back id. See [[Reader workbench#When pad words leave the pad]].
