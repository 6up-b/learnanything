# Mobile M2a: Codex review

Stage `mobile-m2a`, branch `mobile/m2a`. Review job `20261103-133433-p2VrYU` (gpt-6.1-sol): 2 High, 6 Medium, 1 Low. Each was reproduced with a failing test first; F8 was then rejected on its reasoning. The record of the stage is `mobile-m2a.md`.

## Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Adopting a desktop draft drops its assistance count | Fixed | `6b3460744c`, `ebeb12e297` | `App.test.tsx` "F1" (3), `attemptType.test.ts`; `test_mobile_handoff.py::test_a_desktop_hinted_draft_adopted_by_the_phone_stays_assisted_evidence` (recorded count, type and `eligible_for_certification` false) and `::test_a_draft_whose_count_is_dropped_certifies…` (the harm, on the server's side) |
| F2 | High | A lost response is treated as permission to create another attempt | Fixed | `6b3460744c` | `App.test.tsx` "F2" (8): running, recorded, never received, failed, status unreachable, the transport's own failure, the request stored before it is sent |
| F3 | Medium | Reopening the app makes a saved submission conflict with itself | Fixed | `6b3460744c` | `App.test.tsx` "F3" (2): latency 42 and the candidate survive a reopen, `toEqual` on the whole request; with the phone's copy gone a failed key is not reused |
| F4 | Medium | Taking a session back retains the phone's stale editor and key | Fixed | `6b3460744c` | `App.test.tsx` "F4": a new editor on the checkpoint's answer, key and count; no write from the old one |
| F5 | Medium | Ordinary navigation discards the current draft | Fixed | `6b3460744c` | `App.test.tsx` "F5" (7): Capture and back, Back and reopen, a failed flush resent, the checkpoint read when the phone has no copy, another item's checkpoint, a skip, a grading outage read while waiting |
| F6 | Medium | Gateway errors bypass the cached app shell | Fixed | `6b3460744c` | `sw.test.ts`: 502, 503 and 504 open the cached shell; 401, 403 and 404 stand; no shell cached keeps the gateway's answer |
| F7 | Medium | Exhausted terminal-write retries leave a job running forever | Fixed | `ebeb12e297`, `dce9dd1fdc` | `test_mobile_jobs.py::test_a_terminal_write_that_keeps_failing_is_paid_without_a_restart`, `::test_a_terminal_failure_that_cannot_be_written_is_read_as_failed` |
| F8 | Medium | Phone serving changes have no algorithm successor | **Rejected** | `dce9dd1fdc` (pin and wording) | Below |
| F9 | Low | The reported 202 share excludes failed submits | Fixed | `ebeb12e297` | `test_mobile_handoff.py::test_the_report_counts_a_failed_submit_in_the_share_of_202` |

Run against the sources from before the fixes, 21 of the 98 PWA tests fail, and the two runtime tests and the report test failed before their fix (`running` where `completed` belongs; 0.5 where 1/11 belongs).

## What changed

