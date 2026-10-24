# Stage T1: plan-first transport (2026-10-21)

Branch `ai/plan-first-transport` from main `55063be64` (migration head 217). Owner decisions of
2026-10-21 (after four security verifies of the Codex lockdown kept finding agent-harness features);
proposal `fixtures-local/codex-transport-proposal.md` §5 step 3. No migration. No live calls, no sign-in:
everything model-backed is tested with fakes (a fake Responses server, recording gates, `StructuredClientFake`).

## Plan (written before the code)

1. **Code-default plan profiles.** `chatgpt` (type `chatgpt_plan`, model `gpt-5.6-sol`, the slug the Codex
   profiles used, as a config value), `chatgpt_low` / `chatgpt_medium` (copies of `chatgpt` with
   `reasoning_effort` low / medium, as `codex_low` / `codex_medium` had) and `chatgpt_luna` (`gpt-6-luna`,
   low: the cheap judge `codex_luna` served). `ai.active_provider` defaults to `chatgpt`;
   `DEFAULT_CODEX_TASK_ROUTES` becomes `DEFAULT_SERVING_TASK_ROUTES` (grading -> chatgpt_low, ingest /
   authoring / animation -> chatgpt_medium, facet identity -> chatgpt_luna, ...); the old table stays as
   `LEGACY_CODEX_TASK_ROUTES` for vaults that set `active_provider = "codex"` (opt-in only). The new-vault
   template routes to the plan profiles.
2. **Codex refused for serving.** New `ai.agent_harness_opt_in` (default false). Without it a `codex_sdk`
   or legacy `http` profile is refused in one place per layer, before any subprocess: the client factory
   (`make_ai_provider_client_from_profile` raises `AgentHarnessRefused`), readiness (`check_ai_runtime`
   reports unavailable without running the Codex health check, which can start processes) and routing
   (`route_profile_mismatch`, so every route, `LEARNLOOP_AI_PROVIDER` and explicit selections read
   unavailable). `fallback_provider_for` never returns an agent-harness profile, opt-in or not.
   `codex.py`, `codex_lockdown.py` and `codex_http.py` stay unchanged (frozen; T2 deletes them).
3. **Plan unavailable: report and ask.** `ready_client_for_task` keeps the existing degrade path
   (the plan's not-ready runtime is returned) and, when the primary is a plan profile and the configured
   OpenRouter profile (`ai.plan_fallback_profile`, default `openrouter`) has its key, it records an offer:
   `AIRuntimeReport.fallback_available = "openrouter"`, and the request's offer collector notes the task.
   A plan failure during a call (usage limit, ineligible, rejected token) marks the collector too.
   The sidecar dispatcher attaches `fallback_available` / `fallback_tasks` / `fallback_profile` to the
   RPC's error details or result; the CLI's JSON output does the same. Choosing it: desktop "Use OpenRouter
   instead" calls the new RPC `ai_use_fallback`, which grants those tasks for this sidecar session (the
   feature, for the session: my call); CLI `LEARNLOOP_AI_FALLBACK=openrouter` grants every task for that
   one command. Only a grant routes to OpenRouter; nothing is sent there otherwise; no key, no offer.
   Metered features keep their existing spend caps (they see a metered client).
4. **Diagnosis inline.** `chatgpt_plan.workspace_mode` defaults to `inline`; an export over
   `max_workspace_chars` (400k) is served in tools mode instead (each round admitted), not refused.
5. **Doctor.** `ai:codex_route_pinned` for every explicit `learnloop.toml` setting (active / fallback
   provider, each `[ai.routing]` entry) that names a Codex profile without the opt-in; `learnloop doctor
   --fix` rewrites them to the plan profiles (codex -> chatgpt, codex_low -> chatgpt_low, codex_medium ->
   chatgpt_medium, codex_luna -> chatgpt_luna; a fallback is cleared). A clear finding when the account's
   model list (cached by `learnloop ai models chatgpt`) lacks a configured slug.
6. **Desktop and onboarding.** The connection sheet already offers "Continue with ChatGPT" when the
   route is not ready; with the new defaults a signed-out plan reaches it. A shell banner shows the
   OpenRouter offer.
7. **Tests by construction** (proposal T1 list (1)-(5), plus (6) the ask, (7) doctor --fix, (8) prompts and
   parsing unchanged), and an import-linter contract that no serving package imports the Codex provider.

## What was built

The plan above, with the deviations listed below. Session resumed on 2026-10-22 from the
interrupted run's uncommitted work (kept: config, refusal, offer bookkeeping, doctor, sidecar RPC,
desktop banner); this session added the import contract, the type-only imports, the probe
silencing, the connect-sheet tiers, the registry rule, every test, and this record.

Resumed again on 2026-10-23 (after further memory kills, the worktree held ~45 uncommitted files
and no gate had run). That session committed the work first (`42ab0bc90`, WIP), then: moved the
existing suite to the T1 defaults (it had been left on the Codex defaults: ~100 failures in 35
files of the Codex-touching set), closed one gap (a grant served background work; see the
OpenRouter section), regenerated the references, and ran the gate below.

### Configuration (`config/schema.py`, `config/template.py`, `config/compat.py`)

- Code-default profiles `chatgpt` (type `chatgpt_plan`, `model = "gpt-5.6-sol"`, effort `low`),
  `chatgpt_low` (low), `chatgpt_medium` (medium) and `chatgpt_luna` (`gpt-6-luna`, low). The tiers
  are copies of the vault's own `[ai.providers.chatgpt]`, so the owner sets one slug for all three
  (`chatgpt_luna` keeps its own slug). The slug is a config value; `gpt-5.6-sol` is the slug the
  Codex profiles served (the "sensible default"); the owner confirms it with
  `learnloop ai models chatgpt`.
- `ai.active_provider = "chatgpt"`; `DEFAULT_CODEX_TASK_ROUTES` is now `DEFAULT_SERVING_TASK_ROUTES`
  (grading/tutor_qa/teach_back/rung_variant -> `chatgpt_low`; canonical_ingest, its retry,
  authoring, animation -> `chatgpt_medium`; facet_identity_judge -> `chatgpt_luna`), the same
  efforts the Codex tiers gave. The pre-T1 table is `LEGACY_CODEX_TASK_ROUTES` (an unset tiered
  route of a vault whose active provider is still `codex`, and the meaning of a legacy
  `routing.<task> = "codex"`); both are refused without the opt-in.
- New keys: `ai.agent_harness_opt_in = false`, `ai.plan_fallback_profile = "openrouter"`; the
  plan's `workspace_mode` default is `"inline"`. Classified in `params/parameter_registry.py`
  (structural, operational: transport admission, never what is measured).
