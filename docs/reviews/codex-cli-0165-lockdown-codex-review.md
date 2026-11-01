# Codex CLI 0.165 lockdown: Codex review

Range reviewed: `5dbfd42b8..fix/codex-cli-0165-lockdown` (head `cc07849b2`), reviewer gpt-6.1-sol,
job `20261031-154349-vTbH9v`. Stage record: `docs/reviews/codex-cli-0165-lockdown.md`.

## Review

The reviewer found **no actionable defects**. Both 0.165 default-on flags (`prediction_preserve_parent_tools`,
`reasoning_effort_override`) are switched off through the existing launch path, neither is in the permitted or
retired-feature exceptions, and either one reading back on still refuses the turn. The classification matches
the upstream 0.165 feature registry; `skills.bundled.enabled` matches upstream `skills_config.rs`. Spec
conformance table: every row implemented, preserved or unchanged.

The reviewer could not run the tests (its `systemd-run` scope failed with `Operation not permitted` on the
user bus), so the stage's pass counts were unverified. This fix step re-ran the gate independently (below):
the counts reproduce exactly.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| (none) | | No actionable defects found | n/a | n/a | n/a |

Noted, out of scope: the reviewer points out that this adaptation does not establish complete isolation for
**opt-in** Codex routes; the frozen review
(`docs/reviews/security-codex-tool-lockdown-codex-review.md`, around line 371) already records the open
explicit-only skill discovery, nested skill-cache invalidation and continuation gaps. This stage only adapts
the lockdown to CLI 0.165 and does not touch them. Serving routes run on tool-free `chatgpt_plan` (T1), and
Codex is refused unless explicitly opted in, so these remain tracked follow-ups, not regressions from this
diff.

No code change in this step.

## Gate (fix step)

* `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`: done.
* `uv run lint-imports --no-cache`: **36 kept, 0 broken.**
* Targeted pytest, one run under `flock /tmp/learnloop-fullsuite.lock`, inside
  `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `env -i` with empty, existing
  `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `uv run --no-sync pytest -n 6`: **1433 passed, 1 skipped** in
  138.2 s (same as the stage record; skip is the pre-existing `test_codex_tool_lockdown.py:393`,
  `openai_codex` not installed).

Test files run (36): `test_codex_cli_0165_lockdown.py`, `test_codex_cli_0164_lockdown.py`,
`test_codex_isolation_mcp_check.py`, `test_codex_lockdown_round2.py`, `test_codex_lockdown_round3.py`,
`test_diagnosis_isolation.py`, `test_codex_lockdown_frozen.py`, `test_codex_tool_lockdown.py`,
`test_ai_tool_isolation.py`, `test_ai_config.py`, `test_ai_single_request.py`, `test_codex_attempt_flow.py`,
`test_codex_http_client.py`, `test_codex_output_schema.py`, `test_codex_runtime.py`, `test_deferred_regrade.py`,
`test_diagnosis_history_modes.py`, `test_diagnosis_input_provenance.py`, `test_e0_corpus.py`,
`test_e0_relabel_round.py`, `test_e0_review_round4_followup.py`, `test_e0_review_round5.py`,
`test_e2e_codex_mock.py`, `test_ingestion_checkpoints.py`, `test_learner_review_system_entries.py`,
`test_lo_general.py`, `test_openai_chat_client.py`, `test_output_budget.py`, `test_pf_generation.py`,
`test_project_cli.py`, `test_provider_resolution_parity.py`, `test_structured_transport_parity.py`,
`test_teach_back.py`, `test_architecture.py`, `test_cli_ingest.py`, `test_plan_first_transport.py`.

No migration, DB, config default, frontend or Tauri change: no durability lane, snapshot regeneration, vitest
or cargo run. No paid or live calls.
