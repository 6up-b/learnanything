# The ChatGPT plan as a peer of Codex

Stage: `chatgpt-plan-peer` (worktree `learnanything-merge3`, branch
`ai/chatgpt-plan-provider`, base `37a2a7e5f`, mvp-0.25, migrations to 204).
Owner direction (2026-10-15): "Definitely have a chatgpt_plan provider beside
Codex." The owner can run LearnLoop on the ChatGPT plan without the Codex SDK
wherever that works better. **No default changes here**: Codex stays the
active provider until the owner decides after the comparison (§7, §8).

Scope kept to `ai/` providers, routing, the diagnosis snapshot transport seam
and the compare command. No migration, no algorithm successor (a transport:
replay reads none of it), no frontend or `src-tauri` change.

## 1. The docs, re-read 2026-10-15

- `developers.openai.com/siwc/token-sharing-open-source/preview-limitations`:
  "Group function/custom tools in namespaces or supply them through
  `additional_tools` input items." Hosted tools (image generation, file
  search, Code Interpreter, computer use, hosted MCP/connectors, `tool_search`)
  are unsupported. Set `store: false` and `stream: true`; "Omit
  `previous_response_id` over HTTP and send the required history in `input`."
  The unsupported request fields are unchanged from 2026-10-12. "Text, images,
  and files are supported when the selected model accepts them"; audio/video
  input, the Files upload API and transcription are not. "Web search remains
  subject to model and account/workspace policy."
- `…/models-and-inference`: the endpoint is `POST https://api.openai.com/v1/responses`;
  success only on `response.completed`; a usage limit can arrive as
  `response.failed` after streaming began. No tool example is given.
- The Responses API reference (`developers.openai.com/api/reference/cli/resources/responses`):
  `namespace_tool { description, name, tools, type }` "Groups function/custom
  tools under a shared namespace"; `include: ["reasoning.encrypted_content"]`
  returns reasoning that can be resent when the API is used statelessly
  (`store: false`).

So function calling **is** supported under plan usage: the read-only
workspace is served by Responses function calling (`workspace_mode = "tools"`,
the default), with the deterministic inline mode as the fallback the task
asked for. Not verified live: the plan sign-in is interactive and the owner's
(§7). If the route rejects the tools, the error names the fix
(`workspace_mode = "inline"`).

## 2. Audit: routes, capabilities, providers (task item 1)

### 2.1 Capabilities by profile type (after this stage)

| Capability | `codex_sdk` | `chatgpt_plan` | `openai_chat` / `openrouter` | `http` (legacy adapter) | others |
|---|---|---|---|---|---|
| Structured completion | yes (agent turn) | yes (one Responses request) | yes | 8 legacy endpoint operations only | — |
| Bounded (one request under `single_request()`) | no | yes | yes | no | — |
| Isolated turn | yes (per-turn permission profile, fail closed) | yes (no tools, by construction) | yes (by construction) | never | — |
| Tool-free | no (runs tools; `TOOL_ISOLATION` bubblewrap for closed-book scopes) | yes | yes | — | — |
| Read-only workspace | yes (its sandbox reads the directory; reports activity best effort) | **yes, new**: served by LearnLoop, recorded exactly | no | no | — |
| Interrupt | yes | yes | no | no | — |
| Images / files in a structured call | none used by any route (isolated turns set `tools.view_image=false`) | none sent (the route accepts them when the model does; not built) | native audio/PDF per `input_modalities` (transcription, PDF markdown) | — | `openai_embedding` embeds images |
| Web search | disabled in isolated turns; no route uses it | not sent (hosted, policy-gated) | — | — | — |
| Embedding | — | — | — | — | `openai_embedding` only |
| Decisions | — | — | — | — | `decider` only |
| Video generation | — | — | `openrouter` only | — | — |

### 2.2 Routes and who can serve them

