"""The cold-retry reschedule (mvp-0.38; owner decision 2026-10-25, Reader CA2 follow-up Q4;
docs/reviews/cold-retry-after-assist.md).

Reader CA2 (mvp-0.35, ``ask.cold_help_converts``) made help taken on a cold
follow-up convert the attempt to practice with help; the measurement was left
to be withdrawn at the next serve, so the repair ended unmeasurable. From
mvp-0.38, with ``practice.reschedule_cold_after_assist`` on:

* help taken on a due repair ``cold_retry`` withdraws it in the attempt's own
  step (the existing typed disposition) and schedules ONE fresh cold retry for
  the same repair, on another independent surface (the lane's one rule), due
  ``COLD_RETRIEVAL_DELAY`` after the attempt that took the help and open for
  ``COLD_RETRY_WINDOW`` (the lane's existing timing);
* the fresh retry measures the repair cold (no hard exposure; the assisted
  attempt is recorded as the co-intervention it is);
* a fresh retry that is itself assisted spawns nothing (one per chain);
* a certification cold probe is never rescheduled (one probe per certificate);
* off, or below the tag: exactly the predecessor;
* replay schedules nothing, and a shadow rebuild is 0/0/0 with the fresh
  retries present;
* the upgrade is the chain's next journalled link.

Fakes only: self-graded attempts, no model call.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import timedelta

import pytest
from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION,
    COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION,
    COLD_RETRY_RESCHEDULE_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    SUPERSEDED_CLAIMS_ALGORITHM_VERSION,
)
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.remediation import (
    ASSISTED_RESCHEDULE_CONTEXT_KEY,
    COLD_RETRIEVAL_DELAY,
    COLD_RETRY_WINDOW,
    WITHDRAWN_COLD_RETRY_OUTCOME,
    reschedule_cold_after_assist_active,
)
from learnloop.ops.vault_upgrade import rewrite_algorithm_version
from learnloop.serve_eligibility import COLD_CHECK_HELP_TAKEN
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, add_followup_item, create_placement_vault
from tests.test_remediation_cold_retry import _drive_to_cold_scheduled, _setup
from tests.ux_phase1_support import set_config

TAG = COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION
PREDECESSOR = ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION
THIRD_ITEM = "pi_svd_define_003"
LO_ITEMS = {"pi_svd_define_001", "pi_svd_define_002", THIRD_ITEM}


def _iso(moment) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _repair(tmp_path, *, version=TAG, switch: bool | None = None, converts: bool = True, third: bool = True):
    """A repair episode at ``cold_scheduled`` with a third item for a fresh surface."""

    vault, repository, misconception_id = _setup(tmp_path)
    if third:
        add_followup_item(vault.root, THIRD_ITEM)
    updates = {("algorithms", "algorithm_version"): version, ("ask", "cold_help_converts"): converts}
    if switch is not None:
        updates[("practice", "reschedule_cold_after_assist")] = switch
    set_config(vault.root, updates)
    vault = load_vault(vault.root)
    episode, primed, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    return vault, repository, episode, primed, cold_item


def _spare(repository, episode) -> str:
    """The repair's one item on neither surface it already used (primed, cold)."""

    used = {str(episode["primed_item_id"]), str(episode["cold_item_id"])}
    [spare] = LO_ITEMS - used
    return spare


def _answer(vault, repository, item_id, moment, *, hints: int = 0):
    return complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="U Sigma V transpose.",
                     attempt_type="independent_attempt", hints_used=hints),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4), clock=FrozenClock(moment),
    )


def _tasks(repository, episode_id):
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id FROM followup_tasks WHERE kind = 'cold_retry' AND remediation_episode_id = ? "
            "ORDER BY created_at, id", (episode_id,)).fetchall()
    return [repository.followup_task(str(row["id"])) for row in rows]


def _table(repository, sql):
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql)]


ASSISTED_AT = NOW + timedelta(days=1, hours=1)


# -- the schedule (fail-first) -----------------------------------------------------------------------


