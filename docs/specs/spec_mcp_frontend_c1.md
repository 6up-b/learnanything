# LearnLoop in ChatGPT and Claude, phase C1: read, ground and share the learner (v1)

**Status:** C1a built on `mcp/c1-read-context` (base `9c5c62df9`, mvp-0.22); C1b specified here, not built.
**Written:** 2026-10-13. **Owner direction (2026-10-13):** start C1; Tailscale Funnel is fine and already
works with both Claude chat and ChatGPT chat; latent learner state (misconceptions, hypotheses, answer
traces) must be shared seamlessly between the local LearnLoop and the chat frontend, through the existing
telemetry.

**Form (owner decision D15):** this is the short implementation spec for phase C1. The long research
document, `docs/specs/spec_mcp_frontend_v1.md` (untracked in the main checkout on 2026-10-13: host
capabilities, personalization, scheduling, the full parity plan), is its research appendix. The phase
plan, the decisions D1–D16 and the integrity design come from the Opus review of that spec
(2026-10-13, `mcp-frontend-review.md` in the orchestrator's session notes; its §3 integrity, §5
transport and §7 phases are restated here where C1 uses them). The M0 probe evidence is
`docs/reviews/mcp-compatibility-probes-2026-10-13.md` and `scripts/mcp_probe/` (also untracked there).
The stage record is [docs/reviews/mcp-c1a.md](../reviews/mcp-c1a.md).

## 1. What C1 is

LearnLoop becomes reachable from an ordinary ChatGPT or Claude conversation as an MCP server running on
the owner's own machine, beside the desktop app, over the same vault. The chat host explains, the learner
talks; LearnLoop supplies what it knows about the learner and the learner's own sources, and records
everything the chat side does in the ledgers the local learner model already reads.

| Part | Scope | State |
|---|---|---|
| **C1a** | The adapter (`learnloop_mcp`), secondary attach, transports and gate, six read tools, the shared latent-state read model, telemetry and exposure, `learnloop mcp serve / token / activity` | Built |
| **C1b** | Capture from chat, confirms (`review_changes`, `decide_change`, `undo_change`), `note_question` with the `external_chat` learner-text gap source | Specified (§8) |
| **C2+** | Practice in chat with the chat assistance context and eligibility class (one algorithm successor), widgets, OAuth | Out of scope (§9) |

Not in C1: serving, grading or scheduling from chat; starting sessions; adding sources; any model call of
LearnLoop's own beyond what an existing service already makes (`find_sources`' rewrite, embedding and
verification, through their own routes, spend caps and receipts).

## 2. Owner decisions in force

| # | Decision | C1 |
|---|---|---|
| D1 | Ingress for cloud chat hosts | **Owner decided 2026-10-13: Tailscale Funnel, approved and working** with Claude chat and ChatGPT chat (Funnel on 443 to loopback, secret token path, Origin allowlist). Agents never run `tailscale`; the owner runs the switch-over in the stage record. The mobile host stays Serve-only |
| D2 | First host and device | Default taken: develop over stdio and the SDK client; claude.ai web first, then ChatGPT web |
| D3 | Hosted deployment | Default taken: out of scope; personal deployment on the owner's machine only |
| D8 | Runtime topology | Default taken: a separate `learnloop mcp serve` process in secondary attach; the desktop stays primary |
| D11 | Learner-text gaps from chat questions | Default taken: yes, tier 2 through `external_chat` (C1b) |
| D12 | Writing context back into the host | Default taken: never automatically |
| D14 | Converge with mobile M2 | Default taken: yes; C1a reuses the mobile host's attach pattern and lists what C1b/C2 need from PR-1..PR-7 (§3.3) |
| D15 | Spec form | This document (short spec) plus the research appendix |
| D16 | ChatGPT training setting | Default taken: the owner checks "Improve the model for everyone" for the account used with LearnLoop |
| D4–D7, D9, D10, D13 | Chat practice, self-grade, relay, cold checks in chat, ingest while closed, export import, answer surface | C2+ (defaults recorded in the review) |

Standing owner decisions (2026-10-12): the recommended defaults are accepted, with frictionless defaults:
honest labels, generous defaults, live changes behind kill switches, no shadow stages.

## 3. Architecture

### 3.1 Packages and boundaries

