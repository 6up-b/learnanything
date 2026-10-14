# Tutor delivery fixes: what the tutor and the retrieval benchmark actually see

**Branch:** `tutor/delivery-fixes` (worktree `learnanything-ux-impl`, base main `4cf54a295` = mvp-0.22, not rebased; the orchestrator merges). Owner-approved 2026-10-13, found by the review of `docs/specs/spec_contextual_source_embeddings_experiments_v1.md` (§4.4, §8.2: "a better index may appear useless because its evidence is clipped").

**Codex review (2026-10-14):** six findings, all fixed; see `docs/reviews/tutor-delivery-fixes-codex-review.md`. Where this record and the fixes differ, the fixes hold. The notes below are updated in place: LO-linked references (F1), the backfill's obligation and job states (F3, F4), and the two kill switches (F5).

| Item | What | Commit |
|---|---|---|
| 1 | Reader Ask gets the nearest neighbours on both sides (i-1, i+1, then widening), not i-3 and i-2 | `43060df29` |
| 2 | Complete blocks for the tutor, the verifier and the labeller, within one explicit token budget whose trims are recorded | `43060df29` |
| 3 | "by Theorem 3.2", "Example 1.4.13", "Equation (3.4)" followed to the numbered block of the same extraction | `43060df29` |
| 4 | (Re-)extraction queues the source-block embedding backfill when embeddings are on; `learnloop doctor` shows dense coverage per source | `0fa0ec1b4` |
| - | DB and configuration references regenerated | `9cf99aa1b`, `4debd69e9` |
| - | First gate run's findings: the knobs classified in the parameter registry, the frozen import-edge inventory, the doctor JSON contract | `8d2deb39c` |

