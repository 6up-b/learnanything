# Router R2a: Codex review fixes

Branch `router/r2a`, worktree `learnanything-merge2`. Codex reviewed the
stage at `b3daffe4c` (job `20261013-220617-fsVq9w`) and returned eight
findings: one High and seven Medium. All eight are fixed. No finding was
rejected. The review's "claims that don't hold" are covered by F4, F5, F6
and F8, plus a correction to the stage record (see below). No model,
Decider or embedding call was made, and no money was spent.

Owner decisions in force (2026-10-12):

- the spec defaults are accepted;
- Codex is unrestrained on the subscription;
- the Decider is `perplexity/pplx-decider-v1.1-27b` on OpenRouter;
- frictionless defaults: honest labels, generous defaults, and live changes
  behind kill switches.

## Findings

| ID | Severity | Title | Verdict | Commit | Test (tests/…) or reason |
|---|---|---|---|---|---|
| F1 | High | Retrying a constraint-vetoed P2 transition bypasses the veto | Fixed | `dcd4eea31` | `test_router_p2_bridge.py::test_a_retried_constraint_vetoed_advance_stays_deferred` (the real RPC, run twice with one idempotency key), `::test_a_standing_decisions_persisted_trace_names_the_same_veto` |
| F2 | Medium | An annotation failure disables every hard constraint | Fixed | `d172f8bb4` | `test_router_g1_feasibility.py::test_an_annotation_failure_keeps_every_refusal`, `::test_a_snapshot_failure_fails_closed_only_where_a_constraint_cannot_be_established`, `::test_without_the_constraints_inputs_every_item_is_refused` |
| F3 | Medium | Session fallback steals attempts bound to another presentation | Fixed | `610dfb2a1` | `test_router_presentations.py::test_the_session_rule_never_takes_an_attempt_bound_to_another_presentation` |
| F4 | Medium | New learner-pick blocks have no router decision to bind | Fixed | `f9d059bd8` | `test_router_r2a_serving.py::test_a_learner_pick_wins_with_no_propensity_and_logs_its_own_decision` (the G9 test, which had asserted the gap), `::test_an_unplanned_proposal_pick_delivers_with_its_blocks_decision` |
| F5 | Medium | Restarting a draft loses its presentation binding | Fixed | `aa5907086` | `test_router_r2a_serving.py::test_a_saved_drafts_presentation_survives_a_restart_and_binds_at_submit`, `::test_a_drafts_presentation_never_binds_another_submission_or_item`; vitest `practiceDraft.test.ts` "restores the draft's plan presentation with the draft", `practiceOffer.test.ts` "falls back to the restored draft's presentation…", `PracticeScreen.test.tsx` "saves and mirrors the plan presentation with the draft" |
| F6 | Medium | Historical work is paired with an unseen current item revision | Fixed | `7271dbc72` | `test_router_card.py::test_past_work_shows_the_revision_it_answered_never_todays_edit` |
| F7 | Medium | Failed and assisted attempts count as demonstrated knowledge | Fixed | `7271dbc72` | `test_router_card.py::test_failed_or_assisted_work_is_never_demonstrated`, `::test_only_the_authoritative_classification_says_demonstrated` |
| F8 | Medium | Resolved misconceptions remain open problems on the card | Fixed | `7271dbc72` | `test_router_card.py::test_a_resolved_promoted_misconception_is_not_an_open_problem` |

### Reproductions on the original code

Every Python test above ran against `b3daffe4c`'s `src/`, extracted into a
scratch root and selected with `-o pythonpath=`. 12 of the 14 tests failed
there. The other two passed, as intended, because they are guards rather
than reproductions:

- `test_only_the_authoritative_classification_says_demonstrated` is F7's
  positive case. The old code also called that topic demonstrated, for the
  wrong reason.
- `test_a_drafts_presentation_never_binds_another_submission_or_item` is
  F5's negative counterpart.

