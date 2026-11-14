"""One synthetic vault that reaches every stage of the due queue's build at once.

DL2's intent vault (``tests/intent_fakes.py``: three practised LOs due now, the placement LOs never practised, so
new material) plus: a due "Check once" on ``lo_a``; an in-progress probe episode on ``lo_svd_definition`` with two
admitted instruments; a teach-back on the same LO; a contrast pair on ``lo_c``; and a cold retry on ``pi_b1``
whose answer was shown after the task was set, so the cold lane defers it. Everything is synthetic.
"""

from __future__ import annotations

from datetime import timedelta

import yaml

from learnloop.clock import FrozenClock
from learnloop.diagnosis.probe_episodes import enter_episode
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_practice_item
from learnloop.vault.yaml_io import write_yaml

from tests.daily_plan_fakes import seed_due
from tests.helpers import NOW_ISO, add_followup_item, admit_probe_instrument_card, append_config_toml
from tests.intent_fakes import NOW, make_intent_vault

CLOCK = FrozenClock(NOW)
SESSION = "sess_due_queue"
PROBE_LO = "lo_svd_definition"
PAIR = ("pi_pair_first", "pi_pair_second")
PAIR_FACET = "f_applicability"
TEACH_BACK = "pi_svd_teach_due"
COLD_ITEM = "pi_b1"


def _pair_member(item_id: str, counterpart: str, *, expected: str, surface_family: str, difficulty: float) -> dict:
    return {
        "id": item_id,
        "learning_object_id": "lo_c",
        "practice_mode": "constructed_response",
        "prompt": f"Diagonalize the matrix in {item_id}.",
        "expected_answer": expected,
        "surface_family": surface_family,
        "difficulty": difficulty,
        "evidence_facets": [PAIR_FACET],
        "evidence_weights": {PAIR_FACET: 1.0},
        "contrast_of": counterpart,
        "differing_component": {
            "facet": PAIR_FACET,
            "capability": "method_selection",
            "structural_change": "the symmetry precondition holds in one member and not the other",
        },
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
            "fatal_errors": [],
        },
        "attempt_types_allowed": ["independent_attempt"],
        "capability": "method_selection",
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def _teach_back_payload() -> dict:
    criteria = [
        {"id": "core_definition", "points": 1.0, "tier": "core", "description": "States what U, Sigma, V are."},
        {"id": "core_geometry", "points": 1.0, "tier": "core", "description": "Explains rotate-scale-rotate."},
        {"id": "core_uniqueness", "points": 1.0, "tier": "core", "description": "Explains what is unique."},
        {"id": "transfer_rank_deficient", "points": 1.0, "tier": "transfer", "description": "A rank-deficient matrix?"},
    ]
    return {
        "id": TEACH_BACK,
        "learning_object_id": PROBE_LO,
        "subjects": None,
        "practice_mode": "teach_back",
        "attempt_types_allowed": ["teach_back"],
        "evidence_facets": ["definition", "geometry", "uniqueness"],
        "evidence_weights": {"definition": 1.0, "geometry": 1.0, "uniqueness": 1.0},
        "criterion_facet_weights": {
            "core_definition": {"definition": 1.0},
            "core_geometry": {"geometry": 1.0},
            "core_uniqueness": {"uniqueness": 1.0},
            "transfer_rank_deficient": {"definition": 1.0},
        },
        "prompt": "Teach the singular value decomposition to a curious student.",
        "expected_answer": "A full explanation of SVD: definition, geometry, uniqueness.",
        "grading_rubric": {"max_points": 4, "criteria": criteria, "fatal_errors": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def build_rich_vault(root):
    """``(vault, repository)`` at ``NOW``, before any queue build."""

    iv = make_intent_vault(root)
    repository = iv.repository
    paths = VaultPaths(iv.vault.root, iv.vault.config)
    add_followup_item(paths.root, "pi_svd_define_002")
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    # The probe episode: a misconception on the LO, two admitted instruments.
    repository.insert_error_event(
        {
            "id": "err_due_queue_slip", "learning_object_id": PROBE_LO, "error_type": "conceptual_slip",
            "severity": 0.7, "is_misconception": True, "status": "active",
            "created_at": NOW_ISO, "updated_at": NOW_ISO,
        }
    )
    admit_probe_instrument_card(repository, items=("pi_svd_define_001", "pi_svd_define_002"))
    enter_episode(vault, repository, PROBE_LO, trigger="misconception", clock=CLOCK)
    # An hour ago the session's serving build committed the probe it put first (value stopping off for that
    # build alone: with it on, these probes' value does not pay for their minutes).
    vault.config.voi_stopping.enabled = False
    build_due_queue(vault, repository, clock=FrozenClock(NOW - timedelta(hours=1)),
                    session=SchedulerSession(session_id=SESSION))
    assert repository.active_probe_presentation_for_session(SESSION) is not None
    # Added after that build, so no earlier build of the session has recorded the pair's serving.
    facets = yaml.safe_load(paths.facets_path.read_text(encoding="utf-8"))
    facets["facets"].append(
        {"id": PAIR_FACET, "kind": "applicability_condition",
         "claim": "The spectral theorem applies only to symmetric matrices."}
    )
    write_yaml(paths.facets_path, facets)
    first, second = PAIR
    write_yaml(paths.practice_item_path("linear-algebra", first), {"schema_version": 1, **_pair_member(
        first, second, expected="Q Lambda Q^T with Lambda = diag(2, 5)", surface_family="matrix_symbolic",
        difficulty=0.5)})
    write_yaml(paths.practice_item_path("linear-algebra", second), {"schema_version": 1, **_pair_member(
        second, first, expected="not orthogonally diagonalizable; the matrix is not symmetric",
        surface_family="matrix_verbal", difficulty=0.55)})
    upsert_practice_item(paths.root, _teach_back_payload(), clock=CLOCK)
    # A wide reward window and an even rate, so the exploration draw has near-ties to choose among.
    append_config_toml(paths.root, "[scheduler]\nselection_exploration_reward_window = 1.0\nselection_exploration_rate = 0.5\n")
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    reviewed = NOW - timedelta(days=10)
    for item_id in PAIR:
        seed_due(repository, item_id, due=NOW - timedelta(days=1), last=reviewed)
    # A "Check once" set eight days ago: due now.
    iv.vault = vault
    iv.choose("learning_object", "lo_a", "check_once", NOW - timedelta(days=8))
    # A cold retry on pi_b1 whose answer was shown after it was set: the cold lane defers it.
    repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="mc_due_queue", learning_object_id="lo_b",
        not_before=(NOW - timedelta(days=1)).isoformat().replace("+00:00", "Z"), selected_item_id=COLD_ITEM,
        expires_at=(NOW + timedelta(days=5)).isoformat().replace("+00:00", "Z"),
        clock=FrozenClock(NOW - timedelta(days=2)),
    )
    repository.insert_reveal_event(
        {"practice_item_id": COLD_ITEM, "learning_object_id": "lo_b", "remediation_episode_id": None,
         "source_kind": "tutor_answer", "amount": 0.3, "basis": "test"},
        clock=FrozenClock(NOW - timedelta(hours=1)),
    )
    vault = load_vault(paths.root)
    return vault, repository
