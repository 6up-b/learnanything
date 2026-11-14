---
title: "learnloop.vault.required_method"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/required_method.py"
source_paths:
  - "src/learnloop/vault/required_method.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.required_method module"
  - "src/learnloop/vault/required_method.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.required_method`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.vault.required_method` exists within [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] to own the behavior summarized by its module contract: Fact-phrased rubric criteria and required methods (owner rule, 2026-10-13).

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py) |
| Source lines | 875 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `required_method_instruction(name: str) -> str` ([source](../../../../../../src/learnloop/vault/required_method.py), line 112) — The explicit instruction for ``name`` ("Use {name} in your answer.").
- `method_instruction(method: Any) -> str | None` ([source](../../../../../../src/learnloop/vault/required_method.py), line 141) — The instruction a required method renders ("Use {name} in your answer."), or None without one.
- `presented_prompt(prompt: Any, method: Any) -> str` ([source](../../../../../../src/learnloop/vault/required_method.py), line 159) — The question as presented: the stored statement, verbatim, then the instruction rendered from ``method`` as its own final paragraph.
- `fit_presented_prompt(prompt: Any, method: Any, limit: int, clip: Callable[[str, int], str]) -> str` ([source](../../../../../../src/learnloop/vault/required_method.py), line 180) — :func:`presented_prompt` on one line within ``limit`` characters, the instruction always whole (method-explicit-3 review F5).
- `answered_prompt(item: Any, contract: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/vault/required_method.py), line 203) — The question an answer was given, as a reader of that answer is shown it (method-explicit-3 review F3): exam review, adjudication, the diagnoser and its history, review exports.
- `answered_question(item: Any, contract: Mapping[str, Any] | None) -> tuple[str | None, Any]` ([source](../../../../../../src/learnloop/vault/required_method.py), line 227) — The (statement, required method) pair :func:`answered_prompt` renders, for a surface that shortens the question (:func:`fit_presented_prompt` keeps the instruction whole): the contract's frozen pair for a method-explicit answer, else the item's current pair; ``(None, None)`` whe…
- `is_source_statement(item: Any) -> bool` ([source](../../../../../../src/learnloop/vault/required_method.py), line 243) — Is ``item``'s prompt a source-authored statement that is never rewritten?
- `same_statement(left: Any, right: Any) -> bool` ([source](../../../../../../src/learnloop/vault/required_method.py), line 265) — Are two statements the same text, whitespace aside?
- `rewrites_decided_statement(existing: Any, prompt: Any) -> bool` ([source](../../../../../../src/learnloop/vault/required_method.py), line 271) — Would writing ``prompt`` rewrite a statement whose requirement was decided on its wording?
- `class SourceStatementDecision` ([source](../../../../../../src/learnloop/vault/required_method.py), line 295) — The one-time judgment on a source statement (``learnloop.content.
- `advisory_statement_flag(prompt: Any, name: str) -> AdvisoryFlag | None` ([source](../../../../../../src/learnloop/vault/required_method.py), line 383) — An ADVISORY flag: does ``prompt`` seem to negate the method ``name`` ("without X", "do not use X", "X is not allowed") or leave it optional ("You may use X", "X or any other method", "for example by X")?
- `class MethodPhrase` ([source](../../../../../../src/learnloop/vault/required_method.py), line 444) — A criterion phrased by method: the matched text and the method it names.
- `method_phrase(description: Any) -> MethodPhrase | None` ([source](../../../../../../src/learnloop/vault/required_method.py), line 451) — The method a criterion's description names, by the conservative heuristic.
- `name_tokens(text: Any) -> frozenset[str]` ([source](../../../../../../src/learnloop/vault/required_method.py), line 485) — Content tokens of a method name (generic words dropped, crude singulars).
- `names_match(left: Any, right: Any) -> bool` ([source](../../../../../../src/learnloop/vault/required_method.py), line 498) — Does one method name contain the other's content tokens (case, plurals and generic words aside)?
- `class MethodTarget` ([source](../../../../../../src/learnloop/vault/required_method.py), line 525) — A target that IS a method, and the existing metadata that says so.
  - `names(self) -> tuple[str, ...]` (line 535; public)
  - `matches(self, name: Any) -> bool` (line 538; public)
  - `matching_name(self, name: Any) -> str | None` (line 541; public) — The target's own name or alias that ``name`` names, if any.
  - `as_context(self) -> dict[str, Any]` (line 546; public) — What a generation prompt is shown (name, basis, the linked id).
  - `link(self) -> dict[str, str]` (line 558; public)
- `method_targets(vault: Any, *, learning_object_id: str | None, facet_ids: Iterable[str]=(), capability: str | None=None) -> list[MethodTarget]` ([source](../../../../../../src/learnloop/vault/required_method.py), line 571) — The method targets of an item aimed at ``learning_object_id`` and ``facet_ids``.
- `learning_object_method_targets(vault: Any, learning_object_id: str, facet_ids: Iterable[str]=()) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/vault/required_method.py), line 620) — A generation context's ``required_method_targets`` for one learning object.
- `best_target(name: Any, targets: Sequence[MethodTarget]) -> MethodTarget | None` ([source](../../../../../../src/learnloop/vault/required_method.py), line 628) — The target a proposed method name names (:func:`names_match`; the one sharing most tokens first), or None.
- `normalize_required_method(payload: dict[str, Any], targets: Sequence[MethodTarget], *, source_statement: bool=False, rubric_criterion_ids: Sequence[str] | None=None, judge_source: SourceJudge | None=None) -> list[str]` ([source](../../../../../../src/learnloop/vault/required_method.py), line 652) — Hold a written item's ``required_method`` FIELD to the rule, in place.
- `inherit_required_method(payload: dict[str, Any], parent: Any) -> list[str]` ([source](../../../../../../src/learnloop/vault/required_method.py), line 729) — A variant that keeps its parent's rubric verbatim keeps its required method.
- `class RequiredMethodProblem` ([source](../../../../../../src/learnloop/vault/required_method.py), line 759)
- `required_method_problems(item: Any, rubric: Any) -> list[RequiredMethodProblem]` ([source](../../../../../../src/learnloop/vault/required_method.py), line 769) — What doctor reports for one item under the rule.

