# UX-41: runaway whitespace in a structured build answer

Status: fixed in the working tree of `fix/ux41-runaway-whitespace`, not yet committed or landed. No live-route verification.

## Step 0 — code audit before implementation

The reported cause is consistent with the code and the measured failure location, though the model's internal reason is not observable. `SynthRecipe` declares properties in order: `id`, `composition`, `all_of`, `any_of`, `integration`. `integration: SynthIntegrationComponent | None = None` permits null. `ChatGPTPlanProviderClient._text_format` calls `strict_output_schema`, then `request_body` sends it as `text.format` with `type=json_schema`, `strict=true`. `_strict_json_schema` recursively makes **every property required**, preserves property order, removes defaults and forbids extra properties. It does **not** make every field nullable: only the declared nullable types admit null. Thus the key after `any_of` cannot be left out even though rule 14 explicitly requests omission. Whitespace can delay emitting the required key indefinitely.

Audit method: searched all production Python for `omit`, `absent`, `leave out`, and `optional`, inspected prompt-building matches and shared guidance, and searched production Markdown/text (including teacher doctrine). An AST string scan also checked strings outside conventionally named prompt files. Other output-related matches, left unchanged:

| Place | Exact instruction | Wire requirement and hazard |
| --- | --- | --- |
| `attempts/ai_contracts.py`, grading candidates | "`mechanism` is optional — fill it only when an obvious mechanism label applies, and leave it null rather than reaching for the nearest one." | Required nullable key; explicit null already resolves the ambiguity. No omission conflict. |
| `diagnosis/split/contract.py`, diagnostician | "Write each `statement` as plain prose about what the learner did or believed; `mechanism` is optional." | Candidate cause `mechanism` is required nullable on the strict wire. Ambiguous optional wording without explicit null: same potential hazard; deferred. |
| `teacher/doctrine/v1/99-contract.md` | "Each turn you return one object: a `message` for the learner (Markdown with LaTeX), optionally a `prediction` or a `check` (never both open at once), and zero or more `requests`." | `TeacherTurnV1` and derived turns require both nullable `prediction` and `check` keys. Potential omission conflict; deferred. |
| `content/facet_identity/judge.py` | "List every merge and absorb set; you may omit singleton keep_distinct sets, and any label you do not list is kept distinct." | Omits list entries, not declared object properties; the containing list remains required. No same hazard. |
| `practice_index/retrieval.py` | "each with a short quote copied verbatim from the exercise's statement that shows the facet (leave out any facet you cannot quote)" | Omits facet list entries, not keys. No same hazard. |
| `figures/routes.py`, advanced panels | "gradient or a flow, optionally over a heat map such as the objective" (shape: `heatmap?:{expr, cells?, contours?, label}`) | Figure spec travels inside the `spec_json` string; its inner optional fields are not strict wire properties. No same hazard. |

Other matches concern input fields/context, comments and docstrings, CLI/learner prompts, semantic absence in evidence, or prohibitions against omission, rather than permission to omit an output key. The tutor's optional `figure_goal` commentary is paired with the prompt's explicit "Null when no figure would help"; required nullable, already safe. The synthesis prompt's shared criteria guidance explicitly says "Without a listed target, leave `required_method` null"; already safe. No other synthesis sentence instructs omission of a required key. The normalization diagnostic "otherwise leave it absent" is review prose, not a synthesis prompt instruction.

The algorithm-change playbook applies to scoring, scheduling, projection or admissibility semantics and persisted meaning. This change corrects wire representation and transport recovery only. Deliberately bump both existing synthesis prompt-version variants and their explained pins; no algorithm tag, migration, historical rewrite or vault-reference regeneration.

## Measurement supplied by the orchestrator

Five identical synthesis requests were measured. Two completed in 234 and 240 seconds, with 43,419 and 45,237 output characters (about 11,600 tokens); first delta at 9 seconds, about 290 characters/second. One produced 31,385 normal characters, then 97,992 characters consisting only of newlines/spaces (lines of 5–7 spaces), about 136 characters/second. The runaway began inside `blueprints[0].recipes[0]` immediately after `"any_of": []`. The server ended it at 899 seconds without `response.completed`. The walk failed similarly twice; a retry exhausted the twenty-minute ceiling. A completed answer stumbled at the same spot with two whitespace-only lines before the comma and `"integration": null`. All 16 recipes in completed answers carried null integration. Legitimate consecutive whitespace was at most 15 characters.

