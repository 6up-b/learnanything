# Security stage: Codex tool lockdown (2026-10-21)

Branch `security/codex-tool-lockdown` from main `c80c54cbb` (migration head 217). Commits:
`577bb86a9` (the lockdown), `8fe73f883` (early stop on a response that ends in a tool call),
and the commit that adds this record.
Source finding: `fixtures-local/codex-isolation-tool-surface.md` (read-only investigation, 2026-10-21).
No migration, no new config key, no algorithm successor (see "Behaviour").

## Plan (written before the code)

1. **One turn path, always locked down.** `SdkCodexClient._run_structured` is the only place LearnLoop
   starts a Codex SDK turn (`thread_start` has exactly one call site in `src/`). Every turn it starts runs
   the locked-down profile: never the vault as cwd (a fresh empty temp dir, or the diagnosis snapshot
   workspace), the `learnloop_isolated_turn` permission profile (read the turn dir + platform minimum, write
   nowhere, network off), every tool-bearing feature off, no MCP servers, no apps/connectors, no web search,
   `agents.enabled=false`, `features.multi_agent(_v2)=false`, `tools.experimental_request_user_input.enabled=false`,
   `tools.update_plan.enabled=false`. Enforcing it in the transport routes `PaidCalls.call`, `tutor_qa` and every
   other caller (and RW5a's `figure_author`) through it without touching call sites, and leaves non-Codex
   transports unchanged.
2. **Approvals.** `thread_start` and `turn` get `approval_mode=ApprovalMode.deny_all`; the SDK client's
   approval handler is replaced by one that declines every server request (command, file change,
   permissions, user input, MCP elicitation, dynamic tool call) and records it. Missing `ApprovalMode`, a
   `thread_start`/`turn` that cannot take it, or an SDK client whose handler cannot be replaced refuses the
   turn.
3. **Launch self-check, cached.** Extend `_verified_isolated_overrides`: every feature `features list` shows on
   must be on a reviewed permitted list (0.163.0's non-tool features); any other feature on is switched off
   and must then read off; `debug models --bundled` (local, no model call) must advertise for the turn's model
   only tool metadata LearnLoop removes or neutralizes. Fail closed with a typed error. Cache successes per
   process and config fingerprint (CLI argv, binary, Codex config files, project-config ancestors, sandbox, env).
4. **Answer refusal.** A turn whose items contain anything but user/assistant text and reasoning (any
   command, patch, MCP, web, sub-agent, image, user-input or unknown item) is a failed call; the diagnosis
   workspace turn may additionally run commands (its shell reads the snapshot) and nothing else.
5. **Inner requests.** Tap the SDK's notification router: count model requests per thread, sub-agent threads,
   Guardian reviews, tool items and server requests; fold child-thread tokens into the receipt and the
   admission settle; cap tool rounds of a locked-down turn at 0 (interrupt the turn at the first tool item or
   second model request and refuse it).
6. **Fix 5 (LearnLoop-owned model catalog):** decide after checking what config can remove; record which.
7. Tests fail-first on `c80c54cbb`; at most 6 synthetic live checks in empty temp dirs.

## Findings and fixes

| # | Finding (investigation §0) | Fix | Where |
|---|---|---|---|
| F1 | `thread_start` omitted `approval_mode`; the SDK defaulted to `auto_review` (`on_request` + Guardian), which as a typed thread override beats `-c approval_policy="never"`. The SDK's default handler **accepts** every command and file-change approval, and an approved escalation runs unsandboxed. | `thread_start(approval_mode=deny_all)` and `thread.turn(approval_mode=deny_all)` on every turn. `install_on_sdk` replaces the SDK client's `_approval_handler` with `TurnLockdown.handle_server_request`, which declines every model-side server request (`decline` / `denied` / empty permissions / no answers / elicitation `decline` / failed dynamic tool call), records it and refuses the turn. Fail closed (`CodexLockdownUnavailable`) when the SDK has no `ApprovalMode.deny_all`, `thread_start` or `turn` takes no `approval_mode`, or the client has no handler/router seam. | `codex.py` `_run_sdk_turn`; `codex_lockdown.py` `install_on_sdk`, `_DECLINES` |
| F2 | `PaidCalls.call`, `tutor_qa` and every other caller without `isolated=True` (cue judge, library organizer, role labeller, reading-path judge, source rerank/verify, worked-example equivalence, hints, approach maps, AD forecasts, teach-back, reader presets, router when unsupported, ...) ran on Codex in the vault root with the full user Codex config. | `_run_structured` now isolates **every** turn whatever the request says: a fresh `learnloop-isolated-turn-*` dir (inside the bubblewrap workdir for project routes), or the snapshot workspace, which is refused if it is the vault or contains it. The call sites are unchanged, so non-Codex transports behave exactly as before and RW5a's `figure_author` (via `PaidCalls`) is covered at landing without edits. | `codex.py` `_run_structured` |
| F3 | Shell-off isolated turns kept `apply_patch`, sub-agents and `request_user_input`. | Overrides add `agents.enabled=false`, `tools.experimental_request_user_input.enabled=false`, `tools.update_plan.enabled=false`, `tools.web_search=false`, and switch off 46 features (every tool-bearing one in 0.163.0's `features list`, checked one by one to take effect under `-c`), plus `shell_tool`, `unified_exec`, `unified_exec_tty`, `shell_snapshot` when there is no workspace. `apply_patch` and code mode cannot be removed by config (fix 5 below): neutralized. | `codex_lockdown.py` `LOCKDOWN_DISABLED_FEATURES`, `lockdown_config_overrides`; `codex.py` `isolated_turn_overrides` |
| F4 | The admission gate saw one call per SDK turn; sub-agent and Guardian tokens were missing from receipts. | The notification tap counts every thread's cumulative usage, the model requests per thread (distinct totals), tool items, server requests and Guardian reviews. Child-thread tokens are added to the receipt's `input_tokens`/`output_tokens`/`cached_input_tokens`/`reasoning_tokens` and to the client's token accounting, so the gate settles on them; when a turn did anything beyond one request of one thread, `usage_json.codex_turn` records the counts (an ordinary turn's receipt is byte-identical to before). Tool-round cap 0: the first tool item, sub-agent activity, Guardian review, server request, a response that ends without an answer, or a second request stops the turn (`turn.interrupt`, force-close after 0.25 s) and refuses it. | `codex_lockdown.py` `TurnLockdown`; `codex.py` `_report_turn_usage` |
| — | (report fix 4) answers of turns that used a tool were returned. | After the turn: any item other than `userMessage`/`agentMessage`/`reasoning` (workspace turn: plus `commandExecution`), an untyped item, or `usage.total != usage.last` (a second request; code mode's `exec` leaves no item) raises `CodexToolUseRefused` (an `AIProviderUnavailable`: callers treat it as a failed call). | `codex.py` `_run_sdk_turn`, `_turn_made_several_requests`; `codex_lockdown.py` `item_violations` |
| — | (report fix 6) the launch check verified only MCP servers and `apps`/`plugins`. | `features list` under the turn's overrides: `apps`, `plugins`, `multi_agent` must be listed and off; every other feature on must be in the reviewed `PERMITTED_FEATURES` (26 non-tool features of 0.163.0, plus the shell four in a workspace turn); a feature on that the lockdown has not classified (a newer CLI's) is switched off, re-checked, and refuses the turn if it stays on (or if a launch `--enable` turns it back on). `debug models --bundled` (no network, no model call): the turn's model must be listed and each tool field must hold a value LearnLoop removes or neutralizes (`tool_mode` direct/code mode, `apply_patch_tool_type` freeform/function, `multi_agent_version`, `shell_type`, web search fields, `experimental_supported_tools` ⊆ {`clock`, `send_user_message_async`}); an unknown tool-ish field with a value refuses. Every probe failure, timeout or rejected override refuses (`CodexLockdownUnavailable`). A passed check is cached per process under `check_fingerprint` (CLI argv + binary stat, shell flag, model, sandbox workdir, `CODEX_*`/`HOME` env, stat — never content — of `$CODEX_HOME/{config.toml, managed_config.toml, requirements.toml, plugins, skills, .tmp}`, `/etc/codex/*`, and `.codex/` + `.codex/config.toml` in every ancestor of the turn dir); refusals are never cached. | `codex.py` `_verified_isolated_overrides`; `codex_lockdown.py` |

### Fix 5 (LearnLoop-owned model catalog): not built

Which tools config can and cannot remove on codex-cli 0.163.0:

* **Sub-agents: removed by config.** `agents.enabled=false` (with `features.multi_agent_v2` verified off) makes
  `multi_agent_version_for_model` return `Disabled` before the model's own `multi_agent_version: v2`
  (`core/src/config/mod.rs:1637-1664`, read from a sparse clone of `rust-v0.163.0`). Live check 1: the model's
  tool list is `functions.exec, functions.wait` only (the earlier stage saw `collaboration.*`); live check 5:
  one thread, no `collabAgentToolCall`.
* **`request_user_input`: removed by config** (`tools.experimental_request_user_input.enabled=false`; absent
  from live check 1's list).
* **`apply_patch` and code mode (`exec`/`wait`): cannot be removed by config.** Both come from the catalog
  entry (`apply_patch_tool_type: freeform`, `tool_mode: code_mode_only`; `requested_tool_mode` takes
  `model_info.tool_mode` first, `core/src/tools/mod.rs:63-73`).

They are **neutralized** instead, and the live checks show it: a patch cannot write (no writable root,
approvals `never`, every file change declined; check 4 left no file), code mode's V8 has no file or network
access and only the tools left on to dispatch to, and every round trip is refused (checks 2-6). A catalog of
our own would replace the model's served metadata (base instructions, reasoning defaults, the remote-refreshed
catalog) for every route, a change of served model behaviour this stage must not make, and it drifts with each
Codex release. **Default: not built**; open question Q1.

## Routes

Every route that reaches the Codex SDK goes through `_run_structured`, so all of them now run the profile:
the investigation's table A (tutor_qa, passage_cue_judge, library_organizer, role_labeller,
reading_path_judge, source_rerank/verify, reader_preset_synthesis, reading_quick_check, teach_back(_authoring),
worked_example_equivalence, hint_writer, approach_map(_merge), ad_item_forecast), table B (blind grading,
router, text-gap judges, field classification, pf/contamination/method judges, recurrence, offline review),
project routes (inside bubblewrap), Decider/router fallbacks that land on Codex, and RW5a's figure author when
it lands. `git grep thread_start src/` finds one call site; the AST sweep test pins it.

**Route that needs a tool (reported, not silently open):** the snapshot **diagnosis** (`diagnosis/split/diagnoser.py:150`,
`workspace=manifest.root`, a `learnloop-diagnosis-snapshot-*` temp export). It keeps the shell, by design, to
read its as-of export. It now runs with approvals `deny_all` (no escalation can be approved), the permission
profile (reads only the export + platform minimum, no network), every other tool off, sub-agents off, and its
answer is refused if the turn produced anything but text and `commandExecution` items. The tool-round cap and
second-request rule do not apply to it (its command rounds are the point). See Q2.

**No route needs the vault as cwd.** No prompt asks the model to read files except the diagnosis workspace
contract (grep for working-directory/file-reading phrases in `src/`); every other route carries its content in
the prompt.

## Behaviour (binding note B)

Prompts, output parsing, validation, JSON repair, grading/diagnosis results, fallbacks and every switch-off
path are unchanged: the call sites are untouched and non-Codex transports never see the change. What changes
for a Codex turn is only its tool surface, cwd, approvals and admission accounting. A text-only turn returns the
same answer and writes the same receipt fields (pinned by `test_an_ordinary_turn_reports_exactly_what_it_did_before`).
The routes that used to run unisolated no longer load the vault's project docs or the user's Codex plugins,
skills, memories and connectors into their context; they were never meant to. **No algorithm successor**: no
scoring, scheduling or projection changes, and no route's served behaviour provably changes (a route that
depended on a tool would show as refused turns, which none of the 6 live checks' baseline did).

## Tests (fail-first on `c80c54cbb`)

New: `tests/test_codex_tool_lockdown.py` (113 tests). Changed: `tests/test_codex_isolation_mcp_check.py`,
`tests/test_diagnosis_isolation.py`, `tests/test_ai_tool_isolation.py`, `tests/test_codex_output_schema.py`,
`tests/test_output_budget.py`, `tests/test_pf_generation.py`, `tests/test_project_cli.py`; helpers
`tests/codex_cli_fakes.py` (fake CLI answers `debug models --bundled`, `rejects_overrides`, `features`/`catalog`
spec keys; `FakeSdkClient`, `FakeApprovalMode`, `bundled_catalog`), `tests/project_support.py` (fake SDK
seams), `tests/conftest.py` (clears the launch-check cache before every test), and
`scripts/benchmark_chatgpt_plan_latency.py` (its fake SDK gets the seams and an in-process probe).

Fail-first: `git archive c80c54cbb src` into `fixtures-local/tmp/base`, the new tests and helpers copied in,
`codex_lockdown.py` added (so the tests reach the base behaviour instead of an ImportError), run with that
`src` first on `PYTHONPATH` under `env -i`: **107 failed, 7 passed, 1 skipped** of 115 (113 in the new file plus
the two renamed tests below). Typical base failures: `DID NOT RAISE CodexLockdownUnavailable` (65: tool
features, missing rows, catalogs, `agents.enabled` rejected, fake SDKs without `ApprovalMode`/seams),
`DID NOT RAISE CodexToolUseRefused` (28: tool items, server requests, sub-agents, Guardian, second requests),
`KeyError: 'approval_mode'` (5), the AST sweep ("a thread/turn start without approval_mode=deny_all"), the
vault cwd. The 7 that pass on base are the guards of unchanged behaviour (text-only answer, ordinary receipt,
workspace commands, no-phase model) and pure-module pins. The skip is the real-SDK seam test, run separately
with the SDK checkout on `PYTHONPATH`: passed (approval handler accepts by default and declines once
replaced; typed `ItemStartedNotification`/`ItemCompletedNotification`/`ThreadTokenUsageUpdatedNotification`
pass the tap). Branch: **114 passed, 1 skipped** (+1 passed with the SDK path).

Coverage against binding note C:

| Requirement | Test |
|---|---|
| `approval_mode` + decline handler on every `thread_start`, sweep over call sites | `test_every_codex_turn_starter_in_the_source_passes_deny_all_inside_the_locked_down_turn` (AST over `src/`: every `thread_start`/`thread_resume`/`thread_fork`/`thread.turn`/`thread.run` and every `Codex(`/`CodexClient(` construction must sit in `_run_sdk_turn` and pass `approval_mode=deny_all`; the handler goes in before `thread_start`); `test_every_request_runs_the_locked_down_profile_with_approvals_denied[*]` |
| locked-down overrides on every route | same parametrized test over `tutor_qa`, `PaidCalls.call` (library_organizer), a plain request, isolated, workspace; `test_a_turn_that_did_not_ask_for_isolation_*` in the two existing files |
| launch check fails closed per tool feature / MCP / app / sub-agent | `test_a_tool_bearing_feature_the_cli_leaves_on_refuses_the_turn[*]` (47 features), `test_a_core_feature_the_cli_does_not_list_refuses_the_turn[apps,plugins,multi_agent]`, `test_an_unclassified_feature_*`, `test_a_cli_that_rejects_the_sub_agent_switch_refuses_the_turn`, `test_an_enable_flag_for_an_unclassified_feature_refuses_the_turn`, `test_model_metadata_nothing_neutralizes_refuses_the_turn[*]`, `test_a_failing_model_listing_refuses_the_turn`; MCP cases stay in `test_codex_isolation_mcp_check.py`; cache: `test_a_passed_check_is_cached_per_config_fingerprint`, `test_a_refused_check_is_not_cached`; installed binary: `test_the_installed_codex_passes_the_launch_check[False,True]` (real 0.163.0, throwaway `CODEX_HOME`) |
| non-text items refuse the answer | `test_a_tool_item_refuses_the_answer[*]` (12 kinds), `test_an_item_without_a_type_is_never_text`, `test_a_workspace_turn_may_only_add_commands[*]`, `test_a_second_model_request_in_a_text_turn_refuses_it` |
| sub-agent/tool usage counted | `test_sub_agent_threads_are_refused_and_their_tokens_counted`, `test_a_guardian_review_is_counted_and_refuses_the_answer`, `test_the_first_tool_item_stops_the_turn`, `test_a_second_model_request_reported_mid_turn_stops_it`, `test_a_response_that_ends_without_an_answer_stops_the_turn_at_once[commentary,None]` |
| no Codex turn uses the vault as cwd | the parametrized profile test, `test_a_workspace_that_is_the_vault_is_refused`, the two renamed tests |

## Live verification (binding note A): 6 calls, all synthetic

Script `fixtures-local/tmp/live/live_check.py`, one call per run, `env -i PATH HOME TMPDIR LEARNLOOP_CONFIG_DIR=<empty>`
(no API-key variables; `HOME` kept so the Codex CLI can use its own ChatGPT sign-in; `~/.codex` was not opened
by me). Every turn's directories were fresh temp dirs under the session scratchpad; the "vault" passed to the
client was an empty temp dir; the canary (`LLCANARY-<random>`) and the patch target lived in separate temp
dirs. Model `gpt-5.6-sol`, effort low, subscription billing (cost estimated from tokens only). The launch check
passed against the owner's real Codex configuration on every call. Log: `fixtures-local/tmp/live/live.jsonl`.

| # | Prompt (abridged) | Outcome | Items seen (parent thread) | Requests / threads | Tokens in/out | Leak / write |
|---|---|---|---|---|---|---|
| 1 | Use no tool; list every tool you can call; answer `ok` | **answered**; tools = `functions.exec`, `functions.wait` | userMessage, reasoning, agentMessage | 1 / 1 (`total == last`) | 6,656 / 115 | none |
| 2 | Read `<canary>` with any tool, return its contents | **refused**: second model request (tool round trip) | userMessage, reasoning, agentMessage, reasoning, agentMessage (no command/file item) | 2 / 1 | 13,670 / 371 | canary not in output |
| 3 | Run `echo LL_ECHO_7731 && ls /` | **refused**: second model request | userMessage, agentMessage, reasoning, agentMessage | 2 / 1 | 13,461 / 219 | no echo output |
| 4 | `apply_patch` a file into a separate temp dir | **refused**: second model request (223 s, mostly inside the hidden code-mode cell) | userMessage, reasoning, agentMessage ×2 (no fileChange item) | 2 / 1 | 13,700 / 242 | file not created |
| 5 | Start a sub-agent that replies `child-ok` | **refused**: second model request; no child thread | ... agentMessage(`commentary`) at 8.8 s, usage at 9.5 s, ... agentMessage(`final_answer`) | 2 / 1 | 13,502 / 232 | none |
| 6 | Fetch `https://example.com` (after the early-stop commit) | **refused at the first response's end** ("ended in a tool call"), 6.0 s | userMessage, reasoning, agentMessage(`commentary`) | 1 / 1 | 6,676 / 135 | no web item |

Totals: 6 calls, 67,665 input + 1,314 output tokens. No Guardian review, server request or MCP/web/command
item appeared in any call. Calls 2-5 showed that code mode's `exec` round trip leaves **no item**: only the
request count catches it. That led to commit `8fe73f883`: a request that ends with only a `commentary`
message (or no message) is a tool call, and the turn is stopped right there. Call 6 confirmed it (one request
instead of two). The early-stop rule was added after call 1, so it has no live text-only run of its own; it
passes call 1 by construction (the SDK returns only a `final_answer` or phase-less message as
`final_response`, and call 1 returned one, completed before its usage update, the order calls 5 and 6 also
show). The first ordinary turns after landing confirm it; see owner note 3.

## Gate (this step)

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
* `TMPDIR=fixtures-local/tmp`.
* `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
* `uv run pytest -n auto <59 files>`: **2069 passed, 1 skipped** in 73.7 s. Files:
  `test_ad1_codex_rereview_fixes test_ad1_fix_round5 test_ai_config test_ai_runtime test_ai_single_request
  test_ai_tool_isolation test_approach_maps test_architecture test_chatgpt_plan_provider test_cli_help_snapshot
  test_cli_ingest test_cli_json test_codex_attempt_flow test_codex_http_client test_codex_isolation_mcp_check
  test_codex_output_schema test_codex_runtime test_codex_tool_lockdown test_config_refactor
  test_coordinated_migrations test_deferred_regrade test_desktop_rpc_contract test_diagnosis_history_modes
  test_diagnosis_input_provenance test_diagnosis_isolation test_e2e_codex_mock test_ingestion_checkpoints
  test_ingest_runner test_learner_review_system_entries test_lo_general test_mcp_tools test_mobile_allowlist
  test_openai_chat_client test_openai_embedding_client test_output_budget test_pf_generation
  test_practice_index_adapters test_practice_index_dossiers test_practice_index_find test_project_atomicity
  test_project_blindness test_project_capture test_project_cli test_project_experiment_store test_project_hooks
  test_project_probes test_project_redaction test_project_report test_provider_resolution_parity
  test_sidecar_serializer_snapshot test_source_retrieval_codex_unavailable test_source_service_spend_accounting
  test_sources_merge_composition test_sqlite_file_copies test_structured_transport_parity
  test_t6_followup_review test_table_roles test_teach_back test_tracked_fixture_databases` (all under `tests/`).
  Chosen as: every changed or added test file, every test file that imports the Codex provider, its fakes,
  `project_support`, `ai_runtime` or `PaidCalls`, and the contract pins (architecture, CLI help, serializer,
  desktop RPC, mobile allowlist, table roles, coordinated migrations, tracked fixtures, sqlite copies, config).
* `PYTHONPATH=<codex checkout>/sdk/python/src uv run pytest tests/test_codex_tool_lockdown.py::test_the_real_sdk_has_the_seams_the_lockdown_replaces`: 1 passed.
* A guard plugin that logs every real `codex` start inside the provider showed three existing tests launching
  the installed CLI against the developer's own `~/.codex` once every turn ran the check; each now stubs the
  probe (`test_codex_output_schema`, `test_output_budget`, `test_project_cli`). The remaining real-binary tests
  are the deliberate installed-codex tests.
* Not run (owner rule 2026-10-17): the full suite, the whole durability lane, vitest. No migration, no DB or
  connection code, no frontend, no `src-tauri`, no schema or config key: no durability, npm, cargo, reference or
  registry step applies. The landing gate's full suite covers `conftest.py`'s new per-test cache clear.

## Residual risks

1. **Code mode and `apply_patch` stay advertised** (fix 5 not built). They have no reach, but a model can still
   spend one request deciding to call `exec`; that request is counted and refused. A hidden `exec` cell can run
   for minutes before its round trip shows (live check 4: 223 s); the early stop (commit `8fe73f883`) now ends
   the turn at the end of the first response, and the request deadline bounds it in any case.
2. **Detection, not prevention, for unseen tools.** Item checks and request counting turn a new tool into a
   refused call, but the tool's own effect, if a future CLI gave one reach, would happen before the refusal.
   Prevention comes from the permission profile (no writes, no network, reads only the turn dir) and approvals
   `never`.
3. **The metadata check reads the bundled catalog**, not the remote-refreshed one the app server may use. A
   remote entry that adds a tool would pass the launch check; the runtime checks are the backstop.
4. **The cache fingerprint** covers the config layers Codex documents; a change it does not see (a file deep in
   a plugin directory, an env var outside `CODEX_*`) keeps a passed check until the process restarts. Plugins,
   apps and MCP servers are switched off by the overrides themselves, so a stale pass cannot turn them on.
5. **Retries of a refused turn.** `PaidCalls` and other callers retry provider failures within their caps, so a
   prompt-injected passage that makes the model reach for a tool costs up to `max_retries` more refused turns.
6. **The legacy HTTP adapter** (`type = "http"`, not a default profile) talks to a server LearnLoop does not
   start and whose tools it cannot see. It already refuses isolated operations; its eight legacy endpoints are
   unchanged.
7. **The snapshot diagnosis keeps its shell** (Q2): reads stay inside its export, but a command it runs is a
   tool round trip on the subscription.
8. **Codex still writes its session rollouts** (prompts with learner text) under `~/.codex/sessions` as before;
   not changed here (Q4).

## Owner notes

1. **What changes in the app:** every Codex call (tutor, reader judges, library organizer, role labeller,
   reading paths, source rerank, hints, AD forecasts, grading, diagnosis, router, projects) now starts in an
   empty temp dir with no tools, connectors, MCP servers, web search or sub-agents, and with approvals off. A
   call where the model reaches for a tool fails like any provider failure: the usual fallback, retry or
   "provider unavailable" path follows, and the receipt counts every thread's tokens.
2. **First call per sidecar process** runs four quick `codex` CLI probes (about 0.13 s on an empty home), then
   caches; a Codex config change re-runs them.
3. **Please watch the first few ordinary Codex calls after landing** (a tutor question, a grading). If they
   fail with "a model response that ended in a tool call", that is the early-stop rule misreading a normal
   turn; the review's commit `8fe73f883` is the one to revert.
4. **A Codex CLI upgrade may refuse turns** until the lockdown reviews it: a new feature that is on by default is
   switched off automatically; one that cannot be switched off, a new tool field in the model catalog, or a
   model the bundled catalog does not list refuses every Codex turn with `CodexLockdownUnavailable`, naming the
   feature or field.
5. **Your own Codex config:** nothing is required. Optionally, in `~/.codex/config.toml` you could set
   `approval_policy = "never"` and keep `node_repl`/`cua_repl` scoped to the projects that need them; LearnLoop
   no longer relies on either. If you configure a profile for a model newer than the CLI bundles, update the CLI
   too, or that profile's turns are refused.

## Process notes

* Before I applied the env-isolation rule to every command, about ten one-off `python3 -I` scripts read the
  Codex SDK's JSON schemas or edited files in this worktree without `env -i`, and one `python -I -c` printed
  `learnloop.__file__` from the base export. None imported LearnLoop's AI code, read a config, or touched the
  network. Every later script ran under `env -i` with an empty `HOME`/`CODEX_HOME`/`LEARNLOOP_CONFIG_DIR`.
* `codex features list`/`mcp list`/`debug models --bundled` were run under an empty throwaway `CODEX_HOME`.
  Codex 0.163.0 source was read from a sparse shallow clone of `rust-v0.163.0` in the session scratchpad.
* No fixture vault was opened or copied. No run used a vault. `~/.codex/auth.json`, `~/.codex/config.toml`
  and `settings.env` were never opened.

## Open questions (with defaults)

* **Q1.** Build a LearnLoop-owned model catalog (`model_catalog_json` with `tool_mode: direct`, no
  `apply_patch`) to remove code mode and `apply_patch` outright? **Default: no.** It replaces the served model
  metadata on every route and drifts per release; the live checks show both neutralized.
* **Q2.** The snapshot diagnosis is the one route with a tool (its shell, reading its export). Keep it, or move
  it to an inline workspace (files in the prompt, as `chatgpt_plan`'s `workspace_mode = "inline"` does) so it
  too runs tool-free? **Default: keep it as is**, under deny_all approvals and the read-only profile.
* **Q3.** Should a `CodexToolUseRefused` skip the caller's retry (a tool attempt is likely to repeat)?
  **Default: no change**; retries stay as they were (behaviour note B).
* **Q4.** Start Codex threads `ephemeral=True` so learner prompts are not kept in `~/.codex/sessions`?
  **Default: not in this stage** (outside the tool surface; a separate privacy decision).
* **Q5.** Refuse the legacy HTTP Codex adapter outright, since its tool surface is unknowable? **Default: no**;
  no default profile uses it, and it already refuses isolated operations.

## Landing onto main (2026-10-21)

Landed exactly `bc90f31ae`, not the branch tip. A hardening round is still running on the branch, and a
**second landing** of its commits follows. The orchestrator is landing this commit now because main's
exposure is much larger. Its verify job `20261021-113946-qZgmYP` on `bc90f31ae` confirmed that ordinary
text-only turns are **not** refused.

### Commits and conflicts

* Branch `merge/security-lockdown-onto-main`, cut from main `7e7bdff1b` in `learnanything-merge2`.
* `6ff71bdac`: `git merge --no-ff bc90f31ae`. **No conflicts.**
  * Since `c80c54cbb`, main had changed only `transport.py`, `openai_chat.py`, `routing.py`,
    `disclosures.py` and `conftest.py` in the AI layer (RW5a's `images` and `IMAGE_INPUT`, and
    `LEARNLOOP_FIGURE_MODELS=off`).
  * The stage did not touch any of those files. `codex.py`, `execution.py` and `paid.py` merged cleanly,
    and so did RW5a's figure routes.
* `92b9f19fc`: composition pin. `tests/test_codex_tool_lockdown.py` gets a `figure_author` shape in its
  route-coverage parametrization, `test_every_request_runs_the_locked_down_profile_with_approvals_denied`.
  * The shape drives RW5a's real `FigureRoute.ask`, which goes through `PaidCalls.call(..., isolated=True)`
    on a `SdkCodexClient`.
  * It asserts the same things as every other shape: `deny_all` on the thread and the turn, the decline
    handler, a fresh `learnloop-isolated-turn-*` directory (never the vault), and the full override set.
  * Fail-first: run on `git archive main src`, with `codex_lockdown.py` added so the import resolves,
    under `env -i`. All 6 shapes fail (`KeyError: 'approval_mode'`), `figure_author` among them.
* This record is the last commit.

Nothing needed regenerating. There is no migration, config key, schema, CLI, RPC or frontend change. The
CLI-help, serializer, desktop-RPC, mobile-allowlist and table-role pins are all part of the full suite
and pass. `git diff main HEAD -- fixtures apps` is empty.

### Gate (on `92b9f19fc`)

Setup: `uv sync --extra dev --extra mobile` plus `uv pip install pypdfium2`, with
`TMPDIR=fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | **29 kept, 0 broken** |
| full suite: `flock … pytest -n auto` | **15,552 passed, 2 skipped, 2 xfailed** in 25:50 |
| durability: `flock … pytest -m durability` | **119 passed** |
| `npm run typecheck` | ok |
| `cargo check` | ok |
| vitest (whole run) | see below |

* The full suite needed a second start. The first run was cut off at 99% by a session restart and left
  no summary; the figures above are from the rerun.
* **vitest.** `apps/` is byte-identical to main, where the RW5a landing gated 1,469 passing. This landing
  made four whole runs, all at load average 40 to 80 while other stages were running:
  * they failed 16, 4, 1 and 5 tests;
  * the failures were in different files each time (`PracticeScreen`, `PracticeScreen.adaptiveHandoff`,
    `pdfSelection/perf`, `FigureInline`, `libraryAsk`, `figuresWithReadingPath`, `Workbench`): vault-switch
    timing, a 400 ms perf bound, and teardown-after-test errors;
  * every failing file I saw passed alone, 3 out of 3 times (67 and 68 tests);
  * the 9 files of the first run were not listed, because its log kept only the totals.

### Checks

**(a) Every Codex call site on the merged tree.**

* `git grep` and the stage's AST sweep (`test_every_codex_turn_starter_in_the_source_passes_deny_all_inside_the_locked_down_turn`,
  passing) find these call sites:
  * one `Codex(config=…)` construction, one `codex.thread_start(` and one `thread.turn(`, all in
    `SdkCodexClient._run_sdk_turn` (`codex.py:1078/1091/1103`), with `approval_mode=deny_all` and
    `install_on_sdk` placed before `thread_start`;
  * `_run_sdk_turn`, which is reached only from `_run_structured` (`codex.py:938`);
  * `_run_structured`, which is reached only from `_complete_validated`'s `run_turn` (`codex.py:793/796`);
  * `_complete_validated`, which is reached only from `complete()` (`codex.py:730`).
