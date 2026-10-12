# Daily-loop spec: review notes

**Branch:** `docs/daily-loop-spec`, from `main` at `16db5ac5`.
**Deliverable:** `docs/specs/spec_daily_loop_v1.md`. Docs only: no code, no migration, no fixture touched.
**Prompt:** `implementation_handoffs.md` §3 "Daily-loop spec", with three overrides:
- the worktree and branch were already created;
- the owner accepted "most defaults" on 2026-10-12, so every open question gets a concrete default, marked "default, owner may override";
- the router, the implementation goal and the daily-loop review, including its Follow-ups, were also read.

## What the spec decides

| Area | Decision |
|---|---|
| **Plan container (P1–P4)** | A daily plan per local date. Remembered minutes. Four lanes (repair, maintain, new, push) mapped to canonical actions. `split_v1`: repair ≤ 30%, maintain ≤ 60%, the rest to new and push, shown and never asked. Finite, with follow-ups displacing rather than appending. Done when done; "keep going" adds +10 minutes. Auto-advance from feedback, with the list one key away |
| **Router interface** | §6.8 defines `PlanState`, `BlockCandidate`, `BlockSource`, `BlockChooser` and `BlockChoice`, plus the rules the container enforces: feasibility before choice, lane budgets as constraints, closed choice with fallback, learner picks win, decisions logged at block boundaries. DL1 ships the deterministic `legacy_lanes_v1` source and `lane_quota_v1` chooser; router R2 plugs into the same interface |
| **Intent (Q7, Q8)** | Commitments carry intent through one control: Master, Learn, Keep, Light touch, Check once, Reference, Pause, Let go. No commitment means today's behaviour. Goals become optional deadlines, linked through the existing `goal_id` on commitment versions. Per-intent recall targets (0.80, 0.85, 0.90, 0.92; uncommitted 0.90) apply **at serving time** through an effective-due ratio, so persisted `due_at` and replay never change. The ratio is exactly 1 at 0.90 |
| **New material (Q11)** | Load-based admission: projected 14-day review load plus new load ≤ 80% of the minutes, at most 10 and at least 1 new item a day. Learner requests are exempt; "more new material" is a labelled override |
| **Time estimates (Q12)** | Shrinkage from the learner's own latencies, to the practice-mode median, to an optional LLM `expected_minutes`, to 3.0; plus measured feedback dwell |
| **Items before reading (Q5)** | One reading block a day for an as-you-read source, with up to 3 optional, formative pre-questions from the existing quick-check producer |
| **Capture (C1–C4)** | An Alt+C box (text, URL, image) writing mobile M1's `capture_inbox`. One Captures strip with no debt count. A leased background processor: classify, file silently, solve and verify with PF's rules. One-tap "Practice this" (item + `help_me_remember` request + one-member family), with Move and undo. Unverified keys may be adopted, labelled, and never certify. The reader's "Remember later" presets move onto the same adoption path |
| **Re-entry (P6)** | Goal-optional. A capped plan of ≤ 15 minutes and ≤ 8 items, using the repair and maintain lanes, triaged by intent, with Light touch left out. No overdue count and no due-date rewrite |
| **Streak (P5)** | Same count (days with a started session); the label is made honest ("begin today's plan…") |
| **Successors** | `daily_plan_v1` (kill switch `plan.enabled`) and `intent_v1` (`intent.enabled`), each needing a shadow rebuild with zero projection deltas. Capture is a content change behind `capture.*` switches |
| **Phases** | DL0 start friction → DL1 finite plan → DL2 intent → DL3 capture → DL4 images, reader presets and pre-questions. External rows for router R2, mobile M2a and M3, and project M2. An agent prompt template is in §17 |

## Code audit summary (base `16db5ac5`)

- **Today is an open list.** `get_today_queue` gets no limit from Today. Minutes only toggle `short_session` and a logged readiness factor that `_priority` never reads. Nothing ends a session, and "next" on feedback returns to the list.
- **The readiness form changes nothing served.** Energy and sleep are logged only. Minutes reset to 30 every visit. The Start preview uses a heuristic limit that Today ignores.
- **The shadow planner has no durations.** `expected_minutes` is always `None` and the fallback is a flat 3 minutes. The only live duration is the client-reported `latency_seconds`; `log_attempt_duration` has no live caller.
- **Re-entry needs an active goal.** Without one there is no panel and no cap. The stale-session gap bug is fixed only on `fix/daily-loop-followups` (F1).
- **The streak counts session starts,** while the badge says "practice today".
- **Capture.** Outside the reader, every in-app path needs a subject or an LO. The reader's "Remember later" output waits in a proposal review queue. Tutor promotion of a new LO goes to review. Image drop-in is not built. Phone capture exists only on `mobile/m1`.
- **Intent.** Commitments already hold the intentions vocabulary but serve only requested items and staged-owned P2 runs. LO status has no learner control. FSRS uses 0.9 for everything.
- **Unmerged dependencies** (integration branch, `mobile/m1`, Phases 5a, 5b and 6) are named by branch in §3.9, without line numbers.

## Gate results

| Check | Result |
|---|---|
| Code citations re-checked in this worktree | 124 distinct `file:line` citations. A script resolved each one, including bare `:NNN` continuations, and printed the cited line. 0 missing files, 0 out-of-range lines; each line was read against its claim. Two short-form paths and one off-by-two line were fixed during the check |
| Internal consistency | Full read-through after drafting. Fixed: the split example (didn't match `split_v1`); Pause's wording; lane placement of "Check once" requests; requests vs lane budgets; `Goal.commitment_id`, dropped in favour of the existing `goal_id`; reused list keys (Esc and `b`) instead of a new `l` |
| `git diff --check` | Clean |
| Tests | Not run: docs only, nothing executable changed |

## Open owner confirmations

All of these have defaults in force (§14); each is "default, owner may override".
1. **Q0.** How often you open LearnLoop and what stops you. The default order is DL0/DL1 → DL2 → DL3; the DL1 two-week plan report checks it.
2. **Q5.** As-you-read plus optional pre-questions.
3. **Q7.** Commitments as the intent object, with goals as deadlines.
4. **Q8.** The target table: 0.80, 0.85, 0.90, 0.92; uncommitted 0.90.
5. **Q11.** Load ceiling 0.80, cap 10, floor 1.
6. **Q12.** The estimator.
7. **D5.** Adopting a capture whose answer isn't verified (labelled, never certifies).
8. **D6.** Auto-confirming source imports up to $0.50.
9. **D8.** The streak keeps counting session starts, with an honest label (alternative: count only days with an answered item).
10. **D10.** The reader's "Remember later" presets skip the proposal review queue.
11. **D12.** The capture processor on by default, with metered spend capped at $1.00 a day.

## Observations outside this spec's scope (not edited here)

- **Router.** `spec_action_router_v1.md` D9 still says "the configured frontier route (bounded transport)". Its §6.2 and the 2026-10-12 owner decision allow Codex without a physical-request bound. D9's wording looks stale.
- **Mobile.** The header of `spec_mobile_tailnet_v1.md` still says it depends on Q0–Q18 "unanswered", and §6.5 waits on Q14. Q14 is decided (minutes only), and the capture processor it defers to is now §4.3 of this spec. Cross-spec notes are recorded in §16.
- **Handoffs.** The "Daily-loop implementation" row in `implementation_handoffs.md` §1 can point at this spec's §12 phases and §17 template.
