# Chat frontend C1a: the MCP adapter, its read side and the shared learner model

**Stage:** `mcp-c1a`, branch `mcp/c1-read-context`, base `9c5c62df9` (main, mvp-0.22).
**Spec:** [spec_mcp_frontend_c1.md](../specs/spec_mcp_frontend_c1.md) (C1, owner decision D15's short spec).
**Codex review:** [mcp-c1a-codex-review.md](mcp-c1a-codex-review.md): ten findings (four High), all reproduced
and fixed in `e0fdfef36`; the re-review confirmed F1-F3, reopened F4 and raised F11 and F12, all reproduced and
fixed in `8c42bfecf`; F4 round 3 (the verify of `4493140a2` reopened F4 for misconception, candidate and gap
text) was reproduced and fixed by one guarded renderer in `3e1725836`; the review of that fix
([mcp-c1a-f4-codex-review.md](mcp-c1a-f4-codex-review.md)) raised F1-F3 (diagnosis context lost through derived
beliefs, generated topic names and ids, malformed provenance lists), all reproduced and fixed. The F4 round 4
gate there supersedes the ones below.
**Owner direction (2026-10-13):** start C1; Tailscale Funnel is fine and already works with Claude chat and
ChatGPT chat (D1); latent learner state (misconceptions, answer traces) must be shared seamlessly between the
local LearnLoop and the chat frontend through the existing telemetry.

## What was built

| Piece | Where |
|---|---|
| The MCP adapter (entry point): six tools, structured outputs, honest annotations, the telemetry wrapper, the host label | `src/learnloop_mcp/` (`server.py`, `hosts.py`) |
| Transports: stdio; stateless JSON streamable HTTP on 127.0.0.1:8769 behind the endpoint gate (secret path, exact Host/Origin allowlists, 64 KiB bodies, no access log) | `src/learnloop_mcp/http_app.py`, `cli.py`, `__main__.py` |
| Secondary attach (the mobile host's attach plus PR-1's read side), content freshness | `src/learnloop/remote/runtime.py` |
| Read-only views: status, today, progress, library | `src/learnloop/remote/views.py` |
| Grounded passages (find_sources under a server-derived caller, extra withholding, full blocks, citations) | `src/learnloop/remote/sources.py` |
| Telemetry in `interaction_events` and exposure in `source_exposure_events`; the activity report | `src/learnloop/remote/telemetry.py` |
| The secret endpoint token (machine-local) | `src/learnloop/remote/endpoint_token.py` |
| **The shared latent-state read model** (misconceptions and candidates, open hypotheses with evidence for/against and repairs tried, recurrence groups, answer traces, open learner-text gaps, retention risks) with the G5 leakage rules | `src/learnloop/learner_context.py` |
| `learnloop mcp serve | token show | token rotate | activity` | `src/learnloop/cli/mcp.py`, `learnloop.app_launch.serve_mcp` |
| Migration **210 (placeholder)**: `interaction_events.kind` += `chat_tool_call`, `origin` += `chat_host` | `migrations/210_chat_mcp_interaction_events.sql`, `fixtures/migration_head_210/` |
| R2a's `open_learner_state_hypotheses`, applied byte-identically from `router/r2a` (so the merge is clean either way) | `src/learnloop/db/stores/daily_plans.py` |
| Import-linter: 4 new contracts, 4 extended | `pyproject.toml` |
| Tests (34) | `tests/test_mcp_tools.py`, `test_mcp_http.py`, `test_mcp_runtime.py`, `test_mcp_cli.py`, `tests/mcp_world.py` |

No model is called by any of this. The only model calls reachable are an existing service's own:
`find_sources`' query rewrite, query embedding and listwise verification, through their routes, the shared
service spend cap and their receipts. No paid call was made in this stage.

## Decisions and defaults taken

- **D1 (owner, 2026-10-13): Funnel approved and working.** The server binds loopback only; the owner points
  Funnel at it (runbook below). Agents ran no `tailscale` command; the probe service on 8768 and
  `scripts/mcp_probe/state` were not touched.
- **SDK packaging:** `mcp==2.3.0` as the optional extra `mcp`; it resolves cleanly with the app's pins
  (starlette 1.7.0, uvicorn 0.54.0, python-multipart 0.0.32 unchanged). It installs 16 more packages (cryptography and pyjwt among them) and bumps `idna`
  3.17 → 3.20 in the shared lock (`httpx2` needs it). It is also in the `dev` extra, so `uv sync --extra dev
  --extra mobile` installs it and the MCP tests never skip silently (unlike the mobile extra).
- **Telemetry kind:** a new `interaction_events` kind needs the CHECK widened, so one migration was
  unavoidable; it is numbered **210 as a placeholder** (renumber at merge; the head fixture was upgraded from
  `migration_head_201` with only 210 applied and renamed, every hard-coded reference updated, the DB
  references regenerated and validated). `origin` gains `chat_host`: a host model acting in the learner's
  chat is neither the learner's own typed action nor LearnLoop's system nor owner tooling.
- **Exposure context:** chat passages use the existing `library` context with `entity_type =
  'chat_tool_call'` (no second CHECK widening); every exposure reader matches on spans, whatever the context.
- **Annotations:** five views read-only (they append only their audit row); `find_sources` not read-only
  (its exposure rows change which items still count as unexposed checks). Open question Q1.
- **Answer excerpts:** the chat applies one rule the R2a card does not: a learner answer that reproduces the
  item's answer key is withheld (a correct answer is the key). Open question Q2.
- **Citations** carry the learner's title for a source, never a local `file://` path (found in the manual
  run: `find_sources`' own hit title is the original URI when no display title exists).
- **R2a convergence:** R2a has not landed on main (`router/r2a`, 13 commits). The read model's
  `open_hypotheses` and `recent_answer_traces` keys are a superset of the card's `open_hypotheses` and
  `recent_work` keys (pinned by `test_read_model_fields_match_the_router_card_for_convergence`).

## Security model

The M0 probe's, which both hosts accepted through Funnel on 443: loopback bind only (`--host` other than
127.0.0.1 is refused); the persistent secret path `/<token>/mcp` (constant-time compare; `/mcp` and every
other path is a 404; `token rotate` takes effect without a restart); exact Host allowlist (421) and exact
Origin allowlist (`https://chatgpt.com`, `https://claude.ai`, `https://<public host>`, `--public-origin`;
403), absent Origin allowed; 64 KiB request bodies (413); stateless JSON responses; 32 connections; no proxy
headers; no access log, `--log-level trace` refused (uvicorn's trace logs paths); the token is stored 0600 in
a 0700 `.learnloop/mcp/` with a `.gitignore` of `*`, printed only by `token show|rotate`.

**Risk R1, OAuth deferred: the URL is the credential.** Anyone holding it can read the learner's state
through the six tools and write telemetry and exposure rows. Follow-up (review §5.4): single-user OAuth with
CIMD, short-lived audience-bound tokens and a consent page reachable only over the tailnet, before chat
practice (C2) and preferably before C1b's writes.

## Owner runbook: switch the connector from the probe to LearnLoop

Run by the owner (agents never run `tailscale`). `<host>` is the machine's `*.ts.net` name; `<vault>` the
vault the desktop uses. Until this branch is on main and the desktop has opened the vault once (migration
210), try it on a backup copy: `learnloop mcp serve` refuses a vault whose schema differs (exit 78).

```bash
uv sync --extra dev --extra mobile            # dev carries the mcp extra
.venv/bin/learnloop mcp token show --vault <vault> --public-host <host>.ts.net
.venv/bin/learnloop mcp serve --vault <vault> --public-host <host>.ts.net --public-host <host>.ts.net:443
# point Funnel's 443 at it (replaces the probe's route to 8768):
tailscale funnel --bg --https=443 http://127.0.0.1:8769
tailscale funnel status
# when satisfied, stop the probe:
systemctl --user stop learnloop-mcp-probe.service
```

Then, in claude.ai (Settings › Connectors) and ChatGPT (the custom MCP server), replace the probe URL with
`https://<host>.ts.net/<token>/mcp` from `token show`, and refresh each host's tool list (the probe report
saw a stale list in Claude until it was refreshed). Rollback: `tailscale funnel --bg --https=443
http://127.0.0.1:8768` (back to the probe) or `tailscale funnel --https=443 off`. The review's alternative is
a dedicated Funnel port (`--https=8443` or `10000`) for this endpoint only, keeping 443 as it was (Q3).

