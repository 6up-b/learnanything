# Mobile PR-5, PR-6 and PR-7: request origin, device eligibility, desktop freshness

Stage `mobile-pr5-pr7`, branch `mobile/pr5-pr7` in `learnanything-merge2`, base `dac6ed96de` (migration head 238, latest
algorithm `mvp-0.43`). Spec: `docs/specs/spec_mobile_tailnet_v1.md` §3.3, §6.4, §6.5, §6.8, §9.5, G9, G11, G12; as-built
notes §9.6, §9.7, §9.8.

Scope: the three prerequisites, three commit groups in order. No host (M2) code and no phone UI. **No migration, no
algorithm successor, no new config key or parameter** at this record (the Codex review added one kill switch,
`practice.device_eligibility_enabled`, and moved the filter into the build; see `mobile-pr5-pr7-codex-review.md`): nothing the
desktop serves changed, and a None origin takes none of the new branches. No model calls and no paid calls; synthetic vaults only.

## Commits

| Commit | What |
|---|---|
| `c66dde3be0` | PR-5: `RequestOrigin`, `SidecarContext.request_origin` and `acting_as`, surfaces from the origin, `request_device_id` replaced |
| `d80ce2fc8a` | PR-6: `scheduling/device_eligibility.py`, applied at each door; the `adopt_session` RPC |
| `a500c7fab8` | PR-7: the bump on the shared handlers; the app-level poll; session-moved detection |
| `48806c6788` | catalogs regenerated (`desktop_validate` pins: 313 sources, 302 entry-reachable, 319 active) |
| (this record) | this record and the spec's as-built notes |

## 0. What moved since the spec was written

Checked at this base. Every citation for these three stages moved; the facts behind them held, except where noted.

| Spec citation | Now | Note |
|---|---|---|
| §6.8 `practice.py:528`, `:638` (`entry_surface` hard-coded) | `practice.py:1279` and `:1524` take it as a parameter (`submit_attempt_on`, `submit_dont_know_on`); written at `:1327`, `:1392`, `:1589`, `:1615` | RW2a split the RPCs from one shared body, so the workbench already names its own surface. The RPCs now pass the origin's |
| §6.8 `db/stores/collection.py:42`, `:77` | `:54` (`finalize_scheduler_offer`), `:154` (`bind_submission_offer`) | Same defaults |
| §6.8 `substrate/data_quality.py:78` | `:79` | Still the cohort key, so `phone_practice` needs no report change |
| §3.3 `TodayScreen.tsx:341-360` (the poll) | was `:424-449` on this base; removed here | Today's line count is 1,931, not 1,698. **New:** the simple shell's Today (`TodayPlace`) never polled at all, so the poll's old home covered only the classic shell |
| §3.3 `repositories.py:4621` | `:5443` (`queue_revision`), `:5453` (`bump_queue_revision`) | Attempts still do not bump it. About 30 other sites do, all conditional on real change (checked for a build that bumps every time; none) |
| §3.3 `migrations/117…sql:101` | unchanged | |
| §3.1 `queue.py:53-71` (`get_queue_revision`) | `queue.py:87` | Still reloads once per completed job. Its job read went through `list_batches`' views (changed here, §3) |
| §6.4 `practice.py:790-818` (skip) | `practice.py:1916` | PR-4 made the checkpoint clear and the offer one transaction (`publish_offer(alongside=)`), which is where the filter went |
| §6.4 `PracticeScreen.tsx:414-417` (probe contract) | `PracticeScreen.tsx:706` | Same rule: committing is the serve |
| §6.5 `sessions.py:41-47`, `:108-132`, `:135-141`, `repositories.py:9037-9049` | replaced by PR-4 (`db/stores/session_ownership.py`) | As §9.5 records |
| §3.1 `practice.py:687-737`, `completion_lock.py:27` | `practice.py:1196`; `completion_lock.py:27` | |
| §3.3 `practice.py:587-594` | `practice.py:1473` | The winner's receipt |
| §3.3 `db/connection.py:105-114`, `server.py:118-139` | `connection.py:107`, `:116`; `server.py:245` | |
| §3.3 `vault_watcher.rs:106` | `:107` | |
| §3.4 `client.ts:267-279`, `:280+`, `:300+` | `client.ts:394`, `:414`, cache section after it | The list of DTO imports grew; `call()` is unchanged |
| §3.4 `commands.rs:65-75` | `:65` | |
| §3.4 `components/ui.tsx:2-3`, `App.tsx:1` | unchanged | |
| §3.4 `FeedbackScreen.tsx:999` | `:1050` | Today 1,931, Practice 3,114, Feedback 3,400, AskOverlay 1,480 lines: §3.4's argument for separate phone screens is stronger |
| §3.1 `context.py:45-80` | `context.py:170` (`load`) | More primary duties since; §9.2 lists them |
| §3.1 `repositories.py:778` | `repositories.py:1067` | |
| §3.1 `pyproject.toml:123-129` | `:648` | |
| §3.3 `content/pipeline/runner.py:648-665` | `:797` | PR-3 |

