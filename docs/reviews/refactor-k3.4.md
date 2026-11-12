# Refactor K3.4: the append call is bounded and checkpointed

Branch `refactor/k3.4-append-bounded`, based on main `72ace2968a` (K0 pins, K3.1-K3.3 and D2a landed). Step K3.4 of
arc K (`docs/specs/refactor_strategy_v3.md` §2.17), specified in `docs/reviews/k2-ingestion-strategy-2026-11-11.md`
§3.1 from the K2 map's KX2, KM4 and KB5.

Rules held: each fix starts from a test that fails on the base; no learner scoring change, no successor, no
`algorithm_version` change, no migration; no live model call; the append scopes and manifests keep their bytes
(the `K3.2.scope` pins did not move; the new ceiling is a refusal and stays out of the manifest's `token_budget`).

## Problem

The append call (and its one span round) had no per-call checkpoint, no request-level generation limit and no input
ceiling. Its output check ran after the paid call with an estimator that escapes non-ASCII, and a budget failure
went through `except StudyMapError: raise`, leaving the `agent_runs` and `synthesis_runs` rows `running` until
startup's sweep. A retry of any failed append re-paid the call (one or two calls).

## Failing tests (red on the base, green after)

Written and run before any source change, against the base sources (the K3.4 tests were the only edit in the tree):

`tests/test_source_append.py`:
- `test_a_retry_after_an_append_gate_failure_makes_no_model_call`: red, the retry called the model again (2 calls,
  expected 1). An exam-only facet reword hard-fails `exam_authority` deterministically. It also checks both run rows
  of both attempts end `failed`.
- `test_an_over_budget_append_answer_is_checkpointed_and_the_retry_does_not_repay`: red, 2 calls for two attempts
  under a 200-token output budget; after, 1, and a third attempt under a raised budget reuses the answer and completes.
- `test_an_append_budget_failure_leaves_both_run_rows_failed`: red, `(['running'], ['created'])`.
- `test_the_append_call_runs_under_its_output_limit`: red, the fake saw `output_limit() == None`; after, the budget.
- `test_an_append_over_its_input_ceiling_is_refused_before_any_call`: red, nothing raised and the call was paid;
  after, `append_input_over_ceiling` with zero calls, one `append_input_ceiling` diagnostic and both run rows
  `failed`, and the same append under the default ceiling goes through.
- `test_append_output_is_counted_without_escaping_non_ascii`: red, `budget_exceeded` for a CJK summary that fits
  (900 tokens escaped, 150 unescaped, budget 600).

`tests/test_keep_ahead_append_units.py`:
- `test_an_append_over_its_input_ceiling_fails_once_and_the_card_says_so`: a book through Add and one keep-ahead
  step with the house fakes and `append_input_ceiling = 1000` in the vault config. Red, the append was sent; after,
  nothing is sent, the build job fails with `append_input_over_ceiling` and `retryable: false`, and the book card's
  line is "Questions for Ch. 3 are too much to write at once" (problem tone, no action, the message in details).

## What changed

| File | What |
| --- | --- |
| `src/learnloop/content/synthesis/source_set_synthesis.py` | `_synthesis_pass_key` takes `purpose` (default `"synthesis_pass"`, so A14 is byte-identical); `_checkpointed_pass` takes the `result_model` it validates |
| `src/learnloop/content/synthesis/source_append.py` | `append_checkpoint_key(prompt, settings)`: the pass key builder under `purpose="append_reconciliation"` with the `AppendReconciliation` schema (no budget). `_AppendCall`: reads the checkpoint first; otherwise checks the estimated input (prompt plus schema, bootstrap's estimate) against `append_input_ceiling`, calls under `generation_limit(append_output_tokens)`, saves the answer before the output check; the output check (fresh or reused) uses bootstrap's non-escaping `_result_tokens`. An unlimited run has neither limit. The settings are a bootstrap pass's (`model_settings` plus the run's provider and model). `APPEND_INPUT_OVER_CEILING` and its typed `StudyMapError` with one diagnostic. The `StudyMapError` arm finalizes both run rows for every typed failure (the gate arm's own finalization folded into it; the agent run's message is now `code: message`, as bootstrap's). `_output_tokens` deleted |
| `src/learnloop/content/pipeline/jobs.py` | `handle_append_synthesis` maps `append_input_over_ceiling` to `retryable=False` (beside `source_set_not_found`); the comment says what a retry now does |
| `src/learnloop/content/pipeline/add_source.py` | the book card's line for that code: "Questions for {chapters} are too much to write at once", no Retry, the message (numbers and the setting) in details |
| `src/learnloop/config/schema.py` | `IngestBudgetsConfig.append_input_ceiling = 84000`, with the why; a comment on `append_output_tokens` saying it is now also the generation limit |
| `tests/goldens/effective_defaults.toml` | `ingest.budgets.append_input_ceiling = 84000`, added deliberately (`--write`) |
| `tests/identity_pins_helpers.py`, `tests/goldens/identities.toml`, `tests/goldens/identity_shapes.toml` | new site `K3.4` (the append checkpoint key, with and without the one-facet rule); `append_reconciliation_prompt` moves from provenance-only to that site's sources, and `AppendReconciliationContext` gets its shape pin |

## The defaults and why their values

- **`append_input_ceiling = 84000`** (new). The sum of what one append call is built from when its new material
  fits one bootstrap shard: the neighbourhood cap (`append_neighborhood_input_tokens`, 24000), one shard of new
  inventories (`synthesis_shard_input_tokens`, 40000), one span round (12 spans of at most 4000 characters, 12000)
  and the fixed part (8000: the room `synthesis_total_input_ceiling` leaves above its shard; the append's
  instructions and schema measure about 6600). Each uncheckpointed call is held to it, so a span round of an append
  whose first call fit is not refused. With K3.2 a keep-ahead append sends one build's units (the measured second
  build was about 3x10^4 inventory tokens), so routine appends stay well under it.
- **Output budget:** the existing `append_output_tokens = 10000`, now also the request's generation limit (as each
  bootstrap pass runs under its shard output budget). No new output default. The metered-build admission gate now
  sees the append's own ceiling (10000) where it reserved the larger synthesis default for a request that named none.
