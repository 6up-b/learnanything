---
title: "learnloop.adaptive_difficulty.relatedness"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/relatedness.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/relatedness.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.relatedness module"
  - "src/learnloop/adaptive_difficulty/relatedness.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.relatedness`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.relatedness` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Learned relatedness and implication: the proposal and its structure (spec_adaptive_difficulty_v1 §5.10, D19).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/relatedness.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py) |
| Source lines | 858 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class LoadingV1(WireModel)` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 82)
- `class ItemLoadingsV1(WireModel)` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 88)
- `class RelatedV1(WireModel)` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 93)
- `class LearningObjectCouplingsV1(WireModel)` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 99)
- `class RelatednessV1(WireModel)` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 104) — The proposal: per item, its loadings; per LO, its related LOs.
- `lo_subject(vault: Any, lo: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 118)
- `reserved(unit: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 130)
- `run_in_force(run: Mapping[str, Any], epoch: str | None) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 134) — Whether a saved run may be used now: it was proposed at the current protection epoch (E2, owner decision 2026-10-21: one vault-wide epoch; any protection change, anywhere, takes every run out of use until it is proposed and adopted again).
- `live_judgments(connection: Any, *, view: Any) -> set[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 144) — The judgments of the runs in force (the view reads only runs of its epoch): a frozen loading may name these and no other (the replay, the serve's frozen loadings).
- `lo_facets(view: Any, lo: Any) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 153) — The LO's authored facets, else its visible active items' facets, through the operation's material view (A8; Codex verify F17's audit, F19): a facet only withheld items name is never quoted to a prompt, never steers generation and never enters the replay's structure.
- `subjects(vault: Any) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 161)
- `subject_inputs(vault: Any, repository: Any, subject: str, *, protected: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 167) — Exactly what the proposal reads for one subject: LO and facet text, the concept graph and prerequisites, and the stems of the subject's unprotected items.
- `touched_units(inputs: Mapping[str, Any], runs: Sequence[Mapping[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 249) — The units whose fingerprint changed (or that are new) since their latest ok run: all of them when the subject has none.
- `focus(inputs: Mapping[str, Any], units: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 264) — The inputs restricted to proposing for ``units`` only (the whole subject stays as context; the input hash covers the focus, so an unchanged request is never re-asked).
- `prompt(inputs: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 276)
- `class Proposal` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 295)
- `validate(answer: RelatednessV1 | Mapping[str, Any], inputs: Mapping[str, Any]) -> Proposal` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 301) — Drop what fails validation: unknown ids, another subject's facet, self-loadings or self-couplings, more than three per unit; the loadings' sum capped at 1.
- `class ProposalOutcome` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 368)
  - `as_dict(self) -> dict[str, Any]` (line 377; public)
- `run_key(subject: str, input_hash: str, epoch: str | None=None) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 382) — A run's identity: the subject, the prompt's hash and its protection epoch (E2), so a run proposed at another epoch never answers for a new request.
- `claim_key(subject: str, input_hash: str, epoch: str | None=None) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 389)
- `coupling_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 404)
- `propose_subject(vault: Any, repository: Any, subject: str, *, client: Any=None, clock: Clock | None=None, fence: Any=None, live_vault: Callable[[], Any] | None=None, protected: Any=None) -> ProposalOutcome` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 411) — One subject's proposal, under its durable claim; never with ``learned_coupling`` off.
- `class ReinterpretationNeedsShadow(ValueError)` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 573) — A later coupling version reinterprets what exists: shadow-rebuild report first (§5.10, §11.1).
- `candidate_version(connection: Any, subject: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 577) — The coupling version adopting would write now: every unit's latest ok run.
- `adopt(repository: Any, subject: str, *, adopted_by: str, note: str | None=None, clock: Clock | None=None, confirm_reinterpretation: bool=False) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 598) — Adopt the proposals now in force for ``subject`` as its next coupling version.
- `shadow_report(vault: Any, repository: Any, subject: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 622) — What adopting the candidate version would change, computed in memory (the playbook's shadow rebuild for a reinterpretation): the subject view's state hash and every attempt whose subject-view trace moves.
- `class VaultStructure(M.Structure)` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 664) — The relatedness in force, as of the replay's current time (``now``, in days).
  - `__init__(self, *, facet_los: Mapping[str, Sequence[str]], lo_facets: Mapping[str, Sequence[str]], couplings: Mapping[str, Sequence[_UnitProposal]] | None=None, loadings: Mapping[str, Sequence[_UnitProposal]] | None=None, versions: Mapping[str, str] | None=None) -> None` (line 670; internal)
  - `fixed(cls, *, facet_los: Mapping[str, Sequence[str]], lo_facets: Mapping[str, Sequence[str]], couplings: Mapping[str, Mapping[str, float]] | None=None, loadings: Mapping[str, Mapping[str, float]] | None=None) -> 'VaultStructure'` (line 682; public) — A structure whose proposals hold from the start (a synthetic vault's, ``learnloop.sim``): ``couplings`` LO -> {LO: C}, ``loadings`` revision -> {facet: Q}.
  - `_in_force(props: Sequence[_UnitProposal], at: float) -> dict[str, float]` (line 696; internal)
  - `named(self, lo: str, at: float | None=None) -> dict[str, float]` (line 703; public)
  - `coupling(self, lo: str, at: float | None=None) -> dict[str, float]` (line 706; public) — Symmetrized strengths ``C_{LM}``: the mean of the two sides (0 for a side that names none).
  - `loadings(self, content_hash: str | None, at: float | None=None) -> dict[str, float]` (line 725; public)
  - `_partners(self, facet: str) -> dict[str, float]` (line 730; internal)
  - `_regression(self, facet: str, name_for: Callable[[str], str], existing: Callable[[str], bool]) -> M.Regression` (line 740; internal)
  - `facet_regression(self, facet: str, existing: Callable[[str], bool]) -> M.Regression` (line 754; public)
  - `cell_regression(self, facet: str, capability: str, existing: Callable[[str], bool]) -> M.Regression` (line 757; public)
  - `coupled_facets(self, facet: str) -> tuple[str, ...]` (line 760; public)
- `load_structure(connection: Any, vault: Any, *, view: Any, coupled: bool=True, override: Mapping[str, Mapping[str, Any]] | None=None) -> VaultStructure` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 767) — The relatedness in force for the replay: the adopted versions' runs from the start, later runs from their write time.

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/relatedness.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 68)
- `TASK` ([src/learnloop/adaptive_difficulty/relatedness.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 70)
- `PROMPT_VERSION` ([src/learnloop/adaptive_difficulty/relatedness.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 71)
- `ROUTE` ([src/learnloop/adaptive_difficulty/relatedness.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 72)
- `OWNER_KIND` ([src/learnloop/adaptive_difficulty/relatedness.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 73)
- `STRENGTHS` ([src/learnloop/adaptive_difficulty/relatedness.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 74)
- `STEM_LIMIT` ([src/learnloop/adaptive_difficulty/relatedness.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 75)
- `SUMMARY_LIMIT` ([src/learnloop/adaptive_difficulty/relatedness.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 76)
- `_CAPS` ([src/learnloop/adaptive_difficulty/relatedness.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 77)
- `EPOCH_UNIT` ([src/learnloop/adaptive_difficulty/relatedness.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 125)
- `RESERVED` ([src/learnloop/adaptive_difficulty/relatedness.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 127)

### Explicit exports

`__all__` declares:

- `OWNER_KIND`
- `PROMPT_VERSION`
- `EPOCH_UNIT`
- `Proposal`
- `ProposalOutcome`
- `ReinterpretationNeedsShadow`
- `ROUTE`
- `RelatednessV1`
- `STRENGTHS`
- `TASK`
- `VaultStructure`
- `adopt`
- `candidate_version`
- `load_structure`
- `lo_facets`
- `lo_subject`
- `prompt`
- `propose_subject`
- `run_in_force`
- `live_judgments`
- `shadow_report`
- `subject_inputs`
- `subjects`
- `focus`
- `touched_units`
- `validate`

## Internal implementation anchors

- `_excerpt(text: Any, limit: int) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 113)
- `_latest_unit_hashes(runs: Sequence[Mapping[str, Any]]) -> dict[str, str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 234) — The fingerprint each unit had at its latest ok run (a run's ``units`` maps unit -> hash).
- `_client(vault: Any, injected: Any | None) -> tuple[Any | None, str | None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 393)
- `_record(repository: Any, subject: str, inputs: Mapping[str, Any], proposal: Proposal, *, model: str, created_at: str, admit: Callable[[], None]) -> tuple[str | None, int]` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 513)
- `_ledger(connection: Any, table: str, reader: Callable[..., Any], **kwargs: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 563) — AD's own run ledgers: through the operation's view inside one, else as stored (the owner's ``adopt`` command runs outside any operation and reads no learner data).
- `_stamp(value: Any) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 653)
- `class _UnitProposal` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py), line 659)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `lo_facets`; statically calls `lo_facets`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness_jobs|learnloop.adaptive_difficulty.relatedness_jobs]] — imports `module`; statically calls `propose_subject`, `subject_inputs`, `subjects`, `touched_units`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; statically calls `live_judgments`, `lo_subject`, `load_structure`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `module`; statically calls `live_judgments`
- [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]] — imports `module`; statically calls `adopt`, `coupling_on`, `focus`, `prompt`, `propose_subject`, `shadow_report`, `subject_inputs`, `subjects`, `touched_units`
- [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]] — imports `VaultStructure`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/claims|learnloop.adaptive_difficulty.claims]] — imports `LeaseLost`, `ReceiptWriteFailed`, `claimed`; calls `claimed`
- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `item_revision`; calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `module`; calls `Regression`, `cell_name`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `current`, `entry`, `epoch_of`, `own_write`; calls `current`, `entry`, `epoch_of`, `own_write`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `load_events`, `run`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `ProtectedContent`, `SendGuard`, `ask_llm`, `refusal_status`; calls `SendGuard`, `ask_llm`, `refusal_status`
- [[Reference/Modules/learnloop/adaptive_difficulty/spend|learnloop.adaptive_difficulty.spend]] — imports `module`; calls `ad_envelope`, `models_off`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `switch_on`; calls `switch_on`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `module`; calls `has_table`, `insert_coupling_version`, `insert_relatedness_run`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`, `resolve_client`; calls `plan_route`, `resolve_client`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]], [[Reference/Modules/learnloop/adaptive_difficulty/relatedness_jobs|learnloop.adaptive_difficulty.relatedness_jobs]], [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]], [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]], [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_contract_helpers.py](../../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_a_run_whose_quoted_revision_was_replaced_then_protected_is_not_used`
  - `test_a_saved_run_proposed_before_its_subject_was_protected_is_not_used`
  - `test_a_stale_run_never_answers_for_a_re_proposal`
  - `test_the_background_scheduler_sees_a_run_whose_recorded_context_is_protected`