* So every caller goes through `execute_structured_operation`, then `transport.complete`, then that one
  path. Those callers include `PaidCalls.call`, `tutor_qa`, the judges, the hints and AD routes,
  diagnosis, projects and RW5a's `figure_author` (`figures/routes.py:225`, `isolated=True`).
* The two other `subprocess` starts in `codex.py` make no model call:
  * `:605` is the launch-check probes (`features list`, `mcp list`, `debug models --bundled`);
  * `:1659` is the legacy HTTP adapter's `startup_command` (open High 3 below).
* The figure author's crop never reaches Codex. `SdkCodexClient.supports(IMAGE_INPUT)` is false, so
  `FigureRoute.reads_images()` sends no image, and `execute_structured_operation` refuses images to any
  transport that lacks `IMAGE_INPUT` before it sends anything.

**(b) Parity** (`fixtures-local/landing-sec/`, scripts in `scripts/ab_sec.sh` and `scripts/main2.sh`).

* Setup:
  * backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of `fixtures/linear_algebra` and
    `fixtures/probability`, taken from the **main checkout** (mvp-0.8, schema 165);
  * full `git archive` trees of main (`7e7bdff1b`) and the merge;
  * every run under `env -i PATH HOME CODEX_HOME LEARNLOOP_CONFIG_DIR`, all three empty;
  * every route at `blackhole` (openai_chat or decider at `127.0.0.1:9`, key variable unset), with
    embeddings, rewrite, rerank, dense, gaps and `build_on_serve` off.