A user unit, if wanted (`~/.config/systemd/user/learnloop-mcp.service`):

```ini
[Service]
WorkingDirectory=%h/Documents/thinking/learnanything
ExecStart=%h/Documents/thinking/learnanything/.venv/bin/learnloop mcp serve --vault <vault> --public-host <host>.ts.net --public-host <host>.ts.net:443
Restart=on-failure
RestartPreventExitStatus=78
```

The server loads provider keys the way the app does (`~/.config/learnloop/settings.env`), so
`find_sources`' rewrite and verification run on their configured routes. The machine must be awake; when it
is not, the hosts show a connection error and the tool instructions tell the model to say LearnLoop at home
is offline. D16: check "Improve the model for everyone" in the ChatGPT account used with LearnLoop.

`learnloop mcp activity --vault <vault>` shows what the chat side did (calls by tool and host, passages
shown).

## Manual runs (backup-API copies, no model, no network)

`fixtures/linear_algebra` and `fixtures/probability` (the worktree's committed copies) were copied with
`learnloop.db.copies.copy_tree_with_databases` to `fixtures-local/c1a-manual/`, migrated there, attached as a
secondary process and every tool called in-process, with every model client refused (the services' paid
routes got no client). Results (ms per call):

| Vault | status | today | progress | library | learning_context (topic) | learning_context (all) | find_sources |
|---|---|---|---|---|---|---|---|
| linear_algebra (mvp-0.8, plan off) | 164 | 294 | 421 | 301 (3 sources) | 327 (1 hypothesis, 5 traces) | 283 (2 hypotheses, 12 traces, 7 risks) | 981 (4 passages, 2 held for a check) |
| probability (mvp-0.8, plan off) | 106 | 293 | 329 | 461 (4 sources) | 271 (2 traces) | 167 | 1100 (6 passages) |

Observed on real data: a correct "complete this sentence" answer was withheld as stating the key; a
hypothesis on a diagnostic probe's answer kept no statement; a citation's title was a local `file://` path
(fixed: learner titles). Paid routes asked for: `source_query_rewrite` (given no client). **Paid calls: 0;
cost: $0.**

## What C1b and C2 still need from the mobile prerequisites (PR-1..PR-7)

| Prerequisite | C1a | C1b | C2 |
|---|---|---|---|
| PR-1 secondary attach | Read side built (`RemoteRuntime`); `SidecarContext.load_secondary` not built | Not needed (domain services, not handlers) | Needed |
| PR-2 state sync never restores stale scheduling state | Not needed | Not needed | Needed |
| PR-3 synthesis sweep primary-only | Not needed | Not needed | If the host binds a runner |
| PR-4 atomic sessions and handoff | Not needed | Not needed | Needed |
| PR-5 request origin on the context | Origin on telemetry only | Needed (capture and gap provenance) | Needed (`entry_surface`) |
| PR-6 eligibility module | Not needed | Not needed | Needed (class `chat`) |
| PR-7 desktop freshness (`queue_revision`) | Not needed | Needed | Needed |

**C2 integrity successor (not built):** the attempt column `assistance_observability = host_unobserved`
with coldness `unassisted = unknown`; the chat eligibility class before the offer receipt (no exam, held-out,
certification cold probe, repair cold retry, probe, calibration or golden-path item in chat); reveal kinds
`solution_request` and `host_reported`; `host_chat_conversation` among the unobserved channels; one successor
under the playbook with a kill switch (spec §7).

## Convergence tasks

1. **R2a card:** when `router/r2a` lands, its `CardGatherer` reads its sections from
   `learnloop.learner_context` (one predicate set, one leakage rule set): `withheld_items` is a superset of
   the card's `_withheld_items` (adds cold checks, repair cold retries and probes); `_pinned_stems` is the
   card's logic. `open_learner_state_hypotheses` is already shared (identical hunk).
2. **Library composition:** `remote.views.library` composes the same public functions as the sidecar's
   `get_source_library` (learner title, kind noun, status line, readiness); extract one shared function and
   switch both adapters in one change (the spec's rule) when the UX phases stop editing that handler.
3. **Mobile attach:** `learnloop_mobile.host.attach` can call `learnloop.remote.runtime.check_schema`.

## Gate

Run on the branch head (commit `d5e82e929` and its parents), TMPDIR in the worktree's `fixtures-local/tmp`:

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` (dev carries `mcp==2.3.0`) and `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **21 kept, 0 broken** (4 new contracts) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | first run 10,672 passed, 1 failed (`test_route_rules_in_grader.py::test_migration_186_keeps_its_trigger_which_nothing_writes_now` hard-codes head 201; fixed to the placeholder 210); rerun **10,673 passed**, 0 failed (12 min 47 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10,573 deselected (includes the two-process stdio test) |
| The C1a tests alone | 34 passed (tools 22, HTTP 5, runtime 4, CLI 3) |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated; validate `errors: []` (schema head 210) |
| CLI help snapshot | regenerated (`learnloop mcp` and its 5 subcommands, the root) |
| npm / cargo | not applicable: nothing under `apps/learnloop-tauri` changed |
| Paid calls | none ($0) |

## Open questions for the owner

- **Q1:** `find_sources` is annotated not read-only because it records exposure, so ChatGPT may ask before
  running it (once per conversation). Mark it read-only for less friction, treating the exposure row like an
  audit row?
- **Q2:** keep the chat-only rule that withholds a learner's own answer when it restates the answer key?
- **Q3:** Funnel 443 retargeted from the probe to 8769 (as in the runbook), or a dedicated Funnel port for
  LearnLoop with 443 restored?
- **Q4:** OAuth before C1b's writes (capture, confirms, chat questions), or before C2 only?
- **Q5:** migration 210 is a placeholder: renumber at merge alongside the other in-flight stages.
