"""Daily-loop DL2 fix round 6 (orchestrator ruling on the verify of
``1846cef39``, Codex job 20261020-133353-evoWmI): the fail-first tests.

The ruling: ONE "Check once" feasibility gate
(``scheduling.intent.serving.check_feasibility``), the same under the staged,
mixture and DL1-pair policies, which every candidate passes before it can be
selected or forced: held-out protection always (whatever
``goals.held_out_selection`` says; that switch keeps governing ordinary
serving), assessment reservations, exam pools, the build's admission, and the
staged frame's mandatory constraints (``hard_exposure_collision`` included),
evaluated even under DL1's pair purely as a check gate. Every due,
unanswered, unreplaced check is planned or recorded in ``checks_unplanned``
with its reason and each refused candidate's key.

F18 (High): held-out material became a check with ``held_out_selection``
off. F19 (Medium): under DL1's pair a check bypassed the frame's
``hard_exposure_collision``. F20 (Medium): a due check whose candidates the
admission refused vanished with no recorded miss.

The behaviour tests ran against ``1846cef39`` and failed for the reasons the
findings give; the controls passed (counts in
``docs/reviews/daily-loop-dl2-codex-review.md``). Fakes only: the mixture
policy runs on a fake runtime with no model set up, the staged one with
``router.mode = "staged"``; no model is ever asked.
"""

from __future__ import annotations

import random
from datetime import timedelta
from pathlib import Path

import pytest

from learnloop.algorithm_versions import INTENT_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.content.sources import exam_material
from learnloop.daily_plan.engine import DEFAULT_POLICY, PlanEnv, build_plan
from learnloop.daily_plan.policy import policy_for
from learnloop.db.repositories import MasteryState, Repository
from learnloop.goals import exam_pool
from learnloop.intent.control import Scope, apply_choice
from learnloop.scheduling import serving_exclusions
from learnloop.substrate.activities import open_administration, reserve_surface, resolve_legacy_item
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml
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


def _policy(vault, repository, clock, name):
    policy = policy_for(vault, repository, clock=clock, runtime=fake_runtime(), serve=True)
    assert (policy is DEFAULT_POLICY) == (name == "dl1_pair"), name
    return policy


def _plan(vault, repository, at, name, *, budget=15.0):
    clock = MovableClock(at)
    env = PlanEnv(vault=vault, repository=repository, clock=clock, policy=_policy(vault, repository, clock, name))
    return build_plan(env, kind="normal", budget=budget, remembered=int(budget), minutes_source="chip")


def _planned(record):
    return {item.practice_item_id for item in record.items()}


def _miss(record, commitment):
    rows = [row for row in record.split.get("checks_unplanned") or [] if row["commitment_id"] == commitment]
    assert len(rows) == 1, record.split.get("checks_unplanned")
    return rows[0]


def _keys(miss):
    return {(row["practice_item_id"], row["constraint_key"]) for row in miss["refused_candidates"]}


def _iv(tmp_path, name, extra=""):
    iv = make_intent_vault(tmp_path / "vault")
    append_config_toml(iv.root, POLICY_TOML[name] + extra)
    iv.reload()
    return iv


def _held_out(monkeypatch, items):
    found = frozenset(items)
    monkeypatch.setattr(exam_material, "held_out_items", lambda vault, repository: found)
    monkeypatch.setattr(serving_exclusions, "held_out_items", lambda vault, repository: found)


def _exam_reserved(monkeypatch, items):
    found = set(items)
    monkeypatch.setattr(exam_pool, "reserved_item_ids", lambda repository: set(found))
    monkeypatch.setattr(serving_exclusions, "reserved_item_ids", lambda repository: set(found))


# -- F18: held-out material is never a check, whatever held_out_selection says ---------------------


@pytest.mark.parametrize("name", POLICIES)
def test_f18_held_out_material_never_becomes_a_check_with_the_switch_off(tmp_path, monkeypatch, name):
    iv = _iv(tmp_path, name, "[goals]\nheld_out_selection = false\n")
    _held_out(monkeypatch, {"pi_c2", "pi_b1"})
    commitment = iv.choose("practice_item", "pi_c2", "check_once", NOW).commitment_id
    record = _plan(iv.vault, iv.repository, DUE_DAY, name)
    assert "pi_c2" not in _planned(record)
    miss = _miss(record, commitment)
    assert miss["reason"] == "refused_candidates"
    assert _keys(miss) == {("pi_c2", "held_out_material")}
    # The switch keeps governing ordinary serving exactly as before: the
    # uncommitted held-out item is still served with it off.
    assert "pi_b1" in iv.queue(DUE_DAY)


def test_f18_control_the_switch_on_still_withholds_ordinary_held_out_items(tmp_path, monkeypatch):
    iv = _iv(tmp_path, "dl1_pair")
    _held_out(monkeypatch, {"pi_b1"})
    assert "pi_b1" not in iv.queue(DUE_DAY)