**No algorithm successor.** Everything here is context delivery (what one tutor answer reads) and retrieval evaluation (what the relevance judges and the T6 labeller read). Nothing is scored, scheduled, projected or served differently, no evidence or persisted meaning changes, and replay reads none of it (`docs/algorithm-change-playbook.md`: no successor unless persisted meaning changes). Live at every version behind kill switches or bounds (owner's standing ruling). **Migration:** none; **schema:** unchanged (head 201). **Config:** five modelled defaults (below); every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry (all fourteen) recomputed and the template `.pyc` cleared. **CLI help:** unchanged (doctor gains a note, no option). **Frontend / `src-tauri`:** untouched.

**Paid calls:** none ($0.00). Every model and embedding call in the tests is a house fake (`StubReaderClient`, `FakeSourceLLM`, `HashingEmbedder`). The before/after examples below ran the base code (`git archive 4cf54a295`) and this branch, read-only, against backup-API copies of the owner's vaults (`fixtures-local/tdf-linear_algebra`, `fixtures-local/tdf-probability`, made with `learnloop.db.copies.copy_tree_with_databases`). No key was read and no network was used.

Not in scope (other stages or owner questions): `find_sources`' pool choice, RW1c (Reader retrieval), GLM-OCR itself.

## Item 1: Reader neighbours

**Bug.** `reader/span_view.py` returns `previous_spans` as blocks i-3..i-1 (ascending) and `next_spans` as i+1..i+3. `tutor_qa._reader_source_spans` concatenated previous + next and stopped at `max(4, len(spans) + 2)` spans. A quoted one-block selection (quote + block = 2 spans) therefore delivered i-3 and i-2 only: never the block right before the step, nothing after it. Without a quote it delivered i-3, i-2, i-1 and still nothing after.

**Fix.** The tutor no longer reads `span_view` (its previews stay for the Reader's prev/next paging; the tutor's frozen-cycle exemption `tutor.tutor_qa -> reader.span_view` is removed from `pyproject.toml`). `tutor/context_delivery.py` reads the extraction's blocks once (`db.stores.source_block_fts.extraction_blocks`), and `neighbour_order` walks out from the selection's own ends: i-1, i+1, i-2, i+2, i-3, i+3 (`NEIGHBOUR_RADIUS` = 3 content blocks a side). Page furniture (`PageHeader`, `PageFooter`, `TableOfContents`) and empty blocks are not neighbours. A held-out neighbour (the `withheld` material, `content.sources.exam_material.held_out_material`) is skipped and counted, as before. Each neighbour carries its signed `offset`. A multi-block selection widens from its first and last block.

**Example (probability copy).** A learner selects "By Theorem 1.4.8, there are n(n-1)···(n-k+1) ways to make an ordered choice ..." in the proof of the binomial coefficient formula (`s159`) and asks.

Before (base):

| relation | span | chars | text |
|---|---|---|---|
| selected_text | s159 | 110 | By Theorem 1.4.8, there are n(n-1)···(n-k+1) ways ... |
| in_view | s159 | 402 | Proof. Let A be a set with \|A\| = n. ... |
| surrounding | s156 | 72 | the displayed formula of Theorem 1.4.15 (i-3) |
| surrounding | s157 | 0 | an empty page header (i-2) |

After:

| relation | span | offset | chars | text |
|---|---|---|---|---|
| selected_text | s159 | | 110 | (the quote) |
| in_view | s159 | | 402 | Proof. Let A be a set ... |
| referenced | s114 | | 383 | Theorem 1.4.8 (Sampling without replacement). Consider n objects ... (item 3) |
| surrounding | s158 | -1 | 38 | For k > n, we have binom(n, k) = 0. |
| surrounding | s160 | +1 | 367 | The binomial coefficient is often defined in terms of factorials ... |
| surrounding | s156 | -2 | 72 | the displayed formula |
| surrounding | s161 | +2 | 50 | binom(100, 2) = 4950 |
| surrounding | s155 | -3 | 70 | Theorem 1.4.15 (Binomial coefficient formula). For k <= n, we have |
| surrounding | s162 | +3 | 244 | can even be done by hand, whereas ... |

The tutor went from 584 characters (one of them an empty header, the block before the step missing) to 1,736: the step's statement, the theorem it cites, both sides of the step.

## Item 2: complete blocks within one budget

**Cuts removed.**

| Where | Before | After |
|---|---|---|
| Reader neighbours (tutor) | `span_view` preview, 240 chars | the complete block |
| Retrieved and pinned spans (`source_retrieval.tutor.span_context`) | 600 chars, whitespace collapsed | the complete canonical block, unchanged |
| LO-linked spans (`practice_leakage.build_cross_source_spans`, the provider-less fallback) | 600 chars | completed from the block in `tutor_qa._delivered_source_spans` (`context_delivery.hydrate`); `build_cross_source_spans` keeps its cap for its other consumers |
| Verifier (`verify._candidates`), the remediate check and `find_sources._verify` | 900 chars | `verify.judge_passage`: the complete block, whitespace collapsed, trimmed only past `source_retrieval.passage_token_budget` |
| T6 labeller (`evaluation.py`, `LABEL_PASSAGE_CHARS`) | 900 chars | the same `judge_passage` |

The 240-character preview stays where it is a UI preview: `span_view`'s `previous_spans` / `next_spans` for the Reader's paging.

**The budget.** `tutor_qa.context_token_budget` (default 24,000 tokens, the repository's chars/4 estimate, about 96,000 characters; bounds 1,000 to 400,000) bounds the source text of one tutor turn. `context_delivery.apply_budget` keeps spans in priority order. The first span that does not fit is trimmed to what is left: an exact prefix of its canonical text, cut at a word boundary in the last tenth, so offsets into it stay canonical. A remainder under 32 tokens drops it instead. Every later span is dropped. Trims and drops are recorded on the question's `source_context.delivery` (`budget_tokens`, `used_tokens`, `trimmed` with kept/total characters, `dropped`), together with the neighbours delivered and withheld and the references followed or not. The receipt is written only when it records something, so an ordinary question's row is unchanged. Priority: the learner's quote, the blocks in view, the blocks they cite, the neighbours nearest first, then what the neighbours cite. Outside the Reader the order is the chosen spans (at most `_MAX_CITATION_SPANS` = 4: the provider's picks or pins, else the LO's linked spans), then what they cite.

**The judges' budget.** `source_retrieval.passage_token_budget` (default 4,000 tokens per candidate, 16,000 characters) bounds one judged passage; a trimmed passage ends in "…" and is counted (`Verification.trimmed_passages`, the verification manifest's `trimmed_passages`, the T6 report's `passages.label_trimmed` / `verify_trimmed`). A block of at most 900 characters reads exactly as it did, so its request hash, and the verdicts already in `judgment_ledger`, still answer it; a longer block is a new request (the ledger key is the prompt's hash, so nothing stale is served). The verification's token cap now follows the prompt it sends (`verify_caps(..., input_tokens=estimated_call_tokens(prompt, ...))`, floor `VERIFY_INPUT_TOKENS_BOUND`), so complete passages cannot price a verification out of its cap. The dollar cap (`rerank_max_cost_usd`, 0.30) is unchanged. The T6 dry-run plan bounds a passage by the budget or the scope's longest block, whichever is smaller. The report's manifest is `t6-eval-v3`: its labels read complete passages.

**How much was cut** (the copies, content blocks of every extraction):

| Copy | Blocks | > 240 | > 600 | > 900 | Longest | Over the 16,000-char judge budget |
|---|---|---|---|---|---|---|
| linear_algebra | 972 | 71 | 3 | 1 | 1,766 | 0 |
| probability | 510 | 171 | 26 | 10 | 3,337 | 0 |

LO-linked tutor spans (the provider-less path), measured with `tutor_qa._source_spans` before and after `hydrate`: linear algebra 1 of 78 cut (150 characters restored), probability 8 of 63 cut (3,251 characters restored). Example, probability `lo_weight_ordered_and_unordered_bootstrap_outcomes`, `s503`: 600 of 1,917 characters, ending mid-word ("... it only mat"); now whole. Neither copy has a block past either default budget, so nothing is trimmed on them.

## Item 3: references followed

**Parsing** (`ingest/block_roles.py`, beside the lead-role regex it reuses: `_LEAD_RE` is now built from the same `_ENVIRONMENT_WORDS`).
- `numbered_label(text, block_type)`: the numbered environment a block opens. Name first ("Theorem 1.4.1 (Multiplication rule).", "**Theorem 3.2.** Let", "Lemma 2.1:"), only when the number ends the label (a name in parentheses, punctuation, a new capitalized sentence or the end; "Theorem 1.4.8 tells us ..." is a sentence about it, not its label). Number first ("1.20 definition: vector space", "★ 1.4.11 (Labeling objects)."; the kind optional). Equations tagged `\tag{3.4}` or ending "(3.4)". Proof and solution leads and table-of-contents lines are not labels.
- `numbered_references(text)`: capitalized named references ("Theorems 1.4.7 and 1.4.8", "Example 1.4.13", "Lemma 2.1", "Definition 4", "Corollary 2", "Thm. 3.2"), equations in either case ("equation (3.4)", "Eqs. (3.5)-(3.6)"), and a bare dotted number after a cue word ("by 1.32", "see 1.13", "in 1.3"), which Axler's book uses throughout. "for example 2 apples" is prose, not a reference.

**Resolution** (`context_delivery.follow_references`). Within the passage's own extraction only, never another extraction or source. A named reference matches a label of its kind (name-first or number-first); a bare number matches only a number-first label, and a bare number that names none is prose and is not recorded. The nearest occurrence before the passage wins, else the nearest after (a forward reference). The numbered block joins the context with the blocks that complete its statement (`_environment`): a heading label's body, a display equation after it, or a sentence the label block leaves open ("... The naive probability of A is" + the formula), up to `MAX_REFERENCE_BLOCKS` = 4, never into the next numbered block, heading, proof or solution. At most `MAX_REFERENCES` = 4 references per turn; more are recorded unresolved. Each block is its own `referenced` citation span (`reference`, `referenced_from`), so the citation allowlist and each span's canonical text hold.

**The exam rule.** Reader: the held-out material (the neighbours' rule). Retrieved and pinned spans (`source_retrieval.tutor.with_references`): inside the provider's scope (an item-bound scope already leaves out the item's passages, exercises and solutions), never exam material, never a passage that reproduces the practised item's answer; the provider's manifest records what was followed. LO-linked spans: the same rules over the question's own teaching scope (`source_retrieval.tutor.linked_reference_filter`, injected by the adapter; the item's links of every relation and extraction, exercise and solution regions with their bodies; Codex review F1), and none followed without it. In practice and feedback every path also refuses a block whose own lead names an exercise or a solution ("Exercise 3.2", "Problem 3.2.", "Solution:"), whatever its role hint: a transcript's captions are all `ordinary_prose`, and a hint may be missing or wrong (Codex re-review F7). A refused block is recorded unresolved with its reason. Kill switch: `tutor_qa.resolve_references = false`.

**On the copies** (every block of every extraction scanned, nothing filtered): probability's textbook extraction has 45 numbered labels; 6 distinct references resolve (Example 1.2.3, Theorems 1.4.7, 1.4.8 and 1.4.15, Examples 1.4.13 and 1.6.4) and 4 do not (end-of-chapter "Problem 26", "Problem 27", "Problem 62", "Exercise 4", which are not numbered blocks of that extraction). Axler's extraction has 40 labels; 7 resolve (1.3, 1.13, 1.30, 1.32, 1.45 and Example 1.44, mostly bare numbers) and 3 do not ("Exercise 13", "Exercise 1", "Exercise 12").

**Example (linear algebra copy).** A selection "then −v [which equals (−1)v by 1.32] is also in U" (`s343`, the subspace criterion's proof). Before: the quote, the block, then i-3 and i-2 (`s340`, and `s341` cut at 240 of 255 characters). After: the quote, the block, `1.32 the number −1 times a vector` with its statement `(−1)v = −v for every v ∈ V` (referenced, two blocks), then `s342` (-1), `s344` (+1), `s341` (-2), `s345` (+2), `s340` (-3), `s349` (+3; three furniture or empty blocks between are skipped). The extraction's own OCR dropped the italic symbols; the tutor reads what the extraction holds.

## Item 4: source vectors follow extraction

**Before.** Dense retrieval ranks an extraction only when every embeddable block has a `source_block/text` vector for `embedding.model`; only the explicit `learnloop embeddings backfill --record-kind source_block` bought them. A new import or a re-extraction (a page repair, another engine, a future GLM-OCR pass) left its source to keyword search, silently.

**After.** `content.pipeline.jobs.queue_source_vectors` is the one hook every path that completes an extraction run calls (`handle_import` for a new extraction, `handle_extraction_repair`). When `embedding.enabled`, `embedding.backfill_enabled` and `embedding.backfill_sources_on_extract` (new, default true) are all on, it queues a `source_embedding_backfill` job as its own batch, so the import never waits on it and a failure never fails the import. A job whose batch was cancelled queues nothing (the runner's existing transaction). The job (`source_retrieval.source_vectors.backfill_source_vectors`) embeds the source's **current** extraction (`corpus.current_extractions`' rule: a new top-level extraction is current; a page repair composes onto its parent, which stays current, so the repair's job finds the parent already embedded and buys nothing). It goes through the existing path, `ops.embedding_backfill.backfill_embeddings`: both switches checked again at run time (a job queued before a switch went off records `disabled` and sends nothing), caps sized to the extraction (every record, its batches, a retry of the largest batch) with the money bounded by `embedding.source_backfill_max_cost_usd` (new, default 1.00 per run; the T6 follow-up's 4,259-block book cost about $0.01), the advisory lock, `embedding_backfill` model-call receipts, content-addressed reuse (only missing hashes are bought). A model without a published price uses `source_retrieval.query_embedding_price_per_million` (the same model embeds the queries) or is refused as unpriced, as the CLI does. Codex review F3/F4: it queues only what the source is owed (`backfill_owed`), on fresh and reused extractions alike, and a queueing failure fails the import retryably. Only a complete run completes the job: lock contention and provider failures fail it retryably, an over-budget run or a vector-width conflict fails it for the owner. The job's result is aggregate only (counts, caps, charges, model), never block text; its batch shows the book's title in Activity.

GLM-OCR (parallel stage): any extractor reached through `RunnerServices.extract_ir` in these two handlers is covered. A new extraction path outside them should call `queue_source_vectors(ctx, extraction_id)` after `complete_extraction_run`.

**Doctor.** `learnloop doctor` prints one line and `--json` gains `dense_retrieval`: per source (its current extraction), embeddable blocks, blocks with a vector, `complete` / `partial` / `none` / `empty`; the three switches; whether dense retrieval is effectively on and why; whether the automatic backfill is on (`source_vectors.source_coverage`, read-only, no vector bytes read; a database before the vector store reads as nothing embedded). On the owner's vault copies (their configs predate Phase 1):

```
Dense source retrieval: off (embedding.enabled off: retrieval ranks by keyword only); 0 of 4 sources complete, 0 of 456 blocks embedded (qwen/qwen3-embedding-8b); automatic backfill after extraction: embedding.enabled is false.
```

(linear algebra: 0 of 3 sources, 0 of 699 blocks.) With embeddings switched on, a fresh import reads `on (every source has a complete set of block vectors); 1 of 1 sources complete` (`tests/test_source_vector_backfill.py::test_doctor_shows_dense_coverage_per_source`).

## Configuration

| Key | Default | Meaning |
|---|---|---|
| `tutor_qa.context_token_budget` | 24000 | Tokens (chars/4) of source text one tutor turn reads |
| `tutor_qa.resolve_references` | true | Kill switch for item 3 |
| `source_retrieval.passage_token_budget` | 4000 | Tokens of one passage a relevance judge reads |
| `embedding.backfill_sources_on_extract` | true | Kill switch for item 4 (acts only with both embedding switches on) |
| `embedding.source_backfill_max_cost_usd` | 1.00 | Money cap of one automatic source backfill run |
| `tutor_qa.expanded_delivery` | true | Kill switch for items 1 and 2 on the tutor's side: false restores the predecessor's window and cuts (Codex review F5) |
| `source_retrieval.complete_passages` | true | Kill switch for the judges' complete passages: false restores 900 characters and t6-eval-v2 (Codex review F5) |

Modelled defaults, left out of the decision-only template. All fourteen snapshots (mvp-0.9 to mvp-0.22) recomputed with `defaults_fingerprint_for_version`; each moves only because the effective config gains the keys (`tests/test_config_refactor.py` and the `test_mvp0*_upgrade.py` pins: 149 passed). The parameter registry (`params/parameter_registry.py`) classifies `tutor_qa.context_token_budget` and `embedding.source_backfill_max_cost_usd` as structural/operational (a context-size bound and a spend cap, no measurement authority); `source_retrieval.passage_token_budget` falls under the existing `source_retrieval.` operational rule and the two booleans are not numeric leaves.

## Tests (fail first)

`tests/test_tutor_delivery_fixes.py` (22) and `tests/test_source_vector_backfill.py` (7). Run against the base code (`git archive 4cf54a295 src migrations`, `PYTHONPATH` and pytest's `pythonpath` pointed at it): the delivery file 19 failed, 3 passed; the backfill file errored on import (`source_retrieval.source_vectors` does not exist). The failures are the bugs: neighbours `['s3', 's4', 's5']` (i-3, i-2, i-1) instead of i-1, i+1, ...; a multi-block selection's neighbours `['s2', 's3']`; retrieved and pinned spans and the labeller's passages cut (600, 900); no budget receipt; no `referenced` spans; the label and reference parsers missing. The three that pass on the base are guards: a held-out neighbour stays out, the kill switch, and the manifest equalling the tutor's context (they hold before and must keep holding). On this branch all 29 pass (the pinned-span test was added after ruff caught a shadowed `span_keys` in `PinnedSpanProvider`, which `tests/test_pinned_span_bridge.py` also covers).

## Gate

Run on `4debd69e9` (the code is final at `8d2deb39c`; later commits are documents), `TMPDIR` = the worktree's `fixtures-local/tmp`:

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 17 contracts kept, 0 broken (the tutor's `reader.span_view` exemption removed) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10668 passed**, 0 failed, 48 warnings (11 min 47 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10569 deselected |
| `db_generate_reference.py` / `db_validate_reference.py` | schema head 201, 319 table notes, 819 configuration leaves (was 814); errors [] |
| `validate_vault.py` | passed, 1102 notes |
| Frontend / `cargo check` | not run: nothing under `apps/` changed |

The first full run (on `9cf99aa1b`) had 10 failures, 10658 passed: the parameter registry did not classify `embedding.source_backfill_max_cost_usd` (5 registry and grading-CLI tests, and the P0 cutover test that audits the registry), the frozen function-local import inventory (a new `tutor_qa -> content.sources.exam_material` function-local import, now module level, and the retired `tutor_qa -> reader.span_view` edge, now removed from the inventory), and the doctor JSON contract (`dense_retrieval`). Fixed in `8d2deb39c`; the targeted runs before it had covered 600+ tests of the touched areas but not these three global checks.

## Notes for the owner

- **Bare-number references** ("by 1.32") are an extension of the item-3 list, for Axler's numbering. They resolve only against number-first labels of the same extraction ("1.32 the number −1 times a vector"), and an unmatched bare number is treated as prose, so "in 2.5 seconds" adds nothing unless the book has a result numbered 2.5.
- **Metered verification routes**: complete passages make a verification prompt larger only for blocks over 900 characters (10 of 510 in the probability copy). The token cap follows the prompt; the 0.30 dollar cap does not, so a pool of very long blocks on an expensive metered route could be refused for spend and fall back to the LO-linked spans (recorded as `over_budget`, as before). Codex and the ChatGPT plan are not money-capped.
- **Reader answer events** now store the complete delivered spans in `reader_answer_submitted.manifest` and `question_events.source_context.source_spans` (they stored the cut previews). The manifest is now built with the tutor's own inputs (the held-out material, the budget, the switch), so it records exactly what the tutor was given; before, it left out the held-out filter.

## Landing onto main

**Branch:** `merge/delivery-onto-main` (worktree `learnanything-merge2`), from main `56579d271` (`mvp-0.23`, LATEST; router R2a and RW3a landed). Not pushed. Owner-directed, 2026-10-14, single phase: merge `275fd5f7e`, references (provenance only) `078705224`, this record. `tutor/delivery-fixes` (`c1c3511e4`) and its worktree `learnanything-ux-impl` were not modified.

**Main since this branch's base `4cf54a295`:**
- the contextual-embeddings experiment spec (docs only);
- router R2a (`mvp-0.23`, migration 202, head fixture `migration_head_202`): the staged frame on Today, `plan_presentations` receipts, the stored learner-state card (`LearnerStateCardV1`), and the fifteen `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries `mvp-0.9`..`mvp-0.23`;
- the Reader hook extraction and RW3a margin cues: `ReaderScreen` split into hooks, `reader/reader_cues.py`, `[cues]`, three RPCs.

**Paid calls:** none ($0.00). **Migration:** none from this branch (head 202 is main's). **Algorithm version:** unchanged, no successor (replay reads none of the delivery). **Config:** the branch's seven keys beside R2a's `[router]` keys and RW3a's `[cues]`: 829 effective leaves (803 active, 7 compat, 15 dormant, 4 legacy) in 50 sections. All fifteen `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries were recomputed from the composed defaults (template `.pyc` deleted, `config/template.py` touched; a fresh process then found every stored fingerprint equal to `defaults_fingerprint_for_version`). **CLI help:** `--write` reproduced the merged snapshot (no change). **RPCs:** none added by this branch, so no mobile allowlist pin. **Frontend / `src-tauri`:** the merge changes nothing under `apps/` relative to main, so the frontend gate and `cargo check` were not run.

### Conflicts

| File | Resolution |
|---|---|
| `src/learnloop/config/template.py` (14 hunks) | Main's R2a and RW3a notes kept and the branch's notes added: its full note after RW3a's in `mvp-0.9` (now "all fourteen ... on its branch, and all fifteen again from the composed defaults when it landed after router R2a and RW3a"), its "moves it too" line in `mvp-0.10`..`mvp-0.22`, and the same line added to `mvp-0.23`, which the branch never saw. Every hash recomputed (above). |
| 372 notes under `Reference/` | Taken from main, then regenerated (below) |
| Auto-merged, both sides kept | `config/schema.py` (the branch's `tutor_qa`, `embedding` and `source_retrieval` keys beside `[router]` and `[cues]`); `params/parameter_registry.py` (the branch's structural/operational rule for `tutor_qa.context_token_budget` and `embedding.source_backfill_max_cost_usd` beside R2a's `router.card_token_budget` / `router.payload_retention_days` rule); `cli/app.py` (doctor's `dense_retrieval` note beside R2a's `upgrade --to mvp-0.23`); `pyproject.toml` and `tests/architecture_function_local_domain_imports.txt` (the retired `tutor_qa -> reader.span_view` edge removed; main added no edge to either) |

### Compositions

**Where main's new code reads source passages.** None of it reads through the tutor's delivery, and none of it brings back a tutor cut:
- **RW3a margin cues** (`reader/reader_cues.py`) read the Guide's `suggested_passages` (`reader_guidance`): span ids, LO ids and titles, never block text. *Check me* proposes an item (`reader.cue_action`) and opens it as a learner pick; it does not call the tutor. The one cut it adds, `prompt[:219]`, shortens the proposed item's prompt that `check_me_proposal` (`learnloop_sidecar/handlers/reader.py`) returns to the shell, not a tutor context.
- **R2a's learner-state card** (`daily_plan/router_card.py`, `router/card.py`) never reads source text, a reference solution, an answer key or a rubric (its own contract). It reads `question_events` only as a seven-day count (`tutor_questions`), so the complete spans this branch now stores in `question_events.source_context` do not reach the card or its `router.card_token_budget`. `router/outcomes.py` reads `question_events`' item, attempt, facets and time only.
- **`reader.span_view`** keeps its importers (`reader_dialogue`, `reader_restoration`, `diagnosis.remediation`, the provenance handler) for the Reader's paging; `learnloop.tutor` imports it nowhere (lint: the frozen-cycle contract kept with the exemption gone). `reader_dialogue.build_reader_manifest` and `ask` still go through `tutor_qa._reader_source_spans`, so the Reader's manifest is the tutor's delivered context.
- **No tutor cut reintroduced.** In the tutor paths (`tutor/tutor_qa.py`, `tutor/context_delivery.py`, `source_retrieval/tutor.py`, `source_retrieval/verify.py`, `reader/reader_dialogue.py`, the sidecar's `tutor_qa` handler) the 240- and 600-character cuts survive only as `context_delivery.PREVIEW_CHARS` / `SPAN_CHARS` behind `tutor_qa.expanded_delivery = false`, and the 900-character judge passage only as `verify.PREDECESSOR_PASSAGE_CHARS` behind `source_retrieval.complete_passages = false`. Main's code calls none of the functions whose signatures the branch changed (`span_context`, `verify_caps`, `_candidates`, `_reader_source_spans`, `build_reader_manifest`).
- **Budgets side by side.** `tutor_qa.context_token_budget` (24,000) bounds one tutor turn's source text; `source_retrieval.passage_token_budget` (4,000) one judged passage; R2a's `router.card_token_budget` (16,000) the stored card. They bound different payloads and none reads another's.

**Pipeline Map.** The Reader section gains one line on the tutor's context delivery (nearest neighbours on both sides, whole blocks under `tutor_qa.context_token_budget`, deterministic references including a bare "by 1.32", complete judge passages, the automatic source-vector backfill and doctor's dense coverage, the kill switches) and `src/learnloop/tutor/context_delivery.py` in its `source_paths`. It keeps main's R2a and RW3a edits.

### References

- `db_generate_reference.py`: schema head 202, 321 table notes, 829 configuration leaves (803 active, 7 compat, 15 dormant, 4 legacy) in 50 sections; regenerated again on the merge commit for provenance (`078705224`, `source_commit` lines only).
- Prose counts: `Configuration.md`'s catalog line and `Database.md`'s validator line, 822 became 829 (sections stay 50; the `DERIVED` callout's "19 of 321" is unchanged, no table added).
- `db_validate_reference.py`: errors `[]`.
- `validate_vault.py`: passed, 1105 notes.
- `git diff --check 56579d271 HEAD`: clean.

### Gate

Run in this worktree at `078705224` with `TMPDIR=<worktree>/fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok (the sync removes pypdfium2; the install puts back 5.14.0) |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** (the frozen-cycle contract with the tutor's `reader.span_view` exemption gone; `unmatched_ignore_imports_alerting = "error"` holds) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,892 passed, 1 failed**, 48 warnings (10 min 48 s, once the lock came free behind other worktrees' suites). The failure is main's own flake, below |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10,793 deselected, 1 warning (1 min 48 s) |
| Frontend / `cargo check` | not run: the merge changes nothing under `apps/` relative to main |
| Defaults | all 15 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` fingerprints equal to `defaults_fingerprint_for_version` in a fresh process after the recompute |
| CLI help | `python tests/test_cli_help_snapshot.py --write`: no change |
| References | see above |

**Targeted run before the gate** (on the composed tree): `test_config_refactor.py`, every `test_mvp0*_upgrade.py`, `test_tutor_delivery_fixes.py`, `test_source_vector_backfill.py`, `test_architecture.py`, `test_cli_help_snapshot.py`, `test_cli_json.py`, `test_reader_cues.py`, `test_router_card.py`, `test_mobile_allowlist.py` and the `test_param*` files: 412 passed.

**The one failure is a flake on main, not this merge.** `tests/test_reader_rw3a_landing.py::test_check_me_goes_through_the_plan_path_and_is_logged_once[planned]` (RW3a's landing test, untouched here) failed once in the full run (`decision["chosen_practice_item_id"]` `pi_svd_define_002`, the check's item `pi_svd_define_001`). Rerun alone:
- on the merge: the file 5 times, 1 failed and 4 passed;
- on main `56579d271`'s code (the `git archive` export, with pytest's `pythonpath` pointed at it and the loaded `learnloop` printed after each run): the case 12 times, **2 failed**, 10 passed.

A probe of the case (16 runs on the merge) shows why: the 25-minute plan is not the same on every run. Usually it is one block whose router decision chose `pi_svd_define_001` (14 runs), and the test passes. Sometimes that block's decision chose `pi_svd_define_002`, the Learning Object's other item, so the pick of `_001` is served by a block whose `chosen_practice_item_id` is `_002` (the failure above). Once the plan held `pi_extra_1` alone, so the pick became its own `learner_pick` block, which this case's `learner_pick == 0` assertion also rejects. The test assumes one plan shape that the plan does not guarantee. No code here touches planning, and main fails at the same rate, so it is left for RW3a's owner (Q-D1 below).

### Parity

**Copies.** Backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of this worktree's tracked `fixtures/linear_algebra` and `fixtures/probability` (`mvp-0.8`), in `fixtures-local/delivery-parity`.

**Migration, each copy by its own code** (`migration_coordinator.migrate_vault`), 47 migrations each, to head 202:
- main `56579d271`: `src`, `migrations` and `pyproject.toml`, exported with `git archive` and run on `PYTHONPATH` (a probe printed the archive's `learnloop/__init__.py`, and its `cli/app.py` has no `_dense_retrieval_note`);
- the merge: this worktree's own code.

**Runs.** On each copy, `learnloop rebuild --shadow --json` and `learnloop doctor --json`, with `LEARNLOOP_CONFIG_DIR` an empty directory.

**Result.** **0 replay differences**: the shadow rebuilds match exactly on both fixtures once ULIDs, timestamps, ids, hashes and the copy's path are set aside. Doctor differs only by the new `dense_retrieval` key; the issues are identical.

| Fixture | Replayed attempts | Facet | Mastery | Schedule | Doctor issues | Errors | `criterion:unknown_dependency` |
|---|---:|---:|---:|---:|---:|---:|---:|
| linear algebra | 70 | 22 | 6 | 47 | 106 | 1 | none |
| probability | 2 | 2 | 1 | 1 | 134 | 49 | 46 |

These are the fixtures' existing drift at `mvp-0.8`, the same figures as the RW3a landing.

**The doctor difference** (the merge only):
- linear algebra: `dense_retrieval` = `effective: false`, reason `embedding.enabled off: retrieval ranks by keyword only`, switches `embedding.enabled false`, `source_retrieval.enabled true`, `source_retrieval.dense true`, model `qwen/qwen3-embedding-8b`, `auto_backfill: embedding.enabled is false`, totals 3 sources, 699 blocks, 0 covered, 0 complete; per source (all `none`, 0 covered): the two 3Blue1Brown transcripts (217 and 142 blocks) and Axler (340). Text line: `Dense source retrieval: off (embedding.enabled off: retrieval ranks by keyword only); 0 of 3 sources complete, 0 of 699 blocks embedded (qwen/qwen3-embedding-8b); automatic backfill after extraction: embedding.enabled is false.`
- probability: the same switches and reason; totals 4 sources, 456 blocks, 0 covered, 0 complete; per source (all `none`): pset1 (25 blocks), recitation1 (17), Blitzstein and Hwang (399), the Elevator paradox article (15). Text line: `Dense source retrieval: off (embedding.enabled off: retrieval ranks by keyword only); 0 of 4 sources complete, 0 of 456 blocks embedded (qwen/qwen3-embedding-8b); automatic backfill after extraction: embedding.enabled is false.`

Both match the branch's own record above.
- `live_database.unchanged` is true on every run, and each copy's `state.sqlite` hash is the same before and after its runs (the text doctor run included).
- Doctor exits 1 on both sides, as on main.
- The tracked fixtures were only copied: `git status fixtures/` is clean.

### Safety

- No paid call, no real provider, no network. No key, credential, `.env` or `settings.env` file was read, nor `~/.config/learnloop/`.
- The main checkout was not touched. The owner's working vaults were opened only by the backup API, to copy them.
- Nothing was pushed, rebased or stashed. `tutor/delivery-fixes` and `learnanything-ux-impl` were not modified.

### Open questions for the owner (defaults applied)

- **Bare-number references** ("by 1.32"): **kept**, as built. They resolve only against number-first labels of the same extraction, and an unmatched bare number is prose. `tutor_qa.resolve_references = false` turns every reference off.
- **Verification spend on metered routes**: `source_retrieval.rerank_max_cost_usd` **stays 0.30** until real use shows refusals. Complete passages enlarge a verification prompt only for blocks over 900 characters; a refusal falls back to the LO-linked spans and is recorded `over_budget`, so it is visible when it happens. Codex and the ChatGPT plan are not money-capped.
- **Embeddings in the owner's vaults**: **stay off** until the owner turns them on. The automatic backfill acts only with `embedding.enabled` and `embedding.backfill_enabled` both on, so nothing is queued or sent today; doctor's dense-coverage line says so on each vault.
- **Budgets as listed**: `tutor_qa.context_token_budget` 24,000, `source_retrieval.passage_token_budget` 4,000, `embedding.source_backfill_max_cost_usd` 1.00 per run, `tutor_qa.resolve_references` true, `embedding.backfill_sources_on_extract` true; the kill switches `tutor_qa.expanded_delivery` and `source_retrieval.complete_passages` true.
- **Q-D1 (not this branch's).** `test_reader_rw3a_landing.py`'s `planned` case is order-dependent on main (2 of 12 runs fail on main's own code; see Gate). Recommended: RW3a's owner makes the case build a plan whose block holds only the checked item (or asserts on the block that serves the pick rather than on its decision's first choice). Not changed here, since the test and the planning code are main's.