## Prompt correction and stored work

Only these two sentences of rule 14 change; every other byte of rule 14 stays the same.

Before:

> INTEGRATION IS THE EXCEPTION, NOT THE DEFAULT: `integration` is OPTIONAL and
> most recipes should OMIT it.

After:

> INTEGRATION IS THE EXCEPTION, NOT THE DEFAULT: `integration` key is always present
> and most recipes should set `integration` to null.

Before:

> If you cannot name that failure, leave `integration` absent; an omitted
> integration component is the correct and expected output.

After:

> If you cannot name that failure, set `integration` to null; a null
> integration component is the correct and expected output.

The exception's meaning, capability rules and whole-task instrumentation requirement are unchanged. No other sentence needs correction. Both `SOURCE_SET_SYNTHESIS_PROMPT_VERSION` and `SOURCE_SET_SYNTHESIS_FACET_IDENTITY_PROMPT_VERSION` gain `-null-integration`; `source_set_synthesis_prompt_version` remains the selector.

The pin test before regeneration reports **4 failed, 341 passed**. Regenerated with the supplied `py.sh python tests/test_identity_pins.py --write`; only these four pins move (`identity_shapes.toml` is byte-identical):

| Pin | Before SHA-256 | After SHA-256 | Why |
| --- | --- | --- | --- |
| `A1-A4.manifest_hash.init` | `6240b4e6ac12ec42ec9139fa87179baf31e7b610991962a5d5485f9d4754b500` | `8609bfe44177fe14b79272b7994263165f20741d951d88ba019e2fd752de4cdb` | The bootstrap manifest records the selected prompt version. |
| `A1-A4.manifest_hash.legacy` | `cafe24d6a39f2a971ef010d13f77919ca56b5df428bfc457e81315b49d0cc7e6` | `e734f5a7762668917c601a5e2c1eb3de787c5bf78e9ed0251cb89f23ff4e0430` | Same version provenance under the legacy config input. |
| `A14.pass_key` | `b4fcba8761d3e0fd0e23ec55357c66c8996b5c83fe28432954db99a73f3dbafc` | `75340fb6c697d1b83b7752de8d77106636295f056706a09c0d07c96e24b58d68` | The plain synthesis request hashes the changed prompt and version. |
| `A14.pass_key.one_facet_per_skill` | `b223e76b7f52c01f5f37eae354fb86e4a56b9fda254f5d0a6cbdb4d1a59e83cf` | `0ced5e31c54c7d10580e081cf8b2897fb97a4be11e8756622d75caaf65a8500b` | The facet-identity variant uses the same corrected rule and its own bumped version. |

An in-progress rebuild under the new prompt misses old synthesis pass checkpoints, and completed synthesis shard checkpoints also miss because their keys are the base pass's request key. Those passes/shards are asked again. Inventory windows/units, append prompts, and graph-structuring checkpoints do not change identity (a newly generated input can of course change a later graph request). The manifest hash and the agent run's recorded input-context hash change as provenance; completed runs are not reused by that hash. Existing curriculum, proposals, receipts and saved checkpoint rows are not rewritten or deleted, and already completed builds are not automatically rebuilt.


### Additional prompt-dependent pins found by the required broad tests

The broad runs found one additional request digest outside `test_identity_pins.py`, plus nine whole-build goldens. These are explained by the same prompt correction, not unrelated identity drift:

- `tests/test_first_questions_arrive.py::WITHIN_BUDGET_REQUESTS`: `dde2d9311363cd77c271d95d0acb2a5269eae805a79ded4fd44c598bd560177c` → `646fb09aa7694a73078e6324b5a0ce6c657c0104562645efb97c639aad3e854f`. It pins the complete inventory/synthesis prompts and their working limits. The synthesis prompt/version moves; inventory and all working limits stay identical.
- Nine files under `tests/goldens/synthesis_tail/` change, listed below. Every changed leaf is a prompt version, a prompt-derived pass/shard key or request digest, an input-size estimate (+10 tokens per synthesis pass, +20 for two passes), or that estimate repeated in an input-ceiling error. No candidate, gate verdict, curriculum file, output allowance, actual token usage or returned proposal semantics changes. All append goldens remain byte-identical.

