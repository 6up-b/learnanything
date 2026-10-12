"""Integrated PF-a projection tests; requires the foundation's migration 167."""
from datetime import timedelta

import pytest

from learnloop.db.repositories import Repository
from learnloop.substrate.family_memory import rebuild_family_memory
from learnloop.substrate.family_memory_rows import load_rows
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, create_basic_vault


def _attempt(repo, n, **overrides):
    values = {
        "id": f"attempt-{n}", "practice_item_id": "pi_svd_define_001",
        "learning_object_id": "lo_svd_definition", "practice_mode": "define",
        "attempt_type": "independent_attempt", "rubric_score": 4,
        "created_at": (NOW+timedelta(days=n)).isoformat(),
        "learner_answer_md": "PRIVATE LEARNER RESPONSE",
    }
    values.update(overrides)
    repo.insert_practice_attempt(values)


def _vault(tmp_path):
    paths = create_basic_vault(tmp_path/"vault")
    return load_vault(paths.root), Repository(paths.sqlite_path)


def _family(vault):
    from learnloop.vault.models import ActivityFamily

    family = ActivityFamily(
        id="family-test", learning_object_id="lo_svd_definition",
        idea_statement="Definition of SVD", retrieval_target="Recall the decomposition",
        created_at=NOW.isoformat(), updated_at=NOW.isoformat())
    vault.activity_families[family.id] = family
    item = vault.practice_items["pi_svd_define_001"]
    vault.practice_items[item.id] = item.model_copy(update={
        "family_id": family.id, "variant_relation": "same_target"})
    return family


def test_no_family_rebuild_does_not_touch_other_state(tmp_path, monkeypatch):
    vault, repo = _vault(tmp_path)
    _attempt(repo, 0)
    before = repo.list_all_attempts()
    monkeypatch.setattr("learnloop.substrate.family_memory.load_rows",
                        lambda *a, **kw: pytest.fail("no-family rebuild need not read outcomes"))
    assert rebuild_family_memory(vault, repo)["families"] == 0
    assert repo.list_all_attempts() == before


def test_projection_deterministic_cold_only_no_models_and_undo(tmp_path, monkeypatch):
    import learnloop.ai.client as clients

    vault, repo = _vault(tmp_path)
    _family(vault)
    for n, overrides in enumerate([
        {}, {"hints_used": 1}, {"primed": True}, {"attempt_type": "hinted_attempt"},
        {"attempt_type": "diagnostic_probe"}, {"attempt_type": "teach_back"},
        {"attempt_type": "dont_know", "rubric_score": 0}, {},
    ]):
        _attempt(repo, n, **overrides)
    repo.insert_reveal_event({
        "practice_item_id": "sibling", "learning_object_id": "lo_svd_definition",
        "source_kind": "tutor_answer", "amount": 1,
        "created_at": (NOW+timedelta(days=6, hours=12)).isoformat()})

    def forbidden(*args, **kwargs):
        pytest.fail("rebuild must not call models, generators, or live scheduling caches")

    monkeypatch.setattr(clients, "make_ai_provider_client", forbidden)
    monkeypatch.setattr(clients, "make_ai_provider_client_from_profile", forbidden)
    monkeypatch.setattr(repo, "practice_item_state", forbidden)
    monkeypatch.setattr(repo, "activity_card_state", forbidden)
    original = repo.list_all_attempts()
    first = rebuild_family_memory(vault, repo)
    with repo.connection() as connection:
        state = [tuple(r) for r in connection.execute("SELECT * FROM family_memory_state")]
    assert first["reviews"] == 2
    assert first == rebuild_family_memory(vault, repo)
    with repo.connection() as connection:
        assert state == [tuple(r) for r in connection.execute("SELECT * FROM family_memory_state")]
    assert repo.list_all_attempts() == original
    item = vault.practice_items["pi_svd_define_001"]
    vault.practice_items[item.id] = item.model_copy(update={"family_id": None, "variant_relation": None})
    assert rebuild_family_memory(vault, repo)["families"] == 0
    with repo.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM family_memory_state").fetchone()[0] == 0


@pytest.mark.parametrize("relation,count", [("same_target", 1), ("isomorph", 1), ("near", 0), ("far", 0)])
def test_projection_relation_gate(tmp_path, relation, count):
    vault, repo = _vault(tmp_path)
    _family(vault)
    item = vault.practice_items["pi_svd_define_001"]
    vault.practice_items[item.id] = item.model_copy(update={"variant_relation": relation})
    _attempt(repo, 0)
    assert rebuild_family_memory(vault, repo)["reviews"] == count


