# Refactor I2b: the frozen intent view after the check split

Branch `refactor/i2b-intent-view`, based on main `9dd771a788`, the landing of I2a. This is the second of I2's three
sub-steps (`docs/reviews/refactor-i2.md` §5, option A; `docs/reviews/refactor-i2a.md` §8 and §9). It is a structure
step. Line numbers are at the branch tip, in `src/learnloop/scheduling/scheduler.py` unless another file is named.

**Outcome.** All three parts are built.

- **The check split is the build's one intent read.** Inside `_due_queue`, the DL2 check split is now the only read
  between the admission's gathered reads and the ranking. After it, the admission, the probe score, the intent gate,
  the push lane, the follow-up door and the check picks all read a frozen copy of the view
  (`IntentServing.frozen`), which holds no readers.
- **The teach-back site reads nothing.** It values from the same loaded value context as the probe site, and that
  context's repository raises if anything reads through it.
- **I2a's acceptance criterion is met.** `_reachable_episodes` now filters on intent's whole gate, check holds
  included. The two "large, unconsulted, one item reachable" builds read 437 and 1,037 SELECTs again, the counts
  from before I2a. Every other measured build reads exactly what it read at the base (§5).

No golden moved. P-ast holds apart from the one substitution `self.intent_view` → `self.reads.intent_view` (§4).

## 1. Intent's reads, and where the build makes them

`IntentServing` (`scheduling/intent/serving.py`) is built by `intent_serving`. Building it reads the commitment
snapshots, the FSRS weights and the attempts that answer checks. Some reads stay lazy and happen only when a method
first needs them:

- **The check split** (`checks`). It asks the build's admission about every due, unanswered check's candidates
  (`check_candidate_refusal`). It also runs the check gate (`CheckGate`), the eligibility decision for each candidate
  and the Reader follow-up gate. It runs on first use of `checks`, which `filter_requests`, `withhold_reason`,
  `due_checks` and `pick_checks` reach.
- **The review anchors** (`_anchor`, `load_anchors`). Read only when an effective due is computed for an item whose
  recall target is not 0.90.

The admission needs intent in two places. Its intent gate (`withhold_reason`) needs the split, and the split asks the
admission. The probe score (`effective_due_or_none`) needs the anchors.

That is the circle: a probe-surface candidate of a due check reaches the probe gate during the split, so the split
needs the episode's reads. But I2a's acceptance criterion needs the split's result to decide which episodes to read.

## 2. What the build does now

1. **The admission's reads, part one.** This is I2a's gather, `_gather_admission_reads`, now told which episodes to
   read. With an intent view it reads only the episodes the split can consult: probing episodes with one of
   `_check_split_candidates(view)` on their LO, where those candidates are the due, unanswered checks' candidates that
   pass the routine gate. Without an intent view nothing is split, so it reads every probing episode with a
   routine-passing item on its LO. During the split, `AdmissionReads.intent_view` is the live view.
2. **The check split** (`bind_admission`, then `filter_requests`). This is the one read left in intent.
3. **What is reachable** (`_reachable_items`, `:3236`). The items that pass the routine gate and intent's whole gate
   (`withhold_reason`, check holds included). Both are answered from values already read: the split is done, so the
   live view answers without reading.
4. **The frozen view.** `intent_view.frozen(anchors_for=...)` (serving.py `:263`) returns a copy with these
   properties:
   - its checks are split;
   - its review anchors are loaded if one of the given items has a recall target other than 0.90;
   - it has no readers: the eligibility closure, admission, admission factory, gate factory and follow-up gate are all
     None.

   The build passes the reachable items that have a stored due. Those are the only items whose effective due the
   ranking can ask: the probe score and the push lane run only for admitted items, and admitted items are a subset of
   the reachable ones. If an effective due ever needs anchors the build did not foresee, the frozen view raises
   (`_anchors_not_gathered`) rather than reading or answering without them.
5. **The admission's reads, part two** (`_after_check_split`, `:3355`). It adds three things:
   - the episodes of the reachable items that part one did not read;
   - the teach-back site's latencies, when the site is on and a reachable item is a teach-back;
   - one value-context copy whose repository raises (`_decision_context`), loaded for both value sites.

   It sets `intent_view` to the frozen view, and the build hands the admission this value (`admission.reads`).
6. **Everything after this reads the frozen view and the final reads.** That covers the candidate loop's intent gate
   and push lane, the follow-up door's filter, the check picks, the probe score's effective due
   (`self.reads.intent_view`) and the teach-back value admission (`reads.voi_context`).

Nothing writes between part one and the candidate loop: the split, the frozen copy and part two are all reads. So
every value is the one the lazy read returned. Probe scores the split computed are cached in the admission and are
equal to what the frozen view would give, since the effective due is the same function over the same anchors.

**Outside a build**, `check_admission` and `pool_admission` keep `_LazyAdmissionReads`, which now carries the live
view (`intent_view`). They have no ranking after the split, so they have nothing to freeze for.

## 3. Reads that moved, and what became unconditional

