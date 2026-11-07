"""Mobile v2 stage V3, the items V2's landing carried (docs/reviews/phone-v2-v2-today-plan.md, "Open items"):

* **The F9 class on a finished plan.** *Keep going* on a ``complete`` plan and ``plan_more_new{confirm}`` wrote
  their stop-override receipt before ``build_plan``, in a transaction of their own. A phone whose session moved
  during the build was refused ``session_moved`` with the receipt already committed: an override recorded for an
  extension that never existed. Landing ruling R3's rule now covers both: the build's slow work comes first, and the
  receipt commits inside the transaction that inserts the new plan, which checks the session's owner, so a refusal
  leaves no receipt. Reproduced first (Codex's away-and-back shape, as R3's test).
* **``help_assists.surface`` records ``phone_practice``** (ruling R5: the CHECK widening goes into V3): an item's own
  hint revealed on the phone is a row with the phone's surface; the desktop's stays ``practice``.

No model and no network.
"""

from __future__ import annotations

import pytest

pytest.importorskip("starlette")

from learnloop.daily_plan import engine

from tests.mobile_host_helpers import rows
from tests.test_mobile_v2_plan import _call, _desktop, _next, _phone_day, plan_world  # noqa: F401

_PLANS = "SELECT id, kind, status, minutes_budget, split_json FROM daily_plans ORDER BY created_at, id"


def _receipts(repository):
    return rows(repository, "SELECT session_id, end_reason, plan_id, detail_json FROM session_receipts "
                            "WHERE kind = 'stop_response' ORDER BY created_at, id")


def _phone_to_a_finished_plan(phone, repository, root) -> str:
    """The phone's day; the desktop answers what it left; the phone takes the session back and reaches done."""

    session_id = phone.start()["sessionId"]
    _phone_day(phone, session_id)
    ctx = _desktop(root)
    owner = repository.fetch_session(session_id)
    _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": owner.get("owner_generation") or 0})
    for _index in range(8):
        step = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
        if step is None or step["kind"] != "item":
            break
        _call(ctx, "submit_dont_know", {"sessionId": session_id, "practiceItemId": step["practiceItemId"],
                                        "hintsUsed": 0, "planPresentationId": step.get("presentationId")})
    generation = repository.fetch_session(session_id).get("owner_generation") or 0
    phone.rpc("adopt_session", {"sessionId": session_id, "expectedGeneration": generation})
    done = _next(phone, session_id, "next_done")
    assert done["step"]["kind"] == "done" and done["plan"]["status"] == "complete", done["plan"]["status"]
    return session_id


def _away_and_back_during_the_build(monkeypatch, repository, session_id: str, phone_device: str, *, on_call: int = 1):
    """During the extension's build (``_prepare_plan``'s slow pool), the desktop adopts the phone's session and the
    phone adopts it back: the session is the phone's again, at a later generation. ``on_call``: which prepare (the
    ``more_new`` preview prepares once before its build)."""

    real = engine._prepare_plan
    calls: list[int] = []

    def away_and_back(env, **kwargs):
        calls.append(1)
        if len(calls) == on_call:
            generation = int(repository.fetch_session(session_id).get("owner_generation") or 0)
            repository.adopt_session(session_id, None, generation)
            repository.adopt_session(session_id, phone_device, generation + 1)
        return real(env, **kwargs)

    monkeypatch.setattr(engine, "_prepare_plan", away_and_back)
    return calls


def test_keep_going_on_a_finished_plan_refused_mid_build_leaves_no_override_receipt(plan_world, monkeypatch):
    phone, _host, repository, paths = plan_world
    session_id = _phone_to_a_finished_plan(phone, repository, paths.root)
    calls = _away_and_back_during_the_build(monkeypatch, repository, session_id, phone.device["device_id"])
    before, receipts = rows(repository, _PLANS), _receipts(repository)
    status, error = phone.error("plan_keep_going", {"sessionId": session_id})
    assert calls and (status, error["code"]) == (409, "session_moved")
    # Nothing committed: no override for an extension that was never made, and no new plan.
    assert _receipts(repository) == receipts == []
    assert rows(repository, _PLANS) == before


