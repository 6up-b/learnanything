---
title: "learnloop.figures.prefetch_model"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/prefetch_model.py"
source_paths:
  - "src/learnloop/figures/prefetch_model.py"
source_commit: "ec2060b5e053639a05d205609eb9d564cee70209"
source_commit_timestamp: "2026-11-02T07:07:21-05:00"
source_worktree_state: "clean"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.prefetch_model` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5d P5: the prefetch decision model (spec_reader_show_me_figures_v1 §10b.3, §10b.5, §15).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py) |
| Source lines | 503 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `ec2060b5e053639a05d205609eb9d564cee70209` |
| Commit timestamp | `2026-11-02T07:07:21-05:00` |

## Public API

- `class Observation` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 121) — One closed, built decision: its trigger, source, judge probability and whether it was opened.
- `class OpenPosterior` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 138) — A mixture over the pooling grid of Gaussian posteriors on the opening coefficients.
  - `_index(self, kind: str) -> int` (line 149; internal)
  - `features(self, trigger_kind: str, source: str | None, p_open_content: float | None) -> np.ndarray` (line 152; public)
  - `summary(self) -> dict[str, Any]` (line 162; public) — Prior to posterior on alpha and beta_kind (LP §3.3 contraction), for the report.
  - `sample(self, rng: np.random.Generator) -> np.ndarray` (line 189; public)
- `open_posterior(observations: Iterable[Observation]) -> OpenPosterior` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 206) — Filter the closed, built decisions (in the order given: time order) on every grid point.
- `class PlanDay` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 229) — One past local day with plan activity: its load and whether a usage-limit pause was hit.
- `tokens_per_request(days: Iterable[PlanDay]) -> float | None` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 239) — The measured mean tokens of a request that reported them, or None (none reported).
- `class PausePosterior` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 249)
  - `standardized(self, load: float) -> float` (line 259; public)
  - `load(self, day: PlanDay) -> float` (line 262; public)
  - `summary(self) -> dict[str, Any]` (line 265; public)
- `plan_load(day: PlanDay | Mapping[str, Any], per_request: float | None=None) -> float` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 275) — A day's plan load in requests, with the known tokens in it (spec §10b.3: "the day's plan requests, plus tokens where known"; Codex review F14).
- `pause_posterior(days: Sequence[PlanDay]) -> PausePosterior` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 292)
- `class Waits` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 313) — Per tier, the log-normal mean of the measured pressed build latency (minutes), and the tier mixes.
  - `expected(self, trigger_kind: str) -> float | None` (line 321; public) — The expected minutes a prebuild for this trigger kind saves, or None (no measured tier).
  - `summary(self) -> dict[str, Any]` (line 336; public)
- `lognormal_mean(minutes: Sequence[float]) -> float | None` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 344)
- `waits(latencies: Mapping[str, Sequence[float]], pressed_tiers: Sequence[str], prefetch_tiers_by_kind: Mapping[str, Sequence[str]] | None=None) -> Waits` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 360)
- `class Incremental` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 378) — What one prebuild adds to the plan's load, measured (Codex review F14): the figure author's calls per authored request (a repair is a second call), and the rich author's calls per rich job.
  - `expected(self, rich_share: float) -> float` (line 386; public)
- `class Candidate` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 391)
- `class Decision` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 400)
- `class Model` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 411) — Everything a decision reads, recomputed from the ledger.
  - `expected_requests(self, trigger_kind: str) -> float` (line 424; public) — The plan requests a prebuild for this trigger kind is expected to make: the author's measured calls, plus the rich calls times the kind's measured rich share (else the pressed builds' share).
  - `digest(self) -> str` (line 432; public) — The posterior's identity, so an audit can recompute a decision.
  - `_draw(self, rng: np.random.Generator, candidate: Candidate, wait: float) -> tuple[float, float, float]` (line 448; internal)
  - `decide(self, candidate: Candidate, rng: np.random.Generator) -> Decision` (line 459; public) — One Thompson draw decides (build iff its EU > 0); the propensity is the share of :data:`POSTERIOR_DRAWS` further draws that would build.

### Module constants

- `MODEL_VERSION` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 71)
- `TRIGGER_KINDS` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 72)
- `RICH_TIERS` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 73)
- `QUICK_TIERS` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 74)
- `ALPHA_PRIOR_MEAN` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 78)
- `ALPHA_PRIOR_SD` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 79)
- `KIND_PRIOR_MEAN` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 81)
- `KIND_PRIOR_SD` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 82)
- `POOLING_GRID` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 85)
- `PAUSE_INTERCEPT_PRIOR_MEAN` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 87)
- `PAUSE_INTERCEPT_PRIOR_SD` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 88)
- `PAUSE_SLOPE_PRIOR_MEAN` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 89)
- `PAUSE_SLOPE_PRIOR_SD` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 90)
- `POSTERIOR_DRAWS` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 92)
- `P_CONTENT_CLIP` ([src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py), line 94)

### Explicit exports

`__all__` declares:

- `ALPHA_PRIOR_MEAN`
- `ALPHA_PRIOR_SD`
- `KIND_PRIOR_MEAN`
- `KIND_PRIOR_SD`
- `MODEL_VERSION`
- `PAUSE_INTERCEPT_PRIOR_MEAN`
- `PAUSE_INTERCEPT_PRIOR_SD`
- `PAUSE_SLOPE_PRIOR_MEAN`
- `PAUSE_SLOPE_PRIOR_SD`
- `POOLING_GRID`
- `POSTERIOR_DRAWS`
- `P_CONTENT_CLIP`
- `QUICK_TIERS`
- `RICH_TIERS`
- `TRIGGER_KINDS`
- `Candidate`
- `Decision`
- `Incremental`
- `Model`
- `Observation`
- `OpenPosterior`
- `PausePosterior`
- `PlanDay`
- `Waits`
- `lognormal_mean`
- `open_posterior`
- `pause_posterior`
- `plan_load`
- `tokens_per_request`
- `waits`

## Internal implementation anchors

- `_logit(p: float) -> float` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 97)
- `_sigmoid(x: float) -> float` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 102)
- `_log_lik(y: int)` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 109)
- `class _Filter` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 131)
- `_prior(sources: Sequence[str], tau: float, sigma: float) -> _Filter` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 194)
- `_mix(tiers: Iterable[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/figures/prefetch_model.py), line 353)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `Candidate`
- [[Reference/Modules/learnloop/figures/prefetch_ledger|learnloop.figures.prefetch_ledger]] — imports `module`; statically calls `Incremental`, `Model`, `Observation`, `PlanDay`, `open_posterior`, `pause_posterior`, `waits`

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

Static participation evidence comes from [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/figures/prefetch_ledger|learnloop.figures.prefetch_ledger]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_no_measured_wait_means_no_prebuild`
  - `test_plan_trigger_judges_the_reading_section_decides_logs_and_builds`
  - `test_the_opening_posterior_learns_from_closed_built_decisions`
  - `test_the_pause_cost_reads_measured_pauses`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f14_a_builds_expected_requests_are_measured`
  - `test_f14_known_tokens_move_the_load_and_missing_tokens_count_as_an_average_request`
- [tests/test_followups_batch6_prefetch_decided_once.py](../../../../../../tests/test_followups_batch6_prefetch_decided_once.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains prefetch model within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/prefetch_model.py](../../../../../../src/learnloop/figures/prefetch_model.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
