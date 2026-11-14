# Refactor D5, part 2: the canonical-state predicate and its callers

Step D5 part 2 of arc D (`docs/specs/refactor_strategy_v3.md` §2.6), on branch `refactor/d5b-canonical-state-predicate`, based on `f3f3fa9b9a`: main at `2f35db5173` (D5 part 1 and K2.4a-c landed) plus R1-6's fix, treated as landed. Structure track: no served or persisted value changes for a vault at or above the floor (`OLDEST_SUPPORTED = mvp-0.58`, head `mvp-0.59`). The method is D4's (`docs/reviews/refactor-d4.md`) and part 1's (`docs/reviews/refactor-d5.md`), whose §1(d) table and §7 list what this part removes.

## 1. Step 0, before any deletion

### (a) The recount

At the base, `learner/facet_state_reader.is_canonical_state_vault` (a test of the vault's tag against `CANONICAL_STATE_VERSIONS`, which holds every tag from `mvp-0.7` through the head) has 32 calls in 15 files and one wrapper (`attempts/grading.py:284`, a lazy indirection with the same name). The calls are part 1's C1-C32, one for one; only C21 moved (`learner/facet_evidence_timeline.py:1164` at part 1's tip, `:1180` here, from R1-6's change above it). No string dispatch names the predicate (no `METHOD_REGISTRY`, Typer, `MODULE_INVENTORY` or `_reg_const` entry; no frontend, phone or script caller; the frontend reads the DTO fields `supported`, `canonicalKeys` and `modelVersion`). Two tests named it: `test_learner_read_model_pinning` (owner lane: asserted the fixture is canonical) and `test_today_headline` (patched `headline.is_canonical_state_vault`, T4).

| # | call (base line) | dead branch (the legacy vault) | outcome |
|---|---|---|---|
| C1 | `attempts/attempts.py:3296` | `write_legacy_facet_state=True`: the per-LO `evidence_facet_recall_state` rows and the legacy `facet_uncertainty` rows persisted | gone with the writer (§2) |
| C2 | `attempts/attempts.py:4264` | an attempt's facet priors from the per-LO table | gone |
| C3 | `attempts/attempts.py:5289` | the don't-know attribution keeps `recall_failure` / `scaffold_failure` | gone; `_dont_know_error_type` loses `vault` |
| C4 | `attempts/grading.py:373` | the five legacy builtin severities | gone with `builtin_error_type_defaults` |
| C5, C6 | `attempts/grading.py:1941`, `:1961` | the grader's prompt offers the five legacy error types, their selection policy, and the legacy seed names unfiltered | gone first and alone (§1(c)) |
| C7 | `attempts/grading.py:1997` | a grader's legacy error name left unmapped | gone |
| C8-C16 | `learner/facet_state_reader.py:106`, `:363`, `:376`, `:391`, `:417`, `:463`, `:468`, `:521`, `:533` | the wrappers read the per-LO tables (every stored uncertainty row whatever its stamp) | gone |
| C17, C18 | `learner/capability_grid.py:122`, `:221` | `supported=False`; no blueprint readiness | gone |
| C19 | `learner/recall_coverage.py:645` | no canonical reader | gone |
| C20 | `learner/facet_diagnostics.py:395` | the frontier coverage falls back to facet-level mass | gone |
| C21 | `learner/facet_evidence_timeline.py:1180` | no Ready derivation | gone |
| C22 | `daily_plan/headline.py:71` | no capability cells; "learning" from the LO's last mastery evidence | gone |
| C23 | `diagnosis/misconceptions.py:280` | the statement-matching registry normalization | gone |
| C24, C25 | `diagnosis/probe_instance_generation.py:244`, `:307` | no compositional pair; no mechanism ids in the misconception fatal set | gone |
| C26, C27 | `goals/goal_certification.py:114`, `:219` | nothing demonstrated; no recipe gaps | gone |
| C28 | `goals/goal_projection.py:709` | no blueprint readiness | gone |
| C29 | `scheduling/selection_rewards.py:438` | the flat blend for a blueprint-bearing LO | gone |
| C30 | `learnloop_sidecar/handlers/facet_detail.py:267` | no canonical reader | gone |
| C31 | `learnloop_sidecar/handlers/knowledge_model.py:92` | `supported: false` | gone |
| C32 | `learnloop_sidecar/handlers/facets.py:74` | facet rows keyed by their raw id; `canonical_keys: false` | gone |

### (b) The replay question

Every one of the 32 calls reads **the vault's current tag** (`vault.config.algorithms.algorithm_version`), never a row's stored tag, a marker or a shape. Where that tag comes from is unchanged since D4 §1(b) and part 1 §1(b): `load_vault` refuses a vault below the floor or one with no tag (ADR-019); doctor, the MCP server's and phone host's attach, and journals below the floor are refused the same way; the shadow rebuild's forced tag is refused below the floor; `learnloop upgrade` sets the tag to the table's links, which start at the floor; a `LearnLoopConfig()` built in code (tag `mvp-0.6`) reaches none of these calls in production (D-23); the two harnesses that build their own vault below the floor are refused (D-24). Replay (`rebuild-derived-state`, the shadow rebuild, the attempt replay path) runs every stored attempt under the vault's current tag, so it took the canonical branch at every one of these calls already. **A tag this code does not know** (D-31) now gets the canonical branch here, as it already did at part 1's sites; the door fix stays D-31's.

**Kept, class (c): readers of stored rows by shape or by their own tag.**

| site | what it reads | why it stays |
|---|---|---|
| `learner/facet_state_reader.current_facet_uncertainty` and the `FACET_BELIEF_FIX_VERSIONS` filters in `stored_facet_uncertainty_for_lo` / `stored_facet_uncertainty_state` | a stored uncertainty row's own `algorithm_version` | an mvp-0.6-era row a canonical vault still holds is never the successor's prior; the set varies at the floor |
| `content/facet_identity/actions.py:336` (`Repository.facet_ids_with_recall_evidence`) | whether any `evidence_facet_recall_state` row names a facet | an upgraded vault keeps the per-LO rows it wrote before `mvp-0.7` (the owner copies hold 80, 3 and 7); they still count as graded evidence for a facet's history |
| `substrate/shadow_rebuild.py:125` (the `facet` projection spec) | `evidence_facet_recall_state` rows before and after | the shadow report's facet comparison |
| `Repository.reset_learning_object_derived_state` | deletes an LO's `evidence_facet_recall_state` and `facet_uncertainty` rows | rebuild clears what it re-derives (unchanged) |
| `diagnosis/error_taxonomy_map.map_legacy_error_type` (now called unconditionally at the grader's taxonomy filter, `_normalized_recall_error_type`, `_dont_know_error_type`) | an error type stored or emitted under a legacy name | maps legacy names onto mechanisms on read |
| `diagnosis/error_taxonomy.BUILTIN_ERROR_TYPES` | the legacy grader names | known at every tag so a grade naming one proposes no new error type |
| `learner/recall_coverage.predicted_correctness(vault=None)` | the per-LO table | not a tag gate (a caller-shape branch): no caller omits the vault, so it reads a table nothing writes; kept, as D4 kept `adjudication`'s vault-less path (§7) |

### (c) The grader prompt, first and alone

C5/C6 build `_grading_error_taxonomy`, which goes into `GradingContext.error_taxonomy`: the joint grader's prompt, its payload, `grading_context_hash` (stored as an agent run's `input_context_hash`), and through `blind_context_from_grading_context` the blind grader's prompt and hash. The legacy branch was removed alone (`6e14e18d91`) and checked byte for byte: a scratch script built the fixed in-memory vault of `tests/identity_pins_helpers.py` at `mvp-0.58` and `mvp-0.59`, once as the pins hold it and once with seven more error types in `error_types.yaml` (the legacy seed names `recall_failure`, `scaffold_failure`, `arithmetic_slip`, `conceptual_error`, `incomplete_answer`, a mechanism-looking `procedural_error` and a custom one), and dumped for both practice items the taxonomy, `grading_context_payload`, `grading_prompt`, `grading_prompt_version`, `grading_context_hash`, `joint_grading_prompt_tokens`, the blind payload, prompt, prompt version and hash, and the `GradingProposal` / `StuckGradingProposal` schemas. Run with the base code (`git archive` of `f3f3fa9b9a` on `PYTHONPATH`) and with the branch: **identical, all 546,090 bytes**; the same after the attempts commit (which also replaced `builtin_error_type_defaults` in the taxonomy's filter). The bytes that disappeared are only the legacy branch's (the five-type card, its selection policy, and the unfiltered seed list a `LearnLoopConfig()` built in code at `mvp-0.6` would have produced).

