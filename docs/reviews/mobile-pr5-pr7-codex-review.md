# Mobile PR-5, PR-6 and PR-7: Codex review (gpt-6.1-sol) and fix round

Stage `mobile-pr5-pr7`, branch `mobile/pr5-pr7`, codex job `20261103-020659-4oIq1a`. Six Medium findings, no High. Each was reproduced first:
F1, F2 by the new tests on the pre-fix sources; F3 by the new parametrized cases; F4, F5 by the new vitest cases; F6 by inspection (there was no switch to test).

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Phone filtering corrupts router propensities | **Fixed** | b0684f8a4f, 14bb2c6153 | `test_a_limited_offer_logs_no_probability_for_an_item_below_the_cut_it_cannot_show`. Before: `head_distribution` gave an image below the cut and the hunt 0.25 each |
| F2 | Medium | The limit before eligibility can starve the phone | **Fixed** | b0684f8a4f, 14bb2c6153 | `test_a_limit_is_applied_after_the_filter_so_the_top_item_cannot_starve_the_phone`, `test_the_reentry_cap_is_applied_after_the_filter_too`, `test_a_follow_up_naming_an_ineligible_item_cannot_come_back_at_the_top`. Before: an empty queue |
| F3 | Medium | Valid Markdown references bypass eligibility | **Fixed** | d99c09c7a7 | `test_reference_forms_resolve_as_the_renderer_resolves_them` (10 cases), `test_brackets_the_renderer_shows_as_text_stay_eligible` (9) |
| F4 | Medium | Focus does not recover a missed bump | **Fixed; the refetch at an unchanged token is superseded by ruling R1 (Sol verify V1)** | 25fde8c546 | `useQueueRevisionPoll.test.tsx` "refetches once at an unchanged token", "counts visibility and focus arriving together as one return", "holds a return's refetch while quiet", "keeps a return's refetch through a failed token read"; `test_a_failed_bump_is_owed_and_the_hosts_next_request_pays_it_once` |
| F5 | Medium | A failed session read consumes the handoff signal | **Fixed** | 25fde8c546 | "keeps a failed read owed: the next tick at the same revision reads again", "retries a failing read once a tick, never in a loop and never beside a read in flight" |
| F6 | Medium | Device serving has no successor or kill switch | **Kill switch and policy name fixed; successor rejected** | b0684f8a4f | `test_switched_off_*` at the queue, the skip, both by-id doors, the probe contract and adoption; `test_the_phones_decision_names_the_rules_and_the_desktops_does_not`. The successor's reason is below |

## What changed

**F1, F2: the filter is in the build.** Filtering after the build could not be right for either: the cut had already fallen, and the draw's support already held items the phone cannot show. `build_due_queue(device_filter=)` now
asks before an item becomes a candidate, so the exploration's support, the composition, the slate and the limit (a client's or the re-entry cap) see only what the phone can answer, and the logged probabilities are the phone's real ones by construction. There is
no second rule in `_OfferHeadRule` to keep in step, and `publish_offer` is back to its signature on main.

- **Orchestrator ruling R1 holds.** The gate is `BuildGates.device_gate`, last in `serving_exclusions.admission_reason`, reason `device_ineligible`, so a "Check once" asks the same predicate and a cold candidate the phone cannot show never decides a check. `test_r1_every_gate_of_the_build_is_the_admission_predicates` is unchanged.
- **`device_deferred_count` is what the build would have served.** The candidate loop still ranks a refused item, and holds it after the zero-priority filter, so a hunt that is not due is not "waiting for the desktop". The count no longer depends on where the cut fell.
- **The by-id ways in.** A follow-up task naming such an item is skipped and stays pending for the desktop. A committed probe presentation on such an item is neither pinned nor ended by a phone's build: it was the session's assignment, and the desktop resumes it (`test_a_presentation_on_an_item_the_phone_cannot_show_survives_the_phone_queue`).
- **The desktop is untouched.** `device_filter` is None with no origin, `device_gate` then returns None, and the reply and router row stay pinned by `test_the_desktop_queue_is_unfiltered_and_has_no_count`.

**F3: a parser.** The renderer is remark (CommonMark, plus GFM and math). `_prompt_reason` now strips code and math as before, then parses with `markdown-it-py` (already installed through `rich`, now a direct dependency; `uv.lock` gains only the two edges) and reads image, link and HTML tokens. So a shortcut, collapsed or full reference
resolves through its definition, a local autolink counts, and indented code is code. **One behaviour flips on purpose:** `![graph][fig1]` with no definition was `embeds_image`, and is now eligible, because the renderer shows it as text on every device. The old test's case moved. The parse is cached per prompt (`lru_cache`, 4096: a memory bound, not a decision).

