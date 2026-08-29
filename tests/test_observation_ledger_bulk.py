from __future__ import annotations

import json

from learnloop.clock import FrozenClock
from learnloop.db.stores.observation_ledger import (
    load_authoritative_observation_ledger,
    load_canonical_observation_ledger,
)
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.substrate.canonical_projection import (
    p0_effective_evidence_mass,
    project_canonical_facet_state,
)
from learnloop.attempts.effective_observation import (
    load_effective_observation_references,
)
from learnloop.learner.facet_evidence_timeline import facet_evidence_timeline
from learnloop.attempts.outcome_schemas import COARSE_RESPONSE_SLUG
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version


def _insert_attempts(repository: Repository, count: int) -> None:
    for index in range(count):
        attempt_id = f"attempt_{index:03d}"
        repository.insert_practice_attempt(
            {
                "id": attempt_id,
                "practice_item_id": "item",
                "learning_object_id": "lo",
                "practice_mode": "short_answer",
                "attempt_type": "independent_attempt",
                "hints_used": index % 2,
                "primed": index % 3 == 0,
                "created_at": NOW_ISO,
                "updated_at": NOW_ISO,
            }
        )
        # Deliberately insert the lexically later id first with an identical
        # timestamp + criterion.  Replay order must use the id tie-breaker, not
        # insertion/rowid order.
        repository.insert_grading_evidence(
            attempt_id,
            [
                {
                    "id": f"z_{index:03d}",
                    "criterion_id": "same",
                    "points_awarded": 2.0,
                    "grader_tier": 1,
                    "created_at": NOW_ISO,
                },
                {
                    "id": f"a_{index:03d}",
                    "criterion_id": "same",
                    "points_awarded": 1.0,
                    "grader_tier": 1,
                    "created_at": NOW_ISO,
                },
            ],
        )


def _read_statements(statements: list[str]) -> list[str]:
    return [
        statement
        for statement in statements
        if statement.lstrip().upper().startswith(("SELECT", "WITH"))
    ]


def test_observation_ledgers_have_constant_query_budget_and_stable_order(tmp_path):
    repository = Repository(tmp_path / "state.db")
    _insert_attempts(repository, 24)

    with repository.connection() as connection:
        statements: list[str] = []
        connection.set_trace_callback(statements.append)
        base = load_canonical_observation_ledger(connection)
        connection.set_trace_callback(None)

        assert len(base) == 24
        assert len(_read_statements(statements)) == 2
        assert [row["attempt_id"] for row in base] == sorted(
            row["attempt_id"] for row in base
        )
        assert [row["points_awarded"] for row in base[0]["evidence"]] == [1.0, 2.0]
        assert base[0]["primed"] is True

        statements.clear()
        connection.set_trace_callback(statements.append)
        authoritative = load_authoritative_observation_ledger(connection)
        connection.set_trace_callback(None)

    # Two base scans + four lineage scans, independent of attempt count.  The
    # previous implementation executed 1 + N + up to 3N reads.
    assert len(_read_statements(statements)) == 6
    assert [row["attempt_id"] for row in authoritative] == [
        row["attempt_id"] for row in base
    ]
    assert all(row["active_interpretation"] is None for row in authoritative)


def _vault_and_repository(tmp_path, *, version: str = "mvp-0.7"):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, version)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def test_primed_provenance_reaches_projection_and_blocks_certification(tmp_path):
    vault, repository = _vault_and_repository(tmp_path)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="A = U Sigma V transpose.",
            attempt_type="independent_attempt",
            primed=True,
        ),
        SelfGradeInput(
            criterion_points={"correctness": 4}, fatal_errors=[], confidence=4
        ),
        clock=FrozenClock(NOW),
    )

    ledger = repository.canonical_observation_ledger()
    assert len(ledger) == 1 and ledger[0]["primed"] is True

    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))
    cells = repository.facet_capability_evidence_all()
    assert cells, "the primed observation still belongs in the evidence audit"
    assert sum(cell.certification_credit for cell in cells) == 0.0


