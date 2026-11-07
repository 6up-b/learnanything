"""Mobile v2 stage V3 (spec §8's V3 row; owner decision D3): probes answered on the phone.

Through the shared sidecar handlers, the phone as a request origin with the host's ``phone_probes`` on (what the host
sets on every origin it makes), the desktop as a None origin, on FG1's live-shape vault at V3's successor tag, every
model faked (the grader and diagnoser ``BlindRivalClient``, the author ``AuthorFake``):

* **burn and single use across both devices:** a generated follow-up probe opened by the phone's Next is burned at that
  serve under the phone's surface; the desktop's doors refuse it; the phone's own re-open is the same administration;
  answered, it is never served again on either device. The reverse holds too: one the desktop served is refused on the
  phone, and the phone's Next goes on;
* **held feedback released only on the answer:** the miss's worked answer and causes stay held on both devices until
  the phone's answer; the answer's display is refused while held;
* **the probe contract's no-help rules:** the contract the phone gets forbids hints, Ask, worked examples and the
  answer, and the server refuses a hint reveal during it;
* **switch off and below the tag:** the phone is V2's exactly (the hand-off line, Next goes on writing nothing, every
  door reserved, a probe's presentation refused at submit);
* **the cap boundary (G10):** a phone's admission is one transaction with its cap count, so a concurrent answer can't
  commit between them; at the cap the phone's next admission is refused.

No model call and no network.
"""

from __future__ import annotations

import sqlite3
import threading
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import LESSON_OPPORTUNITY_ALGORITHM_VERSION, PHONE_PROBES_ALGORITHM_VERSION
from learnloop.diagnosis.split.jobs import drain
from learnloop.followup_run.serving import PHONE_HANDOFF_LINE, is_holding
from learnloop.followup_serve import identity, workflow as wf
from learnloop.followup_serve.gates import PHONE_SURFACE, SERVING_SURFACE
from learnloop_sidecar import handlers  # noqa: F401 - registers the methods
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY
from learnloop_sidecar.request_origin import RequestOrigin

from tests.followup_serve_helpers import LIVE_ITEM, BlindRivalClient, live_shape_vault
from tests.test_followup_rival_factor import _Ready, _generate
from tests.test_mobile_v2_plan import plan_world  # noqa: F401 - fixture

TAG = PHONE_PROBES_ALGORITHM_VERSION
PHONE = RequestOrigin(device_id="dev_phone", phone_probes=True)
#: The phone as V2 was, and as the host makes it with ``phone_probes = false``.
V2_PHONE = RequestOrigin(device_id="dev_phone")


def _call(ctx, name, params, origin=None):
    spec = METHOD_REGISTRY[name]
    with ctx.acting_as(origin):
        return spec.handler(ctx, spec.params_model.model_validate(params))


def _refused(ctx, name, params, origin, code):
    with pytest.raises(SidecarError) as caught:
        _call(ctx, name, params, origin)
    assert caught.value.code == code, caught.value
    return caught.value


def _world(tmp_path, monkeypatch, *, version: str = TAG, owner=PHONE):
    paths, _vault, _repository = live_shape_vault(tmp_path, version=version)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    client = BlindRivalClient()
    monkeypatch.setattr("learnloop_sidecar.handlers.practice.ready_grading_provider",
                        lambda *_a, **_k: ("fake", _Ready(), client))
    session = _call(ctx, "start_session", {"availableMinutes": 30}, owner)["sessionId"]
    return SimpleNamespace(ctx=ctx, client=client, session=session, paths=paths)


@pytest.fixture
def world(tmp_path, monkeypatch):
    return _world(tmp_path, monkeypatch)


def _miss(world, origin) -> str:
    vault, repository = world.ctx.require_vault()
    result = _call(world.ctx, "submit_attempt", {
        "sessionId": world.session, "practiceItemId": LIVE_ITEM, "answerMd": "A = U Sigma V wrong",
        "attemptType": "independent_attempt", "latencySeconds": 60,
    }, origin)
    attempt_id = result["attemptId"]
    drain(vault, repository, client_factory=lambda: world.client, embedding_factory=lambda: None)
    return attempt_id


def _ready(world, origin):
    """A miss on ``origin``'s device with two rival causes, its question generated and ready."""

    attempt_id = _miss(world, origin)
    _generate(world)
    world.ctx.reload(maintenance=False)
    _vault, repository = world.ctx.require_vault()
    row = wf.attempt_workflow(repository, attempt_id)
    assert row["state"] == wf.READY and row["practice_item_id"], row
    return attempt_id, row, repository


