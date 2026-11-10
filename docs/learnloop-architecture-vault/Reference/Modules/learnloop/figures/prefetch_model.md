---
title: "learnloop.figures.prefetch_model"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/prefetch_model.py"
source_paths:
  - "src/learnloop/figures/prefetch_model.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.prefetch_model module"
  - "src/learnloop/figures/prefetch_model.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.prefetch_model`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.prefetch_model` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5d P5: the prefetch decision model (spec_reader_show_me_figures_v1 §10b.3, §10b.5, §15).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py) |
| Source lines | 633 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Observation` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 141) — One closed, built decision: its trigger, source, judge probability and whether it was opened.
- `class OpenPosterior` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 158) — A mixture over the pooling grid of Gaussian posteriors on the opening coefficients.
  - `_index(self, kind: str) -> int` (line 169; internal)
  - `features(self, trigger_kind: str, source: str | None, p_open_content: float | None) -> np.ndarray` (line 172; public)
  - `summary(self) -> dict[str, Any]` (line 182; public) — Prior to posterior on alpha and beta_kind (LP §3.3 contraction), for the report.
  - `sample(self, rng: np.random.Generator) -> np.ndarray` (line 209; public)
- `open_posterior(observations: Iterable[Observation]) -> OpenPosterior` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 226) — Filter the closed, built decisions (in the order given: time order) on every grid point.
- `class PlanDay` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 249) — One past local day with plan activity: its load and whether a usage-limit pause was hit.
- `tokens_per_request(days: Iterable[PlanDay]) -> float | None` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 259) — The measured mean tokens of a request that reported them, or None (none reported).
- `class PausePosterior` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 269)
  - `standardized(self, load: float) -> float` (line 279; public)
  - `load(self, day: PlanDay) -> float` (line 282; public)
  - `summary(self) -> dict[str, Any]` (line 285; public)
- `plan_load(day: PlanDay | Mapping[str, Any], per_request: float | None=None) -> float` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 295) — A day's plan load in requests, with the known tokens in it (spec §10b.3: "the day's plan requests, plus tokens where known"; Codex review F14).
- `pause_posterior(days: Sequence[PlanDay]) -> PausePosterior` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 312)
- `class WaitEstimate` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 333) — The quick tiers' W from pressed author calls with a prior (``prefetch_decision_v2``), and its basis.
  - `facts(self) -> dict[str, Any]` (line 347; public) — Numbers only (a decision record's ``wait_estimate``, the report's ``estimate_by_tier``).
- `wait_estimate(pressed: Sequence[float], others: Sequence[float], *, strength: float=WAIT_PRIOR_STRENGTH) -> WaitEstimate` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 358) — W from pressed minutes with a prior seeded by the other measured minutes (pure).
- `class Waits` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 389) — Per tier, the log-normal mean of the measured pressed build latency (minutes), and the tier mixes.
  - `expected(self, trigger_kind: str) -> float | None` (line 399; public) — The expected minutes a prebuild for this trigger kind saves, or None (no measured tier).
  - `basis(self, trigger_kind: str) -> str` (line 414; public) — Which measurement :meth:`expected` reads for this kind: ``kind_mix``, ``pressed_mix``, ``author_call`` (no tier mix yet) or ``none`` (no measured tier: no estimate).
  - `summary(self) -> dict[str, Any]` (line 425; public)
- `lognormal_mean(minutes: Sequence[float]) -> float | None` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 437)
- `waits(latencies: Mapping[str, Sequence[float]], pressed_tiers: Sequence[str], prefetch_tiers_by_kind: Mapping[str, Sequence[str]] | None=None, estimates: Mapping[str, WaitEstimate] | None=None) -> Waits` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 453) — The measured waits.
- `class Incremental` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 482) — What one prebuild adds to the plan's load, measured (Codex review F14): the figure author's calls per authored request (a repair is a second call), and the rich author's calls per rich job.
  - `expected(self, rich_share: float) -> float` (line 490; public)
- `class Candidate` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 495)
- `class Decision` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 511)
- `class Model` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 524) — Everything a decision reads, recomputed from the ledger.
  - `expected_requests(self, trigger_kind: str) -> float` (line 543; public) — The plan requests a prebuild for this trigger kind is expected to make: the author's measured calls, plus the rich calls times the kind's measured rich share (else the pressed builds' share).
  - `digest(self) -> str` (line 551; public) — The posterior's identity, so an audit can recompute a decision.
  - `_draw(self, rng: np.random.Generator, candidate: Candidate, wait: float) -> tuple[float, float, float]` (line 569; internal)
  - `decide(self, candidate: Candidate, rng: np.random.Generator) -> Decision` (line 580; public) — One Thompson draw decides (build iff its EU > 0); the propensity is the share of :data:`POSTERIOR_DRAWS` further draws that would build.

### Module constants

- `MODEL_VERSION_V1` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 81)
- `MODEL_VERSION` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 84)
- `TRIGGER_KINDS` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 85)
- `RICH_TIERS` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 86)
- `QUICK_TIERS` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 87)
- `ALPHA_PRIOR_MEAN` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 91)
- `ALPHA_PRIOR_SD` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 92)
- `KIND_PRIOR_MEAN` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 94)
- `KIND_PRIOR_SD` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 95)
- `POOLING_GRID` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 98)
- `PAUSE_INTERCEPT_PRIOR_MEAN` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 100)
- `PAUSE_INTERCEPT_PRIOR_SD` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 101)
- `PAUSE_SLOPE_PRIOR_MEAN` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 102)
- `PAUSE_SLOPE_PRIOR_SD` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 103)
- `POSTERIOR_DRAWS` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 105)
- `P_CONTENT_CLIP` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 107)
- `WAIT_PRIOR_STRENGTH` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 114)
- `RULE_NO_MEASURED_LATENCY` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 505)
- `RULE_SAMPLED_EU_POSITIVE` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 506)
- `RULE_SAMPLED_EU_NOT_POSITIVE` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 507)

### Explicit exports

`__all__` declares:

- `ALPHA_PRIOR_MEAN`
- `ALPHA_PRIOR_SD`
- `KIND_PRIOR_MEAN`
- `KIND_PRIOR_SD`
- `MODEL_VERSION`
- `MODEL_VERSION_V1`
- `PAUSE_INTERCEPT_PRIOR_MEAN`
- `PAUSE_INTERCEPT_PRIOR_SD`
- `PAUSE_SLOPE_PRIOR_MEAN`
- `PAUSE_SLOPE_PRIOR_SD`
- `POOLING_GRID`
- `POSTERIOR_DRAWS`
- `P_CONTENT_CLIP`
- `QUICK_TIERS`
- `RICH_TIERS`
- `RULE_NO_MEASURED_LATENCY`
- `RULE_SAMPLED_EU_NOT_POSITIVE`
- `RULE_SAMPLED_EU_POSITIVE`
- `TRIGGER_KINDS`
- `WAIT_PRIOR_STRENGTH`
- `Candidate`
- `Decision`
- `Incremental`
- `Model`
- `Observation`
- `OpenPosterior`
- `PausePosterior`
- `PlanDay`
- `WaitEstimate`
- `Waits`
- `lognormal_mean`
- `open_posterior`
- `pause_posterior`
- `plan_load`
- `tokens_per_request`
- `wait_estimate`
- `waits`

## Internal implementation anchors

- `_logit(p: float) -> float` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 117)
- `_sigmoid(x: float) -> float` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 122)
- `_log_lik(y: int)` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 129)
- `class _Filter` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 151)
- `_prior(sources: Sequence[str], tau: float, sigma: float) -> _Filter` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 214)
- `_mix(tiers: Iterable[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 446)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `Candidate`
- [[Reference/Modules/learnloop/figures/prefetch_ledger|learnloop.figures.prefetch_ledger]] — imports `module`; statically calls `Incremental`, `Model`, `Observation`, `PlanDay`, `open_posterior`, `pause_posterior`, `wait_estimate`, `waits`
- [[Reference/Modules/learnloop/figures/records|learnloop.figures.records]] — imports `POSTERIOR_DRAWS`, `QUICK_TIERS`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adf_numeric|learnloop.adf_numeric]] — imports `adf_update`, `normalized_log_weights`; calls `adf_update`, `normalized_log_weights`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/figures/prefetch_ledger|learnloop.figures.prefetch_ledger]], [[Reference/Modules/learnloop/figures/records|learnloop.figures.records]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_decision_records.py](../../../../../../tests/test_figure_decision_records.py) — direct import
  - `test_deferred_and_capped_decisions_are_deferred_records`
  - `test_prebuilds_record_no_measured_latency_then_sampled_eu_positive_with_the_wait_and_seed`
  - `test_the_recorded_seed_redraws_the_pass_exactly`
