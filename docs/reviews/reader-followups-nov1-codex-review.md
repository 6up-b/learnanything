# Reader follow-ups Nov 1: Codex review fix round

Branch `reader/followups-nov1`, worktree `learnanything-astrafix`. Codex review
job `20261101-092938-1KlppV` (gpt-6.1-sol). It reported two findings, one High and
one Medium. Codex could not run tests, because its sandbox denied the systemd user
scope and `uv` cache locking. The stage record is in
`docs/reviews/reader-followups-nov1.md`.

## Review

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Cached comparisons omit the current request's provenance | fixed | 20402f4e3f | `tests/test_whole_comparison_reuse_provenance.py` (6 tests; the 4 bug tests failed before the fix) |
| F2 | Medium | The deadline abandons requests before response headers arrive | fixed | 74b496d47b | `tests/test_chat_total_transport_deadline.py` (rewritten over a fake httpcore network backend: 5 failed + 2 teardown errors before the fix, 8 passed after) |

### F1: a reused comparison is checked with the current call's provenance

**Reproduction.** Every regression warms the cache before the protected
contributor appears, as the review asked. On the old code, four tests failed with
`DID NOT RAISE SidecarError`:

- `test_f1_a_reused_comparison_with_a_new_exam_pin_is_withheld_whole`. The direct
  `compare_sources` call compares `ext_book:s6` and `ext_text:t3`, then repeats the
  comparison with an extra exam pin. The comparison is reused (one
  `source_comparisons` row) and was shown.
- `test_f1_the_reuses_dropped_pin_is_persisted_for_later_reads`. After the reuse,
  RW4d's `withheld_comparisons` on the stored id still found nothing to withhold.
- `test_f1_find_sources_compare_reads_a_reuses_persisted_exam_pin`. A direct call
  reuses `find_sources(compare)`'s comparison with an exam pin. The next
  `find_sources(compare)` reuses the same row.
- `test_f1_a_cached_tutor_comparison_checks_the_current_questions_passage`. A
  question asked in `ext_book` runs the comparison. A second question is asked at
  `ext_text:t3`, and then chapter 5 is held out. The second question's run reused
  the comparison and showed it, because its question is linked only when the run
  row is written, after the check.

**Fix.**

- `instructional/sources.py`: `refuse_withheld_comparison(..., caller=, current=)`
  reads the union of the stored provenance and the current call's contributors
  (`current_contributors`): the tutor question (`caller.ref` for a tutor caller),
  the anchor keys, the dropped pins and the unverified sources. The check runs
  before any response or view is built. All three surfaces pass their caller and
  result: the direct RPC (`handlers/source_service.py`), `find_sources(compare)`
  (the comparison on the manifest), and the tool run (`instructional/tools.py`).
- `reader/source_objects.py`: RW4d's own helpers take these contributors.
  `comparison_passages(..., passages=)` and
  `withheld_comparisons(..., question_event_ids=, passages=)` resolve them like
  the rest and still fail closed. The rule is not copied anywhere else.
- `source_retrieval/compare.py` and `db/stores/source_service.py`
  (`add_comparison_reuse_provenance`): on reuse, the call's dropped pins and
  unverified sources are added to the stored row, de-duplicated by passage. The
  write happens only when something is new; a reuse with nothing new writes
  nothing, which `test_f1_a_reuse_with_nothing_new_protected_is_shown_and_writes_nothing`
  checks. This persists the reuse provenance that later reads depend on, the
  library's deliveries and keeps included, without editing the library-ask path.
  A pin dropped as "no such passage" is not written, since it would make the
  shared comparison unresolvable for every later reader
  (`test_f1_a_reuses_pin_naming_no_passage_is_not_persisted`). The current call
  still fails closed on such a pin, as the fresh path does. The tutor question
  needs no new storage: the run row already records it once the check passes.

There is no schema change (the existing `dropped_pins_json` and
`unverified_sources_json` columns of a WORKFLOW table), and no new parameter.
`NO_SUCH_PASSAGE` is the existing reason label, now named as a constant.

### F2: the deadline cancels the request in the transport

