# Reader follow-ups Nov 1b

Stage `reader-followups-nov1b`, branch `reader/followups-nov1b` (base `0d607bdfe9`, worktree `learnanything-merge2`).

This stage builds four queued follow-ups. Each one has fail-first tests named after the finding it closes.

- **No migration, no successor, no config key. Kill switches unchanged.**
- One new module constant, `figures/labels.py:MIN_SEGMENT_WORDS`, a `keep` structural bound. It is registered in `params/parameter_registry.py`.
- Nothing here changes persisted meaning (scoring, scheduling, projections). It does change what a figure author's answer goes through: label-like free text now costs the existing repair call, then is stripped or refused, and a stored figure's label-like text is left out when presented (Codex review, below). That changes no evidence, so it takes no successor; the figure tiers' existing kill switches cover it.
- No paid or live model call was made. Every model in the tests is a fake. The adapter test runs the real `openai` SDK and httpx over httpcore with a fake network backend, so no socket is opened.
- No Python ran outside pytest except `lint-imports`.
- Cost: $0.

## 1. RW5d §9b.4: the free-text label rule (P2b ruling R2)

P2b ruling R2 (`reader-rw5d-p2b-manim.md`): "The §9b.4 rule that model-written free text (narration, title, what it
shows, assumptions) must not read like a check label is not built in this stage. Queued as a follow-up to land before
the owner gives the Manim opt-in."

### What changed

**The label module** (`src/learnloop/figures/labels.py`, new) holds the code-owned label constants:

- the grammar figure's and the abstention badges;
- the sketch badges;
- the Manim badges and its closing check line;
- the check lines' lead, `CHECKS_LEAD = "checked by LearnLoop:"`.

These constants moved out of `figures/service.py` and `figures/rich.py`. Both modules re-export them under their old names, as the same objects, so every caller and test is unchanged.

**Matching.** `label_like(text)` matches structurally, built from those constants and not from a hand-written phrase list:

- **Label phrases.** Each label as written, plus each segment of three or more words that states a check, plus its positive form (*not checked against the book* → *checked against the book*). The full set is `LABEL_PHRASES`.
- **Check words in badge form.** The check words are `CHECK_LABEL_WORDS = ("checked", store.VERIFIED_RW5C)`. Badge forms are:
  - bracketed: *(checked)*, *[verified]*;
  - their own `·` segment or the whole text: *Verified*;
  - a lead: *Checked: …*;
  - naming LearnLoop: *verified by LearnLoop*, *LearnLoop has checked*.
- **Check-mark glyphs** (`CHECK_GLYPHS`: ✓ ✔ ☑ ✅ 🗸).
- **Normalization.** Matching ignores case, Unicode compatibility forms (NFKC) and separator variants (`·•∙⋅`).
- **Not matched:** ordinary prose, such as *check that the area is 1*, *we verified the identity by expanding*, *the box is checked*, *the sum is verified.*

**Fields read.** The rule reads:

