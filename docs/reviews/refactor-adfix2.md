# Arc D close fixes, group 2: K9.1 (TH-3), K9.2 (K9-1), K9.3 (K9-2), D-46, D-50

Branch `fix/arc-d-close-2`, based on main `5c561264c7`. One commit per row, each from a failing test.

| Row | Commit | Kind |
|---|---|---|
| K9.1 (TH-3) | `55205863a2` | product: a mid-check stop settles the block's committed answers |
| K9.2 (K9-1) | `4f5b325939` | product (desktop): "You asked me not to check" only after the learner's own Not now |
| K9.3 (K9-2) | `ce11173c99` | tests and replay: the primed-sibling ranking takes a clock |
| D-46 | `7ea8af7d4b` | product: a vault switch moves the ingest loops to the new vault |
| D-50 | `4bd00d1d91` | tests: the transport deadline tests measure on a clock they control |

None of the five changes persisted meaning in the playbook's sense (`docs/algorithm-change-playbook.md` step 1): no stored row is read differently, no projection, score or schedule moves, no tag, no identity pin. K9.1 writes rows that were missing (below). No new learner-facing sentence was written.

## K9.1 (TH-3): a mid-check stop settles the block's committed answers

**Failing tests** (`tests/test_teach_handoff_stop_settles.py`, at the base):
- `test_a_mid_check_stop_normalizes_joint_answers_and_releases_their_feedback`: two in-block misses on a joint vault, each through `run_post_attempt_pipeline` (so `_defers_to_block_end` skips them), then the stop: no misconception row (`assert [] == ['The SVD is ...']`).
- `test_a_mid_check_stop_queues_the_blind_answers_diagnosis`: two blind-graded in-block misses, then the stop: no `diagnose` job for either answer (`assert 0 == 1`).
- `test_the_calibration_dialogue_s_stop_settles_its_committed_turns`: two dialogue turns with misses, the stop, then `end_dialogue_block` (what `DialogueProbe.stopAndTeach` does next): no misconception row. The ledger's TH-3 said the dialogue was unaffected because it ends its block after the stop; it is affected: the stop converts the episode first, so `end_dialogue_block` returns `None` at `probe_dialogue.py:463` and `end_diagnostic_block` would return early at `probe_blocks.py:332` anyway.
- `test_a_stop_with_nothing_committed_settles_nothing` (the new return shape; failed by its signature).

Each test forbids `learnloop.ai.routing.ready_client_for_task` during the stop.

**Cause.** `diagnosis/probe_episodes.py:3462-3509` (`stop_diagnosing_and_teach`) set `converted_to_tutoring` and never ran the block end; `attempts/post_attempt.py:155-188` had deferred each in-block answer's normalization (`:156`), follow-up workflow (`:164`) and diagnosis job (`:185`) to it (`_defers_to_block_end`, `:312-322`).

**Fix, and why this one.** The strategy's shape. The block end's steps 1, 2 and 2b (`probe_blocks.py:337-401`) and the claim-checked render after them (`:402-437`, which must follow normalization and is per answer, not routing) are now `probe_blocks.settle_block_answers(vault, repository, episode, *, ai_client, clock)`, returning the released feedback and the touched misconception ids. `end_diagnostic_block` calls it where those lines were (its payload is unchanged; `test_probe_block_end.py` passes unchanged). `stop_diagnosing_and_teach` calls it first, with `ai_client=None`, before it reads the posterior (the block end also reads the posterior after normalization), then does exactly what it did. It now returns `StoppedCheck(decision, released_feedback)` instead of the bare decision; the sidecar's `stop_probe_diagnosing` returns `releasedFeedback` beside `decision`, marked `heldForReview` by the same `mark_released_held` the block end's payload goes through, and `StopProbeResultDto` declares the field. The route is untouched: the desktop still opens the lesson, the terminal app still notifies.

