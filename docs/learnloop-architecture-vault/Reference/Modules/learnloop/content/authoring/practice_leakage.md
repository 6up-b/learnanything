---
title: "learnloop.content.authoring.practice_leakage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/practice_leakage.py"
source_paths:
  - "src/learnloop/content/authoring/practice_leakage.py"
source_commit: "b18685c89ea24659f1ed763ea937199a39a96fb8"
source_commit_timestamp: "2026-11-06T09:42:06-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.practice_leakage module"
  - "src/learnloop/content/authoring/practice_leakage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.practice_leakage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.practice_leakage` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: ING M8 — cross-source practice generation leakage controls (spec §8.5, §14).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/practice_leakage.py](../../../../../../../src/learnloop/content/authoring/practice_leakage.py) |
| Source lines | 483 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b18685c89ea24659f1ed763ea937199a39a96fb8` |
| Commit timestamp | `2026-11-06T09:42:06-05:00` |

## Public API

- `class HeldOutInventory` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 49) — Deterministic fingerprint of held-out exam text (§8.5).
  - `empty(self) -> bool` (line 58; public)
- `class CrossSourceSpan` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 63)
  - `as_dict(self) -> dict[str, Any]` (line 72; public)
- `held_out_spans(vault: LoadedVault, repository: Repository, *, subject_ids: set[str] | None=None) -> list[HeldOutSpan]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 119) — Every held-out span vault-wide, with its identity and text (§4.2, §8.5).
- `build_held_out_inventory(vault: LoadedVault, repository: Repository, *, subject_ids: list[str] | None=None, shingle_n: int=DEFAULT_SHINGLE_N) -> HeldOutInventory` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 144) — Fingerprint every held-out exam span text vault-wide (§8.5).
- `inventory_for_texts(texts: list[str], *, shingle_n: int=DEFAULT_SHINGLE_N) -> HeldOutInventory` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 158) — The deterministic fingerprint of the given held-out texts (§8.5).
- `check_leakage(text: str, inventory: HeldOutInventory) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 180) — Deterministic overlap findings between ``text`` and held-out material.
- `screen_practice_payload(payload: dict[str, Any], inventory: HeldOutInventory) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 224) — Leakage findings for one generated practice-item payload (§14).
- `class ReservedQuestions` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 234) — What a generated probe's words may not reproduce, as this module's gate reads it.
- `reserved_questions(vault: LoadedVault, repository: Repository, withheld: Any) -> ReservedQuestions` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 247) — Every question ``withheld`` (the one authority, ``learner_protection.withheld_items``) still holds for an exam or an assessment, and every held-out span: stem, solution and rubric.
- `distinctive_words(stem: str, reserved: ReservedQuestions) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 288) — A reserved stem's words distinctive in this vault, by its own text (the teacher exam-question guard's landing ruling R1): no other item's prompt, answer or rubric shows them, and no passage the learner can read does (``source_shows``: source text outside held-out and exam spans;…
- `reserved_findings(text: str, reserved: ReservedQuestions) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 317) — What this text reproduces of a reserved question: ``check_leakage``'s contiguous wording and distinctive numbers, and a whole stem.
- `reserved_payload_findings(payload: dict[str, Any], reserved: ReservedQuestions) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 330) — The same, over everything a learner sees of a generated item: stem, key, rubric, hints.
- `learner_visible_text(payload: dict[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 336)
- `matching_phrases(text: str, findings: list[dict[str, str]]) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 340) — The stretches of ``text`` the findings fall in, in order: its own words only, so telling its author about them shows nothing of a reserved question it hadn't already written.
- `build_cross_source_spans(vault: LoadedVault, repository: Repository, learning_object_id: str, *, max_spans_per_item: int=4, exam: exam_material.ExamMaterial | None=None) -> list[CrossSourceSpan]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 407) — Bounded multi-source grounding spans for one learning object (§8.5).

### Module constants

