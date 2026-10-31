# codex-cli-0165-lockdown: the isolated-turn launch check on Codex CLI 0.165.0

**Branch:** `fix/codex-cli-0165-lockdown` in `learnanything-dl0`, from `main` at `5dbfd42b8`.
**Scope:** `src/learnloop/ai/providers/codex_lockdown.py` (two features added to
`LOCKDOWN_DISABLED_FEATURES`, docstrings), `tests/codex_cli_fakes.py` (the fake renders bundled skills),
new `tests/test_codex_cli_0165_lockdown.py`.
**Migration / schema / config / frontend / successor:** none.
**Live or paid calls:** none. Every Codex command below ran under `env -i` with an empty, existing `HOME`
and `CODEX_HOME` (session scratchpad), no sign-in and no model request (`features list`, `--version`,
`--help`, `debug prompt-input`).
**Kill switch:** unchanged. Plan routes (`chatgpt_plan`) never reach this check. Only opted-in Codex
turns run it, and it still fails closed.

## Symptom, and a correction to the brief

`/usr/lib/node_modules/@openai/codex` was updated on 2026-10-29; `codex --version` prints
`codex-cli 0.165.0`. Three installed-CLI tests failed on `main` (reproduced here: 3 failed, 54 passed in
`test_diagnosis_isolation.py` + `test_codex_isolation_mcp_check.py`):
`test_diagnosis_isolation::test_configured_mcp_servers_are_listed_and_disabled` and
`test_codex_isolation_mcp_check::test_the_installed_codex_passes_the_launch_check[False]/[True]`.

The brief (from the CA3 landing gate) names the two entries as `features.prediction_preserve_parent_tools`
and `skills.bundled`. The full diff (`pytest -vvv`) shows the two extra overrides are actually:

```
+     'features.prediction_preserve_parent_tools=false',
+     'features.reasoning_effort_override=false',
```

`skills.bundled.enabled=false` came from pytest's truncated summary (*"Left contains 2 more items, first
extra item: 'skills.bundled.enabled=false'"*): that is a positional artefact of the list diff. The override
has been on every launch since hardening round 3 (`skill_disable_overrides`) and is in both lists.

Also: the check did **not** refuse the turn on 0.165.0. Both features honour their switch, so the existing
"unclassified" step switched each off and read it back off, and the turn would have run. The tests failed
because they compare the exact overrides, which is the deliberate classification signal recorded in the
0.164 review. This stage classifies both, and still records evidence for `skills.bundled` as asked.

## Evidence

### CLI (empty `HOME`/`CODEX_HOME`)

`codex features list`, default:

```
prediction_preserve_parent_tools         stable             true
reasoning_effort_override                stable             true
```

With `-c features.prediction_preserve_parent_tools=false -c features.reasoning_effort_override=false`, and
again with `--disable prediction_preserve_parent_tools --disable reasoning_effort_override`:

```
prediction_preserve_parent_tools         stable             false
reasoning_effort_override                stable             false
```

`codex features --help`: *"--disable <FEATURE> Disable a feature (repeatable). Equivalent to
`-c features.<name>=false`"*. **Both switches work.**

Every other feature 0.165.0 reports on is already classified (computed against `PERMITTED_FEATURES`,
`LOCKDOWN_DISABLED_FEATURES` and `SHELL_FEATURES`: unclassified-and-on = exactly these two; no classified
name is missing from the listing). `realtime_conversation` and `worktrees` are still `removed true`.

`features list` has **no `skills.bundled` row** (nor any row for a `skills.*` key); the only skill rows are
`skill_env_var_dependency_prompt` (removed, false), `skill_mcp_dependency_install` and `skill_search` (both
already in `LOCKDOWN_DISABLED_FEATURES`) and `skip_host_skill_discovery` (under development, false).

`codex debug prompt-input` (renders the model-visible input; no model request), with
`-c skills.max_context_tokens=10000`:

* default: one `<skills_instructions>` block listing `imagegen`, `openai-docs`, `skill-creator`,
  `skill-installer` from the root `$CODEX_HOME/skills/.system` (0.165.0 installs `review-agent` there too
  but does not list it);
* plus `-c skills.bundled.enabled=false`: **no `<skills_instructions>` block**;
* plus `-c skills.bundled=false` instead: Codex refuses to load the configuration, *"invalid type: boolean
  `false`, expected struct BundledSkillsConfig in `skills.bundled`"* (same for `features list`).

So `skills.bundled` needs its own path, `skills.bundled.enabled`, which is what LearnLoop sends.

### Source (tag `rust-v0.165.0`, commit `360319d`)

