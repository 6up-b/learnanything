---
title: "learnloop.followup_run.admission"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_run/admission.py"
source_paths:
  - "src/learnloop/followup_run/admission.py"
source_commit: "workspace/uncommitted @ HEAD efd894886714472c5495a6a6b87e97e8a774701a"
source_commit_timestamp: "2026-11-04T00:19:09-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_run"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.followup_run.admission module"
  - "src/learnloop/followup_run/admission.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-run"
---

# `learnloop.followup_run.admission`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_run.admission` exists within [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] to own the behavior summarized by its module contract: From an authored question to a pinned offer, with no human in the loop (spec §4.1, §5.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_run/admission.py](../../../../../../src/learnloop/followup_run/admission.py) |
| Source lines | 379 |
| Owning package | [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD efd894886714472c5495a6a6b87e97e8a774701a` |
| Commit timestamp | `2026-11-04T00:19:09-05:00` |

## Public API

- `class AdmissionFailed(RuntimeError)` ([source](../../../../../../src/learnloop/followup_run/admission.py), line 44) — No question passed the checks (§6.2).
  - `__init__(self, reason: str, *, detail: Mapping[str, Any] | None=None) -> None` (line 47; internal)
- `class OfferRefused(RuntimeError)` ([source](../../../../../../src/learnloop/followup_run/admission.py), line 53) — A hard refusal arrived at the pin (an episode conflict): nothing is served.
  - `__init__(self, reason: str) -> None` (line 56; internal)
- `class AdmittedProbe` ([source](../../../../../../src/learnloop/followup_run/admission.py), line 62)
- `blind_generator(probe: AuthoredProbe) -> Any` ([source](../../../../../../src/learnloop/followup_run/admission.py), line 72) — Bundles over the deterministic sensor's vocabulary, uniform across hypotheses.
- `manipulation_contract(probe: AuthoredProbe) -> dict[str, Any]` ([source](../../../../../../src/learnloop/followup_run/admission.py), line 109)
- `author_probe(vault: Any, repository: Repository, *, workflow: Mapping[str, Any], factor_id: str, decision: Mapping[str, Any], client: Any) -> tuple[AuthoredProbe, Any, Any]` ([source](../../../../../../src/learnloop/followup_run/admission.py), line 134) — The one authoring call for this workflow, and its output checks.
- `persist_item(vault: Any, repository: Repository, probe: AuthoredProbe, *, template: Any, card: Any, workflow_id: str | None, episode_id: str | None=None, source: str='workflow', client: Any=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/followup_run/admission.py), line 177) — The mint's persistence and single-use handling, reused (§4.1).
- `admit(repository: Repository, *, candidate_id: str, receipt: Mapping[str, Any], clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/followup_run/admission.py), line 264) — The machine admission receipt: the ladder, walked by what actually checked it.
- `withdraw_interrupted(repository: Repository, *, workflow_id: str, factor_id: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/followup_run/admission.py), line 276) — Before a retry: what an interrupted run of this workflow left is retired, its pin ended, and its candidate withdrawn, or the retry's own question would duplicate its class.
- `commission_only(vault: Any, repository: Repository, probe: AuthoredProbe, *, factor_id: str, practice_item_id: str, client: Any=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/followup_run/admission.py), line 291) — An entry or a failed lane's later generation: an active candidate, pinned by no one yet.
- `commission_and_pin(vault: Any, repository: Repository, probe: AuthoredProbe, *, workflow: Mapping[str, Any], factor_id: str, decision_id: str | None, practice_item_id: str, client: Any=None, clock: Clock | None=None) -> AdmittedProbe` ([source](../../../../../../src/learnloop/followup_run/admission.py), line 324) — Commissioning of the explicit item, machine admission, and the pinned offer.

### Module constants

- `MACHINE_REVIEWER` ([src/learnloop/followup_run/admission.py](../../../../../../src/learnloop/followup_run/admission.py), line 38)
- `SYSTEM_AXES` ([src/learnloop/followup_run/admission.py](../../../../../../src/learnloop/followup_run/admission.py), line 40)
- `OUTCOME_SCHEMA` ([src/learnloop/followup_run/admission.py](../../../../../../src/learnloop/followup_run/admission.py), line 41)

### Explicit exports

`__all__` declares:

- `AdmissionFailed`
- `AdmittedProbe`
- `MACHINE_REVIEWER`
- `OfferRefused`
- `admit`
- `author_probe`
- `blind_generator`
- `commission_and_pin`
- `commission_only`
- `manipulation_contract`
- `persist_item`
- `withdraw_interrupted`

## Internal implementation anchors

- `_template_and_card(vault: Any, repository: Repository, learning_object_id: str, clock: Clock | None) -> tuple[Any, Any]` ([source](../../../../../../src/learnloop/followup_run/admission.py), line 120)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `module`; statically calls `author_probe`, `commission_and_pin`, `commission_only`, `persist_item`, `withdraw_interrupted`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `FOLLOWUP_PROBE_PROMPT_VERSION`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `accept_probe_offer`; calls `accept_probe_offer`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `build_causal_hypothesis_set`, `transition_probe_candidate`; calls `build_causal_hypothesis_set`, `transition_probe_candidate`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_commissioning|learnloop.diagnosis.causal_probe_commissioning]] — imports `commission_probe_instrument`, `support_scores`; calls `commission_probe_instrument`, `support_scores`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `administered_surface_exclusions`; calls `administered_surface_exclusions`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `DIALOGUE_MICROPROBE_V1`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `LLM_GENERATOR_ID`, `LLM_GENERATOR_VERSION`, `applicable_families`, `ensure_instrument_card`, `family_measurement_intent`, `generated_instance_payload`, `instance_gate_errors`; calls `applicable_families`, `ensure_instrument_card`, `family_measurement_intent`, `generated_instance_payload`, `instance_gate_errors`
- [[Reference/Modules/learnloop/followup_run/authoring|learnloop.followup_run.authoring]] — imports `AuthoredProbe`, `AuthoringRejected`, `build_context`, `check_output`, `request_authored_probe`; calls `build_context`, `check_output`, `request_authored_probe`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `module`; calls `item_revision`, `register`, `retire_unbound`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f3_a_crash_after_the_pin_ends_the_pin_with_the_retired_item`
  - `test_f5_the_author_builder_itself_refuses_them_for_entry_and_need_work`

## Modification guidance

- Make changes here when the responsibility remains admission within learnloop.followup_run; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_run/admission.py](../../../../../../src/learnloop/followup_run/admission.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
