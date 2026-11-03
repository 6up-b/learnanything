# codex-cli-0166-lockdown: the isolated-turn launch check on Codex CLI 0.166.0

**Branch:** `fix/codex-cli-0166-lockdown` in `learnanything-dl0`, from `main` at `392970f3db`.
**Scope:** `src/learnloop/ai/providers/codex_lockdown.py` (eight features added to
`LOCKDOWN_DISABLED_FEATURES`, comments), `tests/codex_cli_fakes.py` (the fake app server reports its plugin
startup tasks), new `tests/test_codex_cli_0166_lockdown.py`.
**Migration / schema / config / frontend / successor:** none.
**Live or paid calls:** none. Every Codex command below ran under `env -i` with an empty, existing `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` (stage scratch directory), no sign-in and no model request
(`features list`, `--version`, `--help`, `debug prompt-input`, plus one direct `debug models --bundled`, which
prints the catalog in the binary, and the launch check's own probes, from a small script under the same `env -i`).
`codex app-server` was not started by hand, so the network result below rests on source reading, not a traffic
capture (see Open items). No turn ran outside pytest; inside it, the existing `test_codex_lockdown_frozen.py` runs
one against its loopback stand-in. The only network use was the two public source clones.
**Kill switch:** unchanged. Only opted-in Codex turns run this check, and it still fails closed.

## Verdict

**No new 0.166.0 capability can run on an isolated Codex turn, and nothing had to be refused.** The launch
check on the real CLI passes. Plugin discovery makes no request and loads nothing on an isolated turn: all of
it sits behind `features.plugins`, which has always been required off.

The plan route is not affected. `chatgpt_plan` never reaches this check, and nothing in this review suggests
otherwise: `providers/chatgpt_plan.py` and `ai/chatgpt_plan/` do not import the lockdown, the Codex provider or
start a `codex` process (`git grep`).

## Symptom, and the hypothesis tested

`/usr/lib/node_modules/@openai/codex` was updated on 2026-11-02 19:35; `codex --version` prints
`codex-cli 0.166.0`. Reproduced here on the base commit, 3 failed:
`test_diagnosis_isolation.py::test_configured_mcp_servers_are_listed_and_disabled` and
`test_codex_isolation_mcp_check.py::test_the_installed_codex_passes_the_launch_check[False]/[True]`.

The landing agent's hypothesis holds. The full `pytest -vvv` diff of each is exactly one line:

```
+     'features.plugin_discovery_prefetch=false',
```

The check did not refuse the turn: the feature honours its switch, so the existing "unclassified" step
switched it off and read it back off. The tests failed because they compare exact overrides, the deliberate
classification signal recorded in the 0.164 review.

## Evidence: features

Source is tags `rust-v0.165.0` (`360319d`) and `rust-v0.166.0` (`6ff1e1c`), from shallow, blob-less clones in
the stage scratch directory (not in the repo). The feature table is compared from `features/src/lib.rs`: 185 ->
193 keys, **8 new, 1 changed, 0 gone**. `Features::apply_map` is byte-identical, so none of the new keys is
skipped. Against the lockdown's lists, 0.166.0's `features list` gives exactly one unclassified feature on
(`plugin_discovery_prefetch`, shell on and off) and no classified name is missing.

Switches, read back from `features list` in an empty environment:

| Feature | Stage, default | `-c =true` / `--enable` | `-c =false` / `--disable` | `-c true` then `-c false` |
|---|---|---|---|---|
| `plugin_discovery_prefetch` | stable, **on** | on / on | off / off | off |
| `critical_path_timing` | under development, off | on / on | off / off | off |
| `guardian_native_multi_agent_history` | under development, off | on / on | off / off | off |
| `mcp_connection_sharing` | under development, off | on / on | off / off | off |
| `omit_skill_descriptions` | under development, off | on / on | off / off | off |
| `simplified_selection_hints` | under development, off | on / on | off / off | off |
| `skill_catalog_deltas` | under development, off | on / on | off / off | off |
| `untrusted_as_tool_output` | under development, off | on / on | off / off | off |
| `code_mode_tool_description_first` (changed) | **removed** (was under development), off | on / on | off / off | off |

**All honour their switch.** Under the full isolated overrides (81 keys, from the real
`_verified_isolated_overrides`) all eight read off, with `plugins` and `remote_plugin` off too; 28 features read
on, all permitted or reviewed-retired, none new.

What each does, at every non-test read site in 0.166.0:

| Feature | What it does | Run code | Network | Plugins or tools | Read files | On an isolated turn |
|---|---|---|---|---|---|---|
| `plugin_discovery_prefetch` | See below | No | Yes, if `plugins` is on | Fetches catalog data into a cache, loads nothing | Writes a cache under `CODEX_HOME` | Inert twice over, and off |
| `mcp_connection_sharing` | `core/src/config/mod.rs:1978` -> `discover_local_stdio`; `codex-mcp/src/connection_manager.rs:592`: discovers the protocol of a local stdio MCP server, shares connections | Yes, the configured server | Only what that server does | MCP tools | Only what that server does | No server is on (`mcp list` must read each off), and off |
| `skill_catalog_deltas` | `ext/skills/src/catalog_delta.rs`: skill additions and edits reach the context as deltas | No | No | Skills' metadata | Skill metadata | No skill listed, and off |
| `omit_skill_descriptions` | `ext/skills/src/config.rs`: descriptions dropped from the rendered catalog | No | No | Shape only | No | No skill listed, and off |
| `simplified_selection_hints` | `core/src/plugins/render.rs:27`: a shorter developer hint when a client selects a plugin | No | No | Text only | No | Plugins off, and off |
| `untrusted_as_tool_output` | `core/src/session/turn_input.rs:958`: client-supplied additional context as named tool outputs, not messages | No | No | No tool, but a tool-output item in the input | No | LearnLoop's providers send no additional context (`git grep`), and off |
| `critical_path_timing` | `core/src/tools/parallel.rs:86` and others: records internal timing paths | No | No | No | No | Off |
| `guardian_native_multi_agent_history` | `core/src/tools/multi_agent_tool.rs:126`, `guardian/prompt.rs:165`, `ext/guardian-v2/.../config.rs:86`: Guardian reviews state-changing multi-agent calls | No | Guardian's own model call | No | No | Needs multi-agent v2 and Guardian, both off, and off |
| `code_mode_tool_description_first` | No reader left, only its row in the feature table | No | No | No | No | Off |

`mcp_connection_sharing` has one more reason to send the switch explicitly:
`core/src/config/runtime_refresh.rs` lets a host default set it during a runtime refresh unless a layer names the
key. The `-c` override is such a layer.

## Evidence: plugin discovery

Doc comment (`features/src/lib.rs:358`): *"Prefetch the plugin directory, featured plugins, and recommendations
at app-server startup. Inventory-only hosts can disable this. Legacy suggestions read the cached directory."*

**It is a switch for existing traffic, not new traffic.** The diff of `core-plugins/src/manager.rs` shows 0.165.0
ran the same fetches unconditionally behind `plugins_enabled`. 0.166.0 adds the `prefetch_discovery` parameter and
an early return.

The only read is `app-server/src/message_processor.rs:573`, passed to
`maybe_start_plugin_startup_tasks_for_config` (`manager.rs:2885`), whose whole body is `if
config.plugins_enabled { ... }` (`:2893`). `plugins_enabled` is `features.enabled(Feature::Plugins)`
(`core/src/config/mod.rs`, `plugins_config_input`). So with `features.plugins=false` nothing is spawned: no curated
repo sync, marketplace auto-upgrade, installed-plugin refresh, bundle sync, recommendations, catalog refresh or
featured-plugin fetch.

**The prefetch switch alone would not be enough.** Codex's own test
(`app-server/tests/suite/v2/plugin_list.rs:2022`) runs with `features.plugin_discovery_prefetch=false` and still
downloads a remote plugin bundle. The lock that matters is `features.plugins`, in `REQUIRED_OFF_FEATURES`: it must
be listed and read off or the turn refuses. `test_the_real_lock_on_plugin_startup_stays_required` pins that, and
the mutation below shows it fails if `plugins` leaves that list.

Every other way in, each checked:

* Each function has its own gate: `maybe_start_curated_repo_sync_for_config` (`:772`), the installed-plugins
  refresh (`:1643`), `maybe_start_remote_installed_plugin_bundle_sync` (`:1670`),
  `maybe_start_remote_catalog_cache_refresh` (`:1857`), `featured_plugin_ids_for_config` (`:1949`),
  `recommended_plugins_mode_for_config` (`:1980`, also needs `remote_plugin` and backend auth),
  `plugins_for_config` (`:832`, returns no plugins, so nothing loads) and
  `plugin_skill_snapshots_for_config` (`:808`).
* Two callers hard-code `prefetch_recommendations` true, `account_processor.rs:319` (account change) and
  `manager.rs:1886` (`plugin/list`). Both reach only the gated functions above, and LearnLoop's client sends
  neither request.
* The startup config keeps the overrides on both paths. The normal path is built with `cli_kv_overrides`
  (`app-server/src/lib.rs`), and the *"Invalid configuration; using defaults"* fallback uses
  `load_default_config`, which still applies `current_cli_overrides()` (`config_manager.rs:481`) while ignoring
  the user and project layers. An invalid config cannot turn plugins back on.
* `features list` and the app server read the same value (`config.features.enabled`, `cli/src/main.rs:1940`).

The new crate that sounds like a risk, `plugin-host` (*"Bounded IPC and lifetime management for the dedicated V8
plugin process"*), has no production caller in 0.166.0. `--codex-ui-plugin-process` is parsed in
`code-mode-host/src/main.rs:99`, and only tests spawn it (`PluginProcess`, `HELPER_ARGUMENT`:
no non-test site outside the crate). It is not wired to a feature, a tool or the app server, so no switch applies.
If a later CLI wires it in, it needs its own review.

Readback on the real CLI (`debug prompt-input`, incremental form): four message items, no `<skills_instructions>`
block, `rendered_skills` empty, no tool declared, no occurrence of `plugin`. With only the prefetch switched back
on, the items are the same apart from generated ids, timestamps and the arg0 temp path: as expected, the prefetch
has no prompt effect. Running these commands wrote only `installation_id` and `.sandbox_migration` to the empty
`CODEX_HOME`, so no plugin cache was created by the CLI paths exercised; those paths do not start the app server,
so this says nothing further about startup traffic.

## Evidence: everything else that changed

| Surface | 0.165.0 -> 0.166.0 | Reaches an isolated turn? |
|---|---|---|
| CLI (`cli/src/main.rs`, `doctor.rs`, `queue_cmd.rs`; `app-server/src/main.rs`) | `queue --resume`, `doctor --network-only` (its WebSocket probe, called only from `doctor.rs`), `exec-server` moved to the `exec-server-cli` crate, no new global or app-server flag. 0.165's review did not record `--help` text, so this is a source diff of the clap definitions; 0.166.0's `--help` is in the stage scratch directory | No. LearnLoop runs only `codex --config ... app-server --listen stdio://` and the check's probes |
| Tools | No new tool: `spec_plan.rs` changes a parameter, `handlers/mod.rs` a visibility; the three new literal tool names are in test files; `native_tool_review.rs` is Guardian's | No. The readback declares none, and the launch check would refuse one |
| Server requests (`ServerRequest`) | Same set | Any request is a violation, the turn is stopped |
| Client requests | Adds `account/gcp/setup`, `accountSession/list`, `accountSession/switch` | LearnLoop's client sends none |
| Item kinds | `ThreadItem` wraps `ThreadItemPayload` with start and completion times, flat on the wire; 19 kinds, same names | `item_kind` still reads `type`; only text kinds are allowed, an unknown kind refuses |
| Model catalog | `ModelInfo` 47 fields, unchanged; adds `gpt-6.1-terra`; new approval-message templates (text) | Every entry is pinned tool-free; `debug models` must return that pin, and passes. `model_catalog_json` still gives a `StaticModelsManager` |
| Config schema | New: `AwsSigV4Config`, `BodySecretSubstitutionConfig` (`NetworkMitmActionToml`, only in the network proxy), `ModelProviderInfo.credential_file`, `project_id`, `location` (GCP providers), `memories.consolidation_service_tier`, `rollout_budget.enforce_limit`, a TUI key. Changed: `thread_unload_delay_secs` default 1800 -> 60, `GatewayOAuthConfig.delivery` optional | The proxy, memories and rollout budget are off and the profile has no network. A GCP provider is a lower layer's own provider choice, not a new capability. A thread with subscribers is not unloaded |
| Extensions (`app-server/src/extensions.rs`) | No new `install`; two new fields on the skills config. Cloud skills predate 0.166.0, and their provider exists only with `--cloud-skills-snapshot`, which LearnLoop does not pass | No |
| Startup (`app-server/src/lib.rs`, `message_processor.rs`) | Renamed cloud-config loader, marketplace warnings through a channel; no new background task outside the plugin gate | No new reach |
| Package | Linux vendor directory holds `codex`, `codex-code-mode-host`, `rg`, `bwrap`, the voice host. The 0.165.0 package was not available to compare (nothing installed or downgraded) | `code_mode_host` is an already reviewed permitted feature; `tool_mode` is pinned to `direct` |

## The fix

1. All eight new names are added to `LOCKDOWN_DISABLED_FEATURES`, each with a comment saying what it does and why
   it is off. Every isolated launch sends `features.<key>=false`, and the launch check requires each to read
   `false`. Seven default off in 0.166.0: classifying them means a config layer that turns one on is caught in the
   first listing, and that the turn's readback keeps today's shape.
2. **The check's rule is unchanged.** No name is permitted or a reviewed retired flag: if a CLI leaves one on
   (switch ignored, or reported `removed`), the turn is refused. An unknown new feature is still switched off and
   must read back off, or the turn refuses. No allowlist, no skip, no xfail.
3. `code_mode_tool_description_first` is left unclassified on purpose. It is off, retired, and has no reader. If a
   layer turns it on, the existing step switches it off and requires it to read off; if its switch stopped working,
   the turn refuses. Both cases are tested.
4. `PERMITTED_FEATURES` and `REVIEWED_RETIRED_FEATURES` are untouched.

## Tests

* New `tests/test_codex_cli_0166_lockdown.py`, 22 tests, all on the fake CLI or pure functions:
  * all eight are switched off, never permitted, never retired-tolerated; reading on refuses at stage `stable` and
    at stage `removed`;
  * `plugins` stays in `REQUIRED_OFF_FEATURES`, and a listing with it missing refuses;
  * every launch (shell on and off) sends all eight and `features.plugins=false`;
  * fake 0.166.0: the turn runs, all eight off in the launch and in the single `features list` probe (no
    unclassified round); the fake app server starts no plugin task and has no plugin-brought server;
  * the fake's model of the prefetch: off alone leaves the bundle sync running, `plugins` off leaves nothing;
  * each name's switch ignored: the turn is refused, naming `codex-cli 0.166.0` and the feature at `(stable)`
    (parametrized over all eight); `plugins` ignored refuses whatever the prefetch says; the prefetch retired by a
    later CLI with its switch ignored refuses;
  * a 0.165.0 listing without the new rows still runs;
  * the retired flag on with a working switch is switched off, with an ignored one refuses;
  * an unknown new feature left on still refuses (message names the version and what to review), and one whose
    switch works is switched off and the turn runs.
* `tests/codex_cli_fakes.py`: the fake app server prints `plugin_startup_tasks`, modelled on 0.166.0's
  `maybe_start_plugin_startup_tasks_for_config`.
* Mutation checks: with the eight names removed from `LOCKDOWN_DISABLED_FEATURES`, 9 tests fail (6 of the new ones,
  plus the 3 installed-CLI tests); with `plugins` removed from `REQUIRED_OFF_FEATURES`,
  `test_the_real_lock_on_plugin_startup_stays_required` fails. Restored, all pass.
* The 3 installed-CLI tests pass against the real 0.166.0. The existing fake-binary pin
  `test_codex_tool_lockdown.py::test_a_tool_bearing_feature_the_cli_leaves_on_refuses_the_turn` is parametrized over
  `LOCKDOWN_DISABLED_FEATURES`, so it now covers all eight with the switch ignored.

## Gate (this step; the full suite runs once in the landing gate)

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: done.
* `lint-imports --no-cache` (in the worktree venv, under `env -i`): **42 kept, 0 broken.**
* Pytest, every run inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6`, under
  `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`:
  * before the fix, the three tests: **3 failed**;
  * after the fix, the new file, the 0.165 and 0.164 files and the two installed-CLI files: **105 passed**;
  * final run (under `flock /tmp/learnloop-fullsuite.lock`) of the 37 files below: **1464 passed, 1 skipped** in 116.9 s. The skip is pre-existing: `test_codex_tool_lockdown.py` (`openai_codex` not installed).

Test files run (the 0.165 stage's set plus the new file, which is also every test file `git grep` finds using the
lockdown module, the Codex provider or the fake CLI, and every file naming the installed CLI):
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

The brief's "12 test files that use the real CLI" comes from `docs/reviews/followups-batch7.md`, which does not name
them. A search here for the installed CLI finds 9 files, all in this set; this set is a superset of the lockdown
stage's files rather than a reproduction of that exact 12.

No migration, DB, config default, frontend or Tauri change, so no durability lane, snapshot regeneration, vitest or
cargo run.

## Open items

* **No traffic capture.** The brief limits Codex commands to ones that do not start the app server, so "no network
  request on an isolated turn" is proven from source and from the switches' readback. A capture would mean
  starting the real app server against a loopback `chatgpt_base_url` and recording what it asks for, as
  `test_codex_lockdown_frozen.py` already does for a turn. Left out rather than worked around through a test; a
  reviewer or the owner can decide if it is worth having.
* `plugin-host` and `--codex-ui-plugin-process` are unwired in 0.166.0. No switch reaches them; the watch point is a
  later CLI wiring them in, which would need a feature (then classified) or a tool (then refused).
* 0.165.0's other new keys (`guardianv3`, `guardian_recorded_items`, `tui_multi_backend`) remain unclassified, as
  that review left them. They are off by default, and the unclassified step covers a layer that turns one on.
* The installed-CLI exact-override tests will keep going red on each Codex update that adds a default-on feature,
  by design (the 0.164 review's open item stands). They block every landing's full suite until classified.
