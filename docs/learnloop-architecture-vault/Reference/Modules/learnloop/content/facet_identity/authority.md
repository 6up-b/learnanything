---
title: "learnloop.content.facet_identity.authority"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/facet_identity/authority.py"
source_paths:
  - "src/learnloop/content/facet_identity/authority.py"
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
  - "learnloop.content.facet_identity.authority module"
  - "src/learnloop/content/facet_identity/authority.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-facet-identity"
---

# `learnloop.content.facet_identity.authority`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.facet_identity.authority` exists within [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] to own the behavior summarized by its module contract: Facet meaning authority: the one chokepoint (Codex verification of F6 and its re-review, 2026-10-13).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/facet_identity/authority.py](../../../../../../../src/learnloop/content/facet_identity/authority.py) |
| Source lines | 1404 |
| Owning package | [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class MeaningPolicy` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 141) — Which changes to a registered facet the chokepoint admits without explanatory support.
- `meaning_policy(config: LearnLoopConfig) -> MeaningPolicy` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 166) — The admission policy a vault's config selects (``facet_identity.reword_confirm``).
- `class FacetAuthorityError(ValueError)` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 183) — A facet meaning write the chokepoint refused (nothing was written).
  - `__init__(self, code: str, message: str, *, facet_id: str | None=None) -> None` (line 186; internal)
- `overlay(before: Mapping[str, Any] | None, values: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 195) — The entry a write leaves: ``values`` over ``before`` (what ``upsert_facet`` writes).
- `authority_meaning(entry: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 202) — The :data:`AUTHORITY_FIELDS` of an entry, normalized (an absent entry has none).
- `authority_changes(before: Mapping[str, Any] | None, after: Mapping[str, Any] | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 211) — The :data:`AUTHORITY_FIELDS` that differ (for a new facet: every one it states).
- `class ResolvedCitation` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 222) — A citation the resolver validated: its role and locator come from the ids.
  - `locator(self) -> str` (line 235; public)
  - `supports(self) -> bool` (line 239; public)
  - `citation(self) -> dict[str, Any]` (line 242; public) — The ids a proposal's ``meaning_support`` carries (re-resolved at apply).
  - `yaml_ref(self) -> dict[str, Any]` (line 248; public) — The provenance ref a facet (or any entity) records for this citation.
  - `gate_ref(self, *, held_out: bool=False) -> ProvenanceRef` (line 264; public)
- `class CitationProblem` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 272) — A citation that does not resolve, and why.
  - `label(self) -> str` (line 278; public)
- `class CitationResolver` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 327) — Resolves citations against source-set members (their selected units and roles).
  - `__init__(self, members: Sequence[_Member], *, load_ir: Callable[[str], Any], load_overrides: Callable[[str], Sequence[Mapping[str, Any]]], load_revision: Callable[[str], str | None] | None=None, load_exam: Callable[[], EM.ExamMaterial] | None=None) -> None` (line 335; internal)
  - `is_exam(self, extraction_id: str, span_id: str) -> bool` (line 359; public) — Whether the one exam predicate names this span exam material.
  - `for_source_sets(cls, repository: Any, source_sets: Iterable[Any], *, exam_source_sets: Iterable[Any] | None=None) -> CitationResolver` (line 369; public) — Members of ``source_sets``; exam material read over ``exam_source_sets`` (the vault's every set: a span that is exam material in ANY set is exam), else over ``source_sets``.
  - `for_source_set(cls, repository: Any, source_set: Any, *, exam_source_sets: Iterable[Any] | None=None) -> CitationResolver` (line 402; public)
  - `for_vault(cls, repository: Any, vault: Any) -> CitationResolver` (line 407; public)
  - `with_span_support(self, vault: Any, repository: Any, *, asked: Mapping[str, Mapping[str, Any]] | None=None, record: dict[str, dict[str, Any]] | None=None) -> CitationResolver` (line 410; public) — Attach the span-support check (switch ``decider_routes.facet_span_support``).
  - `_index(self, extraction_id: str) -> _Units | None` (line 434; internal)
  - `excerpt(self, citation: ResolvedCitation, *, limit: int=280) -> str | None` (line 449; public) — The cited span's text, shortened, for the owner to judge a reword by.
  - `_members_for(self, extraction_id: str) -> list[_Member]` (line 467; internal) — The members an extraction run belongs to: by its id, else by the revision it extracted.
  - `resolve(self, citation: Mapping[str, Any], *, default_relation: str='support') -> ResolvedCitation | CitationProblem` (line 486; public) — Validate a citation by its ids; the model's role, source, revision and locator are ignored.
  - `exam_material(self, citation: Mapping[str, Any]) -> bool` (line 550; public) — Whether a citation that does not resolve still names exam material by its span.
  - `resolve_ref(self, ref: Mapping[str, Any], *, default_relation: str='support') -> ResolvedCitation | CitationProblem` (line 577; public) — Resolve a persisted provenance ref by the span its locator names (its identity).
- `class Contribution` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 595) — The citations one source of a write's meaning offers (a candidate, a reword, an absorbed facet).
- `contributions(citations: Iterable[Mapping[str, Any]], *, label: str='write') -> tuple[Contribution, ...]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 602)
- `support_entries(contributed: Iterable[Contribution]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 606) — A proposal payload's ``meaning_support``: each contribution's citations by id.
- `contributions_from_support(meaning_support: Any) -> tuple[Contribution, ...]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 625) — Parse a payload's ``meaning_support`` (a flat citation list is one contribution).
- `write_contributions(payload: Mapping[str, Any], *, before: Mapping[str, Any] | None, after: Mapping[str, Any], resolver: CitationResolver | None=None) -> tuple[Contribution, ...]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 681) — What supports a proposal write: its ``meaning_support``, reconciled with the refs it records.
- `class MeaningVerdict` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 719) — Whether one facet meaning write is allowed, and why.
  - `diagnostic(self, *, entity_refs: Sequence[str] | None=None, severity: str='review', suggested_action: str | None=None) -> dict[str, Any]` (line 737; public) — A typed review record for a producer that dropped, or held for the owner, what this verdict refuses.