```
learnloop_mcp/               the adapter (entry point): protocol, schemas, gate, host label
  server.py                  six tools, the telemetry wrapper
  http_app.py                streamable HTTP, the endpoint gate, transport security
  hosts.py                   which host made a call (a label, never authority)
  cli.py, __main__.py        serve (http | stdio)
learnloop/remote/            application services for out-of-process frontends
  runtime.py                 secondary attach, content freshness
  views.py                   status, today, progress, library (read-only attach)
  sources.py                 grounded passages (find_sources under a server-derived caller)
  telemetry.py               chat calls and exposure in the existing ledgers; the activity report
  endpoint_token.py          the secret endpoint path, machine-local
learnloop/learner_context.py the shared latent-state read model (§4.6)
learnloop/cli/mcp.py         `learnloop mcp serve | token show | token rotate | activity`
```

Import-linter (all kept): `mcp-adapter-is-independent` (no CLI, TUI, sidecar or mobile);
`mcp-adapter-calls-application-services` (the adapter imports only `learnloop.remote`,
`learnloop.learner_context` and the primitives; every domain and infrastructure package is forbidden to
it); `domain-does-not-import-mcp` (only `learnloop.app_launch` loads the adapter, as it loads the TUI);
`evidence-never-reads-remote-views` (replay, evidence, scheduling and the router never import the remote
services or the read model). The CLI, TUI, sidecar and mobile contracts now also forbid `learnloop_mcp`.
The SDK is the optional extra `mcp` (`mcp==2.3.0`, the probe's version; also in `dev` so its tests always
run). It resolves cleanly with the app's pins; it bumps `idna` 3.17 → 3.20 in the shared lock.

### 3.2 Transports and the gate

- **stdio** for development clients (`learnloop mcp serve --transport stdio`, `python -m learnloop_mcp`).
- **Streamable HTTP**, stateless, JSON responses, bound to `127.0.0.1` only (any other `--host` is
  refused), default port **8769** (the probe on 8768 is untouched), 64 KiB request limit, 32 connections,
  5 s keep-alive, no proxy headers trusted, **no access log**.
