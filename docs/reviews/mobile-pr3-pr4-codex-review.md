# Mobile PR-3 and PR-4: Codex review and fixes

Stage `mobile-pr3-pr4`, branch `mobile/pr3-sweep-primary-only` in `learnanything-merge2`. Codex review job
`20261027-123723-hN2i52` (gpt-6.1-sol). Codex worked from source traces only: the shared test lock was held, so it ran
no tests. The implementer record is `docs/reviews/mobile-pr3-pr4.md`.

This step adds the successor **mvp-0.36** (F4), with its kill switch `practice.attempt_keeps_content_state`. There is
no new migration and no new parameter. No model calls and no paid calls were made, and only synthetic vaults were used.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Skip can delete the adopting device's draft | fixed | `2fe25984e` | `test_a_skip_never_clears_the_draft_of_a_device_that_adopted_while_the_queue_was_built`, `test_a_skip_refuses_a_session_that_moved_and_came_back_while_the_queue_was_built` (both red on `3ace56123`: no error raised, the phone's draft cleared); control `test_the_owner_skips_as_before` |
| F2 | Medium | A stale replacement retry silently ends the caller's newer session | fixed | `2fe25984e` | `test_a_retried_replacement_never_ends_the_session_it_created` (red on `3ace56123`: the retry created C and ended B with its draft) |
| F3 | Medium | Ownership enforcement misses disclosure displays and hint mutations | fixed | `2fe25984e` | `test_every_session_scoped_write_from_the_old_owner_is_session_moved` now covers 13 writes. Red on `3ace56123` for `record_self_grade_disclosure` with a display id, `practice.request_hint`, `practice.record_hint_reveal` and `practice.answer_discriminating`. The freeze branch passed on the base too, through the patch |
| F4 | Medium | The attempt-state change alters serving without a successor or kill switch | fixed | `72208d5a5`, `f25a8f169` | `tests/test_attempt_content_state_successor.py` (21 tests): the gate, serving at and below the tag, same-version rebuild at three settings, and the upgrade chain. `test_attempt_content_state_race.py` now runs at the tag and adds a below-tag control (the race returns) |

## F1: skip re-checks ownership where it writes

`skip_practice_item` still refuses early when another device owns the session, before it builds the queue. It keeps
the `owner_generation` it read. The writes then happen together:

- `publish_offer` takes a new argument, `alongside`. It runs first inside one `BEGIN IMMEDIATE` transaction that also
  commits the offer (`finalize_scheduler_offer`, or the empty-offer decision).
- The slow work stays outside that transaction: the queue build, the teach-back readiness probe and the router
  decision. So the write lock is never held across them.
- For a skip, `alongside` does two things. It calls `require_session_owner(…, expected_generation=g)`, then clears the
  checkpoint. A refusal rolls back the offer as well.

The generation check closes one more window. In it, the phone adopts the session, saves its own draft, and the desktop
adopts the session back. All of this happens while the desktop's queue is being built. The owner matches again, but
the checkpoint now holds the phone's draft, so the generation check refuses the skip.

Both tests make the interleaving real:

- they monkeypatch `practice.build_due_queue` to return the real queue;
- then a second `Repository` adopts the session and patches the checkpoint with `device_id=dev_phone`;
- then the skip resumes.

## F2: an explicit `replace` is validated first

`start_session_exclusive` now checks `replace` against the open sessions **before** the same-owner rule. Its
compare-and-swap is on the session id.

