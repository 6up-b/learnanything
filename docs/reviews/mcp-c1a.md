# Chat frontend C1a: the MCP adapter, its read side and the shared learner model

**Stage:** `mcp-c1a`, branch `mcp/c1-read-context`, base `9c5c62df9` (main, mvp-0.22).
**Spec:** [spec_mcp_frontend_c1.md](../specs/spec_mcp_frontend_c1.md) (C1, owner decision D15's short spec).
**Codex review:** [mcp-c1a-codex-review.md](mcp-c1a-codex-review.md): ten findings (four High), all reproduced
and fixed in `e0fdfef36`; the re-review confirmed F1-F3, reopened F4 and raised F11 and F12, all reproduced and
fixed in `8c42bfecf`; F4 round 3 (the verify of `4493140a2` reopened F4 for misconception, candidate and gap
text) was reproduced and fixed by one guarded renderer in `3e1725836`; the review of that fix
([mcp-c1a-f4-codex-review.md](mcp-c1a-f4-codex-review.md)) raised F1-F3 (diagnosis context lost through derived
beliefs, generated topic names and ids, malformed provenance lists), all reproduced and fixed; its re-review
confirmed F3 and reopened F1 (a history answer's grading) and F2 (a shown belief's generated topic id), both
reproduced and fixed in round 5. **Narrowed (owner decision 2026-10-14, "land narrow, then fix source"):**
the last verify reopened F1 and F2 a fifth time (diagnoses read the whole-vault snapshot without recording
what they opened), so `learning_context`, `today` and `progress` now show only authored vault text, the
learner's own pinned answers and structure; everything a model wrote is held back until a write-time record
says what it was written from ([mcp-c1a-narrow.md](mcp-c1a-narrow.md): what chat shows now, the follow-up
stage, the gate that supersedes the ones below and in the F4 record).
**Landed on main (2026-10-15)** with migration **203** (the placeholder 210 renumbered) and one model-context
protection shared with router R2a's card (Q16): see "Landing onto main" at the end. The sections above it describe
the branch as built and keep its placeholder wording.
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
| **The shared latent-state read model** (misconceptions and candidates, open hypotheses with evidence for/against and repairs tried, recurrence groups, answer traces, open learner-text gaps, retention risks) with the G5 leakage rules; since the narrow stage one structural text rule (`TextGuard`) | `src/learnloop/learner_context.py` |
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

## Landing onto main

**Branch:** `merge/mcp-c1a-onto-main` (worktree `learnanything-merge2`), from main `b9fcaf121`. Main had, since this
branch's base `9c5c62df9`:
- router R2a (`mvp-0.23`: `LearnerStateCardV1`, `plan_presentations`, migration 202), R2b + R2c (`mvp-0.24`) and
  method-explicit items (`mvp-0.25`, LATEST);
- RW3a, the tutor delivery fixes, GLM-OCR and its quality pass, plan determinism;
- the storage and adaptive-difficulty specs (docs only);
- migrations to 202 (head fixture `fixtures/migration_head_202`) and seventeen defaults snapshots (mvp-0.9 .. mvp-0.25).

The merge is a real `--no-ff` merge of `mcp/c1-read-context` (`c84c30e9d`, unchanged). Not pushed. Single phase. The
sections above, [mcp-c1a-narrow.md](mcp-c1a-narrow.md) and the three Codex review records describe the branch as
built and keep its placeholder wording (210).

**No algorithm version.** The adapter writes only telemetry and exposure rows. The convergence changes what the
router's card withholds, a model-context protection that replay never reads. R2a's exam-protection composition and
method-explicit's card stems were landed the same way.
**Paid calls:** none ($0.00); no network, no key read. **`apps/`:** unchanged, so no frontend or `cargo` gate.

| Commit | What |
|---|---|
| `024b1d9ea` | the merge: the renumber and head fixture, the convergence (`learnloop.learner_protection`), the compositions, the landing tests, the CLI help snapshot, the regenerated references, the Pipeline Map |
| (this commit) | this section, and the references' source stamps on the merge commit (stamps only, 374 notes) |

### Renumbered: 210 → 203 (Q5, done)

- `migrations/210_chat_mcp_interaction_events.sql` is `203_chat_mcp_interaction_events.sql`. Its header names both
  numbers ("built on mcp/c1-read-context as 210 ... renumbered 203 at its landing after main's 202"); the temporary
  table is `interaction_events__203`.
- Main's 202 does not touch `interaction_events`. So the rebuilt CHECKs (all of main's kinds plus `chat_tool_call`;
  `origin` plus `chat_host`) are a superset.