def _adopt(world, origin):
    _vault, repository = world.ctx.require_vault()
    generation = int(repository.fetch_session(world.session).get("owner_generation") or 0)
    _call(world.ctx, "adopt_session", {"sessionId": world.session, "expectedGeneration": generation}, origin)


def _answer(world, item_id: str, presentation_id: str, origin):
    _vault, repository = world.ctx.require_vault()
    result = _call(world.ctx, "submit_attempt", {
        "sessionId": world.session, "practiceItemId": item_id, "answerMd": "An answer.",
        "attemptType": "diagnostic_probe", "latencySeconds": 40, "probePresentationId": presentation_id,
    }, origin)
    vault, _ = world.ctx.require_vault()
    drain(vault, repository, client_factory=lambda: world.client, embedding_factory=lambda: None)
    return result


# -- burn and single use across both devices ----------------------------------------------------------------------


def test_the_phone_opens_its_question_burns_it_as_the_phones_and_the_desktop_is_refused(world):
    attempt_id, row, repository = _ready(world, PHONE)
    item_id = row["practice_item_id"]
    assert row["surface"] == PHONE_SURFACE
    # The phone reads the desktop's line, not V2's hand-off, and its Next opens the question.
    status = _call(world.ctx, "followup_status", {"attemptId": attempt_id}, PHONE)
    assert status["line"] != PHONE_HANDOFF_LINE and status["held"] is True
    step = _call(world.ctx, "followup_next", {"attemptId": attempt_id}, PHONE)
    assert step["action"] == "open" and step["practiceItemId"] == item_id
    # Listing and Next never burn; the serve does, under the phone's surface.
    assert identity.closed_probe_ids(repository) == frozenset()
    detail = _call(world.ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": world.session}, PHONE)
    assert detail["id"] == item_id
    assert identity.served_surface(repository, item_id) == PHONE_SURFACE
    contract = _call(world.ctx, "get_probe_contract", {"practiceItemId": item_id, "sessionId": world.session}, PHONE)
    assert contract["active"] is True and contract["presentationId"] == row["presentation_id"]
    # The phone's re-open (a reload, the app reopened) is the same administration.
    _call(world.ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": world.session}, PHONE)
    # The desktop takes the session: every door refuses the phone's question, and its Next goes on.
    _adopt(world, None)
    _refused(world.ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": world.session}, None,
             identity.GENERATED_PROBE_CLOSED)
    _refused(world.ctx, "open_queue_item", {"practiceItemId": item_id}, None, identity.GENERATED_PROBE_CLOSED)
    _refused(world.ctx, "get_probe_contract", {"practiceItemId": item_id, "sessionId": world.session}, None,
             identity.GENERATED_PROBE_CLOSED)
    assert _call(world.ctx, "followup_next", {"attemptId": attempt_id})["action"] == "continue"
    # Nothing the desktop did there wrote anything: still the phone's, still ready, still held.
    assert identity.served_surface(repository, item_id) == PHONE_SURFACE
    assert wf.get(repository, row["id"])["state"] == wf.READY and is_holding(wf.get(repository, row["id"]))


def test_the_phones_answer_releases_the_held_feedback_and_the_question_is_never_served_again(world):
    attempt_id, row, repository = _ready(world, PHONE)
    item_id = row["practice_item_id"]
    params = {"attemptId": attempt_id, "recordOpen": False}
    # Held on both devices until the answer: the worked answer, the causes, their display.
    for origin in (PHONE, None):
        bundle = _call(world.ctx, "get_feedback", params, origin)
        assert bundle["followup"]["held"] is True and bundle["feedbackMd"] is None and bundle["repairSuggestions"] == []
    _refused(world.ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "d_phone"}, PHONE,
             "followup_feedback_held")
    _call(world.ctx, "followup_next", {"attemptId": attempt_id}, PHONE)
    _call(world.ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": world.session}, PHONE)
    contract = _call(world.ctx, "get_probe_contract", {"practiceItemId": item_id, "sessionId": world.session}, PHONE)
    # Opened and not yet answered, still held.
    assert _call(world.ctx, "get_feedback", params, PHONE)["followup"]["held"] is True
    answer = _answer(world, item_id, contract["presentationId"], PHONE)
    assert answer["attemptId"]
    settled = wf.get(repository, row["id"])
    assert settled["state"] == wf.SETTLED and settled["release_reason"] == wf.RELEASE_PROBE_ANSWERED
    # The phone's answer is the probe's observation, recorded on the phone's surface.
    attempt = repository.fetch_practice_attempt(answer["attemptId"])
    assert attempt["probe_presentation_id"] == contract["presentationId"]
    assert attempt["entry_surface"] == "phone_practice" and attempt["attempt_type"] == "diagnostic_probe"
    for origin in (PHONE, None):
        bundle = _call(world.ctx, "get_feedback", params, origin)
        assert bundle["followup"]["held"] is False
    # Its display may be recorded now: nothing is held any longer.
    assert _call(world.ctx, "record_answer_display", {"attemptId": attempt_id, "displayId": "d_after"}, PHONE)
    # Never again, on either device, by any door; Next goes on.
    _refused(world.ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": world.session}, PHONE,
             identity.GENERATED_PROBE_CLOSED)
    _refused(world.ctx, "open_queue_item", {"practiceItemId": item_id}, PHONE, identity.GENERATED_PROBE_CLOSED)
    assert _call(world.ctx, "followup_next", {"attemptId": attempt_id}, PHONE)["action"] == "continue"
    _adopt(world, None)
    _refused(world.ctx, "open_queue_item", {"practiceItemId": item_id}, None, identity.GENERATED_PROBE_CLOSED)
    queue = _call(world.ctx, "get_today_queue", {"sessionId": world.session})
    listed = {item["practiceItemId"] for section in queue["sections"] for item in section["items"]}
    assert item_id not in listed


def test_a_question_the_desktop_served_is_refused_on_the_phone_and_the_phones_next_goes_on(tmp_path, monkeypatch):
    world = _world(tmp_path, monkeypatch, owner=None)
    attempt_id, row, repository = _ready(world, None)
    item_id = row["practice_item_id"]
    assert _call(world.ctx, "followup_next", {"attemptId": attempt_id})["action"] == "open"
    _call(world.ctx, "open_queue_item", {"practiceItemId": item_id})
    assert identity.served_surface(repository, item_id) == SERVING_SURFACE
    _adopt(world, PHONE)
    _refused(world.ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": world.session}, PHONE,
             identity.GENERATED_PROBE_CLOSED)
    _refused(world.ctx, "open_queue_item", {"practiceItemId": item_id}, PHONE, identity.GENERATED_PROBE_CLOSED)
    assert _call(world.ctx, "followup_next", {"attemptId": attempt_id}, PHONE)["action"] == "continue"
    # The phone's list never offers it, and says one question waits for the desktop.
    queue = _call(world.ctx, "get_today_queue", {"sessionId": world.session}, PHONE)
    listed = {item["practiceItemId"] for section in queue["sections"] for item in section["items"]}
    assert item_id not in listed and queue["deviceDeferredCount"] >= 1
    # The desktop takes it back and answers its own administration.
    _adopt(world, None)
    contract = _call(world.ctx, "get_probe_contract", {"practiceItemId": item_id, "sessionId": world.session})
    assert contract["active"] is True
    _answer(world, item_id, contract["presentationId"], None)
    assert wf.get(repository, row["id"])["state"] == wf.SETTLED


def test_the_plans_step_filter_holds_only_what_the_phone_may_not_open(world):
    from learnloop_sidecar.handlers.daily_plan import _step_filter

    attempt_id, row, repository = _ready(world, PHONE)
    item_id = row["practice_item_id"]
    vault, _ = world.ctx.require_vault()
    item = vault.practice_items[item_id]
    with world.ctx.acting_as(PHONE):
        on = _step_filter(world.ctx, vault, repository, world.session)
    with world.ctx.acting_as(V2_PHONE):
        off = _step_filter(world.ctx, vault, repository, world.session)
    assert on.holds(item) is None and off.holds(item) == "generated_probe"
    # Served on the desktop, it is the desktop's: the phone's step holds it for the desktop's next Next.
    _adopt(world, None)
    _call(world.ctx, "open_queue_item", {"practiceItemId": item_id})
    with world.ctx.acting_as(PHONE):
        assert _step_filter(world.ctx, vault, repository, world.session).holds(item) == "generated_probe"
    assert attempt_id


# -- the probe contract's no-help rules -----------------------------------------------------------------------------


def test_the_contract_on_the_phone_forbids_help_and_the_server_refuses_a_hint_during_it(world):
    attempt_id, row, repository = _ready(world, PHONE)
    item_id = row["practice_item_id"]
    _call(world.ctx, "followup_next", {"attemptId": attempt_id}, PHONE)
    _call(world.ctx, "get_practice_item", {"practiceItemId": item_id, "sessionId": world.session}, PHONE)
    contract = _call(world.ctx, "get_probe_contract", {"practiceItemId": item_id, "sessionId": world.session}, PHONE)
    assert contract["forcedAttemptType"] == "diagnostic_probe"
    assert contract["restrictions"] == {
        "hintsDisabled": True, "askTutorDisabled": True, "workedExampleDisabled": True,
        "answerRevealDisabled": True, "feedbackDeferred": True,
    }
    vault, _ = world.ctx.require_vault()
    if vault.practice_items[item_id].hints:
        reply = _call(world.ctx, "practice.record_hint_reveal", {
            "sessionId": world.session, "practiceItemId": item_id, "submissionId": "s_hint", "authoredIndex": 0,
            "answerMd": "", "revealedAt": None}, PHONE)
        assert reply["recorded"] is False and reply["reason"] == "diagnostic_block"
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM help_assists WHERE practice_item_id = ?",
                                  (item_id,)).fetchone()[0] == 0


# -- switch off, and below the tag: V2's phone ----------------------------------------------------------------------


@pytest.mark.parametrize("case", ["switch_off", "below_the_tag"])
def test_without_phone_probes_the_phone_is_v2s(tmp_path, monkeypatch, case):
    origin = V2_PHONE if case == "switch_off" else PHONE
    version = TAG if case == "switch_off" else LESSON_OPPORTUNITY_ALGORITHM_VERSION
    world = _world(tmp_path, monkeypatch, version=version, owner=origin)
    attempt_id, row, repository = _ready(world, origin)
    item_id = row["practice_item_id"]
    events_before = repository.connection().execute("SELECT COUNT(*) FROM followup_workflow_events").fetchone()[0]
    status = _call(world.ctx, "followup_status", {"attemptId": attempt_id}, origin)
    assert status["line"] == PHONE_HANDOFF_LINE
    assert _call(world.ctx, "followup_next", {"attemptId": attempt_id}, origin) == {
        "version": 1, "action": "continue", "line": None, "practiceItemId": None, "presentationId": None}
    # Next wrote nothing (V2's phone never asked).
    assert wf.get(repository, row["id"])["next_requested_at"] is None
    assert repository.connection().execute("SELECT COUNT(*) FROM followup_workflow_events").fetchone()[0] \
        == events_before
    for name, params in (("get_practice_item", {"practiceItemId": item_id, "sessionId": world.session}),
                         ("open_queue_item", {"practiceItemId": item_id}),
                         ("get_probe_contract", {"practiceItemId": item_id, "sessionId": world.session})):
        _refused(world.ctx, name, params, origin, identity.GENERATED_PROBE_RESERVED)
    _refused(world.ctx, "submit_attempt", {
        "sessionId": world.session, "practiceItemId": item_id, "answerMd": "x", "attemptType": "diagnostic_probe",
        "probePresentationId": row["presentation_id"]}, origin, "validation_error")
    assert identity.closed_probe_ids(repository) == frozenset()


# -- the cap boundary (G10) ----------------------------------------------------------------------------------------


def _probe_world(tmp_path, monkeypatch, *, config: str = ""):
    from learnloop.db.repositories import Repository
    from learnloop.diagnosis.probe_episodes import enter_episode
    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.loader import load_vault

    from tests.helpers import admit_probe_instrument_card, append_config_toml, create_basic_vault, set_algorithm_version

    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    set_algorithm_version(paths, TAG)
    # The opening episode this world enters is served (placement otherwise ignores an unanswered one).
    append_config_toml(paths.root, "\n[placement]\ninitial_probes = true\n" + config)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository)
    loaded = load_vault(paths.root)
    sync_vault_state(loaded, repository)
    episode = enter_episode(loaded, repository, "lo_svd_definition")
    assert episode.status == "in_progress"
    monkeypatch.setattr("learnloop_sidecar.handlers.practice.ready_grading_provider",
                        lambda _vault, override=None: ("test", SimpleNamespace(ready=True), object()))
    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    return paths, repository, ctx