- **Endpoint gate (the probe's model):** only `/<token>/mcp` reaches the server, compared in constant
  time; `/mcp` and every other path is a 404. The token is `secrets.token_urlsafe(32)` in
  `<vault>/.learnloop/mcp/endpoint-token` (0600, directory 0700, a `.gitignore` of `*`), printed only by
  `learnloop mcp token show|rotate`, never logged; a rotation takes effect without a restart.
- **Host and Origin allowlists, exact:** Host is `127.0.0.1:<port>`, `localhost:<port>` or a
  `--public-host` (421 otherwise); Origin is absent (server-to-server, allowed), `https://chatgpt.com`,
  `https://claude.ai`, `https://<public host>` or a `--public-origin` (403 otherwise). `--log-level trace`
  is refused (uvicorn's trace logs request paths).
- **OAuth is deferred.** The URL is the credential (risk R1, §10); the follow-up is single-user OAuth with
  CIMD and a tailnet-only consent page (review §5.4).

### 3.3 Second process: secondary attach

`RemoteRuntime.attach` is the mobile host's M1 attach (refuse unless the applied migrations equal this
code's, exit 78; `Repository.attach` without migration) plus the read side of the mobile spec's PR-1
`load_secondary`: the vault's YAML is loaded read-only and **none** of `SidecarContext.load`'s work runs
(no migration, state sync, projection refresh, certification scheduling, startup maintenance, ingest
runner or workers). Views read through a read-only attach, so viewing cannot write. The loaded vault is
reloaded when the vault's content fingerprint (path, size and mtime of every YAML, TOML and Markdown file,
cached 2 s) changes; the database is read fresh on every connection. The desktop writes YAML in place
(truncate, then write), so a load is kept only when the fingerprint is the same before and after it and the
source-sets file is not caught empty; a load the files keep changing under (3 tries) is marked
`vault:snapshot_unsettled`, protection is never read from it (fail closed), and the next request loads
again (Codex review F1). Writes are telemetry, exposure, and what an existing service writes when called;
SQLite (WAL, `busy_timeout`) serializes them with the desktop's.

What C1b and C2 still need from the mobile spec's prerequisites:

| Prerequisite | C1a | C1b | C2 |
|---|---|---|---|
| PR-1 secondary attach | Read side built (`RemoteRuntime`); `SidecarContext.load_secondary` not built | Writes go through domain services, not handlers: not needed | Needed (handler composition for submit) |
| PR-2 content sync never restores stale scheduling state | Not needed (no state sync) | Not needed | Needed |
| PR-3 abandoned-synthesis sweep primary-only | Not needed (no ingest runner) | Not needed | Needed if the host binds a runner |
| PR-4 atomic sessions and handoff | Not needed (no sessions) | Not needed | Needed |
| PR-5 request origin on the context | Origin labelled on telemetry (`chat_host`, host) | Needed for capture and gap provenance (`external_chat`) | Needed (`entry_surface`) |
| PR-6 eligibility module | Not needed | Not needed | Needed (class `chat`) |
| PR-7 desktop freshness (`queue_revision`) | Not needed (nothing the desktop shows changes) | Needed (capture, confirms) | Needed |

## 4. Tools (C1a)

All six return structured content (an output schema per tool) and the same JSON as text. Arguments are
bounded; none names a path, SQL, caller, policy or vault (MCP-12). Annotations are honest: the five views
write only their audit row, so they are read-only; `find_sources` also records the passages it shows as
exposure, a learner-model side effect, so it is not marked read-only (hosts may ask before running it).

| Tool | Reads | Notes |
|---|---|---|
| `status` | vault, algorithm version, schema, AI readiness per route, waiting jobs, grades held for review | Readiness from configuration only: a Codex or ChatGPT-plan route reads `not_checked` (probing would start a process) |
| `today` | the plan the app built today (blocks: lane, minutes, why, topics, item counts), due now, break, headline | Never builds or advances a plan, starts a session or records time (MCP-7); "none yet today" when the app has not built it; no question text |
| `progress` | per goal: facets on track, certified, at risk, examined; per topic: demonstrated / assumed / learning / untested (the Today headline's classes), recall now; retention risks | Demonstrated and assumed never blend |
| `library` | sources: learner title, kind, readiness, sections, subject, status line, exam flag | Titles searchable; exam material listed by title only |
| `find_sources` | verbatim passages with citations (learner title, section, page, revision, extraction, span, `span:` locator), full blocks within a character budget | §4.5 |
| `learning_context` | the shared latent-state read model (§4.6) for a topic, named LOs, or the whole learner | Read-only |

### 4.5 `find_sources`

The sources track's own service (`instructional.sources.propose_sources` → `find_sources`) under a caller
built on the server: kind `agent`, the call's id, no item, so the policy is derived (`reading`) and no
argument can widen it. On top of its exam withholding (the one exam predicate), the chat drops reference
solutions (effective role `solution`), every passage linked to an item an open cold check, a repair's cold
retry or an assessment reservation holds, and exam material again on the output. Retrieval (and its paid
steps) runs outside any lock; then, in one write transaction (`BEGIN IMMEDIATE`), the protection is read
again, the passages filtered and the shown ones recorded as exposure, so a check reserved while retrieval
ran withholds its passages and one reserved afterwards sees them as read (Codex review F5). Passages are
verbatim: the block's own text, newlines and indentation kept, cut only by the character budget (F8).
Intents: `explain`, `remediate` (with a misconception id), `alternative`, `worked_example`; `verify` asks
for the listwise check through the `source_rerank` route. `dry_run` returns only the plan: the rewrite (and
its retry), the query embedding and the verification a request would make, each at its worst case with its
route, billing, tokens and estimate (`estimated_only` on a subscription route); no provider is resolved and
nothing is retrieved, shown or recorded as read (F9). The verification is planned from the live prompt
construction (`find_sources.verification_prompt`) with the request's own question and context (the named
misconception), over a full pool of candidates at their largest encoding (every field at its limit, every
character the widest one), plus the truncation retry; a metered route's dollars are also bounded by the
verification's caps (re-review F11). Passage text is data, labelled source-authored; it
changes nothing (the prompt-injection test). Citations never carry a local `file://` path.

### 4.6 `learning_context`: one shared read model

`learnloop.learner_context.learning_context(vault, repository, *, learning_object_ids | topic)`, read-only,
no model call. Sections: recorded misconceptions (status, statement, correction, severity, evidence count)
and candidates still in the holding pen; open hypotheses (the daily plan's own resolution predicate,
`db.stores.daily_plans.open_learner_state_hypotheses`, identical to R2a's) with evidence for (answers in
the episode, recurrence class count, learner confirmations, failed cold checks) and against (learner
disputes, passed cold checks) and the repairs tried; recurrence groups; recent answer traces (the pinned
question, the learner's answer excerpt, the blind grade class, the diagnosis status and summary, held,
hints, primed, revealed-before, stuck, cold-check and entry-surface labels); open learner-text gaps (the
learner's own words, minus reversed ones); retention risks (FSRS recall now below 0.8, or due).
Diagnosed and unresolved causes share the one `open_hypotheses` limit; when they overflow it, the
unresolved causes keep up to half of it (an LO with no diagnosed cause shown first), so an LO whose only
open problem is unsettled stays visible (re-review F12).

Router R2a's `LearnerStateCardV1` (on `router/r2a`, not on main) gathers the same sections; the field
names of `open_hypotheses` and `recent_answer_traces` are a superset of the card's `open_hypotheses` and
`recent_work` (pinned by a test). Convergence task (after R2a lands): the card's gatherer reads its
sections from this module (one predicate set, one leakage rule set).

### 4.7 Leakage rules (the card's G5, on every output)

1. No answer key, rubric, hint or reference solution is read into any payload; free text that could quote
   a key (a correction, a hypothesis or misconception statement, a diagnosis summary, the learner's own
   answer) is dropped when it reproduces any key its item is known to have had: today's YAML, every
   assessment-contract snapshot and every practice-item snapshot, so the key an attempt was graded against
   counts after an edit (`learner_context.KeyBook`, read for filtering only; `tutor_qa.span_leaks_expected`),
   and says so. Answer and diagnosis text needs affirmative evidence of the revision it was graded against
   (exactly one pinned contract on its own item): an answer with no pinned contract shows no answer,
   diagnosis summary or hypothesis text, and a hypothesis or recurrence-group statement drawn from one is
   withheld too, since a key nothing records any more cannot be filtered (re-review F4). Chat adds this rule for the learner's own answer (a correct answer that states the key is
   withheld); the card shows it.
2. Exam and held-out material (`exam_material.item_exam_status`: the canonical exercise and every
   provenance form, block locators and namespaced span ids included), items reserved for an assessment or
   a held-out exam, items held by an open cold check or a repair's cold retry, and diagnostic probes keep
   their result but show no question and no answer (`learner_context.withheld_items`), nor does a
   hypothesis or recurrence group drawn from any of their answers, nor an item the vault cannot read
   (deleted, or its file unreadable). If those predicates cannot be read, or the source sets cannot be
   trusted (a file the loader could not read, one caught empty mid-write, an unsettled snapshot:
   `learner_context.protection_issues`), nothing shows (fail closed, named in `unknowns`); `find_sources`
   refuses and `library` marks every source as possibly exam material. A topic or ids that match nothing
   return no learner history.
3. A grade held for review (`held_grades`) is "held for review", never a score.
4. A question is the attempt's pinned contract prompt, never today's edited prompt; only the prompt is
   read from a contract.

## 5. Telemetry: the chat side in the existing ledgers

| What | Where | Fields |
|---|---|---|
| Every tool call, failures included | `interaction_events`, kind `chat_tool_call` (migration **210, a placeholder number**), origin `chat_host` | `subject` = tool; `actor` = `chat_host_model`; `client_id` = host (`claude` / `chatgpt` / `unknown`, from Origin, User-Agent, `openai/*` metadata or client name: a label, never authority); payload: surface `chat_mcp`, transport, call id, status and error code, argument and result hashes, counts, LOs touched, exposure ids, duration, `authority_class = salience_only`; `policy_version` = algorithm version; `client_idempotency_key` = `chat_mcp:<call id>` |
| Passages shown | `source_exposure_events` (context `library`, entity `chat_tool_call`, the call id), via `instructional.interventions.record_shown_spans` | Written **before** the passages are returned; the exposure rule, the coldness receipts and the Reader's progress read them as for the Reader |
| Existing service writes | `find_sources`' own receipts, service spend, verification ledger | Unchanged |

A call is recorded before it returns; a call that cannot be recorded returns an error, not a result. A
request the SDK rejects before any tool body runs (arguments that fail the input schema: `invalid_arguments`;
an unknown tool: subject `unknown_tool`) is recorded at the dispatch boundary (`LearnLoopServer`), and a
dispatched call is recorded once (Codex review F10).
Rows of the new kind are salience-only: `reject_salience` refuses them, no existing reader selects the
kind, replay keeps them as raw ledger rows and never reads them as observations. `learnloop mcp activity`
reports calls by tool, host, status and day, the topics touched and the passages shown.

## 6. Gates (C1a)

Tests with the SDK's in-process client, a loopback HTTP server and a real second process (no network, no
model): tool schemas and annotations; the leakage rules on every tool against planted keys, contract keys,
exam text, cold stems and passages, reserved and probe stems and a held score; fail-closed protection; the
token path, Host, Origin and size rules over HTTP; the token never in a log record; rotation without a
restart; secondary attach refusal (exit 78) and no writes from attach or views; a `python -m learnloop_mcp`
stdio process beside a loaded desktop sidecar, in the durability lane; telemetry rows and host labels;
exposure making an item built on a shown passage ineligible as an independent check; `today` writing
nothing to plans, blocks, sessions or receipts; the CLI. Plus lint-imports, the full suite and the
durability lane, the DB reference regenerate and validate.