- what each figure shows (`demonstrates`) and its assumptions, on the spec, the sketch, the V3 quick figure and the rich brief;
- the tier reason (`why_this_tier`, and V2's `why_not_spec`);
- a Manim figure's `title` and `narration_md`.

Labels drawn inside the frame (series, readout and probe labels) are not this rule's fields. Identifiers stay with the sketch tier's `impersonates`.

**On a hit, the repair call.** `label_problems` writes the problem in code's words, naming the field and the phrase. It becomes the author's (or rich author's) problem for its one existing repair call. The check runs before the spec, sketch or brief is parsed (`figures/service.py:_free_text`, called right after the status is read). No new call is added: this is the existing second attempt.

**Still violating after the repair**, each tier keeps its existing path:

- **Spec or sketch:** shown without that text (`_without_label_text`, `labels.strip_json`). `demonstrates` is emptied, a label-like assumption is dropped, and every other field is kept.
- **Tier reason:** replaced with `REASON_WITHHELD`, in code's words, on the `figure_tier` receipt.
- **Rich brief:** stripped the same way before the rich job receives it.
- **Manim title or narration:** `manim_figure.parse_figure` raises `ManimFigureError`, so the rich job's second attempt fails like any invalid answer. The figure is stored `failed` and never shown. This applies to the render-repair path too. The narration is the video's transcript, its text alternative, so a cut transcript is not shown.

### Tests

`tests/test_figure_label_wording.py`, 37 tests.

**The matcher**, tested without the rest of the pipeline:

- 15 label-like texts are matched, and 10 ordinary or empty texts are not (`REASON_WITHHELD` included);
- the vocabulary comes from the code-owned constants, and the tiers' constants are the module's own objects;
- desktop parity: `FIGURE_FRAME`, `SKETCH_FRAME` and `RICH_FRAME` carry the same strings, and every badge-slot or check-line string the desktop draws reads as a label;
- problems are in code's words;
- `strip_json` leaves out only label-like text.

**The tiers** (`test_r2_…`):

- spec demonstrates: repair with code's words;
- spec still label-like: shown without the text, stored without it;
- ordinary prose costs no repair call;
- sketch still label-like: shown without the text;
- a label-like `why_not_spec`: repaired, then left out of the receipt;
- rich brief and `why_this_tier`: repaired, then left out (the brief reaches the rich author stripped);
- Manim title: repair with code's words;
- Manim narration still label-like: refused, stored failed, no render.

**Fail-first evidence.** The behaviour tests were run with the rule switched off: a pytest plugin replaced `label_problems` with "no problems" and `strip_json` with identity. **7 of 8 `r2_` tests failed.** The one that passed is the ordinary-prose test, which is expected.

## 2. RW5d P2b R1: failed corrections from the durable rows

P2b ruling R1 (F14 remainder): "Queued follow-up: discover unresolved correction failures from durable figure/request
rows instead of the job window."

### What changed

- **New lookup.** `rich.rich_job_for_request(repository, request_id)` finds the newest `figure_rich` job of a figure request, over the whole queue. It uses `newest_ingest_job_by_payload`, as `rich_job_for_quick` already does.
- **`service.rich_pending`** now walks the window's jobs first, then the jobs of every stored failed rich correction for this source whose job is outside the window. A stored failed correction is a row that is `failed`, has a rich spec version, a `supersedes_id` and a `request_id`. Its job is found by the request id and must correct the same figure.
- **Same rules as before.** Both kinds of job go through the existing loop: input dedupe, a newer correction of the same figure speaks for it, `_failed_correction`'s still-newest check, the show-me switch and held-out passages.
- **Retry.** "Try again" (`rich_revision_retry`) already read the job by id over the whole queue.
- **`list_figures`** never read the window. The fuller line's job comes from `rich_job_for_quick`, which reads the whole queue. It is unchanged.
- **The window itself** (newest 500) still serves the pending and waiting lines, which are recent by nature.

### Tests

`tests/test_figure_rich_failed_correction_durable.py`, 4 tests. The window is aged out by filtering the job out of `rich_jobs`, which is what 500 newer rich jobs would do.

| Test | Before the fix |
|---|---|
| a failed correction outside the window still lists its line, with the same reason, job and retry | **failed** |
| a failed correction of a fuller version, outside the window | **failed** |
| a newer in-window correction still speaks for the figure | passed |
| a replaced failed correction lists nothing | passed |

## 3. Chat adapter R1: no environment proxy on the metered adapter

Reader follow-ups Nov 1 ruling R1 (F2 remainder): "Queued as a follow-up: bound nested TLS I/O, or set trust_env=False
on the metered adapter's client."

### What changed

- **The choice:** `trust_env=False`. LearnLoop has no proxy configuration key (`AIProviderConfig` has no proxy field, and neither does the config schema), so this follows the brief's rule: no explicit key, so drop the environment proxy.
- **Where.** `OpenAIChatProviderClient` builds the SDK's `DefaultHttpxClient(trust_env=False, verify=httpx.create_ssl_context(trust_env=True))`. This also covers `openrouter`, which subclasses it.
- **Effect:**
  - HTTPS_PROXY, HTTP_PROXY, ALL_PROXY and `.netrc` no longer route or authenticate a metered call. It connects straight to `base_url`, under the total deadline.
  - The certificate store still follows SSL_CERT_FILE or SSL_CERT_DIR (else certifi), exactly as before. Only the proxy is dropped.
- **Documentation:**
  - the comment at the construction site, including what to do if a proxy setting is ever added: pass it explicitly and bound nested TLS reads per `recv` first;
  - one paragraph in `docs/learnloop-architecture-vault/Workflows/Configure AI Providers.md`.
- **Unchanged:** `_DeadlineNetworkStream`. Its TLS-in-TLS path is now reachable only through an explicit proxy, and none exists.

### Tests

In `tests/test_chat_total_transport_deadline.py`:

- **`test_nov1_r1_an_environment_proxy_no_longer_routes_metered_calls[https-443 | http-80]`.** Every proxy variable is set to `http://proxy.invalid:3128`. The call must connect to `deadline.invalid` itself and answer.
  - Before the fix, both cases **failed** with `[('proxy.invalid', 3128)] == [('deadline.invalid', …)]`: the call went to the proxy.
  - The fake server now records each connection's `(host, port)`.
- **`test_nov1_r1_the_certificate_store_still_follows_the_environment`.** A missing SSL_CERT_FILE still fails construction, as it did before.

## 4. RW4d fresh path: a "no such passage" pin is not persisted

Reader follow-ups Nov 1, open item 3: "a fresh comparison stores every dropped pin, including one dropped as 'no such
passage' … the stored comparison is withheld whole (fail closed) for every later reader."

### What changed

- `source_retrieval/compare.py` stores `dropped_pins` without the `NO_SUCH_PASSAGE` pins, the same rule as the reuse path (Codex review F1).
- `result.dropped_pins` still carries the pin, so the current call is still refused whole (`comparison_withheld`).

### Tests

`tests/test_whole_comparison_reuse_provenance.py::test_nov1_open_item_3_a_fresh_comparisons_pin_naming_no_passage_is_not_persisted`:

- the fresh call with a pin naming no passage fails closed;
- the stored row has no "no such passage" pin;
- `withheld_comparisons` does not withhold it;
- a later call reuses it.

Before the fix it **failed**: the stored row had `"reason": "no such passage"`.

## Gate (this step; the full suite runs once, in the landing gate)

Every pytest ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run at a time. `TMPDIR` was outside the worktree, and no live call was made. The doc scripts ran under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No frontend, `src-tauri`, schema, migration or DB/connection code changed, so npm, vitest, cargo and the durability lane do not apply.

- **Environment:** `uv sync --extra dev --extra mobile` then `uv pip install pypdfium2`: ok.
- **`uv run lint-imports --no-cache`:** **36 kept, 0 broken**.
- **Targeted pytest:** `uv run pytest -q -n 6 -p no:cacheprovider` over 112 files: **2711 passed, 3 skipped, 2 xfailed, 0 failed** (4:52).
  - The 112 files are every file added or changed here, every test file that imports or drives `figures.service`, `figures.rich`, `figures.manim_figure`, `figures.labels`, the figure, rich or sketch fixtures, `source_retrieval.compare` or `compare_sources`, `openai_chat`, plus the contract tests (architecture, registry audit, tracked fixture databases, public-tip guards, SQLite file copies).
  - The first run of the same set had **1 failure**, `test_figures_final_round.py::test_the_view_sends_closed_property_check_keys_only`. That test pinned the old behaviour: a figure whose `demonstrates` is *"matches the book's equation (checked)"* was shown as written. It now gives that answer twice and asserts the text is left out, while the panel label inside the frame is kept. Rerun alone: 7 passed. Then the whole set again: clean, as above.
- **References** (the line citations this branch moved):
  - `db_generate_reference.py` regenerated 358 table notes; `db_validate_reference.py` errors `[]`.
  - `desktop_generate.py` added the new test's cross-boundary contracts to `FigureInline`, `RichFigure` and `SketchFigure`. `desktop_validate.py` passes byte for byte (297/297 TS + 5/5 Rust).
  - `validate_vault.py` passes (1365 notes, 1363/1363 reachable).
- **Fail-first evidence** is recorded under each item above.

Test files run: test_agent_run_tokens.py, test_ai_config.py, test_ai_runtime.py, test_ai_single_request.py, test_approach_maps.py, test_architecture.py, test_attempt_ai_flow.py, test_attempt_completion.py, test_batch3_landing.py, test_chat_total_transport_deadline.py, test_compare_keep_switch_off.py, test_compare_sources_keep.py, test_compare_sources.py, test_config_refactor.py, test_contamination_report.py, test_curriculum_c0b_landing.py, test_deferred_regrade.py, test_diagnose_review.py, test_diagnose_review_spend.py, test_diagnosis_input_provenance_landing.py, test_diagnosis_isolation.py, test_diagnostic_augmentation.py, test_e0_review_round2.py, test_e0_review_round3.py, test_e0_review_round4.py, test_family_proposals.py, test_figure_label_wording.py, test_figure_offers.py, test_figure_predictions.py, test_figure_region.py, test_figure_revisions.py, test_figure_rich_contract.py, test_figure_rich_failed_correction_durable.py, test_figure_rich_job.py, test_figure_rich_rereview_fixes.py, test_figure_rich_review_fixes.py, test_figure_rich_rpc.py, test_figures_codex_review.py, test_figures_final_round.py, test_figures_fix_round2.py, test_figures_fix_round3.py, test_figures_fix_round4.py, test_figures_fix_round5.py, test_figures_rpc.py, test_figures_rw5b_fix_round2.py, test_figures_rw5b_review.py, test_figures_scope_redesign.py, test_figures_show_me_codex_review.py, test_figures_show_me.py, test_figure_verification.py, test_find_sources_intents.py, test_ingestion_checkpoints.py, test_interaction_signals.py, test_learner_text_gaps_review.py, test_library_ask.py, test_library_ask_review.py, test_library_exercises.py, test_lo_general.py, test_manim_figure_checks.py, test_manim_sandbox_hostile.py, test_migrations.py, test_mobile_allowlist.py, test_model_usage_report.py, test_multimodal_client.py, test_openai_chat_client.py, test_openai_embedding_client.py, test_output_budget.py, test_passage_links.py, test_plan_first_transport.py, test_practice_index_paid.py, test_probability_prep.py, test_project_cli.py, test_provider_resolution_parity.py, test_public_tip_guards.py, test_reader_ca3_codex_rereview.py, test_reader_ca3_codex_review.py, test_reader_ca3_codex_round3.py, test_reader_ca3_compare_anywhere.py, test_reader_ca3_landing_ca5a.py, test_reader_ca4_landing.py, test_reader_ca4_table_by_point.py, test_reader_compare_table.py, test_reader_find_sources_callers.py, test_reader_intentions.py, test_reader_intent.py, test_reader_rw3b_review_fixes.py, test_reader_tutor_offers.py, test_registry_audit.py, test_retrieval_interventions_write_points.py, test_router_r2b_serving.py, test_rw4d_rw3b_composition.py, test_sketch_hostile.py, test_sketch_sandbox_review.py, test_sketch_service.py, test_sketch_verify.py, test_source_ingestion.py, test_source_service_spend_envelopes.py, test_sources_merge_composition.py, test_spend_controls.py, test_sqlite_file_copies.py, test_structured_transport_parity.py, test_t6_followup_composition.py, test_t6_followup_review.py, test_tool_registry.py, test_tool_results_withhold_answers.py, test_tools_cli.py, test_tracked_fixture_databases.py, test_tui_feedback.py, test_tutor_tool_requests.py, test_ux_phase1_review_fixes.py, test_whole_comparison_provenance_surfaces.py, test_whole_comparison_reuse_provenance.py.

## Open items

1. **Owner (P2b item 2):** the Manim opt-in can now be given. R2's rule (item 1) is built and covers a Manim figure's title, narration, brief and tier reason.
2. **First-attempt figure lost.** A label hit on the first attempt spends the one repair call on the wording. If that repair then fails for another reason (numerics, a schema error), the first attempt's figure is not kept as a fallback, the same as for any other first-attempt problem. Keeping a stripped first attempt as a fallback (as the Manim pacing repair does) would be a small follow-up if it matters in practice.
3. ~~**"matches the book" is not matched.**~~ Superseded by the Codex review (F1): N-a's source-verification claim is matched on its own (`SOURCE_CLAIM_VERBS`, `SOURCE_NOUNS`).
4. **The JS half.** `js_animation`'s `html`/`js` string literals (§9b.4) wait for the JS half (G-SM14).

## Landing onto main

Branch `reader/followups-nov1b` in worktree `learnanything-merge2`, landed onto main `e9693b3700` (curriculum C2 notes, migration 229, head fixture `migration_head_229`). The orchestrator fast-forwards and pushes. No migration, no config key, no successor. No paid or live model call. Cost: $0.

### Step 0: the orchestrator's scoped verify remainder (F1), fixed

The scoped Sol verify (job `20261101-151747-gKdoDv`) found F2 and F4 closed, and F3's presentation coverage closed. It left one remainder of F1: `This curve matches **the book**.` was not matched, because the Markdown-normalized lines ran only the badge forms and not the source claim. `label_like` now also reads the text as its Markdown renders, and runs the label phrases and the source claim on it:

- emphasis, code spans, and link or image targets are dropped;
- the lines are joined without their leads.

So a claim inside formatting, or one split over a line break, is matched. 23 tests were written fail-first: before the fix, 9 failed and 14 passed (the 8 ordinary-prose negatives, plus 6 cases the plain fold already caught). After it, the wording file has 87 passed and the figure set has 850 passed. Commit `ad0b2759a6`. The full account is in the Codex review record, "Orchestrator scoped verify remainder, fixed".

### Merges

- **`6cdf5499af`: merge of main `e9693b3700`** (a merge, not a rebase).
  - Conflicts: only the generated references (358 DB table notes, 77 config field notes, the field catalog, the DB index). Main's side was taken for each, then regenerated.
  - `params/parameter_registry.py` auto-merged and keeps both sides' entries: C2's `notes.*` rules and this branch's `figure_labels:MIN_SEGMENT_WORDS`.
  - `config/template.py` did not conflict. The branch does not touch it, so no fingerprint changed.
- **`de84c79024`: regenerated after the merge**, with `.pyc` cleared first:
  - `db_generate_reference.py` wrote 360 table notes; `db_validate_reference.py` errors `[]`;
  - `desktop_generate.py` and `desktop_validate.py`: passed, 299/299 TS/TSX and 5/5 Rust, byte for byte;
  - `module_validate.py`: links all resolved;
  - `validate_vault.py`: passed, 1370 notes, 1368/1368 reachable.
- **After the gate**, main was still `e9693b3700`, so no second merge was needed.

### Gate (tree `de84c79024`)

The doc scripts and every Python run ran under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, and with `TMPDIR` outside the worktree.

- **`lint-imports --no-cache`:** 37 kept, 0 broken.
- **Full pytest** (`flock /tmp/learnloop-fullsuite.lock`, 10G scope, `-n 8 --dist worksteal`): **23453 passed, 0 failed**, 90 skipped, 47 xfailed (38:47). Nothing needed a rerun.
- **Durability lane** (`-m durability`, 5G, `-n 6`): **179 passed**, 1 skipped.
- **Owner lane** (`-m owner_vaults`, 5G, `-n 6`): `LEARNLOOP_OWNER_VAULTS` named fresh backup-API copies (`copy_tree_with_databases`) of `learnanything-ad1/fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}`, in the gitignored `fixtures-local/landing-nov1b/`.
  - **83 passed, 2 failed, 4 skipped**, as expected.
  - The 2 failures are the known pre-existing owner-data ones: `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies::…[arxiv_v2]`.
- **Frontend** (this branch has no frontend change; main's merge brought 12 `apps/` files): `npm install` ok, `typecheck` ok, whole vitest (`--maxWorkers=4`, 5G) **247 files, 2367 tests passed**, `frontend:build` ok.
- **cargo:** not run. `src-tauri` is identical to main.

### Smoke (fresh owner copies, `fixtures-local/landing-nov1b-smoke/`)

**Setup:**

- Fresh backup-API copies of the three mvp035 owner copies.
- Every AI route at the `127.0.0.1:9` blackhole, with the key variables unset.
- `env -i` with an empty `HOME`, `CODEX_HOME` and config directory.
- An audit hook logs every process start and socket connect, and refuses non-loopback connects and Codex process starts.
- Main's code (`e9693b3700`) against the branch's (`de84c79024`), each a `git archive` with `migrations/`.
- On each copy: `upgrade` mvp-0.35 → mvp-0.40 (head 229), a primary load, `rebuild-derived-state`.
- Nothing was requested, rendered or built. No Manim or bwrap ran.

**Results:**

- **Today and the daily plan** are byte-identical, main against branch:
  - linear_algebra: 525266 B and 84705 B;
  - probability: 740827 B and 124030 B;
  - arxiv_v2: 344204 B and 32442 B.
- **`reader.figures`** listings and `reader.prompt_contract` show 0 differences on 9 real readings (3 + 2 + 4). These copies hold no stored figure, so every listing was empty on both sides. The stored-figure presentation path is covered by the F3 and remainder tests.
- **Proxy probe.** The real `OpenAIChatProviderClient` made one metered call attempt to `http://127.0.0.1:9/v1`, with `HTTPS_PROXY`, `HTTP_PROXY` and `ALL_PROXY` (both cases) set to `http://proxy.invalid:3128`.
  - Branch code: it connected only to `('127.0.0.1', 9)`, three attempts (the call and its retries). No lookup or connect touched `proxy.invalid`.
  - Main's code, as a control: it looked up `proxy.invalid` and made no connect, so the probe can tell the two apart.
  - Both ended with `CodexUnavailable: Connection error.`
- **`rebuild --shadow`** on the branch's copies: facet, mastery and schedule are 0/0/0 on all three, and the live database is unchanged.
- **Receipts:** 0 new `model_call_receipts` across the 12 databases compared with base.
- **Audit log:** 5 lines (two `uname -p` starts, three `127.0.0.1:9` connects), 0 refused, no non-loopback socket.

### Rulings (orchestrator)

- R1: "F3's request for a version/successor is rejected: the rule changes which figure text is shown, not evidence (spec §15); the figure tiers' existing switches cover it. Accepted."
- R2: "Stored Manim videos are shown with label-like transcript lines replaced in LearnLoop's own words rather than withheld (proportionate bar); flagged to the owner."
- R3: "With the §9b.4 label rule landed, the standing Manim opt-in is the owner's to give."

### Open items

1. **Owner:** the standing Manim opt-in is now the owner's to give (R3). R2 (stored Manim transcripts shown with label-like lines replaced, not withheld) is flagged to the owner.
2. **Keeping a stripped first attempt as a fallback.** A label hit on the first attempt spends the one repair call. If that repair then fails for another reason, the first attempt's figure is not kept (open item 2 above). This is a small follow-up if it matters in practice.
3. **`js_animation` literals.** The `html`/`js` string literals (§9b.4) wait for the JS half (G-SM14, which failed its probe; the sketch tier stays off).