- `span_support_text(support: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 773) — One plain clause on a span-support check that did not say ``supports``.
- `check_meaning_write(facet_id: str, *, before: Mapping[str, Any] | None, after: Mapping[str, Any], registered: bool, contributions: Sequence[Contribution], resolver: CitationResolver | None, require_resolved: bool=False, policy: MeaningPolicy=REWORD_CONFIRM) -> MeaningVerdict` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 788) — Judge one write of a facet's meaning from validated citations (the §4.2 rule, once).
- `source_views(verdict: MeaningVerdict, resolver: CitationResolver | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 918) — The validated citations of a write, as its history records them.
- `visible_sources(sources: Iterable[Mapping[str, Any]], resolver: CitationResolver | None, *, excerpt_limit: int=280) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 945) — Recorded source views as the owner may see them now (Codex review F3).
- `written_provenance(before: Mapping[str, Any] | None, after: Mapping[str, Any], verdict: MeaningVerdict, resolver: CitationResolver | None, *, record_support: bool=True) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 979) — The provenance a checked write records: what it displays is what was validated.
- `added_provenance(before: Mapping[str, Any] | None, written: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1022) — The refs a write adds that were validated (what its ``entity_source_links`` rows record).
- `class Join` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1040) — A candidate merged or absorbed into a survivor: whether its meaning joined.
- `join_candidate(survivor: Mapping[str, Any], retired: Mapping[str, Any], *, survivor_id: str, action: str, absorb_as: str | None, contribution: Contribution, registered: bool, resolver: CitationResolver | None) -> Join` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1048) — Merge or absorb a candidate into ``survivor``, through the authority rule.
- `merged_survivor(survivor: Mapping[str, Any], retired: Sequence[Mapping[str, Any]], *, action: str, absorb_as: str | None, alias_ids: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1080) — A vault merge's survivor: the union of registered facets (their meaning was admitted).
- `class OwnerEdit` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1093) — The owner's own Library save: explicit manual authority, audited.
- `class Cited` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1106) — A change supported by recorded citations, judged by :func:`check_meaning_write`.
- `class RegisteredMerge` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1118) — A vault merge of registered facets: the survivor must be their union, recomputed here.
- `class Restore` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1128) — An undo or recovery: each changed facet must be exactly an entry an action recorded.
- `registry_entries(document: Any, *, strict: bool=True) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1137) — ``{facet id: entry}`` of a registry document; ``strict`` refuses an id listed twice.
- `check_registry_text(paths: VaultPaths, text: str, *, basis: Mapping[str, Basis], resolver: CitationResolver | None=None) -> dict[str, MeaningVerdict]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1214) — Verify, without writing, that every meaning change ``text`` makes to facets.yaml is authorized.
- `write_registry_text(paths: VaultPaths, text: str, *, basis: Mapping[str, Basis], resolver: CitationResolver | None=None) -> None` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1249) — Replace facets.yaml with ``text`` if every meaning change in it is authorized.
- `class ProposalAuthority` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1277) — The chokepoint's context for one proposal apply.
  - `__init__(self, resolver_factory: Callable[[], CitationResolver | None]) -> None` (line 1286; internal)
  - `resolver(self) -> CitationResolver | None` (line 1293; public)
  - `record(self, facet_id: str, entry: Mapping[str, Any]) -> None` (line 1299; public)
  - `for_proposal(cls, vault: Any, repository: Any, patch_id: str, *, asked: Mapping[str, Mapping[str, Any]] | None=None, record: dict[str, dict[str, Any]] | None=None) -> ProposalAuthority` (line 1303; public) — ``record`` / ``asked``: the span-support verdicts asked before the vault lock (review F1).