def test_help_on_a_due_cold_retry_schedules_one_fresh_retry_on_another_surface(tmp_path):
    vault, repository, episode, primed, cold_item = _repair(tmp_path)
    spare = _spare(repository, episode)
    [old] = _tasks(repository, episode["id"])
    assisted = _answer(vault, repository, cold_item, ASSISTED_AT, hints=1)

    # The assisted retry is withdrawn in the attempt's own step, with the typed disposition.
    withdrawn, fresh = _tasks(repository, episode["id"])
    assert withdrawn["id"] == old["id"] and withdrawn["status"] == "expired"
    assert withdrawn["consumed_attempt_id"] is None
    outcome = repository.causal_cold_outcome_for_task(old["id"])
    assert outcome["outcome"] == WITHDRAWN_COLD_RETRY_OUTCOME
    detail = outcome["detail"] if isinstance(outcome.get("detail"), dict) else json.loads(outcome["detail_json"])
    assert detail["stage"] == "submit" and detail["reason"] == COLD_CHECK_HELP_TAKEN

    # One fresh retry for the same repair, on a surface the repair has not used.
    primed_item = repository.fetch_practice_attempt(primed.attempt_id)["practice_item_id"]
    assert fresh["status"] == "pending" and fresh["selected_item_id"] == spare
    assert spare not in {primed_item, cold_item}
    assert (fresh["case_kind"], fresh["case_ref"]) == (old["case_kind"], old["case_ref"])
    # Timed by the lane's existing rule, from the attempt that took the help.
    assert fresh["not_before"] == _iso(ASSISTED_AT + COLD_RETRIEVAL_DELAY)
    assert fresh["expires_at"] == _iso(ASSISTED_AT + COLD_RETRIEVAL_DELAY + COLD_RETRY_WINDOW)
    # It carries the repair's scheduling-time context (the primed source) and where it came from.
    assert fresh["source_attempt_id"] == old["source_attempt_id"] == primed.attempt_id
    assert fresh["context"]["source_attempt_id"] == old["context"]["source_attempt_id"]
    marker = fresh["context"][ASSISTED_RESCHEDULE_CONTEXT_KEY]
    assert marker["from_task_id"] == old["id"] and marker["assisted_attempt_id"] == assisted.attempt_id
    assert marker["withdrawn_cold_item_id"] == cold_item
    # Its opportunity is decided "scheduled"; the episode waits on the fresh surface.
    [decision] = _table(repository, "SELECT d.* FROM cold_measurement_opportunity_decisions d JOIN "
                                    "cold_measurement_opportunities o ON o.id = d.measurement_opportunity_id "
                                    f"WHERE o.trigger_kind = 'assisted_cold_retry' AND o.trigger_ref = '{old['id']}'")
    assert decision["decision"] == "scheduled" and decision["followup_task_id"] == fresh["id"]
    episode_now = repository.remediation_episode(episode["id"])
    assert episode_now["state"] == "cold_scheduled" and episode_now["cold_item_id"] == spare


def test_the_fresh_retry_is_invisible_until_due_then_measures_the_repair_cold(tmp_path):
    from learnloop.attempts.coldness_receipt import evaluate_final_coldness

    vault, repository, episode, _primed, cold_item = _repair(tmp_path)
    spare = _spare(repository, episode)
    assisted = _answer(vault, repository, cold_item, ASSISTED_AT, hints=1)
    _withdrawn, fresh = _tasks(repository, episode["id"])
    assert repository.active_followup_task_for_item(spare, kind="cold_retry",
                                                     at=_iso(ASSISTED_AT + timedelta(hours=23))) is None

    due = ASSISTED_AT + COLD_RETRIEVAL_DELAY + timedelta(minutes=5)
    cold = _answer(vault, repository, spare, due)
    consumed = repository.followup_task(fresh["id"])
    assert consumed["status"] == "consumed" and consumed["consumed_attempt_id"] == cold.attempt_id
    episode_now = repository.remediation_episode(episode["id"])
    assert episode_now["state"] == "completed" and episode_now["cold_attempt_id"] == cold.attempt_id

    evaluation = evaluate_final_coldness(vault, repository, task=consumed, cold_attempt_id=cold.attempt_id,
                                         clock=FrozenClock(due))
    assert evaluation.hard_contamination is None
    assert evaluation.derived["qualifies_as_cold_retrieval"] is True
    # Honest attribution: the help taken in between is recorded as a co-intervention.
    assert assisted.attempt_id in evaluation.derived["retrieval_cointervention_event_ids"]


