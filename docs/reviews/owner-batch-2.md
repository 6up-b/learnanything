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
