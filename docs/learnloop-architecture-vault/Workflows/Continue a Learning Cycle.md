---
title: Continue a Learning Cycle
aliases:
  - Resume a Study Session
  - Session Checkpoint Recovery
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-09-23
source_commit: 0622ea164f76ad7e1d62a00afda51473dbcd992e
source_commit_timestamp: "2026-09-23T13:06:55-04:00"
source_paths:
  - src/learnloop_sidecar/handlers/sessions.py
  - src/learnloop_sidecar/handlers/practice.py
  - src/learnloop_sidecar/server.py
  - src/learnloop/attempts/post_attempt.py
  - src/learnloop/attempts/completion_lock.py
  - src/learnloop/db/stores/completion.py
  - src/learnloop/db/stores/collection.py
  - apps/learnloop-tauri/src-tauri/src/errors.rs
  - apps/learnloop-tauri/src-tauri/src/sidecar.rs
  - tests/test_attempt_completion.py
  - src/learnloop/learner/session_learning_diff.py
  - src/learnloop/db/repositories.py
  - tests/test_session_attempt_attribution.py
  - tests/test_sidecar_contract.py
  - tests/test_reentry_short_session.py
tags:
  - learnloop/workflow
  - learnloop/session
  - learnloop/recovery
---

# Continue a Learning Cycle

Use this workflow after closing the desktop, losing a response, or returning later. A session checkpoint is navigation state, not the learning record; committed attempts and grading evidence remain authoritative in [[State and Persistence]].

## Normal continuation

1. Reopen the same vault.
2. Open **Today**.
3. If an open session exists, choose the offered resume action.
4. Confirm the restored practice item and draft answer before submitting.
5. Finish normally so the learning diff and checkpoint cleanup run.

The checkpoint can preserve:

- current practice item id;
- current answer or a feature-owned conversation envelope;
- focus-block state;
- pending grading proposal;
- readiness state;
- its last update timestamp.

> [!important] Resume invariant
> Restoring a checkpoint must not create an attempt. Only a committed submission writes `practice_attempts` and evidence.

## After a lost submission response

Do not change the answer and immediately submit a second time.

1. Let the UI retry with the same stable submission id (`recover_practice_submission`, or a repeated `submit_attempt` / `submit_dont_know`).
2. The backend resolves the submission id to exactly one of four outcomes:

| What the database holds for the submission id | Outcome |
|---|---|
| A row in `attempt_submission_receipts` | The stored response is returned unchanged (`status: "recovered"` from recovery). |
| An attempt with a pending `attempt_completion_work` row | The saved result is completed: no regrade, only misconception normalization may call the grading provider, and follow-ups are inserted only while the attempt's session is still open. The response and its receipt are then written. |
| An attempt with no completion work, or pending work that does not record its probe episode | Fails closed with the non-retryable `submission_committed` error, carrying the attempt id; the attempt is never graded or applied again. |
| No attempt | Recovery reports `status: "pending"`, and the original request can be applied once. |

The unique index on `practice_attempts.submission_id` protects the same invariant at the database boundary. When two requests with one submission id race, the loser's insert fails on that index and it answers with the winner's committed attempt. ^submission-idempotency

A pending completion row stores the probe episode the attempt was applied under (`route_json = {"applied_probe_episode_id": …}`), written in the attempt's own transaction. A resumed completion routes the learner, and decides whether feedback stays deferred, from that episode rather than from whichever episode is open when recovery runs. Completion also runs under a per-database advisory file lock (`attempt-completion.lock` beside `state.sqlite`), so a sidecar and a TUI resuming the same attempt cannot both normalize it; a process that waits more than 120 s for the lock gets the retryable `completion_busy` error.

## Scheduler offer binding

The first draft save or submission binds its submission id to the scheduler candidate it was served under (`submission_intents`). Reopening the same item from a refreshed Today queue sends the new queue's candidate with the same submission id; that candidate is accepted only when it is a returned, unconsumed offer of the same item in the same session, and the attempt still links to the original offer. A submission id reused for another item or session, or a candidate that was never offered for it, is rejected with `validation_error`. See [[Collection and Dataset Contract]] for how offers become collection records.

## Transient errors during continuation

| Code | Raised by | Retryable | Meaning |
|---|---|---|---|
| `database_busy` | sidecar, any RPC | yes | SQLite reported `database is locked`/`busy`; the transaction was rolled back and a retry resumes by submission id. |
| `completion_busy` | sidecar, any RPC | yes | Another process holds the attempt-completion lock. |
| `grading_provider_reset` | desktop shell, after a sidecar restart | yes | The replacement sidecar refused the learner's grading-provider choice; the choice was dropped and grading uses the vault's configured provider. |
| `vault_changed` | desktop shell | no | The command was issued for the previously selected vault and was not run against the current one. |
| `submission_committed` | sidecar | no | See the outcome table above. |

## If the UI offers no resumable session

Run read-only checks:

```bash
VAULT="$HOME/LearnLoop/linear-algebra"

uv run learnloop doctor --json --vault "$VAULT"
sqlite3 -readonly "$VAULT/state.sqlite" \
  'SELECT id, started_at, ended_at FROM sessions ORDER BY started_at DESC LIMIT 5;'
sqlite3 -readonly "$VAULT/state.sqlite" \
  'SELECT session_id, current_practice_item_id, updated_at FROM session_checkpoints;'
```

- An `ended_at` value means the session was closed; start a new session.
- An open session with no checkpoint can be continued only as a fresh selection surface.
- A checkpoint for the open session should be restored by the desktop; collect sidecar logs before attempting state repair.

> [!warning] Never repair a checkpoint with SQL
> Direct updates can detach drafts, grading proposals, and session attribution. Use [[Doctor Migrations and Recovery]] if structural health fails, or start a new session if the prior one is already ended.

## Starting over intentionally

Beginning a new session closes any previous open session and creates a new context with new energy/time constraints. It does not erase attempts attributed to the older session.

Use this when:

- the available time or energy materially changed;
- the previous session is already complete;
- the draft was intentionally abandoned.

## End-of-session confirmation

After ending in the UI, verify that the latest session has `ended_at` and no active checkpoint if diagnosing lifecycle behavior:

```bash
sqlite3 -readonly "$VAULT/state.sqlite" \
  'SELECT id, started_at, ended_at, energy, available_minutes FROM sessions ORDER BY started_at DESC LIMIT 1;'
```

The durable learning result should be inspected by attempt id, not inferred from the absence of a checkpoint. Continue at [[Inspect Persistent State#Trace one attempt]].

## Related notes

- [[Start a Learning Cycle]]
- [[State and Persistence]]
- [[Doctor Migrations and Recovery]]
- [[Tutor and Teach-Back Workflow#Resume and outage behavior]]
- [[Process Model Output#Post-attempt completion]]
- [[Collection and Dataset Contract]]
