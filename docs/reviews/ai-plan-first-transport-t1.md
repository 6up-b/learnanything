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
