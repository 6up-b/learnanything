---
title: "diagnosis_adjudications"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite diagnosis_adjudications"
  - "table diagnosis_adjudications"
schema_head: 156
table_name: "diagnosis_adjudications"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "126_diagnosis_adjudication.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/126_diagnosis_adjudication.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/tutor/durable_promotion.py"
  - "src/learnloop/diagnosis/diagnosis_adjudication.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `diagnosis_adjudications`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives diagnosis adjudication a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `diagnosis_receipt_id`, `adjudicated_repair_class_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/126_diagnosis_adjudication.sql`.
- **Schema touched by:** `126_diagnosis_adjudication.sql`, `132_surfaced_belief_corrections.sql`, `139_certification_cold_probes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `diagnosis_receipt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `verdict` | `TEXT` | yes | — | — | Stored value |
| `system_abstained` | `INTEGER` | yes | — | — | Stored value |
| `adjudicated_anchor_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `adjudicated_anchor_kind` | `TEXT` | no | — | — | Stored value |
| `adjudicated_repair_md` | `TEXT` | no | — | — | Stored value |
| `adjudicated_repair_class_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `queue_reason` | `TEXT` | yes | — | — | Stored value |
| `learner_report_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/causal_attribution_reports\|causal_attribution_reports.id]] | Stored value |
| `adjudicator_source` | `TEXT` | yes | — | — | Stored value |
| `rationale` | `TEXT` | no | — | — | Stored value |
| `decision_policy_version` | `TEXT` | no | — | — | Stored value |
| `repair_policy_version` | `TEXT` | no | — | — | Stored value |
| `grading_prompt_version` | `TEXT` | no | — | — | Stored value |
| `grader_model` | `TEXT` | no | — | — | Stored value |
| `receipt_schema_version` | `INTEGER` | no | — | — | Stored value |
| `system_snapshot_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `supersedes_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/diagnosis_adjudications\|diagnosis_adjudications.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `supersedes_id` → [[Reference/Database/Tables/diagnosis_adjudications|`diagnosis_adjudications.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `learner_report_id` → [[Reference/Database/Tables/causal_attribution_reports|`causal_attribution_reports.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `uq_diagnosis_adjudications_supersedes` on `supersedes_id` (unique).
- `uq_diagnosis_adjudications_root` on `attempt_id` (unique).
- `idx_diagnosis_adjudications_queue_reason` on `queue_reason`, `created_at`.
- `idx_diagnosis_adjudications_versions` on `grading_prompt_version`, `grader_model`, `created_at`.
- `idx_diagnosis_adjudications_verdict` on `verdict`, `created_at`.
- `idx_diagnosis_adjudications_receipt` on `diagnosis_receipt_id`.
- `idx_diagnosis_adjudications_attempt` on `attempt_id`, `created_at`, `id`.
- `sqlite_autoindex_diagnosis_adjudications_1` on `id` (unique).

Database triggers:

- `diagnosis_adjudications_no_delete` — schema-enforced lifecycle or immutability constraint.
- `diagnosis_adjudications_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.active_diagnosis_adjudication()`
- `Repository.adjudicated_attempt_ids()`
- `Repository.diagnosis_adjudication()`
- `Repository.diagnosis_adjudications_for_attempt()`
- `Repository.insert_diagnosis_adjudication()`
- `Repository.list_diagnosis_adjudications()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/diagnosis_adjudication.py`
- `src/learnloop/tutor/durable_promotion.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_certification_cold_probe.py`
- `tests/test_diagnosis_adjudication.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE diagnosis_adjudications (
  id TEXT PRIMARY KEY,

  -- (1/4) The attempt.  No FK: goal-series rewind can remove attempt
  -- projections and the adjudication record must survive as immutable audit,
  -- exactly as `causal_hypotheses.attempt_id` does.
  attempt_id TEXT NOT NULL,

  -- The exact system output being judged.  A verdict that cannot say WHICH
  -- diagnosis it judged is not an eval record once the receipt changes, and
  -- `attempt_debug_payloads` is replay-rebuildable.
  diagnosis_receipt_id TEXT NOT NULL,

  -- (4/4) The verdict on what the system chose.
  --
  -- A4 names five values.  `should_not_have_abstained` is a SIXTH, added
  -- deliberately: the five have no value for a FALSE abstention, so
  -- abstention precision = correctly_abstained / (all abstentions) would be
  -- 1.0 by construction and the metric §12 asks for could never fail.
  -- Standing constraint 2 / §11 ("no new enum without an abstention arm and a
  -- two-tailed fill-rate watch") requires both tails to be representable.
  -- The enum is CHECK-constrained on an append-only table, so it calcifies.
  verdict TEXT NOT NULL CHECK (verdict IN (
    'correct',
    'wrong_anchor',
    'wrong_repair',
    'should_have_abstained',
    'correctly_abstained',
    'should_not_have_abstained'
  )),

  -- What the system DID, snapshotted at adjudication time.  This is what makes
  -- the abstention confusion matrix computable in SQL without re-deriving a
  -- receipt that replay may have rebuilt:
  --   TP = system_abstained=1 AND verdict='correctly_abstained'
  --   FP = system_abstained=1 AND verdict='should_not_have_abstained'
  --   FN = system_abstained=0 AND verdict='should_have_abstained'
  --   TN = system_abstained=0 AND verdict IN (correct, wrong_anchor, wrong_repair)
  system_abstained INTEGER NOT NULL CHECK (system_abstained IN (0, 1)),

  -- (2/4) The adjudicated first-divergence anchor, in the `FirstDivergence`
  -- shape (codex/schemas.py) so it compares directly against the receipt's
  -- `divergence_anchors.first_observable_divergence`.
  adjudicated_anchor_json TEXT,
  adjudicated_anchor_kind TEXT CHECK (
    adjudicated_anchor_kind IS NULL
    OR adjudicated_anchor_kind IN (
      'span', 'between_spans', 'missing_required_step', 'whole_answer', 'none'
    )
  ),

  -- (3/4) The adjudicated minimal repair.  NL first (structure-late, §2): the
  -- prose is always admissible; the repair-class id is recorded only when the
  -- adjudicated repair matches one the episode actually offered, which is what
  -- `repair_class_match_rate` (§3 B5) scores against.
  adjudicated_repair_md TEXT,
  adjudicated_repair_class_id TEXT,

  -- How this attempt reached the adjudicator.  Required for B4: an eval set
  -- drawn only from learner contests is ~100% negative verdicts and its
  -- agreement with the planted set means nothing.
  queue_reason TEXT NOT NULL CHECK (queue_reason IN (
    'learner_contest',
    'system_abstention',
    'anchor_disagreement',
    'incomplete_repair_mapping',
    'sampled',
    'manual'
  )),

  -- Provenance only.  The contest's typed reason is a PRIOR the CLI displays;
  -- it never sets the verdict (that would launder bounded-trust learner
  -- evidence into the `adjudicated` support authority, which §2 forbids).
  learner_report_id TEXT REFERENCES causal_attribution_reports(id),

  -- Full-authority sources only.  `learner_clarification` is deliberately
  -- absent: grade adjudication gives it a bounded trust weight < 1, and a
  -- bounded-trust label is not usable as eval ground truth.
  adjudicator_source TEXT NOT NULL CHECK (adjudicator_source IN (
    'human_owner', 'independent_expert', 'deterministic_verifier'
  )),
  rationale TEXT,

  -- Version pins.  Sliced by §3 B5 ("reported per prompt version and per
  -- model"); all four of these change within a single Phase A/C week, and a
  -- verdict that cannot name the version it judged is not reusable afterwards.
  decision_policy_version TEXT,
  repair_policy_version TEXT,
  grading_prompt_version TEXT,
  grader_model TEXT,
  receipt_schema_version INTEGER,

  -- The rest of the manifest plus the system's own anchor/repair choice, so a
  -- record scores without re-reading a mutable debug payload: grader provider
  -- and revision, grading agent run, mechanism taxonomy version + hash,
  -- support authority, contamination class, selection basis, resolution
  -- counts, plausible hypothesis ids, and the system anchor/repair.
  system_snapshot_json TEXT NOT NULL,

  supersedes_id TEXT REFERENCES diagnosis_adjudications(id),
  created_at TEXT NOT NULL,

  -- The verdict vocabulary partitions on what the system did.  Rejecting the
  -- crossed cells is what stops "the system abstained AND its anchor was
  -- wrong" from being recorded as `wrong_anchor` and vanishing from the
  -- abstention denominator.
  CHECK (
    (system_abstained = 1
     AND verdict IN ('correctly_abstained', 'should_not_have_abstained'))
    OR
    (system_abstained = 0
     AND verdict IN ('correct', 'wrong_anchor', 'wrong_repair',
                     'should_have_abstained'))
  ),

  -- A record that scores anchor accuracy must carry an anchor.
  -- `should_have_abstained` and `correctly_abstained` are exempt: the whole
  -- claim there is that the vocabulary cannot name the cause.
  CHECK (
    verdict NOT IN ('correct', 'wrong_anchor', 'wrong_repair',
                    'should_not_have_abstained')
    OR adjudicated_anchor_json IS NOT NULL
  ),

  -- `wrong_repair` asserts the system's repair was wrong; without the repair
  -- that should have been chosen the record scores nothing.
  CHECK (
    verdict != 'wrong_repair'
    OR adjudicated_repair_md IS NOT NULL
    OR adjudicated_repair_class_id IS NOT NULL
  )
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