**Step 0.**
- *Callers of the block end:* `probe_episodes.record_episode_evidence` (`:2173`), from the attempt step (`attempts.py:3467`, no client), on every surface whose submit reaches it, the phone's `submit_attempt` included when `phone_probes` is on; `probe_dialogue.end_dialogue_block` (`:464`), from the sidecar's `end_probe_dialogue` (`handlers/calibration.py:159`, with the ready grading client); the terminal app's feedback screen (`tui/screens/feedback.py:403-411`, with its client), which ends the block after every in-block answer because it shows feedback per answer.
- *Callers of the stop:* the sidecar's `stop_probe_diagnosing` (`handlers/practice.py:668`), reached by the desktop practice card (`PracticeScreen.stopDiagnosing`) and the calibration dialogue (`DialogueProbe.stopAndTeach`); the terminal app's ^t (`tui/screens/practice.py:313-326`). The phone cannot reach the stop: `stop_probe_diagnosing` is not allowlisted (`tests/test_mobile_rpc.py`), nor are the dialogue methods.
- *Normalization with `ai_client=None` reaches no model,* so the stop runs it inline (no hand-off to the diagnose thread). By reading: the only model call in normalization is `misconceptions._match_misconception`, gated on `ai_client is not None` (`misconceptions.py:175`), and the Decider (`_decided_match`) is reached only from there. In the rest of what the settle runs (`causal_attribution.materialize_causal_episode`, `causal_factor_deferral`, `probe_episodes.maybe_reprobe_for_misconception` and the `enter_episode` it may call, `tutor/durable_promotion.sweep_late_promotion_evidence`, `update_misconception_posteriors_and_resolve`, `followups.run_deferred_block_repair_hooks`, `claim_checked_feedback`, `common_repair_recommendation`, `guided_redo_available`) no module resolves a client: the diagnosis modules that do (`split/jobs.py`, `probe_instance_generation.py`, `diagnostic_gate.py`, `diagnostic_surface_supply.py`, `grading_hardcases.py`, `probe_dialogue.py`) are reached only through `enqueue_diagnosis` (a queued job the worker runs later) and `generate_instances_for_episode`, whose model path is gated on `ai_client is not None` (`probe_instance_generation.py:1086`). The attempt step's block end has always run this path with no client. The three tests' guard on `ready_client_for_task` holds.
- *Idempotent per answer:* normalization is per error event, `enqueue_diagnosis` keys its job on the attempt id, the repair consultation skips factors with a receipt; and each block is settled once, since the stop acts on an open episode and converts it, after which neither the stop nor the block end acts on it.

**What a learner sees, per committed answer.**
- *Desktop practice card:* before and after, the lesson opens at once. Before, the answers were never normalized (the lesson's brief lists the topic's open misconceptions, `teacher/brief.py:342-348`, `:878`, and its opening record counts them, `teacher/episodes.py:117-149`: theirs were missing), a blind answer was never diagnosed (no later repair or follow-up from it), and their feedback was never shown anywhere. After, their misconceptions are on the topic when the lesson opens (as registry rows when normalization registers them; a belief normalization holds as a candidate is not in the brief, as after a block end) and a blind answer's diagnosis is queued; the feedback is released by the server but still shown nowhere (TH-4, below).
- *Calibration dialogue:* the same, before and after; the dialogue's results never showed after a stop (`ended` is null, which `onDone` receives) and still do not.
- *Terminal app ^t:* unchanged in practice. It ends the block after each in-block answer it shows, so the segment it stops in has no committed answer; only answers committed on the desktop in the same block, then ^t, are settled now. The notification is unchanged.
- *Phone:* no stop; unaffected.