def test_an_unassisted_cold_retry_is_consumed_as_before_and_schedules_nothing(tmp_path):
    vault, repository, episode, _primed, cold_item = _repair(tmp_path)
    result = _answer(vault, repository, cold_item, ASSISTED_AT)
    [task] = _tasks(repository, episode["id"])
    assert task["status"] == "consumed" and task["consumed_attempt_id"] == result.attempt_id


# -- the bound ---------------------------------------------------------------------------------------


def test_help_on_the_fresh_retry_too_ends_it_and_spawns_nothing(tmp_path):
    vault, repository, episode, _primed, cold_item = _repair(tmp_path)
    spare = _spare(repository, episode)
    _answer(vault, repository, cold_item, ASSISTED_AT, hints=1)
    _withdrawn, fresh = _tasks(repository, episode["id"])

    again = ASSISTED_AT + COLD_RETRIEVAL_DELAY + timedelta(minutes=5)
    _answer(vault, repository, spare, again, hints=1)
    tasks = _tasks(repository, episode["id"])
    assert len(tasks) == 2  # one fresh retry per chain
    assert tasks[1]["id"] == fresh["id"] and tasks[1]["status"] == "expired"
    assert repository.causal_cold_outcome_for_task(fresh["id"])["outcome"] == WITHDRAWN_COLD_RETRY_OUTCOME
    # A third assisted answer anywhere in the repair finds no open retry and schedules nothing.
    _answer(vault, repository, cold_item, again + timedelta(days=2), hints=1)
    assert len(_tasks(repository, episode["id"])) == 2


def test_without_another_independent_surface_the_refusal_is_recorded_and_nothing_is_scheduled(tmp_path):
    vault, repository, episode, _primed, cold_item = _repair(tmp_path, third=False)
    [old] = _tasks(repository, episode["id"])
    _answer(vault, repository, cold_item, ASSISTED_AT, hints=1)
    [withdrawn] = _tasks(repository, episode["id"])
    assert withdrawn["status"] == "expired"
    [decision] = _table(repository, "SELECT d.* FROM cold_measurement_opportunity_decisions d JOIN "
                                    "cold_measurement_opportunities o ON o.id = d.measurement_opportunity_id "
                                    f"WHERE o.trigger_kind = 'assisted_cold_retry' AND o.trigger_ref = '{old['id']}'")
    assert (decision["decision"], decision["reason"]) == ("structurally_refused", "no_independent_surface")
    assert repository.remediation_episode(episode["id"])["cold_item_id"] == cold_item


# -- certification probes are not rescheduled ----------------------------------------------------------


def test_an_assisted_certification_probe_is_left_as_the_predecessor_leaves_it(tmp_path):
    vault, repository, _episode, _primed, _cold_item = _repair(tmp_path)
    spare = _spare(repository, _episode)
    probe = repository.create_followup_task(
        kind="certification_cold_probe", case_kind="certification", case_ref="cert_test",
        not_before=_iso(NOW), expires_at=_iso(NOW + timedelta(days=30)), selected_item_id=spare,
        context={"kind": "certification_cold_probe", "certificate_id": "cert_test"},
        learning_object_id="lo_svd_definition", clock=FrozenClock(NOW),
    )
    _answer(vault, repository, spare, ASSISTED_AT, hints=1)
    assert repository.followup_task(probe["id"])["status"] in {"pending", "served"}
    probes = _table(repository, "SELECT id FROM followup_tasks WHERE kind = 'certification_cold_probe'")
    assert [row["id"] for row in probes] == [probe["id"]]


# -- the switch: off, or below the tag, is the predecessor --------------------------------------------


@pytest.mark.parametrize(("version", "switch", "converts", "active"), [
    (TAG, None, True, True), (TAG, False, True, False), (TAG, None, False, False),
    (PREDECESSOR, None, True, False), (PREDECESSOR, True, True, False),
], ids=["tag", "tag-switch-off", "tag-ca2-off", "predecessor", "predecessor-switch-on"])
def test_the_gate_is_the_tag_its_switch_and_ca2s_rule(tmp_path, version, switch, converts, active):
    vault, _repository, _episode, _primed, _cold = _repair(tmp_path, version=version, switch=switch,
                                                           converts=converts)
    assert reschedule_cold_after_assist_active(vault) is active
    assert reschedule_cold_after_assist_active(None) is False