**Methods the spec assumed and PR-4 did not build.** §4.5 lists `adopt_session` "(new, PR-4)" as an existing method; PR-4
built the repository operation and no RPC. PR-6 and PR-7 need the door, so it is registered here (§2), with no Tauri
command: the desktop's "adopt it back" is M2's, and a registered method with no command is denied to the phone by the
allowlist enumeration and invisible to the desktop.

**Things §6.8 and §6.4 could not name** are the tables below.

## 1. PR-5: request origin

`learnloop_sidecar/request_origin.py` holds `RequestOrigin(device_id, surface)`, frozen, with a non-blank device and the
one surface there is so far (`phone`). `SidecarContext.request_origin` defaults to None; `ctx.acting_as(origin)` sets it
for one call and restores it, also on a refusal. `ctx.origin_device_id` replaces `request_device_id` everywhere (the three
handler modules; the function is gone). One context belongs to one worker thread (§3.1), and no background job reads the
origin: the checks in `hints.py`, `figures.py` and the others run at acceptance.

**Every `entry_surface` and desktop default, and what was decided:**

| Site | Value | Decision |
|---|---|---|
| `submit_attempt` RPC (`practice.py`) | `desktop_practice` | **From the origin:** `phone_practice` |
| `submit_dont_know` RPC, and a stuck submit that becomes one | `desktop_practice` | **From the origin** |
| `_bind_offer` from a submit | store default | **From the origin** (`bind_surface`; the workbench's own still passes) |
| `save_practice_draft`'s `_bind_offer` | store default | **From the origin:** a draft binds first, so without this the intent would be `desktop_practice` |
| `record_learner_pick` (router) | the bind's surface | Follows the bind |
| `publish_offer`'s `finalize_scheduler_offer` | `desktop_queue` | **From the origin:** `phone_queue` |
| `get_today_queue`'s router `surface` | `desktop_queue` | **From the origin**; `full_list` under a serving plan, as on the desktop (see Open question 2) |
| skip's router `surface` | `skip_requeue` | Unchanged: it names the action; the receipt says which device |
| `teach_back.py:388` (`desktop_teach_back`) and its bind | as written | **Unchanged.** Not on any phone allowlist, and teach-back is ineligible until voice. `phone_teach_back` is voice teach-back's |
| `reader/workbench.py` `desktop_reader_workbench`, `desktop_practice_workbench` | as written | **Unchanged.** `workbench.*` is not on the allowlist; a phone answer goes through `submit_attempt`, whose fold still counts an open problem's help |
| `diagnosis/split/workbench_trace.py` `WORKBENCH_SURFACES` | as written | Unchanged, for the same reason |
| `teacher/checks.py` `ENTRY_SURFACE = "lesson"` | device-neutral | **Unchanged.** Lessons are not on the allowlist; M2+'s to split if lessons reach the phone |
| `content/authoring/rung_variants.py` `desktop_rung_variant` | as written | Unchanged: not allowlisted |
| `hints/report_adaptive.py` `ATTEMPT_SURFACES` (`practice`: `desktop_practice`) | as written | **Unchanged, on purpose.** "Avoidance" means not asking for a hint that was offered, and the M2 phone has no hint panel, so its attempts must not count there. An unfiltered report still counts them |
| `help_assists.surface` (hint rows) | `practice`, `workbench`, … | Not a device field; hint RPCs are not on the M2 allowlist |
| `goals/exam_session.py`, `exam_seeding.py`, `learner/recall_calibration.py`, `attempts/observations.py` | their own | Unchanged: not reachable from the phone |
| `cli/app.py`, `tui/screens/practice.py`, `sim/*` | their own | Unchanged: other hosts |
| `learnloop_mcp/server.py` | reads the column | Unchanged. The MCP runtime has its own surfaces and no `SidecarContext` origin |
| `learner_context.py`, `substrate/data_quality.py`, `adaptive_difficulty/*` | read or classify the column | No value lists; `phone_practice` is carried as is |

No CHECK constraint names a surface (`migrations/` searched), and `router_decisions.surface` is free text; its migration
comment lists the values and does not constrain them.

**No attribution from the owner (§6.8).** `test_an_attempts_device_is_the_request_never_the_sessions_owner` adopts a session
back between two attempts. `test_a_submit_accepted_before_a_handoff_keeps_the_phones_surface` adopts it during the phone's
grade, and the attempt stays `phone_practice` with the session already the desktop's.

## 2. PR-6: device eligibility

`ineligibility_reason(vault, item, device_class)` returns the first of `desktop_only_mode`, `multi_turn_teach_back`,
`error_hunt`, `laddered_stem`, `lesson_check`, `links_llpdf`, `embeds_image`, `references_item_asset`, for `phone` only.
`vault` is the spec's parameter and nothing reads it yet.

- **`DESKTOP_ONLY_MODES = {diagnostic_microprobe}`.** The modes in use are `short_answer`, `constructed_response`,
  `open_text`, `multiple_choice`, `diagnostic_probe`, `diagnostic_microprobe`, `teach_back` and the rest of
  `default_practice_mode_item_coverage`. A microprobe is one turn of a linked dialogue.
- **No pattern list for text cues.** "See the figure below" is eligible, and a test pins three such prompts. The module
  scans Markdown syntax only, after stripping code and math, because `$n![k](x)$` is a formula and `[0,1](x)` an interval.
  An item asset is a link with `file:` or `asset:`, or a relative target that is a path. The vault has no item-asset
  field, so this is what "references an item asset" can mean at this base.

**Item kinds landed since the spec:**

| Kind | Decision |
|---|---|
| Workbench steps | **Eligible.** A way of answering, not a kind of item. The item is ordinary text; an open problem stays on the desktop; a phone answer counts its carried help through the existing fold. Adopting with a steps draft does not touch the problem |
| Reader-imported exercises (`canonical_exercise`) | **Eligible.** Text prompt; a test pins it. A figure the book had and the transcript lost is `suspected_figure`'s case |
| Figures (RW5c, RW5d) | **No rule.** On-demand help beside an item, never its stimulus. An item whose prompt embeds one is `embeds_image` |
| A lesson's held check (`teacher_lesson_v1`) | **Ineligible (`lesson_check`).** The queue never offers it (`LESSON_HOLD`); the by-id doors now refuse it on the phone, because it belongs to its lesson |
| Delayed lesson checks (DL2 Check once) | **Eligible.** An ordinary vault item served cold, which is what the phone does |
| Choices checks | **Eligible** by the same token: their options are in the prompt's text |

**Where it applies.**

| Path (§6.4) | State |
|---|---|
| `get_today_queue`, before `finalize_scheduler_offer` | **Here**, inside the build since the Codex review (F1, F2; built in `publish_offer`): the receipt lists what the phone showed. `device_deferred_count` is absent for the desktop. The router gets `device_ineligible` under exclusions, and no outcome of the draw can hold a dropped item |
| The skip's rebuild | **Here**, by the same function |
| `open_queue_item`, `get_practice_item` | **Here:** `desktop_only`, with session and without (a read-only open on the phone would render what it cannot show) |
| `adopt_session` | **Here**, through PR-4's `current_item_ineligible` seam and the new RPC |
| `get_probe_contract` | **Here, beyond §6.4's list:** committing a presentation is a serve, so a stale client cannot commit one for an item it cannot show |
| Draft saves and submits | **Not doors,** as `serving.py` says of its other refusals: an answer in progress still saves. A phone cannot have composed one for an item it was refused |
| The plan RPCs | **M2.** Not on the allowlist. They cannot simply filter at the build: the plan is one stored record per day, so filtering there would hide items from the desktop. The by-id doors already refuse a step a plan names |
| An active probe contract not rendered, "continue it on the desktop" | **M2's client** |
| `suspected_figure` in the M2 report | **M2:** the report does not exist. Nothing here reads text cues, and how the report detects one is M2's choice given §6.4's warning about pattern lists |
| "N items waiting for the desktop" | **M2's UI**; the count is here |

**§6.4's implementation check is done.** The M2 prerequisites row asks for it.
`test_a_presentation_committed_on_the_phone_resumes_on_the_desktop`: the phone commits and serves a presentation and moves on;
a fresh desktop context adopts the session back, and `get_probe_contract` returns the same presentation, active, with no second
one. So `ineligibility_reason` does not exclude probe-capable items. One limit: a desktop that *starts a new session* instead of
adopting gets `probe_assigned_to_other_session`, the same as after any closed session today.

**The desktop's serving is unchanged (G9).** `device_filter` returns None for None, and the build then takes no new branch.
`test_the_desktop_queue_is_unfiltered_and_has_no_count` pins the reply's keys, the unfiltered list and the router's row.

## 3. PR-7: desktop freshness

**§6.5 and §9.5 on what belongs here.** §6.5 lists the desktop's adopt / start fresh prompt and the "continued on your phone"
banner under "Desktop changes (M2)", beside PR-7's poll, and §9.5 says the prompts for the two new codes are M2's. So this stage
builds the poll, the read on a window's return (no refetch of its own: ruling R1) and the session re-read, and detects the move; G12's "shows `session_moved`" is finished by
M2's banner.

**The bump.** `request_origin.host_mutation` on the handlers themselves, so M2's RPC and job workers have nothing to remember and
a test can drive it through a fake host origin. Job completion is `submit_attempt`, `submit_dont_know` and
`answer_grading_clarification` returning; session start, adopt, end and skip are theirs. It runs after the handler's commit, as
§3.3 says, with one exception to "a refusal doesn't bump": `submission_committed`, whose attempt is in. A failed bump is logged and
swallowed: the learner's write stands, the bump stays owed, on its own vault, for the host's next request there (Codex review F4, Sol verify V3). A window's return refetches nothing at an unchanged token (ruling R1). A host that dies owing one is M2's: it bumps once at start. Desktop writes have no origin and no bump.

**Polling cost.**

- One `get_queue_revision` per 3 s tick (the existing interval, a `keep` bound in the hook's comment). No refetch and no session read
  while the token holds. `App.queueRevision.test.tsx` counts an idle Today: five ticks, five token reads, no plan or count read.
- **One call in flight.** The sidecar pipe is serialized, so a tick during a 60 s grade waits; later ticks add nothing behind it.
- **Asleep while hidden,** reading the token and the session at once when the window comes back, with no refetch of its own (ruling R1). Being merely unfocused keeps polling (a window beside another).
- **`get_queue_revision` itself got cheaper,** because it now runs on every screen: it read every recent batch's full view
  (`list_batches`: dependencies, rung requests, `_batch_view`) plus one `get_ingest_job` per completed job. It now reads batches and
  jobs and checks in-memory state first (`IngestJobManager.completed_jobs_awaiting_reload`).
- **The first poll no longer refetches.** Today refetched on its first tick each mount, because that read may reload the vault. The
  RPC now says so (`reloaded: true`), which also closes a missed edge: a reload on any later tick used to change nothing the client
  could see. An idle start refetches nothing.

**Holding, as amended by ruling R2 (Sol verify V1b).** A revision change does two things, and only one is held. `notifyQueueChanged`
invalidates `TAG.queue`, and the App always mounts `get_daily_plan` under it, so an invalidation rebuilds the plan on the pipe, which can
start work and writes rows for a list nobody is looking at. `revisionPollHeld` lifts the hold only on Today's list: every other tab, Today's
practice, feedback and block review stages, and an exam, calibration session, lesson or golden-path run hold it. While held, a change is
remembered and the read asks for no reload (`holdReload`); on the return to Today one read reloads what is owed and one refetch pays for it
all. Reading the session is held for nothing, and its result goes to a separate store, never `setSession`, so the question's `key` and its
draft cannot change. `App.queueRevision.test.tsx` pins that the question screen is not remounted.

**Detection.** `session_snapshot` adds `ownerDeviceId`, `ownerLabel` and `ownerGeneration` once a session has left the desktop (owner set
or generation above 0). Absent reads as the desktop at generation 0, so a desktop session's reply is byte-identical and the serializer
snapshot is untouched; M2's phone reads the generation it adopts with from the same place. `useSessionMoved()` holds `{sessionId, reason:
adopted | ended, ownerLabel, ownerGeneration}`, cleared when the session changes or comes back. A write the desktop makes meanwhile is
refused by the sidecar with `session_moved` (PR-4), which the desktop shows as an error until M2's banner; nothing can reach that before
the host exists.

## 4. Persisted and served meaning

No successor and no migration. With no origin: `publish_offer` drops nothing and adds no key; the surfaces are the same strings; the session
reply is unchanged; no bump runs. `get_queue_revision` is the one desktop RPC whose work changed, and only by what it reads, plus an optional
key when it reloaded and an optional `holdReload` field (ruling R2). Removing Today's first-tick refetch changes when a refetch runs, not what is served. No config key, parameter or
model constant was added; `REVISION_POLL_MS` is the old poll's interval, and `DRAFT_PREVIEW_CHARS` is PR-4's.

## 5. Gate (this step; the full suite runs once in the landing gate)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, pytest at `-n 6`
at most, one at a time; `lint-imports` and the catalog scripts under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **42 kept, 0 broken** |
| New files while building: `test_request_origin` (with `test_session_ownership`: 110), `test_device_eligibility` (47), `test_host_queue_revision` (13, with `test_ingest_jobs`: 39) | all passed |
| **Targeted set**, 191 files, `docs/reviews/artifacts/mobile-pr5-pr7-targeted-tests.txt`: every test file naming a changed function or module (`publish_offer`, skip, `get_today_queue`, `open_queue_item`, `get_practice_item`, `get_probe_contract`, start, end, adopt, draft, the submits, clarification, `queue_revision`, `session_snapshot`, `get_session`, checkpoints, teach-back, self-grade disclosure, `METHOD_REGISTRY`, the offer stores) and the contract set present (architecture, CLI help snapshot, desktop RPC contract, serializer snapshot, sidecar contract, mobile allowlist, table roles, tracked fixture databases, coordinated migrations, module catalog inventory, public tip guards, secondary attach, host coexistence, ingest jobs, session ownership) | **4,270 passed, 35 skipped, 0 failed** in 12 min 13 s |
| Mobile suite with the extra: `test_mobile_allowlist`, `_host_auth`, `_capture`, `_doctor`, `_pairing`, `_host_coexistence`, `_shortcuts`, `test_architecture`, `test_request_origin` | **504 passed**, none skipped |
| Durability lane (`-m durability`): the three new files, `test_session_ownership`, `_migration`, `test_attempt_content_state_race`, `test_secondary_attach`, `test_mobile_host_coexistence`, `test_synthesis_sweep_primary_only` | **181 passed** |
| `npm install`, `npm run typecheck` | clean |
| vitest `src/app/`, `src/api/`, `src/screens/TodayScreen*`, `src/screens/today` (37 files, including the two new) | **322 passed** |
| `npm run frontend:build` | ok |
| `desktop_generate`, `module_generate`, `desktop_validate`, `module_validate` | regenerated (313 TS notes, 1,156 module notes); valid |
| `cargo check` | not run: nothing under `src-tauri` changed |
| DB reference scripts | not run: no schema change |

**Not run here, by the owner's rule:** the full suite, the whole durability lane, the whole vitest run.

## 6. Open questions and notes for M2

1. **A `limit` cuts before the phone's filter.** Closed by the Codex review (F2): the filter is inside the build, so the cut falls among items the phone can answer.
2. **`full_list` on the phone.** Under a serving plan `today_head_served` is False, so a phone's Today offer logs `full_list` and every bind as a
   learner pick. If M2a's phone shows the queue rather than the plan, its head is served and this should follow the origin. `daily_plan.py` says
   M2a will show the plan through allowlisted RPCs, and §4.5 does not list them: M2 has to decide, and the plan's stored record is shared (§2).
3. **`suspected_figure`.** §6.4 says it is logged in M2's report and warns against pattern lists. How it is detected without one (a word search
   limited to the report, a learner's "this needs a figure", a judged pass) is M2's.
4. **A retried mutation bumps again.** A cached submit, a retried adopt or a second end re-bump: one extra refetch on the desktop, harmless. Not worth a
   check on each path.
5. **Focus events under WebKitGTK and Hyprland** were not exercised (no GUI runs here): `focus` and `visibilitychange` are DOM events, and the 3 s tick
   covers a window that reports neither, so the worst case is a 3 s delay.
