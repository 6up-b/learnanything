---
title: "learnloop.adaptive_difficulty.dose_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/dose_report.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/dose_report.py"
source_commit: "workspace/uncommitted @ HEAD b1c67e1f52ee99dcfab1eeca5de019d636162201"
source_commit_timestamp: "2026-11-06T11:48:24-05:00"
source_worktree_state: "modified"
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
  - "learnloop.adaptive_difficulty.dose_report module"
  - "src/learnloop/adaptive_difficulty/dose_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.dose_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.dose_report` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The dose-and-burden analysis (``ad_dose_report_v1``; spec_adaptive_difficulty_v1 §10.4, D20, D21).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py) |
| Source lines | 457 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD b1c67e1f52ee99dcfab1eeca5de019d636162201` |
| Commit timestamp | `2026-11-06T11:48:24-05:00` |

## Public API

- `coefficient_draws(view: Any, *, draws: int=DRAWS, seed: str=SEED) -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 67) — Posterior draws of each kind's two curve coefficients (``γ̄_m + δ_{κ,m}``) and of ``γ``, from the subject view's mixture over the grid.
- `curve(c1: np.ndarray | float, c2: np.ndarray | float, n: float) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 91)
- `points_gain(delta_logit: np.ndarray | float) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 96) — The rise in unassisted success at the band's centre (75%) from a logit shift, at warmth 0.
- `nnls(X: np.ndarray, y: np.ndarray, iterations: int=5000) -> np.ndarray` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 103) — Non-negative least squares by projected gradient (small problems; deterministic).
- `minutes_per_event(visits: Sequence[Mapping[str, Any]], *, samples: int=1000) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 117) — Each kind's minutes per event (NNLS of visit active minutes on counts plus a constant).
- `useful_dose(c1: np.ndarray, c2: np.ndarray, minutes: float | None, reference_per_minute: np.ndarray | float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 136) — ``n*``: the largest dose whose own event adds at least the practice reference per minute.
- `class OfferOutcome` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 164)
- `offer_effect(outcomes: Sequence[OfferOutcome], variant: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 173) — The offer's effect against ``none`` (Horvitz-Thompson with the logged propensities), its 95% interval and anytime-valid sequence, moderated by the dose already taken and the level band.
- `label(curve_sign: float | None, randomized: Mapping[str, Any] | None) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 209) — "tested by randomized offers" only when the arm's sequence excludes 0 and agrees in sign.
- `level_band(p: float | None) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 235)
- `moderated_contrasts(records: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 251) — Observational "helps when" contrasts (§10.4): per kind, the realized cold success of first attempts after at least one event of the kind against those after none, within each predicted level band (the forecast fixed before the attempt), and per subkind moderator (answer mode, qu…
- `helps_when_lines(contrasts: Mapping[str, Mapping[str, Any]], randomized: Mapping[str, Mapping[str, Any] | None]) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 279) — A "helps when" line appears only when its moderated contrast's interval excludes 0 (and the contrast is a help); "tested by randomized offers" when the offers' moderated estimate agrees in sign with an interval excluding 0, else "what preceded better recall for you".
- `recommendation(kind: str, n_star: Mapping[str, Any], tag: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 305)
- `lesson_draws(view: Any, subkind: str, *, draws: int=DRAWS, seed: str=SEED) -> tuple[np.ndarray, np.ndarray, str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 320) — Teacher TE3a: posterior draws of a lesson subkind's two curve coefficients from the subject view's mixture (as :func:`coefficient_draws`), or from the seeded prior (``ad_lesson_priors_v1``) while the bank has no lesson coordinate; and which of the two it is.
- `lesson_row(view: Any, inputs: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 345) — Teacher TE3a (spec_teacher_v1 rev 5 §14.2): the ``lesson`` row.
- `analyse(view: Any, *, visits: Sequence[Mapping[str, Any]], answer_minutes: float | None, median_doses: Mapping[str, float], offers: Mapping[str, Sequence[OfferOutcome]] | None=None, records: Sequence[Mapping[str, Any]]=(), lessons: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 380) — The whole section (``ad_dose_report_v1``): curves, gains, minutes, useful doses, offers, lines; with ``lessons`` (teacher TE3a, while lesson opportunities are live), the ``lesson`` row and its lines.

### Module constants

- `DOSE_REPORT_VERSION` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 45)
- `DRAWS` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 46)
- `SEED` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 47)
- `BAND_CENTRE` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 48)
- `MAX_DOSE` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 49)
- `KIND_NAMES` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 50)
- `TESTED` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 56)
- `OBSERVATIONAL` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 57)
- `CANT_TELL` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 58)
- `LEVEL_BANDS` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 221)
- `BAND_TEXT` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 222)
- `SUBKIND_MODERATORS` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 225)
- `SUBKIND_TEXT` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 229)
- `LESSON_NAME` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 316)
- `PRIOR_ONLY` ([src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 317)

### Explicit exports

`__all__` declares:

- `CANT_TELL`
- `DOSE_REPORT_VERSION`
- `KIND_NAMES`
- `OBSERVATIONAL`
- `OfferOutcome`
- `TESTED`
- `analyse`
- `coefficient_draws`
- `curve`
- `helps_when_lines`
- `label`
- `lesson_draws`
- `lesson_row`
- `level_band`
- `minutes_per_event`
- `moderated_contrasts`
- `nnls`
- `offer_effect`
- `points_gain`
- `recommendation`
- `useful_dose`

## Internal implementation anchors

- `_seed(text: str) -> int` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 61)
- `_difference(with_rows: Sequence[float], without_rows: Sequence[float]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 241)
- `_excludes_zero(interval: Sequence[float] | None) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py), line 275)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `module`; statically calls `OfferOutcome`, `analyse`
- [[Reference/Modules/learnloop/sim/ad_gates|learnloop.sim.ad_gates]] — imports `module`; statically calls `label`, `offer_effect`
- [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]] — imports `MAX_DOSE`, `OfferOutcome`, `module`, `points_gain`; statically calls `OfferOutcome`, `nnls`, `points_gain`, `useful_dose`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `module`; calls `dose_basis`, `residual_success`, `success_inverse`
- [[Reference/Modules/learnloop/adaptive_difficulty/monitoring|learnloop.adaptive_difficulty.monitoring]] — imports `module`; calls `confidence_sequence`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`; calls `lesson_coordinate`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]], [[Reference/Modules/learnloop/sim/ad_gates|learnloop.sim.ad_gates]], [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad3_dose_arm.py](../../../../../../tests/test_ad3_dose_arm.py) — direct import
  - `test_cant_tell_exactly_when_the_interval_is_wide_or_minutes_unknown`
  - `test_dose_report_recommendation_follows_fitted_curves`
  - `test_helps_when_lines_only_when_the_moderated_contrast_excludes_zero`
  - `test_recommendations_never_act`
  - `test_tested_label_only_when_the_offers_agree_in_sign_and_exclude_zero`
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_the_reports_lesson_row_at_the_prior_and_after_lessons`

## Modification guidance

- Make changes here when the responsibility remains dose report within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/dose_report.py](../../../../../../src/learnloop/adaptive_difficulty/dose_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