def test_pure_diagnostic_is_unassisted_but_cannot_bank_certification(tmp_path):
    """Assistance is a display fact, not a proxy for evidence eligibility."""

    vault, repository = _vault_and_repository(tmp_path)
    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="A = U Sigma V transpose.",
            attempt_type="diagnostic_probe",
            # The attempt resolver permits diagnostic administration only when
            # it was presented through the probe lane. An invalid id is stripped
            # before persistence, but still exercises the immutable attempt-type
            # policy this replay regression targets.
            probe_presentation_id="missing_presentation",
        ),
        SelfGradeInput(
            criterion_points={"correctness": 4}, fatal_errors=[], confidence=4
        ),
        clock=FrozenClock(NOW),
    )

    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))
    cells = repository.facet_capability_evidence_all()
    assert cells, "diagnostic evidence remains visible in the belief audit"
    assert sum(cell.certification_credit for cell in cells) == 0.0

    series = facet_evidence_timeline(vault, repository, cells[0].facet_id)
    point = next(point for point in series if point.attempt_id == result.attempt_id)
    assert point.assisted is False
    assert point.demonstrated == 0.0


def test_recorded_near_clone_disqualification_survives_both_replays(tmp_path):
    vault, repository = _vault_and_repository(tmp_path)
    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="A = U Sigma V transpose.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(
            criterion_points={"correctness": 4}, fatal_errors=[], confidence=4
        ),
        clock=FrozenClock(NOW),
    )
    repository.record_causal_activity_classification(
        attempt_id=result.attempt_id,
        contamination_class="verification",
        near_clone=True,
        near_clone_basis="shared_surface_group",
        source="regression_test",
        clock=FrozenClock(NOW),
    )

    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))
    cells = repository.facet_capability_evidence_all()
    assert cells
    assert sum(cell.certification_credit for cell in cells) == 0.0

    series = facet_evidence_timeline(vault, repository, cells[0].facet_id)
    point = next(point for point in series if point.attempt_id == result.attempt_id)
    assert point.assisted is False
    assert point.demonstrated == 0.0