- **The anchors.** At the base they were read during ranking, the first time an admitted item with a non-0.90 target
  and a stored due was scored. Now they are read at the freeze when any reachable item with a stored due has such a
  target. That is a superset by at most this one read, in a build where every such item is withheld by a later gate
  (placement, cold start, the probe gate or the device). No measured build pays it.
- **The teach-back latencies.** At the base they were read at the teach-back admission when a teach-back was in the
  greedy queue. Now they are read in part two when a reachable item is a teach-back. Again a superset by at most one
  read, when every reachable teach-back is withheld later. No measured build pays it.
- **Episode reads.** No new kind. They are now limited to episodes with an item past intent's whole gate, so a build
  where intent holds every reachable item of the LO for a check no longer reads the episode.

## 4. P-ast

A scratch script compared base `9dd771a788` with the tip using `ast.dump`.

| Definition | Result |
|---|---|
| `_BuildAdmission`: `admits_check_candidate`, `check_candidate_refusal`, `in_probe`, `device_gate`, `freshness_gate`, `placement`, `placement_gate`, `cold_start_gate`, `probe_gate`, `reserved_annotation` | identical |
| `_BuildAdmission.probe_score` | identical after `self.intent_view` → `self.reads.intent_view` |
| `_BuildAdmission.__init__` | the `intent_view` parameter and attribute removed (now in `reads`) |
| `_LazyAdmissionReads`, every property | identical; `__init__` gains `intent_view` |
| `_load_voi_reads`, `_prospective_familiarity`, `_probing_episodes`, `_teach_back_value_admission`, `_persist_offer`, `_head_probe_presentation`, `check_admission`, `pool_admission` | identical |
| `_episode_probe_reads` | the decision-context copy moved into `_decision_context` (same two statements) |
| `_gather_admission_reads` | takes `episodes` and `intent_view` from the caller instead of computing the filter |
| `_outside_build_admission` | passes `intent_view` to the lazy reads instead of to the admission |
| `IntentServing` | every method identical; `frozen` added |

## 5. Query counts

SELECT and WITH statements per build, counted the same way as in I2a §5. The scratch script is not committed. Base
(`9dd771a788`) and tip were run back to back on the same vault builders. Two rows are new: `intent_targets_serving`
and `intent_targets_read`, the goldens of §6. Times are single runs and noisy.

| Build | Items | Base | Tip | Change | s base | s tip |
|---|---|---|---|---|---|---|
| serving_with_session | 18 | 222 | 222 | 0 | 0.152 | 0.178 |
| read_with_session | 18 | 195 | 195 | 0 | 0.102 | 0.098 |
| read_without_session | 18 | 162 | 162 | 0 | 0.098 | 0.101 |
| admission_gates_serving | 21 | 191 | 191 | 0 | 0.110 | 0.138 |
| admission_gates_read | 21 | 147 | 147 | 0 | 0.094 | 0.122 |
| admission_probe_reads | 18 | 214 | 214 | 0 | 0.022 | 0.022 |
| admission_phone | 19 | 219 | 219 | 0 | 0.103 | 0.102 |
| admission_unconsulted_episode | 18 | 137 | 137 | 0 | 0.019 | 0.016 |
| admission_empty | 18 | 113 | 113 | 0 | 0.015 | 0.016 |
| admission_waiting_check_episode | 18 | 183 | 151 | -32 | 0.018 | 0.016 |
| intent_targets_serving | 18 | 247 | 247 | 0 | 0.102 | 0.100 |
| intent_targets_read | 18 | 193 | 193 | 0 | 0.099 | 0.099 |
| large n=100, read | 318 | 962 | 962 | 0 | 4.05 | 4.02 |
| large n=100, serving | 318 | 1,422 | 1,422 | 0 | 4.29 | 4.08 |
| large n=100, value stopping off | 318 | 956 | 956 | 0 | 0.060 | 0.061 |
| large n=100, phone | 318 | 962 | 962 | 0 | 4.01 | 4.02 |
| large n=100, unconsulted | 318 | 437 | 437 | 0 | 0.049 | 0.035 |
| **large n=100, unconsulted, one item reachable** | 318 | 969 | **437** | **-532** | 0.056 | 0.035 |
| large n=300, read | 918 | 2,562 | 2,562 | 0 | 11.87 | 11.86 |
| large n=300, serving | 918 | 3,822 | 3,822 | 0 | 12.20 | 12.00 |
| large n=300, value stopping off | 918 | 2,556 | 2,556 | 0 | 0.177 | 0.183 |
| large n=300, phone | 918 | 2,562 | 2,562 | 0 | 11.84 | 11.77 |
| large n=300, unconsulted | 918 | 1,037 | 1,037 | 0 | 0.068 | 0.072 |
| **large n=300, unconsulted, one item reachable** | 918 | 2,569 | **1,037** | **-1,532** | 0.134 | 0.076 |

The acceptance criterion is met: 437 and 1,037 are the counts from before I2a (`refactor-i2a.md` §5), and every
other row is equal to the base.

