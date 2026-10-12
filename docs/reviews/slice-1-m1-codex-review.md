# Slice 1 M1: Codex review fixes

Branch `slice-1/m1`, worktree `learnanything-slice1-m1`. Review job
`codex-agent/jobs/20261012-014721-rpoAmU`, against the stage as gated at
`93951f2b`. Each finding was reproduced first (a failing test, or for F1 a
direct run of the installed Codex sandbox), then fixed, one commit per
finding. F1 and F2 share a commit because they share one transport fix.
Fakes only. No live or paid model call was made.

## Review

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Snapshot mode does not confine reads to the snapshot | fixed | `a6632636` | `tests/test_diagnosis_isolation.py`: `test_the_builtin_read_only_sandbox_reads_the_whole_disk` (shows the defect on the installed `codex-cli 0.161.0`), `test_an_isolated_turn_cannot_read_a_sentinel_outside_its_workspace`, `test_the_app_server_starts_the_thread_under_the_learnloop_profile`, `test_a_snapshot_turn_runs_under_the_profile_never_the_builtin_sandbox` |
| F2 | High | The Codex blind grader retains access to learner history | fixed | `a6632636` | `test_an_isolated_turn_without_a_workspace_starts_in_an_empty_directory`, `test_the_blind_grader_always_asks_for_an_isolated_turn`, `test_isolated_overrides_switch_the_tools_off`, `test_configured_mcp_servers_are_listed_and_disabled`, `test_a_review_refuses_a_grader_or_diagnoser_that_cannot_isolate` |
| F3 | High | Metered spend admission does not cover physical requests | fixed | `b3c5b942` | `tests/test_diagnose_review_spend.py`: `test_a_json_repair_is_a_second_admitted_request_on_a_metered_route`, `test_transport_retries_are_admitted_too`, `test_admitted_repairs_are_charged_and_capped_by_the_admitted_output`, `test_the_route_allowance_is_enforced_when_the_profile_sets_no_limit` |
| F4 | High | E1's supposed ground truth is not verified | fixed | `febfd387` | `test_a_valid_alternative_is_verified_on_its_submitted_derivation`, `test_a_synthetic_error_is_known_only_when_the_planted_error_is_verified`, `test_sympy_never_sees_model_text_outside_a_safe_math_alphabet` |
| F5 | Medium | As-of repair history leaks future outcomes and hypotheses | fixed | `5aaed8ea` | `test_repairs_before_filters_owners_and_cold_outcomes_by_the_cutoff` |
| F6 | Medium | Nested diagnosis fields bypass the firewalls | fixed | `de75c3b1` | `test_nested_cause_targets_and_scopes_pass_the_firewalls`, `test_causal_cause_scopes_on_an_invalid_measurement_become_unknown`, `test_repair_preserve_and_target_refs_are_closed_world` |
| F7 | Medium | Unanchored quotes become validated recurrence evidence | fixed | `aa89f678` | `test_a_stored_unanchored_divergence_quote_is_not_verbatim_evidence` |
| F8 | Medium | Citation validity combines unrelated targets and scopes | fixed | `bdc13625` | `test_citation_validity_is_judged_on_the_overlapping_target_itself` |
| F9 | Medium | A malformed cause reference crashes the run | fixed | `65147fb1` | `test_malformed_cause_refs_are_recorded_never_raised_or_wrapped` (7 cases) |
| F10 | Medium | Retried diagnoses can permanently miss their judgments | fixed | `0019fc74` | `test_a_diagnosis_repaired_on_resume_is_judged_and_only_the_current_revision_counts` |
| F11 | Medium | Resume silently mixes experiment configurations | fixed | `63eda57e` | `test_a_resume_restores_the_persisted_experiment_and_refuses_changes`, `test_cli_resume_with_only_the_run_dir_keeps_the_original_settings` |
| F12 | Medium | Failed probes are treated as completed checkpoints | fixed | `ab5a5cc8` | `test_failed_probes_are_retried_on_resume_without_regenerating_paid_inputs` |
| F13 | Medium | Owner adjudication can attach to a diagnosis the owner never saw | fixed | `20122617` | `test_an_owner_verdict_never_lands_on_a_receipt_the_owner_did_not_see`, `test_arm_a_is_the_stored_diagnosis_not_the_joint_repeat` |
| F14 | Medium | E4 compares unrelated events by list position | fixed | `89b5bca7` | `test_e4_aligns_events_by_localization_and_target_not_list_position` |
| F15 | Medium | One judge pass is reported as two-pass confirmation | fixed | `104c3069` | `test_one_judge_pass_is_never_reported_as_a_confirmed_link` |
| F16 | Medium | Subscription routes still consume the physical-call cap | rejected | n/a | It conflicts with the spec. Slice A §5 rule 6 (owner, 2026-10-12) exempts subscription transports from a cap on **physical requests**, but says "**Caps still apply to call count**, candidates and pairs, so a runaway loop stops". The refusal at `max_calls=0` is that call-count cap, set by the owner. The physical-request exemption is now implemented by F3: a Codex unit's retries, JSON repairs and regenerations are never charged. `test_subscription_routes_have_no_physical_request_bound` runs 3 physical turns under `max_calls=1, max_retries=0` and charges 1 call and 0 retries. |

