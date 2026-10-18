"""Adaptive hints H2a: evidence, with no new rules (spec_adaptive_hints_v1 §5, §10.1; G-H2, G-H3).

Through the real sidecar submit path (self-graded, no provider): each shown
hint at levels 1-3 adds one to the attempt's ``hints_used``; a shown hint at
level 4-5 sets ``primed`` and adds nothing; a key overlap writes a
``reveal_events`` ``tutor_answer`` row with basis ``hint:<kind>:L<level>``;
``submit_dont_know`` folds them too; ``max_useful_hints`` clamps the total;
authored reveals stay client-counted, so nothing counts twice; a cancelled,
withheld or never-delivered hint counts nothing; a discriminating answer
changes nothing; an earlier submission's rows never reach a later attempt.
``resolve_attempt_activity_policy`` gives the existing eligibility (the
reviewer's §10.1 confirmation). Fakes only.
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import closing

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.diagnosis.causal_activity_policy import resolve_attempt_activity_policy
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, assists, hint_vault, prefer, reveals, store_map

ARGMAX = '[hints]\nchoice_policy = "argmax"\n'
SELF_GRADE = {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3}


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _sidecar(tmp_path, *, config: str = "", cap: int | None = None, inline: bool = True, **item):
    paths = hint_vault(tmp_path, config=ARGMAX + config, **item)
    store_map(paths)
    if cap is not None:
        item_path = paths.practice_item_path("linear-algebra", ITEM)
        data = read_yaml(item_path)
        data["hint_policy"] = {"max_useful_hints": cap}
        write_yaml(item_path, data)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = inline
    ctx.hint_seed = "e"
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def _hint(ctx, session, option: str, *, key: str = "k1", writer=None, **params):
    ctx.hint_writer_client = writer or WriterFake()
    ctx.hint_chooser_client = ChooserFake(prefer(option, 0.9))
    payload = {"sessionId": session, "practiceItemId": ITEM, "submissionId": key, "answerMd": WORK, **params}
    return _call(ctx, "practice.request_hint", payload)


def _submit(ctx, session, *, key: str = "k1", hints: int = 0, attempt_type: str = "independent_attempt"):
    return _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": attempt_type,
        "hintsUsed": hints, "selfGrade": SELF_GRADE, "submissionId": key})


def _attempt(paths, attempt_id: str) -> dict:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def test_levels_one_to_three_add_one_each_and_attach_to_the_attempt(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    for option in ("approach_question@L1", "localize@L2", "next_step@L3"):
        job = _hint(ctx, session, option)
        assert job["result"]["status"] == "ready" and job["result"]["shown"] is True
    result = _submit(ctx, session)
    attempt = _attempt(paths, result["attemptId"])
    assert attempt["hints_used"] == 3
    # Each shown hint's key overlap is a reveal, so auto-prime's existing sum
    # applies to hints as to tutor answers (§5); nothing else sets primed here.
    from learnloop.attempts.attempts import AUTO_PRIME_REVEAL_THRESHOLD

    total = sum(reveal["amount"] for reveal in reveals(paths.sqlite_path))
    assert bool(attempt["primed"]) is (total >= AUTO_PRIME_REVEAL_THRESHOLD)
    assert {row["attempt_id"] for row in assists(paths.sqlite_path)} == {result["attemptId"]}
    policy = resolve_attempt_activity_policy(attempt_type=attempt["attempt_type"], primed=bool(attempt["primed"]),
                                             hints_used=attempt["hints_used"])
    # Assisted: no certification credit; a hinted practice review still
    # schedules unless the reveals' sum primed it (then a repair activity).
    assert policy.counts_as_assisted and not policy.eligible_for_certification
    assert policy.eligible_for_fsrs is (not attempt["primed"])
    assert policy.contamination_class == ("repair_activity" if attempt["primed"] else "verification")
    plain = resolve_attempt_activity_policy(attempt_type="independent_attempt", primed=False, hints_used=3)
    assert plain.counts_as_assisted and plain.eligible_for_fsrs and not plain.eligible_for_certification


@pytest.mark.parametrize("level, option", [(4, "worked_chunk@L4"), (5, "walkthrough@L5")])
def test_worked_help_sets_primed_and_adds_no_count(tmp_path, level, option):
    paths, ctx, session = _sidecar(tmp_path)
    job = _hint(ctx, session, option, takenLevel=level)
    assert job["result"]["level"] == level and job["result"]["evidence"] == {
        "countsAsHint": False, "primed": True, "level": level}
    attempt = _attempt(paths, _submit(ctx, session)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (0, 1)
    policy = resolve_attempt_activity_policy(attempt_type=attempt["attempt_type"], primed=True, hints_used=0)
    assert policy.contamination_class == "repair_activity"
    assert not policy.eligible_for_fsrs and not policy.eligible_for_certification and policy.counts_as_assisted


def test_a_key_overlap_writes_a_tutor_answer_reveal_with_the_hint_basis(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "walkthrough@L5", takenLevel=5)
    [reveal] = reveals(paths.sqlite_path)
    assert (reveal["source_kind"], reveal["basis"]) == ("tutor_answer", "hint:walkthrough:L5")
    assert 0 < reveal["amount"] <= 1


def test_a_hint_with_no_key_overlap_writes_no_reveal(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    job = _hint(ctx, session, "approach_question@L1", answerMd="")
    assert job["result"]["hintMd"] == "What would your first move be?"
    assert reveals(paths.sqlite_path) == []


def test_submit_dont_know_folds_shown_hints_too(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "next_step@L3")
    _hint(ctx, session, "worked_chunk@L4", takenLevel=4)
    result = _call(ctx, "submit_dont_know", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1"})
    attempt = _attempt(paths, result["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (1, 1)
    assert {row["attempt_id"] for row in assists(paths.sqlite_path)} == {result["attemptId"]}


@pytest.mark.parametrize("submit", ["attempt", "dont_know"])
def test_max_useful_hints_clamps_the_folded_total(tmp_path, submit):
    paths, ctx, session = _sidecar(tmp_path, cap=1)
    _hint(ctx, session, "approach_question@L1")
    _hint(ctx, session, "next_step@L3")
    if submit == "attempt":
        result = _submit(ctx, session)
    else:
        result = _call(ctx, "submit_dont_know", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1"})
    assert _attempt(paths, result["attemptId"])["hints_used"] == 1
    # The assist rows keep the true count for reports.
    assert sum(1 for row in assists(paths.sqlite_path) if row["shown"] and row["counted_by"] == "server") == 2


def test_authored_reveals_stay_client_counted_and_nothing_counts_twice(tmp_path):
    paths, ctx, session = _sidecar(tmp_path, config="chooser_enabled = false\n")
    # The screen reveals authored hint 0 itself (client-counted) ...
    _call(ctx, "practice.record_hint_reveal", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                               "authoredIndex": 0, "answerMd": WORK})
    # ... then asks the service, whose fallback serves authored hint 1 (server-counted).
    job = _hint(ctx, session, "next_step@L3")
    assert (job["result"]["kind"], job["result"]["authoredIndex"]) == ("authored", 1)
    attempt = _attempt(paths, _submit(ctx, session, hints=1, attempt_type="hinted_attempt")["attemptId"])
    assert attempt["hints_used"] == 2
    counted = sorted((row["counted_by"], row["authored_index"]) for row in assists(paths.sqlite_path))
    assert counted == [("client", 0), ("server", 1)]


def test_a_cancelled_hint_is_never_shown_and_counts_nothing(tmp_path):
    paths, ctx, session = _sidecar(tmp_path, inline=False)
    gate = threading.Event()
    job = _hint(ctx, session, "next_step@L3", writer=WriterFake(gate=gate))
    assert job["state"] == "pending"
    cancelled = _call(ctx, "practice.cancel_hint", {"jobId": job["jobId"]})
    assert cancelled["cancelled"] is True
    gate.set()
    hint_job = ctx.hint_jobs.get(job["jobId"])
    assert hint_job.done.wait(30)
    assert _call(ctx, "practice.hint_job", {"jobId": job["jobId"]})["state"] == "cancelled"
    [row] = assists(paths.sqlite_path)
    assert row["shown"] == 0 and row["shown_at"] is None
    attempt = _attempt(paths, _submit(ctx, session)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (0, 0)
    assert reveals(paths.sqlite_path) == []


def test_a_delivered_hint_cannot_be_cancelled(tmp_path):
    _paths, ctx, session = _sidecar(tmp_path)
    job = _hint(ctx, session, "next_step@L3")
    answer = _call(ctx, "practice.cancel_hint", {"jobId": job["jobId"]})
    assert (answer["cancelled"], answer["reason"]) == (False, "already_shown")


def test_a_withheld_or_undelivered_hint_counts_nothing(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.hints import service as S
    from learnloop.vault.loader import load_vault

    paths, ctx, session = _sidecar(tmp_path)
    leak = WriterFake([lambda c: {**_good(c), "hint_md": "So P = 1/4."}] * 2)
    assert _hint(ctx, session, "next_step@L3", writer=leak)["result"]["status"] == "withheld"
    # Prepared through the service but never delivered (no job read): never shown.
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    prepared = S.request_hint(vault, repository, S.HintRequestV1(
        practice_item_id=ITEM, session_id=session, submission_id="k1", work_md=WORK), writer_client=WriterFake(),
        chooser_client_factory=lambda: ChooserFake(prefer("next_step@L3", 0.9)), seed="u")
    assert prepared.status == S.READY
    attempt = _attempt(paths, _submit(ctx, session)["attemptId"])
    assert (attempt["hints_used"], attempt["primed"]) == (0, 0)


def test_a_discriminating_answer_changes_nothing_in_the_attempt(tmp_path):
    from tests.hint_fakes import add_hypothesis

    def run(root, answer: bool) -> tuple:
        paths, ctx, session = _sidecar(root)
        add_hypothesis(paths.sqlite_path, "h1", "Adds one to a CDF value")
        add_hypothesis(paths.sqlite_path, "h2", "Reads the CDF as the density")
        job = _hint(ctx, session, "discriminating@L1")
        if answer:
            _call(ctx, "practice.answer_discriminating", {
                "sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                "questionAssistId": job["result"]["assistId"], "answerMd": "0"})
        attempt = _attempt(paths, _submit(ctx, session)["attemptId"])
        return attempt["hints_used"], attempt["primed"], len(reveals(paths.sqlite_path))

    assert run(tmp_path / "a", True) == run(tmp_path / "b", False) == (1, 0, 0)


def test_an_earlier_submissions_hints_never_reach_a_later_attempt(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    _hint(ctx, session, "next_step@L3", key="k1")
    first = _attempt(paths, _submit(ctx, session, key="k1")["attemptId"])
    second = _attempt(paths, _submit(ctx, session, key="k2")["attemptId"])
    assert (first["hints_used"], second["hints_used"]) == (1, 0)


def test_a_primed_attempt_with_no_hint_count_is_classified_as_a_counted_one_is():
    """§10.1's reviewer check: worked help (primed, no count) and a primed
    attempt that also counted hints resolve to the same policy, as a guided
    redo's (primed, no count) does; the level alone decides, by existing
    rules."""

    for attempt_type in ("independent_attempt", "hinted_attempt"):
        no_count = resolve_attempt_activity_policy(attempt_type=attempt_type, primed=True, hints_used=0)
        counted = resolve_attempt_activity_policy(attempt_type=attempt_type, primed=True, hints_used=2)
        assert no_count == counted
        assert no_count.contamination_class == "repair_activity" and not no_count.eligible_for_fsrs
        assert not no_count.eligible_for_certification and no_count.counts_as_assisted
    hinted = resolve_attempt_activity_policy(attempt_type="independent_attempt", primed=False, hints_used=1)
    authored_era = resolve_attempt_activity_policy(attempt_type="hinted_attempt", primed=False, hints_used=1)
    assert hinted.counts_as_assisted == authored_era.counts_as_assisted is True
    assert hinted.eligible_for_certification == authored_era.eligible_for_certification is False


def _good(context):
    from tests.hint_fakes import good_answer

    return good_answer(context)
