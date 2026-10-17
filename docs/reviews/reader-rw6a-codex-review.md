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
