# Reader workbench RW6a: Codex review and fixes (stage `reader-rw6a`)

Branch `reader/rw6a` (worktree `learnanything-merge4`), reviewed at
`c8f92b946` (codex job `20261017-105622-NINqMX`). Stage record:
`docs/reviews/reader-workbench-RW6a.md`. Spec:
`docs/specs/spec_reader_workbench_v1.md` §9.1, §5.4, §14 (G25, G31, G50);
UX `docs/specs/ux_reader_workbench_v1.md` §4.8, §4.12, W12, S10, S11.

Each finding was reproduced first, then fixed. Backend: the new tests in
`tests/test_reader_recap_review.py` failed **10 of 10** on the reviewed code.
F1 was also reproduced through the reviewed API itself (a scratch run that was
not kept, calling the old `demonstrated_since` with the real
`lo_certification` and the real timelines): the missed gain returned `[]`, and
the spurious gain returned `lo_composite` dated at the unused alternative's
attempt. F3's test runs the production fold (`fold_demonstrated_timeline`
over an observation and its correction), and on the reviewed code the revoked
success cleared the claim. Frontend: the fixes were reverse-applied as one
patch (`git apply -R`) over the nine changed modules. The 11 new vitest tests
in `ReaderScreen.recapReview.test.tsx` and `reader/recapReview.test.tsx` failed
**11 of 11** on that code, and the patch was then re-applied. All pass on the
fix.

**Paid calls:** none ($0.00). Fakes only. No provider, no key and no vault
were opened, so no live verification was needed: RW6a adds no model route.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | "Since last time" uses the wrong certification transition | fixed | `1d83a114c` | `test_f1_a_gain_at_the_recipes_capability_counts_although_the_facet_had_credit`, `test_f1_an_unused_alternative_crossing_later_is_not_a_new_gain`, `test_f1_dated_by_the_attempt_that_completed_the_recipe`, `test_f1_nothing_is_claimed_while_the_lo_is_not_demonstrated_now`, `test_f3_the_timeline_carries_each_attempts_effective_credit_and_capability_credit` (all real ledger, real `lo_certification`) |
| F2 | Medium | "Revisit once" can create duplicate commitments | fixed | `296db5f43` | vitest *F2: revisit once from the card commits once, and the card and Wrap up then show it done*, *F2: a retry after an uncertain result reuses the request's key* |
| F3 | Medium | A revoked success still removes the independent-check claim | fixed | `1d83a114c` | `test_f3_a_success_regraded_to_nothing_leaves_the_claim_open` (revoked, standing, regraded up, older attempt regraded in the window) |
| F4 | Medium | Resolving an inquiry at the destination removes its undo | fixed | `1d83a114c` | `test_f4_resolving_at_the_destination_moves_the_inquiry_to_resolved_with_undo`, `test_f4_an_old_inquiry_resolved_and_undone_in_the_reader_stays_listed` |
| F5 | Medium | "Open" does not reopen the selected inquiry | fixed | `296db5f43` | vitest *F5: open shows that inquiry on Ask, expanded and in view, with its crumb* |
| F6 | Medium | The `w` shortcut can open an invisible wrap-up | fixed | `296db5f43` | vitest *F6: w from the Ask tab, or with the rail collapsed, opens Wrap up where it can be seen*, *F6: the opening reveals the Guide before anything is recorded* |
| F7 | Medium | A failed wrap-up read is recorded as a successful opening | fixed | `296db5f43` | vitest *F7: a failed wrap-up read shows nothing and records no opening*, *F7: a failed event write leaves the loaded lists shown*, *F7: where the learner lands, a failed read records no opening and the line stays* |
| F8 | Medium | Abandoned problems disappear from the recap | fixed | `1d83a114c`, `296db5f43` | `test_f8_an_abandoned_problem_is_in_the_recap_with_a_reopen`; vitest *F8: an abandoned problem reads set aside, with a reopen through resume* |
| F9 | Medium | Skim mode does not mute the new proactive UI | fixed | `296db5f43` | vitest *F9: skim mutes the card and the rail's offer; w still opens Wrap up on request*, *F9: muted by skim, the rail's offer is withheld and the card folds* |
| F10 | Medium | Disabling inquiries leaves recap controls that cannot work | fixed | `1d83a114c` | `test_f10_inquiry_off_refuses_every_recap_rpc_and_names_no_switch` |

