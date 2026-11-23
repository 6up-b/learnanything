# Refactor I2c: the due queue's ranking in two pure stages

Branch `refactor/i2c-pure-stages`, based on main `54be27df69`. This is the last of I2's three sub-steps
(`docs/reviews/refactor-i2.md` §5, option A; `refactor-i2a.md` §9; `refactor-i2b.md` §8). It is a structure step.
Line numbers are at the branch tip, in `src/learnloop/scheduling/scheduler.py`.

**Outcome.** The ranking is now two pure stages.

- **Stage one,** `admit_due` (`:659`), is the build's admission over `AdmissionReads`. The check split asks it about
  the due checks' candidates. That split stays the shell's one intent read between the stages.
- **Stage two,** `rank_due` (`:686`), takes the admission with the reads after the split and a `RankInputs` value,
  and returns a `RankedQueue`. It reaches no repository, and neither does the composition it returns, which the
  offer trace and the head probe's propensity re-run (§6).

A serving build with a session makes one persist call, `_persist_due_queue` (`:1040`). The serving entry point is
renamed `build_due_queue` → `serve_due_queue`, next to `read_due_queue`.

No golden moved and P-ast holds (§4). Every build's reads are equal to, below or slightly above the base; none
doubles (§5).

## 1. What the ranking read at the base

After I2b, `_due_queue` (646 lines) read through the repository at four places below the check split:

1. `_order_new_material(vault, repository, ...)`. It read the taught-first signals (`load_answers` and the blocking
   signals) for the LOs of the new-material slots.
2. `compose(...)`. It read the generated-probe identities (`generated_probe_ids(repository)`) on every call: the live
   composition, each of the offer trace's counterfactual outcomes, and each of the head probe's composed-head
   propensity outcomes.
3. `repository.active_probe_presentation_for_session(...)`, the session's committed presentation, read before the
   pin decision.
4. The device filter. This is the host's object, not the repository: `_held_for_device` called
   `DeviceFilter.holds_back`, which asks the host's predicate again and adds to `deferred`.

The base's withheld reasons were appended to the caller's `OfferTrace.exclusions` while the build ran.

## 2. What the build does now

`_due_queue` (`:236`) is the shell. In order:

1. **Reads.** Unchanged from I2b. A serving build's pre-ranking writes stay among these reads.
2. **Stage one.** `admit_due`, a thin constructor of `_BuildAdmission` that names the stage.
3. **The check split.** The one read between the stages.
4. **The reads after the split.** I2b's `_after_check_split`, with the frozen view.
5. **The ranking's own reads**, each made once:
   - the taught-first signals for every LO, but only when a reachable item can be new material, which stage one's
     own `placement` answers without reading;
   - the generated-probe identities;
   - the session's committed presentation.
6. **Stage two.** `rank_due` with a `RankInputs` (`:605`).
7. **Merging the stage's outputs.** The shell merges `RankedQueue.exclusions` into the offer trace's exclusions, or
   into a local map when only the slate record needs them, keeping the order in which items were withheld. It adds
   `RankedQueue.device_deferred` to `DeviceFilter.deferred`.
8. **Persist.** A serving build with a session calls `_persist_due_queue`: `_persist_offer`, then `record_slate`.
9. **The offer trace,** when asked for, filled from the stamped queue.

`rank_due` covers the follow-up doors' intent and device filters and the candidate loop (`_score_candidates`,
`:880`). It then sorts, orders new material, picks the due checks, computes the propensities, values the teach-backs
and makes the seeded draw. It finishes with the composition, the pin decision and the limit. The device's refusals
come from `AdmissionReads.device_refusals`, which I2a gathered with the same `refuses` call. `_held_for_device`
(`:1508`) now reads them and adds to a `deferred` set, so stage two never calls the host.

**`record_slate` moved before the offer trace.** At the base the slate's decision record was written after
`_fill_offer_trace`. The trace writes nothing and, now that the generated-probe identities are hoisted, reads
nothing. `record_slate` reads none of the trace's fields. So the two commute, and the serving goldens' rows,
including the decision record and its numbered ids, are unchanged.

