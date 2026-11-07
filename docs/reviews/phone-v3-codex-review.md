# Phone v2, stage V3: Codex review and its fixes

**Stage:** `docs/reviews/phone-v2-v3-probes.md` (branch `phone/v3-probes`). **Reviewed tip:** `2e91909c72` (gpt-6.1-sol; job `20261107-021618-i27TXx`). The reviewer's own run could not start its tests (`systemd-run --user --scope`: "Operation not permitted" on its user bus), so its findings were traced from source. Each was reproduced here first: the new tests were written and run against `2e91909c72`'s code, where the reproducing ones fail, and then pass on the fix.

## Findings

| Id | Severity | Title | Verdict | Commit | Test (fails on `2e91909c72`, passes on the fix) |
|---|---|---|---|---|---|
| F1 | High | A non-owner phone can burn the desktop's probe | **Fixed** | `0b1619dcdd` | `tests/test_mobile_v3_codex_review.py::test_f1_a_phone_that_doesnt_own_the_session_never_burns_the_desktops_ready_probe[get_practice_item, get_probe_contract, open_queue_item]` (base: no refusal; the phone's door burned the desktop's ready probe under `surface = phone`) |
| F2 | High | Desktop Next destroys an accepted phone answer's diagnostic presentation | **Fixed** | `0b1619dcdd` | `test_f2_the_desktops_next_keeps_a_phone_probe_whose_answer_is_being_graded` (base: the desktop's Next ended the presentation, so the phone's answer recorded with no `probe_presentation_id` and the workflow was `skipped`) |
| F3 | Medium | Cached V2 clients receive V3 serving semantics they cannot complete | **Fixed** | `0b1619dcdd` | `test_f3_a_v2_app_gets_v2s_doors_from_a_v3_host_and_burns_nothing`, `test_f3_a_v2_apps_plan_step_holds_a_generated_probe_for_the_desktop` (base: the V2 app's plan Next served the generated probe, and `followup_next` answered 200); vitest `src/api/http.test.ts` "says on every /rpc that this app answers probes" |

No finding was rejected. The positive controls in the same file pass on both trees: the owning phone still burns its own probe (`test_f1_the_owning_phone_still_burns_it_as_its_own`), the desktop's Next still moves past a phone-served probe with no answer on its way (`test_f2_with_no_answer_on_its_way_the_desktops_next_still_moves_past_the_phones_probe`), and the current app still gets V3's door (`test_f3_the_v3_app_says_it_answers_probes_and_gets_v3s_door`).

## What changed

### F1: ownership in the claim's transaction (`learnloop_sidecar/serving.py`, `handlers/sessions.py`, `handlers/practice.py`, `handlers/queue.py`)

- `refuse_generated_probe_door` takes `owned`, a check that runs first inside the transaction that claims the burn (`_claim_refusal` wraps `owned()` and `identity.claim_serve` in one `repository.atomic()`), so no adopt can commit between the check and the burn.
- `sessions.phone_claim_owner` builds it: for a phone with `phone_probes` on, `refuse_moved_session` on the named session; for the sessionless door (`open_queue_item`) the same function's pin (no other device owns the open session; V2 landing ruling R1's rule). None for the desktop and for a phone that serves no probe, so neither path changes (no transaction is added at a None origin).
- `get_probe_contract` under the phone also runs the check at the start of its admission transaction (the presentation it commits is the session owner's to answer). The PWA already shows `session_moved` from any call as the handoff.

### F2: a phone answer on its way is not abandoned (`handlers/daily_plan.py`, `learnloop/capture/jobs.py`)

- `_abandon_phone_served` skips a phone-served plan item whose answer the host accepted and has not finished (`capture.jobs.submission_in_flight`: an open `mobile_jobs` submit naming the item) or that has an answer since its serve. The presentation stays open and the held feedback stays held, so the phone's answer, when the job worker commits it, is the probe's observation and settles the workflow (`probe_answered`); the plan's reconcile then marks the item done and the desktop's next Next moves on.
- Meanwhile the desktop's Next resumes that step, as it resumes any plan item whose phone answer is still being graded, and its door refuses the phone's question (`generated_probe_closed`) until the answer commits. The learner's own Skip still abandons it (FG1 §4.2's explicit abandonment). A job that fails leaves the session's owner (the desktop) to abandon it at the next Next, as before, since no retry can be accepted from the phone after the handoff.
- The reviewer's "the desktop is the same at every version" point is answered by scope, not by a version gate: the abandonment reads and writes nothing in a vault with no phone burn, and only a phone at the tag makes one. After a rollback below the tag, abandoning a phone-served probe is still what keeps the desktop's Next from stranding on a question its door refuses. The stage record's wording was corrected (`phone-v2-v3-probes.md` §3).

### F3: probe capability negotiated per request (`learnloop_mobile/host.py`, `learnloop_mobile/runtime.py`, PWA `api/http.ts`)

