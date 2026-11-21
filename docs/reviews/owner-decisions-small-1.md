# Small owner decisions, batch 1

Decisions dated 2026-11-20. `T` and `P` below are the supplied `t.sh` and `py.sh` wrappers. Each pytest command used explicit files. The landing and arc-close gates were outside this run.

## S4

The strategy should name the refactor steps that adaptive difficulty's memory model and evidence packets build on, and give the facts about help before an answer a place in Appendix B.

`docs/specs/refactor_strategy_v3.md` now lists RE2 and L4 for adaptive difficulty, and E7b, L2, P1 (EP2) and the Appendix B help facts for evidence packets. Appendix B points to the reveal ledger, `help_assists`, help questions in `question_events`, the attempt columns and AD's `AttemptFacts`. EP0 names the shared attempt-facts view. G5's reader moves stay deferred.

Proof. The prerequisites were checked against the two feature specs and the November 16 strategy audit. A wrapper Python check reported `S4: two spec links and five source links resolve`. The shared architecture checks below passed. Neither feature spec's implementation was exercised.

## T4

Both K9.5b test-coupling counts should be held by the structure ratchet.

`scripts/refactor_measures.py` computes both measures. `tests/test_structure_ratchets.py` checks them against the two new entries in `tests/goldens/structure.toml`. The decision is recorded in K9-8 in `docs/reviews/refactor-bug-ledger.md`.

- **465 private patch sites.** Count each syntactic monkeypatch, setattr or mock.patch site targeting a private attribute of an actual `learnloop` module. Resolve import aliases and module re-exports. Count loops and each K9.5b-audited dynamic site once. Exclude class and instance attributes, test modules, `learnloop_sidecar` and public names.
- **23 source-dependent assertions.** Count assertions whose expressions depend on `inspect.getsource` directly or through assignments in the same function or at module scope. A source-read call used only for setup or parameterization contributes no assertion. The original measurement script, with its mobile test location brought up to date, independently counted 465 patches, 23 assertions and 29 source-read calls at this tip.

Proof. `P python tests/test_structure_ratchets.py --write` ended with `wrote tests/goldens/structure.toml`. Only the two new ceilings were taken from that output. A temporary addition to the tracked structure test file contributed one private patch and one source-dependent assertion. `T tests/test_structure_ratchets.py -q -n 2` reported `private_patch_sites` at 466 against 465 and `source_text_assertions` at 24 against 23. Its last line was `1 failed, 3 passed in 9.31s`. After removal, `T tests/test_refactor_measures.py tests/test_structure_ratchets.py -q -n 2 -m "not arc_close"` ended with `8 passed in 9.21s`, and the direct measure returned `{'private_patch_sites': 465, 'source_text_assertions': 23}`. The timed measurement lanes were outside this run.

## K5-4

The learner field and intervention outcomes keep their own research coldness rules.

`src/learnloop/field/outcomes.py` and `src/learnloop/substrate/intervention_outcomes.py` name the two rules and document the differences from `qualifies_as_cold_retrieval` at the readers. `src/learnloop/placement/state.py` describes its stricter receipt check as placement's. The ledger records the decision. `tests/test_family_memory_projection.py` pins a field memory retrieval that passes with a failed delay finding. `tests/test_coldness_receipt.py` runs the intervention replayer on a case where a recent retrieval in the same topic causes the receipt's cold claim to fail and the targeted answer still receives `cold_success`.

Proof. The shared readers and rebuild command below ended with `157 passed, 2 skipped in 12.68s`. No live vault or historical owner dataset was compared.

## D-47

The five writes begun before a refusal can finish by design.

`docs/reviews/refactor-bug-ledger.md` records the owner decision in D-47's status. `docs/learnloop-architecture-vault/Architecture/Desktop Architecture.md` lists Reader synthesis, paid-work receipts, a running reading sweep, a request-started background job and a racing exam grade.

Proof. The list was checked against D-47 and the owner sheet. A wrapper Python check reported `D-47: status and all five writes documented`. The shared architecture checks below passed. The five races were reviewed as documentation only and were not induced at runtime.

## UX-39 ceiling

