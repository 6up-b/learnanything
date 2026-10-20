"""Daily-loop DL2 fix round 7 (the verify of ``b08eea05a``, Codex job
20261020-145125-pSv997): the fail-first tests.

F21 (Medium): a due "Check once" on an LO with no practice items vanished
from the plan's accounting (``CheckState.pending`` read an empty candidate
list as "replaced"). Replacement is now tracked on its own: a check whose
scope the commitment still governs stays due and is recorded as
``no_candidates``; a genuinely replaced one (every item it covered decided by
another commitment) is still suppressed.

F22 (Medium): an error inside the admission predicate escaped the check gate.
Every read the gate makes is now caught and refused as
``constraints_unavailable``, naming the failing input.

The behaviour tests ran against ``b08eea05a`` and failed for the reasons the
findings give; the controls passed. Fakes only; no model is ever asked.
"""

from __future__ import annotations

import sqlite3
from datetime import timedelta

import pytest

from learnloop.algorithm_versions import INTENT_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.content.sources import exam_material
from learnloop.daily_plan.engine import PlanEnv, build_plan
from learnloop.daily_plan.policy import policy_for
from learnloop.db.repositories import MasteryState, Repository
from learnloop.intent.control import Scope, apply_choice
from learnloop.scheduling import scheduler
from learnloop.scheduling.intent import feasibility
from learnloop.scheduling.intent.serving import intent_serving
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from tests.daily_plan_fakes import MovableClock, iso, record_attempt, seed_due
from tests.helpers import append_config_toml, create_daily_plan_vault
from tests.intent_fakes import NOW, make_intent_vault
from tests.router_model_fakes import fake_runtime

POLICIES = ("dl1_pair", "staged", "mixture")
POLICY_TOML = {
    "dl1_pair": "[router]\nenabled = false\n",
    "staged": '[router]\nmode = "staged"\n',
    "mixture": '[router]\nmode = "mixture"\nrestraint = false\n',
}
DUE_DAY = NOW + timedelta(days=8)


def _plan(vault, repository, at, *, budget=15.0):
    clock = MovableClock(at)
    policy = policy_for(vault, repository, clock=clock, runtime=fake_runtime(), serve=True)
    env = PlanEnv(vault=vault, repository=repository, clock=clock, policy=policy)
    return build_plan(env, kind="normal", budget=budget, remembered=int(budget), minutes_source="chip")


def _misses(record, commitment):
    return [row for row in record.split.get("checks_unplanned") or [] if row["commitment_id"] == commitment]


# -- F21: a check whose scope has no items yet ------------------------------------------------------


def _empty_lo_world(tmp_path, name):
    los = {"lo_full": [("pi_full", 2.0)], "lo_empty": []}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los, version=INTENT_ALGORITHM_VERSION)
    append_config_toml(paths.root, POLICY_TOML[name])
    vault = load_vault(paths.root)
    assert "lo_empty" in vault.learning_objects
    assert not [item for item in vault.practice_items.values() if item.learning_object_id == "lo_empty"]
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    reviewed = NOW - timedelta(days=10)
    record_attempt(repository, "pi_full", "lo_full", reviewed)
    seed_due(repository, "pi_full", due=NOW - timedelta(days=1), last=reviewed)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_full", logit_mean=0.0, logit_variance=1.0, evidence_count=1,
            last_evidence_at=iso(reviewed), algorithm_version=vault.config.algorithms.algorithm_version,
            updated_at=iso(reviewed),
        )
    )
    commitment = apply_choice(vault, repository, Scope("learning_object", "lo_empty"), "check_once",
                              clock=FrozenClock(NOW)).commitment_id
    return vault, repository, commitment


@pytest.mark.parametrize("name", POLICIES)
def test_f21_a_due_check_on_an_lo_with_no_items_is_recorded_as_no_candidates(tmp_path, name):
    vault, repository, commitment = _empty_lo_world(tmp_path, name)
    view = intent_serving(vault, repository, now=DUE_DAY)
    assert [check.commitment_id for check in view.due_checks()] == [commitment]
    record = _plan(vault, repository, DUE_DAY)
    (miss,) = _misses(record, commitment)
    assert miss["reason"] == "no_candidates"
    assert miss["refused_candidates"] == []
    assert miss["line"] == "Nothing to check yet: this topic has no questions."