**F4: a return refetches once at any token.** §3.3 says "adds a refetch when the window regains focus"; the as-built note had narrowed that to "only if the token moved", and no token can show a bump that never landed. Held while quiet, as a change is. A focus and a `visibilitychange` that arrive during one token read are one return. A failed read keeps it owed for the next tick, with no loop.
The bump itself is recoverable too: `bump_for_host` sets `SidecarContext.host_bump_owed` on failure and `acting_as` retries it at the start of the host's next request, never failing that request. An atomic bump was not chosen: the mutations commit in many transactions across handlers, and the point of `host_mutation` is that the host has nothing to remember. A host that dies with a bump owed is what the focus refetch was for. **Superseded by Sol verify V1 and ruling R1, below:** a return no longer refetches at an unchanged token.

**F5: a session read stays owed until one answers.** Retried once a tick, inside the tick's one-call-in-flight, so never in a loop or beside another call. A read that came back for a session no longer open keeps it owed, for the one open now.

**F6: the switch.** `practice.device_eligibility_enabled` (default true; classified structural/operational in the parameter registry; every snapshot recomputed, and dropping the key reproduces them: the two snapshot tests pop it). Off, a phone request is served as the desktop is at every door, because all of them ask `serving._device_rules_on`. A phone offer's router inputs name the rules: `device_policy: device_eligibility_v1`, or `off`.

**F6: why no successor.** The playbook's 2026-10-17 rule covers a change to which items are served as measurements. Rejected here for three concrete reasons:

1. **Nothing is served differently on any existing surface.** `learnloop_mobile.allowlist.ALLOWLIST` is empty and nothing in `src/` calls `acting_as`, so no origin exists in production, and the desktop takes no new branch (G9, pinned).
2. **No predecessor state exists for a tag to protect.** The playbook's form is "below the tag, or with the switch off, the predecessor's code". A phone queue has no predecessor: below such a tag a phone would be shown items it cannot render, which §6.4 forbids and no vault has ever been in. A vault that M2 serves at mvp-0.43 should still filter.
3. **It would cost the owner an upgrade for nothing:** an extra link in the chain, a snapshot and an upgrade path for a tag with no desktop effect, while a data-capture stage may land its own.

The question belongs to M2, which opens the door: see below. The switch answers the finding's concrete scenario (a faulty rule cannot be disabled without editing content or code).

## The review's "claims that don't hold"

| Claim | Now |
|---|---|
| "The desktop's next focus catches up" | True at this round: F4. **False since ruling R1:** a return reads and refetches nothing at an unchanged token; the host's next request on that vault pays a failed bump |
| The router decision describes the published phone policy | True, by construction: F1 |
| The prompt scan covers image embeds and asset references | True for reference forms: F3. A raw `<a href>` or `<object>` is still not read: the renderer has no raw HTML plugin, so it shows nothing there |
| Desktop parity justifies no successor | Partly conceded: a switch now exists; the successor stays rejected for the reasons above |

## Consequences and open questions

1. **F6's successor is a ruling to confirm.** It is rejected at this stage; if the owner's rule is read as covering phone serving, the natural place is M2's landing, when an origin first exists.
2. **Superseded by ruling R1 (a return refetches nothing at an unchanged token).** A window's return cost one Today rebuild at this round. Every alt-tab away and back runs one `get_today_queue` and `get_daily_plan` when Today or the App is listening, each writing its usual slate and router row. That is §3.3 as written, and the review's fix. If it shows up in use, M2 can skip a return shorter than some interval (a `keep` bound), which is not added here because nothing measures it yet.
3. **A check's refused candidate is not counted as waiting.** An ineligible candidate of a due "Check once" is refused by the check gate (`intent_check_refused`), which runs first, so `device_deferred_count` omits it. The count errs low by that item, and the check serves its next candidate.
4. **The owed bump is in memory.** It is lost with the process. The focus refetch covered that at this round; since ruling R1, M2's host bumps once at start, so the token moves (recorded for M2, not built).