`admission_waiting_check_episode` (151) is the same build at golden size, and it is back to its pre-I2a count too.

An earlier cut froze the anchors whenever any item had a non-0.90 target. On `admission_empty` that read 4 SELECTs
the base never made (`load_anchors` and its held-grade marks). That is why `frozen` takes `anchors_for`.

## 6. Proof

- **Goldens added first, on the base source** (`964034dfeb`):
  - `intent_targets_serving` (`build_intent_targets_vault`, with one instrument flipped to a diagnostic surface in
    memory): "Master" on `lo_c` and "Light touch" on `lo_b` move the effective due, and so the forgetting risk, away
    from the stored due. A due "Check once" on the probe's LO is split over candidates the build's admission decides;
    one of them is a diagnostic surface that the probe gate scores during the split.
  - `intent_targets_read`: the same vault, sessionless.

  `tests/test_due_queue_golden.py` passes all 18 tests at the tip, the 16 from I2a and these two. None moved.
- **Golden stability.** At the base, after recording, the goldens pass under `PYTHONHASHSEED` 0, 1, 777 and 12345.
- **`tests/test_frozen_intent_view.py`** (new, 3 tests):
  - The frozen view gives the same `withhold_reason`, `effective_due_or_none`, `pushes` and due checks as the live
    view for every item, with the repository's `connection` replaced by a raiser. It holds no readers.
  - A frozen view not asked for anchors raises on an effective due that needs them.
  - The teach-back admission's context raises on a repository read, and its admission and receipts equal those from
    a fresh repository-backed `VoiContext`.
- **I2a's value-decision test** (`test_the_probe_value_decision_reads_nothing_where_it_is_computed`) still passes.
- **Identity pins.** Unchanged (§9).

## 7. Judgment calls

- **The two-part gather.** The episodes the split needs are read before it, the rest after. The alternative, reading
  every routine-reachable episode before the split, is I2a's cost, which this step exists to remove.
- **`anchors_for` is the reachable items with a stored due**, not every item. It is a superset of every item whose
  effective due the build asks. A miss raises rather than changing a value.
- **The frozen view is a `dataclasses.replace` copy of `IntentServing`**, not a new type. Its methods are the same
  code, so nothing intent decides is written twice.
- **One value-context copy for both value sites.** The teach-back site reads latencies alone, and the probe site's
  loading covers them.
- **`admission.reads` is reassigned after the split.** A new admission object would recompute the probe scores the
  split already made.

## 8. What I2c needs from this

- **The two pure stages are in place.** Stage one is the admission, check gates included, over `AdmissionReads`
  (part one) and the live view. The split sits between the stages and is the shell's one read. Stage two is the
  admission and ranking over `AdmissionReads` (part two, with the frozen view and the loaded value context). Neither
  stage reaches the repository.
- **The persist step** still takes the two episode caches (copies of the gathered maps). I2c's persist call can take
  `AdmissionReads`.
- **I2-2** (the read build's follow-up marks) stays open to arc I's close, as briefed.

## 9. Commands and results

All runs went through the scratch wrapper. Each pytest command was a script under the step's scratch directory, run
in a `systemd-run --user --scope` with `MemoryMax=3G`: `-n 1`, and `-n 2` for the affected set. All at `f0edeea55d`.

| Check | Result |
|---|---|
| `tests/test_identity_pins.py` | 357 passed |
| `tests/test_structure_ratchets.py` | 3 passed |
| `tests/test_architecture.py` (alone) | 18 passed |
| `tests/test_test_layout.py` (alone) | 3 passed |
| `tests/test_public_tip_guards.py` | 14 passed |
| `tests/test_effective_defaults_golden.py` | 3 passed |
| `tests/test_cli_help_snapshot.py` | 26 passed |
| `tests/test_kill_switches.py` | 8 passed |
| `tests/test_sqlite_file_copies.py` | 1 passed |
| `scripts/affected_tests.py --base 9dd771a788` | 1,333 files, in 14 chunks of at most 100, `-m "not arc_close"`: 21,092 passed, 88 skipped, 13 xfailed, 0 failed |
| `tests/test_due_queue_golden.py` and `tests/test_frozen_intent_view.py` | 21 passed |
| `ruff check` | clean |
| `lint-imports --no-cache` | 45 kept, 0 broken |
| `scripts/check_gate_partition.py` | 32,909 = 32,843 landing + 66 arc_close |
| `git diff --check` | clean |

Structure golden, each line raised by hand in the commit that needed it; every other number is equal or lower:
- `golden_json_lines`: 269,135 -> 281,223 (`38b05e431b`).
- `scheduler.py`: 4,090 -> 4,196 (`f0edeea55d`).

## 10. Not verified

- **The pinned pypdfium2.** The worktree setup's `uv pip install --offline pypdfium2==5.14.0` found no cached
  wheel, so the worktree has pypdfium2 4.30.0. No test this step touches imports it.
- **The owner copies' shadow and cost.** Agents do not open owner vaults.
- **P-draw.** Its harness was not rerun.
