"""Outcome projection is ledger-derived, read-only and fails closed."""
import hashlib
import json

import pytest

from learnloop.field.outcomes import data_check, load_attempt_rows, load_facet_rows, rebuild_outcome_view
from tests.helpers import NOW_ISO
from tests.test_km3_projections import blueprint_vault, COMP_A  # noqa: F401
from tests.test_facet_evidence_timeline import _attempt


def _pin_snapshot(connection, vault, attempt_id, item_id="pi_comp_a", *, snapshot_at=NOW_ISO, selection_at=NOW_ISO, demand=None):
    item = vault.practice_items[item_id]
    raw = json.dumps(item.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    connection.execute(
        "INSERT OR IGNORE INTO practice_item_snapshots VALUES (?,?,?,?)",
        (digest, item_id, raw, snapshot_at),
    )
    candidate = f"candidate-{attempt_id}"
    connection.execute(
        """INSERT INTO decision_features(id,decision_id,decision_type,ability_vector_json,
        item_demand_vector_json,algorithm_version,created_at) VALUES (?,?,'selection','{}',?,'test',?)""",
        (candidate, candidate, json.dumps({"content_hash": digest, **(demand or {})}), selection_at),
    )
    connection.execute("UPDATE practice_attempts SET scheduler_candidate_id=? WHERE id=?", (candidate, attempt_id))
    return digest


def test_missing_revision_excluded_and_current_content_opt_in(blueprint_vault):
    vault, repository = blueprint_vault
    _attempt(vault, repository, "pi_comp_a", 4)
    with repository.connection() as connection:
        excluded, = load_attempt_rows(connection, vault)
        assert excluded.revision_status == "excluded"
        assert excluded.effective_mass == 0
        current, = load_attempt_rows(connection, vault, legacy_fallback="current_content")
        assert current.revision_status == "reconstructed_current"
        assert current.outcome == 1
        assert current.effective_mass > 0
        with pytest.raises(ValueError):
            load_attempt_rows(connection, vault, legacy_fallback="silently_guess")


def test_exact_debug_agreement_and_no_debug_authority(blueprint_vault):
    vault, repository = blueprint_vault
    result = _attempt(vault, repository, "pi_comp_a", 4)
    with repository.connection() as connection:
        digest = _pin_snapshot(connection, vault, result.attempt_id)
        row, = load_facet_rows(connection, vault)
        assert row.revision_status == "exact"
        assert row.item_snapshot_hash == digest
        assert row.outcome == 1
        assert row.facet_share == 1
        assert data_check(connection, vault)["debug_validation"] == {"compared": 1, "mismatched": 0}
        connection.execute(
            "UPDATE attempt_debug_payloads SET payload_json=? WHERE attempt_id=?",
            (json.dumps({"facet_outcomes": {COMP_A: 0}}), result.attempt_id),
        )
        assert load_facet_rows(connection, vault) == (row,)
        assert data_check(connection, vault)["debug_validation"]["mismatched"] == 1


def test_latest_epoch_and_canonical_merge(blueprint_vault):
    vault, repository = blueprint_vault
    result = _attempt(vault, repository, "pi_comp_a", 4)
    with repository.connection() as connection:
        _pin_snapshot(connection, vault, result.attempt_id)
        old = connection.execute("SELECT * FROM grading_evidence WHERE attempt_id=?", (result.attempt_id,)).fetchone()
        connection.execute("UPDATE grading_evidence SET superseded_at=? WHERE id=?", (NOW_ISO, old["id"]))
        connection.execute(
            """INSERT INTO grading_evidence(id,attempt_id,criterion_id,points_awarded,grader_tier,
            created_at,grading_revision,assessment_contract_version_id) VALUES (?,?,?,1,1,?,2,?)""",
            ("replacement", result.attempt_id, old["criterion_id"], NOW_ISO, old["assessment_contract_version_id"]),
        )
        connection.execute("INSERT INTO facet_merges VALUES (?,?,?,NULL,NULL)", (COMP_A, "merged_facet", NOW_ISO))
        row, = load_facet_rows(connection, vault)
        assert row.facet_id == "merged_facet"
        assert row.outcome == .25
        assert row.facet_share == 1
        assert load_attempt_rows(connection, vault)[0].outcome == .25


def test_dont_know_and_priming_do_not_double_discount(blueprint_vault):
    vault, repository = blueprint_vault
    result = _attempt(vault, repository, "pi_comp_a", 4)
    with repository.connection() as connection:
        _pin_snapshot(connection, vault, result.attempt_id)
        clean, = load_attempt_rows(connection, vault)
        connection.execute("UPDATE practice_attempts SET primed=1 WHERE id=?", (result.attempt_id,))
        primed, = load_attempt_rows(connection, vault)
        assert primed.effective_mass == clean.effective_mass
        assert primed.features.primed and not primed.features.cold
        connection.execute("UPDATE practice_attempts SET attempt_type='dont_know',primed=0 WHERE id=?", (result.attempt_id,))
        unknown, = load_attempt_rows(connection, vault)
        assert unknown.outcome == 0
        assert unknown.effective_mass == vault.config.evidence.attempt_types["dont_know"].evidence_mass


def test_rebuild_deterministic_and_never_writes_evidence(blueprint_vault):
    vault, repository = blueprint_vault
    result = _attempt(vault, repository, "pi_comp_a", 4)
    with repository.connection() as connection:
        _pin_snapshot(connection, vault, result.attempt_id)
        protected = ("grading_evidence", "learning_object_mastery", "facet_recall_state", "facet_capability_evidence")
        before = {t: tuple(tuple(r) for r in connection.execute(f"SELECT * FROM {t}")) for t in protected}
        assert rebuild_outcome_view(connection, vault) == 1
        first = tuple(tuple(r) for r in connection.execute("SELECT * FROM facet_outcome_observations"))
        rebuild_outcome_view(connection, vault)
        assert first == tuple(tuple(r) for r in connection.execute("SELECT * FROM facet_outcome_observations"))
        assert before == {t: tuple(tuple(r) for r in connection.execute(f"SELECT * FROM {t}")) for t in protected}
        assert load_attempt_rows(connection, vault)[0].serving_origin == "unknown"


def test_edited_current_item_never_changes_exact_row(blueprint_vault):
    vault, repository = blueprint_vault
    result = _attempt(vault, repository, "pi_comp_a", 4)
    with repository.connection() as connection:
        _pin_snapshot(connection, vault, result.attempt_id)
        before = load_attempt_rows(connection, vault)
        vault.practice_items["pi_comp_a"] = vault.practice_items["pi_comp_a"].model_copy(update={"prompt": "changed today"})
        assert load_attempt_rows(connection, vault) == before


def test_multifacet_weight_is_not_multiplied(blueprint_vault):
    vault, repository = blueprint_vault
    item = vault.practice_items["pi_comp_a"]
    vault.practice_items[item.id] = item.model_copy(update={
        "evidence_facets": [COMP_A, "facet_component_b"],
        "evidence_weights": {COMP_A: .75, "facet_component_b": .25},
        "criterion_facet_weights": {"c1": {COMP_A: .75, "facet_component_b": .25}},
    })
    result = _attempt(vault, repository, item.id, 4)
    with repository.connection() as connection:
        _pin_snapshot(connection, vault, result.attempt_id)
        assert load_attempt_rows(connection, vault)[0].revision_status == "excluded"
        rows = load_facet_rows(connection, vault, legacy_fallback="current_content")
        assert all(row.revision_status == "reconstructed_current" for row in rows)
        assert len(rows) == 2
        assert sum(r.facet_share for r in rows) == pytest.approx(1)
        assert sum(r.effective_mass * r.facet_share for r in rows) == pytest.approx(
            load_attempt_rows(connection, vault, legacy_fallback="current_content")[0].effective_mass
        )


def test_partial_fractional_criterion_uses_assessed_denominator(blueprint_vault):
    from learnloop.vault.models import Rubric, RubricCriterion

    vault, repository = blueprint_vault
    item = vault.practice_items["pi_comp_a"]
    rubric = Rubric(criteria=[
        RubricCriterion(id="c1", points=.5, description="Measured criterion"),
        RubricCriterion(id="c2", points=3.5, description="Not assessed"),
    ])
    vault.practice_items[item.id] = item.model_copy(update={"grading_rubric": rubric})
    result = _attempt(vault, repository, item.id, .5)
    with repository.connection() as connection:
        _pin_snapshot(connection, vault, result.attempt_id)
        connection.execute(
            "DELETE FROM grading_evidence WHERE attempt_id=? AND criterion_id='c2'",
            (result.attempt_id,),
        )
        row, = load_attempt_rows(connection, vault)
        assert row.revision_status == "exact"
        assert row.outcome == 1.0


def test_quarantine_has_zero_mass_even_without_assistance(blueprint_vault, monkeypatch):
    from learnloop.field import outcomes

    vault, repository = blueprint_vault
    result = _attempt(vault, repository, "pi_comp_a", 4, hints_used=1)
    original = outcomes.load_authoritative_observation_ledger

    def quarantined(connection):
        rows = original(connection)
        rows[0]["active_interpretation"] = {
            "quarantine_state": "quarantined",
            "response_posterior_json": '{"correct":1}',
            "shared_certainty_lcb": 1.0,
        }
        return rows

    monkeypatch.setattr(outcomes, "load_authoritative_observation_ledger", quarantined)
    with repository.connection() as connection:
        _pin_snapshot(connection, vault, result.attempt_id)
        row, = load_attempt_rows(connection, vault)
        assert row.effective_mass == 0
        assert row.mass_without_assistance == 0


def test_serving_offer_join_is_not_a_propensity(blueprint_vault):
    vault, repository = blueprint_vault
    result = _attempt(vault, repository, "pi_comp_a", 4)
    with repository.connection() as connection:
        _pin_snapshot(connection, vault, result.attempt_id)
        candidate = f"candidate-{result.attempt_id}"
        connection.execute("INSERT INTO sessions(id,started_at) VALUES ('session',?)", (NOW_ISO,))
        connection.execute(
            """INSERT INTO scheduler_slates(id,generated_at,selection_policy,session_context_json,
            config_snapshot_json,algorithm_version,created_at,updated_at)
            VALUES ('slate',?,'policy','{}','{}','test',?,?)""", (NOW_ISO,) * 3,
        )
        connection.execute(
            """INSERT INTO scheduler_slate_candidates(id,slate_id,practice_item_id,rank,selected_mode,
            priority,components_json,algorithm_version,created_at,selection_propensity)
            VALUES (?,'slate','pi_comp_a',1,'practice',1,'{}','test',?,.25)""",
            (candidate, NOW_ISO),
        )
        connection.execute(
            "INSERT INTO scheduler_offer_receipts VALUES ('slate',?,'desktop_queue','learnloop-events-v1',?)",
            (json.dumps([candidate]), NOW_ISO),
        )
        connection.execute(
            """INSERT INTO submission_intents(submission_id,session_id,practice_item_id,
            scheduler_candidate_id,entry_surface,created_at)
            VALUES ('submission','session','pi_comp_a',?,'desktop_practice',?)""",
            (candidate, NOW_ISO),
        )
        connection.execute(
            """UPDATE practice_attempts SET submission_id='submission',
            collection_version='learnloop-events-v1' WHERE id=?""", (result.attempt_id,),
        )
        row, = load_attempt_rows(connection, vault)
        assert row.serving_origin == "learner_pick"
        assert row.serving_propensity is None
        connection.execute(
            "UPDATE scheduler_slate_candidates SET components_json=? WHERE id=?",
            (json.dumps({"intervention_followup": 1}), candidate),
        )
        assert load_attempt_rows(connection, vault)[0].serving_origin == "forced_followup"
        connection.execute(
            """INSERT INTO probe_episodes(id,learning_object_id,status,trigger,algorithm_version,
            created_at,updated_at) VALUES ('episode','lo_composite','complete','initial','test',?,?)""",
            (NOW_ISO, NOW_ISO),
        )
        connection.execute(
            """INSERT INTO probe_presentations(id,probe_episode_id,practice_item_id,
            scheduler_candidate_id,state_segment_id,status,created_at,updated_at)
            VALUES ('presentation','episode','pi_comp_a',?,'segment','submitted',?,?)""",
            (candidate, NOW_ISO, NOW_ISO),
        )
        connection.execute(
            "UPDATE practice_attempts SET probe_presentation_id='presentation' WHERE id=?",
            (result.attempt_id,),
        )
        for kind in ("legacy-unverified", "unavailable_composed_offer"):
            connection.execute(
                "UPDATE scheduler_slate_candidates SET propensity_kind=?,selection_propensity=.25 WHERE id=?",
                (kind, candidate),
            )
            probe, = load_attempt_rows(connection, vault)
            assert probe.serving_origin == "system_probe"
            assert probe.serving_propensity is None
            assert data_check(connection, vault)["serving_propensity_availability"]["system_probe_unavailable"] == 1
        connection.execute(
            "UPDATE practice_attempts SET collection_version='legacy-unversioned' WHERE id=?",
            (result.attempt_id,),
        )
        assert load_attempt_rows(connection, vault)[0].serving_origin == "unknown"


@pytest.mark.durability
def test_durable_rebuild(blueprint_vault):
    test_rebuild_deterministic_and_never_writes_evidence(blueprint_vault)


@pytest.mark.parametrize("kind", ["excluded", "zero_mass", "quarantined"])
def test_zero_mass_attempt_does_not_change_later_valid_weight(blueprint_vault, monkeypatch, kind):
    from learnloop.field import outcomes

    vault, repository = blueprint_vault
    first = _attempt(vault, repository, "pi_comp_a", 4)
    second = _attempt(vault, repository, "pi_comp_a", 4)
    original = outcomes.load_authoritative_observation_ledger

    def ledger(connection):
        rows = original(connection)
        if kind == "quarantined":
            next(r for r in rows if r["attempt_id"] == first.attempt_id)["active_interpretation"] = {
                "quarantine_state": "quarantined",
                "response_posterior_json": '{"correct":1}',
                "shared_certainty_lcb": 1.0,
            }
        return rows

    monkeypatch.setattr(outcomes, "load_authoritative_observation_ledger", ledger)
    with repository.connection() as connection:
        connection.execute(
            "UPDATE practice_attempts SET created_at='2098-01-01T00:00:00Z' WHERE id=?",
            (second.attempt_id,),
        )
        if kind != "excluded":
            _pin_snapshot(connection, vault, first.attempt_id)
        _pin_snapshot(connection, vault, second.attempt_id)
        if kind == "zero_mass":
            vault.config.evidence.attempt_types["guided_walkthrough"].evidence_mass = 0
            connection.execute("UPDATE practice_attempts SET attempt_type='guided_walkthrough' WHERE id=?", (first.attempt_id,))
        rows = {r.attempt_id: r for r in load_attempt_rows(connection, vault)}
        assert rows[first.attempt_id].effective_mass == 0
        assert rows[second.attempt_id].effective_mass > 0
        # Skips are absent entirely from the fold; this is the no-row baseline.
        connection.execute("UPDATE practice_attempts SET attempt_type='skip' WHERE id=?", (first.attempt_id,))
        assert load_attempt_rows(connection, vault) == (rows[second.attempt_id],)


@pytest.mark.parametrize("receipt", ["snapshot_at", "selection_at"])
def test_future_receipt_cannot_prove_revision(blueprint_vault, receipt):
    vault, repository = blueprint_vault
    result = _attempt(vault, repository, "pi_comp_a", 4)
    with repository.connection() as connection:
        _pin_snapshot(connection, vault, result.attempt_id, **{receipt: "2099-01-01T00:00:00Z"})
        row, = load_attempt_rows(connection, vault)
        assert row.revision_status == "excluded"
        assert row.effective_mass == 0


@pytest.mark.parametrize("change", [
    {"evidence_facets": ["changed_facet"]},
    {"evidence_weights": {COMP_A: .2}},
    {"practice_mode": "retrieval"},
    {"learning_object_id": "changed_lo"},
    {"criterion_facet_weights": {"c1": {"changed_facet": 1}}},
])
def test_selected_revision_must_match_attempt_receipts(blueprint_vault, change):
    vault, repository = blueprint_vault
    result = _attempt(vault, repository, "pi_comp_a", 4)
    item = vault.practice_items["pi_comp_a"]
    vault.practice_items[item.id] = item.model_copy(update=change)
    with repository.connection() as connection:
        _pin_snapshot(connection, vault, result.attempt_id)
        assert load_attempt_rows(connection, vault)[0].revision_status == "excluded"


def test_changed_numeric_mapping_is_not_proven_by_same_targets(blueprint_vault):
    vault, repository = blueprint_vault
    item = vault.practice_items["pi_comp_a"]
    shared = {
        "evidence_facets": [COMP_A, "facet_component_b"],
        "evidence_weights": {COMP_A: .5, "facet_component_b": .5},
    }
    vault.practice_items[item.id] = item.model_copy(update={
        **shared, "criterion_facet_weights": {"c1": {COMP_A: .1, "facet_component_b": .9}},
    })
    result = _attempt(vault, repository, item.id, 4)
    vault.practice_items[item.id] = item.model_copy(update={
        **shared, "criterion_facet_weights": {"c1": {COMP_A: .9, "facet_component_b": .1}},
    })
    with repository.connection() as connection:
        _pin_snapshot(connection, vault, result.attempt_id)
        assert load_attempt_rows(connection, vault)[0].revision_status == "excluded"


def test_frozen_compiled_targets_must_match_selected_item(blueprint_vault):
    vault, repository = blueprint_vault
    item = vault.practice_items["pi_comp_a"]
    criterion = item.grading_rubric.criteria[0].model_copy(update={"targets": []})
    rubric = item.grading_rubric.model_copy(update={"criteria": [criterion]})
    vault.practice_items[item.id] = item.model_copy(update={"grading_rubric": rubric})
    result = _attempt(vault, repository, item.id, 4)
    # Prompt, rubric hash, LO, mode and coverage still agree; compiled targets
    # differ solely because the selected capability no longer matches grading.
    vault.practice_items[item.id] = vault.practice_items[item.id].model_copy(update={"capability": "retrieval"})
    with repository.connection() as connection:
        _pin_snapshot(connection, vault, result.attempt_id)
        assert load_attempt_rows(connection, vault)[0].revision_status == "excluded"


def test_requested_text_is_not_a_machine_readable_request_receipt(blueprint_vault):
    vault, repository = blueprint_vault
    result = _attempt(vault, repository, "pi_comp_a", 4)
    with repository.connection() as connection:
        connection.execute("INSERT INTO sessions(id,started_at) VALUES ('session',?)", (NOW_ISO,))
        connection.execute(
            """INSERT INTO submission_intents(submission_id,session_id,practice_item_id,
            entry_surface,created_at) VALUES ('submission','session','pi_comp_a','desktop_practice',?)""",
            (NOW_ISO,),
        )
        connection.execute(
            """UPDATE practice_attempts SET submission_id='submission',collection_version='learnloop-events-v1',
            learner_answer_md='I requested this item' WHERE id=?""", (result.attempt_id,),
        )
        row, = load_attempt_rows(connection, vault)
        assert row.serving_origin == "unknown"
        assert row.serving_propensity is None


@pytest.mark.parametrize("llm", [False, True])
@pytest.mark.parametrize("captured", [False, True])
def test_historical_subject_and_demand_ignore_current_lo(blueprint_vault, llm, captured):
    vault, repository = blueprint_vault
    item = vault.practice_items["pi_comp_a"]
    vault.practice_items[item.id] = item.model_copy(update={
        "difficulty": .9 if llm else None,
        "difficulty_source": "llm_estimate" if llm else None,
    })
    result = _attempt(vault, repository, item.id, 4)
    with repository.connection() as connection:
        _pin_snapshot(connection, vault, result.attempt_id, demand=(
            {"difficulty_b": .37, "discrimination_a": 1.4} if captured else {}
        ))
        connection.execute("UPDATE practice_attempts SET subject='historical' WHERE id=?", (result.attempt_id,))
        before, = load_attempt_rows(connection, vault)
        assert before.revision_status == "exact"
        assert before.features.subject_id == "historical"
        assert before.features.b == pytest.approx(.37 if captured else vault.config.mastery.irt.difficulty_default)
        assert before.features.difficulty_variance == (1.0 if llm else 0.0)
        assert before.features.difficulty_source.endswith("_missing_historical_prior") is not captured
        lo = vault.learning_objects[item.learning_object_id]
        vault.learning_objects[lo.id] = lo.model_copy(update={"subjects": ["changed"], "difficulty_prior": .99})
        assert load_attempt_rows(connection, vault) == (before,)