**Why not a third stage.** The pre-ranking writes (supply reconciliation, placement's fast track, the cold lane's
deferrals) sit between reads that must see them (`refactor-i2.md` §3). They stay in the shell under `serving`, as
I2-1's fix left them. Moving them behind the persist call would reorder reads and writes, which this step does not
do.

## 3. The serving entry point and the flag

- **The flag is already gone.** `persist_explanations` had 0 uses at the base. I2-1's fix
  (`refactor-i2.md` §8.2, `6c7918046e`) removed it and ported its 117 uses with a script. That fix kept the name
  `build_due_queue` for the serving build.
- **The rename.** This step renames it `serve_due_queue` (commit `2e8b1029c2`) with a whole-word replacement script:
  196 uses in 71 files across `src/`, `tests/`, `scripts/` and the two hand-written vault notes that name it. Reviews
  and specs keep the old name as history; the vault's generated references are regenerated at landing. No test
  function's name contains it, so no pinned draw's node id moves. The script:

```python
word = re.compile(r"\bbuild_due_queue\b")
paths = git grep -lzw build_due_queue -- src tests scripts docs/learnloop-architecture-vault/Concepts \
                                         docs/learnloop-architecture-vault/Maps
for path in paths: path.write_text(word.sub("serve_due_queue", path.read_text()))
```

- **The persist call.** "One persist call that the serving callers make" is `_persist_due_queue`. Every serving
  caller reaches it through `serve_due_queue`; a read caller never does.

## 4. P-ast

