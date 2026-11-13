# Refactor D4: constant gates in attempts and the learner model

Step D4 of arc D (`docs/specs/refactor_strategy_v3.md` §2.6), on branch `refactor/d4-constant-gates-attempts`, based on main `0ea5459b76` (the floor `OLDEST_SUPPORTED = mvp-0.58` is enforced at every door, the upgrade chain is one table, the head is `mvp-0.59`). Structure track: no served or persisted value changes for a vault at or above the floor.

## 1. Step 0, before any deletion

### (a) The count at the real floor

`scripts/refactor_measures.py` classified gates against `mvp-0.43`, its old default. It now reads `algorithm_versions.OLDEST_SUPPORTED` (commit `dc0959d421`). At the base:

| floor | gate sites (`x in *_VERSIONS`) | constant at the floor | varying |
|---|---|---|---|
| `mvp-0.43` (the old default) | 103 | 79 | 24 |
| `mvp-0.58` (the enforced floor) | 103 | 95 | 8 |

The 8 that vary at `mvp-0.58` are the facet-belief successor's (`FACET_BELIEF_FIX_VERSIONS`, `FACET_BELIEF_CORRECTION_VERSIONS`: `mvp-0.59` only), five of them in `learner/facet_state_reader.py`; they are live branches and stay. In `attempts/` the classifier finds 17 constant sites and in `learner/` 6, as the strategy counted. Every set tested at those 23 sites holds both `mvp-0.58` and `mvp-0.59` (checked by importing them), so each gate takes its successor branch on every vault that opens.

### (b) Can a dead branch still run?

Each of the 23 gates reads the vault's current tag (`vault.config.algorithms.algorithm_version`, or the same through `getattr` on a duck-typed vault), never a tag stored on a row. So replay of a row written under an older tag runs today's branch, the one that stays. Where a vault's tag comes from:

