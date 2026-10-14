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