### What changed, by finding

- **F1, F2 (transport isolation).**
  - **New capability.** `ai/transport.py` adds `ISOLATED_TURN` and `StructuredRequest.isolated`, and a workspace implies isolation. `execute_structured_operation(isolated=True)` refuses any transport that does not declare the capability, and never routes an isolated request to a legacy endpoint adapter. Chat-completion transports offer the model no tools, so they declare it by construction.
  - **Permission profile.** The Codex SDK client runs every isolated turn under the permission profile `learnloop_isolated_turn`, passed as app-server `--config` overrides. The profile can read the workspace (or a fresh empty directory, removed after the turn) plus Codex's `:minimal` platform set. It cannot write, and it has no network.
  - **Settings the overrides turn off.** Approvals never prompt. Web search, connectors (`apps`), plugins, sub-agents, browser and computer use, memories, hooks, skills search, `view_image` and project docs are all off.
  - **MCP servers.** These run outside the command sandbox, so each one `codex mcp list --json` reports for the turn's directory is disabled by name. Listing fails closed, because disabling a server name Codex does not know breaks its config load.
  - **No sandbox mode on thread start.** The thread is never given one: the installed app server showed that `sandbox: "read-only"` replaces the profile with the built-in mode, which reads the whole disk.
  - **Fails closed.** An SDK whose `CodexConfig` cannot take `config_overrides`, or a launch command without `app-server`, fails closed. A turn with no workspace also has the shell tool off.
  - **Callers.** Blind grading, diagnosis (every mode), the judge, the planted generator and the probes always request isolation. A review refuses a grading or diagnosis route that cannot isolate, before anything is copied.
- **F3 (spend).**
  - **Metered routes.** `ReviewSpend` watches the physical `model_call` receipts inside each paid unit. The first request is admitted up front. Each transport retry or JSON repair is admitted as a retry when its receipt starts, and a refusal means it is never sent. Each request is reconciled with its own usage.
  - **Output limit.** The transport is held to the admitted output limit (`generation_limit`). That limit is the route allowance, or the profile's larger `max_tokens`, which the estimate then prices.
  - **Subscription routes.** These keep one logical call against the call cap with no physical-request bound, and now check cancellation before every physical request.
- **F4 (E1 probes).**
  - **Valid alternatives.** One counts as verified only when its final answer equals the reference, the derivation the grader sees ends with that answer, and none of its numeric equations is false.
  - **Synthetic errors.** These are judged on the answer itself, not on the generator's declaration. The concluding line must state a final answer that SymPy, or exact numeric comparison, shows differs from the reference. A correct answer is excluded as `not_wrong`.
  - **E1 metric.** E1 now compares the blind grader's miss rate on verified-wrong synthetic answers (full marks given anyway) with its owner-adjudicated error rate on real answers. Both are binary, with a Wilson interval.
  - **SymPy input.** Model text reaches SymPy only within a safe math alphabet, because its parser evaluates Python.
