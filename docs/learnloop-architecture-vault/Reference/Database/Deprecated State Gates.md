---
title: "Deprecated State Gates"
status: "needs-owner-input"
doc_version: "1.0"
architecture_version: "post-refactor"
schema_head: 156
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-17"
aliases:
  - "Deprecated table telemetry"
  - "Contested SQLite tables"
source_paths:
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/db/table_roles.py"
  - "tests/test_doctor.py"
  - "tests/test_source_layer.py"
  - "REFACTOR_PROPOSAL.md"
tags:
  - "learnloop/database/compatibility"
  - "learnloop/status/needs-owner-input"
  - "learnloop/status/dormant-owner-gated"
---

# Deprecated State Gates

Three tables have no established production caller after the refactor, but they remain schema- and code-compatible until production-vault telemetry and an explicit owner decision justify a later step. ^deprecated-state-gate

| Table | Intended function | Current evidence | Current action |
|---|---|---|---|
| [[Reference/Database/Tables/source_exam_profiles\|source_exam_profiles]] | Materialized deterministic exam-profile cache | CRUD retained; no upstream caller found | Preserve and report row count |
| [[Reference/Database/Tables/source_locator_schemes\|source_locator_schemes]] | Cached locator-scheme detection | CRUD retained; no upstream caller found | Preserve and report row count |
| [[Reference/Database/Tables/learner_theta\|learner_theta]] | Legacy learner IRT theta state | Superseded as canonical projection, but old-vault meaning may remain | Preserve and report row count |

> [!warning] Zero is a stop gate, not deletion permission
> All ten repository fixture databases had zero rows where these tables existed. No owner production vault was available. The refactor therefore performed no schema drop, archive rename, or code detachment.

## Doctor behavior

Plain doctor counts each present table read-only. A nonzero count emits `sqlite:deprecated_table_not_empty` with `action: stop_and_escalate`. A table absent because an old fixture predates its migration is reported as unavailable, not silently interpreted as empty.

```bash
learnloop doctor --vault /absolute/path/to/real-vault --json
```

Look for the deprecated-table counts/issues in the JSON report. Run this against every real vault before proposing any detachment.

## Retirement sequence

1. Collect read-only counts from owner production vaults.
2. If any count is nonzero, stop and inspect semantics with the owner.
3. Only after clean evidence, separately review code detachment.
4. Observe releases and real vaults after detachment.
5. Treat any archive rename or schema mutation as a later, explicit owner-gated decision.

The sequence deliberately separates “no current caller,” “no rows in known vaults,” and “safe to destroy data.” They are not equivalent claims.

## Tests

- `tests/test_doctor.py` pins zero/nonzero telemetry and stop-and-escalate output.
- `tests/test_source_layer.py` pins that contested exam-profile CRUD remains available until owner telemetry permits a decision.
- `tests/test_table_roles.py` pins the compatibility role.
