---
title: Collection and Dataset Contract
aliases:
  - Collection Contract
  - Dataset Export
  - learnloop-events-v1
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-09-23
source_commit: 2a218baead1b47a34debd9464568936ff58f1c28
source_commit_timestamp: "2026-09-23T15:42:12-04:00"
source_paths:
  - src/learnloop/outcome_contract.py
  - src/learnloop/db/stores/collection.py
  - src/learnloop/substrate/dataset.py
  - src/learnloop/substrate/data_quality.py
  - src/learnloop/cli/data.py
  - src/learnloop/scheduling/scheduler.py
  - src/learnloop/scheduling/evaluation.py
  - src/learnloop/attempts/attempts.py
  - migrations/161_collection_contract.sql
  - migrations/162_false_remediation_adjudications.sql
  - migrations/164_item_snapshots_and_adjudication_fk.sql
tags:
  - learnloop/concept
  - learnloop/evidence
  - learnloop/scheduling
  - learnloop/dataset
---

# Collection and Dataset Contract

LearnLoop records enough provenance on every attempt and every scheduler decision to tell, later and offline, **where an observation came from**, **what the learner was offered**, and **which labels it can support**. The contract is versioned, local, and read-only for analysis: `learnloop data-quality` reports coverage and `learnloop dataset-export` writes a reproducible artifact from a backup, never from the live database.

