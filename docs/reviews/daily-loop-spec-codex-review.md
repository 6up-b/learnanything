# Daily-loop spec: Codex review fixes

**Stage:** `daily-loop-spec`. **Branch:** `docs/daily-loop-spec`, worktree `learnanything-daily-loop-spec`.
**Reviewed commit:** `fd2de33c` (Codex job `20261012-005719-0EVJP5`; 3 High and 9 Medium findings, review read-only).
**Deliverable changed:** `docs/specs/spec_daily_loop_v1.md`, plus one line in `docs/specs/spec_action_router_v1.md` §7.3 (F12). Docs only: no code, migration or fixture touched. No AI calls were made.

**How each finding was reproduced.** This stage is a spec, so there is nothing to run a failing test against. Each finding was checked against the code on this branch, the other specs, or the `mobile/m1` branch (read with `git show`). All 12 reproduced, so none were rejected. Each fix also names the test the implementing phase must add (§13 of the spec).

## Findings

| ID | Severity | Title | Verdict | Commit | Reproduction, and the test the spec now requires |
|---|---|---|---|---|---|
| F1 | High | Unverified practice can still earn certification credit | Fixed | `1219b31c` | **Reproduced.** `policy_for_class("verification")` makes an ordinary attempt certification-eligible (`learnloop/causal_activity_policy.py:72`, via `diagnosis/causal_activity_policy.py:145`). `certification_credit` then pays any direct, unassisted evidence (`learner/capability_mapping.py:246`), and the canonical projection gates credit only on that eligibility (`substrate/canonical_projection.py:852`). Excluding pools didn't stop it. **Fix:** an attempt-time `practice_attempts.reference_status`, read by `resolve_attempt_activity_policy` like `primed`; never retroactive; successor `capture_reference_v1`. The reconciliation with PF §5.3's no-publish rule is explicit. **Test:** `test_capture_unverified.py` (G7): no credit in either projection, FSRS still updated, no retroactive credit after verification, credit after it, rebuild reproduces the ledger |
| F2 | High | Feasibility rules permit both plan and lane overspend | Fixed | `c47f79a5` | **Reproduced** from §6.8 rule 1 as written: `minutes_left + 2` admitted 7 minutes with 5 left, and the lane test only checked for zero minutes. **Fix:** requested items are deducted before the split; redistribution runs at every boundary, in §6.2's flow-on order; a candidate must fit both `minutes_left` and its lane's minutes, with no tolerance; learner picks are deducted from the lanes too. **Tests:** G13 names both counterexamples; `test_daily_plan_build.py` covers request deduction |
| F3 | High | Purge leaves searchable copies of sensitive captures | Fixed | `b5e29f22` | **Reproduced.** `purge_capture` on `mobile/m1` (`src/learnloop/capture/inbox.py:252`) nulls only `capture_inbox` text, URL, note and `source_app`, and `capture_routes.intent_json`. Copies the spec adds survive: `capture_processing` content, `model_call_receipts.input_text`/`output_text` (`migrations/160_model_call_receipts.sql:13`, `:15`), work checkpoints and `embedding_vectors`. Nothing stopped a leased worker from writing content after a purge. **Fix:** new §4.7. Purge clears every processed copy. `judgment_ledger` rows are content-free by construction, because the ledger is append-only (`migrations/166_embedding_substrate_and_judgments.sql:49`). Purge undoes adoption and redacts the item, keeping attempts. The worker rechecks `purged_at` inside its commit transaction. **Test:** new gate G15 and `test_capture_purge.py` (after processing, during processing with a leased fake worker, after adoption, search) |
| F4 | Medium | The worker cannot perform promised verification retries | Fixed | `4a21630b` | **Reproduced** from §4.3: only state `new` with `processed_at` null was selected, so an adopted (`routed`) capture never got its retry. **Fix:** three separate work states (processing, adoption, verification), a selection rule for each, and retries for adopted or adoption-requested captures. Those run once per new verifier version (how Phase 5a reaches older captures), or after an error with 1 h / 1 d / 7 d backoff. Unadopted captures are never retried (L9). The 12-call cap counts the capture's whole life. **Test:** `test_capture_processor.py` selection cases |
| F5 | Medium | Minimum block size makes small workloads unservable | Fixed | `405d151e` | **Reproduced.** `legacy_lanes_v1` packed strictly into 5–15 minute blocks, so a 3.5-minute item made no candidate. P4 §4.1 (`spec_p4_controller_and_scale.md:262`) allows "one activity may be a complete three-minute block". **Fix:** blocks aim for 5–15 minutes with no minimum. Small maintain and repair groups merge. Estimates are never padded. `lane_quota_v1` stops only when nothing feasible remains. **Test:** `test_daily_plan_build.py`: one 3.5-minute item; several small groups; 4 minutes left |
| F6 | Medium | Intent precedence contradicts "Pause" and "Reference" | Fixed | `fa5c0499`, `3ee90153` | **Reproduced** from §5.3: "item-level wins" and "exclude only when no active commitment covers it" disagreed. A subject Pause fans out to LO commitments (§5.1), and adopted items stay requests through the `help_me_remember` branch of `requested_practice_item_ids` (`db/repositories.py:4574`). **Fix:** one resolution. The most recent choice decides disposition. The latest active control choice decides depth, and request commitments never lower it. Broad choices replace earlier narrow ones. The request query honours paused, reference-only and stopped. Control commitments are marked `provenance.via = intent_control`. **Tests:** G4 lists the cases; `test_intent_resolution.py` checks consequence-line parity |
| F7 | Medium | New-first classification misroutes delayed project probes | Fixed | `c5465258`, `3ee90153` | **Reproduced** from §6.1's order (repair, new, maintain, push): a never-attempted due probe matched `new` first. **Fix:** "scheduled checks" (due project probes, assumed-known first reviews, "Check once") are classified first, into maintain. They are never new material and are capped. Over-cap probes stay "later". **Test:** `test_daily_plan_build.py`, the probe case and the fifth probe |
| F8 | Medium | Reading blocks lack a persistence and completion contract | Fixed | `ff73b7b5` | **Reproduced:** `BlockCandidate` had only item ids, and completion was defined through items. **Fix:** a `ReadingTarget` payload, stored as `attention_blocks.reading_json`. Progress comes from the existing `reader.mark_section_progress` (`learnloop_sidecar/handlers/reader.py:1371`) and `reader_section_progress` (`migrations/106_reader_section_progress.sql:6`). Three `block_ended` outcomes, interrupted and next-day continuation, partial blocks, typed `next_plan_item` steps and a `plan_reading_ended` RPC. **Tests:** `test_daily_plan_reading.py` plus vitest |
| F9 | Medium | "Keep going" silently changes tomorrow's remembered budget | Fixed | `26a4379d` | **Reproduced** from §6.6: "the default is the last plan's budget", which includes `keep_going` and re-entry plans. **Fix:** the remembered value is the minutes last chosen with a chip, stored as `daily_plans.remembered_minutes` and carried forward. Generated budgets never change it. **Test:** `test_daily_plan_rpc.py`: 40, then keep going 10, gives 40 the next day; re-entry leaves it |
| F10 | Medium | Effective-due calculation uses an unreliable interval anchor | Fixed | `3c76b3f2`, `01a32584` | **Reproduced** in code. An FSRS-ineligible attempt keeps `due_at` (`attempts/attempts.py:2717`) but sets `last_attempt_at=now_iso` (`:2958`). **Fix:** the anchor is the latest attempt that `classify_attempt_activity` marks `eligible_for_fsrs`, the same decision as `attempts.py:2694` and `:2699`. Null-state and missing-anchor fallbacks are defined. **Test:** `test_intent_recall_targets.py`: primed and diagnostic attempts between reviews; a fixture-copy check that anchor + S × `fsrs_interval_factor` reproduces `due_at` |
| F11 | Medium | The headline labels partially demonstrated LOs as demonstrated | Fixed | `e2c47e00` | **Reproduced:** `demonstrated_mass` is a per-facet fraction (`learnloop_sidecar/handlers/knowledge_map.py:359`), and `> 0` admitted partial LOs. **Fix:** blueprint LOs use `lo_certification` (`learnloop/goals/goal_certification.py:275`). Other LOs need every facet's `facet_demonstration` (`:104`) complete. Partial LOs count as "learning". **Test:** `test_today_headline.py`: partial capability, partial facet, integration gap |
| F12 | Medium | Router and plan kill switches specify incompatible fallbacks | Fixed | `7ce23f08` | **Reproduced:** router §7.3 said "returns Today to the legacy scheduler", while its G8 says "the pre-router version", which after DL1 is the plan with `lane_quota_v1`. **Fix:** a `plan.enabled` × `router.enabled` table in §6.8, and the router's §7.3 line revised to "pre-router version" (one line). **Test:** G1 and `test_daily_plan_kill_switch.py` cover every row |

