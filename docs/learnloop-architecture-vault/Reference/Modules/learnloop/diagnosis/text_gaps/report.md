---
title: "learnloop.diagnosis.text_gaps.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/text_gaps/report.py"
source_paths:
  - "src/learnloop/diagnosis/text_gaps/report.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.text_gaps"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.text_gaps.report module"
  - "src/learnloop/diagnosis/text_gaps/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-text-gaps"
---

# `learnloop.diagnosis.text_gaps.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.text_gaps.report` exists within [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] to own the behavior summarized by its module contract: ``learnloop gaps report``: what the pipeline did, per kind and chooser (no call).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/text_gaps/report.py](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py) |
| Source lines | 298 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `wilson(successes: int, trials: int, z: float=1.96) -> list[float] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py), line 41)
- `build_report(vault: LoadedVault, repository: Repository, *, since: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py), line 139)
- `batch_review(repository: Repository, *, since: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py), line 212) — Slip, wording and unmatched readings, with the learner's text (owner only).
- `plan_report(repository: Repository, *, since: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py), line 226) — The dry run: population sizes only, nothing written.
- `render_markdown(report: Mapping[str, Any], review: list[dict[str, Any]]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py), line 236)
- `write_report(vault: LoadedVault, repository: Repository, out: Path, *, since: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py), line 291)

### Module constants

- `REPORT_VERSION` ([src/learnloop/diagnosis/text_gaps/report.py](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py), line 38)

### Explicit exports

`__all__` declares:

- `REPORT_VERSION`
- `batch_review`
- `build_report`
- `plan_report`
- `render_markdown`
- `wilson`
- `write_report`

## Internal implementation anchors

- `_rate(successes: int, trials: int) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py), line 51)
- `_pair_agreement(connection: Any, task: str, *, since: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py), line 56) — LLM vs Decider on the same pair (latest standing verdict of each).
- `_check_counts(rows: list[Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py), line 83)
- `_first_checks(vault: LoadedVault, repository: Repository, gaps: list[dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py), line 91) — The created prerequisites' light commitments and their delayed checks.
- `_card_taps(connection: Any, attempt_ids: set[str], *, since: str | None) -> int` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py), line 121) — T1's diagnosis-card "not the same mistake" taps on these answers.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]] — imports `build_report`, `plan_report`, `write_report`; statically calls `build_report`, `plan_report`, `write_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `module`; calls `gaps`, `jobs`, `reversals`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `FAILURE_VERDICTS`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `NEEDED_TASK`, `SAME_BELIEF_TASK`, `SAME_PREREQUISITE_TASK`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `LEARNER_TEXT_GAP_SOURCE`, `diagnosis_can_arrive`, `load_placement_state_from_connection`, `placement_active`; calls `diagnosis_can_arrive`, `load_placement_state_from_connection`, `placement_active`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `math`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followups_batch5_c5_ledger.py](../../../../../../../tests/test_followups_batch5_c5_ledger.py) — direct import
  - `test_a_notes_ledger_verdicts_have_the_shared_shape_and_the_report_reads_them`
- [tests/test_learner_text_gaps.py](../../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_slip_and_wording_are_signals_only_and_listed_for_batch_review`
- [tests/test_learner_text_gaps_flow.py](../../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_the_report_counts_per_kind_and_chooser_and_its_dry_run_writes_nothing`
- [tests/test_learner_text_gaps_rereview.py](../../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f6_only_a_tap_on_a_belief_answer_is_counted`
- [tests/test_learner_text_gaps_review.py](../../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f11_first_checks_per_chooser_survive_the_creation_switch_and_since_windows_everything`
  - `test_f11_pair_agreement_honours_since`
- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_the_gaps_report_skips_decider_failure_rows`

## Modification guidance

- Change report policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/text_gaps/report.py](../../../../../../../src/learnloop/diagnosis/text_gaps/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
