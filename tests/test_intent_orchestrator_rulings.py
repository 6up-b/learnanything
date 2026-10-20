"""Daily-loop DL2 fix round 3 (orchestrator rulings R1-R3 on the final verify,
Codex job 20261020-013947-7LLooy): the fail-first tests.

F11 (reopened): a never-attempted diagnostic_probe sibling was taken as a
"Check once"'s cold candidate, withheld the exposed ordinary candidate as
practice, and was then rejected by the scheduler's freshness gate: the queue
served neither. R1: one admission predicate
(``serving_exclusions.admission_reason``) for the build and the check.

F12 (new): a cold check answered through the frozen self-grade flow (the key
displayed unlinked, exempted at submit by its retry key and frozen trace)
was counted as exposure when the check read its attempt, and the check was
postponed seven days, again at every repetition. R2: one "disclosures
attributable to this attempt" function
(``serve_eligibility.attributable_disclosure_ids``).

The behaviour tests ran against ``32040fcbc`` (the verified commit) and
failed for the reasons the findings give; the controls passed (counts in
``docs/reviews/daily-loop-dl2-codex-review.md``). Fakes only; no model is
ever called.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.intent.checks import served_check, settle_answered_checks
from learnloop.scheduling import scheduler, serving_exclusions
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.daily_plan_fakes import iso
from tests.intent_fakes import ITEM_LO, NOW, make_intent_vault


def _tutor_reveal(repository, item_id, at):
    repository.insert_reveal_event(
        {
            "practice_item_id": item_id,
            "learning_object_id": ITEM_LO.get(item_id),
            "source_kind": "tutor_answer",
            "amount": 1.0,
            "created_at": iso(at),
        }
    )


def _as_diagnostic_probe(iv, item_id):
    path = next(iv.root.rglob(f"{item_id}.yaml"))
    payload = read_yaml(path)
    payload["practice_mode"] = "diagnostic_probe"
    write_yaml(path, payload)
    iv.reload()


@pytest.fixture
def probe_iv(tmp_path):
    """lo_a: ordinary ``pi_a1`` (reviewed) and an active, never-attempted
    ``diagnostic_probe`` ``pi_a2`` with no open probe episode."""

    iv = make_intent_vault(tmp_path / "vault", unattempted=("pi_a2",))
    _as_diagnostic_probe(iv, "pi_a2")
    return iv


def _exposed_a1_check(iv):
    commitment = iv.choose("learning_object", "lo_a", "check_once", NOW).commitment_id
    due_day = NOW + timedelta(days=8)
    # Standing tutor exposure on A, two days back (past the LO's one-day
    # hold, so it alone decides A: practice).
    _tutor_reveal(iv.repository, "pi_a1", due_day - timedelta(days=2))
    return commitment, due_day


# -- F11 (reopened) / R1: one admission predicate ------------------------------------------------


def test_f11_a_fresh_diagnostic_probe_never_suppresses_the_servable_candidate(probe_iv):
    """The verify reproduction as written: B passes the routine gate, is
    eligible cold, and the freshness reserve rejects it; A must be served."""

    iv = probe_iv
    _commitment, due_day = _exposed_a1_check(iv)
    queue = iv.queue(due_day)
    assert "pi_a2" not in queue, "the freshness reserve still keeps a diagnostic surface out"
    assert "pi_a1" in queue
    serving = iv.serving(due_day)
    assert serving.withhold_reason("pi_a1") is None
    (check,) = serving.checks.values()
    assert (check.eligible, check.exposed) == ((), ("pi_a1",))
    # The practice view agrees (its own admission over the same predicate).
    assert served_check(iv.vault, iv.repository, "pi_a1", now=due_day)["cold"] is False


def test_f11_the_plan_pool_offers_the_admitted_candidate(probe_iv):
    """The plan reads its own intent view: its check split admits the same
    candidates as the queue's."""

    iv = probe_iv
    _commitment, due_day = _exposed_a1_check(iv)
    serving = iv.serving(due_day)
    assert list(serving.check_item_ids(["pi_a1", "pi_a2"])) == ["pi_a1"]
    assert "pi_a1" in iv.requested(due_day) and "pi_a2" not in iv.requested(due_day)


def test_f11_an_admitted_cold_sibling_is_still_preferred(tmp_path):
    """Control: an ordinary cold sibling the build admits still takes the check."""

    iv = make_intent_vault(tmp_path / "vault")
    _commitment, due_day = _exposed_a1_check(iv)
    assert [item for item in iv.queue(due_day) if item in ("pi_a1", "pi_a2")] == ["pi_a2"]
    assert iv.serving(due_day).withhold_reason("pi_a1") == "intent_check_held"