**Persisted meaning.** The rows are the block end's own, from the same function: misconception registry rows or held candidates and their error-event links, `post_attempt_jobs` `diagnose` rows (both `WORKFLOW`), and the causal hooks' decision receipts (`RECEIPT`). Replay never re-normalizes ("persisted misconception_id links survive rebuilds", `followups.py`), and a rebuild reads none of these by when they were written, so nothing differs between "written at the stop" and "written at the block end", other than write times. One difference in inputs: the stop passes no client, as the attempt step's block end does, while the dialogue's and the terminal app's block ends pass the grading client. So at a dialogue stop two differently worded statements of one mix-up merge only by exact normalized text, not by the model's match. This is a judgment call (the strategy's `ai_client=None`); a client would put a model call on the request thread before the lesson opens.

**A failure while settling** now fails the stop (the desktop's existing "Could not stop the diagnostic check." and the check goes on), as the same failure fails the submit that closes a block; the settle is not wrapped. A judgment call: the alternative is to log it and convert anyway, leaving those answers as before.

**Episodes stopped before this fix** are left as they are. Per stopped block, a vault is missing, for each answer committed in the stopped segment: on a joint vault its normalization (a registry row or candidate per misconception error event, and the event's link) and its causal hooks' receipts; on a blind vault its one `diagnose` job and so its diagnosis. Doctor could list such blocks: a `converted_to_tutoring` episode whose segment before its `tutoring_transition` segment has observations whose attempts have no `diagnose` job (blind) or misconception error events with no link (joint). Not built, not backfilled.

**Vault.** `Concepts/Diagnosis and Remediation.md`'s hand-off line (it said the block is not ended) now says the stop settles first, for all three surfaces, and that no screen shows the released feedback yet. The comment in `DialogueProbe.tsx` that said closing the dialogue releases and normalizes the turns is corrected.

**Changed assertions.** `test_probe_episodes::test_stop_and_teach_ends_measurement_and_segments_evidence` reads `stopped.decision[...]` for the new return type (same check). `test_sidecar_probe::test_stop_probe_diagnosing_converts_episode` gains `releasedFeedback == []`.

## K9.2 (K9-1): "You asked me not to check" only after the learner's own Not now

**Failing test** (vitest, new `components/CausalAttribution.test.tsx`): a `needs_disambiguation` status with `probeOffered: false` and `reason` `defer_recent_burden` or `defer_session_budget` rendered "You asked me not to check again for now"; 2 of 3 failed at the base.

**Cause.** `apps/learnloop-tauri/src/components/CausalAttribution.tsx:403` branched on `status === "needs_disambiguation" && !probeOffered` alone. The orchestrator withholds the offer for three reasons (`causal_orchestrator.py:1875-1903`), and `needs_disambiguation` with no offer is reached only by those three (`:1865`, `:1894`; `RepairStatus` is built at four sites, none other with that status).

**Fix.** The line shows only for `reason === "defer_learner_preference"`. For the other two the panel shows what it shows above that line for every status: the orchestrator's `message` (`DEFERRED_OFFER_MESSAGE`, "…I won't ask again right now.", which says nothing of the learner). Nothing new is written. The DTO comments (`dto.ts`, `probeOffered` and `CausalRepairActionId`) that called every withheld offer the learner's deferral are corrected.

**Siblings checked for the same line:** `FollowupPanel.tsx` (`screens/feedback/`), `PracticeScreen.tsx`, `DialogueProbe.tsx`, the terminal app's screens and the phone's pages: none renders a repair status or the line (`probeOffered`, `probe_offered` and the reason codes appear nowhere else in the frontends or the terminal app). The panel is mounted by `CausalAttribution.tsx` itself and `RepairScreen.tsx`; both get the fix.

**What a learner sees.** Before: told "You asked me not to check again for now" when the app held the check back for recent burden or the session's budget. After: only the orchestrator's sentence that it won't ask again right now. Their own "Not now" is unchanged.

## K9.3 (K9-2): the primed-sibling ranking takes a clock

**Failing test** (`tests/test_primed_sibling_clock.py::test_a_sibling_answered_minutes_ago_by_the_given_clock_ranks_last`): two siblings, the one that covers the need's facet answered at the vault's clock's now. At the base the function has no clock (`TypeError`); the same test calling it without one (scratch run, deleted) picked the recently answered sibling (`'pi_svd_sibling_recall' == 'pi_svd_sibling_explain'`): on the wall clock an answer from ten minutes ago by the test's clock is months old.

**Cause.** `learnloop_sidecar/handlers/feedback.py:1100` read `SystemClock().now()`.

**Fix.** `_pick_primed_sibling(..., *, clock: Clock | None = None)`, `now = (clock or SystemClock()).now()`. Its three call sites in `start_primed_retry` (`:955`, `:964`, `:997`) pass nothing: the handler has no injected clock (the sidecar context carries none), so production behaviour is unchanged. The copy-or-call question against `remediation._rank_items` is K8's; the function stays where it is. The test calls the private function with plain values: no public door takes a clock.

**Siblings checked.** The other wall-clock reads in the diagnosis lane's handlers are the intent check views in `handlers/practice.py` (`:410`, `:416`, `:662`), which read the wall clock at the handler and pass `now` into the core: the core already takes the clock, as this one now does. Not changed.

**What a learner sees.** Nothing changes.

## D-46: a vault switch moves the ingest loops to the new vault

**Failing test** (`tests/test_ingest_vault_switch.py::test_a_vault_switch_drains_the_new_vault_and_claims_nothing_more_in_the_old`): a sidecar context bound to vault A, two jobs queued there with the first held in its handler; a load of vault B (the switch), one job queued in B, `_ensure_worker()` (what every enqueue door does), then A's job released. At the base B's job never ran in 10 s, and the handler record was `['old', 'old']`: after the switch the drain thread finished A's job, claimed A's second job, then went idle and exited; nothing started a worker for B.

**Cause.** `content/pipeline/jobs.py:5566-5569` (`_worker_loop`) and `:5617-5619` (`_quick_check_worker_loop`) took `self._runner` once, at thread start. `bind` with another vault (`:4131-4141`) replaced the host's runner but left the old one running, and `_ensure_worker` (`:5549`) starts no thread while the old one is alive.

**Fix, as the row says.** The two loops read the host's runner at each turn. `bind` to another vault halts the previous runner (`IngestRunner.halt`), outside the host's lock and without a join (it runs on the request thread that loaded): the old runner claims nothing more, renews no lease and fences its job in flight at its next write. The reading sweep already read the host's runner each pass; the other `self._runner` reads are per request.

**What a learner sees.** Before: after opening another vault, the previous vault's queued imports and builds went on running in the background (writing that vault), and the new vault's queued work could wait until the old queue was empty and something kicked a worker again (an enqueue, or the reading sweep's next pass for a book's preparation). After: the new vault's work starts as soon as the old job's call returns (its provider call is interrupted by the halt); the old vault's queued work waits until that vault is opened again. **Judgment call:** the old vault's job in flight is fenced, so when that vault is reopened it shows as interrupted ("Interrupted before completion", resumable) once its lease expires, where before it finished in the background. The row prescribes the halt; the alternative is to let the job in flight finish and only stop claiming, which needs a runner mode that does not exist. I followed the row.

## D-50: the transport deadline tests measure on a clock they control

**What the row asked.** Can the caller of `openai_chat`'s total deadline wait for a read in flight after the cancel (up to one more per-operation timeout)?

**Answer: no.** There is no watcher thread and no cancel. Every network operation runs in the caller's thread with a timeout of `min(its own, the deadline's remaining time)` (`_bounded`, `src/learnloop/ai/providers/openai_chat.py:122-133`; reads `:156-157`, writes per partial send `:179-189`, connect and TLS `:194-227`), and none starts once the deadline has passed. The last read therefore ends at the deadline. The retry loop gives up once the deadline cannot fit another attempt (`_retry_delay`, `:637-640`), and the JSON repair runs only on a response that arrived (`:422-433`). No product fault.

**What the 2.003 s was.** The test measured wall time from before `client.complete`, which also counts what runs before the deadline is armed in `_create_within_deadline`: building the request, the receipt, and the openai SDK's lazy imports on a worker's first chat request, all slower on a loaded machine. A scratch probe (deleted) that adds 1.0 s of work before the deadline is armed measured 2.001 s with a transport window of exactly 1.0 s and one socket: the landing gate's number, with the bound intact. That the gate's extra second was this is inference; the run under load was not repeated (no CPU stress).

**Fix (tests only).** A `VirtualClock` in `tests/test_chat_total_transport_deadline.py` is the deadline's clock (`monkeypatch` of `OC._deadline_clock`) and the fake network's: with it, an operation advances the clock by its duration instead of sleeping. The four tests that compared wall time with the bound plus `SLACK` (the dribbling body, the dribbled headers, slow connect and upload, partial sends) now assert `elapsed <= enforced_total_seconds(1.0)` on that clock, with only float rounding (`1e-9`) beside it. No slack was raised; the bound is now exact, so it is stricter than before: with `_bounded` mutated to ignore the deadline (scratch, reverted), all four fail by one operation's overshoot (1.009 s, 1.020 s), which the old `+ 0.75 s` would have let through. The narration test keeps its wall-clock check from socket open to close. Their other checks (one socket, bytes served short of the whole, nothing in flight at return, nothing run in the 0.3 s after) are unchanged.

**Changed assertions.** The four `returned - started < bound + SLACK` on wall time became `returned - started <= bound + ROUNDING` on the virtual clock (reason above). With the virtual clock an abandoned request's reads would not take real time, so "nothing ran in the 0.3 s after" catches less there; the served-bytes and sockets checks still would (an abandoned request would read the whole body), and the design has no second thread.

**What a learner sees.** Nothing changes.

## Ledger

TH-3, K9-1, K9-2, D-46, D-50 marked fixed with their commits. New: **TH-4** (the stop's released feedback has no screen; UX journey audit). The K9 strategy's K9.1-K9.3 lines say done.

## Wording questions for the UX audit

- **TH-4:** where the feedback released at a mid-check stop appears once the learner is in a lesson (the practice card and the dialogue open the lesson at once), and with which words. The server returns it in the block end's shape, so the existing released-feedback list (`ProbeBlockResult`, `DiagnosticReviewScreen`) could show it unchanged; whether before the lesson, inside it, or as a link from it is the audit's (K9 strategy §7).
- **K9.2:** whether a check withheld for burden or budget should say anything beyond the orchestrator's "I won't ask again right now", and in which words.

## Not verified

- The desktop with a real stop: the sidecar payload is tested at the core and the RPC (`releasedFeedback`), and nothing renders it.
- A stop on a vault whose diagnose worker then runs the queued diagnoses (the jobs are asserted, not run).
- D-46 with a real provider call in flight at the switch: the halt's interrupt was exercised only through the code path (the test's handler waits on an event).
- D-50's landing-gate overshoot reproduced under load: not attempted (no CPU stress); the cause is inferred from the probe.
- The terminal app's ^t after desktop-committed answers in the same block (read, not run).