- `DEFAULT_SHINGLE_N` ([src/learnloop/content/authoring/practice_leakage.py](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 37)
- `_SEMANTIC_RELATION_PRIORITY` ([src/learnloop/content/authoring/practice_leakage.py](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 41)
- `_SPAN_TEXT_CAP` ([src/learnloop/content/authoring/practice_leakage.py](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 45)

## Internal implementation anchors

- `_normalize_tokens(text: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 87)
- `_shingles(tokens: list[str], n: int) -> set[str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 91)
- `_numeric_literals(text: str) -> set[str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 99) — Distinctive numeric literals: multi-digit integers, decimals, fractions, or percentages.
- `_held_out_span_texts(vault: LoadedVault, repository: Repository, *, subject_ids: set[str] | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 136) — The text of every held-out exam span vault-wide (§4.2 use modes).
- `_payload_surfaces(payload: dict[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 197) — Concatenate the learner-visible surfaces of a practice-item payload.
- `_source_shows(repository: Repository, withheld: Any) -> Callable[[str], bool]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 297) — R10: a phrase the learner can read in source text outside held-out spans can't leak.
- `_lo_facet_ids(vault: LoadedVault, learning_object) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 367) — Canonical facet ids a learning object teaches: blueprint recipe components plus its practice items' evidence facets.
- `_span_text(repository: Repository, extraction_id: str, span_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 384)
- `_span_id_from_locator(locator: str | None) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/practice_leakage.py), line 395)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `build_cross_source_spans`, `build_held_out_inventory`, `screen_practice_payload`; statically calls `build_cross_source_spans`, `build_held_out_inventory`, `screen_practice_payload`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `build_held_out_inventory`, `screen_practice_payload`; statically calls `build_held_out_inventory`, `screen_practice_payload`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `reserved_payload_findings`, `reserved_questions`; statically calls `reserved_payload_findings`, `reserved_questions`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `build_cross_source_spans`; statically calls `build_cross_source_spans`
- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `learner_visible_text`, `matching_phrases`, `reserved_payload_findings`; statically calls `learner_visible_text`, `matching_phrases`, `reserved_payload_findings`
- [[Reference/Modules/learnloop/followup_run/authoring|learnloop.followup_run.authoring]] — imports `reserved_findings`, `reserved_questions`; statically calls `reserved_findings`, `reserved_questions`
- [[Reference/Modules/learnloop/followup_run/lesson_probe|learnloop.followup_run.lesson_probe]] — imports `reserved_findings`; statically calls `reserved_findings`
- [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]] — imports `held_out_spans`, `inventory_for_texts`, `screen_practice_payload`; statically calls `held_out_spans`, `inventory_for_texts`, `screen_practice_payload`
- [[Reference/Modules/learnloop/ops/contamination/recipes|learnloop.ops.contamination.recipes]] — imports `held_out_spans`; statically calls `held_out_spans`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `build_cross_source_spans`, `build_held_out_inventory`, `screen_practice_payload`; statically calls `build_cross_source_spans`, `build_held_out_inventory`, `screen_practice_payload`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `build_cross_source_spans`; statically calls `build_cross_source_spans`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `build_cross_source_spans`; statically calls `build_cross_source_spans`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `build_cross_source_spans`; statically calls `build_cross_source_spans`
- [[Reference/Modules/learnloop/teacher/guards|learnloop.teacher.guards]] — imports `distinctive_words`, `inventory_for_texts`, `reserved_findings`, `reserved_questions`; statically calls `distinctive_words`, `inventory_for_texts`, `reserved_findings`, `reserved_questions`
- [[Reference/Modules/learnloop/teacher/topics|learnloop.teacher.topics]] — imports `reserved_findings`, `reserved_questions`; statically calls `reserved_findings`, `reserved_questions`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `build_cross_source_spans`; statically calls `build_cross_source_spans`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `HeldOutSpan`, `module`; calls `exam_material`, `held_out_spans`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `phrase_shown_outside`; calls `phrase_shown_outside`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `WITHHELD_EXAM`, `WITHHELD_RESERVED`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `presented_prompt`; calls `presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] and 11 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_contract.py](../../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_exam_protection.py](../../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_held_out_unit_of_any_role_joins_the_leakage_inventory`
  - `test_an_unresolvable_held_out_mark_fingerprints_its_whole_extraction`
  - `test_cross_source_teaching_spans_never_carry_exam_material`
- [tests/test_exam_protection_identity.py](../../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_f14_a_refresh_never_drops_signal_only_protection`
- [tests/test_followup_reserved_only.py](../../../../../../../tests/test_followup_reserved_only.py) — direct import
  - `test_a_short_reserved_stem_is_still_a_match_within_longer_words`
  - `test_r10_a_phrase_only_a_held_out_span_shows_still_matches`
  - `test_r10_a_phrase_source_text_outside_held_out_spans_shows_is_no_match`
  - `test_wording_an_ordinary_item_already_shows_is_no_match`
- [tests/test_method_explicit_landing.py](../../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_the_leakage_screen_reads_the_rendered_question`
- [tests/test_practice_leakage.py](../../../../../../../tests/test_practice_leakage.py) — direct import
  - `test_cross_source_context_is_bounded_and_authority_first`
  - `test_held_out_inventory_flags_planted_phrase_and_passes_fresh_text`
  - `test_screen_practice_payload_catches_expected_answer_leak`
- [tests/test_teacher_exam_question_guard.py](../../../../../../../tests/test_teacher_exam_question_guard.py) — direct import
  - `test_a_short_reserved_question_counts_when_an_ordinary_item_shows_its_number`
  - `test_distinctive_is_read_from_the_vaults_own_items_and_readable_passages`
  - `test_the_matcher_reads_both_items_as_withheld_questions`
  - `test_unreadable_protection_fails_closed`

## Modification guidance

- Change practice leakage policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/practice_leakage.py](../../../../../../../src/learnloop/content/authoring/practice_leakage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