- The V3 app sends `LearnLoop-Capabilities: phone_probes` on every `/rpc`. The host's `phone_probes` reaches a request only when its switch is on **and** the app said so (`MobileHost._client_probes`): otherwise `followup_next` answers `phone_probes_off`, a submit naming a presentation `validation_error`, and every short call and job runs under a V2 origin (`RequestOrigin.phone_probes` false): the plan step holds a generated probe for the desktop, every door answers `generated_probe_reserved`, nothing is burned.
- A long job runs with what its app said when this run accepted it (`HostRuntime._probes_said`). A job a restarted host picks up (another run's) runs as V2's unless it is a submit, whose only V3 meaning is naming a presentation, which the host admitted only from an app that said it answers probes.
- `GET /api/v1/meta` still reports the host's switch; the digest mismatch still offers *Reload*.
- `tests/mobile_host_helpers.Phone` sends the header by default (the current app); `without_capabilities()` is the cached V2 app.

## Gate (this step; the full suite runs once in the landing gate)

Run in the worktree. Every pytest, vitest and npm run went through `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`; pytest at `-n 6`, vitest at `--maxWorkers=4`; every Python or CLI call outside pytest under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`; `TMPDIR` outside the worktree. No paid or live call: every model is a fake.

| Lane | On | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, then `uv pip install --offline pypdfium2==5.14.0`; `npm install --prefer-offline` in `apps/learnloop-mobile` | ok |
| Import contracts | `lint-imports --no-cache` | **43 kept, 0 broken** |
| Reproduction on the base | `tests/test_mobile_v3_codex_review.py` with `2e91909c72`'s `src` first on the path (`-o pythonpath=`) | **7 failed** (F1 x3: no refusal; F2: presentation ended; F3 x3: the V2 app's door served the probe, its plan step served it, the header constant absent), 3 passed (the positive controls) |
| The fixes | `tests/test_mobile_v3_codex_review.py` | **10 passed** |
| Targeted set | 100 files: every `tests/test_mobile_*.py` and `tests/test_followup*.py`; every test file naming `refuse_generated_probe_door`, `_claim_refusal`, `refuse_moved_session`, `_abandon_phone_served`, `accept_job`, `start_job`, `mobile_jobs`, `call_short`, `HostRuntime`, `mobile_host_helpers`, `capture.jobs` or `RequestOrigin(`; the contract set (`test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_architecture`, `test_cli_help_snapshot`, `test_config_refactor` (defaults snapshot), `test_table_roles`, `test_registry_audit`, `test_module_catalog_inventory`, `test_public_tip_guards`), the display-label audit (`test_sidecar_measurement`, `test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`), the process-launch allowlist (`test_codex_lockdown_round3`), the frozen cycles (`test_codex_lockdown_frozen`), `test_session_ownership`, `test_probe_orchestration_remainder` | **1971 passed, 0 failed** (8 min) |
| Durability | `--durable-sqlite` on `test_mobile_v3_codex_review.py` and `test_mobile_v3_probes.py` (WAL, FULL: the claim's and the admission's transactions) | **21 passed** |
| Phone app | `npm run typecheck`; `npx vitest run --maxWorkers=4 src/api/http.test.ts src/api/timing.test.ts src/api/contract.test.ts`; `npm run build` | clean; **3 files, 29 passed**; built |
| Desktop app | no file under `apps/learnloop-tauri` changed | no desktop vitest, build or `cargo check` needed |
| References | no schema change (no migration); `module_validate.py` | PASS (1:1 coverage) |

**Test files run, for reading the landing gate against:** `review_fix_set.txt` in the stage's scratch directory (`/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/a22010cc-5149-4947-a2b8-247f18b8f1a0/scratchpad/phone-v3/`), reproducible from the targeted-set row above.

## Process notes

- Every source edit used the editor. One test (`test_f3_the_app_and_the_host_name_the_same_capability_header`) was appended to the new test file with a shell heredoc.
- The reproduction against `2e91909c72` ran the new test file with that commit's `src` (`git archive` into the stage's scratch directory, outside the worktree) first on the import path. One `python -c` that only printed a module's path (to confirm the base `src` was the one imported) ran outside `env -i`; it imported nothing that makes a call.
- Left for later, smallest way to finish: during the seconds a phone answer is being graded after a handoff, the desktop's PracticeScreen shows the door's generic refusal for that resumed step (`generated_probe_closed`; stage record §2 item 3). A typed desktop line for it, or a desktop step filter (stage record §9 question 1), would remove that window.

## Re-review

**Reviewed tip:** `4bf66282ef` (gpt-6.1-sol; job `20261107-024610-sP8ZIo`), verdict REOPENED on F1. As before, the reviewer traced source only (its user bus refused `systemd-run`, and a read-only filesystem stopped `uv`). F2 and F3 were confirmed fixed, with no new defects in the fix commits. The reopened F1 was reproduced here first: the new tests ran against `4bf66282ef`'s code in the worktree before the fix, and all six failed with no refusal (`DID NOT RAISE`).

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 (reopened) | High | `phone_claim_owner` discards the pin and generation `refuse_moved_session` returns, and a stale phone serve naming a session the desktop ended takes the sessionless fallback and burns the probe | **Fixed** | `fc0eb0cb95` | `tests/test_mobile_v3_codex_review.py`: `test_f1_reopened_a_stale_phone_serve_naming_a_session_the_desktop_ended_burns_nothing[get_practice_item, get_probe_contract]`, `test_f1_reopened_a_session_the_phone_ended_itself_is_refused_too`, `test_f1_reopened_a_handoff_and_back_between_the_check_and_the_claim_refuses_the_named_burn` (generation change), `test_f1_reopened_an_end_between_the_check_and_the_claim_refuses_the_named_burn`, `test_f1_reopened_a_sessionless_phone_door_keeps_the_session_it_started_against` (on `4bf66282ef`, each one burned the probe under `surface = phone` with no refusal) |
| F2 | High | Desktop Next destroys an accepted phone answer's presentation | Confirmed fixed by the reviewer | `0b1619dcdd` | no change |
| F3 | Medium | Cached V2 clients get V3 serving | Confirmed fixed by the reviewer | `0b1619dcdd` | no change |

No finding was rejected.

### What changed (`learnloop_sidecar/handlers/sessions.py`)

- `phone_claim_owner` pins what it will check when the door starts, and the claim's transaction (`serving._claim_refusal`) and the phone's probe admission (`get_probe_contract`) run that pin. It no longer calls `refuse_moved_session` again inside the transaction. The pin is only run where a burn or an admission commits, so a phone door that burns nothing (an ordinary item) is refused nothing new.
- **A named session** is pinned with its owner's generation and checked with `require_session_owner(require_open=True, expected_generation=pinned)`. If it ended since (the desktop adopted and ended it: `session_moved`; the phone ended it itself: the ended-session `validation_error` the desktop has always received), or if it moved, even to the desktop and back to the phone, it is refused and nothing is claimed. A named session never takes the sessionless fallback any more. A job accepted for the session (`accepted_session_id`) is checked against the owner its acceptance checked, as in `refuse_moved_session`.
- **A sessionless door** (`open_queue_item`) pins the open session it started against through `_pin_open_session`, which was factored out of `refuse_moved_session`'s sessionless branch with no change in behaviour (V2 landing ruling R1). A handoff and back before the claim now refuses the burn. Before, a fresh lookup at claim time found the phone's own session again and burned the probe.
- The desktop (a None origin) and a phone without `phone_probes` still get `None`: no check and no transaction, so both are unchanged. `refuse_moved_session` returns what it did before, for every caller.

### Gate (this step; the full suite runs once in the landing gate)

The rules were the same as above: every pytest run inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at `-n 6`; `lint-imports` under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`; `TMPDIR` outside the worktree. No paid or live call was made, and every model was a fake.

| Lane | On | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, then `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `lint-imports --no-cache` | **43 kept, 0 broken** |
| Reproduction on the base | the six new tests on `4bf66282ef`'s `src` (the worktree before the fix) | **6 failed** (`DID NOT RAISE`: each door burned the probe), 4 passed (the earlier F1 tests and the positive control) |
| The fix | `tests/test_mobile_v3_codex_review.py` | **16 passed** |
| Targeted set | 101 files, the first round's set plus every test file naming `phone_claim_owner` or `session_moved`: every `tests/test_mobile_*.py` and `tests/test_followup*.py`; every test file naming `refuse_generated_probe_door`, `_claim_refusal`, `refuse_moved_session`, `phone_claim_owner`, `_abandon_phone_served`, `accept_job`, `start_job`, `mobile_jobs`, `call_short`, `HostRuntime`, `mobile_host_helpers`, `capture.jobs`, `RequestOrigin(` or `session_moved`; the contract set (`test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_architecture`, `test_cli_help_snapshot`, `test_config_refactor` (defaults snapshot), `test_table_roles`, `test_registry_audit`, `test_module_catalog_inventory`, `test_public_tip_guards`), the display-label audit (`test_sidecar_measurement`, `test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`), the process-launch allowlist (`test_codex_lockdown_round3`), the frozen cycles (`test_codex_lockdown_frozen`), `test_session_ownership`, `test_probe_orchestration_remainder` | **1982 passed, 0 failed** (7 min 57 s) |
| Durability | `--durable-sqlite` on `test_mobile_v3_codex_review.py`, `test_mobile_v3_probes.py` and `test_session_ownership.py` (WAL, FULL: the claim's and the admission's transactions) | **54 passed** |
| Phone and desktop apps | no frontend file changed | no npm, vitest, build or `cargo check` needed |
| References | no schema change, no new module | none needed |

**Test files run, for reading the landing gate against:** `/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/a22010cc-5149-4947-a2b8-247f18b8f1a0/scratchpad/phone-v3/rereview_fix_set.txt`, which can be rebuilt from the targeted-set row above.

### Process notes

- Every edit to source and tests used the editor. The first version of one new test re-armed its injected handoff on the desktop's later open. That was a test bug, fixed by making the injection run once, and the code under test did not change.
- Nothing is left open from this round.