### Module constants

- `CRITERIA_BY_FACT_RULE_VERSION` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 80)
- `METHOD_INSTRUCTION_TEMPLATE` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 83)
- `CRITERIA_BY_FACT_GUIDANCE` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 86)
- `REQUIRED_METHOD_VARIANT_GUIDANCE` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 105)
- `_DASHES` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 118)
- `SOURCE_REQUIRES` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 291)
- `_ABBREVIATIONS` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 312)
- `_CLAUSES` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 313)
- `_MD_LINK` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 315)
- `_MD_HTML` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 316)
- `_TEX_TEXT` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 317)
- `_TEX_DELIMITERS` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 318)
- `_MD_MARKS` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 319)
- `_MD_UNDERSCORES` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 320)
- `_FILLER` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 335)
- `_NEGATED_BEFORE` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 339)
- `_NEGATED_AFTER` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 343)
- `_OPTIONAL_BEFORE` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 348)
- `_ALTERNATIVE_BEFORE` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 354)
- `_OPTIONAL_AFTER` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 355)
- `_ANY_METHOD` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 366)
- `_OPTION_WINDOW` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 371)
- `_METHOD_NOUNS` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 418)
- `_NOUN` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 428)
- `_VERB` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 429)
- `_NOUN_PHRASE` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 432)
- `_VERB_SPAN` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 433)
- `_BY_SPAN` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 434)
- `_OPEN` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 436)
- `_ARTICLES` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 440)
- `_GENERIC` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 478)
- `METHOD_CONCEPT_TYPES` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 517)
- `METHOD_FACET_KINDS` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 519)
- `OPEN_METHOD_CAPABILITIES` ([src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py), line 521)

### Explicit exports

`__all__` declares:

- `AdvisoryFlag`
- `CRITERIA_BY_FACT_GUIDANCE`
- `CRITERIA_BY_FACT_RULE_VERSION`
- `METHOD_CONCEPT_TYPES`
- `METHOD_FACET_KINDS`
- `METHOD_INSTRUCTION_TEMPLATE`
- `MethodPhrase`
- `MethodTarget`
- `OPEN_METHOD_CAPABILITIES`
- `REQUIRED_METHOD_VARIANT_GUIDANCE`
- `RequiredMethodProblem`
- `SOURCE_REQUIRES`
- `SourceJudge`
- `SourceStatementDecision`
- `advisory_statement_flag`
- `answered_prompt`
- `answered_question`
- `best_target`
- `fit_presented_prompt`
- `inherit_required_method`
- `is_source_statement`
- `learning_object_method_targets`
- `method_instruction`
- `method_phrase`
- `method_targets`
- `name_tokens`
- `names_match`
- `normalize_required_method`
- `presented_prompt`
- `required_method_instruction`
- `required_method_problems`
- `rewrites_decided_statement`
- `same_statement`

