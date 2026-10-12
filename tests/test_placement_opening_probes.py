"""Owner decision 2026-10-12 (Slice A Phase 6 open question 1): under placement,
an opening episode an earlier version opened and nobody answered is ignored for
serving, feedback routing and instrument generation. Nothing rewrites or closes
it until the learner or an error acts on its LO (a door that opens an episode
adopts it), so ``placement.enabled = false`` (and ``placement.initial_probes =
true``) serve every untouched one again exactly as the predecessor did.
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


def _upgraded(tmp_path, name="vault", *, placement_toml=None, empty_lo=False, before_upgrade=None):
    """A vault whose opening episodes were opened at mvp-0.10, then moved to
    mvp-0.11 (as the owner's upgrade does: nothing is rewritten).
    ``before_upgrade(paths, vault, repository)`` runs at mvp-0.10."""

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
    if before_upgrade is not None:
        before_upgrade(paths, vault, repository)
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


# -- Codex review fixes (2026-10-12): every door that acted on the episode ----


def _sidecar(paths):
    import learnloop_sidecar.handlers  # noqa: F401 -- registers methods
    from learnloop_sidecar.context import SidecarContext

    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    return ctx


def _submit_on_lo_diag(ctx, submission_id="s-1"):
    from tests.test_graph_editor_reads import _call

    session = _call(ctx, "start_session", {"energy": "medium"})
    return _call(ctx, "submit_attempt", {
        "sessionId": session["sessionId"], "practiceItemId": "pi_diag_mid", "answerMd": "an answer",
        "attemptType": "independent_attempt", "submissionId": submission_id,
        "selfGrade": {"criterionPoints": {"correctness": 2}, "confidence": 3},
    })


def _in_progress_lo_diag(paths, vault, repository):
    episode = repository.open_probe_episode("lo_diag")
    repository.update_probe_episode_status(episode.id, status="in_progress", clock=_at(0.5))


@pytest.mark.parametrize("placement_toml", [None, "[placement]\nenabled = false\n"], ids=["placement", "kill-switch"])
def test_an_answer_on_an_ignored_episode_is_not_held_back_for_it(tmp_path, monkeypatch, placement_toml):
    """F1: the completion route, the applied-episode record, the attempt
    result and the next-probe peek treat the ignored episode as absent; the
    kill switch defers feedback to it exactly as the predecessor did."""

    from tests.test_graph_editor_reads import _call

    paths, vault, repository = _upgraded(
        tmp_path, placement_toml=placement_toml, before_upgrade=_in_progress_lo_diag,
    )
    episode = repository.open_probe_episode("lo_diag")
    assert episode.status == "in_progress"
    assert episode_ignored(load_vault(paths.root), repository, episode) is (placement_toml is None)
    ctx = _sidecar(paths)
    recorded = []
    save = Repository.save_attempt_completion

    def record(self, **kwargs):
        recorded.append(kwargs.get("applied_probe_episode_id"))
        return save(self, **kwargs)

    monkeypatch.setattr(Repository, "save_attempt_completion", record)

    result = _submit_on_lo_diag(ctx)
    route = repository.attempt_completion(result["attemptId"])["route"]
    next_probe = _call(ctx, "get_next_probe_item", {"learningObjectId": "lo_diag"})
    if placement_toml is None:
        assert result["probeEpisode"] is None and route is None
        # The save in the attempt's own transaction (a later save refreshes only the result).
        assert recorded[0] is None
        # The answer was new material: the episode is still the untouched opening one.
        assert episode_ignored(load_vault(paths.root), repository, repository.open_probe_episode("lo_diag"))
        assert next_probe["active"] is False
    else:
        assert result["probeEpisode"] == {
            "episodeId": episode.id, "feedbackDeferred": True, "status": "in_progress",
        }
        assert route == {"episode_id": episode.id, "feedback_deferred": True, "status": "in_progress"}
        assert recorded[0] == episode.id


def test_the_overconfidence_list_adopts_an_ignored_episode(tmp_path):
    """F2, door 1: "probe me" on an LO whose only open episode is ignored is
    served: the episode is adopted (origin stamped), so it stops being ignored."""

    from tests.test_graph_editor_reads import _call

    paths, vault, repository = _upgraded(tmp_path)
    before = repository.open_probe_episode("lo_diag")
    assert episode_ignored(vault, repository, before)

    started = _call(_sidecar(paths), "start_overconfidence_probe", {"learningObjectId": "lo_diag"})
    adopted = repository.open_probe_episode("lo_diag")
    assert started["episodeId"] == adopted.id == before.id
    assert adopted.origin == "overconfidence_list"
    assert adopted.target_decision["kind"] == "adopted_opening_episode"
    assert adopted.target_decision["requested_trigger"] == "goal_diagnostic"
    assert adopted.hypothesis_set_id != before.hypothesis_set_id
    # Held to the overconfidence list's own contract: a routing conclusion.
    assert adopted.minimum_independent_observations == vault.config.probe.episode.placement_minimum_observations
    assert not episode_ignored(vault, repository, adopted)
    assert "lo_diag" in servable_open_episodes(vault, repository)
    # Served behind its episode again (not as new material), as the predecessor served it.
    queue = build_due_queue(vault, repository, clock=_at(2), persist_explanations=False)
    assert not any(s.components.get("new_material") for s in queue if s.learning_object_id == "lo_diag")
    # Every episode no door touched is still ignored.
    assert {e.learning_object_id for e in repository.open_probe_episodes().values()
            if e.id in ignored_opening_episode_ids(vault, repository)} >= PLACEMENT_LOS - {"lo_diag"}


def test_an_error_driven_reprobe_adopts_an_ignored_episode(tmp_path):
    """F2, door 3: a high-severity misconception on the LO is not blocked by
    the ignored episode (field §5.2: a diagnostic episode still opens when a
    wrong answer leaves a real choice of repair)."""

    from learnloop.diagnosis.probe_episodes import maybe_reprobe_for_misconception

    _paths, vault, repository = _upgraded(tmp_path)
    before = repository.open_probe_episode("lo_diag")
    assert maybe_reprobe_for_misconception(vault, repository, "lo_diag", severity=0.3, clock=_at(3)) is None
    reprobed = maybe_reprobe_for_misconception(vault, repository, "lo_diag", severity=0.9, clock=_at(3))
    assert reprobed is not None and reprobed.id == before.id
    assert reprobed.target_decision["requested_trigger"] == "misconception"
    assert reprobed.origin is None
    assert not episode_ignored(vault, repository, reprobed)
    # Now a real episode owns the LO: a second re-probe is refused as before.
    assert maybe_reprobe_for_misconception(vault, repository, "lo_diag", severity=0.9, clock=_at(4)) is None


def test_an_adopted_reprobe_is_held_to_the_reprobe_contract(tmp_path):
    """Re-review F1: an error-driven re-probe that adopts the opening episode
    keeps the two-observation breadth contract of a diagnostic re-entry, not
    the opening episode's one-observation placement minimum, and is pinned to
    the calibration channel and algorithm version of now, not of the version
    that opened it."""

    from learnloop.diagnosis.probe_episodes import maybe_reprobe_for_misconception
    from learnloop.diagnosis.probe_robust import load_pinned_channel

    _paths, vault, repository = _upgraded(tmp_path)
    episode_config = vault.config.probe.episode
    assert (episode_config.placement_minimum_observations, episode_config.minimum_independent_observations) == (1, 2)
    before = repository.open_probe_episode("lo_diag")
    assert (before.minimum_independent_observations, before.algorithm_version) == (1, "mvp-0.10")
    # The pin the opening episode carries is from when an earlier version
    # opened it; make it visibly stale.
    with repository.connection() as connection:
        connection.execute(
            "UPDATE probe_episodes SET calibration_model_id = NULL, calibration_model_hash = 'stale', "
            "probe_mapping_version = 'stale' WHERE id = ?",
            (before.id,),
        )
        connection.commit()

    reprobed = maybe_reprobe_for_misconception(vault, repository, "lo_diag", severity=0.9, clock=_at(3))
    assert reprobed.id == before.id and reprobed.trigger == "initial"
    assert reprobed.minimum_independent_observations == 2
    assert reprobed.maximum_observations == episode_config.maximum_observations
    assert reprobed.algorithm_version == "mvp-0.11"
    # Re-resolved at adoption: a channel persisted now, which the decision
    # path can load.
    channel = load_pinned_channel(repository, reprobed.calibration_model_hash)
    assert channel is not None and channel.model_hash == reprobed.calibration_model_hash
    assert (reprobed.calibration_model_id, reprobed.probe_mapping_version) == (
        channel.model_id, channel.mapping_version,
    )
    # Exactly what enter_episode stamps on a fresh misconception re-probe (the
    # channel resolves to a new snapshot on every call).
    from learnloop.diagnosis.probe_episodes import episode_open_contract

    contract = episode_open_contract(vault, repository, "lo_diag", trigger="misconception", clock=_at(3))
    pinned = {"calibration_model_id", "calibration_model_hash"}
    with repository.connection() as connection:
        pins = connection.execute(
            "SELECT target_contract_version_id, target_support_hash FROM probe_episodes WHERE id = ?", (reprobed.id,),
        ).fetchone()
    stored = {key: getattr(reprobed, key) for key in contract if hasattr(reprobed, key) and key not in pinned}
    stored.update(target_contract_version_id=pins[0], target_support_hash=pins[1])
    assert stored == {key: value for key, value in contract.items() if key not in pinned}


def test_an_adopted_episode_that_completes_without_a_gap_opens_no_tutor(tmp_path):
    """Re-review F2: the adoption stamp is provenance, not a §12.1 typed
    transition. An adopted episode that completes without a gap (the block end
    writes no decision) neither opens the tutor nor reaches its context; a
    typed decision the block end writes still does."""

    from learnloop.diagnosis.probe_episodes import _set_target_decision, maybe_reprobe_for_misconception
    from learnloop.tutor.tutor_qa import _diagnostic_decision_for, build_tutor_opening

    _paths, vault, repository = _upgraded(tmp_path)
    adopted = maybe_reprobe_for_misconception(vault, repository, "lo_diag", severity=0.9, clock=_at(3))
    repository.update_probe_episode_status(
        adopted.id, status="complete", completion_reason="decision_stable", completed_at=NOW_ISO, clock=_at(4),
    )
    assert repository.probe_episode(adopted.id).target_decision["kind"] == "adopted_opening_episode"
    item = vault.practice_items["pi_diag_mid"]
    assert _diagnostic_decision_for(vault, repository, item, "practice") is None

    class NoPaidOpening:
        def __getattr__(self, name):
            raise AssertionError(f"the tutor was asked to open ({name})")

    assert build_tutor_opening(vault, repository, NoPaidOpening(), practice_item_id="pi_diag_mid") is None

    typed = {"diagnosed_gap": "misconception:m1", "tutor_move": "contrast_cases", "target_facets": []}
    _set_target_decision(repository, adopted.id, typed, clock=_at(5))
    assert _diagnostic_decision_for(vault, repository, item, "practice") == typed


def test_a_named_calibration_adopts_an_ignored_episode(tmp_path):
    _paths, vault, repository = _upgraded(tmp_path)
    before = repository.open_probe_episode("lo_diag")
    session_id = repository.create_session(available_minutes=25, clock=_at(3))
    start_calibration_session(
        vault, repository, session_id=session_id, learning_object_ids=["lo_diag"],
        generate_missing=False, clock=_at(3),
    )
    adopted = repository.open_probe_episode("lo_diag")
    assert adopted.id == before.id
    assert adopted.target_decision["requested_trigger"] == "manual"
    assert not episode_ignored(vault, repository, adopted)
    # A named calibration keeps the breadth contract (re-review F1).
    assert adopted.minimum_independent_observations == vault.config.probe.episode.minimum_independent_observations == 2


def test_the_causal_quick_check_stops_the_episode_being_ignored(tmp_path):
    """F2, door 2: "Take the quick check" relocks the unmeasured opening
    episode onto the cause set and stamps its origin; it is then served."""

    from learnloop.diagnosis.causal_orchestrator import accept_probe_offer

    from tests.helpers import admit_probe_instrument_card
    from tests.test_causal_orchestrator import (
        LO_ID,
        PROBE_ITEM,
        _activate_probe_candidate,
        _add_probe_item,
        _seed_factor,
    )

    def opening_episode_on_lo_id(paths, vault, repository):
        from learnloop.diagnosis.probe_episodes import enter_episode

        _add_probe_item(paths.root)
        if repository.open_probe_episode(LO_ID) is None:
            enter_episode(load_vault(paths.root), repository, LO_ID, trigger="initial", clock=_at(0))

    paths, vault, repository = _upgraded(tmp_path, before_upgrade=opening_episode_on_lo_id)
    before = repository.open_probe_episode(LO_ID)
    assert before.trigger == "initial" and episode_ignored(vault, repository, before)

    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    _activate_probe_candidate(repository, factor_id, first_id, second_id)
    offer = accept_probe_offer(vault, repository, factor_id=factor_id, clock=_at(5))
    assert offer.accepted, offer.reason
    relocked = repository.probe_episode(offer.episode_id)
    assert relocked.id == before.id and relocked.trigger == "initial"
    assert relocked.origin == f"causal_factor:{factor_id}"
    assert not episode_ignored(vault, repository, relocked)
    assert LO_ID in servable_open_episodes(vault, repository)


def test_an_ignored_episode_feeds_no_reader_that_scores_it(tmp_path, monkeypatch):
    """F6: the intervention trigger, tutor Q&A and the staged controller's
    robust value read the ignored episode as absent."""

    from types import SimpleNamespace

    from learnloop.diagnosis import followups
    from learnloop.scheduling import state_signals
    from learnloop.tutor.tutor_qa import _diagnostic_decision_for

    paths, vault, repository = _upgraded(tmp_path, before_upgrade=_in_progress_lo_diag)
    episode = repository.open_probe_episode("lo_diag")
    assert episode_ignored(vault, repository, episode)

    seen = []
    original = followups._probe_unfamiliar_probability

    def spy(vault, repository, result, probe_state, episode):
        seen.append(episode)
        return original(vault, repository, result, probe_state, episode)

    monkeypatch.setattr(followups, "_probe_unfamiliar_probability", spy)
    _submit_on_lo_diag(_sidecar(paths))
    assert seen == [None]

    typed = {"diagnosed_gap": "misconception:m1", "tutor_move": "contrast_cases"}
    closed = SimpleNamespace(status="complete", target_decision=typed)
    monkeypatch.setattr(repository, "probe_episodes_for_learning_object", lambda _lo: [closed])
    item = vault.practice_items["pi_diag_mid"]
    assert _diagnostic_decision_for(vault, repository, item, "practice") == typed

    monkeypatch.setattr(state_signals, "_commitment_learning_object_ids", lambda *_args: {"lo_diag"})
    assert state_signals.decision_relevant_robust_value(repository, None, "c") == state_signals.OPEN_EPISODE_ROBUST_VALUE
    assert state_signals.decision_relevant_robust_value(
        repository, None, "c", ignored_episode_ids=ignored_opening_episode_ids(vault, repository),
    ) == 0.0


def test_a_notice_raised_before_placement_is_held_not_resolved(tmp_path):
    """F7: a probe-pool-empty notice the predecessor raised for a starved
    opening episode is neither resolved by the sweep nor by the feed's aging;
    the kill switch finds it as it was."""

    from learnloop.ops.maintenance_feed import generate_maintenance_feed

    def raise_notice(paths, vault, repository):
        swept = reconcile_empty_probe_pools(vault, repository, clock=_at(0.5), provider_available=False)
        assert len(swept["notice_ids"]) == 1

    def pool_notices():
        return [n for n in repository.maintenance_notices(include_hidden=True) if n["notice_type"] == "probe_pool_empty"]

    paths, vault, repository = _upgraded(tmp_path, empty_lo=True, before_upgrade=raise_notice)
    (notice,) = pool_notices()
    assert (notice["dedup_key"], notice["status"]) == ("lo_empty", "active")

    swept = reconcile_empty_probe_pools(vault, repository, clock=_at(2), provider_available=False)
    assert swept["resolved_notice_ids"] == [] and swept["notice_ids"] == []
    generate_maintenance_feed(vault, repository, clock=_at(3))
    (held,) = pool_notices()
    assert (held["id"], held["status"]) == (notice["id"], "active")

    append_config_toml(paths.root, "[placement]\nenabled = false\n")
    off = load_vault(paths.root)
    swept = reconcile_empty_probe_pools(off, repository, clock=_at(4), provider_available=False)
    assert swept["notice_ids"] == [notice["id"]] and swept["resolved_notice_ids"] == []


def test_probe_instances_reaches_an_ignored_episode_when_the_lo_is_named(tmp_path):
    """F12: ``--lo`` names the LO, as naming it in a calibration does."""

    paths, _vault, repository = _upgraded(tmp_path, empty_lo=True)
    episode = repository.open_probe_episode("lo_empty")
    unnamed = CliRunner().invoke(app, ["probe-instances", "--vault", str(paths.root), "--no-llm", "--json"])
    assert unnamed.exit_code == 0, unnamed.output
    assert json.loads(unnamed.output)["episodes"] == []
    named = CliRunner().invoke(
        app, ["probe-instances", "--vault", str(paths.root), "--no-llm", "--json", "--lo", "lo_empty"],
    )
    assert named.exit_code == 0, named.output
    assert [entry["episode_id"] for entry in json.loads(named.output)["episodes"]] == [episode.id]