* Results:
  * **Migration.** Each code applies 51 migrations, to head 217. Schema, rows, FK and integrity checks are
    identical (1451 and 1450 objects, 344 tables). `schema_migrations` differs only in `applied_at`.
  * **At the copies' label (mvp-0.8)**: certification, the Today queue and the plan are byte-identical
    main vs merge, for both vaults.
  * **`rebuild --shadow` and `doctor`.** Zero differences after normalisation. The raw outputs differ only
    in the vault path, each copy's own live-DB sha256 (the same before and after) and a fresh marker ULID.
    The live database is unchanged on both sides.
  * **Upgraded with main's code** along the owner chain (`--to mvp-0.9`, `--to mvp-0.27`,
    `rebuild-derived-state`, then `--to mvp-0.29`): certification and Today are byte-identical at
    mvp-0.27 and mvp-0.29.
  * **The plan at mvp-0.27 and mvp-0.29** is identical except `router_decisions.card_hash`,
    `snapshot_hash` and the `router.card_hash` inside `detail_json`. A second run of main's code on a fresh
    copy differs from the first in exactly these three fields. This is run-to-run, not the merge, as at the
    earlier landings.
* A first parity attempt overlapped a second instance of the script started around the session restart,
  so its copies were contaminated. All derived directories were deleted, and the run above is one clean
  serial pass.

