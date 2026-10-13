# Owner batch 2: T1 guard advisory, B1 fixes

Branch `fix/owner-batch-2` from `main` at `b2a2bd2e`. Owner-directed (2026-10-12).
Prompt: `docs/specs/implementation_handoffs.md` §4, "Owner batch: T1 guard
advisory, B1 fixes", plus item 2d sent by the coordinator during the stage (the
writer's output budget, found in the owner's second real run).

## Plan (written before coding)

**1. T1's upgrade guard becomes advisory.**
- `config/schema.py`: `recurrence.require_guard: bool = False`.
- `diagnosis/recurrence/upgrade.py`: `upgrade_to_mvp012` still computes the
  guard's status for the configured judge. With `require_guard = false` (the
  default) it no longer refuses: the result carries notes with the guard's
  status (judged / missing / false merges on either path, the citation-path
  check) and what an M1 run with planted cases would add, and the upgrade
  proceeds. With `require_guard = true` every earlier refusal is restored
  unchanged, including "the judge route names no model".
- `ops/vault_upgrade.py`: `UpgradeResult.notes` (advisory lines, printed on
  success). `cli/app.py` prints them; the help text drops "refused while".
- No version semantics change: `mvp-0.12` means what it meant; only whether
  `upgrade` refuses moves. Kill switch unchanged (`recurrence.enabled`).
- The new config key moves every effective-defaults snapshot (mvp-0.9 to
  mvp-0.12), so all four are recomputed with `defaults_fingerprint_for_version`;
  the configuration reference is regenerated.
- Docs: spec_embedding_consumers_v1 §3.6, the guard and upgrade docstrings,
  `Algorithm Versions and Reproducibility.md`.

**2. B1 fixes** (`diagnosis/recurrence/benchmarks.py`, `ops/pf_calls.py`,
`ops/embedding_compare.py`, `cli/embeddings.py`, `cli/recurrence.py`).
- a. The hypothesis cache key includes the writer identity: model, profile type,
  endpoint, reasoning effort, thinking, response format, profile max_tokens and
  the writer output budget. The dry run computes it from config the same way the
  run computes it from the resolved role client, so the plan's "cached" count
  matches the run. Rows without a writer are ignored.
- b. B1 and B3 get `markdown_lines`, so the harness's `.md` renders their
  tables (recall@25 / MAP@25 per method, model and view) instead of falling
  through to the valid-alternative table.
- c. `PFCaller` records `billed`: the provider-reported cost of every physical
  request, by billing class, and how many requests reported none. The report's
  Markdown leads with it; "charged" (reservations, never refunded) stays as the
  cap-accounting line. `--input-price-per-million` / `--output-price-per-million`
  price input and output separately (admission, reservation and reconciliation);
  `--price-per-million` remains, labelled a single-rate upper bound.
- d. `--writer-output-tokens` (default 2000) on `embeddings compare` and
  `recurrence bench`, in the plan's tokens, the reservation, the request's
  `max_tokens` and the cache identity. A writer profile's `reasoning_effort`
  already reaches OpenRouter as `reasoning.effort`; a test pins that for the B1
  writer and the effort is in the cache identity. A truncated or invalid writer
  output is a failed case (not retried, not cached; a rerun asks again): it
  counts as a miss in the hypothesis view and the report counts failed cases by
  error type. Provider outages and caps still stop the run.

**Migrations:** none. **Algorithm successors:** none. **Spend caps and routes:**
unchanged (B1's writer stays the `recurrence_hypothesis_writer` role on the
`diagnosis` route). **`judgment_ledger` writes:** none new. **Paid calls:** none
(tests use fakes).

**Tests (written first, failing before the change):** advisory default upgrades
with notes (no guard run, a recorded false merge, the chain from mvp-0.9, the
CLI); `require_guard = true` keeps every refusal (the existing refusal tests run
with it); B1 cache identity (new writer, new effort, new budget, old rows);
B1 Markdown table; billed vs charged and split pricing; writer output budget in
plan and request; reasoning effort on the wire; a truncated case does not stop
the run.

## What was built

Commits on `fix/owner-batch-2`: `37e2723e` (plan and fail-first tests),
`947158bb` (implementation), `8ad534b9` (regenerated reference), then this
record.

### 1. T1's upgrade guard is advisory