- [tests/test_ad23_fix_r5.py](../../../../../../tests/test_ad23_fix_r5.py) — direct import
- [tests/test_ad23_fix_r9.py](../../../../../../tests/test_ad23_fix_r9.py) — direct import
  - `test_with_the_predicate_unavailable_relatedness_prepares_nothing`
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_the_grid_arm_never_reads_a_later_answer`
- [tests/test_ad3_reading.py](../../../../../../tests/test_ad3_reading.py) — direct import
  - `test_reading_reaches_loading_items_and_coupled_topics`
  - `test_self_check_verdict_shifts_prediction_never_evidence`
- [tests/test_ad3_relatedness.py](../../../../../../tests/test_ad3_relatedness.py) — direct import
  - `test_a_later_coupling_version_needs_its_shadow_report`
  - `test_caps_hold`
  - `test_each_loading_and_coupling_is_one_ledger_row_and_invalid_outputs_drop`
  - `test_relatedness_proposal_reads_no_learner_or_held_out_data`
  - `test_unchanged_input_makes_no_call_and_a_change_reproposes_only_what_it_touches`
- [tests/test_ad3_subject_view.py](../../../../../../tests/test_ad3_subject_view.py) — direct import
  - `test_a_proposal_recorded_after_a_coordinate_exists_changes_no_earlier_state`
  - `test_coupling_is_prediction_only`
  - `test_shadow_report_names_what_a_new_version_reinterprets`
  - `test_shared_terms_alone_never_show_likely_ready`
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_a_relatedness_run_is_in_force_at_its_epoch_only`

## Modification guidance

- Make changes here when the responsibility remains relatedness within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/relatedness.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