@pytest.mark.parametrize("name", POLICIES)
def test_f21_control_a_genuinely_replaced_check_is_still_suppressed(tmp_path, name):
    """Every item the LO check covered is decided by a later item choice: the
    check is replaced everywhere and the plan neither plans nor records it."""

    iv = make_intent_vault(tmp_path / "vault")
    append_config_toml(iv.root, POLICY_TOML[name])
    iv.reload()
    commitment = iv.choose("learning_object", "lo_a", "check_once", NOW).commitment_id
    iv.choose("practice_item", "pi_a1", "pause", NOW + timedelta(minutes=1))
    iv.choose("practice_item", "pi_a2", "pause", NOW + timedelta(minutes=2))
    view = iv.serving(DUE_DAY)
    assert commitment not in {check.commitment_id for check in view.due_checks()}
    record = _plan(iv.vault, iv.repository, DUE_DAY)
    assert _misses(record, commitment) == []
    assert commitment not in {row["commitment_id"] for row in record.split.get("checks") or []}


# -- F22: every read the gate makes fails closed, naming its input -------------------------------------


def _due_check(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    commitment = iv.choose("practice_item", "pi_c2", "check_once", NOW).commitment_id
    return iv, commitment


def _boom(*_args, **_kwargs):
    raise sqlite3.OperationalError("disk I/O error")


def test_f22_an_admission_error_is_a_named_refusal_not_an_exception(tmp_path, monkeypatch):
    """The verify's fault injection: the protected sets read, then the
    admission predicate's item-state read raises."""

    iv, commitment = _due_check(tmp_path)
    monkeypatch.setattr(scheduler._BuildAdmission, "check_candidate_refusal", _boom)
    view = iv.serving(DUE_DAY)
    (check,) = view.due_checks()
    ((item_id, refusal),) = check.refused
    assert item_id == "pi_c2"
    assert refusal["constraint_key"] == "constraints_unavailable"
    assert refusal["detail"]["input"] == "build_admission"
    assert refusal["detail"]["error"] == "OperationalError"
    record = _plan(iv.vault, iv.repository, DUE_DAY)
    (miss,) = _misses(record, commitment)
    assert miss["reason"] == "refused_candidates"
    assert [(row["practice_item_id"], row["constraint_key"]) for row in miss["refused_candidates"]] == [
        ("pi_c2", "constraints_unavailable")
    ]


@pytest.mark.parametrize("failing", ["held_out_material", "assessment_reservation", "exam_pool"])
def test_f22_a_protected_set_error_names_its_input(tmp_path, monkeypatch, failing):
    iv, _commitment = _due_check(tmp_path)
    if failing == "held_out_material":
        monkeypatch.setattr(exam_material, "held_out_items", _boom)
    elif failing == "assessment_reservation":
        monkeypatch.setattr(feasibility, "reserved_assessment_items", _boom)
    else:
        monkeypatch.setattr(feasibility.exam_pool, "reserved_item_ids", _boom)
    (check,) = iv.serving(DUE_DAY).due_checks()
    ((_item_id, refusal),) = check.refused
    assert refusal["constraint_key"] == "constraints_unavailable"
    assert refusal["detail"]["input"] == failing


def test_f22_a_frame_error_names_its_input(tmp_path, monkeypatch):
    from learnloop.scheduling import frame_constraints

    iv, _commitment = _due_check(tmp_path)
    monkeypatch.setattr(frame_constraints, "evaluate_mandatory", _boom)
    (check,) = iv.serving(DUE_DAY).due_checks()
    ((_item_id, refusal),) = check.refused
    assert refusal["constraint_key"] == "constraints_unavailable"
    assert refusal["detail"]["input"] == "staged_frame"


def test_f22_control_no_error_no_refusal(tmp_path):
    iv, _commitment = _due_check(tmp_path)
    (check,) = iv.serving(DUE_DAY).due_checks()
    assert check.refused == () and check.servable == ("pi_c2",)

