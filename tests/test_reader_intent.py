"""RW1b's intent box router (spec_reader_workbench_v1 §4.2, §4.4; gates G3, G57).

* One typed choice to the Decider (route ``reader_intent``, decider-only) picks
  the action; the options are the actions that exist when the call is made.
* An empty Enter makes no model call; an unavailable, timed-out, spent-out,
  tied or failing Decider, and a day at its call cap, route to Ask.
* Every routing appends one ``judgment_ledger`` row (task ``reader_intent``,
  judge ``decider``); a speculative one's fate is a superseding row; a
  "change" is a ``learner_card`` correction.
* Speculation stops at 80% of the day's calls and with its switch off; Enter
  still routes.
* The sidecar runs a routing off the request path and answers a read with it;
  each RPC refuses with its switch off, and held-out material is never sent.
* With ``reader_intent.enabled`` off the prompt contract is the base's.

The Decider is a fake (``tests.router_model_fakes.FakeDecider``): no network.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.clock import FrozenClock
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import reader_intent as RI
from tests.helpers import NOW, append_config_toml
from tests.recap_fixtures import call, context
from types import SimpleNamespace

from tests.router_model_fakes import FakeDecider as _FakeDecider
from tests.test_reader_guidance import _setup


class FakeDecider(_FakeDecider):
    """The router's fake Decider at the Decider's listed input price."""

    settings = SimpleNamespace(price_per_million_input=0.02)


CLOCK = FrozenClock(NOW)
ON = RI.Availability(active_reading=True, workbench=True, sources=True)


def _prefer(option: str):
    return lambda refs: {ref: (0.9 if ref == option else 0.1 / max(1, len(refs) - 1)) for ref in refs}


def _route(vault, repo, text="why are the densities weighted by p?", *, decider=None, speculative=False,
           available=ON, clock=CLOCK):
    decider = decider if decider is not None else FakeDecider(choice=_prefer("ask_help_me_reason"))
    return RI.route(vault.root, vault.config, repo, text=text, quote="F_X(x) = p F_Y(x) + (1-p) F_Z(x)",
                    extraction_id="ext1", span_ids=["s1"], available=available, speculative=speculative,
                    client_factory=lambda: decider, clock=clock)


def _ledger(repo):
    with repo.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = 'reader_intent' ORDER BY created_at, rowid")]


def _receipts(repo):
    with repo.connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind = 'reader_intent' AND parent_call_id IS NULL"
        ).fetchone()[0]


# -- routing ---------------------------------------------------------------------------------------


def test_the_decider_picks_the_action_and_the_row_is_ledgered(tmp_path):
    vault, repo = _setup(tmp_path)
    decider = FakeDecider(choice=_prefer("ask_help_me_reason"))
    routing = _route(vault, repo, decider=decider)
    assert (routing.status, routing.action, routing.intention) == ("routed", "ask_help_me_reason", "understand")
    (call_,) = decider.calls
    question = call_["questions"][RI.QUESTION_NAME]
    # The options are the actions that exist, described in plain words.
    assert set(question.options) == {action.id for action in RI.available_actions(ON)}
    assert call_["state"]["learner_text"] == "why are the densities weighted by p?"
    (row,) = _ledger(repo)
    assert (row["judge"], row["verdict"], row["prompt_version"]) == ("decider", "ask_help_me_reason",
                                                                       RI.QUESTION_SET_VERSION)
    rationale = json.loads(row["rationale"])
    assert rationale["speculative"] is False and "fate" not in rationale
    # The learner's words are not kept on the ledger, only a hash.
    assert "weighted" not in json.dumps(row)
    assert _receipts(repo) == 1


def test_an_empty_enter_asks_with_no_model_call(tmp_path):
    vault, repo = _setup(tmp_path)
    decider = FakeDecider()
    routing = _route(vault, repo, "   ", decider=decider)
    assert (routing.status, routing.action) == ("empty", RI.DEFAULT_ACTION)
    assert decider.calls == [] and _ledger(repo) == [] and _receipts(repo) == 0


@pytest.mark.parametrize("error, reason", [
    (AIProviderUnavailable("Decider unavailable"), "unavailable"),
    (TimeoutError("timed out"), "timeout"),
    (SpendLimitExceeded("calls"), "refused"),
    (RuntimeError("boom"), "failed"),
])
def test_a_decider_that_cannot_answer_routes_to_ask(tmp_path, error, reason):
    vault, repo = _setup(tmp_path)
    routing = _route(vault, repo, decider=FakeDecider(error=error))
    assert (routing.status, routing.action, routing.reason) == ("fallback", RI.DEFAULT_ACTION, reason)
    (row,) = _ledger(repo)
    assert row["verdict"] == reason


def test_a_tie_names_no_action_and_routes_to_ask(tmp_path):
    vault, repo = _setup(tmp_path)
    routing = _route(vault, repo, decider=FakeDecider())  # uniform: every option ties
    assert (routing.status, routing.action, routing.reason) == ("fallback", RI.DEFAULT_ACTION, "tied")


def test_an_unready_route_is_never_a_chat_fallback(tmp_path):
    vault, repo = _setup(tmp_path)
    routing = RI.route(vault.root, vault.config, repo, text="quiz me later", quote="q", extraction_id="ext1",
                       span_ids=["s1"], available=ON, clock=CLOCK)
    assert routing.status == "fallback" and routing.reason in {"unavailable", "timeout", "failed"}
    from learnloop.ai.routing import DECIDER_TASKS

    assert "reader_intent" in DECIDER_TASKS


def test_a_day_at_the_call_cap_routes_to_ask_without_a_call(tmp_path):
    vault, repo = _setup(tmp_path)
    append_config_toml(vault.root, "\n[reader_intent]\nmax_calls_per_day = 1\n")
    from learnloop.vault.loader import load_vault

    vault = load_vault(vault.root)
    assert _route(vault, repo).status == "routed"
    decider = FakeDecider(choice=_prefer("test_me_later"))
    routing = _route(vault, repo, decider=decider)
    assert (routing.status, routing.reason, decider.calls) == ("fallback", "capped", [])


def test_speculation_stops_at_eighty_percent_and_enter_still_routes(tmp_path):
    vault, repo = _setup(tmp_path)
    append_config_toml(vault.root, "\n[reader_intent]\nmax_calls_per_day = 5\n")
    from learnloop.vault.loader import load_vault

    vault = load_vault(vault.root)
    for _ in range(4):
        assert _route(vault, repo, speculative=True).status == "routed"
    decider = FakeDecider(choice=_prefer("test_me_later"))
    stopped = _route(vault, repo, speculative=True, decider=decider)
    assert (stopped.status, stopped.reason, decider.calls) == ("not_made", "speculation_stopped", [])
    assert _route(vault, repo, decider=decider).status == "routed"  # Enter routes until the cap
    assert len(decider.calls) == 1


def test_speculation_switched_off_is_never_made(tmp_path):
    vault, repo = _setup(tmp_path)
    append_config_toml(vault.root, "\n[reader_intent]\nspeculative_enabled = false\n")
    from learnloop.vault.loader import load_vault

    vault = load_vault(vault.root)
    decider = FakeDecider(choice=_prefer("test_me_later"))
    routing = _route(vault, repo, speculative=True, decider=decider)
    assert (routing.status, routing.reason, decider.calls) == ("not_made", "speculation_off", [])
    assert _route(vault, repo, decider=decider).status == "routed"


def test_a_speculative_routings_fate_is_a_superseding_row(tmp_path):
    vault, repo = _setup(tmp_path)
    used = _route(vault, repo, speculative=True)
    discarded = _route(vault, repo, "quiz me on this later", speculative=True,
                       decider=FakeDecider(choice=_prefer("test_me_later")))
    assert json.loads(_ledger(repo)[0]["rationale"])["fate"] == "pending"
    assert RI.record_fate(repo, used.judgment_id, "used") is not None
    assert RI.record_fate(repo, used.judgment_id, "used") is None  # idempotent
    assert RI.record_fate(repo, discarded.judgment_id, "discarded") is not None
    rows = _ledger(repo)
    fates = {row["supersedes_id"]: json.loads(row["rationale"])["fate"] for row in rows if row["supersedes_id"]}
    assert fates == {used.judgment_id: "used", discarded.judgment_id: "discarded"}
    # A routing made on Enter has no fate to record.
    enter = _route(vault, repo, "explain this differently", decider=FakeDecider(choice=_prefer("alt_explanation")))
    assert RI.record_fate(repo, enter.judgment_id, "used") is None


def test_change_records_the_learners_correction(tmp_path):
    vault, repo = _setup(tmp_path)
    routing = _route(vault, repo)
    correction = RI.record_correction(repo, routing.judgment_id, "test_me_later")
    rows = _ledger(repo)
    learner = next(row for row in rows if row["id"] == correction)
    assert (learner["judge"], learner["verdict"], learner["supersedes_id"]) == (
        "learner_card", "test_me_later", routing.judgment_id)
    assert json.loads(learner["rationale"])["routed"] == "ask_help_me_reason"
    cancelled = RI.record_correction(repo, _route(vault, repo, "hmm").judgment_id, None)
    assert next(row for row in _ledger(repo) if row["id"] == cancelled)["verdict"] == "cancelled"
    with pytest.raises(ValueError):
        RI.record_correction(repo, routing.judgment_id, "compare_sources")


def test_the_options_are_only_the_actions_that_exist(tmp_path):
    vault, repo = _setup(tmp_path)
    decider = FakeDecider(choice=_prefer("test_me_later"))
    _route(vault, repo, decider=decider, available=RI.Availability())
    options = set(decider.calls[0]["questions"][RI.QUESTION_NAME].options)
    assert not options & {"next_step", "why_step", "assumptions", "reconstruct", "another_way", "work_through"}
    assert {"ask_answer_directly", "test_me_later", "highlight", "import_exercise"} <= options


def test_a_held_out_passage_is_never_routed(tmp_path):
    vault, repo = _setup(tmp_path)
    decider = FakeDecider(choice=_prefer("test_me_later"))
    routing = _route(vault, repo, decider=decider, available=RI.Availability(model=False))
    assert routing.reason == "protected" and decider.calls == [] and _ledger(repo) == []


# -- the sidecar -------------------------------------------------------------------------------------


def _ctx(root, decider):
    ctx = context(root)
    ctx.reader_intent_inline = True
    ctx.reader_intent_client_factory = lambda: decider
    return ctx


def test_the_sidecar_routes_off_the_request_path_and_records_the_outcome(tmp_path):
    vault, _repo = _setup(tmp_path)
    ctx = _ctx(vault.root, FakeDecider(choice=_prefer("test_me_later")))
    started = call(ctx, "reader.route_intent", {"extractionId": "ext1", "spanIds": ["s1"], "text": "quiz me later",
                                                "quote": "The singular value decomposition", "speculative": True})
    assert started["state"] == "done" and started["action"] == "test_me_later"
    assert started["effect"] == {"kind": "preset", "preset": "test_me_later"}
    read = call(ctx, "reader.intent_routing", {"routingId": started["routingId"]})
    assert read["action"] == "test_me_later"
    assert call(ctx, "reader.intent_outcome", {"routingId": started["routingId"], "outcome": "used"})["recorded"]
    _vault, repo = ctx.require_vault()
    with repo.connection() as connection:
        events = [json.loads(row[0]) for row in connection.execute(
            "SELECT payload_json FROM interaction_events WHERE kind IN "
            "('reader_action_invoked', 'reader_job_queued', 'reader_job_completed') ORDER BY created_at, id")]
    assert [e.get("event") or e.get("job_kind") for e in events] == ["intent_routing", "intent_routing", "intent_routed"]
    assert all(e["authority_class"] == "salience_only" for e in events)
    routed = events[-1]
    assert (routed["used"], routed["speculative"], routed["intention"]) == (True, True, "consolidate")
    assert "quiz" not in json.dumps(events)  # no learner words in the events


def test_an_empty_enter_through_the_sidecar_writes_nothing(tmp_path):
    vault, _repo = _setup(tmp_path)
    decider = FakeDecider()
    ctx = _ctx(vault.root, decider)
    done = call(ctx, "reader.route_intent", {"extractionId": "ext1", "spanIds": ["s1"], "text": ""})
    assert (done["status"], done["action"]) == ("empty", RI.DEFAULT_ACTION)
    assert decider.calls == []


def test_a_threaded_routing_is_read_back_while_pending_then_done(tmp_path):
    import threading

    vault, _repo = _setup(tmp_path)
    gate = threading.Event()
    ctx = context(vault.root)
    ctx.reader_intent_client_factory = lambda: FakeDecider(choice=_prefer("connect_it"), gate=gate)
    started = call(ctx, "reader.route_intent", {"extractionId": "ext1", "spanIds": ["s1"], "text": "link it"})
    assert started["state"] == "pending"
    assert call(ctx, "reader.intent_routing", {"routingId": started["routingId"]})["state"] == "pending"
    gate.set()
    done = call(ctx, "reader.intent_routing", {"routingId": started["routingId"], "waitMs": 1000})
    for _ in range(20):
        if done["state"] == "done":
            break
        done = call(ctx, "reader.intent_routing", {"routingId": started["routingId"], "waitMs": 1000})
    assert (done["state"], done["action"]) == ("done", "connect_it")


@pytest.mark.parametrize("toml, code", [
    ("\n[reader_intent]\nenabled = false\n", "intent_disabled"),
    ("\n[reader_inquiry]\nenabled = false\n", "inquiry_disabled"),
])
def test_the_routing_rpcs_refuse_while_switched_off(tmp_path, toml, code):
    from learnloop_sidecar.errors import SidecarError

    vault, _repo = _setup(tmp_path)
    append_config_toml(vault.root, toml)
    decider = FakeDecider(choice=_prefer("test_me_later"))
    ctx = _ctx(vault.root, decider)
    for name, params in (("reader.route_intent", {"extractionId": "ext1", "spanIds": ["s1"], "text": "quiz me"}),
                         ("reader.intent_routing", {"routingId": "rint_x"}),
                         ("reader.intent_outcome", {"routingId": "rint_x", "outcome": "used"})):
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params)
        assert caught.value.code == code
    assert decider.calls == []


def test_the_sidecar_never_sends_a_held_out_passage(tmp_path, monkeypatch):
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.handlers import reader_intent as handlers

    vault, _repo = _setup(tmp_path)
    decider = FakeDecider(choice=_prefer("test_me_later"))
    ctx = _ctx(vault.root, decider)
    monkeypatch.setattr(handlers.RG, "reading_protection",
                        lambda *_a, **_k: {"withheld": False, "held_out_span_ids": ["s1"], "message": "held out"})
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.route_intent", {"extractionId": "ext1", "spanIds": ["s1"], "text": "quiz me"})
    assert caught.value.code == "exam_material" and decider.calls == []


# -- the prompt contract (kill-switch parity) ------------------------------------------------------


def _base_contract(vault) -> dict:
    """The contract as the base built it: RW1a's fields and nothing of RW1b's."""

    inquiry = RD.inquiry_enabled(vault)
    contract = RD.reader_prompt_contract(branches=inquiry)
    contract["reader_enabled"] = RD.reader_enabled(vault)
    if inquiry:
        contract["inquiry_enabled"] = True
    return contract


@pytest.mark.parametrize("toml", [
    # RW4a's library ask, RW1c's tutor, RW4d's keep and RW7a's reading paths add their own keys; their switches
    # are off here too (G20).
    "\n[reader_intent]\nenabled = false\n[reader_active_reading]\nenabled = false\n[library_ask]\nenabled = false\n"
    "[reader_tutor]\nretrieval_enabled = false\noffers_enabled = false\n[reader_compare]\nkeep_enabled = false\n"
    "[reading_paths]\nenabled = false\n",
    "\n[reader_inquiry]\nenabled = false\n[reader_tutor]\nretrieval_enabled = false\noffers_enabled = false\n"
    "[reading_paths]\nenabled = false\n",
])
def test_switched_off_the_prompt_contract_is_the_bases(tmp_path, toml):
    from learnloop_sidecar.dto import versioned

    vault, _repo = _setup(tmp_path)
    append_config_toml(vault.root, toml)
    ctx = context(vault.root)
    loaded, _ = ctx.require_vault()
    assert call(ctx, "reader.prompt_contract", {}) == versioned(_base_contract(loaded))


def test_switched_on_the_contract_carries_the_grouped_palette(tmp_path):
    vault, _repo = _setup(tmp_path)
    contract = call(context(vault.root), "reader.prompt_contract", {})
    groups = [group["group"] for group in contract["intent"]["palette"]]
    # orient: RW4a's "what do I need first?" and RW7a's "what matters here?"
    assert groups == ["understand", "apply", "consolidate", "transfer", "orient", "mark"]
    assert contract["intent"]["speculateAfterMs"] == 600 and contract["intent"]["speculative"] is True
    assert contract["activeReading"] == {"foldBlocks": 3}


def test_the_disclosure_names_speculative_text(tmp_path):
    from learnloop.ai.disclosures import judge_route_disclosures

    vault, _repo = _setup(tmp_path)
    entry = next(e for e in judge_route_disclosures(vault.config) if e["route"] == "reader_intent")
    assert entry["judge"] == "decider" and "before you press Enter" in entry["disclosure"]
    assert "speculative_enabled" in entry["disclosure"]


def test_a_later_day_counts_its_own_calls(tmp_path):
    vault, repo = _setup(tmp_path)
    _route(vault, repo)
    # The allowance is reserved on the routing's clock; the day is a UTC day.
    assert RI.calls_today(repo, clock=CLOCK) == 1
    assert RI.calls_today(repo, clock=FrozenClock(NOW + timedelta(days=1))) == 0


def test_the_report_counts_used_routings_and_corrections_on_them_only(tmp_path):
    from learnloop.reader.reader_report import build_reader_report

    vault, _repo = _setup(tmp_path)
    ctx = _ctx(vault.root, FakeDecider(choice=_prefer("test_me_later")))
    used = call(ctx, "reader.route_intent", {"extractionId": "ext1", "spanIds": ["s1"], "text": "quiz me",
                                             "speculative": True})
    dropped = call(ctx, "reader.route_intent", {"extractionId": "ext1", "spanIds": ["s1"], "text": "quiz",
                                                "speculative": True})
    call(ctx, "reader.intent_outcome", {"routingId": used["routingId"], "outcome": "used"})
    call(ctx, "reader.intent_outcome", {"routingId": used["routingId"], "outcome": "corrected",
                                        "action": "help_me_remember"})
    call(ctx, "reader.intent_outcome", {"routingId": dropped["routingId"], "outcome": "discarded"})
    call(ctx, "reader.intent_outcome", {"routingId": dropped["routingId"], "outcome": "corrected"})
    _v, repo = ctx.require_vault()
    report = build_reader_report(repo.sqlite_path)["intent"]
    assert (report["routings"], report["speculative"], report["used"], report["discarded"]) == (2, 2, 1, 1)
    assert report["corrected"] == {"count": 1, "of": 1, "share": 1.0}