- No new table: `interaction_events` is already RAW_LEDGER in `table_roles.py`, so it needs no replayer.
- **Head fixture:** main's `fixtures/migration_head_202` was renamed `migration_head_203` (the branch's
  `migration_head_210` was dropped). Its `state.sqlite` was rebuilt as follows:
  - a backup-API copy of main's 202 database (`learnloop.db.copies.backup_database`);
  - only 203 applied by `apply_migrations`; then `wal_checkpoint(TRUNCATE)` → `(0, 0, 0)` and
    `journal_mode=DELETE`;
  - `integrity_check` ok, `foreign_key_check` empty;
  - then copied back into place with the backup API.
  The README gains the 203 paragraph and the build chain.
- **Hard-coded head paths:** 24 test files (main added `test_mvp023/024_upgrade`, `test_plan_determinism` and
  `test_method_explicit_upgrade` since the base). Also the two `_scripts/db_*_reference.py` (both
  `SCHEMA_PATH`, `SCHEMA_HEAD = 203` and the generator's two other mentions), the max-migration assertion
  (`test_route_rules_in_grader.py`: 203) and `docs/decider-tier1-migration.md`.
- The branch's own tests pinned no 210 beyond those. `remote/telemetry.py` and the C1 spec's telemetry row now say
  203.
- `docs/specs/spec_storage_sync_v1.md` is left as written. It cites main at `bffe086ec`, so its `migration_head_202`
  is today's `migration_head_203`: the same content plus 203's CHECK widening, and S0/S3's sanitization scope is
  unchanged.

### Converged: one protection, two text rules (Q16, as built)

New module **`src/learnloop/learner_protection.py`**, the one authority for what of the learner's past work a model
context may show. Router R2a's `LearnerStateCardV1` (`daily_plan/router_card.py`), R2c's teach-back summaries
(`daily_plan/router_teach_back.py`) and the chat's read model (`learner_context.py`) all read it. Each reader keeps its
own **text rule** as a parameter of `past_work_text` / `statement_text` (`TextRule`):
- **The card: `router_card.CardText`, G5.** Its reader is the router model, so it shows the learner's own answers
  (pinned or not) and the statements LearnLoop's diagnosers wrote.
- **The chat: `learner_context.TextGuard`, unchanged.** It shows authored text, pinned answers that state no key,
  and (c) text only with a write-time record.

| Predicate | Card before (main) | Chat before (branch) | Now, shared (`learner_protection`) |
|---|---|---|---|
| Withheld items | exam material by the one exam predicate, unreleased exam pools and reserved surfaces; failure → none shown | the same, plus held-out items, open cold checks and repair cold retries, probes, items the vault cannot read, untrusted protection metadata (`protection_issues`) | `withheld_items` → `Withheld` (the chat's set, with reasons); the card's `_withheld_items` delegates to it |
| An attempt's own protection | `exam_attempt` or a withheld item | `TextGuard.attempt_reason` (+ `exam_evidence`, a probe attempt or presentation, unknown item) | `attempt_protection`, through `PastWork.attempt_reason` |
| Held grades | `held_for_review_attempts`, `_result` | the same, its own `_result` | `attempt_result`, `PastWork.held` → THE predicate (`held_grades`) |
| Pinned revisions | `_pinned_stems` (`$.prompt` + `$.required_method`, `fit_presented_prompt`) | `_pins` (`$.prompt` only) | `pinned_contracts` → `PinnedContract.question`. Chunked, own-item, exactly one live contract; the frozen statement, then the frozen method's sentence, kept whole within the limit |
| Statements written from protected work | a diagnosed cause on exam or reserved work (its head's attempt only); gap words never checked | `TextGuard._protected` over every answer of the episode, and over a gap's answer and item | `PastWork.evidence_reason` via `statement_text`, with `hypothesis_answers` (every version's answer in the episode) |
| R2c teach-back summaries | `CardGatherer._withheld_items` (frozenset or None) | — | `withheld_items` + `attempt_protection` when summarizing; `summaries_for` takes a `Withheld` |

**The method-explicit merge note is applied.** The chat's question as graded is `PinnedContract.question`, the card's
rendering: the contract's frozen pair, which is `answered_question`'s contract branch, never the item's current
prompt. For an item without a required method, the chat's stems are byte-identical to the branch's.

**What the card now does differently** (a stricter model context; its text rule is unchanged):
- **Newly withheld past work.** It withholds questions and answers on items held by an open cold check or repair
  cold retry, on probes and probe attempts, on `exam_evidence` work and on items the vault can no longer read.
- **Newly withheld statements.** It withholds a cause's statement when any answer of its episode is protected (not
  only its head's). It withholds a learner-named gap's words when they rest on a protected answer or item; gap
  entries gain a `withheld` key.
- **Reasons and notes.** `withheld` names the shared reason: "exam or held-out material" (was "exam or reserved
  material"), "reserved for an assessment", "a check waiting in the app", "a diagnostic check", "the protection rules
  could not be read". A protection failure's unknown is the shared "which material is protected could not be read: no
  question or answer is shown". Unreadable pins give the shared `PINS_UNREADABLE`.

**Unchanged on both readers.** Nothing in the chat's output changed: the 129 branch tests pass unmodified. The card
is otherwise unchanged too: answers whole, the builder's clips, the stored-card format.

- **Tests updated (wording and API only):** `test_router_card.py` (2: the exam reason, the failure unknown),
  `test_router_r2a_landing.py` (3: `Withheld.item_ids`, the reason, its text) and `test_router_r2c_teach_back.py` (1:
  it patches `learner_protection.withheld_items`).
- **New: `tests/test_mcp_c1a_landing.py` (6):**
  - the card and the chat withhold the same past work for the same reasons (exam work, a cold-retry item, a deleted
    item);
  - both render the pinned question with its frozen method;
  - a statement written from protected work is withheld by both (an episode revised from an exam answer, a gap on an
    exam answer);
  - the text rule is each reader's own (the card shows a cause and an unpinned answer; the chat holds both back);
  - a teach-back on a cold-check item is never summarized;
  - no reader keeps a protection of its own: an AST check of names and SQL outside docstrings, and the chat's
    re-exports are the shared objects.
- **Fail first:** the six were run against the pre-convergence code. In an isolated overlay of `src/` (main's
  `router_card.py` and `router_teach_back.py`, the branch's `learner_context.py`, with `-o pythonpath=` and its own
  `migrations/`), **5 of 6 failed** on their divergence or leak assertions. The text-rule test passed: it pins what
  the convergence keeps.
- **Import-linter:** a 22nd contract, `learner-protection-sits-below-its-readers`. `learnloop.learner_protection`
  imports neither reader (`learner_context`, `daily_plan`, `router`, `remote`) nor any adapter.

### Compositions

| File | Resolution |
|---|---|
| `pyproject.toml` | main's `glm-ocr` extra beside the branch's `mcp` extra (`mcp==2.3.0`, also in `dev`); the branch's packages, root packages and four contracts |
| `uv.lock` | both extras and `provides-extras = ["mobile", "dev", "pdf", "glm-ocr", "mcp"]`; `uv lock --check --offline` passes (178 packages); `uv sync --offline` installed the SDK from the cache |
| `source_retrieval/find_sources.py` | The branch's public verification helpers (the MCP dry run's) are kept, composed with main's tutor delivery fixes. `verification_candidates(vault, pool)` judges main's complete passage (`judged_passage`). `widest_candidates(vault)` fills each passage to the vault's limit (`verify.passage_limit`; 900 with `complete_passages` off). `verification_context` uses main's `practice_question` (review F5: the statement shortened, never the method's sentence). Main's prompt-sized caps on `_verify` are kept; the branch's `PASSAGE_CHARS = 900` is dropped |
| `remote/sources.py` (auto-merged, composed) | the dry run's caps are sized like the live call's: `verify_caps(..., input_tokens=estimated_call_tokens(widest prompt))` (main's delivery-fix rule), so its worst case matches the live bound |
| 20 test files, the two `db_*_reference.py` scripts | main's side, then 202 → 203 (above) |
| 24 head-fixture files (rename/rename) | main's `migration_head_202` kept, the branch's `migration_head_210` dropped; then renamed and rebuilt (above) |
| 370 notes under `Reference/`, `tests/cli_help_snapshot.json` | main's side, then regenerated |

### Generated files

- **Defaults snapshots:** no config change, so all seventeen `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries were recomputed
  (template `.pyc` deleted, file touched) and all match. Unchanged.
- **CLI help snapshot** (`--write`): gains `mcp`, `mcp serve`, `mcp token`, `mcp token show`, `mcp token rotate` and
  `mcp activity`; the root's help changes; nothing else.
- **References:** `db_generate_reference.py`, then `db_validate_reference.py`: `errors: []`, schema head 203, 321
  table notes. The prose counts needed no change: no table and no config leaf was added.
- **Mobile allowlist pins:** none. MCP is not a sidecar RPC; `src/learnloop_sidecar`, `src/learnloop_mobile` and
  `apps/` are unchanged by the merge, and `tests/test_mobile_allowlist.py` passes unchanged.
- **Pipeline Map:** the chat frontend is no longer "planned". A new bullet covers its six read tools, transports and
  gate, what it shows and what it holds back, its telemetry, and the shared protection. The card's paragraph and the
  "Protection rules" box name the shared protection. `validate_vault.py` passed (1,106 notes, 22,144 links).

### Gate

At `024b1d9ea` (the merge), with `TMPDIR=<worktree>/fixtures-local/tmp`. Logs:
`fixtures-local/c1a-landing-fullsuite.log` and `c1a-landing-durability.log`, each headed by the commit.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok (`--offline` after the merge: the SDK and 15 dependencies from the cache; pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **22 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **11,658 passed**, 0 failed, 16 warnings (19 min 28 s). The reading-sweep timing flake (`test_d_work_the_cli_finishes_leaves_the_request_due_for_the_sweep`) did not appear; nothing needed a rerun |
| `flock ... uv run pytest -m durability -n auto` | **101 passed** (34 s). It includes the two-process stdio test, `test_mcp_runtime.py::test_a_second_process_serves_the_vault_beside_the_desktop_sidecar` |
| The C1a tests alone (seven files) | 135 (the branch's 129 and the 6 landing tests), all in the full run |
| Before the commit | the router, MCP, method-explicit, exam-protection, plan-determinism, teach-back, migration, table-role, rebuild, shadow, CLI-help, mobile-allowlist, fixture, copy, config and source-retrieval files: 926 passed |
| npm / cargo | not applicable: nothing under `apps/` changed |

### Parity

**Setup.** Backup-API copies (`copy_tree_with_databases`) of this worktree's tracked `fixtures/linear_algebra` and
`fixtures/probability` (both `mvp-0.8`), in `fixtures-local/c1a-parity`.
- Each was migrated by its own code (`migration_coordinator.migrate_vault`). On main's side, `b9fcaf121` was exported
  with `git archive` and put first on `PYTHONPATH` (the probe printed the archive's `learnloop/__init__.py`): 47
  migrations to 202. The merge's side: 48 to 203.
- On each copy, `learnloop rebuild --shadow --json` and `learnloop doctor --json`, with `LEARNLOOP_CONFIG_DIR` an
  empty directory.
- Shadows were compared structurally after setting aside ULIDs, timestamps, ids, hashes and paths. Doctor reports
  were compared both positionally and as issue multisets.

| Check | Fixture | Shadow (facet / mastery / schedule) | Shadow differences | Doctor main → merge |
|---|---|---|---:|---|
| own version (`mvp-0.8`) | linear algebra | 22 / 6 / 47 both sides | **0** | 107 → 107 issues (1 error both); multiset identical |
| | probability | 2 / 1 / 1 both sides | **0** | 138 → 138 (49 errors, 46 `criterion:unknown_dependency`, both); identical |
| **`mvp-0.25`** (`upgrade --to mvp-0.9`, then `--to mvp-0.25`, each side by its own code; `rebuild-derived-state` twice) | linear algebra | 0 / 0 / 0 both sides | **0** | 57 → 57 (1 error); identical |
| | probability | 0 / 0 / 0 both sides | **0** | 102 → 102 (49 errors); identical |

`live_database.unchanged` is true on every shadow. Each copy's `state.sqlite` hash is identical before and after its
shadow and doctor. Doctor exits 1 on both sides, as on main. The tracked fixtures were only copied: their hashes
(`a3972c00…`, `0ac51001…`) are the same before and after, and `git status fixtures/` is clean; `arxiv_v2` was not
opened.

### Manual MCP run (the merged copies, in-process, no network)

**Setup.**
- A backup-API copy of each merged own-version copy (at 203) was attached with
  `RemoteRuntime.attach(load_environment=False)`, every `*_API_KEY` blanked and every model client refused (a
  service's paid route recorded and given no client).
- Every tool was called through the official SDK `Client` in-process. Nothing was bound to any port; the probe
  service on 8768 and `scripts/mcp_probe/state` were not touched; no `tailscale` command ran.
- Outputs: `fixtures-local/c1a-manual/`; report `fixtures-local/c1a-manual-report.json`.

| Tool | linear algebra | probability |
|---|---|---|
| `status` (ms) | ok (110) | ok (115) |
| `today` | plan off, 23 due now (316) | plan off, 1 due now (119) |
| `progress` | 7 retention risks, no goals (286) | 1 risk (222) |
| `library` | 3 sources (274) | 4 sources (316) |
| `learning_context` (all) | 12 traces: 5 questions and 4 answers shown, 1 answer withheld ("it states the answer key"), 7 exam work (no question, no answer); 2 open hypotheses, **both statements withheld** (one "a diagnostic check", one "Held back until LearnLoop records what this was written from"); 7 risks (288) | 2 traces, 2 questions and 2 answers; 1 risk (173) |
| `learning_context` (topic) | "eigenvalues": nothing matched, named in `unknowns` (82) | "conditional probability": 2 traces (155) |
| `find_sources` | 4 passages, 2 held for a check; unverified (491) | 6 passages (480) |

**Withheld text stays withheld.** Every derived text on record was searched for in every output:
- linear algebra: 1 misconception statement, 1 correction, 1 candidate, 3 hypothesis statements; none appears;
- probability: nothing derived on record.

This matches the narrow stage's run on the same data.

**The tools wrote only their audit rows**, on the throwaway copies: `interaction_events` +7 each, and
`source_exposure_events` +4 and +6. The parity copies' hashes were unchanged. Paid routes asked for:
`source_query_rewrite`, given no client. **Paid calls: 0; cost: $0.**

### Owner runbook: storage spec §6.10

The deployment runbook is now [spec_storage_sync_v1.md](../specs/spec_storage_sync_v1.md) §6.10. It supersedes the
443 runbook above and answers Q3:
- **Funnel port 8443** (D7) instead of 443, with the unit's Host allowlist changed in the same step:
  `--public-host <hub>.<tailnet>.ts.net:8443` (otherwise every request through the new port gets a 421).
- The unit runs from the deployment checkout (D13), and the vault lives under the data root (D5).
- The owner re-points the claude.ai and ChatGPT connector URLs to `https://<hub>.<tailnet>.ts.net:8443/<token>/mcp`
  (`learnloop mcp token show`) and refreshes each host's tool list.
- The spec did not verify that both connectors accept port 8443; if either refuses, its fallback swaps the ports.
- Agents run no `tailscale` command. A vault the desktop has not opened since this landing is at 202, and
  `learnloop mcp serve` refuses it (exit 78) until migration 203 runs.

### Open questions (defaults applied)

- **Q15 (learner questions):** a question the learner typed during a pinned attempt stays (c), held back, until
  `question_events` record the item contract it was asked about (Q10, in the follow-up stage). Applied: unchanged.
- **Q16 (R2a convergence):** as built above. The predicates and the protection are shared in
  `learnloop.learner_protection`, and the text rule is a parameter: the card keeps G5, the chat keeps `TextGuard`.
  The card withholds the chat's whole protected set; the chat shows exactly what it did.
- **Q5 (the renumber):** done, 210 → 203.
- **The follow-up stage "diagnosis input provenance" (spec §4.8)** is still to come; it unlocks the prose. Each writer
  records what it read, in the transaction that writes the text: diagnoses, C4 receipts inside the grading
  transaction, regrade lineage, `question_events`' item contract, and what of an item a writer saw. A
  `ProvenanceSource` reading those records then replaces `no_write_provenance`. Neither reader needs another change,
  and the card's text rule is unaffected.
- Q1 (`find_sources` not read-only), Q2 (the chat's answer-states-the-key rule) and Q4 (OAuth before C1b or C2) are
  unchanged. Q3 is answered by the storage spec (8443).

### Safety

- No paid call, no subscription call, no network. Nothing bound but in-process transports. No key, credential, `.env`
  or `settings.env` file was read, nor `~/.config/learnloop/` or `scripts/mcp_probe/state`.
- The main checkout and `mcp/c1-read-context` (worktree `learnanything-mcp`) were not touched. This worktree's
  tracked `linear_algebra` and `probability` were opened only by the backup API (hashed before and after: unchanged);
  `arxiv_v2` not at all. Nothing was pushed or stashed.
