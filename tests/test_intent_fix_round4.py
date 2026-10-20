"""Daily-loop DL2 fix round 4 (orchestrator rulings on the verify of
``8e0ca1875``, Codex job 20261020-021715-9JeVsu): the fail-first tests.

F13 (High): an assisted reconstruction (``reconstruction_after_walkthrough``,
unprimed, no hints) satisfied a "Check once". R1: ``on_your_own`` is the
activity policy's canonical assistance classification.

F14 (Medium): teach-back composition (and ``pick_checks`` before it) could
drop a due check on every build. R2: a due check survives composition and is
planned within the plan's minutes; the only non-serve is minutes exhausted,
recorded (the contract test builds plans at advancing clocks over randomized
vaults).

F15 (Medium): a check that also carries a stricter measurement duty (a cold
follow-up, an active diagnostic) promised help the duty then refused. R3: it
is served under that duty, with a banner chosen server-side that promises no
help; an on-your-own completion satisfies both.

The behaviour tests ran against ``8e0ca1875`` and failed for the reasons the
findings give; the controls passed (counts in
``docs/reviews/daily-loop-dl2-codex-review.md``). Fakes only; no model is
ever called.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import INTENT_ALGORITHM_VERSION
from learnloop.attempt_types import SUPPORTED_ATTEMPT_TYPES
from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.daily_plan.engine import PlanEnv, build_plan
from learnloop.db.repositories import MasteryState, Repository
from learnloop.diagnosis.causal_activity_policy import attempt_counts_as_assisted
from learnloop.intent.checks import served_check, settle_answered_checks
from learnloop.intent.control import Scope, apply_choice
from learnloop.scheduling import scheduler
from learnloop.scheduling.intent.serving import on_your_own
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.daily_plan_fakes import MovableClock, iso, record_attempt, seed_due
from tests.helpers import create_daily_plan_vault
from tests.intent_fakes import ITEM_LO, NOW, make_intent_vault

#: The activity policy's legacy assistance channels (never a check on your own).
ASSISTED_TYPES = {"hinted_attempt", "guided_walkthrough", "reconstruction_after_walkthrough"}


# -- F13 / R1: the canonical assistance classification -------------------------------------------


@pytest.mark.parametrize("attempt_type", SUPPORTED_ATTEMPT_TYPES)
@pytest.mark.parametrize("signals", ["plain", "primed", "hinted"])
def test_f13_on_your_own_is_the_activity_policys_classification(attempt_type, signals):
    """Every activity class: only an unassisted, unprimed attempt with no
    hints answers a check, exactly as the activity policy classifies it."""

    row = {
        "attempt_type": attempt_type,
        "primed": 1 if signals == "primed" else 0,
        "hints_used": 1 if signals == "hinted" else 0,
    }
    expected = signals == "plain" and attempt_type not in ASSISTED_TYPES
    assert on_your_own(row) is expected
    assert on_your_own(row) is not attempt_counts_as_assisted(
        attempt_type=attempt_type, primed=bool(row["primed"]), hints_used=row["hints_used"]
    )


@pytest.mark.parametrize(
    "contamination",
    [
        ("diagnostic_probe", 0, 0, True),  # pure_diagnostic
        ("diagnostic_probe", 0, 1, False),  # instructional_diagnostic
        ("independent_attempt", 1, 0, False),  # repair_activity
        ("independent_attempt", 0, 0, True),  # verification
    ],
    ids=["pure_diagnostic", "instructional_diagnostic", "repair_activity", "verification"],
)
def test_f13_every_contamination_class(contamination):
    attempt_type, primed, hints, expected = contamination
    assert on_your_own({"attempt_type": attempt_type, "primed": primed, "hints_used": hints}) is expected


def _attempt_of_type(repository, item_id, at, attempt_type):
    attempt_id = f"att_{attempt_type}_{int(at.timestamp())}"
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, "
            "attempt_type, latency_seconds, created_at, primed, hints_used) "
            "VALUES (?, ?, ?, 'short_answer', ?, 120, ?, 0, 0)",
            (attempt_id, item_id, ITEM_LO[item_id], attempt_type, iso(at)),
        )
        connection.commit()
    return attempt_id


def test_f13_an_assisted_reconstruction_leaves_the_check_pending_and_dates_it_again(tmp_path):
    """The verify reproduction: an unprimed, hint-free reconstruction after a
    walkthrough is practice: the check stays pending, dated again."""

    iv = make_intent_vault(tmp_path / "vault")
    commitment = iv.choose("practice_item", "pi_b1", "check_once", NOW).commitment_id
    attempt_at = NOW + timedelta(days=8, minutes=5)
    _attempt_of_type(iv.repository, "pi_b1", attempt_at, "reconstruction_after_walkthrough")
    later = FrozenClock(attempt_at + timedelta(minutes=1))
    assert settle_answered_checks(iv.vault, iv.repository, clock=later) == []
    assert C.resolve_disposition(iv.repository, commitment) == "one_check_pending"
    (check,) = iv.serving(attempt_at + timedelta(minutes=1)).checks.values()
    assert check.answered_by is None and check.date_source == "after_practice"
    assert check.date == attempt_at + timedelta(days=7)


def test_f13_an_independent_attempt_still_answers(tmp_path):
    """Control."""

    iv = make_intent_vault(tmp_path / "vault")
    commitment = iv.choose("practice_item", "pi_b1", "check_once", NOW).commitment_id
    attempt_at = NOW + timedelta(days=8, minutes=5)
    _attempt_of_type(iv.repository, "pi_b1", attempt_at, "independent_attempt")
    later = FrozenClock(attempt_at + timedelta(minutes=1))
    assert settle_answered_checks(iv.vault, iv.repository, clock=later) == [commitment]


# -- F14 / R2: a due check survives composition and is planned within the minutes ------------------


def _as_teach_back(root, item_id):
    path = next(root.rglob(f"{item_id}.yaml"))
    payload = read_yaml(path)
    payload["practice_mode"] = "teach_back"
    payload["attempt_types_allowed"] = ["teach_back"]
    write_yaml(path, payload)


def _never_worth_its_minutes(monkeypatch):
    """Every teach-back's value of information below its minutes (the
    verify's 12.95 value-minutes against 15 cost-minutes, on every build)."""

    monkeypatch.setattr(scheduler, "_teach_back_value_admission", lambda *args, **kwargs: (frozenset(), []))


