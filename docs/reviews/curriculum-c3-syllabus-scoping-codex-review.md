# Curriculum C3: Codex review, fix round 1

**Stage:** `curriculum-c3-syllabus-scoping`, branch `curriculum/c3-syllabus-scoping` (worktree `learnanything-dl2`).
**Reviewed:** `0d607bdfe9..ad846f246b` (Codex job `20261101-143049-pAlZKj`, gpt-6.1-sol; five Medium findings, no High).
**Stage record:** `docs/reviews/curriculum-c3-syllabus-scoping.md`.

No paid or live call was made: every model is a fake (`DeliverableFake`, `FakeServiceLLM`, C0a's
`CoverageJudgeFake`). The reference and catalog generators ran under `env -i` with an empty, existing `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No owner vault was opened, `~/.config/learnloop` was not read, and nothing
ran against `fixtures/linear_algebra`, `fixtures/probability` or `fixtures/arxiv_v2`. There is no migration, and
nothing changes persisted meaning (no successor).

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Past papers from unrelated subjects expand the deliverable | fixed | `9b98bccfa9` | `tests/test_curriculum_c3_codex_review.py`: `test_past_papers_are_read_per_subject_never_vault_wide`, `test_an_ambiguous_deliverable_reads_no_past_papers`, `test_a_syllabus_names_the_subject_and_another_subject_s_papers_stay_out`, `test_a_resolution_s_topics_name_the_subject_for_the_next_one` |
| F2 | Medium | Assessment mappings carried by facets disappear | fixed | `9b98bccfa9` | `test_a_mapping_carried_by_a_canonical_facet_counts` (positive: the citation is on the facet only), `test_a_held_out_unit_cited_by_a_facet_contributes_nothing` (held-out negative) |
| F3 | Medium | A syllabus can still become a practice item | fixed | `9b98bccfa9` | `test_a_syllabus_exercise_is_refused_before_any_model_call[syllabus_member, syllabus_unit_override]`, `test_a_syllabus_made_during_the_import_writes_nothing`, `test_the_reader_s_own_import_refuses_a_syllabus_before_any_model_call[syllabus_member, syllabus_unit_override]`, `test_the_one_write_refuses_a_syllabus_draft`, control `test_a_unit_override_leaves_the_rest_of_the_book_practice` |
| F4 | Medium | Past-paper mappings lack request-time protection revalidation | fixed | `9b98bccfa9` | `test_a_mapping_held_out_during_the_call_publishes_nothing` (marked during the call: nothing published, facet scope unchanged), `test_a_mapping_held_out_before_the_request_is_never_sent` (0 calls), control `test_a_change_that_leaves_the_sent_ids_practice_available_publishes` |
| F5 | Medium | The desktop cannot attach a syllabus as a scope input | fixed (picker) | `9b98bccfa9` | `apps/learnloop-tauri/src/screens/reader/DeliverableScope.syllabus.test.tsx` (the panel sends `{goalId, kind: "passage", extractionId, spanIds: []}`; error path; no picker without a syllabus; plain copy); backend `test_the_scope_view_offers_readable_syllabi_only`, `test_a_vault_without_a_syllabus_keeps_c0b_s_view` |
| claim | (review note) | "The fixture contains every kind of exam material" overstates it | fixed in part | `4d444edda0` | the fixture now also holds an exam-role unit override inside a book (`ext_mixed`), an outline exam pick outside every source set (`ext_outline`) and an unmarked alternate reading of a protected book (`ext_lay_alt`), each with its own sentinel; G-C1 and G-C2 cover them (`test_the_fixture_holds_every_kind_of_exam_material`, `test_gc1_…`, `test_gc2_a_syllabus_with_the_exam_role_is_refused_and_nothing_is_written`). Held-out *signals* are not built here: the exam predicate's own suite covers them (`tests/test_exam_protection.py`), and every reader here reads that one predicate. The fixture docstring says so |

**Fail-first evidence.** With the source fixes reverted on the WIP commit (the three import paths restored to
`ad846f246b`, the guard called without the prompt, the past-papers subjects made vault-wide, and the facet refs
dropped), **13 of the 18** new tests failed. The other five pass either way: the held-out facet negative, the two
controls, and the two F5 view tests, whose helper was left in place. With the fixes restored, all 18 pass.

## What changed

**F1, "of this subject" (§5.3).** A new function, `deliverables.deliverable_subjects(vault, repository, goal_id,
inputs)`, reads the deliverable's subject from its own explicit context. It takes the first of these that names
one:

1. the source sets that hold the readings of its passage inputs (a syllabus);
2. the subjects of the topics its newest resolution needs, when they are a single subject;
3. the vault's subject, when every active topic belongs to one.

Otherwise the context is ambiguous: the set is empty and no past paper contributes. `past_paper_learning_objects`
now requires the subjects. Only LOs of those subjects count. A cited unit whose source belongs to source sets
counts only when one of those sets is of those subjects. A source in no set (an outline pick) is judged by its
LO's subject. As a result, a physics paper never names `lo_force` for a linear-algebra deliverable. It also never
names an LA topic (`lo_eigen`) that only the physics paper tests. `build_scope_prompt` and `scope_view` read the
same subjects. A first resolution in a two-subject vault without a syllabus therefore sends v1's prompt. Once
that resolution names its topics, the next resolution reads that subject's papers. The stage's earlier decision 3
("vault-wide") is superseded.

**F2, facet-carried mappings.** `_learning_object_refs` returns the LO's own source refs plus those of its
canonical evidence facets. This is the Reader's mapping (`reader_progression.learning_objects_for_section`). The
block-level held-out filter applies to both sources of refs.

**F3, never practice.** In `exam_material`, a new `scope_only_material` resolves the material of `syllabus`
members and unit overrides through `role_material`, and a new `scope_only_among` tests keys against it. An
unreadable predicate answers True (fail closed). Independently of exam protection, the following refuse that
material:

- `source_exercise_import` refuses it at admission, on the complete statement region, before any model call.
- `source_exercise_import` refuses it again before the write-ahead, on the region and every block the draft
  cites, read from the vault on disk.
- `jobs.handle_reader_exercise_import` (the Reader's own import) refuses it before authoring, with error code
  `scope_only` and a plain message.
- `exercise_authoring.write_draft` refuses it as the shared publication backstop, raising
  `ExerciseAuthoringError`.

Needs and harvests go through `import_source_exercise`, so these checks cover them too.

**F4, request-time revalidation.** `ScopePrompt` now carries the past-papers ids it sent and the subjects they
were read for. `passage_guard(..., prompt=)` builds C0a's `CoverageGuard` whenever ids were sent, text-only inputs
included. Its `gate` reads `past_paper_learning_objects` again on the snapshot being admitted, before every
physical request and before the publication (the existing `guard.check("recording the scope")` under the
mutation lock). If any sent id no longer has a practice-available unit (for example, its unit was marked held out
meanwhile), every later request and the publication are refused (`protection_changed`, C0a's stale message), and
nothing is written. A change that leaves every sent id practice-available still publishes. The gate fails closed:
an unreadable predicate returns `[]`, which closes the gate.

**F5, the desktop's syllabus input.** `scope_view` now carries `syllabi`: the readings a `syllabus` member holds
whole that the scope library reads now (`deliverables.syllabus_documents`). The list excludes exam material and
readings held back, and is empty when the predicate cannot be read. The key is present only when the list is
non-empty, so a vault without a syllabus gets C0b's view exactly. In `DeliverableScopePanel`, a "from your
syllabus" picker sends `curriculum.set_scope` with `kind: "passage"`, the deliverable's id, the extraction and an
empty selection. The server then reads the whole syllabus and records its spans (§5.2). A Reader-selection action
was not added: the finding accepts either entry, and a picker covers the whole-document case without a new
selection menu.

## Gate (this step; the full suite runs once at landing)

- `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest, `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6`
  over the 90 files listed below: **2405 passed, 3 skipped, 2 xfailed** (8 min 27 s).