## 7. Integrity successor (C2, not built)

Chat practice needs one algorithm successor under the playbook (review §3.8): the attempt column
`assistance_observability` (`host_unobserved` for chat-served attempts, so coldness `unassisted` is
`unknown` and they never qualify as cold retrieval, held-out validation, certificate or repair
verification); the **chat eligibility class** applied before the offer receipt (never exam or held-out
items, certification cold probes, repair cold retries, probe presentations, calibration sittings or
golden-path assessments; one quiet "a quick check is waiting in the app" line instead); reveal kinds
`solution_request` and `host_reported` with the `reveal_events.source_kind` CHECK widened;
`host_chat_conversation` among the known unobserved channels; `entry_surface` from the request origin.
Old vaults behave exactly as before.

## 8. C1b (next)

- `capture(text | url, note)` through `learnloop.capture` (idempotent on a client key; reference-only);
  `inbox` read.
- Confirms: `review_changes` (pending proposals and facet rewordings), `decide_change` (accept, reject,
  edit; facet rewording through `confirm_reword`), `undo_change`; YAML writes under `vault_mutation_lock`,
  then the desktop refreshes (PR-7).
- `note_question(text, about)`: learner text from chat into the learner-text gap pipeline with the new
  source kind `external_chat` (tier 2: may change hypotheses and routing, never mastery, evidence,
  coldness or FSRS), migrated in the same `learner_text_gaps` CHECK widening as the Reader workbench's
  `workbench_text` and `reader_formative`; attribution (learner words versus host summary) on the row.
