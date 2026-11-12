"""What other test files use from ``tests/test_probe_episodes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    episode_hypothesis_set,
    serve_presentation,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import (
    NOW,
    NOW_ISO,
    admit_probe_instrument_card,
    append_config_toml,
    create_basic_vault,
    pin_old_basic_vault,
    set_algorithm_version,
)


#: Kill-switch fragments for the predecessors probe tests pin (D7 removes each switch).
VOI_STOPPING_OFF = "[voi_stopping]\nenabled = false"
PLACEMENT_OFF = "[placement]\nenabled = false"

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)


def _setup(
    tmp_path,
    *,
    with_card: bool = True,
    extra_item: bool = False,
    algorithm_version: str | None = None,
    old_path: bool = False,
    switched_off: str | None = None,
):
    """``old_path`` puts the vault back to the pre-D2a basic vault
    (``pin_old_basic_vault``), for a test of a path no head vault takes.
    ``switched_off`` is a TOML fragment turning a kill switch off on the head
    vault, for a test of the predecessor that switch serves (it goes with the
    switch in D7)."""

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    if old_path:
        paths = pin_old_basic_vault(paths)
    if switched_off is not None:
        append_config_toml(vault_root, switched_off)
    if algorithm_version is not None:
        set_algorithm_version(paths, algorithm_version)
    if extra_item:
        _add_item(vault_root, "pi_svd_define_002", surface_family="fresh_surface")
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    if with_card:
        items = (ITEM_ID, "pi_svd_define_002") if extra_item else (ITEM_ID,)
        admit_contrast_card(repository, items=items)
    return vault_root, loaded, repository


def _add_item(vault_root, item_id: str, *, surface_family: str | None = None) -> None:
    upsert_practice_item(
        vault_root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "diagnostic_probe", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": f"Fresh-surface prompt for {item_id}.",
            "expected_answer": "A matrix factorization into U, Sigma, and V transpose.",
            "surface_family": surface_family,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [
                    {
                        "id": "conceptual_slip",
                        "description": "Confuses SVD with a different decomposition.",
                        "max_grade": 1,
                    }
                ],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )


def admit_contrast_card(
    repository: Repository,
    *,
    card_id: str = "card_svd_contrast",
    items: tuple[str, ...] = (ITEM_ID,),
    rows: dict | None = None,
) -> None:
    admit_probe_instrument_card(repository, card_id=card_id, items=items, rows=rows)


def _commit(loaded, repository, episode, *, item_id: str = ITEM_ID):
    hypothesis_set = episode_hypothesis_set(repository, episode)
    instruments = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
    eligible = next(entry for entry in instruments if entry.item.id == item_id)
    presentation = commit_presentation(loaded, repository, episode, eligible, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)
    return presentation