- Frontend (`apps/learnloop-tauri`, memory-capped): `npm install` ok; `npm run typecheck` clean; vitest `--maxWorkers=4` on
  `src/screens/reader/DeliverableScope.syllabus.test.tsx` (new), `src/components/syllabusRole.test.tsx`,
  `src/screens/reader/DeliverableSliceCard.test.tsx`, `src/copy/denyList.test.tsx`, `src/copy/denyList.phase4.test.tsx`:
  **5 files, 84 passed**; `npm run frontend:build` ok.
- Nothing under `src-tauri` changed (no cargo check needed).
- Desktop catalog: `desktop_generate.py` then `desktop_validate.py`: passed (297/297 TypeScript/TSX, reproducible
  byte for byte).
- DB/config reference: `db_generate_reference.py` then `db_validate_reference.py`: `errors: []`. The run
  regenerated only line citations that moved; the schema is unchanged.
- No migration and no DB/connection code changed, so the durability lane was not needed.
- C2 (notes) is still not merged here: this fix step does not merge. The stage record's open item stands (merge
  C2, then add `note_link_judge` to the G-C1 sweep).

Targeted files: `tests/test_ad_guard.py`, `tests/test_ad_projection.py`, `tests/test_architecture.py`, `tests/test_attach_to_family.py`, `tests/test_codex_output_schema.py`, `tests/test_compare_sources_keep.py`, `tests/test_curriculum_c0b_landing.py`, `tests/test_curriculum_c1_codex_review_fixes.py`, `tests/test_curriculum_c1_fix_round2.py`, `tests/test_curriculum_c1_fix_round3.py`, `tests/test_curriculum_c1_fix_round4.py`, `tests/test_curriculum_c1_fix_round5.py`, `tests/test_curriculum_c1_landing.py`, `tests/test_curriculum_c1_plan_follows_path.py`, `tests/test_curriculum_c1_round5_followups.py`, `tests/test_curriculum_c3_codex_review.py`, `tests/test_curriculum_c3_exam_scoping.py`, `tests/test_deliverable_codex_review.py`, `tests/test_deliverable_path.py`, `tests/test_deliverable_rpcs.py`, `tests/test_deliverable_scope.py`, `tests/test_desktop_rpc_contract.py`, `tests/test_diagnosis_input_provenance_landing.py`, `tests/test_discriminating_search.py`, `tests/test_exam_protection_identity.py`, `tests/test_exam_protection_landing.py`, `tests/test_exam_protection.py`, `tests/test_exam_protection_review.py`, `tests/test_exercise_arm.py`, `tests/test_exercise_authoring.py`, `tests/test_facet_locks_landing.py`, `tests/test_figures_codex_review.py`, `tests/test_figures_show_me_codex_review.py`, `tests/test_figures_show_me.py`, `tests/test_import_split_parity.py`, `tests/test_key_ladder_labels.py`, `tests/test_learner_pick_proposal.py`, `tests/test_library_ask_review.py`, `tests/test_library_exercises.py`, `tests/test_mcp_c1a_landing.py`, `tests/test_method_explicit_landing.py`, `tests/test_mobile_allowlist.py`, `tests/test_openrouter_client.py`, `tests/test_output_budget.py`, `tests/test_plan_first_transport_grant_scope.py`, `tests/test_plan_first_transport.py`, `tests/test_plan_follows_path.py`, `tests/test_practice_leakage.py`, `tests/test_reader_ca1_astra_codex_review.py`, `tests/test_reader_ca1_astra_fixes.py`, `tests/test_reader_ca1_astra_redesign.py`, `tests/test_reader_ca1_astra_rereview.py`, `tests/test_reader_ca1_codex_review.py`, `tests/test_reader_ca1_unicode_containment.py`, `tests/test_reader_digest_narrative.py`, `tests/test_reader_followups_rereview.py`, `tests/test_reader_pdf_selection.py`, `tests/test_reader_rw3b_protection.py`, `tests/test_reader_tutor_offers.py`, `tests/test_reading_hardening_landing.py`, `tests/test_reading_paths.py`, `tests/test_reference_check_binding.py`, `tests/test_reference_gate_imports.py`, `tests/test_required_method_authority.py`, `tests/test_required_method_items.py`, `tests/test_required_method_round3_rereview.py`, `tests/test_reread_safety_landing.py`, `tests/test_reread_safety.py`, `tests/test_router_card.py`, `tests/test_router_reader_activity.py`, `tests/test_rw4d_rw3b_composition.py`, `tests/test_scheduler_golden.py`, `tests/test_secondary_attach.py`, `tests/test_section_coverage.py`, `tests/test_section_coverage_review.py`, `tests/test_section_coverage_rpcs.py`, `tests/test_sidecar_reader.py`, `tests/test_sidecar_serializer_snapshot.py`, `tests/test_source_exercise_import.py`, `tests/test_source_exercise_rpcs.py`, `tests/test_source_first_needs.py`, `tests/test_source_roles.py`, `tests/test_source_service_spend_accounting.py`, `tests/test_source_service_spend_envelopes.py`, `tests/test_source_sets.py`, `tests/test_sources_merge_composition.py`, `tests/test_structured_transport_parity.py`, `tests/test_table_roles.py`, `tests/test_tracked_fixture_databases.py`, `tests/test_tutor_delivery_fixes.py`.

