---
title: "learnloop.content.facet_identity.actions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/facet_identity/actions.py"
source_paths:
  - "src/learnloop/content/facet_identity/actions.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.facet_identity"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.facet_identity.actions module"
  - "src/learnloop/content/facet_identity/actions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-facet-identity"
---

# `learnloop.content.facet_identity.actions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.facet_identity.actions` exists within [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] to own the behavior summarized by its module contract: Applied facet-identity actions, the vault-level merge, rewords, and one-tap undo.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py) |
| Source lines | 2100 |
| Owning package | [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class FacetIdentityActionError(ValueError)` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 112)
  - `__init__(self, code: str, message: str) -> None` (line 113; internal)
- `class FacetAuthorityRefusal(FacetIdentityActionError)` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 118) — The meaning-authority chokepoint refused a registry write; nothing was written.
- `insert_action(connection: Any, record: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 125)
- `action_by_id(repository: Repository, action_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 130)
- `list_actions(repository: Repository, *, run_id: str | None=None, status: str | None=None, limit: int | None=200) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 135)
- `normalized_entry(entry: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 145) — An entry as ``facets.yaml`` stores it, minus the recomputed fingerprint.
- `stored_entry(entry: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 155) — The entry to write: validated, with its deterministic fingerprint.
- `file_state(record: Mapping[str, Any], facets: Sequence[Any]) -> str` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 265) — Which side of an action facets.yaml shows: ``after``, ``before`` or ``neither``.
- `facet_evidence(repository: Repository, facet_ids: Iterable[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 324) — Which of ``facet_ids`` carry graded evidence, and how much (provenance only).
- `graded_shared_criteria(vault: LoadedVault, repository: Repository, facet_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 345) — Graded criteria whose frozen contract names two of ``facet_ids`` at one capability.
- `hold_back_shared(survivor: str, retired: Sequence[str], shared: Sequence[Mapping[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 400) — Split ``retired`` into the facets that can merge and those a graded criterion holds back.
- `affected_learning_objects(vault: LoadedVault, facet_ids: Iterable[str]) -> list[str]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 435)
- `refresh_derived_state(root: Path, repository: Repository, affected: Iterable[str], *, clock: Clock | None=None) -> None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 447) — Re-sync and re-fold the affected learning objects (evidence re-keyed).
- `merge_registered_facets(root: Path, repository: Repository, *, survivor: str, retired: Sequence[str], action: str, absorb_as: str | None, origin: str, run_id: str, judge: str, judge_model: str | None, prompt_version: str | None, judgment_ids: Sequence[str]=(), detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 460) — Merge or absorb registered facets into ``survivor``, live, with an undo record.
- `record_proposed_actions(repository: Repository, actions: Sequence[Mapping[str, Any]], *, origin: str, run_id: str, proposal_id: str | None, clock: Clock | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 598) — Persist a run's in-run and attach actions with the proposal that carries them.
- `meaning_changes(before: Mapping[str, Any] | None, after: Mapping[str, Any] | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 640) — The :data:`MEANING_FIELDS` that differ between two entries of one facet.
- `record_reword(repository: Repository, *, action_id: str, facet_id: str, before: Mapping[str, Any], after: Mapping[str, Any], run_id: str, proposal_id: str | None, proposal_item_id: str | None=None, origin: str='proposal', sources: Sequence[Mapping[str, Any]] | None=None, presentation: bool=False, fields: Sequence[str] | None=None, span_support: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 649) — Record a facet version: ``facet_id``'s meaning changed from ``before`` to ``after``.
- `record_reword_confirm(repository: Repository, *, action_id: str, facet_id: str, before: Mapping[str, Any] | None, after: Mapping[str, Any], fields: Sequence[str], sources: Sequence[Mapping[str, Any]], unresolved: Sequence[str], meaning_support: Sequence[Mapping[str, Any]], message: str, run_id: str, proposal_id: str | None, proposal_item_id: str | None=None, span_support: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 726) — Hold a reword for the owner: a ``proposed`` ``reword`` action with ``detail.confirm``.
- `is_reword_confirm(record: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 784) — A reword held for (or decided by) the owner's confirm.
- `confirm_view(record: Mapping[str, Any], vault: LoadedVault | None=None, *, resolver: authority.CitationResolver | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 833) — What the owner sees of a reword confirm: the facet, the wording before and after, the sources.
- `pending_reword_confirms(repository: Repository, vault: LoadedVault | None=None, *, facet_ids: Iterable[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 886) — Rewords waiting for the owner's confirm (newest first), optionally only for ``facet_ids``.
- `reword_confirms_by_item(repository: Repository) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 908) — ``{proposal item id: confirm status}`` of every reword a proposal item held for a confirm.
- `confirm_reword(root: Path, repository: Repository, action_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1008) — The owner confirms a held reword: it applies as the owner's manual authority, with an undo.
- `keep_current_wording(root: Path, repository: Repository, action_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1183) — The owner keeps the facet's current wording: the held reword closes, nothing is written.
- `wording_key(entry: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1282) — The key of a facet entry's meaning (``authority.AUTHORITY_FIELDS``): a verdict's ``right_id``.
- `registry_save_by_id(repository: Repository, save_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1290)
- `interrupted_registry_saves(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1295) — Library saves left ``applying`` by an interrupted process (oldest first).
- `registry_save_state(record: Mapping[str, Any], current: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1302) — Which side of its file write a Library save is on: ``after``, ``before`` or ``neither``.
- `save_registry_text(root: Path, repository: Repository, text: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1429) — Write the owner's own edit of facets.yaml (the desktop Library) with facet versions.
- `facet_history(repository: Repository, facet_id: str, vault: LoadedVault | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1581) — Every action whose survivor is ``facet_id`` (rewords and merges), newest first.
- `effective_status(record: Mapping[str, Any], vault: LoadedVault) -> str` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1596) — ``proposed`` until the vault shows what the action wrote, then ``applied``.
- `describe(record: Mapping[str, Any], vault: LoadedVault | None=None, *, resolver: authority.CitationResolver | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1622) — A compact view for results, the CLI and the desktop app.
- `undo_action(root: Path, repository: Repository, action_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1711) — Restore the facets.yaml entries and ``facet_merges`` rows one action replaced.
- `append_owner_verdicts(connection: Any, record: Mapping[str, Any], *, created_at: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1793) — An undo is the owner's verdict (§0 rule 6): ``different`` for every pair of the set.
- `interrupted_actions(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1906) — Action rows left ``applying`` or ``undoing`` by an interrupted process (oldest first).
- `recover_interrupted_actions(root: Path, repository: Repository, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1915) — Finish every interrupted merge or undo from the side of the file write it stopped on.

### Module constants

- `IN_FLIGHT` ([src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 105)
- `UNDO_LIMITS` ([src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 107)
- `HELD_BACK_NOTE` ([src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 429)
- `MEANING_FIELDS` ([src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 626)
- `REWORD_TASK` ([src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 630)
- `SPAN_SUPPORT_EXCERPT_CHARS` ([src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 632)
- `REWORD_UNDO_LIMITS` ([src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 634)
- `CONFIRM_RATIONALE` ([src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 720)
- `_UNLISTED_KEYS` ([src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 800)
- `LIBRARY_RUN_ID` ([src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1239)
- `MANUAL_AUTHORITY_TASK` ([src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1244)
- `MANUAL_AUTHORITY_RATIONALE` ([src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1246)

### Explicit exports

`__all__` declares:

- `FacetAuthorityRefusal`
- `FacetIdentityActionError`
- `HELD_BACK_NOTE`
- `CONFIRM_RATIONALE`
- `MANUAL_AUTHORITY_TASK`
- `MEANING_FIELDS`
- `REWORD_TASK`
- `REWORD_UNDO_LIMITS`
- `append_owner_verdicts`
- `action_by_id`
- `confirm_reword`
- `confirm_view`
- `is_reword_confirm`
- `keep_current_wording`
- `pending_reword_confirms`
- `record_reword_confirm`
- `reword_confirms_by_item`
- `affected_learning_objects`
- `describe`
- `facet_evidence`
- `facet_history`
- `graded_shared_criteria`
- `hold_back_shared`
- `effective_status`
- `insert_action`
- `list_actions`
- `meaning_changes`
- `merge_registered_facets`
- `normalized_entry`
- `record_proposed_actions`
- `record_reword`
- `save_registry_text`
- `file_state`
- `interrupted_actions`
- `interrupted_registry_saves`
- `recover_interrupted_actions`
- `refresh_derived_state`
- `registry_save_by_id`
- `registry_save_state`
- `stored_entry`
- `undo_action`
- `wording_key`

## Internal implementation anchors

- `_facets_document(paths: VaultPaths) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 164)
- `_index(facets: Sequence[Any], facet_id: str) -> int | None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 175)
- `_write_registry(paths: VaultPaths, text: str, basis: Mapping[str, authority.Basis], *, resolver: authority.CitationResolver | None=None) -> None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 182) — Replace facets.yaml through the meaning-authority chokepoint (atomic, write-ahead safe).
- `_check_registry(paths: VaultPaths, text: str, basis: Mapping[str, authority.Basis], *, resolver: authority.CitationResolver | None=None) -> None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 201) — What :func:`_write_registry` would refuse, decided without writing (or recording) anything.
- `_merge_basis(record: Mapping[str, Any]) -> dict[str, authority.Basis]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 213) — A merge or absorb of registered facets writes their union, recomputed by the writer.
- `_restore_basis(record: Mapping[str, Any]) -> dict[str, authority.Basis]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 222) — An undo writes back exactly the entries the action recorded.
- `_restoration(repository: Repository, vault: LoadedVault, record: Mapping[str, Any], document: Mapping[str, Any]) -> tuple[str, dict[str, authority.Basis], authority.CitationResolver | None]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 244) — The facets.yaml text an undo writes, the basis each restored entry carries, and its resolver.
- `_record_parts(record: Mapping[str, Any]) -> tuple[str, list[str], dict[str, Any], dict[str, Any], dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 256)
- `_applied_document(document: dict[str, Any], record: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 284) — ``document`` with the action applied (survivor replaced, retirees removed).
- `_restored_document(document: dict[str, Any], record: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 298) — ``document`` with the action undone (survivor and retirees as before).
- `_abandon(repository: Repository, record: Mapping[str, Any], *, reason: str, clock: Clock | None=None) -> None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 570) — Withdraw an ``applying`` intent whose file write never happened.
- `_delete_merge_rows(repository: Repository, rows: Iterable[Sequence[str]]) -> int` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 590)
- `_confirm_status(record: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 790)
- `_other_changes(before: Mapping[str, Any], after: Mapping[str, Any], listed: Sequence[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 803) — What a reword changes beside its wording (aliases, error signatures, repairs...), as a confirm writes it.
- `_lazy_resolver(repository: Repository | None, vault: LoadedVault | None) -> Any` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 819) — One citation resolver for a listing, built on first use (``None`` without a repository and vault).
- `_merged_list(old: Sequence[Any], new: Sequence[Any], mine: Sequence[Any]) -> list[Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 919) — A three-way merge of one list field: today's list, less what the reword removed, plus what it added.
- `_confirmed_entry(current: Mapping[str, Any], held_before: Mapping[str, Any], held_after: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 929) — The facet as the confirm writes it: today's entry with what the held reword changed.
- `_pending_confirm(repository: Repository, action_id: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 983)
- `_reword_wording_key(old: Mapping[str, Any] | None, new: Mapping[str, Any] | None) -> tuple[dict[str, Any], str]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 997) — The wording an owner verdict on a reword is about: its meaning fields (a version), else its title and examples.
- `_confirm_source_links(facet_id: str, current: Mapping[str, Any], written: Mapping[str, Any], proposal_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1148) — The ``entity_source_links`` rows a confirm installs: the validated refs its write adds (fixed ids).
- `_install_source_links(repository: Repository, links: Sequence[Mapping[str, Any]], *, created_at: str) -> None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1159) — Install a confirmed reword's source links (idempotent: ``INSERT OR IGNORE`` on fixed ids and the unique key).
- `_reopen_confirm(repository: Repository, action_id: str, *, reason: str, clock: Clock | None=None) -> None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1173) — A confirm whose write never landed: the reword waits for the owner again (its verdict is withdrawn by its save).
- `_grant_owner_authority(connection: Any, *, facet_id: str, before: Mapping[str, Any] | None, after: Mapping[str, Any], fields: Sequence[str], save_id: str, created_at: str, origin: str='library', rationale: str=MANUAL_AUTHORITY_RATIONALE, extra: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1252) — Append the owner's ``granted`` verdict for one facet's new meaning: scope, actor, time, rationale.
- `_abandon_registry_save(repository: Repository, record: Mapping[str, Any], *, reason: str, file: str, clock: Clock | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1329) — Withdraw a Library save that never landed: its verdicts ``withdrawn``, the intent ``abandoned``.
- `_recover_registry_saves(root: Path, repository: Repository, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1345) — Settle every Library save left ``applying`` (Codex re-review 2, F7).
- `_withdraw_authority_grants(connection: Any, judgment_ids: Iterable[str], *, reason: str, created_at: str) -> None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1376) — Supersede each ``granted`` verdict of a save that never landed with ``withdrawn`` (once).
- `_parse_registry_text(text: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1400) — The edited facets.yaml as an editable document, or ``invalid_registry``.
- `_current_entries(paths: VaultPaths) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1591)
- `_later_actions(repository: Repository, record: Mapping[str, Any]) -> list[str]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1698)
- `_record_undo_intent(connection: Any, record: Mapping[str, Any], *, clock: Clock | None=None) -> None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1784) — The write-ahead undo intent: the owner's verdicts, and the row becomes ``undoing``.
- `_finish_undo(root: Path, repository: Repository, record: Mapping[str, Any], *, document: dict[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 1867) — Restore the file, drop the merge rows, refresh, mark ``undone`` (idempotent).
- `_settle_refused_undo(repository: Repository, record: Mapping[str, Any], refusal: FacetIdentityActionError, *, clock: Clock | None=None) -> None` ([source](../../../../../../../src/learnloop/content/facet_identity/actions.py), line 2039) — An ``undoing`` intent whose restoration the chokepoint refuses: back to ``applied``, the refusal kept.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/facets|learnloop.cli.facets]] — imports `FacetIdentityActionError`, `confirm_reword`, `describe`, `keep_current_wording`, `list_actions`, `undo_action`; statically calls `describe`, `list_actions`, `undo_action`
- [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]] — imports `HELD_BACK_NOTE`, `action_by_id`, `describe`, `facet_evidence`, `merge_registered_facets`, `recover_interrupted_actions`; statically calls `action_by_id`, `describe`, `facet_evidence`, `merge_registered_facets`, `recover_interrupted_actions`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `record_reword`, `record_reword_confirm`; statically calls `record_reword`, `record_reword_confirm`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `meaning_changes`; statically calls `meaning_changes`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `record_proposed_actions`; statically calls `record_proposed_actions`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `describe`, `list_actions`, `record_proposed_actions`; statically calls `describe`, `list_actions`, `record_proposed_actions`
- [[Reference/Modules/learnloop/curriculum/subject_registry|learnloop.curriculum.subject_registry]] — imports `HELD_BACK_NOTE`, `action_by_id`, `describe`, `merge_registered_facets`, `pending_reword_confirms`; statically calls `action_by_id`, `describe`, `merge_registered_facets`, `pending_reword_confirms`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `interrupted_actions`, `interrupted_registry_saves`, `recover_interrupted_actions`; statically calls `interrupted_actions`, `interrupted_registry_saves`, `recover_interrupted_actions`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `recover_interrupted_actions`; statically calls `recover_interrupted_actions`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `facet_history`; statically calls `facet_history`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_identity|learnloop_sidecar.handlers.facet_identity]] — imports `FacetIdentityActionError`, `action_by_id`, `confirm_reword`, `describe`, `keep_current_wording`, `list_actions`, `undo_action`; statically calls `action_by_id`, `confirm_reword`, `describe`, `keep_current_wording`, `list_actions`, `undo_action`
- [[Reference/Modules/learnloop_sidecar/handlers/library|learnloop_sidecar.handlers.library]] — imports `FacetIdentityActionError`, `save_registry_text`; statically calls `save_registry_text`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `pending_reword_confirms`, `reword_confirms_by_item`; statically calls `pending_reword_confirms`, `reword_confirms_by_item`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `module`; calls `Cited`, `OwnerEdit`, `RegisteredMerge`, `Restore`, `added_provenance`, `authority_changes`, `authority_meaning`, `check_meaning_write`, `check_registry_text`, `contributions_from_support`, `merged_survivor`, `registry_entries`, `visible_sources`, `write_contributions`, `write_registry_text`, `written_provenance`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `TASK`
- [[Reference/Modules/learnloop/content/facet_identity/span_support|learnloop.content.facet_identity.span_support]] — imports `module`; calls `label`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `entity_source_link_rows`; calls `entity_source_link_rows`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/facet_identity|learnloop.db.stores.facet_identity]] — imports `module`; calls `action_by_id`, `delete_merge_rows`, `graded_contract_version_ids`, `insert_action`, `insert_registry_save`, `list_actions`, `registry_save_by_id`, `registry_saves`, `set_status`, `settle_registry_save`, `update_action`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `record_content_recalibration`; calls `record_content_recalibration`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/facet_fingerprint|learnloop.vault.facet_fingerprint]] — imports `semantic_fingerprint`; calls `semantic_fingerprint`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `EvidenceFacet`, `EvidenceFacetsFile`, `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `yaml_from_string`, `yaml_to_string`; calls `read_yaml`, `yaml_from_string`, `yaml_to_string`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `copy`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/facets|learnloop.cli.facets]], [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]], [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]], [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]], [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_authority_review_helpers.py](../../../../../../../tests/facet_authority_review_helpers.py) — direct import
- [tests/facet_identity_actions_helpers.py](../../../../../../../tests/facet_identity_actions_helpers.py) — direct import
- [tests/facet_reword_confirm_helpers.py](../../../../../../../tests/facet_reword_confirm_helpers.py) — direct import
- [tests/test_decider_landing.py](../../../../../../../tests/test_decider_landing.py) — direct import
  - `test_a_book_carrying_the_retired_keep_local_is_asked_like_any_other`
  - `test_a_tied_span_check_inside_an_automatic_build_waits_for_the_owner`
  - `test_an_automatic_builds_apply_asks_the_span_check_before_the_vault_lock`
  - `test_inside_an_automatic_builds_request_gate_the_span_check_is_admitted_and_settled`
- [tests/test_facet_authority.py](../../../../../../../tests/test_facet_authority.py) — direct import
  - `test_a_library_save_listing_a_facet_twice_is_refused_and_writes_nothing`
  - `test_a_proposal_create_over_a_registered_facet_needs_explanatory_support_or_the_owners_confirm`
  - `test_an_ingest_consolidation_keeps_exam_only_meaning_out_and_its_undo_cannot_mint_it`
  - `test_an_uncited_append_facet_carrying_a_registered_id_never_rewrites_it`
  - `test_the_writer_never_writes_a_reword_whose_only_support_is_unselected`
- [tests/test_facet_authority_rereview.py](../../../../../../../tests/test_facet_authority_rereview.py) — direct import
  - `test_a_save_intent_has_a_closed_lifecycle`
  - `test_a_save_that_fails_in_process_settles_its_intent`
  - `test_a_save_that_lands_records_a_settled_intent`
  - `test_doctor_reports_and_settles_an_interrupted_save_with_no_reword`
  - `test_recovery_keeps_the_verdict_of_a_save_killed_after_its_write`
  - `test_recovery_withdraws_the_verdict_of_a_save_killed_before_its_write`
- [tests/test_facet_authority_review.py](../../../../../../../tests/test_facet_authority_review.py) — direct import
  - `test_a_library_save_that_never_lands_withdraws_its_authority_verdicts`
  - `test_a_re_extraction_never_makes_an_exam_only_restoration_admissible`
  - `test_an_undo_never_mints_a_candidate_whose_recorded_citations_no_longer_resolve`
  - `test_every_library_change_to_a_facets_meaning_records_the_owners_authority_verdict`
  - `test_recovery_settles_an_undo_intent_the_authority_rule_refuses`
  - `test_recovery_withdraws_the_verdicts_of_a_library_save_killed_before_its_write`
  - `test_the_writer_never_writes_a_reword_citing_the_unselected_half_of_a_split_unit`
- [tests/test_facet_identity.py](../../../../../../../tests/test_facet_identity.py) — direct import
  - `test_an_undone_in_run_merge_stays_apart_when_the_run_is_planned_again`
  - `test_an_undone_merge_is_an_owner_verdict_and_dedupe_never_reapplies_it`
  - `test_dedupe_dry_run_plans_calls_and_cost_with_no_client_or_change`
  - `test_dedupe_regression_set_merges_the_agreed_pairs_and_keeps_the_distinct_ones`
- [tests/test_facet_identity_actions.py](../../../../../../../tests/test_facet_identity_actions.py) — direct import
  - `test_a_criterion_graded_before_the_merge_keeps_its_two_facets_apart`
  - `test_a_facet_that_used_to_be_locked_merges_and_undoes_exactly`
  - `test_a_held_back_retiree_stays_registered_while_the_rest_of_the_set_merges`
  - `test_a_merge_intent_whose_file_changed_meanwhile_is_withdrawn`
  - `test_a_merge_interrupted_after_its_file_write_already_resolves_through_the_alias`
  - `test_a_merge_interrupted_before_its_file_write_keeps_the_facets_evidence_apart`
  - `test_a_merge_rekeys_evidence_and_undo_restores_facets_and_evidence_exactly`
  - `test_a_merge_without_an_undo_says_so_and_refuses`
  - `test_an_interrupted_merge_is_finished_by_recovery`
  - `test_an_interrupted_undo_is_finished_by_a_retry`
  - `test_an_undo_interrupted_after_its_file_write_keeps_the_restored_facets_evidence_apart`
  - `test_dedupe_reports_a_held_back_retiree_as_refused`
  - `test_doctor_reports_an_interrupted_merge_and_fix_state_finishes_it`
  - `test_recovery_withdraws_a_merge_that_a_criterion_graded_meanwhile_names_both_facets`
  - `test_the_sidecar_finishes_an_interrupted_merge_when_it_opens_the_vault`
  - `test_undo_refuses_to_overwrite_a_later_change`
- [tests/test_facet_identity_composition.py](../../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_an_undo_still_supersedes_the_judges_merged_rows`
  - `test_facets_with_evidence_merge_whatever_the_retired_lock_key_says`