Ten Medium findings, all fixed, none rejected. No High finding was raised.

## What changed, by finding

**F1 (the certification transition).** `demonstrated_since` now runs on the
real ledger. Its signature is `(vault, repository, lo_ids, *, after)`, and
the mocked pure variant is gone. An LO counts when `lo_certification(...)`
holds now and the **same predicate** did not hold at the previous session's
end. "The same predicate" means `recipe_gaps`: hard components at their
capability, one alternative per `any_of` group, and the integration cell.
`recipe_gaps` and `lo_certification` gained an optional `demonstrated`
resolver (`facet -> demonstrated capabilities`). It defaults to the ledger now,
so every existing caller is byte-identical, and the docstring's one-predicate
rule still holds. The as-of resolver reads a new read-side field on
`TimelinePoint`: `capability_credit`, which holds every capability's cumulative
credit after the event, with the embedded-share cap applied exactly as
`canonical_projection` banks the cell. Corrections are folded at the moment
they landed. The gain is dated by the moment after `after` at which the LO last
went from not demonstrated to demonstrated, and `attempt_id` is the attempt at
that point. If the curve and the ledger ever disagree, nothing is claimed. The
old mocked dating test in `tests/test_reader_recap.py` was removed, because the
finding asked for real transitions, and it points to the new tests.

**F3 (effective successes).** `TimelinePoint` also carries `attempt_credit`,
the credit this attempt contributes after this epoch. Because a correction
replaces it, an attempt's last point is its effective grading. A claim is
answered only by an attempt made at or after the session's start whose latest
point still holds unassisted, unprimed credit. Neither new field is in
`as_dict`, so receipts, snapshots and the curve's API are unchanged.
`test_receipt_exactness`, `test_facet_evidence_timeline` and the certification
suites pass. The existing claims test now passes `attempt_credit=1.0` on its
synthetic success.

