# Refactor I2a: the due queue's admission reads, gathered up front (stopped twice at the query-count rule)

Branch `refactor/i2a-admission-reads`, based on main `3018ac3f16`. This is the first of I2's three sub-steps
(`docs/reviews/refactor-i2.md` §5 option A, approved by the owner on 2026-11-20: "superset reads, two pure stages,
as I2a, I2b, I2c"). Structure track. Line numbers are at the branch tip, in `src/learnloop/scheduling/scheduler.py`.

**Outcome.** The first cut (`ab47edc9a9`) gathered every in-progress probe episode and computed its value decision
in the gather. It stopped at the brief's query-count rule. A build whose episode no item reaches more than doubled
its reads, and took 4 to 12 s instead of under 0.1 s (§5, first table).

The coordinator chose two options from §8 of that stop, together: gather an episode only when an item could reach
it, and compute its value decision where the admission consults it, from gathered reads only. The second cut
(`eef705fc55`, with `b258170128` moving one import) does both. Every golden, the P-ast comparison and the pins still hold:
- The paused, put-away and empty cases now read exactly what the base read.
- The value decision's compute is back at its consult, and that consult makes no repository read.

One case still more than doubles the reads, so the step stops again. In that case an item of the episode's LO
passes the routine gate and intent's exclusions, but a later gate withholds it: here, a "Check once" that is not
due yet. With 100 or 300 instruments on the LO, SELECTs go from 437 to 969 and from 1,037 to 2,569. Time goes
from 0.03 s to 0.06 s and from 0.07 s to 0.15 s. The remaining cost is `eligible_instruments`' reads for each
item on the LO, with no valuation. The options are in §8.

## 1. What the admission read, and where

`_BuildAdmission` (`:3473`) holds the build's per-item gates that come after the routine gate
(`serving_exclusions.BuildGates`), asked through `serving_exclusions.admission_reason`, and its probe score. At the
base it held a repository, eleven `_Once` readers and three caches.

- **Eager reads.** In a queue build, ten of the readers were values the build had already read (`_Once.of`).
- **Lazy reads.** It made five kinds of read itself, inside `probe_score`, and only for an item that had passed the
  earlier gates:
  - `administered_surface_exclusions`, once;
  - `_load_episode_context` and `_load_episode_eligible`, once per episode, cached;
  - `voi.probe_episode_decision`, once per episode, through the build's lazy `VoiContext`, with
    `qualifying_observation_count` and `session_qualifying_total`;
  - `familiarity_discount`, once per probe candidate.
- **Device check.** `device_gate` asked the host's `DeviceFilter.refuses`, last, and only for an item that passed
  every other gate.
- **Outside a build.** `check_admission` and `pool_admission` built the same class over `_Once` closures that read
  on first use.

## 2. The value and its gather

`AdmissionReads` (frozen dataclass, `:3016`) holds plain values. The build creates it with
`_gather_admission_reads` (`:3240`) where it used to construct `_BuildAdmission`: after every write the build makes
before ranking, and before intent's check split and the candidate loop.

| Field | Read behind it | Where |
|---|---|---|
| `exclusions` | `routine_serving_exclusions` | `_due_queue`, as before |
| `item_states` | `practice_item_states()` | `_due_queue`, as before |
| `placement_serving` | `_placement_serving(persist=serving)` (on a serving build, the fast track runs first) | `_due_queue`, as before |
| `open_episodes` | `servable_open_episodes` when placement serves, else `open_probe_episodes` | `_due_queue`, as before |
| `probe_block_reason` | `probe_serving_block_reason` (after `calibration_cap_lifted`) | `_due_queue`, as before |
| `mastery_states` | `mastery_states()` | `_due_queue`, as before |
| `frontier` | `build_goal_frontier` (after the cold lane's deferral writes) | `_due_queue`, as before |
| `errors_by_lo` | `active_error_events`, grouped | `_due_queue`, as before |
| `fsrs_weights` | `resolve_fsrs_weights` | `_due_queue`, as before |
| `recent_attempts_by_lo` | `list_recent_attempts_by_learning_objects(frontier)` plus `held_attempt_ids` marks | `_due_queue`, as before |
| `administered_surfaces` | `administered_surface_exclusions` | gather, when a reachable episode exists (else None) |
| `episode_contexts` | `_load_episode_context`, per reachable episode | gather |
| `episode_eligibles` | `_load_episode_eligible` (`eligible_instruments`), per reachable episode with a context | gather |
| `probe_familiarity` | per `(episode, item)`: `resolve_coverage`, then `familiarity_discount_from_attempts` over one `list_recent_attempts_by_learning_object` plus `mark_held_attempts` read per LO | gather |
| `voi_context` | a copy of the build's `VoiContext` after `_load_voi_reads` (`:3122`): latencies (`item_minutes`), triage routes (`label_actions`) and, for each episode posterior's labels with mass, the routes' intervention durations and the measured unresolved cost (`loss_table`). Its repository is `_NoRepository` (`:3114`), which raises on any read | gather, when an episode needs a decision (else None) |
| `qualifying_observations` | `qualifying_observation_count`, per reachable episode with an instrument (value stopping on) | gather |
| `session_qualifying_observations` | `session_qualifying_total`, once | gather |
| `pinned_channels` | `probe_robust.load_pinned_channel`, per such episode with a calibration model hash | gather |
| `device_refusals` | `DeviceFilter.refuses(item)` for every item; None without a filter | gather |

**Reachable** (`_reachable_episodes`, `:3211`): an in-progress episode with a locked set and no probe block, with
at least one item on its LO that passes two gates. Both are computed from the gathered values and the build's
intent view, with no read of their own:
- **The routine gate**, `serving_exclusions.routine_withhold_reason(vault, item, state, exclusions)`. It fails for
  retired, inactive state, an exam reservation, held-out material, a reserved cold check, a rung-variant hold,
  staged ownership, a generated probe closed or reserved, a dialogue instance, an administered diagnostic probe, an
  unservable stimulus, no LO, or a put-away LO.
- **Intent's exclusions**, `intent_view.intent(item_id).excluded`: Pause, Reference, Let go. This is the part of
  intent's gate that does not wait on the check split. That split asks the admission itself, so it cannot run
  before the gather.

The admission scores an item's probe only after both gates, so an episode that fails this test is never consulted.
The later gates (a pending check, the generated-probe request rule, placement, cold start, the freshness reserve)
are not asked. An episode those gates alone keep from every item is still read: that is the stop in §5.

**The value decision.** It is computed in `probe_score` at its consult, as at the base:
`voi.probe_episode_decision(self.reads.voi_context, episode, list(eligibles), context[1], session_id=...,
qualifying_observations=..., session_qualifying_observations=..., pinned_channel=...)`. Every argument comes from
the reads. `voi.probe_episode_decision` gained an optional keyword, `pinned_channel`. Its default,
`READ_PINNED_CHANNEL`, reads the channel through `ctx.repository` as before. No other caller changes.

**A read that raises** in the gather is kept as a `_ReadFailed` and raised by `_gathered` where the admission first
asks for it, which is where the lazy build raised it. A failure while loading the value context is stored with the
episode's channel, so that episode's decision raises it.

**Outside a build**, `_LazyAdmissionReads` (`:3305`) has the same field names. Each field is a `cached_property`
whose body is the old closure. The episodes' reads (all probing episodes, with no reachability filter, since
nothing is read until the first probe score) are made together on first need. The decision is computed at its
consult there too, over its own value-context copy with no repository.

**What `_BuildAdmission` keeps:** `voi_probe_decisions`, the episodes it consulted, in consult order. The offer
trace, the slate record and the forecasts carry exactly these. The persist step's episode caches are copies of the
gathered maps without the failed reads.

## 3. Reads that became unconditional

All of these hold only for a reachable episode (§2), not for every in-progress one:

| Read | Before | After | Cost when paid |
|---|---|---|---|
| `administered_surface_exclusions` | when an item of the episode reached the probe score | when a reachable episode exists | 1 query |
| episode context | the same, past the surface check | per reachable episode | a few queries |
| `eligible_instruments` | the same | per reachable episode with a context | about 10 fixed queries plus `resolve_instrument` for each item on the LO |
| the two qualifying counts, the pinned channel, `VoiContext`'s latencies, routes, durations and unresolved cost | when an instrument reached the value gate | per reachable episode with an instrument (value stopping on) | a few queries; no valuation |
| familiarity | per probe candidate admitted by value | per eligible instrument | 1 read per episode LO (was 1 per candidate) |
| `DeviceFilter.refuses` | per item past every other gate | once per item, phone builds | no query in these vaults; the host's media predicate was not measured |

Nothing between the gather and the candidate loop writes, so every gathered value is the one the lazy read returned.

## 4. P-ast

A scratch script (`ast` over `git show 3018ac3f16:...` and the tip) normalized the base's `_BuildAdmission` methods
with `self.<field>()` → `self.reads.<field>` for the ten eager fields.

| Definition | Result |
|---|---|
| `admits_check_candidate`, `freshness_gate`, `placement_gate`, `probe_gate`, `reserved_annotation` | identical |
| `check_candidate_refusal`, `in_probe`, `placement`, `cold_start_gate` | identical after the substitution |
| `device_gate` | one line: `self.device_filter ... .refuses(item)` → `self.reads.device_refusals ... _gathered(self.reads.device_refusals[item.id])` |
| `probe_score` | read sites only (below) |
| `__init__` | the repository, the `_Once` readers, the caches and `device_filter` → `reads` |
| `_LazyAdmissionReads.placement_serving`, `.open_episodes`, `.frontier`, `.recent_attempts_by_lo` vs the base closures | identical bodies, with names rebound to `self.` attributes |
| `pool_admission` | `admission.item_states()` / `.exclusions()` → `admission.reads.*` |
| `_load_episode_context`, `_load_episode_eligible`, `_head_probe_presentation`, `_persist_offer`, `check_admission`, `_teach_back_value_admission` | identical |

`probe_score`'s differences:
- **Repository.** `repository` is dropped from the unpacking.
- **Surfaces.** The lazy `administered_surface_exclusions` block becomes `_gathered(self.reads.administered_surfaces)`.
- **Context and eligibles.** `_load_episode_context(...)` and `_load_episode_eligible(...)` become lookups.
- **The value decision** is the same call at the same place. Its arguments change only where they come from:
  - `self.voi_context()` → `self.reads.voi_context`;
  - `_load_episode_eligible(...).values()` → the gathered eligibles' values;
  - the two count reads → gathered counts;
  - a `pinned_channel=` keyword is added from the gathered channels.
- **Familiarity.** The `rubric` / `resolve_coverage` / `familiarity_discount` statements become one lookup. The
  `resolve_coverage` call in `_prospective_familiarity` is `ast.dump`-identical. `familiarity_discount` is replaced
  by its own two halves, with the recent-attempts read made once per LO.

## 5. Query counts

SELECT and WITH statements per build, counted by a trace callback on every connection
`learnloop.db.connection.connect` opens during the build call. The scratch script is not committed. The base and
the tip were run back to back on the same machine with the same script.

The large vaults are `build_rich_vault` plus n items on each of three LOs:
- `lo_a`, due;
- the probe's LO, linked to its instrument card, so every one is an eligible instrument;
- `lo_spectral`, new material.

The variants:
- **unconsulted:** the probe's LO is paused.
- **one reachable:** every item of the probe's LO is exam-reserved except `pi_svd_define_001`, which has a
  "Check once" that is not due.
- **waiting_check (golden):** the same shape on the golden vault, using pauses.

Times are single runs and noisy.

**Second cut (tip `eef705fc55`), base → tip:**

| Build | Items | SELECT base | SELECT tip | Change | s base | s tip |
|---|---|---|---|---|---|---|
| serving_with_session | 18 | 221 | 222 | +1 | 0.150 | 0.154 |
| read_with_session | 18 | 194 | 195 | +1 | 0.101 | 0.100 |
| read_without_session | 18 | 161 | 162 | +1 | 0.099 | 0.098 |
| admission_gates_serving | 21 | 192 | 191 | -1 | 0.108 | 0.112 |
| admission_gates_read | 21 | 148 | 147 | -1 | 0.095 | 0.095 |
| admission_probe_reads | 18 | 215 | 214 | -1 | 0.022 | 0.022 |
| admission_phone | 19 | 218 | 219 | +1 | 0.106 | 0.103 |
| admission_unconsulted_episode | 18 | 137 | 137 | 0 | 0.016 | 0.016 |
| admission_empty | 18 | 113 | 113 | 0 | 0.015 | 0.015 |
| admission_waiting_check_episode | 18 | 151 | **183** | +32 | 0.018 | 0.018 |
| large n=100, read | 318 | 961 | 962 | +1 | 4.04 | 4.08 |
| large n=100, serving | 318 | 1,421 | 1,422 | +1 | 4.13 | 4.15 |
| large n=100, value stopping off | 318 | 1,057 | 956 | -101 | 0.093 | 0.088 |
| large n=100, phone | 318 | 961 | 962 | +1 | 4.03 | 4.09 |
| large n=100, unconsulted | 318 | 437 | 437 | 0 | 0.033 | 0.033 |
| **large n=100, unconsulted, one item reachable** | 318 | 437 | **969** | **+532 (2.2x)** | 0.033 | 0.058 |
| large n=300, read | 918 | 2,561 | 2,562 | +1 | 12.00 | 11.89 |
| large n=300, serving | 918 | 3,821 | 3,822 | +1 | 12.28 | 12.18 |
| large n=300, value stopping off | 918 | 2,857 | 2,556 | -301 | 0.183 | 0.184 |
| large n=300, phone | 918 | 2,561 | 2,562 | +1 | 11.92 | 12.49 |
| large n=300, unconsulted | 918 | 1,037 | 1,037 | 0 | 0.114 | 0.084 |
| **large n=300, unconsulted, one item reachable** | 918 | 1,037 | **2,569** | **+1,532 (2.5x)** | 0.073 | 0.147 (2.0x) |

Reading the table:
- **+1:** a build whose probes value stopping withheld now makes one familiarity read for the episode's LO.
- **Minus rows:** builds that valued probes make one familiarity read per LO instead of one per candidate.
- **Unconsulted and empty:** they read what the base read, and the goldens record no episode read (§6).
- **Bold rows:** these are the stop. An item reaches past the reachability test, a later gate withholds it, and
  the gather reads the episode's instruments. The valuation's seconds are gone (0.06 s and 0.15 s against 4.2 s
  and 12.4 s in the first cut), but `eligible_instruments` still makes its reads per item on the LO.

**First cut (`ab47edc9a9`), for the record:** the same rows as above, except:
- unconsulted episode: 137 → 169;
- empty: 113 → 127;
- large unconsulted: 437 → 969 (0.035 → 4.24 s) and 1,037 → 2,569 (0.075 → 12.40 s).

## 6. Proof

- **Goldens.** All 14 tests of `tests/test_due_queue_golden.py` pass at the tip, under `PYTHONHASHSEED` 0, 1, 777
  and 12345. That is 15 records: the three whole-queue ones, eleven admission ones and the waiting-check one, plus a
  reach test. Every record was recorded on the base code (`3018ac3f16` source). Nothing was regenerated after a
  source commit.
- **Reads per episode** (`episode_reads` in `admission_unconsulted_episode` and `admission_empty`). These records
  spy on the scheduler's probe-episode reads: `administered_surface_exclusions`, `episode_hypothesis_set`,
  `eligible_instruments` and the two qualifying counts. Both say none, at the base and at the tip.
- **Fail-first.**
  - The first cut's scheduler fails these two records.
  - Recording every gathered decision instead of the consulted ones fails `admission_unconsulted_episode`.
  - Familiarity read with empty covered facets fails `admission_probe_reads`.
- **No read at the consult.** `test_the_probe_value_decision_reads_nothing_where_it_is_computed` runs on the
  golden vault (an episode with a pinned channel) and on the gates vault, both in a build and outside one. It wraps
  `voi.probe_episode_decision` and checks two things: that the context it receives raises on a repository read, and
  that its decision's `as_dict()` equals the one computed with a fresh repository-backed `VoiContext` and the
  channel read lazily. It also asserts that a decision was computed in each place.
- **Identity pins.** Unchanged (§10).
- **Draws.** The two seeded draws take the same inputs. The goldens pin the exploration and the contrast-pair rows.
- **A reader holding a snapshot.** The gather uses the repository's ordinary short connections. No new long-lived
  read.

## 7. Goldens added (all recorded on the base code)

`b93ae06b00`, `1f8dd1ff8f` and `51a59d11f1`. Built by `tests/due_queue_helpers.py`, stored in
`tests/goldens/due_queue/`:
- **`admission_gates_serving` / `admission_gates_read`.** These withhold items for `retired`, `inactive_state`,
  `reserved_exam`, `cold_check_reserved`, `diagnostic_microprobe`, `diagnostic_probe_administered`,
  `no_learning_object`, `lifecycle_put_away`, `intent_paused`, `diagnostic_freshness_reserve`,
  `placement_assumed_withheld` and `diagnostic_reserved`, plus a valued diagnostic surface in the episode.
- **`admission_probe_reads`.** Value stopping off, with familiarity discounted to 0.85.
- **`admission_phone`.** `device_ineligible`, `cold_start_unattempted`, and the filter's `deferred`.
- **`admission_unconsulted_episode`.** The probe's LO is paused; a phone read; episode reads: none.
- **`admission_empty`.** Every item retired; episode reads: none.
- **`admission_waiting_check_episode`.** One item reachable but held by a check that is not due. Queue, trace and
  rows only. It deliberately has no read record, since the gather reads this episode and the base did not.
- **`outside_admission_gates` / `outside_admission_probe`.** `pool_admission` and `check_admission` asked about
  every item.
- **The reach test.**

Not reached:
- `unservable_stimulus`: `unservable_reason` always returns None.
- `rung_variant_hold`, `staged_owned`, `generated_probe_*`: set memberships the step passes through untouched.
- `placement_maintained_withheld`.
- `voi_value_below_minutes_cost` on a diagnostic surface.
- `zero_priority`.

## 8. The decisions and the options at the second stop

- **First stop.** The options were: accept the cost; filter by the routine gate; compute the value decision at its
  consult; or make the episode reads lazy. The coordinator (2026-11-22) chose the second and third together. They
  are implemented as §2 describes. The filter counts intent's exclusions (Pause, Reference, Let go) as well as the
  routine gate, because "a paused LO's episode is not gathered" needs them.
- **Second stop.** The only case left is an episode whose LO has an item that passes both filters while every such
  item is withheld by a later gate. The later gates are:
  - a pending or held "Check once";
  - the generated-probe request rule;
  - placement;
  - cold start;
  - the device.

  The gather reads that episode's instruments: 2.2x and 2.5x SELECTs with 100 and 300 instruments, and 2x time at
  300. The options:
  1. **Accept it.** It needs a later gate to withhold every reachable item of an episode with many instruments. The
     time cost is now small (0.15 s at 300 instruments), and the owner copies' episodes have a handful of
     instruments, so there it is likely a few dozen queries. Not measured.
  2. **Filter on intent's whole gate after the check split.** Not possible as things stand: the split asks the
     admission's own predicate, which can reach the probe score. I2b's frozen intent view, split once, could make
     this the gate, and the filter would then read exactly what the lazy build read except for placement and cold
     start.
  3. **Make `eligible_instruments` cheaper.** For example, resolve instruments only for items that are not
     routine-withheld or intent-excluded. This changes a diagnosis module's read (not its result) and is outside
     I2a.
  4. **Gather an episode's instruments lazily.** That keeps a read between the decisions, which is option B's
     boundary in `refactor-i2.md` §5.

## 9. What this means for I2b and I2c

- **I2c's first pure stage can now include the whole admission:** every gate, the probe score and each episode's
  value decision. These are computed from `AdmissionReads` with no repository. The only exception is
  `self.intent_view`, which `probe_score` reads through `effective_due_or_none` and which I2b freezes. The value
  decision runs at its consult, over the gathered value context, so a pure stage pays the valuation only for
  episodes it consults.
- **I2b** freezes the intent view, which would also allow §8 option 2. It also makes the teach-back site's
  `VoiContext` repository-free. The probe site's context is already a gathered copy with `_NoRepository`.
- **The persist step** still takes the episode caches, as copies of the gathered maps. I2c's persist call can take
  `AdmissionReads`.
- **Outside readers.** `check_admission` and `pool_admission` keep `_LazyAdmissionReads`.

## 10. Commands and results

All runs went through the scratch wrapper. Every pytest run was a script under the step's scratch directory with
`-n 1 -p no:cacheprovider`, inside a `systemd-run --user --scope` with `MemoryMax=3G`.

**Second cut** (`eef705fc55`, then `b258170128`):

| Check | Result |
|---|---|
| `tests/test_identity_pins.py` | 357 passed |
| `tests/test_structure_ratchets.py` | 3 passed |
| `tests/test_public_tip_guards.py` | 14 passed |
| `tests/test_effective_defaults_golden.py` | 3 passed |
| `tests/test_kill_switches.py` | 8 passed |
| `tests/test_sqlite_file_copies.py` | 1 passed |
| `tests/test_test_layout.py` | 3 passed |
| `tests/test_architecture.py` | 18 passed (see below) |
| `tests/test_device_eligibility.py` | 101 passed |
| `tests/test_due_queue_golden.py` | 16 passed, under `PYTHONHASHSEED` 0, 1, 777 and 12345 |
| `tests/test_voi_stopping.py` | 65 passed |
| the 93 name-filtered files, three chunks | 378 passed, 3 skipped, 1 xfailed; 408 passed, 3 skipped; 279 passed, 2 skipped |
| `test_voi_stopping`, `test_scheduler_probe_eig`, `test_probe_episodes`, after `b258170128` | 105 passed |
| `ruff check` | clean |
| `lint-imports --no-cache` | 45 kept, 0 broken |
| `scripts/check_gate_partition.py` | 32,834 = 32,768 landing + 66 arc_close |
| `git diff --check` | clean |

`tests/test_architecture.py` first failed at `eef705fc55`. `test_function_local_domain_imports_match_the_frozen_edge_inventory`
caught a new function-local import of `probe_robust` from the scheduler. Moving that import to module level then
broke the frozen-cycles contract. `b258170128` reads the channel through `voi_stopping.read_pinned_channel`
instead, which adds no edge. After it, the architecture check, the goldens, the pins and the ratchets pass again.

**First cut** (`ab47edc9a9`):
- identity pins 357; ratchets green;
- guards 14, defaults 3, CLI help 26, kill switches 8, file copies 1, layout 3, architecture 18, device 101;
- the 93 name-filtered files: 375 passed, 3 skipped, 1 xfailed; 408 passed, 3 skipped; 279 passed, 2 skipped;
- ruff clean; lint-imports 45 kept; gate partition 32,831.

**Structure golden.** Each line below was raised by hand in the commit that needed it; every other number is equal
or lower.
- `golden_json_lines`: 237,130 → 267,270 → 269,135.
- `scheduler.py`: 3,752 → 3,983 → 4,090. It is 4,087 at the tip.

## 11. Tests changed

- **`tests/test_device_eligibility.py::test_a_check_once_asks_the_same_gate`.** The stand-in now carries
  `reads.device_refusals` instead of `device_filter.refuses`. Its assertions are unchanged.
- **The golden file.** The unconsulted and empty tests spy on the scheduler's public probe-read names. The new
  value-decision test wraps the public `voi.probe_episode_decision`. No private name is patched.

## 12. Not verified

- **Owner copies.** P-shadow and the measured cost on the owner copies were not run. Agents do not open owner
  vaults.
- **Affected tests.** The full `affected_tests.py` set was not run, only the name-filtered chunks.
- **P-draw.** The harness was not rerun.
- **The phone's media predicate.** Its cost when on was not measured.