- [tests/test_figure_wait_estimate.py](../../../../../../tests/test_figure_wait_estimate.py) — direct import
  - `test_at_the_tag_the_rows_say_v2_and_the_records_carry_ws_basis`
  - `test_background_calls_do_not_outweigh_the_presses_in_w`
  - `test_switched_off_or_below_the_tag_the_rows_say_v1_and_the_records_are_as_before`
  - `test_switched_off_w_the_blocked_minutes_and_the_digest_are_v1s_exactly`
  - `test_the_limits_are_v1s_w_with_no_press_and_the_presses_own_with_no_other_call`
  - `test_the_presses_weight_is_learned_as_n_over_n_plus_one_and_a_shift_never_widens_the_spread`
  - `test_the_reader_report_reads_the_ledger_as_the_decisions_do`
  - `test_the_wait_estimate_is_the_presses_shrunk_toward_the_other_calls_by_one_measurement`
  - `test_with_no_measured_pause_the_decision_its_propensity_and_the_order_are_the_same`
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_no_measured_wait_means_no_prebuild`
  - `test_plan_trigger_judges_the_reading_section_decides_logs_and_builds`
  - `test_the_opening_posterior_learns_from_closed_built_decisions`
  - `test_the_pause_cost_reads_measured_pauses`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f14_a_builds_expected_requests_are_measured`
  - `test_f14_known_tokens_move_the_load_and_missing_tokens_count_as_an_average_request`
- [tests/test_followups_batch6_prefetch_decided_once.py](../../../../../../tests/test_followups_batch6_prefetch_decided_once.py) — direct import
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains prefetch model within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
