# ChatGPT-plan provider ("Continue with ChatGPT")

Stage: `providers/chatgpt-plan` (worktree `learnanything-chatgpt-plan`, base `b2a2bd2e`).
Prompt: `docs/specs/implementation_handoffs.md` §4, "ChatGPT-plan provider".

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