## Gate (this step; the full suite runs once in the landing gate)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, pytest at `-n 6`, vitest at `--maxWorkers=4`, one at a time. `lint-imports` and the catalog scripts ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No model call, no paid call, synthetic vaults only.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **42 kept, 0 broken** |
| **Targeted run 1**, 275 files (the stage's 191, plus every test naming `build_due_queue`, `device_eligibility`, the fingerprints, `parameter_registry`, `bump_for_host`, `acting_as`) | 6,017 passed, 51 skipped, 3 xfailed, **3 failed**: all three this round's own (R1's gate test; two snapshot tests that needed to pop the new key). Fixed by 14bb2c6153 |
| **Targeted run 2**, 152 files, on the final code: every file naming `build_due_queue`, `admission_reason`, `serving_exclusions`, `slot_facts`, `pool_admission`, `check_admission`, `get_today_queue`, `skip_practice_item`, the fingerprints, `parameter_registry` | **3,876 passed, 38 skipped, 3 xfailed, 0 failed** in 40 min 58 s |
| **Contract and mobile set** on the final code, 22 files (architecture, CLI help snapshot, config refactor, coordinated migrations, desktop RPC contract, ingest jobs, mobile allowlist, capture, doctor, host auth, host coexistence, pairing, shortcuts, module catalog inventory, public tip guards, secondary attach, session ownership and its migration, sidecar contract, serializer snapshot, table roles, tracked fixture databases), plus `test_device_eligibility`, `test_host_queue_revision`, `test_request_origin` | **873 passed, 5 skipped, 0 failed** |
| Directly touched files after the gate move: `test_device_eligibility`, `test_host_queue_revision`, `test_request_origin`, `test_intent_orchestrator_rulings`, `test_teacher_te1b_suggestions`, `test_teacher_te1_successor`, `test_ad23_inversion`, `test_ad23_intent_compose` | **373 passed** |
| Durability (`-m durability`): `test_device_eligibility`, `test_host_queue_revision` | **92 passed** |
| `npm install`, `npm run typecheck` | clean |
| vitest `useQueueRevisionPoll.test.tsx`, `App.queueRevision.test.tsx` | **28 passed** |
| `npm run frontend:build` | ok |
| `db_generate_reference`, `module_generate`, `desktop_generate`; `db_validate_reference`, `module_validate`, `desktop_validate` | regenerated (1,129 config leaves; 1,156 module notes; 313 TS notes); all valid |
| `cargo check` | not run: nothing under `src-tauri` changed |

The union of files is `docs/reviews/artifacts/mobile-pr5-pr7-codex-review-targeted-tests.txt`.

**Not run here, by the owner's rule:** the full suite, the whole durability lane, the whole vitest run.

## Sol verify V1 to V3 (job `20261103-041613-smoeES`) and the orchestrator's rulings

The scoped verify came back NOT CLEAN with three Mediums, and the answer to its item 5 showed the review's fix for F4 cost more than it recovered. The orchestrator ruled (the rulings are recorded verbatim in `mobile-pr5-pr7.md` under "Landing onto main"). Each fix was reproduced first and is its own commit.

| Id | Ruling | Finding | Commit | Reproduction, then the test |
|---|---|---|---|---|
| V1 | R1 | A window's return invalidates the queue at an unchanged token | 46f27b3b1d | 200 returns made 200 invalidations, now 0, with 200 session reads: "200 returns at an unchanged revision" and the pins of a refetch reversed |
| V1b | R2 | The moved poll refetches and reloads on screens where Today's poll never ran | da3182176a | A job on Library or Reader, in a lesson or an exam reloaded at once: `App.queueRevision.test.tsx` "ruling R2", `revisionPollHeld`'s matrix, `test_a_held_read_leaves_a_completed_job_for_the_read_that_may_reload` |
| V2 | R3 | The prompt scan disagrees with the renderer in both directions | 2bdb6dfd81 | All four named cases failed: `test_what_the_renderer_shows_as_text_or_a_web_link_stays_eligible`, `test_what_the_renderer_resolves_is_still_kept_for_the_desktop`, `test_an_escape_changes_only_the_delimiter_it_escapes` |
| V3 | | An owed bump can be paid on the wrong vault and lost | b9e7c8f33f | A's debt was paid on B: `test_an_owed_bump_belongs_to_its_vault`, `test_two_vaults_owe_separately_and_a_failed_retry_stays_owed` |

**V1.** `back` no longer calls `notifyQueueChanged`. A return does the immediate token read and owes a session read; a refetch needs `changed` or `snapshot.reloaded`. This is the reverse of F4 above. F4's concern is met by the session read on return and by the owed bump. A host that dies owing one is M2's: the host bumps once at start, so the token moves (recorded, not built).

**V1b.** `revisionPollHeld` decides the hold, and `get_queue_revision` gains `holdReload` (default false; declared, because `ParamsModel` forbids extras). The Rust command becomes a passthrough, since it used to send a fixed empty object. While held, the read leaves a completed job owed and a change is remembered. The hold lifting reads at once, and only a read that was free to reload pays what was remembered, so a held change and a held reload are one refetch and it runs after the reload. A read in flight when the hold lifts is followed by one that may reload; a failed read keeps the debt for the next tick.

Three readings the brief did not settle, reviewed and accepted by the orchestrator (R2 as amended, R5):

1. **Feedback and block review hold.** They replace `TodayScreen` on the Today tab, so the hold lifts only at `todayStage` queue. This overrides the earlier note that the feedback stage is not held.
2. **The simple shell's Today lifts it, though main had no poll there.** Main's only `getQueueRevision` caller was the classic `TodayScreen`. This is the one desktop difference kept on purpose, R5: a real revision change or a completed reload job refreshes the simple Today, and an idle token rebuilds nothing.
3. **The simple shell's Start tab counts as Today** (it renders `TodayPlace`); the classic shell's Start is its own screen and holds.

A golden-path run also holds, as a body-replacing overlay. Command overlays (Ask, Settings, the inspector, repair) sit over a list that stays mounted, and do not hold, as on main.

**V2.** Under R3 this is the last round on the scan's agreement with the renderer; any further disagreement is Low. A protocol-relative link is remote. GFM footnote definition lines and references go before the parse (a definition holding a real image is Low). `llpdf:` is read on rendered link and image targets and raw HTML, not as a substring, so the old pin of bare prose as a link went. The math strip keeps a backslash escape, so `\$5` opens no math and `\\$x$` still does. The quick exit stays: a target or HTML needs `[` or `<`. No new parser or dependency.

**V3.** `SidecarContext.host_bumps_owed` is a set of `vault_root`. A host request pays only the current vault's and clears only that one; a failed retry stays owed and never fails the request.

**Item 5 of the verify, the cost of a return, is answered by V1:** no rebuild, so none of the slates, offers, router decisions or background starts it listed. R4 keeps the successor question for M2.

**Gate for this step:** `test_device_eligibility`, `test_host_queue_revision`, `test_request_origin`, `test_desktop_rpc_contract`, `test_sidecar_contract`, `test_question_queue`: 294 passed, 5 skipped. Durability lane on the first five: 200 passed. Vitest `useQueueRevisionPoll.test.tsx`, `App.queueRevision.test.tsx`, `src/screens/TodayScreen*`: 65 passed; every `src/app/App*` file also run. `npm run typecheck` clean. `cargo check` clean, because `commands.rs` changed.

## Scoped Sol review of step 0 (job `20261103-044532-744Tsp`)

Verdict NOT CLEAN on one finding, ruled Low and not fixed; V1, V1b, V2 and V3 each pass, with no other new finding in `db63ec8ec3..27497a7340`.

| Id | Sol's severity | Finding | Verdict |
|---|---|---|---|
| 1 | Medium | `commands.rs`: the passthrough makes `input` mandatory, so an older `invoke("get_queue_revision")` with no input fails before Python and its poll silently stops | **Low, not fixed (ruling R6):** the frontend and the shell ship together in one app, and the one caller sends input |

**The question it was asked: keep the simple shell's freshness?** It recommended keeping it, as a freshness correction, and the orchestrator ruled so (R5). It found no self-sustaining loop: follow-up and placement bumps settle, plan boundaries persist their decisions, and prefetch and AD preparation do not bump this token. The cost it measured: an unchanged idle token gives 0 poll-driven rebuilds an hour; continuous genuine changes at the 3 s cadence could reach 1,200 invalidation cycles an hour (about 2,400 scheduler builds with the full list open), which needs work landing throughout the hour. A rebuild on such a change can start the existing background work, under its existing switches and budgets, so a refetch is not a free read. Refreshed rows can move under the full list's keyboard selection, on genuine changes only; main's file watcher already allowed that. Main had a real database-only gap (a Reader follow-up's new check stayed stale on the simple Today until something else refreshed), though newly authored YAML already reached it through the file watcher.
