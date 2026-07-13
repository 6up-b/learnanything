"""Predictive EIG as the default diagnostic objective (spec §7.4/§7.5)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    enter_episode,
    episode_hypothesis_set,
)
from learnloop.services.probe_families import (
    CONTRAST_CONFUSABLE_DEFAULT_ROWS,
    CONTRAST_CONFUSABLE_V1,
    InstrumentCard,
    instrument_predictive_information_gain,
    validate_and_compile_card,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)


def _compiled(rows=None):
    card = InstrumentCard(
        id="card_test",
        version=1,
        family_template_id=CONTRAST_CONFUSABLE_V1.id,
        family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=LO_ID,
        target_decision="test",
        bindings={"target_facet": "recall", "confusable_concept": "eigendecomposition"},
        hypotheses=tuple(CONTRAST_CONFUSABLE_V1.hypothesis_slots),
        conditional_observations=rows or CONTRAST_CONFUSABLE_DEFAULT_ROWS,
        target_facets=("recall",),
    )
    return validate_and_compile_card(card, CONTRAST_CONFUSABLE_V1)


def test_hypothesis_independent_candidate_has_zero_predictive_eig():
    instrument = _compiled()
    flat_rows = {
        slot: {outcome: "occasional" for outcome in CONTRAST_CONFUSABLE_V1.observation_alphabet}
        for slot in CONTRAST_CONFUSABLE_V1.hypothesis_slots
    }
    flat = _compiled(rows=flat_rows)
    posterior = {slot: 1.0 / 5 for slot in CONTRAST_CONFUSABLE_V1.hypothesis_slots}
    slot_map = {slot: slot for slot in posterior}
    target = _compiled()  # a distinct held-out instrument

    informative = instrument_predictive_information_gain(
        posterior, instrument, slot_map, [(target, slot_map)]
    )
    uninformative = instrument_predictive_information_gain(
        posterior, flat, slot_map, [(target, slot_map)]
    )
    assert informative.eig_nats > 0
    # A candidate whose conditionals are identical across hypotheses never
    # moves the posterior, so held-out predictions never sharpen (§2.2).
    assert uninformative.eig_nats == 0.0


def test_predictive_eig_requires_held_out_targets():
    instrument = _compiled()
    posterior = {slot: 1.0 / 5 for slot in CONTRAST_CONFUSABLE_V1.hypothesis_slots}
    slot_map = {slot: slot for slot in posterior}
    # The candidate never predicts itself (held-out means held out).
    self_only = instrument_predictive_information_gain(
        posterior, instrument, slot_map, [(instrument, slot_map)]
    )
    assert self_only.target_count == 0
    assert self_only.eig_nats == 0.0


def _add_item(vault_root, item_id, surface_family):
    upsert_practice_item(
        vault_root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["diagnostic_probe", "dont_know"],
            "evidence_facets": ["recall"],
            "prompt": f"Prompt for {item_id}.",
            "expected_answer": "Answer.",
            "surface_family": surface_family,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )


def test_predictive_objective_is_default_and_persisted(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_item(vault_root, "pi_svd_define_002", "surface_two")
    _add_item(vault_root, "pi_svd_define_003", "surface_three")
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(
        repository, items=(ITEM_ID, "pi_svd_define_002", "pi_svd_define_003")
    )
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    entries = eligible_instruments(
        loaded, repository, episode, hypothesis_set=episode_hypothesis_set(repository, episode)
    )
    assert len(entries) == 3
    # With >= predictive_target_minimum held-out instruments, predictive EIG
    # per expected second is the primary objective (§7.4).
    assert all(entry.selection_objective == "predictive_eig" for entry in entries)
    assert entries[0].predictive_information_rate >= entries[-1].predictive_information_rate
    assert all(entry.predictive_eig > 0 for entry in entries)

    presentation = commit_presentation(loaded, repository, episode, entries[0], clock=CLOCK)
    components = presentation.selection_components
    # §7.3: components stay separately inspectable — hypothesis EIG and
    # predictive EIG are logged side by side, never added.
    assert components["selection_objective"] == "predictive_eig"
    assert components["predictive_eig"] > 0
    assert components["actual_hypothesis_eig"] > 0
    assert components["predictive_information_rate"] > 0


def test_hypothesis_fallback_when_target_set_inadequate(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, items=(ITEM_ID,))
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    entries = eligible_instruments(
        loaded, repository, episode, hypothesis_set=episode_hypothesis_set(repository, episode)
    )
    assert len(entries) == 1
    # A single instrument leaves no held-out targets: hypothesis EIG remains
    # the fallback and audit objective (§7.4).
    assert entries[0].selection_objective == "hypothesis_eig"
    assert entries[0].predictive_target_count == 0
    assert entries[0].expected_information_gain > 0