- `verify_registry_transition(paths: VaultPaths, targets: Sequence[Mapping[str, Any]], *, checked: Mapping[str, Mapping[str, Any]]) -> None` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1330) — Refuse a staged facets.yaml whose meaning changes no checked facet item wrote.

### Module constants

- `AUTHORITY_FIELDS` ([src/learnloop/content/facet_identity/authority.py](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 124)
- `PRESENTATION_FIELDS` ([src/learnloop/content/facet_identity/authority.py](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 131)
- `CONFIRMABLE_CODES` ([src/learnloop/content/facet_identity/authority.py](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 134)
- `SPAN_SUPPORTS` ([src/learnloop/content/facet_identity/authority.py](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 137)
- `REWORD_CONFIRM` ([src/learnloop/content/facet_identity/authority.py](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 158)
- `EXPLANATORY_ONLY` ([src/learnloop/content/facet_identity/authority.py](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 163)
- `PROPOSAL_ONLY_KEYS` ([src/learnloop/content/facet_identity/authority.py](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 172)
- `HELD_OUT_EVALUATION` ([src/learnloop/content/facet_identity/authority.py](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 174)
- `UNRESOLVED_ROLE` ([src/learnloop/content/facet_identity/authority.py](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 176)
- `ALLOWED_CODES` ([src/learnloop/content/facet_identity/authority.py](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 178)
- `_SPAN_SUPPORT_TEXT` ([src/learnloop/content/facet_identity/authority.py](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 766)

### Explicit exports

`__all__` declares:

- `ALLOWED_CODES`
- `AUTHORITY_FIELDS`
- `CONFIRMABLE_CODES`
- `EXPLANATORY_ONLY`
- `HELD_OUT_EVALUATION`
- `SPAN_SUPPORTS`
- `PRESENTATION_FIELDS`
- `REWORD_CONFIRM`
- `Basis`
- `Cited`
- `CitationProblem`
- `CitationResolver`
- `Contribution`
- `FacetAuthorityError`
- `Join`
- `MeaningPolicy`
- `MeaningVerdict`
- `OwnerEdit`
- `PROPOSAL_ONLY_KEYS`
- `ProposalAuthority`
- `RegisteredMerge`
- `ResolvedCitation`
- `Restore`
- `UNRESOLVED_ROLE`
- `added_provenance`
- `authority_changes`
- `authority_meaning`
- `check_meaning_write`
- `span_support_text`
- `check_registry_text`
- `contributions`
- `contributions_from_support`
- `join_candidate`
- `meaning_policy`
- `merged_survivor`
- `overlay`
- `registry_entries`
- `source_views`
- `support_entries`
- `verify_registry_transition`
- `visible_sources`
- `write_contributions`
- `write_registry_text`
- `written_provenance`

## Internal implementation anchors

- `class _Member` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 283)
- `class _Units` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 296) — One extraction's units: each raw and each effective unit with the spans it holds.
- `_authority_rank(role: str) -> int` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 319) — Lower is less authoritative: exam, then roles that never support a claim, then explanatory.
- `_invalid_support(message: str) -> FacetAuthorityError` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 613)
- `_cited_span(citation: Any, where: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 617)
- `_refs(entry: Mapping[str, Any] | None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 660)
- `_ref_key(ref: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 666)
- `_new_refs(before: Mapping[str, Any] | None, after: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 672)
- `_span_key(citation: Mapping[str, Any]) -> tuple[str, str]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 677)
- `_verdict(facet_id: str, allowed: bool, code: str, message: str='', **kwargs: Any) -> MeaningVerdict` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 784)
- `_file_entries(paths: VaultPaths) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1159)
- `_check_basis(facet_id: str, before: Mapping[str, Any] | None, entry: Mapping[str, Any], basis: Basis | None, current: Mapping[str, Mapping[str, Any]], resolver: CitationResolver | None) -> MeaningVerdict` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1168)
- `_proposal_source_set(vault: Any, repository: Any, patch_id: str) -> Any` ([source](../../../../../../../src/learnloop/content/facet_identity/authority.py), line 1320)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `module`; statically calls `Cited`, `OwnerEdit`, `RegisteredMerge`, `Restore`, `added_provenance`, `authority_changes`, `authority_meaning`, `check_meaning_write`, `check_registry_text`, `contributions_from_support`, `merged_survivor`, `registry_entries`, `visible_sources`, `write_contributions`, `write_registry_text`, `written_provenance`
- [[Reference/Modules/learnloop/content/facet_identity/span_support|learnloop.content.facet_identity.span_support]] — imports `authority_meaning`; statically calls `authority_meaning`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `module`; statically calls `added_provenance`, `authority_changes`, `check_meaning_write`, `meaning_policy`, `overlay`, `source_views`, `support_entries`, `verify_registry_transition`, `write_contributions`, `written_provenance`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `module`; statically calls `authority_changes`, `check_meaning_write`, `contributions`, `meaning_policy`, `overlay`, `support_entries`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `module`; statically calls `CitationProblem`, `Contribution`, `check_meaning_write`, `join_candidate`, `meaning_policy`, `overlay`, `support_entries`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/content/facet_identity/span_support|learnloop.content.facet_identity.span_support]] — imports `check`; calls `check`
- [[Reference/Modules/learnloop/content/facet_identity/views|learnloop.content.facet_identity.views]] — imports `union_payload`; calls `union_payload`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `materialize_targets`, `text_hash`; calls `materialize_targets`, `text_hash`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `exam_material`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `ASSESSMENT_ONLY_ROLES`, `CITATION_RELATIONS`, `EXAM_UNCORROBORATED`, `EXPLANATORY`, `can_authorize_semantic`, `is_semantic_support`, `support_verdict`; calls `can_authorize_semantic`, `is_semantic_support`, `support_verdict`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `effective_unit_spans`; calls `effective_unit_spans`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `ProvenanceRef`; calls `ProvenanceRef`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `enabled`; calls `enabled`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `BLOCK_SPAN_V1`, `format_block_span`, `parse_block_span`; calls `format_block_span`, `parse_block_span`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `EvidenceFacet`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `yaml_from_string`; calls `read_yaml`, `yaml_from_string`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `copy`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]], [[Reference/Modules/learnloop/content/facet_identity/span_support|learnloop.content.facet_identity.span_support]], [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]], [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_authority_review_helpers.py](../../../../../../../tests/facet_authority_review_helpers.py) — direct import
- [tests/test_apply_recovery.py](../../../../../../../tests/test_apply_recovery.py) — direct import
  - `test_a_registry_save_of_the_text_already_there_writes_nothing`