The frontend tests ran in a scratch copy of the app with `b3daffe4c`'s
`practiceDraft.ts`, `practiceOffer.ts`, `PracticeScreen.tsx`, `App.tsx`,
`dto.ts` and `client.ts`. The three new tests failed there, as did the two
existing `practiceDraft` assertions whose expected shape gained
`planPresentationId`. In-memory checks also reproduced F6, F7 and F8 before
the fix:

- F6: the card showed the edited `NEW_STEM…` prompt.
- F7: an incorrect, hinted, primed attempt gave `demonstrated`.
- F8: "Confuses rank and nullity" was listed although its misconception was
  resolved.

### What changed

**F1. A retried veto stays a veto** (`scheduling/controller_cutover.py`).

- **The problem.** A retry with the same idempotency key reloads the
  standing staged decision, which carries no in-memory feasibility report.
  `_constraint_or_evsi_veto` therefore returned `None`.
- **The fix.** When the report is absent, the predicate reads the persisted
  trace's `exclusions`. Both paths take them in candidate-ref order, so the
  first call and every retry name the same veto.
- **Unchanged.** An ownership-only refusal is still not a veto.
- **The integration test** makes the run's only owned item inactive (a real
  `active_status` constraint) and calls `golden_path.advance` twice. Both
  calls return `result: null` with the same `vetoReason` and staged decision.
  The run's state and event count do not move, and exactly one deferral
  artifact is written.

**F2. Feasibility is separate from the annotations** (`daily_plan/staged_frame.py`).

- **No constraint inputs** (states, surfaces or reservations unreadable):
  every item is refused (`constraints_unavailable`).
- **The controller snapshot fails:** only items that need fresh evidence are
  refused (`freshness_unknown`, P4's rule). Ordinary items are still
  evaluated against the reservations.
- **One item's evaluation fails:** that item is refused.
- **An annotation read fails** (cold checks or the ladder): that read alone
  fails and is named in `staged_frame.error`. Refusals already made are
  kept.
- An unreadable cold-check read leaves reversibility unknown, so no item
  block enters `draw_support`.

**F3. The session-rule fallback** (`router/outcomes.py`) only takes attempts
sent with no presentation id. An attempt bound to another block's
presentation is never credited to a block whose own presentations went
unanswered.

**F4. A learner pick's block logs its own decision** (`daily_plan/engine.py`,
`router/plan_log.py`).

- The decision is logged in the block's transaction: `chosen_ref`
  `pick:<item>`, `learner_pick = 1`, no propensity, policy `learner`.
- The block, its presentation and a proposal's delivery all name it, which
  completes G9's decision → presentation → attempt chain.
- The G9 test had codified the missing chain; it now asserts the chain. An
  unplanned proposal pick through the RPC is covered.

**F5. The draft keeps its presentation.**

- **Sidecar.**
  - `save_practice_draft` stores `planPresentationId` in the checkpoint's
    practice envelope, beside the draft's retry key. There is no schema
    change. Every save replaces the value, and a save without one clears it.
  - `checkpoint_dto` returns `plan_presentation_id`.
  - A submit (or "I don't know") that sends no presentation reads the one its
    own draft named. The draft must be on the same item and use the same
    retry key. Binding is still validated at the attempt insert.
- **Desktop.**
  - The autosave and the in-memory mirror carry the id.
  - `restoredPracticeDraft` restores it.
  - `planPresentationForServe` falls back to the restored draft's id when no
    live offer for the item names one. Primed retries and guided redos still
    get none.
- No new RPC parameter: `plan_presentation_id` was already accepted (and
  pinned in `test_mobile_allowlist.py`).

**F6. Past work shows the revision it answered** (`daily_plan/router_card.py`).

- **Where the stem comes from.** It is the prompt of the attempt's pinned
  assessment contract: the single contract named by the attempt's
  unsuperseded `grading_evidence`, which must belong to the attempt's item.
  Only `$.prompt` is read (`json_extract`), so the contract's answer key and
  rubric are never read.
