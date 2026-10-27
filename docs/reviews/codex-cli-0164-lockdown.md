# codex-cli-0164-lockdown: the isolated-turn launch check on Codex CLI 0.164.0

**Branch:** `fix/codex-cli-0164` in `learnanything-astrafix`, from `main` at `5c6a0834f`.
**Scope:** `src/learnloop/ai/providers/codex_lockdown.py`, `src/learnloop/ai/providers/codex.py`
(the launch check's feature step), `tests/codex_cli_fakes.py`, new `tests/test_codex_cli_0164_lockdown.py`.
**Migration / schema / config / frontend / successor:** none.
**Live or paid calls:** none. Every Codex command below ran under `env -i` with an empty,
existing `HOME` and `CODEX_HOME`, no sign-in and no model request.
**Kill switch:** unchanged. Plan routes (`chatgpt_plan`) never reach this check. Only opted-in
Codex turns run it, and it still fails closed.

## Symptom

The machine's Codex CLI is now `codex-cli 0.164.0`. The launch check refused every isolated
Codex turn with:

```
Codex does not report feature realtime_conversation, worktrees off under the isolated turn's overrides
(a tool, connector, plugin or sub-agent could load); refusing the isolated turn.
```

Ten tests that run the installed CLI failed: `test_codex_isolation_mcp_check` x3,
`test_codex_lockdown_round2` x3, `test_codex_lockdown_round3` x3 and
`test_diagnosis_isolation::test_configured_mcp_servers_are_listed_and_disabled`. I reproduced
all ten on `5c6a0834f` (10 failed, 100 passed in the four files).

## Evidence: what the two features are now

### CLI (empty `HOME`/`CODEX_HOME`)

`codex features list`:

```
realtime_conversation                    removed            true
worktrees                                removed            true
```

The listing is the same with `-c features.realtime_conversation=false -c features.worktrees=false`,
and the same with `--disable realtime_conversation --disable worktrees`. **The override does not
turn either one off.** That is why adding them to the disabled list could not fix this: both were
already in `LOCKDOWN_DISABLED_FEATURES`, which 0.163.0 needed, and 0.164.0 ignores the switch.
`codex features --help` says `--disable` is equivalent to `-c features.<name>=false`.
`codex --version` prints `codex-cli 0.164.0`.

### Source (tag `rust-v0.164.0`, commit `6aaac69`)

I read the source from a sparse, shallow, blob-less clone in the session scratchpad. It is not in
the repo.

* `codex-rs/features/src/lib.rs`, the feature specs: `Worktrees` has `stage: Stage::Removed,
  default_enabled: true`, with the doc comment *"Removed compatibility flag. Managed worktrees and
  repository-aware sessions are always available."* `RealtimeConversation` also has `Stage::Removed,
  default_enabled: true`, with *"Removed compatibility flag. TUI voice availability follows platform
  support."*
* `Features::apply_map` applies `features.*` from TOML and from `-c`. It skips both keys:
  `"tui_app_server" | "worktrees" | "realtime_conversation" => { continue; }`. So no configuration
  layer can change them, ours included.
* Nothing gates on either flag. Across `features/`, `core/src/`, `app-server/src/`, `tui/src/`,
  `exec/src/` and `cli/src/`, the only other reference is
  `core/src/config/managed_features.rs:246`. It warns *"Ignoring removed `features` requirement
  ... availability no longer depends on this feature flag"*.
* **Realtime conversation.** A voice session starts only when the client sends
  `ClientRequest::ThreadRealtimeStart` (`app-server/src/message_processor.rs:1022`). LearnLoop's
  client sends `thread_start` and `turn` and nothing else. The prompt-input readback declares no
  tool, and any realtime notification or item would be an unexpected item, which refuses the turn.
* **Worktrees.** The managed-worktree tools are `create_worktree`, `list_worktrees` and
  `get_worktree_creation_status` (`tui/src/managed_worktree_tool_specs.rs`). Only the TUI attaches
  them, and it does so on its own thread start (`tui/src/dynamic_tools_mcp.rs`
  `ThreadToolTransport::configure`): either as `params.dynamic_tools`, or as a local
  `codex_worktrees` MCP server inserted into that thread's `config`. LearnLoop's `thread_start`
  passes neither. `TurnLockdown` declines every `item/tool/call`, the launch check pins every MCP
  server off, and the readback must declare no tool.

**Conclusion.** Both flags are retired compatibility keys. The isolated turn cannot switch them
off, and in a turn LearnLoop starts they offer the model nothing.

### The three other features 0.164.0 turns on by default

Once the two retired flags passed, three more tests failed: the two
`test_the_installed_codex_passes_the_launch_check` cases and the diagnosis-isolation test. They
compare the exact overrides, and 0.164.0 has three features on by default that the lockdown had not
classified. The existing "unclassified" step switched each off and read it back off, so the turn
was safe, but the overrides changed. From the source:

| feature | stage, default | doc comment | classified |
|---|---|---|---|
| `bedrock_setup_wizard` | stable, on | Offer Amazon Bedrock setup during TUI sign-in onboarding | switched off |
| `incremental_tools` | stable, on | Track top-level tool definitions in world state and emit incremental context updates | switched off (the turn declares tools as on 0.163.0, where it was off; the readback still forces it on through `READBACK_OVERRIDES` to list every tool) |
| `mcp_oauth_refresh_coordination` | stable, on | Let RMCP coordinate OAuth refresh through the configured credential store | switched off (an isolated turn has no MCP server) |

On the real CLI, `-c features.<key>=false` turns each one off (`features list` shows `false`).
Switching a feature off only makes the turn stricter. The runtime result is the same as before,
when the unclassified step was already switching them off; the classification is now explicit and
reviewed.

## The fix

1. **`REVIEWED_RETIRED_FEATURES`** (`codex_lockdown.py`) maps `realtime_conversation` and
   `worktrees` to the reason each is reviewed. Such a feature may read on **only** when the same
   `features list` reports its stage as exactly `removed`. At any other stage it must read off, as
   before. Both stay in `LOCKDOWN_DISABLED_FEATURES`, so a CLI that still reads the switch (0.163.0)
   turns them off and the launch keeps sending `features.<key>=false`.
2. **The check's rule is unchanged.** `feature_violations(states, shell=..., stages=...)` still
   names every feature that is on unless it is permitted. There is no allowlist for unknown features
   and no tolerance for `removed` as such: an **unreviewed** feature reported `removed` and on still
   refuses, and so does a required-off one (`apps`, `plugins`, `multi_agent`). Called without
   stages, the function behaves exactly as before. `SdkCodexClient._feature_listing` parses the
   stage column, the words between the name and the state (for example `under development`).
3. **A clearer refusal for the next CLI.** `feature_refusal(...)` builds the message. It names the
   CLI version (`codex --version`, run only on the refusal path; if that probe fails it says
   `version unknown`, and only a line shaped like a version reaches the message, never stderr or a
   config line). It also names each feature with its reported stage, says when Codex no longer reads
   a removed feature's switch, and names where to classify the feature (`PERMITTED_FEATURES` or
   `REVIEWED_RETIRED_FEATURES` in `codex_lockdown.py`). For example:

   ```
   Codex (codex-cli 0.165.0) does not report feature future_tool (removed) off under the isolated turn's
   overrides (a tool, connector, plugin or sub-agent could load); refusing the isolated turn. Codex no
   longer reads the switch of a removed feature (future_tool), so no override turns it off. Isolated Codex
   turns stay refused on this CLI until future_tool is reviewed for it and classified in
   learnloop/ai/providers/codex_lockdown.py (PERMITTED_FEATURES for a non-tool feature,
   REVIEWED_RETIRED_FEATURES for a removed flag that offers the turn nothing).
   ```

   This changes only the message. Nothing is tolerated automatically.
4. **`bedrock_setup_wizard`, `incremental_tools` and `mcp_oauth_refresh_coordination`** are added
   to `LOCKDOWN_DISABLED_FEATURES`.

### Will the next CLI break the same way?

* **A new feature that is on by default and whose switch works** is switched off automatically by
  the existing unclassified step and must read back off. The turn runs. The installed-CLI tests that
  compare exact overrides will fail, and that failure is the signal to classify the feature.
* **A feature that is retired and on, or a new one whose switch is ignored,** refuses. The new
  message names the version, the stage and the place to classify it, so the owner or an agent knows
  exactly what to review.
* **A reviewed retired flag that comes back at another stage** must read off again.

## Tests

* New: `tests/test_codex_cli_0164_lockdown.py`, 15 tests, all using the fake CLI or pure
  functions:
  * the pin on the reviewed list: exactly the two flags, still disabled, never permitted or
    required-off;
  * a retired flag may read on only at stage `removed`, checked against five other stages and
    against a call with no stages;
  * an unreviewed `removed` feature still refuses, and so does a required-off one;
  * the content of the refusal message;
  * version-text sanitizing;
  * on a fake 0.164.0, the turn runs and the switches are still sent;
  * a reviewed flag at stage `stable` with an ignored switch refuses;
  * a newer CLI's unreviewed retired feature refuses and the message names version, stage and
    where to classify it;
  * a failing `--version` probe still refuses, with the message saying `version unknown` and
    leaking nothing.
* Fake CLI: `tests/codex_cli_fakes.py` gains `feature_stages` (the stage column) and `version`
  (`--version`).
* Existing fake-binary pins are kept and pass. These include
  `test_codex_tool_lockdown.py::test_a_tool_bearing_feature_the_cli_leaves_on_refuses_the_turn`,
  which now also covers the five 0.164.0 names at stage `stable` with the switch ignored,
  `test_an_unclassified_feature_that_stays_on_refuses_the_turn` and
  `test_an_enable_flag_for_an_unclassified_feature_refuses_the_turn`.
* The ten installed-CLI tests pass against the real 0.164.0. No test is skipped or xfailed by this
  change.

## Gate (this step; the full suite runs once in the landing gate)

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: done.
* `uv run lint-imports --no-cache`: **36 kept, 0 broken.**
* Pytest. Every run was inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`,
  used `-n 6`, ran under `flock /tmp/learnloop-fullsuite.lock`, and used `env -i` with empty,
  existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.
  * The four installed-CLI files, before the fix: **10 failed, 100 passed.**
  * Those four plus the new file, after the fix: **125 passed.**
  * Final run of the 33 files listed below: **1362 passed, 1 skipped** in 105 s.

Test files run:
`test_codex_cli_0164_lockdown.py`, `test_codex_isolation_mcp_check.py`, `test_codex_lockdown_round2.py`,
`test_codex_lockdown_round3.py`, `test_diagnosis_isolation.py`, `test_codex_lockdown_frozen.py`,
`test_codex_tool_lockdown.py`, `test_ai_tool_isolation.py`, `test_ai_config.py`, `test_ai_single_request.py`,
`test_codex_attempt_flow.py`, `test_codex_http_client.py`, `test_codex_output_schema.py`, `test_codex_runtime.py`,
`test_deferred_regrade.py`, `test_diagnosis_history_modes.py`, `test_diagnosis_input_provenance.py`,
`test_e0_corpus.py`, `test_e0_relabel_round.py`, `test_e0_review_round4_followup.py`, `test_e0_review_round5.py`,
`test_e2e_codex_mock.py`, `test_ingestion_checkpoints.py`, `test_learner_review_system_entries.py`,
`test_lo_general.py`, `test_openai_chat_client.py`, `test_output_budget.py`, `test_pf_generation.py`,
`test_project_cli.py`, `test_provider_resolution_parity.py`, `test_structured_transport_parity.py`,
`test_teach_back.py`, `test_architecture.py`.

These are the files that import the Codex provider, the lockdown module or the fake CLI, or that
check the experiments boundary (`disabled_features`). One pre-existing skip:
`test_codex_tool_lockdown.py:393`, because `openai_codex` is not installed. No migration, DB,
frontend or Tauri change, so there is no durability lane, vitest or cargo run.

## Open items

* The installed-CLI tests that compare exact overrides will go red whenever a Codex update adds a
  new feature that is on by default, even though the product switches that feature off and runs.
  This is deliberate, because it is the classification signal. Turning them into "unclassified
  extras allowed" tests would hide the signal, so that is left to the owner.
* There are many leftover `learnloop-codex-catalog-*` directories in `/tmp`, from earlier runs and
  not from this stage's code path. I neither inspected nor removed them. This may be worth a
  follow-up check on whether some exit path leaves them behind.