**F4 (Wrap up's membership).** Wrap up's inquiries are the ones the session
touched, plus any root whose status was set between the session's start and
now. Each one is listed by its current status, so a resolve, or its undo, from
Wrap up in the Reader or at the destination moves the line between *Still
open* and *Resolved* instead of dropping it. The typed summary
(`ReaderSessionSummaryV1`, G25) is unchanged: it still reports what the session
itself resolved.

**F5 (open).** `useReaderInquiry.openInquiry(rootId, spanId)` is the recap's
*open* and *open ▸*. It clears the Ask find filter, expands the root, pushes a
`branch` crumb on the detour strip (with the root's exchange id, so walking
back restores the Guide), shows the passage, selects Ask and scrolls the
inquiry's card into view. An id that is not in this source's history falls
back to a peek at the passage.

**F2 (one commitment).** `commitInquiry` now refuses a second request for the
same root and preset while one is in flight. It also refuses one that is
already committed (`committedFor`: the chip's own state, and the anchor's
`test_me_later` annotation). A retry after a failed or uncertain call reuses
the same `clientIdempotencyKey`. The key is cleared only on success. The card
and Wrap up both read the same state and show *revisit once ✓*, which is not
actionable once committed. The ordinary Ask chip already showed this.

**F6 and F7 (opening Wrap up).** The footer and `w` share one opening. It
first reveals the Guide with the rail expanded (`showGuideRail`), reads
Wrap up, shows it, and only then records `wrap_up_opened`, fire-and-forget. A
failed read shows nothing and records nothing, so the offer stands. A failed
event write leaves the loaded lists on screen. The destination line
(`WrapUpOffer.tsx`) follows the same order.

**F8 (abandoned problems).** The card's *Unfinished* list now includes
abandoned workbench sessions, with `status: "abandoned"`, the line
*… · set aside* and **Reopen this problem ▸**. That link goes through the
existing resume path (`workbenchOpen` with `entry: "resume"`), which reopens an
abandoned session (RW2a's `resume_session`).

**F9 (skim mutes).** While skimming (`muted`: inquiry on and the mode set to
skim), the card is not presented. It waits folded, so *last time ▸* reopens it
after skimming. The rail's *Wrap up (under a minute)* and the key bar's `w`
entry are withheld. `w` itself still opens Wrap up on request. A Reader left
while skimming arms no destination offer: `ReaderScreen` reports `muted`
through the new optional `onSkimmingChange`, and `App` keeps it in a ref.
Stored activity is untouched.

**F10 (the inquiry dependency).** All four recap RPCs refuse
`inquiry_disabled` while `reader_inquiry.enabled` is off, and they refuse
before any read or write. The config DTO also omits the `recap` key, so the
desktop asks nothing. This enforces the stage record's §3 item 1 ("no card,
no Wrap up, no offer") instead of relying on the absence of visits.

## Claims that didn't hold, now

- *"Dated by the certifying attempt"*: now the recipe predicate's own
  transition (F1).
- *Independent-check claims reflect an unassisted success*: now the
  attempt's effective grading (F3).
- *"`w` … opens the three lists in the rail"*: it reveals the Guide first
  (F6).
- *Inquiry off means no card, no Wrap up, no offer*: now enforced at the
  RPCs and in the config DTO (F10).
- The dating and action coverage is real now. The F1 tests use the real
  ledger and the real `lo_certification`, F4 performs the resolve and the undo
  round trip through `build_wrap_up`, and F2, F5 and F6 run through the Reader.

## Not changed (the review's other notes)

- **Missing presentation elements** (a map link, actions on the reinforcing
  lines, element-level switch-off controls, the optional Today re-entry
  card): these are not defects in what RW6a ships, and none of them is in
  the findings list. Adding them would widen the stage, so they are left as
  the stage record's open items.
- **Scope, G31, G50, security, persistence**: the review found these
  conforming, and the fixes keep them so. There is no migration, no table, no
  route and no new write. The only write is still the three salience events.
  F7 makes `wrap_up_opened` accurate. Import contracts: 24 kept.

## Gate

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 24 kept, 0 broken |
| Full suite, `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | 12925 passed, 2 xfailed, 1 failed under load: `test_sidecar_reader_p3_slice2.py::test_reading_usable_with_synthesis_worker_down` (a subprocess RPC test, `KeyError: 'result'`; code this step does not touch). Rerun alone 3 times: 1 passed each time. Total 12926 passed |
| Durability lane, `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | 106 passed, 12822 deselected |
| `npm install`, `npm run typecheck` | ok |
| `npm test` (vitest) | 114 files, 934 passed (923 before, plus the 11 new tests). The first run, made while the full suite held the machine, had one timing failure in `Workbench.test.tsx` *F8: a vault switch …*. That file passed 35 of 35 alone 3 times, and the whole run passed 934 of 934 afterwards |
| `npm run frontend:build` | ok |
| `cargo check` | not rerun: nothing under `src-tauri` changed in this fix step (the stage's own gate ran it) |
| DB references | not needed: no schema change |

## Round 2

A Codex verify of the round 1 fixes (1d83a114c, 296db5f43) came back
**REOPENED** on two findings. It found F2 and F4–F10 fixed, and no
default-path regression: 300 certification cases and 300 timeline histories
matched c8f92b946, and all 24 import contracts passed. It also asked for one
missing test (F9). The fixes are on `reader/rw6a` after e8d624fc4.

### Findings and rulings

**F1 (round 2) [Medium]: historical certification still took in later
regrades** (`recap.py:513`, `facet_evidence_timeline.py:717`). Attempt A is
first unassessed. Before the previous session ends, attempt B on the same
surface earns 1.0 and certifies the LO. Later A is regraded successfully.
The extraction worked out B's novelty discount from A's *latest* grading, so
B's earlier credit was cut to 0.25 after the fact. The "as of the session's
end" read then found the LO uncertified and reported A's regrade as a new
gain.
*Ruling:* the as-of-cutoff read uses only the grading state in effect at the
cutoff: gradings, regrades and corrections written at or before it, the
novelty and discount accounting included. "Now" reads the current state, as
before. It is a recap-only read: with default arguments, every existing
caller of `recipe_gaps`, `lo_certification`, the timeline extraction and
fold, `TimelinePoint.as_dict` and the receipts stays byte-identical to
c8f92b946. No algorithm successor, and no change to scoring, scheduling,
projections or serialization.

**F3 (round 2) [Medium]: uncredited embedded evidence cleared the
independent-check claim** (`recap.py:469` `_effective_success_since`,
`facet_evidence_timeline.py:453`). An unassisted attempt that supplies only
embedded credit for the facet banks nothing under the default
embedded-share cap of 0.5 when the cell has no direct credit. But
`attempt_credit` held the uncapped contribution, so the claim was cleared.
*Ruling:* only credit that banks toward certification after the cap clears
a claim. Round 1's correction handling stays: a success regraded to nothing
still does not clear.

**F9 [Low, test only]:** skim suppressing the destination wrap-up offer in
`App.tsx` had only been inspected. It needed a direct integration assertion.

### Fixes

- **F1.** `facet_evidence_timeline.snapshot_as_of(snapshot, cutoff)` is the
  grading ledger as it stood at the cutoff. It keeps only the
  grading-evidence rows written by then, and a row superseded later counts
  as still standing. Replaying that snapshot makes each attempt's latest
  epoch *at the cutoff* the one that drives novelty, so a later regrade
  cannot rewrite what an earlier attempt banked. The replay hold
  (`contract_unrecorded`) has no timestamp of its own, so it is kept only
  for attempts whose rows were all written by the cutoff.
  `facet_evidence_timelines` gains an optional keyword `as_of` (default
  `None`: the ledger now, unchanged). A new `vault_timeline_snapshot` loads
  the snapshot, P0 masses included, once. `demonstrated_since` now evaluates
  `certified(lo, moment)` on the curve replayed as of that moment, both at
  the cutoff and at each candidate dating moment, memoized per moment over
  one snapshot. "Now" is still `lo_certification` on the ledger.
- **F3.** `TimelinePoint` gains one read-side field outside `as_dict`:
  `attempt_banked_credit`. It is what this attempt's latest-epoch credit adds
  to its cells, as the ledger banks them with the embedded-share cap
  applied, at this event: for each cell, the capped total minus the capped
  total without the attempt. `_effective_success_since` reads it instead of
  `attempt_credit`. Embedded-only credit in a cell with no direct credit
  banks 0 under the cap, so the claim stays. The latest-point rule (a
  success regraded to nothing does not clear) is unchanged.
- **Tests.** In `tests/test_reader_recap_review_r2.py`, everything runs
  through the production ledger writes (`complete_self_graded_attempt`,
  `apply_attempt` with a PF-c unassessed criterion, `supersede_self_grade_rows`
  plus `insert_grading_evidence` for a regrade, the canonical projection),
  extraction, fold, `lo_certification` and the recap. No timeline is mocked.
  - F1: the exact A/B scenario through `demonstrated_since`. Nothing is new
    since minute 60, and B is still the gain since minute 7. The as-of curve
    equals the curve as it stood before the later regrades, at mvp-0.7 and
    at the latest tag (regrade-contract epochs).
  - F3: the embedded-only case under the vault's real default cap (asserted
    0.5 from `vault.config`), plus a control with the cap off (1.0), where
    the same embedded credit banks and answers the claim.
  - Round 1's F3 regression folded synthetic, uncapped events into a mocked
    `facet_evidence_timelines`. It is rewritten through the real ledger as
    four cases: revoked, standing, regraded up, and before the session. The
    mocked version in `tests/test_reader_recap_review.py` is removed. The
    second half of `test_reader_recap.py::test_claims_needing_an_independent_check_are_assisted_only_facets`
    also patched in synthetic points with `attempt_credit=1.0`. It now uses
    real attempts: an assisted one, one before the session, and an
    unassisted one.
- **F9.** `apps/learnloop-tauri/src/app/App.wrapUpSkim.test.tsx` renders the
  real `App` shell, with stubs for the Reader, the library and the offer, an
  api Proxy, and the Tauri event and file-drop hooks. It goes Reader →
  Library through the nav. Not skimming, the wrap-up line is armed. When the
  Reader reports skim through `onSkimmingChange`, no offer renders. No
  production frontend code changed.

### Fail-first

Each new test was run against the old code without overwriting the
edits. The edited files were copied to the scratchpad first, the old
files were written from `git show`, and the edits were restored from the
copies afterwards (`cmp`-verified).

- pytest against e8d624fc4's `recap.py` and `facet_evidence_timeline.py`:
  **4 of 4** new regression tests fail. That is the F1 scenario, the as-of
  curve test (both versions; the `as_of` keyword does not exist there), and
  the F3 embedded-only test, which fails at its final assertion: the claim
  is cleared. The F3 cap-off control and the four rewritten round 1 cases
  pass on both trees, as expected: they pin behaviour that was already
  right, now through the real path.
- vitest: the F9 suppression is already in e8d624fc4 (round 1), so the test
  passes there. Against c8f92b946's `App.tsx` (before round 1's F9 fix), the
  skim case fails, **1 of 1**, and the control passes. `App.tsx` was
  restored and is identical to HEAD.

### Default path against c8f92b946

A seeded comparison, run as a temporary pytest file and then removed, loads
c8f92b946's `facet_evidence_timeline.py` and `goal_certification.py` from
`git show` as separate modules and checks them against the working tree:

- **300 randomized ledger histories.** Each has a recipe of 3 kinds, mvp-0.7
  or the latest tag (174 and 126 cases), a default cap of 0.5 or 1.0 (219
  and 81), and 2–9 operations: self-graded attempts with random points and
  hints, PF-c unassessed attempts, regrades, and trace observations
  licensing a supporting target. Across them: 1,862 timeline points, 363
  corrections, 623 discounted points, 13 points with capped embedded credit
  and 25 certified LOs. For each history the extraction's events, every
  facet's folded curve (`as_dict` serialized, plus every field c8f92b946's
  `TimelinePoint` had), the single-facet curve, `recipe_gaps` and
  `lo_certification` (default arguments) are identical. A replay
  `as_of` a moment after every write also equals the current curve exactly.
