# mvp-0.17 route-check replay fixture

A small vault graded under mvp-0.17's separate proofs-and-explanations route
check: an item-kind reading, an independent re-derivation and a deterministic
gate. The check was deleted by `grading/route-check-in-grader`, which folded
its protective core into the grader's prompt (owner decision 2026-10-13).

The fixture proves that a vault with mvp-0.17 history still replays exactly.
Replay reads the blind records and the evidence rows. It never reads the check.

- **Generated at:** `e238fa07a`, by `generate_at_e238fa07a.py`, using the
  test fakes of that commit. Only that commit can run it, because it imports
  the deleted `learnloop.attempts.proof_check`.
- **Version:** `algorithm_version = "mvp-0.17"`. The schema is at migration
  186, with a rollback journal (`journal_mode = DELETE`), vacuumed. A copy
  opened by later code migrates forward on load (on main: the sources
  track's 187-195, facet locks' 196-197 and UX Phase 1's 198-199); the
  fixture itself stays at 186.
- **Outcomes recorded** (`expected.json`):
  - restored;
  - restored and disputed;
  - a learner-meaning clarification (trigger `route_check_disagreement`);
  - flagged;
  - P1 unlocated;
  - held for review;
  - a hold that a failed regrade check kept (`hold_kept_from`);
  - an adjudicated (released) hold;
  - a not-proof-like reading;
  - an unavailable checker;
  - a wrong final answer that the final-answer check outranked.
- **Derived state:** rebuilt twice with the clock in `expected.json`, so it
  is at its fixed point. That is the replay of every version below the
  rebuild-equivalence successor (`mvp-0.34`,
  `docs/reviews/rebuild-equivalence-fix.md`), which read the attempts recorded
  after the one it recomputed. The successor's bounded replay moves
  `attempt_surprise`, `learning_object_mastery` and
  `practice_item_quality_state` once, on the LOs with more than one attempt,
  and the rebuild after that changes nothing.

`tests/test_mvp017_route_check_replay.py` copies the fixture with the backup
API and checks four things:

- every grade, hold and calibration identity matches `expected.json`;
- a rebuild with today's code changes no derived row and no ledger row (and,
  with the successor's bounded replay, moves only those three tables and is
  then at its fixed point, causal hypotheses included);
- `raw_grade_events` only gains rows; compared without surrogate ids, it is
  unchanged;
- an upgrade of the copy (to `mvp-0.20`, through the sources track's
  `mvp-0.18` and `mvp-0.19`) rewrites no grade.

Never open the fixture writable in place: copy it first.