def test_g10_a_phone_admission_is_one_transaction_with_its_cap_count(tmp_path, monkeypatch):
    """The host's two workers act for one device at once: the admission on the RPC worker (here), an answer on the job
    worker (a write from another connection). Between the admission's cap count and its commit no answer can commit,
    so the count it read is the count at its commit, and the cap can't be passed by the interleaving."""

    import learnloop_sidecar.handlers.practice as practice

    paths, repository, ctx = _probe_world(tmp_path, monkeypatch)
    session_id = _call(ctx, "start_session", {"availableMinutes": 60}, PHONE)["sessionId"]
    real = practice.probe_serving_block_reason
    seen: list[str] = []

    def a_concurrent_answer_tries_to_commit(*args, **kwargs):
        reason = real(*args, **kwargs)

        def answer() -> None:
            connection = sqlite3.connect(paths.sqlite_path, timeout=0.2)
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.rollback()
                seen.append("committed_inside")
            except sqlite3.OperationalError as locked:
                seen.append(f"blocked: {locked}")
            finally:
                connection.close()

        worker = threading.Thread(target=answer)
        worker.start()
        worker.join()
        return reason

    monkeypatch.setattr(practice, "probe_serving_block_reason", a_concurrent_answer_tries_to_commit)
    contract = _call(ctx, "get_probe_contract", {"practiceItemId": "pi_svd_define_001", "sessionId": session_id}, PHONE)
    assert contract["active"] is True, contract
    assert seen and seen[0].startswith("blocked") and "locked" in seen[0]
    # The desktop is serial and keeps its own path: no transaction is held around its admission.
    seen.clear()
    desktop = SidecarContext()
    desktop.load_secondary(paths.root)
    generation = int(repository.fetch_session(session_id).get("owner_generation") or 0)
    _call(desktop, "adopt_session", {"sessionId": session_id, "expectedGeneration": generation})
    _call(desktop, "get_probe_contract", {"practiceItemId": "pi_svd_define_001", "sessionId": session_id})
    assert seen == ["committed_inside"]


