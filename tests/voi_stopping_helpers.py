"""What other test files use from ``tests/test_voi_stopping.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from contextlib import closing

from learnloop.clock import FrozenClock
from learnloop.config.schema import LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.daily_plan.lanes import (
    ScheduledCheck,
    classify_pool,
    register_scheduled_check_provider,
    unregister_scheduled_check_provider,
)
from learnloop.diagnosis.followups import evaluate_intervention_followup
from learnloop.diagnosis.probe_episodes import enter_episode
from learnloop.diagnosis import voi_stopping as voi
from learnloop.scheduling.scheduler import SchedulerSession, read_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.daily_plan_fakes import make_env, scheduled
from tests.helpers import (
    NOW,
    NOW_ISO,
    add_followup_item,
    admit_probe_instrument_card,
    append_config_toml,
    create_basic_vault,
    create_daily_plan_vault,
    set_algorithm_version,
)


CLOCK = FrozenClock(NOW)
LO = "lo_svd_definition"


def _config(version: str, **switches) -> LearnLoopConfig:
    config = LearnLoopConfig()
    config.algorithms.algorithm_version = version
    for name, value in switches.items():
        setattr(config.voi_stopping, name, value)
    return config


def _minutes(monkeypatch, minutes: float) -> None:
    """Pin every candidate's expected minutes (the value must pay for them)."""

    monkeypatch.setattr(
        voi.VoiContext,
        "item_minutes",
        lambda self, item, authored_minutes=None: voi.MinutesEstimate(float(minutes), "authored_prior"),
    )


class _Repo:
    """Just enough repository for a VoiContext: no latencies, seeded routes."""

    def __init__(self, routes):
        self._routes = routes

    def failure_triage_routes(self):
        return list(self._routes)

    def connection(self):
        import sqlite3

        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute(
            "CREATE TABLE practice_attempts (practice_item_id TEXT, practice_mode TEXT, latency_seconds REAL)"
        )
        connection.execute(
            "CREATE TABLE interaction_events (kind TEXT, attempt_duration_ms INTEGER)"
        )
        return closing(connection)


def _ctx(routes=()):
    from types import SimpleNamespace

    return voi.VoiContext(SimpleNamespace(config=LearnLoopConfig()), _Repo(routes))


ROUTES = [
    {"reason": "unfamiliar_or_missing_knowledge", "first_intervention": "study", "active": 1},
    {"reason": "memory_lapse", "first_intervention": "review", "active": 1},
    {"reason": "false_belief_or_confusion", "first_intervention": "contrast", "active": 1},
]
INFORMATIVE = {"unfamiliar": {"wrong": 0.9, "right": 0.1}, "robust_initial_grasp": {"wrong": 0.1, "right": 0.9}}


def _candidate(ref, members, minutes):
    return voi.Candidate(ref=ref, minutes=voi.MinutesEstimate(minutes, "authored_prior"), members=(members,))


def _cap():
    return voi.former_cap(voi.SITE_PROBE_EPISODE, value=4, count=0)


def _probe_vault(tmp_path, version: str, *, toml: str = ""):
    """Two never-seen items bound to an in-progress re-probe episode (router
    R1's fixture): the queue's only candidates are the two probes."""

    paths = create_basic_vault(tmp_path / version.replace(".", "_"))
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": []})
    add_followup_item(paths.root, "pi_svd_define_002")
    set_algorithm_version(paths, version)
    append_config_toml(paths.root, "[plan]\nenabled = false\n" + toml)
    repository = Repository(paths.sqlite_path)
    repository.insert_error_event(
        {
            "id": "err_conceptual_slip", "learning_object_id": LO,
            "error_type": "conceptual_slip", "severity": 0.7, "is_misconception": True,
            "status": "active", "created_at": NOW_ISO, "updated_at": NOW_ISO,
        }
    )
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    admit_probe_instrument_card(repository, items=("pi_svd_define_001", "pi_svd_define_002"))
    enter_episode(vault, repository, LO, trigger="misconception", clock=CLOCK)
    return paths, load_vault(paths.root), repository