def test_f14_an_item_check_on_a_teach_back_survives_composition(tmp_path, monkeypatch):
    iv = make_intent_vault(tmp_path / "vault")
    _as_teach_back(iv.root, "pi_b1")
    iv.reload()
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    _never_worth_its_minutes(monkeypatch)
    for day in (8, 9, 10):
        assert "pi_b1" in iv.queue(NOW + timedelta(days=day)), day


def test_f14_an_lo_check_whose_cold_candidate_is_a_teach_back_is_served(tmp_path, monkeypatch):
    """pick_checks takes the cold teach-back and drops the exposed sibling;
    composition must not then drop the teach-back."""

    iv = make_intent_vault(tmp_path / "vault")
    _as_teach_back(iv.root, "pi_a2")
    iv.reload()
    iv.choose("learning_object", "lo_a", "check_once", NOW)
    due_day = NOW + timedelta(days=8)
    iv.repository.insert_reveal_event(
        {"practice_item_id": "pi_a1", "learning_object_id": "lo_a", "source_kind": "tutor_answer",
         "amount": 1.0, "created_at": iso(due_day - timedelta(days=2))}
    )
    _never_worth_its_minutes(monkeypatch)
    lo_a = [item for item in iv.queue(due_day) if item in ("pi_a1", "pi_a2")]
    assert lo_a == ["pi_a2"]


