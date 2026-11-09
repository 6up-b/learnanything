# Decider v1.2: the dead Decider route (2026-11-09)

Branch `fix/decider-v1-2` on main `a36da14a4a`.

## Problem

The default Decider model, `perplexity/pplx-decider-v1.1-27b`
(`DEFAULT_DECIDER_MODEL`), has no endpoints on OpenRouter any more. A real
call returns HTTP 404 "No endpoints found for perplexity/pplx-decider-v1.1-27b".
The owner checked by hand: the same request body answered with
`perplexity/pplx-decider-v1.2` gets HTTP 200 at
`POST https://openrouter.ai/api/alpha/decisions`, with the answer
`{"ready": {"type": "noul", "noul": 0.987}}` and cost 1.96e-06.

Every Decider call in the owner's vaults failed, and none completed:
104 on arxiv_v2 since Nov 4 and 14 on probability (Oct 25-26). Nothing
showed it. The receipts kept only `error_type = DecisionRequestFailed`
with NULL usage, not the HTTP status. All 8 router traces on arxiv_v2 mark
the decider `unreachable`. That status comes from the router's free check
of the model listing, so the router never sent a paid request.

## Change

1. **Default model `perplexity/pplx-decider-v1.2`**, pinned to the version,
   never the `pplx-decider-latest` alias (`config/schema.py`).
   - The OpenRouter dialect takes it from `DEFAULT_DECIDER_MODEL`.
   - The Perplexity direct dialect now sends `pplx-decider-v1.2`
     (`ai/providers/decider.py`).
   - `facet_identity/judge.py` `KNOWN_PRICES_PER_MILLION` names the new slug.
   - The price stays $0.02 per million input tokens, output free.
   - Specs that state the default carry the new slug and the date of the
     change. That is the router spec (§6 Model and profile, D4), daily loop,
     learner field, reader workbench, source practice, adaptive difficulty
     and implementation goal. The generated config reference was updated too.
   - Tests and fakes name the new slug, and the fake's dated answer is now
     `-20261016`.
   - `tests/test_judge_routes.py::test_an_explicit_vault_profile_stays_authoritative`
     keeps `pplx-decider-v1.1-27b` on purpose. That test shows an owner's
     explicit profile beating the code default, and Perplexity's direct API
     still accepts the v1.1 name.
2. **A failed call records its HTTP status and the provider's error text**,
   with no migration (see "How the status is stored").
3. **`learnloop doctor` reports model route health** (see "Doctor").

### API contract check (public docs only, no calls)

- **OpenRouter's free endpoint listing** (`/api/v1/models/perplexity/pplx-decider-v1.2/endpoints`,
  read 2026-11-09):
  - output modality `decisions`;
  - Perplexity at 0.00000002 per prompt token, Makora at 0.000000019;
  - completion price 0, context 262144;
  - endpoint name `perplexity/pplx-decider-v1.2-20261016`.
- **Perplexity's API reference** (`docs.perplexity.ai/api-reference/decisions-post`)
  documents the request and response for `pplx-decider-v1.2`.
  - Request: `model`, `state`, `questions`. Question types are `noul`,
    `choice` and `score`, as before.
  - Response: `model`, `answers`, `usage` (`input_tokens`, `output_tokens`).
  - Answer fields: `noul` has `type` and `noul`. `choice` has `type`,
    `choice`, `confidence` and `probabilities`. `score` has `type`, `score`,
    `confidence`, `legend` and `probabilities`.
  - These are the fields `_ANSWER_FIELDS` already allows.
  - `pplx-decider-v1.1-27b` and `pplx-decider-v1-27b` "remain accepted and
    select `pplx-decider-v1.2`". So on the direct API, v1.1 already ran on
    v1.2.
- **The only new response fields are conditional.** `search_results` and
  `fetched_results` come back only with `mode: "web_grounding"`. We never
  send `mode`, because `request_body` sends `model`, `state` and `questions`
  only. So the strict parser (`_RESPONSE_FIELDS`, `_ANSWER_FIELDS`,
  `_USAGE_FIELDS`) needs no change. If a future answer did carry an unknown
  field, the parser would fail closed, the call would be a failed receipt,
  and doctor would now show it.
- **OpenRouter's extra response fields** were observed in R0's paid
  readiness call (`docs/reviews/router-r0.md`): `id`, `provider` and
  `usage.cost`. Those were for v1.1. For v1.2 only the owner's one-off check
  exists, and it reported the answer shape and cost (see "Unverified").

