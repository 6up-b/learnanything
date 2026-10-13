# Reader workbench RW1a: Codex review fixes (stage `rw1a-inquiry`)

Branch `reader/rw1a-inquiry`, worktree `learnanything-rw1a`. Review of the
stage at `b7e04b0b` (Codex job `20261013-050117-td7SEA`): twelve findings,
two High and ten Medium. All twelve reproduce and all twelve are fixed. In
four places the fix narrows or adapts the suggested one; each is explained
below. No finding was rejected. No model, Decider or embedding call was made,
and no money was spent: every test uses fakes.

Owner decisions in force (2026-10-12): spec defaults accepted, Codex
unrestrained on the subscription (estimated_only), the Decider is
`perplexity/pplx-decider-v1.1-27b` on OpenRouter, frictionless defaults
(honest labels, generous defaults, live changes behind kill switches).

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Passage checks expose ambient Codex tools to untrusted source text | Fixed | `842fd375` | `tests/test_reader_passage_check.py::test_the_passage_check_request_is_an_isolated_turn`, `::test_a_transport_that_cannot_isolate_the_passage_is_refused_before_any_request`, `::test_the_job_fails_closed_with_a_named_reason_when_isolation_is_unavailable` |
| F2 | High | The new paid check has no spend admission control | Fixed | `842fd375` | `test_reader_passage_check.py::test_a_metered_route_without_an_owner_price_makes_no_request`, `::test_a_metered_check_over_its_dollar_cap_makes_no_request`, `::test_an_exhausted_daily_budget_makes_no_request`, `::test_a_failed_call_is_receipted_and_counts_toward_the_daily_cap`, `::test_a_metered_check_is_one_admitted_physical_request_held_to_its_output_allowance`, `::test_codex_on_the_subscription_runs_without_a_price_and_is_estimated_only`, `::test_the_job_reports_a_refusal_as_its_error_code_and_sends_nothing` (2 cases), `::test_the_vaults_spend_settings_reach_the_check` |
| F3 | Medium | Concurrent requests violate the inquiry reuse key | Fixed | `842fd375` | `test_reader_passage_check.py::test_the_database_refuses_a_second_row_for_one_reuse_key`, `::test_overlapping_workers_make_one_model_call_and_one_row`, `::test_a_late_completion_never_replaces_the_check_the_learner_saw`, `::test_a_crashed_claim_is_recovered_by_its_own_job_at_once_and_by_others_after_its_lease`, `::test_a_crashed_claim_from_another_job_is_taken_over_after_its_lease`, `::test_a_second_request_while_one_is_live_joins_its_job` |
| F4 | Medium | Queued quick checks can remain pending indefinitely | Fixed | `842fd375` (sidecar), `d417dd9d` (Reader) | `ReaderScreen.review.test.tsx`: "a queued quick check that fails says why in place…", "a lost sidecar shows offline instead of waiting forever, and the check lands when it comes back", "a pending quick check can be cancelled…", "a check the model can't be reached for…"; `tests/test_reader_reconnect.py::test_the_quick_check_read_reports_its_durable_jobs_state` |
| F5 | Medium | The kill switch leaves an invisible return stack active | Fixed | `d417dd9d` | `ReaderScreen.review.test.tsx`: "with the switch off, a search into another passage of a source left earlier lands and is saved there" |
| F6 | Medium | Several specified detours still have no way back | Fixed (scope below) | `d417dd9d` | `ReaderScreen.review.test.tsx`: "a Guide 'worth a second look' passage is a detour: Alt+← restores the passage and the capture", "opening another book from its library card after leaving one leaves a way back" |
| F7 | Medium | Back/forward navigation inflates return rates above 100% | Fixed | `842fd375` (report), `d417dd9d` (Reader) | `returnStack.test.ts`: "a detour is returned once…"; `ReaderScreen.review.test.tsx`: "returning, walking forward and returning again records each detour's return once"; `tests/test_reader_report.py::test_a_detour_returned_to_again_counts_once_so_the_rate_never_exceeds_one`, `::test_a_return_whose_opening_is_outside_the_window_is_not_counted` |
| F8 | Medium | The workflow funnel omits the new model-backed action | Fixed (client-side records, see below) | `842fd375` (payload), `d417dd9d` (Reader) | `ReaderScreen.review.test.tsx`: the queued and completed records in "a lost sidecar shows offline…", the failure records in "…fails says why in place…", "…can be cancelled…" and "…can't be reached for…"; `tests/test_reader_report.py::test_the_passage_quick_check_is_a_model_backed_action_in_the_funnel`; `tests/test_reader_reconnect.py::test_a_landed_inquiry_check_names_its_model_and_prompt_version` |
| F9 | Medium | "Continue the dialogue" can attach to the wrong inquiry | Fixed | `d417dd9d` | `AskOverlay.reader.test.tsx`: "continuing a chosen question attaches to that inquiry, not the span's newest one (two roots on one span)", "Today's 'continue the dialogue' names the chosen reader question" |
| F10 | Medium | Switching to skim leaves an existing reconnect prompt visible | Fixed | `d417dd9d` | `ReaderScreen.review.test.tsx`: "choosing skim after the reconnect line appeared hides it in both places" |
| F11 | Medium | Self-check verdicts never reach `judgment_ledger` | Fixed | `842fd375` | `tests/test_reader_reconnect.py::test_each_self_check_verdict_is_a_learner_card_judgment_and_a_change_supersedes`, `::test_the_self_check_and_its_ledger_row_commit_together`; `::test_answering_and_self_checking_an_inquiry_check_is_formative` now allows exactly that one ledger row and still no evidence row |
| F12 | Medium | Learner-edited captures are labelled as verbatim source quotations | Fixed | `842fd375` (sidecar), `d417dd9d` (Reader) | `tests/test_reader_branches.py::test_an_edited_capture_keeps_the_sources_wording_apart_from_the_learners`, `::test_with_the_switch_off_an_edited_capture_changes_nothing`; `ReaderAskBranches.test.tsx`: "an edited capture shows the book's wording as the source…"; `ReaderScreen.review.test.tsx`: "an Ask about an edited capture keeps the book's wording apart from the learner's" |