- **F5.** Repair classes keep owners and cold verifications raw, with the cold attempt id and timestamp. `repairs_before` filters both by the cutoff, then aggregates.
- **F6.** A single typed-reference check now covers cause `target_ref`, repair `target_refs` and `preserve_refs`. Facets must be known (closed world, counted). Criteria must be the item's. Checkpoints must belong to an available trace contract. Answer spans must re-anchor. The passed-target firewall applies to targets, criteria included. Nested cause scopes the diagnoser does not own (`item_contract`, `grader_interpretation`, `interaction_context`), and causal scopes on a non-valid event, become `unknown`.
- **F7.** A citation that does not re-anchor in the learner's answer is dropped. The stored-divergence fallback is gone.
- **F8.** History attempts keep each attribution's targets with its own validity scope, and each failed criterion with its facets. S4 requires a valid non-pass on the overlapping target itself.
- **F9.** `cause:<event>:<cause>` needs exactly two nonnegative decimal indices, both within bounds. Anything else is recorded as an issue.
- **F10.** Every judge row carries a revision. That is the hash of the judged arms' diagnosis ids and contents, of the cited link set, or of the planted statements. A changed input is judged again as an appended revision. The report and `import-links` read only the revision that matches each target's current candidates, and the report counts the superseded rows.
- **F11.**
  - **What `run.json` keeps.** It persists the complete options, the planted manifest included, and a binding: the source vault, a hash of the vault content that contexts read, each route's provider/model/settings, and every prompt version.
  - **Resume.** A resume restores the persisted options. The CLI tells explicit flags from defaults, and an explicit different option, another vault or vault content, a changed route or a new prompt version gets `incompatible_resume` before any call.
- **F12.** Probe checkpoints now separate settled outcomes (graded, unverified, invalid criterion, not wrong) from retryable failures (generation or grading failed). Drafts and probe ids are persisted, so a grading retry re-grades the same draft.
- **F13.**
  - **Bound verdicts.** Each arm (a) spot-check option carries the identity of the receipt shown to the owner: receipt id, snapshot hash and view hash, from the scratch copy. The verdict is written only if the live receipt still matches, checked inside one vault transaction. Otherwise the reason is `receipt_changed_since_review`.
  - **Also fixed.** The reproduction showed that arm (a)'s explanation was the joint *repeat's* prose: the review wrote its own grading receipts into the scratch copy, and the stored-analysis lookup picked the newest. That lookup now ignores receipts owned by the review.
- **F14.** E4 aligns blind attributions to stored joint error events one-to-one, by overlapping validated spans (or nested quotes) and compatible targets. Registry matches are compared only on aligned pairs. Unmatched and ambiguous events are reported separately.
- **F15.** A link is confirmed only when both passes of its current revision judged it the same. A single pass is reported as an incomplete pair and excluded from every confirmed-link metric. Arms are credited from the current diagnoses.

### Deviations and notes

1. **The joint grader's re-runs are not isolated.** These are arm (a) on planted learners and E1's joint repeat. They measure today's production joint grader, which runs in the vault root. Isolating them would change what E1 compares against. If the owner wants the baseline isolated too, it is a one-argument change in `runner.joint_grade`.
2. **The synthetic-error probe has a narrower but verified truth.** Only "not full marks" is known, and only when the stated final answer is decidably different from the reference. In a vault whose references are symbolic or matrix-valued (linear algebra), most synthetic drafts are excluded as `unverified`; the report shows every status. On the fixtures-local smoke run, all 6 were unverified, and 2 of 6 valid alternatives were verified.
3. **Output allowances were raised and the retry default widened.** Metered output allowances are now 6,000 grading, 8,000 diagnosis, 4,000 judge and 6,000 generator tokens. They are enforced on the transport now, so they must leave room for reasoning tokens. `diagnose run --max-retries` defaults to 50: every metered transport retry and JSON repair now draws on it.
4. **Codex dependence.** The isolation needs Codex CLI permission profiles (verified on `codex-cli 0.161.0`, installed here) and an SDK `CodexConfig` with `config_overrides` (the current SDK has it). Older SDKs fail closed and arm (e) is then skipped, as before. `codex features list` still reports `unified_exec` as on even when overridden off. The permission profile is the enforced boundary either way: the sentinel test passes with the shell on and with it off.
5. **The real-binary tests make no model call.** They run `codex sandbox` and a bare `app-server` `thread/start` under a throwaway `CODEX_HOME`, and skip when Codex is not installed.

### Manual check (fakes only, on a backup-API copy)

The test fakes ran a full review on `fixtures-local/m1-linear_algebra` (run directory `fixtures-local/m1-runs/review-fixes-smoke`).
- **First run:** status `complete`, 190 fake calls. Every grading, diagnosis, judge and generator call was isolated; only the joint grader's re-runs were not.
- **Resume with only the run directory:** `complete`, 0 calls.
- **Copy unchanged:** the copy's `state.sqlite` SHA-256 was the same before and after (`092b795a…`).
- **Report:** rendered (15 KB) with E4 alignment counts, incomplete link pairs and superseded judgment rows.

