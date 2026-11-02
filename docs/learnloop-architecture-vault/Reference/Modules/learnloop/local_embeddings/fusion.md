---
title: "learnloop.local_embeddings.fusion"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/local_embeddings/fusion.py"
source_paths:
  - "src/learnloop/local_embeddings/fusion.py"
source_commit: "1ccb33cf698b65745ab5669ac3b1fd9888dd860e"
source_commit_timestamp: "2026-10-24T21:00:05-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.local_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.local_embeddings.fusion module"
  - "src/learnloop/local_embeddings/fusion.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-local-embeddings"
---

# `learnloop.local_embeddings.fusion`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.local_embeddings.fusion` exists within [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] to own the behavior summarized by its module contract: Learned rank fusion across embedding spaces (spec_local_contextual_retrieval_v1 §5.2, §9.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/local_embeddings/fusion.py](../../../../../../src/learnloop/local_embeddings/fusion.py) |
| Source lines | 560 |
| Owning package | [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1ccb33cf698b65745ab5669ac3b1fd9888dd860e` |
| Commit timestamp | `2026-10-24T21:00:05-04:00` |

## Public API

- `list_key(name: str, space_id: str | None=None, encoder_id: str | None=None) -> str` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 109) — A list's immutable identity: its name, its space id, and (for a local space) its query encoder id (Codex review F12).
- `list_name(key: str) -> str` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 117)
- `seed_weights(default: str, lists: Sequence[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 126)
- `feature_row(ranks: Mapping[str, int], lists: Sequence[str], rrf_k: float) -> np.ndarray` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 130)
- `examination_seed(position: int) -> float` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 134)
- `parse_feedback(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 218) — Group feedback rows into queries with their delivered spans and signals.
- `fit_examination(queries: Sequence[Mapping[str, Any]]) -> dict[int, float]` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 280) — Relative examination by position from randomized (explored) deliveries: a Beta posterior per position seeded at ``1/pos`` with one pseudo-observation, normalized to position 1.
- `fit_context(queries, lists, rrf_k, examination, types, mean0_beta: np.ndarray | None)` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 302) — One context's MAP fit under the examination-and-relevance likelihood (or None without data).
- `refit(rows: Sequence[Mapping[str, Any]], *, default: str, rrf_k_seed: float) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 335) — Every context's posterior from the feedback rows (deterministic; replay-safe).
- `posterior_for(posteriors: Mapping[str, Mapping[str, Any]], consumer: str, query_kind: str) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 386) — The context's posterior, else the consumer-agnostic global one (partial pooling's fallback).
- `learned_weights(posterior: Mapping[str, Any] | None, available: Sequence[str]) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 414) — The posterior mean's ``max(beta, 0)`` renormalized over ``available`` (logged; None: no posterior or no positive weight).
- `thompson_weights(posterior: Mapping[str, Any] | None, available: Sequence[str], *, seed: int) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 428) — A Thompson draw of the weights (§5.2): ``max(beta, 0)`` of one posterior draw, renormalized over ``available``.
- `selection_propensity(posterior: Mapping[str, Any] | None, available: Sequence[str], policy: Callable[[frozenset[str]], frozenset[str]], chosen: frozenset[str], *, seed: int) -> tuple[float, dict[str, float]]` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 446) — The probability that the resolver's selection ``policy``, applied to a Thompson draw from ``posterior`` over ``available``, selects exactly ``chosen``, and each list's probability of being selected (Codex re-review F18).
- `explore(order: Sequence[str], features: Mapping[str, np.ndarray], posterior: Mapping[str, Any] | None, lists: Sequence[str], *, seed: int) -> tuple[list[str], dict[str, Any]]` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 482) — Reorder only the spans the posterior cannot order (Thompson draw within tie bands); returns the new order and each moved span's propensity.
- `refit_posteriors(vault: Any, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 533) — Recompute ``retrieval_fusion_posteriors`` from every feedback row, in order (the replayer's body, ``learnloop embeddings fusion refit`` and the ingest host's background refresh).
- `rng_seed(receipt_id: str) -> int` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 551) — The draw's seed, keyed by the query receipt (a replay is reproducible).

### Module constants

- `FIT_VERSION` ([src/learnloop/local_embeddings/fusion.py](../../../../../../src/learnloop/local_embeddings/fusion.py), line 75)
- `SPACE_LISTS` ([src/learnloop/local_embeddings/fusion.py](../../../../../../src/learnloop/local_embeddings/fusion.py), line 76)
- `SIGNAL_TYPES` ([src/learnloop/local_embeddings/fusion.py](../../../../../../src/learnloop/local_embeddings/fusion.py), line 77)
- `GLOBAL` ([src/learnloop/local_embeddings/fusion.py](../../../../../../src/learnloop/local_embeddings/fusion.py), line 78)
- `NEWTON_STEPS` ([src/learnloop/local_embeddings/fusion.py](../../../../../../src/learnloop/local_embeddings/fusion.py), line 80)
- `NEWTON_TOLERANCE` ([src/learnloop/local_embeddings/fusion.py](../../../../../../src/learnloop/local_embeddings/fusion.py), line 81)
- `PROPENSITY_DRAWS` ([src/learnloop/local_embeddings/fusion.py](../../../../../../src/learnloop/local_embeddings/fusion.py), line 83)
- `RRF_K_GRID` ([src/learnloop/local_embeddings/fusion.py](../../../../../../src/learnloop/local_embeddings/fusion.py), line 85)
- `MIN_PROPENSITY` ([src/learnloop/local_embeddings/fusion.py](../../../../../../src/learnloop/local_embeddings/fusion.py), line 87)
- `SELECTION_DRAWS` ([src/learnloop/local_embeddings/fusion.py](../../../../../../src/learnloop/local_embeddings/fusion.py), line 90)
- `PRIOR_BASIS` ([src/learnloop/local_embeddings/fusion.py](../../../../../../src/learnloop/local_embeddings/fusion.py), line 92)

