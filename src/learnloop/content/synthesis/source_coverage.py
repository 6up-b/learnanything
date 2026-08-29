"""Source-set coverage preview (spec_source_ingestion_v2 §9.3, CLI first).

Builds the members × concepts/claims matrix from unit inventories, kept on three
orthogonal axes rather than one overloaded cell:

- **inventory evidence** — claimed forms definition | explanation | example |
  exercise | assessment | omitted/unknown (from the inventories);
- **curriculum linkage** — applied | proposed | stale | unlinked with source
  role. Real linkage becomes available when `entity_source_links` lands in M5/M6;
  until then every cell emits ``unlinked`` behind the named
  ``CURRICULUM_LINKAGE_SEAM`` so the axis is honest, not faked;
- **assessment alignment** — task families/capabilities/representations/formats
  from the deterministic exam profiles (§7).

Plus a deterministic collection-readiness report (§9.3): no primary explanation,
instruction-light/exam-heavy, no practice material, assessment task families with
no teaching coverage, teaching content with no representative assessment, and
material not yet inventoried. Deterministic JSON, no LLM, no learner state.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.content.synthesis.exam_profile import ExamUnitEntry, aggregate_exam_profile
from learnloop.content.sources.role_authority import role_authority
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.content.synthesis.source_unit_selection import effective_scope_groups
from learnloop.content.synthesis.source_unit_inventory import profile_satisfies
from learnloop.vault.models import LoadedVault, SourceSet

# Real curriculum linkage arrives with entity_source_links in ING M5/M6; until
# then every cell is 'unlinked'. Named so the seam is greppable.
CURRICULUM_LINKAGE_SEAM = "entity_source_links_m5_m6"

# inventory-evidence forms (§9.3).
_FORMS = ("definition", "explanation", "example", "exercise", "assessment")


def _best_inventory(rows: list[dict[str, Any]], unit_id: str, requested_profile: str) -> dict[str, Any] | None:
    """The richest cached inventory for a unit that satisfies the request."""

    candidates = [row for row in rows if row["unit_id"] == unit_id]
    if not candidates:
        return None
    satisfying = [
        row
        for row in candidates
        if profile_satisfies(row["inventory_profile"], row["inventory_schema_version"], requested_profile)
    ]
    pool = satisfying or candidates
    pool.sort(key=lambda row: (row["inventory_profile"] != "combined", row["inventory_profile"]))
    return pool[0]


def _forms_for_inventory(inventory: dict[str, Any]) -> set[str]:
    forms: set[str] = set()
    for claim in inventory.get("claims", []):
        kind = claim.get("kind")
        if kind == "definition":
            forms.add("definition")
        elif kind == "example":
            forms.add("example")
        else:
            forms.add("explanation")
    for coverage in inventory.get("coverage_claims", []):
        for form in coverage.get("pedagogical_forms", []):
            normalized = str(form).strip().lower()
            if normalized in _FORMS:
                forms.add(normalized)
    for signal in inventory.get("practice_signals", []):
        if signal.get("kind") == "worked_example":
            forms.add("example")
        else:
            forms.add("exercise")
    if inventory.get("assessment_signals"):
        forms.add("assessment")
    return forms


def build_source_coverage(repo: Repository, vault: LoadedVault, source_set: SourceSet) -> dict[str, Any]:
    """Deterministic coverage preview for one source set (§9.3)."""

    members_out: list[dict[str, Any]] = []
    concept_evidence: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    exam_entries: list[ExamUnitEntry] = []
    not_inventoried: list[dict[str, str]] = []
    semantic_forms_present = False
    practice_present = False
    exam_present = False
    explanatory_member_present = False

    for member in source_set.members:
        authority = role_authority(member.default_role)
        extraction_id = resolve_extraction_id(repo, member.revision_id)
        member_units: list[dict[str, Any]] = []
        scope_units = [scope.unit_id for scope in member.scope]
        rows = repo.unit_inventories_for_revision(member.revision_id) if extraction_id else []
        ir = repo.load_document_ir(extraction_id) if extraction_id is not None else None
        selection = repo.get_unit_selection(extraction_id) if extraction_id is not None else None

        # Whole artifact when scope empty (§4.3): use the extraction's units.
        if not scope_units and ir is not None:
            scope_units = [unit.unit_id for unit in ir.units] if ir is not None else []

        role_overrides = {scope.unit_id: scope.role_override for scope in member.scope if scope.role_override}
        groups = (
            effective_scope_groups(
                ir,
                (selection or {}).get("boundary_overrides") or [],
                scope_units,
                role_by_unit=role_overrides,
                default_role=member.default_role,
            )
            if ir is not None
            else [
                {
                    "unit_id": unit_id,
                    "unit_ids": [unit_id],
                    "role": role_overrides.get(unit_id, member.default_role),
                    "merged": False,
                }
                for unit_id in scope_units
            ]
        )
        resolved_groups: list[tuple[dict[str, Any], dict[str, Any] | None]] = []
        for group in groups:
            inventory_row = _best_inventory(rows, str(group["unit_id"]), "combined")
            if inventory_row is None and len(group["unit_ids"]) > 1:
                for source_unit_id in group["unit_ids"]:
                    source_group = {
                        "unit_id": str(source_unit_id),
                        "unit_ids": [str(source_unit_id)],
                        "role": group["role"],
                        "merged": False,
                    }
                    resolved_groups.append(
                        (
                            source_group,
                            _best_inventory(rows, str(source_unit_id), "combined"),
                        )
                    )
            else:
                resolved_groups.append((group, inventory_row))

        for group, inventory_row in resolved_groups:
            unit_id = str(group["unit_id"])
            effective_role = str(group["role"])
            unit_authority = role_authority(effective_role)
            if inventory_row is None:
                not_inventoried.append({"source_id": member.source_id, "unit_id": unit_id})
                member_units.append({"unit_id": unit_id, "role": effective_role, "inventoried": False})
                continue
            inventory = inventory_row["inventory"]
            forms = _forms_for_inventory(inventory)
            if unit_authority.semantic_contract and (forms & {"definition", "explanation", "example"}):
                semantic_forms_present = True
                explanatory_member_present = True
            if "exercise" in forms or inventory.get("practice_signals"):
                practice_present = True
            if inventory.get("assessment_signals"):
                exam_present = True
            for mention in inventory.get("concept_mentions", []):
                name = (mention.get("name") or "").strip().lower()
                if name:
                    concept_evidence[name][member.source_id] |= forms
            member_units.append(
                {
                    "unit_id": unit_id,
                    "role": effective_role,
                    "inventoried": True,
                    "inventory_profile": inventory_row["inventory_profile"],
                    "inventory_evidence": sorted(forms),
                    "curriculum_linkage": "unlinked",
                    "curriculum_linkage_seam": CURRICULUM_LINKAGE_SEAM,
                    "semantic_authority": unit_authority.semantic_contract,
                    "assessment_authority": unit_authority.assessment_alignment,
                }
            )
            if effective_role == "exam" and unit_authority.assessment_alignment:
                paper_metadata = (selection or {}).get("exam_paper_metadata", {}) if selection else {}
                exam_entries.append(
                    ExamUnitEntry(unit_id=unit_id, inventory=inventory, paper_metadata=paper_metadata)
                )
        members_out.append(
            {
                "source_id": member.source_id,
                "revision_id": member.revision_id,
                "role": member.default_role,
                "semantic_authority": authority.semantic_contract,
                "assessment_authority": authority.assessment_alignment,
                "units": member_units,
            }
        )

    exam_profile = aggregate_exam_profile(exam_entries).as_dict() if exam_entries else None

    concept_matrix = [
        {
            "concept": concept,
            "sources": {source_id: sorted(forms) for source_id, forms in sorted(sources.items())},
        }
        for concept, sources in sorted(concept_evidence.items())
    ]

    readiness = _readiness_report(
        source_set=source_set,
        concept_evidence=concept_evidence,
        exam_profile=exam_profile,
        not_inventoried=not_inventoried,
        semantic_forms_present=semantic_forms_present,
        practice_present=practice_present,
        exam_present=exam_present,
        explanatory_member_present=explanatory_member_present,
    )

    return {
        "source_set_id": source_set.id,
        "subject_id": source_set.subject_id,
        "curriculum_linkage_seam": CURRICULUM_LINKAGE_SEAM,
        "members": members_out,
        "concept_matrix": concept_matrix,
        "assessment_alignment": exam_profile,
        "readiness": readiness,
    }


def _readiness_report(
    *,
    source_set: SourceSet,
    concept_evidence: dict[str, dict[str, set[str]]],
    exam_profile: dict[str, Any] | None,
    not_inventoried: list[dict[str, str]],
    semantic_forms_present: bool,
    practice_present: bool,
    exam_present: bool,
    explanatory_member_present: bool,
) -> dict[str, Any]:
    """The deterministic collection-readiness signals (§9.3)."""

    flags: list[dict[str, str]] = []

    def flag(code: str, message: str) -> None:
        flags.append({"code": code, "message": message})

    if not explanatory_member_present:
        flag("no_primary_explanation", "No source with semantic authority provides a definition/explanation.")
    if exam_present and not explanatory_member_present:
        flag("instruction_light_exam_heavy", "The collection is exam-heavy with no explanatory teaching source.")
    if not practice_present:
        flag("no_practice_material", "No practice/exercise material is present in the selected units.")
    if not_inventoried:
        flag("material_not_yet_inventoried", f"{len(not_inventoried)} selected unit(s) have no cached inventory.")

    # Assessment task families with no teaching coverage: any exam task family whose
    # name overlaps no taught concept.
    taught_terms = set(concept_evidence.keys())
    if exam_profile:
        untaught: list[str] = []
        for task_family in exam_profile.get("task_families", {}):
            if not any(term in task_family or task_family in term for term in taught_terms):
                untaught.append(task_family)
        if untaught:
            flag(
                "assessment_families_without_teaching",
                "Assessment task families with no teaching coverage: " + ", ".join(sorted(untaught)),
            )
    if not exam_profile and concept_evidence:
        flag("teaching_without_assessment", "Teaching content has no representative assessment source.")

    return {"ready": not flags, "flags": flags, "not_inventoried": not_inventoried}