| Bootstrap golden | Changed leaves |
| --- | ---: |
| `bootstrap_clean_applied.json` | 7 |
| `bootstrap_gate_fails.json` | 4 |
| `bootstrap_instrument_gate_holds.json` | 7 |
| `bootstrap_items_off.json` | 7 |
| `bootstrap_over_input_ceiling.json` | 4 |
| `bootstrap_rerun_rejected.json` | 7 |
| `bootstrap_rerun_waiting.json` | 1 |
| `bootstrap_sent_span_round.json` | 10 |
| `bootstrap_unlimited.json` | 7 |

Distinct checkpoint/shard identity changes (repeated wherever the same request appears):

| Request | Old key | New key | Old → new prompt digest |
| --- | --- | --- | --- |
| Clean applied | `3a93dba1b6a4b06666a615bee35da9bcd9e9555a16f1611ef9ef0c295f4c9335` | `2b81ece803784d3550838b1aed342f6b963699ccefa53851dc6489a2d4df4e88` | `13d7d687865bddf9` → `c267a5eadc483ece` |
| Ordinary base pass | `2f79d8a436881e86431c784c3cf47416e26e171c089790278507b50ee5e8bd2e` | `bdb95932e8972446afba3240eccdf6d5d85af8b93f8b75d0cb2ded071cb47c3f` | `394e00ffb38c0779` → `7fed21ca7c3b7544` |
| Items off | `2edb7881bd1fda965ccae4c246634beeb289dc97185a30a5de7b517ca379b187` | `d57d7b488033293aff7934fd478c984ffcc1e1070986d26bb2873f4475bdf6a5` | `ae97b2e3b0a716ef` → `940b7c5d17bf41dc` |
| Resolved-span pass | `aeef46fbaf95f8121936b3241f017941ecfd4f772a2030fe69efa158761b6f59` | `4e2ea05aa997c01f5bb306bab862924b051816bbddfdcc54105ac60331e6c0d1` | `05e47b47eb4f025c` → `20b9cd96aa9ba64e` |

Before updating these records, a temporary pytest hook captured actual records through the existing `SYNTHESIS_TAIL_GOLDEN_ACTUAL` seam and the failed first-document assertion's rendered requests. Recursive comparison found exactly the 54 leaves above. A second diagnostic restored **only** the old synthesis prompt text and both old version constants in memory: **26 passed** against all old records. This isolates every golden change to part A. Only the nine differing JSON files and the one request digest were updated. The temporary hook and its conftest registration were removed; `tests/conftest.py` is unchanged.

## Guard, retry and learner outcome

`ResponsesStream.send` enables the reader guard only for `text.format.type == "json_schema"`. `_read_stream` watches `response.output_text.delta` characters, preserving a run across delta boundaries, resetting it on each non-whitespace character. It checks the entire delta, including a run followed by normal text inside the same delta. Empty deltas and lifecycle/reasoning events neither reset nor increase this answer-text counter. Plain text and `json_object` mode are not watched.

`MAX_STRUCTURED_WHITESPACE = 2_000` is the single named limit. Exactly 2,000 is allowed; the next whitespace character cuts the stream using the existing socket shutdown and cleanup path. That is over 100 times the observed legitimate maximum (15) and about 49 times below the measured runaway (97,992): ample room for ordinary formatting without another fifteen-minute stall. At the measured runaway rate the extra wait is roughly 15 seconds, plus event delivery granularity. The reader counts the full received delta in telemetry even if the guard crosses its threshold partway through it. Raw whitespace inside JSON strings also counts; this policy targets schema answers with no legitimate very long raw whitespace run, not arbitrary text preservation.

The provider classifies the cut as `ChatGPTPlanTransient`, with `provider_error.code` and the physical receipt's `finish_reason` both `runaway_whitespace`. `_send` retains its existing **three total attempts** (initial plus two retries), 0.5–1 second then 1–2 second backoffs, and remaining-time check. `single_request()` still sends at most one. A runaway raises before JSON validation, so it does not enter the separate JSON repair round. Tools-mode workspace calls have their existing per-round requests; this bound describes the single synthesis request, not every request of an arbitrary workspace turn.