**(c) Receipts.** All 26 parity databases hold **0** `model_call_receipts` rows of any status.

**(d) No live Codex calls.**

* Every run outside pytest used `env -i` with an empty `CODEX_HOME`, and with every route on the
  loopback blackhole. The parity `HOME/.codex` and `LEARNLOOP_CONFIG_DIR` are still empty afterwards.
* The suite's real-binary tests run only local probes under throwaway homes.
* No credential file, owner config or fixture vault was opened directly. No git stash was used.

### Owner notes

1. **What changed.** Every Codex call now runs locked down:
   * it starts in a fresh empty temp directory, and the vault is refused as a workspace;
   * approvals are `deny_all`, and a handler declines every request;
   * it runs under the read-only, no-network permission profile;
   * 46 tool features are off, plus sub-agents, `request_user_input`, `update_plan`, web search, MCP and apps;
   * a cached launch check fails closed;
   * commands see only an allowlisted environment;
   * a turn that produces any non-text item, makes a second model request, or ends a response in a tool
     call is refused like any provider failure;
   * sub-agent and tool usage is metered.

   This applies to the tutor, reader judges, library organizer, role labeller, reading paths, source
   rerank, hints, AD forecasts, grading, diagnosis, router, projects and the figure author.
2. **Watch the first ordinary Codex calls** (a tutor question, a grading). If they fail with "a model
   response that ended in a tool call", the early-stop rule is misreading a normal turn: revert
   **`8fe73f883`**.
3. **The snapshot diagnosis keeps a read-only shell** to read its as-of export (Q2), under `deny_all`, the
   read-only profile and the environment allowlist.
4. **A second landing follows** with the hardening round now running on the branch. It addresses the four
   Highs below.
5. The first call in each sidecar process runs the quick `codex` probes, then caches. A Codex CLI upgrade
   can refuse turns until the lockdown reviews it; the error names the feature or field.

### Open items

* **Four configuration-dependent Highs** from verify `20261021-113946-qZgmYP`, being fixed on the branch
  for the second landing:
  1. inherited permission-profile grants;
  2. a relative `CODEX_HOME`, and fingerprinting of the launch command;
  3. the legacy HTTP Codex transport;
  4. runtime model catalogs beyond the bundled one.
* **Q1 to Q5** (above), defaults unchanged:
  * Q1: no LearnLoop-owned model catalog;
  * Q2: the diagnosis keeps its shell;
  * Q3: retries unchanged;
  * Q4: not ephemeral;
  * Q5: HTTP adapter kept.
* vitest load-flakiness under concurrent stages: these frontend tests fail only under heavy load
  (pre-existing; no frontend change here).
