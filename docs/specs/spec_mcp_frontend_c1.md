# LearnLoop in ChatGPT and Claude, phase C1: read, ground and share the learner (v1)

**Status:** C1a built on `mcp/c1-read-context` (base `9c5c62df9`, mvp-0.22), narrowed on 2026-10-14 by owner
decision ("land narrow, then fix source", §4.7); C1b specified here, not built.
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
| `learning_context` | the shared latent-state read model (§4.6) for a topic, named LOs, or the whole learner | Read-only; wording a model wrote is held back (§4.7) |

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
no model call. Sections: recorded misconceptions (status, severity, evidence count, dates) and candidates still
in the holding pen; open hypotheses (the daily plan's own resolution predicate,
`db.stores.daily_plans.open_learner_state_hypotheses`, identical to R2a's) with evidence for (answers in the
episode, recurrence class count, learner confirmations, failed cold checks) and against (learner disputes,
passed cold checks) and the repairs tried; recurrence groups; recent answer traces (the pinned question, the
learner's answer excerpt, the blind grade class, the diagnosis status, held, hints, primed, revealed-before,
stuck, cold-check and entry-surface labels); open learner-text gaps (what kind, which action, which topic, minus
reversed ones); retention risks (FSRS recall now below 0.8, or due). Since the narrow stage (§4.7) the
statements, corrections, summaries and gap targets in these sections are held back unless rule (c) releases
them: since the diagnosis-input-provenance stage (§4.8, migration 204) a text whose writer recorded what it
read, completely, with every recorded input safe, is shown; the entries, ids, statuses, counts and dates
always show.

