# One eligibility decision: Codex review and fixes

**Stage:** `serve-eligibility-decision`, branch `serving/one-eligibility-decision`, on top of the stage record (`docs/reviews/serve-eligibility-decision.md`, tip `f6623c52f`).
**Review:** Codex job `20261017-004842-PHYZEz` (four findings: two High, two Medium).
**Result:** all four fixed. F2's suggested remedy, re-selecting a fresh surface, is deferred to the owner (Q44). The stage is now the algorithm successor **mvp-0.27**, with the kill switch **`eligibility.enabled`**.
**No migration** (207 stays free). No RPC name. No frontend change. Grading, regrade and replay are untouched. One config key: `[eligibility] enabled`, a modelled default that is left out of the decision-only template.
**Paid calls:** none. Every test uses fakes. The shadow runs used an empty config directory.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Auto-primed drafts can bypass the cold-submit guard | fixed | `efc53a86c` | `test_serve_eligibility_review.py::test_f1_an_auto_primed_draft_is_refused_when_its_cold_task_falls_due_during_grading[successor, below_the_tag, switch_off]`; `::test_f1_the_decision_refuses_any_primed_draft_and_names_its_provenance` |
| F2 | High | Ordinary practice permanently contaminates the promised cold measurement | fixed (the re-selection remedy is deferred, Q44) | `efc53a86c` | `test_serve_eligibility.py::test_the_queue_serves_a_cold_retry_submit_would_prime_as_practice_and_ends_it_honestly` (the disposition, the final receipt, the sweep, no later cold retry); `test_serve_eligibility_review.py::test_f2_*` (3 tests) |
| F3 | Medium | Retiming starts at queue construction and is not refreshed by practice | fixed | `efc53a86c` | `test_serve_eligibility_review.py::test_f3_a_delayed_open_and_submit_after_a_withdrawing_build_are_plain_practice`, `::test_f3_a_cold_check_is_never_served_on_an_item_practised_since_it_was_set`, `::test_f3_a_cold_check_served_unpractised_is_still_served` (the control) |
| F4 | Medium | Serving and historical admissibility changes have no successor or kill switch | fixed | `efc53a86c` | `test_serve_eligibility_review.py::test_f4_*` (14 cases: the vocabulary, the gate, the upgrade and the chain, new vaults, and the predecessor with the switch off and below the tag on the queue, submit, the plan, probes and Q33); `test_ux_phase4_feedback.py::test_f1l_the_quick_check_never_presents_an_item_inside_routine_display_coverage[*-predecessor]` |

## Reproduced first

**In-memory reproductions** on the branch tip, run before any change:
- **F1.** An auto-primed draft from 10:00:00 is submitted at 10:02, after its routine display lapsed and its cold task fell due. It was accepted: `DID NOT RAISE`.
- **F2.** After the practice attempt, the coldness receipt of the later cold retry has `hard_contamination = cold_item_answer_revealed_post_primed`, from the practice attempt itself (`cold_item_answer_reveal`). `surface_novelty` is `fail`, and no reveal came after the task.
- **F3.** A Monday 10:00 build re-timed the check to Tuesday 10:00. A practice answer submitted at Tuesday 10:00 was refused: "a cold retry must be unassisted and unprimed: its answer was shown (tutor answer at …)".

**Fail-first run of the final tests.** The new and updated tests ran on a `git archive` of the branch tip `f6623c52f` (`fixtures-local/failfirst-review/`). The property test, which uses new API, was excluded. **26 of 53 failed.** Among them:
- F1 at the successor, below the tag and with the switch off: `DID NOT RAISE`;
- F2's queue test: the item was not labelled, and the check was re-timed, not ended;
- F3's delayed open and submit: the task stayed `served`, not withdrawn;
- F3's practised-since-scheduled case: the cold retry was in the queue;
- F4's predecessor cases: the branch served every version the same way, so the queue did not list the cold retry, and probes were refused at mvp-0.26 too;
- the vocabulary, gate, upgrade and new-vault tests: new API.

The 27 that passed are pure, SQL-parity and control cases that hold on both trees.

## F1: any primed draft is refused a cold check