- [tests/test_exam_protection.py](../../../../../../../tests/test_exam_protection.py) — direct import
  - `test_exam_material_in_any_revision_of_an_exam_source_is_exam_to_every_reader`
- [tests/test_facet_authority.py](../../../../../../../tests/test_facet_authority.py) — direct import
  - `test_the_registry_writer_refuses_exam_only_meaning_whatever_the_caller_declares`
- [tests/test_facet_authority_rereview.py](../../../../../../../tests/test_facet_authority_rereview.py) — direct import
  - `test_a_declared_citation_covers_a_recorded_span_only_when_it_resolves`
- [tests/test_facet_authority_review.py](../../../../../../../tests/test_facet_authority_review.py) — direct import
  - `test_a_citation_of_an_earlier_extraction_of_a_member_revision_keeps_its_role`
  - `test_selecting_one_child_of_a_split_unit_never_selects_its_sibling`
  - `test_split_children_keep_their_own_role_overrides_in_any_order`
  - `test_the_registry_writer_refuses_an_owner_edit_with_no_audit_record`
- [tests/test_facet_locks_landing.py](../../../../../../../tests/test_facet_locks_landing.py) — direct import
  - `test_a_held_out_textbook_unit_is_exam_material_to_both_predicates`
  - `test_an_exam_members_material_is_exam_to_both_predicates`
- [tests/test_facet_reword_confirm.py](../../../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_a_held_out_evaluation_unit_is_exam_material_whatever_its_members_role`
  - `test_the_chokepoint_judges_titles_and_examples_without_an_explanatory_citation`
  - `test_the_registry_writer_refuses_exam_only_meaning_and_an_unconfirmed_reword`
- [tests/test_facet_reword_confirm_review.py](../../../../../../../tests/test_facet_reword_confirm_review.py) — direct import
  - `test_the_policy_follows_the_switch`
- [tests/test_facet_span_support.py](../../../../../../../tests/test_facet_span_support.py) — direct import
  - `test_a_check_whose_input_changed_under_the_lock_waits_for_the_confirm`
  - `test_exam_only_support_is_refused_before_the_decider_and_the_owner_edit_bypasses_it`
  - `test_only_a_registered_facets_meaning_is_checked`
  - `test_the_check_reads_each_cited_span_once`
  - `test_the_span_switch_restores_the_cited_reword_and_reword_confirm_off_skips_the_check`

## Modification guidance

- Change authority policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/facet_identity/authority.py](../../../../../../../src/learnloop/content/facet_identity/authority.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