def _predecessor_state(repository, episode_id):
    """What the lane holds after the assisted answer, without ids and write times."""

    tasks = [{key: task[key] for key in ("kind", "status", "selected_item_id", "not_before", "expires_at",
                                         "consumed_attempt_id")} for task in _tasks(repository, episode_id)]
    episode = repository.remediation_episode(episode_id)
    outcomes = _table(repository, "SELECT outcome FROM causal_cold_outcomes")
    decisions = _table(repository, "SELECT decision, reason FROM cold_measurement_opportunity_decisions "
                                   "ORDER BY created_at, id")
    return tasks, (episode["state"], episode["cold_item_id"]), outcomes, decisions


@pytest.mark.parametrize(("version", "switch"), [(TAG, False), (PREDECESSOR, None)],
                         ids=["tag-switch-off", "predecessor"])
def test_off_or_below_the_tag_the_assisted_retry_is_left_open_exactly_as_the_predecessor(tmp_path, version, switch):
    from learnloop.scheduling.scheduler import apply_eligibility_writes, cold_check_decision

    vault, repository, episode, _primed, cold_item = _repair(tmp_path, version=version, switch=switch)
    _answer(vault, repository, cold_item, ASSISTED_AT, hints=1)
    reference_vault, reference, ref_episode, _p, ref_cold = _repair(tmp_path / "ref", version=PREDECESSOR)
    _answer(reference_vault, reference, ref_cold, ASSISTED_AT, hints=1)
    assert _predecessor_state(repository, episode["id"]) == _predecessor_state(reference, ref_episode["id"])

    [task] = _tasks(repository, episode["id"])
    assert task["status"] in {"pending", "served"}
    assert repository.remediation_episode(episode["id"])["cold_item_id"] == cold_item
    # ...and the next serve withdraws it as practised since scheduled (the predecessor's rule).
    later = _iso(ASSISTED_AT + timedelta(minutes=10))
    decision = cold_check_decision(vault, repository, cold_item, now_iso=later)
    apply_eligibility_writes(vault, repository, decision, clock=FrozenClock(ASSISTED_AT + timedelta(minutes=10)))
    assert repository.followup_task(task["id"])["status"] == "expired"
    assert len(_tasks(repository, episode["id"])) == 1


# -- replay and rebuild equivalence -------------------------------------------------------------------


def test_replay_schedules_nothing_and_leaves_the_lane_as_live_left_it(tmp_path):
    from learnloop.substrate.replay import rebuild_derived_state

    vault, repository, episode, _primed, cold_item = _repair(tmp_path)
    _answer(vault, repository, cold_item, ASSISTED_AT, hints=1)
    sql = "SELECT * FROM followup_tasks ORDER BY id"
    before = (_table(repository, sql), _table(repository, "SELECT * FROM remediation_episodes ORDER BY id"),
              _table(repository, "SELECT id FROM cold_measurement_opportunities ORDER BY id"))
    rebuild_derived_state(load_vault(vault.root), repository, clock=FrozenClock(ASSISTED_AT + timedelta(hours=2)))
    after = (_table(repository, sql), _table(repository, "SELECT * FROM remediation_episodes ORDER BY id"),
             _table(repository, "SELECT id FROM cold_measurement_opportunities ORDER BY id"))
    assert after == before
    assert len(_tasks(repository, episode["id"])) == 2


def _equivalent_repair(tmp_path, *, switch: bool):
    """The repair on a rebuild-equivalent vault (the placement vault at the tag,
    synced, as tests/test_rebuild_equivalence.py builds it; the basic vault's
    seeded due item is not rebuild-equivalent at any version)."""

    from learnloop.substrate.state_sync import sync_vault_state

    paths = create_placement_vault(tmp_path / "vault", version=TAG)
    add_followup_item(paths.root)
    add_followup_item(paths.root, THIRD_ITEM)
    set_config(paths.root, {("practice", "reschedule_cold_after_assist"): switch})
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    misconception_id = repository.insert_misconception(
        learning_object_id="lo_svd_definition", statement="Confuses SVD with eigendecomposition.",
        correction_statement="SVD applies to any matrix.", facet_ids=["recall"], target_facet="recall",
        confused_with_facet="application", severity=0.8, clock=FrozenClock(NOW),
    )
    episode, _primed, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    return paths, vault, repository, episode, cold_item


