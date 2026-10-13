# Daily loop: capture without debt, a finite plan, one intent control, and humane re-entry (v1)

**Status:** draft for owner review (2026-10-12). It is the spec that `implementation_goal.md` §1 calls `spec_daily_loop_v1.md`.

**Owner decisions in force (2026-10-11 and 2026-10-12):**
- **`daily_loop_frictionless_defaults.md` wins** over everything else here. C1–C4, S1–S5, P1–P7 and R1–R3 are decided; this spec turns them into contracts.
- **The recommended defaults are accepted** ("most defaults", 2026-10-12). Every open question below (Q0, Q5, Q7, Q8, Q11, Q12, and this spec's own D1–D12) has a concrete default that implementation proceeds on. Each is marked **default, owner may override**; the owner can change any of them at the phase checkpoint that uses it (§12).
- **Codex on the owner's ChatGPT subscription** may run every paid LLM role here without a physical-request bound. Its cost is estimated from reported token usage and labelled `estimated_only` (Slice A plan §5 rule 6). Call-count caps still apply.
- **The Decider is `perplexity/pplx-decider-v1.1-27b` on OpenRouter.** It belongs to the action router, which fills this plan's blocks (§6.8); this spec makes no Decider calls.
- **Honest labels, generous defaults.** Live changes go behind kill switches; there are no shadow stages by default.

**Sources:**
- `docs/specs/daily_loop_frictionless_defaults.md` (the decisions);
- `docs/brainstorming/Daily Loop Open Questions.md` (Q0–Q18 and their status table);
- `docs/brainstorming/LearnLoop_User_Intentions_v2.md` (§3, §5, §10, §12–§15) and `User intentions.md`;
- `spec_action_router_v1.md` (the router fills the plan's blocks; R2 needs this plan);
- `spec_learner_field_v1.md` §3.1, §5.2, §5.3; `spec_embedding_consumers_v1.md` §5.3 and §5.9;
- `spec_mobile_tailnet_v1.md` §6.5, §6.7, §9.1 (revision 4: M1 built on `mobile/m1`, phone acceptance A1–A3 pending);
- `spec_project_understanding_v1.md` §5.2 and §9;
- `docs/reviews/daily-loop-bugs.md`, including its Follow-ups section on `fix/daily-loop-followups`;
- `implementation_goal.md` and `implementation_handoffs.md`.

**Relationship to other specs:**

| Spec | Relationship |
|---|---|
| `spec_action_router_v1.md` | This spec defines the plan container: minutes, lanes, block boundaries, "keep going", re-entry, the streak and what the learner sees. The router chooses blocks through the interface in §6.8. Before R2 a deterministic chooser fills it |
| `spec_learner_field_v1.md` §5.2 (Slice A Phase 6) | Phase 6 decides *which* new material starts and how "assumed known" works. This spec decides *how much* new material a day admits (Q11) and maps "assumed known" onto intent (§5.6) |
| `spec_embedding_consumers_v1.md` §5.3, §5.9 | Capture solving reuses PF's verified-reference rules. `find_practice` powers the "Practice on…" box and recalls filing candidates |
| `spec_mobile_tailnet_v1.md` §6.7 | Its M3 "background capture processor" is §4.3 here. The phone shows this plan from M2a |
| `spec_project_understanding_v1.md` | Due delayed probes enter the plan's maintain lane from project M2 (§6.9) |

**Citation convention.** Every `file:line` below was checked on this branch (base `16db5ac5`). Python paths are relative to `src/` (`learnloop/…`, `learnloop_sidecar/…`), frontend paths to `apps/learnloop-tauri/src/` (`screens/…`, `components/…`, `app/…`), and `migrations/…` to the repo root. Work on unmerged branches is named by branch, without line numbers.

---

## 0. Thesis

The audit (§3) found four kinds of friction, none of them about learning itself:
- **No end.** Today is an uncapped ranked list. The minutes the learner enters are displayed and counted down but bound nothing, and finishing an item returns to the list.
- **A form every day.** Energy and sleep sliders are logged and change nothing served. Minutes reset to 30 every time.
- **Capture needs a home.** Outside the reader, every in-app capture path needs a subject or a learning object first. The reader's "Remember later" presets need none, but their output waits in a review queue. Nothing captures from outside the app on this base.
- **Intent has no single carrier.** Commitments already hold the intentions vocabulary (depth presets, dispositions), but only two narrow paths read them when serving (requested items and staged-owned P2 runs). "Push" means "has an active goal", topic status has no learner control, and every item is maintained at 90% recall.

The fix keeps the engine and changes the container:
- **A finite daily plan** of N remembered minutes, split by the system across maintain, repair, push and new, done when done, with "keep going".
- **One intent control** on top of commitments, with per-intent recall targets.
- **A capture box** whose saves are references; filing, solving and verification happen in the background, and one tap adopts a capture into practice.
- **Re-entry** as a small automatic session.
- **The streak, kept,** with an honest label.

Block choice inside the plan is the action router's job (§6.8).

---

## 1. Scope

**In scope:**
- **Capture (C1–C4):** the capture box with a shortcut (text, URL, image); one inbox for every channel; silent background filing, correctable with one tap; background verified solving; one-tap "Practice this"; the reader's "Remember later" presets moved onto the same adoption path.
- **Intent (Q7, Q8):** commitments as the intent carrier, one control, per-intent recall targets, goals as optional deadlines.
- **The daily plan (P1–P4, Q9–Q12):** the plan container, the system-set split, new-material pace, time estimates, auto-advance, remembered minutes, "keep going", items before reading (Q5), the optional Today headline, and the block-chooser interface the router fills.
- **Re-entry (P6, Q13)** and **the streak (P5).**
- **Persistence, successors, kill switches, tests, gates and phases.**

**Not in scope:**
- **Block choice by a model.** That is router R2.
- **Item selection within a block.** It stays with the scheduler's ranking (and later P4 §4.4's selectors and `find_practice`).
- **Placement** (which new material starts, "assumed known"): Slice A Phase 6.
- **Grading changes.** P7 keeps grading synchronous; Slice 1 moves diagnosis off the request path.
- **The phone client.** The mobile spec owns it; it consumes this plan.
- **An OS-global hotkey and the browser extension** (§15).

---

## 2. Standing constraints

- **L1. Honest labels.** Every number the learner sees equals what is served: plan size, minutes, split, refresher count, verification status. Model estimates are labelled as estimates. A control that claims an action that doesn't happen is removed, not faked (the "postpone" precedent, `docs/reviews/daily-loop-bugs.md` §3).
- **L2. Generous defaults.** No step is added to protect a model. A capture asks nothing. The split asks nothing. The intent control is optional, and no commitment means today's behaviour.
- **L3. Agency wins.** The learner's explicit choices (an item from the full list, "Practice this", "more new material") are always honoured. They are recorded as the learner's (a `learner_pick` block, or a learner request), never as a sampled choice (router §7.3).
- **L4. Never evidence from a prediction.** An unverified solution never certifies anything (C3). Duration estimates, recall targets and the headline's expected recall never write evidence, mastery, certification, coldness or FSRS state.
- **L5. Replay.** Rebuild and replay make zero model and zero embedding calls. Capture processing outputs (filings, transcripts, solutions, verdicts) are persisted inputs and never re-run on rebuild.
- **L6. Serving changes are successors.** Each change to what is served is an algorithm successor with a kill switch that restores the previous behaviour exactly, checked by a shadow rebuild on a backup-API copy under `fixtures-local/` (§11).
- **L7. Spend controls.** Every paid step uses the Phase 1 framework (`learnloop/ai/spend.py`): caps before requests, `--dry-run` with a cost estimate, resumable work, receipts with the caps in force. Codex runs without a physical-request bound and is recorded `estimated_only`. Every LLM, verifier or owner verdict appends to `judgment_ledger`.
- **L8. Embeddings recall, models decide, the scheduler admits.** Embeddings may propose filing candidates; they never decide identity, filing or difficulty alone.
- **L9. No capture debt.** No surface shows unprocessed or unadopted captures as a to-do count. A capture that is never adopted costs nothing.
- **L10. Grading stays learner-blind.** Nothing in the plan, intent or capture context reaches the grader beyond the item and the answer.

---

## 3. Code truth (audited 2026-10-12 on base `16db5ac5`)

### 3.1 Today, Start and the queue

- **Today asks for everything.** `TodayScreen` calls `get_today_queue` with the session id, minutes and energy, and no `limit` (`screens/TodayScreen.tsx:166`, `:174`). The handler builds the whole eligible queue (`learnloop_sidecar/handlers/queue.py:80`). Its only cap is the re-entry cap added by `fix/daily-loop-bugs` (`:90`, `:93`).
- **Every eligible item with priority > 0 is returned** (`learnloop/scheduling/scheduler.py:468`), composed by the goal quota (`:506`) and the requested-items floor (`:514`), sliced by `limit` only at the end (`:558`), and grouped as "Due now / Probe queue / Later today" (`learnloop_sidecar/handlers/queue.py:218`).
- **Minutes bound nothing served.** `available_minutes` only sets `short_session` (≤ `short_session_minutes` = 20 suppresses probe EIG; `learnloop/scheduling/scheduler.py:158`, `learnloop/config/schema.py:92`) and a logged `readiness_factor` (`learnloop/scheduling/scheduler.py:1641`) that `_priority` never reads (`:1484`). Today shows the minutes as a "BUDGET" counting down from session start (`screens/TodayScreen.tsx:827`, `:1662`). Nothing ends the session.
- **The Start screen previews a different list.** Its preview passes a `limit` derived from energy, sleep and minutes (`screens/StartScreen.tsx:1571`, `:1684`); Today then ignores that limit.
- **No auto-advance.** "Next" on feedback (`n` or Enter, `screens/FeedbackScreen.tsx:1863`) returns to the list (`app/App.tsx:880`).
- **New material** enters through an opening diagnostic episode per LO (`learnloop/substrate/state_sync.py:152`, `:175`). Never-attempted LOs are otherwise kept out by the cold-start gate unless they are on a goal frontier, in an episode, or requested (`learnloop/scheduling/scheduler.py:280`, `:295`). Slice A Phase 6 turns the opening probes off.
- **Propensities.** Composed offers record `propensity_kind = unavailable_composed_offer` (`learnloop/scheduling/scheduler.py:642`). ε-exploration is skipped when a probe heads the slate (`:1544`).

### 3.2 The shadow planner

- **The P4 staged policy** chooses one 5–15 minute attention block, then one activity (`learnloop/scheduling/staged_policy.py:51`, `:52`, `:53`). It runs in shadow except for staged-owned P2 golden-path runs (`:24`; `learnloop/scheduling/controller_cutover.py:46`).
- **It has no durations.** Every candidate's `expected_minutes` is `None` (`learnloop/scheduling/controller_snapshot.py:259`). The budget constraint uses a flat 3-minute bound (`:43`), and the loss table falls back to 3 minutes (`learnloop/scheduling/action_loss.py:46`).
- **Block storage exists.** `attention_blocks` and `attention_block_events` (`migrations/096_controller_snapshots.sql:102`, `:117`) are WORKFLOW and RECEIPT (`learnloop/db/table_roles.py:74`, `:73`), with writers (`learnloop/scheduling/controller_store.py:133`, `:163`). This plan reuses them (§10).
- **The canonical actions** include `maintain`, `instruct` and `practice(completion_or_repair)` (`learnloop/scheduling/controller_actions.py:21`, `:18`, `:31`), which the plan's lanes map onto (§6.1).
- **Shadow-only pieces.** The knowledge-model §11.2 intent planner logs and never reorders (`learnloop/scheduling/intent_planner.py:1`). The re-entry adapter (`learnloop/scheduling/reentry_adapter.py:50`, a 5-question cap) and the short-session adapter are registered parameters with no live caller.

### 3.3 The welcome-back panel

- **Trigger.** The gap since `most_recent_ended_at` must exceed `hypothesis.reentry_gap_days` = 7 (`learnloop/scheduling/reentry_summary.py:110`; `learnloop/config/schema.py:118`).
- **It needs an active goal.** `reentry_session_cap` returns `None` without one (`learnloop/scheduling/reentry_summary.py:88`). Today queries the summary only for the primary active goal (`screens/TodayScreen.tsx:297`, `:302`), and the handler falls back to the nearest active goal (`learnloop_sidecar/handlers/goals.py:440`, `:112`). A learner who only maintains material never sees re-entry.
- **The count.** `refresher_count = len(slipped)` over the goal's facets (`learnloop/scheduling/reentry_summary.py:172`). Since `fix/daily-loop-bugs` it caps the Today queue (`learnloop_sidecar/handlers/queue.py:90`).
- **A stale open session hid the panel.** `start_session` ends other open sessions at "now" (`learnloop_sidecar/handlers/sessions.py:47`; `learnloop/db/repositories.py:9056`), resetting the gap. `fix/daily-loop-followups` F1 fixes this (last real activity, not the stamp); it is not on this base.
- **There is no "re-entry done, keep going" moment.**

### 3.4 The streak

- `session_day_streak` counts local calendar days with a **session start** (`learnloop/db/repositories.py:8878`, `:8888`). It is returned on load and at session end (`learnloop_sidecar/context.py:283`; `learnloop_sidecar/handlers/sessions.py:102`).
- The badge says "practice today to keep your streak" (`screens/StartScreen.tsx:1594`, `:1607`), but starting a session is what counts. The welcome-back panel never mentions the streak (`screens/TodayScreen.tsx:1509`).

### 3.5 The readiness form

- **Desktop:** energy and sleep sliders plus minute chips (`screens/StartScreen.tsx:1787`, `:1789`, `:1790`). Defaults are 0.7, 0.5 and 30 minutes on every visit (`:1669`, `:1670`, `:1671`); nothing is remembered. Begin sends all three (`:1715`).
- **TUI:** the same sliders (`learnloop/tui/screens/start.py:228`, `:229`). **CLI:** `--energy` (`learnloop/cli/app.py:1758`).
- **Storage:** `sessions` (`migrations/001_initial.sql:348`) via `create_session` (`learnloop/db/repositories.py:8820`). Energy reaches only the logged readiness factor (§3.1).

### 3.6 Capture paths

| Path | What it needs at capture | Where it lands | Reaches practice? |
|---|---|---|---|
| **Write a card** (`components/WriteCardDialog.tsx:80`) | An LO, a prompt **and** the expected answer | `author_item` (`learnloop/content/authoring/item_authoring.py:89`) | Immediately |
| **Quick Add** (`components/QuickAddDialog.tsx:46`, `:234`, `:543`) | A subject, a token budget and consent ticks | An import and synthesis batch | Through the study map |
| **Reader "Remember later"** (`screens/ReaderScreen.tsx:82`; presets at `learnloop/reader/reader_capture.py:74`, `:81`, `:82`) | A selection | A commitment (`test_me_later` → `keep_in_touch`; `help_me_remember` → `remember_key_ideas`) plus a synthesis request whose results are proposals "NEVER auto-admitted" (`learnloop/reader/reader_requests.py:8`) | Only if the learner accepts a proposal: a review queue |
| **Reader "write my own question"** | A passage | Fixed by `fix/daily-loop-bugs`: a learner-authored card when an active LO cites the passage, requested through a `help_me_remember` commitment (`learnloop/db/repositories.py:4574`); otherwise reference only. `fix/daily-loop-followups` F3 adopts those later | Yes, first slot |
| **Reader quick checks** | Nothing | One AI-written question at a section's end, formative only, "never attempts/mastery" (`learnloop/reader/reader_quick_check.py:12`, `:13`) | Only if escalated |
| **Tutor-question promotion** | A tutor exchange | Auto-applies when it attaches to an existing LO; a new LO always routes to review (`learnloop/tutor/promotions.py:649`, `:654`) | Sometimes after review |
| **Image drop-in** | — | Specified (`docs/specs/spec_image_dropin_ingest.md`, status "proposed"); not built | — |
| **Phone capture** | Nothing | Built on `mobile/m1`, not merged: `capture_inbox` (RAW_LEDGER) and `capture_routes` (WORKFLOW, with `processing` state and lease fields), a desktop Inbox strip with manual routes, and `learnloop.capture` (`create_capture`, `route_capture`, `dismiss_capture`, `purge_capture`) | Only by a manual route |

On this base nothing captures from outside the app, and every in-app path except the reader asks for a subject or an LO first.

### 3.7 Intent carriers

- **Topic status.** `LearningObject.status` ∈ {active, dormant, resolved} (`learnloop/vault/models.py:327`) is gated at every serving door since `fix/daily-loop-bugs` (`learnloop/vault/lifecycle.py:37`; `learnloop/scheduling/scheduler.py:259`). No learner control writes it: only proposal deactivations and rejected auto-applies do (`learnloop/content/proposals/patches.py:806`, `:865`), or a YAML edit.
- **Goals** (`learnloop/vault/models.py:61`) carry status, `target_recall` (default 0.8, `:82`) and `due_at`. "Push" is the goal-frontier component (`learnloop/scheduling/scheduler.py:1715`; `learnloop/goals/goal_projection.py:844`), weighted 0.25.
- **Commitments** already hold the intentions vocabulary (`learnloop/curriculum/commitments.py`): commit actions (`:35`), depth presets `keep_in_touch | remember_key_ideas | work_fluently | master_tasks_like_these` (`:39`), target kinds (`:43`), dispositions `active | paused | reference_only | one_check_pending | satisfied | stopped` (`:53`), and per-action default depth policies (`:61`). Serving reads them only for requested items (`learnloop/db/repositories.py:4574`) and staged-owned P2 runs. Depth and disposition change nothing served.
- **Retiring an item** works (`learnloop/content/authoring/item_authoring.py:198`); a too-easy or too-hard retirement also writes an LO claim (`:246`).
- **One recall target for everything.** FSRS intervals use `desired_retention = 0.9` (`learnloop/scheduling/fsrs.py:137`, `:139`; called at `learnloop/attempts/attempts.py:2706`).

### 3.8 Session time and durations

- **Sessions** record start, end and minutes (`migrations/001_initial.sql:348`). `end_session` returns attempt counts and the streak (`learnloop_sidecar/handlers/sessions.py:78`).
- **The only live duration** is the client-reported `latency_seconds` per attempt, from item display to submit (`screens/PracticeScreen.tsx:648`; `learnloop_sidecar/handlers/practice.py:106`, `:525`).
- **`attempt_duration` interaction events** come only from the legacy backfill (`learnloop/substrate/compat/activity_backfill.py:373`). `log_attempt_duration` (`learnloop/substrate/activities.py:949`) has no live caller, so P4's pooled median (`learnloop/scheduling/action_loss.py:181`) sees only backfilled rows.
- **Nothing records time spent reading feedback,** and no per-item estimate reaches the UI.

### 3.9 Unmerged work this spec builds on (2026-10-12)

| Branch | What this spec uses from it |
|---|---|
| `fix/daily-loop-followups` (inside `integrate/slice-a-2-3`) | F1's last-activity gap; F3's adoption sweep; F4's retire-the-card path |
| `integrate/slice-a-2-3` (Phases 2 and 3, migrations 167–168 there) | The map's `untested` state; interaction signals (field §3.1); `ActivityFamily` with `FamilyReference.verification` |
| `mobile/m1` (migration 167 there, to be renumbered) | `learnloop.capture`, `capture_inbox`, `capture_routes`, the Inbox strip |
| Not built yet | Phase 5a (solver panel and verifier), Phase 5b (`find_practice`), Phase 6 (placement, `assumption_decisions`) |

---

## 4. Capture (C1–C4)

### 4.1 The capture box

- **Open it anywhere** with **Alt+C** (D4), from the command palette ("capture"), or from a "+" on Today. It is a small overlay with one field and an optional one-line note.
- **The field takes text, a URL or arXiv id, or an image**, pasted or dropped (PNG, JPEG, HEIC, WebP; same limits as mobile M1's 20 MB).
- **In the reader,** Alt+C with a selection prefills the selection and keeps its source anchor.
- **Enter saves. Nothing else is asked.** The receipt toast says "Saved · filing in the background", with **Practice this** and **Undo**.
- **No Rust change is needed.** The overlay is React and the write is a sidecar method (`capture.create`), so B3 (the broken Rust toolchain) doesn't block it. An OS-global hotkey is deferred (§15).

### 4.2 One inbox for every channel

- **Every channel writes `capture_inbox`** through `learnloop.capture.create_capture` (from `mobile/m1`): the box (`device_id` null, `source_app = "desktop_box"`), image drop-in, the phone Shortcut, and the reader. A capture made in the reader also records its source anchor (the reader annotation and span) in a new nullable `capture_inbox.source_anchor_json`, which is included in the capture's request fingerprint.
- **The Captures strip** replaces mobile M1's Inbox strip on Today. It lists recent captures with their filing, kind, verification status and actions (Practice this, Move, Dismiss, Purge; M1's manual routes stay under "More"). It has a search box over text, note, URL and transcript.
- **No debt (L9).** The strip shows no unprocessed or unadopted count, and nothing nags.
- **States.** `capture_routes.state` keeps M1's meanings. A capture stays `new` (a reference) after processing. `processing` holds only while a processor lease is live. `routed` (route `practice_this`) means adopted. `failed` means processing gave up after retries; the capture is still a searchable reference.

### 4.3 The background processor (C2, C3)

A leased job over captures that have work due. It runs in the desktop sidecar (on load and every 5 minutes while the app is open) and as `learnloop capture process [--dry-run]`. Mobile M3 may also run it in the host under its secondary-attach rules.

**Three separate work states** live in `capture_processing`, so finishing one never hides another:
- **Processing** (`processing_state` = `pending` | `done` | `failed`): steps 1–5 below.
- **Adoption** (`adopt_requested_at`, `adopted_at`): completing a "Practice this" tapped before processing finished (§4.4).
- **Verification** (`verification` = `pending` | `verified` | `unverified`, with `unverified_reason` = `no_checker` | `disagreement` | `uncited` | `error`, `verifier_version`, `verification_attempts`, `next_verification_at`).

**Which captures it picks.** A capture is selected when it is neither purged (§4.7) nor dismissed and one of these holds:
1. **Processing is `pending`.** That is a first run, or a retry after an error with backoff, up to 3 tries; then it is `failed`. The route state is `new`.
2. **Adoption was requested**, it hasn't completed or stopped, and processing is `done`, so adoption can complete. With `capture.unverified_adoption = false`, adoption also waits for `verified`.
3. **A verification retry is due** for a capture that is adopted (route `practice_this`) or has adoption requested, and whose verification is `unverified`:
   - **A new verifier.** For `no_checker`, `disagreement` and `uncited`, it retries once each time the verifier version in force differs from the recorded `verifier_version`. That is how Phase 5a's arrival reaches captures adopted before it.
   - **An error.** For `error`, it retries when `next_verification_at` has passed, with backoff of 1 hour, 1 day and 7 days.

  Unadopted captures are not retried, because verification only matters for practice and a reference costs nothing (L9).

**The call cap limits calls, not work.** Rules 1 and 3 need model calls, so they select a capture only while its lifetime call budget (below) isn't spent. Rule 2 selects it whatever the budget: completing an adoption from persisted results needs no call. So a worker that stopped after committing results made with the last allowed call still completes the adoption on its next run.

**Leases.** Leases (`capture_routes.lease_owner`, `lease_expires_at`) make concurrent runners safe. A `new` capture shows `processing` while it is leased (M1's meaning). An adopted capture keeps `routed` while a verification retry holds its lease.

**Steps, per capture:**
1. **Transcribe** images (route `ai.routing.image_transcription`, the image drop-in spec's §3 contract). A low-confidence read is labelled "couldn't read this clearly"; one tap fixes the transcript later. Before DL4, image captures are stored and listed but wait, unprocessed, for this step.
2. **Classify the kind** (`capture_classify`; `judgment_ledger` task `capture_kind`): `problem` (something to solve), `idea` (a passage or concept to remember), `question` (the learner's own question), `source` (URL or arXiv id), or `note` (reflective; no correctness target).
3. **File it silently** (`capture_file`).
   - Candidates are recalled from the vault's LOs by title and text search, plus `find_practice`'s dossier retrieval once Phase 5b is merged (L8). An LLM picks one LO or "none".
   - Confident → filed under that LO (and its subject). Not confident → **unfiled**, still searchable. There is no "needs a home" step.
   - The verdict appends to `judgment_ledger` (task `capture_filing`).
4. **Work out the answer** (`problem` and `question` kinds), reusing PF's verified-reference rules (`spec_embedding_consumers_v1.md` §5.3):
   - **Solve.** The `capture_solve` route writes a worked solution and final answer.
   - **Verify.** For a numeric or symbolic answer, at least two independent solve-first solves on the PF solver-panel route must agree with it, plus the sympy equivalence check in PF's bubblewrap sandbox. For a proof or explanation, an independent high-effort solve-first derivation by a strong model must match. For a `question` about a captured source span, a quote-verified span containing the answer verifies it.
   - **Result.** `verified` with the check named, or `unverified` (disagreement, no check possible, or an uncited rationale labelled `inferred`). Verdicts append to `judgment_ledger` (task `reference_verification`).
   - **Before Phase 5a merges,** solving still runs but nothing can verify, so every answer is `unverified` (§4.4 says what that allows).
5. **`idea`, `source` and `note`** need no answer. A `source` gets cheap metadata (title, arXiv abstract) through the existing source library, with no paid call.

**Spend (L7).** Routes `capture_classify`, `capture_file`, `capture_solve` and `image_transcription` fall back to the active provider when unset.
- **A lifetime call cap.** `capture.max_calls_per_capture` (12) counts every call made for the capture over its whole life: processing, drafting at adoption, and every verification retry. The count comes from its receipts (`owner_kind = capture`). Once it is reached, no further call is made for the capture:
  - **Work that needs no call still finishes.** That is the adoption of a `problem` or `question` whose answer is worked out, or of an `idea` whose drafts are already checkpointed, with its bookkeeping (item, commitment, family, route), and purge.
  - **Work that needs a call stops, and says so.** An adopted capture shows "verification stopped". Processing still `pending` becomes `failed` (`last_error = call_cap`), and the capture stays a searchable reference (§4.2). An adoption that would still need a call (an `idea`'s drafts, or a verification while `capture.unverified_adoption = false`) closes with `adopt_stopped_reason = call_cap`, and the strip shows "Couldn't make practice from this: call limit reached". It is not retried.
- **A daily cost cap.** Metered routes are capped at `capture.max_daily_cost_usd` = $1.00 a day.
- **Codex** runs without a physical-request bound and is recorded `estimated_only`; the call cap still applies.
- **On by default** (D12); `capture.processor_enabled = false` stops it.

### 4.4 "Practice this" (C1)

One tap, from the receipt, the Captures strip or the phone (mobile M3). It is offered for `problem`, `idea`, `question` and `source`; a `note` stays a reference (intentions §13). Adoption is idempotent per capture and undoable.

| Kind | What one tap does |
|---|---|
| `problem` | Creates one practice item (`worked_problem`): the prompt is the problem as captured (or its transcript), the expected answer is the worked solution. **The first review is "solve it"** |
| `idea` | Drafts one or two retrieval items answer-first, PF `source_anchored` style (`capture_draft` route). Each answer must be quoted from the captured text or its source span; that quote check is what verifies it |
| `question` | One item: the learner's question as the prompt, the background answer as the key |
| `source` | Starts Quick Add with defaults: the subject is inferred and the brief is `as_you_read`. If the estimated cost is ≤ `capture.auto_import_max_usd` = $0.50 (D6), it confirms itself. Otherwise Quick Add's single confirm appears, because a whole-source import is a paid batch, not a capture decision |

**For item-producing kinds, adoption also:**
- **Files the item under the capture's LO.** An unfiled capture is filed under a "Captured" LO in an auto-created "Captured" subject, labelled as auto-created. "Move" re-files it in one tap later.
- **Creates a `help_me_remember` commitment** (`remember_key_ideas`) with a `legacy_practice_item` target. The item is then a learner request through the existing branch of `requested_practice_item_ids` (`learnloop/db/repositories.py:4574`): it is eligible for the requested front slot (§6.1, "Requests first") and exempt from the cold-start gate (§3.1) and from the new-material cap (§6.3).
- **Adds a one-member practice family** whose reference points at the item's key (it holds no copy; §4.7) and whose `reference.verification` is the processor's result, once Phase 3 is merged. PF-b can then generate isomorphs of a captured problem, but only once its reference is `verified` (below). `ActivityFamily.source_kind` gains `captured`.
- **Records the route** with `route_capture(…, route="practice_this", result_refs=…)`.

**Before processing finishes,** the tap records the request (`capture_processing.adopt_requested_at`, creating the row if needed). The receipt says "Will be ready once the answer is worked out", and adoption completes when the processor does. If processing ends `failed` instead, the request closes with `adopt_stopped_reason = processing_failed`, and the strip says "Couldn't make practice from this".

**An unverified answer never certifies anything (C3, L4).** By default (D5) adoption is still allowed:
- The item is labelled "answer key not verified" wherever it shows.
- **Its attempts schedule and teach, but never certify.** They update FSRS and count as learning evidence on the map. They earn no certification credit, by an attempt-time gate:
  - **Recorded at attempt time.** Every attempt records the served item's reference status in a new column, `practice_attempts.reference_status` (`not_applicable` | `verified` | `unverified`). It defaults to `not_applicable` for existing rows and for every item not made from a capture. The attempt transaction sets it from `capture_processing.verification`, and nothing updates it afterwards, so replay reads the same value.
  - **Enforced where certification is decided.** `resolve_attempt_activity_policy` (`learnloop/diagnosis/causal_activity_policy.py:202`) takes `reference_status` as an immutable attempt signal, like `primed` and `hints_used`. `unverified` forces `eligible_for_certification = False` and leaves FSRS eligibility and assistance unchanged. Both certification projections already take eligibility from that resolver: the canonical projection (`learnloop/substrate/canonical_projection.py:677`, gating credit at `:852`) and the facet timeline (`learnloop/learner/facet_evidence_timeline.py:668`, `:740`). An ordinary independent attempt is otherwise eligible (`learnloop/diagnosis/causal_activity_policy.py:145`) and would earn credit (`learnloop/learner/capability_mapping.py:246`). Excluding pools alone therefore isn't enough.
  - **Never retroactive.** A later verification doesn't make earlier attempts certify, because they were graded against an unchecked key. Attempts made after the label clears record `verified` and certify normally. Attempts graded against a key that was later corrected stay ineligible.
  - **A projection successor.** This changes what a projection means, so it is the successor `capture_reference_v1` (§11). With no `unverified` attempts, every projection equals its predecessor's.
- It is also excluded from certification cold probes, exam pools and Phase 6's assumed-known checks.
- Verification is retried in the background for adopted captures (§4.3). If it later succeeds, the label clears. If it finds the stored key wrong, the key is replaced through `edit_item` and the learner sees "answer key corrected".

**How this fits PF's no-publish rule** (`spec_embedding_consumers_v1.md` §5.3). PF never publishes an unverified *generated* candidate, because that would serve the system's own unchecked key to a learner who didn't ask for it. Adoption is narrower:
- the problem is the learner's own capture;
- it is served only because the learner asked ("Practice this", L3);
- it is labelled, and it never certifies.

It is not a PF publish path. The one-member family's reference stays `unverified`, so §5.3's rule still blocks every generated variant until that reference verifies. With `capture.unverified_adoption = false`, PF's rule governs captures too: adoption waits until the answer is `verified`.

**Undo** retires the item through the existing retire path (`item_authoring.retire_item`) and the commitment through `commitments.retire`, the same pairing as `fix/daily-loop-followups` F4.

### 4.5 The reader's "Remember later" presets

Under `capture.reader_presets_adopt` (default true; false restores the proposal path), "help me remember", "connect it" and "test me later" stop producing reviewable proposals (§3.6):
- **"Help me remember" and "connect it"** make the selection a capture with its source anchor and adopt it as an `idea` (§4.4). The cards are drafted answer-first from the cited span, and the quote check verifies them. No review queue (R1). The existing commitment keeps its depth preset.
- **"Test me later"** adopts as a single delayed cold check. The card is drafted the same way, and its `test_me_later` commitment (disposition `one_check_pending`, policy `hold_at_target`) targets it. The check is served through the "Check once" mechanism (§5.2): a dated request that starts `capture.test_me_later_days` = 7 days after the commitment. When answered, the commitment is satisfied (`commitments.satisfy_single_check`, `learnloop/curriculum/commitments.py:717`), and nothing recurs.
- **"Write my own question"** keeps its current path (`fix/daily-loop-bugs`, F3, F4).

### 4.6 Channels and order (C4)

| Order | Channel | Phase |
|---|---|---|
| 1 | The in-app box with Alt+C (text, URL, image paste and drop) | DL3 (images processed in DL4) |
| 2 | Image drop-in (the box, the Ingest screen's drop target, phone photos) | DL4 |
| 3 | Phone capture over the tailnet | Mobile M1 stores; DL3's processor handles its rows; mobile M3 shows results on the phone |
| 4 | Browser extension | Deferred (§15) |

### 4.7 Purge (accidental sensitive shares)

Mobile M1's `purge_capture` nulls the capture's text, URL and note, deletes its media unless it is shared, and leaves a fingerprint tombstone (`capture_inbox.purged_at`; mobile §6.7, §9.1). The daily loop makes processed copies of that content, so purge extends to them. **After a purge, nothing derived from the capture's content can be read or found in the vault**, except two things kept on purpose (below): an adopted capture's attempt history, and the destinations of M1's manual routes. Backups and dataset exports made before the purge are separate files that it does not reach.
- **`capture_inbox.source_anchor_json`** is nulled.
- **`capture_processing`.** Its content columns (`transcript_md`, `solution_md`, `final_answer`, `verification_check`) are nulled, and `purged_at` is set. Ids, kind, states, costs and timestamps stay, so spend accounting still adds up.
- **Receipts.** The capture's `model_call_receipts` rows (`owner_kind = capture`) keep their hashes, tokens and cost, but `input_text` and `output_text` are nulled. Like M1's tombstone, this is an "immutable except purge" exception.
- **Checkpoints.** The processor keys its `model_work_checkpoints` as `capture:<id>:…`, and purge deletes them.
- **Embeddings.** `embedding_vectors` rows with `record_kind = capture` for the capture are deleted.
- **Judgments.** Capture tasks write content-free `judgment_ledger` rows by construction. The `rationale` holds a code and a confidence, never capture text or model prose; any prose stays in `capture_processing`. So nothing in that append-only ledger needs redaction.
- **Search** reads the live columns and skips purged captures, so the Captures strip can no longer find it.
- **An adopted capture.** Purge asks once: "Also removes the practice item made from it. Your past answers and their feedback are kept."
  - It undoes the adoption (§4.4, Undo).
  - It replaces the item's prompt, answer and worked solution with "[removed]" through `edit_item`. The one-member family's reference names the item rather than copying its solution, so it holds no copy.
  - **It redacts every stored revision of the item.** `edit_item` changes only the vault item. The item's text is also copied wherever a revision is recorded, and on this base those copies are:
    - `practice_item_snapshots.item_json`, the whole item, written whenever the scheduler scores it (`learnloop/db/repositories.py:8673`). A queue build alone makes one, before any attempt;
    - `activity_surfaces.surface_json`, the exact wording: prompt, expected answer, parameters and media (`learnloop/substrate/activities.py:176`), written when an attempt resolves the item's activity;
    - `assessment_contract_versions.contract_json`, which holds the prompt, the expected answer and the criterion descriptions (`learnloop/learner/assessment_contracts.py:118`, `:119`, `:98`), written at attempt time;
    - grading receipts. The grading request carries the prompt and expected answer (`learnloop/attempts/ai_contracts.py:572`). The sidecar owns its receipts by submission (`owner_kind = submission`, `learnloop_sidecar/server.py:113`), found through `submission_intents.practice_item_id`. The TUI owns them by session (`owner_kind = tui`, `learnloop/tui/state.py:61`), so those are found by the item id in the grading input.
  - **How a revision is redacted.** In each JSON copy the text fields become "[removed]": prompt, expected answer, worked solution, hints, parameters, media, and criterion and fatal-error descriptions. The row's new `redacted_at` is set. Every id, hash, target, weight and point value stays. The hashes (`content_hash`, `surface_hash`, `contract_hash`, `item_content_hash`) are digests that hold no text, and immutable rows join on them (`decision_features`, grading evidence, the familiarity ledger). Grading receipts keep hashes, tokens and cost and lose `input_text` and `output_text`, like the capture's own receipts.
  - **Immutability.** `practice_item_snapshots` forbids every update and delete (`migrations/164_item_snapshots_and_adjudication_fk.sql:13`, `:15`). DL3's migration replaces its update trigger with one that admits only this redaction: `redacted_at` goes from null to set, and `content_hash`, `practice_item_id` and `created_at` stay unchanged. Deletes stay forbidden. The other two tables are append-only RAW_LEDGER without triggers, so redaction is their one documented exception, like M1's tombstone. Later idempotent writes find the redacted row by its key (`INSERT OR IGNORE` on `content_hash`, and the hash lookups of the other two writers), so they never write the text back.
  - **Replay.** Rebuild reads only ids, hashes and structure from these rows, never their text, and never re-derives a hash from a redacted row. A rubric rehydrated from a redacted contract (`learnloop/learner/assessment_contracts.py:154`) keeps its criterion ids, points and targets, with "[removed]" descriptions. A rebuild after a purge therefore reproduces the canonical projection, facet timeline, mastery and FSRS state from before it (G15). One derived value changes, by design. Learner field F1 (`spec_learner_field_v1.md` §3) proves an `exact` revision by re-hashing the snapshot, which a redacted row cannot pass. So attempts on the purged item resolve as a missing revision (`excluded` by default), the status that spec already gives content that is gone. The dataset export marks redacted rows and skips their hash check.
  - **Kept: attempt history.** The item's attempts stay, with the learner's typed answers, scores, grading evidence and feedback. Feedback can quote the key, which is why the purge prompt names it.
  - Destinations of M1's manual routes are kept, as built (mobile §9.1).
- **Purge during processing.** Purge and the processor's result commit share M1's short capture writer reservation (mobile §9.1), and purge clears any lease. The processor rechecks `capture_inbox.purged_at` inside the transaction that writes its results. If it is set, the processor writes no content, redacts the receipt of any call that finished after the purge, and stops work on the capture.

---

## 5. Intent (Q7, Q8)

### 5.1 The intent object: commitments (Q7; default, owner may override)

**Commitments carry intent; goals are optional deadlines on top.** The vocabulary already exists (§3.7), and it is the intentions doc's own (§3, §5).
- **No commitment means today's behaviour:** every lane is eligible at the 0.90 recall target. Nobody has to set intent for anything to work (L2).
- **What the control writes.** It creates or versions commitments through `learnloop.curriculum.commitments`: `create_commitment` (`learnloop/curriculum/commitments.py:300`), `append_commitment_version` (`:414`), `change_depth_policy`, `change_disposition`, `pause`, `retire`. It uses the existing commit-class actions: `help_me_remember` with the chosen depth preset for Master, Learn, Keep and Light touch, and `test_me_later` for "check once". It adds no new action and no table.
  - **Its own commitments.** The control creates its commitments with `provenance = {"via": "intent_control"}` (`create_commitment` already takes `provenance`). Later choices on the same LO, item, subject or source version or re-dispose that commitment.
  - **Other commitments are left alone.** It never versions commitments that other paths created: capture adoption (§4.4), the reader presets (§4.5), written questions. Those are *request commitments*: they make items learner requests.
- **Targets.** A commitment targets LOs (`learning_object`), single items (`legacy_practice_item`) or a source (`source_locator`). A control on a subject or a source fans out to one commitment whose targets are its active LOs.

### 5.2 The single control

One segmented control on an LO, a subject, a source, a capture and an item. It shows the plain-language consequence and the projected cost (intentions §5, §10). The consequence is computed by the same resolution the queue uses (§5.3). It names what the choice replaces, for example "Pause 12 topics · replaces your earlier setting on 2 topics and 1 item":

| Choice | Commitment | What it does | Recall target (§5.3) |
|---|---|---|---|
| **Master** | `master_tasks_like_these`, active | Push and new lanes; transfer and harder variants keep coming | 0.92 |
| **Learn** | `work_fluently`, active | Push and new lanes until fluent | 0.90 |
| **Keep** | `remember_key_ideas`, active | Maintenance only; no new or harder material | 0.85 |
| **Light touch** | `keep_in_touch`, active | Occasional maintenance; lapses are fine; left out of re-entry | 0.80 |
| **Check once** | `test_me_later` action, disposition `one_check_pending` | One delayed cold check. Once it is answered the commitment is `satisfied`, and nothing it covers is served until a later choice | — |
| **Reference** | disposition `reference_only` | Kept and searchable; never served | — |
| **Pause** | disposition `paused` | Not served until resumed; history kept. Forgetting continues, so resuming starts with what has come due | — |
| **Let go** | disposition `stopped` | Not served; history kept | — |
| *(none)* | no commitment | Today's behaviour | 0.90 |

- **The projected cost** is shown as "about N min/day of reviews", computed from §6.4's estimates and §5.3's targets.
- **How "Check once" is served.** The covered items are held back until `capture.test_me_later_days` (7) after the commitment. Then one item becomes a dated learner request: the commitment's item target if it has one, otherwise the scheduler's top-ranked item of the LO. It is served once, as a scheduled check in the maintain lane (§6.1), and its attempt satisfies the commitment.
  - The request uses one new branch in `requested_practice_item_ids` (`learnloop/db/repositories.py:4574`), dated `created_at + test_me_later_days`. That is the same queue-time derivation `fix/daily-loop-bugs` used for written questions, so nothing new is persisted. The existing branch counts only `help_me_remember` commitments.
  - `followup_tasks` is not used, because its `kind` CHECK admits only `cold_retry` and `certification_cold_probe` (`migrations/139_certification_cold_probes.sql:52`).
- **Lane eligibility never blocks a learner request (L3).** An item the learner adopted or asked for is served under Keep or Light touch too; "no new material" means the system adds none on its own. **Disposition does block it:** a Pause, Reference or Let go chosen after the request excludes the item, request or not (§5.3).
- **Intent is never asked at capture** (Q6, C2). A capture is a reference until "Practice this" (§4.4).

### 5.3 Per-intent recall targets (Q8; default, owner may override)

**Targets:** keep_in_touch 0.80, remember_key_ideas 0.85, work_fluently 0.90, master_tasks_like_these 0.92; uncommitted 0.90 (`[intent] recall_targets`).

**They apply at serving time, never to persisted state.**
- `due_at` keeps being written at 0.90 (`learnloop/attempts/attempts.py:2706`), so replay and stored FSRS state are unchanged.
- The queue reads an **effective due**:

  `effective_due = anchor + (due_at − anchor) × ratio(target)`

  where `ratio(target) = (target^(1/−w20) − 1) / (0.9^(1/−w20) − 1)`, with `w20` the decay weight in use. The interval is proportional to stability (`learnloop/scheduling/fsrs.py:137`), so the ratio needs no stability and keeps the surprise factor already folded into `due_at`.
- **The anchor is the review that produced `due_at`.** It is the `created_at` of the item's latest attempt that fed FSRS, meaning one that `classify_attempt_activity` marks `eligible_for_fsrs` from the row's attempt type, `primed` and `hints_used`. That is the same decision the attempt path makes before it writes `due_at` (`learnloop/attempts/attempts.py:2694`, `:2699`).
  - **It is not `last_attempt_at`.** An attempt that doesn't feed FSRS keeps the stored `due_at` and stability but still advances `last_attempt_at` (`learnloop/attempts/attempts.py:2717`, `:2958`). A primed retry or a diagnostic administration between two reviews therefore moves neither the anchor nor the effective due.
  - **Null state.** With no item state or a null `due_at`, there is no effective due, as today: the item is not due-classified. With no qualifying attempt (state imported or backfilled without one) or an anchor not before `due_at`, the effective due is `due_at` unscaled, and `learnloop plan report` counts such items.
- **At 0.90 the ratio is exactly 1,** so uncommitted items are served exactly as today, whatever the anchor.
- `_forgetting_risk` and the maintain lane use `effective_due` in place of `due_at`.

**Resolving an item's intent: the most recent choice wins.** Several commitments can cover one item. One rule decides both whether the item is served and at which depth and target. With `intent.enabled`:

1. **Covering commitments.** These are the commitments whose current targets include the item (`legacy_practice_item`) or its LO (`learning_object`), including the LO-level commitments a subject or source control fans out to. Retired commitments drop out. `satisfied` ones stay: a completed check is how "Check once" ends, not a withdrawal. A commitment whose only targets are `source_locator`s covers no item, as today.
2. **Disposition.** Each covering commitment's *choice time* is its latest version or disposition change (`commitment_events`), with one exception. Satisfying a check is not a choice, so the `disposition_changed` event that `satisfy_single_check` appends (`learnloop/curriculum/commitments.py:717`) doesn't move the choice time. The most recent choice decides. Ties go to the item-level commitment, then to the higher recall target.
   - `paused`, `reference_only` or `stopped`: the item is not served, and it is not a learner request either.
   - `satisfied`: the same. This is the "then nothing" of "Check once": the check was the whole intent, and it is done. It lasts until a later choice covers the item.
   - `one_check_pending`: the item is held back until its check date, then served once as a dated request (§5.2).
   - `active`: the item is served.
3. **Depth and recall target**, when served. They come from the most recent `active` intent-control commitment covering the item. If there is none, they come from the commitment that decided step 2. A request commitment therefore never lowers a depth the learner chose with the control.
4. **No covering commitment:** uncommitted. Today's behaviour, target 0.90.

**What this means for broad and narrow choices:**
- **A broad choice is the newest choice.** A choice on a subject, source or LO is the most recent choice for everything it covers, so it replaces earlier narrower settings. A subject Pause therefore pauses an LO set to Master and items adopted earlier.
- **A narrow choice made afterwards overrides it** for its own scope. Pause on one item under an LO set to Master excludes that item, and the rest of the LO stays at Master.
- **Replaced settings don't come back.** Resuming, or choosing again, is a new choice.
- **Requests follow the same rule.** The existing `help_me_remember` branch of `requested_practice_item_ids` (`learnloop/db/repositories.py:4574`) skips intent-control commitments, because choosing Master or Keep on an item is not a request. Every branch skips items whose resolved disposition is `paused`, `reference_only`, `stopped` or `satisfied`. A "Check once" (the control's, or a reader "test me later", §4.5) becomes a request only through the dated branch (§5.2), and only while its pending commitment decides the item's disposition. If a newer choice has replaced it, the check is never served. With `intent.enabled = false` the query is unchanged.

Reaching a target permits closure (intentions §5).

**Integrative questions** (one complex question refreshing several concepts) stay deferred (§15).

### 5.4 Goals as optional deadlines

- **A deadline is a goal.** "Add a deadline" on a commitment creates or updates a `Goal` with `creation_source: "learner"`, `due_at`, and the commitment's LOs as its facet scope. It then appends a commitment version whose `goal_id` names that goal. The link already exists: commitment versions carry `goal_id` (`migrations/072_commitments.sql:72`; `learnloop/curriculum/commitments.py:309`), so no vault model or schema change is needed.
- **The goal machinery is reused unchanged:** frontier, forecasts, exams, the goal report.
- **Push.** The push lane takes items on active-goal frontiers (as today) and items under Learn and Master commitments.

### 5.5 Mapping the existing carriers

| Carrier | After this spec |
|---|---|
| Commitments | The intent object (§5.1) |
| Goals | Optional deadlines (§5.4); goal frontiers still feed push |
| LO status (dormant, resolved) | Unchanged: a content-lifecycle gate written by proposals and YAML. The learner's control is §5.2, not LO status |
| Retiring an item | Unchanged |
| Reader commitments | Shown in the control like any other commitment |

### 5.6 "Assumed known" and intent

Slice A Phase 6 marks LOs "assumed known (not tested)" with a first review at 14 days.
- Under this spec, an assumed LO with no commitment is served as **Keep** for that check: maintain lane, target 0.85.
- A failed check returns it to learning (Phase 6). Learning-intent material is new-lane eligible again.
- An explicit commitment always wins.

---

## 6. The daily plan (P1–P4)

### 6.1 The plan container

A **daily plan** belongs to one local calendar date (D9) and one vault, and is shared across devices.

**Its parts:**
- **minutes:** the remembered budget (§6.6);
- **kind:** `normal`, `reentry` (§7) or `keep_going` (an extension, linked to its parent);
- **a split:** minutes per lane (§6.2), with a one-line reason for each;
- **blocks:** coherent groups of items that aim for 5–15 minutes (the staged policy's bounds, §3.2). A block may be shorter: a single item, or the last work that fits the minutes left, is a complete block. Estimates are never padded to reach 5 minutes (P4 §4.1: "one activity may be a complete three-minute block"). Each block has a lane, a canonical action, its LOs, its planned items with estimates, and who chose it (§6.8).

**The lanes:**

| Lane | Canonical action | Items |
|---|---|---|
| `repair` | `practice(completion_or_repair)` | Follow-up tasks (cold retries, intervention follow-ups) and previously attempted items on LOs with an **open diagnosed problem**: an unresolved causal hypothesis or an open unresolved-cause factor (Slice 1 M2, Slice 2 T1). *Owner decision 2026-10-12, at DL1's merge: a recent error alone is not repair; DL1's recency bound (`recent_error` ≥ e^-2) is only the fallback while the diagnosis split is off (a vault below `mvp-0.10`, or `diagnosis.split_enabled = false`). Never-attempted items stay new material.* |
| `maintain` | `maintain` | **Scheduled checks**, attempted or not: a due "Check once" (§5.2), assumed-known first reviews (§5.6) and due project probes (§6.9). Items whose effective due (§5.3) has passed. Previously attempted learner requests |
| `new` | `instruct` | Never-attempted items on learning-eligible LOs, in Phase 6's order (opening probes, before Phase 6); never-attempted learner requests; reading blocks (§6.10) |
| `push` | `practice(transfer \| integration \| fluency)` | Items on goal frontiers or under Learn and Master commitments that are not yet due |

- **Classifying items.** Each eligible item from the scheduler's ranked list takes the first lane that matches, in this order:
  1. **scheduled checks → maintain.** These are fixed-date cold checks, so they come before `repair` and `new`, and many have never been attempted: a project probe always, an assumed-known item or a "Check once" card often. They are never new material: they don't count toward §6.3's admission or item cap, and re-entry admits them (§7). Due project probes beyond `plan.project_probes_max_per_day` stay in the full list as "later", never in `new`;
  2. repair;
  3. new;
  4. maintain (effective due passed, previously attempted requests);
  5. push.

  An item that matches none stays in the full list as "later".
- **Not planned.** `practice(depth_progression)` and `assess_terminal` are never planned blocks. They stay with the staged rule, as in router §7.1.

**Rules:**
- **Finite (P1).** The plan's estimated minutes never exceed its budget. Nothing new is added mid-plan, except that follow-ups produced by this session's errors may **displace** later planned items. Displaced items go back to the pool; they are not debt.
- **Done when done.** The plan completes when its planned items and reading blocks are done or skipped, however long that took. Finishing early or late is fine, and actual time is shown honestly.
- **Requests first (L3).** Up to `tutor_promotion.requested_items_per_session` learner requests (default 1, `learnloop/config/schema.py:599`) go in the first block, as the queue's requested floor does today. Their estimates are deducted from the budget **before** the split (§6.2), so they sit outside the lane budgets but inside the plan's minutes. Further requests wait in their lane, exempt from the new-item cap.
- **Learner picks (L3).** Opening any item from the full list is a one-item learner-pick block. Its estimate is deducted from the minutes left, and from the lanes' remaining minutes in the order push, new, repair, maintain. Planned items that no longer fit are displaced, so the plan stays finite.
- **Captures don't grow today's plan.** An item adopted mid-day joins tomorrow's plan, or "keep going" today (acceptance criterion 6).
- **Mid-plan minute changes** re-plan the remaining blocks.

### 6.2 The split (P3)

The system sets the split, shows it, and asks nothing. Rule `split_v1`, with M the budget in minutes minus the estimates of the requested items already placed in the first block (§6.1):
1. **Repair** = min(repair load, `plan.repair_max_share` × M); the share defaults to 0.30.
2. **Maintain** = min(due maintenance load, `plan.maintain_max_share` × M); the share defaults to 0.60. Overdue maintenance never takes the whole budget (Q10; the MaiMemo finding).
3. **The rest** (at least 10% of M, since 0.30 + 0.60 < 1) goes to new and push:
   - new = min(the admitted new-material minutes from §6.3, half the rest if push candidates exist, else all of it);
   - push takes the remainder up to its load.
4. **Unused minutes flow on:** to maintenance overflow, then repair overflow, then push. New never receives flowed minutes beyond §6.3's admitted new-material minutes. The container repeats this step at every block boundary (§6.8, rule 1).

**Shown as one line:** "25 min · maintain 13 · repair 4 · new 4 · push 4", with a "why" listing each lane's load and cap.

**Re-entry plans** use only repair and maintain (§7).

### 6.3 New-material pace (Q11; default, owner may override)

**Mechanism: load-based admission with a hard cap and a floor.**
- **Review load.** L = the projected mean daily review minutes over the next H = 14 days (`plan.load_horizon_days`). It is the sum of §6.4's estimate over items in non-excluded intents, counting `ceil(H / interval)` reviews for each item whose effective due falls in the horizon.
- **The cost of a new item** is est_minutes × (1 + `plan.new_item_reviews_14d`) / H a day, with 4 reviews assumed for its first 14 days.
- **Admission.** New items are admitted by intent (Learn and Master first, then uncommitted; Keep and Light touch add none), in Phase 6's order within each, while L plus the admitted cost stays ≤ `plan.load_ceiling` × M (0.80).
  - **Cap:** at most `plan.max_new_items_per_day` = 10 a day, across the day's plans and extensions. The count is of new items actually planned.
  - **Floor:** at least `plan.min_new_items_per_day` = 1 when learning-eligible new material exists and the plan isn't re-entry.
  - **Reading blocks** (§6.10) use new-lane minutes but don't count toward the item cap.
- **Exempt (L3):** learner requests (Practice this, written questions, tutor promotions, rung variants). Never-attempted ones take the first new-lane slots. Scheduled checks (a due "Check once", assumed-known first reviews, project probes) are not new material at all (§6.1).
- **"More new material"** on the done screen bypasses the ceiling and the cap once. It shows the trade-off first: "adds about N min/day of reviews for two weeks" (intentions §10).
- **PF's `pf.max_published_per_day`** (10) stays as a generation-volume guard. Serving pace is this admission, not that cap.
- **Before Phase 6,** the new lane carries the opening-probe items (§3.1) under the same admission.

### 6.4 Time estimates (Q12; default, owner may override)

**The learner's own durations, with an LLM estimate as the starting guess.**

```
est_minutes(item) = answer_minutes(item) + feedback_minutes

answer_minutes = (Σ own latencies + k · g) / (n_item + k)
g              = (n_mode · median_mode + k · prior) / (n_mode + k)
prior          = item.expected_minutes if present, else 3.0
k              = 3 pseudo-observations
```

- **Own latencies** are `practice_attempts.latency_seconds` (§3.8), winsorized at `plan.latency_cap_minutes` = 15.
- `median_mode` is the learner's median for the item's `practice_mode`.
- **`expected_minutes` is a new optional `PracticeItem` field.** Authoring prompts (generation, capture drafting) write it from now on. It is omitted when null and is not in the scheduling hash. There is no backfill by default: mode medians cover existing items. The prior of 3.0 is the existing conservative constant (`learnloop/scheduling/controller_snapshot.py:43`).
- **`feedback_minutes`** is the learner's median feedback dwell (from a plan item's `item_done` event to the next `item_served`, capped at 5 minutes). It defaults to 0.5 until 10 observations exist.
- **Reading blocks** are estimated as the section's words left ÷ `plan.read_words_per_minute` (120), where words left = section words × (1 − spans seen ÷ span count) from `reader_section_progress` (§6.10).
- **Estimates are labelled** "about" in the UI. Each planned item's estimate is stored on its plan event, so the report can compare estimated and actual time (§12, DL1 gate).

### 6.5 Auto-advance and "keep going" (P1, P2)

- **Auto-advance.** "Next" on feedback (`n` or Enter) opens the next planned item directly. Feedback stays until the learner moves on; there is no timer. The list is one key away: Esc or `b`, which already go back to it (`screens/FeedbackScreen.tsx:1864`). The next item and the next block are computed while feedback shows.
- **Block boundaries** show one line ("Block 2 of about 3 · maintain · about 8 min · why") and continue on Enter.
- **The done screen:** "Today complete · 26 min · 9 items", with the streak marked and two buttons:
  - **Keep going:** a `keep_going` plan of `plan.keep_going_minutes` = 10 (D3), split by `split_v1` over what remains (usually maintenance overflow and push), with the day's new-item cap still in force;
  - **Done.**
- **"More new material"** sits beside them (§6.3).
- **An empty plan** (nothing due, nothing to admit) says so: "Nothing due today", with "Keep going" offering push or new material if any exists.

### 6.6 Minutes, and no readiness form (P4)

- **The sliders are removed** on desktop and in the TUI. `start_session` keeps accepting `energy` and `sleep_quality` for old clients and the CLI, but nothing sends them. The scheduler's `energy` input stays and logs `None`.
- **Minutes are remembered.** The remembered value is the learner's ordinary daily budget: the minutes last chosen with a chip.
  - **Generated budgets never change it.** These are a `keep_going` extension (10), a re-entry plan's cap (§7), and the normal plan offered after re-entry for the day's remaining minutes. So a learner who usually plans 40 minutes and finishes a 10-minute "keep going" gets 40 again tomorrow, not 10.
  - **Storage.** Every plan stores `remembered_minutes`, carried forward from the previous plan unless a chip set it. Today's default is the latest plan's `remembered_minutes`.
  - **Fallbacks.** Before the first plan, the default is the last session's `available_minutes`. On a fresh vault it is 25 (D1).
- **One tap changes them:** chips for 10, 15, 25, 40 and 60 on Start and Today. A tap sets the remembered value and re-plans the remaining blocks. On a re-entry plan, the tap still sets the remembered value, but the re-entry plan keeps its cap (§7), and the normal plan offered after it uses the tapped value.

### 6.7 What the learner sees

**Start:**

```
Today  ·  25 min ▾  ·  maintain 13 · repair 4 · new 4 · push 4        (why)
First: Conditional independence · 4 items · about 8 min
[ Begin ↵ ]                                        ● 6 days streak
```

**Today, during the plan:**
- the split line;
- the current block with its planned items (the current one highlighted);
- the next blocks summarized ("next: new · about 6 min");
- the Captures strip;
- the "Practice on…" box (§6.9);
- the full list one key away.

**The optional headline** (`plan.headline`, default on; D7) is one line:

> 14 demonstrated · 3 assumed · 9 learning · 6 untested — expected recall today 87%

It counts active LOs in non-excluded intents, each in exactly one class, in this order:
- **assumed:** an open Phase 6 assumption whose first review hasn't resolved;
- **demonstrated:** the whole LO is certified, never just part of it.
  - An LO with authored blueprints uses the existing predicate: `lo_certification(...).demonstrated` (`learnloop/goals/goal_certification.py:275`), which also checks component and integration gaps.
  - Any other LO needs every required capability of every one of its facets demonstrated: each facet's `facet_demonstration` (`:104`) covers all its required capabilities. That is a `demonstrated_mass` of 1 for every facet in the map's computation (`learnloop_sidecar/handlers/knowledge_map.py:359`), not just above 0.
- **learning:** direct evidence but not demonstrated as a whole, including LOs that are partly demonstrated;
- **untested:** no direct evidence.

**Expected recall today** is the mean FSRS retrievability now over items with memory state in non-excluded intents. Its tooltip says "a model estimate, not a test" (L1). Before Phase 6, "assumed" is omitted rather than shown as 0.

**What it never shows:** an overdue count, a backlog number or capture debt.

### 6.8 The block-chooser interface (what the router fills)

The plan container owns minutes, lanes, finiteness, re-entry and the streak. A **source** proposes block candidates and a **chooser** picks one at each block boundary. In DL1 both are deterministic. Router R2 replaces them with the staged frame (source) and the logged mixture of staged, Decider and LLM (chooser).

```python
Lane = Literal["repair", "maintain", "new", "push"]

@dataclass(frozen=True)
class PlanState:                      # everything a chooser may read
    plan_id: str
    kind: Literal["normal", "reentry", "keep_going"]
    minutes_budget: float
    minutes_left: float               # budget − estimates of all chosen blocks (finished and current)
    lane_minutes_left: Mapping[Lane, float]  # each lane's allotment − its chosen blocks, after redistribution (rule 1)
    days_since_last_activity: int     # re-entry is kind == "reentry"
    streak_days: int
    current_block_id: str | None
    intents: Mapping[str, IntentView] # per candidate LO (§5): choice, disposition, target, deadline

@dataclass(frozen=True)
class ReadingTarget:                  # a reading block's section (§6.10)
    source_id: str
    extraction_id: str
    section_id: str
    section_title: str
    words_left: int                   # section words × (1 − spans_seen / span_count)
    partial: bool                     # the block covers only part of what is left

@dataclass(frozen=True)
class BlockCandidate:
    candidate_id: str
    lane: Lane
    action: str                       # canonical action (controller_actions)
    subtype: str | None
    learning_object_ids: tuple[str, ...]
    item_ids: tuple[str, ...]         # planned items, in within-block order; empty for reading
    reading: ReadingTarget | None     # set only for a reading block (lane "new")
    est_minutes: float
    planner_value: float              # the source's own score, logged and shown
    reason: str                       # plain-language reason from the source

CONTINUE_CURRENT = "continue_current" # offered while a block is in progress
STOP_FOR_TODAY = "stop_for_today"     # offered when minutes_left < 5 or nothing feasible (rule 4)

class BlockSource(Protocol):
    name: str
    def candidates(self, state: PlanState) -> list[BlockCandidate]: ...

@dataclass(frozen=True)
class BlockChoice:
    candidate_id: str                 # a candidate id, CONTINUE_CURRENT or STOP_FOR_TODAY
    chosen_by: Literal["lane_quota", "staged", "mixture", "learner_pick"]
    propensity: float | None          # exact for sampled choices; 1.0 deterministic; None learner pick
    why: str
    why_kind: Literal["computed", "model_written", "model_no_rationale"]
    decision_ref: str | None          # router_decisions.id from R2

class BlockChooser(Protocol):
    name: str
    def choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice: ...
```

**What the container enforces** (the chooser cannot override it):
1. **Redistribution, then feasibility, before every choice.**
   - **Redistribution.** A lane releases its remaining minutes when it has no candidates left, or when even its smallest remaining candidate is larger than its remaining minutes. Released minutes flow in §6.2 step 4's order (maintain, repair, push) to the first lane that still has a candidate. The new lane never receives more than its admitted new-material minutes. The block event records each release.
   - **Feasibility.** A candidate is feasible only when its estimate is ≤ `minutes_left` **and** ≤ `lane_minutes_left[lane]` after redistribution. There is no tolerance.
   - The chooser sees only feasible candidates. Whatever the chooser prefers, no block can overspend its lane or the plan, so P3's split stays the plan's.
2. **Closed choice.** A choice naming an unknown or infeasible id falls back to `lane_quota_v1`, flagged `fallback` on the block event (router G1, G7).
3. **Learner picks win** and are logged as `learner_pick` with no propensity (router G9).
4. **`STOP_FOR_TODAY`** is offered only when fewer than 5 minutes are left or nothing feasible remains. Being offered doesn't make it chosen: while a feasible candidate exists, `lane_quota_v1` chooses it, so a 3-minute item still fits into the last 4 minutes. Stopping ends the plan with its reason ("today's minutes are used" or "nothing more worth doing today") and offers "keep going".
5. **Decisions happen at block boundaries only:** the first block when the plan is built, the next one while the last item's feedback shows (router §8).
6. **Every decision is logged** as an `attention_block_events` row of kind `block_chosen`: the candidate set (ids, lanes, estimates, planner values), the chooser, the propensity and the fallback flag. R1 extends this logging; R2 adds `router_decisions`.

**DL1's implementations:**
- **`legacy_lanes_v1` (the source).** It classifies the scheduler's ranked eligible list into lanes (§6.1) and groups each lane's items by LO, in the scheduler's order. It then packs the groups into blocks of up to 15 estimated minutes:
  - **Never larger** than its lane's remaining minutes or the plan's.
  - **Small groups.** In `maintain` and `repair`, an LO group under 5 minutes merges, in rank order, with the lane's next groups up to the bound, because interleaved review is coherent there. In `new` and `push`, a block stays on one LO and may be short.
  - **No minimum.** A block under 5 minutes is still offered when that is all the lane has, or all that fits: one due item, the lane's last items, or the plan's last minutes.
- **`lane_quota_v1` (the chooser).** It picks the feasible candidate from the lane with the largest unspent share of its split; ties go in the order repair, maintain, new, push, then to the higher planner value. Its "why" is `computed`: "maintain: 3 reviews past their 85% target".

**What R2 maps onto this:** `LearnerStateCardV1`'s session fields come from `PlanState`, and its intent field from §5. `choose_block`'s candidates are the feasible set. `continue_current` and `stop_for_today` are the constants above.

**How `plan.enabled` and `router.enabled` combine.** The router only fills the plan, so its kill switch returns Today to the *pre-router* version, which is the plan with the deterministic pair when `plan.enabled` is on. The router spec's §7.3 kill-switch line is revised to say so; its G8 already says "the pre-router version".

| `plan.enabled` | `router.enabled` | Today serves | Source and chooser |
|---|---|---|---|
| false | false | DL0's open queue, with `fix/daily-loop-bugs`' re-entry cap | none |
| false | true | The same open queue. R2 needs the plan, so the router has nothing to fill; R1's logging is unaffected | none |
| true | false | The finite plan | `legacy_lanes_v1` and `lane_quota_v1` |
| true | true | The finite plan | the staged-frame source and the router chooser (R2) |

The container's rules (minutes, lanes, finiteness, requests first, learner picks, re-entry, the streak) are the same in the last two rows. Only block choice differs.

### 6.9 Other item sources in the plan

- **Project understanding's delayed probes** (project M2 onward) are ordinary PF items. Due ones are scheduled checks in the maintain lane (§6.1), although they have never been attempted, at most `plan.project_probes_max_per_day` = 4 a day. Diffs labelled `automation` or `all_at_once` come first (project §5.3).
- **Assumed-known first reviews** (Phase 6) go in the maintain lane.
- **"Practice on…"** is a box on Today. A typed query ("conditional independence") goes to `find_practice` (Phase 5b); the learner chooses items from its proposals, and they become a learner-pick block. Before Phase 5b, a plain text search over item prompts stands in.

### 6.10 Items before reading (Q5; default, owner may override)

**As-you-read, plus optional pre-questions.**
- **A reading block.** A source imported `as_you_read` under a Learn or Master intent (or uncommitted) puts at most one reading block a day in the new lane: "Continue §3.2 · about 12 min". It is the reader guide plan's next unfinished section, carried as a `ReadingTarget` (§6.8). Starting it opens the reader there. Section completion still triggers item generation as today (`learnloop/reader/reader_progression.py`), and those items enter the new lane on later days.
- **Its size.** The estimate is the section's words left (§6.4). When that exceeds what the new lane, the plan or a block (15 minutes) has left, the block is a **partial reading block** of the size that fits: "Continue §3.2 · about 12 min (of about 25)". It never counts more minutes than it was given.
- **Progress** comes from the reader's existing `reader.mark_section_progress` (`learnloop_sidecar/handlers/reader.py:1371`). That method writes `reader_section_progress` (`migrations/106_reader_section_progress.sql:6`: spans seen, span count, completion). While a reading block is current, each call also appends a `reading_progress` block event with the spans seen and the span count.
- **Ending.** The block ends with a `block_ended` event whose `outcome` is one of:
  - `section_completed`: the reader marks the section complete;
  - `left_reader`: the learner goes back to the plan (Esc, or "Back to today's plan" in the reader);
  - `skipped`: the learner skips it from the block line.

  In every case its estimate counts as used, like a planned item done or skipped, and the plan moves to the next block. The sidecar method `plan_reading_ended` records the end, and `next_plan_item` returns the next step.
- **Interrupted reading.** If the app closes or the learner leaves Today mid-block, the block stays current, and reopening the plan reopens the reader at that section. If the day ends first, the plan is `abandoned`, but section progress is kept in `reader_section_progress`. The next day's reading block continues the same section with the words left.
- **Typed steps.** `next_plan_item` returns either `{"kind": "item", …}` or `{"kind": "reading", "reading": ReadingTarget, …}`, so the client never guesses what a block holds.
- **Pre-questions (DL4).** The block opens with up to `plan.pre_questions` = 3 questions, skippable and never required. They come from the existing quick-check producer, run at section start instead of section end.
  - They are **formative only**, like quick checks: recorded on `reader_authored_questions`, never attempts, mastery or evidence (`learnloop/reader/reader_quick_check.py:12`).
  - A pre-question answered correctly shows one tap, "I know this", which is the Phase 6 self-report. It is the learner's choice, never automatic.
- **Untaught material is never treated as taught.** Nothing from an unread section reaches the maintain lane.

---

## 7. Re-entry (P6, Q13)

- **Trigger.** Days since the learner's last real activity (`fix/daily-loop-followups` F1) exceed `hypothesis.reentry_gap_days` (7). **No goal is needed.**
- **The plan** is kind `reentry`:
  - its minutes are min(remembered minutes, `plan.reentry_minutes` = 15), with at most `plan.reentry_max_items` = 8 items (D11);
  - it uses the repair and maintain lanes only;
  - *owner decision 2026-10-12:* "keep going" after it builds the plan for the day's remaining minutes, which leads with new material (new takes its admitted minutes first, under ordinary admission, and its blocks win the chooser's ties), so new material is offered easily once the short re-entry is done;
  - its order: assumed-known checks that came due, then intent tier (Master, Learn and goals with deadlines; then Keep; then uncommitted), then the scheduler's rank. **Light touch is left out.**
- **The panel** stays survival-first:
  > Welcome back — 23 days. Still solid: 41. Slipped below target: 6 (eigenvalues, Bayes' rule, …). Today: a short re-entry, about 12 min, 7 items.

  - Solid and slipped are computed over LOs in active intents, comparing current retrievability with each one's intent target (§5.3), not over a goal's facets.
  - With an active goal, slipped facets are still named in blueprint-weight order, as today.
- **No debt screen.** No overdue count is shown and no due dates are rewritten, so the clock is never reset as if nothing were forgotten (intentions §10). Light-touch material fades honestly. It is visible on the map and returns through the maintain lane's capped share over the following days.
- **After re-entry:** "Re-entry done. Keep going?" offers a normal plan for the day's remaining minutes.
- **With `plan.enabled = false`,** the `fix/daily-loop-bugs` queue cap (`learnloop_sidecar/handlers/queue.py:90`) stays in force unchanged.

---

## 8. The streak (P5)

- **Kept, with the same computation:** local days with a started session (`learnloop/db/repositories.py:8878`). Phone sessions count automatically, since mobile M2 sessions are rows in `sessions`.
- **The label is made honest (D8).** The badge says "begin today's plan to keep your streak", which is what is counted, instead of "practice today…" (`screens/StartScreen.tsx:1607`). When today's plan is complete it shows "today ✓".
- **It never appears** in the re-entry panel, in reminders, or as pressure on the done screen. "Keep going" adds nothing to it. There are no freeze mechanics.
- **Reports never use the streak as a success measure** (intentions §15).

---

## 9. Grading latency (P7)

Grading stays synchronous. The plan hides what it can: the next item and block are computed while feedback shows (§6.5). `learnloop plan report` shows submit-to-feedback p50 and p95 from attempt receipts, against a target of p50 ≤ 15 s and p95 ≤ 60 s. The target is reported, not enforced.

---

## 10. Persistence

**Migrations.** Numbers are assigned when each phase lands (`ls migrations/`; the head is 166 on this base, and 167–168 are claimed by unmerged branches). Follow `CLAUDE.md`'s head-fixture procedure.

| Table | Role (`learnloop/db/table_roles.py`) | Phase | Contents |
|---|---|---|---|
| `daily_plans` | WORKFLOW | DL1 | `id`, `local_date`, `kind` (`normal` \| `reentry` \| `keep_going`), `parent_plan_id`, `minutes_budget`, `remembered_minutes` (the ordinary budget in force; §6.6), `minutes_source` (`chip` \| `carried` \| `generated`), `split_json` (lane minutes, loads, caps, reasons), `admission_json` (§6.3 inputs and result), `estimator_version`, `source`, `chooser`, `status` (`open` \| `complete` \| `stopped` \| `abandoned`), `algorithm_version`, `config_hash`, `created_at`, `completed_at` |
| `attention_blocks` (existing, migration 096) | WORKFLOW | DL1 | `ADD COLUMN daily_plan_id TEXT`, `plan_ordinal INTEGER`, `lane TEXT`, `chosen_by TEXT`, `decision_ref TEXT`, `reading_json TEXT` (the `ReadingTarget` of a reading block, else null). Existing rows stay null |
| `attention_block_events` (existing) | RECEIPT | DL1 | New kinds: `block_chosen`, `block_started`, `block_ended` (with `outcome`; for reading `section_completed` \| `left_reader` \| `skipped`), `item_planned`, `item_served`, `item_done`, `item_skipped`, `item_displaced`, `reading_progress` (spans seen, span count). `detail_json` carries `practice_item_id`, `scheduler_candidate_id`, `est_minutes`, `wall_ms` and `serving_origin` (`daily_plan` \| `learner_pick`) |
| `capture_inbox` (existing, from mobile M1) | RAW_LEDGER | DL3 | `ADD COLUMN source_anchor_json TEXT` (nullable; set at insert for reader captures, part of the request fingerprint, cleared by purge) |
| `practice_attempts` (existing) | RAW_LEDGER | DL3 | `ADD COLUMN reference_status TEXT NOT NULL DEFAULT 'not_applicable'` (`not_applicable` \| `verified` \| `unverified`), set once at attempt time (§4.4) |
| `practice_item_snapshots` (existing, migration 164) | RECEIPT | DL3 | `ADD COLUMN redacted_at TEXT`. The update trigger is replaced by one that admits only purge's redaction (§4.7); the delete trigger is unchanged |
| `assessment_contract_versions`, `activity_surfaces` (existing) | RAW_LEDGER | DL3 | `ADD COLUMN redacted_at TEXT`, set only by purge's redaction (§4.7) |
| `capture_processing` | WORKFLOW (paid outputs; never re-run on rebuild) | DL3 | `capture_id` (PK); processing (`processing_state` = `pending` \| `done` \| `failed`, `processed_at`, `processing_attempts`, `last_error`); `kind`, `transcript_md`, `transcript_confidence`; filing (`subject_id`, `learning_object_id`, `confidence`, `filing_status` = `filed` \| `unfiled` \| `moved`); answer (`solution_md`, `final_answer`); verification (`verification` = `pending` \| `verified` \| `unverified`, `unverified_reason`, `verification_check`, `verifier_version`, `verification_attempts`, `next_verification_at`); adoption (`adopt_requested_at`, `adopted_at`, `adopt_stopped_reason` = `call_cap` \| `processing_failed`, `practice_item_ids_json`, `commitment_id`, `family_id`); `purged_at` (§4.7); `model_ids_json`, `prompt_versions_json`, `estimated_cost_usd`, `cost_kind` (`metered` \| `estimated_only`), `updated_at` |

**Vault model additions** (optional, omitted when null, outside the scheduling hash):
- `PracticeItem.expected_minutes` (DL1);
- `ActivityFamily.source_kind` gains `captured` (DL3; needs Phase 3).

**No new tables or fields for intent.** DL2 writes commitment versions and events through the existing API; deadlines use the existing `goal_id` on commitment versions (§5.4).

**Config:**
- `[plan]`: `enabled`, `new_admission_enabled`, `reading_blocks`, `reading_from_furthest` (true; UX Phase 1's reading step, a live change wherever the plan acts, see §11), `default_minutes` (25), `minutes_presets`, `repair_max_share` (0.30), `maintain_max_share` (0.60), `keep_going_minutes` (10), `load_horizon_days` (14), `load_ceiling` (0.80), `new_item_reviews_14d` (4), `max_new_items_per_day` (10), `min_new_items_per_day` (1), `latency_cap_minutes` (15), `read_words_per_minute` (120), `pre_questions` (3), `reentry_minutes` (15), `reentry_max_items` (8), `project_probes_max_per_day` (4), `headline` (true).
- `[intent]`: `enabled`, `recall_targets_enabled`, `recall_targets`.
- `[capture]`: `enabled`, `processor_enabled`, `reader_presets_adopt`, `unverified_adoption` (true), `max_calls_per_capture` (12), `max_daily_cost_usd` (1.00), `auto_import_max_usd` (0.50), `test_me_later_days` (7).

**Receipts and verdicts:**
- `model_call` purposes: `capture_classify`, `capture_file`, `capture_solve`, `capture_draft`, `image_transcription`, `reader_pre_question`.
- `judgment_ledger` tasks: `capture_kind`, `capture_filing`, `reference_verification`.
- An owner verdict is appended for every Move and every adoption undo, so filing error stays measurable without a review chore (the PF undo pattern).

**Replay.** None of these tables is DERIVED. Replay ignores the plan and capture tables. Projections read only `practice_attempts.reference_status`, an attempt-row field recorded once (§4.4). Redacted revisions keep every id, hash and structural field that rebuild reads (§4.7). Rebuild never calls a model (L5).

---

## 11. Algorithm successors and kill switches

| Change to what is served or projected | Successor | Kill switch | The switch restores |
|---|---|---|---|
| Today serves the finite plan: split, blocks, new-material admission, reading blocks, plan-based and goal-optional re-entry, auto-advance within the plan | `daily_plan_v1` (the next free algorithm version at DL1's landing) | `plan.enabled`; sub-switches `plan.new_admission_enabled` and `plan.reading_blocks` | DL0's Today: the open queue with `fix/daily-loop-bugs`' re-entry cap |
| Intent: exclusion by disposition, per-intent recall targets, push from Learn and Master, re-entry triage by intent | `intent_v1` (the next free version at DL2's landing) | `intent.enabled`; sub-switch `intent.recall_targets_enabled` | Serving reads commitments only for requested items, as today |
| Capture adoption | None: content, like writing a card | `capture.enabled`, `capture.processor_enabled` | No box, no processor; M1's manual routes |
| Certification ignores attempts on unverified keys (§4.4) | `capture_reference_v1`, a projection successor (the next free version at DL3's landing) | None that re-enables certification (C3). `capture.unverified_adoption = false` stops new unverified adoptions, so the gate has nothing to act on | — (with no `unverified` attempts, projections equal the predecessor's) |
| Reader presets through adoption | None: content path | `capture.reader_presets_adopt` | Reviewable proposals |
| DL0's UI changes, the headline, the streak label, pre-questions | None: display and formative only | `plan.headline` (the headline only) | — |
| The reading block continues from the furthest section read and skips front matter while a chapter is left (UX Phase 1 usability round 1, U4; added after DL1) | None: a live change behind its kill switch (owner ruling at the UX Phase 1 landing on main, `docs/reviews/ux-phase1.md` "Landing onto main": live changes behind kill switches, not successors, for serving changes replay never reads, as in the facet-locks F6 ruling). The branch built it as a placeholder successor (`docs/reviews/ux-phase1-round2-codex-review.md`, F2 and its re-review); the landing dropped the tag. No scoring, scheduling or projection change; plans already composed keep their rows, and replay never reads the selection | `plan.reading_from_furthest` | DL1's selection (mvp-0.14's): the first unfinished section in book order, front matter included |

**For each successor** (`docs/algorithm-change-playbook.md`):
- an upgrade function and a fingerprint entry;
- a shadow rebuild on a `fixtures-local/` backup-API copy of each tracked fixture, showing **zero** mastery, facet and projection deltas. `daily_plan_v1` and `intent_v1` change serving only, and `capture_reference_v1` acts only on `unverified` attempts, which the fixtures don't have;
- a served-set diff documented in the phase review;
- the head fixture regenerated.

**Kill-switch parity is a gate:** with the switch off, the Today RPCs return byte-identical results to the predecessor on fixture copies (G1, G4).

---

## 12. Rollout

The daily-loop implementation is Wave 2 of `implementation_goal.md` §3. Every phase goes through its loop: implement, Codex adversarial review, fix, gate, integrate. Phases merge one at a time.

| Phase | Builds | Needs | Serving change | Gate and checkpoint |
|---|---|---|---|---|
| **DL0: start friction** | Minutes-only Start (desktop and TUI); remembered minutes (last session's); one-tap minute chips; auto-advance from feedback to the head of the live queue, with the list one key away; the honest streak label | Nothing (this base) | None (UI only) | G11; vitest and pytest for each item; `get_today_queue` output unchanged on fixture copies |
| **DL1: the finite plan** | `daily_plans` and the `attention_blocks` columns (one migration); `split_v1`; §6.3 admission; §6.4 estimator and `PracticeItem.expected_minutes`; `legacy_lanes_v1` and `lane_quota_v1` behind §6.8's interface; plan RPCs (`get_daily_plan`, `set_plan_minutes`, `next_plan_item`, `plan_reading_ended`, `plan_keep_going`, `plan_more_new`, `plan_learner_pick`, `get_today_headline`); Today plan view, block lines, done screen, keep going; goal-optional re-entry (§7); reading blocks without pre-questions; the headline; `learnloop plan show \| report` | DL0; `fix/daily-loop-followups` merged (F1). Phase 6 preferred, not required | `daily_plan_v1`, `plan.enabled` | G1–G3, G10, G12, G13; shadow rebuild with zero projection deltas. **Owner checkpoint:** two weeks of use, then read `learnloop plan report` (days active, plan starts and completions, estimated vs actual minutes, keep-going rate, open-to-first-item time). That answers Q0 (§14) |
| **DL2: intent** | Intent resolution (§5.1, §5.3 precedence); the single control (§5.2) on LO, subject, source, item and capture views, with the cost preview; serving-time recall targets; disposition exclusion; push from intent; deadlines (a learner goal linked through the commitment version's `goal_id`); re-entry triage by intent; assumed-known as Keep (§5.6) | DL1 | `intent_v1`, `intent.enabled` | G4; shadow rebuild with zero projection deltas; uncommitted items' order byte-identical at 0.90. **Owner checkpoint:** the target table (Q8) |
| **DL3: capture** | `capture.create` and the box (Alt+C, text, URL, image paste and drop stored); the Captures strip replacing M1's Inbox strip; the processor (§4.3) for text and URL captures (images wait for DL4); purge of processed content and of the adopted item's stored revisions (§4.7); `capture_processing`, `capture_inbox.source_anchor_json`, `practice_attempts.reference_status` and the `redacted_at` columns with the snapshot trigger (one migration); the attempt-time certification gate (§4.4); Practice this (§4.4); Move and undo; spend controls and `learnloop capture add \| list \| process [--dry-run]`; the "Practice on…" box (§6.9) | DL1 (the "Practice on…" block); mobile M1 merged; Slice A Phase 5a merged for verification (otherwise answers stay `unverified`, §4.3); Phase 3 for the one-member family; Phase 5b for `find_practice` (text search until then) | `capture_reference_v1` (projection; otherwise content) | G5–G9, G15; shadow rebuild with zero projection deltas. **Owner checkpoint:** capture report (captures per week by channel, filing confidence, Moves, verification rate, adoption rate) |
| **DL4: images, reader presets, pre-questions** | Image transcription in the processor (the `image_transcription` route, added here if the image drop-in spec hasn't landed); image drop-in on the Ingest screen into `capture_inbox`; reader presets through adoption (§4.5); pre-questions in reading blocks (§6.10) | DL3 | None | G5–G9 and G15 for images; G14 |
| *Router R2 (router spec)* | The staged-frame source and the router chooser through §6.8 | DL1; R1 | The router's successor | Router G1–G9 |
| *Mobile M2a (mobile spec)* | The phone shows the plan through allowlisted plan RPCs | DL1; mobile M2 prerequisites | — | Mobile gates |
| *Mobile M3 (mobile spec)* | Processor results and Practice this on the phone | DL3 | — | Mobile gates |
| *Project M2 (project spec)* | Due probes in the maintain lane | DL1; project M2 | — | Project gates |

---

## 13. Gates and tests

| # | Gate |
|---|---|
| G1 | **Plan kill switch.** With `plan.enabled = false`, `get_today_queue`, Start and Today behave exactly as DL0 on fixture copies, including the re-entry cap, whatever `router.enabled` says. Each row of §6.8's switch table has a parity test: both `plan.enabled = false` rows equal DL0; `plan.enabled = true, router.enabled = false` equals DL1; with both on, the container's invariants (G2, G12, G13) hold as in DL1 |
| G2 | **Finite.** A plan's planned estimate never exceeds its budget, and no lane's blocks exceed its allotment after redistribution. Requested items are deducted before the split. Follow-ups and learner picks displace and never append. Captures adopted mid-plan don't join it. Keep going is the only extension |
| G3 | **Honest numbers.** Every count and minute figure on Start, Today, the done screen and the re-entry panel is derived from the plan DTO, and a test asserts each displayed number equals what is served |
| G4 | **Intent kill switch and identity.** With `intent.enabled = false`, serving matches DL1. With it on, uncommitted items' effective due equals `due_at` exactly (ratio 1 at 0.90). Exclusion and depth follow §5.3's most-recent-choice resolution: an item Pause under an LO Master excludes the item; a subject Pause after adoption excludes the adopted items, requests included; an LO choice after an item Pause re-includes the item; a request commitment never lowers a control-chosen depth; the control's consequence line equals the resolved result. "Check once" serves exactly one item, after the delay, then nothing: after the check is answered, later plan builds serve none of the items it covers, even under an older LO Master, until a later choice covers them. A check replaced by a newer choice before its date is never served. Satisfying a check doesn't move its choice time. Persisted `due_at` never changes |
| G5 | **Saving is a reference.** `capture.create` creates no practice item and no commitment. "Practice this" creates exactly one adoption per capture, idempotent under retries and concurrent runners; undo retires the item and the commitment |
| G6 | **No decisions at capture.** The capture API has no subject, LO or intent parameter. Filing never blocks saving, and unfiled captures are found by search |
| G7 | **Verification.** `verified` requires the §4.3 checks (PF's tests reused). An item with an unverified key is excluded from certification cold probes, exam pools and assumed-known checks, and is labelled everywhere it shows. An ordinary independent, unassisted attempt on it schedules FSRS but earns zero certification credit in both projections. That still holds after the key later verifies; attempts made after verification certify; a rebuild reproduces both |
| G8 | **Replay.** Rebuild makes zero model and embedding calls with capture and plan tables populated; `capture_processing` is never re-run; DL1, DL2 and DL3 shadow rebuilds show zero projection deltas on the fixture copies |
| G9 | **Spend.** The processor respects the lifetime per-capture call cap and the daily cost cap. The call cap stops calls, never call-free work: an adoption whose results are persisted completes after the cap is reached, and work that still needs a call ends with its label; `--dry-run` prints calls, tokens and cost; Codex receipts are `estimated_only`; every filing and verification verdict is in `judgment_ledger` |
| G10 | **Re-entry.** It shows without any goal after the gap (measured per F1); it respects the minute and item caps; Light touch is excluded; no overdue count and no streak text appear; no due date is rewritten |
| G11 | **Streak.** The count is unchanged on fixture copies; the label matches what is counted; phone sessions count |
| G12 | **Learner picks win** and are logged with no propensity; picks displace the plan's tail rather than growing it |
| G13 | **Chooser interface.** A candidate larger than `minutes_left` (e.g., 7 minutes with 5 left) or than its lane's remaining minutes (e.g., 10 minutes with 1 left) is never offered. A fake chooser that names an unknown or infeasible id, or that tries to overspend a lane, cannot do so: the container falls back and flags it. Released lane minutes follow §6.2's flow-on order. Every block decision is logged with its candidate set |
| G14 | **Formative pre-questions.** They write no attempt, observation, mastery or FSRS row |
| G15 | **Purge.** After a purge, no capture text, transcript, solution, answer, receipt text, checkpoint or embedding of the capture remains, and search can't find it. That holds when the purge comes after processing, during processing (a worker holding the lease writes no content afterwards), and after adoption. After adoption the adoption is undone and the item's text is replaced in the vault and in every stored revision (snapshots, surfaces, contracts, grading receipts), including when a queue build made the only copy; attempts are kept. A sentinel planted in the capture is found afterwards only in the item's attempt history (and in M1's manual-route destinations, which §4.7 keeps). A rebuild after the purge reproduces the projections from before it, except learner field F1's revision status for the purged item's attempts (§4.7) |

**Tests** (fakes only: `tests/structured_ai.py`, `tests/openai_fakes.py`; vault builders from `tests/helpers.py`):
- **DL0:** `StartScreen.test.tsx` (no sliders; remembered minutes; chips); `FeedbackScreen` (Next opens the next item; Esc and `b` still open the list); `tests/test_daily_loop_start_minutes.py` (`start_session` without energy; TUI has no sliders; streak label).
- **DL1:**
  - `tests/test_daily_plan_split.py` (shares, flow-on, re-entry lanes);
  - `test_daily_plan_build.py` (lane classification, including a never-attempted due project probe on an uncommitted, learning-eligible LO landing in maintain under the probe cap and outside the new-item cap, and the fifth due probe staying "later"; block packing, including a single due item of 3.5 minutes as a complete block, several small maintain groups merged into one block, and a 3.5-minute item served with 4 minutes left; finiteness; request deduction before the split; displacement; learner picks);
  - `test_daily_plan_admission.py` (ceiling, cap, floor, exemptions, "more new");
  - `test_duration_estimates.py` (shrinkage, winsorizing, fallbacks, reading estimate);
  - `test_daily_plan_reentry.py`;
  - `test_daily_plan_kill_switch.py` (G1, including every row of §6.8's `plan.enabled` × `router.enabled` table; the router-on rows use a fake router chooser);
  - `test_block_chooser_interface.py` (G13);
  - `test_daily_plan_rpc.py` (including remembered minutes: 40, then a 10-minute keep going, defaults to 40 the next day; a 15-minute re-entry plan and the post-re-entry remainder leave 40 in place; a chip tap on a re-entry plan changes the remembered value but not the re-entry cap);
  - `test_daily_plan_reading.py` (the words-left estimate; a partial block when the section exceeds the remaining minutes; each `block_ended` outcome advancing the plan and consuming the estimate; `reading_progress` events from `reader.mark_section_progress`; resuming an interrupted block; the next day continuing the same section; `next_plan_item` returning a typed reading step);
  - `test_today_headline.py` (one of two required capabilities demonstrated on a facet → learning; one of two facets fully demonstrated → learning; every facet fully demonstrated → demonstrated; a blueprint LO with all components but an integration gap → learning; each LO in exactly one class);
  - vitest for the plan view, block lines, done screen and keep going, and for a reading step opening the reader at its section and returning to the plan.
- **DL2:** `tests/test_intent_resolution.py` (the §5.3 cases, ties, and consequence-line parity; "Check once": an uncommitted item and an item under an older LO Master each get one check, and after it is answered the next plan builds exclude them; a later LO choice re-includes them; an LO Master chosen after an item's "Check once" but before its date replaces the check, which is then never served; the satisfaction event leaves the choice order unchanged); `test_intent_recall_targets.py` (the ratio; identity at 0.90; the kill switch; the anchor: a primed retry and a diagnostic attempt between two reviews leave the anchor and the effective due unchanged, while an ordinary review moves both; no state, a null `due_at`, or no qualifying attempt fall back as §5.3 says; on fixture copies, for each item with an anchor and a surprise record, anchor + stability × that attempt's `attempt_surprise.fsrs_interval_factor` reproduces the stored `due_at` within one second, which catches any drift between the anchor rule and the attempt path); `test_intent_exclusion.py`; `test_intent_goal_deadline.py`; vitest for the control and its cost preview.
- **DL3:**
  - `tests/test_capture_box.py`;
  - `test_capture_processor.py` (classify, file, unfiled, solve-verify agreement and disagreement, caps, dry-run, resume, leases, ledger; the selection rule: an adopted, `routed` capture with `unverified_reason = no_checker` is retried once when the verifier version changes and keeps `routed` under the lease; an `error` retries on backoff; an unadopted capture is not retried; adoption requested before processing completes afterwards; the lifetime call cap counts processing, drafting and retries together and stops further calls; with processing done on the last allowed call and the adoption still pending, the next run completes a `problem` adoption with zero model calls, while an `idea` adoption that still needs drafts closes with `call_cap`; processing still pending at the cap becomes `failed`, and a requested adoption closes with `processing_failed`);
  - `test_capture_adopt.py` (idempotence, request front slot, family, undo);
  - `test_capture_unverified.py` (G7: an independent attempt on an unverified key earns no credit in the canonical projection or the facet timeline; it still updates FSRS; a later verification doesn't retroactively certify it; the next attempt after verification does; a rebuild reproduces the same ledger; `capture.unverified_adoption = false` defers adoption until `verified`);
  - `test_capture_replay.py` (G8);
  - `test_capture_purge.py` (G15: purge after processing; purge while a fake worker holds the lease and then commits; adopt, build the queue, then purge, which redacts the snapshot the queue build wrote, and a later queue build leaves the redacted row as it is; adopt, answer with a fake LLM grader, then purge, which redacts the surface, the contract and the grading receipt; a sentinel scan of every text column in the vault database and of the vault's files, with hits allowed only in the item's attempt rows and rows keyed by their attempt ids; the snapshot trigger rejecting every update except the redaction; a rebuild before and after the purge; search afterwards).
- **DL4:** `tests/test_capture_images.py`; `test_reader_presets_adopt.py`; `test_reader_pre_questions.py` (G14).

**Every phase also runs** `uv run lint-imports --no-cache`, `uv run pytest -n auto`, `uv run pytest -m durability`, `npm run typecheck && npm test` when the frontend changed, and the DB reference generate and validate scripts when the schema changed.

---

## 14. Decisions: recommended defaults (accepted 2026-10-12 as "most defaults"; each default, owner may override)

**The questions this spec was asked to settle:**

| Q | Question | Default (default, owner may override) |
|---|---|---|
| **Q0** | How often you open LearnLoop, and what stops you | **Assume** near-daily intent with irregular, short sessions, where starting (a form every day) and never ending (an open list) are the main friction. **So** DL0 and DL1 come first, intent second, capture third. DL1's two-week `learnloop plan report` measures it (days active, plan starts, completion, open-to-first-item time), and the owner answers Q0 at the DL1 checkpoint. If capture away from the desk turns out to be the bigger blocker, DL3 moves ahead of DL2 |
| **Q5** | Items from a book before reading it | **As-you-read, plus optional pre-questions** (§6.10). A Learn source puts one reading block a day in the new lane, opened with up to 3 skippable, formative pre-questions. Nothing unread reaches maintenance |
| **Q7** | Which object carries intent | **Commitments, with goals as optional deadlines** (§5.1, §5.4). One control (§5.2); no commitment means today's behaviour |
| **Q8** | What "maintain" costs | **Per-intent recall targets** at serving time: Light touch 0.80, Keep 0.85, Learn 0.90, Master 0.92, uncommitted 0.90 (§5.3). Integrative questions are deferred (§15) |
| **Q11** | The new-material mechanism | **Load-based admission:** projected review load + new load ≤ 80% of the budget, at most 10 new items a day, at least 1. Learner requests are exempt, and "more new material" is a labelled override (§6.3) |
| **Q12** | Where time estimates come from | **The learner's own durations, with an LLM estimate as the starting guess:** shrinkage from own latencies → practice-mode median → `expected_minutes` prior → 3.0, plus feedback dwell (§6.4) |

**This spec's own decisions:**

| # | Decision | Default (default, owner may override) |
|---|---|---|
| D1 | First-run minutes | 25, then remembered |
| D2 | Split caps | Repair ≤ 30%, maintain ≤ 60%, the rest to new and push (§6.2) |
| D3 | "Keep going" size | +10 minutes per tap |
| D4 | Capture shortcut | Alt+C, in-app (an OS-global hotkey is deferred) |
| D5 | Adopting a capture whose answer isn't verified | Allowed: labelled; it schedules and teaches but never certifies (an attempt-time gate); verification is retried (§4.4) |
| D6 | Auto-confirming a source import from "Practice this" | When estimated cost ≤ $0.50; otherwise Quick Add's single confirm |
| D7 | The Today headline | Shown by default, one line, hideable |
| D8 | Streak semantics | Count unchanged (days with a started session); label made honest |
| D9 | Plan day boundary | Local calendar date, the same as the streak |
| D10 | Reader "Remember later" presets | Through adoption, no review queue (§4.5) |
| D11 | Re-entry size | ≤ 15 minutes and ≤ 8 items; Light touch excluded |
| D12 | The capture processor | On by default, with metered spend capped at $1.00 a day; Codex `estimated_only` |

---

## 15. Deferred, with triggers

| Deferred | Revisit when |
|---|---|
| Integrative questions that credit several concepts from one answer (Q8's second option) | PF families are live and the idea-key replay (Phase 3b) shows multi-concept credit predicts later recall |
| An OS-global capture hotkey (Tauri plugin) | B3 is fixed and the in-app box is used most days |
| The browser extension | Captures from the box and the phone show a gap for web pages |
| A readiness model (energy, sleep) | P4 U-011's affect stream is wired into the snapshot |
| Offline phone practice | Mobile D9's conditions |
| Streak forgiveness mechanics | The owner asks |

---

## 16. Cross-spec notes (record when each phase merges)

- **Router.** R2's input is §6.8. `LearnerStateCardV1`'s session and intent fields come from `PlanState` and §5. The lane budgets are feasibility constraints the staged frame must honour. The router's §7.3 kill switch returns Today to the pre-router version, which is the plan with `lane_quota_v1` when `plan.enabled` is on (§6.8's switch table; revised in the router spec with this spec).
- **Learner field.**
  - DL1 is the "finite, system-ordered plan" that field F7 waits on. Plan events carry `serving_origin` (`daily_plan` or `learner_pick`).
  - §5.2's "when daily-loop Q7 exists" mapping is §5.6 here.
  - §5.3's re-entry hand-off is §7 here.
  - §3's `revision_status`: a snapshot redacted by a capture purge (§4.7) can't be re-hashed, so it counts as a missing revision (`excluded` by default).
- **Embedding consumers.** Capture verification reuses that spec's §5.3 verified-reference rules. Adopting a capture whose key is unverified is a narrow, learner-requested exception to §5.3's no-publish rule, with an attempt-time certification gate (§4.4); generated variants still need a verified reference. Its §5.9 "practice this box" is the "Practice on…" box (§6.9). `pf.max_published_per_day` becomes a generation guard; serving pace is §6.3.
- **Mobile.**
  - §6.7's background processor is §4.3. T6 is met when DL3 lands; the phone's part is M3.
  - `purge_capture` extends to processed content, receipts, checkpoints, embeddings, adopted items and their stored revisions (§4.7); M1's own purge and its manual-route destinations are unchanged.
  - Q14 is answered (minutes only), so §6.5's readiness note and the header's "Depends on … Q0–Q18 … unanswered" can be updated.
  - M2a's allowlist adds the DL1 plan RPCs.
- **Project understanding.** From M2, due probes enter the maintain lane (§6.9).
- **Slice A.** Phase 6's new-material ordering feeds §6.3's admission. Phase 5a's verifier is reused by §4.3.
- **Handoffs.** The "Daily-loop implementation" row in `implementation_handoffs.md` §1 uses the template below, once per phase.

---

## 17. Agent prompt template

Fill in `<n>` (DL0–DL4), the phase row from §12, and the base branch. Give it to a fresh agent in the repo. The Codex review and fix steps follow `implementation_goal.md` §2.

```text
Implement LearnLoop daily-loop phase DL<n>, as specified in
docs/specs/spec_daily_loop_v1.md (§12 row "DL<n>", plus the sections that row cites).

Before coding, read: CLAUDE.md; docs/specs/implementation_handoffs.md §0 (standard rules
and invariants); spec_daily_loop_v1.md in full; docs/specs/daily_loop_frictionless_defaults.md;
the sections of other specs the row names; db/table_roles.py;
docs/algorithm-change-playbook.md. Then write a short plan (files, migrations, successor
and kill switches, spend caps and model routes, judgment_ledger writes, tests) to
docs/reviews/daily-loop-dl<n>.md and proceed.

Work in your own worktree on a new branch daily-loop/dl<n>, created from <base branch>.
Follow §0 of the handoffs and §2 of the spec, especially:
- only the successor and kill switches §11 lists for this phase; with the switch off,
  behaviour is byte-identical to the predecessor (gates G1/G4);
- recall targets and estimates never touch persisted FSRS state or evidence;
- replay makes no model or embedding calls; capture outputs are persisted inputs;
- every paid step uses the spend framework with --dry-run; Codex is allowed for every
  LLM role without a physical-request bound and is recorded estimated_only;
- no live or paid AI calls in development or tests (fakes only);
- manual runs only on learnloop.db.copies backups under fixtures-local/; never commit
  changes to fixtures/linear_algebra, fixtures/probability or fixtures/arxiv_v2;
- if the spec contradicts the code, record it in the review file, take the
  conservative option (switch off, no evidence writes) if work can continue, else stop.

Done means: the phase's gates (§13) pass; its listed tests exist and pass;
uv run lint-imports --no-cache, uv run pytest -n auto and uv run pytest -m durability
pass; npm run typecheck && npm test pass if the frontend changed; the DB reference
scripts pass if the schema changed; a shadow rebuild on a fixtures-local copy is
reported for any successor. The review file lists what was built, deviations, test
results with pass counts, files touched, migrations, owner-run commands (dry-run
first) and open questions. Commit with clear messages; do not merge or push.
```

---

*Related: `daily_loop_frictionless_defaults.md` · `spec_action_router_v1.md` (§3, §6.3, §7, §8) · `spec_learner_field_v1.md` (§3.1, §5.2, §5.3) · `spec_embedding_consumers_v1.md` (§5.3, §5.9) · `spec_mobile_tailnet_v1.md` (§6.5, §6.7, §9.1) · `spec_project_understanding_v1.md` (§5.2, §9) · `docs/brainstorming/Daily Loop Open Questions.md` · `docs/brainstorming/LearnLoop_User_Intentions_v2.md`*