- New-vault template: `[ai.providers.chatgpt]` and the routes on the plan tiers.
- Every recorded defaults snapshot (mvp-0.9 ... mvp-0.29) moves because the effective defaults
  gained the profiles and keys; each was recomputed from the composed defaults
  (`defaults_fingerprint_for_version`) and commented. **No algorithm successor**: prompts,
  parsing, scoring, scheduling, projections and replayed meaning do not change; the served MODEL
  changes (Codex to the plan's models), which the owner approved. Receipts already key on
  provider + model, so history stays attributable.

### Codex refused for serving (`ai/agent_harness.py`)

- `AGENT_HARNESS_PROFILE_TYPES = {codex_sdk, http, http_adapter}`. Without
  `ai.agent_harness_opt_in` such a profile is refused in one place per layer, before its module is
  imported or any process starts:
  - the single client factory `make_ai_provider_client_from_profile` raises `AgentHarnessRefused`
    (an `AIProviderUnavailable`, so every caller's degrade path applies);
  - readiness (`check_ai_runtime`) reports `provider_unavailable` with the refusal text and never
    runs the Codex health check (which can start the app-server);
  - routing (`route_profile_mismatch`) reads the refusal, so every `[ai.routing]` value,
    `LEARNLOOP_AI_PROVIDER` and explicit selection of a Codex profile is unavailable.
- `fallback_provider_for` never returns an agent-harness profile, opt-in or not.
- `codex.py`, `codex_lockdown.py` and `codex_http.py` are unchanged (frozen). `runtime.py` keeps
  `check_codex_runtime` / `codex_config_from_ai_profile` as function-local shims (one patch point
  for the frozen path's tests); `attempts.py`, `regrade.py` and `ops/startup.py` import
  `CodexRuntimeReport` under `TYPE_CHECKING` only.
- Import-linter contract `serving-never-imports-the-codex-provider`: no module of `learnloop`,
  `learnloop_sidecar`, `learnloop_mobile` or `learnloop_mcp` imports `learnloop.ai.providers.codex`,
  `codex_http` or `codex_lockdown`, except the factory, the readiness shim, the three type-only
  imports and the frozen modules among themselves (each listed with its reason). It composes with
  the security branch's `codex-sdk-only-in-its-provider` (a different id).

### The plan unavailable: report and ask (`ai/plan_fallback.py`, `ai/routing.py`)

- An **offer** exists only when `ai.plan_fallback_profile` names an `openrouter`-type profile whose
  API key is present. No key, no offer, no action shown.
- When a routed (not pinned) plan route is unavailable, `ready_client_for_task` returns the plan's
  unavailable resolution (the existing degrade path, no client) with
  `runtime.fallback_available = "openrouter"`, `fallback_profile` and one added sentence in the
  message; the request's offer collector notes the task. A plan request that fails for
  availability mid-call (signed out, plan usage not granted, usage limit, ineligible, a token
  refused after its one refresh) marks the collector too, so the hint names the plan routes the
  request resolved.
- Readiness probes make no offer (`plan_fallback.quiet()`): the snapshot's health line and startup
  maintenance (deferred regrades wait for the plan).
- The typed hint: the sidecar dispatcher adds `fallback_available: "openrouter"`, `fallback_tasks`,
  `fallback_profile`, `plan_signed_out` to the RPC's error `details` (or camelCase to a degraded
  dict result); the CLI's JSON output (`cli.render._dump`) adds the same keys.
- **The choice** (my call, as the brief allowed): desktop "Use OpenRouter instead" calls the new
  RPC `ai_use_fallback {provider: "openrouter", tasks}`, which grants **those tasks (the feature)
  for the rest of this sidecar session**; `{stop: true}` revokes. The CLI's
  `LEARNLOOP_AI_FALLBACK=openrouter` grants every task for that one command. A granted task uses
  OpenRouter only while the plan cannot serve it (a ready plan route is always used first); a
  pinned selection (a named profile, `LEARNLOOP_AI_PROVIDER`) is never replaced. A granted request
  is an ordinary metered request on that profile (`fallback_from` names the plan profile; receipts
  record the provider and model that answered), so the features' existing spend caps apply.
  Nothing is sent to OpenRouter without the grant: no OpenRouter client is even built.
- **Background jobs** (added on the 2026-10-22 resume): hints (`practice.request_hint`), the
  library ask/notes/compare/tutor jobs, margin-note discovery and the Guide's reading path run on
  worker threads, which have no RPC collector (a `ContextVar` does not cross into a new thread), so
  their offers were lost. Each job now collects its own (`plan_fallback.collecting()` in its
  thread) and keeps the hint on the job (`fallback_offer`; for reading paths beside the failed
  judgment state, so the view payload is unchanged); the poll RPC that finds the job done
  (`practice.hint_job`, `reader.library_job`, `reader.cue_discovery_job`, each `reader.reading_path`
  read of a failed judgment) relays it (`plan_fallback.relay_hint`) into its own hint, so it
  reaches the desktop at top level. A nested collector (a job run inline) also hands its offers to
  the enclosing one. The intent box's router is the Decider (OpenRouter), not a plan route, so it
  is unchanged. The post-attempt worker and exam grading copy the RPC's context, but their offers
  land after that RPC has answered: a deferred diagnosis or exam grade reports through its own
  state, and the next feature RPC that meets the plan asks (open question Q7).
- **A grant never serves background work** (fixed 2026-10-23). `plan_fallback.quiet()` (readiness
  probes, startup maintenance) now also honours no grant, session or CLI: before the fix, a
  desktop session that had granted "grading" would, on a vault switch, have run startup
  maintenance's deferred-regrade backlog on OpenRouter, which the learner never chose. That
  backlog now waits for the plan. Pinned in `test_unavailable_offers_openrouter_only_when_configured_and_sends_nothing_unasked`.
- `ai_use_fallback` is desktop-only (pinned in `tests/test_mobile_allowlist.py`), registered in
  `src-tauri` (`commands.rs`, `main.rs`) and `api/client.ts` (`aiUseFallback`).
- Desktop: `api/client.ts` notes any hint on a result or error into `app/planFallback.ts`; one shell
  banner (`components/PlanFallbackOffer.tsx`) says "ChatGPT isn't available right now.", explains
  that OpenRouter charges the learner's OpenRouter account, and offers "Use OpenRouter instead",
  "Continue with ChatGPT" (when the plan is signed out) and "Not now". The feature keeps showing
  its own unavailable state.

### Diagnosis inline (`ai/providers/chatgpt_plan.py`)

- `workspace_mode` defaults to `"inline"` (one request, no tools). An export over
  `max_workspace_chars` (400k) is served in tools mode instead of being refused: each round is
  its own admitted request (`_send_once`), the record says `mode: "tools", inline_overflow: true`.
  A workspace turn under a single-request budget is still refused before sending (unchanged).

### Doctor (`ops/plan_transport.py`, `ops/doctor.py`, `cli/app.py`)

- `ai:codex_route_pinned` (warning) for every setting **written in `learnloop.toml`** (read with
  `tomllib`, never a code default) that names a Codex profile without the opt-in:
  `ai.active_provider`, `ai.fallback_provider`, each `[ai.routing]` entry (list routes too).
- `learnloop doctor --fix [--dry-run] [--json]` rewrites them in place (comments kept,
  `settings_store.apply_config_updates`): `codex -> chatgpt`, `codex_low -> chatgpt_low`,
  `codex_medium -> chatgpt_medium`, `codex_luna -> chatgpt_luna`, another Codex-typed profile by its
  effort; a Codex `fallback_provider` is cleared. No silent aliasing at load.
- `ai:chatgpt_plan_model_not_listed` when the signed-in account's model list (remembered by
  `learnloop ai models chatgpt`, per account subject) lacks a configured slug, naming the setting.
- The machine's sign-in/pause state moved under `doctor --ai`: every vault now uses the plan, so a
  signed-out machine is not a finding of each vault (`learnloop ai status chatgpt` and the
  desktop's "Continue with ChatGPT" report it).

### Onboarding (`learnloop_sidecar/handlers/first_run.py`)

- With the plan as the default route, a signed-out machine reaches the existing connection sheet's
  "Continue with ChatGPT" (`needs: "connect"`), and the banner offers it too.
- `connect_ai {provider: "chatgpt"}` now keeps the effort tiers (each use case on its default tier
  route instead of flattening onto `chatgpt`) and picks the slug: an explicit model, else the
  file's `[ai.providers.chatgpt] model`, else the code default, kept when the account lists it,
  else the first listed model (one GET of the model catalog; when it cannot be fetched a slug
  already written is kept and doctor reports it if unlisted).

## Deviations from the brief and the plan

1. **Configured non-Codex `fallback_provider` kept.** A `fallback_provider` the owner wrote (for
   example `openrouter`) still serves an unavailable plan route as before; it is explicit owner
   configuration, not a silent fallback. The template writes `fallback_provider = ""`. Open
   question Q3.
2. **Grant scope = the feature's tasks for the sidecar session** (desktop), every task for one
   command (CLI); grants are process-wide, so they survive a vault switch within the session.
3. **Round 2-3 guards are not on this base.** The brief says "keep round 3's launch-site sweep" and
   "keep the codex-sdk-only-in-its-provider contract"; both live on the security branch (landing
   now as the second security landing), not on `55063be64`. T1 adds its own complementary checks
   (a different contract id, a T1 launch sweep) so the two compose; the landing keeps both.
4. **Tools mode on overflow is unconditional.** An explicit `workspace_mode = "inline"` cannot be
   told apart from the default, so an oversized export is served in tools mode either way (it was
   refused before).
5. **Doctor's signed-out finding moved under `--ai`** (see Doctor).
6. **Existing Codex-double tests opt in rather than move to plan fakes.** About 60 existing tests
   drive features through the frozen Codex doubles (`install_fake_codex_sdk`, the legacy HTTP
   double, `check_codex_runtime` patches). Rather than rewrite them in T1, they now say so:
   `tests/helpers.py::use_codex_harness(vault_root)` restores the pre-T1 configuration (active
   provider `codex`, `codex_low`/`codex_medium` tiers) with `ai.agent_harness_opt_in = true`, and
   `configure_codex_http` calls it. Readiness-only tests whose fixture meant "the default route is
   ready" use `patch_plan_ready(monkeypatch)` instead (the plan reads signed in; nothing is built or
   sent). T2 moves the opted-in tests to plan fakes (listed below).

## Tests that prove the property (`tests/test_plan_first_transport.py`)

1. **Route resolution.** Every `AITask` under the code defaults, the plan signed in / paused /
   signed out, with and without an OpenRouter key: the resolved client is never an agent-harness
   type and (generation tasks) `supports(TOOL_FREE)`; an unavailable plan route is not ready and
   carries the offer exactly when OpenRouter is configured; nothing is sent. Every task over every
   configured profile as its `[ai.routing]` value; every profile as `fallback_provider`
   (`fallback_provider_for` never returns Codex) and as `LEARNLOOP_AI_PROVIDER`. Process starts are
   patched to fail the test throughout. The opt-in admits a pinned Codex route and Codex is still
   never a fallback.
2. **Admission equals wire.** A fake Responses server's request list writes a shared ordered log
   with a recording gate: first try, transient 503 retry, 401 refresh, JSON repair, inline workspace,
   tool rounds, inline overflow into tools mode, usage limit (then paused: neither admitted nor
   sent). In each, posts == admits and the log is exactly admit n, post n.
3. **Body grammar.** Every body has keys within `{model, instructions, input, store, stream, text,
   reasoning}`, `store: false`; `tools`/`include` only in tools mode with exactly the `workspace`
   namespace of function tools; inline diagnosis sends no tools; `_respond` (plain calls and
   repairs) builds no tools by AST.
4. **One egress point (AST).** `ResponsesStream(...)` is built only in `_send_once`; the module's one
   `.send(` is `stream.send` inside `_send_once`'s `with model_call(...)`. Every module importing an
   HTTP client is in an audited table (model inference: the plan, the OpenAI-compatible/OpenRouter
   family, transcription, and the frozen Codex modules; the rest send no route's prompt). Base-URL
   validation pinned (OpenAI https or loopback only).
5. **No serving Codex launch.** Each agent-harness type without the opt-in raises
   `AgentHarnessRefused` from the factory with process starts patched to fail; readiness of each
   Codex profile runs no health check; a clean interpreter importing the CLI, the sidecar, startup
   and the attempt modules and resolving every task (and explicit Codex selections) has loaded no
   `learnloop.ai.providers.codex*` or `openai_codex` module; an AST sweep finds no process launch
   mentioning Codex outside the frozen provider; plus the import-linter contract.
6. **The OpenRouter ask.** No key: no offer, `ai_use_fallback` refused (`fallback_unavailable`).
   A key: typed offer on the runtime, the collector, the RPC error details and the CLI JSON; no
   OpenRouter client built until chosen; probes ask nothing; the grant serves that task only;
   pinned selections never replaced; the CLI env grant; a ready plan always first; a plan call
   failing for usage mid-request offers its route; `ai_use_fallback` validates tasks, grants,
   `stop` revokes.
7. **doctor --fix.** Every pinned setting reported (active, fallback, each route, a list route),
   `--dry-run` writes nothing, `--fix` rewrites with comments kept and the findings clear; opted-in
   vaults are not reported; CLI `--fix --dry-run`, `--fix --json`, and `--dry-run` alone exits 2;
   the unlisted-slug finding.
8. **Prompts and parsing unchanged.** The stage touches no prompt builder or parser (the diff's
   files are transport selection, config, doctor, the sidecar and the desktop shell); a route's
   prompt reaches the plan's wire verbatim. The served model changes (owner-approved); no
   projection or replayed meaning changes, so no algorithm successor.

Existing tests updated for the owner decisions: `test_chatgpt_plan_workspace.py` (a paused plan
never falls back to Codex, opt-in or not; inline overflow is served in tools mode; inline is the
default), `test_chatgpt_plan_cli.py` (sign-in findings under `--ai`; an unrouted plan needs every
default route moved), `test_ux_phase1_connect_ai.py` (tiers kept), `test_config_refactor.py`
(template moved Codex tiers to plan tiers of the same slug and effort), `test_mobile_allowlist.py`
(`ai_use_fallback` desktop-only), `tests/cli_help_snapshot.json` (doctor `--fix`).
Desktop: `src/components/PlanFallbackOffer.test.tsx` (hint parsing, merge, nothing sent until
chosen, exact tasks granted, "Continue with ChatGPT" only when signed out, "Not now").

### Existing tests moved to the T1 defaults (2026-10-23)

Each change follows an owner decision; none relaxes an assertion about prompts, parsing or meaning.

- **Default pins** (route and profile names, `codex_low`/`codex_medium`/`codex` to
  `chatgpt_low`/`chatgpt_medium`/`chatgpt`, only on `assert` lines of the failing tests):
  `test_ai_config.py`, `test_settings_sidecar.py`, `test_settings_store.py` (also the new template
  comment), `test_sidecar_contract.py`, `test_sidecar_animation.py`, `test_project_cli.py`,
  `test_probability_prep.py`, `test_ingest_m3.py`, `test_ingest_runner.py`, `test_ingest_jobs.py`,
  `test_judge_routes.py` (and the plan's disclosure text), `test_embedding_route_isolation.py`,
  `test_method_phrasing_report.py` (the writer is the plan), `test_family_proposals.py` (dry run on
  the plan), `test_source_retrieval_codex_unavailable.py` (T6 routes follow the active plan
  profile), `test_provider_resolution_parity.py` (the matrix's default row is the plan; its named
  row a `chatgpt_plan` profile).
- **Signed-out plan, not a missing checkout:** `test_cli_propose.py`, `test_cli_json.py`
  (`provider_auth_required` replaces `codex_missing`).
- **Codex never a fallback:** `test_sidecar_contract.py::test_sidecar_submit_attempt_never_falls_back_to_codex_when_routed_ai_unavailable`
  (was `..._falls_back_to_codex_...`): a configured `fallback_provider = "codex"` is ignored, the
  learner is asked to grade (`grading_fallback_required`), the Codex double receives nothing.
- **Explicit opt-in for the frozen path:** `use_codex_harness` / `agent_harness_opt_in=True` in
  `test_cli_ingest.py`, `test_codex_runtime.py`, `test_cli_generate_practice.py`,
  `test_ingest_runner.py`, `test_family_proposals.py`, `test_provider_resolution_parity.py`,
  `test_ai_config.py`, and every `configure_codex_http` user (`test_cli_attempt.py`,
  `test_cli_propose.py`, `test_deferred_regrade.py`, `test_model_call_receipt_owners.py`,
  `test_sidecar_teach_back.py`, `test_sidecar_tutor_qa.py`, `test_tui_feedback.py`, ...).
  `test_facet_identity_composition.py` now pins both sides: `codex_luna` refused without the
  opt-in, admitted with it.
- **Tools mode pinned where a test scripts workspace rounds:** `test_ai_compare.py` (its two plan
  profiles) and `test_chatgpt_plan_landing.py` (what the plan served file by file). Inline, the
  new default, is covered by `test_plan_first_transport.py` and `test_chatgpt_plan_workspace.py`.
- **Goldens, only the keys this stage moves:** `tests/fixtures/figures_switch_off_backlog.json` and
  `figures_switch_off_queued_job.json` re-recorded with `RW5A_WRITE_GOLDEN=1` (the diff is only the
  route names); `tests/fixtures/compare_keep_switch_off.json` edited by hand (three
  unavailable-route `reason` strings; regenerating on this tree would have pulled in later
  stages' keys).

## Owner-run commands (after the stage lands; none was run here)

```bash
uv run learnloop ai signin chatgpt            # or desktop Settings -> Continue with ChatGPT
uv run learnloop ai models chatgpt            # confirms the slugs; doctor remembers the list
uv run learnloop ai latency --vault <copy> --provider chatgpt --runs 3   # synthetic prompts only
uv run learnloop doctor --vault <vault> --fix --dry-run   # then without --dry-run
```

`learnloop ai compare --profiles codex,chatgpt` (the proposal's optional step 1 comparison) needs
`ai.agent_harness_opt_in = true` on the copy it runs against: without it the Codex profile is
refused (review F9). The `chatgpt`/`openrouter` comparison needs no opt-in.

If the account lacks `gpt-5.6-sol` (or `gpt-6-luna`), set `[ai.providers.chatgpt] model` (the
low/medium tiers follow it) and `[ai.providers.chatgpt_luna] model`; `learnloop doctor` names them.
Codex quota is exhausted until 2026-10-27 and Q5 assumes the plan shares that pool, so the plan
likely reads paused/unavailable until then: the unavailable state plus "Use OpenRouter instead"
(desktop) / `LEARNLOOP_AI_FALLBACK=openrouter` (CLI) is what serves meanwhile.

## Gate (implement step, 2026-10-23; targeted only, owner rule 2026-10-17)

Every pytest/vitest/npm/cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G
-p MemorySwapMax=1G -- ...` (pytest `-n 6` at most, vitest `--maxWorkers=4`, one run at a time), with
`TMPDIR=fixtures-local/tmp`. No full suite, no whole durability lane, no whole vitest run. No
migration and no DB/connection change, so no durability tests were due. Another stage's landing
full suite (merge2) ran on the machine meanwhile; nothing of it was touched.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 30 kept, 0 broken (includes `serving-never-imports-the-codex-provider`) |
| `tests/test_plan_first_transport.py` | 38 passed |
| Every `tests/test_*.py` naming Codex (207 files), first run | 97 failed (35 files), the rest passed; after the moves above every failing file reran green (the last 13 files: 345 passed) |
| Every other test file exercising a changed module or routing (202 files: handlers hints/library_ask/cue discovery/reading paths/first_run/chatgpt_plan, doctor, startup, regrade, render, registry, sidecar context/server, compat, readiness/routing callers) | 3,077 passed, 2 xfailed, 7 failed (3 files); after the tools-mode pins and the golden edit: 34 passed in those 3 files |
| Contract pins and snapshots after all edits (`test_cli_help_snapshot`, `test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_architecture`, `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_sqlite_file_copies`, `test_config_refactor`, the six `test_chatgpt_plan_*` files, `test_ux_phase1_connect_ai`, `test_plan_first_transport`, and the three defaults-snapshot files not in the sets above) | 513 passed |
| Startup maintenance and grant tests after the `quiet()` fix (5 files) | 334 passed |
| `npm install`; `npm run typecheck` | ok; clean |
| `npx vitest run --maxWorkers=4` on `PlanFallbackOffer.test.tsx`, `ConnectAI.test.tsx`, `ChatGPTPlanSettings.test.tsx`, `App.wrapUpSkim.test.tsx`, `autoAdvance.test.tsx`, `dailyPlan.test.tsx`, `queryCache.test.ts` | 7 files, 37 passed |
| `npm run frontend:build` | built |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | finished |
| `db_generate_reference.py`, `db_validate_reference.py` | regenerated (1,006 configuration leaves in 69 sections, head 217); 0 errors after updating the two prose leaf counts (952 -> 1,006) in `Configuration.md` and `Database.md` |
| `validate_vault.py` | passed (1,142 notes) |

`module_validate.py` (895 missing module notes, 474/959 coverage) and `desktop_validate.py`
(an unclassified `components/pdfSelection/testing/syntheticBook.ts`) fail on files this stage
never touched; they are not part of this stage's gate and were left as found.

The test-file lists are reproducible: `git grep -l codex -- 'tests/test_*.py'` (the first set);
the second set is the files matching the changed modules' names (`handlers.(hints|library_ask|
reader_cue_discovery|reading_paths|first_run|chatgpt_plan)`, `request_hint`, `hint_job`,
`library_job`, `cue_discovery`, `reading_path`, `ops.doctor`, `run_doctor`, `ops.startup`,
`startup_maintenance`, `chatgpt_plan`, `plan_fallback`, `cli.render`, `attempts.regrade`,
`parameter_registry`, `learnloop_sidecar.context`/`.server`, `config.compat`) or the routing entry
points (`active_provider`, `fallback_provider`, `ready_client_for_task`, `check_ai_runtime`,
`make_ai_provider_client`, `runtime_for_provider`, `provider_for_task`), minus the first set.
About 450 test files ran in all; the landing gate's full suite covers the rest (notably files that
reach the default route only indirectly).

**Process notes.** No live or paid call, no sign-in, no run on any vault copy (no smoke run was
needed: every behaviour is pinned with fakes). Every Python run outside pytest used `env -i` with an
empty HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR (the reference scripts, edit scripts), except one early
2026-10-23 edit script that rewrote `tests/test_ai_config.py` with plain `python3`: it imported
only `pathlib` (no LearnLoop module, no network, no credential read). No tracked fixture vault was
opened; `git status` is clean apart from the commits below.

**Commits on `ai/plan-first-transport`** (from `55063be64`), then this record's commit:

- `42ab0bc90` WIP T1 plan-first transport: resumed partial work (config profiles, Codex refusal, OpenRouter offer, doctor fix, sidecar RPC, desktop banner, tests)
- `dbefcfbad` T1: move existing tests to the plan-first defaults (use_codex_harness opt-in helper for frozen Codex doubles, patch_plan_ready for readiness-only tests, default route pins on the plan tiers)
- `d35c9982b` T1: existing tests follow the owner decisions (Codex never a fallback, plan defaults in pins and goldens, opt-in for the frozen Codex doubles)
- `50126c457` T1: a grant never serves background work (quiet probes and startup maintenance honour no grant; a deferred regrade backlog waits for the plan)
- `35a258d3b` T1: regenerate the references (1006 configuration leaves in 69 sections: the four ChatGPT-plan profiles, ai.agent_harness_opt_in, ai.plan_fallback_profile; schema head 217 unchanged; 0 validation errors)
- `9d3f7bca3` T1: compare and landing tests pin tools mode explicitly (they script workspace rounds; inline is the default); the compare-keep golden's three unavailable reasons edited by hand

## Open questions (defaults in force)

| # | Question | Default |
|---|---|---|
| Q1 | Slugs: does the account list `gpt-5.6-sol` and `gpt-6-luna`? | the defaults; doctor names any unlisted slug |
| Q2 | Grant scope: the feature's tasks for the desktop session (vs. one request) | session, per feature, per vault, only tasks that vault was offered (review F4) |
| Q3 | A `fallback_provider` the owner wrote (non-Codex) still serves an unavailable plan route silently; should it ask instead? | **closed by review F1:** it asks. For a plan route a metered `fallback_provider` is never used; doctor reports it (`ai:plan_metered_fallback`) |
| Q4 | Strict `json_schema` on the plan (never verified live) | `json_schema`; flip to `json_object` per profile if `ai latency` says so |
| Q5 | Shared usage pool with the Codex CLI | assumed shared |
| Q6 | Tools mode for an oversized export even when `workspace_mode = "inline"` is explicit | **closed by review F7:** no. An explicit inline refuses; only the unwritten default overflows to tools, and a tools turn's resent input is capped at 4 x `max_workspace_chars` |
| Q7 | Post-attempt diagnosis and exam grading run after their RPC answered: should their unavailable plan route raise the banner on its own (a pushed event) rather than at the next feature RPC? | no push in T1; they report through their own deferred state |

## T2 retirement list ("retire the Codex serving path")

- Delete `src/learnloop/ai/providers/codex.py`, `codex_lockdown.py`, `codex_http.py`; the
  `runtime.py` shims and its Codex branch; the factory's `codex_sdk`/`http` branches;
  `agent_harness.py` (or keep it as a plain "unknown type" refusal); the `TYPE_CHECKING` imports
  in `attempts/attempts.py`, `attempts/regrade.py`, `ops/startup.py` and startup's Codex runtime
  and `CODEX_PROVIDER_NAMES` regrade branch; the `codex_*` CLI labels (`cli/app.py`,
  `cli/runtime.py`), `content/pipeline/add_source.py`'s Codex checks, the sidecar `kill-codex`
  CLI verb, doctor's `codex_runtime` field (a JSON contract change) and `[codex]` config.
- Config: `CodexSDKProviderConfig`, `CodexHTTPProviderConfig`, the code-default `codex*`
  profiles, `LEGACY_CODEX_TASK_ROUTES`, compat's Codex aliasing, `ai.agent_harness_opt_in` (and
  its registry rule), `CODEX_TO_PLAN_PROFILE` once `doctor --fix` has run on the owner's vaults.
- Import-linter: drop `serving-never-imports-the-codex-provider`'s exemptions (or the contract)
  and the security branch's `codex-sdk-only-in-its-provider`.
- Tests: about 86 files with Codex doubles (`install_fake_codex_sdk`, `legacy_codex_http_double`,
  `stub_isolation_probe`, `check_codex_runtime` patches) move to `StructuredClientFake` or the plan
  fakes; delete `test_codex_*` lockdown/runtime files and `codex_cli_fakes.py`. Start with the
  tests T1 opted in explicitly (`git grep -l "use_codex_harness\|agent_harness_opt_in.*True" tests`),
  then drop `use_codex_harness` and `patch_plan_ready`'s Codex counterpart fixtures.

## Landing onto main (2026-10-23)

Landed in worktree `learnanything-merge2`, branch `merge/t1-onto-main`, from main `558e85ab1` (UX2 on top of
the security hardening rounds 2-3, RW2c and RW5a). Main is not fast-forwarded here; the orchestrator lands it.
No migration (head **217**, head fixture `migration_head_217` unchanged) and no algorithm successor.

### Commits and conflicts

- `b60e146f0` the merge of `ai/plan-first-transport` (`536b78419`). Conflicts:
  - `config/template.py`: the 20 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries, each keeping both sides' comment
    lines (main's RW2c and UX2, then T1's), main's fingerprints in place until the regeneration;
  - 412 generated reference notes: main's side, then regenerated.
  - Everything else merged without conflict: `config/schema.py`, the parameter registry (main's `figures.*`,
    `workbench.*`, `ui.shell` keys beside T1's `ai.*` keys), `ai/routing.py`, `ai/client.py` (T1's
    agent-harness refusal first, then main's round-2 `refuse_legacy_http_transport` for `http`/`http_adapter`),
    the Codex provider and lockdown modules (main's; T1 does not touch them), `App.tsx`, `dto.ts`,
    `client.ts`, `commands.rs`, `main.rs`. T1 adds no window keydown listener (`PlanFallbackOffer.tsx` and
    `ChatGPTPlanSettings.tsx` have none), so the `screenLeavesKey` guard has nothing new to cover.
- `bb279900e` `classicIsBase.test.ts`. T1 changes `components/ChatGPTPlanSettings.tsx` and adds
  `components/PlanFallbackOffer.tsx` (both shells), so the exact-list check failed. **Deviation from the brief:**
  moving `BASE` to main's tip (`558e85ab1`, which already holds UX2) would empty UX2's own diff, so the exact-list
  check and the round-5 guard-file check (`added.length > 0`) would fail or compare nothing. `BASE` stays
  `a9ae97e34` with a comment, and a new `LATER_LANDINGS` map names T1's two files; `STAGE_CHANGES`,
  `TARGET_RULE_FILES` and every check are unchanged. Failed before, 6/6 after.
- `0ecc600ea` **New finding, fixed: the paid roles never asked about OpenRouter.** See below.
- `df739a1c9` the regeneration.
- `91565a346` gate fixes (three tests and one golden; see the gate).
- `f07dcd338` this record; `172113ce7` the Today fix (below, after the orchestrator's review of the first record).
- `84a3f8947` and `4a8868f09`: the grant-scope fix from the verify of `0ecc600ea` / `172113ce7` (below).
- `88b466d96` (WIP) and `0ee2cebb5`: round 2, from the verify of `84a3f8947` / `4a8868f09` (below).

### Finding at the landing: the paid roles (fixed, `0ecc600ea`)

The brief asked to prove that RW2c's comparison lines and example search and RW5a's figure routes resolve to
the plan and go through the ask-before-OpenRouter path. They resolve to the plan, but they never asked: every paid
role plans a `PaidRoute` (`practice_index.paid.plan_route`) and builds it with `resolve_client`, which resolved
**pinned** (`explicit=route.provider`). Routing never replaces a pinned selection and makes no offer for one. So
hints (`hint_writer`, `hint_outcome`, `approach_map`), the workbench check and RW2c's comparison lines
(`workbench_check`), the example search (`source_query_rewrite`, `source_rerank` and the other source-retrieval
roles), figures (`figure_author`), the AD LLM routes, the practice-index judges and the source-service judges
reported the plan as unavailable but never offered OpenRouter, and no grant could serve them. T1's tests resolved
those tasks through `ready_client_for_task` (unpinned), not through the paid path, so they did not see it. The
gap was already on T1's own base for hints, RW2b's check and RW5a; RW2c's lines ride the same `CheckRoute`.

The fix is in `practice_index/paid.py` only:

- `plan_route` names the OpenRouter profile when all of these hold: the learner granted the task; the feature's
  price is set (`offer_blocker` is `None`); the route is a routed, not pinned, plan route; no readiness probe is
  running (`quiet()` honours no grant); and the plan is not ready. Plan readiness reads local files only. The
  route's billing is then `metered` and every cap applies; it is never `subscription`.
- `resolve_client` resolves a routed plan route through routing's unpinned path. That path makes the offer, and
  a ready route is noted so that a mid-call availability failure also offers. `resolve_client` refuses any
  profile other than the planned one: a grant given after planning, or a configured fallback. A route planned
  under a grant that has since ended ("Stop using OpenRouter") is refused too. Pinned selections
  (`LEARNLOOP_AI_PROVIDER`, embedding, deciders, `field_question_classifier`) resolve as before.

`tests/test_plan_first_transport_paid_roles.py` extends T1's route-resolution property (test 1) to the paid path.
It covers **every `AITask` on the merged tree** (`get_args(AITask)`; main added no `AITask` after `55063be64`, so
its features ride existing tasks, which the test names). It checks, in the paused and signed-out states:

- each routed task plans onto a plan profile billed as the subscription;
- `resolve_client` returns no client and makes exactly the offer `ready_client_for_task` makes;
- probes and pinned selections ask nothing;
- a grant plans and builds OpenRouter as metered;
- a revoke refuses a route planned under the grant;
- a ready plan always comes first;
- nothing is sent to the plan or OpenRouter.

It failed before the fix (first routed task, then the revoke case) and passes after.

### Regeneration (`df739a1c9`)

- **Defaults snapshots.** The template `.pyc` was cleared, and the snapshots were recomputed and checked with
  `-B` under `env -i` (empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`). All **20** entries were rewritten
  (main's RW2c/UX2 defaults plus T1's plan profiles and `ai.*` keys), then **0 mismatches**.
- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, schema head **217**,
  **339** table notes, **1,011** configuration leaves in **69** sections (main 957 + T1's 54). The two prose
  counts (`Configuration.md`, `Database.md`) were updated from 957.
- **Unchanged, with their tests passing:** the CLI help snapshot, the RPC pins, the serializer snapshot and the
  mobile allowlist. Their tests (`test_cli_help_snapshot`, `test_mobile_allowlist`, `test_sidecar_transport`,
  `test_sidecar_serializer_snapshot`, `test_required_method_items`, `test_config_refactor`,
  `test_settings_store`) and every test file reading `DEFAULTS_SNAPSHOT_BY_ALGORITHM` gave 318 + 531 passed.
- **`validate_vault.py`**: passes (1,142 notes, 1,140/1,140 reachable).
- **Failing before this stage, not fixed:**
  - `desktop_validate.py` still stops on `components/pdfSelection/testing/syntheticBook.ts`;
  - `module_validate.py` reports **1,005** issues (999 at the UX2 landing; the 6 new ones are T1's new modules
    without notes, such as `ai/agent_harness.md` and `ai/chatgpt_plan/*`).

### Gate

Setup: `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` (5.14.0), `TMPDIR` = merge2's
`fixtures-local/tmp`, every later command `uv run --no-sync`. Every pytest, vitest, npm and cargo command ran in
a `systemd-run --user --scope` (pytest 10G/2G with `-n 8`, never `-n auto`; vitest and the rest 5G/1G), one test
command at a time, with the full suite and durability under `flock /tmp/learnloop-fullsuite.lock`. Logs are in
`fixtures-local/landing-t1/out/`.

| Step | Result |
|---|---|
| `lint-imports --no-cache` | **31 kept**, 0 broken: main's 30 plus T1's `serving-never-imports-the-codex-provider`, beside the security branch's `codex-sdk-only-in-its-provider` |
| full suite at `df739a1c9` (`-n 8`, 44 min) | **15,755 passed**, 8 failed, 3 skipped, 2 xfailed. Six were real composition failures, fixed in `91565a346` (below). Two were load flakes that passed alone 3 times out of 3: `test_reading_hardening_2_fixes::test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep` and `test_reading_request_sweep::test_b_a_start_deferred_behind_a_queued_build_runs_that_build_and_then_acts` |
| the six, after `91565a346` (with the paid-role tests) | 46 passed |
| after `172113ce7` (the Today fix; targeted, no full rerun): the new test, the three `test_plan_first_transport*` files, the teach-back, daily-plan, probe-pool, router-offer and queue-serialization files, and every test file naming `authoring_provider_available` / `teach_back_offerable` / `reconcile_empty_probe_pools` / `filter_unready_teach_back` (22 files) | **303 passed** |
| after `172113ce7`: every test file naming `get_today_queue`, `next_plan_item` or `start_teach_back` (32 files) | **849 passed** |
| `lint-imports` after `172113ce7` | 31 kept, 0 broken |
| after `84a3f8947` (grant scope): the four `test_plan_first_transport*` files, the lockdown and `test_chatgpt_plan_*` files | **225 passed** |
| after `84a3f8947`: the job and worker files touched (ingest runner/jobs, hints, library ask, cue discovery, reading paths, item authoring, sidecar context and transport, and every file naming the job classes or `IngestRunner(`; 44 files) | **901 passed**; `lint-imports` 31 kept |
| after `4a8868f09`: every file naming the key-check ladder, imports or `exercise_verification` (14 files) | **535 passed** |
| **full suite at `4a8868f09`** (`-n 8`, 10G scope, under the lock; the dispatch and the runner core changed) | **15,775 passed**, 0 failed, 3 skipped, 2 xfailed (33 min) |
| durability (`-m durability`, at `91565a346`) | **119 passed** |
| `npm install`; `npm run typecheck` | ok; clean |
| `npm test -- --maxWorkers=4` (the whole vitest run) | **198 files, 1,665 tests passed**, no unhandled error, no snapshot written (UX2's landing: 197 / 1,658) |
| `npm run frontend:build` | built |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished |

The six composition failures, fixed in `91565a346`:

- `test_codex_lockdown_round2.py` (3: an `http`/`http_adapter` profile, the http runtime check). T1's
  agent-harness gate now refuses these before main's tool lockdown is reached. **Both layers are kept and
  pinned**: without `ai.agent_harness_opt_in` T1 refuses; with it, the lockdown still refuses. Neither runs a
  health request or a startup command.
- `test_roles_switch_off.py` (RW4e's switch-off golden). The three `rewrite.reason` strings of an unavailable
  route are now the signed-out plan's, not the missing Codex checkout's. The golden was edited by hand (exactly
  three strings), as T1 did for `compare_keep_switch_off.json`.
- `test_source_retrieval_codex_unavailable.py` (2). The test's fake `ResolvedClient` now names the profile it
  resolved, because `resolve_client` checks that profile against the planned one (the paid-role fix).

### Parity (backup-API copies; `fixtures-local/landing-t1/`)

**Setup.**

- `fixtures/linear_algebra` and `fixtures/probability` were copied from the **main checkout** with
  `learnloop.db.copies` (both at `mvp-0.8`). `arxiv_v2` was never opened.
- Every run used `env -i` with an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, so the plan was signed
  out.
- (a) and (b): every route was on a 127.0.0.1:9 profile or off (`neutralize3.py`). Learner-text gaps,
  `build_on_serve` and outcome placement were off.
- (c): every chat route was on a `chatgpt_plan` profile; every provider `base_url`, the plan's and OpenRouter's
  included, was 127.0.0.1:9 (`planify.py`).
- (d): the vaults' own Codex pins were kept, with every `base_url` at 127.0.0.1:9 (`dprep.py`).
- `run.py` installs an audit hook that logs every process start and **refuses** any whose arguments mention
  Codex.

| Check | Result |
|---|---|
| (a) schema and rows, main vs merge, `mvp-0.8` copies opened by each code | both migrate 51 to head **217**. 1,451 / 1,450 schema objects identical, 0 SQL differences, every row identical (16,542 / 7,640 rows in 344 tables). `schema_migrations` differ only in `applied_at`. `foreign_key_check` 0, `integrity_check` ok, WAL |
| (a) `rebuild --shadow`, `doctor` | identical after normalisation (both vaults) |
| (b) certification, recipe gaps, curves, Today, daily plan at a frozen clock, at `mvp-0.8` | **byte-identical** (both vaults) |
| (b) the same after main's upgrades to `mvp-0.27` and `mvp-0.29` | certification and Today **byte-identical**. The daily plan is identical except `router_decisions.card_hash`, `snapshot_hash` and the card hash inside `detail_json`. A second run of main's code on a fresh copy differs from the first in exactly these three fields, and from the merge's in exactly these three (`plan_repeat.sh`): run-to-run noise, as at the earlier landings |
| (c) the real sidecar, main vs merge, at `mvp-0.8` (migrated) and `mvp-0.29`, both vaults, no key and a FAKE `OPENROUTER_API_KEY` (16 runs, 12 calls each) | see the differences below |
| (d) `doctor` on the vaults' own settings | main reports no Codex finding. The merge reports `ai:codex_route_pinned` (warning): **8** on linear_algebra (`ai.active_provider` and 7 routes) and **9** on probability (`ai.active_provider` and 8 routes, `animation` included). Every other issue is identical to main's |
| (d) `doctor --fix` on a SECOND copy (the merge) | `--fix --dry-run` writes nothing. `--fix` rewrites `active_provider = "codex"` to `"chatgpt"` and each `codex_low` / `codex_medium` route to `chatgpt_low` / `chatgpt_medium` (comments kept; diffs in `out/d/*_fix.diff`). Afterwards `doctor` reports exactly main's issues |
| no Codex process, no live call | the audit log is **empty**: no process of any kind was started, so none was refused. **0** `model_call_receipts` rows of any status on all 48 copy databases |

The differences in (c), every one listed:

- `initialize` and `load_vault`:
  - `capabilities.methods` has 433 entries on main and 434 on the merge (`ai_use_fallback`);
  - `availableGradingProviders` has 11 entries on main and 10 on the merge (Codex profiles are no longer
    offered: T1 review F9);
  - `health.codex.status` is `provider_missing_config` on main and `provider_unavailable` on the merge (refused
    by T1's gate);
  - the merge's config lists the `chatgpt_low`, `chatgpt_medium` and `chatgpt_luna` profiles.
- `get_config`: the same three profiles.
- `get_ai_connection`: **identical** on both codes, with and without the key: `needs: "connect"`, "Not signed in
  with ChatGPT on this machine", no `fallbackAvailable` (a status read makes no offer).
- `chatgpt_plan_status`: `signed_out` on both. The merge lists 4 profiles (main 1) and adds
  `openrouterGrantedTasks: []`.
- No key: Today, the practice serve and the tutor question are identical. The tutor question is refused
  `provider_unavailable` on both, and there is no offer anywhere.
- Fake key:
  - the merge's tutor error carries `details: {fallback_available: "openrouter", fallback_tasks: ["tutor_qa"],
    plan_signed_out: true}` (the offer is shown, nothing is sent);
  - on **linear_algebra**, `get_today_queue` gains the top-level hint `fallbackAvailable: "openrouter",
    fallbackTasks: ["authoring", "teach_back"], planSignedOut: true`. The queue itself is identical.
- Certification and plan (in (b)) and the Today queue's content are byte-identical.

**New finding: the Today read raised the OpenRouter banner (fixed, `172113ce7`).** At `f07dcd338`, with an
OpenRouter key and the plan unavailable, Today raised the "Use OpenRouter instead" banner for `authoring` and
`teach_back`. Both `get_today_queue` and the daily plan's `next_plan_item` (found by the sweep below) carried the
hint, although the learner had used no AI feature. Today ran two readiness probes outside `plan_fallback.quiet()`:

- the teach-back filter (`teach_back_offerable`, for the queue's and the daily plan's unready teach-back items);
- the empty probe-pool sweep (`diagnostic_surface_supply.authoring_provider_available`, called from
  `build_due_queue`).

Owner rule: ask only when a feature the learner USED could not run. The fix:

- `teach_back_offerable` runs under `quiet(honour_grants=True)`. It makes no offer, but a grant still counts, so
  once the learner chose OpenRouter for teach-back, Today offers teach-back items again.
- `authoring_provider_available` runs under `quiet()`. It makes no offer and honours no grant, because what it
  gates is background generation.
- `start_teach_back` (the feature, used) resolves its provider itself and still asks.

`tests/test_plan_first_transport_today_quiet.py` failed on `f07dcd338` (both tests) and passes after. It checks:

- `load_vault`, `get_ai_connection`, `get_runtime_health`, `get_today_headline`, `get_start_summary` and
  `get_today_queue` (with and without a session) carry no offer;
- the teach-back item is still filtered out while its AI is down;
- `start_teach_back` reports `provider_unavailable` with `fallback_tasks: ["teach_back"]`;
- after a grant of `teach_back` and `grading`, Today serves the teach-back item and still asks nothing;
- the probe-pool sweep makes no offer and honours no grant;
- nothing is sent.

**Sweep of the desktop's load and Today RPCs.** These are the RPCs `App.tsx`, `TodayScreen.tsx` and
`StartScreen.tsx` call:

- `initialize`, `load_vault`, `get_ai_connection`, `get_runtime_health`, `get_review_counts`,
  `get_source_library`, `chatgpt_plan_status`;
- `get_start_summary`, `get_today_headline`, `get_queue_revision`, `get_reentry_summary`, `get_decay_pressure`,
  `get_overconfidence_list`, `goals_list`, `get_goal_report`, `list_ingest_batches`;
- `get_today_queue`, `start_session`, `next_plan_item`, then `get_today_queue` again.

They were driven through the merge's `_handle` on fresh copies of the four parity vaults (c8 and c29, both
fixtures, planified, fake OpenRouter key), with a hook printing the stack of every offer noted (`today_probe.py`).

- At `f07dcd338` the only offers came from these two probes: `get_today_queue` and `next_plan_item` on
  linear_algebra.
- After the fix, **no call on any copy carries an offer**. `get_overconfidence_list` and `get_goal_report`
  answered a parameter error to the empty params; neither made an offer.
- 0 receipts and no process start.

### Verify of `0ecc600ea` and `172113ce7`: a grant served background work (fixed, `84a3f8947`, `4a8868f09`)

The verify **reopened with one Medium** (no High). It confirmed the rest:

- nothing is sent without a grant;
- grants stay per task;
- a ready plan always comes first;
- billing and caps are correct;
- pinning holds;
- Codex is unreachable;
- the Today fix holds.

**The Medium, a regression from `0ecc600ea`.** `paid.plan_route` / `_granted_provider` honoured any session grant
not under `quiet()`. A grant was process-wide, so background threads used it:

- the import-key-check recovery started on every `load()` (`context.py`, `import-key-check-recovery`);
- the Reader import's background key check (`jobs._verify_quietly`, `reader-import-key-check`);
- the edit re-check (`item_authoring`, `edit-key-recheck`).

Example: a learner who granted `source_solution_match` in a primed retry had those checks served by OpenRouter
from then on. The same risk was latent in `build_on_serve`, hint outcome placement and AD preparation.

**The fix, by construction** (`learnloop/ai/plan_fallback.py`):

- **`interactive()`** marks the thread serving one learner request. It is set by the sidecar's RPC dispatch
  (`server._handle`) and by the CLI command (`command_grant`; not for `learnloop mcp serve`). The flag holds that
  thread's ident, so a context copied to another thread (`copy_context()` workers) is not interactive.
- **`is_granted`** honours a session or command grant only on that thread, or under a job token (below). Never
  inside `quiet()`, which is unchanged. Every other thread, now and in the future, defaults to no grant.
- **Per-job tokens.** `capture_grant(vault_root)` returns a token, but only inside a learner request (or a job
  that carries one) and never under `quiet()`. The token names the vault and the tasks granted then.
  `job_grant(token)` enters it on the worker. At use, a session task must still be granted, so "Stop using
  OpenRouter" ends a running job's use at its next route.
- **The jobs that carry a token,** each because the learner pressed the feature and its retry after "Use
  OpenRouter instead" runs off the RPC thread:
  - the sidecar's four feature jobs whose offers T1 relays: hints (`HintJobs`, also the workbench's help, the
    worked example and "Compare with the book's method"); the library ask/notes/compare/tutor jobs
    (`LibraryJobs`, also the figure build and revise); margin-note discovery; and the Guide's reading path;
  - every ingest batch enqueued in a learner request, or by a job carrying a token
    (`runner._enqueue_batch` captures, `_run_claimed` enters). This covers the add-source build (review F3),
    Reader quick and inquiry checks, exercise imports and the other runner jobs the learner starts. The token
    lives in process memory, so after a restart a batch runs on the plan;
  - the import's time-boxed key check (`source_exercise_import._run_time_boxed`). It runs on a copied-context
    thread inside the primed retry's import, and it carries that request's token (`4a8868f09`).
- **Nothing else carries a token** and nothing inherits one implicitly:
  - the three key-check threads above, which are fresh threads;
  - the shared background launcher (`BackgroundBuilds.launch`, a fresh `contextvars.Context()`), which serves
    `build_on_serve`, hint outcome placement and AD preparation;
  - the post-attempt worker and exam grading, which copy the RPC's context to another thread (so a deferred
    diagnosis waits for the plan, consistent with Q7);
  - the daily-plan router's parallel components and the teach-back summary (copied contexts).
- **Low, fixed:** with `ai.fallback_provider = "manual"`, `_granted_provider` returns `None`, because routing
  answers manual before any grant.
- **In-request paths that still use a grant:** the primed retry's `import_source_exercise` (synchronous in the
  RPC, with its time-boxed check carrying the token); the workbench check (synchronous); hints, compare,
  examples and figures (token jobs); `start_teach_back` (synchronous). The existing T1 grant tests now resolve
  inside `interactive()`, through an autouse `learner_request` fixture in `test_plan_first_transport.py` and
  `test_plan_first_transport_paid_roles.py`, and one wrap in `test_chatgpt_plan_provider.py`.

**Tests** (`tests/test_plan_first_transport_grant_scope.py`, 10 tests). Every test fails on `091a7cfcb`. That
was shown by running the file against an export of that tree with a shim that adds the new names (`interactive`
as a no-op, and so on) over the old behaviour. All pass after the fix.

- the property over every paid `AITask`:
  - outside a request, no grant serves;
  - inside one, exactly routing's grants serve;
  - a fresh thread and a copied context plan nothing onto OpenRouter;
  - a job with the request's token plans exactly the request's routes;
  - `quiet()` honours nothing;
  - a revoke ends a carried token;
- the CLI command's grant: its own thread only, or a captured token; none for a host;
- `fallback_provider = "manual"`: never replaced;
- with `source_solution_match` granted, the startup recovery, the Reader import's background check (started
  from inside a job carrying the grant) and the edit re-check each plan onto the plan profile, billed as the
  subscription, and build no client;
- the shared background launcher (`build_on_serve`, hint outcome, AD) plans `approach_map`, `hint_outcome`,
  `ad_forecast_llm`, `ad_feature_audit` and `hint_writer` onto the plan under a grant;
- a hint job started in the request carries its grant, and one started off a request does not;
- an ingest batch carries the token only when the learner enqueued it;
- the import's time-boxed check carries its request's grant, and the same check off any request does not.

Nothing is sent in any of these tests.

**Lows recorded, not fixed:**

- a configured plan-to-plan `fallback_provider` cannot serve a paid role: `resolve_client` refuses a profile
  other than the planned one (`paid.py`);
- the CLI eval tasks without a `METERED_PRICE_SETTINGS` entry get an offer that their command may then refuse;
- revoking a grant does not stop a multi-call job between routes. A token job stops at its next route, but a
  call already running finishes;
- Today needs both the `teach_back` and the `grading` grants before it shows teach-back items again;
- the daily-plan router's parallel components run in copied contexts, so they carry no grant, while the first,
  inline one does.

### Verify of `84a3f8947` and `4a8868f09`: only a press carries a grant into queued work (fixed, `0ee2cebb5`)

The Opus verify **reopened with one Medium and two Lows**. The orchestrator's ruling: the Medium stands, because
scrolling is not pressing.

**The Medium.** Every RPC counted as a learner request, including the RPCs the desktop sends by itself:

- `reader.mark_section_progress`, sent on scroll (`useReadingProgress.ts`), handles a first reach of a section
  through `keep_ahead_for_reader`, which leads to `act_on_reading_request` / `request_auto_build` and then
  `runner.enqueue_batch`;
- a completed section is handled by `enqueue_practice_expansion`.

Both enqueues ran inside `interactive()`, and `runner._enqueue_batch` captured a token for **every** task granted on
the vault. The token also chained: `after_auto_build` and child batches re-captured it through
`JobContext.enqueue_batch`. So a learner who granted `canonical_ingest` on "Create study map" queued keep-ahead and
practice-expansion builds on OpenRouter merely by scrolling. The reading sweep acting on the same request ran on
the plan, which was inconsistent.

**The fix, by construction:**

- **(a) Opt-in at the presses.** `learnloop_sidecar/pressed.py` names `PRESSED_RPCS`, the RPCs a learner press
  sends, each with its feature, and the dispatch (`server._handle`) enters `plan_fallback.pressed(vault, feature)`
  for them alone. The presses, by feature:
  - **build:** Add, the book card's actions (Build now, Build the whole book, Retry, Allow upload, Read again with
    OCR), Create study map, Quick add, Import, Inventory, Extraction repair, Resume batch;
  - **Reader check:** the section question, the selection check, the inquiry answer;
  - **exercise import:** the Reader's import, the textbook import, the workbench retry, the primed retry;
  - **the rung variant**, **the animation** and **question promotion**;
  - **practice:** create goal, starter practice, commissioning practice;
  - **hints and workbench:** request hint, Check my work, request help, Compare, Show example;
  - **library:** ask, notes, tutor, compare, figure request and revise, Find exercises;
  - **the reading path,** only on its retry.

  `runner.enqueue_batch` never captures. A batch carries a token only through an explicit `grant=`, or from the
  press around the call (`plan_fallback.pressed_token`). An AST test pins that `plan_fallback.pressed(` is entered
  only by the dispatch.
- **(b) Narrowed tokens.** A token names `plan_fallback.FEATURE_TASKS[feature]` ∩ the vault's grants, never every
  granted task. For example, a build carries `canonical_ingest`, `canonical_ingest_retry` and `authoring` at most.
- **(c) Children.** `JobContext.enqueue_batch` passes a token on only with `inherit_grant=True`, which is used once:
  the planner's own planned build (`run_auto_study_map`). `after_auto_build`'s keep-ahead and every other follow-up
  inherit nothing. `job_grant` is now always entered by a job's runner, token or not. Inside a job, neither the
  learner request nor a press around it counts: a job drained in the pressed request's own thread is still a job.
- **(d) A second guard.** `mark_section_progress` runs its keep-ahead and practice-expansion enqueues under `quiet()`.
- **The sidecar jobs.** The four feature jobs (hints and the workbench, the library and figures, margin notes, the
  reading path) take their token from the press around their start, narrowed to its feature. A job that no press
  started runs under `quiet()`: margin-note discovery on open, the reading path on open, a workbench suggestion, the
  library's exercise candidates. It asks nothing, because a grant could never serve it.
- **The CLI.** The command with `LEARNLOOP_AI_FALLBACK=openrouter` is its own press, with every task on any vault.
  The work it queues and drains carries that grant; a host (`learnloop mcp serve`) carries none.
- **In-request (synchronous) calls are unchanged.** In any RPC they use a grant the learner gave, because they are
  that request.

**Low 1, fixed:**

- `runner.resume_batch` refreshes the batch's token from a press (a pressed Retry: `source_action` retry,
  `retry_build`, `resume_ingest_batch`, the workbench retry), narrowed. Otherwise (startup, a sweep, a job) it drops
  the token.
- `revoke(vault)` drops that vault's batch tokens, so a later re-grant revives nothing.

**Low 2, fixed:**

- a batch runs through `_run_claimed`, with `job_grant` entered only for a pressed enqueue;
- the dispatch's own marker is pinned.

**What carries a token now, and why:** a batch enqueued by a pressed RPC, or the pressed planner's own planned build;
a sidecar job started by a pressed RPC; the import's time-boxed key check inside a pressed import or a job carrying
a token; the CLI command with the variable set. Each is narrowed to its feature. Nothing else carries one.

**Tests** (`tests/test_plan_first_transport_pressed_grants.py`, 8 tests). They fail on `47ba994e7`, shown by running
the file against an export of that tree with the new names shimmed over the old behaviour
(`fixtures-local/landing-t1/out/r2-fail-before-shim.log`). The frontend-enumeration test there fails only on the
export's missing `client.ts`, since it is a property of the new table. All pass after. The tests:

- scrolling a book (`mark_section_progress` through `_handle`: first reach and completion of two sections) queues
  keep-ahead builds, none of which carries a token;
- "Build the whole book" (`source_action`) carries a token narrowed to the build's tasks;
- `_run_claimed` grants a pressed batch's job, and neither an unpressed-request batch nor a background one;
- a child carries a token only when told to, and a job drained in the pressed thread sees no press;
- a resume refreshes from a press or drops the token, and `revoke(vault)` clears it with no revival on re-grant;
- the dispatch marks every RPC interactive and only `PRESSED_RPCS` pressed. Every registered RPC, dispatched with a
  stub that enqueues, carries a token exactly when it is a press, narrowed to its feature;
- no RPC the desktop calls (from `api/client.ts`) that it sends by itself is a press: job polls, `get_`/`list_`
  reads, progress, status, margin-note discovery, the workbench opening and suggesting, the exercise candidates,
  the daily plan's next item, vault load and the AI connection;
- only the dispatch enters a press, and only audited sites pass `inherit_grant`.

The existing tests now start their jobs inside their presses: `test_plan_first_transport.py` (the background-jobs
offer test, plus a check that an unpressed job asks nothing) and `test_plan_first_transport_grant_scope.py`.

| Run | Result |
|---|---|
| the five `test_plan_first_transport*` files, the lockdown and `test_chatgpt_plan_*` files | **234 passed** |
| every ingest/runner/reader/reading/UX-phase-1/workbench/hint/library/figure/cue/first-run file and every file naming `mark_section_progress`, `enqueue_batch`, `resume_batch`, `source_action`, `IngestRunner(`, the job classes or `plan_fallback` | **3,341 passed**, 1 skipped |
| `lint-imports` | 31 kept, 0 broken |
| full suite at `0ee2cebb5` (`-n 8`, 10G scope, under the lock; the runner core and the dispatch changed) | **15,782 passed**, 1 failed, 3 skipped, 2 xfailed (33 min). The one failure is the known load flake `test_reading_hardening_2_fixes::test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep` (it also failed in the first gate at `df739a1c9`, before any grant change); it passed alone 3 times out of 3 |

**Lows recorded, not fixed:**

- `PRESSED_RPCS` is maintained by hand. A new press must be added there, or its queued work runs on the plan (the
  safe default). The table's tests catch an automatic sender added to it, but not a press left out of it.
- `source_action`'s `allow_upload` resumes the add batch as a press (`build`); the learner pressed it.

### Owner notes

- **No migration** (head 217) and no successor: only the served model changes (Codex to the plan's models),
  which the owner approved.
- **What the learner sees:**
  - every serving route defaults to the tool-free ChatGPT plan (`chatgpt`, `chatgpt_low`, `chatgpt_medium`,
    `chatgpt_luna`);
  - Codex is refused unless `ai.agent_harness_opt_in = true`, and is never a fallback;
  - while the plan is unavailable, each feature shows its own unavailable state. If OpenRouter is set up, one
    banner offers "Use OpenRouter instead" (and "Continue with ChatGPT" when signed out). Nothing is sent to
    OpenRouter until the learner chooses, and a grant never serves background work. Since this landing that
    includes hints, the workbench check and "Compare with the book's method", worked examples and figures,
    each once its price is set;
  - Settings shows "Stop using OpenRouter" while a grant holds.
- **The owner's vaults pin Codex** (`active_provider = "codex"`, `codex_low`/`codex_medium` routes). Until
  `learnloop doctor --fix` runs on them, their AI features read "unavailable" (refused), with the doctor
  warning naming each setting.
- **Owner-run commands:**
  - `learnloop ai signin chatgpt` (or desktop Settings, then "Continue with ChatGPT");
  - after **2026-10-27**, `learnloop ai models chatgpt` (confirms `gpt-5.6-sol` / `gpt-6-luna`; doctor
    remembers the list);
  - `learnloop ai latency --provider chatgpt` on a copy (synthetic prompts);
  - `learnloop doctor --fix --dry-run`, then `learnloop doctor --fix`, on each vault.
- The plan likely reads as unavailable or paused until the shared usage resets on **2026-10-27** (Q5 assumes
  it shares the Codex pool). Meanwhile the ask-OpenRouter path serves: the desktop banner, or
  `LEARNLOOP_AI_FALLBACK=openrouter` for one CLI command.

### Open questions (defaults in force)

Q1-Q7 above, unchanged:

- Q1, slugs: the defaults, and doctor names any unlisted slug;
- Q2, grant duration: per feature, per vault, for the sidecar session;
- Q3, a non-Codex `fallback_provider`: asked, never used silently;
- Q4: `json_schema`;
- Q5: the usage pool is assumed shared;
- Q6: inline is the default; tools mode applies only for an oversized export under the unwritten default;
- Q7: no post-attempt push.

### Open items

- `module_validate.py` (1,005) and `desktop_validate.py` (`syntheticBook.ts`) fail as before. T1's new modules
  have no module notes.
- The full suite ran at `df739a1c9`. `91565a346` changes three tests and one golden only, verified by the
  targeted run and by the durability lane at that head. `172113ce7` (two readiness probes made quiet) was verified
  by the targeted runs above. After the grant-scope fix, the full suite ran again at `4a8868f09` and was green.
  One earlier attempt at `84a3f8947` was stopped at 98%: one xdist worker was stuck in
  `test_reading_request_sweep::test_b_…` at a load average of about 190 (another stage's suite was also running).
  That file and `test_reading_hardening_2_fixes.py` then passed alone (19 passed). The durability lane was not
  rerun (no database or connection change since `91565a346`).
- The Lows recorded in the verify section above (plan-to-plan fallback for paid roles, CLI eval offers, revoke
  mid-call, Today's two grants for teach-back, the router's parallel components).
- T2 (retire the Codex serving path) as listed above. Main's round-2 lockdown tests now pin both layers. When T2
  deletes the Codex modules, they go with them.
