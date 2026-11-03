"""Mobile PR-5: request origin and provenance (spec_mobile_tailnet_v1 §6.8, G11).

The phone host (M2) sets ``SidecarContext.request_origin`` around each call; the
desktop sidecar leaves it None. So the host here is a sidecar context acting as a
paired device (``ctx.acting_as``). Attempts, offers and bindings take their
surface from the origin, session ownership its device, and no parameter can set
any of them.

Durability lane: production pragmas and WAL on fresh vaults, because the handoff
tests move a session between two devices.
"""

from __future__ import annotations

import threading

import pytest
from pydantic import ValidationError

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.db.repositories import Repository
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY
from learnloop_sidecar.request_origin import RequestOrigin

from tests.helpers import add_followup_item, create_basic_vault, seed_due_item

pytestmark = pytest.mark.durability

ITEM = "pi_svd_define_001"
SECOND_ITEM = "pi_svd_define_002"
PHONE = RequestOrigin(device_id="dev_phone")
SELF_GRADE = {"criterionPoints": {"correctness": 4}, "confidence": 4}


def _call(ctx: SidecarContext, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _world(tmp_path):
    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    repository = seed_due_item(paths)
    add_followup_item(paths.root, SECOND_ITEM)
    repository.upsert_practice_item_state(
        SECOND_ITEM, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z", active=True,
    )
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO mobile_devices (id, label, scope, token_hash, created_at) "
            "VALUES (?, 'Phone', 'app', 'hash', '2026-11-03T00:00:00Z')",
            (PHONE.device_id,),
        )
        connection.commit()
    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    ctx.grading_provider_override = "manual"
    return paths, repository, ctx


def _rows(repository: Repository, sql: str, *args) -> list[dict]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(sql, args).fetchall()]


def _attempt_surface(repository: Repository, attempt_id: str) -> str:
    return _rows(repository, "SELECT entry_surface FROM practice_attempts WHERE id = ?", attempt_id)[0]["entry_surface"]


def _items(queue: dict) -> list[dict]:
    return [item for section in queue["sections"] for item in section["items"]]


def _submit(ctx, session_id: str, item: str = ITEM, **extra) -> dict:
    return _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": item, "answerMd": "an answer",
        "attemptType": "independent_attempt", "selfGrade": SELF_GRADE, **extra,
    })