**Which pins cover the kept branch:** no identity pin covers the grading context (`tests/identity_pins_helpers.py` registers no grading prompt; `grading_context_hash` is provenance, not a reuse key). The kept branch is covered by `test_grading_context` (the nine mechanism ids in order and the targeting policy on a head vault) and `test_km4_taxonomy::test_grader_taxonomy_emits_mechanism_vocabulary` (moved to the head), and by the scratch dump above. `tests/test_identity_pins.py` passes unchanged at every commit it was run on; nothing was written with `--write`.

## 2. What went, by package

| commit | package | what |
|---|---|---|
| `6e14e18d91` | grader prompt | C5, C6 |
| `79d990aaaf` | attempts (and the writer) | C1, C2, C3, C4, C7 and the `grading.py` wrapper. `_persist_attempt_application` loses `write_legacy_facet_state`; `Repository.record_attempt_outcome` and `replace_attempt_derived_outcome` lose `facet_recall_states`; `Repository._upsert_facet_recall_state` (their only use) goes. `builtin_error_type_defaults`, `BUILTIN_ERROR_TYPE_DEFAULTS` and `CANONICAL_ERROR_TYPES` go; the validator, severity, taxonomy and `diagnosis/error_taxonomy.persist_unknown_error_type_proposals` read `MECHANISM_ERROR_TYPE_DEFAULTS`. **S19**: `_guard_legacy_facet_write` goes whole (judgment call 2) |
| `08dcc890ac` | learner | C8-C21. `canonical_facet_uncertainty_on` is `facet_belief_fixes_on` alone; `_covered_frontier_fraction` loses `aggregate_facet_recall` and `learning_object_id` and its facet-level fallback; `facet_ready_derivation` returns `ReadyDerivation` (never `None`); the grid's `supported` is True for every LO the vault holds (False still for an unknown LO) |
| `dd94e8ed76` | daily_plan | C22. `_demonstrated` and `_has_direct_evidence` lose the flag, and the mastery read only the legacy branch used |
| `cf7d65e7e0` | diagnosis | C23-C25. The statement-matching normalization and the two helpers only it used (`_event_facet_ids`, `_event_statement_provenance`); the compositional path's shared helpers stay (`_candidate_misconceptions`, `_durable_match`, `_match_misconception`, `request_misconception_match`, `_decided_match`, `_registry_match_id`, `maybe_reprobe_for_misconception`) |
| `196dc6804a` | goals | C26-C28 |
| `b81b3b81b6` | scheduling | C29 (`selection_rewards.py` only; `scheduler.py` untouched) |
| `7f4eb4eef1` | sidecar handlers | C30-C32: the DTOs send `supported: True`, `ready` always, `canonical_keys: True`, the values every supported vault already sent |
| `fbe00ee1c9` | the predicate | `is_canonical_state_vault` deleted; the function-local edge `attempts.grading -> learner.facet_state_reader` leaves `tests/architecture_function_local_domain_imports.txt` (it went with the wrapper in `79d990aaaf`; the inventory test fails on a stale edge, so that commit alone fails `test_architecture`) |
| `898fe50793` | structure golden | largest import component 188 to 186, modules in a cycle 285 to 283 (`goals.goal_certification` and `scheduling.selection_rewards` left the cycle with their import of `facet_state_reader`); no number rose |