@pytest.mark.parametrize("switch", [True, False], ids=["on", "off"])
def test_a_shadow_rebuild_is_zero_with_the_fresh_retries_present(tmp_path, switch):
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    paths, vault, repository, episode, cold_item = _equivalent_repair(tmp_path, switch=switch)
    spare = _spare(repository, episode)
    _answer(vault, repository, cold_item, ASSISTED_AT, hints=1)
    _answer(vault, repository, spare, ASSISTED_AT + COLD_RETRIEVAL_DELAY + timedelta(minutes=5))
    statuses = [task["status"] for task in _tasks(repository, episode["id"])]
    assert statuses == (["expired", "consumed"] if switch else ["pending"])
    result = shadow_rebuild(load_vault(paths.root))
    assert result.live_database_unchanged
    assert result.learner_state_diff["summary"] == {"mastery": 0, "facet": 0, "schedule": 0}


# -- the chain and the upgrade -------------------------------------------------------------------------


@pytest.fixture
def _cli_process(monkeypatch):
    """This process as the CLI is: importing it installs the completion."""

    from learnloop import activation_journal
    from learnloop.cli.runtime import _complete_interrupted_activation

    monkeypatch.setattr(activation_journal, "_COMPLETER", _complete_interrupted_activation)


def _vault_at(tmp_path, name, version):
    return create_placement_vault(tmp_path / name, version=version)


def _version(paths) -> str:
    return load_vault(paths.root).config.algorithms.algorithm_version


def _journal(paths):
    return paths.sqlite_path.with_name(paths.sqlite_path.name + ".claim-fixes-activation")


def _activated(paths, version=TAG) -> bool:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return connection.execute(
            "SELECT 1 FROM derived_state_rebuilds WHERE scope = 'p0_projection_activation' AND algorithm_version = ?",
            (version,),
        ).fetchone() is not None


def test_mvp038_is_one_constant_after_mvp037_and_the_latest():
    from learnloop.cold_retry_reschedule_upgrade import PREDECESSOR as UPGRADE_PREDECESSOR
    from learnloop.config.schema import PracticeConfig
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
    from learnloop.params.parameter_registry import classify_config_path

    assert SUCCESSOR_CHAIN[-3:] == (SUPERSEDED_CLAIMS_ALGORITHM_VERSION, PREDECESSOR, TAG) == (
        "mvp-0.36", "mvp-0.37", "mvp-0.38")
    assert TAG == LATEST_ALGORITHM_VERSION and UPGRADE_PREDECESSOR == PREDECESSOR
    assert COLD_RETRY_RESCHEDULE_VERSIONS == frozenset({TAG})
    assert PracticeConfig().reschedule_cold_after_assist is True
    rule = classify_config_path("practice.reschedule_cold_after_assist")
    assert rule is not None and rule.kind == "structural" and "kill switch" in rule.rationale
    for version in SUCCESSOR_CHAIN:
        assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[version] == defaults_fingerprint_for_version(version), version
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[PREDECESSOR]