- **The phone's copy of a question (F2, F3, F5).** `store/sessionCache.ts` holds the answer, the key, the draft's help, the request as sent and what is known of how it ended. It is written on every change, and the request is written before it is sent.
- **One rule for a key (F2).** The outcome of a request is `none`, `failed` (the host said so) or `unknown`. An unknown outcome is settled with `GET /api/v1/submissions/{id}` before anything else goes: completed opens the feedback, accepted or running waits, and an unreachable host sends nothing. A key is replaced at the submit, and only when the job is known to have failed and the answer changed, or its request is gone. A key the host never saw keeps serving, so a late copy of the old request meets a typed conflict and not a second grade. `edit` no longer mints anything.
- **Which errors say how it ended.** None, since the re-review below. This round read anything typed except `desktop_offline` and `internal` as an end, and that was F2's reopening.
- **Help on an adopted draft (F1).** `DraftAssist` carries the checkpoint's authored count, `pageSeen`, `hintSeen`, the first-hint marker and the plan presentation. A save sends the count, because each save replaces it, and the flags, because they live under the key. A submit sends the desktop's `answerHints`, `authoredHints` and `bookCounted`, and `phoneAttemptType` takes the desktop's hint branch. Help with no answer yet also reopens the question.
- **Taking back (F4).** The next view is worked out first, then the session and the view are set in one step, so the old question never renders under the new owner. An adoption drops the phone's copies, and the owner generation is in the question's React key.
- **Navigation (F5).** A question flushes on unmount, except after a skip or a settled submit, and a failed save stays dirty. Today restores from the phone's copy, then the checkpoint's draft for that item. Capture now sits over the practice side instead of replacing it, so an open question keeps its editor, its serve and a submit under way.
- **The service worker (F6).** Any 5xx from Serve opens the cached shell. A 4xx stands.
- **Owed terminal writes (F7).** A job whose row could not be written after its retries stays in memory; `job_status`, `submission_status` and `/rpc`'s read of a coalesced retry answer from there, and a background thread retries every 5 s until it is paid. A last try runs at stop, and whatever is left the next start recovers from the row, as before.
- **The report (F9).** The denominator is every logged submit response. `submit_responses` gives the total, the 200s, the 202s and the failures, so the share cannot hide them.
- **Beyond a finding, because F2 leads there more often.** The waiting view keeps waiting through a lost desktop instead of dropping to Today, and a grading outage read from afar shows the phone's own message, not "Grade your answer". The symbol bar is disabled while the question is frozen.

## F8, rejected

The finding asks for a successor with version gates covering the phone's filter and head policy. It does not hold, for three reasons.

1. **`head_served` is not a serving policy.** `publish_offer` passes it only to `build_today_offer_decision`, which writes the decision row. It reorders nothing and filters nothing. The finding's "phone-specific head policy" is the log's account of a list the phone shows head first.
2. **Gating it on the switch would damage logged decision data.** With the filter off the phone still shows its head first and "Next" still opens it. Logging `full_list` and `not_served` for that would record a list the learner picked from when it served one. `test_mobile_rpc.py::test_the_kill_switch_takes_the_filter_off_and_the_log_still_says_what_the_phone_showed` pins the switch-off row.
3. **The filter has no predecessor code path to keep.** The 2026-10-17 playbook rule asks that below a tag, or with the switch off, every serve path keeps the predecessor's code. The only new serve path here is a phone's: below this stage's host no origin exists, so no phone was ever served, and the desktop's path takes no new branch at a None origin. A tag below which a phone goes unfiltered would describe a state no vault was in. This is R4's question, decided at M2's landing as R4 asks (`mobile-m2a.md` §1 item 7), and the filter already has its kill switch.

What the finding did get right is the wording: `mobile-m2a.md` §1 item 7 and the spec's §9.9 read as if the switch covered everything, and they now say it governs the filter only. **The successor decision is flagged for the owner**, since it was the stage's reading of R4 and the owner may overrule it at the checkpoint.

## Claims that did not hold

| Claim | Now |
|---|---|
| "The PWA resends the first request's fields exactly" | True across a reopen too (F3) |
| An edit follows a terminal failure that "wrote nothing" | A key is freed only by a known failure (F2) |
| "The handoff carries the draft and submission ID" | True on the same item, and the help comes too (F1, F4) |
| The cached shell covers backend unavailability | Covers a 5xx from Serve (F6) |
| `practice.device_eligibility_enabled` supplies the serving rollback | Reworded: it is the filter's switch, and the log is not a serving change (F8) |

The spec's §6.3 note and §9.9 and the record's §1 item 7, §2 and §3 are amended to match.

## Limits left