def test_the_desktop_is_the_none_origin_and_records_what_it_always_did(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    assert ctx.request_origin is None and ctx.origin_device_id is None

    session = _call(ctx, "start_session", {"availableMinutes": 20})
    queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
    item = _items(queue)[0]
    _call(ctx, "save_practice_draft", {
        "sessionId": session["sessionId"], "practiceItemId": item["practiceItemId"], "answerMd": "half",
        "submissionId": "sub-desktop", "schedulerCandidateId": item["schedulerCandidateId"],
    })
    attempt = _submit(ctx, session["sessionId"], item["practiceItemId"], submissionId="sub-desktop",
                      schedulerCandidateId=item["schedulerCandidateId"])

    assert _attempt_surface(repository, attempt["attemptId"]) == "desktop_practice"
    assert {row["entry_surface"] for row in _rows(repository, "SELECT entry_surface FROM scheduler_offer_receipts")} == {
        "desktop_queue"}
    assert _rows(repository, "SELECT entry_surface FROM submission_intents") == [{"entry_surface": "desktop_practice"}]
    assert _rows(repository, "SELECT owner_device_id FROM sessions") == [{"owner_device_id": None}]


def test_a_phone_request_records_its_surfaces_from_the_origin(tmp_path):
    """G11: the attempt, the offer, the draft's binding and the router's rows."""

    _paths, repository, ctx = _world(tmp_path)
    with ctx.acting_as(PHONE):
        session = _call(ctx, "start_session", {"availableMinutes": 20})
        queue = _call(ctx, "get_today_queue", {"sessionId": session["sessionId"]})
        items = _items(queue)
        # A pick of the second item, so the router logs the bind's surface too.
        item = items[1]
        _call(ctx, "save_practice_draft", {
            "sessionId": session["sessionId"], "practiceItemId": item["practiceItemId"], "answerMd": "half",
            "submissionId": "sub-phone", "schedulerCandidateId": item["schedulerCandidateId"],
        })
        attempt = _submit(ctx, session["sessionId"], item["practiceItemId"], submissionId="sub-phone",
                          schedulerCandidateId=item["schedulerCandidateId"])
    assert ctx.request_origin is None

    assert _attempt_surface(repository, attempt["attemptId"]) == "phone_practice"
    assert {row["entry_surface"] for row in _rows(repository, "SELECT entry_surface FROM scheduler_offer_receipts")} == {
        "phone_queue"}
    assert _rows(repository, "SELECT entry_surface FROM submission_intents") == [{"entry_surface": "phone_practice"}]
    assert _rows(repository, "SELECT owner_device_id FROM sessions") == [{"owner_device_id": PHONE.device_id}]
    picks = _rows(repository, "SELECT surface FROM router_decisions WHERE decision_kind = 'learner_pick'")
    offers = _rows(repository, "SELECT surface FROM router_decisions WHERE decision_kind = 'today_offer'")
    assert picks == [{"surface": "phone_practice"}]
    # M2a (open item 3): under a serving plan too, a phone's offer is its own surface.
    assert offers and {row["surface"] for row in offers} == {"phone_queue"}


def test_a_submit_on_the_phone_binds_its_own_surface_without_a_draft_first(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    with ctx.acting_as(PHONE):
        session = _call(ctx, "start_session", {"availableMinutes": 20})
        item = _items(_call(ctx, "get_today_queue", {"sessionId": session["sessionId"]}))[0]
        attempt = _submit(ctx, session["sessionId"], item["practiceItemId"], submissionId="sub-direct",
                          schedulerCandidateId=item["schedulerCandidateId"])
    assert _attempt_surface(repository, attempt["attemptId"]) == "phone_practice"
    assert _rows(repository, "SELECT entry_surface FROM submission_intents") == [{"entry_surface": "phone_practice"}]


def test_a_dont_know_and_a_stuck_answer_on_the_phone_carry_the_phone_surface(tmp_path):
    """The other two ways an attempt is written from a submit RPC."""

    _paths, repository, ctx = _world(tmp_path)
    with ctx.acting_as(PHONE):
        session = _call(ctx, "start_session", {"availableMinutes": 20})
        dont_know = _call(ctx, "submit_dont_know", {
            "sessionId": session["sessionId"], "practiceItemId": ITEM, "submissionId": "sub-dk",
        })
        stuck = _call(ctx, "submit_attempt", {
            "sessionId": session["sessionId"], "practiceItemId": SECOND_ITEM, "answerMd": "",
            "attemptType": "independent_attempt", "declaredStuck": True, "submissionId": "sub-stuck",
        })
    assert _attempt_surface(repository, dont_know["attemptId"]) == "phone_practice"
    assert _attempt_surface(repository, stuck["attemptId"]) == "phone_practice"


@pytest.mark.parametrize("name, params", [
    ("start_session", {}),
    ("get_today_queue", {}),
    ("skip_practice_item", {"sessionId": "s", "practiceItemId": ITEM}),
    ("save_practice_draft", {"sessionId": "s", "practiceItemId": ITEM, "answerMd": "a"}),
    ("submit_attempt", {"sessionId": "s", "practiceItemId": ITEM, "answerMd": "a",
                        "attemptType": "independent_attempt"}),
    ("submit_dont_know", {"sessionId": "s", "practiceItemId": ITEM}),
    ("open_queue_item", {"practiceItemId": ITEM}),
    ("get_practice_item", {"practiceItemId": ITEM}),
    ("end_session", {"sessionId": "s"}),
])
@pytest.mark.parametrize("field", ["entrySurface", "entry_surface", "deviceId", "device_id", "surface", "requestOrigin",
                                   "deviceClass", "ownerDeviceId"])
def test_no_parameter_can_set_the_surface_or_the_device(name, params, field):
    """T8: the params models forbid every other key, so a client claims nothing."""

    with pytest.raises(ValidationError):
        METHOD_REGISTRY[name].params_model.model_validate({**params, field: "phone"})


def test_session_ownership_follows_the_origin_device(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    with ctx.acting_as(PHONE):
        phone_session = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
        _call(ctx, "update_session_checkpoint", {"sessionId": phone_session, "currentAnswer": "on the phone"})

    # The desktop may read it, and every write of its own is refused.
    with pytest.raises(SidecarError) as moved:
        _call(ctx, "update_session_checkpoint", {"sessionId": phone_session, "currentAnswer": "on the desktop"})
    assert moved.value.code == "session_moved" and moved.value.details["owner_label"] == "Phone"
    with pytest.raises(SidecarError) as elsewhere:
        _call(ctx, "start_session", {"availableMinutes": 20})
    assert elsewhere.value.code == "session_open_elsewhere"
    assert repository.fetch_session_checkpoint(phone_session)["current_answer"] == "on the phone"

    with ctx.acting_as(PHONE):
        ended = _call(ctx, "end_session", {"sessionId": phone_session})
    assert ended["endedAt"] is not None


def test_another_paired_device_is_refused_on_the_phones_session(tmp_path):
    _paths, _repository, ctx = _world(tmp_path)
    with ctx.acting_as(PHONE):
        session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    with ctx.acting_as(RequestOrigin(device_id="dev_tablet")), pytest.raises(SidecarError) as moved:
        _call(ctx, "save_practice_draft", {"sessionId": session_id, "practiceItemId": ITEM, "answerMd": "x"})
    assert moved.value.code == "session_moved"


def test_an_attempts_device_is_the_request_never_the_sessions_owner(tmp_path):
    """No attribution from the owner (§6.8): the session moves, the attempts keep
    the device that made them, and a later attempt takes its own origin's."""

    _paths, repository, ctx = _world(tmp_path)
    with ctx.acting_as(PHONE):
        session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
        on_phone = _submit(ctx, session_id, ITEM, submissionId="sub-1")["attemptId"]

    generation = repository.fetch_session(session_id)["owner_generation"]
    repository.adopt_session(session_id, None, generation)
    assert repository.fetch_session(session_id)["owner_device_id"] is None
    on_desktop = _submit(ctx, session_id, SECOND_ITEM, submissionId="sub-2")["attemptId"]

    assert _attempt_surface(repository, on_phone) == "phone_practice"
    assert _attempt_surface(repository, on_desktop) == "desktop_practice"


def test_a_submit_accepted_before_a_handoff_keeps_the_phones_surface(tmp_path, monkeypatch):
    """Ownership is checked at acceptance (§6.5): the session moves to the desktop
    while the phone's answer is being graded, and the attempt is still the
    phone's, because its surface was read from the request."""

    from learnloop_sidecar.handlers import practice as practice_handlers

    _paths, repository, ctx = _world(tmp_path)
    with ctx.acting_as(PHONE):
        session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    other = Repository(repository.sqlite_path)
    original = practice_handlers._self_grade

    def adopt_then_grade(payload):
        other.adopt_session(session_id, None, other.fetch_session(session_id)["owner_generation"])
        return original(payload)

    monkeypatch.setattr(practice_handlers, "_self_grade", adopt_then_grade)
    with ctx.acting_as(PHONE):
        attempt = _submit(ctx, session_id, ITEM, submissionId="sub-race")["attemptId"]

    assert repository.fetch_session(session_id)["owner_device_id"] is None
    assert _attempt_surface(repository, attempt) == "phone_practice"


def test_acting_as_restores_the_origin_after_a_refused_call():
    ctx = SidecarContext()
    with pytest.raises(RuntimeError), ctx.acting_as(PHONE):
        assert ctx.origin_device_id == PHONE.device_id
        raise RuntimeError("refused")
    assert ctx.request_origin is None and ctx.origin_device_id is None
    with ctx.acting_as(PHONE), ctx.acting_as(None):
        assert ctx.request_origin is None


def test_an_origin_names_a_device_and_a_known_surface():
    with pytest.raises(ValueError):
        RequestOrigin(device_id=" ")
    with pytest.raises(ValueError):
        RequestOrigin(device_id="dev", surface="desktop")


def test_each_context_keeps_its_own_origin():
    """§3.1: two workers, two contexts; one worker's origin never reaches the other."""

    first, second = SidecarContext(), SidecarContext()
    seen: list[str | None] = []
    with first.acting_as(PHONE):
        thread = threading.Thread(target=lambda: seen.append(second.origin_device_id))
        thread.start()
        thread.join()
    assert seen == [None]
