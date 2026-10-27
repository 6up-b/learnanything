# Codex CLI 0.164.0 lockdown: Codex review and fix step

Range reviewed: `5c6a0834f..fix/codex-cli-0164` (commits 182e5c55a, 2876dbf88).
Codex job: 20261027-100558-Tb4k2G (gpt-6.1-sol).

## Review

The Codex review found no actionable defects in the diff and established no false claims. Every
spec-conformance row is preserved or unaffected (transport compatibility only: no persisted
meaning, routing default, storage, replay, spend or grading-context change).

The reviewer could not run tests: its memory scope failed with `Failed to connect to user scope bus … Operation
not permitted`. The gate below reruns the implementer's tests on this machine against the installed
`codex-cli 0.164.0`, so the pass counts are now verified.

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| — | — | No actionable defects found | — | — | Nothing to fix |
| N1 | note (out of scope) | The frozen review `security-codex-tool-lockdown-codex-review.md` leaves skill-discovery and continuation gaps open on opt-in Codex routes | rejected for this stage (not introduced or closed here) | — | Predates this diff, and only opt-in Codex routes reach it (serving routes are plan-first per T1). Closing it would widen this stage's scope. It stays an open item for the owner's queue. |

No High findings, so no fixes were made.

## Gate (2026-10-27, worktree learnanything-astrafix, HEAD 2876dbf88 before this record)

- `uv sync --extra dev --extra mobile`: resolved 179 packages. `uv pip install pypdfium2`: installed 5.14.0.
- `uv run lint-imports --no-cache`: 36 kept, 0 broken.
- Installed CLI: `codex --version` reports `codex-cli 0.164.0`.
- Targeted pytest batch 1, `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6`:
  **838 passed, 1 skipped** (skip: `tests/test_codex_tool_lockdown.py:393`, the optional `openai_codex` SDK is not installed).
  Files: tests/test_codex_cli_0164_lockdown.py (alone: 15 passed), tests/test_codex_lockdown_frozen.py,
  tests/test_codex_lockdown_round2.py, tests/test_codex_lockdown_round3.py, tests/test_codex_tool_lockdown.py,
  tests/test_codex_isolation_mcp_check.py, tests/test_codex_runtime.py, tests/test_codex_output_schema.py,
  tests/test_codex_http_client.py, tests/test_codex_attempt_flow.py, tests/test_ai_tool_isolation.py,
  tests/test_ai_single_request.py, tests/test_ai_config.py, tests/test_e2e_codex_mock.py,
  tests/test_plan_first_transport.py, tests/test_provider_resolution_parity.py,
  tests/test_structured_transport_parity.py, tests/test_openai_chat_client.py, tests/test_output_budget.py.
- Targeted pytest batch 2 (same scope, `-n 6`): **564 passed**.
  Files: tests/test_architecture.py, tests/test_cli_ingest.py, tests/test_deferred_regrade.py,
  tests/test_diagnosis_history_modes.py, tests/test_diagnosis_input_provenance.py,
  tests/test_diagnosis_isolation.py, tests/test_e0_relabel_round.py, tests/test_e0_review_round4_followup.py,
  tests/test_e0_review_round5.py, tests/test_ingestion_checkpoints.py,
  tests/test_learner_review_system_entries.py, tests/test_lo_general.py, tests/test_pf_generation.py,
  tests/test_project_cli.py, tests/test_teach_back.py.
- I found these files with `git grep` for `codex_lockdown`, `providers.codex` and `codex_cli_fakes` under tests/.
- Not run, and not needed: no migration, DB or connection code changed, so no durability lane; no frontend
  or src-tauri change, so no vitest, npm or cargo; no schema change, so no DB reference scripts. The full suite is
  left to the landing gate (owner rule, 2026-10-17).
- I made no live or paid calls.