def _withheld_reasons(function) -> tuple[set[str], int]:
    """Every literal reason ``function`` passes to ``withheld(...)``, and the
    number of calls whose reason is not a literal."""

    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    literals: set[str] = set()
    computed = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "withheld":
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                literals.add(first.value)
            else:
                computed += 1
    return literals, computed


def test_r1_every_gate_of_the_build_is_the_admission_predicates():
    """No gate only in the scheduler: the build's candidate loop withholds an
    item only for a reason ``admission_reason`` gives (one computed call),
    plus ``zero_priority`` (ranking: a request, which every check candidate
    is, carries the requested floor, so it never meets it)."""

    literals, computed = _withheld_reasons(scheduler.build_due_queue)
    assert literals == {"zero_priority"}
    assert computed == 1
    assert scheduler._REQUESTED_PRIORITY_FLOOR > 0
    source = inspect.getsource(scheduler.build_due_queue)
    assert source.count("admission_reason(") == 1
    assert "routine_withhold_reason(" not in source
    assert "diagnostic_freshness_reserve" not in source
    # Every gate the predicate gives is one of the build's own reason codes.
    gates_source = inspect.getsource(scheduler._BuildAdmission) + inspect.getsource(
        serving_exclusions.routine_withhold_reason
    )
    for reason in serving_exclusions.ADMISSION_GATES:
        assert f'"{reason}"' in gates_source, reason
    assert len(set(serving_exclusions.ADMISSION_GATES)) == len(serving_exclusions.ADMISSION_GATES)


def test_r1_check_selection_asks_the_builds_admission_predicate(probe_iv, monkeypatch):
    """The check's candidate selection consults the same function the
    candidate loop does, for each candidate, as a request."""

    iv = probe_iv
    _commitment, due_day = _exposed_a1_check(iv)
    calls: list[tuple[str, bool, bool]] = []
    real = scheduler.admission_reason

    def spy(vault, item, state, exclusions, gates, *, requested, intent_gate=None):
        calls.append((item.id, requested, intent_gate is not None))
        return real(vault, item, state, exclusions, gates, requested=requested, intent_gate=intent_gate)

    monkeypatch.setattr(scheduler, "admission_reason", spy)
    iv.queue(due_day)
    check_calls = {(item_id, requested) for item_id, requested, from_loop in calls if not from_loop}
    loop_calls = {item_id for item_id, _requested, from_loop in calls if from_loop}
    assert check_calls == {("pi_a1", True), ("pi_a2", True)}
    assert {"pi_a1", "pi_a2"} <= loop_calls
    # The views built outside the queue ask it too.
    calls.clear()
    assert iv.serving(due_day).withhold_reason("pi_a1") is None
    assert {(item_id, requested) for item_id, requested, _loop in calls} == {("pi_a1", True), ("pi_a2", True)}


def test_r1_the_predicate_names_the_freshness_reserve_for_a_check_candidate(probe_iv):
    iv = probe_iv
    _commitment, due_day = _exposed_a1_check(iv)
    view = iv.serving(due_day)
    admitted = scheduler.check_admission(iv.vault, iv.repository, now=due_day, intent_view=view)
    assert admitted("pi_a1") is True
    assert admitted("pi_a2") is False


# -- F12 / R2: one "disclosures attributable to this attempt" function ------------------------------


@pytest.fixture
def side(tmp_path):
    """An intent vault behind the sidecar (the frozen self-grade flow is the
    desktop's): the check is chosen eight days before the real clock, so it
    is due when the sidecar submits."""

    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    iv = make_intent_vault(tmp_path / "vault")
    context = SidecarContext()
    context.load(iv.root)
    # Never a real grading provider: "manual" is a never-ready runtime.
    context.grading_provider_override = "manual"
    return iv, context


def _call(context, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(context, spec.params_model.model_validate(params))


def _self_grade_flow(context, session_id, item_id, submission_id, *, answer="my own answer"):
    """Freeze the trace, display the key (unlinked), submit unchanged, acknowledge."""

    _call(context, "save_practice_draft", {
        "sessionId": session_id, "practiceItemId": item_id, "answerMd": answer, "submissionId": submission_id,
    })
    _call(context, "record_self_grade_disclosure", {
        "sessionId": session_id, "practiceItemId": item_id, "submissionId": submission_id, "answerMd": answer,
    })
    _call(context, "record_self_grade_disclosure", {
        "sessionId": session_id, "practiceItemId": item_id, "submissionId": submission_id, "answerMd": answer,
        "displayId": f"display_{submission_id}",
    })
    result = _call(context, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": item_id, "answerMd": answer,
        "attemptType": "independent_attempt", "submissionId": submission_id,
        "selfGrade": {"criterionPoints": {"correctness": 4}, "confidence": 3},
    })
    _call(context, "acknowledge_practice_submission", {
        "sessionId": session_id, "practiceItemId": item_id, "submissionId": submission_id,
    })
    return result["attemptId"]


