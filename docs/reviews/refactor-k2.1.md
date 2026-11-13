# Refactor K2.1: one checkpoint helper

Branch `refactor/k2.1-checkpoint-helper`, based on main `aaf144f8ce`. Step K2.1 of arc K
(`docs/specs/refactor_strategy_v3.md` §2.17), specified in `docs/reviews/k2-ingestion-strategy-2026-11-11.md` §3.2
from the K2 map's KB3 (§3.4 of `docs/reviews/k2-ingestion-map-2026-11-11.md`). Structure track: no served value
changes, and every existing checkpoint key keeps its bytes.

## Problem

Six model-work recipes each wrote their own load, validate, discard and save cycle and their own key policy (inventory
window, synthesis pass, legacy ingest window, the LLM facet judge, the Decider, GLM-OCR; the append call since K3.4
borrowed the pass's). Three paid call families on the synthesis path had no per-call checkpoint at all: the concept
graph structuring call, the persona fire judgements and the vault epigraphs, so a retry paid for them again.

## The helper

`ai/execution.py`, beside `content_key` and `model_settings`:

- `request_key(*, purpose, prompt, schema=None, settings=None, identity_extra=None)`: the one rendered key, what a
  request sends. The output budget is out of it; a caller adds it through `identity_extra` only where a truncated
  answer could still validate, which is the LLM facet judge's case, now stated at its key.
- `ModelCheckpoint(store, key, purpose, read)`: the cycle. `load()` reads the saved answer back through `read`, and
  discards one that raises `ValueError` (pydantic's `ValidationError` is one), `KeyError` or `TypeError`; `save()`,
  `discard()`, and `answer(call, usage=...)` for the whole cycle (the saved answer, or `call()`'s saved before it is
  returned, and whether it was reused).
- `checkpointed(store, *, purpose, prompt, schema, settings, result_model, identity_extra=None, validate=None)`:
  a `ModelCheckpoint` under `request_key`, reading its answer as `result_model` (and `validate`).
- `CheckpointStore`: the protocol a `Repository` already meets (`model_checkpoint`, `save_model_checkpoint`,
  `discard_model_checkpoint`).

No registry and no class hierarchy: one frozen dataclass and two functions.

## Sites

| site | key | cycle |
|---|---|---|
| inventory window | `inventory_window_key` → `request_key` (schema named by `schema_version` through `identity_extra`, as before) | `window_checkpoint(repo, key, spans)`: loaded at prepare, saved through the runner mailbox (jobs) or directly |
| synthesis pass | `_synthesis_pass_key` → `request_key` | `ModelCheckpoint(..., SourceSetSynthesis.model_validate)`; the preflight and `run_pass` load it, the pass saves before its budget check |
| append call and span round | `append_checkpoint_key` (unchanged, the pass key under its purpose) | `answer()`, the input ceiling inside the call |
| legacy ingest window | `legacy_window_key` (extracted; provider and model in place of settings through `identity_extra`) | `answer()` |
| LLM facet judge | `checkpoint_key` → `request_key` with the budget and effort in `identity_extra` | `_checkpoint`: load before the retry loop, save after it |
| Decider | its own key (question set, input hash, instructions, options, model), unchanged | `_checkpoint`: a saved answer for other pairs no longer reads |
| GLM-OCR window | its own key (file, pages, backend, models), unchanged | `ModelCheckpoint` over the import's repository (`ExtractionContext.checkpoints`) |
| **structuring** (new) | `structuring_checkpoint`: prompt, the schema of the result model it asks for, the run's settings | loaded before the input ceiling (a saved answer is free), saved before the output check; joins the run's saved answers |
| **persona fire** (new) | `fire_checkpoint`: prompt, judgement schema, grader settings, and the trial | `request_diagnostic_fire(..., checkpoints=, trial=)` through `answer()` |
| **epigraphs** (new) | `epigraph_checkpoint`: prompt (which lists the recent epigraphs), schema, client settings | `answer()`; a batch rejected whole is discarded |

Deleted: `_reusable_window_checkpoint`, `_checkpointed_pass`, `_checkpointed_window_proposal`, the LLM judge's inline
cycle, the Decider's `_stored_choices`, `jobs.py`'s `_ModelCheckpoints` (the extractor gets the repository as its store),
the judge's "as everywhere under the policy" comment, and the second hard-coded `purpose="inventory_window"` save.

## Judgment calls

1. **Three names, not one.** The strategy names one `checkpointed(...)` without a call argument. Two sites cannot hand
   the helper a single call: the inventory loads at prepare and saves on the runner thread after a worker's call, and
   the LLM judge loads before a retry loop and saves after it. So the cycle is an object with parts (`ModelCheckpoint`),
   the key is a function (`request_key`), and `checkpointed` is the common composition. The smaller choice that keeps
   one cycle.
2. **Site key functions stay.** `inventory_window_key`, `_synthesis_pass_key`, `append_checkpoint_key` and the judges'
   `checkpoint_key` remain, as one-liners over `request_key`, because the pins (A14, A15, K3.4, K2.1b) and
   `test_ingestion_checkpoints` call them as the production path of each site's key.
3. **Older key shapes kept through `identity_extra`.** The inventory window's `schema_version` and the legacy window's
   top-level `provider`/`model` are not the new shape; they keep their bytes as extras rather than moving (moving them
   would re-pay every saved window).
4. **The Decider keeps its own key.** It sends no prompt or schema (a question set over a state), so it cannot be a
   `request_key` with byte-identical bytes; it uses the cycle under its own key, as GLM-OCR does.
5. **The persona key carries the trial.** The gate asks one question per persona, and two personas can give the same
   answer under the same context. Keyed on the prompt alone, the second would read the first's answer, so a first run
   would pay for fewer judgements than before (and a stochastic grader's two samples would become one). With the
   trial (the `PersonaTrial.persona_id`) a first run pays exactly what it paid before. This is a second stated
   exception beside the judge's budget.
6. **`run_discrimination_gate` left unchanged.** It asks the same fire question `n_trials` times on purpose (repeated
   sampling), outside the synthesis path; it passes no store.
7. **D-9 through the helper.** The structuring answer shaped the candidate the gates judged, so its key joins
   `_SavedAnswers.pass_keys` and a gate rejection drops it with the passes. An epigraph batch whose every line the
   checks reject is discarded for the same reason. A budget failure keeps every answer, as before.
8. **The structuring checkpoint is read before the input ceiling,** as the append call's is: a saved answer costs
   nothing. On a first run nothing is saved, so the order of checks is the base's.
9. **A GLM-OCR answer saved as a non-object is now discarded** like any unreadable one (ledger K2-7, below).
10. **One test assertion changed** (below).

## Fail-first evidence

Written and run against the base sources before the source change (log kept at the step's scratch):

| test | base | tip |
|---|---|---|
| `test_model_work_checkpoints::test_a_retry_after_a_structuring_pass_reads_its_checkpoint` | 2 structuring calls (expected 1) | 1 |
| `test_persona_gate::test_a_retry_of_the_persona_gate_reads_its_fire_checkpoints` | 4 judgements over two gate runs (expected 2) | 2 |
| `test_vault_epigraphs::test_a_retry_after_a_lost_insert_reads_the_paid_batch` | 2 calls (expected 1) | 1 |
| `test_glm_ocr::test_r3_f13_a_stored_window_that_no_longer_reads_is_paid_for_once[not_an_object]` | 2 requests for two reads | 1 |

Guards (pass on both): `test_a_gate_failure_drops_the_structuring_answer_it_judged`,
`test_a_batch_with_nothing_valid_is_not_replayed`, and the cycle's own tests on an in-memory store
(`test_model_work_checkpoints`: key shape, reuse, save with usage, no save on failure, discard of an answer that no
longer reads).

## Assertions changed

- `test_graph_nomination_ingest::test_enabling_nominations_or_completing_the_index_is_a_new_bootstrap`: with the index
  incomplete nothing is nominated, so the second bootstrap's structuring request is byte-identical to the first's and
  its answer is now read back. The test read `structuring_contexts[0].registry_concept_details == []` from a call that
  no longer happens; it now asserts that no structuring call was made and that the run's usage records no nominated
  candidate (`registry_nominated_candidates` is written exactly when registry details are sent). The fact it checks,
  no nomination with an incomplete index, is the same; the third run (index complete) still asserts the details are
  sent.
- `test_glm_ocr::test_r3_f13_...` passes the repository as `checkpoints` (the deleted `_ModelCheckpoints` wrapper was
  its private name) and gains the `not_an_object` case.

## Pins

P-pins: no existing pin moved. Before the move, a commit at the base pinned the four keys that had no pin:
`K2.1a.window_key` (legacy window, through the extracted `legacy_window_key`), `K2.1b.llm`, `K2.1b.llm.reasoning_effort`,
`K2.1b.decider` and `K2.1c.window_key` (GLM-OCR). A13, A14, A15, A20, A22, K3.4 and these held through the move.
New sites: `K2.1d.key`, `K2.1d.key.nominated` (structuring), `K2.1e.key` (persona fire), `K2.1f.key` (epigraphs), and
the shapes of `ConceptGraphContext` and `VaultEpigraphContext`; `concept_graph_structuring_prompt` and
`vault_epigraphs_prompt` move from provenance-only to their sites' sources (K3.4's pattern). Every `--write` added lines
only.

## P-spend

A synthetic vault (two inventoried chapters, two shards, a structuring client that merges, persist failing on the first
build so it is retried), counted per request purpose with a recording fake, on the base and on the tip (a throwaway
test, not committed):

| run | base | tip |
|---|---|---|
| inventory, first | 2 | 2 |
| bootstrap, first (fails at persist) | 2 passes, 1 structuring | 2 passes, 1 structuring |
| bootstrap, retry | 1 structuring, 1 epigraphs | 1 epigraphs |
| append, first (fails at persist) | 1 append | 1 append |
| append, retry | 1 epigraphs | 1 epigraphs |

The bootstrap retry reuses the shards (completed-shard layer) on both. Persona fires do not occur on this fixture (its
items carry no belief-holder material); at the gate (`test_persona_gate`'s retry test) the first run pays 2 on both, the
retry 2 on the base and 0 on the tip. Epigraphs after a lost insert: 1 then 1 on the base, 1 then 0 on the tip. The
legacy window, both judges, inventory windows and GLM-OCR were already checkpointed; their first-run and retry counts
are unchanged by construction (byte-identical keys, the same cycle), held by their existing retry tests
(`test_source_ingestion`, `test_facet_identity*`, `test_model_work_checkpoints`, `test_glm_ocr`). No K3 harness applies.

## Vault

`Workflows/Import Canonical Sources.md` (the checkpoint paragraph at :189): every paid call of ingestion through one
cycle, the key, the three stated exceptions, the structuring and epigraph discards, and the three outer layers that
still answer first (K2.2 changes them). The generated references were regenerated after the source commits.

## Ledger

- **K2-7** (new, fixed): a GLM-OCR window answer saved as a non-object was skipped without being discarded, so each
  read paid again and the new answer was never kept.
- **K2-1** (queued, text extended): the persona gate's silent fallback now also covers a fire checkpoint that cannot
  be read or written (the same `except` wraps the cycle).

## Gates

- Targeted tests on `c269d8a7ee`: `scripts/affected_tests.py --base aaf144f8ce` (1,013 files; `ai/execution.py` reaches
  most of the suite) plus every added or edited test file and `test_identity_pins`, `test_retired_config_identities`,
  `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`,
  `test_structure_ratchets`: 1,016 files, `-m "not arc_close"`, 11 chunks of up to 100 at `-n 4` under the 5 GB cap
  behind the full-suite lock: 17,733 passed, 0 failed (skips and xfails as on main).
- `lint-imports --no-cache`: 42 kept. `ruff check`: clean.
- The four vault validators pass (`db_validate_reference.py`, `module_validate.py`, `desktop_validate.py`,
  `validate_vault.py`); `scripts/check_gate_partition.py`: 31,052 collected, landing 30,992 + arc_close 60.
- References regenerated once after the source commits (`c269d8a7ee`, 27 generated notes); a second run changed nothing.
- No full suite (the orchestrator's landing gate).
- Process: the first three fail-first tests were appended with a heredoc and two import lines edited by a short
  exact-pattern Python script; the GLM-OCR red run swapped the base's `glm_ocr.py` and `jobs.py` into the tree
  (`git show` into place, then restored) and the P-spend probe swapped the base's `src/` in with `git checkout
  aaf144f8ce -- src` and back; the throwaway probe test was deleted, never committed. Every other edit used the Edit
  tool.

## Open items

- **Other paid checkpoint recipes outside ingestion** (`practice_index/paid.py`, `ops/pf_calls.py`,
  `field/classification.py`, `daily_plan/router_teach_back.py`, `source_retrieval/library_ask.py`,
  `source_retrieval/passage_cues.py`) keep their own cycles; K2 is ingestion. Each could move onto the helper in its
  own arc's step.
- **K2.2** (outer caches) and **K2.3** (manifest) follow on this tip; the three outer layers still answer before these
  checkpoints.
- `handle_append_synthesis` still records `calls: 1` for a run whose call came from its checkpoint (K3.4's open item;
  usage display only).
- A structuring answer reused on a retry records its registry-merge verdicts again, as a fresh answer on a retry did
  before (no change; not checked whether `judgment_ledger` dedupes them).
