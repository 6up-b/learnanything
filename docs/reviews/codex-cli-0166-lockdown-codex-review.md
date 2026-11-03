# Codex CLI 0.166 lockdown: Codex review

Range reviewed: `392970f3db..29a7ce0792` (branch `fix/codex-cli-0166-lockdown`), reviewer gpt-6.1-sol, job
`20261102-202322-ChcLAW`. Stage record: `docs/reviews/codex-cli-0166-lockdown.md`.

## Review

The reviewer found **no actionable defects**. All eight new feature keys are switched off, none gains a permitted
or retired-feature exception, and a key that stays on still refuses the turn. The local 0.166 source confirms that
plugin startup tasks stay behind `features.plugins`, so switching off the prefetch alone would not be enough.
Spec conformance table: every row implemented, preserved or unchanged.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| (none) | | No actionable defects found | n/a | n/a | n/a |

The reviewer named two limits on what it could validate. Neither is a defect; this step settles the first and
leaves the second as it stands.

* **Pass counts unverified.** Its `systemd-run` scope could not reach the user bus, so pytest did not start there.
  This step re-ran the gate: the count reproduces exactly (below).
* **The plugin startup tests exercise the fake.** True, and already stated in the test's docstring and in the stage
  record's "No traffic capture" open item. The upstream source supports the fake's model, but no test proves the
  real app server sends nothing. The stage brief does not allow starting the real app server by hand, so this stays
  an open item for the owner or a later stage, not something for this step to work around.

Noted, out of scope: the reviewer repeats that the earlier reviews' skill-discovery, cache-invalidation and
continuation gaps remain open. This stage neither introduces nor closes them
(`docs/reviews/security-codex-tool-lockdown-codex-review.md`). Serving routes run on tool-free `chatgpt_plan`, and
Codex is refused unless opted in.

No code change in this step.

## Checks repeated on the real CLI

Under `env -i` with an empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`; `--version` and
`features list` only, no sign-in, no model request:

* `codex --version`: `codex-cli 0.166.0`.
* All eight are in `LOCKDOWN_DISABLED_FEATURES`. Stages and defaults match the stage record: `plugin_discovery_prefetch`
  stable and on, the other seven under development and off.
* `unclassified_features_on` over the listing as shipped, shell on and off: empty.

One correction to the stage record, with no effect on its result: its "185 -> 193 keys" misses the dotted row
`guardianv2.thread_context`, which is in both versions at stage `removed`. Counted with it, the registry goes
186 -> 194, and `features list` prints 194 rows. The difference is still the same 8 new keys and none gone.

## Gate (fix step)

* `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`: done (no tracked file changed).
* `lint-imports --no-cache` (worktree venv, `env -i`): **42 kept, 0 broken.**
* Targeted pytest, under `flock /tmp/learnloop-fullsuite.lock`, inside
  `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `env -i` as above, `python -m pytest -n 6`:
  **1464 passed, 1 skipped** in 113.1 s, the same count as the stage record. The skip is the pre-existing one in
  `test_codex_tool_lockdown.py` (`openai_codex` not installed).
* `tests/test_config_refactor.py`, which a broad `git grep` also matched: **53 passed**. The match was a false
  positive (`providers[codex_name]`), not a use of the lockdown; run to be sure.

Test files run (the stage record's 37, unchanged):
`test_codex_cli_0166_lockdown.py`, `test_codex_cli_0165_lockdown.py`, `test_codex_cli_0164_lockdown.py`,
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

No migration, DB, config default, frontend or Tauri change, so no durability lane, vitest, build or cargo run. The
full suite is left to the landing gate. No live or paid calls.
