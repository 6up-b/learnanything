# Curriculum C3: exam scoping from a syllabus

**Stage:** `curriculum-c3-syllabus-scoping`, branch `curriculum/c3-syllabus-scoping` (worktree `learnanything-dl2`),
base `0d607bdfe9` (main: mvp-0.40, migration head 228). **Spec:** `docs/specs/spec_deliverable_curriculum_v1.md`
§9 and the §12 C3 row (Q2, decided 2026-10-25). **No paid or live call was made**: every model is a fake
(`DeliverableFake`, C0a's `CoverageJudgeFake`); every ad-hoc script (fingerprint recompute check, CLI help
snapshot, reference generators) ran under `env -i` with an empty, existing `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR` (`scratchpad/curriculum-c3-syllabus-scoping/iso.sh`). No owner vault was opened,
`~/.config/learnloop` was not read, and nothing ran against `fixtures/linear_algebra`, `fixtures/probability` or
`fixtures/arxiv_v2`. **No migration** (source roles are open strings in `source_sets.yaml` and
`source_unit_selections.role_override` has no CHECK). **No successor: no scoring, scheduling, projection or
serving change** (scoping display and proposals only).

## What was built

| Piece | Where |
|---|---|
| The `syllabus` role: in `KNOWN_ROLES`, authority matrix `(False, True)` (assessment alignment only, never semantic authority), default inventory profile `assessment`, and a new `SCOPE_ONLY_ROLES` / `is_scope_only_role`. Not in `ASSESSMENT_ONLY_ROLES`, so the exam predicate never treats it as exam material (never protected) | `content/sources/role_authority.py` |
| Never taught from: a role without semantic authority is already in `corpus.teaching_exclusions` (tutor, Reader Ask, cues, workbench, C0a's library). `teaching_exclusions` and `section_coverage.read_protection` gain `readable_roles` (default empty: every existing caller unchanged); the `Protection` carries it, and `Library.refreshed` and `CoverageGuard` read protection again with the same roles | `source_retrieval/corpus.py`, `source_retrieval/section_coverage.py` |
| Never a coverage candidate, primary or alternate, never a correspondent: C0a's library (the only source of coverage candidates and path sections) passes no readable role, so a syllabus is `left_out` | unchanged C0a code; pinned by tests |
| Never a generation source: `source_set_synthesis._collect_inputs` (bootstrap and append share it) skips a syllabus unit after the exam check (exam spans still feed the leakage gate), whatever inventory a manual run made; the desktop's `build_study_map` payload never inventories syllabus units (a syllabus-only member is skipped rather than refused) | `content/synthesis/source_set_synthesis.py`, `learnloop_sidecar/handlers/ingest.py` |
| A syllabus passage is a scope input: `deliverables.scope_library` is C0a's library with `readable_roles={"syllabus"}`; `passage_texts` and `passage_guard` read it, so the exam predicate, held-back readings and every other non-teaching role refuse exactly as before, and the request-time guard reads protection again with the syllabus role (a syllabus given the exam role during the call keeps nothing). A `passage` input with no selection reads a syllabus whole ("a whole short document", §5.2), its spans recorded explicitly on the row; any other reading still needs a selection | `source_retrieval/deliverables.py` |
| Past papers (§9.2): `past_paper_learning_objects` lists, by id, the active LOs whose provenance cites a block of practice-available assessment material: exam material (members, exam units, outline exam picks) or problem-set material (members, unit overrides) **not** in the held-out partition (`held_out_evaluation` units, readings held back until marked, held-out signals). A ref naming an extraction without a block counts only when that extraction is assessment material whole with nothing held out in it. An unreadable predicate contributes nothing (fail closed). No unit text is read | `source_retrieval/deliverables.py` |
| The resolver reads it as `past_papers_test` (ids) with one more instruction sentence, prompt version `deliverable_scope_resolver.v2`, recorded on the resolution row, the ledger verdict and the route's receipt. **Off, or with nothing to contribute, the prompt is v1 byte for byte** (no key, same text, same state key) | `source_retrieval/deliverables.py` (`build_scope_prompt`, `resolve`) |
| The scope view marks the needed topics the past papers test (`on_past_papers`, present only with the switch on); the desktop's scope panel shows *· on your past papers* with a tooltip saying only which topics were read, never questions | `deliverables.scope_view`; `screens/reader/DeliverableScope.tsx`, `api/dto.ts` |
| Kill switch `[curriculum] exam_units_in_scope` (default true; frictionless default, live behind a switch), classified (`structural`, `operational`) in the parameter registry; every defaults snapshot mvp-0.9 … mvp-0.40 recomputed (dropping the key reproduces every earlier value: 31/31) | `config/schema.py`, `params/parameter_registry.py`, `config/template.py` |
| Role surfaces with honest labels: the CLI `source-set add --role` help names the known roles and what a syllabus does (CLI help snapshot regenerated: one entry); the desktop's two role pickers (collection membership, the outline's role pick) offer `syllabus` and, when it is chosen, say "used only to scope what your deliverables need — never taught from, never practice, never protected (don't give it the exam role, or LearnLoop hides it whole)"; `roleLabel("syllabus")`. The RPCs (`upsert_source_set`, `save_unit_selection`'s known-role check) needed nothing beyond `KNOWN_ROLES` | `cli/source_set.py`, `components/AddToCollection.tsx`, `components/OutlineAndPlan.tsx`, `components/RewordConfirms.tsx` |
| Spec §9.5 "as built" note; desktop catalog and DB/config reference regenerated (prose leaf counts 1095 → 1096) | `docs/specs/spec_deliverable_curriculum_v1.md`, `docs/learnloop-architecture-vault/` |

## The fixture (`tests/exam_scope_fixtures.py`)

C0b's deliverable vault (book `ext_book`; exam-role source `ext_exam`; book `ext_lay` with the held-out unit
`lay_held`) plus a past paper `ext_paper` (role `exam`: `paper_q1` `available_for_practice`, `paper_q2`
`blueprint_only`, `paper_q3` `held_out_evaluation`), a problem set `ext_pset` (`pset_1` unmarked, `pset_2`
held out), a syllabus with the `syllabus` role `ext_syl`, a syllabus with the `exam` role `ext_syl_exam`, and
three protected items on `lo_matrices` (exam-reserved, made from the held-out unit, made from a
practice-available exam unit). Every exam text carries its own sentinel; the syllabus carries `SYLLABUSMARKER`,
which only the scope resolver may read. LO provenance: `lo_matrices` → `paper_q1`, `lo_vectors` → `paper_q2`,
`lo_inner` → `pset_1`, `lo_det` → the exam-role source (all practice-available); `lo_spectral` → only held-out
material; `lo_eigen` → only the book.

