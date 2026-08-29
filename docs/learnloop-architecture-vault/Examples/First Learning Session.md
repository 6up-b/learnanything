---
title: First Learning Session
aliases:
  - First Learning Cycle Example
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/cli/app.py
  - src/learnloop/tui/app.py
  - src/learnloop_sidecar/handlers/sessions.py
  - tests/test_session_attempt_attribution.py
  - tests/test_reentry_short_session.py
tags:
  - learnloop/example
  - learnloop/session
  - learnloop/learning-cycle
---

# First Learning Session

This example starts with an already applied study map. If the vault was just initialized and imported, finish [[Build a Study Map]] first; extraction alone creates no queue items.

## Prerequisites

- `$VAULT` points to an mvp-0.9 vault with active practice items
- `learnloop doctor --json` is clean
- a ready grader, or manual mode for ordinary non-diagnostic items

## 1. Preview three selections

```bash
uv run learnloop review \
  --limit 3 \
  --available-minutes 20 \
  --energy medium \
  --json --vault "$VAULT"
```

A representative queue entry includes:

```json
{
  "practice_item_id": "pi_…",
  "learning_object_id": "lo_…",
  "priority": 0.0,
  "selected_mode": "…",
  "reasons": ["…"],
  "components": {}
}
```

Field values depend on current time and learner state. The command is a snapshot, not a promise that the UI must keep the same order after constraints change.

## 2. Explain the first item

```bash
ITEM=<practice-item-id-from-review>

uv run learnloop show "$ITEM" --json --vault "$VAULT"
uv run learnloop why "$ITEM" --json --vault "$VAULT"
```

Check the prompt, allowed answer type, rubric, selection reasons, due pressure, and readiness effect. Algorithm interpretation stays in [[Scheduling and Selection]].

## 3. Start interactively

Terminal UI:

```bash
uv run learnloop today --vault "$VAULT"
```

Or open the same vault in the desktop app and use **Today**.

Enter:

- energy: medium;
- sleep quality: your actual value;
- available time: 20 minutes;
- optional session note.

Begin, answer before revealing help, and submit once. See [[Start a Learning Cycle#For each selected item]] for the evidence boundary.

## 4. Finish rather than closing abruptly

Use **End session**. The result should report attempts/items reviewed, follow-ups, cold checks separately, streak, and a learning diff. It should not call every completed item “mastered.”

## 5. Observe the session receipt

After the UI exits:

```bash
sqlite3 -readonly "$VAULT/state.sqlite" <<'SQL'
.headers on
.mode box
SELECT id, started_at, ended_at, energy, available_minutes
FROM sessions ORDER BY started_at DESC LIMIT 1;
SELECT id, practice_item_id, correctness, session_id, created_at
FROM practice_attempts ORDER BY created_at DESC LIMIT 5;
SQL
```

Expected:

- the latest session has `ended_at`;
- attempts submitted in the session reference its id;
- there is no active navigation checkpoint after a normal finish.

> [!info] Interrupted instead?
> Reopen the same UI and use [[Continue a Learning Cycle]]. Do not infer failure merely because the process closed; checkpoints and stable submission ids are designed for recovery.

## CLI-only alternative

For a single ordinary item with an explicit self-grade, use [[Manual Attempt and State Inspection]]. It records an attempt but is not a substitute for the warm-up/session/end lifecycle.

^first-session-observations

