"""What other test files use from ``tests/test_router_probe_ties.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.probe_episodes import enter_episode
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import (
    NOW,
    NOW_ISO,
    add_followup_item,
    admit_probe_instrument_card,
    append_config_toml,
    create_basic_vault,
    set_algorithm_version,
)


def _probe_vault(tmp_path, version: str, *, toml: str = ""):
    """Two never-seen items bound to an in-progress diagnostic episode: two
    PROBE-intent candidates and nothing due, so Today's head is whichever probe
    the queue puts first (the probe section is the only one). The daily plan
    (mvp-0.14 and later) is switched off, so Today is the legacy queue whose
    head the offer serves."""

    paths = create_basic_vault(tmp_path / version.replace(".", "_"))
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": []})
    add_followup_item(paths.root, "pi_svd_define_002")
    set_algorithm_version(paths, version)
    append_config_toml(
        paths.root,
        "[scheduler]\nselection_exploration_rate = 0.2\nselection_exploration_reward_window = 5.0\n"
        "[plan]\nenabled = false\n" + toml,
    )
    repository = Repository(paths.sqlite_path)
    repository.insert_error_event(
        {
            "id": "err_conceptual_slip", "learning_object_id": "lo_svd_definition",
            "error_type": "conceptual_slip", "severity": 0.7, "is_misconception": True,
            "status": "active", "created_at": NOW_ISO, "updated_at": NOW_ISO,
        }
    )
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    admit_probe_instrument_card(repository, items=("pi_svd_define_001", "pi_svd_define_002"))
    # A misconception re-probe, not an opening ("initial") episode: from
    # mvp-0.11 placement ignores unanswered opening episodes (owner decision
    # 2026-10-12), so only a re-probe's items are in-episode probes there.
    enter_episode(vault, repository, "lo_svd_definition", trigger="misconception", clock=FrozenClock(NOW))
    return paths, load_vault(paths.root), repository