## Gates

| Gate | Test (`tests/test_curriculum_c3_exam_scoping.py`) |
|---|---|
| G-C1: no `section_coverage_judge`, `deliverable_scope_resolver` or `deliverable_path_judge` request captured by `StructuredClientFake` contains any sentinel (or its first word); the syllabus reaches the resolver only; no path row, path view, Guide slice, readiness view or correspondent names an exam reading, the syllabus, or the held-out section of `ext_lay` | `test_gc1_no_request_correspondent_path_row_or_slice_names_exam_material`, `test_a_syllabus_never_teaches_and_is_never_a_coverage_candidate`, `test_past_papers_contribute_their_lo_ids_only_and_held_out_units_nothing` |
| G-C1 for `note_link_judge` | `test_gc1_note_link_judge_requests_carry_no_exam_material_from_sources` (added at the landing, after C2 merged) |
| G-C2: a syllabus span with the exam role is refused as a scope input (a selection and the whole document), as is every other kind of exam material, and nothing is written; a syllabus made exam after it was added is never sent (0 calls); made exam during the call, nothing is kept | `test_gc2_a_syllabus_with_the_exam_role_is_refused_and_nothing_is_written`, `test_gc2_the_same_syllabus_given_the_exam_role_is_refused`, `test_gc2_a_syllabus_made_exam_after_it_was_added_is_never_sent`, `test_a_syllabus_made_exam_during_the_call_keeps_nothing` |
| G-C3: readiness checks never pick an exam-reserved item, an item made from a held-out unit or one made from exam material | `test_gc3_readiness_checks_never_pick_exam_reserved_or_held_out_items` |
| Off is C0b byte for byte: with the switch off the past-papers reader is never called and the prompt equals the one rendered with an empty list (text, state key, version v1); the stored resolution is v1; the view carries no `on_past_papers` | `test_off_is_c0b_byte_for_byte` |
| Held-out units contribute nothing, at once when a unit is held out later | `test_past_papers_contribute_their_lo_ids_only_and_held_out_units_nothing` |
| A syllabus is never inventoried for a study map | `test_a_syllabus_is_never_inventoried_for_a_study_map` |

