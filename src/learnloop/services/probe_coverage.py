"""Hypothesis-contrast / family coverage report (spec §9.5, Checkpoint 3.3).

Coverage is a generation-target check over family/card bindings, not an item
backlog: for every decision-relevant hypothesis distinction an episode could
instantiate, there should be at least two signature-distinct family templates
able to separate it — one direct or minimal instrument, and one contrast,
perturbation, counterexample, shifted-surface, or transfer instrument. The
report feeds the §10 generation workflow rather than hand-authoring queues.
"""

from __future__ import annotations

from typing import Any

from learnloop.db.repositories import Repository
from learnloop.services.probe_families import (
    InstrumentCard,
    ProbeFamilyTemplate,
    map_episode_labels_to_slots,
    validate_and_compile_card,
)
from learnloop.services.probe_hypotheses import build_episode_hypothesis_set
from learnloop.vault.models import LoadedVault

# Instrument kinds by §9.5 role.
DIRECT_KINDS = ("minimal_recall", "prediction")
SHIFTED_KINDS = ("contrast", "perturbation", "counterexample", "dialogue")
# Kinds satisfying the integrative/long-form expectation for procedural or
# multi-step knowledge (none built-in yet — reported as a gap when required).
INTEGRATIVE_KINDS = ("proof_skeleton", "derivation", "extended_case")

_PAIR_SEPARATION_THRESHOLD = 0.25


def family_coverage_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """Per-LO coverage of instantiable hypothesis contrasts by admitted
    family/card bindings, with the §9.5 direct+shifted requirement."""

    learning_objects: list[dict[str, Any]] = []
    totals = {
        "learning_objects": 0,
        "learning_objects_with_bindings": 0,
        "contrasts": 0,
        "contrasts_fully_covered": 0,
        "contrasts_uncovered": 0,
        "integrative_gaps": 0,
    }

    for lo_id in sorted(vault.learning_objects):
        learning_object = vault.learning_objects[lo_id]
        if learning_object.status != "active":
            continue
        totals["learning_objects"] += 1
        hypothesis_set = build_episode_hypothesis_set(vault, repository, lo_id)
        labels = [hypothesis.label for hypothesis in hypothesis_set.hypotheses]

        instruments: list[dict[str, Any]] = []
        for record in repository.probe_instrument_cards_for_learning_object(lo_id):
            family_record = repository.probe_family_template(
                record.probe_family_template_id, record.probe_family_template_version
            )
            if family_record is None or family_record.status not in ("provisional", "trusted"):
                continue
            template = ProbeFamilyTemplate.from_dict(family_record.template)
            card = InstrumentCard.from_dict(record.card)
            try:
                instrument = validate_and_compile_card(card, template)
            except Exception:
                continue
            slot_map = map_episode_labels_to_slots(instrument, labels, bindings=card.bindings)
            instance_ids = repository.probe_items_for_card(record.id, record.version)
            instruments.append(
                {
                    "card_id": record.id,
                    "card_version": record.version,
                    "family_template_id": template.id,
                    "family_template_version": template.version,
                    "family_status": family_record.status,
                    "instrument_kind": template.instrument_kind,
                    "instance_count": len(instance_ids),
                    "slot_map": slot_map,
                    "_instrument": instrument,
                }
            )
        if instruments:
            totals["learning_objects_with_bindings"] += 1

        contrasts: list[dict[str, Any]] = []
        for index, left in enumerate(labels):
            for right in labels[index + 1 :]:
                covering_direct: set[str] = set()
                covering_shifted: set[str] = set()
                for entry in instruments:
                    slot_map = entry["slot_map"]
                    if slot_map is None:
                        continue
                    left_slot, right_slot = slot_map.get(left), slot_map.get(right)
                    if left_slot is None or right_slot is None or left_slot == right_slot:
                        continue
                    instrument = entry["_instrument"]
                    distance = 0.5 * sum(
                        abs(
                            instrument.rows[left_slot][outcome]
                            - instrument.rows[right_slot][outcome]
                        )
                        for outcome in instrument.outcome_alphabet
                    )
                    if distance < _PAIR_SEPARATION_THRESHOLD:
                        continue
                    if entry["instrument_kind"] in DIRECT_KINDS:
                        covering_direct.add(entry["family_template_id"])
                    else:
                        covering_shifted.add(entry["family_template_id"])
                covered = bool(covering_direct) and bool(covering_shifted)
                distinct_families = covering_direct | covering_shifted
                totals["contrasts"] += 1
                if covered and len(distinct_families) >= 2:
                    totals["contrasts_fully_covered"] += 1
                elif not distinct_families:
                    totals["contrasts_uncovered"] += 1
                contrasts.append(
                    {
                        "pair": [left, right],
                        "direct_families": sorted(covering_direct),
                        "shifted_families": sorted(covering_shifted),
                        "fully_covered": covered and len(distinct_families) >= 2,
                    }
                )

        from learnloop.services.probe_families import knowledge_type_tokens

        needs_integrative = bool(
            knowledge_type_tokens(learning_object.knowledge_type)
            & {"procedure", "procedural", "proof", "derivation"}
        )
        has_integrative = any(
            entry["instrument_kind"] in INTEGRATIVE_KINDS for entry in instruments
        )
        if needs_integrative and not has_integrative:
            totals["integrative_gaps"] += 1

        for entry in instruments:
            entry.pop("_instrument", None)
            entry.pop("slot_map", None)

        learning_objects.append(
            {
                "learning_object_id": lo_id,
                "knowledge_type": learning_object.knowledge_type,
                "hypothesis_labels": labels,
                "instruments": instruments,
                "contrasts": contrasts,
                "uncovered_contrasts": [
                    contrast["pair"] for contrast in contrasts if not contrast["fully_covered"]
                ],
                "needs_integrative_family": needs_integrative and not has_integrative,
                "pending_generation_needs": [
                    {
                        "need_id": need.id,
                        "target_key": need.target_key,
                        "missing_capability": need.missing_capability,
                    }
                    for need in repository.probe_generation_needs(
                        learning_object_id=lo_id, status="pending"
                    )
                ],
            }
        )

    return {
        "version": 1,
        "totals": totals,
        "learning_objects": learning_objects,
    }