def test_f14_the_teach_back_count_cap_never_drops_a_check(tmp_path, monkeypatch):
    """Below the value rule (the count cap), a check is never the one cut."""

    iv = make_intent_vault(tmp_path / "vault")
    for item_id in ("pi_b1", "pi_c1", "pi_c2"):
        _as_teach_back(iv.root, item_id)
    iv.reload()
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    monkeypatch.setattr(scheduler, "_teach_back_value_admission", lambda *args, **kwargs: (None, []))
    capped = scheduler._enforce_teach_back_session_cap
    monkeypatch.setattr(
        scheduler, "_enforce_teach_back_session_cap",
        lambda queue, cap, **kwargs: capped(queue, 0, **kwargs),
    )
    assert "pi_b1" in iv.queue(NOW + timedelta(days=8))


def _env(iv, at, session_id=None):
    return PlanEnv(vault=iv.vault, repository=iv.repository, clock=MovableClock(at), session_id=session_id)


def test_f14_a_due_check_is_planned_first_within_the_minutes(tmp_path):
    """Due reviews fill the maintain lane's share; the check is still planned."""

    iv = make_intent_vault(tmp_path / "vault")
    iv.choose("practice_item", "pi_c2", "check_once", NOW)
    record = build_plan(_env(iv, NOW + timedelta(days=8)), kind="normal", budget=5.0, remembered=5, minutes_source="chip")
    assert "pi_c2" in {item.practice_item_id for item in record.items()}
    (row,) = record.split["checks"]
    assert row["practice_item_id"] == "pi_c2"
    # A scheduled check in the maintain lane, not a request (§5.2, §6.1).
    assert record.split["requested"] == []
    (planned,) = [item for item in record.items() if item.practice_item_id == "pi_c2"]
    assert planned.lane == "maintain" and planned.check_kind == "check_once"


def test_f14_a_check_the_minutes_cannot_hold_is_recorded_not_silent(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    iv.choose("practice_item", "pi_c2", "check_once", NOW)
    record = build_plan(_env(iv, NOW + timedelta(days=8)), kind="normal", budget=1.0, remembered=1, minutes_source="chip")
    assert "pi_c2" not in {item.practice_item_id for item in record.items()}
    (miss,) = record.split["checks_unplanned"]
    assert miss["practice_item_id"] == "pi_c2" and miss["reason"] == "plan_minutes_exhausted"


# -- F14 contract: randomized vaults, plans at advancing clocks --------------------------------------

BUILDS = 6


def _random_vault(root, rng: random.Random):
    target = [(f"pi_t{index}", float(rng.choice([1.0, 2.0, 3.0, 6.0]))) for index in range(rng.randint(1, 3))]
    los = {"lo_t": target}
    for lo_index in range(rng.randint(1, 4)):
        los[f"lo_f{lo_index}"] = [
            (f"pi_f{lo_index}_{index}", float(rng.choice([1.0, 2.0, 4.0]))) for index in range(rng.randint(1, 3))
        ]
    paths = create_daily_plan_vault(root, learning_objects=los, version=INTENT_ALGORITHM_VERSION)
    teach_backs = [item_id for item_id, _ in target if rng.random() < 0.4]
    for item_id in teach_backs:
        _as_teach_back(paths.root, item_id)
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
    if rng.random() < 0.5:
        scope = Scope("practice_item", rng.choice(target)[0])
    else:
        scope = Scope("learning_object", "lo_t")
    commitment = apply_choice(vault, repository, scope, "check_once", clock=FrozenClock(NOW)).commitment_id
    due_day = NOW + timedelta(days=8)
    for item_id, _minutes in target:
        roll = rng.random()
        if roll < 0.25:
            # Standing exposure: the item is practice (still the check's to serve).
            at = due_day - timedelta(days=2)
        elif roll < 0.4:
            # A recent reveal: the LO waits one cold delay.
            at = due_day - timedelta(hours=2)
        else:
            continue
        repository.insert_reveal_event(
            {"practice_item_id": item_id, "learning_object_id": "lo_t", "source_kind": "tutor_answer",
             "amount": 1.0, "created_at": iso(at)}
        )
    return vault, repository, commitment, {item_id for item_id, _ in target}


@pytest.mark.parametrize("seed", range(16))
def test_f14_contract_a_due_check_is_planned_within_n_builds_or_every_miss_says_minutes(tmp_path, seed, monkeypatch):
    """R2's contract: over randomized vaults (item or LO checks, teach-backs
    never worth their minutes, standing and recent exposure, due reviews
    competing for the maintain share) and plans built at advancing clocks
    with random budgets, the commitment's item is planned within
    ``BUILDS`` builds, or every build that missed it recorded that the
    plan's minutes were exhausted."""

    rng = random.Random(seed)
    vault, repository, commitment, targets = _random_vault(tmp_path / "vault", rng)
    _never_worth_its_minutes(monkeypatch)
    misses: list[tuple[int, list]] = []
    served = False
    for build in range(BUILDS):
        at = NOW + timedelta(days=8 + build, hours=1)
        env = PlanEnv(vault=vault, repository=repository, clock=MovableClock(at))
        budget = float(rng.choice([1, 2, 4, 8, 15, 30]))
        record = build_plan(env, kind="normal", budget=budget, remembered=int(budget), minutes_source="chip")
        planned = {item.practice_item_id for item in record.items()} & targets
        if planned:
            served = True
            break
        misses.append((build, list(record.split.get("checks_unplanned") or [])))
    if served:
        return
    for build, unplanned in misses:
        reasons = {row["reason"] for row in unplanned if row.get("commitment_id") == commitment}
        assert reasons == {"plan_minutes_exhausted"}, (seed, build, unplanned)


# -- F15 / R3: a check under a stricter measurement duty -------------------------------------------------

MEASURED = "measured on your own"


def _cold_retry(repository, item_id, at):
    return repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref=f"ep_{item_id}",
        context={"kind": "causal_cold_verification", "source_attempt_id": "att_src"},
        not_before=iso(at - timedelta(hours=1)), selected_item_id=item_id,
        expires_at=iso(at + timedelta(days=5)), clock=FrozenClock(at - timedelta(hours=2)),
    )