def _fingerprint(queue):
    return [
        (s.practice_item_id, round(s.priority, 12), sorted((k, round(v, 12)) for k, v in s.components.items()))
        for s in queue
    ]


def _build(vault, repository, *, session_id="sess", trace=None):
    return read_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=session_id), offer_trace=trace,
    )


def _followup_setup(tmp_path, version):
    from tests.followups_helpers import _surprising_attempt

    vault_root = tmp_path / version.replace(".", "_")
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)
    loaded.config.algorithms.algorithm_version = version
    return loaded, repository, result


def _further(loaded, repository, result, **kwargs):
    return evaluate_intervention_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction=result.surprise_direction,
        bayesian_surprise=result.bayesian_surprise,
        grader_confidence=result.grader_confidence,
        error_event_written=bool(result.error_event_ids),
        available_minutes=30,
        session_id="sess",
        **{"session_interventions_for_lo": 1, **kwargs},
    )


def _teach_back_vault(tmp_path, version):
    from tests.teach_back_helpers import _seed_lo_evidence, _setup, _teach_item_payload

    _root, vault, repository = _setup(tmp_path / version.replace(".", "_"),
                                      extra_items=[_teach_item_payload("pi_svd_teach_002")])
    _seed_lo_evidence(repository)
    vault.config.algorithms.algorithm_version = version
    return vault, repository


def _probe_items(eig=0.2):
    return [scheduled(f"pi_probe_{i}", "lo_repo", probe_eig_total=eig) for i in range(5)]


def _checks(ids=None):
    ids = ids or [f"pi_probe_{i}" for i in range(5)]
    return {item_id: ScheduledCheck("project_probe", priority=1 if item_id == "pi_probe_4" else 0) for item_id in ids}


def _probe(item_id, lo, facets, *, lo_variance=0.5, facet_variance=0.2, mass=0.5, hypothesis_eig=0.0, channel=None):
    """A due project probe carrying the scheduler's reward body, so its
    ``probe_eig_total`` decomposes and it can be valued conditionally
    (``channel``: its likelihood rows over an open episode's hypotheses)."""

    from dataclasses import replace

    from learnloop.scheduling.selection_rewards import (
        ItemDemandVector,
        LearnerAbilityVector,
        probe_information_gain_components,
    )

    ability = LearnerAbilityVector(
        learning_object_id=lo, lo_mastery=0.0, lo_mastery_variance=lo_variance,
        facet_recall_mean_by_facet={f: 0.5 for f in facets},
        facet_recall_variance_by_facet={f: facet_variance for f in facets},
        facet_independent_evidence_mass_by_facet={f: mass for f in facets},
        misconception_posterior_by_error_type={},
    )
    demand = ItemDemandVector(
        learning_object_id=lo, evidence_weights=dict(facets), difficulty_b=0.0, discrimination_a=1.0,
        retrieval_demand=0.5, transfer_distance=0.0, scaffold_level=0.0, surface_family=None,
        misconception_targets=[], repair_targets=list(facets), bad_item_suspicion=0.0,
    )
    probe_eig = probe_information_gain_components(ability, demand, hypothesis_eig=hypothesis_eig)
    item = scheduled(item_id, lo, probe_eig_total=float(probe_eig["total_reduction"]))
    return replace(
        item,
        reward_debug={"ability_vector": ability.as_dict(), "item_demand_vector": demand.as_dict(), "probe_eig": probe_eig},
        hypothesis_channel=channel,
    )


def _admission(probes_planned=0, version="mvp-0.21", minutes_budget=None):
    """The plan engine's own admission (greedy, conditional), as the plan calls it."""

    from types import SimpleNamespace

    from learnloop.daily_plan.engine import _project_probe_admission

    config = _config(version)
    env = SimpleNamespace(vault=SimpleNamespace(config=config), repository=None, plan_config=config.plan)
    return _project_probe_admission(env, probes_planned, minutes_budget=minutes_budget)