- An adopted draft's *earlier on this question* opening counts only under its own key; the phone is never told of it (`mobile-m2a.md` §3 item 7).
- All of this is jsdom against a fake host. A4 (a real phone, Safari, a killed app) remains the owner's and unverified, including `localStorage` surviving on iOS. If it does not survive, a reopened draft falls back to the checkpoint and a failed key is replaced rather than retried.
- F7's debt lives in memory, so a host that dies owing it relies on restart recovery, as before.

## Gate

No full suite, by the owner's rule of 2026-10-17; the landing gate runs it. Tree at `dce9dd1fdc` plus the regenerated catalog committed with this record.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | Done |
| `uv run lint-imports --no-cache` (isolated env) | 42 kept, 0 broken |
| Targeted pytest, `-n 6`, memory-capped | **881 passed** |
| Durability: `-m durability --durable-sqlite` on `test_mobile_jobs.py`, `test_mobile_two_process.py`, `test_mobile_handoff.py`; then `--durable-sqlite` on all of `test_mobile_jobs.py`, `test_mobile_handoff.py` | 1 passed; 49 passed |
| `apps/learnloop-mobile`: `npm install`, `npm run typecheck` | Pass |
| `apps/learnloop-mobile`: vitest (all 6 files), `--maxWorkers=4` | **98 passed** |
| `apps/learnloop-mobile`: `npm run build` | Built |
| `apps/learnloop-tauri` (not changed; the phone imports from it): `npm install`, `npm run typecheck`, `npm run frontend:build` | Pass, built |
| `module_generate.py`, `module_validate.py` | 1158 notes; PASS, links 38211/38211 |

Not run, because nothing under them changed: `cargo check` (no `src-tauri` change), the DB reference scripts (no schema change), desktop vitest (no desktop file changed).

Targeted pytest files: `test_architecture`, `test_capture_desktop`, `test_capture_domain`, `test_capture_originals_race`, `test_capture_route_recovery`, `test_codex_lockdown_round2`, `test_codex_lockdown_round3`, `test_compare_sources_keep`, `test_deliverable_rpcs`, `test_e0_isolation`, `test_lp_claim_fixes_rereview`, `test_mobile_allowlist`, `test_mobile_doctor`, `test_mobile_handoff`, `test_mobile_host_auth`, `test_mobile_host_coexistence`, `test_mobile_jobs`, `test_mobile_pairing`, `test_mobile_rpc`, `test_mobile_two_process`, `test_notes_linked`, `test_public_tip_guards`, `test_reader_ca1_as_printed`, `test_reader_ca5_also_in_books`, `test_section_coverage_rpcs`.

No model or paid calls; synthetic vaults only.

## Re-review

Job `20261103-140335-Uvq2Ac` (gpt-6.1-sol): F1 confirmed fixed, F2 reopened, one new Medium (F10). Verdict REOPENED. Both were reproduced through the real `App` and transport first: of the 22 new tests, 21 fail on the sources before these fixes. The one that passes is the skip of a job the host never took, which has nothing to catch.

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Adopted assistance lost | Confirmed fixed earlier | `6b3460744c`, `ebeb12e297` | No change this round |
| F2 | High | Typed errors treated as a job's end, so a key is replaced with no status read | Fixed | `3120775412` | `App.test.tsx` "F2, re-review" (18): host_busy after four requests, running and finished; five other typed errors; a typed error with no job keeps the key; a grading outage read back first; `submission_conflict` running, finished, failed; a refused status read sends nothing; the stored outcome; a skip over an unsettled key (4) |
| F10 | Medium | A failed Skip disables draft saving | Fixed | `3120775412` | `App.test.tsx` "F10" (4): a refused skip saves at once and keeps the answer; once only; a failed save is resent on leaving; nothing saves during a skip, and one that lands puts nothing back |

### What changed