**What chat shows, and what it holds back (owner decision 2026-10-14; the right column is shown under (c)
once a text's write-time record is complete and safe, §4.8):**

| Shown | Held back (`Held back until LearnLoop records what this was written from`) |
|---|---|
| Every entry, with its id, status, severity, evidence and episode counts, dates, labels, held state, repairs tried | Misconception statements and corrections; candidate statements |
| The learner's own answer on a pinned attempt, through the answer guard (its protection, its pinned contract, every key its item is known to have had) | Hypothesis statements (open hypotheses, a trace's diagnosis hypotheses) and recurrence-group statements |
| The question as graded (the pinned contract's prompt) | Diagnosis summaries (the status still shows) |
| Topic names and ids the learner or an authored vault file wrote | What a learner-text gap was matched to (a belief's statement); a generated topic it created or matched shows a fixed label |
| A gap's words when they are a pinned answer (a diagnosis's or a stuck answer's gap: the answer as the attempt records it) | A gap's words when they are a question the learner asked (no pinned answer behind them, Q10) |
| Retention risks, with authored topic names | Every generated topic's name (a fixed label) and id (an opaque keyed alias, accepted back as a named id by `learning_context` and `find_sources`; its raw id is answered as unknown and a topic search does not match its words), and the question of an item seeded on one |
| Recurrence groups, each under an opaque keyed key (Q13) | |

The output schema types and closes every field (F4 round 3), and every text field is classified
(`learner_context.RELEASED_BY`, `STRUCTURAL_FIELDS`): released only by (a), (b) or (c) of §4.7, or structural
(ids, codes, times, fixed notes); a test checks the classes against the advertised schema and the values each
field holds, with and without write-time records.
Diagnosed and unresolved causes share the one `open_hypotheses` limit; when they overflow it, the
unresolved causes keep up to half of it (an LO with no diagnosed cause shown first), so an LO whose only
open problem is unsettled stays visible (re-review F12).

Router R2a's `LearnerStateCardV1` (on `router/r2a`, not on main) gathers the same sections; the field
names of `open_hypotheses` and `recent_answer_traces` are a superset of the card's `open_hypotheses` and
`recent_work` (pinned by a test). Convergence task (after R2a lands): the card's gatherer reads its
sections from this module (one predicate set); whether the card, whose reader is the router's model and not a
chat host, also takes the narrow text rule is an owner question (record, Q16).

### 4.7 Leakage rules (the card's G5, on every output)

1. **One structural rule for text (owner decision 2026-10-14, "land narrow, then fix source").** A text
   leaves LearnLoop only when it is
   - **(a) authored vault text**: a topic's name or id that the learner or an authored vault file wrote, and
     the question as graded (its pinned contract's prompt);
   - **(b) the learner's own answer on a pinned attempt**, through the answer guard: the answer passes its
     protection (rule 2), it was graded against exactly one pinned contract on its own item (the revision;
     the absence of a recorded change does not establish it, re-review F4), and it reproduces no key its
     item is known to have had: today's YAML, every assessment-contract snapshot and every practice-item
     snapshot (`learner_context.KeyBook`, read for filtering only; `tutor_qa.span_leaks_expected`). Chat adds
     one rule the card does not: a correct answer that states the key is withheld (Q2);
   - **(c) a derived text with a recorded, complete write-time provenance whose inputs are all safe**
     (`learner_context.WriteProvenance`, read through a `ProvenanceSource`; by default
     `recorded_write_provenance`, the `text_write_provenance` records of §4.8): the record covers the text
     as stored (its hash), every answer it names passes (b)'s checks under the revision it was read with,
     every item its protection, every item whose rubric or reference solution the writer read can no
     longer be answered cold (`learner_protection.PastWork.solution_reason`), every source ref is not exam
     material, every learner question records the contract of its own unprotected item (Q10), every topic
     is authored or carries its own folded record, and the text reproduces no key of those items and
     topics. The kill switch `diagnosis.chat_shows_recorded_text` (on) puts back "nothing derived".

   Everything else is held back with one plain reason, `Held back until LearnLoop records what this was
   written from`; an entry whose own answer is protected names that instead ("a check waiting in the app").
   `learner_context.TextGuard` is the one renderer: `_authored` (a), `answer` (b) and `derived` (c) each
   build their own release type (`AuthoredText`, `AnswerText`, `RecordedText`) and nothing else does (a
   test pins it). A **generated topic** (the learner-text pipeline's prerequisite: by its provenance, its
   `lo_ltg_` id, or a gap recording its creation) has a name drafted from the learner's words and an id
   carrying a slug of it, so both are (c): while held back the entry shows `a topic named from the learner's
   own words (…)` and an opaque alias `lo_withheld_<HMAC>`. **Aliases are keyed** (HMAC-SHA256 under a
   per-vault secret, `.learnloop/mcp/alias-key`, 0600 beside the endpoint token, made once by `learnloop mcp
   serve` under a lock, never printed; without it a process key): an unkeyed digest let a client that
   guessed a title or a root statement confirm it (the old `sha256(id)` alias, Q13's group key). A raw
   generated id names nothing while its name is held back (`learning_context` and `find_sources` answer it
   as an id the vault does not have): it is the title's slug, so accepting it would confirm a guess.
   **`today` and `progress`** name topics through the same guard (Q12): plan block topics, goal topics, the
   assumed list and retention risks; a plan block's why, which embeds the titles it was built with, is shown
   only when it was computed and touches no generated topic.

   **Why no output-side provenance any more.** Rounds 3 to 5 of F4 followed each text's provenance from the
   output back to the answers behind it (error events, episodes, promotions, gaps, a diagnosis's context
   receipt). Each verify found an input no record names: a snapshot diagnosis reads the whole-vault export
   without recording what it opened, so a key (or a generated title) it copied left no trace; a joint
   grader's C4 receipt is written outside the grading transaction, so a missing receipt reads as "shown
   nothing" (Q14); a regrade re-mints error-event ids (Q9); a tutor question records no item revision
   (Q10). Output-side matching cannot replace input provenance, so it was removed; provenance is trusted only
   when it is recorded as the text is written.
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

### 4.8 Diagnosis input provenance (built: `diagnosis/input-provenance`, migration 204)

Every writer of a model-written text records, in the transaction that writes it, exactly what it read, as
a closed record (`db.stores.write_provenance`, table `text_write_provenance`, RAW_LEDGER, append-only): its
own reads plus the recorded inputs of every derived text it read. A text's provenance is the union of its
writers' rows; a text with no row, an incomplete row, or a row whose hash no longer matches the text is
held back. Old rows have none and stay held back; a re-diagnosis writes new, recorded ones.

- **Gradings** (`kind = grading`, keyed by attempt): the answer under its pinned contract, the item's
  question, rubric and reference solution, its topic, and the prior answers the joint grader was shown
  (C4). **Q14:** the joint grade, its Phase-C receipt and this record commit in one transaction (a receipt
  that cannot be written fails the grading), so a missing receipt means "not augmented". A grading made
  before migration 204 is accounted for by its own ledger: blind (learner-blind by construction), a
  model-free grade (no grader text), a joint grade with a C4 receipt; a joint model grade without one is
  incomplete.
- **Diagnoses** (`diagnosis.split.provenance`): every attempt the context showed (under its pinned
  contract; with its grading folded in when a grader's output about it was shown, and its item's rubric
  and reference solution counted as read), the diagnosed item's rubric and reference solution, the
  neighbourhood's topics, and every prior hypothesis, registry statement, repair and unresolved-cause
  factor read (their records folded in). **The snapshot workspace:** the transport's reported reads are
  mapped to the export entries they served (a plain read serves its file; a listing names only; anything
  else counts as the whole export); no report, or a path outside the export, makes the record incomplete.
- **Copy writers:** materialized hypotheses fold the attempt's grading and the diagnosis whose causal view
  lies over the event (a factor's candidate: every completed diagnosis of the attempt); a hypothesis
  version that keeps its head's statement carries the head's record; candidates (error hunts, the gap
  reader, a confirmed factor) and promoted misconceptions fold their sources; a correction frozen from
  facet claims records the source refs those facets were authored from.
- **Learner-text gaps:** a question's words record the question with its contract (Q10), its item, the
  attempt it was asked during, the passage a Reader question was asked on and, when the learner could have
  seen the item's solution first (a feedback question, a reveal), the solution and the grading; the
  drafter of a generated topic records the reading, the learner text and its context, the asking topic and
  the concept titles it was shown. A tutor question's reading is written by the tutor, whose inputs are not
  recorded yet: what it names (a belief, a drafted topic, a seeded item) is recorded incomplete.
- **Q9:** a regrade's re-minted error events record the ids they replace (`error_event_lineage`), so a
  belief listing a replaced event still resolves (`current_error_event_ids`; the diagnosis history reads it).
- **Q10:** `question_events.assessment_contract_version_id`: the item as presented mid-attempt, or the
  graded attempt's pinned contract.
- **What of an item a writer saw:** a rubric or reference solution read for an item the learner can still
  answer cold (its attempt window is open: the retrieval policy's rule for unlocking an item's own
  solution) holds the text back until the window closes.

The router card keeps its G5 rule; it may read the same records.

## 5. Telemetry: the chat side in the existing ledgers

| What | Where | Fields |
|---|---|---|
| Every tool call, failures included | `interaction_events`, kind `chat_tool_call` (migration **203**; built as 210, a placeholder number, and renumbered at its landing), origin `chat_host` | `subject` = tool; `actor` = `chat_host_model`; `client_id` = host (`claude` / `chatgpt` / `unknown`, from Origin, User-Agent, `openai/*` metadata or client name: a label, never authority); payload: surface `chat_mcp`, transport, call id, status and error code, argument and result hashes, counts, LOs touched, exposure ids, duration, `authority_class = salience_only`; `policy_version` = algorithm version; `client_idempotency_key` = `chat_mcp:<call id>` |
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
exam text, cold stems and passages, reserved and probe stems and a held score; the narrow rule (every text
field classified and checked against the advertised schema, the last verify's reproductions held back,
generated names never shown by `learning_context`, `today` or `progress`, keyed aliases); fail-closed protection; the
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
- **R3: answer leakage through teaching context:** the G5 rules above (since 2026-10-14 nothing a model
  wrote is shown until its inputs are recorded at write time, §4.7–4.8); the chat practice successor (§7)
  is what makes chat attempts honest.
- **R4: two processes, one vault:** SQLite serializes; C1a writes only append-only ledger rows.
- **R5: drift from R2a's card:** one read model, field names pinned by a test, convergence task recorded.
