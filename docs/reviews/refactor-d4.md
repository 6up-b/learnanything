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
| L1 | `learner/facet_evidence_timeline.py:425` `_with_p0_masses` | `P0_PROJECTION_VERSIONS` | yes | the timeline carries no P0 mass map | (d): see below (first taken as (a), restored in `5b10db4222`) |
| L2 | `learner/facet_evidence_timeline.py:848` `_observation_events_by_facet` | `REGRADE_CONTRACT_VERSIONS` | yes | epochs ordered by first-seen stamp and accumulated across epochs; no unrecorded-contract hold | (d): see below (first taken as (a), restored in `5b10db4222`) |
| L3 | `learner/facet_state_reader.py:56` `is_canonical_state_vault` | `CANONICAL_STATE_VERSIONS` | yes | the legacy (`mvp-0.6`) per-LO facet state | (d): see below |
| L4 | `learner/mastery.py:188` `claim_fixes_live` | `CLAIM_FIXES_VERSIONS` | yes | the predecessor's claim seeds, re-anchors, merges and ranking | (b): switch `mastery.claim_fixes_enabled` |
| L5 | `learner/mastery.py:203` `replaced_claims_kept` | `SUPERSEDED_CLAIMS_VERSIONS` | yes | the replace seam deletes a replaced claim | (a) |
| L6 | `learner/residual_diagnostics.py:264` `residual_dependence_report` | `CANONICAL_STATE_VERSIONS` | yes | an empty report | (a) |

**L3, kept (d).** `is_canonical_state_vault` is not one gate but a predicate called 21 times in `attempts/` and `learner/` and 11 more in 9 files of `daily_plan/`, `diagnosis/`, `goals/`, `scheduling/` and the sidecar's handlers (and wrapped once more in `attempts/grading.py:284`; every call is listed in §7). Deleting the tag test would leave every one of those calls a constant the tag-gate count no longer sees, and its legacy branches are the pre-canonical projection path the strategy gives to D5 ("the pre-canonical projection path (LEGACY-ONLY row)", with `attempts/attempts.py:3322`'s legacy writer). So the predicate and all its callers stay, for D5 to take with that path; the record lists them for it (§7). A5 and A6 test the same set directly and are taken here: their dead branches are no-ops.

**L1 and L2, kept (d).** The evidence timeline mirrors the canonical projection's fold ("one authority, shared with the canonical projection"), and the projection has the same two gates (`substrate/canonical_projection.py`, D5's P0 and regrade-contract sites). Both were first deleted here (`d640f1e7ab`); the full sweep then showed the two folds disagreeing at every tag below `mvp-0.8` / `mvp-0.26` (`test_receipt_exactness`, `test_receipt_derivation`, `test_reader_recap_review*`, `test_projection_evidence_polarity`: timeline P0-discounted, projection not). No vault that opens is there, so nothing served changed, but a pair that must agree should go in one step: both gates were restored (`5b10db4222`) for D5 to take with the projection's.

**Kept as (c)**, readers of old rows by shape or marker (none is a tag gate, all are listed so no later step reads them as one):