- **F2: only the status read settles a key.** `saysHowItEnded` is gone. Every send starts `unknown`, and its own error leaves it there, typed or not. From the phone a job's end and a refusal before any job look the same. So `GET /api/v1/submissions/{id}` is the only thing that sets `failed` or `none`, and a key is replaced only after `failed`. A retry after a grading outage costs one more GET and one more draft save. The request sent is unchanged.
- **F2: `submission_conflict`.** It no longer frees the key. The request just refused is dropped from the phone's copy, since it could only conflict again. So a running job is waited for, a finished one opens its feedback, and a failed one takes a new key even for the same answer.
- **F10.** `onSkipped` now returns whether the host recorded the skip. While a skip is in flight no save goes out and the question's controls are disabled, so a double tap sends one skip. If it lands, nothing is saved and the unmount flush stays quiet. If it is refused, the answer is saved at once, because the debounce will not fire again until the next edit. If that save fails too, the draft stays dirty and leaving sends it.
- **Beyond the finding, same class as F2.** A skip clears the phone's copy, which held the key, and reopening the question would then mint a new one over a job that might still land. So a skip over an `unknown` key reads the status first. A running job is waited for, a recorded attempt opens, and an unreadable status skips nothing. This adds one GET and only when the key is unsettled.

The spec's §6.3 note says the same, and the first round's "Which errors say how it ended" line above is marked superseded.

### Limits left

- A job that failed with a non-retryable error returns the same failure for the same answer, until the learner changes it. That behaviour is unchanged and was not in the findings.
- `submission_conflict` shows the host's own message, "This request id was used for a different request." It is rare and the next tap settles it, so the wording was left alone.
- This is still jsdom against a fake host, with A4 the owner's.

### Gate

