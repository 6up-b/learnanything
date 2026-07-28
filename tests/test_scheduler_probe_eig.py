from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.probe_episodes import enter_episode
from learnloop.services.scheduler import SchedulerSession, build_due_queue
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card, create_basic_vault


def _setup_probe_vault(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    # Remove goals so probe_eig is the only thing that can keep the item in the queue.
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": []})
    repository = Repository(paths.sqlite_path)
    repository.insert_error_event(
        {
            "id": "err_conceptual_slip",
            "learning_object_id": "lo_svd_definition",
            "error_type": "conceptual_slip",
            "severity": 0.7,
            "is_misconception": True,
            "status": "active",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )
    loaded = load_vault(vault_root)
    # Probe redesign §9: probe candidacy requires an executable instrument
    # binding, so the scheduler tests admit a card for the basic vault's item.
    admit_probe_instrument_card(repository)
    enter_episode(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    return vault_root, repository


def test_probe_eig_included_only_for_in_progress_probe(tmp_path):
    vault_root, repository = _setup_probe_vault(tmp_path)
    loaded = load_vault(vault_root)

    queue = build_due_queue(
        loaded,
        repository,
        clock=FrozenClock(NOW),
        session=SchedulerSession(session_id="s1"),
    )

    assert [item.practice_item_id for item in queue] == ["pi_svd_define_001"]
    assert queue[0].components["probe_eig"] > 0.0

    events = repository.elicitation_events("s1")
    assert len(events) == 1
    assert events[0]["policy"] == "probe_eig"
    assert events[0]["selected_practice_item_id"] == "pi_svd_define_001"


def test_short_session_suppresses_probe_eig(tmp_path):
    vault_root, repository = _setup_probe_vault(tmp_path)
    loaded = load_vault(vault_root)

    short_queue = build_due_queue(
        loaded,
        repository,
        clock=FrozenClock(NOW),
        session=SchedulerSession(session_id="short", available_minutes=10),
        persist_explanations=False,
    )
    normal_queue = build_due_queue(
        loaded,
        repository,
        clock=FrozenClock(NOW),
        session=SchedulerSession(session_id="normal"),
        persist_explanations=False,
    )

    short_item = next(i for i in short_queue if i.practice_item_id == "pi_svd_define_001")
    normal_item = next(i for i in normal_queue if i.practice_item_id == "pi_svd_define_001")
    assert short_item.components["probe_eig"] == 0.0
    assert normal_item.components["probe_eig"] > 0.0
    assert normal_item.priority > short_item.priority


def test_short_session_keeps_probe_eig_when_probe_is_only_reason(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": []})
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(vault_root)
    admit_probe_instrument_card(repository)
    enter_episode(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    queue = build_due_queue(
        loaded,
        repository,
        clock=FrozenClock(NOW),
        session=SchedulerSession(session_id="short", available_minutes=10),
        persist_explanations=False,
    )

    assert [item.practice_item_id for item in queue] == ["pi_svd_define_001"]
    assert queue[0].components["probe_eig"] > 0.0


def test_scheduler_explanations_persist_only_for_named_sessions(tmp_path):
    vault_root, repository = _setup_probe_vault(tmp_path)
    loaded = load_vault(vault_root)

    build_due_queue(loaded, repository, clock=FrozenClock(NOW))

    assert repository.latest_scheduler_explanation("pi_svd_define_001") is None


def test_probe_eig_persisted_in_scheduler_explanation(tmp_path):
    vault_root, repository = _setup_probe_vault(tmp_path)
    loaded = load_vault(vault_root)

    build_due_queue(
        loaded,
        repository,
        clock=FrozenClock(NOW),
        session=SchedulerSession(session_id="s2"),
    )

    explanation = repository.latest_scheduler_explanation("pi_svd_define_001")
    assert explanation is not None
    assert "probe_eig" in explanation["components"]
    assert explanation["components"]["probe_eig"] > 0.0
    reward = explanation["target_scope"]["selection_reward"]
    assert reward["probe_eig"]["hypothesis"]["reduction"] > 0.0
    assert reward["probe_eig"]["lo_mastery"]["reduction"] > 0.0
    assert reward["probe_eig"]["facet_recall"]["reduction"] >= 0.0
    assert reward["components"]["probe_eig_total"] >= reward["components"]["probe_eig_hypothesis"]


def test_probe_eig_uses_prospective_familiarity_discount(tmp_path):
    """Facet-overlap familiarity from a DIFFERENT surface discounts probe EIG.

    An attempt on the probe item itself no longer merely discounts — the
    never-before-seen gate hard-excludes the whole surface group from probe
    candidacy (see test_diagnostic_probe_freshness.py). The discount path pinned
    here is the surviving one: incidental practice on a sibling surface with
    overlapping facets makes the probe's evidence less independent.
    """

    from learnloop.vault.writer import upsert_practice_item

    vault_root, repository = _setup_probe_vault(tmp_path)
    upsert_practice_item(
        vault_root,
        {
            "id": "pi_svd_sibling_surface",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "A fresh sibling surface on the same facet.",
            "expected_answer": "A matrix factorization into U, Sigma, and V transpose.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=FrozenClock(NOW),
    )
    loaded = load_vault(vault_root)

    baseline_queue = build_due_queue(
        loaded,
        repository,
        clock=FrozenClock(NOW),
        session=SchedulerSession(session_id="baseline"),
        persist_explanations=False,
    )
    baseline_item = next(
        i for i in baseline_queue if i.practice_item_id == "pi_svd_define_001"
    )
    complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_sibling_surface",
            learner_answer_md="I do not know",
            attempt_type="dont_know",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )

    discounted_queue = build_due_queue(
        loaded,
        repository,
        clock=FrozenClock(NOW),
        session=SchedulerSession(session_id="discounted"),
        persist_explanations=False,
    )
    discounted_item = next(
        i for i in discounted_queue if i.practice_item_id == "pi_svd_define_001"
    )

    assert discounted_item.components["probe_eig_familiarity_discount"] < 1.0
    assert discounted_item.components["probe_eig"] < baseline_item.components["probe_eig"]
    assert discounted_item.components["probe_eig"] == (
        discounted_item.components["probe_eig_raw"]
        * discounted_item.components["probe_eig_familiarity_discount"]
    )
    assert discounted_item.reward_debug["probe_eig"]["independent_evidence_discount"] == discounted_item.components["probe_eig_familiarity_discount"]


def test_readiness_factor_is_persisted_without_changing_priority(tmp_path):
    vault_root, repository = _setup_probe_vault(tmp_path)
    loaded = load_vault(vault_root)

    baseline = build_due_queue(
        loaded,
        repository,
        clock=FrozenClock(NOW),
        session=SchedulerSession(session_id="baseline"),
        persist_explanations=False,
    )
    with_readiness = build_due_queue(
        loaded,
        repository,
        clock=FrozenClock(NOW),
        session=SchedulerSession(session_id="ready", energy="medium", available_minutes=40),
    )

    baseline_item = next(i for i in baseline if i.practice_item_id == "pi_svd_define_001")
    ready_item = next(i for i in with_readiness if i.practice_item_id == "pi_svd_define_001")
    explanation = repository.latest_scheduler_explanation("pi_svd_define_001")

    assert ready_item.readiness_factor == 0.875
    assert ready_item.priority == baseline_item.priority
    assert explanation is not None
    assert explanation["readiness_factor"] == 0.875