Every retry shares the call's original deadline: foreground stays hard-deadline bounded, background uses the original profile's output-idle timeout (default 180 seconds) and **1,200-second absolute ceiling across the call**. Existing cancellation ordering and watchdog tests remain unchanged. A stop/quit/interrupt prevents another request.

For automatic inventory/bootstrap/append builds, an exhausted transient is in `AIProviderUnavailable`, so UX-13's bounded handler loop gives **one more round**, not zero: up to **six physical requests** for this repeatedly runaway call across two handler tries. Each new call has its own 1,200-second ceiling; the job does not get an unbounded retry. A ceiling timeout is excluded by `a_retry_may_cure` and gets no automatic second round. Manual builds do not get the automatic job retry. The test drains the runner again after failure and sees no new requests. The existing failed build state and **Try again** action remain the learner's outcome; during the one automatic retry the host reports “Trying again”. A learner explicitly choosing Try again starts fresh work, with unchanged checkpoints still reusable.

## Failed-stream delivery receipts (part C)

No schema change or migration. Existing `model_call_receipts.usage_json` stores these JSON members under `chatgpt_plan`:

- `output_characters`: total decoded answer-text delta characters received, including whitespace and the complete delta that triggers a cut (not bytes or tokens).
- `seconds_to_first_output`: monotonic elapsed seconds from the physical stream send to the first nonempty answer-text delta; null when none arrives. Lifecycle and reasoning events do not count as answer text.

The stream owns these counters, so errors, early EOF, incomplete responses, timeout and interrupt retain them. The provider meters failures with the same request id, subscription billing marker, any provider usage and existing workspace metadata. Partial answer text is never added to the receipt; unknown token usage stays unknown. The tests inspect both observer receipts and the six durable physical-request receipts of a failed job.

## Fail-first evidence

`tests/test_chatgpt_plan_runaway.py` reuses the real reader/watchdog with `tests/plan_deadline_fakes.py`'s clock and HTTP double. The helper adds per-request event selection and explicit EOF, without changing the existing deadline tests.

- Initial baseline run: **11 failed, 4 passed**. One failure was a test setup error: the legitimate long answer's fake cadence exceeded the 1,200-second ceiling. Increased only its simulated delivery rate; also replaced an error-event approximation of EOF with a real fake EOF.
- Corrected run with production code still unchanged: **10 failed, 5 passed**. Both built-prompt variants failed their present/null requirement; runaway-to-success sent only one request instead of two; every-try-runaway succeeded instead of exhausting six requests and failing; single-request mode did not raise the new transient; five receipt cases lacked delivery metadata or did not cut. The legitimate long indented answer, three non-schema modes and interrupt were already passing controls, not claimed as failing defect reproductions.
- After implementation: **32 passed**, combining the new file's 15 cases with all 17 unchanged UX-39 deadline tests. Durable receipt assertions were added to the exhausted-job case and are included in the final focused rerun below.

## Review judgments and limits

Read first: the guard is JSON-schema-only; its threshold is operational, not a measured maximum for every conceivable JSON document. Only answer-text deltas count, and counts include a whole triggering delta. The automatic job retry remains one extra round (six physical requests in the all-runaway case), whereas a twenty-minute ceiling still prohibits that extra round. The prompt bump deliberately invalidates synthesis pass/shard reuse but changes no historical scoring or projection meaning. The two other ambiguous prompt families found in step 0 are deferred.

No network or model calls were made. The real ChatGPT plan route, actual server cancellation/latency, a live book build and landing gate are **not verified** here; the orchestrator checks those. No staging or commit, no owner vault or credential reads, no generated vault references, no changes to `CLAUDE.md` or `refactor-status.md`.

## Validation commands and results

`T` means the supplied `t.sh`; `P` means the supplied `py.sh`. All invocations use explicit files; related chunks contain 40 and 21 files. No whole-suite invocation, at most two workers; layout and architecture run alone with one. Commands below use these wrapper aliases to avoid machine-local paths.

