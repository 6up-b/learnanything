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
| G-C1 for `note_link_judge` | **Not yet**: C2 (notes) is not on main; see open items |
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
  over the files listed below: see the result line in the stage's final report.
- Frontend (`apps/learnloop-tauri`, memory-capped): `npm install` ok; `npm run typecheck` clean; vitest
  `--maxWorkers=4` on `src/components/syllabusRole.test.tsx` (new), `AddToCollection.test.tsx`,
  `OutlineAndPlan.escape.test.tsx`, `RewordConfirms.test.tsx`, `screens/reader/DeliverableSliceCard.test.tsx`:
  **5 files, 35 passed**; `src/copy/denyList.test.tsx`, `denyList.phase4.test.tsx`: **2 files, 57 passed**;
  `npm run frontend:build` ok. Nothing under `src-tauri` changed (no cargo check needed).
- Desktop catalog: `desktop_generate.py` then `desktop_validate.py`: passed (297/297, reproducible).
- DB/config reference: `db_generate_reference.py` then `db_validate_reference.py`: `errors: []`.
- No migration, no DB/connection code changed: no durability lane needed.

## Open items

- **C2 (notes) lands first** (in `learnanything-ad1`). When it is on main, merge it here and add
  `note_link_judge` to the G-C1 sweep (link notes for the fixture's deliverable path with C2's fake and assert no
  sentinel in its requests). Expected conflicts: `config/template.py` (every snapshot: recompute all with
  `defaults_fingerprint_for_version`, both keys present) and `section_coverage.CoverageGuard._refusal` (C2
  composes `also` hooks there; keep `readable_roles=self._library.protection.readable_roles` on its
  `read_protection` call), plus the regenerated references.
- The owner may want the past-papers list per subject once goals carry a subject or source sets (AD §16's
  deferred `source_set_ids`).
