# K9.12 — probe declines, hook failures and passed stopping rules

Finished 2026-11-17, incorporating the orchestrator's two rulings and two design changes. No decision, observation writer, SQL statement, warning, migration, configuration field or algorithm tag changed. No commit was made. K9-60 and K9-61 are fixed; no mandatory stop remains. Two generated-reference validators and seven sandbox-dependent tests remain unverified/pending as detailed below.

## Records and declines

`chain_records` has a pure builder and the usual two-line, never-raising writer. The subject is **attempt**, presentation stays in facts, parent is `provenance.current_cause()`. There is no grade lookup, connection handling or `dataclasses.replace`. Under an entry-point scope the decline shares the action's trace with the later grade; outside it, subject lookup still reaches it.

Declines in evaluation order (original positions refer to `git show HEAD:src/learnloop/diagnosis/causal_discrimination.py`; current positions are re-derived):

| Code | Original return / current decline |
|---|---|
| `pinned_bundles_empty` | :655, split absent pin from empty bundles / :677 |
| `candidate_not_current` | :663, missing candidate or obsolete blind-input contract / :685 |
| `already_observed` | :669, existing observation / :694, only if no row names this attempt |
| `no_deterministic_rubric` | :672, sensor :592, missing current item or rubric / :697 |
| `no_assessed_criterion` | :672, sensor :620, no supplied criterion features / :697 |
| `pinned_bundle_missing` | :677 / :702 |
| `declared_features_not_covered` | :681 / :707 |

All seven constants live together in `chain_records` and pass `provenance.is_code`. Facts contain attempt/presentation/candidate ids and declared/supplied key counts, never learner text or feature values. The private sensor returns features plus a reason; its public wrapper retains the dictionary API. The sensor has no held-grade check; none was invented. Missing evidence still supplies the same zero-valued features.

The two original early returns remain silent. **No causal pin (including an empty pin) is also silent.** A causal pin with empty bundle ids records `pinned_bundles_empty`. Existing observation rows carry `probe_attempt_id`: a same-attempt observation is silent, another attempt (or unknown/null ownership) records `already_observed`. This adds only the comparison on the already-fetched rows, no read. Successful classification still uses its original observation writer, AST-identical to HEAD.

P1 uses served/pinned probes and real grading/observation services. Three damaged/legacy-row cases are tested directly at `auto_classify_pinned_probe`, then reached through the real `why attempt` CLI: empty bundles (current serving pins bundles), an obsolete candidate (current activation refuses its contract), and a missing bundle (current serving pins existing immutable bundles). Missing current item is a changed loaded-vault snapshot. The different-attempt case uses the production observation writer with another persisted attempt; the own-attempt case uses that writer with this attempt. The two new silent tests assert no `probe_classification` record. The AI-graded block-settlement test intercepts the writer, proves the grade does not exist yet, then proves `why attempt` reaches the decline with the eventual grade's action trace. The first self-graded version of this fixture did not settle the block; corrected to AI grading without changing source.

The four grade-keyed hook steps are `machine_check_sweep`, `cold_verification_wiring`, `probe_classification_hook`, `common_repair_consultation`. Each failed record keeps `learning_object_id` and adds `phase=grade_keyed`. All four tests complete the attempt and reach exactly one matching failed record. Existing post-diagnosis calls are unchanged. The complete current vocabulary also includes `escalation_receipt`, `learner_text_enqueue`; no retired shadow-selection code remains.

## Completion detail and readers

`evaluate_completion` keeps a local ordered `passed` list; a completion closure writes it in the existing detail, and an optional argument carries it to `_complete_on_value_stop`. The public reason-string API stays unchanged. Explicitly disabled action/robust gates are omitted; the budget comparison is listed when evaluated and false, and omitted when its evaluated gate lifts the exhausted cap, without an extra gate read. All eight rule sites retain their order and conditions; continuing persists nothing. Part C is **20 net source lines**.

All completions inside the evaluator, including robust and value stops, carry `rules_passed`. Direct calls to the value-completion helper without evaluator context, learner controls (`stop_diagnosing_and_teach`), `close_diagnostic_segment` and direct episode-status writes omit it. No list is guessed. `_robust_gate_verdict`, its existing override/completion/forecast functions and robust selection are untouched (protected functions AST-identical).

Readers audited across src/apps/sidecar/tests: `test_voi_stopping.py` and the direct `test_voi_v2.py` read named fields; `sim_probe_validation_helpers.py` returns detail for named-field checks; `diagnosis_journey_helpers.py` snapshots every column. `test_voi_merge_composition.py` compares the whole value receipt: it now asserts the exact new list separately, removes only that key and keeps receipt equality. `voi_restore_scenarios.py` summarizes named receipt fields but compares the integration summary whole: a rules-only detail previously absent must still summarize as no value-decision receipt. Its reader now handles exactly that metadata-only shape; no restore golden or decision assertion was changed. The repository writes the column; AD's column classification names it. No frontend or sidecar reader was found.

