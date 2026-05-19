from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.probes import enter_probe
from learnloop.services.scheduler import SchedulerSession, build_due_queue
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault


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
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
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
