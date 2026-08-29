# Test Suite Audit

Date: 2026-05-30

## Executive Summary

The Python test suite is healthy on the current working tree: the baseline run passed 492 tests, and after adding one focused repository test the final run passed 493 tests. There are no current skips or xfails. The earlier `python3 -m pytest` collection failures were caused by using Python 3.10 against a project that requires Python 3.12; `uv run pytest` is the correct workflow.

The biggest risk is not correctness drift but cost and shape: many product-critical behaviors are covered only through broad integration tests, especially CLI, sidecar, source ingestion, proposals, and TUI flows. Those tests are useful and nontrivial, but the full suite takes about 15 minutes, so new low-level helpers should get focused tests before relying on the full integration path.

## Test Suite Map

- Core algorithms: `test_fsrs.py`, `test_mastery.py`, `test_irt_difficulty.py`, `test_irt_end_to_end.py`, `test_surprise.py`, `test_calibration.py`, `test_recall_calibration.py`.
- Scheduler, probes, recall coverage, interventions: `test_scheduler.py`, `test_scheduler_golden.py`, `test_scheduler_probe_eig.py`, `test_probe_eig.py`, `test_probe_entry.py`, `test_probe_attempt_updates.py`, `test_probe_belief_posterior.py`, `test_hypothesis_sets.py`, `test_recall_coverage_interventions.py`, `test_facet_diagnostics_v03.py`, `test_self_attributed_misconceptions.py`.
- Attempts, grading, regrade, replay, followups: `test_attempts.py`, `test_attempt_ai_flow.py`, `test_codex_attempt_flow.py`, `test_codex_grading_validation.py`, `test_grading_context.py`, `test_self_grade.py`, `test_deferred_regrade.py`, `test_replay.py`, `test_followups.py`, `test_observation_templates.py`.
- Vault, persistence, migrations, doctoring: `test_init.py`, `test_migrations.py`, `test_repositories.py`, `test_state_sync.py`, `test_vault_writer.py`, `test_doctor.py`, `test_concepts.py`, `test_patch_compiler.py`, `test_patch_applier.py`, `test_proposal_persistence.py`, `test_proposal_review_policy.py`.
- CLI, AI runtime, Codex/OpenAI clients: `test_cli_commands.py`, `test_cli_entrypoint.py`, `test_cli_json.py`, `test_cli_attempt.py`, `test_cli_generate_practice.py`, `test_cli_ingest.py`, `test_cli_observations.py`, `test_cli_propose.py`, `test_agent_runs.py`, `test_ai_config.py`, `test_ai_runtime.py`, `test_codex_runtime.py`, `test_codex_output_schema.py`, `test_codex_http_client.py`, `test_openai_chat_client.py`.
- Ingestion and source grounding: `test_ingest_detect.py`, `test_ingest_fetchers.py`, `test_ingest_service.py`, `test_source_ingestion.py`, `test_source_ingestion_adapters.py`, `test_authoring_context.py`.
- TUI, sidecar, end-to-end contracts: `test_tui_app.py`, `test_tui_today.py`, `test_tui_practice.py`, `test_tui_feedback.py`, `test_tui_theme.py`, `test_sidecar_contract.py`, `test_e2e_local.py`, `test_e2e_codex_mock.py`, `test_e2e_tui.py`, `test_large_practice_flow.py`, `test_show.py`.

## Per-File Classification

Keep as is:
`test_agent_runs.py`, `test_ai_config.py`, `test_ai_runtime.py`, `test_attempt_ai_flow.py`, `test_attempts.py`, `test_authoring_context.py`, `test_calibration.py`, `test_cli_attempt.py`, `test_cli_commands.py`, `test_cli_entrypoint.py`, `test_cli_ingest.py`, `test_cli_json.py`, `test_cli_observations.py`, `test_cli_propose.py`, `test_codex_attempt_flow.py`, `test_codex_grading_validation.py`, `test_codex_http_client.py`, `test_codex_output_schema.py`, `test_codex_runtime.py`, `test_concepts.py`, `test_debug_advance.py`, `test_deferred_regrade.py`, `test_doctor.py`, `test_e2e_codex_mock.py`, `test_e2e_local.py`, `test_e2e_tui.py`, `test_facet_diagnostics_v03.py`, `test_followups.py`, `test_fsrs.py`, `test_grading_context.py`, `test_hypothesis_sets.py`, `test_ingest_detect.py`, `test_ingest_fetchers.py`, `test_ingest_service.py`, `test_init.py`, `test_irt_difficulty.py`, `test_irt_end_to_end.py`, `test_large_practice_flow.py`, `test_mastery.py`, `test_migrations.py`, `test_observation_templates.py`, `test_openai_chat_client.py`, `test_patch_applier.py`, `test_patch_compiler.py`, `test_probe_attempt_updates.py`, `test_probe_belief_posterior.py`, `test_probe_eig.py`, `test_probe_entry.py`, `test_proposal_persistence.py`, `test_proposal_review_policy.py`, `test_recall_calibration.py`, `test_recall_coverage_interventions.py`, `test_replay.py`, `test_scheduler.py`, `test_scheduler_golden.py`, `test_scheduler_probe_eig.py`, `test_self_attributed_misconceptions.py`, `test_self_grade.py`, `test_show.py`, `test_source_ingestion.py`, `test_source_ingestion_adapters.py`, `test_state_sync.py`, `test_surprise.py`, `test_tui_app.py`, `test_tui_today.py`, `test_vault_writer.py`.