## Successor decision: none

The playbook asks first whether the change alters persisted meaning.

- The served model changes, but the questions, parsing, scoring, scheduling,
  projections, serving rules and replay do not.
- No stored value was produced by v1.1: no Decider call ever completed in a
  vault backup.
- Each future answer records the model that produced it in its receipt
  (`model`, `resolved_model`) and in its judgment row (`judge_model`), and
  question-set versions are unchanged.
- The only completed v1.1 call on record is R0's paid readiness check on a
  fixture copy (`docs/reviews/router-r0.md`), which stored nothing in a
  vault.
- The precedent is Plan-first transport T1 (2026-10-21), which changed the
  served model of every serving route without a successor. This is the same
  kind of change on a narrower scale, and it acts at every version.

Playbook item 4 (a default change needs a version/fingerprint decision) is
met by recomputing the snapshots.

- The code-default `openrouter_decider` profile is in the effective config
  at every version, so all 45 snapshots in `DEFAULTS_SNAPSHOT_BY_ALGORITHM`
  move.
- They were recomputed with `defaults_fingerprint_for_version`, and the
  change is recorded in the comment block above the entries.
- Items 5-8 (tables, replay, shadow rebuild, migration fixture) do not apply:
  no table, projection or replayed meaning changes.

## How the status is stored

There is no migration (251 and 252 are claimed elsewhere). Two existing
`model_call_receipts` columns are used.

- **`finish_reason`** gets `http_<status>` (for example `http_404`), or
  `network` when the request failed with no HTTP status (a timeout or
  connection error). `chatgpt_plan.py` already records its failures exactly
  this way, so readers see one convention.
- **`output_text`** gets the provider's error text: `type: message` from the
  JSON error body, at most 300 characters. It is what the endpoint answered.
  On a 200 the column holds the raw answer body, so this keeps its meaning.
- **Redaction** removes the request's own key, any `Bearer …` span, any
  `sk-…` key and any unbroken run of 32 or more `[A-Za-z0-9_-]`. It runs
  before truncation, so a cut can never leave part of a key behind. Model
  slugs survive because `.` and `/` break the run. The same redacted text is
  now the exception message, and router traces and ledger rows store
  `str(exc)`, so they no longer carry anything a provider might echo.
- **Usage stays NULL** on a rejected call: it is unknown, never zero.

## Doctor

New module `learnloop.ops.model_routes`: a pure core, `route_health`, plus
the store reader `model_route_receipts`. `ops/doctor.py` calls it whenever
the database has receipts.

- **Routes.** A route is a call purpose on one provider profile, as its root
  receipts record them, for example (`learner_gap_kind`,
  `openrouter_decider`). Child receipts belong to their root. One purpose can
  run on two profiles at once: the probability arms ask the Decider and an LLM
  under `llm_probability`, and a working arm must not hide a dead one. The
  route's model is the one its latest completed or failed call names.
  Receipt times are compared as instants, not text.
- **Facts reported for every route** (in `doctor --json` under `model_routes`):
  - provider, model and the profile's configured model;
  - number of calls;
  - the last completed call (time, provider, model);
  - failures since that call, with the time of the first and the last;
  - the last failure's `error_type`, `finish_reason` and error text;
  - when the current provider/model was first used;
  - `model_changed_since`, `superseded_by` and `flagged`.
- **Error text is shown only for transport failures** (`finish_reason`
  `http_*` or `network`). A failed parse of a paid answer never puts model
  output in the report.
- **Text output.** One line per route that failed since its last completed
  call, then a count of the rest. For example:
  `model route learner_gap_kind (openrouter_decider, perplexity/pplx-decider-v1.1-27b): last completed never; 104 failed since, last 2026-11-09T… (http_404)`
  and `model routes: N with receipts, K failed since their last completed call, M not`.
- **Flag (warning `ai:model_route_failing`).** There is no threshold. A route
  is flagged when it has failed since its provider/model last changed and
  nothing has completed since then, or it never completed at all.
  - Three things count as a change:
    - the model its calls name changes;
    - the provider profile is now configured with a model other than the
      receipts' (the route then waits for its next call, which shows what
      the new model does);
    - the purpose moved to another profile, so that all of this route's
      calls come before the other profile's first call (`superseded_by`).
  - A started, interrupted or truncated call counts as a call. It neither
    recovers a route nor resets what is known about it.
  - So after this lands, the owner's v1.1 failures appear as facts, not
    flags, until the first v1.2 call. If that call fails too, the route is
    flagged.