def test_more_new_confirmed_on_a_finished_plan_refused_mid_build_leaves_no_override_receipt(plan_world, monkeypatch):
    phone, _host, repository, paths = plan_world
    session_id = _phone_to_a_finished_plan(phone, repository, paths.root)
    preview = phone.rpc("plan_more_new", {"sessionId": session_id, "confirm": False})
    if not preview["preview"]["available"]:
        pytest.skip("no new material left to admit")  # pragma: no cover - the plan vault has unseen items
    calls = _away_and_back_during_the_build(monkeypatch, repository, session_id, phone.device["device_id"], on_call=2)
    before, receipts = rows(repository, _PLANS), _receipts(repository)
    status, error = phone.error("plan_more_new", {"sessionId": session_id, "confirm": True})
    assert len(calls) >= 2 and (status, error["code"]) == (409, "session_moved")
    assert _receipts(repository) == receipts == []
    assert rows(repository, _PLANS) == before


def test_keep_going_on_a_finished_plan_commits_its_override_with_the_extension(plan_world):
    phone, _host, repository, paths = plan_world
    session_id = _phone_to_a_finished_plan(phone, repository, paths.root)
    finished = rows(repository, _PLANS)[-1]
    going = phone.rpc("plan_keep_going", {"sessionId": session_id})
    assert going["plan"]["kind"] == "keep_going"
    receipts = _receipts(repository)
    assert [(r["session_id"], r["end_reason"], r["plan_id"]) for r in receipts] == [
        (session_id, "offered_stop_overridden", finished["id"])]
    assert '"keep_going"' in receipts[0]["detail_json"]


def test_the_desktops_keep_going_on_a_finished_plan_records_as_before(plan_world):
    """The desktop (a None origin): one override receipt and the extension, as before the change."""

    phone, _host, repository, paths = plan_world
    session_id = _phone_to_a_finished_plan(phone, repository, paths.root)
    ctx = _desktop(paths.root)
    generation = repository.fetch_session(session_id).get("owner_generation") or 0
    _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": generation})
    finished = rows(repository, _PLANS)[-1]
    going = _call(ctx, "plan_keep_going", {"sessionId": session_id})
    assert going["plan"]["kind"] == "keep_going"
    assert [(r["end_reason"], r["plan_id"]) for r in _receipts(repository)] == [
        ("offered_stop_overridden", finished["id"])]


# -- help_assists.surface (migration 250; V2's landing ruling R5) ------------------------------------------------


def test_an_items_own_hint_revealed_on_the_phone_records_the_phones_surface_and_the_desktops_stays_practice(
        tmp_path, monkeypatch):
    from starlette.testclient import TestClient

    from learnloop_mobile.host import create_app
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    from tests.mobile_host_helpers import HOSTNAME, ITEM, CountingGrader, Phone, config_for, install_grader, pair, seeded_vault

    paths, repository = seeded_vault(tmp_path / "vault")
    install_grader(monkeypatch, CountingGrader())
    vault_ctx = SidecarContext()
    vault_ctx.load(paths.root)
    vault, _ = vault_ctx.require_vault()
    if not vault.practice_items[ITEM].hints:
        pytest.skip("the seeded item has no authored hint")  # pragma: no cover
    with TestClient(create_app(config_for(paths.root)), base_url=f"https://{HOSTNAME}") as client:
        phone = Phone(client, pair(repository))
        session_id = phone.start()["sessionId"]
        params = {"sessionId": session_id, "practiceItemId": ITEM, "submissionId": "sub_hint_phone", "authoredIndex": 0,
                  "answerMd": "a start", "revealedAt": None}
        assert phone.rpc("practice.record_hint_reveal", params)["recorded"] is True
        phone.rpc("end_session", {"sessionId": session_id})
    spec = METHOD_REGISTRY["start_session"]
    desktop_session = spec.handler(vault_ctx, spec.params_model.model_validate({"availableMinutes": 25}))["sessionId"]
    spec = METHOD_REGISTRY["practice.record_hint_reveal"]
    reply = spec.handler(vault_ctx, spec.params_model.model_validate(
        {**params, "sessionId": desktop_session, "submissionId": "sub_hint_desktop"}))
    assert reply["recorded"] is True
    assert rows(repository, "SELECT submission_id, surface FROM help_assists ORDER BY submission_id") == [
        {"submission_id": "sub_hint_desktop", "surface": "practice"},
        {"submission_id": "sub_hint_phone", "surface": "phone_practice"},
    ]
    vault_ctx.close()