Keep but improve:
`test_sidecar_contract.py` is useful but very broad; split future additions into handler-level tests where possible.
`test_tui_practice.py`, `test_tui_feedback.py`, and `test_tui_theme.py` are meaningful but expensive and should stay focused on user-visible behavior rather than CSS/private implementation details.
`test_cli_generate_practice.py`, `test_proposal_persistence.py`, and `test_source_ingestion.py` are current and important, but dense; future edge cases should prefer local helper/unit tests unless the CLI/API contract itself is under test.
`test_repositories.py` is useful and now includes the added streak regression test; keep adding small persistence tests here for new repository helpers.

Rewrite:
No tracked tests should be rewritten immediately. The only rewrite candidate is structural: over time, split `test_sidecar_contract.py` by contract surface (`sessions`, `practice`, `proposals`, `files`, `sqlite`) once the sidecar API stabilizes.

Remove:
No tracked test file or test function is currently obsolete enough to delete. Legacy-named tests still guard compatibility behavior such as old config sections, migration forward-compatibility, old attempt types, and legacy evidence wrappers.

Add new test coverage:
Added now: `test_session_day_streak_counts_active_and_alive_streaks` in `tests/test_repositories.py`.

## Recommended Removals

- Remove generated bytecode/cache artifacts: `tests/__pycache__`, `src/learnloop/**/__pycache__`, and `src/learnloop_sidecar/**/__pycache__`. These were removed.
- Do not remove `fixtures/linear_algebra_legacy`: it is still a valid compatibility fixture name and the suite exercises migration/config compatibility.
- Do not delete `test_grading_context.py::test_legacy_evidence_coverage_wrapper_is_score_independent`; it protects an active compatibility wrapper, not dead behavior.

## Recommended Rewrites

- No immediate rewrites. The current failing/stale-signal count is zero under the correct Python workflow.
- Future rewrite target: decompose `test_sidecar_contract.py` if sidecar development continues, because failures there would currently be slower to localize.

## Recommended Improvements

- Keep adding narrow repository/service tests for new helpers before exposing them through sidecar or CLI tests.
- Prefer behavior assertions over mock-call assertions. Current mock-heavy tests mostly mock clear boundaries (`openai`, optional fetchers, runtime health), which is acceptable.
- Consolidate repeated fake AI/Codex client setup only if repetition starts obscuring assertions. Local duplication is currently readable enough.
- Consider marker-based CI lanes later: fast unit/service subset on every push and full integration/TUI suite on PR or scheduled runs.

## Missing Coverage

Highest priority:
1. Session/streak edge cases around local date boundaries and duplicate sessions per day.
2. Sidecar serialization of newly added session/streak and diagnostic fields through the UI contract.
3. Additional negative tests for diagnostic proposal matching when multiple needs and multiple diagnostic items are generated without explicit source refs.
4. Fixture integrity checks that validate checked-in fixture vaults against current migrations and YAML schema.
5. Frontend/API DTO tests for recently changed Tauri client fields, if a JS test runner is introduced.

## Legacy Artifacts

- Removed: generated `__pycache__` directories under tests and source packages.
- Intentional, keep: `fixtures/linear_algebra_legacy`, legacy config mapping tests, and migration tests for older schemas.
- Watch: checked-in SQLite fixture files are large and changed in this working tree. They are product fixtures, not pytest goldens, but future changes should document why each DB fixture update is necessary.

## Action Plan

1. Safe deletions: keep generated caches out of the tree; no tracked tests deleted.
2. Low-risk refactors: extract sidecar contract helper assertions only when editing that area.
3. Rewrites: defer sidecar-contract splitting until API churn slows.
4. New tests: continue adding focused repository/service tests for new helpers; add sidecar serializer coverage for new public response fields.
5. CI/coverage: use `uv run pytest -q -ra` as the authoritative command; optionally add a fast subset lane once suite time becomes a bottleneck.

## Commands Run

- `python3 -m pytest --collect-only -q`: failed during collection because system Python is 3.10 and the project requires Python >=3.12.
- `uv run python --version`: `Python 3.12.13`.
- `uv run pytest -q -ra`: baseline result `492 passed in 933.96s`.
- `uv run pytest tests/test_repositories.py -q`: focused result `3 passed in 2.57s`.
- `uv run pytest -q -ra`: final result `493 passed in 907.07s`.

## Unresolved Risks

- The current worktree contains many pre-existing production, fixture, migration, and frontend changes. This audit did not attempt to separate ownership of those changes or revert them.
- No frontend TypeScript/Rust test suite was run; this audit focused on the configured pytest suite.
- The suite is passing but slow. Slow tests tend to discourage frequent local full-suite runs, so a future fast lane would be valuable.
