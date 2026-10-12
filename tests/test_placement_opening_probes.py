"""Owner decision 2026-10-12 (Slice A Phase 6 open question 1): under placement,
an opening episode an earlier version opened and nobody answered is ignored for
serving and for instrument generation. It is never rewritten or closed, so
``placement.enabled = false`` (and ``placement.initial_probes = true``) serve it
again exactly as the predecessor did.
"""

from __future__ import annotations

from datetime import timedelta
import json

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.calibration_sessions import CalibrationSessionError, start_calibration_session
from learnloop.diagnosis.diagnostic_surface_supply import (
    probe_pool_empty_conditions,
    reconcile_empty_probe_pools,
)
from learnloop.placement.state import (
    episode_ignored,
    ignored_opening_episode_ids,
    servable_open_episodes,
)
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, append_config_toml, create_placement_vault, set_algorithm_version

PLACEMENT_LOS = {"lo_diag", "lo_eigen_basics", "lo_spectral"}


def _at(minutes: float) -> FrozenClock:
    return FrozenClock(NOW + timedelta(minutes=minutes))


def _upgraded(tmp_path, name="vault", *, placement_toml=None, empty_lo=False):
    """A vault whose opening episodes were opened at mvp-0.10, then moved to
    mvp-0.11 (as the owner's upgrade does: nothing is rewritten)."""

    paths = create_placement_vault(tmp_path / name, version="mvp-0.10")
    if empty_lo:
        # An LO in a goal's scope with no item: its opening episode starves.
        write_yaml(
            paths.learning_object_path("linear-algebra", "lo_empty"),
            {
                "schema_version": 1, "id": "lo_empty", "title": "Empty", "subjects": ["linear-algebra"],
                "concept": "diagonalization", "knowledge_type": "definition", "status": "active",
                "contradicts": None, "summary": "No items yet.", "prerequisites": [], "confusables": [],
                "difficulty_prior": 0.5, "tags": [], "provenance": {"origin": "human", "source_refs": []},
                "created_at": NOW_ISO, "updated_at": NOW_ISO,
            },
        )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=_at(0))
    if empty_lo:
        from learnloop.diagnosis.probe_episodes import enter_episode

        enter_episode(vault, repository, "lo_empty", trigger="initial", clock=_at(0))
    set_algorithm_version(paths, "mvp-0.11")
    if placement_toml:
        append_config_toml(paths.root, placement_toml)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(1))
    return paths, vault, repository


def _episodes(repository):
    return {lo: (e.id, e.trigger, e.status) for lo, e in repository.open_probe_episodes().items()}


def _fingerprint(vault, repository, minutes=2):
    queue = build_due_queue(vault, repository, clock=_at(minutes), persist_explanations=False)
    return sorted((lo, trigger, status) for lo, (_id, trigger, status) in _episodes(repository).items()), [
        (s.practice_item_id, round(s.priority, 12), sorted((k, round(v, 12)) for k, v in s.components.items()))
        for s in queue
    ]


def test_unanswered_opening_episodes_are_ignored_and_their_los_start_as_learning(tmp_path):
    paths, vault, repository = _upgraded(tmp_path)
    episodes = _episodes(repository)
    assert {lo for lo, (_id, trigger, status) in episodes.items() if trigger == "initial"} >= PLACEMENT_LOS
    assert ignored_opening_episode_ids(vault, repository) == {e[0] for e in episodes.values()}
    assert servable_open_episodes(vault, repository) == {}

    queue = build_due_queue(vault, repository, clock=_at(2), persist_explanations=False)
    new = {s.learning_object_id for s in queue if s.components.get("new_material")}
    assert new >= PLACEMENT_LOS
    # Nothing was rewritten or closed by serving.
    assert _episodes(repository) == episodes


@pytest.mark.parametrize(
    "switch", ["[placement]\nenabled = false\n", "[placement]\ninitial_probes = true\n"],
    ids=["kill-switch", "initial-probes"],
)
def test_the_switches_serve_the_opening_episodes_again_exactly(tmp_path, switch):
    _p, baseline_vault, baseline_repository = create_and_sync_predecessor(tmp_path)
    _paths, vault, repository = _upgraded(tmp_path, placement_toml=switch)
    assert ignored_opening_episode_ids(vault, repository) == frozenset()
    assert _fingerprint(vault, repository) == _fingerprint(baseline_vault, baseline_repository)