- Request origin on the context (PR-5) for those writes; the salience-firewall test covers `external_chat`.

## 9. Later (C2+)

The practice loop (`start_session`, `next_activity`, `submit_answer` as an accepted job, feedback,
hints, `show_solution`, `report_help`), after R2a (`plan_presentations`) and PR-1..PR-7 land, with the
successor of §7; widgets; OAuth (CIMD, tailnet-only consent); scheduled check-ins; chat-history import and
the context pack (C4); a focused page for cold checks, probes and exams (C5).

## 10. Risks

- **R1: the URL is the credential.** Anyone with the URL can read the learner's state (C1a is read-only;
  `find_sources` writes exposure). Mitigations: 256-bit token path, rotation, Funnel only for this port,
  exact Origin/Host checks, no logging of paths, a read-only tool surface; OAuth before writes beyond C1b.
- **R2: host training on tool results** (ChatGPT consumer plans, D16): return the minimum; no learner-model
  internals beyond what the read model shows.
- **R3: answer leakage through teaching context:** the G5 rules above; the chat practice successor (§7)
  is what makes chat attempts honest.
- **R4: two processes, one vault:** SQLite serializes; C1a writes only append-only ledger rows.
- **R5: drift from R2a's card:** one read model, field names pinned by a test, convergence task recorded.