def test_g10_at_the_cap_the_phones_next_admission_is_refused(tmp_path, monkeypatch):
    """With the session's qualifying-observation cap spent by a phone probe answer, the phone's next admission is
    refused ``session_cap_reached``, exactly as the desktop's."""

    paths, repository, ctx = _probe_world(
        tmp_path, monkeypatch,
        config="\n[voi_stopping]\nenabled = false\n\n[probe.episode]\nsession_qualifying_observation_cap = 1\n")
    session_id = _call(ctx, "start_session", {"availableMinutes": 60}, PHONE)["sessionId"]
    first = _call(ctx, "get_probe_contract", {"practiceItemId": "pi_svd_define_001", "sessionId": session_id}, PHONE)
    assert first["active"] is True, first
    # The phone's answer qualifies (recorded as the probe redesign's own tests record one, on this session).
    from tests.test_probe_orchestration_remainder import _submit

    vault, _ = ctx.require_vault()
    _submit(vault, repository, score=4, attempt_type="diagnostic_probe", presentation_id=first["presentationId"],
            session_id=session_id)
    assert repository.qualifying_probe_observation_count_for_session(session_id) == 1
    again = _call(ctx, "get_probe_contract", {"practiceItemId": "pi_svd_define_001", "sessionId": session_id}, PHONE)
    assert again["active"] is False and again["reason"] == "session_cap_reached"
    assert repository.qualifying_probe_observation_count_for_session(session_id) == 1


