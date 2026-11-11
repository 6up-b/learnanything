---
title: "learnloop.source_retrieval.query_student"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/query_student.py"
source_paths:
  - "src/learnloop/source_retrieval/query_student.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.query_student module"
  - "src/learnloop/source_retrieval/query_student.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.query_student`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.query_student` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: P2, the query student: teacher targets, the screen, recipes, seeds, evaluation and adoption (spec_local_contextual_retrieval_v1 §7.1, §7.2, §9.3, §10 P2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/query_student.py](../../../../../../src/learnloop/source_retrieval/query_student.py) |
| Source lines | 1555 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `context(vault: LoadedVault, root: Path | None=None) -> tuple[dict[str, Any] | None, str | None, str | None]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 116) — ``(setup manifest, student space id, None)`` or ``(None, None, why)``.
- `home(root: Path, space: str) -> Path` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 127)
- `p2_meter(root: Path, space: str) -> GpuMeter` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 131) — P2's capped meter (6 GPU-hours, keep): teacher targets, every run, failed runs included.
- `setup_bases(*, root: Path | None=None, run: Callable[..., Any]=subprocess.run, adopt: Mapping[str, Path] | None=None, verify_weights: bool=True, dry_run: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 161) — Record the two pinned bases: adopted in place (verified, never moved) or downloaded at their pinned revisions into the data root, every file checked by size and SHA-256.
- `bank_fingerprint(bank: Sequence[Mapping[str, Any]]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 209) — The bank's identity: every question's id, retrieval text and labels (evidence sets, answer spans and the judged blocks, when the bank records them).
- `targets_index(space_home: Path) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 219)
- `teacher_vectors(space_home: Path, ids: Sequence[str], *, kind: str='queries') -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 226) — ``{id: unit float32 vector}`` from the int8 shards (rows that never arrived are absent).
- `all_rows(root: Path, space: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 232) — Every stored question of every vault for this space.
- `missing_bank_targets(index: Mapping[str, Any], bank: Sequence[Mapping[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 241) — Bank questions with no teacher vector for their CURRENT text.
- `screen_current(index: Mapping[str, Any], bank: Sequence[Mapping[str, Any]]) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 248)
- `screen_leakage(index: dict[str, Any], targets_dir: Path, rows: Sequence[Mapping[str, Any]], bank: Sequence[Mapping[str, Any]]) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 253) — The teacher-cosine leakage guard (keep, may only tighten), bound to ONE complete bank (Codex review F2): it runs only when every question of this bank has its teacher vector, screens every synthetic question that has a target against all of them, and records the bank's fingerpri…
- `eligible_rows(rows: Sequence[Mapping[str, Any]], index: Mapping[str, Any], bank: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 280) — THE admission rule, shared by training and evaluation (Codex review F2, F7): a question with a teacher target that this bank's complete leakage screen passed.
- `run_targets(vault: LoadedVault, repository: Repository, *, bank_path: Path | None, root: Path | None=None, launcher: Callable[..., dict[str, Any]] | None=None, meter: GpuMeter | None=None, preflight: Callable[[], list[str]] | None=None, locks: Callable[[], Any]=gpu_locks, dry_run: bool=False, yielder: Callable[[], Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 293) — One 9B batch in query mode for every question and bank question still owed a target.
- `teacher_vectors_from(index: Mapping[str, Any], targets_dir: Path, ids: Sequence[str], kind: str) -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 406)
- `documents(vault: LoadedVault, repository: Repository, space: str, *, exclude: Set[tuple[str, str]]=frozenset(), extraction_ids: Sequence[str] | None=None) -> tuple[list[str], np.ndarray]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 464) — The grouped space's current covered blocks: ``(record ids, unit float32 matrix)``.
- `training_candidates(vault: LoadedVault, repository: Repository, space: str, *, bank: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]], by_extraction: Mapping[str, str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 474) — The permitted training candidate manifest (Codex review F3): the covered blocks of the TRAINING families only (no held-out family, no source without training questions), with every contextual window that holds a bank support left out.
- `complete_evidence(ranked: Sequence[str], sets: Sequence[Sequence[tuple[str, str]]], k: int=10) -> float | None` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 490) — 1 when some evidence set's every required block is in the top ``k``, 0 when none is, None when unlabelled.
- `unjudged_blocks(ranked: Sequence[str], question: Mapping[str, Any], k: int=10) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 499) — The top ``k``'s blocks the label protocol never judged for this question: neither in an evidence set nor in the bank's ``judged`` list (a bank without one judged nothing else).
- `judged_outcome(ranked: Sequence[str], question: Mapping[str, Any], k: int=10) -> float | None` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 508) — Complete evidence, with unjudged material latent (Codex review F5, re-review F5, spec §9.1): when no set completes but the top ``k`` holds a block the label protocol never judged for this question, that block may be another complete set: the outcome is unknown (None, imputed by…
- `read_ledger(space_home: Path) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 526)
- `effective_budgets(n_train: int) -> list[int]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 530) — The nested budgets the data allows today (a budget above the data is the data).
- `teacher_quality(space_home: Path, *, seed: int=0) -> tuple[np.ndarray, str]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 549) — The teacher's bank quality draws: its evaluated outcomes when evaluation ran, else E1's committed aggregates.
- `exchange_rates(space_home: Path, mu: float) -> tuple[SD.ExchangeRate, SD.ExchangeRate]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 565) — ``(lambda, nu)``: the seeded priors (``student_decision.PRIOR_BASIS``) updated by every recorded owner choice (Codex review F14).
- `record_owner_choice(space_home: Path, *, rate: str, dq: float, cost: float, s: float, accepted: bool, what: str, judgment_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 578) — One costed owner choice, an observation of ``rate`` (``lambda``: quality per dollar; ``nu``: quality per GPU-hour) in the logistic choice model ``P(accept) = sigma((dq - rate * cost) / s)`` (spec §9.1: "every owner decision between costed options is an observation").
- `run_actions(runs: Sequence[Mapping[str, Any]], *, teacher_q: np.ndarray, box_s: float) -> list[SD.Action]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 600)
- `choose(runs: Sequence[Mapping[str, Any]], *, teacher_q: np.ndarray, box_s: float, mu: float, lam: SD.ExchangeRate | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 610)
- `next_step(ledger: Mapping[str, Any], *, n_train: int, has_positives: bool, teacher_q: np.ndarray, box_s: float, hours_left: float, dataset: str='', lam: SD.ExchangeRate | None=None, nu: SD.ExchangeRate | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 616) — The schedule's next run, or ``{"step": "evaluate", ...}`` when the chosen recipe has its seeds.
- `campaign(vault: LoadedVault, repository: Repository, *, root: Path, space: str, bank: Sequence[Mapping[str, Any]], persist: bool=True) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 707) — One vault's training campaign against one bank (Codex review F7, F8, F9): the eligible questions (:func:`eligible_rows`), their families in the vault's persisted family mapping, the permitted training candidates, and the dataset fingerprint that names every run and checkpoint ma…
- `build_dataset(vault: LoadedVault, repository: Repository, *, root: Path, space: str, budget: int, bank_path: Path, out_dir: Path, camp: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 747) — The run's files: the nested training budget, the development split, the permitted training candidates and the teacher's top-k over them (no held-out family, no bank-tainted window, Codex review F3), each query's same-source hard negatives, the temperature.
- `trainer_job(spec: Mapping[str, Any], *, space: str, base_dir: Path, data_dir: Path, out_dir: Path, temperature: float, plan_id: str, dataset_fingerprint: str='', training_families: Sequence[str] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 795)
- `install_checkpoint(output: Mapping[str, Any], *, root: Path, space: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 817) — Pin the trained checkpoint by SHA-256 under the space and move it into place.
- `run_next(vault: LoadedVault, repository: Repository, *, bank_path: Path | None, root: Path | None=None, launcher: Callable[..., dict[str, Any]] | None=None, meter: GpuMeter | None=None, preflight: Callable[[], list[str]] | None=None, locks: Callable[[], Any]=gpu_locks, dry_run: bool=False, yielder: Callable[[], Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 837) — Plan (and unless ``dry_run``, run) the schedule's next training run.
- `comparison_fingerprint(bank_print: str, record_ids: Sequence[str], question_ids: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 954) — What makes two arms' outcomes comparable (re-review F4): the bank's labels (its fingerprint), the candidate units every arm ranks (the space's current block ids) and the in-scope questions.
- `run_training_families(camp: Mapping[str, Any], budget: int) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1006) — Every family a run at ``budget`` on this campaign consumes (Codex final verify F19): its training and development queries' families and the families of the candidate blocks its KD top-k, positives and hard negatives come from (and the candidate manifest's own families).
- `checkpoint_training_families(run: Mapping[str, Any], camp: Mapping[str, Any], *, root: Path, space: str) -> tuple[set[str] | None, str]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1021) — ``(families, basis)``: the families the checkpoint actually trained on (F19).
- `bank_scope(bank: Sequence[Mapping[str, Any]], repository: Repository) -> tuple[list[dict[str, Any]], dict[str, int]]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1065) — The questions every arm is scored on (Codex review F4): those whose every evidence and answer span lies in THIS vault's current corpus.
- `evaluate(vault: LoadedVault, repository: Repository, *, bank_path: Path | None, root: Path | None=None, encoder_factory: Callable[[str], Any] | None=None, arms: Mapping[str, Path] | None=None, dry_run: bool=False, checkpoint: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1122) — A checkpoint on the bank beside the teacher (and any adopted incumbent), every arm on the same frozen questions, candidate units and labels; §9.3's expected utility over the MEASURED actions RECOMMENDS.
- `owner_choice(vault: LoadedVault, repository: Repository, *, accept: bool, root: Path | None=None, checkpoint: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1387) — The owner's answer to an evaluation's recommendation (``student adopt`` / ``student reject``).
- `revoke(vault: LoadedVault, repository: Repository | None=None, *, root: Path | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1443) — The owner's per-checkpoint kill switch: the serving pointer is removed, the owner's verdict appended to ``judgment_ledger`` (when the vault's repository is given) and the ledger.
- `status(vault: LoadedVault, repository: Repository, *, root: Path | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1469) — Doctor's view of P2: bases, data, targets, runs, the meter, the adoption and the replay.
- `plan(vault: LoadedVault, repository: Repository, *, bank_path: Path | None, root: Path | None=None, client: Any | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1500) — The whole P2 dry run: what each owner command would do, with time, GPU and plan-call estimates.

### Module constants

- `SHARD_SIZE` ([src/learnloop/source_retrieval/query_student.py](../../../../../../src/learnloop/source_retrieval/query_student.py), line 99)
- `DEV_MAX` ([src/learnloop/source_retrieval/query_student.py](../../../../../../src/learnloop/source_retrieval/query_student.py), line 101)
- `MIN_TEMPERATURE` ([src/learnloop/source_retrieval/query_student.py](../../../../../../src/learnloop/source_retrieval/query_student.py), line 103)
- `E1_AGGREGATES` ([src/learnloop/source_retrieval/query_student.py](../../../../../../src/learnloop/source_retrieval/query_student.py), line 107)
- `TRAINER_SCRIPT` ([src/learnloop/source_retrieval/query_student.py](../../../../../../src/learnloop/source_retrieval/query_student.py), line 112)
- `_DOWNLOAD` ([src/learnloop/source_retrieval/query_student.py](../../../../../../src/learnloop/source_retrieval/query_student.py), line 153)
- `LABEL_MODEL` ([src/learnloop/source_retrieval/query_student.py](../../../../../../src/learnloop/source_retrieval/query_student.py), line 922)
- `PRIOR_ALTERNATIVE` ([src/learnloop/source_retrieval/query_student.py](../../../../../../src/learnloop/source_retrieval/query_student.py), line 924)
- `LABEL_ACQUISITION` ([src/learnloop/source_retrieval/query_student.py](../../../../../../src/learnloop/source_retrieval/query_student.py), line 928)
- `JUDGMENT_TASK` ([src/learnloop/source_retrieval/query_student.py](../../../../../../src/learnloop/source_retrieval/query_student.py), line 931)
- `TRAINING_FAMILIES_PROVENANCE` ([src/learnloop/source_retrieval/query_student.py](../../../../../../src/learnloop/source_retrieval/query_student.py), line 994)

### Explicit exports

`__all__` declares:

- `E1_AGGREGATES`
- `JUDGMENT_TASK`
- `LABEL_MODEL`
- `SHARD_SIZE`
- `all_rows`
- `bank_fingerprint`
- `bank_scope`
- `build_dataset`
- `campaign`
- `choose`
- `comparison_fingerprint`
- `complete_evidence`
- `context`
- `documents`
- `effective_budgets`
- `eligible_rows`
- `evaluate`
- `exchange_rates`
- `install_checkpoint`
- `judged_outcome`
- `missing_bank_targets`
- `next_step`
- `owner_choice`
- `p2_meter`
- `plan`
- `read_ledger`
- `record_owner_choice`
- `revoke`
- `run_next`
- `run_targets`
- `screen_current`
- `screen_leakage`
- `setup_bases`
- `status`
- `targets_index`
- `teacher_quality`
- `teacher_vectors`
- `trainer_job`
- `training_candidates`
- `unjudged_blocks`

## Internal implementation anchors

- `_read_json(path: Path, default: Any) -> Any` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 137)
- `_write_json(path: Path, value: Any) -> None` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 144)
- `_sha(*parts: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 205)
- `_documents(vault: LoadedVault, repository: Repository, space: str, *, exclude: Set[tuple[str, str]]=frozenset(), extraction_ids: Sequence[str] | None=None) -> tuple[list[str], np.ndarray, list[str], int]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 424) — ``(record ids, unit float32 matrix, each row's extraction, blocks left out as bank-tainted)``.
- `_ledger_path(space_home: Path) -> Path` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 522)
- `_spec_key(spec: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 536)
- `_completed(ledger: Mapping[str, Any]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 541)
- `_tried(ledger: Mapping[str, Any]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 545)
- `_rates_path(space_home: Path) -> Path` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 561)
- `_late_counts(run: Mapping[str, Any], box_s: float) -> tuple[int, int]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 594)
- `_vault_rows(root: Path, space: str, vault: LoadedVault) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 703)
- `_incomplete_bank(camp: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 738)
- `_outcomes(bank: Sequence[Mapping[str, Any]], vectors: Mapping[str, np.ndarray], record_ids: Sequence[str], matrix: np.ndarray) -> tuple[dict[str, float | None], dict[str, list[str]]]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 934) — ``(outcomes, owed)``: each question's judged outcome, and for each latent one the retrieved blocks its label protocol never judged (what a label batch would judge).
- `_evaluation_candidate(ledger: Mapping[str, Any], step: Mapping[str, Any], adoption: Mapping[str, Any] | None, checkpoint: str | None, *, root: Path, space: str) -> tuple[Mapping[str, Any] | None, str, str | None]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 962) — ``(run, basis, refusal)``: the checkpoint to evaluate (re-review F17).
- `_consumed_queries(camp: Mapping[str, Any], budget: int) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 997) — ``(train, dev)``: the queries a run at ``budget`` gives the trainer (the nested budget, the development split's first ``DEV_MAX`` by rank).
- `_strata(bank: Sequence[Mapping[str, Any]], question_families: Mapping[str, set[str]], trained_families: set[str] | None) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1049) — The reported strata.
- `_monthly_query_usd(repository: Repository) -> float` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1083)
- `_judge(repository: Repository, *, checkpoint: str, space: str, judge: str, verdict: str, evidence: Mapping[str, Any], score: float | None=None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1094) — An auditable verdict in ``judgment_ledger`` (handoff §0.6: every verifier or owner verdict; Codex review F15).
- `_withdraw(repository: Repository, *, root: Path, space: str, adoption: Mapping[str, Any], judge: str, why: str, evaluation_id: str | None=None, verdict: str='withdrawn') -> str` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1109) — Remove the serving pointer (atomic) and record the verdict.
- `_is_evaluation(record: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1374)
- `_latest_evaluation(space_home: Path, checkpoint: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/query_student.py), line 1380)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `context`, `evaluate`, `owner_choice`, `plan`, `revoke`, `run_next`, `run_targets`, `setup_bases`, `status`; statically calls `context`, `evaluate`, `owner_choice`, `plan`, `revoke`, `run_next`, `run_targets`, `setup_bases`, `status`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `documents`; statically calls `documents`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/retrieval_spaces|learnloop.db.stores.retrieval_spaces]] — imports `spaces`; calls `spaces`
- [[Reference/Modules/learnloop/local_embeddings/cache|learnloop.local_embeddings.cache]] — imports `CacheUnreadable`, `VectorCache`, `cache_path`; calls `VectorCache`, `cache_path`
- [[Reference/Modules/learnloop/local_embeddings/gpu_meter|learnloop.local_embeddings.gpu_meter]] — imports `GpuBudgetExceeded`, `GpuMeter`; calls `GpuMeter`
- [[Reference/Modules/learnloop/local_embeddings/launcher|learnloop.local_embeddings.launcher]] — imports `LocksBusy`, `ScopedLauncher`, `gpu_locks`; calls `ScopedLauncher`
- [[Reference/Modules/learnloop/local_embeddings/pins|learnloop.local_embeddings.pins]] — imports `module`; calls `data_root`, `limits`
- [[Reference/Modules/learnloop/local_embeddings/setup|learnloop.local_embeddings.setup]] — imports `load_manifest`; calls `load_manifest`
- [[Reference/Modules/learnloop/local_embeddings/student_decision|learnloop.local_embeddings.student_decision]] — imports `module`; calls `Action`, `ArmOutcomes`, `aggregate_arm`, `bank_quality_draws`, `continue_training`, `decide`, `dev_quality_draws`, `difference_sd`, `late_draws`, `seeded_lambda`, `seeded_nu`
- [[Reference/Modules/learnloop/local_embeddings/student_pins|learnloop.local_embeddings.student_pins]] — imports `module`; calls `base_dir`, `bases_manifest_path`, `space_home`
- [[Reference/Modules/learnloop/local_embeddings/student_trainer|learnloop.local_embeddings.student_trainer]] — imports `base_problems`, `checkpoint_digest`, `module`, `sha256_file`; calls `base_problems`, `checkpoint_digest`, `sha256_file`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `current_extractions`; calls `current_extractions`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `build_job`, `canary_check`, `epoch_of`, `exclusive_gpu_yield`, `local_reason`, `measured_epoch`, `preflight_problems`; calls `build_job`, `canary_check`, `epoch_of`, `exclusive_gpu_yield`, `local_reason`, `measured_epoch`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `block_record_id`; calls `block_record_id`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `module`; calls `bank_supports`, `current_rows`, `data_dir`, `extraction_families`, `family_map`, `generate`, `load_bank`, `nested`, `question_families`, `stored_queries`, `vault_held_out`, `vault_key`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `StudentEncoder`, `adoption_path`, `bases_manifest`, `checkpoint_dir`, `read_adoption`, `replay_report`, `student_space`; calls `StudentEncoder`, `adoption_path`, `bases_manifest`, `checkpoint_dir`, `read_adoption`, `replay_report`, `student_space`
- [[Reference/Modules/learnloop/source_retrieval/windows|learnloop.source_retrieval.windows]] — imports `expected_keys`, `mean_vector`, `windows_by_extraction`; calls `expected_keys`, `mean_vector`, `windows_by_extraction`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `hashlib`, `json`, `math`, `os`, `pathlib`, `shutil`, `subprocess`, `typing`, `uuid`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/query_student_helpers.py](../../../../../../tests/query_student_helpers.py) — direct import
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_a_failed_run_blocks_the_schedule_with_its_reason`
  - `test_a_newly_held_out_familys_older_rows_leave_training`
  - `test_a_run_is_reused_only_on_the_dataset_it_learned`
  - `test_a_targets_run_interrupted_before_the_bank_shards_admits_no_question`
  - `test_consecutive_owner_decisions_resolve_to_their_evaluation`
  - `test_dry_runs_never_write_the_family_mapping`
  - `test_every_recipe_trains_measures_and_writes_a_pinned_checkpoint`
  - `test_only_the_current_producers_pinned_families_are_provenance`
  - `test_priors_never_decide_and_no_evaluation_changes_serving_by_itself`
  - `test_reevaluation_strata_come_from_the_checkpoint_training_families`
  - `test_targets_are_one_metered_query_batch_with_the_canaries_and_the_cosine_guard`
  - `test_targets_refuse_a_drifted_teacher_and_wait_for_a_busy_gpu`
  - `test_the_default_base_loader_is_called_with_its_keyword_only_device`
  - `test_the_owner_revoke_is_a_judgment_ledger_verdict`
  - `test_the_pinned_families_are_every_family_the_run_consumed`
  - `test_the_schedule_screens_both_bases_then_recipes_then_seeds_by_expected_utility`
  - `test_the_scheduled_candidate_is_recommended_adopted_and_a_lost_reevaluation_recommends_withdrawal`
  - `test_the_serving_checkpoint_is_reevaluated_on_corrected_labels`
  - `test_the_trainer_job_and_manifest_pin_the_training_families`
  - `test_the_whole_p2_dry_run_starts_nothing_and_estimates_time_gpu_and_plan_calls`
  - `test_training_candidates_hold_training_families_only_and_no_bank_tainted_window`
  - `test_unjudged_retrieved_material_is_latent_never_a_miss`

## Modification guidance

- Make changes here when the responsibility remains query student within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/query_student.py](../../../../../../src/learnloop/source_retrieval/query_student.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