def test_p0_replays_bulk_load_calibration_references_once(tmp_path, monkeypatch):
    """Three model hashes, including legacy LCB reconstruction, stay O(1)."""

    vault, repository = _vault_and_repository(tmp_path, version="mvp-0.9")
    for index in range(3):
        complete_self_graded_attempt(
            vault,
            repository,
            AttemptDraft(
                practice_item_id="pi_svd_define_001",
                learner_answer_md=f"A = U Sigma V transpose ({index}).",
                attempt_type="independent_attempt",
            ),
            SelfGradeInput(
                criterion_points={"correctness": 4}, fatal_errors=[], confidence=4
            ),
            clock=FrozenClock(NOW),
        )

    ledger = repository.canonical_observation_ledger_v2()
    interpretations = [row["active_interpretation"] for row in ledger]
    assert len(interpretations) == 3 and all(interpretations)
    schema = repository.fetch_outcome_schema_version(slug=COARSE_RESPONSE_SLUG)
    assert schema is not None

    model_ids: list[str] = []
    for index, interpretation in enumerate(interpretations):
        raw = repository.raw_grade_event(interpretation["raw_grade_event_id"])
        assert raw is not None
        emission = f"{raw['observed_class']}|{raw['confidence_bucket']}"
        content_hash = f"projection-bulk-model-{index}"
        model_id = repository.insert_calibration_model(
            model={
                "semver": f"99.0.{index}",
                "content_hash": content_hash,
                "scope_level": "global",
                "outcome_schema_id": schema["schema_id"],
                "outcome_schema_version": int(schema["version"]),
                "backoff_chain_json": "[]",
                "status": "heuristic",
            },
            alphas={
                "success": {emission: 9.0},
                "partial_success": {emission: 2.0},
                "other": {emission: 1.0},
            },
            clock=FrozenClock(NOW),
        )
        model_ids.append(model_id)
        with repository.connection() as connection:
            connection.execute(
                """
                UPDATE grade_interpretations
                   SET calibration_model_id = ?, calibration_model_hash = ?,
                       shared_certainty_lcb = ?
                 WHERE id = ?
                """,
                (
                    model_id,
                    content_hash,
                    0.6 if index < 2 else None,
                    interpretation["id"],
                ),
            )
            connection.commit()

    # Force one historical interpretation through the fallback that needs the
    # pooled alpha lineage and raw emission. Its non-point posterior prevents
    # the deterministic short-circuit from hiding those reference reads.
    legacy_interpretation = interpretations[-1]
    with repository.connection() as connection:
        connection.execute(
            """
            UPDATE grade_interpretations
               SET response_posterior_json = ?, reference_prior_ids_json = ?
             WHERE id = ?
            """,
            (
                json.dumps(
                    {"success": 0.8, "partial_success": 0.1, "other": 0.1}
                ),
                json.dumps(model_ids),
                legacy_interpretation["id"],
            ),
        )
        connection.commit()

    ledger = repository.canonical_observation_ledger_v2()
    with repository.pinned():
        connection = repository.connection()
        statements: list[str] = []
        connection.set_trace_callback(statements.append)
        references = load_effective_observation_references(
            repository,
            (row.get("active_interpretation") for row in ledger),
        )
        connection.set_trace_callback(None)
    # Models, pooled alphas, raw events, and the one fitted-prior lookup: four
    # reads whatever the number of attempts, hashes, or lineage members.
    assert len(_read_statements(statements)) == 4
    assert set(references.calibration_models_by_hash) == {
        f"projection-bulk-model-{index}" for index in range(3)
    }
    # Bulk and compatibility paths are numerically identical, including the
    # legacy alpha/raw-grade fallback.
    for row in ledger:
        direct = p0_effective_evidence_mass(
            repository,
            interpretation=row.get("active_interpretation"),
            attempt_type_mass=1.0,
        )
        bulk = p0_effective_evidence_mass(
            repository,
            interpretation=row.get("active_interpretation"),
            attempt_type_mass=1.0,
            references=references,
        )
        assert bulk == direct

    calls = {"models": 0, "alphas": 0, "raw": 0, "fitted": 0}
    original_models = repository.calibration_models_by_hashes
    original_alphas = repository.calibration_alphas_by_model_ids
    original_raw = repository.raw_grade_events_by_ids
    original_fitted = repository.active_fitted_parameters

    def models_once(values):
        calls["models"] += 1
        return original_models(values)

    def alphas_once(values):
        calls["alphas"] += 1
        return original_alphas(values)

    def raw_once(values):
        calls["raw"] += 1
        return original_raw(values)

    def fitted_once(scope):
        calls["fitted"] += 1
        return original_fitted(scope)

    monkeypatch.setattr(repository, "calibration_models_by_hashes", models_once)
    monkeypatch.setattr(repository, "calibration_alphas_by_model_ids", alphas_once)
    monkeypatch.setattr(repository, "raw_grade_events_by_ids", raw_once)
    monkeypatch.setattr(repository, "active_fitted_parameters", fitted_once)
    for name in (
        "find_calibration_model_by_hash",
        "fetch_calibration_alphas",
        "raw_grade_event",
    ):
        monkeypatch.setattr(
            repository,
            name,
            lambda *_args, _name=name, **_kwargs: (_ for _ in ()).throw(
                AssertionError(f"P0 replay used singular lookup {_name}")
            ),
        )

    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))
    assert calls == {"models": 1, "alphas": 1, "raw": 1, "fitted": 1}

    cells = repository.facet_capability_evidence_all()
    assert cells
    series = facet_evidence_timeline(vault, repository, cells[0].facet_id)
    assert series
    assert calls == {"models": 2, "alphas": 2, "raw": 2, "fitted": 2}