### Gate

All results below are on the final fix commit (`a6632636`; the commit after it records only this document).

| Gate | Result |
|---|---|
| `uv sync --extra dev` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 6 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` (run with `-q -p no:cacheprovider`) | **6257 passed**, 0 failed (14 warnings, pre-existing), 3 m 08 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` (run with `-q -p no:cacheprovider`) | **63 passed**, 6194 deselected, 0 failed, 32 s |
| Frontend (`npm run typecheck`, `npm test`) | not run: no frontend change |
| DB reference generate/validate | not run: no schema change (no migration; the scratch-only `review_*` DDL is unchanged) |

New and changed tests:
- **New file `tests/test_diagnosis_isolation.py`:** 16 tests, 6 of them against the installed Codex.
- **New file `tests/test_diagnose_review_spend.py`:** 6 tests.
- **Additions to existing files:** `test_diagnosis_contract.py` (+6 functions, 12 collected tests, 7 of them the parametrized F9 cases), `test_diagnose_review.py` (+11), `test_diagnosis_history_modes.py` (+1).
- **Rewritten:** the two fake-SDK workspace tests that asserted the built-in `read-only` sandbox were folded into one test, `test_codex_workspace_replaces_the_vault_root`.
- **Snapshot:** `tests/cli_help_snapshot.json` updated for the `diagnose run` help text.

### Open questions for the owner

1. **Isolate the joint-grader baseline in M1?** See deviation 1.
2. **Synthetic probe coverage.** With symbolic references the probe is mostly excluded. Should M1 also accept owner-confirmed synthetic answers, or is the binary, SymPy-decidable subset enough for the real-vs-synthetic decision?
3. **Supersedes `slice-1-m1.md` open question 1.** The read-only workspace no longer uses `sandbox="read-only"`; it uses the permission-profile overrides above.

## Re-review

Review job `codex-agent/jobs/20261012-025612-TfErU7`, against `93951f2b..a0ad170f`. It confirmed F1, F2, F3, F6, F7, F8, F9, F10, F13 and F15 as fixed. It reopened F4, F5, F11, F12, F14 and F16, and added F17. Each reopened finding was reproduced with a failing test first, then fixed in its own commit (F4 and F17 share one, because they share the rewritten checker). F16 is rejected again, with a test that pins the spec's rule. Fakes only. No live or paid model call was made.

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F4 | High | E1 ground truth: unparsed steps are skipped, and token presence stands in for the asserted conclusion | fixed | `2b4c6703` | `tests/test_diagnose_review.py`: `test_every_relation_in_an_alternative_is_checked_never_skipped` (reproduced `verified` for `Let x=1. Then x+x=99.\nTherefore 2.`), `test_the_asserted_conclusion_is_parsed_not_found_as_a_token` (reproduced `verified_wrong` for `1+1=2.\nThe answer is 2, not 3.` declared `3`), `test_sympy_never_sees_model_text_outside_a_safe_math_alphabet` (extended) |
| F5 | Medium | As-of history ignores when a record was written | fixed | `d157ec7f` | `tests/test_diagnosis_history_modes.py::test_as_of_history_needs_each_record_written_before_the_cutoff` (reproduced: an owner and a hypothesis version written at hour 7 about a hour-1 attempt, and a cold observation recorded at hour 7 for a hour-2 cold attempt, were all visible at a hour-5 cutoff) |
| F11 | Medium | The route binding omits `profile.max_tokens` | fixed | `065b6c80` | `test_a_resume_refuses_a_changed_output_limit` (reproduced: a resume with `max_tokens` 9,000 → 100 completed) |
| F12 | Medium | A probe draft is checkpointed only after grading returns | fixed | `ddfe88cd` | `test_a_probe_draft_survives_an_interruption_while_it_is_graded` (reproduced: zero checkpoints after a cancellation while the first draft was graded) |
| F14 | Medium | Unvalidated quotes remain an E4 alignment fallback | fixed | `b35575d8` | `test_e4_aligns_only_on_localization_validated_in_the_answer` (reproduced: two `whole_answer` anchors with null offsets and the same invented text aligned, n=1) |
| F16 | Medium | Subscription requests still reserve `calls=1` against the shared cap | rejected | `6e48861d` (test only) | It conflicts with the spec. Slice A §5 rule 6 exempts Codex from a **physical-request** bound, tokens and dollars, but says "**Caps still apply** to call count, candidates and pairs, so a runaway loop stops". The shared implementation on `integrate/slice-a-2-3` (`ai/spend.py`, `SpendBudget(subscription=True)`) does the same: only `max_total_tokens` and `max_estimated_usd` go unenforced, and "the candidate, pair, call and retry caps still stop a runaway loop". `max_calls=0` refusing a Codex unit is that call-count cap, set by the owner. Exempting it would leave nothing to stop a Codex loop. `tests/test_diagnose_review_spend.py::test_the_call_count_cap_still_stops_subscription_work` pins the behaviour: nothing is sent, and tokens and dollars are never capped. |
| F17 | Medium | Numeric verification strips leading minus signs | fixed | `2b4c6703` | `test_numeric_checks_keep_unary_signs_and_whole_expressions` (reproduced: the old checker returned `['1 + 3 = 2.']` for `-1 + 3 = 2.`) |