**The defect.** `attempts.submit_decision` passed `declared_primed = primed and auto_primed_reveal_total is None`. An auto-primed draft was therefore judged on the ledger alone, at the second resolution (`apply_attempt`'s, minutes later). When the exposure lapsed during grading, the primed answer consumed the cold task. Main's guard refused any primed draft.

**The fix.**
- `declared_primed` is now the draft's `primed` flag, whoever set it. A new `auto_primed` input carries the provenance.
- `_decide_submit` checks, in order:
  - hints, or a hinted attempt: `cold_check_assisted`;
  - the ledger primes it now: `cold_check_primed`, naming the rows;
  - the draft is primed: `cold_check_auto_primed`, "…: its answer was still shown when this answer was started", or `cold_check_assisted`, "…: it was declared primed".
- The provenance explains the refusal; it never exempts the draft. Below the tag, submit is main's bare guard (F4).

## F2: the measurement is withdrawn, honestly

**The cause.** Re-timing a cold check on an item whose answer stands cannot give a cold reading:
- unpractised, submit primes the item until an attempt;
- practised, the coldness receipt reads that attempt as a hard exposure of the cold item (`cold_item_answer_reveal`) and the surface as administered (`surface_novelty` fails).

The promise "its check comes a day after you practise it" was false, and the learner's later "check" was spent on contaminated evidence.

**The fix.** The practice item is never the measurement target any more. When the decision sees such a check (`cold_check_answer_shown`, due or not), the check is **withdrawn**, persisted only by a serve that writes, through `diagnosis.remediation.withdraw_cold_measurement`, in one transaction:
- **A repair `cold_retry`.** It records its typed §4.3 disposition, `unmeasurable_no_held_out_surface`. The detail has `stage = serve`, the reason code, the reveal rows and the decision record, with `servable_opportunity = false`. It then records its final coldness receipt and expires. The expiry sweep sees the outcome and writes nothing more. The saved repair forecast resolves as censored.
  - The outcome is not `contaminated_or_assisted`. Migration 145's CHECK keeps every consume-time disposition to a concrete cold attempt, and an `INSERT OR IGNORE` would have dropped the row silently. That was caught by the first test run.
  - The outcome is not `right_censored_expired` either, which claims a genuine opportunity the learner never took.
  - If the disposition cannot be written, the task is left open, so nothing ends unlabelled.
- **A `certification_cold_probe`.** It expires through the certification lane's own door for a probe whose claim no longer stands (`_cancel_stale_probes`'s). Its rate reads it as unmeasured.

The item is served as ordinary practice. Its label is "Practice: you've seen this answer, so this question no longer counts as a check." The queue reason is "practice, not a check: this question can no longer be a fresh check". Its answer is accepted, primed, and no cold check on the item comes back.

**Deferred: re-selecting a fresh surface (Q44).** The review's remedy was to select a replacement surface through the measurement workflow. That changes measurement selection, which this stage does not own (the stage notes keep it to serving, eligibility and submit admissibility):
- a re-ranking of the repair lane's candidates, or `select_held_out_probe_item`;
- a new writer of `followup_tasks.selected_item_id` and the episode's `cold_item_id`;
- an opportunity decision and the forecast binding;
- a delay anchored after the practice attempt.

Ending the measurement with an honest typed disposition is the in-scope fix. It removes the false promise and the doomed check. It also improves on main, which ran the same case into a refusal loop and then `right_censored_expired`.

## F3: nothing is anchored to a queue build

**The cause.** Withdrawal removes the re-time, so no check is left to anchor or refresh. A later decision on the item finds no open cold check (`no_cold_check`), and the open, the submit at 10:00 and the submit at 09:59:30 are all plain practice.

**The fix also closes the general case.** The decision now withdraws a cold check whose item was attempted after the check was set (`cold_check_practised_since_scheduled`): the item's last attempt is later than the task's creation, and that attempt did not answer it. The receipt reads such an attempt as a hard exposure and resets the retrieval delay, so serving the check would only spend it. This covers a practice answer through a path that wrote nothing (a non-persisting build, a stale client) and ordinary ranked practice of the cold item.

The control is unchanged: an unpractised, unrevealed check is served when it falls due, and its answer consumes it. `until` is None for a withdrawal, and the plan step's `check_due_at` is null. Nothing advertises a time that is not persisted.

## F4: successor mvp-0.27 and its kill switch