**Reproduction.** I rewrote the test file around a fake httpcore network backend,
installed as httpcore's default `SyncBackend`. The real adapter, the real `openai`
SDK, httpx and httpcore's HTTP/1.1 run over a fake socket that honours each
operation's timeout the way `settimeout` does. On the old adapter:

- delayed headers failed with "a network operation was still running when the
  adapter returned";
- in the narration case, 3 operations were in flight when the call returned. These
  were concurrent replacement requests from the retry loop;
- the slow-connect-and-upload case and the dribbling body also failed;
- two tests hit the thread-leak guard at teardown.

**Fix** (`ai/providers/openai_chat.py`). The worker thread, the response hook and
the stream wrapper are gone.

- The SDK's own `DefaultHttpxClient` pools, including any proxy mounts, send
  through `_DeadlineNetworkBackend`. In the calling thread, it bounds every network
  operation by `min(the operation's timeout, the deadline's remaining time)`: TCP
  connect, TLS, upload, response headers and body. It starts no operation once the
  deadline has passed.
- When the adapter raises (`TotalDeadlineExceeded`), the request's transport work
  is over, so nothing runs beside a retry or a narration successor.
- Name resolution is the system resolver's. If the deadline passes during it, the
  new connection is closed before anything is sent.
- `test_f2_the_deadline_is_armed_on_the_sdks_own_http_client` fails if an
  httpx/httpcore upgrade moves the pool. If arming fails, a warning is logged.
- The `transport=` test seam is removed; the tests use the fake network backend.
- The lease (`narration_lease_seconds`) is still
  `ceil(enforced_total_seconds(timeout)) + CLAIM_LEASE_SECONDS`. This is now the
  actual enforced bound of the request's transport activity.

## Gate (this fix step; the full suite runs once, in the landing gate)

Every pytest command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G --`, with
TMPDIR in the session scratchpad.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted run, `uv run pytest -n 6` on 51 files: **1341 passed, 3 skipped** (123 s).
  The files:
  - new or changed: `test_whole_comparison_reuse_provenance`,
    `test_whole_comparison_provenance_surfaces`, `test_chat_total_transport_deadline`
  - chat adapter users: `test_agent_run_tokens`, `test_ai_single_request`,
    `test_diagnose_review_spend`, `test_diagnosis_isolation`, `test_figure_region`,
    `test_ingestion_checkpoints`, `test_lo_general`, `test_model_usage_report`,
    `test_multimodal_client`, `test_openai_chat_client`, `test_openrouter_client`,
    `test_output_budget`, `test_plan_first_transport`, `test_practice_index_paid`,
    `test_project_cli`, `test_provider_resolution_parity`, `test_router_r2b_serving`,
    `test_structured_transport_parity`, `test_t6_followup_composition`,
    `test_t6_followup_review`, `test_ux_phase1_review_fixes`
  - narration: `test_reader_digest_narrative`, `test_reader_rw6b_p2_landing`
  - comparisons, RW4d and tools: `test_compare_sources`, `test_compare_sources_keep`,
    `test_compare_keep_switch_off`, `test_find_sources_intents`,
    `test_library_exercises`, `test_reader_ca3_codex_review`,
    `test_reader_ca3_compare_anywhere`, `test_reader_ca4_table_by_point`,
    `test_reader_compare_table`, `test_reader_find_sources_callers`,
    `test_reader_tutor_offers`, `test_rw4d_rw3b_composition`, `test_source_objects`,
    `test_library_ask`, `test_library_ask_review`, `test_sidecar_reader_p3_slice2`,
    `test_source_service_spend_envelopes`, `test_sources_merge_composition`,
    `test_tool_registry`, `test_tool_results_withhold_answers`, `test_tools_cli`,
    `test_tutor_tool_requests`
  - contracts: `test_architecture`, `test_table_roles`, `test_mobile_allowlist`
- `uv run pytest -n 6 --durable-sqlite` on the two whole-comparison files (the new
  store write under production pragmas and WAL): **14 passed**.
- `git diff --check 2eb4bf6e61..HEAD`: clean.
- Not run, because nothing they cover changed: frontend, cargo, migration,
  durability lane, DB reference scripts (no schema change). No live or paid calls
  were made.