## Internal implementation anchors

- `_squash(text: str) -> str` ([source](../../../../../../src/learnloop/vault/required_method.py), line 122)
- `_method_name(method: Any) -> str | None` ([source](../../../../../../src/learnloop/vault/required_method.py), line 130) — The name of a required method given as the item's field, a frozen contract's ``required_method`` mapping, or None.
- `_whitespace_normalized(text: Any) -> str` ([source](../../../../../../src/learnloop/vault/required_method.py), line 261)
- `_plain_text(text: str) -> str` ([source](../../../../../../src/learnloop/vault/required_method.py), line 323)
- `_match_form(text: str) -> str` ([source](../../../../../../src/learnloop/vault/required_method.py), line 377) — Case-folded, dashes and hyphens as spaces, one space between words.
- `_facet_name(facet: Any, facet_id: str) -> str` ([source](../../../../../../src/learnloop/vault/required_method.py), line 566)
- `_rubric_criterion_ids(payload: Mapping[str, Any]) -> list[str] | None` ([source](../../../../../../src/learnloop/vault/required_method.py), line 644)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `CRITERIA_BY_FACT_GUIDANCE`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `learning_object_method_targets`, `method_targets`, `normalize_required_method`; statically calls `learning_object_method_targets`, `method_targets`, `normalize_required_method`
- [[Reference/Modules/learnloop/content/authoring/pf_contracts|learnloop.content.authoring.pf_contracts]] — imports `REQUIRED_METHOD_VARIANT_GUIDANCE`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `CRITERIA_BY_FACT_GUIDANCE`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `CRITERIA_BY_FACT_GUIDANCE`, `MethodTarget`, `advisory_statement_flag`, `best_target`, `is_source_statement`, `method_phrase`, `method_targets`, `names_match`; statically calls `advisory_statement_flag`, `best_target`, `is_source_statement`, `method_phrase`, `method_targets`, `names_match`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `SOURCE_REQUIRES`, `SourceStatementDecision`, `required_method_instruction`; statically calls `SourceStatementDecision`, `required_method_instruction`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `rewrites_decided_statement`; statically calls `rewrites_decided_statement`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `is_source_statement`, `learning_object_method_targets`, `method_targets`, `normalize_required_method`, `rewrites_decided_statement`, `same_statement`; statically calls `is_source_statement`, `learning_object_method_targets`, `method_targets`, `normalize_required_method`, `rewrites_decided_statement`, `same_statement`
- [[Reference/Modules/learnloop/content/proposals/required_method_override|learnloop.content.proposals.required_method_override]] — imports `best_target`, `is_source_statement`, `method_targets`, `names_match`; statically calls `best_target`, `is_source_statement`, `method_targets`, `names_match`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `CRITERIA_BY_FACT_GUIDANCE`
- [[Reference/Modules/learnloop/content/synthesis/normalize|learnloop.content.synthesis.normalize]] — imports `advisory_statement_flag`, `method_targets`, `normalize_required_method`; statically calls `advisory_statement_flag`, `method_targets`, `normalize_required_method`
- [[Reference/Modules/learnloop/curriculum/rung_backfill|learnloop.curriculum.rung_backfill]] — imports `fit_presented_prompt`; statically calls `fit_presented_prompt`
- [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]] — imports `fit_presented_prompt`; statically calls `fit_presented_prompt`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `required_method_problems`; statically calls `required_method_problems`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/diagnosis/offline_review/planted|learnloop.diagnosis.offline_review.planted]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/diagnosis/offline_review/probes|learnloop.diagnosis.offline_review.probes]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `answered_prompt`; statically calls `answered_prompt`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `answered_prompt`; statically calls `answered_prompt`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `fit_presented_prompt`; statically calls `fit_presented_prompt`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `fit_presented_prompt`, `presented_prompt`; statically calls `fit_presented_prompt`, `presented_prompt`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `fit_presented_prompt`, `method_instruction`; statically calls `fit_presented_prompt`, `method_instruction`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `method_phrase`, `method_targets`, `required_method_problems`; statically calls `method_phrase`, `method_targets`, `required_method_problems`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `inherit_required_method`; statically calls `inherit_required_method`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `fit_presented_prompt`; statically calls `fit_presented_prompt`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `fit_presented_prompt`; statically calls `fit_presented_prompt`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `fit_presented_prompt`, `presented_prompt`; statically calls `fit_presented_prompt`, `presented_prompt`
- [[Reference/Modules/learnloop/reader/reader_cues|learnloop.reader.reader_cues]] — imports `answered_question`, `fit_presented_prompt`; statically calls `answered_question`, `fit_presented_prompt`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `fit_presented_prompt`; statically calls `fit_presented_prompt`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]] — imports `fit_presented_prompt`; statically calls `fit_presented_prompt`
- [[Reference/Modules/learnloop/tutor/reader_modes|learnloop.tutor.reader_modes]] — imports `fit_presented_prompt`; statically calls `fit_presented_prompt`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `answered_prompt`; statically calls `answered_prompt`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `answered_prompt`; statically calls `answered_prompt`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `fit_presented_prompt`; statically calls `fit_presented_prompt`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `method_instruction`; statically calls `method_instruction`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `presented_prompt`; statically calls `presented_prompt`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `method_instruction`; statically calls `method_instruction`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`, `typing`, `unicodedata`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]], [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]], [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/content/authoring/pf_contracts|learnloop.content.authoring.pf_contracts]], [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] and 44 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/method_explicit_landing_helpers.py](../../../../../../tests/method_explicit_landing_helpers.py) — direct import
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_a_method_explicit_question_records_the_contract_it_was_presented_with`
- [tests/test_grading_hardcases.py](../../../../../../tests/test_grading_hardcases.py) — direct import
  - `test_cell_5_pairs_each_required_method_with_the_same_mathematics_without_one`