**The successor.**
- `algorithm_versions`: `ELIGIBILITY_DECISION_ALGORITHM_VERSION = "mvp-0.27"`, appended to `SUCCESSOR_CHAIN`, with `ELIGIBILITY_DECISION_VERSIONS`. New vaults start there.
- `learnloop upgrade` targets it by default (`eligibility_decision_upgrade.upgrade_to_mvp027`): from mvp-0.26, or from mvp-0.9 to mvp-0.25 through mvp-0.26's own activation. It is a tag change plus an idempotent rebuild of the same projection namespace, and anything older is refused.
- `DEFAULTS_SNAPSHOT_BY_ALGORITHM` gains mvp-0.27. All eighteen earlier snapshots were recomputed, because the effective config gains the `[eligibility]` section.

**The gate.** `serve_eligibility.decision_active(vault)` is true at mvp-0.27 or later with `eligibility.enabled`. No vault reads as off. Below it, or switched off, every path runs **mvp-0.26's own code**, not a re-derivation of it:
- **Submit.** Main's bare guard and an unbounded window. Q33's `reveal_window_bounded` is honoured only at the successor.
- **The queue's cold lane.** `_predecessor_defer_revealed_cold_followups` and `_predecessor_cold_check_hold_until` are main's functions verbatim, and `_cold_task_reveals` and `deferred_cold_followups` are restored to main's text.
- **The serve-time decision** (`cold_check_serve_decision`, read by the plan's serve) is main's hold in the record's terms. `revalidate_cold_check` returns None, so no `eligibility` key appears in a payload. The CLI asks no serve decision. It still validates before it prompts, at every version: the refusal is submit's own, only earlier.
- **Probes** (`routine_display_covers_item`, `refuse_routine_display_covered` and `serve_presentation`, which now take `vault`): main's routine-coverage guard, with main's exception text.
- **The quick check:** the serving exclusions alone.

**Kept at every version, as bug fixes with no persisted effect:** the CLI's validation before the prompt, and the completion doors validating at the clock they were given.

**Shadow and upgrade check** on backup-API copies of the tracked `fixtures/mvp017_route_check_replay` (`fixtures-local/successor-shadow/`). Each copy was upgraded mvp-0.17 → mvp-0.26 (holding its one uncited epoch, as mvp-0.26 does), then mvp-0.26 → mvp-0.27. On both copies:
- `rebuild --shadow --json` shows 0 facet, 0 schedule and 0 non-label mastery deltas. Only the rows' `algorithm_version` labels move.
- The live database hash is unchanged.
- `doctor --json` gives the same 3 issue codes on both.

The owner's vaults are at mvp-0.8, below the chain's mvp-0.9 floor, so they are unaffected until the owner upgrades.

## The claims that did not hold

- **"Submit's rule … is kept exactly."** It is now: any primed draft is refused (F1).
- **"The cold check comes back one delay later, cold."** Withdrawn. No check is promised on an item that cannot take it cold, and the measurement ends with an honest typed disposition (F2, F3).
- **"Anything served as practice is accepted as practice."** It now holds across a delayed open and a delayed submit, because the check is withdrawn, not re-timed (F3). A stale client that submits on a check it was never served still meets submit's guard, with the cause named (Q43).
- **"No successor or switch is needed."** Superseded by mvp-0.27 and `eligibility.enabled` (F4).

## Files

- `src/learnloop/serve_eligibility.py`:
  - F1's submit order and the `auto_primed` input;
  - the withdrawals: reason codes `cold_check_practised_since_scheduled` and `cold_check_auto_primed`, a `withdrawals` field, `writes`, `pending_writes` and `with_pending_writes`;
  - `decision_active`.
- `src/learnloop/scheduling/scheduler.py`: the gate on every cold-check entry point, `apply_eligibility_writes`, the lane's withdrawals, and main's functions kept for the predecessor.
- `src/learnloop/diagnosis/remediation.py`: `withdraw_cold_measurement`.
- `src/learnloop/attempts/attempts.py`: the submit gate, F1 and the Q33 gate.
- Probe paths (`probe_episodes.py`, `probe_dialogue.py`, `causal_orchestrator.py`, `sim/diagnostic_validation.py`, `learnloop_sidecar/handlers/practice.py`): the `vault` threaded through.
- `diagnosis/quick_check.py` and `learnloop_sidecar/handlers/queue.py`: the gate.
- `cli/app.py`: the attempt's gate and writes, and `upgrade --to mvp-0.27`.
- New modules and config: `algorithm_versions.py`, `eligibility_decision_upgrade.py` (new), `config/schema.py` (`EligibilityConfig`) and `config/template.py` (the snapshots).
- Tests:
  - `tests/test_serve_eligibility.py`, updated to the successor and to withdrawals;
  - `tests/test_serve_eligibility_review.py` (new, 26 cases);
  - `tests/test_ux_phase4_landing.py`, restored to main: it pins the predecessor at mvp-0.6, and its successor half is in the review file;
  - `tests/test_ux_phase4_feedback.py`: the quick-check test is parametrized by version, and the sim test's double takes `vault`;
  - the chain-tail pins in 17 upgrade and version tests;
  - `tests/cli_help_snapshot.json`.
- Docs:
  - the architecture vault: the version concept and registry notes, the pipeline map, and the regenerated config and DB references (a new `Config - eligibility` note, with 861 leaves in 53 sections);
  - `docs/algorithm-change-playbook.md`: a recorded rule;
  - the stage record: a superseded note.

## Gate

Run in the worktree with `TMPDIR=<worktree>/fixtures-local/tmp`, after `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`.

| Check | Result |
|---|---|
| `uv run --no-sync lint-imports --no-cache` | 22 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **12796 passed, 2 xfailed**, 0 failed (18 min 36 s, on `efc53a86c`). The 2 xfails are main's strict ones. The first run, on the same code before the commit, gave 12794 passed and 2 failed under heavy load: `test_stuck_prompt.py::test_kill_switch_restores_dont_know_exactly` (an effective mass of 0.670 against 0.7) and `test_mvp021_upgrade.py::test_the_successor_rebuild_equals_mvp020s_projection` (facet capability evidence). Both use the system clock, both are at versions below the tag (the predecessor path, main's code), and both passed alone three times and with their files at `-n 8` (63 passed). They are timing flakes, and the clean rerun confirms it |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **106 passed**, 12692 deselected |
| `db_generate_reference.py`, then `db_validate_reference.py` | regenerated; validator: 0 errors (325 table notes, 861 config leaves) |
| `validate_vault.py` | passed: 1112 notes, every non-template note reachable |
| CLI help snapshot | regenerated (`upgrade` only) |
| RPC pins (`tests/test_mobile_allowlist.py`) | unchanged (no RPC name) |
| frontend (`npm …`), `cargo check` | not run: nothing under `apps/` changed |
| migration, head fixture | none |