- **Desktop.** The palette's "doctor" reads runtime health, not
  `run_doctor`, so there is no desktop mirror and no new UI.

## What each feature did while the Decider failed

These paths come from the code, checked at the call sites. Every failure was
caught, and nothing crashed.

| Purpose | Fallback while the Decider failed | Seen by the learner |
|---|---|---|
| `learner_gap_kind` | Tier 1 (`decider_judgments.py` status `unavailable`): the context model's reading decided the kind (`diagnosis/text_gaps/tier1.py`). For stuck answers, one LLM call on `learner_gap_reader`. With no reading, the kind was `unread` and no action was taken. A ledger row has verdict `unavailable`, and `learner_text_gaps.chooser = context_model`. | No |
| `learner_gap_same_prerequisite`, `learner_gap_same_belief` (and `learner_gap_prerequisite_needed`) | The pair was marked `failed`. The LLM judge on route `learner_gap_judge` decided instead (`tier1.py`). If that also failed, the reading was deferred. The ledger has a `failed` row and then the LLM's row. | No |
| `ad_item_forecast` (`llm_v3:decider`) | No replacement. A `forecast_receipts` row was written with status `failed`, p NULL and a `<key>:failed:<time>` key (`adaptive_difficulty/outside.py`). The separate `llm_v3:llm` forecaster ran as usual. Forecasts are never a serving input. | No |
| `ad_feature_audit` | The ledger got `unavailable`. The LLM judge on route `ad_feature_audit` judged instead, with `rationale.fallback = "unavailable"` (`feature_audit.py`). | No |
| `reader_intent` | Code only: the action fell back to Ask (`ask_answer_directly`), status `fallback`, ledger `unavailable` (`reader/reader_intent.py`). Each failed call was settled as sent, so it used up one of the day's `max_calls_per_day`. | **Yes:** "(LearnLoop's model couldn't choose, so this asks)" (`IntentBox.tsx`) |
| `hint_chooser` | `fallback_choice` (`hints/chooser.py`) served the item's authored hints first, then `next_step` from the `hint_writer` LLM route; the workbench used its taken choice. Ledger `unavailable`. `help_assists.chooser = fallback`, propensity 1, `chooser_reason = unavailable`. | A normal hint, with no notice found |
| router (`router_decider` route, purpose `router_decision`) | The free listing check failed first, giving `unreachable`, so no paid call was sent. The Decider's mixture share went to the usual rule, and its restraint share to `insert_now`. With `sensor_source = "decider"` there was no sensor of record. `router_decisions` has `fallback = 'decider'` with its reasons. The Decider stays logged advice and comparator only, with no serving share (spec §15), unchanged. | **Yes**, in block details: "The first model couldn't be reached, so its share went to the usual rule." (`router/why.py`) |

Other purposes that reach a Decider `decide()` fail the same way, through
their own LLM fallback or by being skipped. They are `misconception_match`,
`diagnosis_link_judgment`, `field_question_classification`, the
contamination judgments, `facet_span_support`, `required_method_statement`,
`facet_identity_judgment`, `rubric_phrasing_judgment`, `llm_probability`,
`judge_readiness` and `compare_scope`.

What the outage cost:
- comparator data: no Decider forecasts, audits or router advice to compare
  against the LLM paths;
- LLM calls the Decider would have saved: the gap-judge and feature-audit
  fallbacks;
- reader intent: Ask instead of a chosen action, plus spent daily routing
  allowance;
- no change to grading, scheduling or what was served.

## Codex review

One read-only review of `a36da14a4a..6d58440b82` (gpt-6.1-sol, effort
high). Job: `~/.cache/codex-agent/jobs/20261109-125531-GB2Vs2`. It reported
six findings. It confirmed that all 45 fingerprints were recomputed
correctly, that no successor is needed under the playbook and the T1
precedent, that the parser needs no change for the documented v1.2
contract, and that no receipt consumer misreads the new failed-receipt text.
It measured about 0.62 s and 73 MiB for the reader plus the aggregation over
100k synthetic receipts.

