# Curriculum C2b (vault notes): Codex review round 5, fix step

Branch `curriculum/c2b-vault-notes` (worktree `learnanything-dl2`), reviewed at `a60bb14b3f` by
`codex-agent` job `20261102-004112-IbYkNL` (`gpt-6.1-sol`). Rounds 1-4 and the stage record are in
`docs/reviews/curriculum-c2b-vault-notes.md`. Reviewer rule (owner 2026-11-01): privacy/blindness
findings about learner text outside grading are not defects; only grade contamination, exam-material
leakage, evidence leakage, unapproved spend (or correctness).

## Review

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Existing links expose notes after their original anchor becomes protected | fixed | `313f196092` | `tests/test_notes_c2b_review5.py::test_c2b_r5_f1_a_linked_note_whose_anchor_became_protected_is_withheld_everywhere` (failed before the fix: the Lay note's sentinel and its source heading `5.1 Eigenvectors and eigenvalues` were still on `notes.path`, `notes.marks` and `notes.passages` after `hold_out("lay_eigen")`) |
| F2 | High | Note-derived text records incomplete source provenance | fixed | `b7ea2b2856`, `76262cc748` | `test_c2b_r5_f2_a_notes_reading_records_its_anchor_heading_and_every_section_span` and the negative test `test_c2b_r5_f2_protecting_an_input_the_old_record_omitted_withholds_the_text` (both failed with the pre-fix `provenance.py`: the gap's and the belief candidate's records named only `ext_book/s2`, so `TextGuard.past.source_reason` released them after the note's own Lay section was held out); `test_c2b_r5_f2_the_note_gate_refuses_once_a_bound_source_is_protected` |
| F3 | Medium | Meaning search bypasses the vault's selected local embedding stack | rejected (claim corrected) | `76262cc748` (docs only) | See below: outside the stage, no protection/spend defect |

### F1 (fixed)

`note_links.effective_rows` (the one rule for which links stand) now takes the vault and, by
default, drops every snapshot whose note is a Reader annotation anchored beside protected material
now (`withhold_protected`: `VN.protected_keys` on every note key, C0a's predicate read now,
unreadable = every annotation withheld). `effective`, and so `for_goal`, `marks`, `for_passages` and
Compare's `take_text`, all deliver through it. The ledger keeps its rows (no delete; the test checks
the `learner_notes` and `learner_note_links` counts). C5's `note_gaps.linked_notes` passes
`withhold=False` on purpose: `note_text` already refuses such a note by name (`NoteWithheld`), so its
job is skipped as withheld rather than as unlinked (behaviour unchanged).

API change for parallel stages (TE1's `read_note`): `NL.effective(repository, rows, *, vault, goal_id=None)`
and `NL.effective_rows(repository, rows, *, vault, goal_id=None, withhold=True)`; `vault` is a
required keyword (a caller that forgets it fails loudly instead of skipping the check).

### F2 (fixed)

When a note's reading is prepared, `note_gaps.note_text` now freezes every book span the text and
context carry text from as `source_refs`:

* the annotation's anchors (`VN.anchor_sources`: every anchor version it ever had, since the
  snapshot was taken from one of them, with the header blocks of their sections, whose text is the
  note's heading; an anchor version with no segments names its whole reading);
* every span of each linked section read (`note_gaps._section_spans`: the section's own spans from
  the reading, which include the header that gives the passage's title and every block `SC.peek`
  can supply; a ref keeps no `section_id`, so the section is recorded by its spans).

They travel on the prepared text as `LearnerText.bound_sources` (never sent, never checkpointed),
`provenance.note_record` writes them into the gap's record and, through `reading_record`, into a
belief candidate's, and `NoteGate`'s refusal revalidates them against the protection read now
(`note_gaps._sources_out`). Section spans are read apart from `_section_lead` so the lead's existing
test seam (`test_step0_*`) is unchanged.

### F3 (rejected, with the claim corrected)

The local stack (`embedding.local`, `embedding.source_space.default = "local:grouped"`) is the
contextual pplx v2 9B *document* space: book extractions windowed and indexed by the GPU batch worker
(`local_embeddings.worker`, the `local_source_index` job), queried through the adopted query student.
Notes are not extractions; putting them in that space needs a new window/record type for the GPU
worker, its canaries and coverage, and a decision on whether to embed notes with the 9B teacher at
all. That is a retrieval-architecture change, not this stage's (owner's scope for C2b: the vault's own
notes, words and meaning search, tend removed, past papers option A).

It is not a protection, evidence or grading defect, and the spend is not unapproved: the hosted path
runs only under the owner's own `embedding.enabled` and `embedding.backfill_enabled` (the same
switches that already authorize hosted source backfills and the resolver's hosted coverage
completion when the local default is selected), capped per run and priced. With hosted embeddings
off the picker shows exact words with an honest label (`meaning: false`), which is the stated
behaviour. Other non-span meaning consumers (C0a's coverage query, Compare) also embed through the
hosted `queries.embed_query_texts`.

The reviewer is right that the stage's claim "the same model, route, query path as the tutor's
library retrieval" overstated it. Corrected in the spec (§10.5) and the `vault_notes` / `note_links`
module docs: the vault's hosted embedding model and route (`embedding.model`) through the tutor's
hosted query path; the local contextual space indexes book extractions only and does not cover notes.
Recorded as an open item for the owner (below).

### Claims that don't hold (reviewer)

* "Exam protection kept": now holds for existing link delivery (F1) and persisted note-derived text
  (F2); the spec's §10.5 protection bullet says both.
* "Same embedding stack as the tutor's library retrieval": corrected (F3).

## Gate

Owner rule 2026-10-17: no full suite, whole durability lane or whole vitest here. Every pytest ran
inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at `-n 6`, one
run at a time, `TMPDIR` in the stage scratch directory.

* `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`: done.
* `uv run lint-imports --no-cache`: **40 kept, 0 broken**.
* New tests alone (`tests/test_notes_c2b_review5.py`): **4 passed**; F1's and F2's first two failed
  before their fixes (F2 checked by restoring the pre-fix `provenance.py` for one run: 2 failed).
* Targeted set, first run: 1364 passed, 1 failed, 2 xfailed. The failure
  (`test_notes_as_learner_text.py::test_step0_a_checkpointed_note_reading_is_never_reused_after_its_inputs_change`)
  was this fix's: `note_text` had stopped calling `_section_lead`, the test's seam; section spans
  are now read separately (`76262cc748`). Notes files rerun (`test_notes_c2b_review5.py`,
  `test_notes_as_learner_text.py`, `test_notes_linked.py`, `test_notes_vault_search.py`):
  **79 passed**.
* Targeted set, final run (61 files, below): **1365 passed, 0 failed, 2 xfailed** (5 min 28 s).
* No migration, schema, DB/connection, config key, frontend or `src-tauri` change: no durability
  tests, npm, vitest or cargo needed. The generated DB/config references cite source lines of
  `note_links.py`, so `db_validate_reference.py` first reported one stale cite
  (`notes.max_candidates` -> `note_links.py:565`); `db_generate_reference.py` then
  `db_validate_reference.py`: errors `[]` (scripts run under `env -i` with empty, existing
  HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR).
* No live or paid call; every model and embedding client a fake. Spend: $0.

Targeted test files (every file naming `note_links`, `vault_notes`, `note_gaps`, `notes_fixtures`,
`learner_note`, the text-gaps provenance/contract/sources/pipeline/jobs or `LearnerText(`, every
file exercising write-time provenance or `TextGuard`, minus migration/schema files that only name
the table, plus the contract tests):
`test_architecture.py`, `test_chatgpt_plan_landing.py`, `test_codex_lockdown_round3.py`, `test_concepts.py`, `test_curriculum_c2b_past_papers.py`, `test_curriculum_c3_codex_review.py`, `test_curriculum_c3_exam_scoping.py`, `test_desktop_rpc_contract.py`, `test_diagnosis_input_provenance_landing.py`, `test_diagnosis_input_provenance.py`, `test_diagnostic_augmentation.py`, `test_e0_review_round8.py`, `test_figure_predictions.py`, `test_figure_revisions.py`, `test_figure_rich_review_fixes.py`, `test_figure_rich_rpc.py`, `test_figures_codex_review.py`, `test_figures_fix_round2.py`, `test_figures_fix_round3.py`, `test_figures_fix_round4.py`, `test_figures_rpc.py`, `test_figures_scope_redesign.py`, `test_figures_show_me_codex_review.py`, `test_figures_show_me.py`, `test_figures_switch_off.py`, `test_forecast_receipts_landing.py`, `test_held_grade_composition.py`, `test_hint_feedback_texts.py`, `test_hint_h2b_review.py`, `test_judge_routes.py`, `test_learner_data_relax_2.py`, `test_learner_text_gaps_composition.py`, `test_learner_text_gaps_flow.py`, `test_learner_text_gaps.py`, `test_learner_text_gaps_rereview.py`, `test_learner_text_gaps_review.py`, `test_learner_text_source_widening.py`, `test_mcp_c1a_landing.py`, `test_mcp_c1a_narrow.py`, `test_mobile_allowlist.py`, `test_notes_as_learner_text.py`, `test_notes_c2b_review5.py`, `test_notes_linked.py`, `test_notes_never_read.py`, `test_notes_vault_search.py`, `test_reader_ca2_fix_orchestrator.py`, `test_reader_formative_texts.py`, `test_reader_rw1b_review.py`, `test_reader_rw3b_review_fixes.py`, `test_reader_tutor_switch_off.py`, `test_reading_paths.py`, `test_regrade_contract_successor.py`, `test_required_method_round3_review.py`, `test_sidecar_close_cancels_jobs.py`, `test_sketch_service.py`, `test_t6_followup_composition.py`, `test_table_roles.py`, `test_tier1_decider.py`, `test_tracked_fixture_databases.py`, `test_ux_phase4_landing.py`, `test_workbench_text_gaps.py`.

## Open items

* F3: whether notes should join the local contextual space when the owner selects it as the source
  default (a GPU worker record type for notes, or a decision that notes stay on the hosted model).
  Until then notes' meaning search is the hosted space, under `embedding.enabled` /
  `backfill_enabled`.
* Round 4 F2's accepted residual (a retry inside one embedding batch is not re-gated) stands.
* Parallel stages: `NL.effective` / `NL.effective_rows` now require `vault=` (F1);
  `LearnerText.bound_sources` is new (F2).

## Re-review of round 5 (Codex job 20261102-012346-6YalUi)

Verdict REOPENED: F1 reopened, F2 confirmed fixed, no new defects in the fix commits.

| id | severity | title | verdict | commit | test / reason |
|----|----------|-------|---------|--------|---------------|
| F1 | High | Older snapshot anchors went unchecked (delivery checked only the newest anchor) | fixed | `f2aa9b0347` (+ references `1cb79ddb61`) | `tests/test_notes_c2b_review5.py::test_c2b_r5_rereview_f1_a_snapshot_from_an_older_anchor_is_withheld_once_that_anchor_is_protected`, `::test_c2b_r5_rereview_f1_a_notes_reading_refuses_a_snapshot_from_a_now_protected_older_anchor` (both failed before the fix) |
| F2 | High | Complete provenance reaches downstream guards | confirmed fixed (round 5) | `b7ea2b2856` | no change |

**F1 reproduced.** Steps: link a Reader note written beside Lay's eigenvector section, move it by hand
onto ext_book s3 (unprotected; `manual_anchor` adds a newer anchor version and keeps the old one),
then hold out `lay_eigen`. Before the fix, path lines, marks and Compare's band still delivered
the stored snapshot, with the note's sentinel and Lay's header as its heading.
`VN.protected_keys` returned `set()` because the newest anchor is unprotected. The gap reading's
`note_text` also read the snapshot instead of raising `NoteWithheld`. (The downstream request guard
already refused it, through F2's `bound_sources`.)

**Fix.** A stored snapshot records no anchor of its own, and one snapshot row can be reused for
identical content. So the code now checks every anchor version the annotation ever had, plus each
section header, the same history that `anchor_sources` freezes for a gap reading. This is the
conservative option the finding suggested.
* `vault_notes.snapshot_protected_keys` (new, public) checks every anchor version.
  `protected_keys` is unchanged: it judges the note as it reads now, so it stays right for current
  text sent to embedding batches and to `NotesGuard`. Both share `_protected`. `_segments` and
  `_anchors` replace the copied segment-reading loop, and `anchor_sources` uses `_segments` too.
* `note_links.withhold_protected` uses `snapshot_protected_keys`. That covers every delivery
  boundary through `effective_rows` (path lines, marks, Compare band and take text).
* `note_gaps.note_text` calls `VN.beside_protected(..., every_anchor=True)`.
  `beside_protected` gains the keyword-only `every_anchor=False`, so other callers keep their
  current behaviour. One test's monkeypatch lambda in `test_notes_as_learner_text.py` now
  forwards `**kw`.
* Ledger rows are kept: delivery withholds them and nothing is deleted.

Accepted effect: a note that was ever anchored beside material that is protected now is withheld
from delivery and from gap reading, even after it moves elsewhere, because a snapshot cannot say
which anchor it came from. The learner's own text is still listed in the Reader. No migration.

Interfaces for parallel stages: `VN.snapshot_protected_keys` is new and
`VN.beside_protected(..., every_anchor=)` gained a keyword. The `note_links` and `learner_notes`
APIs are unchanged.

### Gate (re-review)

Every pytest ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`,
at `-n 6` at most, one run at a time, with `TMPDIR` in the stage scratch directory.

* `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`: done.
* `uv run lint-imports --no-cache`: **40 kept, 0 broken**.
* New tests before the fix: both **failed** (sentinel and Lay header delivered; `NoteWithheld` not
  raised). After the fix, `tests/test_notes_c2b_review5.py`: **6 passed**.
* Targeted run 1 (15 files): `test_notes_c2b_review5.py`, `test_notes_as_learner_text.py`,
  `test_notes_linked.py`, `test_notes_never_read.py`, `test_notes_vault_search.py`,
  `test_curriculum_c2b_past_papers.py`, `test_missing_vocabulary_notes.py`,
  `test_learner_text_gaps.py`, `test_curriculum_c3_exam_scoping.py`, `test_figures_switch_off.py`,
  `test_reader_tutor_switch_off.py`, `test_reading_paths.py`, `test_annotations.py`,
  `test_architecture.py`, `test_learner_notes_vault_origin_migration.py`: **244 passed, 0 failed**.
* Targeted run 2 (13 files, text-gaps, provenance and contract tests):
  `test_learner_text_gaps_composition.py`, `test_learner_text_gaps_flow.py`,
  `test_learner_text_gaps_rereview.py`, `test_learner_text_gaps_review.py`,
  `test_learner_text_source_widening.py`, `test_diagnosis_input_provenance.py`,
  `test_diagnosis_input_provenance_landing.py`, `test_workbench_text_gaps.py`,
  `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`, `test_table_roles.py`,
  `test_tracked_fixture_databases.py`, `test_compare_sources_keep.py`: **574 passed, 0 failed,
  2 xfailed**.
* `db_generate_reference.py` then `db_validate_reference.py`, under `env -i` with an empty,
  existing HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR: errors `[]`. The only content change is
  the new test file in the source lists; the rest is commit stamps.
* There was no migration, schema, DB/connection, config-key, frontend or `src-tauri` change, so no
  durability tests, npm, vitest or cargo were needed.
* No live or paid calls were made; every model is a fake. Spend: $0.