```sh
T="$SCRATCH/t.sh"
P="$SCRATCH/py.sh"
"$T" tests/test_chatgpt_plan_runaway.py -q -n 2
# Initial unchanged production: 11 failed, 4 passed in 1.76s (one bad long-stream test cadence).
# Corrected unchanged production: 10 failed, 5 passed in 1.69s.
"$T" tests/test_chatgpt_plan_runaway.py tests/test_chatgpt_plan_deadline.py -q -n 2
# First fixed run: 32 passed in 1.96s.
"$T" tests/test_identity_pins.py -q -n 2
# Before regeneration: 4 failed, 341 passed in 16.55s; all four explained above.
"$P" python tests/test_identity_pins.py --write
# Exit 0; exactly four identity digests changed, no shape change.
"$P" ruff check
# All checks passed!
"$P" lint-imports --no-cache
# Contracts: 43 kept, 0 broken.
```

related-1:

```sh
"$T" \
  tests/test_ad_guard_offer_receipts.py \
  tests/test_chatgpt_plan_cli.py \
  tests/test_chatgpt_plan_deadline.py \
  tests/test_chatgpt_plan_deadline_socket.py \
  tests/test_chatgpt_plan_landing.py \
  tests/test_chatgpt_plan_provider.py \
  tests/test_chatgpt_plan_runaway.py \
  tests/test_chatgpt_plan_sidecar.py \
  tests/test_chatgpt_plan_signin.py \
  tests/test_chatgpt_plan_workspace.py \
  tests/test_coldness_receipt.py \
  tests/test_curriculum_c1_plan_follows_path.py \
  tests/test_daily_plan_admission.py \
  tests/test_daily_plan_build.py \
  tests/test_daily_plan_composition.py \
  tests/test_daily_plan_kill_switch.py \
  tests/test_daily_plan_owner_decisions.py \
  tests/test_daily_plan_reading.py \
  tests/test_daily_plan_reentry.py \
  tests/test_daily_plan_replay.py \
  tests/test_daily_plan_review_regressions.py \
  tests/test_daily_plan_rpc.py \
  tests/test_daily_plan_split.py \
  tests/test_first_questions_arrive.py \
  tests/test_first_questions_today.py \
  tests/test_followups_batch6_prefetch_plan_wait.py \
  tests/test_forecast_receipts.py \
  tests/test_forecast_receipts_landing.py \
  tests/test_ingest_runner.py \
  tests/test_intent_plan.py \
  tests/test_intent_planner.py \
  tests/test_mobile_v2_plan.py \
  tests/test_mobile_v4_plan.py \
  tests/test_model_call_receipt_owners.py \
  tests/test_plan_determinism.py \
  tests/test_plan_determinism_landing.py \
  tests/test_plan_first_transport.py \
  tests/test_plan_first_transport_grant_scope.py \
  tests/test_plan_first_transport_offer_grants.py \
  tests/test_plan_first_transport_offer_grants_r5.py \
  -q -n 2 -m 'not arc_close'
# Interrupted, exit 130: mobile TestClient setup stalled; no completed summary, not counted.
```

related-2:

```sh
"$T" \
  tests/test_plan_first_transport_paid_roles.py \
  tests/test_plan_first_transport_today_quiet.py \
  tests/test_plan_follows_path.py \
  tests/test_plan_refs.py \
  tests/test_planted_misgrade.py \
  tests/test_receipt_derivation.py \
  tests/test_receipt_exactness.py \
  tests/test_rw2d_receipts_migration.py \
  tests/test_sidecar_synthesis.py \
  tests/test_sim_planted_types_forty_seeds.py \
  tests/test_source_set_synthesis.py \
  tests/test_synthesis_answer_reuse.py \
  tests/test_synthesis_criterion_dependencies.py \
  tests/test_synthesis_eval.py \
  tests/test_synthesis_gates.py \
  tests/test_synthesis_identifiability.py \
  tests/test_synthesis_manifests.py \
  tests/test_synthesis_runs_repo.py \
  tests/test_synthesis_sweep_primary_only.py \
  tests/test_synthesis_tail_golden.py \
  tests/test_teacher_te2log_receipt.py \
  -q -n 2 -m 'not arc_close'
# 12 failed, 147 passed, 5 skipped in 20.73s: 3 socket denials, 9 explained bootstrap golden mismatches (corrected below).
```