- **No contract, or several:** no stem shows, and the line says "question
  revision not recorded". The learner's own answer still shows.
- Today's prompt is never substituted. This is the class of error R0's F3
  fixed.

**F7. Demonstrated is the headline's word, not "graded"** (`router_card.py`,
`daily_plan/headline.py`, `router/card.py`).

- **The source of `demonstrated` and `assumed`.** Both now come only from
  `headline.classify_learning_objects`, restricted to the card's topics with
  a new `learning_object_ids` argument that does not change the classes.
  That classification uses capability-matched, unassisted certification
  credit and open placement assumptions.
- **Other topics with attempts:**
  - `assisted_only`: every attempt used hints or was a primed redo;
  - `attempted_not_demonstrated`: otherwise.
- **Topics without attempts** keep the headline's `learning`, or are
  `untested`.
- **If the classification cannot be read,** no topic is shown as
  demonstrated, and the card names that as an unknown.
- **Rendering.** The evidence summary now counts attempts. "With hints"
  became "assisted (hints or a primed redo)". Statuses render without
  underscores.

**F8. One resolution predicate** (`db/stores/daily_plans.py`, `router_card.py`).

- The daily plan's predicate is factored out as
  `open_learner_state_hypotheses(connection, learning_object_ids=None)`.
  `open_diagnosed_problem_learning_object_ids` and the card both use it.
- A validated cause whose promoted misconception is resolved is closed.
- Each card entry keeps its evidence: `hypothesis_id`, `attempt_id`,
  `error_event_id` and any open `promoted_misconception_id`.

### Claims that didn't hold

- **G9 and proposal decision references:** fixed by F4.
- **"A resumed retry key keeps" the presentation:** fixed by F5. The stage
  record's sentence is annotated.
- **Historical stems:** fixed by F6. The record is annotated.
- **The card's open problems:** fixed by F8.
- **"A fixed set of bounded queries per boundary"** was inaccurate. The
  gatherer's reads scale with the card's topics (at most 40), never with
  candidate items:
  - the topics' attempt history is read in full, for the evidence counts;
  - held grades are read in 500-attempt chunks;
  - the headline classification reads each topic's certification.

  The module docstring and `router-r2a.md` deviation 4 now say this. The
  reads were not restructured, which would have been beyond the finding's
  scope.

### Not changed (spec-conformance notes)

Codex's conformance table also lists gaps that were already documented
deviations or deferrals. They are left as they were:

- deterministic staged tie-breaking (deviation 2, open question 1);
- forced follow-ups placed by the container (deviation 3);
- teach-back and probe-block binding (deviation 6);
- the card's richer hypothesis-evidence, repair-outcome and interaction
  signals (R2b's model reads).

## Paid calls and spend

None. Every test uses fakes. No model, Decider or embedding call was made,
and no vault outside `fixtures-local/` was opened.

## Gate

`1bc0e0195` regenerates the DB and config references. Every change is a
moved source anchor:

- the card gatherer's `router.card_token_budget`;
- the daily-plan store's factored predicate;
- 100 `parameter_registry.py` citations that `264b5ed3c` had already shifted
  by seven lines. That commit postdated the stage's last regeneration, so the
  validator was failing at `b3daffe4c`.

The validator now reports 0 errors. There was no schema, config or CLI
change, so the snapshots and the CLI help are unchanged.

All gate runs were at `1bc0e0195`, which has the same code as `7271dbc72`
plus the regenerated references.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 17 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10678 passed**, 0 failed, 0 skipped (865 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10578 deselected (105 s) |
| `npm install` (apps/learnloop-tauri) | ok, no lockfile change |
| `npm run typecheck` | ok |
| `npm test` (vitest) | **488 passed** (73 files) |
| `npm run frontend:build` | ok (the existing chunk-size warning only) |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated; 0 errors |

`TMPDIR` was the worktree's `fixtures-local/tmp` throughout. No tracked
fixture vault was opened or changed.