No full suite, by the owner's rule of 2026-10-17. Tree at `3120775412`. Only `apps/learnloop-mobile` code changed, plus the spec's note and this record.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` (isolated env) | Done |
| `uv run lint-imports --no-cache` (isolated env) | 42 kept, 0 broken |
| Targeted pytest, `-n 6`, memory-capped | **522 passed** |
| `apps/learnloop-mobile`: `npm install`, `npm run typecheck` | Pass (exit 0) |
| `apps/learnloop-mobile`: vitest (all 6 files), `--maxWorkers=4` | **120 passed** (98 before, 22 new; `App.test.tsx` 70) |
| `apps/learnloop-mobile`: `npm run build` | Built |

Targeted pytest files: `test_mobile_allowlist`, `test_mobile_doctor`, `test_mobile_host_auth`, `test_mobile_jobs`, `test_mobile_rpc`, `test_mobile_handoff`, `test_public_tip_guards`. `test_mobile_allowlist` and `test_mobile_doctor` reference the phone app; the others pin the host contract the fix relies on (no server code changed).

Not run, because nothing under them changed: durability (no migration or DB code), `cargo check` (no `src-tauri` change), the DB reference scripts (no schema change), desktop vitest and build (no desktop file changed), the module catalog (no Python changed).

No model or paid calls; synthetic vaults only.

## Final verify, and landing step 0

Job `20261103-141659-Qx4lon` (gpt-6.1-sol): F1 and F10 confirmed fixed, F2 reopened a second time, one new Medium (F11). Verdict REOPENED. Under the stuck-loop rule (ruling R2 in `mobile-m2a.md`, "Landing onto main") the F2 fix moved to the server. Each fix below was reproduced first: 15 of the first 17 new pytest cases and 7 of 8 new vitest cases failed for F2, 14 of 14 for F11, and the report's test for the contest line.

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F2 | High | A job's `failed` didn't establish that no attempt committed | Fixed on the server | `cf6a6b0afb`, `49b6587ab7` | `test_mobile_jobs.py` after "ruling R2" (18 cases, fault injection through the real runtime); `App.test.tsx` "F2, final" (8 cases, the real App and transport) |
| F11 | Medium | A lost Skip reply restored the skipped draft | Fixed | `ed191bfe92` | `App.test.tsx` "F11" (14) |
| HTTPS port | Landing | The owner's patch on M2a's routes | Verified, pinned | `d7382c141d` | `test_mobile_https.py`: `/rpc` and `/app/*` at 443 and 8445, right Host and Origin accepted, another port refused |
| Contest line | Landing | A rate that is 0 by construction | Fixed | `16445def7a` | `test_mobile_handoff.py` |

### What changed

- **F2: `failed` now means no attempt committed.** `HostRuntime.submission_status` and `job_status` go through one read: for a submit, a receipt is `completed` with its result, and an attempt with no receipt is `running`, before anything the job's row says. `_run_job`'s failure path asks the same question before it writes: it writes `failed` only if no attempt committed, and a debt asks again before it pays. If that check itself can't be read, the waiter hears `running`, not `failed`.
- **F2: the re-drive.** A status read of a committed attempt queues one `recover_practice_submission` under the same key on the job worker. Never beside the job completing it (`_waiters`) or another recovery (`_redriving`), so one poll starts one at most and no polling starts none. The read itself still reads. The recovery goes through the job worker's `_dispatch` and writes the row through `_finish`, so F7's debt applies. It is a `host_mutation` now, so the desktop's token moves when it finishes; with no origin it does nothing new on the desktop.
- **F2: a completion that can't finish is `recorded`.** `submission_committed` from the handler, or three failed tries (`_REDRIVES_BEFORE_DELAYED`, a `keep` bound: it only decides how long a phone waits), makes the row `recorded`, with `attempt_id` on the status and `409 submission_committed` on `/rpc`. The attempt stands and its key is spent. The phone opens its feedback from every path that reads a status and from a polled job, acknowledging the key as a completed submit does. Later reads go on trying; healed, it becomes `completed`. A later host start retries a recorded job as well, up to `MAX_BOOTS`, so a completion nobody reads again isn't simply abandoned. Three boots of a committed attempt end `recorded`, not `host_restart_exhausted`.
- **F2: a schema change.** `recorded` is a new value in `mobile_jobs.state`'s CHECK, in the migration as it then stood (240, unlanded; 239 since the landing's renumbering). The head fixture picked it up at that renumbering (landing step 2), not in this commit, to keep a second 7 MB database out of the history.
- **F2: what a key's truth is.** For a job it is the key its handler answers under (B4's `answering_key`) and only for its item, so another device's reuse of a key for another item keeps its own `validation_error`. A status read with no job (a desktop's submission) uses the key as given, and re-drives it as the reading phone.
- **F2: client logic this made dead.** The second spelling of `attempt_id` and `terminalJob`. `saysHowItEnded` went last round. The phone keeps "a submit's own error leaves the key unknown": that isn't about a failed job, it's about a response that never came.
- **F11.** `onSkipped` returns `recorded`, `refused` or `unknown`. `refused` is any typed error but `internal`; no reply, a reply that isn't ours and `internal` are `unknown`. On `unknown` the phone writes nothing and reads the checkpoint: this item there means it didn't land, so the save goes out and a notice says so; anything else means it landed, so the copy goes and Today is next. If the read fails it says the desktop can't be reached and stays. `skipUnknown` is on the phone's copy, so Back writes nothing, and the next edit, Skip, Submit or reopening reads first. A second Skip sends nothing if the first landed.
- **HTTPS port.** No code change was needed: the host's Host and Origin checks, doctor and pairing already read `https_authority` and `base_url`, and the PWA is same-origin with `/app/`-relative URLs. The new tests pin that for M2a's own routes. The deploy command, the A list and the spec's commands now say `https_port`.
- **The report** said "no contest on the phone" for `phone_practice`; step 0b's R7 replaced that with the observed rate and a note.

### Limits left

- **A skip lost before it reached the host, with nothing in the checkpoint, reads as landed.** A draft that never reached the checkpoint leaves nothing to tell the two apart, so the phone drops its copy and goes to Today, and the item is still there. The learner had asked to discard that answer, so the copy going is what they wanted.
- **Under R2, a further settling case is Low** unless it realistically produces a second grade or a second attempt. A re-drive can't do either: recovery never grades, and it commits no attempt.
- **A successor-key attempt at `MAX_BOOTS`.** `recover_jobs` looks the attempt up by the request's key, with no sidecar in `capture`. A successor-key attempt reaching its third boot gets `failed` on the row, and the status read still says `running` or `recorded` from the attempt, then finishes it. Low.
- This is still jsdom against a fake host for the phone's half, with A4 the owner's; the host's half is the real runtime and ASGI app. The landing smoke's kill tests drive a real host process.

### Gate (step 0)

No full suite, by the owner's rule of 2026-10-17; it runs at landing step 4. Tree: this commit, on `mobile/m2a` with main's `42aeeec9ec` merged.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` (isolated env) | Done |
| `lint-imports --no-cache` | 42 kept, 0 broken |
| Every `test_mobile_*`, `test_public_tip_guards`, `test_architecture`, `test_host_queue_revision`, and the other files naming `recover_practice_submission` (`test_hint_telemetry`, `test_owner_capture_1025`, `test_sidecar_contract`), `-n 6`, memory-capped | **827 passed, 5 skipped** |
| Durability: `-m durability --durable-sqlite` on `test_mobile_two_process`, `test_mobile_host_coexistence`, `test_mobile_jobs`, `test_mobile_handoff`; then `--durable-sqlite` on all of them | 2 passed; 69 passed |
| `apps/learnloop-mobile`: `npm install`, `npm run typecheck` | Pass |
| `apps/learnloop-mobile`: vitest (all 6 files), `--maxWorkers=4` | **142 passed** (120 before, 22 new) |
| `apps/learnloop-mobile`: `npm run build` | Built |

No model or paid calls; synthetic vaults only.

## Scoped verify of step 0, and landing step 0b

Job `20261103-144839-1ikqpG` (scoped, on step 0): F2 closed. Two Mediums, fixed at landing with tests and no further Codex round (ruling R7), and one Low, recorded and not fixed. R6 is the orchestrator's own.

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| R6 | Landing | The root `.gitignore` is the owner's, with local edits | Done | `01b72f0d8b` | `git check-ignore`: with main's root file, `node_modules` and the built app weren't ignored; with `apps/learnloop-mobile/.gitignore` and `src/learnloop_mobile/static/.gitignore` they are. Root file equal to main's |
| V1 | Medium | New text lost after an unresolved Skip | Fixed | `de0d9a11c0` | `App.test.tsx` "F11 … and the read fails too" (4 new, 3 of them failing first; one more failing on the copy's new field) |
| V2 | Medium | The report hid a desktop contest of a phone attempt | Fixed | `cc6654de6b` | `test_mobile_handoff.py`: a contested phone attempt among two reads 0.5, and an uncontested one 0.0, each failing first |
| V3 | Low | The latency report omits a successor-key completion whose row says `failed` | Recorded (R7) | None | The `MAX_BOOTS` successor case in "Limits left" above. Status answers correctly; the row isn't repaired, so `submit_to_feedback_seconds` leaves that one submission out |

### What changed

- **V1.** The phone's copy counts the draft's revisions, and an unresolved skip records the revision it was sent at (`skipRevision`, which replaces last round's `skipUnknown`). A landed skip discards only that revision. If the learner has written since, the text stays on screen and on the phone. It becomes a fresh draft: a new key, no offer (that serve's went with the skip) and the draft's help kept. It is saved once the checkpoint has been read, or submitted under that key. A notice says so. The check runs after the read, because an edit can start one and the editor stays open during it. Skip again means all of it, so it moves the recorded revision up first.
- **V2.** `contest_rate_by_surface` is the observed rate by the attempt's surface, phone included, and `contest_note` says separately that the phone has no button. §9's row and `mobile-m2a.md` say the same.

Tests and gate for this round are the landing's: `mobile-m2a.md`, "Landing onto main".