Read from a shallow, blob-less clone in the session scratchpad (not in the repo), compared with the 0.164.0
clone from the previous stage.

* **Feature spec diff 0.164.0 → 0.165.0** (`codex-rs/features/src/lib.rs`): new keys
  `prediction_preserve_parent_tools` (Stable, on), `guardian_recorded_items`, `guardianv3`,
  `tui_multi_backend` (all UnderDevelopment, off); `reasoning_effort_override` moved from
  UnderDevelopment/off to Stable/on. Nothing else changed stage or default. `Features::apply_map` is
  byte-identical to 0.164.0 (it skips neither new key, matching the CLI result).
* **`prediction_preserve_parent_tools`**, doc comment *"Preserve inherited tool declarations in
  MCP-disabled prediction forks."* Read only in `core/src/session/mod.rs`
  `preserve_parent_tool_declarations()`: the feature **and** the `McpServersDisabled` thread marker. The
  marker is set only by the app server's `thread/fork` with `experimental_disable_prediction_mcp`
  (`request_processors/thread_processor.rs:5367`) and by `thread/sample` with `disable_mcp`
  (`thread_sample.rs:209`). When it holds, the fork skips re-emitting its own `TopLevelToolsState`
  (`session/world_state.rs:168`) so the parent's `additional_tools` declarations stay in its context, and
  adds an *"MCP tools are unavailable for this request"* notice (`session/mod.rs:1806`). It is about which
  tool declarations the model sees, so it is treated as security-relevant. LearnLoop's client sends only
  `thread_start` and `turn`, never a fork or sample, so the marker can never be set on its threads; it is
  switched off anyway (off is stricter: a fork would declare only its own router's tools).
* **`reasoning_effort_override`**, doc comment *"Append trusted response configuration items when the
  selected reasoning effort changes."* When on (and the provider is OpenAI and the model supports effort
  updates), `session/reasoning_effort.rs` `record_reasoning_effort_override` appends a harness-authored
  `ResponseItem::ConfigurationUpdate` (serialized type `configuration_update`) to history, and
  `client.rs` `build_responses_request` keeps it in the request input. When off, effort stays a
  request-level parameter and any such item is filtered from the request copy. No tool, connector, plugin,
  skill or sub-agent. It is switched off because that is exactly 0.164.0's behaviour (it was off by default
  there), it keeps the turn's input free of an item kind the prompt-input readback does not know, and
  LearnLoop already sets effort per turn (`effort=` on the SDK turn).
* **`skills.bundled`** (`config/src/skills_config.rs`): `SkillsConfig.bundled: Option<BundledSkillsConfig>`
  with `enabled: bool` (default `true`); `bundled_skills_enabled_from_stack` reads it. It is a config
  table, not a feature, so no `features.*` key reaches it. Note that an invalid `skills` table makes that
  function warn and return `true` (bundled on); that is why the wrong path must never be used and why the
  launch check reads the effect back in `debug prompt-input` rather than trusting the key.
* The 0.164.0 retired flags still gate nothing (`Feature::Worktrees`/`Feature::RealtimeConversation`
  appear only in `core/src/config/managed_features.rs:246` and tests).

## The fix

1. `prediction_preserve_parent_tools` and `reasoning_effort_override` are added to
   `LOCKDOWN_DISABLED_FEATURES`, each with a comment saying what it does and why it is off. Every isolated
   launch now sends `features.<key>=false` for both, and the launch check requires both to read `false`.
2. **The check's rule is unchanged.** Neither name is permitted, and neither is a reviewed retired flag:
   if a CLI leaves either on (switch ignored, or reported `removed`), the turn is refused. An unknown new
   feature is still switched off and must read back off, or the turn refuses. No allowlist, no skip, no
   xfail.
3. `skills.bundled`: no code change was needed. `skill_disable_overrides` already sends
   `skills.bundled.enabled=false` on every launch; its docstring now records that the key is a config table
   (not a feature), that the bare boolean form fails to load, and that the effect is read back.

## Tests

* New `tests/test_codex_cli_0165_lockdown.py`, 11 tests, all on the fake CLI or pure functions:
  * both names are switched off, never permitted, never retired-tolerated; reading on refuses at stage
    `stable` and at stage `removed`;
  * every launch (shell on and off) sends both `features.*=false` and `skills.bundled.enabled=false`,
    never a `features.*` skills key or a bare `skills.bundled=`;
  * fake 0.165.0 with both on by default and working switches: the turn runs, both off in the launch and in
    the single `features list` probe (no unclassified round);
  * fake 0.165.0 with each name's switch ignored (on): the turn is refused, naming
    `codex-cli 0.165.0` and the feature at `(stable)` (parametrized over both names);
  * an unknown new feature left on still refuses (message names the version and what to review), and
    one whose switch works is switched off and the turn runs;
  * bundled skills, both override paths: `skills.bundled.enabled` alone clears them (no `skills.config`
    needed); a CLI that ignores it gets each bundled skill disabled by name and path through
    `skills.config`; a CLI that ignores both refuses (*"still lists skills"*).
