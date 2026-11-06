"""The contract between the phone's PWA and the host's allowlist (mobile v2 §5.2, §7.2).

* **Method names.** ``retryPolicy.json`` and ``phoneMethods.ts`` are rendered from ``ALLOWLIST``
  (:mod:`learnloop_mobile.client_contract`); a committed copy that differs fails here. Rewrite
  them with ``LEARNLOOP_UPDATE_PHONE_CONTRACT=1``.
* **Parameter shapes.** ``apps/learnloop-mobile/contract/<method>.json`` holds every request
  the phone's wrappers send, recorded by ``src/api/contract.test.ts`` from the wrappers
  themselves. Each goes through the host's own checks: the envelope, the allowlist, the
  constraints, then the method's ``ParamsModel`` (``extra="forbid"``), as ``/rpc`` does.
* **Result shapes.** Each file's ``reads`` names the reply fields the phone's screens use.
  A journey through the real host on a fresh vault asserts every reply carries them.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
from typing import Any

import pytest

from learnloop_mobile import client_contract
from learnloop_mobile.allowlist import ALLOWLIST, check_parameters, validate_envelope

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "learnloop-mobile"
CONTRACT_DIR = APP / "contract"
PHONE_TS = APP / "src" / "api" / "phone.ts"


def _contracts() -> dict[str, dict[str, Any]]:
    return {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in sorted(CONTRACT_DIR.glob("*.json"))}


def _phone_ts_methods() -> set[str]:
    """Every method name ``phone.ts`` passes to ``call`` or ``runLong``."""

    source = PHONE_TS.read_text(encoding="utf-8")
    return set(re.findall(r"\b(?:call|runLong)(?:<[^()]*?>)?\(\s*\"([a-z_.]+)\"", source))


# -- method names ------------------------------------------------------------------


def test_the_generated_client_files_are_the_allowlists():
    if os.environ.get("LEARNLOOP_UPDATE_PHONE_CONTRACT") == "1":
        client_contract.write(ROOT)
    for name, content in client_contract.rendered().items():
        path = ROOT / client_contract.CLIENT_API_DIR / name
        assert path.read_text(encoding="utf-8") == content, (
            f"{path.relative_to(ROOT)} is not what the allowlist renders; rerun with LEARNLOOP_UPDATE_PHONE_CONTRACT=1"
        )


def test_the_generated_list_names_every_allowlisted_method_and_the_digest():
    text = client_contract.render_phone_methods()
    from learnloop_mobile.allowlist import allowlist_digest

    assert f'ALLOWLIST_DIGEST = "{allowlist_digest()}"' in text
    listed = re.search(r"PHONE_METHODS = \[(.*?)\] as const", text, re.S)
    assert listed is not None
    assert set(re.findall(r'"([a-z_.]+)"', listed.group(1))) == set(ALLOWLIST)


def test_phone_ts_names_only_allowlisted_methods():
    named = _phone_ts_methods()
    assert named, "the phone's wrappers name no method: the pattern above no longer reads phone.ts"
    assert named <= set(ALLOWLIST), sorted(named - set(ALLOWLIST))


# -- parameter shapes ----------------------------------------------------------------


def test_every_method_the_phone_names_has_recorded_requests():
    contracts = _contracts()
    assert set(contracts) == _phone_ts_methods()
    for name, contract in contracts.items():
        assert contract["method"] == name
        assert contract["requests"], name
        assert all(request["envelope"]["method"] == name for request in contract["requests"])
        assert isinstance(contract["reads"], list), name


def test_every_recorded_request_passes_the_hosts_own_checks():
    import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
    from learnloop_sidecar.registry import METHOD_REGISTRY

    for name, contract in _contracts().items():
        method = ALLOWLIST[name]
        for request in contract["requests"]:
            envelope = validate_envelope(request["envelope"])
            params = envelope.get("params", {})
            check_parameters(method, params)
            # What runtime.validate does before any dispatch: the method's own model, extra="forbid".
            validated = METHOD_REGISTRY[name].params_model.model_validate(dict(params)).model_dump(mode="json")
            if method.kind == "long":
                assert envelope.get("request_id"), (name, request["wrapper"])
                if name in {"submit_attempt", "submit_dont_know"}:
                    assert envelope["request_id"] == str(validated["submission_id"]).strip()
            else:
                assert "request_id" not in envelope, (name, request["wrapper"])


def test_a_renamed_field_fails_the_model_not_the_phone():
    """The point of the check above: a field the model no longer has is refused here."""

    import learnloop_sidecar.handlers  # noqa: F401
    from pydantic import ValidationError

    from learnloop_sidecar.registry import METHOD_REGISTRY

    request = _contracts()["get_session"]["requests"][0]["envelope"]
    with pytest.raises(ValidationError):
        METHOD_REGISTRY["get_session"].params_model.model_validate({**request["params"], "sessionIdentifier": "s"})


# -- result shapes ---------------------------------------------------------------------


def _has(value: Any, path: str) -> bool:
    """``a.b``, and ``a[].b`` for every element of the list ``a`` (at least one)."""

    head, _, rest = path.partition(".")
    many = head.endswith("[]")
    key = head[:-2] if many else head
    if not isinstance(value, dict) or key not in value:
        return False
    found = value[key]
    if not rest:
        return not many or isinstance(found, list)
    if many:
        return isinstance(found, list) and bool(found) and all(_has(element, rest) for element in found)
    return _has(found, rest)


def test_the_path_reader_reads_lists_and_absent_keys():
    reply = {"sections": [{"items": [{"id": 1}]}], "nothing": None}
    assert _has(reply, "sections[].items[].id")
    assert _has(reply, "nothing")
    assert not _has(reply, "sections[].items[].title")
    assert not _has({"sections": []}, "sections[].items")


@pytest.fixture
def host_world(tmp_path, monkeypatch):
    pytest.importorskip("starlette")
    from starlette.testclient import TestClient

    from learnloop_mobile.host import create_app
    from tests.mobile_host_helpers import CountingGrader, HOSTNAME, Phone, config_for, install_grader, pair, seeded_vault

    paths, repository = seeded_vault(tmp_path / "vault")
    install_grader(monkeypatch, CountingGrader())
    # The contest's regrade finds no grader (it keeps the reason and asks for review): no model is asked.
    import learnloop_sidecar.handlers.ai_providers as providers
    from tests.mobile_host_helpers import DownRuntime

    monkeypatch.setattr(providers, "ready_grading_provider", lambda vault, override=None: ("fake", DownRuntime(), None))
    first, second = pair(repository), pair(repository, label="Other phone")
    app = create_app(config_for(paths.root))
    with TestClient(app, base_url=f"https://{HOSTNAME}") as client:
        yield Phone(client, first), Phone(client, second), repository


def test_every_reply_carries_what_the_phone_reads(host_world):
    """One journey through the real host, on a fresh vault, with the fake grader (§7.2)."""

    phone, other, repository = host_world
    contracts = _contracts()
    replies: dict[str, Any] = {}

    def rpc(name: str, params: dict, *, request_id: str | None = None, on: Any = phone) -> Any:
        replies[name] = on.rpc(name, params, request_id=request_id)
        return replies[name]

    session = rpc("start_session", {"availableMinutes": 15})
    session_id = session["sessionId"]
    rpc("get_session", {"sessionId": session_id})
    queue = rpc("get_today_queue", {"sessionId": session_id, "limit": 20, "availableMinutes": 15})
    rows = [row for section in queue["sections"] for row in section["items"]]
    first, second = rows[0], rows[1]
    rpc("get_practice_item", {"practiceItemId": first["practiceItemId"], "sessionId": session_id})
    rpc("get_probe_contract", {"practiceItemId": first["practiceItemId"], "sessionId": session_id})
    rpc("save_practice_draft", {"sessionId": session_id, "practiceItemId": first["practiceItemId"], "answerMd": "draft",
                                "submissionId": "sub_contract_1", "schedulerCandidateId": first["schedulerCandidateId"]})
    result = rpc("submit_attempt", {
        "sessionId": session_id, "practiceItemId": first["practiceItemId"], "answerMd": "an answer",
        "attemptType": "independent_attempt", "submissionId": "sub_contract_1",
        "schedulerCandidateId": first["schedulerCandidateId"],
    }, request_id="sub_contract_1")
    attempt_id = result["attemptId"]
    rpc("acknowledge_practice_submission", {"sessionId": session_id, "practiceItemId": first["practiceItemId"],
                                            "submissionId": "sub_contract_1"})
    rpc("get_feedback", {"attemptId": attempt_id, "recordOpen": True})
    rpc("get_grading_clarification", {"attemptId": attempt_id})
    rpc("diagnosis_status", {"attemptId": attempt_id})
    # Mobile v2 V2: feedback parity, the plan (off on this vault: each reply says so) and the router's account.
    rpc("record_answer_display", {"attemptId": attempt_id, "displayId": "display_contract_1"})
    rpc("followup_status", {"attemptId": attempt_id})
    rpc("followup_continue_without", {"attemptId": attempt_id})
    rpc("followup_show_anyway", {"attemptId": attempt_id})
    rpc("record_hypothesis_exposure", {"attemptId": attempt_id, "surface": "marks_feedback", "hypothesisVersionIds": [],
                                       "shownAt": "2026-11-06T12:00:00.000Z"})
    rpc("router_objective_explain", {"decisionId": "no_such_decision"})
    rpc("trigger_regrade", {"attemptId": attempt_id, "learnerReason": "The other convention.", "contestId": "contest_c1"},
        request_id="contest_c1")
    rpc("get_daily_plan", {"sessionId": session_id})
    rpc("set_plan_minutes", {"minutes": 10, "sessionId": session_id})
    rpc("plan_keep_going", {"sessionId": session_id})
    rpc("next_plan_item", {"sessionId": session_id, "serve": True}, request_id="next_contract_1")
    rpc("practice.record_hint_reveal", {"sessionId": session_id, "practiceItemId": first["practiceItemId"],
                                        "submissionId": "sub_contract_hint", "authoredIndex": 0, "answerMd": "Half",
                                        "revealedAt": "2026-11-06T12:00:00.000Z"})
    _clarify(repository, attempt_id)
    rpc("answer_grading_clarification", {"attemptId": attempt_id, "answerMd": "I meant the transpose."},
        request_id="clarify_contract_1")
    rpc("get_practice_item", {"practiceItemId": second["practiceItemId"], "sessionId": session_id})
    rpc("skip_practice_item", {"sessionId": session_id, "practiceItemId": second["practiceItemId"]})
    rpc("end_session", {"sessionId": session_id})
    # A session the other phone owns, taken over: adopt's reply is not read, only accepted.
    taken = other.rpc("start_session", {"availableMinutes": 15})
    rpc("adopt_session", {"sessionId": taken["sessionId"], "expectedGeneration": taken.get("ownerGeneration") or 0})

    unchecked = {name: contract.get("replyPinnedBy") for name, contract in contracts.items() if name not in replies}
    # Only a reply this journey cannot reach without a diagnosis model may be pinned elsewhere, by name.
    assert set(unchecked) <= {"submit_eliciting_response", "record_hypothesis_mark"}, sorted(unchecked)
    for pinned in unchecked.values():
        assert pinned and all((ROOT / path.split("::")[0]).is_file() for path in pinned), pinned
    for name, reply in replies.items():
        if name not in contracts:
            continue
        missing = [path for path in contracts[name]["reads"] if not _has(reply, path)]
        assert not missing, (name, missing, sorted(reply) if isinstance(reply, dict) else reply)


def _clarify(repository, attempt_id: str) -> None:
    """A pending clarification question, as the grader leaves one (test_sidecar_trace_and_clarification)."""

    from datetime import timedelta

    from learnloop.clock import parse_utc, utc_now_iso
    from learnloop.ids import new_ulid

    now = parse_utc(utc_now_iso())
    assert now is not None
    repository.insert_grading_clarification({
        "id": new_ulid(), "attempt_id": attempt_id, "criterion_id": "correctness", "reason": "ambiguous_notation",
        "trigger": "hedged_criterion", "question_md": "Which reading did you mean?",
        "expires_at": (now + timedelta(hours=48)).isoformat().replace("+00:00", "Z"),
    })