**Deletion proof** (strategy §2.1) for everything beyond the 32 branches: `is_canonical_state_vault` (both), `builtin_error_type_defaults`, `BUILTIN_ERROR_TYPE_DEFAULTS`, `CANONICAL_ERROR_TYPES`, `write_legacy_facet_state`, `facet_recall_states` (the two repository parameters), `_upsert_facet_recall_state`, `_guard_legacy_facet_write`, `_event_facet_ids`, `_event_statement_provenance`, and `_covered_frontier_fraction`'s two parameters were searched over `src/`, `scripts/`, `tests/`, `apps/` and the vault's `_scripts/` as names and strings: no function-local or `importlib` import, no `METHOD_REGISTRY`, Typer, `MODULE_INVENTORY` or `_reg_const` entry, no frontend or phone caller; the test references are edited (§3). No version set in `algorithm_versions.py` was removed: `CANONICAL_STATE_VERSIONS` is still tested directly by `content/proposals/patches.py:648`, `:1111` and the sidecar's `handlers/serializers.py:358`, `handlers/workbench.py:156` (D6's, part 1 §1(c)).

Edits made by a script rather than the Edit tool (each pattern asserted to occur exactly as often as replaced): the block replacements in `attempts/grading.py`, `attempts/attempts.py`, `db/repositories.py`, `learner/facet_state_reader.py`, `learner/facet_diagnostics.py`, `learner/capability_grid.py`, `learner/recall_coverage.py`, `learner/facet_evidence_timeline.py`, `daily_plan/headline.py`, `diagnosis/misconceptions.py`, `diagnosis/probe_instance_generation.py`, `diagnosis/error_taxonomy.py`, `goals/*`, `scheduling/selection_rewards.py`, the three sidecar handlers, and the test-file edits in §3; three single-line `sed` deletions (an unused import in `db/repositories.py`, an import in `test_recall_coverage_interventions.py`, the stale inventory edge).

