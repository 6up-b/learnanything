"""Graph-prior correction + config retirement (knowledge-model §8.1/§8.3/§16).

Covers the §16 acceptance rows: every semantic ``part_of``/``related``/
``analogous_to``/``confusable_with`` edge produces zero belief change; the
prerequisite direction is respected; the live disagreement weighting is disabled
so calibration-session ordering reverts to plain predictive rate and the signal
is thereafter shadow-only; and the retired ``cross_lo_propagation`` config is
unread (a doctor migration warning fires).
"""

from __future__ import annotations

from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.calibration_sessions import (
    episode_priority_disagreement,
    graph_propagated_prior,
    start_calibration_session,
)
from learnloop.services.doctor import run_doctor
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card, create_basic_vault

PREREQ_CONCEPT = "matrix_basics"
SVD_CONCEPT = "singular_value_decomposition"
PREREQ_LO = "lo_matrix_basics"
SVD_LO = "lo_svd_definition"


def _mastery(lo_id: str) -> MasteryState:
    return MasteryState(
        learning_object_id=lo_id,
        logit_mean=1.2,
        logit_variance=0.4,
        evidence_count=4,
        last_evidence_at=NOW_ISO,
        algorithm_version="mvp-0.6",
        updated_at=NOW_ISO,
    )