def _real_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _check_once(iv, lo_id, at):
    return iv.choose("learning_object", lo_id, "check_once", at).commitment_id


def test_f12_a_frozen_self_grade_answers_the_check(side):
    """The verify reproduction as written: submit admits the attempt unprimed
    with a zero reveal total, and the check is answered, not postponed."""

    iv, context = side
    commitment = _check_once(iv, "lo_a", _real_now() - timedelta(days=8))
    session_id = _call(context, "start_session", {"availableMinutes": 20})["sessionId"]
    attempt_id = _self_grade_flow(context, session_id, "pi_a1", "sub_check")

    attempt = iv.repository.fetch_practice_attempt(attempt_id)
    assert not attempt["primed"]
    displays = [row for row in iv.repository.reveal_events(practice_item_id="pi_a1") if row["attempt_id"] is None]
    assert displays, "sanity: the key's display row is unlinked"

    later = FrozenClock(_real_now() + timedelta(minutes=1))
    assert settle_answered_checks(iv.vault, iv.repository, clock=later) == [commitment]
    assert C.resolve_disposition(iv.repository, commitment) == "satisfied"


def test_f12_a_repeated_self_grade_never_postpones(side):
    """A second "Check once" answered the same way is answered too (the
    verify saw every repetition postpone)."""

    iv, context = side
    start = _real_now() - timedelta(days=8)
    first = _check_once(iv, "lo_a", start)
    session_id = _call(context, "start_session", {"availableMinutes": 20})["sessionId"]
    _self_grade_flow(context, session_id, "pi_a1", "sub_first")
    assert settle_answered_checks(iv.vault, iv.repository, clock=FrozenClock(_real_now() + timedelta(minutes=1))) == [first]

    second = _check_once(iv, "lo_b", start)
    _self_grade_flow(context, session_id, "pi_b1", "sub_second")
    assert settle_answered_checks(iv.vault, iv.repository, clock=FrozenClock(_real_now() + timedelta(minutes=2))) == [second]
    assert C.resolve_disposition(iv.repository, second) == "satisfied"


def test_f12_an_unrelated_disclosure_still_holds(side):
    """Control: a sibling's self-grade key shown just before still holds the
    learning object; the attempt is practice and the check waits again."""

    iv, context = side
    commitment = _check_once(iv, "lo_a", _real_now() - timedelta(days=8))
    session_id = _call(context, "start_session", {"availableMinutes": 20})["sessionId"]
    # B's own frozen self-grade, displayed: B's, not A's.
    _self_grade_flow(context, session_id, "pi_a2", "sub_sibling")
    _self_grade_flow(context, session_id, "pi_a1", "sub_after")

    later = FrozenClock(_real_now() + timedelta(minutes=1))
    assert C.resolve_disposition(iv.repository, commitment) == "one_check_pending"
    settled = settle_answered_checks(iv.vault, iv.repository, clock=later)
    assert commitment not in settled
    (check,) = iv.serving(_real_now() + timedelta(minutes=1)).checks.values()
    assert check.answered_by is None and check.date_source == "after_practice"


def test_r2_one_attributable_disclosure_function(side):
    """Submit and the check read the same function: the rows submit exempts
    for the draft are exactly those the check exempts for its attempt."""

    from learnloop import serve_eligibility as se
    from learnloop.attempts import attempts as attempts_module
    from learnloop.attempts.trace_evidence import compose_learner_trace

    iv, context = side
    session_id = _call(context, "start_session", {"availableMinutes": 20})["sessionId"]
    attempt_id = _self_grade_flow(context, session_id, "pi_a1", "sub_same")
    rows = iv.repository.reveal_events_for_target(practice_item_id="pi_a1", learning_object_id="lo_a")
    trace = compose_learner_trace("my own answer", None)
    draft = se.attributable_disclosure_ids(
        rows, practice_item_id="pi_a1", submission_id="sub_same", learner_answer_md=trace
    )
    key, stored = se.attempt_submission(iv.repository, attempt_id, "pi_a1")
    assert (key, stored) == ("sub_same", trace)
    assert draft and draft == se.attributable_disclosure_ids(
        rows, practice_item_id="pi_a1", submission_id=key, learner_answer_md=stored
    )
    submit_inputs = attempts_module.submit_eligibility_inputs(
        iv.repository, "pi_a1", at=iso(_real_now()), submission_id="sub_same", learner_answer_md=trace
    )
    assert submit_inputs.exempt_reveal_ids == draft
    # Another draft's identity exempts nothing.
    assert not se.attributable_disclosure_ids(
        rows, practice_item_id="pi_a1", submission_id="sub_other", learner_answer_md=trace
    )
