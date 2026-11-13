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

**L3, kept (d).** `is_canonical_state_vault` is not one gate but a predicate called 21 times in `attempts/` and `learner/` and 11 more in 9 files of `daily_plan/`, `diagnosis/`, `goals/`, `scheduling/` and the sidecar's handlers (and wrapped once more in `attempts/grading.py:284`; every call is listed in §7). Deleting the tag test would leave every one of those calls a constant the tag-gate count no longer sees, and its legacy branches are the pre-canonical projection path the strategy gives to D5 ("the pre-canonical projection path (LEGACY-ONLY row)", with `attempts/attempts.py:3322`'s legacy writer). So the predicate and all its callers stay, for D5 to take with that path; the record lists them for it (§6). A5 and A6 test the same set directly and are taken here: their dead branches are no-ops.

**Kept as (c)**, readers of old rows by shape or marker (none is a tag gate, all are listed so no later step reads them as one):

| site | what it reads | why it stays |
|---|---|---|
| `attempts/attempts.py:1437` (`unassessed_evidence_row(row.attribution_json)`) | a stored evidence row's unassessed block | replay leaves those criteria unassessed as the live grade did, whatever today's config |
| `attempts/attempts.py:1519` (the strategy's `:1522`) | the attempt's stored `grading_source` | replay re-enters the live write's observation lane |
| `attempts/attempts.py:1525` (`:1529`) | whether a blind record exists | a blind-graded attempt replays blind |
| `attempts/attempts.py:1534` (`:1540`) | the blind record's hold | a held grade replays held |
| `attempts/attempts.py:1568` `current_epoch_reading` | grading epochs; a pre-contract only grade by shape (`only_grade`), the blind record's maximum | A3's kept branch: it is how rows written before `mvp-0.26` replay under today's tag |
| `learner/facet_evidence_timeline.py:850` (`legacy:{created_at}` epoch key) | rows without a `grading_revision` | went with L2's dead branch: only that branch grouped by it. The kept branch reads the same rows through `grading_epochs.ordered_epochs`, which keys a revision-less row by its `created_at` (the reader that stays) |
| `grading_epochs.py` (`current_epoch`, `ordered_epochs`, `only_grade`) | revision-less rows, epochs citing no contract | the readers replay, the timeline and feedback share for rows written before `mvp-0.26` |
| `learner/facet_state_reader.py:168`, `:470`, `:535` | a stored uncertainty row's own `algorithm_version` | row tags, not the vault's (and the set varies at the floor) |
| `outcome_contract.py:133` (`PRE_HOLD_ROUTE_CHECK_VERSIONS`) | a proof record's own version | the held-grades predicate's neighbour: a row marker, not an algorithm tag |
| `attempts/measurement_corrections.py:243` | the vault's tag against the caller's `projection_version` | an equality with an argument, not a constant |
| `learner/mastery.py:920` | `config.irt.enabled` | a config switch, no tag |

**`held_grades`-adjacent callers.** `held_grades.py`, `grading_epochs.py`, `outcome_contract.py` and `learner_protection.py` test no algorithm tag (the one version set there is the proof-record marker above). The callers of `held_grades` outside `attempts/` (`diagnosis/`, `daily_plan/`, `curriculum/`, `evsi_calibration/`) gate on no tag next to those calls; their packages' own gates are D6's. So nothing beyond `attempts/` and `learner/` is taken, apart from the one caller of L5's predicate outside them (`learnloop_sidecar/handlers/vault.py:114`), which would otherwise be left calling a deleted function.

## 2. What went, by area

Every class (a) site and the tag half of every class (b) site, in four source commits:

| site | outcome | commit |
|---|---|---|
| A9, A12, A13, A14, A17 | tag half gone; each predicate is its kill switch alone | `eef2b7d4d2` |
| A10 | `regrade_contracts = vault is not None` (the vault-less adjudication path, used by no current caller but the signature allows it, stays as it was) | `86df343342` |
| A11, A16 | the regrade and the key adjudication always bind the content they read; `db/stores/source_service.bind_replacement_grade` loses `gated` (both its callers passed the constant) | `86df343342` |
| A15 | a regrade always cites its contract, takes the next revision and supersedes every tier; `regrade_attempt` loses the held-grade read (`prior_held`) only the dead supersede branch used, `_publish_regrade` loses `supersede_tiers` and `cite_contract` | `86df343342` |
| A1, A2 | tag half gone (switches `replay.ledger_bounded`, `practice.attempt_keeps_content_state`) | `51bf76b54e` |
| A3, A4, A5, A6, A8 | gate and dead branch gone | `51bf76b54e` |
| A7 | tag half of the `or` gone, `replay` stays; `_attempt_reference_status` loses its `vault` parameter | `51bf76b54e` |
| L1, L2, L6 | gate and dead branch gone; L2's first-seen epoch grouping (only the dead branch read it) and the cross-epoch accumulation go | `d640f1e7ab` |
| L4 | tag half gone (switch `mastery.claim_fixes_enabled`) | `d640f1e7ab` |
| L5 | `replaced_claims_kept` deleted; `replace_claim_and_reanchor` always keeps the replaced claim in one transaction; the sidecar's starting-level re-seed (`learnloop_sidecar/handlers/vault.py`) passes `keep_replaced=True` | `d640f1e7ab` |
| L3 | kept (d) | — |

Deletion proof for what went beyond the gates (strategy §2.1): `replaced_claims_kept`, `prior_held`, `_publish_regrade`'s two parameters, `bind_replacement_grade`'s `gated` and `_attempt_reference_status`'s `vault` are searched over `src/`, `scripts/`, `tests/` and `apps/` as names and strings: no function-local or `importlib` import, no `METHOD_REGISTRY` / Typer / `MODULE_INVENTORY` entry, no frontend caller; the only test reference (`test_learner_report_superseded`, importing `replaced_claims_kept`) is edited (§3). `keep_replaced` on `Repository.replace_learner_claim` and `learner_profile.seed_global_learner_claim` stays: `bootstrap.create_vault` still seeds a new vault's first claim with the default (no earlier claim, so deleting none and keeping none are the same), which is an open item (§7). No version set in `algorithm_versions.py` was removed (D6's); the imports of them in the edited modules went.

`_compute_resolved_grade_application` shrank from 808 to 803 lines: only A8 sat inside it (A7 is a helper it calls). The long-function count fell from 81 to 80 (`_observation_events_by_facet`, 211 to 193); `regrade_attempt` 406 to 376, `replay_existing_attempt` 151 to 138.

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