### What changed, by finding

- **F4 (E1 probe ground truth).**
  - **Every relation is checked.** `probes.check_relations` tokenizes the whole derivation and takes every maximal run of math tokens that holds a relation as one chain. It decides a chain only when each side parses as plain arithmetic over numbers and single-letter symbols into an exact polynomial normal form (fractions, unary signs, brackets, `^`, implicit products such as `2x`).
    - A definition (`Let x = 1`) binds the symbol, so `x+x=99` is then **false**.
    - Constant sides are compared exactly, to half a unit of a stated rounded decimal.
    - An identity holds when its normal forms match.
  - **What is unchecked.** A conditional equation (`x+x=99` with `x` free), any other relation (`<`, `\neq`, `=>`), LaTeX, functions, a comma-joined tuple (`x, y = 2, 1`, `f(1, 2) = 3`, `1,000`), and a chain next to a prose word that is not a plain connective (`3 times 2 = 2`, `1 + 1 = 2 times 2`) are all **unchecked**. An unchecked chain excludes the draft (`unchecked_relation`); it is never skipped.
  - **The asserted conclusion is parsed.** `asserted_conclusion` reads the last line's structure (`Final answer: X`, `... the answer is X`, `Therefore X`, or the whole line; `x = X` also offers `X`). The assertion must equal the declared final answer, and only then is it compared with the reference. `2, not 3` asserts neither 2 nor 3, so the reviewer's case is `unverified`, not `verified_wrong`.
  - **A difference must be proven.** A synthetic answer is `verified_wrong` only when the difference is decided: exact arithmetic, distinct polynomial normal forms, or SymPy's `Expr.equals` finding a nonzero value. A simplification that fails to reach zero no longer counts. A rounded decimal within its stated precision is not "wrong".
  - **SymPy hardening.** SymPy now sees only bounded safe text: no power towers or computed exponents, no attribute access (`pi.n(...)`), at most 200 characters, and single letters bound to plain symbols.
  - **Prompts.** The probe prompts ask for a closing `Final answer: <answer>` line and plain ASCII equations, one chain per sentence (`grader-probes-v3`).
  - **Recorded detail.** Each check records `asserted_answer` and, when verified, `relations_checked`.
- **F17.** It is fixed by the same checker. Whole expressions are parsed with their unary signs, so `-1 + 3 = 2`, `2 * (-1) = -2`, `-(1 - 3) = 2` and `(1 + 3) / 2 = 2` hold, and `-1 + 3 = -2` is false. A run starts at the first math token, never inside an expression.
- **F5 (as-of history).**
  - **Written before the cutoff.** In a vault, every record must now also have been written before the diagnosed attempt (its `created_at`, parsed as UTC; an unparseable time fails closed). That covers cold observations, repair owners, hypotheses, unresolved factors, misconceptions and registry candidates. A source attempt that precedes the cutoff is no longer enough.
  - **Hypothesis versions.** All causal-hypothesis versions are loaded, since they are immutable audit rows. At each cutoff, the latest version written before it is shown, and a repair class's owners are those versions.
  - **Timestamps.** A mutable row's `last_updated` falls back to its creation time when the last update postdates the cutoff.
- **F11.** The route binding now records the profile's `max_tokens` and the output limit each metered request is held to (`spend.admitted_output_limit`: the route allowance or the profile's larger limit; `None` on subscription routes). A mismatch names the changed settings.
- **F12.**
  - **Drafted checkpoint.** A new probe draft is written at once as `drafted`, a retryable status that carries the draft and its probe id. That happens before it is verified or graded.
  - **Resume.** `drafted` and `grading_failed` rows are re-verified and graded under the same probe id. A cancellation or spend refusal mid-grading never pays to regenerate a draft.
  - **Excluded probes.** These now keep their draft in `detail` for audit.