- **300 randomized pure folds**, with random events, caps (1.0, 0.5, 0.25,
  0.0) and repeat discounts. They are identical.

Result: **600 of 600 identical.** The default path is byte-identical to
c8f92b946.

### Open (found, not fixed: out of scope)

- **[Medium, pre-existing, default path] A regrade to zero on an item whose
  criteria have no authored targets never reaches the Demonstrated curve.**
  `_observation_events_by_facet` emits an epoch's event only for
  `requested & (historical_facets | credited_facets)`. `historical_facets`
  reads authored `criterion.targets` only, and a zero-credit epoch credits
  nothing, so the correction is dropped. The attempt keeps its earlier
  credit on the curve. On an mvp-0.7 vault with the basic item
  (`pi_svd_define_001`, compiled targets), self-graded 4/4 and then
  regraded to 0, the ledger banks 0.0 (`facet_capability_evidence`), but
  the curve still ends at 1.0. That breaks the receipt-exactness invariant
  for such items, and for them round 1's "a success regraded to nothing
  does not clear" does not hold, because the recap reads the curve. The fix
  would change the default extraction (the compiled targets would have to
  count as historical facets). That is a change to the persisted-meaning
  read, which belongs to the algorithm-change playbook and is not in this
  ruling. The round 2 tests use items with authored targets.