**Rejected:** none.

**The review's "claims that don't hold"** are all addressed by the fixes above: lane budgets and finiteness (F2), "never certify" (F1), background verification retries (F4), and the effective-due scaling (F10).

**Consistency follow-ups** (`3ee90153`, `fc8a5553`):
- scheduled checks are classified before `repair` too, since they are fixed-date cold checks;
- the request query excludes only paused, reference-only and stopped items, so a "Check once" still reaches its dated branch;
- §10's replay note now covers `reference_status`;
- G8 and G9 match the new capture rules;
- the §16 PF and mobile notes are updated;
- one off-by-one citation is corrected (`reader.py:1370` → `:1371`).

## Gate results

| Check | Result |
|---|---|
| **Code citations re-checked in this worktree** | A script resolved every `file:line` in the spec, including bare `` `:NNN` `` continuations assigned to the preceding path: **139 distinct citations, 0 missing files, 0 out-of-range lines** (85 with explicit paths, 54 continuations). Each line was read against its claim. The 17 citations added or re-purposed by these fixes were checked individually; one was off by one and is fixed. Branch citations (`mobile/m1`) are named by branch, without line numbers, as the spec's convention says |
| **Internal consistency** | Full read-through after the fixes. Searches for each superseded phrase (`+ 2`, "union rule", "last plan's budget", `last_attempt_at +`, `demonstrated_mass > 0`, "legacy scheduler", "blocks of 5–15", "highest target wins", "same standard as a learner-written card", the old classification order) found **0 hits**. Markdown tables: **16 tables in the spec and 8 in the router spec, 0 rows with a wrong column count** |
| **`git diff --check`** | Clean from the branch base (`16db5ac5..HEAD`) and over the review fixes (`fd2de33c..HEAD`) |
| **Tests** | Not run. Docs only: no executable file changed |