gates:

```sh
"$T" \
  tests/test_identity_pins.py \
  tests/test_retired_config_identities.py \
  tests/test_diagnosis_journey_golden.py \
  tests/test_structure_ratchets.py \
  tests/test_effective_defaults_golden.py \
  tests/test_sqlite_file_copies.py \
  tests/test_mobile_allowlist.py \
  -q -n 2 -m 'not arc_close'
# 725 passed in 21.91s.
```

test_layout:

```sh
"$T" \
  tests/test_test_layout.py \
  -q -n 1
# 3 passed in 19.17s.
```

architecture:

```sh
"$T" \
  tests/test_architecture.py \
  -q -n 1
# 18 passed in 29.92s.
```

The first related chunk stalled in the first mobile TestClient fixture. It was interrupted (exit 130); no summary or passes from that interrupted run are counted. The rerun excludes only the two separately attempted mobile files:

```sh
"$T" \
  tests/test_ad_guard_offer_receipts.py \
  tests/test_chatgpt_plan_cli.py \
  tests/test_chatgpt_plan_deadline.py \
  tests/test_chatgpt_plan_deadline_socket.py \
  tests/test_chatgpt_plan_landing.py \
  tests/test_chatgpt_plan_provider.py \
  tests/test_chatgpt_plan_runaway.py \
  tests/test_chatgpt_plan_sidecar.py \
  tests/test_chatgpt_plan_signin.py \
  tests/test_chatgpt_plan_workspace.py \
  tests/test_coldness_receipt.py \
  tests/test_curriculum_c1_plan_follows_path.py \
  tests/test_daily_plan_admission.py \
  tests/test_daily_plan_build.py \
  tests/test_daily_plan_composition.py \
  tests/test_daily_plan_kill_switch.py \
  tests/test_daily_plan_owner_decisions.py \
  tests/test_daily_plan_reading.py \
  tests/test_daily_plan_reentry.py \
  tests/test_daily_plan_replay.py \
  tests/test_daily_plan_review_regressions.py \
  tests/test_daily_plan_rpc.py \
  tests/test_daily_plan_split.py \
  tests/test_first_questions_arrive.py \
  tests/test_first_questions_today.py \
  tests/test_followups_batch6_prefetch_plan_wait.py \
  tests/test_forecast_receipts.py \
  tests/test_forecast_receipts_landing.py \
  tests/test_ingest_runner.py \
  tests/test_intent_plan.py \
  tests/test_intent_planner.py \
  tests/test_model_call_receipt_owners.py \
  tests/test_plan_determinism.py \
  tests/test_plan_determinism_landing.py \
  tests/test_plan_first_transport.py \
  tests/test_plan_first_transport_grant_scope.py \
  tests/test_plan_first_transport_offer_grants.py \
  tests/test_plan_first_transport_offer_grants_r5.py \
  -q -n 2 -m 'not arc_close' --tb=short
# 56 failed, 466 passed, 3 skipped, 1 xfailed, 63 errors in 140.94s.
# 55 failures + all 63 setup errors: socket creation denied (Errno 1).
# The other failure: the explained first-document request digest, corrected below.
```

```sh
timeout --signal=INT --kill-after=5s 45s "$T" tests/test_mobile_v2_plan.py -q -n 2 -m 'not arc_close' -o faulthandler_timeout=15 --tb=short
# Exit 137 after the 45-second interrupt plus 5-second kill grace; no tests counted.
timeout --signal=INT --kill-after=5s 45s "$T" tests/test_mobile_v4_plan.py -q -n 2 -m 'not arc_close' -o faulthandler_timeout=15 --tb=short
# Exit 137 after the 45-second interrupt plus 5-second kill grace; no tests counted.
"$T" tests/test_chatgpt_plan_runaway.py tests/test_chatgpt_plan_deadline.py -q -n 2
# 32 passed in 1.95s (durable receipt assertions and valid long-answer schema included).
```

Both mobile diagnostic traces stop in `starlette.testclient.TestClient.__enter__` → AnyIO `start_task_soon` / `run_sync_from_thread`, while the portal thread waits in the selector. Their test bodies never establish results. The underlying mobile startup hang is not diagnosed here; it is reported separately from the explicit TCP socket denials, not assumed to have the same cause.

