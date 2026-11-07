"""Mobile M2a: session handoff through the real host (spec §6.5, G10).

The desktop here is a sidecar context with no origin, as the desktop's is; the phone is the
host over HTTP with a fake identity header.
"""

from __future__ import annotations

import pytest

pytest.importorskip("starlette")
from starlette.testclient import TestClient

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop_mobile.host import create_app
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.mobile_host_helpers import (
    HOSTNAME, ITEM, SECOND_ITEM, CountingGrader, Phone, config_for, install_grader, pair, rows, seeded_vault,
)


@pytest.fixture
def world(tmp_path, monkeypatch):
    paths, repository = seeded_vault(tmp_path / "vault")
    install_grader(monkeypatch, CountingGrader())
    device = pair(repository)
    desktop = SidecarContext()
    desktop.load_secondary(paths.root)
    app = create_app(config_for(paths.root))
    with TestClient(app, base_url=f"https://{HOSTNAME}") as client:
        yield Phone(client, device), desktop, repository, paths, app.state.host
    desktop.close()


def _desktop(ctx, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _draft(call, session_id: str, *, item: str = ITEM, text: str = "my draft line\nand more", key: str = "key1"):
    return call("save_practice_draft", {"sessionId": session_id, "practiceItemId": item, "answerMd": text, "submissionId": key})


def test_a_phone_start_over_a_desktop_session_asks_with_its_snapshot(world):
    phone, desktop, repository, *_ = world
    session = _desktop(desktop, "start_session", {"availableMinutes": 25})
    _draft(lambda name, params: _desktop(desktop, name, params), session["sessionId"])
    status, error = phone.error("start_session", {"availableMinutes": 25})
    assert (status, error["code"], error["retryable"]) == (409, "session_open_elsewhere", False)
    details = error["details"]
    assert details["session_id"] == session["sessionId"]
    assert details["owner_label"] == "desktop"
    assert details["has_draft"] is True and details["draft_first_line"] == "my draft line"
    assert details["current_practice_item_id"] == ITEM
    assert repository.fetch_session(session["sessionId"])["ended_at"] is None


def test_adopting_carries_the_checkpoint_the_key_and_the_session_and_the_desktop_sees_it(world):
    phone, desktop, repository, *_ = world
    session = _desktop(desktop, "start_session", {"availableMinutes": 25})
    sid = session["sessionId"]
    _draft(lambda name, params: _desktop(desktop, name, params), sid)
    phone.rpc("adopt_session", {"sessionId": sid, "expectedGeneration": 0})
    read = phone.rpc("get_session", {"sessionId": sid})
    assert read["ownerDeviceId"] == phone.device["device_id"] and read["ownerGeneration"] == 1
    assert read["checkpoint"]["currentAnswer"].startswith("my draft line")
    assert read["checkpoint"]["submissionId"] == "key1"
    assert phone.get("/api/v1/submissions/key1").json() == {"state": "unknown"}
    # The desktop's own read, which the poll makes: useSessionMoved's input.
    seen = _desktop(desktop, "get_session", {"sessionId": sid})
    assert seen["ownerLabel"] == "Phone" and seen["ownerGeneration"] == 1
    # G10: the phone's submit under the same key answers the same session.
    assert phone.submit(sid, "key1", answerMd="my draft line\nand more").status_code == 200
    assert rows(repository, "SELECT session_id, entry_surface FROM practice_attempts WHERE submission_id='key1'") == [
        {"session_id": sid, "entry_surface": "phone_practice"}
    ]


def test_writes_from_the_device_that_lost_it_are_session_moved(world):
    phone, desktop, *_ = world
    session = phone.start()
    sid = session["sessionId"]
    # From the phone's side: the desktop took it back.
    _desktop(desktop, "adopt_session", {"sessionId": sid, "expectedGeneration": session["ownerGeneration"]})
    for method, params in (
        ("update_session_checkpoint", {"sessionId": sid, "currentAnswer": "x"}),
        ("clear_session_checkpoint", {"sessionId": sid}),
        ("save_practice_draft", {"sessionId": sid, "practiceItemId": ITEM, "answerMd": "x", "submissionId": "k"}),
        ("skip_practice_item", {"sessionId": sid, "practiceItemId": ITEM}),
        ("acknowledge_practice_submission", {"sessionId": sid, "practiceItemId": ITEM, "submissionId": "k"}),
        ("end_session", {"sessionId": sid}),
    ):
        status, error = phone.error(method, params)
        assert (status, error["code"]) == (409, "session_moved"), method
        assert error["details"]["owner_label"] == "desktop"
        assert error["details"]["owner_generation"] == 1
    # Reads are unrestricted.
    assert phone.rpc("get_session", {"sessionId": sid})["sessionId"] == sid
    # And the desktop's way round.
    phone.rpc("adopt_session", {"sessionId": sid, "expectedGeneration": 1})
    with pytest.raises(SidecarError) as refused:
        _desktop(desktop, "update_session_checkpoint", {"sessionId": sid, "currentAnswer": "x"})
    assert refused.value.code == "session_moved"
    assert refused.value.details["owner_label"] == "Phone"


def test_a_stale_generation_and_a_stale_replace_are_refused(world):
    phone, desktop, *_ = world
    session = _desktop(desktop, "start_session", {"availableMinutes": 25})
    sid = session["sessionId"]
    status, error = phone.error("adopt_session", {"sessionId": sid, "expectedGeneration": 7})
    assert (status, error["code"]) == (409, "session_moved")
    status, error = phone.error("start_session", {"availableMinutes": 25, "replace": "not-the-open-one"})
    assert (status, error["code"]) == (409, "session_open_elsewhere")
    assert error["details"]["session_id"] == sid


def test_start_fresh_keeps_the_replaced_draft_on_record(world):
    phone, desktop, repository, *_ = world
    session = _desktop(desktop, "start_session", {"availableMinutes": 25})
    sid = session["sessionId"]
    _draft(lambda name, params: _desktop(desktop, name, params), sid)
    fresh = phone.rpc("start_session", {"availableMinutes": 25, "replace": sid})
    assert fresh["sessionId"] != sid and fresh["ownerDeviceId"] == phone.device["device_id"]
    assert repository.fetch_session(sid)["ended_at"] is not None
    handoff = repository.session_handoffs(sid)[-1]
    assert handoff["kind"] == "replace"
    assert "my draft line" in str(handoff["checkpoint"] or handoff.get("checkpoint_json"))
    # What the desktop's re-read now says: the session ended elsewhere.
    assert _desktop(desktop, "get_session", {"sessionId": sid})["endedAt"]


def test_a_desktop_start_over_a_phone_session_asks_and_replace_is_its_answer(world):
    """The desktop's half of §6.5, on the shared handler: the prompt is the frontend's."""

    phone, desktop, repository, *_ = world
    session = phone.start()
    sid = session["sessionId"]
    with pytest.raises(SidecarError) as refused:
        _desktop(desktop, "start_session", {"availableMinutes": 25})
    assert refused.value.code == "session_open_elsewhere"
    assert refused.value.details["owner_label"] == "Phone"
    fresh = _desktop(desktop, "start_session", {"availableMinutes": 25, "replace": sid})
    assert "ownerDeviceId" not in fresh
    assert repository.fetch_session(sid)["ended_at"] is not None


def test_adopting_with_a_draft_on_an_item_the_phone_cannot_show_is_refused(world):
    from tests.test_mobile_rpc import _add_item

    phone, desktop, repository, paths, _host = world
    _add_item(paths, repository, "pi_figure", "See ![it](figures/a.png).")
    desktop.reload()
    session = _desktop(desktop, "start_session", {"availableMinutes": 25})
    sid = session["sessionId"]
    _draft(lambda name, params: _desktop(desktop, name, params), sid, item="pi_figure")
    phone.rpc("get_session", {"sessionId": sid})
    world[4].runtime.rpc_worker.context._fingerprint_checked_at = float("-inf")
    status, error = phone.error("adopt_session", {"sessionId": sid, "expectedGeneration": 0})
    assert (status, error["code"]) == (409, "current_item_desktop_only")
    assert repository.fetch_session(sid)["owner_device_id"] is None
    assert repository.fetch_session_checkpoint(sid)["current_answer"].startswith("my draft line")


def test_a_handoff_bumps_the_token_a_desktop_polls(world):
    phone, desktop, repository, *_ = world
    session = _desktop(desktop, "start_session", {"availableMinutes": 25})
    before = repository.queue_revision()["revision"]
    phone.rpc("adopt_session", {"sessionId": session["sessionId"], "expectedGeneration": 0})
    assert repository.queue_revision()["revision"] == before + 1


def test_a_phones_change_reaches_the_token_without_the_desktop_rebuilding(world):
    """Open item 6: a phone's answer moves the token once. What the desktop does with it is the
    poll's (``App.queueRevision.test.tsx``): one refetch, on Today's list or on the return to it."""

    phone, _desktop_ctx, repository, *_ = world
    session = phone.start()
    before = repository.queue_revision()["revision"]
    offers = rows(repository, "SELECT COUNT(*) AS n FROM scheduler_offer_receipts")[0]["n"]
    assert phone.submit(session["sessionId"], "sub1", item=SECOND_ITEM).status_code == 200
    assert repository.queue_revision()["revision"] == before + 1
    assert rows(repository, "SELECT COUNT(*) AS n FROM scheduler_offer_receipts")[0]["n"] == offers


def test_with_phone_probes_off_no_phone_answer_can_name_a_probe_presentation(tmp_path, monkeypatch):
    """G10's cap boundary as M2 and V2 had it: the cap counts qualifying observations, and a qualifying
    observation is an answer naming a presentation. With the host's ``phone_probes`` off (mobile v2 V3's
    kill switch) the phone never answers one, so the host's two workers add none, however they interleave.
    With it on, the admission's transaction holds the boundary (``tests/test_mobile_v3_probes.py``)."""

    paths, repository = seeded_vault(tmp_path / "vault")
    install_grader(monkeypatch, CountingGrader())
    config = config_for(paths.root).model_copy(update={"phone_probes": False})
    with TestClient(create_app(config), base_url=f"https://{HOSTNAME}") as client:
        phone = Phone(client, pair(repository))
        session = phone.start()
        status, error = phone.error("submit_attempt", {
            "sessionId": session["sessionId"], "practiceItemId": ITEM, "answerMd": "x",
            "attemptType": "diagnostic_probe", "submissionId": "s", "probePresentationId": "p",
        }, request_id="s")
        assert (status, error["code"], error["details"]) == (422, "validation_error", {"field": "probe_presentation_id"})
        status, error = phone.error("followup_next", {"attemptId": "a"})
        assert (status, error["code"]) == (409, "phone_probes_off")
        assert phone.get("/api/v1/meta").json()["phone_probes"] is False
    assert repository.qualifying_probe_observation_count_for_session(session["sessionId"]) == 0


def test_a_phone_answer_naming_no_valid_presentation_qualifies_nothing(world):
    """V3, the switch on: a submit may name a presentation, and one that is not this item's committed presentation
    is no qualifying observation (the shared submit path's own validation)."""

    phone, _desktop_ctx, repository, *_ = world
    session = phone.start()
    phone.post("submit_attempt", {
        "sessionId": session["sessionId"], "practiceItemId": ITEM, "answerMd": "x",
        "attemptType": "diagnostic_probe", "submissionId": "s", "probePresentationId": "p",
    }, request_id="s")
    assert repository.qualifying_probe_observation_count_for_session(session["sessionId"]) == 0


# -- the M2 report (§9, §6.4) ---------------------------------------------------------


def test_the_report_counts_the_phone_apart_and_never_touches_serving(world):
    from learnloop.capture import mobile_report

    phone, desktop, repository, paths, _host = world
    session = phone.start()
    assert phone.submit(session["sessionId"], "sub1").status_code == 200
    phone.rpc("end_session", {"sessionId": session["sessionId"]})
    report = mobile_report(repository, prompts={ITEM: "In the graph below, what is f(2)?", SECOND_ITEM: "Graph f."})
    assert report["phone_sessions"] == 1 and report["completion"] == 1.0
    assert report["attempts_by_surface"] == {"phone_practice": 1}
    assert report["submit_to_feedback_seconds"]["count"] == 1
    assert report["share_of_submits_returning_202"] == 0.0
    assert report["contest_rate_by_surface"] == {"phone_practice": 0.0}
    assert report["contest_note"] == "The phone has no contest button; a phone attempt is contested on the desktop."
    assert list(report["weeks"].values())[0] == {"sessions": 1, "attempts": 1, "items": 1}
    assert report["suspected_figure"] == [{"practice_item_id": ITEM, "phrase": "graph below"}]
    assert mobile_report(repository)["suspected_figure"] is None


def test_the_report_counts_a_desktop_contest_of_a_phone_attempt(world):
    """Verify finding 2: the phone has no button, and its attempts can still be contested."""

    from learnloop.capture import mobile_report

    phone, desktop, repository, _paths, _host = world
    session = phone.start()
    attempt = phone.submit(session["sessionId"], "sub1").json()["result"]["attemptId"]
    second = phone.submit(session["sessionId"], "sub2", item=SECOND_ITEM).json()["result"]["attemptId"]
    assert attempt != second
    _desktop(desktop, "trigger_regrade", {"attemptId": attempt, "learnerReason": "I did use the SVD"})
    report = mobile_report(repository)
    assert report["contest_rate_by_surface"] == {"phone_practice": 0.5}
    assert "no contest button" in report["contest_note"]


@pytest.mark.parametrize("prompt,hit", [
    ("See the figure.", True), ("In the table below, find x.", True), ("The diagram shown has two nodes.", True),
    ("Graph the function f.", False), ("Define a table of contents.", False), ("Prove that $x>0$.", False),
    ("", False),
])
def test_suspected_figure_is_a_word_pattern_and_only_a_report(prompt, hit):
    from pathlib import Path

    from learnloop.capture import suspected_figure
    from learnloop.scheduling import device_eligibility

    assert bool(suspected_figure(prompt)) is hit
    # It decides nothing: serving reads Markdown structure, and this module has no word for it.
    source = Path(device_eligibility.__file__).read_text(encoding="utf-8")
    assert "capture" not in source and "suspected_figure(" not in source


def _policy(repository, submission_id: str):
    from learnloop.diagnosis.causal_activity_policy import resolve_attempt_activity_policy

    row = rows(repository, "SELECT id, attempt_type, primed, hints_used FROM practice_attempts WHERE submission_id=?", submission_id)[0]
    policy = resolve_attempt_activity_policy(
        attempt_type=row["attempt_type"], primed=bool(row["primed"]), hints_used=int(row["hints_used"]),
        recorded=repository.all_causal_activity_classifications().get(str(row["id"])),
    )
    return row, policy


def test_a_desktop_hinted_draft_adopted_by_the_phone_stays_assisted_evidence(world):
    """Codex review F1. The server's fold leaves a client's authored hints to the client, so the
    phone carries the checkpoint's count: through its own draft saves, into its submit."""

    phone, desktop, repository, *_ = world
    sid = _desktop(desktop, "start_session", {"availableMinutes": 25})["sessionId"]
    _desktop(desktop, "save_practice_draft", {
        "sessionId": sid, "practiceItemId": ITEM, "answerMd": "half", "submissionId": "hinted", "hintsUsed": 1,
    })
    phone.rpc("adopt_session", {"sessionId": sid, "expectedGeneration": 0})
    checkpoint = phone.rpc("get_session", {"sessionId": sid})["checkpoint"]
    assert checkpoint["hintsUsed"] == 1
    # What the PWA saves and submits for that checkpoint.
    phone.rpc("save_practice_draft", {
        "sessionId": sid, "practiceItemId": ITEM, "answerMd": "half and more", "submissionId": "hinted", "hintsUsed": 1,
    })
    assert phone.rpc("get_session", {"sessionId": sid})["checkpoint"]["hintsUsed"] == 1
    response = phone.submit(sid, "hinted", answerMd="half and more", hintsUsed=1, authoredHints=1, bookCounted=False,
                            attemptType="hinted_attempt")
    assert response.status_code == 200, response.text
    row, policy = _policy(repository, "hinted")
    assert (row["hints_used"], row["attempt_type"]) == (1, "hinted_attempt")
    assert policy.eligible_for_certification is False


def test_a_draft_whose_count_is_dropped_certifies_which_is_why_the_phone_must_carry_it(world):
    """The harm F1 names, pinned on the server's side: nothing there restores a client's count."""

    phone, desktop, repository, *_ = world
    sid = _desktop(desktop, "start_session", {"availableMinutes": 25})["sessionId"]
    _desktop(desktop, "save_practice_draft", {
        "sessionId": sid, "practiceItemId": ITEM, "answerMd": "half", "submissionId": "dropped", "hintsUsed": 1,
    })
    phone.rpc("adopt_session", {"sessionId": sid, "expectedGeneration": 0})
    assert phone.submit(sid, "dropped").status_code == 200
    row, _policy_read = _policy(repository, "dropped")
    assert row["hints_used"] == 0


def test_the_report_counts_a_failed_submit_in_the_share_of_202(world):
    """Codex review F9: nine failures and one 202 is one in ten, not one in one."""

    from learnloop.capture import mobile_report

    _phone, _desktop_context, repository, *_ = world
    with repository.atomic(), repository.connection() as connection:
        for index, status in enumerate([503] * 8 + [409, 202, 200]):
            connection.execute(
                "INSERT INTO mobile_request_log(id, endpoint, status, duration_ms, at) VALUES (?, 'rpc:submit_attempt', ?, 1.0, '2026-11-03T00:00:00+00:00')",
                (index + 1000, status),
            )
    report = mobile_report(repository)
    assert report["share_of_submits_returning_202"] == round(1 / 11, 4)
    assert report["submit_responses"] == {"total": 11, "returned_200": 1, "returned_202": 1, "failed": 9}