def test_canonical_projection_bulk_loads_historical_contracts_once(
    tmp_path, monkeypatch
):
    vault, repository = _vault_and_repository(tmp_path)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="A = U Sigma V transpose.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(
            criterion_points={"correctness": 4}, fatal_errors=[], confidence=4
        ),
        clock=FrozenClock(NOW),
    )

    calls = 0
    original_bulk = repository.effective_assessment_contract_versions

    def bulk_once(version_ids, *, projection_version):
        nonlocal calls
        calls += 1
        return original_bulk(version_ids, projection_version=projection_version)

    monkeypatch.setattr(
        repository, "effective_assessment_contract_versions", bulk_once
    )
    monkeypatch.setattr(
        repository,
        "effective_assessment_contract_version",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("canonical replay must not load a contract per attempt")
        ),
    )

    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))
    assert calls == 1


def test_learning_outcome_labels_compute_all_intervening_counts_in_one_read(
    tmp_path,
):
    repository = Repository(tmp_path / "state.db")
    attempts = [
        ("source_0", "lo", "item_a", "2026-05-19T08:00:00Z"),
        ("source_1a", "lo", "item_a", "2026-05-19T09:00:00Z"),
        ("source_1b", "lo", "item_b", "2026-05-19T09:00:00Z"),
        ("other_lo", "other", "item_x", "2026-05-19T10:00:00Z"),
        ("source_3", "lo", "item_b", "2026-05-19T11:00:00Z"),
        ("current", "lo", "item_a", "2026-05-19T12:00:00Z"),
    ]
    for attempt_id, learning_object_id, item_id, created_at in attempts:
        repository.insert_practice_attempt(
            {
                "id": attempt_id,
                "practice_item_id": item_id,
                "learning_object_id": learning_object_id,
                "practice_mode": "short_answer",
                "attempt_type": "independent_attempt",
                "correctness": 1.0,
                "rubric_score": 4,
                "created_at": created_at,
                "updated_at": created_at,
            }
        )

    with repository.connection() as connection:
        statements: list[str] = []
        connection.set_trace_callback(statements.append)
        repository._insert_learning_outcome_labels(
            connection,
            {"id": "current"},
            algorithm_version="test",
        )
        connection.set_trace_callback(None)
        connection.commit()
        rows = connection.execute(
            """
            SELECT source_attempt_id, intervening_attempt_count
              FROM learning_outcome_labels
             WHERE outcome_attempt_id = 'current'
             ORDER BY source_attempt_id
            """
        ).fetchall()

    # One current-row lookup + one grouped source/range query.  Previously this
    # was 2 + one COUNT query for every source (up to 22 reads per attempt).
    assert len(_read_statements(statements)) == 2
    assert {
        row["source_attempt_id"]: row["intervening_attempt_count"] for row in rows
    } == {
        "source_0": 3,
        "source_1a": 1,
        "source_1b": 1,
        "source_3": 0,
    }


def test_recent_attempts_bulk_query_is_constant_and_partitioned(tmp_path):
    repository = Repository(tmp_path / "state.db")
    for learning_object_id in ("lo_a", "lo_b", "lo_c"):
        for index in range(4):
            repository.insert_practice_attempt(
                {
                    "id": f"{learning_object_id}_{index}",
                    "practice_item_id": f"item_{learning_object_id}",
                    "learning_object_id": learning_object_id,
                    "practice_mode": "short_answer",
                    "attempt_type": "independent_attempt",
                    # Equal timestamps deliberately exercise the stable id
                    # tie-break inside each window partition.
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            )

    with repository.pinned():
        connection = repository.connection()
        statements: list[str] = []
        connection.set_trace_callback(statements.append)
        grouped = repository.list_recent_attempts_by_learning_objects(
            ("lo_c", "lo_a", "missing", "lo_b"), limit=2
        )
        connection.set_trace_callback(None)

    assert len(_read_statements(statements)) == 1
    assert grouped["missing"] == []
    assert {
        learning_object_id: [attempt["id"] for attempt in attempts]
        for learning_object_id, attempts in grouped.items()
        if learning_object_id != "missing"
    } == {
        "lo_a": ["lo_a_3", "lo_a_2"],
        "lo_b": ["lo_b_3", "lo_b_2"],
        "lo_c": ["lo_c_3", "lo_c_2"],
    }