> [!important] Scope
> This is an observational record of one local vault. It licenses coverage reports and supervised datasets with explicit missingness. It does not license off-policy estimates: composed offers carry no selection propensity (see [[#Offers and scheduler decisions]]).

## Versions

`src/learnloop/outcome_contract.py` defines two version stamps. They are string constants written into rows and manifests, not database views.

| Constant | Value | Stamped on |
|---|---|---|
| `COLLECTION_VERSION` | `learnloop-events-v1` | [[practice_attempts]] and [[scheduler_slates]] (written explicitly by the repository), [[scheduler_offer_receipts]] and [[false_remediation_adjudications]] (written explicitly by the collection store), [[submission_intents]], [[attempt_completion_work]] and [[model_call_receipts]] (column default in migrations 159–161) |
| `LABEL_VERSION` | `learnloop-outcomes-v1` | every exported outcome record and every adjudication |

`DATASET_VERSION` in `src/learnloop/substrate/dataset.py` is `2`, written as `dataset_version` in an export's `manifest.json`. Version 2 adds `split_policy`; a manifest without `split_policy` (version 1) split by content family, as the `content` policy does.

Attempt and slate rows written before migration 161 carry the column default `legacy-unversioned`. The data-quality report raises alerts (`current_version_violations`) only for the current collection version; older cohorts are reported but not judged.

## Attempt provenance

Migration 161 adds three columns to [[practice_attempts]]. `AttemptDraft` defaults are `entry_surface = "unspecified"` and `evidence_origin = "unknown"`; each door sets its own:

| Door | `entry_surface` | `evidence_origin` | `awaits_completion` |
|---|---|---|---|
| Desktop practice submit / "I don't know" | `desktop_practice` | `human` | yes |
| Desktop teach-back finish | `desktop_teach_back` | `human` | yes |
| CLI practice | `cli_practice` | `human` | yes |
| TUI practice | `tui_practice` | `human` | yes |
| Exam session answers | `exam` | `human` | yes |
| Exam seeding | `exam_seeding` | `human` | no |
| Observation import | `observation` | `human` | no |
| Desktop easier/harder rung-variant request | `desktop_rung_variant` | `human` | no |
| Simulator runs and simulated teach-back | `simulation` | `simulator` | no |
| Diagnostic simulation | `diagnostic_simulation` | `simulator` | no |
| Recall calibration | `recall_calibration` | `simulator` | no |

`awaits_completion = False` marks a door with no post-attempt pipeline: its [[attempt_completion_work]] row is written `completed` with no route when the attempt is applied, so a `pending` row always means an interrupted completion and the data-quality report can count `completion_missing` and `completion_pending` honestly.

## Offers and scheduler decisions

A saved queue build writes one [[scheduler_slates|slate]] with `selection_policy = "composed_offer_v2"` and one [[scheduler_slate_candidates|candidate]] row per considered item. The chain from offer to attempt is:

1. **Decision features.** For each candidate whose learning object resolves, a selection row in [[decision_features]] (`decision_id` = candidate id) holds `ability_vector` (the selector's learner ability vector for the item's learning object plus a mastery summary), `item_demand_vector` (`practice_item_id`, `content_hash`, and the demand fields the selector scores), and `context = {"feature_schema": "selection_features_v1"}`. Components, propensity, policy and collection version are not repeated there; they live on the candidate and slate rows.
2. **Item snapshots.** `content_hash` is the SHA-256 of the item's canonical JSON (the whole model, sorted keys). The same transaction runs `INSERT OR IGNORE` into [[practice_item_snapshots]], so each scored revision is stored once and a decision can be joined to the exact item text after the vault item changes. Both tables refuse UPDATE and DELETE by trigger.
3. **Offer receipt.** The adapter filters the queue (for example, teach-back items whose grading provider is down) and calls `finalize_scheduler_offer(slate_id, candidate_ids)`. It rewrites `was_returned`/`returned_rank` to the shown order and inserts one immutable [[scheduler_offer_receipts]] row. The list must be an ordered subset of the selected candidates; a second finalize with a different list is refused.
4. **Submission intent.** The first save or submit of a draft calls `bind_submission_offer`, which inserts an immutable [[submission_intents]] row keyed by the client's `submission_id` (session, item, candidate, entry surface). The **first offer bound to a submission id wins**: reopening the item from a refreshed queue presents that queue's candidate, which is accepted only if it is a returned, unconsumed offer of the same item in the same session, and the original candidate is returned. A different item or session, or a candidate that is not such an offer, is rejected. Repeat binds read the existing intent without taking the write lock. A teach-back conversation has no submission id: `start_teach_back` and `submit_teach_back_turn` check a newly carried candidate with the same rule, and the conversation state, not a submission intent, keeps the first one until the finished attempt links it.
5. **Attempt.** The attempt stores `submission_id` (unique) and the bound `scheduler_candidate_id`; the candidate's `chosen_attempt_id` records the choice. When two submissions with one id race, the loser's insert fails the unique index and the sidecar answers with the winner's committed attempt.

> [!warning] No selection propensity for composed offers
> Every candidate of a composed slate stores `selection_propensity = NULL` and `propensity_kind = "unavailable_composed_offer"`. The pre-composition draw is kept as `components.base_selection_propensity`; composition after the draw and the learner's own choice change the action distribution, so it is not an importance weight. `learnloop eval` counts these chosen candidates under `unavailable_propensities` (with `unavailable_reason`), judges `off_policy_readiness` only on `recorded_chosen_candidates`, and reports `UNAVAILABLE` when chosen candidates exist but none recorded a propensity. See [[Scheduling and Selection#Explainability and evaluation]].

## Outcome labels

`outcome_records` builds one record per attempt, pairing it with the next attempt on the same learning object (chronological by `created_at`, then id). Each record carries `collection_version` (the attempt's own), `label_version`, `evidence_origin`, `submission_id`, `scheduler_candidate_id`, and five labels:

| Label | Definition as implemented | Status values |
|---|---|---|
| `R_next` | Correctness of the next attempt on the same learning object, with `elapsed_seconds`, `same_item`, `outcome_origin`, and `retention_exclusions` from `retention_exclusions()`: `hints_unknown`/`hinted`, `priming_unknown`/`primed`, `insufficient_delay` (under 86,400 s, or a missing, non-numeric or non-finite delay), `same_session`, `unresolved_grade`, `outcome_unscorable`, plus `non_human_outcome` when the outcome attempt is not human | `pending` (no later attempt), `observed`, `unscorable` |
| `R_cold` | One entry per final [[coldness_receipts]] receipt, per [[causal_cold_outcomes]] repair disposition, and per undecided or unfinalized [[cold_measurement_opportunities]] opportunity. A receipt's value is the cold attempt's correctness only when `qualifies_as_cold_retrieval` is true | `observed`; the receipt's own `outcome` (`cold_failure`, `indeterminate`, `right_censored_*`, …); else `unscorable` (qualified, unscored), `unqualified`, `unknown`; `pending` or the recorded decision for opportunities; `unavailable` with `no_measurement_opportunity` when nothing exists |
| `Q` | Count of [[question_events]] linked to the attempt | `observed_linked_questions` or `unavailable` |
| `B` | Attempt latency only; `total_burden_seconds` is always null | `partial` or `unavailable` |
| `F` | The latest [[false_remediation_adjudications]] row for the attempt (by `created_at`, id) | `adjudicated` with value, author kind and verifier version, or `unavailable` |

Delayed unassisted retention (`R_next`) is distinct from a certified cold measurement; only the cold-measurement ledger can establish the latter.

## False-remediation adjudications

[[false_remediation_adjudications]] is an append-only RAW_LEDGER: UPDATE and DELETE are refused by trigger, and a correction appends another row that supersedes the earlier one in `F`. The table has no foreign key to [[practice_attempts]] (migration 164 rebuilds it without one): scratch replays truncate attempts by walking that foreign-key graph, and the no-delete trigger would abort the walk. `record_false_remediation` checks that the attempt exists instead. Each row needs a boolean value, at least one evidence reference, `author_kind` `human` or `machine`, and a non-empty verifier version. Every reference is a `{table, id}` object naming a RAW_LEDGER or RECEIPT table with a single-column primary key, and `id` must match an existing primary-key value (so `submission_intents` is cited by `submission_id` and `scheduler_offer_receipts` by `slate_id`). Evidence is not required to belong to the adjudicated attempt.

## Dataset splits

`split_assignments` labels every attempt under one of two named policies, chosen with `dataset-export --split-policy` and recorded in the manifest. The policies support different evaluation claims, so neither is a stricter version of the other.

**Shared rules.** Only eligible attempts set cutoffs and occupy buckets: `evidence_origin = "human"` with at least one content-lineage key (`content_provenance = true`). Content lineage is `recipes[].blueprint_id` from the item's [[assessment_contract_versions]], `evidence_fingerprint.source_family` and `evidence_fingerprint.shared_stimulus_id`, and cited source spans from [[entity_source_links]] (`practice_item` and `learning_object` rows that are not `removed` and have a locator, keyed by source or revision plus locator). Ineligible attempts stay in the export as `unavailable_origin` or `unavailable_provenance`. Cutoffs fall at the 70% and 85% points of the distinct eligible timestamps, so a batch recorded at one instant never straddles a cut. `temporal` computes those indices with integer arithmetic (`n * 70 // 100`, so 90 distinct times give 63 training times) and reads a timestamp without an offset as UTC; `content` keeps its original arithmetic and parsing so its exports are unchanged. Rows are ordered by timestamp then id and do not depend on input order or the Python hash seed.

| Policy | Groups and cutoffs | Extra label | Supports | Does not support |
|---|---|---|---|---|
| `temporal` (default) | The learning object stratifies and does not group: each learning object's own eligible history sets its cutoffs. `group_hash` is the SHA-256 of `lo:<learning_object_id>`. | `quarantined_embargo`: a validation or test attempt less than the embargo after the learning object's last training attempt. An attempt exactly the embargo after it is held out. | Forecasting a known learner's next outcome on content they have already practised. | Generalization to unseen content or other learners. Items sharing a stimulus, blueprint or source span can fall on both sides of a cutoff. |
| `content` | Families are connected components (union-find) over the item, its learning object and its content-lineage keys; `surface_family` is a presentation-format label and never joins families. One set of cutoffs covers all eligible attempts. `group_hash` is the SHA-256 of the component's smallest key. | `quarantined_boundary_overlap`: the family's eligible attempts span a cutoff. | Generalization to content whose family never appeared in training. | Forecasting a known learner on practised content; one learner who revisits material can leave no held-out rows. |

`--embargo` is a duration (`7d` by default; `36h`, `90m`, `30s` or `0`) and applies only to `temporal`; it is measured from the latest eligible training attempt of the same learning object, and a duration too large to represent is refused. It is a duration rather than an attempt count because the leak it guards against is short-term memory of the training attempts, which decays with time rather than with the number of intervening attempts. A learning object whose eligible attempts share one distinct timestamp has no training rows and lands wholly in `test`.

> [!warning] Temporal cutoffs differ per learning object
> A training row on one learning object can postdate a held-out row on another. A model that pools across learning objects must build each row's features only from history before that row's timestamp.

Measured on a copy of `fixtures/linear_algebra` with all 70 attempts treated as human (8 learning objects, 5 to 12 attempts each, over 5.6 days):

| Policy | Train | Validation | Test | Quarantined |
|---|---:|---:|---:|---:|
| `content` | 23 | 0 | 0 | 47 boundary overlap |
| `temporal`, `--embargo 0` | 45 | 10 | 15 | 0 |
| `temporal`, `--embargo 1d` | 45 | 1 | 3 | 21 embargo |
| `temporal`, default `7d` | 45 | 0 | 0 | 25 embargo |

The fixture's whole history is shorter than the default embargo, so every held-out row is embargoed. In a vault with months of practice per learning object, only the held-out attempts in the week after each learning object's last training attempt are embargoed.

## Commands

| Command | Behavior |
|---|---|
| `learnloop data-quality [--vault PATH]` | Always prints JSON. Opens the database read-only inside one read transaction and reports attempt cohorts by collection version, entry surface and origin (offer links, propensities, durations, grading and contract coverage, completion rows), model-call cohorts, retention-label rejections, cold-opportunity progress, cold terminal dispositions, adjudication counts, and current-version violations. |
| `learnloop doctor --data-quality [--vault PATH]` | Prints the same report and returns without running the doctor checks; `--fix-state` and `--ai` are ignored with it. |
| `learnloop dataset-export OUTPUT [--split-policy temporal\|content] [--embargo DURATION] [--vault PATH]` | Refuses an existing `OUTPUT`, an unknown policy or a malformed embargo, and prints the output path, snapshot hash, artifact count, split policy and split counts. See below. |
| `learnloop adjudicate-remediation ATTEMPT_ID --false-remediation/--appropriate-remediation --evidence FILE --verifier-version TEXT [--author-kind human\|machine] [--vault PATH]` | Opens the vault through the locked, migrating opener and appends one adjudication; `--author-kind` defaults to `human`. `FILE` is a JSON list of `{table, id}` references. Bad input exits 1 with a one-line message. |

### What an export contains

`dataset-export` creates `OUTPUT`, takes an online SQLite backup into `OUTPUT/snapshot.sqlite`, and exports only from that copy:

- one JSONL per table whose role is RAW_LEDGER or RECEIPT, plus the captured workflow tables `proposed_patches`, `proposed_patch_items`, `synthesis_runs`, `model_work_checkpoints`, `ingest_batches`, `ingest_jobs` and `attempt_completion_work`;
- `outcome_contract.jsonl` (the labels above) and `split_assignments.jsonl`;
- `manifest.json`: dataset, collection and label versions, SHA-256 of the label code, snapshot and schema, migration list, per-artifact row counts and hashes, source asset hashes (assets are referenced, not copied), the inclusion rule, `split_policy`, `split_parameters` (`{"embargo_seconds": …}` for `temporal`, empty for `content`), `splits` (the policy's rule, the claim it does and does not support, and a note that a version 1 manifest without `split_policy` used the content policy), and the data-quality report as `missingness`. Only the export's copy of the report carries `splits`: `{split_policy, parameters, counts}` with rows per split label. `learnloop data-quality` omits it, because assignment depends on export options.

Each JSONL is hashed while written and fsynced; the snapshot is fsynced; the manifest is written to `manifest.json.tmp`, fsynced, renamed into place, and the directory is fsynced. The manifest is therefore the completion marker. Any failure removes the directory the export created.

> [!danger] Exports carry private text
> The snapshot is a full copy of the database, and the JSONL files include every ledger and receipt, among them [[model_call_receipts]] with prompt and response text (`input_text`, `output_text`) (learner answers and source excerpts). Treat an export as the vault itself. See [[Privacy and Trust Boundaries]].

## Related notes

- [[Scheduling and Selection]]
- [[Evidence and Measurement]]
- [[State and Persistence]]
- [[Privacy and Trust Boundaries]]
- [[Version Registry]]