| # | Finding | Ruling |
|---|---|---|
| F1 (medium) | Routes grouped by purpose alone: the probability arms share `llm_probability`, so a working LLM arm hid a dead Decider arm. | **Fixed.** A route is now (purpose, provider). A purpose that moved to another profile is `superseded_by` it, not flagged. Tests cover interleaved arms and a superseded profile. |
| F2 (medium) | Times ordered as text: `Z`, offsets and fractional seconds sort wrongly. | **Fixed.** The core sorts by the parsed UTC instant, with read order as the tie-breaker. Tested with mixed `Z`, `.1+00:00` and `+01:00`. |
| F3 (medium) | An unfinished receipt with NULL provider/model reset the run and cleared a flag. | **Fixed.** Only completed and failed calls set the model or change the run. Others only count as calls. Tested. |
| F4 (medium) | A provider's error text could echo learner text into doctor's output. | **Declined.** The text is the provider's own error message: key-redacted, at most 300 characters, and shown only for transport failures. The request it might echo is already in the same receipt's `input_text`. The owner's rule (Nov 1) is that learner data is not private and only the grader is blinded. Doctor is the owner's own tool, and the proportionate-protection rule (Oct 24) blocks only realistic learner-visible harm. Doctor's text lines never print the error text; only the flagged issue message and `--json` carry it. |
| F5 (medium) | A network exception was redacted on the receipt but re-raised unredacted. | **Fixed.** When redaction changes the message, the caller gets the same redacted text (same exception type, context dropped). Interrupts pass through untouched. Tested with an injected transport echoing a synthetic key. The built-in urllib transport already sent only the exception class. |
| F6 (low) | The template comment cites this record before it was committed, and "no v1.1 call ever completed" ignores R0's paid readiness call on a fixture copy (`router-r0.md`). | **Fixed.** The record is committed. The claim now says no call completed in the owner's vault backups, in the template comment, the router spec and this record. |

Not acted on: Codex noted the reader loads every root receipt rather than
streaming. At the measured 0.62 s and 73 MiB for 100k receipts, doctor does
not need streaming.

## Tests

All runs were targeted, inside a 5G memory scope with at most `-n 6`. The
orchestrator runs the full gate.

- **Core set: 546 passed, 7 skipped.** Run after the fix round. It covers:
  - the Decider client, judge routes, Tier 1 Decider and Decider landing;
  - the router R2b tests (agreement, requests, serving);
  - the doctor tests, including KM1 and identifiability, and the new route
    health tests;
  - receipt owners, exactness and derivation, and forecast receipts;
  - config refactor, architecture, registry audit and the CLI help snapshot;
  - probability CLI and prep, facet-identity composition, method phrasing
    and required-method authority.
- **Snapshot and fingerprint set: 978 passed, 12 skipped, 3 xfailed.** These
  are the 49 files that read `DEFAULTS_SNAPSHOT_BY_ALGORITHM`, a defaults
  fingerprint or a frozen digest.
  - On the first run, eleven successor tests failed. Each freezes an older
    main's effective defaults and hashes them.
  - Each now undoes the decider model first, with
    `tests.helpers.undo_decider_v12`, the same way they drop later keys.
- **Every test that imports a changed fake: 2136 passed, 1 failed, 4 skipped**
  (154 files). The one failure was one of the eleven above, fixed and rerun
  in the snapshot set.
- **`lint-imports --no-cache`:** 43 contracts kept.
- **References.**
  - `module_validate.py` passes. The new module has its note, and the
    catalog and package maps count it.
  - `db_validate_reference.py`: the citations this branch moved were
    corrected (`Config - ai`, `plan`, `diagnosis`, and the regenerated
    `probe`, `recall_coverage` and `scheduler` notes).
  - Eight findings remain, all citing sidecar files this branch does not
    touch. They are on main already.
  - The rest of the full regeneration (about 390 notes changed only in
    `source_commit`, plus older drift in table notes) was not committed.

## Unverified

- No live or paid call was made. v1.2's OpenRouter response key set
  (`id`, `provider`, `usage.cost` and nothing else) is assumed from R0's v1.1
  observation and the owner's 200. If OpenRouter adds a usage field (for
  example `cost_details`), the strict parser fails closed, and doctor now
  shows that route failing.
- The route-health output was not run against the owner's real receipts. A
  backup-API copy of `~/learnloop-backups/20261109-copy` could not be opened
  from the sandbox, so the 104 and 14 counts are the owner's figures.
- `model_changed_since` compares the profile's configured model with the
  receipt's model string. A provider whose client reports a different
  spelling than its profile would read as changed, and its flag would be
  suppressed. The code-default decider profile and the receipts use the same
  string.
- `SettingsScreen.test.tsx` changed only a mocked string, and vitest was not
  run.
