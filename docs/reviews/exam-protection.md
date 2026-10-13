# Exam protection: one exam predicate, the sources merge's five exam gaps, four sources bugs, the Reader's model contexts

**Branch:** `sources/exam-protection` (worktree `learnanything-merge3`), base main `e8d261405` (mvp-0.19, migrations to 197, head fixture `fixtures/migration_head_197`).
**Commits:** see §9.
**Migration:** none (no schema change; migration 193's text gains a corrected comment, §4.2).
**Algorithm successor:** none (§6).
**Paid calls:** none.

**Owner rule (2026-10-13).** Exams and problem sets are assessment material: they may seed question kinds and rigor, but held-out exam material must never be taught, shown to a model as teaching or explanation, leaked into practice, or reused as an independent check after the learner has seen it.

## 1. The one predicate

`src/learnloop/content/sources/exam_material.py` answers, for every reader and writer, *is this span, unit, extraction or item exam or held-out material, and as of which revision?* It is a leaf: at import time it reads only the standard library, `content.sources.role_authority`, `db.connection` and the stdlib-only `db.stores.source_block_fts`; the repository is duck-typed, and the two heavier helpers it can need (a member's pinned extraction, `source_outline.resolve_extraction_id`; a split unit's own blocks, `source_unit_selection.effective_unit_spans`) are imported where they are used.

**What is exam material** (`exam_material(vault, repository)`), read from the vault's source sets and the database's unit selections when it is built:

1. **An exam member, whole, in every revision.** Every extraction of a source (all its revisions and runs) that a source-set member gives the default role `exam`, or that a unit selection's outline role pick names `exam` (the import-batch path's role, before the source joins any set).
2. **An exam unit.** A scope entry with `role_override: exam`: in the member's pinned extraction by unit id with every nested unit (a merged unit is its members; a split child is the blocks under its own heading where that extraction's boundary overrides define it, else its whole raw parent), in every other extraction of the source by the pinned unit's label (a split child by its raw parent's label). A unit that does not resolve in an extraction makes that whole extraction exam material.
3. **A held-out unit, whatever its role.** Every unit marked `held_out_evaluation` in any unit selection of the source, in a source set or not: by id in the extraction whose selection marks it, by label in every other extraction; a split child withholds its whole raw parent, a merged unit its members; an id or label that does not resolve withholds the whole extraction.

**The held-out partition** (`held_out_partition`, `held_out_spans`): rule 3 plus the held-out assessment signals of exam units (their inventories' `held_out` signals, resolved in the member's pinned extraction). It is what the §8.5 leakage gate fingerprints; a whole held-out extraction contributes every block it has.

**Revisions.** `ExamMaterial.verdict(extraction_id, span_id)` returns an `ExamVerdict`: `exam`, `held_out`, the reasons (`exam_member`, `exam_unit`, `held_out_unit`, `unresolved_unit`, `exam_source`), the revision of the extraction the span lies in and the pinned revisions of the members that made it exam. Any revision of an exam source counts.

**Items** (`item_exam_status`): an item reserved for a goal's held-out exam (`exam_reserved`, an unreleased `exam_pool_items` row) is exam material, and so is an item whose own source (its canonical exercise region, its block-level source refs) is.

**Other roles.** `role_material(vault, repository, withheld_role)` is the same member/unit resolution for a caller that withholds more than exams (`corpus.teaching_exclusions`: problem sets, notes, unknown roles), so the resolution exists once.

**Held-out material alone** (`held_out_material(repository)`, `held_out_among(material, extraction_id, span_ids)`, `HELD_OUT_REFUSAL`): rule 3 read from the database's unit selections only (no vault), the same material as `ExamMaterial.held_out`, for the Reader surfaces that hold only a repository (§2.6), with the one learner-facing reason they all show: "This passage is held out for evaluation (an exam you'll sit later), so LearnLoop won't explain it or make questions from it: that keeps the exam a fair test."

