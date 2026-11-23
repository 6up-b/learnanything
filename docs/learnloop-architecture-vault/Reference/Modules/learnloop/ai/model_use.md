---
title: "learnloop.ai.model_use"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/model_use.py"
source_paths:
  - "src/learnloop/ai/model_use.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.model_use module"
  - "src/learnloop/ai/model_use.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.model_use`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.model_use` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: The learner's one OK before LearnLoop uses AI at all, and the check that holds every request to it.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/model_use.py](../../../../../../src/learnloop/ai/model_use.py) |
| Source lines | 218 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class ModelUseNotAccepted(Exception)` ([source](../../../../../../src/learnloop/ai/model_use.py), line 43) — No OK yet: nothing was sent.
  - `__init__(self, message: str=WAITING_MESSAGE) -> None` (line 49; internal)
- `class Acceptance` ([source](../../../../../../src/learnloop/ai/model_use.py), line 55)
- `acceptance_in(consent: Mapping[str, Any] | None, *, where: str='library') -> Acceptance | None` ([source](../../../../../../src/learnloop/ai/model_use.py), line 64) — The OK a ``[ai.consent]`` table holds: the one-OK record first, else an earlier OK of the connection sheet; None when it holds neither (an upload's OK alone, or nothing).
- `record_updates(granted_at: str) -> dict[tuple[str, ...], Any]` ([source](../../../../../../src/learnloop/ai/model_use.py), line 86) — The config updates that write the one OK (``settings_store.apply_config_updates``).
- `machine_acceptance() -> Acceptance | None` ([source](../../../../../../src/learnloop/ai/model_use.py), line 127) — The OK mirrored into this computer's ``ai_defaults.toml`` (any library's, said once here).
- `recorded_acceptance(vault_root: Path | str | None) -> Acceptance | None` ([source](../../../../../../src/learnloop/ai/model_use.py), line 135) — The OK that covers model use for the library at ``vault_root`` now: its own, else this computer's.
- `accepted(vault_root: Path | str | None) -> bool` ([source](../../../../../../src/learnloop/ai/model_use.py), line 146)
- `class AcceptanceLookup` ([source](../../../../../../src/learnloop/ai/model_use.py), line 150) — The live lookup a client carries (:func:`bind`): the OK for its library, read when asked.
  - `__init__(self, vault_root: Path | str | None) -> None` (line 153; internal)
  - `__call__(self) -> bool` (line 156; internal)
- `bind(client: Any, vault_root: Path | str | None) -> Any` ([source](../../../../../../src/learnloop/ai/model_use.py), line 160) — Hold every request ``client`` makes to the OK for the library at ``vault_root``.
- `client_waiting(client: Any) -> bool` ([source](../../../../../../src/learnloop/ai/model_use.py), line 167) — Whether ``client`` is bound to a library that has no OK yet.
- `admit(client: Any) -> None` ([source](../../../../../../src/learnloop/ai/model_use.py), line 175) — Refuse a request before anything is sent when ``client``'s library has no OK.
- `waiting(vault_root: Path | str | None, client: Any | None=None) -> bool` ([source](../../../../../../src/learnloop/ai/model_use.py), line 182) — For a caller about to start model work: an injected client answers for itself (bound or not); otherwise the library's OK decides.
- `require(vault_root: Path | str | None, client: Any | None=None) -> None` ([source](../../../../../../src/learnloop/ai/model_use.py), line 191)

### Module constants

- `MODEL_USE_KEY` ([src/learnloop/ai/model_use.py](../../../../../../src/learnloop/ai/model_use.py), line 29)
- `MODEL_USE_FLOW` ([src/learnloop/ai/model_use.py](../../../../../../src/learnloop/ai/model_use.py), line 30)
- `DISCLOSURE_VERSION` ([src/learnloop/ai/model_use.py](../../../../../../src/learnloop/ai/model_use.py), line 31)
- `EARLIER_OK_FLOW` ([src/learnloop/ai/model_use.py](../../../../../../src/learnloop/ai/model_use.py), line 33)
- `UPLOAD_ONLY_KEYS` ([src/learnloop/ai/model_use.py](../../../../../../src/learnloop/ai/model_use.py), line 35)
- `WAITING_CODE` ([src/learnloop/ai/model_use.py](../../../../../../src/learnloop/ai/model_use.py), line 37)
- `WAITING_MESSAGE` ([src/learnloop/ai/model_use.py](../../../../../../src/learnloop/ai/model_use.py), line 38)
- `LOOKUP_ATTRIBUTE` ([src/learnloop/ai/model_use.py](../../../../../../src/learnloop/ai/model_use.py), line 40)

### Explicit exports

`__all__` declares:

- `Acceptance`
- `AcceptanceLookup`
- `DISCLOSURE_VERSION`
- `EARLIER_OK_FLOW`
- `LOOKUP_ATTRIBUTE`
- `MODEL_USE_FLOW`
- `MODEL_USE_KEY`
- `ModelUseNotAccepted`
- `UPLOAD_ONLY_KEYS`
- `WAITING_CODE`
- `WAITING_MESSAGE`
- `acceptance_in`
- `accepted`
- `admit`
- `bind`
- `client_waiting`
- `machine_acceptance`
- `record_updates`
- `recorded_acceptance`
- `require`
- `waiting`

## Internal implementation anchors

- `_consent_in_file(path: Path, where: str) -> Acceptance | None` ([source](../../../../../../src/learnloop/ai/model_use.py), line 102) — The OK in one TOML file, read again only when the file changed (an unreadable or missing file holds none).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `module`; statically calls `bind`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `module`; statically calls `admit`
- [[Reference/Modules/learnloop/ai/providers/openrouter_video|learnloop.ai.providers.openrouter_video]] — imports `module`; statically calls `admit`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `module`; statically calls `bind`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `module`; statically calls `accepted`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `module`; statically calls `require`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `module`; statically calls `recorded_acceptance`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `module`; statically calls `require`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `module`; statically calls `bind`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `module`; statically calls `bind`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `module`; statically calls `waiting`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `module`; statically calls `waiting`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `module`; statically calls `waiting`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `module`; statically calls `accepted`, `record_updates`, `recorded_acceptance`
- [[Reference/Modules/learnloop_sidecar/handlers/passage_union|learnloop_sidecar.handlers.passage_union]] — imports `module`; statically calls `waiting`
- [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]] — imports `module`; statically calls `waiting`
- [[Reference/Modules/learnloop_sidecar/polled_jobs|learnloop_sidecar.polled_jobs]] — imports `ModelUseNotAccepted`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `ModelUseNotAccepted`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `global_ai_defaults_path`; calls `global_ai_defaults_path`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `os`, `pathlib`, `threading`, `tomllib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]], [[Reference/Modules/learnloop/ai/providers/openrouter_video|learnloop.ai.providers.openrouter_video]], [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] and 13 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ai_ok_world.py](../../../../../../tests/ai_ok_world.py) — direct import
- [tests/test_one_ai_ok.py](../../../../../../tests/test_one_ai_ok.py) — direct import
  - `test_a_fallback_provider_is_held_to_the_same_ok`
  - `test_an_unchecked_model_call_in_any_rpc_answers_waiting_for_ok`
  - `test_no_adapter_sends_anything_before_the_ok_and_each_proceeds_once_it_is_given`
  - `test_the_ok_is_read_live_from_the_library_and_from_this_computer`
  - `test_the_one_record_and_an_earlier_ok_count_and_nothing_else_does`
  - `test_the_readers_ask_waits_for_the_ok_and_sends_nothing`
  - `test_the_video_adapter_asks_for_the_ok_too`
- [tests/test_reader_rd3a_search.py](../../../../../../tests/test_reader_rd3a_search.py) — direct import
  - `test_waiting_for_the_ok_to_use_ai_runs_nothing_by_meaning`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/model_use.py](../../../../../../src/learnloop/ai/model_use.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