@pytest.mark.durability
def test_family_projection_durable_repeat(tmp_path):
    vault, repo = _vault(tmp_path)
    _family(vault)
    _attempt(repo, 0)
    first = rebuild_family_memory(vault, repo)
    assert first == rebuild_family_memory(vault, Repository.attach(repo.sqlite_path))


def test_registry_has_exactly_one_owner():
    from learnloop.substrate.rebuild_orchestrator import derived_table_owners, validate_replayer_registry

    validate_replayer_registry()
    assert derived_table_owners()["family_memory_state"] == ("family_memory",)


def test_dont_know_is_full_mass_observed_failure(tmp_path):
    vault, repo = _vault(tmp_path)
    _attempt(repo, 0, attempt_type="dont_know", rubric_score=0)
    rows, _ = load_rows(vault, repo, legacy_fallback="current_content")
    assert rows[0].outcome == 0
    assert rows[0].features.effective_mass == 1.0


def test_legacy_revision_fallback_is_explicit_and_reveal_is_past_only(tmp_path):
    vault, repo = _vault(tmp_path)
    _attempt(repo, 0)
    _attempt(repo, 2)
    repo.insert_reveal_event({
        "practice_item_id": "sibling", "learning_object_id": "lo_svd_definition",
        "source_kind": "tutor_answer", "amount": 1,
        "created_at": (NOW+timedelta(days=1)).isoformat()})
    strict, source = load_rows(vault, repo)
    assert source["revision_counts"] == {"excluded": 2}
    assert all(r.exclusion == "missing_graded_revision" for r in strict)
    reconstructed, source = load_rows(vault, repo, legacy_fallback="current_content",
                                      for_projection=True)
    assert source["revision_counts"] == {"reconstructed_current": 2}
    assert reconstructed[0].cold and not reconstructed[1].cold
    assert all(r.exclusion is None for r in reconstructed)


def test_legacy_calibration_is_not_invented_for_idea_hier(tmp_path):
    vault, repo = _vault(tmp_path)
    _attempt(repo, 0)
    rows, _ = load_rows(vault, repo, legacy_fallback="current_content")
    assert rows[0].features.effective_mass == 0
    assert rows[0].memory_eligible
    projection, _ = load_rows(vault, repo, legacy_fallback="current_content",
                              for_projection=True)
    assert projection[0].features.effective_mass == 0


def test_old_reveal_does_not_permanently_veto_spaced_reviews(tmp_path):
    vault, repo = _vault(tmp_path)
    _family(vault)
    for day in (0, 2, 7):
        _attempt(repo, day)
    repo.insert_reveal_event({
        "practice_item_id": "sibling", "learning_object_id": "lo_svd_definition",
        "source_kind": "tutor_answer", "amount": .1,
        "created_at": (NOW+timedelta(days=1)).isoformat()})
    rows, _ = load_rows(vault, repo, legacy_fallback="current_content")
    assert [row.cold for row in rows] == [True, False, True]
    assert rebuild_family_memory(vault, repo)["reviews"] == 2


@pytest.mark.parametrize("status,expected", [("pass", True), ("fail", False), ("unknown", False)])
def test_receipt_owns_measurement_window_and_unassisted_claim(tmp_path, status, expected):
    import json

    vault, repo = _vault(tmp_path)
    _attempt(repo, 0)
    _attempt(repo, 7)
    # Before the explicitly recorded cold measurement window: not a permanent
    # veto. The receipt can still reject coldness for another recorded channel.
    repo.insert_reveal_event({
        "practice_item_id": "sibling", "learning_object_id": "lo_svd_definition",
        "source_kind": "tutor_answer", "amount": 1,
        "created_at": (NOW+timedelta(days=1)).isoformat()})
    with repo.connection() as connection:
        connection.execute(
            """INSERT INTO coldness_receipts
               (id, lane, stage, cold_attempt_id, dimensions_json, derived_json,
                telemetry_coverage_json, receipt_version, created_at)
               VALUES ('receipt', 'repair_cold_retry', 'final', 'attempt-7',
                       ?, '{}', ?, 'test', ?)""",
            (json.dumps({"unassisted": {"status": status},
                         "answer_leakage": {"status": "pass"}}),
             json.dumps({"interval": {"from": (NOW+timedelta(days=2)).isoformat(),
                                       "to": (NOW+timedelta(days=7)).isoformat()}}),
             (NOW+timedelta(days=7)).isoformat()))
    rows, _ = load_rows(vault, repo, legacy_fallback="current_content")
    assert rows[-1].cold is expected