- **F14.**
  - **Validated anchors.** Every E4 anchor is validated against the learner's answer, which the report now loads from the scratch copy. Offsets count only when the text there is the quote, up to whitespace. Otherwise the quote must occur exactly once.
  - **What never aligns.** Invented quotes, empty quotes (for example `missing_required_step` events) and ambiguous quotes are reported as *not localized*.
  - **Correspondence.** It needs overlapping validated spans and compatible targets.
  - **Report.** It shows unlocalized blind and stored events next to the unmatched and ambiguous counts.

### Deviations and notes

1. **Narrower valid-alternative coverage on symbolic vaults.** Any equation the exact checker cannot decide now excludes the draft, for example `A = U Sigma V^T`, LaTeX, `sqrt`, or `2x + 3 = 7`. This is what F4 asks for (nothing skipped), but in linear-algebra-style vaults most alternatives will now be `unverified`. The prompts steer generators toward checkable ASCII arithmetic, and the report shows every status.
2. **Prose is not machine-checkable.** A step written in words is not verified. For those steps the spec's "checked by CAS/sympy or the exact key" is met by the key check on the asserted conclusion. `relations_checked` records how much of a verified draft was actually checked.
3. **"and" is not a connective next to an equation**, because English uses it for addition ("1 and 1 = 2"). One existing test's derivation text changed from ", and 1+1 = 2" to ", so 1+1 = 2".
4. **Mutable registry rows still show their current status.** Factors, misconceptions and candidates have no status history. They now appear only once written before the cutoff, but their status is today's. The receipt's `lagged_attempts` discloses this as before. Causal hypotheses, which are versioned, are fully as-of.
5. **Older run directories cannot be resumed.** Runs started before these commits get `incompatible_resume`, because the probe prompt version and the route-binding fields changed. No owner run exists yet.

### Manual check (fakes only, on a backup-API copy)

- **Setup.** The earlier smoke run (`fixtures-local/m1-runs/review-fixes-smoke`) was copied with `learnloop.db.copies.copy_tree_with_databases`. `learnloop diagnose report --vault fixtures-local/m1-linear_algebra` rendered the report (15.6 KB).
- **E4 counts per arm.**
  - **Blind:** 6 localized but unmatched, 0 ambiguous, 0 not localized.
  - **Stored joint:** 3 localized but unmatched, 6 not localized. All 6 have no quote: `missing_required_step`, or an anchor with no kind.
- **Cleanup.** The copy was deleted afterwards.

### Gate (re-review)

All results are on `6e48861d`, the last fix commit; the commit after it records only this section.

| Gate | Result |
|---|---|
| `uv sync --extra dev` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 6 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` (run with `-q -p no:cacheprovider`) | **6265 passed**, 0 failed (14 warnings, pre-existing), 2 m 52 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` (run with `-q -p no:cacheprovider`) | **63 passed**, 6202 deselected, 0 failed, 37 s |
| Frontend (`npm run typecheck`, `npm test`) | not run: no frontend change |
| DB reference generate/validate | not run: no schema change |

New and changed tests:
- **`tests/test_diagnose_review.py`:**
  - **New:** 6 tests: the 3 F4/F17 checker tests, F11, F12 and F14.
  - **Extended:** `test_sympy_never_sees_model_text_outside_a_safe_math_alphabet`.
  - **Changed:** one derivation text in `test_a_valid_alternative_is_verified_on_its_submitted_derivation`; the E4 fixture now carries the learner answer.
- **`tests/test_diagnosis_history_modes.py`:** +1 (F5).
- **`tests/test_diagnose_review_spend.py`:** +1 (F16, pinned).
- **`tests/diagnosis_fakes.py`:** the fake valid alternative ends with a `Final answer:` line.

### Open questions for the owner (re-review)

1. **Valid-alternative coverage on symbolic items.** Should M1 add an owner-confirmed path for alternatives whose equations the exact checker cannot decide? See deviation 1. Today only checkable arithmetic and exact-key conclusions count.
2. **F16.** Should Codex also be exempt from `--max-calls`? That would change Slice A §5 rule 6 and the shared `SpendBudget(subscription=True)`, not just M1. Until then the call cap is the only bound on a runaway Codex loop.