- **`replace` names no open session, and a session is open** (the caller's own included): the call raises
  `session_open_elsewhere` with the open session's snapshot and ends nothing. In Codex's scenario this means B keeps
  its draft, and no C is created. The phone re-reads the session and sees it owns B.
- **`replace` names the caller's own open session:** that session is replaced silently, as before.
- **Nothing is open:** a stale name ends nothing, so the start proceeds.

The spec says only that "a stale `replace` returns `session_open_elsewhere` again". This step uses the same code when
the open session is the caller's own, so the client has a single rule: re-read and ask. Spec §9.5 says so.

## F3: every acceptance boundary that writes

The following writes are now ownership-checked:

- **`record_self_grade_disclosure` with a `display_id`.** The ownership check, the pending-draft check and the
  reveal-row insert are one `atomic()`, so validation and insertion are atomic.
- **`practice.request_hint`.** The check runs at the job's acceptance, replacing the open-session check. Its ended and
  missing errors keep their codes and messages, and a job accepted before a handoff completes.
- **`practice.record_hint_reveal`.**
- **`practice.answer_discriminating`.**

`patch_checkpoint`'s `device_id` no longer has a default. Before this, `save_practice_draft`, the disclosure freeze and
the teach-back state writes all checked against the desktop by omission. That would have refused the owner's own
phone writes once PR-5 sets a request origin. Every caller now passes `request_device_id(ctx)`; the three teach-back
tests that patch directly pass `None`, the desktop.

**Still not ownership-checked:** the workbench, the tutor and Ask, the daily plan, and other session-keyed writes
outside practice. They need the same review before M2 (open question 2).

## F4: successor mvp-0.36 with a kill switch

Codex is right, and the playbook's 2026-10-17 rule applies: a change to which items are served is a successor even
when replay is unchanged. Without a concurrent writer, the attempt used to reopen a row the sync rule keeps closed
while its YAML is active, and the row stayed open until the next content sync. The affected rows are review-parked,
measurement-superseded, a microprobe, or a deactivation that replay keeps. `routine_withhold_reason` serves on
`inactive_state`.

I also looked for a non-versioned fix that would keep the predecessor's behaviour exactly when no other writer is
active, and found none that holds:

- a content-hash compare-and-swap misses a retire, because `practice_item_hash` has no status;
- a snapshot at acceptance leaves the window between the vault load and the acceptance;
- re-deciding with the sync rule misses the deactivations made outside that rule, from item authoring, probe
  lifecycle and causal coherence.

The change:

- **The tag.** `ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION = "mvp-0.36"`, appended to the chain, with
  `ATTEMPT_CONTENT_STATE_VERSIONS`. It is now `LATEST_ALGORITHM_VERSION`.
- **The kill switch.** `[practice] attempt_keeps_content_state = true` in the schema. It is a modelled default, left
  out of the decision-only template. The parameter registry classifies it `structural`/`operational`.
- **The gate.** `attempts.attempt_keeps_content_state(vault)` is true when the vault is at or after the tag and the
  switch is on. `apply_attempt` passes it to `record_attempt_outcome(keep_content_state=…)`.
  - When true, the attempt writes only its scheduling columns (`_record_attempt_practice_item_state`).
  - Otherwise it runs the predecessor's `_upsert_practice_item_state_record`, unchanged.
  - Replay (`replace_attempt_derived_outcome`) is untouched.
- **The upgrade.** `learnloop.attempt_content_state_upgrade` is the next journalled link: the predecessor's manifest,
  the projection activation, the registry refresh, then the journal and the publication last. It accepts mvp-0.35,
  or mvp-0.9 onwards through the chain.
  - The CLI and the desktop sidecar now install its `complete_interrupted_activation`, which hands mvp-0.35's journal
    down the chain.
  - `learnloop upgrade --to mvp-0.36`, and a bare upgrade, target it.
- **The defaults snapshots.** Every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry was recomputed (`defaults_fingerprint_for_version`).
  They moved only because the effective config gained the key, and the key is inert below the tag. mvp-0.36 has its
  own entry.
- **Version pins.** The tests that pin the latest tag or the version sets moved to include mvp-0.36. `test_attempt_write_order`
  hooks both state writers, because the basic vault is mvp-0.6, below the tag.
- **Docs.** The configuration and DB reference was regenerated, with a field description for the key and a leaf count
  of 1,065. Spec §9.5 and the record's §4 note the supersession.
- **Numbering.** Another stage (the learner-report successor) may mint mvp-0.36 first. In that case the landing
  renumbers this one after it: the constant, `PREDECESSOR` and its upgrade, the snapshot entry, and the pins.

The new tests:

- **The gate:** the tag and its switch, the predecessor, and the predecessor with the switch on, which stays inert.
- **Serving without a concurrent writer:**
  - at the tag, a closed row stays closed, its content hash stays the sync's, and the item stays out of serving (not
    `inactive_state`-served);
  - with the switch off, or at mvp-0.35, the row reopens and the item is served, exactly as the predecessor.