## 3. Tests

The rules as D4's and part 1's: a test whose only subject is a deleted branch goes; a test that needed an old vault to get some vault moves to the head with its assertions; old rows whose writer is gone are built by a helper checked against that writer.

**Deleted (only subject a deleted branch):** `test_facet_belief_successor::test_the_legacy_recall_bridge_stays_refused_at_the_tag` and `test_km2b_consumer_rekey::test_every_canonical_version_refuses_legacy_facet_state_write` (the deleted guard); `test_ux_phase2_error_type_proposals::test_an_old_tag_grading_keeps_its_own_vocabulary` (the mvp-0.6 builtin set); `test_receipt_derivation::test_ready_derivation_none_on_legacy_vault` (owner lane: C21's `None`; its file-copy count in `test_sqlite_file_copies` falls 2 to 1); `test_causal_attribution_p0::test_event_facet_ids_never_fall_back_to_attempt_facets` (the deleted helper's own test); `test_km4_taxonomy::test_legacy_vault_still_mints_immediately` and `test_misconception_registry::test_normalization_creates_row_with_provenance`, `::test_normalization_dedupes_by_normalized_statement`, `::test_normalization_is_idempotent`, `::test_llm_match_new_inserts_over_text_match` (C23's statement-matching path mints a durable row from one event; the compositional path never does, so their assertions describe only the deleted path).

**Every assertion changed, and why:**

| test | before | after | why |
|---|---|---|---|
| `test_km4_taxonomy::test_grader_taxonomy_emits_mechanism_vocabulary` (was `test_mvp07_...`) | on an `mvp-0.6` and an `mvp-0.7` vault: the `mvp-0.7` ids are the nine mechanisms, `recall_failure` is among the `mvp-0.6` ids and not the `mvp-0.7` ones | on a head vault: the ids are the nine mechanisms and `recall_failure` is not among them | the `mvp-0.6` half was C5/C6's dead branch |
| `test_km4_taxonomy::test_retrieval_boundary_is_mechanism_based_and_domain_neutral` | the guidance assertions over the mechanism card and the legacy `recall_failure` card | over the mechanism card | `CANONICAL_ERROR_TYPES` (the legacy card) is gone; the same three assertions hold on the card the grader is sent |
| `test_km2b_consumer_rekey::test_attempts_write_no_legacy_facet_state` (was `test_mvp07_vault_refuses_legacy_facet_state_write`) | the per-LO table stays empty after real attempts, and a recall-row and an uncertainty-row write stamped `mvp-0.7` raise | the first half only | the guard is gone (judgment call 2); the table staying empty is unchanged |
| `test_ux_phase2_error_type_proposals::test_a_head_grading_naming_a_mechanism_type_proposes_nothing` | the nine mechanisms propose nothing | also: `recall_failure` proposes nothing | the old-tag test's first line, true at the head too (`BUILTIN_ERROR_TYPES`), kept where a vault opens |
| `test_recall_coverage_interventions::test_dont_know_keeps_full_coverage` (was `..._and_updates_facet_recall`) | on an `mvp-0.6` vault: the debug coverage and ability-transition assertions, the error event `recall_failure` with severity at least 0.60, and the per-LO facet row's masses | on a head vault: the same debug and transition assertions, the error event `retrieval_failure` with severity at least 0.60; the per-LO row assertions removed | the per-LO row was C1's dead write (its canonical counterpart is `test_dont_know_books_canonical_coverage_where_its_failure_mass_lands`, D-6); `retrieval_failure` is the head's name for the same attribution (C3; `test_hinted_dont_know_is_scaffold_failure...` already asserts it for the hinted case) |
| `test_misconception_registry::test_normalization_reactivates_resolved_row`, `::test_statementless_events_create_nothing`, `::test_llm_match_same_merges` | on an `mvp-0.6` vault, error events with no attempt row | on a head vault, the same events with an attempt row (`_insert_attempt`); every assertion kept | the compositional path shares these behaviours (a resolved row is a merge candidate and reactivates, a statementless event is skipped, an LLM `same` verdict merges) and materializes the attempt's episode first, which needs the attempt row |
| `test_today_headline` (fixture) | patched `headline.is_canonical_state_vault` to `True` | no patch | T4: the predicate is gone; the classes asserted are unchanged |
| `test_learner_read_model_pinning` (owner lane, fixture) | asserted the fixture vault is canonical | no assertion | the predicate is gone; every read model is the canonical one |

**Old rows built, not written.** `tests/diagnosis_input_provenance_helpers._misconception_from` builds a belief the statement-matching normalizer wrote (`provenance_writer="normalizer"`); it called the deleted `_event_statement_provenance` and now makes the same three `write_provenance` calls (`attempt_statement_refs`, `closure`, `fold_topic_records`) with the same arguments, so the record is the base writer's by construction. No other test read rows of the deleted writers: `test_km2b_consumer_rekey` and `test_facet_belief_successor` wrote per-LO recall rows only to see the guard refuse them.

**The census** (part 1's scratch plugin wrapping `version_floor.may_open_below_floor`), over the 11 test files this step edited, base code and tests against this branch: **21 test cases opened a vault below the floor at the base, 10 now (-11)**, in 6 files then and 3 now; none is new. The 11 are the deleted tests and the five moved to the head (`test_grader_taxonomy_emits_mechanism_vocabulary`, `test_dont_know_keeps_full_coverage`, and three in `test_misconception_registry`); the 10 left are other tests in `test_km4_taxonomy` (`_mvp06` / `_mvp07` vaults of the compositional and regrade-check tests) and `test_misconception_registry`'s posterior tests, whose subjects are not this step's (the re-tagging step's).

## 4. Proof

**P-shadow.** `/home/saturn/Documents/thinking/learnanything-ad1/fixtures-local/owner-copies-mvp058` (three vaults at `mvp-0.58`), copied with `copy_tree_with_databases` under `fixtures-local/d5b/{before,after}/`; `before` upgraded to `mvp-0.59` and shadow-rebuilt by the base code (`f3f3fa9b9a`, a `git archive` of `src/` and `migrations/` on `PYTHONPATH`), `after` by this branch at `fbe00ee1c9` (the last source commit). Counts only; the copies are deleted.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| `learnloop upgrade`, both | `mvp-0.58 -> mvp-0.59` | same | same |
| shadow facet / mastery / schedule changed, both | 0 / 0 / 0 (80 / 21 / 99 unchanged) | 0 / 0 / 0 (3 / 18 / 77) | 0 / 0 / 0 (7 / 34 / 32) |
| `schedule_effects` due dates moved (items, cards), both | 0, 0 | 0, 0 | 0, 0 |
| replayed attempts | 70 | 3 | 3 |
| live database unchanged by the shadow, both (report, and every table compared before and after) | yes | yes | yes |
| the two shadow reports, marker id, `as_of` and hashes aside | equal | equal | equal |
| every table of the two upgraded copies, row by row (ULIDs, stamps and hex digests normalized) | 402 tables, 19,442 rows: none differ | 402, 10,426: none | 402, 23,877: none |

The shadow report's facet counts are the owner copies' `evidence_facet_recall_state` rows (80, 3, 7): written before `mvp-0.7`, kept by every rebuild on both codes.

**Old rows at the floor and the head.** `fixtures/mvp017_route_check_replay` copied, retagged to `mvp-0.58` and to `mvp-0.59`, rebuilt live twice (`learnloop rebuild-derived-state`) by the base code and by this branch: after the first and after the second rebuild, at both tags, every table of the two copies is equal row by row, ids and stamps normalized, except one `attempt_debug_payloads` row (`att_02_svd_fail`), which is equal once the causal hypotheses' ULIDs replay mints and the diagnosis-receipt id hashed from them are normalized too, as in part 1. The second rebuild grows the ledgers on both codes alike (D-36, open).

**Identity pins** unmoved: `tests/test_identity_pins.py` passes at the attempts commit and at the tip; nothing written with `--write`. `test_retired_config_identities`, `test_effective_defaults_golden` and `test_cli_help_snapshot` pass unchanged.

**Measures** (`scripts/refactor_measures.py` at the enforced floor, base `f3f3fa9b9a` vs tip):

| measure | base | tip |
|---|---|---|
| tag gates: constant at `mvp-0.58` / all (varying) | 56 / 64 (8) | 54 / 61 (7) |
| constant gates in part 1's files (S13, S19, L3) | 3 | 1 (S13, kept (c)) |
| `mvp-0.N` literals: code / docstring / comment | 189 / 388 / 632 | 186 / 364 / 611 |
| functions over 200 lines | 78 | 78 |
| raw lines; code lines (all four packages) | 615,118; 432,574 | 614,656; 432,215 |
| `Repository` methods | 920 | 919 |
| `attempts/grading.py`; `attempts/attempts.py`; `db/repositories.py` | 2,031; 5,701; 27,591 lines | 1,929; 5,679; 27,483 |
| `learner/facet_state_reader.py`; `learner/facet_diagnostics.py`; `diagnosis/misconceptions.py` | 538; 857; 998 | 507; 819; 904 |
| `daily_plan/headline.py`; `learner/capability_grid.py` | 224; 231 | 213; 224 |

The varying gate that went is S19's stamp half (`FACET_BELIEF_FIX_VERSIONS` in the guard; judgment call 2). The predicate's 32 calls were never counted as gates (the classifier sees only `in` tests); the one gate it held (L3) and S19's gate half are the two constant ones.

## 5. The two tables (for arc J)

Nothing is dropped or migrated.

- **`evidence_facet_recall_state`** has **no writer** left in `src/` (the attempt path's was its only one, C1; doctor's alias merge went in part 1). **Readers** remain: `Repository.facet_ids_with_recall_evidence` (facet identity's evidence check), the shadow rebuild's `facet` projection comparison, `Repository.facet_recall_state` / `facet_recall_states` (reached only through `recall_coverage.predicted_correctness` with no vault, which no caller does, and tests), and `reset_learning_object_derived_state`'s delete. Upgraded vaults hold rows there (the owner copies 80, 3, 7).
- **`facet_uncertainty`** has **one writer**: the facet-belief successor's (`mvp-0.59` with `facet_diagnostic.canonical_belief_fixes` on) through `record_attempt_outcome` / `replace_attempt_derived_outcome`; it stays. `Repository.upsert_facet_uncertainty_state` (public) writes it too but has no `src` caller (tests seed rows with it). **Readers:** `learner/facet_state_reader` (the diagnostic layer, attempt priors, the stored-row readers), `instructional/valuation`, `instructional/reader_followups`, and the reset's delete.

## 6. Gates run

All under the empty-home wrapper in 5 GB scopes.
GATES_RESULT

## 7. Judgment calls

1. **The grader prompt's proof is a scratch dump, not a pin.** No identity pin covers the grading context and none was added: `grading_context_hash` is provenance (an agent run's `input_context_hash`), not a reuse key, so the identity-pin registry's rule (compared identities) does not ask for one. The byte comparison against the base code (§1(c)) is the proof; `test_grading_context` pins the ids.
2. **S19 went whole, not only its gate half.** With `_upsert_facet_recall_state` gone, `_guard_legacy_facet_write` guarded only `_upsert_facet_uncertainty_state`: it admitted a row stamped with a successor tag and refused one stamped with any other canonical tag. The only writer that reaches it is the successor's (`write_facet_uncertainty` is `canonical_facet_uncertainty_on`, which requires the successor's tag, and its rows carry that tag: `test_facet_belief_successor` asserts the stamp), so the refusal never fires on a vault that opens; the admitting half only exempted rows from the refusal, so with the refusal gone it does nothing. Part 1 classed that half (c) because it reads the row's stamp; it is the reading of a row being *written*, by a writer that stamps the vault's tag, not of a stored row. The stored-row readers of the same stamp (`current_facet_uncertainty`, the `FACET_BELIEF_FIX_VERSIONS` filters) stay.
3. **The misconception helpers.** Only the two helpers the statement-matching path alone called went; `_candidate_misconceptions`, `_durable_match` and the matchers stay because `_normalize_compositional` calls `_candidate_misconceptions` and `_durable_match` (and `diagnosis/text_gaps/candidates.py` calls the first).
4. **`recall_coverage.predicted_correctness(vault=None)`** keeps its per-LO read: it is a caller-shape branch, not a tag gate, and no caller omits the vault; D4 kept `adjudication`'s vault-less path on the same reasoning. Its comment now says the table is not written. Open item (§8).
5. **DTO fields kept with constant values.** `supported` (grid and timeline) and `canonical_keys` stay in the DTOs with the values supported vaults sent, rather than being removed, so the frontend contract (`apps/learnloop-tauri/src/api/dto.ts`) is unchanged; the grid's `supported` is still False for an LO the vault does not hold.
6. **`_covered_frontier_fraction`'s trace** keeps `denominator_basis = "contract_frontier"` (the only value a supported vault wrote); `contract_frontier_facet_mass` can no longer be produced.
7. **The attempts commit fails `test_architecture` alone**: the wrapper's function-local edge left the inventory in the predicate's commit, not the attempts one. Every later commit passes it.

