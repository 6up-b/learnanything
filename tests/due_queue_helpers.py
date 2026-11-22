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


# -- the admission's paths ------------------------------------------------------------------------------------------

#: Items :func:`build_gate_vault` adds: an unbound diagnostic surface on the probe's LO, a dialogue-turn instance,
#: and a prompt that embeds a picture (a phone holds it for the desktop).
UNBOUND_PROBE = "pi_svd_probe_unbound"
MICROPROBE = "pi_a_microprobe"
ORPHAN = "pi_a_orphan"
SEEN_ON_PROBE_LO = "pi_svd_recall_seen"
FIGURE_ITEM = "pi_c_figure"
#: The item a phone build's session left for the desktop (``DeviceFilter.left_for_desktop``).
LEFT_FOR_DESKTOP = "pi_c1"


def _extra_item(item_id: str, learning_object_id: str, *, mode: str, prompt: str) -> dict:
    return {
        "schema_version": 1,
        "id": item_id,
        "learning_object_id": learning_object_id,
        "practice_mode": mode,
        "prompt": prompt,
        "expected_answer": "An answer.",
        "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0},
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
            "fatal_errors": [],
        },
        "attempt_types_allowed": ["independent_attempt"],
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def _edit_item(paths: VaultPaths, item_id: str, **changes) -> None:
    from learnloop.vault.yaml_io import read_yaml

    path = paths.practice_item_path("linear-algebra", item_id)
    write_yaml(path, {**read_yaml(path), **changes})


def build_gate_vault(root):
    """``(vault, repository)``: :func:`build_rich_vault` where the admission withholds items for most of its reasons.

    Retired (``pi_eig_hard``), an inactive state (``pi_eig_easy``), an exam reservation (``pi_pair_second``), a
    reserved certification check (``pi_c2``), a dialogue-turn instance, an administered diagnostic probe
    (``pi_a2``), an item whose LO is gone, a put-away LO (``lo_spectral``), a diagnostic surface outside any
    episode (``pi_eig_mid``), placement's assumed LO (``lo_diag``, "I know this"), a paused LO (``lo_b``), and
    inside the probe episode two diagnostic surfaces: an instrument the episode values (``pi_svd_define_002``) and
    one with no instrument binding.
    """

    from learnloop.intent.control import Scope, apply_choice
    from learnloop.placement.decisions import record_self_report

    vault, repository = build_rich_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    _edit_item(paths, "pi_eig_hard", status="retired")
    _edit_item(paths, "pi_eig_mid", practice_mode="diagnostic_probe")
    _edit_item(paths, "pi_svd_define_002", practice_mode="diagnostic_probe")
    write_yaml(paths.practice_item_path("linear-algebra", UNBOUND_PROBE), _extra_item(
        UNBOUND_PROBE, PROBE_LO, mode="diagnostic_probe", prompt="State the SVD of a 2x2 rotation."))
    write_yaml(paths.practice_item_path("linear-algebra", MICROPROBE), _extra_item(
        MICROPROBE, "lo_a", mode="short_answer", prompt="One dialogue turn."))
    write_yaml(paths.practice_item_path("linear-algebra", ORPHAN), _extra_item(
        ORPHAN, "lo_a", mode="short_answer", prompt="An item whose LO goes away."))
    lo_path = paths.learning_object_path("linear-algebra", "lo_spectral")
    from learnloop.vault.yaml_io import read_yaml

    write_yaml(lo_path, {**read_yaml(lo_path), "status": "dormant"})
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    repository.upsert_practice_item_state("pi_eig_easy", active=False, clock=CLOCK)
    repository.insert_exam_pool_items([{
        "id": "epi_due_queue", "goal_id": "goal_linear_algebra_ml", "practice_item_id": "pi_pair_second",
        "reserved_at": NOW_ISO,
    }])
    repository.create_followup_task(
        kind="certification_cold_probe", case_kind="certification", case_ref="cert_due_queue",
        learning_object_id="lo_c", not_before=(NOW + timedelta(days=3)).isoformat().replace("+00:00", "Z"),
        selected_item_id="pi_c2", expires_at=(NOW + timedelta(days=9)).isoformat().replace("+00:00", "Z"),
        clock=CLOCK,
    )
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this",
                       clock=FrozenClock(NOW - timedelta(minutes=30)))
    apply_choice(vault, repository, Scope("learning_object", "lo_b"), "pause",
                 clock=FrozenClock(NOW - timedelta(minutes=20)))
    vault = load_vault(paths.root)
    # In memory only: the loader refuses an item whose LO is missing, and state sync deactivates a dialogue-turn
    # instance and an answered diagnostic probe, which would leave the gates that name them unreached.
    vault.practice_items[ORPHAN].learning_object_id = "lo_missing"
    vault.practice_items[MICROPROBE].practice_mode = "diagnostic_microprobe"
    vault.practice_items["pi_a2"].practice_mode = "diagnostic_probe"
    return vault, repository


def build_figure_vault(root):
    """``(vault, repository)``: :func:`build_rich_vault` with an item on ``lo_c`` whose prompt embeds a picture."""

    vault, repository = build_rich_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    write_yaml(paths.practice_item_path("linear-algebra", FIGURE_ITEM), _extra_item(
        FIGURE_ITEM, "lo_c", mode="short_answer", prompt="Read the matrix off the figure.\n\n![a matrix](figures/m.png)"))
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    seed_due(repository, FIGURE_ITEM, due=NOW - timedelta(days=1), last=NOW - timedelta(days=10))
    # Answered yesterday and not due for a month: nothing ranks it. And an answer on a never-evidenced LO whose
    # item set a review, so placement does not start it as new material and nothing else does either.
    seed_due(repository, "pi_c2", due=NOW + timedelta(days=30), last=NOW - timedelta(days=1))
    seed_due(repository, "pi_spec_easy", due=NOW + timedelta(days=30), last=NOW - timedelta(days=1))
    return load_vault(paths.root), repository


def build_probe_history_vault(root):
    """``(vault, repository)``: :func:`build_rich_vault` with an answer two hours ago on another item of the probe's
    LO that shares the instruments' facet, so the probes' familiarity discounts them."""

    from tests.daily_plan_fakes import record_attempt

    vault, repository = build_rich_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    write_yaml(paths.practice_item_path("linear-algebra", SEEN_ON_PROBE_LO), _extra_item(
        SEEN_ON_PROBE_LO, PROBE_LO, mode="short_answer", prompt="Recall the SVD's factors."))
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    attempt_id = record_attempt(repository, SEEN_ON_PROBE_LO, PROBE_LO, NOW - timedelta(hours=2))
    with repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET evidence_facets_json = ? WHERE id = ?",
                           ('["recall"]', attempt_id))
        connection.commit()
    return load_vault(paths.root), repository


def build_unconsulted_episode_vault(root):
    """``(vault, repository)``: :func:`build_rich_vault` with the probe's LO paused, so no item of the in-progress
    episode reaches a gate that reads the episode."""

    from learnloop.intent.control import Scope, apply_choice

    vault, repository = build_rich_vault(root)
    apply_choice(vault, repository, Scope("learning_object", PROBE_LO), "pause",
                 clock=FrozenClock(NOW - timedelta(minutes=20)))
    return load_vault(vault.root), repository