## Open questions for the owner (defaults applied)

- **Q44 (a replacement surface; Codex F2's remedy).** A withdrawn cold check ends its measurement, typed `unmeasurable_no_held_out_surface`. The alternative is to re-select a fresh held-out surface through the measurement workflow (the repair ranking or `select_held_out_probe_item`), timed one delay after the practice attempt. That would keep the measurement, but it changes measurement selection: a new writer of the task's selected item and the episode's cold item, an opportunity decision and the forecast binding. *Default: end it honestly; re-selection is a follow-up stage.*
- **Q36 (revised).** Submit's non-routine rule is kept, and serving agrees by **withdrawing** the cold check rather than re-timing it. *Default: as built.*
- **Q38 (revised).** The label reads "Practice: you've seen this answer, so this question no longer counts as a check." (or "…you've answered this question since its check was set…"). It appears in the queue reason, the plan step's `eligibility` (when that serve made the decision), and the practice detail's `eligibility`. The desktop renders no new note. *Default: no new UI text.*
- **Q40 (superseded).** The kill switch is `eligibility.enabled` (F4).
- **Q43 (revised).** A non-persisting read (a queue built with `persist_explanations = false`, the CLI's dry run) withdraws nothing: it shows the item as practice and recomputes the same decision next time. A stale client that submits a check it was never served still meets submit's guard, with the cause named. *Default: as built.*
- **Q45 (practised since scheduled).** A cold check whose item was attempted after the check was set (and the attempt did not answer it) is withdrawn when a serve meets it. That is any attempt, ranked practice included, not only one this stage served. It is the receipt's own hard-exposure rule, applied before the check is spent instead of after. *Default: as built.*
- Q22 to Q35, Q37, Q39, Q41 and Q42 stand.