def _vault_with_edge(root: Path, relation_type: str):
    """A vault with a prereq LO -> SVD LO edge of the given relation type."""

    paths = create_basic_vault(root)
    write_yaml(
        paths.concepts_path,
        {
            "schema_version": 1,
            "concepts": {
                SVD_CONCEPT: {
                    "title": "Singular Value Decomposition",
                    "type": "procedure",
                    "aliases": ["SVD"],
                    "description": "Matrix factorization.",
                    "tags": [],
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                },
                PREREQ_CONCEPT: {
                    "title": "Matrix basics",
                    "type": "concept",
                    "aliases": [],
                    "description": "Foundational matrix operations.",
                    "tags": [],
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                },
            },
        },
    )
    write_yaml(
        paths.learning_object_path("linear-algebra", PREREQ_LO),
        {
            "schema_version": 1,
            "id": PREREQ_LO,
            "title": "Matrix basics",
            "subjects": ["linear-algebra"],
            "concept": PREREQ_CONCEPT,
            "knowledge_type": "definition",
            "status": "active",
            "contradicts": None,
            "summary": "Foundational matrix operations.",
            "prerequisites": [],
            "confusables": [],
            "difficulty_prior": 0.4,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    # source is the prerequisite of target: matrix_basics --prereq--> svd.
    write_yaml(
        paths.relations_path,
        {
            "schema_version": 1,
            "edges": [
                {
                    "id": "edge_prereq",
                    "relation_type": relation_type,
                    "source": PREREQ_CONCEPT,
                    "target": SVD_CONCEPT,
                    "strength": 0.8,
                    "rationale": "Matrix basics precede SVD.",
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            ],
        },
    )
    return paths


def test_prerequisite_prior_respects_direction(tmp_path, monkeypatch):
    paths = _vault_with_edge(tmp_path / "vault", "prerequisite")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    # Only the prerequisite LO has behavioral evidence.
    masteries = {PREREQ_LO: _mastery(PREREQ_LO)}
    monkeypatch.setattr(repository, "mastery_state", lambda lo_id: masteries.get(lo_id))

    # SVD (the dependent) is informed by its prerequisite's mastery.
    dependent_prior = graph_propagated_prior(vault, repository, SVD_LO)
    assert dependent_prior is not None
    assert dependent_prior > 0.5

    # The prerequisite is NOT informed by its downstream dependent (direction).
    assert graph_propagated_prior(vault, repository, PREREQ_LO) is None


def test_non_prerequisite_edges_produce_zero_belief_change(tmp_path, monkeypatch):
    for relation_type in ("related", "part_of", "confusable_with"):
        paths = _vault_with_edge(tmp_path / f"vault_{relation_type}", relation_type)
        vault = load_vault(paths.root)
        repository = Repository(paths.sqlite_path)
        masteries = {PREREQ_LO: _mastery(PREREQ_LO)}
        monkeypatch.setattr(repository, "mastery_state", lambda lo_id: masteries.get(lo_id))
        # A non-prerequisite edge carries no learner-belief effect (§8.1).
        assert graph_propagated_prior(vault, repository, SVD_LO) is None


# -- Calibration ordering reversion (§16 graph correction) ---------------------


def _two_lo_vault(root: Path):
    """create_basic_vault + a second LO/item on the same concept, both carded."""

    paths = create_basic_vault(root)
    write_yaml(
        paths.learning_object_path("linear-algebra", "lo_svd_apply"),
        {
            "schema_version": 1,
            "id": "lo_svd_apply",
            "title": "SVD application",
            "subjects": ["linear-algebra"],
            "concept": SVD_CONCEPT,
            "knowledge_type": "procedure",
            "status": "active",
            "contradicts": None,
            "summary": "Applying SVD.",
            "prerequisites": [],
            "confusables": [],
            "difficulty_prior": 0.55,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_apply_001"),
        {
            "schema_version": 1,
            "id": "pi_svd_apply_001",
            "learning_object_id": "lo_svd_apply",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Apply SVD.",
            "expected_answer": "Compute the factorization.",
            "difficulty": 0.55,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    return paths


def _planned_order(loaded, repository, weight, session_id, clock):
    loaded.config.probe.calibration.disagreement_weight = weight
    record = start_calibration_session(
        loaded,
        repository,
        session_id=session_id,
        learning_object_ids=[SVD_LO, "lo_svd_apply"],
        clock=clock,
    )
    session = repository.probe_calibration_session(record["calibration_session_id"])
    return list(session.planned_episode_ids)


def test_calibration_ordering_reverts_to_plain_rate(tmp_path):
    clock = FrozenClock(NOW)
    paths = _two_lo_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    from learnloop.services.probe_families import builtin_family_templates

    for template in builtin_family_templates():
        repository.upsert_probe_family_template(
            family_id=template.id,
            version=template.version,
            status="trusted",
            template=template.as_dict(),
            schema_hash=template.schema_hash(),
            clock=clock,
        )
    admit_probe_instrument_card(repository, learning_object_id=SVD_LO, card_id="card_a", items=("pi_svd_define_001",))
    admit_probe_instrument_card(
        repository,
        learning_object_id="lo_svd_apply",
        card_id="card_b",
        items=("pi_svd_apply_001",),
    )
    # Manufacture disagreement on the SVD LO: a confident claim contradicted by a
    # failing attempt (claim signal vs observed-evidence signal).
    repository.insert_learner_claim(
        {
            "id": "claim_confident",
            "claim_type": "self_rating",
            "scope_type": "learning_object",
            "scope_id": SVD_LO,
            "evidence_family": "recall",
            "claimed_level": 0.95,
            "prior_pseudo_count": 4.0,
            "source": "manual_cli",
        },
        clock=clock,
    )
    from learnloop.services.attempts import (
        AttemptDraft,
        SelfGradeInput,
        complete_self_graded_attempt,
    )

    complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="wrong",
            attempt_type="independent_attempt",
            hints_used=0,
        ),
        SelfGradeInput(criterion_points={"correctness": 0}, fatal_errors=[], confidence=4),
        clock=clock,
    )
    assert episode_priority_disagreement(loaded, repository, SVD_LO) > 0.0

    order_no_weight = _planned_order(loaded, repository, 0.0, "s_zero", clock)
    order_high_weight = _planned_order(loaded, repository, 10.0, "s_high", clock)
    assert len(order_no_weight) == 2  # both episodes rankable (positive predictive rate)
    # With the live weighting disabled, the planned order is invariant to the
    # disagreement weight — it follows the plain predictive rate. Under the old
    # boosted ordering these would diverge.
    assert order_no_weight == order_high_weight
    # The disagreement signal is still computable (shadow-only), it simply no
    # longer steers a live decision.
    assert episode_priority_disagreement(loaded, repository, SVD_LO) > 0.0


# -- Config retirement (§8.3/§15) ----------------------------------------------


def test_retired_cross_lo_propagation_config_warns(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    toml_path = paths.root / "learnloop.toml"
    text = toml_path.read_text(encoding="utf-8")
    toml_path.write_text(
        text + "\n[cross_lo_propagation.default]\nhop_decay = 0.9\n", encoding="utf-8"
    )
    report = run_doctor(paths.root)
    codes = {issue.code for issue in report.issues}
    assert "config:retired_cross_lo_propagation" in codes
    warning = next(i for i in report.issues if i.code == "config:retired_cross_lo_propagation")
    assert warning.severity == "warning"


def test_fresh_vault_has_no_retired_config_warning(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    report = run_doctor(paths.root)
    assert "config:retired_cross_lo_propagation" not in {i.code for i in report.issues}