## Owner-facing notes

- **New defaults introduced by the fixes** (all "default, owner may override"):
  - the most-recent-choice intent rule (F6);
  - verification retry timing (once per verifier version; 1 h / 1 d / 7 d after errors) and no retries for unadopted captures (F4);
  - purge of an adopted capture redacts the item but keeps attempt history (F3);
  - scheduled checks always classify into maintain (F7).
- **A new successor:** `capture_reference_v1` (DL3) changes what certification projections mean, for attempts on unverified keys only. It deliberately has no kill switch that re-enables certification (C3). `capture.unverified_adoption = false` is the off-ramp.
- **Cross-spec edit:** `spec_action_router_v1.md` §7.3's kill-switch line now says "pre-router version", which matches its own G8.

## Re-review (Codex job `20261012-011909-hLAhyu`)

**Reviewed range:** `fd2de33c..4458d6f4`. The verdict was REOPENED: F1 and F2 were confirmed fixed, F3 reopened, and two new Medium findings (F13, F14) were raised.
**Deliverable changed:** `docs/specs/spec_daily_loop_v1.md` only. Docs only: no code, migration or fixture touched. No AI calls were made.

**How each finding was reproduced.**
- **F3** was reproduced with a failing test on the base code. A scratch pytest, run in this worktree and not committed, used `create_basic_vault`. It built the queue, then redacted the item with `edit_item` as §4.7 said, then scanned every column of every table for the original prompt and answer. Both cases failed (`2 failed in 1.68s`):
  - queue build only: the text stayed in `practice_item_snapshots.item_json`;
  - with a self-graded attempt: it also stayed in `activity_surfaces.surface_json`.
  - `UPDATE practice_item_snapshots` aborted with "immutable".
  - Reading the code found two more copies the scan couldn't reach in that vault: `assessment_contract_versions.contract_json` (written at attempt time under the canonical algorithm versions) and grading receipts.
- **F13 and F14** concern behaviour that isn't built yet, so they were checked against the spec and the code:
  - F13: §5.3 step 1 dropped `satisfied` commitments, and step 4 then served the item as uncommitted. `satisfy_single_check` appends a `disposition_changed` event (`learnloop/curriculum/commitments.py:717`), which would also have moved the choice time.
  - F14: the selection predicate in §4.3 excluded every capture whose call budget was spent, including one whose only remaining work was a call-free adoption.