def _classify(items, *, minutes=3.0, checks=None, admission=None):
    estimate = minutes if callable(minutes) else (lambda _id: minutes)
    return classify_pool(
        items, item_states={}, requested_ids=[], now=NOW, estimate=estimate,
        checks=checks or _checks([item.practice_item_id for item in items]), probe_cap_left=4,
        project_probe_admission=admission or _admission(),
    )


def _plan_with_probes(tmp_path, version, toml=""):
    from tests.daily_plan_build_helpers import _run_to_end
    from learnloop.daily_plan.engine import build_plan

    paths = create_daily_plan_vault(
        tmp_path / version.replace(".", "_"),
        learning_objects={"lo_repo": [(f"pi_probe_{i}", 1.0) for i in range(5)]},
        version=version,
        plan_toml=toml or None,
    )
    probe_ids = {f"pi_probe_{i}" for i in range(5)}

    def provider(_vault, _repository, item_ids):
        return {item_id: ScheduledCheck("project_probe") for item_id in item_ids if item_id in probe_ids}

    register_scheduled_check_provider(provider)
    try:
        env = make_env(paths.root, _probe_items())
        build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
        record, _ = _run_to_end(env)
        planned = {item.practice_item_id for item in record.items()} & probe_ids
        with env.repository.connection() as connection:
            details = [
                json.loads(row[0])
                for row in connection.execute(
                    "SELECT detail_json FROM router_decisions WHERE decision_kind = 'plan_block'"
                )
            ]
        return planned, details
    finally:
        unregister_scheduled_check_provider(provider)


def _answer_probe(vault, repository, *, score: int = 1):
    from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, apply_attempt
    from learnloop.attempts.attempts import ResolvedGrade
    from learnloop.diagnosis.probe_episodes import (
        commit_presentation,
        eligible_instruments,
        episode_hypothesis_set,
        serve_presentation,
    )
    from learnloop.ids import new_ulid

    episode = repository.open_probe_episode(LO)
    eligible = eligible_instruments(
        vault, repository, episode, hypothesis_set=episode_hypothesis_set(repository, episode)
    )[0]
    presentation = commit_presentation(vault, repository, episode, eligible, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)
    apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=eligible.item.id, learner_answer_md="answer", attempt_type="diagnostic_probe",
                session_id="sess", probe_presentation_id=presentation.id,
            ),
            attempt_id=new_ulid(),
            grade=ResolvedGrade(
                rubric_score=score, criterion_points={"correctness": float(score)}, evidence_rows=[],
                error_attributions=[], grader_confidence=1.0, confidence=4, manual_review_reason=None,
            ),
            grading_source="ai",
        ),
        clock=CLOCK,
    )
    return repository.probe_episode(episode.id)


#: Keep the episode's other stops out of the way (decision stability, action
#: equivalence, the robust abstention after the breadth minimum): only the
#: count or value ends it.
_LONG_EPISODE_TOML = (
    "[probe.episode]\nposterior_stop_threshold = 0.9999\naction_equivalence_enabled = false\n"
    "minimum_independent_observations = 10\n"
    "[probe.block]\ndefault_block_observations = 1\n"
)
_EXTRA_PROBES = tuple(f"pi_svd_define_{index:03d}" for index in range(3, 8))


def _long_probe_vault(tmp_path, version, toml=""):
    paths, _vault, repository = _probe_vault(tmp_path, version, toml=_LONG_EPISODE_TOML + toml)
    for item_id in _EXTRA_PROBES:
        add_followup_item(paths.root, item_id)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    admit_probe_instrument_card(
        repository, card_id="card_svd_contrast_more", items=("pi_svd_define_001", "pi_svd_define_002", *_EXTRA_PROBES)
    )
    return vault, repository


def _qualifying(repository, episode_id):
    return sum(
        1 for row in repository.probe_observations_for_episode(episode_id) if row["observation"].eligible_for_completion
    )