- **A vault on disk**: `load_vault` refuses one below the floor, and one whose `learnloop.toml` names no tag (ADR-019). Doctor, the MCP server's and phone host's attach, and journals below the floor are refused the same way.
- **Shadow rebuild's forced tag** (`--set algorithms.algorithm_version=`): refused below the floor (`build_candidate_config`); at or above it, every set holds it.
- **`learnloop upgrade`**: sets the vault's tag to each row's predecessor, which is the floor or later (the table starts at the floor).
- **Configs built in code** (`LearnLoopConfig()`, tag `mvp-0.6`): in production only `substrate/activities._algorithm_version(None)` (a stamp, ledger D-23) and `params/parameter_registry` (numeric leaves) build one; neither reaches a gate here. `field/priors.load_frozen_priors` passes a namespace vault that carries the loaded vault's own config.
- **Harnesses that build their own vault**: `learnloop goldenpath bootstrap` (`mvp-0.8`) and `learnloop recall-calibration` (`mvp-0.6`) are refused by the floor today (ledger D-24).
- **A tag this code does not know** (`mvp-0.60` from a newer checkout, or another shape): `version_floor.is_below_floor` does not judge it (D1's choice), so such a vault opens, and today every gate in the code reads it as below every tag, which serves it the pre-`mvp-0.7` model throughout. After this step the gates removed here would serve it the head's branch while the others still serve the old one. No supported vault holds such a tag (the floor to the head is what this code opens by ADR-019, and the owner's vaults are at `mvp-0.58`), and what it is served today is already wrong, so this is not a dead branch an owner vault reaches in a supported way. It is a door gap: ledger row D-30 (refuse a tag outside `SUCCESSOR_CHAIN` at the door).

### (c) Every site

Classes: **(a)** a pure tag gate: the gate and its dead branch go. **(b)** tag and kill switch: only the tag half goes; the switch and its off-branch stay for D7. **(c)** a reader of old rows by shape or marker, or a replay path that interprets rows written at an older tag: kept. **(d)** kept for a later step, with the reason.

Line numbers are the base's (`0ea5459b76`).

| # | site | set | constant at `mvp-0.58` | dead branch (below the tag) | class |
|---|---|---|---|---|---|
| A1 | `attempts/attempts.py:1377` `replay_reads_bounded_ledger` | `REPLAY_LEDGER_VERSIONS` | yes | replay reads the whole ledger, not bounded at the replayed attempt | (b): switch `replay.ledger_bounded` |
| A2 | `attempts/attempts.py:1389` `attempt_keeps_content_state` | `ATTEMPT_CONTENT_STATE_VERSIONS` | yes | a live attempt writes the item's whole row | (b): switch `practice.attempt_keeps_content_state` |
| A3 | `attempts/attempts.py:1422` `replay_existing_attempt` | `REGRADE_CONTRACT_VERSIONS` | yes | replay reads every live evidence row and the first cited contract, never the current epoch; no unrecorded-contract hold | (a) |
| A4 | `attempts/attempts.py:2969` `_dual_write_grade_channel` | `REGRADE_CONTRACT_VERSIONS` | yes | the grade channel classifies against today's item rubric, and an unrecorded-contract grade is classified too | (a) |
| A5 | `attempts/attempts.py:3646` `_project_canonical_belief` | `CANONICAL_STATE_VERSIONS` | yes | no canonical projection after an attempt | (a) |
| A6 | `attempts/attempts.py:3740` `_stamp_observation_lineage` | `CANONICAL_STATE_VERSIONS` | yes | evidence rows get no contract snapshot or observation ids | (a) |
| A7 | `attempts/attempts.py:4365` `_attempt_reference_status` | `SOURCE_REFERENCE_GATE_VERSIONS` | yes | a live attempt's `reference_status` is `not_applicable` | (a), the tag half only: the `replay` half of the same `or` is not a tag gate (replay reads the stored status) and stays |
| A8 | `attempts/attempts.py:4584` `_compute_resolved_grade_application` | `P0_PROJECTION_VERSIONS` | yes | a model grade adds no channel variance to the mastery observation's noise | (a) |
| A9 | `attempts/blind_grading.py:85` `split_grading_active` | `DIAGNOSIS_SPLIT_VERSIONS` | yes | new attempts are graded jointly | (b): switch `diagnosis.split_enabled` |
| A10 | `attempts/grade_resolution.py:866` adjudication revision | `REGRADE_CONTRACT_VERSIONS` | yes | the adjudication revises every live row, not the current epoch, under any cited contract | (a), the tag half only: `vault is not None` stays (a caller without the vault still writes as before) |
| A11 | `attempts/grade_resolution.py:1040` `_bind_key_adjudication` | `SOURCE_REFERENCE_GATE_VERSIONS` | yes | a key adjudication never lowers the attempt's `reference_status` | (a) |
| A12 | `attempts/grading_support.py:255` `route_rules_active` | `ROUTE_RULES_VERSIONS` | yes | new blind answers are graded without the own-route rules | (b): switch `proof_check.enabled` |
| A13 | `attempts/grading_support.py:270` `method_rules_active` | `METHOD_EXPLICIT_VERSIONS` | yes | new blind answers are graded without the required-method rules | (b): switch `required_method.enabled` |
| A14 | `attempts/hint_fold.py:243` `fold_follows_attach` | `HELP_FOLD_ATTACH_VERSIONS` | yes | the predecessor's help fold | (b): switch `hints.fold_follows_attach` |
| A15 | `attempts/regrade.py:457` `regrade_attempt` | `REGRADE_CONTRACT_VERSIONS` | yes | a regrade cites no contract, takes no grading revision, and supersedes tier 1 (tiers 1 and 3 for a held, partial or clarified regrade) instead of every tier | (a) |
| A16 | `attempts/regrade.py:633` `regrade_attempt` | `SOURCE_REFERENCE_GATE_VERSIONS` | yes | a regrade never binds to the content it read (no `reference_status` lowering) | (a) |
| A17 | `attempts/stuck.py:78` `stuck_prompt_active` | `STUCK_PROMPT_VERSIONS` | yes | no "I'm stuck" | (b): switch `stuck_prompt.enabled` |
| L1 | `learner/facet_evidence_timeline.py:425` `_with_p0_masses` | `P0_PROJECTION_VERSIONS` | yes | the timeline carries no P0 mass map | (a) |
| L2 | `learner/facet_evidence_timeline.py:848` `_observation_events_by_facet` | `REGRADE_CONTRACT_VERSIONS` | yes | epochs ordered by first-seen stamp and accumulated across epochs; no unrecorded-contract hold | (a) |
| L3 | `learner/facet_state_reader.py:56` `is_canonical_state_vault` | `CANONICAL_STATE_VERSIONS` | yes | the legacy (`mvp-0.6`) per-LO facet state | (d): see below |
| L4 | `learner/mastery.py:188` `claim_fixes_live` | `CLAIM_FIXES_VERSIONS` | yes | the predecessor's claim seeds, re-anchors, merges and ranking | (b): switch `mastery.claim_fixes_enabled` |
| L5 | `learner/mastery.py:203` `replaced_claims_kept` | `SUPERSEDED_CLAIMS_VERSIONS` | yes | the replace seam deletes a replaced claim | (a) |
| L6 | `learner/residual_diagnostics.py:264` `residual_dependence_report` | `CANONICAL_STATE_VERSIONS` | yes | an empty report | (a) |

**L3, kept (d).** `is_canonical_state_vault` is not one gate but a predicate called 23 times in `attempts/` and `learner/` and 23 more in 11 files of `daily_plan/`, `diagnosis/`, `goals/`, `scheduling/` and the sidecar's handlers (and wrapped once more in `attempts/grading.py:284`). Deleting the tag test would leave every one of those calls a constant the tag-gate count no longer sees, and its legacy branches are the pre-canonical projection path the strategy gives to D5 ("the pre-canonical projection path (LEGACY-ONLY row)", with `attempts/attempts.py:3322`'s legacy writer). So the predicate and all its callers stay, for D5 to take with that path; the record lists them for it (§6). A5 and A6 test the same set directly and are taken here: their dead branches are no-ops.

**Kept as (c)**, readers of old rows by shape or marker (none is a tag gate, all are listed so no later step reads them as one):

| site | what it reads | why it stays |
|---|---|---|
| `attempts/attempts.py:1437` (`unassessed_evidence_row(row.attribution_json)`) | a stored evidence row's unassessed block | replay leaves those criteria unassessed as the live grade did, whatever today's config |
| `attempts/attempts.py:1519` (the strategy's `:1522`) | the attempt's stored `grading_source` | replay re-enters the live write's observation lane |
| `attempts/attempts.py:1525` (`:1529`) | whether a blind record exists | a blind-graded attempt replays blind |
| `attempts/attempts.py:1534` (`:1540`) | the blind record's hold | a held grade replays held |
| `attempts/attempts.py:1568` `current_epoch_reading` | grading epochs; a pre-contract only grade by shape (`only_grade`), the blind record's maximum | A3's kept branch: it is how rows written before `mvp-0.26` replay under today's tag |
| `learner/facet_evidence_timeline.py:858` (`legacy:{created_at}` epoch key) | rows without a `grading_revision` | goes with L2's dead branch only if nothing else reads it (§2) |
| `learner/facet_state_reader.py:168`, `:470`, `:535` | a stored uncertainty row's own `algorithm_version` | row tags, not the vault's (and the set varies at the floor) |
| `outcome_contract.py:133` (`PRE_HOLD_ROUTE_CHECK_VERSIONS`) | a proof record's own version | the held-grades predicate's neighbour: a row marker, not an algorithm tag |
| `attempts/measurement_corrections.py:243` | the vault's tag against the caller's `projection_version` | an equality with an argument, not a constant |
| `learner/mastery.py:920` | `config.irt.enabled` | a config switch, no tag |

**`held_grades`-adjacent callers.** `held_grades.py`, `grading_epochs.py`, `outcome_contract.py` and `learner_protection.py` test no algorithm tag (the one version set there is the proof-record marker above). The callers of `held_grades` outside `attempts/` (`diagnosis/`, `daily_plan/`, `curriculum/`, `evsi_calibration/`) gate on no tag next to those calls; their packages' own gates are D6's. So nothing beyond `attempts/` and `learner/` is taken, apart from the one caller of L5's predicate outside them (`learnloop_sidecar/handlers/vault.py:114`), which would otherwise be left calling a deleted function.
