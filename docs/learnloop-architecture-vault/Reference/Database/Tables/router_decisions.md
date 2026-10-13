---
title: "router_decisions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "1e3b56d766f5b133aedca5b64ae06802e8f41a94"
source_commit_timestamp: "2026-10-13T16:01:27-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite router_decisions"
  - "table router_decisions"
schema_head: 197
table_name: "router_decisions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "181_router_decisions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/181_router_decisions.sql"
  - "src/learnloop/cli/router.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/daily_plan/engine.py"
  - "src/learnloop/daily_plan/types.py"
  - "src/learnloop/db/stores/router.py"
  - "src/learnloop/evsi_calibration/live_report.py"
  - "src/learnloop/probe_tie_upgrade.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `router_decisions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives router decision a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It supplies replay-stable input rather than a disposable cache. Rows bind `session_id`, `parent_decision_id`, `scheduler_slate_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Router R1 (spec_action_router_v1 §9, §11; mvp-0.15): decision logging on today's paths (built as migration 176 at mvp-0.12; renumbered 181 and relabelled mvp-0.15 when it merged after main's 176-180, none of which touches these tables). One append-only row per Today offer, staged P2 decision, learner pick and daily-plan block decision (plan_block, through DL1's register_plan_decision_logger hook; owner decision 2026-10-12), with the full candidate set, the chosen candidate and its true propensity (or an explicit 'deterministic'). A list the learner picks from with no system-served head is logged with propensity_kind 'not_served'. The outcome table is a derived cache with one replayer; nothing here is evidence, mastery or certification.

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/181_router_decisions.sql`.
- **Schema touched by:** `181_router_decisions.sql`, `193_retrieval_interventions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `receipt_key` | `TEXT` | yes | — | — | Stored value |
| `decision_kind` | `TEXT` | yes | — | — | Stored value |
| `surface` | `TEXT` | yes | — | — | Stored value |
| `mode` | `TEXT` | yes | — | — | Stored value |
| `policy` | `TEXT` | yes | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `log_version` | `TEXT` | yes | — | — | Stored value |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `parent_decision_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/router_decisions\|router_decisions.id]] | Stored value |
| `scheduler_slate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `controller_decision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `snapshot_hash` | `TEXT` | yes | — | — | Stored value |
| `design` | `TEXT` | no | — | — | Stored value |
| `seed` | `TEXT` | no | — | — | Stored value |
| `candidates_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `exclusions_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `candidate_count` | `INTEGER` | yes | — | — | Stored value |
| `chosen_ref` | `TEXT` | no | — | — | Stored value |
| `chosen_practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `chosen_learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `chosen_scheduler_candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `propensity` | `REAL` | no | — | — | Stored value |
| `propensity_kind` | `TEXT` | yes | — | — | Stored value |
| `learner_pick` | `INTEGER` | yes | `0` | — | Stored value |
| `fallback` | `TEXT` | no | — | — | Stored value |
| `mixture_weights_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `model_distributions_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `sensor_answers_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `question_set_version` | `TEXT` | no | — | — | Stored value |
| `model_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `card_hash` | `TEXT` | no | — | — | Stored value |
| `similar_decision_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `latency_ms` | `INTEGER` | no | — | — | Stored value |
| `cost_usd` | `REAL` | no | — | — | Stored value |
| `detail_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `parent_decision_id` → [[Reference/Database/Tables/router_decisions|`router_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `router_decisions_parent` on `parent_decision_id`.
- `router_decisions_candidate` on `chosen_scheduler_candidate_id`.
- `router_decisions_slate` on `scheduler_slate_id`.
- `router_decisions_session` on `session_id`, `created_at`, `id`.
- `sqlite_autoindex_router_decisions_2` on `receipt_key` (unique).
- `sqlite_autoindex_router_decisions_1` on `id` (unique).

Database triggers:

- `router_decisions_no_delete` — schema-enforced lifecycle or immutability constraint.
- `router_decisions_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/cli/router.py`
- `src/learnloop/db/stores/router.py`
- `src/learnloop/evsi_calibration/live_report.py`
- `src/learnloop/router/outcomes.py`
- `src/learnloop/substrate/rebuild_orchestrator.py`

### Direct SQL writers

- `src/learnloop/db/stores/router.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_daily_plan_owner_decisions.py`
- `tests/test_daily_plan_replay.py`
- `tests/test_daily_plan_review_regressions.py`
- `tests/test_evsi_router_composition.py`
- `tests/test_learner_pick_proposal.py`
- `tests/test_mvp015_upgrade.py`
- `tests/test_router_offer_log.py`
- `tests/test_router_outcomes.py`
- `tests/test_router_probe_ties.py`
- `tests/test_router_r1_composition.py`
- `tests/test_router_staged_p2.py`
- `tests/test_voi_forecasts.py`

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
CREATE TABLE router_decisions (
  id TEXT PRIMARY KEY,
  -- Idempotency: today_offer:<slate>, staged_p2:<controller decision>,
  -- learner_pick:<scheduler candidate>, plan_block:<attention block>.
  receipt_key TEXT NOT NULL UNIQUE,
  decision_kind TEXT NOT NULL CHECK (
    decision_kind IN ('today_offer', 'staged_p2', 'learner_pick', 'plan_block')
  ),
  -- Where the decision was served: desktop_queue | full_list | skip_requeue |
  -- p2_bridge | daily_plan | the bind's entry surface for a learner pick.
  surface TEXT NOT NULL,
  -- Who composed the choice: legacy_queue | staged | daily_plan (R2 adds
  -- mixture).
  mode TEXT NOT NULL,
  -- The policy that chose: composed_offer_v2 | staged_policy_v1 | learner |
  -- the plan chooser (lane_quota_v1).
  policy TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  log_version TEXT NOT NULL,
  session_id TEXT,
  -- A learner pick names the offer it overrode.
  parent_decision_id TEXT REFERENCES router_decisions(id),
  scheduler_slate_id TEXT,
  controller_decision_id TEXT,
  -- Content hash of the decision's inputs (candidates, planner values,
  -- exclusions, the randomization design, the session context and the
  -- configuration that shaped the choice; never the build time).
  snapshot_hash TEXT NOT NULL,
  -- The assignment mechanism when the chosen candidate was drawn
  -- (scheduler_seeded_exploration | epsilon_tiebreak; registered in
  -- db.stores.router.ROUTER_DESIGNS); NULL when the choice was deterministic.
  design TEXT,
  seed TEXT,
  candidates_json TEXT NOT NULL,
  exclusions_json TEXT NOT NULL,
  candidate_count INTEGER NOT NULL CHECK (candidate_count >= 0),
  chosen_ref TEXT,
  chosen_practice_item_id TEXT,
  chosen_learning_object_id TEXT,
  chosen_scheduler_candidate_id TEXT,
  propensity REAL,
  propensity_kind TEXT NOT NULL CHECK (propensity_kind IN ('exact', 'deterministic', 'none', 'not_served')),
  learner_pick INTEGER NOT NULL DEFAULT 0 CHECK (learner_pick IN (0, 1)),
  -- R2 fills these (the Decider and the LLM); NULL while no model chooses.
  fallback TEXT,
  mixture_weights_json TEXT,
  model_distributions_json TEXT,
  sensor_answers_json TEXT,
  question_set_version TEXT,
  model_ids_json TEXT,
  card_hash TEXT,
  similar_decision_ids_json TEXT,
  latency_ms INTEGER,
  cost_usd REAL,
  detail_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  -- A drawn choice has 0 < p < 1; a deterministic one p = 1; a learner pick
  -- has no propensity (its choice was not sampled); a list that served no
  -- head (the learner chooses from it) has neither a choice nor a propensity.
  CHECK (
    (propensity_kind = 'exact' AND propensity > 0 AND propensity < 1)
    OR (propensity_kind = 'deterministic' AND propensity = 1)
    OR (propensity_kind IN ('none', 'not_served') AND propensity IS NULL)
  ),
  CHECK ((learner_pick = 1) = (propensity_kind = 'none')),
  CHECK ((chosen_ref IS NULL) = (propensity_kind = 'not_served'))
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