| site | what it reads | why it stays |
|---|---|---|
| `attempts/attempts.py:1437` (`unassessed_evidence_row(row.attribution_json)`) | a stored evidence row's unassessed block | replay leaves those criteria unassessed as the live grade did, whatever today's config |
| `attempts/attempts.py:1519` (the strategy's `:1522`) | the attempt's stored `grading_source` | replay re-enters the live write's observation lane |
| `attempts/attempts.py:1525` (`:1529`) | whether a blind record exists | a blind-graded attempt replays blind |
| `attempts/attempts.py:1534` (`:1540`) | the blind record's hold | a held grade replays held |
| `attempts/attempts.py:1568` `current_epoch_reading` | grading epochs; a pre-contract only grade by shape (`only_grade`), the blind record's maximum | A3's kept branch: it is how rows written before `mvp-0.26` replay under today's tag |
| `learner/facet_evidence_timeline.py:850` (`legacy:{created_at}` epoch key) | rows without a `grading_revision` | L2's dead branch (stays with L2 for D5); the live branch reads the same rows through `grading_epochs.ordered_epochs`, which keys a revision-less row by its `created_at` |
| `grading_epochs.py` (`current_epoch`, `ordered_epochs`, `only_grade`) | revision-less rows, epochs citing no contract | the readers replay, the timeline and feedback share for rows written before `mvp-0.26` |
| `learner/facet_state_reader.py:168`, `:470`, `:535` | a stored uncertainty row's own `algorithm_version` | row tags, not the vault's (and the set varies at the floor) |
| `outcome_contract.py:133` (`PRE_HOLD_ROUTE_CHECK_VERSIONS`) | a proof record's own version | the held-grades predicate's neighbour: a row marker, not an algorithm tag |
| `attempts/measurement_corrections.py:243` | the vault's tag against the caller's `projection_version` | an equality with an argument, not a constant |
| `learner/mastery.py:920` | `config.irt.enabled` | a config switch, no tag |

**`held_grades`-adjacent callers.** `held_grades.py`, `grading_epochs.py`, `outcome_contract.py` and `learner_protection.py` test no algorithm tag (the one version set there is the proof-record marker above). The callers of `held_grades` outside `attempts/` (`diagnosis/`, `daily_plan/`, `curriculum/`, `evsi_calibration/`) gate on no tag next to those calls; their packages' own gates are D6's. So nothing beyond `attempts/` and `learner/` is taken, apart from the one caller of L5's predicate outside them (`learnloop_sidecar/handlers/vault.py:114`), which would otherwise be left calling a deleted function.

## 2. What went, by area

Every class (a) site and the tag half of every class (b) site, in four source commits (and one that restored L1 and L2):

| site | outcome | commit |
|---|---|---|
| A9, A12, A13, A14, A17 | tag half gone; each predicate is its kill switch alone | `eef2b7d4d2` |
| A10 | `regrade_contracts = vault is not None` (the vault-less adjudication path, used by no current caller but the signature allows it, stays as it was) | `86df343342` |
| A11, A16 | the regrade and the key adjudication always bind the content they read; `db/stores/source_service.bind_replacement_grade` loses `gated` (both its callers passed the constant) | `86df343342` |
| A15 | a regrade always cites its contract, takes the next revision and supersedes every tier; `regrade_attempt` loses the held-grade read (`prior_held`) only the dead supersede branch used, `_publish_regrade` loses `supersede_tiers` and `cite_contract` | `86df343342` |
| A1, A2 | tag half gone (switches `replay.ledger_bounded`, `practice.attempt_keeps_content_state`) | `51bf76b54e` |
| A3, A4, A5, A6, A8 | gate and dead branch gone | `51bf76b54e` |
| A7 | tag half of the `or` gone, `replay` stays; `_attempt_reference_status` loses its `vault` parameter | `51bf76b54e` |
| L6 | gate and dead branch gone | `d640f1e7ab` |
| L1, L2 | taken in `d640f1e7ab`, restored in `5b10db4222` (kept (d), §1) | — |
| L4 | tag half gone (switch `mastery.claim_fixes_enabled`) | `d640f1e7ab` |
| L5 | `replaced_claims_kept` deleted; `replace_claim_and_reanchor` always keeps the replaced claim in one transaction; the sidecar's starting-level re-seed (`learnloop_sidecar/handlers/vault.py`) passes `keep_replaced=True` | `d640f1e7ab` |
| L3 | kept (d) | — |

Deletion proof for what went beyond the gates (strategy §2.1): `replaced_claims_kept`, `prior_held`, `_publish_regrade`'s two parameters, `bind_replacement_grade`'s `gated` and `_attempt_reference_status`'s `vault` are searched over `src/`, `scripts/`, `tests/` and `apps/` as names and strings: no function-local or `importlib` import, no `METHOD_REGISTRY` / Typer / `MODULE_INVENTORY` entry, no frontend caller; the only test reference (`test_learner_report_superseded`, importing `replaced_claims_kept`) is edited (§3). `keep_replaced` on `Repository.replace_learner_claim` and `learner_profile.seed_global_learner_claim` stays: `bootstrap.create_vault` still seeds a new vault's first claim with the default (no earlier claim, so deleting none and keeping none are the same), which is an open item (§7). No version set in `algorithm_versions.py` was removed (D6's); the imports of them in the edited modules went.

`_compute_resolved_grade_application` shrank from 808 to 803 lines: only A8 sat inside it (A7 is a helper it calls), so the strategy's expectation of a large cut does not hold for this function. `regrade_attempt` 406 to 376, `replay_existing_attempt` 151 to 138, `_publish_regrade` 252 to 246. The count of functions over 200 lines is unchanged at 81 (it was 80 while L2 was deleted).

## 3. Tests

Each failing test was read to its gate. The rules applied: a test whose only subject was a deleted branch is deleted; a kill-switch test whose baseline was the predecessor reached through its tag now reaches it through the same switch (the predecessor's code is exactly the switch's off-branch); a test that used an old tag to get some behaviour moves to the head or to the switch that serves that behaviour; a test that reads rows an older tag wrote keeps reading them, built from today's writers (below).

**Rows built, not written.** Four writers are gone that wrote rows a vault at the floor still holds: the regrade below `mvp-0.26` (rows citing no contract, no revision, the model rows it replaced left live), the attempt step below `mvp-0.7` (no revision, contract or observation id), the attempt below the reference gate (`reference_status = not_applicable`), and the predecessor's replay of those. The tests that read such rows now build them with `tests/regrade_contract_successor_helpers.py`'s `as_regraded_before_contracts` (optional `supersede_tiers=(1, 3)` for a held, partial or clarified regrade) and `as_graded_before_contracts`, or a one-column update. **Fidelity**, checked with a scratch test run once on the base code (a `git archive` of `0ea5459b76` on `PYTHONPATH`) and once on this branch with the construction: the `grading_evidence` rows are identical, ids and stamps aside, for the blind and the self-graded/joint regrade at `mvp-0.25`, and for the pre-contract self-grade regraded in the same second and a second later; the seeded `mvp-0.6` history's `grading_evidence` is identical once its observation ids are nulled and its five contract snapshots dropped (`_history_graded_before_contracts`). What still differs is derived state and receipts the head's attempt step and replay write (mastery, surprise, administration snapshots, provenance records, one causal hypothesis version, one uncited contract snapshot); every test that uses the construction rebuilds before it asserts, so none reads them.

**Deleted (only subject a deleted branch):** `test_learner_report_superseded::test_below_the_tag_the_seam_still_deletes_the_replaced_claim` (2 cases); `test_lp_claim_fixes` four `[below_tag]` cases; `test_attempt_content_state_successor` three predecessor cases; `test_help_fold_attach_successor` three predecessor cases; `test_route_rules_in_grader` the old-tag loops of two tests and two predecessor cases of the kill-switch test; `test_required_method_grading` the older-tag line of one test and two predecessor cases; `test_stuck_prompt` the old-tag loop and two old-tag refusal cases; `test_regrade_contract_successor::test_below_the_successor_a_regrade_writes_as_before`, `::test_below_the_successor_old_rows_replay_exactly_as_before` and the predecessor case of the grade-channel test; `test_reference_gate_imports::test_below_the_tag_the_gate_never_runs`, `::test_below_the_tag_a_regrade_changes_nothing`; `test_rebuild_equivalence_review::test_below_the_tag_replay_is_the_predecessors`; `test_rebuild_equivalence`'s three strict xfails at `mvp-0.33` to `mvp-0.35` (they now pass: the deleted-claim defect lived only in the deleted branch; strategy §2.6 D8 had assigned them to D3's old tags).

**Every assertion changed, and why:**

| test | before | after | why |
|---|---|---|---|
| `test_stuck_prompt::test_a_partial_stuck_answer...` | calibration identity `grading_prompt_v2_1_blind_reference_policy` | `+own-route-v2` appended | the vault moved from `mvp-0.13` to the head, where the own-route and method rules are on; the stuck prompt still leaves the base grader's identity (no `+stuck`) |
| `test_stuck_prompt::test_an_ordinary_answer...` | prompt version `mvp-2.1-blind-reference-policy` | `+own-route-v2` appended | same |
| `test_stuck_prompt_composition::test_a_stuck_answers_pfc...` | `{REFERENCE_POLICY_PROMPT_VERSION}+stuck-v1` | `...+own-route-v2+stuck-v1` | moved from `mvp-0.13` to the head |
| `test_route_rules_in_grader::test_f5_a_regrade_supersedes_an_mvp017...` | `_route_judgments(held) == []` ("mvp-0.17: the rule does not run") | the rules' own verdict is written (`checked`, superseding nothing) | the rules run at every tag a vault opens at |
| `test_required_method_grading::test_every_other_regrade...` | the regrade's rows cite no contract (`{None}`) | they cite a snapshot of the edited item, never the answered contract | regrade contracts (mvp-0.26) at every tag; the test's subject (the regrade reads the item as it is now) is what the new assertion checks |
| `test_lp_claim_fixes::test_one_switch_...gated_by_the_tag` | `claim_fixes_live` is False at the predecessor's tag | removed; added: a namespace vault with no config reads off | the tag half is gone; the new line pins the defensive read the docstring names |
| `test_ux_phase4_feedback::test_f9f_a_regrade_in_place...` | response source `live` | `contract` | the regrade cites the contract it read; the key, criteria and maximum asserted are unchanged |
| `test_ux_phase4_feedback::test_f9f_an_ordinary_regrade_reopened...` | response source `live` | `contract` (then the reopened, built-uncited read stays `unrecorded`) | same |
| `test_ux_phase4_feedback::test_f9g_the_a_b_a_b_sequence...` | response `("live", key_a)` | `("contract", key_a)` (later reads of the built uncited regrade stay `unrecorded`) | same |
| `test_ux_phase4_landing::test_a_held_grade_resolves_nothing_until_a_contest_regrade_releases_it` | forecast `censored / graded_contract_unknown`; response `live`, later `unrecorded` | forecast `resolved / pass`; response and later read `contract` | the contest regrade cites its contract at every tag (the uncited case keeps its own test, `test_forecast_receipts::test_a_held_grade_resolves_nothing...`, on built rows) |
| `test_mvp017_route_check_replay` (both replay tests) | every derived table and the attempt rows unchanged by a rebuild at `mvp-0.17`; `manual_review_reason` as recorded | at the fixture's tag: the bounded-replay tables plus the attempt rows change once, then nothing; at the floor (new test): grades and holds as recorded, other ledgers unchanged, fixed point after one rebuild; `held_kept_by_failed_regrade`'s reason is `grade_contract_unrecorded` (held either way, same score) | the bounded replay and the regrade-contract reading apply at every tag; on base code, the same copy retagged to `mvp-0.59` rebuilds to the same rows as this branch at `mvp-0.17` and at `mvp-0.59` (§4) |
| `test_model_grade_lane::test_rebuild_moves_only_learning_objects_with_model_graded_attempts` | monkeypatched `attempts.P0_PROJECTION_VERSIONS` to fake pre-key history, asserted one LO's mastery moves | replaced by `test_replay_reenters_each_attempts_stored_lane`: model and self grades side by side rebuild to zero difference | T4: the test patched the deleted name; its subject (history written while the lane was keyed on mvp-0.8 alone) cannot be written any more; the lane itself is covered by `test_ai_graded_practice_takes_the_soft_score_lane_on_the_init_version` |

**Same assertions, other route** (a predecessor reached through its switch, or a vault moved): `test_lp_claim_fixes` three off-is-the-predecessor tests (baseline `PREDECESSOR` + switch off); `test_attempt_content_state_race` and `test_pr4_superseded_claims_landing` controls (switch off instead of below the tag); `test_route_rules_in_grader` (`V1 = [required_method] enabled = false` on the five tests pinning `own-route-v1`; kill-switch baseline `mvp-0.16` + `proof_check` off); `test_required_method_grading` (baselines + switch; the predecessor-grades replay test writes them with the switch off, then turns it on); `test_stuck_prompt` (kill-switch baseline `mvp-0.12` + switch off; `_stuck_vault` at the head); `test_attempt_completion`, `test_diagnosis_pipeline` (2), `test_diagnosis_async_router`, `test_teach_back` (2): joint grading through `diagnosis.split_enabled = false`; `test_rebuild_equivalence_review` (predecessor baseline + `replay.ledger_bounded` off); `test_learner_report_superseded` (the re-seed passes `True`, the sidecar's value). Built rows (above): `test_regrade_contract_successor` (11 tests through `_legacy_regraded`, the pre-contract tests, the forecast reader's predecessor case), `test_forecast_receipts` (3), `test_ux_phase4_feedback` (6), `test_reader_recap_review_r3` (3, through `regrade_contract_upgrade_helpers._legacy_vault` and `_held_then_released`), `test_held_grade_evidence::test_review_f1...`, `test_reference_gate_imports::test_a_regrade_after_the_tag_binds...`.

Two test files were edited by exact-pattern scripts rather than the Edit tool (`test_lp_claim_fixes`' four parametrized headers, `test_attempt_content_state_successor`'s three), each pattern asserted to occur exactly as many times as replaced.

Found by the full sweep and fixed the same way (each through the split's kill switch unless said): `test_active_errors_overlay::test_overlaid_read_equals_the_raw_read_on_a_joint_vault`, `test_diagnosis_card::test_joint_vault_feedback_carries_no_diagnosis_status`, `test_exam_session::test_an_exam_answer_is_stamped...[mvp-0.9]`, `test_km4_taxonomy::test_taxonomy_regrade_check_no_attribution_regressions`, `test_reader_guidance` (2, `JOINT_SHADOW`), `test_voi_stopping::test_a_joint_vault_lane_is_unchanged`, `test_sim_teach_back` (the module's sim vault; ledger D-31); `test_lp_claim_fixes_review` two `[below_tag]` arms deleted; `test_assessment_contracts::test_legacy_attempt_records_no_observation_lineage` deleted (its only subject was A6's no-op on an mvp-0.6 vault). The receipt, recap and polarity failures were the L1/L2 pairing (§1), resolved by restoring those gates, not by editing the tests.

**The census** (D1's plugin, rebuilt as a scratch plugin wrapping `version_floor.may_open_below_floor` and `shadow_rebuild`'s imported name). In the 33 test files this step edited, run on the base code and on this branch: **407 test cases opened a vault below the floor at the base, 336 now (-71)**; no file left the census (each still has other old-tag tests, D7's or the re-tagging step's). The whole landing selection on this branch (the sweep, §5): 3,862 cases. D3 recorded 4,834 at its tip; the steps that landed between account for the rest, so that difference is not this step's.

## 4. Proof

**P-shadow.** `/home/saturn/Documents/thinking/learnanything-ad1/fixtures-local/owner-copies-mvp058` (three vaults at `mvp-0.58`), copied with `copy_tree_with_databases` under `fixtures-local/d4/{before,after2}/`; `before` upgraded to `mvp-0.59` and shadow-rebuilt by the base code (`0ea5459b76` plus only the measures commit), `after2` by this branch's final source. Counts only; the copies are deleted.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| `learnloop upgrade`, both | `mvp-0.58 -> mvp-0.59` | same | same |
| shadow facet / mastery / schedule changed, both | 0 / 0 / 0 (80 / 21 / 99 unchanged) | 0 / 0 / 0 (3 / 18 / 77) | 0 / 0 / 0 (7 / 34 / 32) |
| `schedule_effects` due dates moved (items, cards), both | 0, 0 | 0, 0 | 0, 0 |
| replayed attempts | 70 | 3 | 3 |
| live database unchanged by the shadow, both | yes | yes | yes |
| the two shadow reports, marker id, `as_of` and hashes aside | equal | equal | equal |
| every table of the two upgraded copies, row by row (ids and stamps normalized) | 402 tables, 19,442 rows: none differ | 402, 10,426: none | 402, 23,877: none |

The same check ran after the first source commits (before L1/L2 were restored) with the same result.

**Old rows at the floor.** The owner copies hold few attempts (70, 3, 3) and no regrade written before contracts, so the replay of older rows was also checked on `fixtures/mvp017_route_check_replay` (rows written at `mvp-0.17`: route-check holds, a regrade the check kept held, an adjudication): copied, retagged to `mvp-0.58` and to `mvp-0.59`, rebuilt twice; the base code and this branch leave every derived table and ledger row identical (ids and stamps aside) after the first and the second rebuild, at both tags.

**Identity pins** unmoved (`tests/test_identity_pins.py` passes; nothing written with `--write`). `test_retired_config_identities`, `test_effective_defaults_golden` and `test_cli_help_snapshot` pass unchanged.

**Measures** (`scripts/refactor_measures.py` at the enforced floor, base vs tip):

| measure | base | tip |
|---|---|---|
| tag gates: constant at `mvp-0.58` / all (varying) | 95 / 103 (8) | 75 / 83 (8) |
| constant gates in `attempts/` + `learner/` | 23 | 3 (L1, L2, L3) |
| `mvp-0.N` literals: code / docstring / comment | 192 / 408 / 643 | 190 / 405 / 642 |
| functions over 200 lines | 81 | 81 |
| raw lines; code lines (all four packages) | 615,318; 432,825 | 615,186; 432,730 |
| `_compute_resolved_grade_application` | 808 lines | 803 |

At the old default (`mvp-0.43`) the base counted 79 / 103.

## 5. Gates run

All under the empty-home wrapper in 5 GB scopes.
- **Every test file of the landing selection** (`scripts/affected_tests.py` selects the whole suite: `db/repositories.py` changed, and `tests/conftest.py` imports it), 1,402 files in 15 chunks of 100 at `-n 4` behind `flock /tmp/learnloop-fullsuite.lock`, with the census plugin: 30,544 passed, 104 skipped, 9 xfailed, 21 failures and errors in 13 files, every one read and fixed (§3). The sweep ran on `a7a704136d`; chunks 10-14 ran after L1/L2 were restored. Then the failing files, every test file this step edited, every file reading the evidence timeline and the iteration set (120 files): 2,818 passed, 17 skipped, 3 xfailed, no failure, on `0db1e24fce`.
- **Arc-close lane** (`-m arc_close`, its 5 files): 24 passed, 36 xfailed (the known strict xfails).
- `test_structure_ratchets` (golden lowered with `--write`: stage comments in `attempts/regrade.py` 18 to 16, plus two entries other landings had already lowered; no number rose), `test_identity_pins`, `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_refactor_measures`: 283 passed.
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken. `scripts/check_gate_partition.py`: 30,795 collected, landing 30,735 + arc_close 60.
- Vault: references regenerated once after the source commits (`c99f23d60c`); a second `generate_all.py` changed nothing; the four validators pass (`db_validate_reference`, `desktop_validate`, `module_validate`, `validate_vault`).
- Not run (the orchestrator's): the durability lane (only `test_attempt_content_state_race`, which this step edited, carries the `durability` marker among the edited files; it ran in the sweep under the fast lane's patches), `--fresh-connections`, vitest, the owner lane.

## 6. Bug ledger

- **D-30** (step 0): a vault at a tag this code does not know opens and is served the pre-`mvp-0.7` model by every remaining gate (a mix once D4-D6 remove gates). Fix: refuse a tag outside `SUCCESSOR_CHAIN` at the door. Open, due at arc D's close.
- **D-31** (the sweep): `learnloop sim` on a vault at or past `mvp-0.10` with the split on fails on a teach-back item (the simulator provider cannot run the isolated blind grader). Pre-existing at the floor. Open, due at arc D's close.

## 7. Open items

- **For D5:** L1 and L2 (the timeline's P0 and regrade-contract gates) go with the projection's (`substrate/canonical_projection.py`). L3, `is_canonical_state_vault`, and its calls: `attempts/grading.py:373`, `:1941`, `:1961`, `:1997` (and its wrapper at `:284`), `attempts/attempts.py:3296`, `:4264`, `:5294`, `learner/facet_state_reader.py:106`, `:363`, `:376`, `:391`, `:417`, `:463`, `:468`, `:521`, `:533`, `learner/capability_grid.py:122`, `:221`, `learner/recall_coverage.py:645`, `learner/facet_diagnostics.py:395`, `learner/facet_evidence_timeline.py:1161`, `daily_plan/headline.py:71`, `diagnosis/misconceptions.py:280`, `diagnosis/probe_instance_generation.py:244`, `:307`, `goals/goal_certification.py:114`, `:219`, `goals/goal_projection.py:709`, `scheduling/selection_rewards.py:438`, and the sidecar's `handlers/facet_detail.py:267`, `handlers/knowledge_model.py:92`, `handlers/facets.py:74`. `fixtures/mvp017_route_check_replay`'s tests now read it at the floor too (§3).
- **For D6:** the sidecar's `live` grading record (`learnloop_sidecar/handlers/serializers.live_grading_record`, `feedback._run_regrade`) is used only when a regrade's rows cite no contract; every regrade cites one now, so the `live` source is never produced (an old uncited regrade is read later as `unrecorded`, never `live`). `keep_replaced=False` on `Repository.replace_learner_claim` / `seed_global_learner_claim` is now used only by `bootstrap`'s first seed of a new vault, where it is the same as `True`. `adjudication`'s vault-less path (`regrade_contracts = vault is not None`) has no caller without a vault. The version sets these sites tested stay in `algorithm_versions.py` (D6 removes the unused ones).
- **For D7:** the kill switches whose tag halves went (`diagnosis.split_enabled`, `proof_check.enabled`, `required_method.enabled`, `stuck_prompt.enabled`, `hints.fold_follows_attach`, `replay.ledger_bounded`, `practice.attempt_keeps_content_state`, `mastery.claim_fixes_enabled`) and their tests, which now reach the predecessor through the switch.
- **The in-code default** (`mvp-0.6`): a `LearnLoopConfig()` built in code now takes the head branch at every site D4 removed; the field's default is inert for these sites.
- **The parallel re-tagging step**: this step edited 33 test files that name old tags (§3's lists); a merge may conflict in `test_route_rules_in_grader`, `test_required_method_grading`, `test_stuck_prompt`, `test_regrade_contract_successor`, `test_ux_phase4_feedback`, `test_forecast_receipts` and the joint-vault files.
- **The strategy's count**: D4's "17 + 6" holds at the enforced floor; three of the 23 (L1, L2, L3) are left for D5.

## 8. Not verified

- The durability lane, `--fresh-connections`, vitest and the owner lane (orchestrator's).
- The desktop's feedback screen with the `contract` source after a regrade (no GUI); the `trigger_regrade` response was checked through the sidecar in tests only.
- P-shadow covers the owner copies' histories, which are small and hold no regrade written before contracts; the replay of such rows at the floor was checked on the tracked `mvp-0.17` fixture and on rows built by the tests' helpers, not on a real owner history.
- The constructed old rows (§3) were checked against the base writers for the scenarios the tests use, not for every shape an older tag could write (a clarified or partial regrade's `(1, 3)` supersession is built by the same helper with its tiers, and was not compared against the base writer).