### 1.1 What changed for each of the three old tests

| | Before | Now |
|---|---|---|
| **A. main's corpus predicates** (`corpus.exam_exclusions` / `exam_withheld` / `teaching_exclusions`) | every revision of an exam source; held-out units of source-set members only; a split or merged unit override was unresolvable, so its whole extraction was withheld | the shared predicate: held-out units **wherever they sit** (a selection outside every source set, the outline role pick `exam`); a split child resolves to its own blocks where its selection defines it, else to its raw parent (still fail closed; §1.2) |
| **B. the facet-meaning resolver** (`CitationResolver`) | only the member's pinned revision resolved, so a citation into another revision of an exam source was neither resolved nor `exam_material` (an uncited, confirmable reword); a held-out unit counted only where it resolved precisely | `resolve`, `exam_material` and `excerpt` ask the shared predicate (`CitationResolver.is_exam`), read over **every source set of the vault** (`exam_source_sets`), so any revision counts, held-out units count wherever they sit and unresolvable units fail closed. The support rule is unchanged: an explanatory citation beside an exam citation still supports a facet's meaning (`role_authority.support_verdict`); the predicate only says which citation is the exam one |
| **C. the leakage inventory** (`practice_leakage.held_out_spans`) | held-out units only inside exam-role units; in the member's pinned extraction only; filtered by subject | `exam_material.held_out_spans`: held-out units of any role, in every extraction of the source, unresolvable marks fingerprinting their whole extraction; the subject filter now narrows only the exam units' held-out signals |

### 1.2 One deliberate narrowing

Main's corpus read raw units only, so a role override on a split child (`chapter#Exam`) could not be resolved and the whole extraction (the whole textbook) was withheld from teaching. The shared predicate resolves it the way the facet rule always has (Codex re-review F3 of the facet authority fixes, spec_source_ingestion_v2 §4.3: each split child keeps its own role): `chapter#Exam` is exam material, `chapter#Theory` still teaches. Where a split cannot be resolved precisely (no boundary override defines it, another revision matched by label) the raw parent is withheld, so a split child never escapes. A held-out split child withholds its whole raw parent everywhere (main's corpus rule, the stricter one, kept). Test: `test_the_exam_half_of_a_split_unit_is_exam_material_and_its_theory_half_still_teaches` (on the base, `ext_split:s1` was withheld too).

## 2. Every reader and writer of the predicate

Each row is a caller; "via" names the shared function it reaches.

### 2.1 Teaching and model contexts (withhold exam material under every policy)