The ranking was moved by a script (`extract_stages.py`, kept in the step's scratch directory). It cuts five blocks
from the base's `_due_queue` and applies six substitutions to the moved text only. The comparison script checked
that each block, with those substitutions, appears verbatim in the tip:

| Block (base lines) | Where it is now | Substitutions |
|---|---|---|
| list initialization (6) | `_score_candidates` | none |
| follow-up intent filter (12) | `rank_due` | none |
| follow-up device filter (8) | `rank_due` | `device_filter is not None` → `device_refusals is not None`; `_held_for_device(vault, device_filter, x, withheld)` → `_held_for_device(vault, device_refusals, x, withheld, device_deferred)` |
| candidate loop (132) | `_score_candidates` | the same `_held_for_device` change |
| sort through shadow intent (130) | `rank_due` | the device changes; `_order_new_material(vault, repository, queue, placement_serving)` → `(vault, queue, placement_serving, taught_first)`; the `generated_probe_ids` import line dropped and `generated_probe_ids(repository)` → `generated_probe_ids`; the presentation read → `inputs.active_session_presentation` |

The base's persist block (17 lines) and slate-record block (24 lines) became `_persist_due_queue`'s two calls, with
the same arguments read from `RankedQueue`.

Whole definitions, compared by `ast.dump`:

| Definition | Result |
|---|---|
| `_persist_offer`, `_head_probe_presentation`, `_fill_offer_trace`, `_insert_pending_followups`, `_teach_back_value_admission`, `_selection_propensities`, `_apply_seeded_exploration`, `_LazyAdmissionReads`, `_gather_admission_reads`, `_after_check_split`, `check_admission` | identical |
| `_apply_contrast_pair_order`, `_BuildAdmission`, `pool_admission`, `read_due_queue` | the renamed name in a docstring only |
| `serve_due_queue` vs `build_due_queue` | identical body; docstring names the persist call |
| `_held_for_device` | reads the gathered refusal (`_gathered(device_refusals[item.id])`) and adds to `deferred` instead of `device_filter.holds_back(item)` |
| `_order_new_material` | filters the shell's every-LO signals to the slots' LOs, where it used to read them for those LOs (the read filters with the same truthiness) |

## 5. Query counts

Counted the same way as in I2a §5: SELECT and WITH per build. Base `54be27df69` and the tip were run back to back.
One row is new: `limit_generated_followup_serving`, the golden of §7. Times are single runs and noisy.

| Build | Items | Base | Tip | Change | s base | s tip |
|---|---|---|---|---|---|---|
| serving_with_session | 18 | 222 | 192 | -30 | 0.150 | 0.145 |
| read_with_session | 18 | 195 | 165 | -30 | 0.099 | 0.098 |
| read_without_session | 18 | 162 | 162 | 0 | 0.098 | 0.096 |
| admission_gates_serving | 21 | 191 | 199 | +8 | 0.109 | 0.106 |
| admission_gates_read | 21 | 147 | 167 | +20 | 0.095 | 0.094 |
| admission_probe_reads | 18 | 214 | 184 | -30 | 0.022 | 0.022 |
| admission_phone | 19 | 219 | 191 | -28 | 0.102 | 0.102 |
| admission_unconsulted_episode | 18 | 137 | 137 | 0 | 0.016 | 0.017 |
| admission_empty | 18 | 113 | 113 | 0 | 0.016 | 0.016 |
| admission_waiting_check_episode | 18 | 151 | 151 | 0 | 0.017 | 0.016 |
| intent_targets_serving | 18 | 247 | 221 | -26 | 0.103 | 0.098 |
| intent_targets_read | 18 | 193 | 193 | 0 | 0.099 | 0.097 |
| limit_generated_followup_serving | 18 | 230 | 200 | -30 | 0.104 | 0.103 |
| large n=100, read | 318 | 962 | 962 | 0 | 4.03 | 4.01 |
| large n=100, serving | 318 | 1,422 | 992 | -430 | 4.07 | 4.09 |
| large n=100, value stopping off | 318 | 956 | 956 | 0 | 0.093 | 0.091 |
| large n=100, phone | 318 | 962 | 962 | 0 | 3.98 | 3.99 |
| large n=100, unconsulted | 318 | 437 | 437 | 0 | 0.034 | 0.032 |
| large n=100, unconsulted, one item reachable | 318 | 437 | 437 | 0 | 0.033 | 0.033 |
| large n=300, read | 918 | 2,562 | 2,562 | 0 | 11.77 | 11.66 |
| large n=300, serving | 918 | 3,822 | 2,592 | -1,230 | 12.20 | 11.90 |
| large n=300, value stopping off | 918 | 2,556 | 2,556 | 0 | 0.182 | 0.174 |
| large n=300, phone | 918 | 2,562 | 2,562 | 0 | 11.90 | 11.85 |
| large n=300, unconsulted | 918 | 1,037 | 1,037 | 0 | 0.071 | 0.102 |
| large n=300, unconsulted, one item reachable | 918 | 1,037 | 1,037 | 0 | 0.067 | 0.069 |

- **The drops.** Builds with a session counted the generated-probe identities once per composition: the live one,
  every counterfactual outcome, and every composed-head outcome on a serving build. They now count them once, which
  takes 26 to 30 reads off a golden-size build and 430 or 1,230 off a large serving build.
- **The rises,** +8 and +20 on the gates vault. That build reads the taught-first signals (about 20 SELECTs) without
  making a new-material slot. Some reachable item's placement answer is "new material", but a later gate in the same
  admission withholds it, for example the freshness reserve on a diagnostic surface. The test "can a reachable item
  be new material" is a superset by design.
- **An earlier cut** read the signals whenever placement served. That added 20 to `admission_empty` as well.
- **No row rises by more than 14%.**

## 6. Proof

- **Goldens.** Recorded first, on the base source (`6b9c832d1a`):
  - `limit_generated_followup_serving`: a serving build with limit 5, where the follow-up door inserts one of two due
    cold retries and leaves out the one whose item carries the generated-probe identity;
  - `limit_read`: a sessionless read with limit 3.

  All 23 tests of `tests/test_due_queue_golden.py` pass at the tip: the due-queue goldens, both intent goldens, the
  limit goldens and the reach test. Recording was stable under `PYTHONHASHSEED` 0, 1, 777 and 12345. None moved.
- **The I2b tests still pass:** `tests/test_frozen_intent_view.py` and I2a's value-decision test.
- **`tests/test_due_queue_stages.py`** (new, 6 builds: rich serving and read, gates, intent targets, generated
  follow-up, phone). It wraps `scheduler.rank_due` so that during the stage the repository's `connection` raises, and
  re-runs the returned composition over the greedy and considered queues inside the guard. It asserts that the build
  ranked through the stage and that the phone's deferred items come back.
- **P-shadow on the goldens.** The rich, gates, intent-targets and generated-follow-up vaults were built once and
  copied with `copy_tree_with_databases` for each side. `learnloop rebuild --shadow --json` was run on base code (an
  archive of `54be27df69`'s `src` first on `PYTHONPATH`) and on branch code. On every vault the two reports are equal
  once ULIDs, hashes, stamps and roots are normalized. The deltas the reports themselves show (facet 3, mastery 3,
  schedule 5; 5 due dates moved) are the synthetic vaults' seeded states replayed, and are the same on both sides.
- **Identity pins** unchanged (§9).

## 7. Measures

| Measure | Base | Tip |
|---|---|---|
| `scheduler.py` lines | 4,196 | 4,428 |
| longest function | `_due_queue`, 646 lines | `_due_queue` (the shell), 366 lines |
| next longest | `_persist_offer` 177 | `rank_due` 192, `_persist_offer` 177, `_score_candidates` 158 |
| functions over 200 lines in `scheduler.py` | 1 | 1 (`_due_queue`) |
| test sites patching a private `scheduler` name | 13 | 13 |
| structure ratchet | | `scheduler.py` 4,196 → 4,428, raised in `03811e4624`; `golden_json_lines` 281,654 → 293,230 in `8d2fc80e9e` |

The file grows by 232 lines: the two frozen types (`RankInputs`, `RankedQueue`), the stages' docstrings and
prologues, and `_persist_due_queue`, whose keyword signature repeats `_persist_offer`'s.

The shell stays over 200 lines because of its pre-ranking reads and writes, about 185 lines. They could move into a
gather that takes `serving` (the `refactor-i2.md` §3 shape), which would bring `_due_queue` under 200 and lower the
ratchet by one. That is not done here; it is §9's follow-up.

## 8. Judgment calls

- **The rename to `serve_due_queue`.** I2-1's fix deliberately kept `build_due_queue` to avoid this churn. The
  coordinator's scope names `serve_due_queue`, so it is done as a separate, mechanical commit that can be dropped on
  its own.
- **`admit_due` is a thin constructor.** Stage one is the admission object itself. The function names the stage and
  gives tests a plain-value door.
- **Taught-first.** It is read when stage one's `placement` says a reachable item can be new material. Calling a
  pure stage-one method in the shell keeps the read away from builds where nothing can be new material.
- **`_held_for_device` reads the gathered refusals.** It returns what it defers instead of calling the host's
  `holds_back`, so stage two never calls back into the host.
- **`record_slate` before the trace,** as §2 explains.

## 9. Commands and results

Run at `2e8b1029c2`. Every command went through the scratch wrapper, each pytest command was a script in a
`systemd-run --user --scope` with `MemoryMax=3G`, at `-n 1`, or `-n 2` for the affected set.

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
| `scripts/affected_tests.py --base 54be27df69`: 1,398 files, 14 chunks of at most 100, `-m "not arc_close"` | 21,922 passed, 102 skipped, 9 xfailed, 0 failed |
| the goldens, the frozen-view tests, the stages tests and the R1 rulings file | 39 passed |
| `ruff check` | clean |
| `lint-imports --no-cache` | 52 kept, 0 broken |
| `scripts/check_gate_partition.py` | 33,177 = 33,111 landing + 66 arc_close |
| `git diff --check` | clean |

## 10. Not verified, and what is left

- **Owner copies.** P-shadow and the cost on the owner copies are the coordinator's lane.
- **P-draw.** The harness was not rerun.
- **Follow-ups:**
  - Move the pre-ranking reads and writes into a gather that takes `serving`, so the shell drops under 200 lines.
  - I2-2, the read build's follow-up marks, stays open to arc I's close, as briefed.