- [tests/test_facet_identity_ingest.py](../../../../../../../tests/test_facet_identity_ingest.py) — direct import
  - `test_a_candidate_matching_a_registered_facet_becomes_its_alias`
  - `test_a_duplicate_candidate_is_merged_before_the_gates_and_undo_re_mints_it`
  - `test_an_unapplied_proposal_records_the_merge_without_an_undo`
  - `test_append_attaches_a_new_facet_to_the_registered_one_it_restates`
  - `test_revalidation_with_the_switch_off_replays_no_stored_plan`
  - `test_the_kill_switch_restores_the_prompt_and_never_calls_the_judge`
  - `test_the_run_summary_names_its_run_and_each_action_its_evidence_and_undo_limits`
  - `test_two_sets_on_one_in_run_survivor_are_one_action_that_undoes_both`
- [tests/test_facet_reword_confirm.py](../../../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_a_cited_reword_records_its_sources_on_the_facets_history`
  - `test_a_confirm_never_shows_exam_text`
  - `test_a_confirm_refuses_when_the_facets_wording_changed_since`
  - `test_a_confirm_that_fails_in_process_stays_pending`
  - `test_a_confirm_whose_support_became_exam_material_is_refused`
  - `test_a_title_change_needs_no_explanatory_citation_and_is_on_the_facets_history`
  - `test_a_worked_example_change_applies_with_its_source_on_the_facets_history`
  - `test_an_exam_only_change_through_a_proposal_is_refused_never_held`
  - `test_an_interrupted_confirm_returns_to_pending_and_withdraws_its_verdict`
  - `test_an_uncited_append_reword_reaches_the_owner_as_a_confirm`
  - `test_an_uncited_reword_of_a_registered_facet_waits_for_the_owners_confirm`
  - `test_confirming_a_reword_applies_it_as_the_owners_authority_with_an_undo`
  - `test_confirming_keeps_what_changed_on_the_facet_since_beside_the_new_wording`
  - `test_keeping_the_current_wording_closes_the_confirm_and_changes_nothing`
  - `test_the_library_stays_the_owners_override_for_exam_wording`
- [tests/test_facet_reword_confirm_review.py](../../../../../../../tests/test_facet_reword_confirm_review.py) — direct import
  - `test_a_confirm_keeps_an_alias_added_since_when_the_reword_adds_one_too`
  - `test_a_confirm_keeps_error_signatures_and_repairs_changed_since`
  - `test_a_confirm_refuses_a_conflicting_change_it_cannot_merge`
  - `test_a_confirmed_reword_installs_its_source_links`
  - `test_a_pending_confirm_hides_a_sources_text_once_its_member_is_an_exam`
  - `test_an_append_title_update_applies_without_a_new_version`
  - `test_an_append_worked_example_update_applies_without_a_new_version`
  - `test_an_interrupted_confirm_installs_its_source_links_on_recovery`
  - `test_with_the_kill_switch_a_reword_held_earlier_can_still_be_decided`
  - `test_with_the_kill_switch_an_unsupported_change_is_refused_at_accept_not_held`
- [tests/test_facet_reword_paths.py](../../../../../../../tests/test_facet_reword_paths.py) — direct import
  - `test_a_cited_facet_reword_records_its_spans_in_the_facets_provenance`
  - `test_a_library_edit_cannot_set_a_facets_version_by_hand`
  - `test_a_library_edit_that_only_grows_a_facet_is_written_as_typed_and_is_not_a_version`
  - `test_a_library_edit_that_rewords_an_evidenced_facet_records_a_version_with_undo`
  - `test_a_library_registry_edit_that_does_not_parse_is_refused_and_writes_nothing`
  - `test_a_library_reword_interrupted_after_the_write_is_finished_by_recovery`
  - `test_a_library_reword_interrupted_before_the_write_is_withdrawn`
  - `test_a_library_reword_whose_write_never_landed_is_withdrawn_by_recovery`
  - `test_a_reword_after_a_reword_undoes_in_order_with_server_versions`
  - `test_a_stale_version_on_an_unchanged_meaning_keeps_the_current_version_and_the_undo`
  - `test_an_append_facet_restructure_applies_as_a_facet_version_with_undo`
  - `test_an_interrupted_reword_undo_records_the_verdict_once`
  - `test_an_oversized_incoming_version_is_ignored_and_every_undo_still_applies`
  - `test_an_uncited_facet_reword_waits_for_the_owners_confirm`
  - `test_undoing_a_reword_appends_the_owners_verdict_to_the_judgment_ledger`
- [tests/test_facet_rewords.py](../../../../../../../tests/test_facet_rewords.py) — direct import
  - `test_a_growth_only_update_is_not_a_version`
  - `test_a_reword_undo_refuses_after_a_later_edit`
  - `test_rewording_an_evidenced_facet_records_a_version_and_its_undo_restores_the_old_wording`
- [tests/test_facet_span_support.py](../../../../../../../tests/test_facet_span_support.py) — direct import
  - `test_a_confirm_finished_by_recovery_labels_the_check`
  - `test_a_tie_between_supports_and_another_option_holds_the_reword`
  - `test_keeping_a_card_that_went_stale_is_no_label`
  - `test_keeping_the_current_wording_labels_the_check_does_not_support`
  - `test_span_support_applies_only_on_supports_else_the_card_shows_verdict_and_span`
  - `test_the_owners_confirm_and_undo_label_the_check`
  - `test_the_owners_undo_of_a_reword_the_check_let_apply_labels_it`
  - `test_the_span_check_is_asked_before_the_vault_lock_is_taken`
- [tests/test_subject_registry.py](../../../../../../../tests/test_subject_registry.py) — direct import
  - `test_propose_facet_merge_still_holds_back_a_shared_graded_criterion`
  - `test_the_owner_merges_a_facet_that_used_to_be_locked_and_can_undo_it`

## Modification guidance

- Change actions policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/facet_identity/actions.py](../../../../../../../src/learnloop/content/facet_identity/actions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