Fail-first evidence: with `scope_library`'s readable role and the synthesis skip reverted, 6 of the 18 tests fail
(the syllabus passage, whole-document, mid-call, after-added, synthesis and G-C1 tests); restored, 18 pass.

## Decisions taken here (open to the owner or the landing)

1. **"Practice-available" is the predicate's partition**: assessment material that is not held out. A unit with
   no use-mode mark is `blueprint_only` by `DEFAULT_EXAM_USE_MODE`, so an exam-role source with no marks
   (`ext_exam`) contributes. Rule 4 holds a protected book's unmarked readings back whole, so they contribute
   nothing.
2. **The mapping is LO provenance at block level** (`exam_material.source_ref_keys`), not section-level
   `learning_objects_for_section`: a section can hold a practice unit and a held-out unit, and a section-level
   mapping would let the held-out one name an LO. AD §9.5 maps units the same way ("the unit's own facet
   mapping").
3. **Vault-wide, not per subject.** The spec says "of this subject"; the deliverable's subject is not known before
   its scope is resolved, and the resolver already reads every active LO of the vault. The ids are the vault's own
   topics, so nothing new leaves the machine.
4. **A new prompt version only when the list is sent** (`v2`), so a vault with no past papers, or the switch off,
   keeps v1's text and state key exactly, and no existing resolution re-resolves unless an input is added.
5. **The syllabus's inventory profile is `assessment`** (for a manual `learnloop inventory`); no build inventories
   it. Its held-out signals mark nothing (only exam-role runs mark).
6. **Compare and `find_sources` keep their own library rule** (exam material out, other roles in, as for notes and
   problem sets today). A syllabus could be a compare counterpart; that is display, not teaching grounding, and
   was left as is (proportionate bar). The tutor, Reader Ask, cues and teacher read `teaching_exclusions`, which
   leaves it out.
7. A problem-set or notes passage is still refused as a scope input with C0b's exam wording; only the syllabus
   role is lifted.

## Gate run (this step; the full suite runs once at landing)

- `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest, `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6`
  over the 86 files listed below: **1765 passed, 12 skipped, 3 xfailed** (20 min 29 s). Files: `tests/test_ad23_successor.py`, `tests/test_architecture.py`, `tests/test_attempt_content_state_successor.py`, `tests/test_batch3_landing.py`, `tests/test_build_study_map_routing.py`, `tests/test_cli_help_snapshot.py`, `tests/test_cold_retry_reschedule.py`, `tests/test_config_refactor.py`, `tests/test_constraint_engine.py`, `tests/test_coordinated_migrations.py`, `tests/test_coverage_on_extract.py`, `tests/test_curriculum_c0b_landing.py`, `tests/test_curriculum_c1_codex_review_fixes.py`, `tests/test_curriculum_c1_fix_round2.py`, `tests/test_curriculum_c1_fix_round3.py`, `tests/test_curriculum_c1_fix_round4.py`, `tests/test_curriculum_c1_fix_round5.py`, `tests/test_curriculum_c1_landing.py`, `tests/test_curriculum_c1_plan_follows_path.py`, `tests/test_curriculum_c1_round5_followups.py`, `tests/test_curriculum_c3_exam_scoping.py`, `tests/test_deliverable_codex_review.py`, `tests/test_deliverable_path.py`, `tests/test_deliverable_rpcs.py`, `tests/test_deliverable_scope.py`, `tests/test_desktop_rpc_contract.py`, `tests/test_diagnosis_input_provenance.py`, `tests/test_exam_protection_identity.py`, `tests/test_exam_protection.py`, `tests/test_exam_readiness_and_conflict.py`, `tests/test_facet_authority.py`, `tests/test_facet_authority_rereview.py`, `tests/test_facet_authority_review.py`, `tests/test_field_workbench_signals.py`, `tests/test_intent_codex_rereview.py`, `tests/test_inventory_merge_parallel.py`, `tests/test_judge_routes.py`, `tests/test_learner_report_superseded.py`, `tests/test_lp_claim_fixes.py`, `tests/test_method_explicit_upgrade.py`, `tests/test_mobile_allowlist.py`, `tests/test_mvp010_upgrade.py`, `tests/test_mvp011_upgrade.py`, `tests/test_mvp013_upgrade.py`, `tests/test_mvp014_upgrade.py`, `tests/test_mvp015_upgrade.py`, `tests/test_mvp016_upgrade.py`, `tests/test_mvp017_upgrade.py`, `tests/test_mvp018_upgrade.py`, `tests/test_mvp020_upgrade.py`, `tests/test_mvp021_upgrade.py`, `tests/test_mvp022_upgrade.py`, `tests/test_mvp023_upgrade.py`, `tests/test_mvp024_upgrade.py`, `tests/test_plan_determinism.py`, `tests/test_plan_follows_path.py`, `tests/test_practice_leakage.py`, `tests/test_quick_add.py`, `tests/test_reader_ca2_one_ask.py`, `tests/test_reader_ca5a_find_section.py`, `tests/test_reader_ca5_also_in_books.py`, `tests/test_reader_ca6_side_by_side.py`, `tests/test_reader_followups_successor.py`, `tests/test_reader_rw3b_protection.py`, `tests/test_reading_step_switch.py`, `tests/test_rebuild_equivalence_review.py`, `tests/test_recurrence_commands.py`, `tests/test_registry_audit.py`, `tests/test_regrade_contract_successor.py`, `tests/test_rw4d_rw3b_composition.py`, `tests/test_section_coverage.py`, `tests/test_section_coverage_review.py`, `tests/test_section_coverage_rpcs.py`, `tests/test_serve_eligibility_review.py`, `tests/test_sidecar_ingest_m3.py`, `tests/test_sidecar_serializer_snapshot.py`, `tests/test_sidecar_synthesis.py`, `tests/test_source_append.py`, `tests/test_source_inventory.py`, `tests/test_source_retrieval_guards.py`, `tests/test_source_roles.py`, `tests/test_source_sets.py`, `tests/test_source_set_synthesis.py`, `tests/test_table_roles.py`, `tests/test_tracked_fixture_databases.py`.
- Frontend (`apps/learnloop-tauri`, memory-capped): `npm install` ok; `npm run typecheck` clean; vitest
  `--maxWorkers=4` on `src/components/syllabusRole.test.tsx` (new), `AddToCollection.test.tsx`,
  `OutlineAndPlan.escape.test.tsx`, `RewordConfirms.test.tsx`, `screens/reader/DeliverableSliceCard.test.tsx`:
  **5 files, 35 passed**; `src/copy/denyList.test.tsx`, `denyList.phase4.test.tsx`: **2 files, 57 passed**;
  `npm run frontend:build` ok. Nothing under `src-tauri` changed (no cargo check needed).
- Desktop catalog: `desktop_generate.py` then `desktop_validate.py`: passed (297/297, reproducible).
- DB/config reference: `db_generate_reference.py` then `db_validate_reference.py`: `errors: []`.
- No migration, no DB/connection code changed: no durability lane needed.
- Main moved to `6318d46cfe` during the stage (one RW5d P2 probe record); C2 is still not on main, so nothing was merged.

## Open items

- **C2 (notes) lands first** (in `learnanything-ad1`). When it is on main, merge it here and add
  `note_link_judge` to the G-C1 sweep (link notes for the fixture's deliverable path with C2's fake and assert no
  sentinel in its requests). Expected conflicts: `config/template.py` (every snapshot: recompute all with
  `defaults_fingerprint_for_version`, both keys present) and `section_coverage.CoverageGuard._refusal` (C2
  composes `also` hooks there; keep `readable_roles=self._library.protection.readable_roles` on its
  `read_protection` call), plus the regenerated references.
- The owner may want the past-papers list per subject once goals carry a subject or source sets (AD §16's
  deferred `source_set_ids`).

## Landing onto main

Branch `curriculum/c3-syllabus-scoping` (worktree `learnanything-dl2`), from tip `855e3b43d3`. Main was
`e9693b3700` at the start and `7401484f91` at the end. **No paid or live call was made.** Every model was a fake.
Every Python/CLI process ran under `env -i` with an empty, existing `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`, with `TMPDIR` outside the worktree. The real `tend` and the owner's notes were never
touched; only C2's fake `tend` over synthetic notes in tmp was used. Only the mvp035 owner copies were opened,
through fresh backup-API copies. No migration (C3 has none; the head stays main's 229).

### Step 0: orchestrator scoped verify remainder (F1), fixed (`a41eeb95d9`)

The third fallback of `deliverables.deliverable_subjects` counted the subjects named by active LOs. Now it reads
`vault.subjects`, and only when exactly one subject is `status: active`; otherwise it returns no subjects, so no
past paper contributes. Fail-first test:
`test_a_second_active_subject_without_topics_leaves_an_unresolved_deliverable_without_past_papers` (linear algebra
with LOs, plus an active physics subject with none). It failed before the fix (`frozenset({'linear-algebra'})`)
and passes after it. A control (a paused second subject keeps the past papers) passes either way. This is recorded
in the codex-review record as "Orchestrator scoped verify remainder, fixed".

### Merges

| Commit | What |
|---|---|
| `7e007245e5` | Merge of main `e9693b3700` (curriculum C2 notes, migration 229 / `migration_head_229`, `NotesGuard` composed into `CoverageGuard` with C1's gate; RW5d P2b; Reader follow-ups; facet fix). Conflicts: `config/template.py` (31 snapshot hunks: C2's note and C3's note both kept; every fingerprint recomputed with `defaults_fingerprint_for_version` after clearing `.pyc`, 31 changed; a second pass changed 0); `section_coverage.CoverageGuard._refusal` (main's `also`/`gate` hooks and `(reason, exception)` refusals kept; `read_protection(..., readable_roles=self._library.protection.readable_roles)` on the same snapshot); 444 generated reference notes (main's side, then regenerated). The hand-kept prose leaf count went 1104 → 1105 (C3's `exam_units_in_scope`) in `Configuration.md` and `Database.md`. After that: `db_validate_reference` errors [], desktop catalog 299 TS / 291 entry-build / ACTIVE 304 reproducible, vault valid. A targeted run (C3, notes, section coverage, C1 landing, config, source roles, judge routes, CLI help, registry; 13 files) gave **286 passed**. |
| `57a051a414` | The `note_link_judge` G-C1 sweep (below). |
| `e8aaea0f12` | Merge of main `7401484f91` (Reader follow-ups Nov 1b: `figures/labels.py`, the figures service's `worded_row`, `openai_chat` `trust_env=False`, no "no such passage" pins on fresh compare rows). Conflicts: 440 generated reference notes only (main's side, then regenerated: `db_validate_reference` errors [], desktop catalog reproducible at 299 / ACTIVE 304, vault valid). `parameter_registry.py` auto-merged (`figure_labels` beside C3's switch); the 31 fingerprints already matched (0 changes). **No manual Python resolution**, so the full suite was not rerun. A targeted run (main's five new test files plus registry audit, both C3 files, config, compare keep, figures show-me, OpenRouter client, Codex lockdown round 3, notes linked; 14 files) gave **392 passed**. |

### G-C1 for `note_link_judge` (`tests/test_curriculum_c3_exam_scoping.py`)

`test_gc1_note_link_judge_requests_carry_no_exam_material_from_sources` runs on the exam-scope fixture:

- Setup: coverage is judged for every LO; the deliverable has the syllabus passage as an input; the scope and the
  path are judged with `DeliverableFake`.
- Linking: `note_links.link_goal` runs with C2's `NoteLinkFake` and C2's fake `tend` over three synthetic notes.
  One is a Pocket Notes page that copies the fixture's practice-available past-paper question (with its
  sentinel) verbatim.

The test asserts:

- At least two judge requests are made, so the sweep is not vacuous.
- Strip each request of the learner's own `notes[].text`. What remains (topic title and statement; passage book,
  section and opening; note titles and headings) contains none of the fixture's sentinels or sentinel words, no
  `SYLLABUSMARKER`, no extraction that is never on a path, and no exam or syllabus section title.
- The copied note reaches the judge at least once, and its quote appears only in its own text. The other notes
  carry no sentinel.
- Every `tend` argv (the queries) carries no sentinel and no syllabus marker.
- Every stored link points at a `deliverable_path_sections` row and never at exam material.

Fail check: with `note_links._lead` temporarily prefixed with a sentinel, the test failed (`AssertionError:
PAPERPRACTICESENTINEL`). The change was reverted.

### Gate

| Step | Tree | Result |
|---|---|---|
| `uv run lint-imports --no-cache` | `57a051a414`, `e8aaea0f12` | **37 kept, 0 broken** each time |
| Full pytest (`flock /tmp/learnloop-fullsuite.lock systemd-run --user --scope --quiet -p MemoryMax=10G -p MemorySwapMax=2G -- <env -i> uv run --no-sync pytest -n 8 -p no:cacheprovider --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml=…`) | `57a051a414` | **23396 passed, 90 skipped, 47 xfailed, 0 failed** (38:38); no unexpected failure to rerun |
| Durability lane (`pytest -m durability -n 6`, 5G scope) | `e8aaea0f12` (final) | **179 passed, 1 skipped** |
| Owner lane (`pytest -m owner_vaults -n 6`; `LEARNLOOP_OWNER_VAULTS` = fresh backup-API copies, `copy_tree_with_databases`, of `learnanything-ad1/fixtures-local/owner-copies-mvp035` in the gitignored `fixtures-local/landing-c3/`, then `landing-c3b/`) | `57a051a414`, `e8aaea0f12` | **83 passed, 2 failed, 4 skipped** both times. The two failures are the known ones (`test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events`, `test_placement_fixture_copies::…[arxiv_v2]`). The count is unchanged (C3 adds no owner test). |
| Frontend: `npm install`, `npm run typecheck`, whole vitest (`npx vitest run --maxWorkers=4`, 5G scope), `npm run frontend:build` | `57a051a414` (the second merge changed nothing under `apps/`) | ok; **249 files, 2375 passed**; typecheck clean; build ok |
| `cargo check` | n/a | not run: the branch's `src-tauri` equals main's |
| DB reference, desktop catalog, vault | after each merge | `db_validate_reference` errors [], `desktop_validate` passed (299 TS / 291 entry-build / ACTIVE 304, byte for byte), `validate_vault` passed |

### Smoke on fresh owner copies (`fixtures-local/landing-c3-smoke/`, driver `scripts/smoke.sh`)

**Setup.**

- Copies: fresh backup-API copies of the three mvp035 owner copies.
- Neutralizing: under each side's own code (`neutralize3.py`), every route points at the `127.0.0.1:9`
  blackhole with the key variable unset; rewrite, rerank, dense and embeddings are off.
- Code: main's `git archive e9693b3700` and the branch's `git archive 57a051a414`, each with `src/`,
  `migrations/` and `tests/`.
- Per copy, under its own side's code: a bare `upgrade`, the primary desktop start, `migrate_vault`,
  `rebuild-derived-state`.
- Isolation: every process ran under `env -i` with an audit hook that logs every process start and socket
  connect and refuses non-loopback sockets and Codex starts.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| upgrade (main and branch) | mvp-0.35 → mvp-0.40, head 229 | same | same |
| Today (3 queue variants, frozen clock), branch vs main | **identical** (525,266 bytes) | identical (740,827) | identical (344,204) |
| Daily plan dump (sidecar handlers, frozen clock, deterministic ids), branch vs main | **identical** (84,696 bytes) | identical (124,021) | identical (32,433) |
| Source roles (every set member's default role and unit overrides; `source_unit_selections` role overrides), main vs branch; `source_sets.yaml` byte-compared with the fresh copy | unchanged | unchanged | unchanged |
| Exam predicate and teaching exclusions, main vs branch | equal (no exam material) | equal (no exam material) | equal (no exam material) |
| `syllabus` offered | branch `KNOWN_ROLES` has it, main's doesn't; the branch CLI `source-set add --help` names it; both desktop role pickers list it | same | same |
| Synthetic deliverable (sentence of the vault's first six topic titles), resolved by the suite's local `DeliverableFake`: main, branch with `exam_units_in_scope` on, branch with it off | prompt v1 and identical text and state key in all three; no `past_papers_test` (past papers `[]`, subject `vector-spaces`); resolver contexts identical; scope view: main == off, and on == main once the on-only `on_past_papers` key (0 of 8 topics marked) is dropped | same (subject `counting`; 0 of 11 marked; the problem-set members map to no LO) | same (subject `llm`; 0 of 9 marked) |
| `rebuild --shadow --json` (branch copy) | **0/0/0**, live unchanged | 0/0/0 | 0/0/0 |

- **Receipts:** **0 new `model_call_receipts`** on every upgrade, Today, plan and shadow copy (probability's 56
  historical rows, 42 completed and 14 failed, unchanged; the others have none). The scope copies hold, beyond
  those 56, exactly 3 rows from the local `DeliverableFake` (one resolution per copy, provider `fake_deliverable`).
- **Audit:** no entries at all: no process start, no socket connect of any kind, nothing refused.
- **Timing:** the smoke ran at `57a051a414` against main `e9693b3700`. It was not rerun after the merge of
  `7401484f91` (Reader follow-ups Nov 1b: figures wording, compare pins, the OpenAI chat transport's
  `trust_env`), which touches nothing C3 reads; that landing recorded its own smoke.

### Orchestrator rulings (verbatim)

- R1: "Past papers count only for the deliverable's subject: syllabus source sets first, then the single subject of its resolved topics, then the vault's only active subject; otherwise none. Accepted; flagged to the owner."
- R2: "A syllabus may still appear as a compare_sources/find_sources counterpart (as notes and problem sets do); teaching grounding excludes it. Accepted for v1."
- R3: "Held-out signals are covered by the exam predicate's own suite, not the C3 fixture. Accepted."
- R4: "A Reader-selection action 'scope my deliverable from this passage' is queued as a follow-up; the scope panel's syllabus picker ships now."

### Open items

- **Owner (R1):** past papers count only for the deliverable's own subject (a syllabus's source sets, else the
  single subject of its resolved topics, else the vault's only active subject). In a vault with two active
  subjects and no syllabus, a first resolution sends no past-papers list.
- **Follow-up (R4):** a Reader-selection action, "scope my deliverable from this passage".
- **Follow-up (R2):** decide whether a syllabus should stay a `compare_sources`/`find_sources` counterpart once
  compare grounding is revisited.
- The owner may want past papers per subject once goals carry a subject or source sets (AD §16's deferred
  `source_set_ids`); R1's fallback order stands until then.
- No owner vault changes: no migration, no successor. `exam_units_in_scope` defaults on and has no effect on the
  current vaults, which have no exam material and no problem-set unit mapped to an LO.
