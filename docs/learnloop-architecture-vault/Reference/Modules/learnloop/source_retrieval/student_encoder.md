---
title: "learnloop.source_retrieval.student_encoder"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/student_encoder.py"
source_paths:
  - "src/learnloop/source_retrieval/student_encoder.py"
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
  - "learnloop.source_retrieval.student_encoder module"
  - "src/learnloop/source_retrieval/student_encoder.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.student_encoder`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.student_encoder` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: The adopted query student behind the resolver's hook (spec_local_contextual_retrieval_v1 §5.1, §7.1 "Serving", §9.3; P2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/student_encoder.py](../../../../../../src/learnloop/source_retrieval/student_encoder.py) |
| Source lines | 545 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class StudentUnavailable(RuntimeError)` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 66) — The query process could not answer (refused, failed its canary, or late).
- `adoption_path(data_root: Path, space_id: str) -> Path` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 71)
- `checkpoint_dir(data_root: Path, space_id: str, sha: str) -> Path` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 75)
- `read_adoption(data_root: Path, space_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 81)
- `student_space(manifest: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 89) — The space a student is trained for: the grouped local space of this epoch (its KD documents).
- `bases_manifest(data_root: Path) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 101)
- `adopted_encoder(vault: LoadedVault, *, data_root: Path | None=None) -> 'StudentEncoder | None'` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 109) — ``spaces.LOCAL_QUERY_ENCODER``: the adopted student, or None (never raises).
- `runtime_dir(sha: str) -> Path` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 148)
- `server_command(env_python: Path, job: Path, *, unit: str) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 153) — The query process inside its own transient scope with the 4G cap (keep).
- `request(socket_path: Path, payload: Mapping[str, Any], *, timeout_s: float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 169) — One JSON-line request over the query process's Unix socket.
- `class StudentEncoder` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 187) — ``LocalQueryEncoder`` for the adopted checkpoint (lazy start, idle exit, measured starts).
  - `__init__(self, vault: LoadedVault, *, space_id: str, checkpoint_sha: str, checkpoint: Path, base_name: str, base_dir: Path, env_python: Path, data_root: Path, spawn: Callable[..., Any] | None=None, clock: Callable[[], float]=time.time, sleep: Callable[[float], None]=time.sleep) -> None` (line 192; internal)
  - `device_class(self) -> str` (line 214; public)
  - `encoder_id(self) -> str` (line 221; public)
  - `status(self) -> dict[str, Any]` (line 226; public)
  - `_alive(self, status: Mapping[str, Any]) -> bool` (line 235; internal)
  - `ready(self) -> bool` (line 247; public)
  - `start_times(self) -> list[float]` (line 251; public)
  - `_record_start(self, seconds: float) -> None` (line 258; internal)
  - `job(self) -> dict[str, Any]` (line 265; public)
  - `start(self) -> bool` (line 278; public) — Start the query process unless one is up or starting (one starter at a time, by a lock).
  - `_write_status(self, value: Mapping[str, Any]) -> None` (line 326; internal)
  - `wait_decision(self, remaining_s: float, weight_share: float) -> tuple[bool, float]` (line 331; public)
  - `_await_ready(self, deadline: float | None) -> None` (line 334; internal)
  - `encode(self, texts: Sequence[str], *, deadline: float | None=None, receipt_id: str | None=None) -> list[list[float]]` (line 348; public)
- `yield_gpu_students(*, wait_s: float=SP.YIELD_WAIT_S, sleep: Callable[[float], None]=time.sleep, clock: Callable[[], float]=time.monotonic) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 383) — Before an exclusive GPU job's start checks (Codex review F11): every query process serving on the GPU is asked to shut down and waited for (at most ``wait_s``, keep), so the 9B worker, the teacher targets and the trainer never find it resident.
- `replay_path(vault_root: Path) -> Path` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 420)
- `queue_replay(vault: LoadedVault, *, receipt_id: str, texts: Sequence[str], vectors: Sequence[Sequence[float]], encoder_id: str, checkpoint_sha: str) -> int` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 439) — Queue a served query for the next teacher replay (never fails the search).
- `pending_replay(vault_root: Path, *, limit: int=SP.REPLAY_MAX_QUERIES) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 460) — Unreplayed queries, newest first, at most ``limit`` (the GPU budget, keep).
- `replay_due(vault_root: Path, *, now: datetime | None=None) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 473) — A replay-only batch is due when queries wait and the last replay is older than REPLAY_EVERY_HOURS.
- `record_replay(vault_root: Path, results: Sequence[Mapping[str, Any]]) -> int` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 489)
- `replay_report(vault: LoadedVault, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 500) — §9.3 on real traffic: the student's teacher top-10 agreement, and the signalled spans each list held in its top 10 (biased toward the delivered student list: a lower bound on the teacher's advantage).

### Module constants

