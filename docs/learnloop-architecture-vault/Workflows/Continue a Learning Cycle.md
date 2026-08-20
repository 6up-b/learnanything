---
title: Continue a Learning Cycle
aliases:
  - Resume a Study Session
  - Session Checkpoint Recovery
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop_sidecar/handlers/sessions.py
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

1. Let the UI retry with the same stable submission id.
2. The backend looks up a committed attempt by that id.
3. If found, it returns the original result; it does not append a duplicate.
4. If no receipt exists, the original request can be applied once.

The unique index on `practice_attempts.submission_id` protects the same invariant at the database boundary. ^submission-idempotency

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