- [tests/test_method_explicit_landing.py](../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_answered_question_is_the_pair_answered_prompt_renders`
- [tests/test_method_phrasing_report.py](../../../../../../tests/test_method_phrasing_report.py) — direct import
  - `test_repairs_are_pending_proposals_applied_only_on_accept`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_no_bound_model_call_receives_item_text_from_outside_the_plan`
- [tests/test_required_method_authority.py](../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_a_generated_prompt_is_stored_as_generated_and_presented_with_the_sentence`
  - `test_a_metered_llm_judge_without_a_price_is_refused_before_sending_and_decides_nothing`
  - `test_a_source_statement_is_valid_by_its_recorded_decision_not_its_wording`
  - `test_a_source_statement_keeps_the_field_only_by_the_judgment`
  - `test_a_source_statement_with_no_judge_keeps_no_requirement`
  - `test_the_owner_overrides_a_source_decision_and_clears_it_through_proposals`
  - `test_the_sentence_is_rendered_from_the_field_never_read_from_the_statement`
  - `test_validation_reads_no_statement_and_only_flags_the_rest`
- [tests/test_required_method_items.py](../../../../../../tests/test_required_method_items.py) — direct import
  - `test_a_target_is_a_method_by_its_concept_type_or_facet_kind`
  - `test_a_variant_inherits_its_parents_required_method`
  - `test_an_authoring_proposal_keeps_a_required_method_only_on_a_method_target`
  - `test_authoring_prompts_carry_the_rule_and_moved_their_versions`
  - `test_method_names_match_on_content_tokens`
  - `test_pf_publication_keeps_the_parents_required_method_and_states_it`
  - `test_rereview_instructions_and_descriptions_raise_no_advisory_flag`
  - `test_rereview_statements_are_advisory_flags_only`
  - `test_synthesis_keeps_a_required_method_only_on_a_procedure_target`
  - `test_synthesis_publishes_a_required_method_presented_with_the_canonical_sentence`
  - `test_the_advisory_flag_reads_negations_and_options_only`
  - `test_the_conservative_heuristic`
  - `test_the_explicit_instruction`
  - `test_the_writer_check_keeps_a_required_method_only_on_its_target`
  - `test_the_writers_keep_the_field_and_never_touch_the_prompt`
  - `test_validation_names_each_problem`
  - `test_validation_reads_no_sentence_and_flags_a_contradiction`
- [tests/test_required_method_reopened.py](../../../../../../tests/test_required_method_reopened.py) — direct import
  - `test_f15_a_generated_items_new_prompt_is_stored_as_generated`
- [tests/test_required_method_rereview.py](../../../../../../tests/test_required_method_rereview.py) — direct import
  - `test_f14_the_generation_guidance_leaves_the_sentence_to_the_writer`
- [tests/test_required_method_round3.py](../../../../../../tests/test_required_method_round3.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains required method within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/required_method.py](../../../../../../src/learnloop/vault/required_method.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