- `REPLAY_FILE` ([src/learnloop/source_retrieval/student_encoder.py](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 53)
- `_REPLAY_SCHEMA` ([src/learnloop/source_retrieval/student_encoder.py](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 54)
- `_ENCODERS` ([src/learnloop/source_retrieval/student_encoder.py](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 62)
- `_ENCODERS_LOCK` ([src/learnloop/source_retrieval/student_encoder.py](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 63)

### Explicit exports

`__all__` declares:

- `REPLAY_FILE`
- `StudentEncoder`
- `StudentUnavailable`
- `adopted_encoder`
- `adoption_path`
- `bases_manifest`
- `checkpoint_dir`
- `pending_replay`
- `queue_replay`
- `read_adoption`
- `record_replay`
- `replay_due`
- `replay_path`
- `replay_report`
- `request`
- `runtime_dir`
- `server_command`
- `student_space`
- `yield_gpu_students`

## Internal implementation anchors

- `_spawn(command: Sequence[str], *, env: Mapping[str, str], log: Path) -> Any` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 163)
- `_pid_alive(pid: Any) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 371)
- `_replay(vault_root: Path) -> sqlite3.Connection` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 424)
- `_text_key(text: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/student_encoder.py), line 433)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `replay_due`; statically calls `replay_due`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `pending_replay`, `record_replay`, `replay_due`, `yield_gpu_students`; statically calls `pending_replay`, `record_replay`, `replay_due`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `StudentEncoder`, `adoption_path`, `bases_manifest`, `checkpoint_dir`, `read_adoption`, `replay_report`, `student_space`; statically calls `StudentEncoder`, `adoption_path`, `bases_manifest`, `checkpoint_dir`, `read_adoption`, `replay_report`, `student_space`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `adopted_encoder`; statically calls `adopted_encoder`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/retrieval_spaces|learnloop.db.stores.retrieval_spaces]] — imports `feedback_rows`; calls `feedback_rows`
- [[Reference/Modules/learnloop/local_embeddings/identity|learnloop.local_embeddings.identity]] — imports `query_encoder_id`; calls `query_encoder_id`
- [[Reference/Modules/learnloop/local_embeddings/launcher|learnloop.local_embeddings.launcher]] — imports `gpu_lock_path`, `launch_environment`; calls `gpu_lock_path`, `launch_environment`
- [[Reference/Modules/learnloop/local_embeddings/pins|learnloop.local_embeddings.pins]] — imports `module`; calls `data_root`
- [[Reference/Modules/learnloop/local_embeddings/student_decision|learnloop.local_embeddings.student_decision]] — imports `module`; calls `should_wait`
- [[Reference/Modules/learnloop/local_embeddings/student_pins|learnloop.local_embeddings.student_pins]] — imports `module`; calls `bases_manifest_path`, `space_home`
- [[Reference/Modules/learnloop/local_embeddings/student_server|learnloop.local_embeddings.student_server]] — imports `module`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `local_reason`, `local_spaces`; calls `local_reason`, `local_spaces`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `block_record_id`; calls `block_record_id`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `models_off`; calls `models_off`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `fcntl`, `hashlib`, `json`, `os`, `pathlib`, `socket`, `sqlite3`, `subprocess`, `threading`, `time`, `typing`, `uuid`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]], [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]], [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/query_student_fakes.py](../../../../../../tests/query_student_fakes.py) — direct import
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iv_with_the_student_off_rw5ds_grounding_retrieval_is_p1s`
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_a_client_that_gives_up_never_stops_the_query_process`
  - `test_a_due_replay_is_scheduled_for_a_fully_indexed_library`
  - `test_a_resident_gpu_student_yields_before_an_index_batch`
  - `test_a_student_that_never_becomes_ready_is_late_within_the_time_box_never_a_hang`
  - `test_consecutive_owner_decisions_resolve_to_their_evaluation`
  - `test_every_recipe_trains_measures_and_writes_a_pinned_checkpoint`
  - `test_only_the_current_producers_pinned_families_are_provenance`
  - `test_priors_never_decide_and_no_evaluation_changes_serving_by_itself`
  - `test_reevaluation_strata_come_from_the_checkpoint_training_families`
  - `test_the_adopted_student_starts_lazily_serves_and_queues_the_teacher_replay`
  - `test_the_kill_switches_take_the_student_and_the_replay_out`
  - `test_the_nightly_index_batch_replays_the_queued_queries_with_the_teacher`
  - `test_the_owner_revoke_is_a_judgment_ledger_verdict`
  - `test_the_query_process_answers_over_its_unix_socket_and_exits_idle`
  - `test_the_resolver_serves_the_adopted_student_and_never_waits_for_a_zero_weight_cold_start`
  - `test_the_scheduled_candidate_is_recommended_adopted_and_a_lost_reevaluation_recommends_withdrawal`

## Modification guidance

- Make changes here when the responsibility remains student encoder within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/student_encoder.py](../../../../../../src/learnloop/source_retrieval/student_encoder.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