Snapshot audit and final edited tests:

```sh
"$T" tests/test_synthesis_tail_golden.py tests/test_first_questions_arrive.py::test_a_build_that_fits_the_working_sizes_sends_the_same_requests -q -n 2 -p tests.ux41_capture_plugin --tb=short
"$T" tests/test_synthesis_tail_golden.py tests/test_first_questions_arrive.py::test_a_build_that_fits_the_working_sizes_sends_the_same_requests -q -n 2 -p tests.ux41_capture_plugin --ux41-old-prompt --tb=short
# Both initial attempts exited 1 before collection: early -p import could not resolve tests. No tests counted.
# Loaded the temporary hook through conftest instead for these two diagnostic runs:
"$T" tests/test_synthesis_tail_golden.py tests/test_first_questions_arrive.py::test_a_build_that_fits_the_working_sizes_sends_the_same_requests -q -n 2 --tb=short
# 10 failed, 16 passed in 5.03s; captured actual records, before updating expected values.
"$T" tests/test_synthesis_tail_golden.py tests/test_first_questions_arrive.py::test_a_build_that_fits_the_working_sizes_sends_the_same_requests -q -n 2 --ux41-old-prompt --tb=short
# 26 passed in 4.95s; only old prompt text/versions substituted in memory.
# Removed temporary hook and restored conftest byte-for-byte; updated only explained expected values.
"$T" tests/test_first_questions_arrive.py tests/test_synthesis_tail_golden.py tests/test_chatgpt_plan_runaway.py tests/test_chatgpt_plan_deadline.py -q -n 2 -m "not arc_close" --tb=short
# 1 failed, 73 passed in 12.68s; sole failure is fake HTTP-server socket creation denied.
```

Final gates after the snapshot updates and removal of the temporary hook:

```sh
"$T" tests/test_identity_pins.py tests/test_retired_config_identities.py tests/test_diagnosis_journey_golden.py tests/test_structure_ratchets.py tests/test_effective_defaults_golden.py tests/test_sqlite_file_copies.py tests/test_mobile_allowlist.py -q -n 2 -m "not arc_close"
# 725 passed in 22.43s.
"$T" tests/test_test_layout.py -q -n 1
# 3 passed in 19.40s.
"$T" tests/test_architecture.py -q -n 1
# 18 passed in 30.02s.
"$P" ruff check
# All checks passed! (initial, intermediate, and final invocations.)
"$P" lint-imports --no-cache
# Contracts: 43 kept, 0 broken. (Initial and final invocations.)
git diff --check
# Exit 0, no whitespace errors.
```

A separate byte comparison of rule 14 against HEAD, applying only the two documented replacements, printed: `Rule 14: only the two specified sentences changed; remaining bytes identical.`

Sandbox exclusions: **121 distinct socket-blocked cases** across the two completed related chunks (118 in the 38-file rerun, 3 in chunk two), all with `PermissionError: [Errno 1] Operation not permitted` at socket construction. They include the real local-socket deadline tests, OAuth/plan fake-server tests and two receipt-owner tests. The one socket failure in the final edited-file run is already in that count. None is counted as a passed check. The two mobile files remain unverified after bounded TestClient startup hangs; no results from those files are counted. The completed related chunks also report eight skips and one expected failure, not passes. The initial interrupted chunk and failed diagnostic-plugin imports contribute no result counts.

All functional failures that could execute were explained prompt snapshots and pass after the narrowly audited update. Final edited-file validation is **73 passed, one socket-blocked failure**. This is not a claim that the full landing gate or the socket-backed transport suite passed in this sandbox.

## Change size

Including both new files (plain `git diff --stat` omits untracked files): **660 insertions, 77 deletions, net +583 lines across 18 files**. Implementation alone (`src/`): 51 insertions, 14 deletions, net +37 lines. No files were staged.

The final diff contains only the three implementation files, the stream fake, the new regression file, the first-document request pin, the identity golden, nine bootstrap goldens, this record and the UX ledger row. No temporary hook, conftest edit, algorithm tag, migration, generated reference or forbidden review-file change remains.