* `tests/codex_cli_fakes.py`: the fake's `debug prompt-input` lists `bundled_skills` unless
  `skills.bundled.enabled=false`, and `ignored_skill_overrides` models a CLI that ignores that key or
  `skills.config`; skill roots are numbered per directory (`r0`, `r1`, ...) as the real CLI does.
* Mutation check: with the two names removed from `LOCKDOWN_DISABLED_FEATURES`, 7 tests fail (4 of the new ones, plus
  the 3 installed-CLI tests); restored, all pass.
* The 3 installed-CLI tests pass against the real 0.165.0. The existing fake-binary pins
  (`test_codex_tool_lockdown.py::test_a_tool_bearing_feature_the_cli_leaves_on_refuses_the_turn`, which is
  parametrized over `LOCKDOWN_DISABLED_FEATURES` and so now covers both new names with the switch ignored;
  `test_an_unclassified_feature_that_stays_on_refuses_the_turn`; the 0.164 file) pass unchanged.

## Gate (this step; the full suite runs once in the landing gate)

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: done.
* `uv run lint-imports --no-cache`: **36 kept, 0 broken.**
* Pytest, every run inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6`,
  under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`:
  * before the fix, `test_diagnosis_isolation.py` + `test_codex_isolation_mcp_check.py`: **3 failed, 54 passed**;
  * after the fix, the new file, the 0.164 file and the four installed-CLI files: **136 passed**;
  * final run (under `flock /tmp/learnloop-fullsuite.lock`) of the 36 files below: **1433 passed, 1 skipped**
    in 112.5 s. The skip is pre-existing: `test_codex_tool_lockdown.py:393` (`openai_codex` not installed).

Test files run (the 0.164 stage's set, plus the new file and every test file `git grep` finds importing the
lockdown module, the Codex provider or the fake CLI):
`test_codex_cli_0165_lockdown.py`, `test_codex_cli_0164_lockdown.py`, `test_codex_isolation_mcp_check.py`,
`test_codex_lockdown_round2.py`, `test_codex_lockdown_round3.py`, `test_diagnosis_isolation.py`,
`test_codex_lockdown_frozen.py`, `test_codex_tool_lockdown.py`, `test_ai_tool_isolation.py`, `test_ai_config.py`,
`test_ai_single_request.py`, `test_codex_attempt_flow.py`, `test_codex_http_client.py`,
`test_codex_output_schema.py`, `test_codex_runtime.py`, `test_deferred_regrade.py`,
`test_diagnosis_history_modes.py`, `test_diagnosis_input_provenance.py`, `test_e0_corpus.py`,
`test_e0_relabel_round.py`, `test_e0_review_round4_followup.py`, `test_e0_review_round5.py`,
`test_e2e_codex_mock.py`, `test_ingestion_checkpoints.py`, `test_learner_review_system_entries.py`,
`test_lo_general.py`, `test_openai_chat_client.py`, `test_output_budget.py`, `test_pf_generation.py`,
`test_project_cli.py`, `test_provider_resolution_parity.py`, `test_structured_transport_parity.py`,
`test_teach_back.py`, `test_architecture.py`, `test_cli_ingest.py`, `test_plan_first_transport.py`.

No migration, DB, config default, frontend or Tauri change, so no durability lane, snapshot regeneration,
vitest or cargo run.

## Open items

* The brief's `skills.bundled` was a misreading of pytest's truncated diff; the real second feature is
  `reasoning_effort_override`. Recorded above so the landing gate reads the change correctly.
* 0.165.0's other new keys (`guardianv3`, `guardian_recorded_items`, `tui_multi_backend`) are off by
  default and were not classified. If a user config turns one on, the unclassified step switches it off and
  requires it to read off (the turn runs; the exact-override tests would flag it). Adding `guardianv3` next to
  `guardian_approval`/`guardianv2` is a possible follow-up, left out here to keep the change to what 0.165.0
  turns on.
* The installed-CLI exact-override tests will keep going red on each Codex update that adds a default-on
  feature, by design (the 0.164 review's open item stands).