## Proof artifacts

Scratch `S` is `/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-k912`; `T=$S/t.sh`, `PY=$S/py.sh`. Original run-1 scripts, outputs and rejected candidate are retained. All run-2 scripts/outputs use `run2-*` names (comparison: `compare_run2.py`; static audit: `audit_run2.py`).

- **P1:** `run2_fail_first.py` temporarily writes untouched HEAD source, runs the final seven-code/four-hook/two-completion cases and restores working bytes in `finally`. `run2-p1-base.txt`: **13 failed in 2.93s**, all for absent new records/keys. `run2-p1-after.txt`: **44 passed in 7.87s**, including silent cases and pre-grade settlement. Run-1 fail-first remains in `p1-base.txt` (13 failures under its earlier design).
- **P2:** before regeneration, **3 failed, 15 passed** (`run2-p2-before.txt`). Regeneration: **18 passed**. `compare_run2.py` strips only allowed rows/keys and walks old/new in parallel, including regex substitution inside longer strings and keys, enforcing both directions of the token bijection and preserving row order. Tokens are scoped per case, as the harness restarts normalization per journey. Output: **map size 1,196; non-token differences 0; count consequences none**. Every mapping is identity in this final fixture. Two subsequent runs: **18 passed**, **18 passed**, both at `-n 3`.
- **Ruling 1 route:** comparison rule only, **no harness change needed**. With the revised silence rules there are no added journey rows, so no counter shift survives. `figure_build_golden_helpers.py` is unchanged. K9-60 records a settled proof issue, not a product bug.
- **P3:** unchanged identity pins, no write flag: all **340** pass in the required combined **420-pass** run (`run2-required.txt`); run 1's standalone result was also 340 passed.
- **P4:** independent checks of causal discriminating observations, probe observations, unresolved factors and all episode completion reasons: **PASS** modulo the same bijection (`run2-p2-comparison.txt`).
- **P5:** ruff passes; lint-imports **42 kept, 0 broken**, no exception added. `chain_records` imports no diagnosis module. No new cross-domain function-local edge: the sensor's canonical-projection import is the existing edge moved with its body; no frozen-import inventory change. `run2-audit.txt` also proves existing SQL strings/hook warnings unchanged, protected ASTs unchanged, pins file unchanged, part C +20 net.

Golden additions per case: **zero `probe_classification`, zero `diagnosis_step` in each** of budget_stop, causal_blocked_pending_review, causal_decline, causal_deferred_machine_checks, causal_needs_disambiguation, causal_safe_common_repair_available, causal_started, cold_fail, cold_pass, deterministic_classification, fg1_ask_now, fg1_wait, held_release, mid_check, recurrence_judge, regrade, text_prerequisite, value_stop. No added row codes to list. Added-row checkout path/SHA/hostname/wall-clock scan: **PASS (0 rows)**. The only changes are three `rules_passed` keys: budget_stop `[]`; regrade `[observation_budget_exhausted, action_equivalent]`; value_stop `[observation_budget_exhausted]`. Anything else: **none**.

## Commands and results

Every test command used T, explicit paths, `-n 3`, one command at a time. Commands below abbreviate only the common path/prefix; full outputs and chunk file lists are in S.

