# Fix round after arc E's review, part 2: the router

Branch `fix/arc-e-review-router`, based on main `8804080fcf` (E1 to E5 and E6a). The review is the read-only Codex
review of `914145d0b9..8804080fcf`; this round takes its findings 4, 5, 7, 8, 9, 10 and 11 (the router's). Structure
and failure handling only: no algorithm tag, migration or config switch. Implementer: one Opus session, no subagents.
"Pre-arc" below is `914145d0b9` (arc E's base; `objective_chooser.py` is identical at `c65d146285` and `931c8d072e`),
"base" is `8804080fcf`; both were exported with `git archive` into the step's scratch directory.

## Findings

### 4. Reads moved across the job threads' publication point (reproduced)

**Verified.** A scratch script (`sampling_schedules.py`) runs five schedules against any checkout's code: a worker
publishes while the deciding thread is held at one point (the job's card build, held in `objective_card.decision_card`
until then, or an earlier decision's carried valuation of the same plan, registered and drained, valued), and the
script prints what the decision recorded. Pre-arc and base differ on three of the five:

| Schedule (where the worker publishes) | Pre-arc | Base | Now |
|---|---|---|---|
| card, right after the mix's draw | statements in the trace; question set `router_objective_v1` in the router row and the decision record | no statements; question set `None` in both | as pre-arc |
| card, at the start of the trace's rows | no statements; question set in both | no statements; `None` in both | as pre-arc |
| card, while the router's record summarizes payloads (after the trace) | no statements; `None` | no statements; `None` | as pre-arc |
| carry, at the start of the trace's rows | `carried_for` holds it | `carried_for` empty | as pre-arc |
| carry, while payloads are summarized | empty | empty | as pre-arc |

The script's outputs at pre-arc and now are equal as JSON on all five; the tests below assert pre-arc's values.

**Every read of what a background thread publishes, in `ObjectiveChooser._decide_objective`** (line numbers: pre-arc
`objective_chooser.py`; base `objective_chooser.py` and `objective_job.py`):

| Read | Published by | Pre-arc | Base | Now |
|---|---|---|---|---|
| `entry.results()` (models' and numeric policy's results) | job threads | first (1551) | first (`J.job_answers`) | unchanged |
| `material["numeric"]`, `PUBLISHED` under the entry's lock | job (early publication) | after results (1557-1564) | same order (`_numeric_answer`) | unchanged |
| `CARRIED` (`_with_carried`) | job, after its answer | after the numeric answer (1575) | same | unchanged |
| the carry registry, written (`_register_carry`) | (this thread) | after the decision id (1589) | same | unchanged point; now with its thread's start under the lock (finding 9) |
| `policy_card` grab (trace's statements, guard's ids) | job's card build | after the draw, the coin, the rule sentence and the titles (1609) | before `choose` (889; E2) | the trace's grab after the draw and the titles (restored); the guard's ids still read before `choose` (see below) |
| `policy_card["statements"]` (same dict) | job's card build | after `_trace`'s rows (1630) | in `objective_trace`, after the rows | unchanged (reads the restored grab) |
| `carried_for` (the registry and `router_objective_traces`) | carry threads, the job's drain | after the rows, the contest, the statements and `goal_dates` (1643) | before `objective_trace` (912; E4) | inside `objective_trace`, after `goal_dates` (restored: `read_carried_for`) |
| `policy_request` (the question set's version) | job's card build | after the trace, the Decider's distribution, latencies and costs (1660) | before `choose` (890; E2) | after costs, before payloads (restored), for the router's record and the decision record |
| `seen(entry)` (provenance) | — | after the record | same | unchanged |

The job's side publishes in the same order at all three (`_objective_job` diffs pre-arc against base only in the
names E3 passed in). `ObjectiveRestraintGate._mixed` reads nothing at a moved point (its diff is renames). The other
reads (`current_weight`, the session's minutes, the availability) are database reads at unchanged points.

**The guard's read before the choice.** The pure choice's rationale guard needs the card's evidence ids before
`choose`; pre-arc read them from the grab at 1609, after the draw. The guard reads them only when the LLM answered with
a rationale (`guard = "absent"` otherwise, and `evidence_labels` only when shown), and the job writes `policy_card`
before it builds the request and asks the LLM, so an answered LLM implies the card was on the material before the
results were taken. The early read therefore sees the same evidence ids as pre-arc whenever they are used. The trace's
own grab is the restored one.

**Rule now.** Each of the three reads is sampled where pre-arc sampled it.

**Diff in words.** `_decide_objective`: the guard's card read stays before `choose`; the trace's card is read again
after the titles; `objective_trace` takes `read_carried_for` (a reader, None with carries off) and calls it after
`goal_dates`; the question set's version is read after costs. The decision record leaves `choose`
(`choose.decision_record(choice, inputs, question_set_version=...)`, built after the trace; `ChoiceInputs` no longer
has the field, `Choice` no longer has `record`), because the record names the late-read version.

**Fail-first.** `tests/test_router_sampling_points.py` (7 cases), run in the base export (the file copied into its
`tests/`): the three card cases where the card lands before the old read and after the new one fail (statements at the
draw; the question set at the draw and at the rows); the carry cases fail on `defer_carry`'s new arguments (the carry's
base behaviour is the script's row above). All 7 pass now.

### 5. The config hash in new decision receipts (no code change, verified)

Removing the `replay` section changed `versions.config` in new `decision_state_receipts` rows (it hashes the whole
config dump). Every reader of the receipt was checked (`git grep` over `src`, `scripts`, the vault's scripts and the
apps): `tail_data._receipt` and `rebuilt_features` read only `state.los` and `pending_reports`; `trace.record` reads
the receipt's `id`; `router_objective/report.py` counts rows by kind; the sidecar and the follow-up router write
receipts. Nothing reads `versions` (or `versions.config`) to group, compare or reuse rows. **Ruling recorded:** the
hash is provenance beside the code revision, which changes at every commit; no code change.

### 7. Proof gaps in the identity pins (verified; pins added)

C3b's `key` is the hash of the numeric seed's reduced identity (the last identity the chooser hashes), and the pinned
draws map each distinct seed to its first-seen ordinal. Added: `C3b.start_key`, the key the chooser hands to
`_start_objective` (the stub now records it), and site `C3m`, `objective_seeds.mix_seed` for a fixed key and decision
id through production's `mix.seed_for` (the pins run `real_draws`). `_chooser_boundary` shares its run with the new
pin and returns the same value (its docstring now says what it holds). `--write` added exactly these two lines to
`tests/goldens/identities.toml`; the shapes file is unchanged:

```
+"C3b.start_key" = "1e97e70191ad03032045f02b4b32ada4898b102deb774c1dbd7913920a0f40cb"
+"C3m.seed" = "bd78d9ced62e805e7b2d84b64096155cde052bbcf909c5a84b927a0cd5eb9ac9"
```

**Mutations (each restored after).** (a) `held_reading_map` dropped from the chooser's own key only (the identity's
`objective.followup_switches` in `ObjectiveChooser.choose`): of `C3*` and `C4*`, only `C3b.start_key` fails
(`C3b.chooser`, `C3.boundary.*`, `C4.*` pass: the reviewer's gap). (b) `mix_seed`'s two arguments swapped: only
`C3m.seed` fails; every other identity pin and all of `tests/test_pinned_draws.py` pass (279 passed).

### 8. A record's construction could change the served block (reproduced)

**Verified** in the base export: the new test with the error injected in `choose._with_record` serves the rules'
fallback pick (`repair:…`) instead of the drawn block (`maintain:…`), `fallback_reason = chooser_error`.

**Rule now.** Building the decision record cannot change what is served. The record is built after the trace by
`_built_record`; when `choose.decision_record` raises, the drawn block is served, `BlockChoice.decision_record` is
None (so `boundary_records` derives the `plan_block` record from the router's record, which holds the same facts:
`tests/test_objective_decision_record.py`), a `decision_record_build` failure record (`builder_error`, type and
`module:function:line`, never the message; `plan_records.step_failure`) rides on the choice's provenance as
`decision_failures`, which `boundary_records.plan_block_records` adds after the boundary's own failed steps, so it is
the block record's child. A warning names the trace and the type.

**Tests** (`tests/test_router_failure_records.py`): the mix's draw is moved onto a block the staged rule did not pick,
and the rules' fallback pick is read first by making the chooser fail; the new test injects at
`choose.decision_record` and the existing one at `boundary_records.plan_block_records`, both now asserting the drawn
block is served and differs from the fallback's. At base the first fails (above) and the second passes, as the review
said.

### 9. D-45, what was still reachable (reproduced; fixed)

**Verified** in the base export (the new tests with the new arguments removed): a thread `defer_carry` started was
running before it was listed (the carry lock was free at its first instruction, and `join_carried(0)` returned True
from inside it), and a carry was recorded by a decision of another plan and of another session. The base has no stop.

**Rules now.** `defer_carry` registers the carry and starts and lists its thread in one hold of the carry lock. Each
carry is tagged with its session and plan and has a stop event: `carried_for` takes the deciding session and plan and
records only theirs; `stop_carries(sqlite_path, keep=None|(session, plan), timeout)` stops every other carry of the
database, takes it off the registry and waits up to `STOP_WAIT_SECONDS` (2 s) for those running and their threads.
`SidecarContext.close` calls it for its vault (only if the job's module was ever loaded); `build_plan` calls it for
every earlier plan's carries once the new plan is inserted. The carried valuation run_numeric hands over takes `stop`:
once set, the clock it gives the rollouts reads just past its deadline (a finite reading), so they end at the next
action as at a deadline (unstopped, the same readings: the draw-for-draw proof below).

**Tests** (`tests/test_carried_valuation_lifecycle.py`, barriers only): the thread is listed in the same hold that
starts it; a running carry is stopped, joined and recorded by no later trace; the sidecar's close stops its vault's
carries and leaves another vault's; a carry is recorded only by its own session and plan; a new plan stops and joins
its predecessors'; the production carried valuation is valued when let run and ends unvalued when stopped.

### 10. The action-kind guard (reproduced; rewritten)

**Verified:** with the teach-back dispatch removed from `objective_inputs.action_for` in the worktree, the old guard
file passed (28 passed). The rewritten `tests/test_action_kinds_complete.py` builds, for each kind with a plan option,
the candidate the plan builds (lane, item practice mode, reading, offer annotation) and asserts `action_for`
dispatches it to that kind, then its trace label and reversibility; stop's value is checked as the acceptance mix of
ending the session now and another block today, and a sequence as valued by its steps (one step equals that step;
a second adds its own). With the teach-back dispatch removed: `test_a_plan_candidate_reaches_its_kind_through_production_dispatch[teach_back]`
fails (`'new_practice' == 'teach_back'`); restored, 34 passed.

### 11. The offer predicate and the cold import (reproduced; fixed)

**Verified** at base: `lesson_offer.is_offer(<candidate with subtype lesson_offer>)` was False and
`is_offer("lesson_offer")` True; `import learnloop.why.reader` loaded NumPy and `learnloop.scheduling.fsrs`.

**Rule now.** `learnloop/plan_refs.py`, a leaf importing nothing of LearnLoop, holds `LESSON_OFFER_SUBTYPE`,
`LESSON_OFFER_PREFIX`, `STOP_FOR_TODAY` and `is_offer_subtype` (raises on anything but a string or None).
`router_objective.types` and `daily_plan.types` re-export them; `types.is_offer` is gone (its callers use
`is_offer_subtype`). `daily_plan.lesson_offer.is_offer` takes a candidate again and raises on a string. The copies in
`router.plan_log` (`OFFER_PREFIX`, `STOP_REF`), `router.decisions` (`STOP_REF`), `db.stores.router_suggestions`
(`OFFER_REF_PREFIX`) and `followup_serve.workflow` (`LESSON_REF_PREFIX`) are now names bound to the leaf's strings
(no contract forbids those edges: the leaf is a top-level module with no imports, added to the "Primitive modules stay
dependency free" contract), and the held-equal test is gone. `why/reconstructed.py`, the four reports, the follow-up
router and decision view, the teacher's diagnosed sources, the stop coin and the sessions read the leaf. The strings'
bytes are unchanged (`tests/test_plan_refs.py` pins them and that every name is the leaf's object).

**Import time of `import learnloop.why.reader`** (`python -X importtime`, cumulative µs, seven fresh interpreters each,
sorted; three interleaved rounds): pre-E6a (`e5d6e3f791`) 12,667 to 17,272, medians 16,564 / 13,639 / 13,518; base
41,180 to 146,283, median 56,873 (NumPy 116 ms of it); now 12,679 to 16,896, medians 15,460 / 13,123 / 12,809. The
modules loaded now are pre-E6a's plus `learnloop.plan_refs` (121 against 120); none of NumPy, `scheduling.fsrs` or
`router_objective.types` (`tests/test_plan_refs.py::test_why_reads_the_offer_prefix_without_loading_numpy`).

## Proofs

**P-draw.** E2's harness as E3 and E5 extended it (scratch `pdraw.py`; only its work path changed, and its recording
option now wraps `rollouts` where `value` is gone) on its ten scenarios, 31 runs: base = the `8804080fcf` export,
tip = this worktree at `5139bca36d`, and again at `fae3920269` (the last source commit; later commits are
documents). Every table, every LLM prompt, every Decider call
and `why <trace> --json`, after the harness's normalization: **byte-equal on all ten** (sha256 of each output, base =
tip: `both` 156663f4a455, `coin` 8247ab842de7, `llm_fails` 876573ecf5b2, `llm_fails_ih5_off` 3d0257ae1254,
`no_models` af09cbf77602, `guard` ade60a0f24c2, `evidence` 95595462e95d, `offers` e324daf540ac, `contest`
d05f532e8bdc, `early` e34c08b8f348). The decision path's connection opens and statements are equal at base and tip
and to E5's record (`both` 57 / 436, `no_models` 74 / 552, `early` 34 / 264, ...). `early` and `no_models` reach the
carried valuation's drain (now given a stop event) and `carried_for` (now read inside the trace's assembly); the base
runs recorded P2's inputs, and the recorded base equals the unrecorded tip, so recording moved nothing.

**P2. `evaluate` replay.** E5's `p2_replay.py` on the 371 calls the base runs recorded (365 distinct), three per
scenario and entry point, 1,602 cases: base and tip **byte-equal** (32,741,316 bytes, sha256
`63fff4d0a70b88e5…f40a` on both, the same digest as E5's record).

**Identity pins.** Two pins added (§7), no existing pin moved; the shapes golden unchanged.

**Structure.** Import cycles with untracked files included: largest component 84 → 84, modules in any cycle 220 →
220, member lists identical. `learnloop.plan_refs` imports nothing; the new edges into it (router, db,
followup_serve, router_objective, daily_plan, why, teacher) cannot close a cycle, and the engine's new import of
`objective_job` cannot either (`objective_job` is in no cycle). Two ratchets rose and the golden was raised in
`fae3920269` with the reasons: root modules 35 → 36 (`plan_refs`: `router_objective` is the only package the names
could join, and `router`, `db` and `followup_serve` cannot import it without a package cycle, which the
"Existing deferred cross-package cycles are frozen" contract forbids) and `daily_plan/engine.py` 6,775 → 6,776 lines
(the new plan's call to `stop_carries`). The golden's other numbers were left as they were (the `--write` run would
also have lowered three numbers the base's K5 commits took down; they are not this round's). `lint-imports
--no-cache`: 43 kept. `ruff check`: clean.

## Targeted gate

| Selection | Files | Result |
|---|---|---|
| `scripts/affected_tests.py --files` over the 37 changed `.py` files (`pyproject.toml` left out), plus the rules block's files and the edited and new test files; 14 chunks of at most 60, `-n 2`, `-m "not arc_close"`, at `5139bca36d` | 835 | 14,717 passed, 52 skipped, 3 xfailed, 1 failed (`test_structure_ratchets`: the two rises above, then raised in `fae3920269`) |
| After `fae3920269`: the router, plan, objective, why, follow-up, IH, TE3 and sidecar files of that selection and the last two chunks again (`test_architecture` and `test_test_layout` apart), 6 chunks | 323 | 4,867 passed, 25 skipped, 1 xfailed |
| `test_architecture`, `test_test_layout`, each alone at `-n 1` | 2 | 18 and 3 passed |
| `test_identity_pins`, `test_retired_config_identities`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_structure_ratchets`, `test_plan_refs`, `test_action_kinds_complete`, `test_choose` | 8 | 456 passed |

`ruff check`: clean. `lint-imports --no-cache`: 43 kept. Vault: `module_validate` and `validate_vault` pass;
references regenerated after the last source commit.

Two of this round's runs had workers killed by the 3 GB memory cap (the ones that held `test_architecture.py` and
`test_test_layout.py` beside six router files: `test_structure_ratchets`, `test_router_failure_records`,
`test_carried_valuation_lifecycle`, `test_router_sampling_points`, `test_forced_withdrawal_records`,
`test_objective_decision_record`); their files passed afterwards in smaller runs (the rows above).

## What is left open

- **A carry no longer crosses a plan or a session (by the ruling; a stored-value change outside P-draw).** Before,
  a carry was keyed by the database alone, so the carried valuation of a plan's last decision (drained by the next
  plan's first job) was recorded in the next plan's trace and lifted the censoring of that transition in the learned
  tail's data. Now it is stopped and dropped when the next plan is built, and that transition stays censored
  `cutoff_unmatched`; likewise across a change of the plan's session. No served decision or draw depends on it, and
  P-draw's journeys are one plan each. If the orchestrator prefers to keep cross-plan attachment within a session, the
  change is the `(session, plan)` owner in `carried_for`, `stop_carries`' `keep` and `build_plan`'s call.
- **Hosts without a close.** Only `SidecarContext.close` (the desktop sidecar and the phone host) calls
  `stop_carries`. The CLI's carries are daemon threads that end with its process; the TUI runs no plan (its contract).
  A carry still running past the 2 s wait finishes on its own and is recorded nowhere.
- **Other failures inside the chooser after the draw** (the trace's assembly, the router's record) still raise into
  the rules' fallback, as before the arc; finding 8's rule covers the decision record's construction, which the arc
  had moved into the choice.
- **The guard's early card read** is equal to pre-arc's on every schedule by the argument in §4 (an answered LLM's
  card is on the material before the results are taken); the tests hold the trace's read, not the guard's.
- Not verified here: the owner's copies (P-draw and P2 on synthetic vaults, as E2 to E5), the whole suite, durability,
  `--fresh-connections`, `arc_close` (the orchestrator's gate).