| Routes | Needs | Codex | ChatGPT plan | Chat (OpenRouter, OpenAI-compatible) |
|---|---|---|---|---|
| `grading` (blind grader), `same_cause_judge`, `learner_gap_judge`, `learner_gap_reader`, `diagnosis_judge`, `diagnosis_generator`, `router_llm`, `llm_probability_llm`, `field_question_classifier`, `contamination_judge`, `rubric_phrasing_judge`, the `pf_*` routes, `tutor_qa`'s reading quick check | isolated turn | yes | yes | yes |
| `diagnosis` in `exact` / `full` / `hybrid` | isolated turn | yes | yes | yes |
| `diagnosis` in `snapshot` | isolated + read-only workspace | yes | **yes (new)** | no (skipped, `provider_lacks_read_only_workspace`) |
| `authoring`, `canonical_ingest(_retry)`, `tutor_qa`, `teach_back`, `rung_variant`, `animation`, `project`, `practice_*`, `source_*` (T6), `source_solution_match`, `source_compare`, `exercise_discrimination`, `worked_example_equivalence` | structured completion | yes | yes | yes |
| `canonical_ingest` native media (`[ingest.native]`), `transcription` | audio / PDF input | no | no (audio unsupported by the route; PDF/image input not built) | yes, per `input_modalities` |
| `video_generation` | async video jobs | no | no | `openrouter` only |
| `embedding` | embeddings | no | no | `openai_embedding` only |
| `tier1_decider`, `router_decider`, `llm_probability_decider`, `learner_gap_decider` | decisions | no | no | `decider` only |
| `facet_identity_judge`, `rubric_phrasing_judge` | structured or decisions | yes | yes | yes, or a `decider` |

Fallback: an unpinned route falls back to `ai.fallback_provider` when its
provider is not ready (signed out, paused, disabled). Routes that never fall
back, by design: an explicit or environment selection, the decider and
embedding routes, and the pinned paid routes (`practice_index.paid`, PF, the
offline reviews), whose checkpoints key on the model.

### 2.3 Every place that requires Codex specifically

