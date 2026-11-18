# K5 fixes on `fix/k5-batch1`

## K5-14 · Deferred grading at startup

`seed-exam-attempts` writes a backdated `exam_evidence` attempt with tier-1 `exam_import` evidence and a score placeholder when no answer is supplied (`src/learnloop/goals/exam_seeding.py:387–429`). The sidecar runs startup maintenance on vault load (`src/learnloop_sidecar/context.py:290`). Both provider branches select through `pending_self_grade_regrade_attempts` (`src/learnloop/attempts/regrade.py:127`). The base selected the placeholder, built a grading context from it, and could publish the resulting tier-3 grade and replay the learning object (`src/learnloop/attempts/regrade.py:189–197,373–391,433,645–659`).

The shared query now uses the live tier-1 row's grader identity. The import's replay can leave `grading_source = 'self'` in feedback metadata, so that field would also admit imports. These are the production tier-1 writers.

| Writer | Grader ID | Startup eligibility |
|---|---|---|
| `src/learnloop/attempts/attempts.py:1098–1099` | `self` | Learner self-grades remain eligible. The existing `self_report` exclusion keeps learner statements out. |
| `src/learnloop/goals/exam_seeding.py:399–400` | `exam_import` | Score-only imports are excluded by the placeholder the seeder already stores. An import with an answer still starts with the reported score and passes its response to the grader when startup grading is ready. |
| `src/learnloop/sim/runner.py:646–647` | `sim` | Synthetic grades are excluded. |

`run_deferred_ai_regrades` uses the same change as the Codex branch. `resolve_awaiting_regrades` joins a stored clarification question to its learner response with a pending or failed grade, independent of grader tier (`src/learnloop/attempts/clarification.py:372–394`, `src/learnloop/db/repositories.py:1864–1892`). Exam seeding creates no clarification. The contract-test helper now uses the production ID `self` in place of its test ID `learner`. The assertions still exercise regrade publication.

Both startup regression cases failed on the base when the structured grader double received the score placeholder. With the query fixed, each provider path regrades the learner answer and the answer-bearing import. The score-only import keeps its score, evidence, feedback metadata, grade-channel records and due date.

## K5-2 · Repair check feedback

Interleaved retrieval on the same topic demotes the repair-effect qualification (`src/learnloop/attempts/coldness_receipt.py:1532–1564`). The verification path still writes the measured pass or failure, then writes the final coldness receipt (`src/learnloop/diagnosis/causal_cold_verification.py:288–315`). On the base, the serializer used the recorded outcome for the directional claim unless the receipt carried a budget downgrade.

The serializer now requires the final receipt's repair-effect qualification to be explicitly true for a directional claim. A measured pass or fail without that qualification gets `repair_effect_unestablished`, its original `passed` and `outcome`, and any available receipt code in `claimDowngradedReason`. The serializer uses the recorded budget, retrieval, or relevant dimension code. A missing receipt supplies no code. Checks without a measured outcome use `unmeasured`.

- The desktop's simple `FeedbackSurface` and classic/details `ColdCheckBanner` both render the measured result and say the check could not show whether the repair helped. The shared copy explains interleaved practice and over-budget reveals in plain language. An unknown claim takes each renderer's existing no-verdict fallback.
- The phone app receives the same bundle and ignores `coldCheckResult`. Its feedback renders the score and other existing fields. The mobile host and static pairing assets have no claim branch.
- The TUI feedback reads the attempt result and has no claim branch. MCP exposes separate learner-context lane and qualification fields, with no repair feedback claim. Neither has a fallback for this field because neither consumes it.
- The causal calibration report skips unknown stored resolution kinds. The recurrence report counts a factor as escalated only for `escalated_unrepaired`, and causal deferral looks for that same kind as a prior escalation. Projection and repository code preserve any non-null stored resolution kind. These readers use the factor record and never see the feedback claim.

On the base, interleaved pass and fail cases returned `repair_confirmed` and `escalated_unrepaired`, a pass with no receipt returned `repair_confirmed`, and an over-budget pass returned `downgraded`. All four assertions now pass. Both clean-check controls kept their directional claims.

### Stored state for the owner's decision

Every consumed unassisted check completes its linked remediation episode (`src/learnloop/diagnosis/remediation.py:1078–1097`). For a recorded measurement, the grade threshold determines the stored result and repair support (`src/learnloop/diagnosis/causal_probe_coherence.py:1905–1914,1937–1969`). The factor handler runs before the final coldness receipt is written. The rows below cover measured checks and matching open factors. Failing a measurement schedules no fresh retry here. Assisted retries have a separate reschedule path (`src/learnloop/diagnosis/remediation.py:831–845`).

| Measured result | Final receipt qualifies | Remediation episode | Matching open factor and support |
|---|---|---|---|
| Pass | Yes | Completed | Resolved as `repair_confirmed`. Matching candidate beliefs are withdrawn. `cold_transfer_success` is recorded. |
| Pass | False or absent | Completed | Same resolution, withdrawal and success support. |
| Fail | Yes | Completed | Resolved as `escalated_unrepaired`. A later recurrence can promote. `cold_transfer_failure` is recorded. |
| Fail | False or absent | Completed | Same escalation and failure support. |

Factor transitions are in `src/learnloop/diagnosis/causal_factor_deferral.py:201–268`. Existing preconditions can prevent a measurement entirely, as with a hard exposure (`src/learnloop/diagnosis/causal_cold_verification.py:265–306`). The owner decision on case closure and repair support remains open. Both fixes leave rebuild rules as they were.

## Verification

- New startup and sidecar cases, `t.sh` with the two explicit test nodes and `-q -n 3`. Initial test setup run had 8 failures. The corrected base run had 6 expected failures and 2 passing controls. The fixed run had 8 passes.
- Identity pins, architecture, test layout, structure ratchets and diagnosis journey golden, `t.sh -q -n 3` with those five paths. 382 passed. The golden and identity pins stayed byte-for-byte the same.
- The bash keyword search matched 22 files. `t.sh` with those explicit paths, `-m "not arc_close" -n 3 -q` and the socket test deselected had 808 passes and one fixture failure. After correcting the fixture grader ID, the same command had 809 passes.
- The remaining tests that use the corrected fixture, `t.sh tests/test_projection_timeline_agreement.py tests/test_reader_recap_review_r3.py tests/test_regrade_contract_replay.py -q -n 3 -m "not arc_close"`. 23 passed.
- `py.sh ruff check` passed. `py.sh lint-imports --no-cache` kept 42 contracts with 0 broken.
- Desktop vitest coverage is in `FeedbackScreen.phase4.test.tsx`. This worktree has no desktop `node_modules`, so vitest was unverified.
- The socket-binding case `tests/test_deferred_regrade.py::test_startup_maintenance_regrades_pending_self_grade_when_codex_ready` was deselected for the sandbox. The five known startup-hang files were outside the keyword match and remain unverified. They are `tests/test_mobile_v3_probes.py`, `tests/test_ih6_workbench_open_item.py`, `tests/test_ih4_preferences_inform_router.py`, `tests/test_mobile_rpc.py` and `tests/test_mobile_v4_reader.py`.