# -- F19: the frame's mandatory constraints gate a check under DL1's pair too ------------------------


def _probe_iv(tmp_path, name):
    """``pi_c2`` a fresh-evidence surface (``practice_mode = "probe"``, one of
    the frame's single-use modes) that the scheduler's own gates admit: they
    key only on ``diagnostic_probe`` (its freshness reserve and attempted
    surface gate), so an exposure without an attempt is the frame's alone to
    see, as in the verify's reproduction."""

    iv = _iv(tmp_path, name)
    path = next(Path(iv.root).rglob("pi_c2.yaml"))
    payload = read_yaml(path)
    payload["practice_mode"] = "probe"
    write_yaml(path, payload)
    iv.reload()
    commitment = iv.choose("practice_item", "pi_c2", "check_once", NOW).commitment_id
    return iv, commitment


@pytest.mark.parametrize("name", POLICIES)
def test_f19_a_check_on_a_seen_probe_surface_is_refused_under_every_policy(tmp_path, name):
    """The verify's reproduction: the probe surface was rendered before
    without an attempt (an exact exposure in the one ledger)."""

    iv, commitment = _probe_iv(tmp_path, name)
    resolved = resolve_legacy_item(iv.vault, iv.repository, iv.vault.practice_items["pi_c2"], purpose="practice")
    open_administration(iv.repository, resolved=resolved)
    record = _plan(iv.vault, iv.repository, DUE_DAY, name)
    assert "pi_c2" not in {item.practice_item_id for item in record.items() if item.check_kind == "check_once"}
    miss = _miss(record, commitment)
    assert miss["reason"] == "refused_candidates"
    assert _keys(miss) == {("pi_c2", "hard_exposure_collision")}


@pytest.mark.parametrize("name", POLICIES)
def test_f19_control_an_unseen_probe_check_is_planned(tmp_path, name):
    iv, commitment = _probe_iv(tmp_path, name)
    record = _plan(iv.vault, iv.repository, DUE_DAY, name)
    assert commitment in {row["commitment_id"] for row in record.split.get("checks") or []}
    assert "pi_c2" in _planned(record)


def test_f19_dl1_pair_plans_are_otherwise_unchanged(tmp_path):
    """Nothing else changes under DL1's pair: the seen probe surface, when no
    check holds it, is planned as DL1 plans it (the frame gates checks only)."""

    iv = _iv(tmp_path, "dl1_pair")
    path = next(Path(iv.root).rglob("pi_c2.yaml"))
    payload = read_yaml(path)
    payload["practice_mode"] = "probe"
    write_yaml(path, payload)
    iv.reload()
    resolved = resolve_legacy_item(iv.vault, iv.repository, iv.vault.practice_items["pi_c2"], purpose="practice")
    open_administration(iv.repository, resolved=resolved)
    record = _plan(iv.vault, iv.repository, DUE_DAY, "dl1_pair", budget=40.0)
    assert "pi_c2" in _planned(record)


# -- F20: every due check is planned or recorded with its reasons -------------------------------------


@pytest.mark.parametrize("name", POLICIES)
@pytest.mark.parametrize("protection", ["exam_reserved", "held_out_switch_on"])
def test_f20_a_check_whose_only_candidate_the_admission_refuses_is_recorded(tmp_path, monkeypatch, name,
                                                                          protection):
    iv = _iv(tmp_path, name)
    if protection == "exam_reserved":
        _exam_reserved(monkeypatch, {"pi_c2"})
        key = "exam_pool"
    else:
        _held_out(monkeypatch, {"pi_c2"})
        key = "held_out_material"
    commitment = iv.choose("practice_item", "pi_c2", "check_once", NOW).commitment_id
    record = _plan(iv.vault, iv.repository, DUE_DAY, name)
    assert "pi_c2" not in _planned(record)
    miss = _miss(record, commitment)
    assert miss["reason"] == "refused_candidates"
    assert _keys(miss) == {("pi_c2", key)}


def _reserve(vault, repository, item_id):
    resolved = resolve_legacy_item(vault, repository, vault.practice_items[item_id], purpose="assessment")
    reserve_surface(repository, surface_id=resolved.surface_id, purpose="assessment")


@pytest.mark.parametrize("name", POLICIES)
def test_f20_a_check_with_a_reserved_and_a_held_candidate_is_recorded(tmp_path, name):
    """The verify's mixed case: one candidate reserved, the other waiting out
    a recent reveal's hold. Nothing serves; the record names both."""

    iv = _iv(tmp_path, name)
    commitment = iv.choose("learning_object", "lo_a", "check_once", NOW).commitment_id
    _reserve(iv.vault, iv.repository, "pi_a1")
    # A's answer shown two hours ago: the LO's cold delay holds B.
    iv.repository.insert_reveal_event(
        {"practice_item_id": "pi_a1", "learning_object_id": "lo_a", "source_kind": "tutor_answer",
         "amount": 1.0, "created_at": iso(DUE_DAY - timedelta(hours=2))}
    )
    record = _plan(iv.vault, iv.repository, DUE_DAY, name)
    assert not {"pi_a1", "pi_a2"} & {row["practice_item_id"] for row in record.split.get("checks") or []}
    miss = _miss(record, commitment)
    assert miss["reason"] == "candidates_held"
    assert miss["held_item_ids"] == ["pi_a2"]
    assert _keys(miss) == {("pi_a1", "assessment_reservation")}