### Explicit exports

`__all__` declares:

- `FIT_VERSION`
- `GLOBAL`
- `PRIOR_BASIS`
- `SIGNAL_TYPES`
- `SPACE_LISTS`
- `examination_seed`
- `explore`
- `feature_row`
- `fit_context`
- `fit_examination`
- `learned_weights`
- `list_key`
- `list_name`
- `parse_feedback`
- `posterior_for`
- `refit`
- `refit_posteriors`
- `rng_seed`
- `seed_weights`
- `selection_propensity`
- `thompson_weights`

## Internal implementation anchors

- `_order(keys: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 121)
- `_sigmoid(z: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 138)
- `_probabilities(design: np.ndarray, theta: np.ndarray, examined: np.ndarray) -> tuple[np.ndarray, np.ndarray]` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 142) — ``(p, dp/dz)`` of the examination-and-relevance likelihood ``p = e * sigma(z)``.
- `_information(design: np.ndarray, weights: np.ndarray, p: np.ndarray, dp: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 150)
- `_map_fit(design: np.ndarray, y: np.ndarray, weights: np.ndarray, examined: np.ndarray, mean0: np.ndarray, precision0: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 154) — MAP of ``P(y = 1) = e * sigma(x .
- `_unit_information(design: np.ndarray, weights: np.ndarray, examined: np.ndarray, at: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 200) — The prior precision worth one observation: the average weighted Fisher information at ``at``.
- `_logit(rate: float) -> float` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 213)
- `_set_propensity(payload: Mapping[str, Any], lists: Sequence[str], ranked: set[str]) -> float` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 237) — The logged probability that the resolver's policy selected the set of lists this search queried (:func:`selection_propensity`, recorded at serve time; Codex re-review F18), consumed as recorded; 1 under the seed, whose selection is not random.
- `_observations(queries: Sequence[Mapping[str, Any]], lists: Sequence[str], rrf_k: float, examination: Mapping[int, float], types: Sequence[str])` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 248) — Design rows ``[features, one-hot signal type]``, outcomes, IPS weights and examination.
- `_explored(query: Mapping[str, Any], delivered: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 276)
- `_default_scale(queries, default_key, rrf_k, examination, types) -> float` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 323) — The default-only maximum-likelihood coefficient: the seed's scale (empirical).
- `_row(key, consumer, kind, lists, types, fit, examination, rrf_k, digest, fitted_at) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 374)
- `_marginals(posterior: Mapping[str, Any], keys: Sequence[str]) -> tuple[np.ndarray, np.ndarray]` ([source](../../../../../../src/learnloop/local_embeddings/fusion.py), line 393) — Mean and covariance over ``keys``; a key the posterior lacks gets mean 0 and the widest marginal variance it holds (``unseen_list``).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `refit_posteriors`; statically calls `refit_posteriors`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `refit_posteriors`; statically calls `refit_posteriors`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `module`, `refit_posteriors`; statically calls `explore`, `feature_row`, `rng_seed`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `module`; statically calls `learned_weights`, `list_key`, `posterior_for`, `rng_seed`, `seed_weights`, `selection_propensity`, `thompson_weights`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `refit_posteriors`; statically calls `refit_posteriors`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/retrieval_spaces|learnloop.db.stores.retrieval_spaces]] — imports `feedback_rows`, `has_tables`, `replace_fusion_posteriors`; calls `feedback_rows`, `has_tables`, `replace_fusion_posteriors`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]], [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_local_fusion_core.py](../../../../../../tests/test_local_fusion_core.py) — direct import
  - `test_examination_is_learned_only_from_randomized_deliveries`
  - `test_exploration_moves_nothing_without_a_posterior_and_only_inside_the_tie_band`
  - `test_no_feedback_means_the_seed`
  - `test_signals_move_the_learned_weights_toward_the_list_that_finds_what_is_cited`
  - `test_the_fit_recovers_relevance_under_a_known_position_bias`
  - `test_the_refit_is_deterministic_and_replay_safe`
  - `test_the_selection_propensity_is_the_policys_joint_probability`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_a_challenger_learns_its_way_up_from_resolver_receipts`
  - `test_a_successor_space_never_inherits_its_predecessors_weights`
  - `test_exploration_is_its_own_switch_and_logs_its_delivered_propensities`
  - `test_signals_join_their_delivery_and_the_posterior_replays_byte_identically`
  - `test_the_logged_selection_probability_is_the_resolvers_joint_one`

## Modification guidance

- Make changes here when the responsibility remains fusion within learnloop.local_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/local_embeddings/fusion.py](../../../../../../src/learnloop/local_embeddings/fusion.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
