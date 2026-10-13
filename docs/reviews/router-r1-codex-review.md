# Router R1: Codex review fixes

Branch `router/r1`, worktree `learnanything-router-r1`. Review of the stage at
`4ec9ae8a`: ten findings (six Medium, four Low; no High). Nine are fixed in
code and F10 is fixed by listing the gaps as deviations. A finding's
suggested fix was narrowed or changed in three places (F7, F8 and F9), each
explained below. No finding was rejected. No model, Decider or embedding
call was made, and no money was spent.

Owner decisions in force (2026-10-12): spec defaults accepted, Codex
unrestrained on the subscription, the Decider is
`perplexity/pplx-decider-v1.1-27b` on OpenRouter, frictionless defaults
(honest labels, generous defaults, live changes behind kill switches).

## Findings

| ID | Severity | Title | Verdict | Commit | Test (tests/…) or reason |
|---|---|---|---|---|---|
| F1 | Medium | A row that breaks a CHECK or NOT NULL is silently dropped | Fixed | `b259d03e` | `test_router_offer_log.py::test_a_row_the_ledger_constraints_refuse_raises_instead_of_vanishing`, `::test_an_offer_row_the_ledger_refuses_is_warned_and_the_offer_still_publishes` |
| F2 | Medium | Staged P2 pairs `continue_current` with a draw propensity and an unserved item | Fixed | `b259d03e` | `test_router_staged_p2.py::test_a_served_successor_is_deterministic_and_the_draw_stays_on_its_item`, `::test_a_run_with_no_successor_logs_the_deferral_it_served`, `::test_the_live_bridge_logs_no_unserved_item_on_its_continue_row` |
| F3 | Medium | Under DL1's plan, full-list rows claim a system-served head | Fixed (seam and logging here; one line at the DL1 merge, with a tripwire test) | `b259d03e` | `test_router_offer_log.py::test_while_the_plan_serves_the_full_list_logs_no_system_choice_and_every_bind_is_a_pick`, `::test_the_full_list_seam_follows_dl1s_plan_once_it_lands` (skips until DL1 lands, then fails until wired) |
| F4 | Medium | At `mvp-0.12` an explored probe is committed as an EIG-labelled presentation | Fixed | `b259d03e` | `test_router_probe_ties.py::test_an_explored_probe_presentation_is_marked_as_drawn_not_as_the_eig_choice`, `::test_a_greedy_probe_presentation_carries_no_exploration_mark` |
| F5 | Low | `design='epsilon_tiebreak'` names a different mechanism | Fixed | `b259d03e` | `test_router_offer_log.py::test_today_offers_name_the_schedulers_own_exploration_as_their_design`, `::test_an_unregistered_design_is_refused`; existing design assertions updated |
| F6 | Low | The head rule probes readiness and reads item states a second time | Fixed | `b259d03e` | `test_router_offer_log.py::test_the_head_rule_and_the_served_list_read_one_state_snapshot`, `::test_teach_back_readiness_is_probed_once_per_offer` |
| F7 | Low | A learner pick is unguarded in the bind; a teach-back reopen writes another pick | Fixed (receipt key kept per candidate, see below) | `b259d03e` | `test_router_offer_log.py::test_a_learner_pick_that_cannot_be_logged_never_fails_the_bind`, `::test_a_teach_back_reopened_from_a_refreshed_list_is_one_pick` |
| F8 | Low | R_next can be structurally unobservable; S provisional from R_cold alone; finished sessions stay `open` | Fixed | `b259d03e` | `test_router_outcomes.py::test_r_next_is_not_applicable_on_a_single_item_learning_object_and_r_cold_finalizes_s`, `::test_an_observed_cold_retrieval_finalizes_s_and_closes_r_next`, `::test_an_untaken_offer_of_an_ended_session_is_not_taken`, `::test_the_replayer_applies_the_vaults_servable_items` |
| F9 | Low | Candidate propensities double-count "continue"; `snapshot_hash` misses the inputs | Fixed | `b259d03e` | `test_router_offer_log.py::test_candidate_propensities_are_one_distribution_with_continue_counted_once`, `::test_the_snapshot_hash_covers_the_decision_inputs_not_the_build_time`; existing sums now cover every candidate |
| F10 | Low | Session-less offers and off-offer picks are not logged | Fixed (listed as deviation 11 in `router-r1.md`) | `b259d03e` | Logging off-offer starts as `learner_pick` would mislabel system-directed serves (see below) |