- **The as-of read replays the grading ledger only.** Trace observations,
  causal activity classifications and the P0 active interpretation masses
  are read as they are now. None of them carries an "effective at" stamp
  the timeline snapshot could filter on. The replay hold is approximated as
  described under Fixes.

### Gate (round 2)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run --no-sync lint-imports --no-cache` | 24 kept, 0 broken |
| Full suite, `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | 12934 passed, 2 xfailed, 0 failed |
| Durability lane, `pytest -m durability` | 106 passed |
| `npm run typecheck` | ok |
| `npm test` (vitest) | 115 files, 936 passed (934 plus the 2 F9 tests). The first run, made while the full suite held the machine, had 2 timing failures in files this step does not touch: `FeedbackScreen.test.tsx` *keeps the old Next …* and the known `Workbench.test.tsx` *F8: a vault switch …*. Rerun alone, the two files passed 46 of 46 in 2 of 3 runs while the suite was running, then 3 of 3 afterwards. The whole run passed 936 of 936 afterwards |
| `npm run frontend:build` | ok |
| `cargo check` | not rerun: nothing under `src-tauri` changed |
| References and snapshots | not needed: no config default and no schema changed |

## Round 3

A Codex verify of round 2 (20fa20a69) confirmed that the A/B regrade and the
embedded-only regressions are fixed through the production paths, and found
no default-output change: 600 fold histories with 13,425 points matched
c8f92b946. It came back **REOPENED** on two Medium findings. The fixes are
ebcfe6ff4 on `reader/rw6a` after 3747dd91d.

### Findings and rulings

**F1 (round 3) [Medium]: the cutoff replay lost historical replay holds**
(`facet_evidence_timeline.py:278`, `snapshot_as_of`). An attempt's
contractless regrade is held at the cutoff (the mvp-0.26 regrade-contract
hold, `grade_contract_unrecorded`). A later contract-bearing regrade
releases the hold. `snapshot_as_of` dropped the later grading, but it took
the historical holds only from the *current* `contract_unrecorded` set,
which no longer has the attempt. So the epoch that was held at the cutoff
banked credit in the replay (its credit at the cutoff went from 0 to its
full value), which can hide a real "Since last time" gain.
*Ruling:* decide the hold as of the cutoff from the grading epoch effective
then, by the predicate production uses when it records the hold
(`attempts.current_epoch_reading`), applied to the grading rows written by
the cutoff, the legacy only-grade exception included. Where part of it
cannot be rebuilt from timestamped rows, add no storage (no table, no
migration in this stage): take the reading that matches what the ledger
credited at the cutoff wherever that is known, and record the gap.

**F2 (round 3) [Medium]: a later correction left claim-clearing banked
credit stale** (`facet_evidence_timeline.py:505`, read at `recap.py:471`
`_effective_success_since`). Before the session, attempt D banks direct
credit. In the session, unassisted attempt E adds embedded credit, which
banks under the 0.5 cap beside D's. Then D is regraded to zero. The cell
banks zero, but E's last point still carried the `attempt_banked_credit`
measured at E's own event, so the claim was cleared.
*Ruling:* whether an attempt clears an independent-check claim is decided
on the current state: each attempt's latest grading, against the cell's
final totals with the cap (the cell's banked credit now with and without
the attempt). Rounds 1 and 2 stand: a success regraded to nothing does not
clear, and uncapped embedded credit does not clear. Recap-only: no change
to the default extraction or fold output, or to `as_dict`.

### Fixes

- **F1.** `snapshot_as_of(snapshot, cutoff, *, vault=None)` now decides the
  hold per attempt as of the cutoff. An attempt with no row written after
  the cutoff has the same current epoch then as now, so it keeps the hold
  the ledger records on it now (that is production's own verdict on that
  epoch, and it keeps the as-of-after-every-write replay equal to the
  current curve). For an attempt with a row written later, the recorded
  hold describes the later epoch, so the new `_epoch_held_as_of(rows,
  vault, item_id)` evaluates `current_epoch_reading`'s predicate over the
  rows as they stood at the cutoff: the current epoch among the rows
  standing then (`grading_epochs.current_epoch`), held when it cites no
  contract, unless it is the attempt's only grade
  (`grading_epochs.only_grade` over the rows written by then, superseded
  ones included) and its score fits today's item maximum
  (`max(rubric.max_points, 1)`, no rubric: not held). A later
  contract-bearing regrade therefore no longer lifts a hold at the cutoff,
  and a later contractless one does not place one there.
  `facet_evidence_timelines(..., as_of=...)` passes the vault. The
  extraction's own gate is unchanged: the set is read only at
  `REGRADE_CONTRACT_VERSIONS`.
- **F2.** `fold_demonstrated_timeline` now measures `attempt_banked_credit`
  at the end of the curve. After every event is folded, each attempt's
  latest-epoch credit is evaluated against the cells' final totals with the
  embedded-share cap: per cell, the capped total minus the capped total
  without the attempt's credit (its embedded share removed with it). The
  value is the same on every point of the attempt. The points are built
  once, after the fold, so there is no second construction pass.
  `_effective_success_since` reads it unchanged, so a claim is cleared only
  by an attempt whose credit still banks now. The field stays read-side and
  outside `as_dict`. `recap._effective_success_since` is its only reader
  (no other caller, test or frontend reads it). The fold's prefix
  invariant (§16) compares `as_dict`, which does not carry the field; the
  fold's docstring names it as the one field measured against the curve's
  end.
- **Tests** (`tests/test_reader_recap_review_r3.py`). Everything goes
  through the production writes: `complete_self_graded_attempt`, the
  regrade door `regrade_attempt` with a deterministic points grader fake,
  and `upgrade_to_mvp026`. Then extraction, fold, `lo_certification` and the
  recap. No snapshot or timeline is mocked.
  - F1, held then released: at mvp-0.25, H is self-graded 0 of 4 (minute
    5), O 2 of 4 on a second surface (minute 10), and H is regraded to 4 of
    4 by the predecessor's door, which cites no contract (minute 20). The
    upgrade to mvp-0.26 holds H (minute 30). The session ends (minute 40).
    H is regraded again at mvp-0.26, citing its contract, which releases the
    hold (minute 50). H's credit at the cutoff is 0, the as-of curve equals
    the curve as it stood before the release, and `demonstrated_since(after
    = minute 40)` reports the LO, dated minute 50, by H. After the release
    nothing is new, and as of a moment after every write the replay equals
    the current curve.
  - F1, predicate parity: on that vault, and on the upgrade suite's
    predecessor vault (a seeded history of only grades, a contract-cited
    grade, and two uncited regrades, one with a blind record), the predicate
    over every attempt's whole ledger holds exactly the attempts the
    upgrade's replay held.
  - F2, at mvp-0.7 and the latest tag: D before the session (4 of 4 on a
    `recall`-targeted item), the assisted session's claim, E in the session
    (embedded `recall` credit, trace-licensed), then D regraded to 0 through
    `regrade_attempt`. The ledger cell banks 0 (`facet_capability_evidence`),
    the curve ends at 0, E's banked credit is 0, and the claim stays open.
    The inverse control (D stands): E's capped embedded credit banks and
    the claim clears.

### Fail-first

The edited `facet_evidence_timeline.py` and `recap.py` were copied to the
scratchpad. 3747dd91d's versions were written from `git show`, the new
tests were run, and the edits were restored from the copies
(`cmp`-verified both times).

- **5 of 5** new regression tests fail on 3747dd91d:
  - F1 held then released fails on the behaviour: H's credit at the cutoff
    is 0.6957788 (its uncited regrade banking), not 0.
  - The two F1 predicate-parity tests (the held-then-released vault and the
    upgrade suite's vault) fail because the predicate does not exist there
    (`ImportError` on `_epoch_held_as_of`). They pin the new function
    against the holds the upgrade's replay recorded.
  - F2 at mvp-0.7 and at the latest tag (mvp-0.27) both fail on the claim:
    `[] == ['recall']`, so E cleared it.
- The F2 inverse control passes on both trees at both versions, as it
  should: it pins behaviour that was already right.

### Default path against c8f92b946

Round 2's seeded comparison was rerun unchanged against this tree. It ran
as a temporary pytest file (removed afterwards), with c8f92b946's
`facet_evidence_timeline.py` and `goal_certification.py` loaded from
`git show` into separate scratchpad modules:

- **300 randomized ledger histories**: mvp-0.7 or the latest tag (174 and
  126), a default cap of 0.5 or 1.0 (219 and 81), 1,862 timeline points,
  363 corrections, 623 discounted points and 25 certified LOs. The
  extraction's events, every facet's folded curve (`as_dict` serialized,
  plus every field c8f92b946's `TimelinePoint` had), the single-facet
  curve, `recipe_gaps` and `lo_certification` (default arguments) are
  identical. A replay `as_of` a moment after every write equals the
  current curve exactly, `attempt_banked_credit` included.
- **300 randomized pure folds** (random events, caps 1.0, 0.5, 0.25 and
  0.0, and repeat discounts) are identical.

Result: **600 of 600 identical.** `attempt_banked_credit` is the one value
that changed, by the ruling. It is not a field c8f92b946 had, and it is not
in `as_dict`.

### Residuals (F1: what the cutoff cannot rebuild from timestamped rows)

- **The only-grade exception's score.** Production compares the attempt
  row's `rubric_score` with today's item maximum. When a later grade has
  overwritten that row, the score as it stood at the cutoff is on no
  timestamped row. So the predicate sums the epoch's `points_awarded` (as
  `calculate_rubric_score` sums them, `int(round(...))`). A fatal-error cap
  or the PF-c assessed-fraction rescale could make the true score differ.
  That only matters for an attempt whose only grade, at the cutoff, was
  later regraded *and* whose item maximum has since dropped below that
  score. When the attempt has no later row, the recorded hold is used, so
  this does not arise.
- **The hold is read under today's tag.** The extraction applies the
  regrade-contract reading (and so the hold) whenever the vault is at
  mvp-0.26 or later now, across its whole history, as the current curve
  does. A cutoff that fell before the vault's upgrade sees an uncited
  regrade as held, although the ledger then (mvp-0.25) banked it. When the
  vault crossed the tag is recorded only in the rebuild and manifest log,
  not on the grading rows, and the stage's ruling adds no storage.
- **Today's item, as replay reads it.** The predicate reads today's rubric
  maximum, as `current_epoch_reading` does at every replay. An item edit
  after the cutoff counts at the cutoff.

### Open (found, not fixed: out of scope)

- **[Low, pre-existing, default path] The current curve has no point where
  a replay hold is placed.** A hold is recorded by replay (the mvp-0.26
  upgrade, or a rebuild) without a grading row. So the current Demonstrated
  curve shows the held attempt's earlier, uncited epoch banking from when it
  was written until the releasing regrade, and only the held epoch, when it
  is last, banks nothing. The recap's "Since last time" no longer reads
  those intermediate points: it replays as of each moment. But the plotted
  history for a held-then-released attempt overstates the hold interval.
  Fixing it would change the default extraction.
- Round 2's open items stand unchanged: a zero regrade on items without
  authored targets never reaches the curve (queued separately), and trace
  observations, activity classifications and the P0 masses are read as
  they are now.

### Gate (round 3)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run --no-sync lint-imports --no-cache` | 24 kept, 0 broken |
| Full suite, `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | 12941 passed, 2 xfailed, 0 failed (12934 plus the 7 round 3 tests); no flakes |
| Durability lane, `pytest -m durability` | 106 passed |
| Frontend gate | not run: nothing under `apps/` changed |
| References and snapshots | not needed: no config default and no schema changed |
