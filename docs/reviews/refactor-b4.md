# Refactor B4: figures

Step B4 of `docs/specs/refactor_strategy_v3.md` (§2.4, cases 3 and 4 of §3.6; the map's S7, S8, S9, S10 and `figures/service.py:2513`). Branch `refactor/b4-figures`, based on main `536963aa30` (B1 landed: ADR-017, `provenance.py`, migration 253, `why` a pure read).

**Result.** The figures' silent paths now leave decision records: every prefetch decision, every filter pass that excluded something, every stop of the build queue, and every figure author attempt. They're written through `provenance.write` (in the decision rows' transaction) or `db/stores/provenance.write_decision` (no second writer API), hold ids, numbers and codes only, and can't change a decision: a fake-model run of five prefetch passes and a pressed build is identical to main's apart from the new rows, and the author's and judge's prompts match a golden written from main's source. No migration, no successor tag, no change to what's served.

## Step 0: `owner_kind NOT LIKE 'prefetch%'` excludes nothing (a measurement bug, reported, not fixed)

The map couldn't verify whether the filter in `figures/prefetch_ledger.py:244` keeps prebuilds out of W. It doesn't. Every figure call's receipt carries `owner_kind = <the route's task>` (`figures/routes.py:552`, `PaidCalls(owner_kind=self.task)`), so a prebuild's author call is `figure_author`, exactly like a press's; the judge's is `figure_prefetch_judge` and a rich job's `figure_rich_author`. No figure receipt's owner kind starts with `prefetch`. The same holds for the blocked-minutes count (`prefetch_ledger.py:194`, `startswith("prefetch")`). The tests never caught it: `tests/test_figures_prefetch.py`'s `seed_wait` writes `owner_kind='sidecar_rpc'`.

Evidence on a backup-API copy of `~/learnloop-backups/20261109-copy` (counts only, script in the step's scratch directory; the author's `owner_id` is `figure:<content_key(input_hash, generation)>`, mapped to its request's `build_mode`):

| Vault | Figure receipts by owner kind | `LIKE 'prefetch%'` | `figure_author` receipts by build mode |
|---|---|---|---|
| arxiv_v2 | `figure_author` 23, `figure_prefetch_judge` 16 | 0 | pressed 2 completed; prefetch 20 completed, 1 failed |
| linear_algebra, probability | none | 0 | none |

**What it changes.** W (the quick tiers' wait) reads every completed `figure_author` call: on arxiv_v2 it's 0.483 min from 22 durations, 20 of them prebuilds' own background calls. Pressed calls alone give 0.636 min from 2. Today no pause is recorded, so the blocked minutes are unmeasured and the cost is 0: EU = p_open × W, the sign of every draw is the same either way, and so is every decision, the queue order and every propensity. What differs is the stored `sampled_eu` and `w_minutes`, about 24% low on this copy. It starts to change decisions once a usage-limit pause is measured, because then W is weighed against a cost: W would be biased toward background call durations, and failed prebuild calls inside a pause window would count as foreground minutes blocked (raising the cost). Prebuilds also measure their own W after the first press: 20 of 22 samples here. Fixing it changes EU, so it's the owner's call (a successor under `docs/algorithm-change-playbook.md`, filtering by `figure_requests.build_mode` through the owner id, or giving prefetch calls their own owner kind).

**Case 4 from the same rows** (a check of §3.6's hypothesis, counts only; B9's `test_why_real_cases.py` owns the real assertion): arxiv_v2 has 12 `skip` decisions, all with a null EU and all created before the first completed `figure_author` call, then 24 non-skip decisions, every one after it with EU > 0. One pressed request precedes the first non-skip. So "12 skips" is the number of candidates decided before the first measured latency, as the map guessed; no constant of 12 exists.

## Records added

| Kind | Status | Rule | Carries | Answers |
|---|---|---|---|---|
| `figure_prebuild` (one per decided candidate; subject `decision:<fpd_id>`, detail `figure_prefetch_decisions`) | `chosen` (build), `excluded` (skip), `deferred` (`deferred_power`, `deferred_plan`, `capped`) | `no_measured_latency`, `sampled_eu_positive`, `sampled_eu_not_positive` (`prefetch_model.RULE_*`, `Decision.rule`) | verdict, draw index, trigger kind and ref, request key, source, judge p, drawn p_open, EU, propensity, benefit and cost minutes, `wait_min` and its basis (`kind_mix`, `pressed_mix`, `author_call`, `none`), `waits_n` and per-tier counts and minutes, blocked minutes, today's load, expected requests, observations, pause days, builds left, render minutes left, mains, plan waiting; versions: model version, posterior digest, **seed**, posterior draws | Case 4; S8 (the reason string was never stored) |
| `figure_prefetch_filter` (one per pass that excluded anything) | `excluded` | the one rule, or `several_rules` | found, kept, `excluded_by_rule` counts; alternatives: up to 10 request keys per rule, `lost_by` the rule (`duplicate_in_pass`, `decided_horizon_open`, `decided_for_trigger`, `no_spans`, `show_me_off`, `withheld`, `grounding_withheld`, `item_protected`, `already_built`, `protection_unavailable`) | S7, protection exclusions included |
| `figure_prebuild_stop` (subject the decision) | `deferred` (the queue ends: this row and the rest wait), `excluded` (passed over), `refused`, `failed` | `foreground_busy`, `rich_in_flight`, `off_mains`, `author_not_plan`, `render_minutes_used`, `daily_builds_used`, `item_protected`, `built_already`, `rich_job_running`, `build_refused`, `build_failed` | waiting count and up to 10 decision ids; a refusal's code; a failure's exception class and `module:function:line` | S9 (the in-memory notes) |
| `figure_author` (one per attempt; subject `figure:<id>` or, for a rich-only build, `job:<id>`; detail `interactive_figures`) | `chosen`, `discarded` (a retry followed), `failed`, `refused` | the attempt's code: `accepted`, `unsupported`, `prediction_dropped`, `model_failed`, `status_invalid`, `tier_reason_missing`, `label_text`, `spec_invalid`, `sketch_invalid`, `brief_invalid`, `prediction_invalid`, `verification_failed`, `source_differs`, a route refusal's code (`capped`, `unrouted`, ...) | attempt number, attempts, all the attempt's codes (`problems`, with extras such as `label_text_stripped`, `quick_dropped`, `source_differs`), problems count, predictions dropped, the author's status (a known medium or `other`), request id (the receipts' `figure:<id>` owner), origin, prefetch decision id, the build's outcome; versions: prompt version, model; a failed call's exception class | Case 3 (attempt 1's problems survive attempt 2); S10 (a salvaged prediction); `service.py:2513` (a refusal stored nothing) |

The brief's five codes are there; the loop has more exits than five, so each gets its own code rather than sharing one (`spec_invalid` is not `prediction_invalid`: since `214c206ff1` a bad prediction drops itself and the figure is `prediction_dropped`; `prediction_invalid` stays for a parser that refuses a spec for a prediction's own problem).

**Where they're written.**
- `figure_prebuild`: built before the transaction (a builder that raises is logged and its records left out), then `provenance.write` per record inside the same `atomic()` as `insert_decisions`, in a savepoint that never raises.
- `figure_prefetch_filter` and `figure_prebuild_stop`: `write_decision`, a short transaction of their own, on the pass's background thread.
- `figure_author`: `_author_and_store` became a wrapper around the old body (`_author_attempts_and_store`), which notes each attempt's verdict as it goes (list appends beside the existing `problems`, never in the control flow) and writes the records with `write_decision` after the build returns or raises. The build's own transaction has committed by then.
- **No record** when the switch is off (the filter's switched-off return, the queue's "switched off" stop), when a pass is cancelled (the vault is closing or switching), or when a build ends in `FiguresChanged` (a `BaseException`: the switch or route changed under it). A switched-off feature writes nothing, as before.

**The trace.** `run_trigger` runs under `trace_scope(current_trace())`: the sidecar drains the prefetch queue on a bare thread, so each pass births one trace, and its records, the judge's calls and the prebuilds' author calls share it. A pressed build runs under its RPC's trace. Outside every entry point (tests), `in_one_trace` gives a build's or a pass's records one trace between them.

**The seed.** `decide_and_log` draws `np.random.SeedSequence().entropy` once when no generator is injected and builds `default_rng(entropy)`. `default_rng()` builds its generator from one fresh `SeedSequence`, and `default_rng(entropy)` with that sequence's entropy is the same generator draw for draw (`test_drawing_the_seed_once_changes_nothing_statistically`), so nothing changes statistically. The seed (a decimal string) is in every `figure_prebuild` record's versions, with the posterior digest and each candidate's draw index: `test_the_recorded_seed_redraws_the_pass_exactly` reloads the model (same digest), redraws from the seed, and gets every sampled EU and propensity bit for bit. An injected generator (tests, `ctx.figure_prefetch_rng`) is recorded as `injected`.

## Proofs

**P-tests** (`tests/test_figure_decision_records.py`, 18 tests, fakes only, read back through `learnloop why --json` or the table):
- case 4: a skip before any measured latency (`no_measured_latency`, EU null, propensity 0, `waits_n` 0, basis `none`, a seed), then after one measured press a build (`sampled_eu_positive`, `waits_n` 1, basis `author_call`, `wait_min` 40/60, cost 0, EU and propensity equal to the row), the second pass's filter record and the pass's shared trace, which reaches the prebuild's author call; the seed redraw; the seed equivalence; `capped` and `deferred_power` as `deferred` records;
- filters: twelve protection exclusions plus a duplicate (counts by rule, exactly ten keys kept), unreadable protection cutting the pass, no record when nothing is excluded;
- build stops: foreground work ending the queue (the waiting ids), a refused and a failed prebuild;
- author: a figure stored failed with both attempts' `verification_failed` (attempt 1 `discarded`, attempt 2 `failed`, same trace, `why figure:<id>`), attempt 1's `spec_invalid` surviving an accepted attempt 2, `model_failed` with its exception class and no message, `label_text`, `prediction_dropped` with its count, a refusal before any call, a rich-only build's `job` subject, a build interrupted after its attempts;
- no prose: every record passes `check_no_prose`, and the passage, equation, goal, label text, prediction prompt and exception messages planted in the fixtures appear in no record;
- **a record never changes a decision**: the same pass run twice, once with `decision_records` dropped and every record builder patched to raise, gives identical decision rows, figures and author prompts.

**Prompt golden** (`tests/test_figure_prompts_golden.py`, `tests/fixtures/figure_prompts_golden.json`): no figure prompt golden existed, so one was added. It was written from main `536963aa30`'s source (a `git archive` of `src` and `migrations` under `fixtures-local/`, run with `PYTHONPATH` and pytest's `pythonpath` both pointed at it, the module path checked), before any B4 code: six prompts (a pressed build refused then accepted and one failed twice, both second prompts carrying the first's problems; the section judge; a prebuild's author). It passes on main again and twice on this branch.

**Fake-model identity, main vs this branch.** A scratch driver (not committed) ran the same sequence on each side: a plan pass (section judge, build), a section pass, an offer pass with a spec refused and a figure failed twice, an off-mains pass with the second book protected (two `deferred_power`), a pass back on mains (two `capped`), then a pressed build. Generators seeded per pass; receipt times normalized after each pass, because a later pass's W reads the earlier author calls' wall-clock durations. Dumped `figure_prefetch_decisions` (8), `interactive_figures` (5), `figure_requests` (5), `judgment_ledger` (11), `model_call_receipts` (11, `trace_id` aside), `plan_usage_pauses`, `ingest_jobs`, every pass result (decisions with EU and propensity, notes, builds) and the judge's (2), the prebuilds' (6) and the press's (2) prompts. After masking ULIDs, UUIDs, call ids and ISO times: **0 differences**. Main wrote no `decision_records`; this branch wrote 19:

| Kind | Status | Rule | Rows |
|---|---|---|---|
| `figure_author` | chosen | accepted | 4 |
| `figure_author` | discarded | spec_invalid | 2 |
| `figure_author` | discarded | verification_failed | 1 |
| `figure_author` | failed | verification_failed | 1 |
| `figure_prebuild` | chosen | sampled_eu_positive | 4 |
| `figure_prebuild` | deferred | sampled_eu_positive | 4 |
| `figure_prebuild_stop` | deferred | daily_builds_used | 1 |
| `figure_prefetch_filter` | excluded | already_built | 1 |
| `figure_prefetch_filter` | excluded | item_protected | 1 |

**P-draw** is not required (no router code is touched) and was not run. **P-shadow** isn't named for B4: figures are outside replay, and `test_decision_records_is_unreachable_from_replay` passes unchanged (no figures module is in the rebuild closure).

**No real model, no network.** Every run used the tests' fakes (`AuthorFake`, `JudgeFake`); the backup copy was only read by SQL.

## Tests

- Targeted lane, `-n 4 --dist worksteal` under the 5 GB scope, after waiting for the full-suite lock: `scripts/affected_tests.py` on the diff (run under the `env -i` wrapper) selected 168 files without falling back, plus the two new files, `test_provenance`, `test_architecture`, `test_cli_help_snapshot`, `test_cli_json` and `test_effective_defaults_golden` (172 files). **3,212 passed, 13 skipped, 1 xfailed** in 6:59, on the committed source.
- New: `tests/test_figure_decision_records.py` (18), `tests/test_figure_prompts_golden.py` (1). Edited: none.
- `lint-imports --no-cache`: 43 kept, 0 broken. `ruff check src tests scripts`: clean.
- The four validators (`validate_vault.py`, `module_validate.py`, `desktop_validate.py`, `db_validate_reference.py`) pass.

## Vault

None named (figures have no note, §5), and no note was made false (`Workflows/Inspect Persistent State` already lists `figure` and `decision` as `why` targets). The references were regenerated once after the source commit with `generate_all.py` (24 notes: the new `figures/records` module note, the changed figure modules, the tables the new tests read, test cross-references, `_generated.md`) and committed; a second run changed nothing.

## Open items

- **The step 0 measurement bug** (above): the owner's call, as a successor, since it changes EU.
- **Retention**: `figure_prebuild` rows are the largest here (about 30 fields, no alternatives); one per decided candidate, so at arxiv_v2's rate (36 decisions so far) they're small against B6's slates. B6 measures bytes per week.
- **B9**: `why --kind figure_prebuild --first-build` (the last skip, the first build and the measurement that changed) reads these rows; `--first-build` isn't built yet. `tests/test_why_real_cases.py` (case 4's count) is B9's.
- **A filter record when the switch went off mid-pass, or a cancelled pass**, is deliberately not written; the pass's notes still say so.
- **Rich jobs** (`figures/rich.py`, the rich author's own attempts) have no per-attempt record; outside B4's files.

## Unverified

- The sidecar's background drain was exercised through `run_trigger` inline, not through `prefetch_runtime`'s thread; the trace birth there is the same `trace_scope` call.
- The durability lane (WAL) wasn't run for the new tests; the landing gate runs it.