def test_regraded_label_is_not_backdated_into_prequential_training(tmp_path, monkeypatch):
    vault, repo = _vault(tmp_path)
    _attempt(repo, 0)
    monkeypatch.setattr(repo, "attempt_regrade_marker", lambda _: {"at": "future"})
    rows, _ = load_rows(vault, repo, legacy_fallback="current_content")
    assert rows[0].exclusion == "regraded_after_attempt"


def test_reveal_read_failure_is_not_reported_as_cold(tmp_path, monkeypatch):
    from learnloop.attempts.reveal_ledger import production_admissibility

    vault, repo = _vault(tmp_path)
    _attempt(repo, 0)

    def broken(**kwargs):
        raise RuntimeError("ledger unavailable")

    monkeypatch.setattr(repo, "reveal_events_for_target", broken)
    # Existing live callers retain best-effort behavior.
    assert production_admissibility(
        repo, practice_item_id="pi_svd_define_001", produced_at=NOW.isoformat()).admissible
    with pytest.raises(RuntimeError, match="ledger unavailable"):
        load_rows(vault, repo, legacy_fallback="current_content")


@pytest.mark.parametrize("score,points,rating", [(1, 5, 2), (3, 3.5, 3), (4, 4.5, 4)])
def test_fsrs_rating_uses_capped_rounded_grade_not_continuous_fraction(
        tmp_path, monkeypatch, score, points, rating):
    from types import SimpleNamespace

    vault, repo = _vault(tmp_path)
    _attempt(repo, 0, rubric_score=score)
    item = vault.practice_items["pi_svd_define_001"]
    monkeypatch.setattr(repo, "fetch_grading_evidence",
                        lambda _: [SimpleNamespace(points_awarded=points)])
    monkeypatch.setattr("learnloop.substrate.family_memory_rows._graded_item",
                        lambda *args: (item, {"rubric_total": 5, "rubric_max_points": 4}))
    rows, _ = load_rows(vault, repo)
    assert rows[0].outcome == points / 5
    assert rows[0].rating == rating


def test_exact_revision_requires_snapshot_hash_and_graded_contract(tmp_path):
    from types import SimpleNamespace
    import hashlib
    import json
    from learnloop.learner.assessment_contracts import compile_assessment_contract
    from learnloop.substrate.family_memory_rows import _graded_item

    vault, repo = _vault(tmp_path)
    item = vault.practice_items["pi_svd_define_001"]
    contract = compile_assessment_contract(vault, item)
    raw = json.dumps(item.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    snapshot_hash = hashlib.sha256(raw.encode()).hexdigest()
    at = NOW.isoformat()
    attempt = {"practice_item_id": item.id, "scheduler_candidate_id": "candidate", "created_at": at}
    evidence = [SimpleNamespace(assessment_contract_version_id="contract")]
    with repo.connection() as connection:
        connection.execute(
            """INSERT INTO assessment_contract_versions
               (id, practice_item_id, contract_hash, contract_json, schema_version, created_at)
               VALUES ('contract', ?, 'contract-hash', ?, 1, ?)""",
            (item.id, json.dumps(contract), at))
        connection.execute(
            "INSERT INTO practice_item_snapshots VALUES (?, ?, ?, ?)",
            (snapshot_hash, item.id, raw, at))
        connection.execute(
            """INSERT INTO decision_features
               (id, decision_id, decision_type, ability_vector_json,
                item_demand_vector_json, context_json, algorithm_version, created_at)
               VALUES ('feature', 'candidate', 'selection', '{}', ?, '{}', 'mvp-0.8', ?)""",
            (json.dumps({"content_hash": snapshot_hash}), at))
        found, graded = _graded_item(connection, attempt, evidence)
        assert found == item and graded == contract
        found, _ = _graded_item(connection, {**attempt, "scheduler_candidate_id": "missing"}, evidence)
        assert found is None
        found, _ = _graded_item(connection, attempt, [])
        assert found is None
        # The hash is of the stored bytes, not a reserialization, and the
        # selected row must still agree with the graded prompt contract.
        bad_hash = hashlib.sha256((raw + " ").encode()).hexdigest()
        connection.execute(
            "INSERT INTO practice_item_snapshots VALUES (?, ?, ?, ?)",
            (bad_hash, item.id, raw, at))
        connection.execute(
            """INSERT INTO decision_features
               (id, decision_id, decision_type, ability_vector_json,
                item_demand_vector_json, context_json, algorithm_version, created_at)
               VALUES ('bad-feature', 'bad-candidate', 'selection', '{}', ?, '{}', 'mvp-0.8', ?)""",
            (json.dumps({"content_hash": bad_hash}), at))
        found, _ = _graded_item(
            connection, {**attempt, "scheduler_candidate_id": "bad-candidate"}, evidence)
        assert found is None