| Caller | Via | What it does with the answer |
|---|---|---|
| `source_retrieval/corpus.teaching_exclusions` | `exam_material` + `role_material` | the tutor's teaching scope and a model reader's withholding: exam and held-out material, plus problem sets, notes, unknown roles and assessment links |
| `corpus.teaching_scope` (callers: `source_retrieval/tutor.tutor_scope` and `tutor_pool`, `find_sources.scope_for` for `assisted_practice`, `post_attempt` on the teaching base and `scope="teaching"`, `instructional/exercises.exercise_scope` (the exercise arm), `instructional/exposure._worked_example_rule` (rule 4's shortlist), `instructional/needs.fulfil_need_from_sources` (the need's retrieval provenance)) | `teaching_exclusions` | drops whole exam extractions from the scope and excludes exam spans |
| `corpus.model_reader_withheld` (caller: `instructional/tools._model_withheld`: `find_sources`, `find_practice` and comparison results returned to a model) | `teaching_exclusions` | `assessment_lane` withholding |
| `corpus.exam_exclusions`, `corpus.exam_withheld` | `exam_material`, `exam_withheld` | the narrow exam set the library-wide paths read |
| `source_retrieval/tutor.PinnedSpanProvider` | `exam_withheld` | a pinned exam span never grounds the tutor ("it is exam material") |
| `source_retrieval/find_sources.find_sources` | `exam_withheld` | exam hits never reach verification nor the learner, under every policy; under `post_attempt` the item's own exam passages are no longer reopened (gap a) |
| `find_sources.scope_for(post_attempt)` | `exam_material` | a whole exam extraction never enters the scope; every exam span (the item's own included) stays excluded (gap a) |
| `source_retrieval/compare._compare_sources` | `exam_withheld` | exam pins and hits never reach the verification or comparison model; an exam pin is labelled "it is exam material" first |
| `content/authoring/practice_leakage.build_cross_source_spans` (callers: `tutor/tutor_qa._source_spans`, `practice_generation` (per target LO), `ops/pf_generation._passages`, `find_sources._provenance_list`, `source_retrieval/tutor.tutor_pool`'s provenance list) | `exam_material` | **new**: a link into exam or held-out material (a legacy `support` link) never grounds the tutor, generation or PF, whatever its relation |
| `ops/pf_generation._passages` (the parent's quoted source refs) | `exam_material` | **new**: an exam-sourced quote of the parent item is not a passage |
| `diagnosis/remediation.prescribe_remediation` (the fallback: the facet's first linked span) | `exam_material` | **new**: a repair never teaches from an exam passage; the next link is used (the ranked provider already went through `find_sources`) |
| `content/synthesis/source_set_synthesis._collect_inputs` | `exam_material` over every source set | **new**: a unit that is exam material by the predicate in a member whose own role teaches (a held-out textbook unit) is assessment only, its inventory never in the synthesis context; every held-out span of the synthesis's extractions joins the `held_out_leakage` gate |
| `content/facet_identity/authority.CitationResolver` (`resolve`, `exam_material`, `excerpt`, `is_exam`) | `exam_material` over every source set | an exam span resolves to the role `exam` (assessment alignment only); an unresolved citation naming exam material stays exam; no excerpt of exam material reaches a confirm card |
| its callers: `check_meaning_write` (every facet writer: `patches._compile_facet` through `ProposalAuthority`, `write_registry_text` with a `Cited` basis, `join_candidate`), `actions.confirm_reword`, `visible_sources`, `synthesis_gates._gate_exam_authority` / `_has_semantic_authority` / `_gate_practice_exam_only` (reading the resolved role), `source_set_synthesis._span_refs` and the registered-id check, `source_append._facet_reword` / `_checked_reword` and its `exam_material` check | the resolver | unchanged code; the exam part is now the shared predicate's |
| resolver construction: `actions.py` (three `for_vault`), `ProposalAuthority.for_proposal` (`for_source_set` with `exam_source_sets=vault.source_sets`), `source_set_synthesis._collect_inputs` (the same) | | a span that is exam material in ANY set is exam (facet-reword-confirm §9 Q5) |

### 2.2 Practice and leakage (never leak held-out material into practice)

| Caller | Via | What it does |
|---|---|---|
| `practice_leakage.held_out_spans` / `build_held_out_inventory` | `held_out_spans` | the leakage fingerprint |
| `content/authoring/practice_generation` (the generation gate) | `build_held_out_inventory` | blocks a generated item reproducing held-out wording or numbers |
| `content/authoring/source_exercise_import._import_source_exercise` | `build_held_out_inventory` | the import's leakage screen (unchanged), now fed by the shared partition |
| `source_exercise_import._import_source_exercise` | `exam_material` | **new (gap d)**: the region is rechecked before any model call; exam or held-out material is `rejected`, `exam_material: ...`, with each span's verdict |
| `source_exercise_import.find_book_solution` | `exam_material` | **new**: an exam or held-out solution never reaches the match model nor the authoring model as the book's solution |
| `content/pipeline/jobs.handle_reader_exercise_import` | `exam_material` (held-out part) | **new**: the Reader's own import refuses a selection in held-out material (`IngestRunnerError`, code `exam_material`) before authoring. Other exam material stays the learner's choice (§8 Q3) |
| `ops/pf_generation` | `build_held_out_inventory` | PF's leakage screen |
| `ops/contamination/detectors`, `ops/contamination/recipes` | `held_out_spans` | contamination reports |

### 2.3 Items, reservations and cold administrations

| Caller | Via | What it does |
|---|---|---|
| `instructional/policy.cold_administration_open` (callers: `caller_for`, `caller_for_question_event`, `tools.run_requested_tool`, the sidecar's `PinnedSpanProvider` in `handlers/tutor_qa`) | `exam_reserved` | **new (gap b)**: an item reserved for a held-out exam is a cold administration: `cold_attempt` ("the item is reserved for a held-out exam", `notes = ("exam_reserved",)`), so nothing is retrieved, compared or proposed and the pinned tutor grounds in nothing |
| `instructional/practice.refuse_exam_reserved_pick` (callers: `record_proposal_selection`, `imported_exercise_selection`; through them the sidecar's `plan_learner_pick` and the open-list serve `get_practice_item`, which now re-checks the selection **before** serving and records the delivery after) | `exam_reserved` | **new (gap c)**: a pick of an item reserved since its proposal is refused before anything is recorded or served |
| `item_exam_status` | `exam_reserved` + `exam_material` | the item-level answer (tests; the open question in §8 Q4) |
| the reservation's own readers, unchanged (they read the same `exam_pool_items` rows the predicate does): `goals.exam_pool.reserved_item_ids` → `scheduling.serving_exclusions` (Today's queue, the quick check, `find_practice` admission) and `practice_index.dossiers`; `scheduling.controller_ownership`; `practice_generation`; the sidecar's `goals` handler | `repository.reserved_exam_pool_item_ids` | quarantine from serving |

### 2.4 Shown material (gap e)

Not an exam predicate but the owner's default for independence: `db/stores/source_service.shown_items` (an item's own material shown ever: a reveal of its answer other than its own attempt's `answer_display`, its canonical exercise region or its import's book solution in `source_exposure_events`, an impression of its prompt or exercise in `instructional_impressions`). Callers: `goals.exam_pool._candidates`, `goals.certification_cold_probe.select_held_out_probe_item`, `diagnosis.remediation.start_remediation_treatment`'s cold item.

### 2.5 Role readers that are not protection (unchanged)

`content/synthesis/source_coverage` (the coverage preview counts exam units as assessment alignment), `content/synthesis/exam_profile` (the aggregate exam profile), `role_authority.support_verdict` / `is_semantic_support` (support, not leakage).

### 2.6 The Reader's model contexts (held-out material is never explained)

Added in the continuation (§9): the draft left these as an owner question, but the owner rule names them ("never shown to a model as teaching or explanation"), and the reader manifest's own contract already said it must not carry an assessment-reserved surface. They refuse **held-out** material (rule 3) whoever selects it; other exam material (an exam member or an `available_for_practice` / `blueprint_only` exam unit) the learner opened stays theirs to ask about (§8 Q1).

| Caller | Via | What it does |
|---|---|---|
| `tutor/tutor_qa.ask_question` (`context="reader"`: Reader Ask, the sidecar's `reader.ask`) | `held_out_material`, `held_out_among` | a question whose span or selection is held out is refused (`HeldOutMaterialRefused`, a `TutorQAError`, so the sidecar returns `validation_error` with the reason) before the question row, the thread or any call |
| `tutor_qa._reader_source_spans` (the reader manifest) | the same material | a held-out neighbour of the passage never enters the manifest |
| `reader/reader_dialogue.ask` (RW1a's dialogue and branches, asking through `ask_question`) | `held_out_material` | refused before any signal lands (answer mode, `learner_question_asked`) |
| `reader/reader_requests.model_synthesis` (demand-paged presets: worked example, another explanation, why it matters, ...; the capture outbox's and `reader.enqueue_request`'s requests) | `held_out_material` | rechecked when the request is sent (a mark may postdate the capture): a request on a held-out passage resolves `failed` with the reason before any call; held-out neighbours leave the window. The capture itself is kept |
| `content/pipeline/jobs.handle_reader_quick_check` (section checks) and `_handle_reader_inquiry_check` (RW1a passage checks) | `held_out_material` | refused with code `exam_material` before a client is built and before a check authored before the mark is handed back |
| `jobs.handle_reader_exercise_import` (§2.2) | `exam_material(...).is_held_out` | the same rule 3 |

### 2.7 Not routed (owner questions, §8)

The library search (only the query reaches a model), the reader guide plan (deterministic, no model) and the embedding backfill (exam text is embedded for search, not for teaching) do not ask the predicate. Reading a source in the Reader is the learner's choice and stays open, held-out units included: the owner rule's last clause allows for the learner having seen exam material, and §2.4 (shown material never becomes an exam item or a cold check) and §8 Q5 (an item exposed after its reservation) cover what that means for the exam.

## 3. The five gaps

| Gap | Before (base) | Fix | Test (failed on the base) |
|---|---|---|---|
| (a) `post_attempt` reopens whole exam extractions | `scope_for(post_attempt)` added every extraction the item names, whole and with no exclusion, and `find_sources` subtracted the item's own spans from the exam set | exam extractions never enter the scope; exam spans (the item's own included) stay excluded; `find_sources` withholds exam under every policy | `test_post_attempt_never_reopens_an_exam_extraction_or_an_exam_item_s_own_span` (base: `ext_exam` in the scope) |
| (b) `cold_administration_open` ignores exam-reserved items | an exam-reserved item was ordinary for the tutor, `find_sources`, comparisons and proposals | reserved means cold, with an honest reason | `test_an_exam_reserved_item_is_a_cold_administration_for_every_caller` |
| (c) picked practice proposals skip the exam-reservation check | `record_proposal_selection` recorded the usage and the item was served | refused before recording or serving, on both serving paths | `test_a_pick_of_an_item_reserved_since_its_proposal_is_refused_before_anything_is_recorded`; sidecar: `test_a_pick_of_an_item_reserved_for_an_exam_since_its_proposal_is_refused_before_serving`, `test_the_open_list_refuses_an_item_reserved_for_an_exam_after_its_pick` |
| (d) an import trusts a stale proposal | the region was imported (only a held-out *exam* unit's wording was screened) | the region's exam and held-out status is rechecked at import, before any paid call | `test_an_import_rechecks_a_stale_proposal_before_any_paid_call` (base: written, with model calls) |
| (e) an exposed import can still become an exam item or a cold probe | the exam pool excluded attempted and unverified items only; the probe and the cold retry ignored exposure | shown material (owner default, conservative, no time window) is never reserved for an exam, a certification cold probe or a cold retry | `test_an_exposed_import_never_becomes_an_exam_item`, `test_an_exposed_import_never_becomes_a_certification_cold_probe`, `test_a_revealed_item_is_never_the_cold_retry` |

## 4. The sources bugs

### 4.1 `action_disagreement` was never set

`needs.fulfil_need_from_sources` compared the valuation's named action with `pending_decision["live_repair_class"]`, which `pending_causal_decision` never set, so a `stop` never logged a disagreement in production (the test injected the key). `pending_causal_decision` now carries `live_repair_class` (`needs.live_repair_class`): the repair the attempt's diagnosis selected (`repair_selection.selected`, what a guided redo and a repair episode run), else the factor's latest live decision receipt when it names exactly one repair class. Logging only; it never changes the repair. Test: `test_a_priced_causal_decision_carries_the_live_repair_class` (base: `KeyError`).

### 4.2 Migration 193's comment

It said `router_decision_id` is "R1's learner_pick row for the pick, when the router_decisions table exists"; the code records the decision of the plan block that served the pick, exactly as the serving path returned it, never a matching-row lookup, NULL when there is none. Comment-only (the migration file and `instructional/interventions.py`'s docstring). A database that already applied 193 keeps the old comment in its stored DDL, and so does `fixtures/migration_head_197`, which the DB reference quotes; the next head-fixture rebuild picks it up. Test: `test_migration_193_describes_router_decision_id_as_the_serving_block_s_decision`.

### 4.3 The daily envelope ignored the injected clock

`daily_envelope(vault, repository, clock)` chose the day by the clock, but its `SharedDailyEnvelope` stamped every reservation, charge and settlement with the system clock (`reserve`, `charge`, `settle`), and its totals used the system clock too. The envelope now keeps its clock (`_now()` for the three writes and the accounting), `service_spend_today` and `spend_report` pass it to the accounting, and an injected clock gets its own cached envelope (the system clock's stays shared per database and day). Test: `test_the_daily_envelope_stamps_its_rows_with_the_injected_clock`.

### 4.4 Harvest's dry run priced the rerank at the wrong setting

The live mixed rerank is priced (and refused when unpriced) at `practice_index.rerank_price_per_million`; the dry run priced it at `source_service.llm_price_per_million`. It now uses the rerank's own setting, named on the row and in the estimate's basis. Test: `test_harvest_dry_run_prices_the_rerank_at_its_own_setting` (base: 0.17229 against 0.034458).

## 5. Tests

`tests/test_exam_protection.py` (24 tests: 21 from the interrupted run, three for the Reader's model contexts added in the continuation) and two sidecar tests in `tests/test_learner_pick_proposal.py`. Fail-first evidence: each was run against a `git archive` of the base commit's `src/` and `migrations/` (`-o pythonpath=<base>/src`, the import path checked): every test failed there except the migration-comment test, which reads the working tree's file (the base's line is the one quoted in §4.2). The predicate's own tests that call the new module failed on the base because it did not exist; each of them also asserts a base reader's behaviour where one existed (the resolver, the corpus, the leakage inventory). The three Reader tests (`test_a_reader_question_about_held_out_material_is_refused_before_anything_is_sent`, `test_a_reader_preset_on_held_out_material_fails_before_any_model_call`, `test_a_reader_check_over_held_out_material_is_refused_before_any_model_call`) were run with the continuation's `src/` changes stashed: all three failed (the preset was sent to the model; the checks built a client; Reader Ask has no refusal there, and with only the neighbour filter disabled its manifest carried the held-out worked example's blocks `t4`/`t5`).

One existing test changed: `test_facet_authority_review.py::test_an_undo_never_mints_a_candidate_whose_recorded_citations_no_longer_resolve`. Its exam member leaves the source set but its selection still marks the paper `held_out_evaluation`, so under the shared predicate it is still exam material and the undo is refused as `exam_authority` (stricter); once the mark is cleared too the citation is merely `unresolved_citation`, as the test asserted. Both refusals mint nothing.

## 6. No algorithm successor

The playbook asks for a successor when a change alters persisted meaning. Nothing here reinterprets a stored row or a replayed projection: withholding more exam material from teaching and models, and the Reader's refusals of held-out material (§2.6), are content and privacy rules; the import recheck, the pick refusal and the cold policy refuse new work; the exam pool, the certification probe and the cold retry choose among future candidates (reservations and tasks already made stand, and a coldness receipt still judges each attempt when it is made). No defaults changed, so no defaults snapshot moved. A protection rule has no kill switch: one that can be turned off is not a protection.

## 7. Gate

Run on `27a60d0fe` (the code as committed; this record is the only later change), with `TMPDIR` set to the worktree's `fixtures-local/tmp`:

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 17 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9978 passed**, 0 failed, 0 skipped (5 min 48 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 9879 deselected |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated (no schema change; cited source lines moved); validate: no errors |
| frontend (`npm ...`), `cargo check` | not run: nothing under `apps/learnloop-tauri` changed |

The first full run (on `2cd7b7c70`) failed one test, `test_architecture.py::test_function_local_domain_imports_match_the_frozen_edge_inventory`: the Reader refusals had added four function-local cross-domain imports. `118fba8a8` moved them to module level (`exam_material` is a stdlib-only leaf, so no cycle) and the rerun above is clean. Targeted runs before the gate: `tests/test_exam_protection.py` 24 passed; the Reader, tutor, quick-check, ingest-job, exam and leakage test files (51 files) 483 passed.

## 8. Open questions for the owner

1. **The Reader and non-held-out exam material** (§2.6). Held-out material is now refused by every Reader model context (the draft's recommended default, applied). An exam member or an `available_for_practice` / `blueprint_only` exam unit the learner opens can still be explained by Reader Ask, presets and checks. Recommended default: keep (the learner chose it, and only held-out material must stay a fair test). Related: a section quick check authored before a unit was marked held out is no longer handed back by its job, but the guide plan (`reader_guidance`, which lists an extraction's authored checks) still shows it; recommended default: hide such rows in a follow-up.
2. **Family reveals for shown material** (§2.4). `shown_items` counts the item's own material only; a sibling's revealed answer does not bar it. Recommended default: keep own-material only (the reveal ledger's time windows already govern family coldness).
3. **Reader imports of non-held-out exam material.** The Reader's import refuses held-out material only; a `blueprint_only` or `available_for_practice` exam unit can still become practice by the learner's own selection. Recommended default: keep (the spec lets an `available_for_practice` paper be practised, and the learner chose it).
4. **Items whose own source is held-out material** (`item_exam_status(...).held_out`), such as an `ingest-exam` question item from a held-out unit, stay ordinary practice for the scheduler. Recommended default: withhold them from routine serving in a follow-up (it changes which items Today serves, so it would take an algorithm successor).
5. **A reserved exam item exposed after its reservation** (read in the Reader while the exam waits) still sits in the exam. Recommended default: drop it at `start_exam` with a labelled note.

## 9. Commits

On `sources/exam-protection`, base main `e8d261405`:

| Commit | What |
|---|---|
| `b66faee43` | One exam predicate: `content.sources.exam_material`, read by every exam reader (corpus, resolver, leakage inventory, synthesis, cross-source spans, PF, remediation's fallback) |
| `dee02d5f9` | Close the sources merge's five exam gaps through the one predicate (post_attempt, cold administrations, picks, the import recheck, shown material) |
| `8e8f41d2a` | Fix four sources bugs: `action_disagreement`, migration 193's comment, the envelope's clock, harvest's rerank price |
| `02ca94d26` | Test the one exam predicate, the five gaps and the four bugs (each failed on the base) |
| `7c495260f` | Regenerate the DB and config references (no schema change; cited source lines moved) |
| `d7920405c` | Never explain held-out material in the Reader: Ask, its dialogue, presets and checks (§2.6), with three tests |
| `2cd7b7c70` | Regenerate the DB and config references again (cited lines moved in `tutor_qa.py` and `jobs.py`) |
| `118fba8a8` | Import the held-out predicate at module level in the Reader and the tutor (the first full run failed `test_architecture.py::test_function_local_domain_imports_match_the_frozen_edge_inventory` on four new function-local cross-domain edges) |
| `27a60d0fe` | Regenerate the DB and config references after the import move |
| this record | `docs/reviews/exam-protection.md` |

The implement step was interrupted by a machine reboot after `7c495260f`, with this record an uncommitted draft. The continuation reviewed the committed diff against the draft and the predicate's callers (a grep of every caller of `exam_material`, `exam_withheld`, `exam_exclusions`, `teaching_exclusions`, `held_out_spans`, `build_held_out_inventory`, `cold_administration_open`, `shown_items` and `refuse_exam_reserved_pick` matches §2), found the Reader's model contexts still showing held-out material to a model, closed that (§2.6), and ran the gate (§7).