The 1,200-second background stream ceiling is a structural operational keep.

`src/learnloop/params/parameter_registry.py` registers `chatgpt_plan:BACKGROUND_CEILING_SECONDS` in the same class as the `figure_manim:FUNCTION_CHECK_SECONDS` and `figure_manim:FUNCTION_CHECK_MEMORY_MB` machine-safety caps. The provider is resolved for this individual entry, leaving its unrelated constants outside the whole-module audit. The UX-39 ledger status records the registration. No registry entry-count golden needed an update.

The database reference generator refreshed the registry line anchors in the configuration notes for `ai`, `error_impacts`, `evidence`, `ingest` and `recall_coverage`.

Proof. Wrapper Python resolved the registry entry and checked that it is structural, operational and outside the persisted decision projection. It printed `chatgpt_plan:BACKGROUND_CEILING_SECONDS = 1200 (structural operational keep)`. `T tests/test_registry_audit.py tests/test_fitted_parameters.py tests/test_item_parameters.py tests/test_chatgpt_plan_deadline.py -q -n 2 -m "not arc_close"` ended with `51 passed in 4.62s`. The optional socket-backed `test_first_questions_arrive.py::test_the_plan_route_request_is_byte_identical_under_a_ceiling` was blocked at socket creation by the sandbox (`PermissionError: [Errno 1] Operation not permitted`). No live stream or model call was run.

## hypothesis_sets

Locked hypothesis sets belong to `RAW_LEDGER` as retained records.

`src/learnloop/db/table_roles.py` reclassifies the table. The probe store inserts locked sets and rebuild clears only `DERIVED` tables, so `rebuild_orchestrator.py` needs no inventory edit. The debug clock command can shift this table's timestamp just as it can for other retained records. The role requires preservation by rebuild and permits that explicit diagnostic operation.

Role membership also controls collection. `src/learnloop/substrate/dataset.py` and `src/learnloop/db/stores/collection.py` use an explicit exception to preserve the existing JSONL inventory and which adjudication evidence references are accepted. `tests/test_table_roles.py`, `tests/test_collection_dataset.py` and `tests/test_rebuild_history_appends.py` pin classification, collection behavior and preservation of an inserted row across rebuild.

The architecture vault's `Reference/Database/Table Roles.md` now links to the generated role counts in place of stale duplicated counts. The database generator and its table note, database catalog and provenance row reflect the new role. The generator also refreshed configuration-note line anchors shifted by the parameter registration.

Proof. The shared readers and rebuild command below ended with `157 passed, 2 skipped in 12.68s`. The two skips are owner-vault dataset cases. The database scripts' result lines are listed below. Reference provenance reflects this worktree before the orchestrator's commit. No owner vault or production shadow rebuild was inspected.

## Shared checks

| Command | Last result line |
|---|---|
| `T tests/test_coldness_receipt.py tests/test_family_memory_projection.py tests/test_intervention_outcomes_replayer.py tests/test_table_roles.py tests/test_collection_dataset.py tests/test_rebuild_history_appends.py tests/test_rebuild_orchestrator.py -q -n 2 -m "not arc_close"` | `157 passed, 2 skipped in 12.68s` |
| `T tests/test_structure_ratchets.py tests/test_identity_pins.py tests/test_public_tip_guards.py tests/test_test_layout.py tests/test_architecture.py -q -n 2 -m "not arc_close"` | `383 passed in 35.85s` |
| `P ruff check` | `All checks passed!` |
| `P lint-imports --no-cache` | `Contracts: 44 kept, 0 broken.` |
| `P python docs/learnloop-architecture-vault/_scripts/db_generate_reference.py` | Exit 0, `"table_notes": 397`, `"uncommitted_inputs": 16` |
| `P python docs/learnloop-architecture-vault/_scripts/db_validate_reference.py` | Exit 0, `"errors": []` |
| `git diff --check` | Exit 0 |

The filename search found `test_table_roles.py` and `test_intervention_outcomes_replayer.py`. It found no test files with `parameter_registry`, `params` or `learner_field` in their names. The related registry, fitted parameter, item parameter and field memory tests are listed above. The identity pin test and golden were unchanged.