| ID | Severity | Title | Verdict | Commit | Test, or reason |
|---|---|---|---|---|---|
| F1 | High | Unverified practice can still earn certification credit | Confirmed fixed by the re-review; no change | `1219b31c` | G7, `test_capture_unverified.py` (unchanged) |
| F2 | High | Feasibility rules permit both plan and lane overspend | Confirmed fixed by the re-review; no change | `c47f79a5` | G13, `test_daily_plan_build.py` (unchanged) |
| F3 | High | Purge leaves historical copies of an adopted capture (reopened) | Fixed | `d593c3f3`, `8d049ebd`, `31926127` | **Reproduced** by the scratch test above. **Fix** (§4.7): purge redacts every stored revision of the item: snapshots, surfaces, contracts, and grading receipts (sidecar by submission, TUI by item id). Text fields become "[removed]" and `redacted_at` is set; ids, hashes, targets, weights and points stay. DL3's migration replaces the snapshot update trigger with one that admits only that redaction; deletes stay forbidden. Replay reads structure, not text. Learner field F1 treats a redacted snapshot as a missing revision (`excluded`), and the learner-field note in §16 says so. The purge prompt now says feedback is kept too. **Tests:** G15 and `test_capture_purge.py` now cover purge after a queue build, after a fake-LLM-graded attempt, a sentinel scan of every text column and of the vault files, the trigger, and a rebuild before and after |
| F13 | Medium | Completed "Check once" items return to ordinary practice | Fixed | `6172d145` | **Fix** (§5.2, §5.3): `satisfied` commitments stay in resolution as a terminal disposition, like `stopped`, until a later choice. Satisfying a check doesn't move the choice time. The request query skips `satisfied` items. The dated check is requested only while its pending commitment decides the item. **Tests:** G4 and `test_intent_resolution.py` cover an uncommitted item and one under an older LO Master after the check, re-inclusion by a later choice, a check replaced before its date, and an unchanged choice order after satisfaction |
| F14 | Medium | Exhausting the model-call budget blocks pending adoption | Fixed | `9d859e20` | **Fix** (§4.3, §4.4, §10): the lifetime cap gates only model-calling work (processing, `idea` drafting, verification retries). Completing an adoption from persisted results is selected whatever the budget. Work that still needs a call ends with a label. A requested adoption that can't finish closes with `adopt_stopped_reason` = `call_cap` \| `processing_failed`. **Tests:** G9 and `test_capture_processor.py` cover processing done on the last allowed call with adoption pending (a `problem` completes with zero calls; an `idea` needing drafts closes with `call_cap`), and processing pending at the cap |

**Rejected:** none.

### Re-review gate results

| Check | Result |
|---|---|
| **Code citations re-checked in this worktree** | A script resolved every `` `path:line` `` in the spec, with bare `` `:NNN` `` continuations assigned to the preceding path on the same line: **144 distinct citations, 0 missing files, 0 out-of-range lines** (107 explicit and 51 continuation occurrences). No code, migration, app or test file changed on this branch since its base (`git diff --stat 16db5ac5..HEAD -- src migrations apps tests` is empty), so the citations checked line by line in the first round still hold. The 11 citations added this round were each read against their claim: `repositories.py:8673`, `activities.py:176`, `assessment_contracts.py:98`, `:118`, `:119` and `:154`, `server.py:113`, `tui/state.py:61`, `attempts/ai_contracts.py:572`, and migration 164 `:13` and `:15` |
| **Internal consistency** | A read-through of §4.3–§4.7, §5.2–§5.3, §10, §12 (DL3), §13 (G4, G9, G15 and the test lists) and §16. A search for 8 superseded phrases ("Retired and `satisfied`", "isn't selected again", the old selection predicate, "Your past answers are kept.", "Attempt history stays, including", "stops selection", "then satisfied \|", "drop out. A commitment") found **0 hits**. Markdown tables: **16 in the spec, 0 rows with a wrong column count** |
| **`git diff --check`** | Clean from the branch base (`16db5ac5..HEAD`), over the first-round fixes (`fd2de33c..HEAD`) and over this round (`4458d6f4..HEAD`) |
| **Tests** | One scratch reproduction ran: **2 failed** (expected; it reproduced F3), and it was then deleted. The suite was not run, because no executable file changed |

### Owner-facing notes (re-review)

New defaults introduced by these fixes. Each is a default the owner may override:
- **Purge of an adopted capture** also redacts the item's stored revisions. It keeps attempt history (answers, scores, grading evidence and feedback) and M1's manual-route destinations. Backups and dataset exports made earlier are not reached.
- **A completed "Check once"** stays terminal for what it covers until a later choice.
- **The capture call cap** stops calls, not call-free adoption. Adoptions that can't finish close with a visible reason and are not retried.