# -- The contract: three policies, random protections ---------------------------------------------------

BUILDS = 4
RECORDED = {"plan_minutes_exhausted", "refused_candidates", "candidates_held", "not_in_pool"}


def _random_world(root, rng: random.Random, name: str, monkeypatch):
    target = [(f"pi_t{index}", float(rng.choice([1.0, 2.0, 3.0]))) for index in range(rng.randint(1, 3))]
    los = {"lo_t": target, "lo_f": [("pi_f0", 2.0), ("pi_f1", 2.0)]}
    paths = create_daily_plan_vault(root, learning_objects=los, version=INTENT_ALGORITHM_VERSION)
    switch_on = rng.random() < 0.5
    append_config_toml(paths.root, POLICY_TOML[name] + ("" if switch_on else "[goals]\nheld_out_selection = false\n"))
    vault = load_vault(paths.root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    reviewed = NOW - timedelta(days=10)
    for lo_id, items in los.items():
        for item_id, _minutes in items:
            record_attempt(repository, item_id, lo_id, reviewed)
            seed_due(repository, item_id, due=NOW - timedelta(days=rng.randint(0, 5)), last=reviewed)
        repository.upsert_mastery_state(
            MasteryState(
                learning_object_id=lo_id, logit_mean=0.0, logit_variance=1.0, evidence_count=1,
                last_evidence_at=iso(reviewed), algorithm_version=vault.config.algorithms.algorithm_version,
                updated_at=iso(reviewed),
            )
        )
    scope = (Scope("practice_item", rng.choice(target)[0]) if rng.random() < 0.5
             else Scope("learning_object", "lo_t"))
    commitment = apply_choice(vault, repository, scope, "check_once", clock=FrozenClock(NOW)).commitment_id
    items = [item_id for entries in los.values() for item_id, _ in entries]
    protected: dict[str, str] = {}
    held_out = {item_id for item_id in items if rng.random() < 0.2}
    exam = {item_id for item_id in items if rng.random() < 0.15}
    reserved = {item_id for item_id in items if rng.random() < 0.2}
    for item_id in sorted(reserved):
        _reserve(vault, repository, item_id)
    for item_id in items:
        if rng.random() < 0.2:
            # Rendered as ordinary practice before: an exposure collision for
            # a fresh-evidence surface; an ordinary item is unaffected.
            resolved = resolve_legacy_item(vault, repository, vault.practice_items[item_id], purpose="practice")
            open_administration(repository, resolved=resolved)
    for item_id in held_out:
        protected[item_id] = "held_out_material"
    for item_id in exam:
        protected.setdefault(item_id, "exam_pool")
    for item_id in reserved:
        protected.setdefault(item_id, "assessment_reservation")
    _held_out(monkeypatch, held_out)
    _exam_reserved(monkeypatch, exam)
    return vault, repository, commitment, {item_id for item_id, _ in target}, protected


@pytest.mark.parametrize("name", POLICIES)
@pytest.mark.parametrize("seed", range(8))
def test_contract_no_infeasible_item_is_planned_as_a_check_and_every_due_check_is_accounted_for(
    tmp_path, monkeypatch, seed, name
):
    rng = random.Random(f"{seed}:{name}")
    vault, repository, commitment, targets, protected = _random_world(tmp_path / "vault", rng, name, monkeypatch)
    for build in range(BUILDS):
        at = DUE_DAY + timedelta(days=build, hours=1)
        budget = float(rng.choice([1, 2, 4, 8, 15, 30]))
        record = _plan(vault, repository, at, name, budget=budget)
        as_checks = {item.practice_item_id for item in record.items() if item.check_kind == "check_once"}
        assert not as_checks & set(protected), (seed, name, build, sorted(as_checks & set(protected)))
        planned = {row["commitment_id"] for row in record.split.get("checks") or []}
        if commitment in planned:
            break
        miss = _miss(record, commitment)
        assert miss["reason"] in RECORDED, miss
        refused = {row["practice_item_id"]: row["constraint_key"] for row in miss["refused_candidates"]}
        # Every protected candidate of the check is named with its reason.
        for item_id in targets & set(protected):
            if item_id in refused:
                assert refused[item_id] == protected[item_id], (miss, protected)
        if miss["reason"] == "refused_candidates":
            assert refused, miss