def test_f15_a_check_with_a_cold_follow_up_is_served_under_that_duty(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    due_day = NOW + timedelta(days=8)
    _cold_retry(iv.repository, "pi_b1", due_day)
    view = served_check(iv.vault, iv.repository, "pi_b1", now=due_day)
    assert view["duty"] == "cold_followup"
    assert MEASURED in view["banner"] and "Help is still here" not in view["banner"]
    assert "help_header" not in view
    assert view["locators_hidden"] is True


def test_f15_a_check_under_an_active_diagnostic_is_served_under_that_duty(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    view = served_check(iv.vault, iv.repository, "pi_b1", now=NOW + timedelta(days=8), duty="diagnostic")
    assert view["duty"] == "diagnostic"
    assert MEASURED in view["banner"] and "help_header" not in view


def test_f15_a_seen_check_with_a_cold_follow_up_stays_practice(tmp_path):
    """Control: a check whose answer was seen is practice (F3) whatever else
    the item carries; the measured banner would claim a check it cannot be."""

    iv = make_intent_vault(tmp_path / "vault")
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    due_day = NOW + timedelta(days=8)
    iv.repository.insert_reveal_event(
        {"practice_item_id": "pi_b1", "learning_object_id": ITEM_LO["pi_b1"], "source_kind": "tutor_answer",
         "amount": 1.0, "created_at": iso(due_day - timedelta(days=2))}
    )
    _cold_retry(iv.repository, "pi_b1", due_day)
    view = served_check(iv.vault, iv.repository, "pi_b1", now=due_day)
    assert view["cold"] is False and view.get("duty") is None
    assert MEASURED not in view["banner"] and "practice" in view["banner"].lower()


def test_f15_an_ordinary_check_still_offers_help(tmp_path):
    """Control: no other duty, the D42 banner and ladder header."""

    iv = make_intent_vault(tmp_path / "vault")
    iv.choose("practice_item", "pi_b1", "check_once", NOW)
    view = served_check(iv.vault, iv.repository, "pi_b1", now=NOW + timedelta(days=8))
    assert view["help_header"] and "Help is still here" in view["banner"]
    assert view.get("duty") is None


@pytest.fixture
def side(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    iv = make_intent_vault(tmp_path / "vault")
    context = SidecarContext()
    context.load(iv.root)
    context.grading_provider_override = "manual"
    return iv, context


def _call(context, name, params):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(context, spec.params_model.model_validate(params))


def _real_now():
    return datetime.now(UTC).replace(microsecond=0)


def test_f15_the_serve_chooses_the_variant_server_side_and_one_completion_satisfies_both(side):
    """The practice item's serve carries the measured banner (no help header)
    when the item has a due cold follow-up; an on-your-own answer completes
    the cold retry and answers the check."""

    iv, context = side
    commitment = iv.choose("practice_item", "pi_b1", "check_once", _real_now() - timedelta(days=8)).commitment_id
    task = _cold_retry(iv.repository, "pi_b1", _real_now())
    session_id = _call(context, "start_session", {"availableMinutes": 20})["sessionId"]
    detail = _call(context, "get_practice_item", {"practiceItemId": "pi_b1", "sessionId": session_id})
    check = detail["intentCheck"]
    assert check["duty"] == "cold_followup" and MEASURED in check["banner"]
    assert "helpHeader" not in check
    assert detail["activeFollowupKind"] == "cold_retry"

    _call(context, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": "pi_b1", "answerMd": "my answer",
        "attemptType": "independent_attempt", "submissionId": "sub_both",
        "selfGrade": {"criterionPoints": {"correctness": 4}, "confidence": 3},
    })
    later = FrozenClock(_real_now() + timedelta(minutes=1))
    assert settle_answered_checks(iv.vault, iv.repository, clock=later) == [commitment]
    with iv.repository.connection() as connection:
        status = connection.execute("SELECT status FROM followup_tasks WHERE id = ?", (task["id"],)).fetchone()[0]
    assert status not in ("pending", "served")


def test_f15_the_probe_contract_carries_the_diagnostic_variant(tmp_path, monkeypatch):
    """An active diagnostic presentation of a due check's item: the contract
    (the server's word that the item is a probe) carries the measured check."""

    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop.diagnosis.probe_episodes import enter_episode
    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.handlers import practice as practice_handlers
    from tests.helpers import admit_probe_instrument_card, create_placement_vault

    # Placement off: its opening episodes are ignored for serving.
    paths = create_placement_vault(
        tmp_path / "vault", version=INTENT_ALGORITHM_VERSION, placement_toml="[placement]\nenabled = false\n"
    )
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository)
    loaded = load_vault(paths.root)
    sync_vault_state(loaded, repository)
    item_id = "pi_svd_define_001"
    apply_choice(loaded, repository, Scope("practice_item", item_id), "check_once",
                 clock=FrozenClock(_real_now() - timedelta(days=8)))
    episode = enter_episode(loaded, repository, "lo_svd_definition")
    assert episode.status == "in_progress"
    monkeypatch.setattr(
        practice_handlers, "ready_grading_provider",
        lambda _vault, override=None: ("test", SimpleNamespace(ready=True), object()),
    )
    context = SidecarContext()
    context.load(paths.root)
    contract = _call(context, "get_probe_contract", {"practiceItemId": item_id, "sessionId": "probe_session"})
    assert contract["active"] is True
    check = contract["intentCheck"]
    assert check["duty"] == "diagnostic" and MEASURED in check["banner"] and "helpHeader" not in check


def test_f15_a_pure_diagnostic_answer_satisfies_the_check(tmp_path):
    """A probe administration on your own (``diagnostic_probe``, no hints,
    unprimed: the policy's pure diagnostic) answers the check too."""

    iv = make_intent_vault(tmp_path / "vault")
    commitment = iv.choose("practice_item", "pi_b1", "check_once", NOW).commitment_id
    attempt_at = NOW + timedelta(days=8, minutes=5)
    _attempt_of_type(iv.repository, "pi_b1", attempt_at, "diagnostic_probe")
    later = FrozenClock(attempt_at + timedelta(minutes=1))
    assert settle_answered_checks(iv.vault, iv.repository, clock=later) == [commitment]