| Place | What | Verdict |
|---|---|---|
| `ai/routing.py` `client_for_provider` | only `codex_sdk` took the caller's deadline | **fixed**: `TURN_DEADLINE_PROFILE_TYPES = {codex_sdk, chatgpt_plan}` (a workspace turn's rounds share one deadline; the async diagnoser's 300 s reaches the plan) |
| `cli/diagnose.py` (review dry run) | `workspace_ready = profile_type == "codex_sdk"` | **fixed**: `WORKSPACE_PROFILE_TYPES` |
| `diagnosis/offline_review/runner.py` | "lacks READ_ONLY_WORKSPACE (Codex SDK only in M1)" | **fixed**: message names both |
| `diagnosis/split/jobs.py` | comment "Codex turns take the async diagnoser's own deadline" | **fixed** (comment) |
| `config/template.py` `[ai.routing]`, `DEFAULT_CODEX_TASK_ROUTES` | a vault pins 8 routes to `codex_low` / `codex_medium`; `active_provider` alone does not move them | **recorded**: the switch-over edits them (§8); template comment says so |
| `config/schema.py` code-default profiles | `codex`, `codex_low`, `codex_medium`, `codex_luna` (facet identity's default) always exist | kept; the plan is configured per vault |
| `cli/app.py`, `cli/runtime.py` (`CODEX_PROVIDER_NAMES`) | "Codex runtime" label, legacy `codex_failed` / `codex_*` status codes | label and legacy JSON codes only; other providers get "AI provider" / `ai_failed` |
| `attempts/attempts.py`, `regrade.py` | `complete_attempt_with_codex_fallback` vs `_ai_fallback`; `codex_revision` column | same code path; `grading_source` label and Codex-only metadata |
| `ai/isolation.py` | `TOOL_ISOLATION` (bubblewrap) | Codex-only by nature; the plan never runs tools, so closed-book scopes hold by construction (`isolation_mode` = `tool_free`) |
| `cli/project.py` `--context-scope repo` | "needs READ_ONLY_WORKSPACE, which is not built yet" | open (§9): both transports now declare it, the project command does not use it |
| `ai/spend.py` and four local copies | subscription billing types | already include `chatgpt_plan` |
| `ai/disclosures.py`, `content/pipeline/add_source.py` | recipient / consent family | already name the ChatGPT plan ("chatgpt" family) |

## 3. The served read-only workspace (task item 2)

`src/learnloop/ai/chatgpt_plan/workspace.py`, wired in
`ai/providers/chatgpt_plan.py`.

- **Tools mode** (default). One namespace, `workspace`, with two strict
  functions: `list_entries(directory)` (names, sizes, subdirectory counts) and
  `read_entry(path, start_line, max_lines)`. LearnLoop answers each call from
  an index of the directory taken when the turn starts: regular files only,
  no symlink followed, no `..`, no absolute path outside the root, no shell,
  search or network. A long file is served in parts ("more follows:
  start_line=N"); a line longer than the allowance is served cut and says so.
- **No search function, deliberately.** A search reads every file it scans;
  diagnosis input provenance counts a search as reading the whole export, so
  one search would turn the exact record into "whole". The export's
  `INDEX.md` (every attempt with its topic, outcome and error types) is the
  map the model reads instead.
- **Provenance by construction.** Each served file or line range is recorded
  (`ServedEntry`: path, sha256 of the file, lines, characters, call id,
  round) as the call runs, before the next request carries it.
  `workspace_activity()` returns the served paths, relative to the root, once
  each, in order; a listing serves names only and a refused call serves
  nothing, so neither appears. A file is recorded when handed out, even if
  the request that would carry it then fails: over-reporting is safe,
  under-reporting is not.
- **Inline mode** (`workspace_mode = "inline"`): every file in the request as
  `<workspace_file path="…">` blocks, every file recorded; refused before
  sending when over `max_workspace_chars`.
- **Bounds.** `max_tool_rounds` (16) rounds of calls are served; the next
  round's calls are answered "answer now" (nothing served); a response after
  that which still calls is invalid output. `max_entry_chars` (24,000) per
  read, `max_workspace_chars` (400,000) per turn. Output: the plan route takes
  no `max_output_tokens`, so no round is capped below the shared policy
  (`ai.output_tokens` 16,384; a caller's budget rides in the prompt once); a
  `response.incomplete` for length is `AIOutputTruncated`, never accepted.
- **Stream-only, no store.** Every round is `store: false`, `stream: true`,
  `include: ["reasoning.encrypted_content"]`, and resends the whole history:
  the prompt, each reasoning item as `encrypted_content` + `summary` (no id,
  no raw content), each function call without its id, and one
  `function_call_output` per call. No `previous_response_id`, no `tool_choice`.
- **Controls per round.** Each round is one physical request with its own
  child receipt (`responses_request`), whose `usage_json.chatgpt_plan` names
  the request id, `billing: "subscription"`, the round, the files that
  request carried for the first time and the number of calls. Interrupt and
  the deadline stop any round (a request is never sent after either); a
  usage-limit error pauses the plan machine-wide; a 401 refreshes and resends
  the same round; a transient failure retries the same round inside the
  deadline. A workspace turn refuses to run under `single_request()` (it is
  several requests). The JSON repair, if needed, is tool-free and never sees
  the workspace.

### 3.1 Wiring to diagnosis input provenance

The provenance landing (merge2, `merge/provenance-onto-main`, migration 205)
maps the diagnoser's reported activity to export entries with
`provenance.served_entries(manifest.entries, workspace_activity())`; a bare
relative path naming an export file is that file's read. The plan's activity
is exactly such paths, so a snapshot diagnosis on the plan records every
served entry as an input, and nothing else, with no change to the diagnoser:
this branch leaves `diagnosis/split/diagnoser.py` untouched (merge2 rewrites
those lines). Checked against merge2's module, loaded by path in a scratch
script (no merge):

| Activity | `served_entries` |
|---|---|
| tools mode: list root, list `attempts`, read `INDEX.md`, read one attempt by `/attempts/…` (normalized), a refused `../etc/passwd` | `("entries", ("INDEX.md", "attempts/…_att_1.md"))` |
| inline mode | `("entries", every file)` |
| nothing read | `("entries", ())` (not "unreported") |

`tests/test_chatgpt_plan_workspace.py::test_served_paths_map_to_export_entries_under_input_provenance`
asserts the first row and skips until `learnloop.diagnosis.split.provenance`
is on main; `test_a_snapshot_diagnosis_on_the_plan_records_exactly_what_it_read`
runs `run_diagnosis` end to end on the plan today.

## 4. Routing, spend and disclosures (task item 3)

- Selectable per route (`[ai.routing] <route> = "chatgpt"`) and as the active
  provider (`[ai] active_provider = "chatgpt"`); the desktop's Settings
  already offers any generation profile. With `fallback_provider = "codex"`
  a route that reaches the plan through configuration (`[ai.routing]`,
  `active_provider` or the grading default) uses Codex while the plan is
  signed out, paused or disabled; only an explicit selection (a command's
  named profile, such as `ai compare --profiles chatgpt`) or an environment
  override (`LEARNLOOP_AI_PROVIDER`) never falls back (`fallback_provider_for`;
  corrected after the Codex review, 2026-10-15: this said "a pinned route
  never falls back", which an `[ai.routing]` entry does not satisfy). Tested
  for grading, diagnosis, tutor_qa, authoring, router_llm and
  same_cause_judge.
- `client_for_provider` gives the plan the caller's whole-operation deadline.
- Spend: billing `subscription` (Slice A plan §5 rule 6), cost estimated from
  the reported usage; every physical request (each workspace round) is a
  receipt with its own input/cached/output/reasoning tokens and
  `billing: "subscription"` in `usage_json`.
- Disclosures: `recipient()` names "OpenAI, through your ChatGPT plan (Sign in
  with ChatGPT; requests are sent with store=false)"; with
  `active_provider = "chatgpt"`, the judgment-route disclosures name it.

## 5. `learnloop ai compare` (task item 4)

```
learnloop ai compare --copy-from <vault> --vault fixtures-local/<name> --profiles codex,chatgpt --dry-run
learnloop ai compare --vault fixtures-local/<name> --profiles codex,chatgpt
```

`src/learnloop/cli/ai_compare.py` (the CLI layer: `ops` may not import
`diagnosis`). Per subscription profile: a few attempts blind-graded (the
latest non-pass and pass first; `--attempt` to choose), one diagnosis
(`snapshot` by default; `--diagnosis-attempt`, `--diagnosis-mode`), one
teach-back authoring draft. Grading reads the contract production
regrading reads (a method-explicit answer's frozen assessment contract);
the draft is judged by the tutor's own validator. Nothing serving is
written: the copy gets receipts and the comparison's verdicts in its
`judgment_ledger` (tasks `ai_compare_grading` / `_diagnosis` /
`_generation`, right side the profile; no serving reader names them). The
report (ids, numbers and local explanations only;
`fixtures-local/reports/ai-compare/<stamp>-<run_id>.json`, never overwritten):

- per call: parsed, valid, error class, a failure's code, HTTP status,
  parameter name and request ids with a locally written hint (never the
  provider's message), seconds, physical requests,
  input/cached/output/reasoning tokens, answering models, receipt and
  judgment ids, spend (planned and reported tokens, `estimated_only`);
  the diagnosis adds status, unknown ids, cited attempts, causal classes,
  workspace rounds and files served; the generation the validator's
  rejection sentence, if any;
- per profile: totals, median and max latency, tokens per call, its
  subscription spend budget (call cap = the plan, `estimated_only`, no
  physical-request bound; every call admitted before it is sent and
  reconciled with reported usage), and plan allowance (ChatGPT plan pause state before and after, usage-limit code;
  a usage-limit error stops that profile, its other calls marked `not_run`);
- per pair: grading agreement (exact rate, mean |Δ|/max, criterion agreement,
  full-credit agreement), diagnosis agreement (same causal classes,
  cited-attempt Jaccard, unknown ids), generation validity; and each
  profile's agreement with the grade the vault recorded.

Safety: a vault whose database git tracks is refused (the owner's working
vaults), checked before the database is opened. The check fails closed: only
git's "untracked" (exit 1) or "not a git repository" lets a vault through; a
timeout, an OS error or any other git failure (dubious ownership, say) refuses
it as a working vault (fixed on resume, 2026-10-15: it used to let those
through); without git only the copy `--copy-from` just made passes.
`--copy-from` makes a backup-API copy (also on a dry run) into a new
directory outside the source, resolving the source's configured database
first: one not named `*.sqlite` is backed up (never byte-copied with its
`-wal`), one configured outside the source is backed up into the copy, and
the copy's `storage.sqlite_path` then names its own database. A `--vault`
whose database lies outside it is refused. Subscription profiles only; the
dry run prints every planned call's token estimate in both output formats.
`tee_model_calls` measures beside the command's receipt observer, so
receipts still land in the copy.

## 6. Tests (fakes only; no live call in the gate)

- `tests/test_chatgpt_plan_workspace.py` (26, one skipped until provenance
  lands): function-tool rounds and request shape, per-round receipts and
  billing, dotted names, terminal output fallback, unencrypted reasoning not
  resent, refused calls (traversal, absolute, symlinked file and directory,
  bad JSON, unknown function and namespace, directory/file confusion, past
  end) serving nothing, a missing call id, line-range parts, the round budget
  and its fail-closed end, the character budget, interrupt, deadline,
  usage-limit pause, 401 refresh resending the same round, transient retry,
  rejected tools naming the inline fix, repair without the workspace, no
  workspace under `single_request()`, inline mode and its budget, a snapshot
  diagnosis end to end, the provenance mapping, routing (capability,
  deadline), Codex fallback while paused, disclosures, profile validation.
- `tests/test_ai_compare.py` (26 cases): dry run sends nothing and
  estimates every call (JSON and text; a generation-only run), a run on a
  `--copy-from` copy (agreement, validity, latency, tokens, allowance, spend
  admission and reconciliation, root receipts' declared caps, judgments in the
  copy's ledger with serving state unchanged; original untouched, receipts in
  the copy), a usage limit stopping a profile, a failed diagnosis keeping its
  codes, the working-vault refusal and its fail-closed check (timeout, other
  git failures, no git), metered/unknown/non-generation profiles refused, copy
  rules, the request meter; and the Codex review's reproductions (an
  external or `..` database relocated, a non-`.sqlite` WAL database backed up,
  an outside database refused, five drafts the tutor rejects, refusal and 400
  sentinels kept out of every output, the frozen contract) and one report
  per run.
- The fake Responses server (`tests/chatgpt_plan_fakes.py`) enforces the
  route's tool contract: namespaced function tools only, hosted tools
  refused, `include` required, no input item with a stored id, reasoning
  items with `encrypted_content` + `summary` and no raw content, every call
  answered exactly once.

## 7. Manual runs (this stage)

All on a backup-API copy of this worktree's tracked `fixtures/probability`
(not the main checkout) at `fixtures-local/compare-probability`, made with
`learnloop.db.copies.copy_tree_with_databases`; a `chatgpt` profile
(`model = "gpt-5.6-sol"`, an assumed slug) was added to the copy's
`learnloop.toml` only. The tracked fixtures were left untouched.

1. Dry run, `--profiles codex,chatgpt`: Codex ready; the plan "Not signed in
   with ChatGPT on this machine". Targets: 2 gradeable attempts (only two in
   this snapshot), diagnosis `01KZ54VPYRZX2Q661XAKX2Z4YN`, generation
   `pi_three_independent_birthd`; 4 calls per profile, 8 at most; grading
   prompts ~3,673 and ~3,702 tokens.
2. Live, `--profiles codex` only (the plan cannot be signed in by an agent):
   4 Codex calls on the subscription. The teach-back authoring draft
   succeeded (15.4 s, 20,175 input / 828 output / 55 reasoning tokens, all
   checks passed). **Both blind gradings and the snapshot diagnosis failed at
   launch in under a second, before any model request**:
   `Codex process closed stdout. stderr_tail=Error: invalid transport in mcp_servers.codex_app`.
3. Live, `--profiles codex --attempts 1 --no-diagnosis --no-generation`: one
   more call, the same launch failure (this run is what surfaced the reason;
   the report now keeps it).

Calls: 5 Codex calls, 4 of which never reached the model; reported usage
21,003 tokens (20,175 input + 828 output); billing subscription, no marginal dollar cost; no OpenRouter
or other paid call. Reports: `fixtures-local/reports/ai-compare/20261015T195642Z.json`
and `…/20261015T195730Z.json` (gitignored).

**Finding.** On this machine every isolated Codex turn fails at launch: the
isolated-turn overrides disable each MCP server Codex lists
(`mcp_servers.<name>.enabled=false`), and for `codex_app` that creates an
entry without a transport, which Codex rejects. Isolated turns carry the
blind grader, the diagnoser and every isolated judge, which is exactly where
the plan needs no sandbox at all. This is Codex-isolation code with its own
review history, so it is recorded here, not changed (§9).

## 8. What the owner runs, and the switch-over (task item 5)

The comparison (interactive sign-in is the owner's):

1. `learnloop ai signin chatgpt` (once per machine), then
   `learnloop ai models chatgpt` to pick a model slug.
2. Add the profile to the vault (alone, this changes nothing):
   ```toml
   [ai.providers.chatgpt]
   type = "chatgpt_plan"
   model = "<a slug from learnloop ai models chatgpt>"
   reasoning_effort = "low"
   timeout_seconds = 900
   ```
3. `learnloop ai compare --copy-from fixtures/probability --vault fixtures-local/compare-plan --profiles codex,chatgpt --dry-run`
   (makes the copy, sends nothing), then
   `learnloop ai compare --vault fixtures-local/compare-plan --profiles codex,chatgpt`.
   `--attempts 5` grades more; `fixtures/linear_algebra` has more history.
4. Read the report: grading agreement and validity, the diagnosis's cited
   attempts and causal classes (and the plan's served files), tokens per call,
   latency, and whether the plan paused.

The switch, only if the owner decides (Codex stays the default otherwise). In
the vault's `learnloop.toml`:

```toml
[ai]
active_provider = "chatgpt"
fallback_provider = "codex"

[ai.routing]          # the eight routes the template pins to Codex profiles
grading = "chatgpt"
canonical_ingest = "chatgpt"
canonical_ingest_retry = "chatgpt"
authoring = "chatgpt"
tutor_qa = "chatgpt"
teach_back = "chatgpt"
rung_variant = "chatgpt"
animation = "chatgpt"

[ai.route_reasoning_effort]   # what codex_medium gave these routes
canonical_ingest = "medium"
canonical_ingest_retry = "medium"
authoring = "medium"
animation = "medium"
```

Then `learnloop config effective --vault <vault>`, `learnloop doctor --vault <vault>`
and `learnloop ai status chatgpt --vault <vault>` (lists the routes now on the
plan). Unset routes (diagnosis, judges, router LLM, …) follow
`active_provider` or grading. Kill switches: `enabled = false` on the profile
(routed and unset routes fall back to Codex), `learnloop ai signout chatgpt`
(machine-wide), or restore the lines above. A snapshot diagnosis on the plan
needs no setting; `workspace_mode = "inline"` if the route ever rejects the
tools.

## 9. Open questions (defaults in force until the owner says otherwise)

1. **Codex isolated turns fail on this machine** (`invalid transport in
   mcp_servers.codex_app`, §7). Default: recorded, not fixed here; a Codex
   isolation stage should only disable listed servers that have a transport
   (or skip built-in app servers). Until then the plan is the only working
   transport for isolated work here.
2. **Live verification of the tool contract under plan usage** (namespace
   tool shape, `include`, `namespace` on returned calls). Default: the owner's
   comparison is the verification; the inline mode is one setting away.
3. **The switch itself.** Default: no change; the owner decides after the
   comparison (§8).
4. **Images and PDFs on the plan** (the route accepts them when the model
   does). Default: not built; native media stays on chat profiles with
   `input_modalities`.
5. **`learnloop project --context-scope repo`** could now use
   READ_ONLY_WORKSPACE on either transport. Default: left for the project
   stage.
6. **A search function in the served workspace.** Default: none (it would
   collapse exact provenance to "whole"); revisit only if the comparison shows
   the plan missing evidence that Codex's searches find.
7. Out of this stage's scope, carried from the owner's message: the
   reading-signal firewall exception with one weight per discrete reading
   event (section read and passage view collated) belongs to the reading
   stage, not to this transport stage.

## 10. Gate

Run on resume (2026-10-15, after a Claude Code restart stopped the earlier
run before its gate was recorded) on tree `0b7f1b449`, which is the stage's
code; the only later commit adds this section. `TMPDIR` was the worktree's
`fixtures-local/tmp`, and both suite runs held `flock /tmp/learnloop-fullsuite.lock`
and used `uv run --no-sync`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (178 packages; pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 22 contracts kept, 0 broken |
| `pytest -n auto` (full suite) | **11,865 passed, 1 skipped**, 0 failed (12 min 35 s); the skip is `test_served_paths_map_to_export_entries_under_input_provenance` (`importorskip` until provenance reaches this branch) |
| `pytest -m durability` | **106 passed**, 11,760 deselected (1 min 55 s) |
| stage tests (`test_chatgpt_plan_workspace`, `test_ai_compare`, `test_chatgpt_plan_provider`) | 63 passed, 1 skipped (64) |
| `tests/test_coordinated_migrations.py` | green (in the full suite) |
| `db_validate_reference.py` | `errors: []` (schema unchanged at 204; the config reference citations were regenerated in `697809d75`) |
| CLI help snapshot | updated in `a3522a1c1` for `ai compare`; green |
| frontend / `src-tauri` | untouched: npm and cargo checks not required |
| tracked fixtures | `git status` clean after both runs |

Not gate items, both failing before this branch too: `module_validate.py` reports
749 issues (module coverage 474/839, all wikilinks and source links resolve).
The base, exported from `37a2a7e5f`, reports 765, and this branch's only
additions are its two new modules (`ai/chatgpt_plan/workspace.py`,
`cli/ai_compare.py`). `desktop_validate.py` stops on
`apps/learnloop-tauri/src/copy/denyList.ts` (UX Phase 1, before the base).

Fixed on resume: the compare command's working-vault check now fails closed
(`0b7f1b449`, §5). Main has since moved to `2c23afe3f` (provenance,
migration 205); this branch was not merged with it. Main's diagnoser reads
`workspace_activity()` with `getattr` and passes it to
`served_entries(manifest.entries, …)`, which is the call the skipped test
makes, so the plan's served paths become the provenance record once the
branch lands.