`41b8ebd6` regenerates the DB and config references (the unique index, the
three new `[reader_inquiry]` fields, moved line citations; the prose leaf
count 756 → 759 in `Configuration.md` and `Database.md`). Validator errors:
`[]`.

### Reproductions on the original code (`b7e04b0b`)

| ID | What the original code did |
|---|---|
| F1 | A probe against the original service (`author_inquiry_quick_check` with a recording transport) printed `request.isolated = False`. |
| F2 | The same probe with a metered transport (`provider_type = "openai_compatible"`) and no price: **1 request sent**, no admission, no cap. |
| F3 | Two overlapping workers (worker A held inside its model call, worker B started meanwhile): **2 model calls, 2 rows** for one reuse key. |
| F4 | All four screen tests failed: the poll never passed the batch (`readerInquiryQuestion` called without `batchId`), two rejected polls left "writing a quick check" on screen, there was no `cancel` control, and an unreachable model recorded nothing. |
| F5 | Switched off, A → search into B → search into A at `span_spectral_worked`: the saved position was **`span_symmetric_prose`** (Codex's probe result, reproduced exactly). |
| F6 | Clicking a "Worth a second look" passage and opening Book B from its library card both left **no detour strip**. |
| F7 | Return, forward, return: **4 `detour_returned` rows for 2 openings**. The report: a detour returned three times gave `{"count": 3, "of": 1, "share": 3.0}`. |
| F8 | No `reader_job_queued` or `reader_job_completed` for a quick check (the screen tests above). The report test passed on the original code: the report counts whatever it is given; the omission was in the Reader, which the screen tests pin. |
| F9 | With roots A (chosen) and B (newer) on one span, the follow-up went out with **`parentExchangeId: "B"`**; `targetForDialogue` carried no question identity. |
| F10 | After choosing "skim quickly", **1 reconnect group remained** (the rail's). |
| F11 | `test_answering_and_self_checking_an_inquiry_check_is_formative` pinned an unchanged `judgment_ledger` count: no verdict was ever appended, and a changed verdict overwrote `self_check`. |
| F12 | The Ask about an edited capture sent only `selectionQuote: "My corrected wording"`, which history rendered under `SourceVoice` ("from the book"). |

The probe script for F1-F3 (scratchpad, not committed) used the new test
file's fake transport with the original service signature. Every new test was
then run against the fixes; the regression run is the gate below.

## What changed

**F1. The passage is an isolated turn.** `request_passage_check` passes
`isolated=True` to `execute_structured_operation`, which already refuses a
transport without `ISOLATED_TURN` before any request (`AIProviderUnavailable`).
On the Codex route this is the isolated permission profile (no files, shell,
network, connectors, MCP servers or vault). The job maps the refusal to the
error code `provider_unavailable`, which the Reader shows as "Couldn't reach
LearnLoop's model". The tests check the request the transport actually
received.

**F2. Spend admission before generation.** `reader_quick_check.PassageCheckSpend`
uses the Phase 1 framework (`learnloop.ai.spend.SpendBudget`, with
`subscription=` set from the client). Before anything is sent:
- **a daily count**: `[reader_inquiry] max_checks_per_day` (default 100),
  counted from the check's own root receipts (`owner_kind =
  reader_inquiry_check`) since UTC midnight. Receipts are written before the
  request, so failed calls count;
- **a metered route** (OpenRouter, an API key): `metered_price_per_million`
  (unset: refused, as the framework requires for an unknown price), the
  bounded estimate (prompt tokens plus the shared output-budget policy's
  allowance) held to `max_usd_per_check` (default $0.25), `single_request()`
  (one admitted request is the only physical request: no hidden retry or
  repair), and `generation_limit` at the reserved allowance. The charge is
  reconciled with reported usage, failed calls included;
- **Codex on the subscription**: no price is needed. The token and dollar
  caps are not enforced, and there is no physical-request bound (Slice A §5
  rule 6). Receipts carry `budget_json.billing = subscription`, `cost_basis =
  estimated_only`, and an `estimated_only` usage estimate (reported usage,
  else the planned estimate).

A refusal raises `PassageCheckRefused` with the reason `capped` or
`spend_refused`. The job fails with that reason as its error code, and the
Reader shows it in place (F4). The three fields are registered in
`parameter_registry` as structural spend bounds. All eight defaults
fingerprints were recomputed.

**F3. One check per reuse key.** Three layers:
- **a durable claim before the call**: `judgment_work_claims` (the shared
  work-claim table of migration 176, task `reader_inquiry_check`, owner = the
  ingest job id). A live claim held by another owner raises
  `InquiryCheckHeld` with no call made (the job completes with `held: true`;
  the Reader keeps polling the question). The same job re-run after a crash
  takes its claim back at once; another owner takes it after the 30-minute
  lease. A failed or refused call releases the claim;
- **fenced completion**: the row is inserted only while the claim still holds,
  in one transaction with the claim's completion. A worker fenced out returns
  the row already there, so a late completion never replaces the check the
  learner answered or dismissed;
- **the database**: migration 189's `idx_reader_authored_questions_inquiry`
  is now `UNIQUE`, and the scoped insert is `ON CONFLICT DO NOTHING`
  (returning the existing row). **Enqueueing** joins a live batch for the
  same root (`subject_id = reader_inquiry_check:<root>`, checked and inserted
  in one `BEGIN IMMEDIATE` transaction).

**F4. The queued check is watched to the end.** `reader.inquiry_question`
accepts the `batchId` that `reader.reconnect_answer` returned and reports
that job's state and error code (only for a job of this inquiry). The Reader
keeps the batch on the check and polls every 3 s:
- landed → the question;
- `failed` → `capped` (Today's quick check budget is used), `unreachable`
  (`provider_unavailable`), or `failed` with the reason in the learner's terms
  (a metered route with no price);
- `cancelled` → gone;
- two rejected polls in a row → "LearnLoop's background service isn't
  responding". The poll carries on, so the check lands when the sidecar comes
  back;
- 200 polls (10 minutes; the Codex turn timeout is 8) → failed (timeout).

Pending has **cancel**, through the existing `cancel_ingest_batch` (no new
RPC, no Rust change).

**F5. Switched off, no hidden stack.** `openSource` builds a return stack only
while `reader_inquiry` is on (read through a ref, since the callback is
declared before the switch). The saved-position effect pins to a root only
while it is on. Switched off, every RPC and the saved position behave as
before.

**F6. Detours with a way back.** In the Guide, the investigative jumps are
now peeks (a detour while `reader_inquiry` is on, a plain jump when off): a
passage worth a second look, a question's "show me the passage", "show the
most relevant passage first" and the "I don't understand" return. A request
result's passage in Notes is a peek too. Contents stays ordinary reading
navigation (no crumb). **Opening another book after leaving one**, whether
from a search hit or **its library card**, is a detour back to the passage
left. Reopening the same source, or the first open of a visit, is reading.
This withdraws deviation 6 and answers open question 1 of `rw1a-inquiry.md`
(both updated there).

**F7. A detour returns once.** The return stack records the detours already
walked back to their origin (`returned`). A return logs `detour_returned`
only for those not yet returned, so walking forward and back again adds
nothing. The report joins returns to the openings in its window by
`detour_id` and counts each detour's first return once. A return whose
opening lies before the window, or is unknown, is not counted, so the rate
never exceeds one.

**F8. The quick check in the funnel.** The Reader records `reader_job_queued`
when the job is queued (`job_kind = quick_check`, `job_id` = the batch, the
asking visit). It records `reader_job_completed` once when the wait ends.
That record carries the status (`completed`, `failed`, `cancelled`), the
failure reason (`capped`, `spend_refused`, `provider_unavailable`, `timeout`,
`offline`, …), the latency and model wait, the model and prompt version (the
inquiry payload now names both), the asking visit's id, and the learner's
activity during the wait. A request that never reached the queue (the model
unavailable, the call rejected) is recorded as queued and failed. The report
test drives these events through `reader.log_activity`.

**F9. The chosen inquiry continues.** `AskTarget.readerQuestionEventId`
carries the question Today's row names. The overlay attaches to that
question's own exchange, so the follow-up inherits its saved selection and
ancestors. If the question has no exchange on the source, the follow-up is a
new thread on the span. Without a named question, it uses the span's newest
exchange, as before.

**F10. Skim mutes at render time.** The rail's reconnect line checks `muted`
when it renders, as the inline one did. A line already shown goes in both
places when the learner switches to skim.

**F11. Self-checks in the ledger.** `self_checked` updates the row and appends
a `judgment_ledger` row in one transaction: task
`reader_quick_check_self_check`, judge `learner_card`, left = the authored
question, right = a hash of the response it judges, prompt version = the
check's. A changed verdict supersedes the previous one; the same verdict
appends nothing; ids derive from the transition, so a retry never appends
twice. Only ids and hashes are stored, never the learner's words. No
evidence, attempt, observation, mastery or FSRS row is written (the
table-count test still pins that).

**F12. An edited capture is the learner's wording.** With `reader_inquiry`
on, an Ask about an edited capture sends `selectionSourceQuote` (the source's
own wording) beside `selectionQuote` (the learner's, which the tutor reads as
before). `reader_answer_submitted` keeps it as `selection_source_quote_md`,
follow-ups inherit it, and `ask_history` returns it (null when unedited).
The thread shows the book's words under the source voice and the edit under
"› your edited capture". Switched off, nothing is sent or stored, and the
payloads are unchanged.

### Where a fix narrows or adapts the suggestion

1. **F3's claim reuses `judgment_work_claims`** instead of a new table (W13
   reuse before building). The table is generic (task, producer, prompt
   version, input hash, lease, epoch) and WORKFLOW, never replayed. Its
   `judgment_id` column holds the authored question's id for this task.
2. **Migration 189 was edited in place** (the index is now `UNIQUE`) rather
   than adding 190. The branch is unmerged and 189 is this stage's own, so
   renumbering at the merge is expected anyway. The head fixture was rebuilt
   as its README describes: main's `migration_head_183` with only 189
   applied, checkpointed, rollback journal, `integrity_check` ok,
   `foreign_key_check` clean. Its dump differs from the previous fixture only
   in the index and 189's `applied_at`. A copy already migrated to 189 (only
   `fixtures-local/probability-rw1a`) keeps the non-unique index, and the
   claim and fenced insert still hold there.
3. **F8 is recorded by the Reader**, as Ask and the exercise import already
   are, because the waiting measure (activity during the wait) and the
   asking visit are known only there. The durable job's outcome comes from
   the job itself (F4's status read). A wait the learner abandons by leaving
   the source records no outcome, so the report then shows queued greater
   than the sum of completed, failed and cancelled. That is honest, not
   inflated.
4. **The daily count applies to Codex too.** It is a logical-call count
   (100 a day), a runaway guard like `learner_text_gaps.max_calls_per_day`.
   It is not a physical-request, token or dollar bound, which the owner
   lifted for the subscription.

### Not changed (out of this stage's scope, recorded)

- The **section** quick check (`author_quick_check`, on `main` before RW1a)
  still has no spend admission or isolation. Applying them would change a
  pre-existing path (and break this stage's kill-switch parity, under which
  section checks are byte-identical). It belongs to the producer's owner;
  recorded as an open question below.
- No new Tauri command: nothing under `apps/learnloop-tauri/src-tauri`
  changed in this fix step (cancel reuses `cancel_ingest_batch`; the job
  state rides on `reader.inquiry_question`). `cargo check` was run anyway,
  because the branch as a whole changes `src-tauri`.

## Open questions for the owner

1. Should the section-boundary quick check (pre-existing) get the same
   isolation and spend admission as the passage check?
2. The passage check's defaults: 100 checks a day, $0.25 per metered check,
   no metered price (a metered route is refused until one is set). Keep?

## Gate (exact results)

Run in this worktree at `41b8ebd6` (the fix commits; only this file and
`rw1a-inquiry.md` changed after them) with `TMPDIR=fixtures-local/tmp`. The suite and the
durability lane ran under `flock /tmp/learnloop-fullsuite.lock`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok (the sync removes `pypdfium2`; reinstalled) |
| `uv run lint-imports --no-cache` | **15 kept, 0 broken** |
| `flock … uv run pytest -n auto` | **9118 passed**, 0 failed, 0 skipped (46 warnings), 5:24 |
| `flock … uv run pytest -m durability` | **96 passed**, 9022 deselected (1 warning), 1:35 |
| `npm install`; `npm run typecheck` | ok; exit 0 |
| `npm test` (vitest) | **268 passed** in 51 files (see note) |
| `npm run frontend:build` | built (Vite's existing large-chunk warning only) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | **exit 0** |
| `db_generate_reference.py` / `db_validate_reference.py` | **errors: []** (307 table notes, 4054 wikilinks checked). Regenerating at `41b8ebd6` changed only the `source_commit` stamps, so the committed references are current and the stamps were not recommitted |

Note: the first vitest run overlapped the full pytest suite and failed 3
tests in `PracticeScreen.test.tsx` (vault-switch timing: "A vault change is
already in progress"). That file is identical to `main` and untouched by
RW1a. Run alone it passed 21/21, and the whole vitest suite rerun on an
idle machine passed 268/268 (the row above).

Targeted run first: `tests/test_reader_passage_check.py`,
`test_reader_reconnect.py`, `test_reader_report.py`,
`test_reader_branches.py`, `test_reader_inquiry_kill_switch.py`,
`test_mobile_allowlist.py`: **149 passed**.

No paid call was made in this fix step (no model, Decider or embedding
request; $0). No vault database was opened; `fixtures/linear_algebra`,
`fixtures/probability` and `fixtures/arxiv_v2` were not touched.
