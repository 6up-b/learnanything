"""Daily-loop DL2 Codex re-review (job 20261020-003824-5riC17): the fail-first tests.

F2 (the successor, reopened), F3 (a "Check once" answered under a sibling's
hold, reopened) and F11 (an unavailable cold sibling suppressing the only
servable candidate). Each test names its finding. The behaviour tests (the
first eight) ran against ``a220306fb`` (the re-reviewed commit): six failed for
the reason the finding gives and the two positive controls passed. The F2
chain, gate, upgrade and new-vault pins name the new tag and have no
predecessor to fail on. Fakes only; no model is ever called.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.daily_plan.engine import PlanEnv, build_plan
from learnloop.intent.checks import PRACTICE_BANNER, served_check, settle_answered_checks
from learnloop.scheduling import serving_exclusions
from learnloop.scheduling.intent.serving import intent_enabled, intent_serving
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.daily_plan_fakes import MovableClock, iso
from tests.intent_fakes import ITEM_LO, NOW, OURS, make_intent_vault

#: The predecessor: the newest tag below the intent successor on this branch.
PREDECESSOR = "mvp-0.27"


@pytest.fixture
def iv(tmp_path):
    return make_intent_vault(tmp_path / "vault")


def _reveal(repository, item_id, at, *, routine=False, attempt_id=None):
    repository.insert_reveal_event(
        {
            "practice_item_id": item_id,
            "learning_object_id": ITEM_LO.get(item_id),
            "source_kind": "answer_display" if routine else "tutor_answer",
            "basis": f"feedback_full_answer:{item_id}" if routine else None,
            "amount": 1.0,
            "attempt_id": attempt_id,
            "created_at": iso(at),
        }
    )


def _retire(iv, item_id):
    path = next(iv.root.rglob(f"{item_id}.yaml"))
    payload = read_yaml(path)
    payload["status"] = "retired"
    write_yaml(path, payload)
    iv.reload()


def _cold_retry(iv, item_id, *, ref):
    iv.repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref=ref,
        context={"kind": "causal_cold_verification", "source_attempt_id": "att_src"},
        not_before=iso(NOW - timedelta(hours=1)), selected_item_id=item_id,
        expires_at=iso(NOW + timedelta(days=5)), clock=FrozenClock(NOW - timedelta(hours=2)),
    )


# -- F2: intent is the successor; below the tag the predecessor's code runs ---------------------------


def test_f2_below_the_tag_commitments_change_nothing_with_the_switch_on(tmp_path):
    bare = make_intent_vault(tmp_path / "bare", version=PREDECESSOR)
    chosen = make_intent_vault(tmp_path / "chosen", version=PREDECESSOR)
    assert chosen.vault.config.intent.enabled, "sanity: the switch is on (its default)"
    chosen.choose("learning_object", "lo_a", "pause", NOW)
    chosen.choose("learning_object", "lo_b", "check_once", NOW)
    chosen.choose("learning_object", "lo_c", "light_touch", NOW)
    at = NOW + timedelta(days=8)
    assert not intent_enabled(chosen.vault.config)
    assert intent_serving(chosen.vault, chosen.repository, now=at) is None

    def ranked(iv):
        return [
            (entry.practice_item_id, round(entry.priority, 12), tuple(sorted(entry.components.items())))
            for entry in build_due_queue(iv.vault, iv.repository, clock=FrozenClock(at), persist_explanations=False)
            if entry.practice_item_id in OURS
        ]

    assert ranked(bare) == ranked(chosen)
    plans = []
    for iv in (bare, chosen):
        env = PlanEnv(vault=iv.vault, repository=iv.repository, clock=MovableClock(at), session_id=None)
        record = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        blocks = [[(item.practice_item_id, item.lane, item.check_kind) for item in block.items] for block in record.blocks]
        plans.append((record.split.get("pool"), record.admission, blocks))
    assert plans[0] == plans[1]


def test_f2_below_the_tag_a_paused_items_cold_retry_is_still_served(tmp_path):
    """The re-review's trigger: at the successor a paused item's pending cold
    retry waits (F1); below it the measurement is admitted as before."""

    below = make_intent_vault(tmp_path / "below", version=PREDECESSOR)
    _cold_retry(below, "pi_a1", ref="mc_f2")
    below.choose("learning_object", "lo_a", "pause", NOW + timedelta(minutes=1))
    assert below.queue(NOW + timedelta(minutes=2))[0] == "pi_a1"

    at_tag = make_intent_vault(tmp_path / "at_tag")
    _cold_retry(at_tag, "pi_a1", ref="mc_f2b")
    at_tag.choose("learning_object", "lo_a", "pause", NOW + timedelta(minutes=1))
    assert "pi_a1" not in at_tag.queue(NOW + timedelta(minutes=2))


def test_f2_the_intent_control_is_off_below_the_tag(tmp_path):
    from learnloop_sidecar.handlers.intent import get_intent

    class _Ctx:
        def __init__(self, iv):
            self._iv = iv

        def require_vault(self):
            return self._iv.vault, self._iv.repository

    below = make_intent_vault(tmp_path / "below", version=PREDECESSOR)
    from learnloop_sidecar.handlers.intent import IntentScopeInput

    params = IntentScopeInput(scope_kind="learning_object", scope_id="lo_a")
    assert get_intent(_Ctx(below), params)["enabled"] is False
    at_tag = make_intent_vault(tmp_path / "at_tag")
    assert get_intent(_Ctx(at_tag), params)["enabled"] is True


# -- F3: an attempt answers a check only when the check could be taken cold then ----------------------


def test_f3_an_attempt_under_a_siblings_hold_is_practice_not_the_check(iv):
    commitment = iv.choose("learning_object", "lo_a", "check_once", NOW).commitment_id
    due_day = NOW + timedelta(days=8)
    # B's answer is shown an hour before the check is due: the whole LO is
    # held for one cold delay.
    _reveal(iv.repository, "pi_a2", due_day - timedelta(hours=1))
    assert iv.serving(due_day).withhold_reason("pi_a1") == "intent_check_held"
    view = served_check(iv.vault, iv.repository, "pi_a1", now=due_day)
    assert view["cold"] is False and view["banner"] == PRACTICE_BANNER
    # A is opened anyway; submit does not prime it (the reveal is B's).
    attempt_at = due_day + timedelta(minutes=5)
    iv.answer("pi_a1", attempt_at)
    later = FrozenClock(attempt_at + timedelta(minutes=1))
    assert settle_answered_checks(iv.vault, iv.repository, clock=later) == []
    assert C.resolve_disposition(iv.repository, commitment) == "one_check_pending"
    (check,) = iv.serving(attempt_at + timedelta(minutes=1)).checks.values()
    assert check.answered_by is None and check.date_source == "after_practice"
    assert check.date == attempt_at + timedelta(days=7)


def test_f3_a_cold_attempt_still_answers_the_check_its_own_feedback_notwithstanding(iv):
    commitment = iv.choose("learning_object", "lo_a", "check_once", NOW).commitment_id
    due_day = NOW + timedelta(days=8)
    assert served_check(iv.vault, iv.repository, "pi_a1", now=due_day)["cold"] is True
    attempt_at = due_day + timedelta(minutes=5)
    attempt_id = iv.answer("pi_a1", attempt_at)
    # The answer shown as this attempt's own feedback, in its own second.
    _reveal(iv.repository, "pi_a1", attempt_at, routine=True, attempt_id=attempt_id)
    later = FrozenClock(attempt_at + timedelta(minutes=1))
    assert settle_answered_checks(iv.vault, iv.repository, clock=later) == [commitment]
    assert C.resolve_disposition(iv.repository, commitment) == "satisfied"


# -- F11: candidates routine serving can never serve do not decide the check ----------------------------


def _exposed_a1_check(iv):
    iv.choose("learning_object", "lo_a", "check_once", NOW)
    due_day = NOW + timedelta(days=8)
    # Standing exposure on A (only an attempt absorbs a tutor answer), two
    # days back: past the LO's one-day hold, so it alone decides A.
    _reveal(iv.repository, "pi_a1", due_day - timedelta(days=2))
    return due_day


def test_f11_a_retired_cold_sibling_never_suppresses_the_servable_candidate(iv):
    due_day = _exposed_a1_check(iv)
    _retire(iv, "pi_a2")
    assert "pi_a1" in iv.queue(due_day)
    assert iv.serving(due_day).withhold_reason("pi_a1") is None
    assert served_check(iv.vault, iv.repository, "pi_a1", now=due_day)["cold"] is False


def test_f11_a_held_out_cold_sibling_never_suppresses_the_servable_candidate(iv, monkeypatch):
    due_day = _exposed_a1_check(iv)
    monkeypatch.setattr(serving_exclusions, "held_out_selection_active", lambda vault: True)
    monkeypatch.setattr(serving_exclusions, "held_out_items", lambda vault, repository: frozenset({"pi_a2"}))
    queue = iv.queue(due_day)
    assert "pi_a2" not in queue and "pi_a1" in queue
    assert iv.serving(due_day).withhold_reason("pi_a1") is None


def test_f11_an_available_cold_sibling_is_still_preferred(iv):
    due_day = _exposed_a1_check(iv)
    lo_a = [item for item in iv.queue(due_day) if item in ("pi_a1", "pi_a2")]
    assert lo_a == ["pi_a2"]
    assert iv.serving(due_day).withhold_reason("pi_a1") == "intent_check_held"


# -- F2: the tag, its upgrade and its snapshot ----------------------------------------------------------


def test_f2_the_chain_ends_at_the_intent_successor():
    from learnloop.algorithm_versions import (
        ELIGIBILITY_DECISION_VERSIONS,
        INTENT_ALGORITHM_VERSION,
        INTENT_VERSIONS,
        LATEST_ALGORITHM_VERSION,
        P0_PROJECTION_VERSIONS,
        SUCCESSOR_CHAIN,
    )
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version

    # Reader workbench RW2d's field signals (built as mvp-0.31) followed it and keep it.
    assert INTENT_ALGORITHM_VERSION == "mvp-0.29" == SUCCESSOR_CHAIN[-2]
    assert LATEST_ALGORITHM_VERSION == SUCCESSOR_CHAIN[-1] == "mvp-0.31"
    assert SUCCESSOR_CHAIN[-3] == PREDECESSOR
    assert INTENT_VERSIONS == frozenset({"mvp-0.29", "mvp-0.31"})
    assert "mvp-0.29" in ELIGIBILITY_DECISION_VERSIONS and "mvp-0.29" in P0_PROJECTION_VERSIONS
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.29"] == defaults_fingerprint_for_version("mvp-0.29")


def test_f2_the_gate_reads_the_version_and_the_switch(tmp_path):
    from tests.helpers import append_config_toml

    at_tag = make_intent_vault(tmp_path / "at_tag")
    assert intent_enabled(at_tag.vault.config)
    append_config_toml(at_tag.root, "[intent]\nenabled = false\n")
    at_tag.reload()
    assert not intent_enabled(at_tag.vault.config)
    for version in ("mvp-0.14", "mvp-0.26", PREDECESSOR):
        assert not intent_enabled(make_intent_vault(tmp_path / version, version=version).vault.config)


def test_f2_the_upgrade_takes_the_predecessor_or_the_chain_and_refuses_the_rest(tmp_path):
    from typer.testing import CliRunner

    from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
    from learnloop.cli.app import app
    from learnloop.intent_upgrade import upgrade_to_mvp029
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_placement_vault

    clock = FrozenClock(NOW)
    direct = create_placement_vault(tmp_path / "direct", version=PREDECESSOR)
    result = upgrade_to_mvp029(direct.root, clock=clock)
    assert result.upgraded and (result.from_version, result.to_version) == (PREDECESSOR, "mvp-0.29")
    assert load_vault(direct.root).config.algorithms.algorithm_version == "mvp-0.29"
    again = upgrade_to_mvp029(direct.root, clock=clock)
    assert not again.upgraded and again.problems == ["vault is already mvp-0.29"]

    chained = create_placement_vault(tmp_path / "chained", version="mvp-0.24")
    assert upgrade_to_mvp029(chained.root, clock=clock).upgraded
    assert load_vault(chained.root).config.algorithms.algorithm_version == "mvp-0.29"

    old = create_placement_vault(tmp_path / "old", version="mvp-0.8")
    refused = upgrade_to_mvp029(old.root, clock=clock)
    assert not refused.upgraded and f"only {PREDECESSOR!r}" in refused.problems[0]
    assert load_vault(old.root).config.algorithms.algorithm_version == "mvp-0.8"

    cli = create_placement_vault(tmp_path / "cli", version=PREDECESSOR)
    invoked = CliRunner().invoke(app, ["upgrade", "--vault", str(cli.root)])
    assert invoked.exit_code == 0, invoked.output
    # The default is the latest successor (RW2d's), through this step.
    assert f"{PREDECESSOR} -> {LATEST_ALGORITHM_VERSION}" in invoked.output


def test_f2_new_vaults_start_at_the_successor_with_intent_live(tmp_path):
    from learnloop.bootstrap import init_vault
    from learnloop.vault.loader import load_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(NOW))
    config = load_vault(tmp_path / "fresh").config
    assert config.algorithms.algorithm_version == "mvp-0.31"  # RW2d's successor keeps intent
    assert intent_enabled(config)