def create_and_sync_predecessor(tmp_path):
    paths = create_placement_vault(tmp_path / "baseline", version="mvp-0.10")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=_at(0))
    sync_vault_state(vault, repository, clock=_at(1))
    return paths, vault, repository


def test_an_answered_opening_episode_is_not_ignored(tmp_path):
    paths, vault, repository = _upgraded(tmp_path)
    episode = repository.open_probe_episode("lo_diag")
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO probe_presentations(id, probe_episode_id, practice_item_id, state_segment_id, "
            "status, submitted_at, created_at, updated_at) VALUES (?, ?, ?, ?, 'submitted', ?, ?, ?)",
            ("pp_answered", episode.id, "pi_diag_mid", "seg", NOW_ISO, NOW_ISO, NOW_ISO),
        )
        connection.commit()
    assert not episode_ignored(vault, repository, episode)
    assert "lo_diag" in servable_open_episodes(vault, repository)
    queue = build_due_queue(vault, repository, clock=_at(2), persist_explanations=False)
    assert not any(s.components.get("new_material") for s in queue if s.learning_object_id == "lo_diag")


def test_an_in_progress_opening_episode_serves_no_probe_and_is_not_parked(tmp_path):
    """The serving doors (scheduler, the desktop probe contract) treat it as
    absent; the probe door does not park it as it would a real episode."""

    import learnloop_sidecar.handlers  # noqa: F401 -- registers methods
    from learnloop_sidecar.context import SidecarContext

    from tests.test_graph_editor_reads import _call

    paths, vault, repository = _upgraded(tmp_path)
    episode = repository.open_probe_episode("lo_diag")
    repository.update_probe_episode_status(episode.id, status="in_progress", clock=_at(1))
    vault = load_vault(paths.root)
    assert episode_ignored(vault, repository, repository.open_probe_episode("lo_diag"))
    queue = build_due_queue(vault, repository, clock=_at(2), persist_explanations=False)
    lo_diag = [s for s in queue if s.learning_object_id == "lo_diag"]
    assert lo_diag and all(s.components.get("new_material") for s in lo_diag)
    assert all(s.components.get("probe_eig", 0.0) == 0.0 for s in lo_diag)

    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    contract = _call(ctx, "get_probe_contract", {"practiceItemId": "pi_diag_mid"})
    assert contract["active"] is False
    assert repository.probe_episode(episode.id).status == "in_progress"

    # With the kill switch the predecessor's door acts on it again (here: no
    # approved grading provider, so it parks the episode, as before).
    append_config_toml(paths.root, "[placement]\nenabled = false\n")
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    _call(ctx, "get_probe_contract", {"practiceItemId": "pi_diag_mid"})
    assert repository.probe_episode(episode.id).status == "pending_items"


def test_an_ignored_opening_episode_commissions_no_instrument_generation(tmp_path):
    paths, vault, repository = _upgraded(tmp_path, empty_lo=True)
    assert repository.open_probe_episode("lo_empty").trigger == "initial"
    assert probe_pool_empty_conditions(vault, repository) == []
    # The needs the predecessor recorded when it opened the episodes stay as
    # they were; the placement sweep adds none and raises no notice.
    needs_before = repository.probe_generation_needs()
    swept = reconcile_empty_probe_pools(vault, repository, clock=_at(2), provider_available=True)
    assert swept["queued_need_ids"] == [] and swept["notice_ids"] == []
    assert repository.probe_generation_needs() == needs_before
    assert not repository.maintenance_notices(include_hidden=True)

    # The owner's generation command skips it too.
    result = CliRunner().invoke(app, ["probe-instances", "--vault", str(paths.root), "--no-llm", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["episodes"] == []

    # An unscoped calibration does not sweep it in; naming the LO still works.
    session_id = repository.create_session(available_minutes=25, clock=_at(3))
    with pytest.raises(CalibrationSessionError):
        start_calibration_session(
            vault, repository, session_id=session_id, generate_missing=False, clock=_at(3),
        )

    # With the kill switch the predecessor's sweep sees the starved episode.
    append_config_toml(paths.root, "[placement]\nenabled = false\n")
    off = load_vault(paths.root)
    conditions = probe_pool_empty_conditions(off, repository)
    assert [c.learning_object_id for c in conditions] == ["lo_empty"]