## 8. Open items

- **For D6:** `CANONICAL_STATE_VERSIONS` is still tested directly at `content/proposals/patches.py:648`, `:1111` and the sidecar's `handlers/serializers.py:358`, `handlers/workbench.py:156` (part 1 §1(c)); the set stays until they go.
- **For J (tables):** §5. `Repository.facet_recall_state` / `facet_recall_states` and `recall_coverage.predicted_correctness`'s vault-less branch read a table nothing writes; `Repository.upsert_facet_uncertainty_state` has only test callers. Both are deletion candidates once arc J decides the tables' fate.
- **The parallel re-tagging step**: this step edited `test_km4_taxonomy`, `test_recall_coverage_interventions`, `test_ux_phase2_error_type_proposals`, `test_km2b_consumer_rekey`, `test_facet_belief_successor`, `test_causal_attribution_p0`, `test_today_headline`, `test_receipt_derivation`, `test_learner_read_model_pinning` and `diagnosis_input_provenance_helpers`; a merge may conflict there.

## 9. Not verified

- The durability lane, `--fresh-connections`, vitest, the owner lane (two owner-lane tests were edited: `test_receipt_derivation`, `test_learner_read_model_pinning`; they collect and skip here) and the arc-close lane (the orchestrator's).
- The desktop's facet screens with the constant DTO values (no GUI); the values are those every supported vault already sent.
- P-shadow covers the owner copies' small histories (70, 3, 3 attempts); the misconception normalization's compositional path on a real owner history with misconception events was not exercised beyond the copies and the tests.