- **Not in `config/template.py`:** the template is decision-only by design (its docstring; every other default
  lives in `schema.py` and shows up in the effective-defaults golden), `test_generated_template_is_decision_only_schema_v2`
  bars modeled budgets from it, and it is at its 80-line cap. So the default and its why are in `schema.py` only.

## Pins

No K0 pin moved. `--write` added `K3.4.append_key` and `K3.4.append_key.one_facet_per_skill` and the
`AppendReconciliationContext` shape; A14 (the pass key) and `K3.2.scope.*` are unchanged. The effective-defaults
golden gained one line.

**One recorded digest moved, deliberately handled:** `tests/test_retired_config_identities.py`'s two whole-config
digests (`BASE_CONFIG_CONTENT_KEY`, `content_key` of the whole config dump, recorded at arc C's base `88607cb3fe`)
moved, because any new default changes a whole-config dump. Those digests exist to hold arc C's *deletions* to their
base; a new default is not a deletion. So the test now takes each default added since that base out before comparing
(`ADDED_SINCE_BASE`, one entry naming K3.4), which keeps the deletion guarantee tied to the recorded base instead of
re-recording it here. What moves in production: a report's whole-config `config_hash` (arc C review row 6: an
embedding-compare report's file name, so a rerun at a fixed input writes beside the earlier report; rows 7-11 are
provenance only). The synthesis manifests, the field arm hashes and the reuse scenarios in that file are unchanged
(they passed untouched). If the orchestrator prefers re-recording the two digests, that is the alternative. P-spend is by construction: a retry of a failed append (gate failure, over-budget answer)
reads the checkpoint and makes zero calls, as the tests show; an over-ceiling append makes none at all.

## Surfaces

- **Desktop book card** (`BookCard` renders `source_status_line`): "Questions for Ch. 3 are too much to write at
  once", problem tone, no action; details show the message ("This update's request comes to about N input tokens,
  over its ceiling of M ([ingest.budgets] append_input_ceiling), so nothing was sent."). Before this step's line, the
  card would have said "need another try" with a Retry that refuses the same way.
- **Desktop Activity panel** (`IngestActivity.tsx`): `append_input_over_ceiling: <message>`, "completed extraction
  and inventory work is preserved", one hard diagnostic with its next step, and "This failure requires configuration
  or scope changes before retrying" (it reads `retryable: false`). Its amber "retry synthesis only" box shows the
  generic recovery sentence; no frontend change.
- **Phone:** shows no book status lines; nothing to change.
- **The append RPC** (`append_source` in the sidecar) already raises `SidecarError(code, ...)` non-retryable.

## Vault

The reference notes were regenerated after the source commits (`_scripts/generate_all.py`, 79 generated notes,
mostly line numbers moved in `schema.py`, `source_append.py` and `add_source.py` citations); a second run changed
nothing. The two prose counts of effective configuration leaves (`Reference/Configuration/Configuration.md`,
`Reference/Database/Database.md`) move from 1180 to 1181 for the new default, as `db_validate_reference.py` requires.
No hand-written note says the append call is unbounded or uncheckpointed, so no other note changed.

## Gates

- Targeted tests: `scripts/affected_tests.py` on the source diff (865 files, `config/schema.py` reaches most of the
  suite) plus every added or edited test file, `test_identity_pins`, `test_retired_config_identities`,
  `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot` and
  `test_config_refactor`: 866 files, `-m "not arc_close"`, nine chunks of up to 100 at `-n 4` under the 5 GB cap:
  15,749 passed, 2 failed (the two whole-config digests above, then handled; that file and `test_identity_pins`
  re-run green), plus the 21 unselected test files that hold a digest (`config_hash`, `version_hash`,
  `manifest_hash` or a 64-hex literal): 528 passed.
- `lint-imports --no-cache`: 42 kept. `ruff check`: clean.
- The four vault validators pass (`db_validate_reference.py` after the two prose counts, `module_validate.py`,
  `desktop_validate.py`, `validate_vault.py`); `scripts/check_gate_partition.py`: 30,966 collected, landing 30,906
  + arc_close 60.
- No full suite (the orchestrator's landing gate).

## Open items

- **The oversized-append split waits for K2.4** (K2.4c: the append's new inventories through the shard runner,
  checkpointed passes split by new units). Until then an append over the ceiling is refused, and the learner's way
  through is a narrower build or a raised ceiling.
- **A retry after an append gate failure now reproduces it at zero cost** unless the vault changed (the prompt, and
  so the key, holds the neighbourhood, not every gate input). That is what the strategy asked (and what bootstrap's
  pass checkpoints already do), but the append has no candidate repair like bootstrap's, and the job stays
  `retryable` with the card's Retry. A fresh model turn after a gate failure needs the checkpoint dropped; the
  owner's call (or K2.1's helper could take a "discard on gate failure" policy).
- **The same for an over-budget answer:** a retry under the same budget fails again at zero cost; a raised budget
  reuses the paid answer. `budget_exceeded` stays retryable, as in bootstrap.
- `handle_append_synthesis` records `calls: 1` for a non-reused run even when the call came from the checkpoint
  (usage display only; real spend is in the receipts).
- **K2.1** moves `append_checkpoint_key` onto `checkpointed(...)` with a byte-identical key; the `K3.4` pin guards it.