| Command | Result / output |
|---|---|
| T tests/test_why_cases.py tests/test_probe_records.py tests/test_voi_merge_composition.py -q -n 3 | Initial fixture iteration: 1 failed, 43 passed (`run2-targeted.txt`); corrected final: **44 passed** (`run2-p1-after.txt`) |
| T tests/test_probe_records.py::test_block_settlement_decline_precedes_grade_and_is_reachable -q -n 3 | **1 passed** (`run2-settlement.txt`) |
| T tests/test_why_cases.py tests/test_probe_records.py -k 'wasnt_this_probe or grade_hook_failure or late_completion or value_stop_omits' -q -n 3 | Untouched-source fail-first: **13 expected failures** (`run2-p1-base.txt`) |
| T tests/test_diagnosis_journey_golden.py -q -n 3 | Before: **3 failed, 15 passed**; after regeneration: **18 passed twice consecutively** (`run2-p2-before/pass1/pass2.txt`) |
| DIAGNOSIS_JOURNEY_WRITE_GOLDEN=1 T tests/test_diagnosis_journey_golden.py -q -n 3 | **18 passed** (`run2-p2-regenerate.txt`) |
| T tests/test_identity_pins.py tests/test_diagnosis_journey_golden.py tests/test_architecture.py tests/test_test_layout.py tests/test_structure_ratchets.py tests/test_cli_help_snapshot.py tests/test_why_cases.py -q -n 3 | **420 passed** (`run2-required.txt`) |
| bash S/run2-chunk-1.sh | 60 explicit files, -q -m 'not arc_close' -n 3: **745 passed, 7 socket-blocked failures** (`run2-chunk-1.log`) |
| bash S/run2-chunk-2.sh | 9 explicit files, same flags: initially **204 passed, 1 failed** (`run2-chunk-2-before.log`); reader corrected: **205 passed** (`run2-chunk-2.log`) |
| T tests/test_voi_v2.py::test_at_their_restore_values_the_switches_reproduce_the_branchs_decisions_exactly -vv -n 3 | **1 failed** before reader correction; full diff proves sole mismatch is metadata-only detail summarized as empty value receipt (`run2-restore-before.txt`); covered by passing chunk rerun |
| PY ruff check | **All checks passed**, twice (`run2-ruff.txt`, `run2-ruff-final.txt`) |
| PY lint-imports --no-cache | **42 kept, 0 broken**, twice (`run2-lint-imports.txt`, `run2-lint-imports-final.txt`) |
| PY python docs/learnloop-architecture-vault/_scripts/validate_vault.py | **PASS**, 2,237 notes; 57,580 links/fragments; 7,994 source paths (`run2-validate-vault.txt`) |
| PY python docs/learnloop-architecture-vault/_scripts/module_validate.py | **PASS**, 1,237/1,237 source modules, 69/69 package maps (`run2-module-validate.txt`) |
| PY python docs/learnloop-architecture-vault/_scripts/desktop_validate.py | **1 error**, stale Reference/_generated.md (`run2-desktop-validate.txt`) |
| PY python docs/learnloop-architecture-vault/_scripts/db_validate_reference.py | **8 errors**, generated source-line citations shifted in followups/probe_completion; 1,160 effective config leaves inspected (`run2-db-validate.txt`) |

`select_tests.py` searches only tests/test_*.py text for the requested vocabulary, the hook wrapper and four callees, yielding **69 files**; arrays in two bash scripts pass explicit lists, maximum 60. Across those chunks **950 passed, 7 not verified**. The four named hanging files are excluded by the script; none matched. No whole-suite run, test kill, retry or leftover `.pytest_tmp/run-*` directory. `git diff --check` passes.

All seven sandbox failures are unchanged `test_cli_generate_practice.py` tests: generate_practice_runs_codex_http_and_persists_proposal; generate_diagnostics_runs_codex_http_and_marks_need_fulfilled; accepting_diagnostic_proposal_queues_today_followup; rejecting_review_required_diagnostic_reopens_need_for_regeneration; generate_diagnostics_resolves_diagnostic_need_source_refs; populate_goal_generates_and_auto_accepts; populate_goal_review_flag_leaves_proposal_pending. Each fails creating its synthetic local HTTP server with PermissionError / Operation not permitted. No product behavior assertion was loosened.

## Vault and handoff

Hand-edited only: `Workflows/Debug a decision.md`, `Workflows/Inspect Persistent State.md`, `Decisions/ADR-017 One decision record, one trace id, one entry point.md`. Each now has last_reviewed 2026-11-17 (the orchestrator set implementation_version to the current tag, mvp-0.59). No Reference file was edited or regenerated; its two validator failures are left for orchestrator regeneration.

K9.14 should explain: `why attempt` answers why a **pinned causal** answer was declined, by these seven codes; ordinary diagnostic answers and already-read own observations are silent because their existing rows answer the question. A failed hook is a `diagnosis_step` with its step/phase; stop detail lists earlier evaluated rules without disabled gates or backfilled knowledge. It should describe subject reachability without a grade-ordering guarantee, and successful classification's existing observation receipt.

First review priorities: three damaged-row fixtures, the metadata-only restore-summary adaptation, zero added journey records after the two silence changes, and the generated-reference refresh required at landing. The landing gate, arc_close tests, four known hanging files and seven socket-dependent tests were not verified here.

## Orchestrator's review

- Run 1 stopped on two points; the rulings are ledger K9-60 (the golden is compared modulo a consistent renaming of its id tokens) and K9-61 (the decline record's subject is the attempt, so `why attempt:<id>` reaches it whether or not the grade record exists yet).
- Two cases the first draft recorded were made silent: an answer on a presentation with no causal pin (the classifier does not apply; it would have been a record per ordinary probe answer) and an answer this same attempt's earlier hook already read.
- My edits after run 2: in `evaluate_completion` the budget rule reads `at_cap` (listed as passed only when the count is below the cap; at the cap with the cap lifted it did not apply) and the action-equivalence gate is one name, `action_rule_applies`, used by the rule and by the passed list; a comment on the silent own-observation return; the three notes' `implementation_version`.
- Checked by me: `git diff` of the golden is three hunks, each a `rules_passed` addition; 593 targeted tests pass after my edits (pins, journey golden, why cases, the new tests, the value-stop and probe-episode suites); ruff clean.