`dfc4f374` regenerates the DB and config references: migration 176's edited
CHECKs and comments, and the router store, which the scanner now finds as the
direct SQL writer (it could not parse `INSERT OR IGNORE`). It also moves the
source anchors.

### Reproductions on the original code

Every test listed above was written first and run against `4ec9ae8a`. 19
of the 21 new tests failed there. The other two passed there as intended,
because they are guards rather than reproductions:
`test_the_live_bridge_logs_no_unserved_item_on_its_continue_row` (the
fixture's live decision has no within-block item) and
`test_a_greedy_probe_presentation_carries_no_exploration_mark`. The regression
run on the fixes is the gate below.

| ID | What the original code did |
|---|---|
| F1 | A `today_offer` row with `propensity_kind='exact'`, `propensity=1.0` (and a row with `snapshot_hash=NULL`) did **not raise**: `insert_router_decision` returned False and wrote 0 rows. Through `get_today_queue` with that row, the offer published, no row was written and **no warning** was logged. |
| F2 | With the production `canonical` dict and a randomized within-block choice: `chosen_ref='continue_current'`, `chosen_practice_item_id='pi_2'`, `chosen_learning_object_id='lo'`, propensity 0.5 `exact`, `epsilon_tiebreak`. With `canonical.to_state=None` (the bridge serves nothing and defers): `chosen_ref='block:measure_diagnostic'`, item `pi_2`. |
| F3 | `publish_offer` had no notion of a list that serves no head. Every list build logged its first item as the system's choice with an exact or deterministic propensity, and binding that item wrote no pick. On `daily-loop/dl1`, `get_today_queue` is the full list one key from the plan, and its picks go through `plan_learner_pick` (read on that branch with `git show`, not merged). |
| F4 | At `mvp-0.12`, with the draw forced to explore, the second in-episode probe went to `queue[0]` and was committed as the session's presentation. Its `selection_components` had **no exploration mark** (`KeyError: 'scheduler_exploration'`). |
| F5 | Today offers were logged with `design='epsilon_tiebreak'` and `exploration.mechanism='scheduler.seeded_exploration'`. No design registry existed. |
| F6 | After the DTO read, the test moved the head's `due_at` (as the post-attempt worker can). The head rule's second read then disagreed: `OfferHeadMismatch: recomposed head 'pi_svd_define_002' != served head 'pi_svd_define_001'`, and **no row** was written. With an unready teach-back in the build, readiness was probed **twice** per offer. |
| F7 | A failure inside `record_learner_pick` (a simulated `no such column`) propagated out of `save_practice_draft`, so the draft failed. A teach-back reopened from a refreshed list (`_conversation_offer` with a bound offer and a new candidate) wrote a **second** pick. |
| F8 | Outcomes had no applicability input. On a single-item learning object, R_next stayed `pending` forever, and with an observed R_cold, S was `provisional` from R_cold alone. An untaken offer of an ended session stayed `open`. |
| F9 | A pinned presentation heading 0.7 of the outcomes put 0.7 on both `continue_current` and the pinned item, so the candidates summed to **1.7**. The hash covered `built_at` but not the session context, the config or readiness (`OfferTrace` had no field for either). |

### What changed

**F1. Refused rows raise; call sites isolate and warn.**
- `insert_router_decision` uses `INSERT … ON CONFLICT(receipt_key) DO
  NOTHING`. A repeated receipt key is still an idempotent no-op that returns
  False. A CHECK or NOT NULL violation raises `sqlite3.IntegrityError`, and an
  unregistered design raises `ValueError` (F5).
- The offer receipt writes the row through `append_router_decision`, which
  wraps the insert in its own savepoint. A refused row rolls back alone with a
  `router R1: the decision ledger refused …` warning, and the offer still
  publishes.
- The empty-offer stop and the staged P2 row already ran inside
  `try/except` with warnings. They now get the refusals instead of losing
  them silently.

**F2. A staged P2 row describes what the bridge served.**
- The chosen candidate follows `advance_live`:
  - **canonical successor:** `continue_current`, deterministic, with no item
    and no LO. The successor is a run-state transition and serves none of the
    staged block's items.
  - **veto, or a run with no successor:** the run defers, logged as
    `stop_for_today` with `detail.served = staged_veto | no_transition`.
- A randomized within-block EVSI choice is a genuine `epsilon_tiebreak`
  assignment from `randomization_layer`, persisted before selection. It now
  sits on the item candidate it drew as `within_block_assignment` (design,
  propensity, seed, assignment id).
- That assignment is the row's propensity only when the staged block itself
  is served. That happens only through the builder without a bridge
  (`canonical=None`); the existing test keeps covering it.

**F3. The full list under the plan is a learner-choice surface.**
- `learnloop_sidecar/handlers/queue.py::today_head_served(vault)` is the
  seam. It returns True here, because the legacy queue is Today. At the DL1
  merge it returns `not plan_active(vault)`.
- When it is false, the build is logged on surface `full_list` with
  `propensity_kind = 'not_served'`. The chosen candidate, propensity, design
  and seed are all NULL, and `detail.head_served` is false. The candidates and
  the queue's head distribution are still recorded.
- `record_learner_pick` then finds no head on the parent, so every bind from
  the list is a `learner_pick`, the first item included, with
  `detail.offer_served_head = false`.
- Migration 176 gains `'not_served'` and a CHECK that a NULL `chosen_ref`
  occurs exactly with `not_served`.
- The tripwire test skips until `learnloop.daily_plan.engine` exists. After
  the merge it fails until the seam reads the plan.
- The DL1 merge checklist is in `router-r1.md` ("Where DL1's plan decisions
  should log").

**F4. An explored probe's presentation says it was drawn.** The selected
item can carry `exploration_selected` (possible only at `mvp-0.12`, because
earlier versions never explore to a PROBE-intent item). In that case the
committed presentation's `selection_components` gains:

```json
"scheduler_exploration": {"mechanism": "scheduler_seeded_exploration", "exploration_selected": true,
                          "exploration_rate": 0.2, "exploration_propensity": 0.2,
                          "greedy_item_id": "<the EIG-greedy item>"}
```

The offer's head propensity is computed later, in the sidecar. The
presentation's `scheduler_candidate_id` joins it to the offer's
`router_decisions` row through the slate. Greedy presentations are unchanged.

**F5. The Today draw has its own design name.**
- Today offers log `design = 'scheduler_seeded_exploration'` (the
  exploration's `mechanism` too).
- `db.stores.router.ROUTER_DESIGNS` registers it beside `epsilon_tiebreak`,
  with a description of each mechanism, and the store refuses any other name.
- The registry lives in the store (the only writer), not in a DB CHECK. A
  CHECK on this append-only table could only be changed by a table rebuild,
  and R2 must add `model_mixture`.
- Rerouting the draw through `randomization_layer` would change non-probe
  serving, as deviation 3 says, so it was not done.

**F6. One state read and one readiness probe per offer.**
- `publish_offer` reads `practice_item_states()` once. It passes that read
  to `scheduled_item_dtos` (new `item_states` argument) and to the head rule.
- One `_TeachBackReadiness` memo serves both the served list's filter (new
  `offerable` argument) and the head rule. It is probed before the row is
  built whenever any outcome would show a teach-back.
- The readiness value is recorded and hashed as an input.

**F7. Logging never fails the bind, and a conversation has one pick.**
- `bind_submission_offer` runs `record_learner_pick` in a
  `router_learner_pick` savepoint and catches any exception. A partial write
  rolls back alone, a warning is logged, and the bind commits.
- `bind_submission_offer(record_pick=False)` validates without picking.
  `teach_back._conversation_offer` passes it whenever the conversation
  already has its first offer.
- **Narrowed:** the receipt key stays `learner_pick:<scheduler candidate>`
  instead of `learner_pick:<submission_id>`. A submission already binds at
  most once (later binds return before logging), and teach-back has no
  submission id, so the suggested key would not have fixed the reopen. Keying
  by submission would instead log a second pick when a learner abandons a
  draft and restarts the same offered candidate. The validate-only bind fixes
  the reopen directly.

**F8. Outcome applicability and finalization.**
- `servable_items_by_learning_object(vault)` lists each learning object's
  active, non-microprobe items. The replayer and `learnloop router log` pass
  it in.
- R_next is `not_applicable` (`no_other_servable_item`) when the action's
  learning object has no other item.
- Only R_cold finalizes S, which the Pipeline plan states twice:
  - An observed R_cold makes S `final`.
  - R_next counts only if it was observed at or before the cold attempt. If
    not, its window is closed (`not_applicable`, `closed_by_r_cold`) and
    S = R_cold. A "next" attempt after the cold retrieval is not immediate
    uptake, and this keeps a final S from moving.
  - R_next alone stays `provisional`. The detail records `s_from`.
- An untaken head whose session has `ended_at` is `not_taken`; migration 176
  gains the value.
- Sessions that never end (the app closed) stay `open`, which is accurate.

**F9. One distribution; the hash covers the inputs.**
- When a presentation is pinned, every outcome in which it heads the offer
  serves it as `continue_current`. That mass is now continue's, and the item's
  entry carries 0 with `served_as: continue_current`.
- A draft's "continue" carries 0, because the queue never resumes a draft;
  the draft's item heads as an ordinary item. The candidates now sum to 1.
  This is slightly broader than "only when it is the chosen ref": when the pin
  heads in some outcomes but another item is served, continue keeps its true
  probability, so the logged policy stays a distribution.
- `learner_pick.detail.offer_probability_of_pick` follows `served_as`.
- The snapshot hash drops `built_at` and adds:
  - the session context (`available_minutes`, `energy`, `short_session`,
    `readiness_factor`);
  - a config snapshot (`[scheduler]` and `[router]` whole, the teach-back cap,
    the requested-items floor, the algorithm version);
  - the in-progress continuation, `head_served`, and the caller's inputs
    (teach-back readiness).
- `OfferTrace` carries `session_context` and `config_snapshot` (scheduler
  edit: two fields plus the fill).

**F10. Listed as deviation 11.**
- **Session-less offers:** they record no slate and no candidate ids, nothing
  can bind to them, and the session-start rebuild is the offer that is served
  and logged.
- **Practice started outside an offer:** these are binds with no candidate
  (library, knowledge map, golden-path or follow-up items). The sidecar cannot
  tell a learner's choice from a system-directed serve on that path, so
  logging them as `learner_pick` would mislabel system choices.
- **`OfferHeadMismatch`:** still refused with a warning rather than logged
  with a wrong number. After F6 only a defect can cause it.
- **Deviation 7 corrected:** `open_queue_item` does reach the sidecar, as
  the review noted; it binds nothing.

### Schema edit and the head fixture

Migration 176 is unmerged and will be renumbered, so it was edited in place
rather than followed by a rebuild migration. The edits:
- `propensity_kind` gains `'not_served'`;
- the propensity CHECK lets `not_served` carry NULL;
- a new CHECK requires `(chosen_ref IS NULL) = (propensity_kind = 'not_served')`;
- `router_outcomes.action_status` gains `'not_taken'`;
- the `design` and `snapshot_hash` comments are updated.

`fixtures/migration_head_176/state.sqlite` was rebuilt the same way as
before:
1. the `migration_head_175` database from `5a9a9e3d`, copied with
   `learnloop.db.copies.backup_database`;
2. migrations applied (only 176 ran);
3. `wal_checkpoint(TRUNCATE)`, then `journal_mode=DELETE`;
4. checked: integrity ok, FK-clean, `max(version)=176`, no WAL companions;
5. installed with the backup API.

Copies migrated with the earlier 176 text (the old `fixtures-local/r1-*`
copies) keep the old CHECKs. They are scratch copies and were not reused.

## Where DL1's plan decisions log (unchanged), plus the F3 checklist

See `router-r1.md`, "Where DL1's plan decisions should log":
1. **The seam:** `today_head_served` → `not plan_active(vault)`, and the
   tripwire test must pass.
2. **Renumbering:** renumber 176 with the rest, and add a `plan_block` kind
   to the CHECK in the same migration if the plan logs there.
3. **Block-boundary rows:** as before, written from
   `daily_plan/engine.py::_boundary` inside `_persist_block`'s transaction.

## Manual run (backup-API copy under `fixtures-local/`)

The worktree's tracked `fixtures/linear_algebra` was copied with
`copy_tree_with_databases` to `fixtures-local/r1fix-linear_algebra`. The
tracked vaults stay clean in `git status`. Steps: `doctor --fix-state`,
`upgrade --to mvp-0.9`, then `upgrade` (to `mvp-0.12`).

The scratch script used the sidecar's own `publish_offer` with model clients
forbidden and the teach-back provider treated as unready. It published one
offer, bound a draft to the second item, then forced the DL1 seam off and
published one list and bound its first item:

| Check | Result |
|---|---|
| Offer row | `today_offer`, `desktop_queue`, design `scheduler_seeded_exploration`, propensity 0.957142857142857 `exact`, 43 candidates |
| Sum of all candidate propensities | 1.000000000001 (12-decimal rounding) |
| Teach-back readiness probes for the offer | **1**; `inputs = {"teach_back_ready": false}` |
| Pick of the second item | `learner_pick`, `none`, parent = the offer, offer probability 0.004761904762 |
| List under the plan (seam off) | surface `full_list`, `not_served`, no chosen ref, no design, 43 candidates |
| Bind of the list's first item | `learner_pick`, `offer_served_head = false` |
| `learnloop router log` after `rebuild-derived-state` | offer `overridden`; list `not_applicable`; both picks `open` / `pending` (the sessions never ended) |
| Shadow rebuild, same version, after a second `rebuild-derived-state` | mastery / facet / schedule **0 / 0 / 0**; live database hash unchanged |

The shadow run after only one `rebuild-derived-state` showed 1 mastery and 7
schedule rows differing by seconds of `due_at`. The same happened on a fresh
copy that never published an offer, and on the pre-fix code (`4ec9ae8a`, run
from a `git archive` export), and a second rebuild converges it. This
matches the two-rebuild sequence R1 recorded, and it is unrelated to these
fixes.

## Paid calls and spend

None: no model, Decider or embedding call; $0.00.

## Gate

Run on `dfc4f374` (code final at `b259d03e`; the later commit is generated
references), with `TMPDIR` = the worktree's `fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | OK |
| `uv run lint-imports --no-cache` | **13 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8,043 passed**, 1 skipped (the DL1 tripwire, until `learnloop.daily_plan` exists), 0 failed, 46 existing warnings; 233 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **86 passed**, 7,958 deselected, 0 failed; 62 s |
| `db_generate_reference.py` / `db_validate_reference.py` | Schema **176**, 293 table notes, 632 config leaves in 37 sections, **0 errors** |
| `validate_vault.py` | Passed (1,063 notes) |
| Head fixture | `migration_head_176` rebuilt: delete journal, integrity ok, FK-clean, `max(version)=176`, no WAL companions |
| Frontend | Not changed (no npm run) |
| Tracked working vaults | Untouched (`git status` clean for `fixtures/linear_algebra`, `probability`, `arxiv_v2`) |

## Open questions

1. **`staged_policy.ladder_eligibility`** is a second copy of the §4.2
   ladder, and it can drift from `evaluate_staged_rule`. It was not in the
   findings and is left as it is. A parity test (the fired rung equals
   `evaluate_staged_rule`'s rule over a matrix of signals) would pin it, if
   wanted before R2.
2. **The F8 window rule**, which closes R_next at the cold attempt, follows
   the Pipeline plan's "R_cold finalizes S". Confirm it before R3 reads S.