- `recurrence.require_guard: bool = False` (`config/schema.py`).
- `diagnosis/recurrence/upgrade.py`:
  - `guard_findings(vault, repository)` returns why the guard has not passed
    for the configured judge, in the same wording as before (minus "before
    switching"), plus the guard status; "the judge route names no model" is
    one of the findings.
  - `upgrade_to_mvp012` refuses on findings only with `require_guard = true`;
    every earlier refusal, including the chain note ("the vault stays at
    mvp-0.9 ..."), comes back unchanged.
  - Otherwise it proceeds (chain included) and returns `advisory_notes`:
    - that the guard is advisory, with the kill switch;
    - the status: passed (judged count, citation path checked) or each
      finding prefixed "Guard status:";
    - when no M1 case was checked, what an M1 run with planted cases would
      add: the citation-path check, the diagnoser's own statements as judge
      cases, and standing registered cases, with the `--from-run` command;
    - how to restore the refusal.
- `UpgradeResult.notes` (`ops/vault_upgrade.py`); `learnloop upgrade` prints
  them under "Upgraded vault: ...".
- Version semantics unchanged: `mvp-0.12` serves what it served, the kill switch
  is still `recurrence.enabled`, and new vaults still start at `mvp-0.12`.
- The four defaults snapshots (mvp-0.9 to mvp-0.12) were recomputed with
  `defaults_fingerprint_for_version`; they move only because the effective
  config gains the key. Docs: spec_embedding_consumers_v1 §3.6 (owner-decision
  note), `Algorithm Versions and Reproducibility.md`, the guard, upgrade and
  `recurrence guard` docstrings.

### 2. B1 fixes

**a. Writer-keyed hypothesis cache** (`benchmarks.py`).
- Each row of `b1_hypotheses.jsonl` now holds `writer`:
  - the model;
  - the generation settings: profile `type`, `base_url`, `reasoning_effort`,
    `thinking`, `response_format` and `max_tokens`;
  - the output budget and the prompt version.
- The key hashes the case together with that writer.
- The dry run computes the writer from config (`configured_writer`, the same
  route resolution as `planned_role_clients`). The run computes it from the
  role client it actually calls: the resolved profile, or an injected client's
  profile. So the plan's `cached` count matches the run (tested on a
  configured OpenRouter route).
- Rows that name no writer model are ignored.
- `resolve_role_clients` also puts an injected client's generation settings in
  its PF checkpoint settings. Resolved clients already carried their full
  profile.

**b. Markdown.**
- `B1Suite.markdown_lines` and `B3Suite.markdown_lines` (`b1_markdown_lines` /
  `b3_markdown_lines`, shared with the local runner's `render_markdown`).
- The harness's `.md` now shows the recall@25 / MAP@25 table per method, model
  and view, plus the writer line and the failed-case line. Before, it fell
  through to the valid-alternative "Grader model" table, which is the empty
  table in the owner's `out/b1-1e07fe275d4142a6.md`.
- A failed run's `.md` now shows its `reason`.

**c. Billed vs charged** (`ops/pf_calls.py`, `ops/embedding_compare.py`).
- `PFCaller.billed()` sums the cost the provider reported on every physical
  request, by billing class. That includes truncated and failed requests,
  which were still paid for, and embeddings. It reports:
  - `requests` and `requests_reporting_cost`;
  - `usd = None` when requests ran and none reported a cost.
- `report()` carries `billed`, `charged` and `pricing`.
- The harness Markdown has a "Spend" section:
  - **Billed (provider-reported)** comes first;
  - then "Charged (cap accounting, reservation-based: the input bound plus
    the full output budget per request, never refunded)", against the cap;
  - then the pricing basis.
- `--input-price-per-million` / `--output-price-per-million` (both or neither;
  not together with `--price-per-million`) price:
  - plan admission: a role's `output_tokens` share at the output rate, the
    rest at the input rate;
  - each request's reservation;
  - reconciliation (reported input and output priced separately, or the
    provider's cost if higher).
- `--price-per-million` remains, labelled in help, report and Markdown as one
  rate for input and output, an upper bound. A role that does not split its
  plan is priced at the higher of the two rates.
- The spend framework's never-refund rule is unchanged, so "charged" is still
  an upper bound by design; it is no longer the headline.

**d. Writer output budget, reasoning effort, failed cases.**
- `--writer-output-tokens` (default `B1_DEFAULT_WRITER_OUTPUT_TOKENS = 2000`;
  was a fixed 300) is on `embeddings compare` and `recurrence bench`
  (`CompareRequest`/`BenchRequest.writer_output_tokens`). It is used in:
  - the plan's tokens, with a separate `output_tokens` share;
  - the reservation;
  - the request's `max_tokens` (through `generation_limit`);
  - the cache identity.
- Reasoning effort: the OpenRouter provider already sends a profile's
  `reasoning_effort` as `extra_body.reasoning.effort`, unless `thinking =
  "disabled"` (`ai/providers/openrouter.py`). Nothing blocked it for the B1
  writer.
  - A test now pins it on the owner's path: a configured OpenRouter writer
    with `reasoning_effort = "low"` sends `{"reasoning": {"effort": "low"}}`
    and `max_tokens = 2000` on every request.
  - The effort is part of the writer identity and the report.
- Failed cases: B1 calls `PFCaller.call(..., retry_invalid_output=False)`, a
  new keyword whose default is unchanged. (As first committed the keyword was
  `retry_truncated` and only skipped retrying a truncation, and a blank
  hypothesis was checkpointed before B1 rejected it, so the claim below did
  not hold for malformed or blank outputs; fixed after the Codex review, see
  `owner-batch-2-codex-review.md`, F1 and F2.)
  - An `AIInvalidOutput` (truncated, malformed, or a blank hypothesis, which
    `MisconceptionHypothesis` now rejects at parse time) is one failed case.
    It is not retried, never cached or checkpointed (a rerun asks again for
    it only), and counts as a miss in the hypothesis view (`n` stays equal
    to the raw view's).
  - `results.writer` reports `written`, `cached`, `failed_cases` and
    `failed_by_error`, plus `resolved_models`, `settings` and
    `output_tokens`.
  - Provider outages, caps and cancellation still stop the run as before.

## Deviations

- The local runner (`run_bench`, `BenchContext`) has had no CLI entry since
  the harness merged (`recurrence bench` aliases `embeddings compare`). It got
  the writer budget, the writer-keyed cache and the shared Markdown, but not
  `billed`: its `ReviewSpend` already prefers reported cost per route.
- `retry_invalid_output` is opt-out per call, not a global PF change: other
  PF roles keep retrying an invalid output.
- Exact fail-first counts are recorded for B1 only:
  `tests/test_recurrence_benchmarks.py` at `37e2723e` gave 10 failed, 11
  passed. The T1 tests failed at `37e2723e` on `'RecurrenceConfig' object has
  no attribute 'require_guard'` (run with `-x`). A later replay of the new
  tests against the old source in a scratch copy was abandoned: that copy
  lacked `migrations/`, so its failures were not meaningful.

## Tests

New, in `tests/test_recurrence_commands.py`:
- `test_the_guard_is_advisory_by_default`
- `test_an_advisory_guard_reports_a_recorded_false_merge_and_still_upgrades`
- `test_an_advisory_guard_that_passed_says_so`
- `test_the_advisory_upgrade_chains_without_a_guard_run` (`mvp-0.9`,
  `mvp-0.11`)
- `test_require_guard_restores_the_refusal`
- `test_a_judge_route_without_a_model_is_advisory_too`
- `test_the_upgrade_command_prints_the_advisory_guard_status`

The existing refusal tests run with `require_guard = true` (`_mvp010(...,
require_guard=True)`, `REQUIRE_GUARD`). `tests/test_mvp011_upgrade.py`'s
default-target check now expects the advisory upgrade to proceed.

New, in `tests/test_recurrence_benchmarks.py`:
- `test_b1_hypothesis_cache_is_keyed_by_the_writer_and_its_settings`: a new
  model, effort or budget writes anew; the same writer reuses.
- `test_b1_ignores_cache_rows_without_a_writer`
- `test_b1_markdown_renders_the_results_table`
- `test_b3_markdown_renders_its_table_on_the_harness`
- `test_b1_writer_output_budget_defaults_to_2000_and_is_planned`
- `test_a_truncated_writer_call_is_a_failed_case_not_a_failed_run`
- `test_the_openrouter_writer_carries_its_effort_and_budget_and_the_bill_is_the_headline`
- `test_a_length_finish_from_openrouter_is_one_failed_case`
- `test_split_pricing_admits_less_than_a_single_upper_bound_rate`
- `test_the_cli_takes_the_writer_budget_and_split_prices`

Test support changes:
- `tests/openai_fakes.py`: a queued response may be a ready-made completion
  (`finish_reason`, `usage.cost`).
- `tests/cli_help_snapshot.json` is refreshed for `upgrade`, `embeddings
  compare`, `recurrence bench` and `recurrence guard`.

## Gate (at `8ad534b9`; this record adds docs only)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` | ok |
| `uv pip install pypdfium2` | ok (5.14.0) |
| `uv run lint-imports --no-cache` | 12 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8280 passed**, 0 failed (5m14s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **87 passed**, 8193 deselected |
| `db_generate_reference.py` / `db_validate_reference.py` | `errors: []`, 298 table notes, 657 configuration leaves (was 656) |
| `validate_vault.py` | passed, 1069 notes |
| Frontend | not changed, so not run |

All runs used `TMPDIR` = the worktree's `fixtures-local/tmp`.

## Files touched

- **Source:**
  - `src/learnloop/config/schema.py`
  - `src/learnloop/config/template.py`
  - `src/learnloop/ops/vault_upgrade.py`
  - `src/learnloop/diagnosis/recurrence/upgrade.py`
  - `src/learnloop/diagnosis/recurrence/guard.py` (docstring)
  - `src/learnloop/cli/app.py`
  - `src/learnloop/diagnosis/recurrence/benchmarks.py`
  - `src/learnloop/ops/pf_calls.py`
  - `src/learnloop/ops/embedding_compare.py`
  - `src/learnloop/cli/embeddings.py`
  - `src/learnloop/cli/recurrence.py`
- **Tests:** the five files listed above, including the help snapshot.
- **Docs:**
  - `docs/specs/spec_embedding_consumers_v1.md`
  - `docs/learnloop-architecture-vault/Concepts/Algorithm Versions and Reproducibility.md`
  - the regenerated `Reference/` notes, which stamp every note with the
    source commit
  - this file

## Migrations, ledger, paid calls

- No migration and no new table.
- No `judgment_ledger` write.
- No paid call: tests use fakes, and no real call was needed to verify an
  interface. The owner's B1 run outputs under the main checkout's
  `fixtures-local/b1-run/` were read only.

## Owner-run commands

**B1 rerun.** Run on the existing backup copy
`fixtures-local/b1-run/linear_algebra` (main checkout), with a new output
directory.
- The writer is the `diagnosis` route of that copy. For GPT-6 Luna, add
  `reasoning_effort = "low"` to its OpenRouter profile; Haiku 5.5 needs no
  effort.
- Fill in the model's current OpenRouter input and output prices.
- Dry-run first:

```bash
uv run learnloop recurrence bench --vault fixtures-local/b1-run/linear_algebra --suite b1 \
  --benchmark <eedi dir> --output fixtures-local/b1-run/run-<writer>-2 \
  --model qwen/qwen3-embedding-8b --model openai/text-embedding-3-small --max-cases 400 \
  --writer-output-tokens 2000 --input-price-per-million <in> --output-price-per-million <out> \
  --embedding-price-per-million 0.02 --max-calls 700 --max-cost-usd <cap> --dry-run
# then the same command without --dry-run
```

- The report's `.md` leads with the billed amount. A rerun into an old output
  directory reuses nothing written by another writer or under another budget;
  failed cases are retried on the next run.
- With split prices the reservation per call is far lower than at 1.6/M for
  everything, but each call still reserves the full 2000-token output budget.
  Size `--max-cost-usd` to the dry run's estimate.

**T1 upgrade.** Unchanged for vaults that should wait:
`recurrence.require_guard = true` keeps the old refusal. Otherwise `learnloop
upgrade --vault <copy>` proceeds and prints the guard status. The playbook's
shadow rebuild on a backup copy still comes first: `learnloop rebuild --shadow
--json --vault <copy>`.

## Open questions

1. **Failed cases count as misses in the hypothesis view.** This is the honest
   end-to-end number at that budget, and the raw view is unaffected.
   Alternatively, report the hypothesis view only over cases that got a
   hypothesis, beside the miss-counting one. The counts are in the report
   either way.
2. **A fully cached rerun now builds the writer's client** to learn its
   identity. An unready writer route therefore fails the run even when every
   hypothesis is cached.
3. **A writer whose model is unknown** (profile and client name none) writes
   rows that are never reused. This is deliberate ("without a model:
   ignored"), at the cost of rewriting.
4. **Plain `openai_chat` profiles** (an OpenAI key, not OpenRouter) still send
   `reasoning_effort` only together with `thinking` (the DeepSeek dialect). A
   direct OpenAI reasoning model as the B1 writer would need that changed;
   OpenRouter routes are fine.
5. **The B1 writer shares the `diagnosis` route.** A dedicated
   `ai.routing.recurrence_hypothesis_writer` route would let a benchmark use a
   different model or effort than live diagnosis without editing the copy's
   diagnosis profile.
6. **"Charged" still never refunds** (spend-framework rule). With the bill as
   the headline that is cap accounting only. Refunding unused output
   reservations would let tighter caps admit more work. That would be a change
   to `ai/spend.py`, outside this batch.