@pytest.mark.parametrize("start", ["mvp-0.9", "mvp-0.30", "mvp-0.35", "mvp-0.36", "mvp-0.37"])
def test_upgrade_to_mvp038_works_from_supported_versions(tmp_path, _cli_process, start):
    from learnloop.cli import app

    paths = _vault_at(tmp_path, "v", start)
    result = CliRunner().invoke(app, ["upgrade", "--to", TAG, "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{start} -> {TAG}" in result.output
    assert _version(paths) == TAG and _activated(paths) and not _journal(paths).exists()
    if start != PREDECESSOR:
        assert _activated(paths, PREDECESSOR)


def test_a_bare_upgrade_targets_mvp038_and_refuses_twice(tmp_path, _cli_process):
    from learnloop.cli import app
    from learnloop.cold_retry_reschedule_upgrade import upgrade_to_cold_retry_reschedule

    paths = _vault_at(tmp_path, "v", PREDECESSOR)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{PREDECESSOR} -> {TAG}" in result.output and _version(paths) == TAG
    again = upgrade_to_cold_retry_reschedule(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_refuses_a_version_before_the_chain(tmp_path):
    from learnloop.cold_retry_reschedule_upgrade import upgrade_to_cold_retry_reschedule

    paths = _vault_at(tmp_path, "old", "mvp-0.9")
    rewrite_algorithm_version(paths.root / "learnloop.toml", "mvp-0.9", "mvp-0.8", durable=True)
    result = upgrade_to_cold_retry_reschedule(paths.root)
    assert not result.upgraded and _version(paths) == "mvp-0.8"
    assert "cannot upgrade from 'mvp-0.8'" in result.problems[0]


def _interrupted(tmp_path, name, predecessor=PREDECESSOR, target=TAG):
    paths = _vault_at(tmp_path, name, predecessor)
    _journal(paths).write_text(json.dumps({"predecessor": predecessor, "target": target}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", predecessor, target, durable=True)
    assert not _activated(paths, target)
    return paths


def test_the_next_cli_command_completes_an_interrupted_mvp038_activation(tmp_path, _cli_process):
    from learnloop.cli import app
    from learnloop.cold_retry_reschedule_upgrade import upgrade_to_cold_retry_reschedule

    paths = _interrupted(tmp_path, "interrupted")
    result = CliRunner().invoke(app, ["backfill-originals", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert not _journal(paths).exists() and _activated(paths) and _version(paths) == TAG
    again = upgrade_to_cold_retry_reschedule(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_completes_its_own_journal(tmp_path):
    from learnloop.cold_retry_reschedule_upgrade import upgrade_to_cold_retry_reschedule

    paths = _interrupted(tmp_path, "interrupted")
    result = upgrade_to_cold_retry_reschedule(paths.root)
    assert result.upgraded and result.notes == [f"completed the interrupted activation of {TAG}"]
    assert not _journal(paths).exists() and _activated(paths)


def test_a_failure_after_the_rename_leaves_the_predecessor_and_no_journal(tmp_path, monkeypatch):
    import learnloop.cold_retry_reschedule_upgrade as upgrade

    paths = _vault_at(tmp_path, "failing", PREDECESSOR)
    real = upgrade._publish_algorithm_version

    def publish_then_fail(config_path, from_version, to_version, *, renamed=None):
        real(config_path, from_version, to_version, renamed=renamed)
        if to_version == TAG:
            raise OSError("the directory fsync failed")

    monkeypatch.setattr(upgrade, "_publish_algorithm_version", publish_then_fail)
    with pytest.raises(OSError):
        upgrade.upgrade_to_cold_retry_reschedule(paths.root)
    assert _version(paths) == PREDECESSOR and not _journal(paths).exists() and not _activated(paths)


def test_an_interrupted_mvp037_activation_then_upgrade_to_mvp038_completes_it(tmp_path, _cli_process):
    """`learnloop upgrade --to mvp-0.38` over an interrupted mvp-0.37
    activation: the CLI's opener (this link's completion, the chain's latest)
    hands the mvp-0.37 journal to its own link, which completes it; the
    upgrade then activates mvp-0.38 from mvp-0.37."""

    from learnloop.cli import app

    paths = _interrupted(tmp_path, "interrupted037", SUPERSEDED_CLAIMS_ALGORITHM_VERSION, PREDECESSOR)
    result = CliRunner().invoke(app, ["upgrade", "--to", TAG, "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{PREDECESSOR} -> {TAG}" in result.output
    assert _version(paths) == TAG and not _journal(paths).exists()
    assert _activated(paths, PREDECESSOR) and _activated(paths)


def test_without_a_completion_an_attach_refuses_and_the_upgrade_still_completes_the_mvp037_journal(
        tmp_path, monkeypatch):
    from learnloop import activation_journal
    from learnloop.cold_retry_reschedule_upgrade import complete_interrupted_activation, upgrade_to_cold_retry_reschedule

    paths = _interrupted(tmp_path, "refused037", SUPERSEDED_CLAIMS_ALGORITHM_VERSION, PREDECESSOR)
    monkeypatch.setattr(activation_journal, "_COMPLETER", None)
    with pytest.raises(activation_journal.InterruptedActivation, match=f"learnloop upgrade --to {PREDECESSOR}"):
        Repository(paths.sqlite_path)
    assert _version(paths) == PREDECESSOR and _journal(paths).exists()
    assert complete_interrupted_activation(paths.root) == PREDECESSOR
    assert not _journal(paths).exists() and complete_interrupted_activation(paths.root) is None
    result = upgrade_to_cold_retry_reschedule(paths.root)
    assert result.upgraded and result.from_version == PREDECESSOR and _version(paths) == TAG
    assert not _journal(paths).exists() and _activated(paths, PREDECESSOR) and _activated(paths)
