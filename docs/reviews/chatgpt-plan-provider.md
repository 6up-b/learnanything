# ChatGPT-plan provider ("Continue with ChatGPT")

Stage: `providers/chatgpt-plan` (worktree `learnanything-chatgpt-plan`, base `b2a2bd2e`).
Prompt: `docs/specs/implementation_handoffs.md` §4, "ChatGPT-plan provider".
Owner direction (2026-10-12): route short structured calls (T6's query rewrite
and verification first) to a fast, capable model on a subscription, and use
Sign in with ChatGPT instead of spawning a Codex instance.

## Plan (written before coding)

**Goal.** A provider type `chatgpt_plan` that calls OpenAI models billed to the
owner's ChatGPT plan through Sign in with ChatGPT token sharing for open-source
apps: one HTTPS request per structured call, no Codex process, no tools.

**Files to add.**
- `src/learnloop/ai/chatgpt_plan/` (machine-local sign-in and session):
  - `store.py`: the credential store outside every vault and the repo, under
    `<LearnLoop config dir>/chatgpt_plan/` (the directory that holds
    `settings.env`): non-secret `account.json`, tokens in the OS keyring when
    the optional `keyring` package has a usable backend, else `tokens.json`
    (0600, atomic writes), the host id, the pause/eligibility state and a
    refresh lock;
  - `oauth.py`: PKCE S256, state and nonce, the authorization URL (first
    registration with `dynamic_agent_client`, later sign-ins with the saved
    `oaiapp_…` id), the loopback listener on `127.0.0.1` (`/auth/callback`),
    the code exchange, refresh with rotation, revocation, and ID-token
    validation (issuer, audience, expiry, nonce; RS256 signature against the
    issuer's JWKS);
  - `session.py`: the access token for a call (refresh near expiry, serialized
    across processes; `invalid_grant` and the other terminal refresh errors
    clear the tokens and require a new sign-in), readiness, sign-out, the
    usage-limit pause;
  - `responses.py`: the Responses request body (`store=false`, `stream=true`,
    `instructions`, no unsupported fields, no tools) and the SSE reader, with
    the documented error codes mapped to LearnLoop errors.
- `src/learnloop/ai/providers/chatgpt_plan.py`: the structured transport.
- `src/learnloop/cli/ai.py`: `learnloop ai signin|signout|status|resume|models chatgpt`
  and `learnloop ai latency`.
- `src/learnloop_sidecar/handlers/chatgpt_plan.py`: desktop sign-in RPCs.
- Desktop: a "ChatGPT plan" Settings section with a **Continue with ChatGPT**
  button, the first-sign-in confirmation, "Using ChatGPT plan" and
  **Manage usage** per the UI/UX guidelines.

**Files to change.** `config/schema.py` (profile type), `ai/client.py`,
`ai/runtime.py` (readiness), `ai/spend.py` and the local copies of the
subscription type sets (billing class `subscription`), `ai/disclosures.py`,
`ops/doctor.py`, the config template (a commented example), the sidecar
settings payload, `tests/conftest.py` (tests never reach an OS keyring),
`tests/test_mobile_allowlist.py`.

**Migrations.** None: the store is machine-local files, not vault state.

**Algorithm successors and kill switches.** Nothing served changes. The
provider is used only by a route that names a `chatgpt_plan` profile;
unconfigured means nothing changes. Per profile, `enabled = false` makes it
not ready (routes that allow fallback fall back), and `learnloop ai signout
chatgpt` turns it off machine-wide.

**Spend caps and model routes.** Billing class `subscription` (Slice A plan §5
rule 6): cost estimated from reported usage (`estimated_only`), call,
candidate, pair and retry caps kept. Receipts name the provider, the profile's
model and the model that answered. The transport also declares the bounded
capability (one physical request per `complete()` under `single_request()`).
Routes: any `ai.routing.*` may name the profile; T6's `source_query_rewrite`
and `source_rerank` first.

**`judgment_ledger` writes.** None: a transport, not a judge. Callers keep
writing their own verdicts.

**Tests.** A fake OAuth server and a fake Responses SSE server, both on
127.0.0.1, with a test RSA key for the ID token. Agents make no live calls to
`auth.openai.com` or `api.openai.com` and never read the real store.

## The docs, re-verified 2026-10-12

Fetched as plain Markdown (no auth) from `developers.openai.com`: `/siwc`,
`/siwc/token-sharing-open-source` (overview), `…/sign-in`,
`…/models-and-inference`, `…/preview-limitations`, `…/token-reference`,
`…/errors-and-recovery`, `…/profiles-and-sessions`, `/siwc/ui-ux-guidelines`
and `/siwc/website`. The Help Center article the owner linked
(`help.openai.com/en/articles/20001542`) answers HTTP 403 to a non-browser
fetch, so it was not read; nothing here depends on it.

Every fact in the prompt's list held. What the docs add or sharpen, and what
the build follows:

- **The two usage codes differ.** `subscription_sharing_usage_limit_exceeded`
  (429) means pause plan requests and send the user to ChatGPT's usage
  settings, without inferring a reset time. `subscription_sharing_usage_unavailable`
  (503) means "preserve credentials and retry later with bounded backoff". The
  prompt grouped them as usage-limit errors; the build treats only the first
  as "plan usage exhausted" and the second as a transient failure.
- **Other codes.** `subscription_sharing_user_not_eligible` (403: do not repeat
  or loop through OAuth), `…_unsupported_capability` (400: inspect `param`,
  never retry the same body), `…_route_not_supported`, `…_invalid_user` (401),
  `chatpass_v2_*` (403), `…_user_unavailable` (503). Before a stream opens an
  error may be `{"detail": "…"}` (401/403/503 direct admission). All are mapped
  (table below).
- **Unsupported request fields:** `background`, `conversation`,
  `max_output_tokens`, `max_tool_calls`, `metadata`, `moderation`,
  `multi_agent`, `prompt`, `prompt_cache_retention`, `safety_identifier`,
  `temperature`, `top_logprobs`, `top_p`, `truncation`, `user`, plus
  `previous_response_id` over HTTP. Hosted tools are unsupported; function
  tools are allowed but this transport sends none.
- **Tokens:** access tokens last 1 hour; refresh tokens 30 days, each refresh
  returning a replacement. The token response also carries
  `earliest_refresh_at`. Refresh omits `scope`; refreshes for one session must
  be serialized.
- **Sign-out** revokes the refresh token at the discovery document's
  `revocation_endpoint` (empty HTTP 200 = success), then clears tokens but
  keeps the registration and host id.
- **Re-enabling plan usage after a decline** repeats OAuth with the full scope
  set and `prompt=consent` (`force_reconsent=true` only after OpenAI confirms
  deployment for the integration).
- **Host id:** `urn:uuid:<uuid4>` is a supported format (the JWK-thumbprint
  form is recommended but optional). A Plus plan's 5-hour usage limit is
  shared across every app using the plan; Pro has none.
- **ID token:** verify its signature against the issuer's JWKS
  (`https://auth.openai.com/.well-known/jwks.json` per the website guide) and
  check `iss`, `aud` (the issued client id), `exp` and the nonce.

## What was built

**Profile.** `type = "chatgpt_plan"`, with `model` (a slug from
`learnloop ai models chatgpt`), `reasoning_effort`, `response_format`
(`json_schema` default, or `json_object`), `enabled` (the per-profile kill
switch), `usage_limit_pause_minutes` (default 15) and `timeout_seconds`.
`base_url` defaults to `https://api.openai.com/v1` and may only be that host or
a loopback URL: the bearer token is a plan credential and is never sent
anywhere else.

**Sign-in** (`ai/chatgpt_plan/oauth.py`, `session.py`).
- Discovery from `https://auth.openai.com/.well-known/openid-configuration`,
  falling back to the documented paths. A fresh `state`, `nonce` and PKCE
  verifier per attempt. The listener binds `127.0.0.1:1455` (the docs'
  example), else any free port; only `/auth/callback` is answered and the
  query (which holds the code) is never logged.
- First registration sends `client_id=dynamic_agent_client`,
  `agent_name_hint=LearnLoop` and the persisted `ext_agent_host_id`. Later
  sign-ins send the saved `oaiapp_…` id and `login_hint` (the saved email),
  never `agent_name_hint`. `id_token_hint` is not sent, so no ID token ever
  sits in a URL.
- The callback is checked in this order: `state` (constant-time), an OAuth
  `error` (declined consent saves nothing), the code, the issued client id (a
  new registration without one is incomplete; a reauthorization callback that
  names another client is rejected). The code exchange uses the issued id, the
  verifier, the same redirect URI and `resource`. On `invalid_grant` the code
  is discarded; a brand-new registration keeps its issued id so the next
  attempt reuses it.
- The ID token: `iss`, `aud`, `exp` (60 s skew), `iat`, nonce, `sub`, and an
  RS256 signature checked against the JWKS (RSASSA-PKCS1-v1_5 by re-encoding,
  in the standard library: the project has no JWT or crypto dependency). A key
  that exists and fails is a refusal; `none` and HMAC algorithms are refused.
  If the JWKS cannot be fetched or has no usable RSA key, the OpenID Connect
  TLS rule applies (the token came straight from the token endpoint over TLS)
  and the account records `id_token_signature = "tls_endpoint"`, visible in
  `learnloop ai status`. A returning sign-in must be the same `sub`, or nothing
  is replaced.
- Plan usage is enabled only if the granted scopes (token response, else the
  callback, else the access token's claim) include
  `chatgpt.tokens.use.direct`. Without it the sign-in is kept and the profile
  reads `plan_usage_disabled`; `--consent` asks again.

**Store** (`ai/chatgpt_plan/store.py`). `<config dir>/chatgpt_plan/` (the
directory of `settings.env`; `LEARNLOOP_CONFIG_DIR` moves it, which is how
every test isolates it). `account.json` holds no token, so status, readiness,
doctor and the Settings payload never read a secret. Tokens go to the OS
keyring when the optional `keyring` package has a usable backend, else to
`tokens.json`. Files are written atomically, mode 0600, in a 0700 directory.
`LEARNLOOP_CHATGPT_SECRET_STORE=file|keyring` forces a backend; the test suite
sets `file`.

**Session.** `access_token()` refreshes 5 minutes before expiry under
`refresh.lock` (an `fcntl` lock across processes plus a thread lock), re-reading
the store first, so concurrent callers send one refresh (tested with four
threads). Access token, expiry, scopes and refresh token are replaced together.
`invalid_grant`, `invalid_refresh_token`, `token_expired`,
`refresh_token_expired`, `refresh_token_invalidated` and `refresh_token_reused`
clear the tokens, keep the registration and raise "sign in again";
`invalid_client` says to register anew (`--new-account`). A network failure or
5xx keeps the credentials and uses the old token while it is still valid.

**Transport** (`ai/providers/chatgpt_plan.py`, `ai/chatgpt_plan/responses.py`).
- One `POST {base_url}/responses`: `model`, `instructions` (the system turn),
  `input: [{role: user, content: prompt}]`, `store: false`, `stream: true`,
  `text.format` (strict `json_schema` from `strict_output_schema`, or
  `json_object` with the schema in the instructions), and `reasoning.effort`
  when the profile sets one. Nothing else; a test asserts no unsupported field
  is ever sent. The output budget rides in the prompt (as for Codex), because
  `max_output_tokens` is not allowed.
- Success only on `response.completed`; the text comes from its `output`
  message parts (deltas as a fallback). A refusal with no text is invalid
  output. `http.client` is used directly so a deadline timer or an interrupt
  shuts the socket down and wakes a blocked read.
- Capabilities: structured completion, bounded structured completion,
  isolated turn, tool-free, interrupt. Not a read-only workspace (no files).
  So blind grading and every other isolated-turn route can use it, and
  `isolation_mode()` reports `tool_free`.
- Under `single_request()`: exactly one request, no retry, no refresh-retry, no
  JSON repair. Otherwise: one JSON repair (as `openai_chat`), up to two retries
  of a transient failure with jittered backoff inside the deadline, and one
  refresh-and-retry after a 401.
- Receipts: every physical request is a child `model_call`
  (`purpose = "responses_request"`) under the operation's root receipt, with
  provider, profile model, endpoint, the answering model (`resolved_model`),
  response id, status, input/output/cached/reasoning tokens, and the request id
  in `usage_json`. Usage is metered before the body is inspected, also for
  `response.failed` and `response.incomplete`.

| Error | Result |
|---|---|
| `subscription_sharing_usage_limit_exceeded` (stream or 429) | `ChatGPTPlanUsageExhausted`; the plan is paused (machine-wide) for the profile's window; message links `https://chatgpt.com/settings/usage` |
| `subscription_sharing_user_not_eligible` | `ChatGPTPlanNotEligible`; the account is marked ineligible until the next sign-in |
| 401 / `subscription_sharing_invalid_user` | `ChatGPTPlanUnauthorized`; the next request refreshes first (in-call retry once unless `single_request`) |
| 400, 403 without code, `…_unsupported_capability`, `…_route_not_supported`, `chatpass_v2_*` | `ChatGPTPlanRequestRejected`, never retried; a rejected `text.format` names the `response_format = "json_object"` fix |
| `…_usage_unavailable`, `…_user_unavailable`, 408/409/429/5xx, network, a stream that ends early | `ChatGPTPlanTransient` (bounded backoff) |
| `response.incomplete` (`max_output_tokens`) | `AIOutputTruncated` |
| deadline / interrupt | `AITurnTimeout` / `AIInterrupted` |

**Plan usage exhausted, and fallback.** The pause is local state, so readiness
reports it with no network call (`provider_unavailable`, "ChatGPT plan usage
exhausted … paused until …; Manage usage: …"). While paused every request is
refused before it is sent, so a retrying caller never hammers the plan. A route
that allows fallback (an unpinned route with `ai.fallback_provider` set) falls
back on its next resolution, as for any provider that is not ready. Pinned
paid routes (`practice_index.paid.resolve_client`, PF, the offline reviews)
never fall back, by design, because their checkpoints key on the model; T6's
rewrite and verification therefore report "unavailable" and the tutor answers
without them. The pause ends by itself after `usage_limit_pause_minutes`, on
`learnloop ai resume chatgpt` / the desktop's "try again now", on a new
sign-in, or on the next completed response.

**Billing.** `chatgpt_plan` joins the subscription types in `ai/spend.py` and
in the four local copies (`practice_index/paid.py`,
`diagnosis/offline_review/runner.py` and `spend.py`, `projects/ai_runtime.py`).
So T6's live rewrite and verification need no `source_retrieval.llm_price_per_million`
on this route, and every paid command reports `billing = subscription`,
`cost_basis = estimated_only`, with the call, candidate, pair and retry caps
kept.

**Readiness and doctor.** `check_ai_runtime` reads the profile, the account
file and the pause state: `provider_missing_config` (no model),
`provider_unavailable` (`enabled = false`, paused, ineligible),
`provider_auth_required` (signed out, plan usage not granted), else `ready`. An
expired access token with a refresh token is ready. Plain `learnloop doctor`
warns (`ai:chatgpt_plan_*`) when a route, `active_provider` or
`fallback_provider` names a `chatgpt_plan` profile this machine cannot serve;
an unrouted profile is not checked. `doctor --ai --ai-provider <profile>`
shows the runtime report.

**CLI.**
- `learnloop ai signin chatgpt [--new-account] [--consent] [--no-browser] [--port N] [--timeout S] [--json]`
- `learnloop ai status chatgpt [--vault V] [--json]`: local files only; with
  `--vault`, each `chatgpt_plan` profile, its readiness and the routes using it.
- `learnloop ai models chatgpt [--vault V --profile P] [--json]`: one unbilled
  `GET /v1/models`; keeps `visibility == "list"` in the server's order.
- `learnloop ai resume chatgpt`, `learnloop ai signout chatgpt`.
- `learnloop ai latency --vault V --provider P [--provider Q] [--runs N] [--dry-run] [--json]`:
  a tiny structured call (no vault text) per run per provider, wall clock and
  time to first event; subscription profiles estimate cost, a metered one
  needs `--price-per-million` and stays inside `--max-cost-usd`; receipts land
  in the vault.

**Desktop.** Settings gains a "ChatGPT plan" section
(`components/ChatGPTPlanSettings.tsx`): status, a black **Continue with
ChatGPT** button (it opens OpenAI's page in the system browser and polls until
the attempt ends; a "cancel" while waiting), the one-time **You're using your
ChatGPT plan** / **Got it** confirmation, **Using ChatGPT plan** with a
**Manage usage** link while a route uses the plan, a **Usage limit reached**
card whose primary action is **Manage usage** (secondary: "try again now"),
each profile with its routes, and sign-out. The AI models selector shows
"· Using ChatGPT plan" beside a `chatgpt_plan` profile. Six sidecar RPCs
(`chatgpt_plan_status`, `…_signin_start`, `…_signin_cancel`, `…_signout`,
`…_acknowledge_welcome`, `…_resume`) need no vault and return no token; the
Tauri shell forwards them; `tests/test_mobile_allowlist.py` pins all six as
desktop-only. `get_settings` carries a `chatgpt_plan` block (local files only).

**Kill switch.** Unconfigured, nothing changes: no profile, no route, no
store read beyond a missing `account.json`. `enabled = false` on a profile, or
signing out, makes it not ready.

## Owner steps

1. **Sign in once** (opens your browser; approve plan usage):
   `uv run learnloop ai signin chatgpt`
   It prints "You're using your ChatGPT plan." the first time.
2. **Pick a model:** `uv run learnloop ai models chatgpt`
3. **Add a profile and point T6 at it.** In the vault's `learnloop.toml`, add
   the profile, and the two keys inside the existing `[ai.routing]` table (do
   not add a second `[ai.routing]` header):

   ```toml
   [ai.providers.chatgpt]
   type = "chatgpt_plan"
   model = "<slug from step 2>"
   reasoning_effort = "low"
   timeout_seconds = 60

   [ai.routing]
   source_query_rewrite = "chatgpt"
   source_rerank = "chatgpt"
   ```

   Then check: `uv run learnloop ai status chatgpt --vault <vault>` and
   `uv run learnloop doctor --vault <vault> --ai --ai-provider chatgpt`.
   T6's checkpoint keys include the provider and model, so answers bought on
   Codex are not reused for the new route (expected). A route that should
   fall back while the plan is paused also needs `ai.fallback_provider`.
4. **The first real call and the latency comparison** (two subscription
   profiles, about six short calls, no vault text; try it on a backup copy
   first if you prefer):
   `uv run learnloop ai latency --vault <vault> --provider chatgpt --provider codex_low --runs 3`
   If the first chatgpt call fails with `ChatGPTPlanRequestRejected` naming
   `text.format`, the plan route does not accept strict structured output: set
   `response_format = "json_object"` on the profile (JSON mode plus one repair).
5. **Desktop:** Settings → ChatGPT plan → **Continue with ChatGPT** does the
   same sign-in.

## Latency comparison

Measured with fakes only (`uv run python scripts/benchmark_chatgpt_plan_latency.py --calls 50`;
Python 3.12.14, Linux). Both fakes answer instantly, so these are each
transport's own overhead per structured call, not model time:

| Path | median | p95 |
|---|---|---|
| `chatgpt_plan` (real client; token read, one loopback HTTP request, SSE parse, validation) | 0.82 ms | 0.95 ms |
| `codex_sdk` with a stand-in app-server (real client; a child process per call plus the JSON-RPC handshake, thread start and turn) | 11.2 ms | 12.0 ms |
| `codex --version` (the installed binary's bare exec; reads no credentials) | 27.8 ms | 78.6 ms |

So with fakes the plan transport costs under a millisecond and the Codex path
at least an order of magnitude more before any model work. The real Codex
app-server also loads its configuration, auth and MCP servers and starts a
thread on every call (an isolated turn also runs `codex mcp list` first), and
the model's own time dominates both. Only a real call measures that, so the
comparison that matters is step 4 above. No real call was made by this stage
(agents make no live calls to `auth.openai.com` or `api.openai.com`); the
owner's first call fills this in.

## Deviations and decisions

1. **Structured output is unverified live.** The default is the strict
   `json_schema` text format; the owner's first call verifies it, and a
   rejection names the one-line switch to `json_object` (no hidden
   downgrade).
2. **The call that hits the usage limit fails; later ones fall back.** There is
   no in-call switch to another provider: the receipts, spend class and pinned
   checkpoint keys of the failed call stay honest, and a pinned paid route
   never changes model silently. Every resolution after the pause starts falls
   back where the route allows it.
3. **`subscription_sharing_usage_unavailable` is transient, not "exhausted"**
   (the docs: preserve credentials, bounded backoff). The prompt listed it
   beside the usage-limit code.
4. **No ChatGPT logo is shipped.** The guidelines' approved buttons carry
   OpenAI's logo; LearnLoop does not redraw a trademark. The button uses the
   approved label and the black format; drop in the official asset when you
   have it.
5. **ID-token signature in the standard library** (RS256 only), with the
   documented TLS fallback recorded when keys are unavailable. No new
   dependency. The keyring is optional (`pip install keyring`); without it the
   0600 file is used.
6. **One registration per machine.** `--new-account` registers a new client
   and replaces the saved one (its tokens are cleared). No account picker.
7. **`id_token_hint` is never sent**, only `login_hint`, so an ID token is never
   placed in a URL the browser or a terminal might keep.
8. **Windows:** the cross-process refresh lock uses `fcntl`; on Windows only
   the in-process lock applies (the app targets local POSIX hosts, as
   `vault_lock.py` does).
9. **`cargo check` could not run here.** This machine's `rustc` fails to start
   (`symbol lookup error: … librustc_driver … undefined symbol … LLVM_23.1`), a
   system toolchain problem. The Rust change is six `sidecar_passthrough!`
   lines and six `generate_handler!` entries, the same shape as their
   neighbours.

## Spend and calls

No real paid or live call was made: every test and the benchmark use the local
fakes; no command touched `auth.openai.com`, `api.openai.com` or the owner's
config directory. Manual checks used a backup-API copy
(`fixtures-local/la-chatgpt-check`, from the worktree's `fixtures/linear_algebra`)
with a temporary `LEARNLOOP_CONFIG_DIR`: `config effective`, `ai status
--vault` and `doctor` (it reported `ai:chatgpt_plan_signed_out` for the two T6
routes, as intended). Cost: $0.

## Tests

New: `tests/test_chatgpt_plan_signin.py` (19), `tests/test_chatgpt_plan_provider.py`
(20), `tests/test_chatgpt_plan_cli.py` (8), `tests/test_chatgpt_plan_sidecar.py` (5),
`apps/learnloop-tauri/src/components/ChatGPTPlanSettings.test.tsx` (5); six new
desktop-only pins in `tests/test_mobile_allowlist.py`. Fakes:
`tests/chatgpt_plan_fakes.py` (one 127.0.0.1 server for discovery, JWKS,
authorize, token, revoke, `/v1/responses` SSE and `/v1/models`, enforcing the
documented contract; a deterministic 2048-bit test RSA key).

They cover: the authorize parameters for first and returning sign-ins; state,
nonce, client-id, account and signature refusals; declined consent; a grant
without plan usage; timeout and cancel; 0600/0700 files and no token in
`account.json` or any status; refresh rotation without `scope`; four
concurrent refreshers sending one refresh; `invalid_grant`; transient refresh
failure; revocation on sign-out; the keyring backend (a fake module); the
request shape and no unsupported field; the output budget in the prompt;
receipts; capabilities and isolation; JSON-object repair; `single_request`
bounds; transient retries; usage limits mid-stream and before the stream, the
local refusal while paused, fallback for an unpinned route and none for a
pinned one, resume; not-eligible; 401 refresh-and-retry; a rejected
`text.format`; incomplete, truncated and stalled streams; signed-out refusal;
the model list; base-URL validation; readiness without network; billing class;
T6's rewrite end to end with receipts in the vault; the CLI commands; the
doctor check; the desktop RPCs and Settings payload; the React section.

## Gate

(filled in below after the runs)

## Files touched

- Added: `src/learnloop/ai/chatgpt_plan/{__init__,store,oauth,session,responses,routes}.py`,
  `src/learnloop/ai/providers/chatgpt_plan.py`, `src/learnloop/cli/ai.py`,
  `src/learnloop_sidecar/handlers/chatgpt_plan.py`,
  `apps/learnloop-tauri/src/components/ChatGPTPlanSettings.tsx` and its test,
  `scripts/benchmark_chatgpt_plan_latency.py`, `tests/chatgpt_plan_fakes.py`,
  four `tests/test_chatgpt_plan_*.py`, this file.
- Changed: `config/schema.py`, `config/template.py`, `ai/client.py`,
  `ai/runtime.py`, `ai/spend.py`, `ai/disclosures.py`, `ops/doctor.py`,
  `practice_index/paid.py`, `diagnosis/offline_review/{runner,spend}.py`,
  `projects/ai_runtime.py`, `cli/__init__.py`, sidecar `handlers/__init__.py`
  and `handlers/settings.py`, `apps/learnloop-tauri/src/{api/client.ts,api/dto.ts,screens/SettingsScreen.tsx}`,
  `src-tauri/src/{commands.rs,main.rs}`, `tests/conftest.py`,
  `tests/test_mobile_allowlist.py`.
- Migrations: none. Schema: unchanged (no DB reference regeneration needed).

## Open questions

1. **Live structured output.** Does the plan route accept the strict
   `json_schema` text format for the model you pick? Your first call answers
   it; if not, `response_format = "json_object"`.
2. **Which model for T6?** `learnloop ai models chatgpt` lists what your
   account offers; a fast, low-effort model fits the rewrite and the
   verification rerank.
3. **Fallback for T6 while paused.** T6's routes are pinned (no silent model
   change), so a paused plan skips the rewrite and verification. Do you want a
   T6-specific fallback route instead, accepting that checkpoints differ by
   model?
4. **Pause length.** 15 minutes after a usage-limit error (one free rejected
   request per window while the limit lasts). Longer, shorter, or a schedule
   aligned to Plus's 5-hour window?
5. **Logo asset.** Should the button carry OpenAI's official ChatGPT logo
   (from their brand assets) once you have it?
6. **Other routes.** Beyond T6, which routes should move to the plan (for
   example the diagnoser or the same-cause judge), now that it serves isolated
   turns?