# -- the plan: the desktop's Next past a probe the phone served -------------------------------------------------------


def test_the_desktops_serving_next_moves_past_a_probe_the_phone_served_and_abandons_it(plan_world):
    """The phone served a single-use question at its plan step and the learner went to the desktop: the desktop's door
    refuses it, so its Next must not be stranded on it. It is abandoned (closed, what it held released) and the plan's
    reconcile displaces it; the desktop's step is the next one."""

    from tests.test_mobile_v2_plan import _call as desktop_call, _desktop, _next

    phone, _host, repository, paths = plan_world
    session_id = phone.start()["sessionId"]
    first = _next(phone, session_id, "v3_next_1")["step"]
    assert first["kind"] == "item"
    served = first["practiceItemId"]
    # That item is a generated probe, burned at the phone's serve (as the phone's door burns one).
    identity.register(repository, practice_item_id=served, revision="rev", source="workflow")
    assert identity.claim_serve(repository, served, surface=PHONE_SURFACE, presentation_id=None).granted
    ctx = _desktop(paths.root)
    generation = int(repository.fetch_session(session_id).get("owner_generation") or 0)
    desktop_call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": generation})
    step = desktop_call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert step is None or step.get("practiceItemId") != served
    assert served in identity.retired_probe_ids(repository)
    planned = [item for block in desktop_call(ctx, "get_daily_plan", {"sessionId": session_id})["plan"]["blocks"]
               for item in block["items"] if item["practiceItemId"] == served]
    assert all(item["state"] != "planned" for item in planned)


def test_a_desktop_serving_next_with_no_phone_burn_abandons_nothing(plan_world):
    from tests.test_mobile_v2_plan import _call as desktop_call, _desktop

    _phone, _host, repository, paths = plan_world
    ctx = _desktop(paths.root)
    session_id = desktop_call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    first = desktop_call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    again = desktop_call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert first["practiceItemId"] == again["practiceItemId"]  # resumed, as before
    assert identity.retired_probe_ids(repository) == frozenset()