## Orchestrator scoped verify remainder, fixed

The orchestrator's scoped verify (job `20261101-150225-8ICy6I`) found F2–F5 closed and one remainder of F1:
"[P2] Subject fallback can still select unrelated papers — deliverables.py:901. The fallback counts subjects
represented by active LOs, rather than active vault subjects. With Math and Physics active, but only Math having
LOs, an unresolved Physics deliverable receives Math's past-paper mappings. Fix: permit this fallback only when
vault.subjects contains exactly one active subject; otherwise return no subjects."

Fix: the third step of `deliverables.deliverable_subjects` now reads `vault.subjects` and returns the subject
only when exactly one has `status: active`; otherwise the set is empty (no past paper contributes). The first two
steps (a syllabus's source sets; the single subject of the resolved topics) are unchanged.

Tests (`tests/test_curriculum_c3_codex_review.py`):
`test_a_second_active_subject_without_topics_leaves_an_unresolved_deliverable_without_past_papers` (linear algebra
with its LOs plus an active physics subject with none: an unresolved deliverable has no subjects, the prompt is
v1 with no `past_papers_test`, and the resolver's request carries none). It failed before the fix
(`frozenset({'linear-algebra'}) != frozenset()`) and passes after it. A control,
`test_a_paused_second_subject_keeps_the_only_active_subject_s_past_papers`, passes either way: a paused second
subject leaves linear algebra as the only active one. Targeted run over the C3, C0b and deliverable files:
119 passed.