- **Same-version rebuild:** `rebuild_derived_state` reproduces the live row (active, hash and scheduling columns) at
  the tag, at the tag with the switch off, and at the predecessor.
- **The upgrade:**
  - it works from mvp-0.9, 0.33, 0.34 and 0.35, and a bare upgrade targets mvp-0.36;
  - it refuses mvp-0.8;
  - a journalled activation is completed by the next CLI command and by the upgrade itself;
  - a failure after the rename leaves the predecessor and no journal;
  - an mvp-0.35 journal is handed down the chain, then the tag activates.

**Effect on the owner's vaults:** none until they run `learnloop upgrade`. Below mvp-0.36 the race PR-4 closes is open,
as on main.

## Claims that did not hold (corrected)

- **"A stale `replace` gets `session_open_elsewhere` again":** it now holds in every case (F2).
- **"`record_self_grade_disclosure` is ownership-checked through the patch":** only the freeze was. The display branch
  is now checked too (F3).
- **"Every session-scoped write checks ownership":** the record and the spec now list exactly which writes are checked,
  and name the ones still open.
- **"No successor":** superseded by mvp-0.36 (F4). Record §4 carries the note.

## Gate (this step; the full suite runs once in the landing gate)

Every pytest run below ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at
`-n 6`, one at a time. The heavy runs also held `flock /tmp/learnloop-fullsuite.lock`. The reference scripts ran
under `env -i` with an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, all three created beforehand.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **36 kept, 0 broken** |
| `tests/test_session_ownership.py` (durability lane) | **27 passed** with the fix. **7 failed** with `3ace56123`'s sources restored (the red check for F1–F3) |
| `test_attempt_content_state_successor.py` + `test_attempt_content_state_race.py` + `test_attempt_write_order.py` | first run: **23 passed, 4 failed**. The 21 successor tests all passed; the 3 race tests and the write-order test failed because the basic vault is mvp-0.6, below the tag. After moving those vaults to the tag, adding the below-tag control and hooking both writers: **7 passed** |
| Version, upgrade and contract set (79 files: every test naming the chain, the latest tag, the snapshots, an upgrade or the activation journal; the parameter registry; architecture, table roles, desktop RPC contract, mobile allowlist, serializer snapshot, config refactor) | first run: **1,563 passed**, 12 skipped, 3 xfailed, **8 failed** (latest-tag pins). After the fix, those 12 files: **234 passed**, 12 skipped, 1 xfailed |
| DB and config reference: `db_generate_reference.py`, then `db_validate_reference.py` | **errors: []** (354 table notes, 1,065 config leaves) |
| Final targeted set, 408 files (`docs/reviews/artifacts/mobile-pr3-pr4-codex-fix-targeted-tests.txt`): the implementer's 374, plus the hint, queue, workbench-discriminate, teach-back and version/contract files | FINAL_RUN_RESULT |

No frontend, Tauri, migration or DB-schema change in this step, so no npm, vitest or cargo work.

## Open questions

1. **Successor numbering at landing.** If the learner-report successor (in `learnanything-ad1`) lands first, this
   becomes mvp-0.37 after it: the constant, the upgrade's `PREDECESSOR`, the snapshot entry, and the pins in the
   `tests/test_mvp0*_upgrade.py` family and the files above.
2. **Session-keyed writes outside practice.** The workbench, tutor and Ask, the daily plan, and the reader writes that
   carry a `session_id` are not ownership-checked yet. Should they be added in PR-5, alongside the request origin, or
   before M2?
3. **The stale-replace code.** This step reuses `session_open_elsewhere` for a stale `replace` even when the open
   session is the caller's own (F2). Does the owner want a distinct code, for example `session_replace_stale`? The
   record's open question 2 asks the same about a stale adopt.
