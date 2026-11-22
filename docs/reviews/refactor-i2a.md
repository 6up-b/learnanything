# Refactor I2a: the due queue's admission reads, gathered up front (stopped at the query-count rule)

Branch `refactor/i2a-admission-reads`, based on main `3018ac3f16`. The first of I2's three sub-steps
(`docs/reviews/refactor-i2.md` §5 option A, approved by the owner on 2026-11-20 with "superset reads, two pure
stages, as I2a, I2b, I2c"). Structure track. Line numbers are at the branch tip, in
`src/learnloop/scheduling/scheduler.py`.

**Outcome.** Built and green on every due queue golden, with every moved decision identical apart from where it
reads. It stops at the brief's query-count rule. In builds that reach the probe episode, the reads barely move
(+1 or -1 SELECT; the familiarity reads went down). But a build with an in-progress probe episode that no item
reaches now reads the whole episode. That includes `eligible_instruments`, which makes a few reads per item on the
episode's LO, and the episode's value decision. On a synthetic vault with 100 or 300 instruments on a paused probe
LO, the build's SELECTs go from 437 to 969 and from 1,037 to 2,569 (2.2x and 2.5x). Its time goes from 0.04 s to
4.2 s and from 0.08 s to 12.4 s. So the change more than doubles that build's reads, and it adds reads that grow with
the number of items where the lazy build made none (§5). This is the cost the owner's table in `refactor-i2.md` §9
listed ("about 5 queries plus one per eligible instrument, and the VoI valuation's compute, per such episode"), but
the table underestimated it, and the brief's rule says to stop. The options are in §8.

## 1. What the admission read, and where

`_BuildAdmission` (`:3375`) is the build's per-item gates after the routine gate (`serving_exclusions.BuildGates`),
asked through `serving_exclusions.admission_reason`, and its probe score. At the base it held a repository, eleven
`_Once` readers and three caches.

- **Eager reads.** In a queue build, ten of the readers were values the build had already read (`_Once.of`).
- **Lazy reads.** It made five kinds of read itself, lazily, inside `probe_score`, and only for an item that passed
  the earlier gates. These were `administered_surface_exclusions` (once), `_load_episode_context` and
  `_load_episode_eligible` (once per episode, cached), `voi.probe_episode_decision` (once per episode, through the
  build's lazy `VoiContext`, plus `qualifying_observation_count` and `session_qualifying_total`), and
  `familiarity_discount` (once per probe candidate).
- **The device.** `device_gate` asked the host's `DeviceFilter.refuses`, last, and only for an item that passed
  every other gate.
- **Outside a build.** `check_admission` and `pool_admission` built the same class over `_Once` closures that read
  on first use.

## 2. The value and its gather

`AdmissionReads` (frozen dataclass, `:3013`) holds plain values only, with no repository inside. The build creates it
with `_gather_admission_reads` (`:3162`), at the point where it used to construct `_BuildAdmission`: after every
write the build makes before ranking, and before intent's check split and the candidate loop.

| Field | The read behind it | Where it is read |
|---|---|---|
| `exclusions` | `routine_serving_exclusions` | `_due_queue`, as before |
| `item_states` | `repository.practice_item_states()` | `_due_queue`, as before |
| `placement_serving` | `_placement_serving(persist=serving)` (fast track first on a serving build) | `_due_queue`, as before |
| `open_episodes` | `servable_open_episodes` when placement serves, else `open_probe_episodes` | `_due_queue`, as before |
| `probe_block_reason` | `probe_serving_block_reason` (after `calibration_cap_lifted`) | `_due_queue`, as before |
| `mastery_states` | `repository.mastery_states()` | `_due_queue`, as before |
| `frontier` | `build_goal_frontier` (after the cold lane's deferral writes) | `_due_queue`, as before |
| `errors_by_lo` | `active_error_events`, grouped | `_due_queue`, as before |
| `fsrs_weights` | `resolve_fsrs_weights` | `_due_queue`, as before |
| `recent_attempts_by_lo` | `list_recent_attempts_by_learning_objects(frontier)` plus `held_attempt_ids` marks | `_due_queue`, as before |
| `administered_surfaces` | `administered_surface_exclusions` | the gather, when an episode can probe (else None) |
| `episode_contexts` | `_load_episode_context` (hypothesis set, posterior) per probing episode | the gather |
| `episode_eligibles` | `_load_episode_eligible` (`eligible_instruments`) per probing episode with a context | the gather |
| `voi_decisions` | `voi.probe_episode_decision` with the two qualifying counts, per probing episode with an instrument, value stopping on | the gather |
| `probe_familiarity` | per `(episode, item)`: `resolve_coverage` then `familiarity_discount_from_attempts` over one `list_recent_attempts_by_learning_object` plus `mark_held_attempts` read per LO | the gather |
| `device_refusals` | `DeviceFilter.refuses(item)` for every item; None without a filter | the gather |

A "probing episode" is one that is in progress, has a locked set and has no probe block (`_probing_episodes`, the
condition `in_probe` and `probe_score` test). The first ten reads stay where they were in `_due_queue`, and the
gather receives them. They sit between the build's pre-ranking writes (placement's fast track before placement's
reads, the cold lane's deferrals before the frontier), and moving them into the gather would need the `serving`
flag inside it. That flag is I2c's shell (`refactor-i2.md` §3, last paragraph).

**A read that raises** in the gather is kept as a `_ReadFailed` and raised by `_gathered` where the admission first
asks for the value, which is where the lazy build raised it. Without this, a build that never needs a value would fail
on it. The case is real: `eligible_instruments` raises `StagedOwnedAdministrationRefused` for an episode whose whole LO
is staged-owned. Today no item of such an episode reaches the probe score, because the routine gate withholds them all.

**Outside a build**, `_LazyAdmissionReads` (`:3219`) has the same field names. Each field is a `cached_property` whose
body is the old closure. The probing episodes' reads are made together, for every probing episode, the first time
any of them is needed (a superset of the per-episode laziness before). `device_refusals` is None.

**What `_BuildAdmission` keeps.** It keeps `voi_probe_decisions`, the episodes it consulted, in consult order: the
offer trace, the slate record and the forecasts carry exactly these, not every episode the gather valued. The
`unconsulted_episode` golden fails if they carry more (shown, §6). The persist step's episode caches are now copies of
the gathered maps without the failed reads. The head probe's episode is always one the admission consulted, so the
copy holds it.

## 3. Reads that became unconditional

| Read | Before | After | Cost per build that pays it |
|---|---|---|---|
| `administered_surface_exclusions` | when an item of a probing episode reached the probe score | when a probing episode exists | 1 query (`attempted_practice_item_ids`) |
| episode context (`fetch_hypothesis_set`, `episode_posterior`) | when an item of the episode reached the probe score past the surface check | per probing episode | a few queries per episode |
| `eligible_instruments` | the same | per probing episode with a context | about 10 fixed queries plus `resolve_instrument` per item on the episode's LO (links, card, family, calibration counts) |
| the episode's value decision (`probe_episode_decision`; `VoiContext` latencies, routes and loss tables on first use; the two qualifying counts) | when an instrument of the episode reached the value gate | per probing episode with an instrument, value stopping on | 2 count reads plus `VoiContext`'s, and the valuation's compute (the large cost in §5) |
| familiarity | per probe candidate the value gate admitted | per eligible instrument, from one read per LO | 1 read per episode LO (down from 1 per candidate) |
| `DeviceFilter.refuses` | per item that passed every other gate, sometimes twice (the check split, then the loop) | once per vault item, phone builds only | no query in the synthetic vaults (the prompt parse is memoized); the host's media predicate, when on, may look up stored assets |

No read is new in kind. Nothing between the gather and the candidate loop writes (intent's check split and the loop
make reads only), so every gathered value is the one the lazy read returned. Values the lazy build never needed are
read and dropped.

## 4. P-ast: the moved decisions

Done by a scratch script (`ast` over `git show 3018ac3f16:...` and the tip). The base's `_BuildAdmission` methods were
normalized by one substitution, `self.<field>()` to `self.reads.<field>` for the ten eager fields, then compared by
`ast.dump`.

| Definition | Result |
|---|---|
| `admits_check_candidate`, `freshness_gate`, `placement_gate`, `probe_gate`, `reserved_annotation` | identical |
| `check_candidate_refusal`, `in_probe`, `placement`, `cold_start_gate` | identical after the substitution |
| `device_gate` | one line: `self.device_filter is None or not self.device_filter.refuses(item)` became `self.reads.device_refusals is None or not _gathered(self.reads.device_refusals[item.id])` |
| `probe_score` | the read sites only (below) |
| `__init__` | the repository, the eleven `_Once` parameters, the caches and `device_filter` became `reads` |
| `_LazyAdmissionReads.placement_serving`, `.open_episodes`, `.frontier`, `.recent_attempts_by_lo` against the base's closures `placement`, `episodes`, `frontier`, `recent` | identical bodies after `vault`/`repository`/`clock`/`config` became `self.` attributes and `exclusions()`/`item_states()`/`placement_serving()`/`frontier_once()` became the properties |
| `pool_admission` | `admission.item_states()` and `admission.exclusions()` became `admission.reads.item_states` and `admission.reads.exclusions` |
| `_load_episode_context`, `_load_episode_eligible`, `_head_probe_presentation`, `_persist_offer`, `check_admission`, `_teach_back_value_admission` | identical |

`probe_score`'s differences, all at read sites:
- `vault, repository, config = ...` lost `repository`.
- The lazy `administered_surface_exclusions` block became `_gathered(self.reads.administered_surfaces)`.
- `_load_episode_context(...)` and `_load_episode_eligible(...).get(item.id)` became lookups in `reads.episode_contexts`
  and `reads.episode_eligibles`.
- The inline `voi.probe_episode_decision(self.voi_context(), episode, list(eligibles), context[1],
  session_id=self.session.session_id, qualifying_observations=..., session_qualifying_observations=...)` became
  `_gathered(self.reads.voi_decisions[episode.id])`. The gather makes the same call with the build's `voi_context`,
  the same eligible map's values in order and the same session id.
- `rubric = ...`, `prospective_coverage = resolve_coverage(...)` and `familiarity_discount(...)` became
  `_gathered(self.reads.probe_familiarity[episode.id, item.id])`. `_prospective_familiarity` keeps the
  `resolve_coverage` call identical (`ast.dump` equal). `familiarity_discount` is replaced by its own two halves
  (`recall_coverage.py:308`: the recent-attempts read with the held mark, then `familiarity_discount_from_attempts`),
  with the read made once per LO.

## 5. Query counts

SELECT and WITH statements per build, counted by a trace callback on every connection `learnloop.db.connection.connect`
opens during the build call only. The script is in the step's scratch directory, not committed. "Large" is
`build_rich_vault` plus n items on each of `lo_a` (due), the probe's LO (linked to its instrument card, so all are
eligible instruments) and `lo_spectral` (new material). "Unconsulted" pauses the probe's LO. Times are one run, noisy.

| Build | Items | Base | Tip | Change | Base s | Tip s |
|---|---|---|---|---|---|---|
| serving_with_session (golden vault) | 18 | 221 | 222 | +1 | 0.158 | 0.163 |
| read_with_session | 18 | 194 | 195 | +1 | 0.106 | 0.105 |
| read_without_session | 18 | 161 | 162 | +1 | 0.108 | 0.101 |
| admission_gates_serving | 21 | 192 | 191 | -1 | 0.112 | 0.113 |
| admission_gates_read | 21 | 148 | 147 | -1 | 0.102 | 0.102 |
| admission_probe_reads (value stopping off) | 18 | 215 | 214 | -1 | 0.025 | 0.027 |
| admission_phone | 19 | 218 | 219 | +1 | 0.107 | 0.108 |
| admission_unconsulted_episode | 18 | 137 | 169 | +32 | 0.074 | 0.149 |
| admission_empty (every item retired) | 18 | 113 | 127 | +14 | 0.018 | 0.017 |
| large, n = 100: read, no session | 318 | 961 | 962 | +1 | 4.20 | 4.23 |
| large, n = 100: serving with session | 318 | 1,421 | 1,422 | +1 | 4.17 | 4.23 |
| large, n = 100: value stopping off | 318 | 1,057 | 956 | -101 | 0.068 | 0.064 |
| large, n = 100: phone read | 318 | 961 | 962 | +1 | 4.17 | 4.19 |
| large, n = 100: unconsulted episode | 318 | 437 | **969** | **+532** | 0.035 | **4.24** |
| large, n = 300: read, no session | 918 | 2,561 | 2,562 | +1 | 12.26 | 12.26 |
| large, n = 300: serving with session | 918 | 3,821 | 3,822 | +1 | 12.77 | 12.77 |
| large, n = 300: value stopping off | 918 | 2,857 | 2,556 | -301 | 0.222 | 0.208 |
| large, n = 300: phone read | 918 | 2,561 | 2,562 | +1 | 12.38 | 12.48 |
| large, n = 300: unconsulted episode | 918 | 1,037 | **2,569** | **+1,532** | 0.075 | **12.40** |

- **The +1.** A build whose probes value stopping withheld now makes one familiarity read for the episode's LO, which
  the base never made.
- **The minus rows.** Builds that valued probes now make one familiarity read per LO instead of one per candidate.
- **The phone predicate** adds no query in these vaults.
- **The two bold rows** are the stop: the episode's per-instrument resolution reads, and the 4-12 s value decision
  (which every build that reaches such an episode already pays today), are now paid by a build that never reaches it.
  An earlier cut that read familiarity per instrument also added +1 per instrument to every build with a probing
  episode. Reading it once per LO removed that.

## 6. Proof

- **Goldens.** All 13 tests of `tests/test_due_queue_golden.py` pass at the tip. Those are the three whole-queue records
  of I2's first part, the eight admission records of §7 and two reach tests. Nothing was regenerated after the source
  commit. They pass under `PYTHONHASHSEED` 0, 1, 777 and 12345.
- **Fail-first resolution.**
  - Recording every gathered value decision instead of the consulted ones fails `admission_unconsulted_episode` and
    its reach test.
  - Reading the familiarity with empty covered facets fails `admission_probe_reads`, whose probes carry a 0.85
    discount from an answer on their LO.
- **Identity pins**: `tests/test_identity_pins.py` 357 passed, nothing written.
- **Draws.** The two seeded draws (exploration, contrast order) take the same inputs. The goldens pin the exploration
  support, roll, choice and every outcome's composition, and the contrast-pair rows.
- **A reader holding a snapshot.** The gather uses the repository's ordinary short connections, as the lazy reads
  did. No connection stays open across the build and no new long-lived read was added.

## 7. Goldens added (recorded on the unchanged code, `b93ae06b00`, `1f8dd1ff8f`)

Built in `tests/due_queue_helpers.py` and recorded in `tests/goldens/due_queue/`:

- **`admission_gates_serving` / `admission_gates_read`** (`build_gate_vault`). A serving build with the session and a
  sessionless read. The withheld items cover these reasons: `retired`, `inactive_state`, `reserved_exam`,
  `cold_check_reserved`, `diagnostic_microprobe`, `diagnostic_probe_administered`, `no_learning_object`,
  `lifecycle_put_away`, `intent_paused`, `diagnostic_freshness_reserve`, `placement_assumed_withheld` and
  `diagnostic_reserved`. They also cover a valued diagnostic surface inside the episode.
- **`admission_probe_reads`** (`build_probe_history_vault`, value stopping off, a new session). Probes scored with
  their information, their familiarity discounted to 0.85, and the elicitation row.
- **`admission_phone`** (`build_figure_vault` with a phone filter). `device_ineligible` for a picture, a teach-back
  and the item the session left for the desktop. Also `cold_start_unattempted`, and the filter's `deferred` set.
- **`admission_unconsulted_episode`.** The probe's LO is paused, and the build is a phone read. No value decision is
  recorded, and the phone is asked only about admitted items.
- **`admission_empty`.** Every item retired, so the queue is empty and the committed presentation is ended.
- **`outside_admission_gates` / `outside_admission_probe`.** `pool_admission` and `check_admission(reasons=True)`
  are asked about every item, plus `check_admission` with no intent view asked about one item. The rows changed are
  recorded (none).
- **`test_the_admission_goldens_reach_their_paths`** fails if a vault stops reaching its gate or read.

**Not reached:**
- `unservable_stimulus`: `unservable_reason` returns None for every item.
- `rung_variant_hold`, `staged_owned`, `generated_probe_closed` and `generated_probe_reserved`: each needs a
  workflow's or a commitment's rows. They are set memberships in `ServingExclusions`, which the step passes through
  untouched.
- `placement_maintained_withheld` and `voi_value_below_minutes_cost`: the latter's `voi_stop` component is pinned on
  non-probe items by the whole-queue goldens, but no diagnostic surface reaches it.
- `zero_priority`: every LO in these vaults is on the goal's frontier.

## 8. For the orchestrator: options at the stop

1. **Accept the measured cost.** The owner's §9 answer covers it in kind, and every golden and the P-ast hold. The
   unconsulted-episode build is the only one that pays: an in-progress episode whose every item is paused, put away,
   withheld by placement, reserved or not answerable on the device. The owner copies' episodes have a handful of
   instruments, not 100, so this probably costs tens of queries and well under a second there. That is not measured,
   because agents do not open owner vaults.
2. **Prefilter by the routine gate.** Gather an episode only when one of its LO's items passes the routine gate (pure
   over values already read). This removes the cost when the episode's items are retired, inactive, reserved or put
   away, but not when they are paused. Intent's gate cannot be asked before the check split binds the admission.
3. **Keep the value decision at its consult, over gathered reads.** This removes the valuation compute (the seconds)
   from unconsulted builds, but not the per-instrument resolution reads. It leaves `VoiContext` lazy, which I2b
   freezes anyway.
4. **Revert the episode reads to lazy for I2a.** Freeze only the ten eager fields, the administered surfaces and the
   device refusals, and put the probe reads to the owner with these numbers. A pure `rank_due` then needs the episode
   reads as a third stage boundary, which is option B's cost in `refactor-i2.md` §5.

## 9. What I2b needs from this

- `AdmissionReads` is the admission's frozen input. I2b's frozen intent view replaces `intent_view` (still the lazy DL2
  view, which `_BuildAdmission` reads only through `effective_due_or_none` in the probe score).
- The `VoiContext` given to the gather (episode decisions) and to `_teach_back_value_admission` is still lazy. I2b
  loads its latencies and drops its repository for the teach-back site, as `refactor-i2.md` §5 says. The gather's
  decisions already load it for builds with a probing episode.
- The persist step still takes the two episode caches (now copies of the gathered maps). I2c's persist call can take
  `AdmissionReads` instead.
- `_LazyAdmissionReads` is the outside readers' form. `check_admission` and `pool_admission` keep it.
- §8's decision decides whether I2c's first pure stage can include the probe score.

## 10. Commands and results

The scratch wrapper (empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`) wrapped every run. Each pytest run was a
script under the step's scratch directory, `-n 1 -p no:cacheprovider`, in a `systemd-run --user --scope` with
`MemoryMax=3G`.

- `tests/test_due_queue_golden.py` at each `PYTHONHASHSEED` of 0, 1, 777 and 12345, at the base (after recording) and
  at the tip: 13 passed each time.
- `tests/test_identity_pins.py`: 357 passed.
- `tests/test_structure_ratchets.py`: green after two lines were raised by hand. `golden_json_lines` went from 237,130
  to 267,270 (the admission goldens, `633b0b7300`). `scheduler.py` went from 3,752 to 3,983 lines (the value, its
  gather and the lazy reader class, which replaces the closures, `ab47edc9a9`). Every other number is equal or lower.
  The functions over 200 lines (70), the import-cycle counts, the private patch sites and the source-text assertions
  are unchanged.
- `tests/test_public_tip_guards.py` 14 passed; `tests/test_effective_defaults_golden.py` 3; `tests/test_cli_help_snapshot.py`
  26; `tests/test_kill_switches.py` 8; `tests/test_sqlite_file_copies.py` 1; `tests/test_test_layout.py` (alone) 3;
  `tests/test_architecture.py` (alone) 18; `tests/test_device_eligibility.py` 101.
- The named test files (93 whose names contain due_queue, scheduler, serving_exclusion, intent, probe, cold_retry,
  daily_plan, mobile_v2_plan, plan_determinism or pinned), in three chunks of at most 32, `-m "not arc_close"`: 375
  passed, 3 skipped, 1 xfailed; 408 passed, 3 skipped; 279 passed, 2 skipped. None failed.
- `ruff check` clean; `lint-imports --no-cache` 45 kept, 0 broken; `scripts/check_gate_partition.py` collected
  32,831 = landing 32,765 + arc_close 66; `git diff --check` clean.

## 11. Tests changed

`tests/test_device_eligibility.py::test_a_check_once_asks_the_same_gate` calls `_BuildAdmission.device_gate` with a
stand-in object. The stand-in now carries `reads.device_refusals` (`{item: True}`, then None) instead of a
`device_filter` with `refuses`. Its two assertions are unchanged.

## 12. Not verified

- **The owner copies.** P-shadow and the cost on the owner copies were not run, since agents do not open owner vaults.
  The step changes no stored row on the goldens. P-shadow replays attempts and never builds a queue.
- **The full `affected_tests.py` set** for `scheduler.py` (more than 150 files) was not run. Only the name-filtered
  chunks above were.
- **P-draw's harness** (not in the repository) was not rerun.
- **The media predicate's cost** on a phone with `media` on (a host serving page images) was not measured.
