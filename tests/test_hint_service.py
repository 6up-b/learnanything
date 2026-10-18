"""Adaptive hints H2a: the hint service (spec_adaptive_hints_v1 §4.1, §4.5, §4.7, §4.8, §6.2, §7.2-7.3;
G-H7, G-H8, G-H11, G-H12).

State assembly from local reads; the options and their preconditions; the
chooser's draws and propensities (joint, conditional on a taken level, 1 for
one option, argmax 1, fallback 1, the learner's picks none); the fallback
(authored hints in order, then ``next_step``); the writer's Codex refusal
(D9); the daily spend cap; the labels and the wording lint. Fakes only.
"""

from __future__ import annotations

import json
import random

import pytest

from learnloop.db.repositories import Repository
from learnloop.hints import chooser as C
from learnloop.hints import kinds as K
from learnloop.hints import service as S
from learnloop.hints.options import build_options
from learnloop.hints.state import assemble_state
from learnloop.vault.loader import load_vault
from tests.hint_fakes import (
    HINTS,
    ITEM,
    WORK,
    ChooserFake,
    WriterFake,
    add_hypothesis,
    assists,
    hint_vault,
    judgments,
    prefer,
    receipts,
    store_map,
)

SESSION = "sess_1"


def _setup(tmp_path, *, config: str = "", with_map: bool = True, **item):
    paths = hint_vault(tmp_path, config=config, **item)
    if with_map:
        store_map(paths)
    return paths, load_vault(paths.root), Repository.attach(paths.sqlite_path)


def _request(**overrides) -> S.HintRequestV1:
    values = {"practice_item_id": ITEM, "session_id": SESSION, "submission_id": "k1", "work_md": WORK}
    values.update(overrides)
    return S.HintRequestV1(**values)


def _ask(vault, repository, *, writer=None, chooser=None, seed="seed-1", **overrides) -> S.HintResultV1:
    return S.request_hint(vault, repository, _request(**overrides), writer_client=writer or WriterFake(),
                          chooser_client_factory=(lambda: chooser) if chooser is not None else (lambda: None),
                          seed=seed)


# -- state assembly ---------------------------------------------------------------------


def test_the_state_reads_the_draft_rivals_map_and_this_attempts_hints(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    add_hypothesis(paths.sqlite_path, "h1", "Adds one to a CDF value as if it were a density")
    add_hypothesis(paths.sqlite_path, "h2", "Reads the CDF as the density")
    item = vault.practice_items[ITEM]
    state = assemble_state(vault, repository, item, session_id=SESSION, submission_id="k1", work_md=WORK)
    assert state.has_work and state.map is not None
    assert {rival.statement for rival in state.rivals} == {
        "Adds one to a CDF value as if it were a density", "Reads the CDF as the density"}
    assert state.unread == [] or set(state.unread) <= {"placement", "prediction"}
    decider = state.decider_state()
    # The Decider reads a typed summary: never the draft, the reference answer or the map's states.
    blob = json.dumps(decider)
    assert WORK.splitlines()[1] not in blob and "1/4" not in blob and "x^2" not in blob
    assert decider["work_characters"] == len(WORK) and decider["open_rivals"] == 2


def test_with_no_draft_in_the_request_the_session_checkpoints_draft_is_read(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    paths, vault, repository = _setup(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)

    def call(name, params):
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    session_id = call("start_session", {"energy": "medium"})["sessionId"]
    call("save_practice_draft", {"sessionId": session_id, "practiceItemId": ITEM, "answerMd": "F(x) = x^2",
                                 "submissionId": "k1"})
    state = assemble_state(vault, repository, vault.practice_items[ITEM], session_id=session_id,
                           submission_id="k1", work_md=None)
    assert state.work_md == "F(x) = x^2"


# -- options and preconditions -----------------------------------------------------------


def _options(vault, repository, *, work: str = WORK, **kwargs):
    state = assemble_state(vault, repository, vault.practice_items[ITEM], session_id=SESSION, submission_id="k1",
                           work_md=work)
    return state, build_options(state, request=kwargs.pop("request", "more"), **kwargs)


def test_a_hint_press_offers_levels_one_to_three_only(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    _state, options = _options(vault, repository)
    assert {option.level for option in options.options} <= {1, 2, 3}
    assert options.has("waypoint") and options.has("subgoal_plan") and options.has("localize")
    assert not options.has("continuation") and not options.has("walkthrough")


def test_preconditions_remove_what_cannot_apply(tmp_path):
    _paths, vault, repository = _setup(tmp_path, with_map=False)
    _state, options = _options(vault, repository, work="")
    assert not options.has("waypoint") and not options.has("subgoal_plan")
    assert options.excluded["waypoint@L3"] == "no_map"
    assert not options.has("localize") and options.excluded["localize@L2"] == "no_work"
    assert not options.has("error_specific")
    assert options.excluded["discriminating@L1"] == "fewer_than_two_rivals"
    assert options.excluded["worked_parallel@L3"] == "no_example"


def test_another_instance_in_the_family_offers_a_worked_parallel(tmp_path):
    from tests.approach_map_fakes import write_item

    paths = hint_vault(tmp_path, family_id="fam_cdf")
    write_item(paths, "pi_cdf_2", prompt="Y has density 3y^2 on [0, 1]. Find P(Y ≤ 1/3).", family_id="fam_cdf")
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    state, options = _options(vault, repository)
    assert options.has("worked_parallel") and state.sibling_prompt and "3y^2" in state.sibling_prompt


def test_a_taken_level_offers_only_that_levels_kinds(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    _state, options = _options(vault, repository, taken_level=4)
    assert options.ids == ["continuation@L4", "worked_chunk@L4"] and options.level_source == "learner_pick"
    _state, options = _options(vault, repository, taken_level=5)
    assert options.ids == ["walkthrough@L5"]


def test_a_hint_press_never_serves_worked_help_and_only_a_pick_takes_it(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    with pytest.raises(S.HintRequestError):
        _ask(vault, repository, taken_level=3)
    for seed in range(8):
        result = _ask(vault, repository, chooser=ChooserFake(), seed=f"s{seed}", submission_id=f"k{seed}")
        assert result.level in (1, 2, 3)


# -- the chooser: draws and propensities ---------------------------------------------------


def test_the_propensity_is_the_probability_the_option_was_drawn_with(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    fake = ChooserFake(prefer("next_step@L3", 0.6))
    result = _ask(vault, repository, chooser=fake, seed="draw-1")
    [row] = assists(_paths.sqlite_path)
    probabilities = json.loads(row["probabilities_json"])["kind_level"]
    drawn = json.loads(row["drawn_option_json"])
    expected = probabilities[drawn["option"]]
    if drawn["kind"] == "waypoint":
        horizon = json.loads(row["probabilities_json"])["horizon"]
        allowed = {key: value for key, value in horizon.items() if int(key) >= 1}
        expected *= allowed[str(drawn["horizon_index"])] / sum(allowed.values())
    assert row["propensity"] == pytest.approx(expected)
    assert result.propensity == pytest.approx(expected) and row["chooser"] == "decider"
    assert row["seed"] == "draw-1" and row["policy_version"].endswith(":sample")
    # The fake was asked one request with the two questions (a waypoint was on offer).
    assert set(fake.calls[0]["questions"]) == {"kind_level", "horizon"}
    assert fake.calls[0]["timeout_seconds"] == pytest.approx(3.0)


def test_a_seed_reproduces_the_draw():
    probabilities = {"a": 0.2, "b": 0.5, "c": 0.3}
    first = C.draw(probabilities, C._rng("same"))
    second = C.draw(probabilities, C._rng("same"))
    assert first == second
    counts = {"a": 0, "b": 0, "c": 0}
    rng = random.Random(7)
    for _ in range(3000):
        counts[C.draw(probabilities, rng)[0]] += 1
    assert counts["b"] / 3000 == pytest.approx(0.5, abs=0.05)


def test_the_joint_propensity_of_a_waypoint_includes_its_horizon(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    fake = ChooserFake(prefer("waypoint@L3", 0.999), horizon={0: 0.0, 1: 0.6, 2: 0.4, 3: 0.0})
    _ask(vault, repository, chooser=fake, seed="w-1")
    [row] = assists(_paths.sqlite_path)
    drawn = json.loads(row["drawn_option_json"])
    assert drawn["kind"] == "waypoint"  # the seeded draw (0.999 on the waypoint)
    assert drawn["horizon_index"] in (1, 2)
    p_option = json.loads(row["probabilities_json"])["kind_level"]["waypoint@L3"]
    p_horizon = {1: 0.6, 2: 0.4}[drawn["horizon_index"]]
    assert row["propensity"] == pytest.approx(p_option * p_horizon)


def test_argmax_serves_the_top_option_and_logs_one(tmp_path):
    _paths, vault, repository = _setup(tmp_path, config="[hints]\nchoice_policy = \"argmax\"\n")
    result = _ask(vault, repository, chooser=ChooserFake(prefer("localize@L2", 0.4)))
    assert (result.kind, result.level, result.propensity) == ("localize", 2, 1.0)


def test_a_taken_level_is_drawn_conditional_on_that_level(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    fake = ChooserFake(prefer("worked_chunk@L4", 0.7))
    result = _ask(vault, repository, chooser=fake, taken_level=4)
    assert list(fake.calls[0]["questions"]["kind_level"].options) == ["continuation@L4", "worked_chunk@L4"]
    [row] = assists(_paths.sqlite_path)
    assert row["level_source"] == "learner_pick" and row["level"] == 4
    assert row["propensity"] == pytest.approx({"worked_chunk": 0.7, "continuation": 0.3}[result.kind])
    assert result.labels["worked_help"] == K.WORKED_HELP_MARK


def test_a_level_with_one_option_logs_one_and_asks_nobody(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    fake = ChooserFake()
    result = _ask(vault, repository, chooser=fake, taken_level=5)
    assert fake.calls == [] and (result.kind, result.level, result.propensity) == ("walkthrough", 5, 1.0)
    [row] = assists(_paths.sqlite_path)
    assert row["chooser"] == "learner_pick" and row["level_source"] == "learner_pick"


def test_every_decider_request_is_one_hint_choice_row_with_labelled_receipts(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    _ask(vault, repository, chooser=ChooserFake(prefer("next_step@L3")))
    [ledger] = judgments(paths.sqlite_path, "hint_choice")
    [row] = assists(paths.sqlite_path)
    assert (ledger["judge"], ledger["left_kind"], ledger["left_id"]) == ("decider", "help_assist", row["id"])
    assert ledger["prompt_version"] == C.QUESTION_SET_VERSION and ledger["verdict"].endswith("@L3")
    [receipt] = receipts(paths.sqlite_path, "hint_chooser")
    assert (receipt["judge"], receipt["question_set_version"]) == ("decider", C.QUESTION_SET_VERSION)
    assert receipt["state_hash"]


# -- the fallback (G-H8) ----------------------------------------------------------------------


@pytest.mark.parametrize("case", ["disabled", "unavailable", "timeout", "error"])
def test_the_fallback_serves_authored_hints_in_order_then_the_next_step(tmp_path, case, monkeypatch):
    config = "[hints]\nchooser_enabled = false\n" if case == "disabled" else ""
    if case == "timeout":
        config = "[hints]\nchooser_timeout_seconds = 0.05\n"
    paths, vault, repository = _setup(tmp_path, config=config)
    chooser = {"disabled": ChooserFake(), "unavailable": None, "timeout": ChooserFake(delay=0.2),
               "error": ChooserFake(error=RuntimeError("bad answer"))}[case]
    served = []
    for _ in range(len(HINTS) + 1):
        result = _ask(vault, repository, chooser=chooser)
        assert result.status == S.READY and result.chooser == "fallback" and result.propensity == 1.0
        S.deliver(repository, str(result.assist_id))
        served.append((result.kind, result.authored_index))
    assert served == [("authored", 0), ("authored", 1), ("next_step", None)]
    rows = assists(paths.sqlite_path)
    reasons = {json.loads(row["contract_failures_json"])["chooser_reason"] for row in rows}
    assert reasons == {{"disabled": "chooser_disabled", "unavailable": "unavailable", "timeout": "timeout",
                        "error": "failed"}[case]}
    labels = [result.labels for result in [_ask(vault, repository, chooser=chooser)]]
    assert labels[0]["origin"] in (K.AI_WRITTEN, K.FROM_THE_ITEM)
    if case == "disabled":
        assert chooser.calls == []


def test_authored_hints_the_client_revealed_are_not_served_again(tmp_path):
    paths, vault, repository = _setup(tmp_path, config="[hints]\nchooser_enabled = false\n")
    from learnloop.hints.telemetry import record_authored_reveal

    record_authored_reveal(repository, item=vault.practice_items[ITEM], session_id=SESSION, submission_id="k1",
                           authored_index=0, work_md=WORK)
    result = _ask(vault, repository)
    assert (result.kind, result.authored_index) == ("authored", 1)
    assert result.labels["origin"] == K.FROM_THE_ITEM and result.labels["kind"] == "from the item"


# -- the writer route: Codex refused (D9), spend (G-H11) ----------------------------------------


def test_the_writer_never_runs_on_codex_and_says_why(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    chooser, writer = ChooserFake(), WriterFake(provider_type="codex_sdk")
    result = _ask(vault, repository, writer=writer, chooser=chooser)
    assert (result.kind, result.authored_index, result.reason) == ("authored", 0, "codex_refused")
    assert "Codex" in str(result.message)
    assert writer.calls == 0 and chooser.calls == []  # nothing spent on a hint that cannot be written


def test_the_unset_writer_route_resolves_to_the_active_provider_and_refuses_codex(tmp_path, monkeypatch):
    _paths, vault, repository = _setup(tmp_path, hints=[])
    monkeypatch.delenv("LEARNLOOP_HINT_MODELS", raising=False)
    from learnloop.hints.writer import WriterRoute

    route = WriterRoute(vault, repository)
    if str(route.route.profile_type) not in ("codex_sdk", "http", "http_adapter"):
        pytest.skip("the test vault's active provider is not Codex")
    assert route.problem().reason == "codex_refused"
    result = S.request_hint(vault, repository, _request(), chooser_client_factory=lambda: None)
    assert result.status == S.UNAVAILABLE and result.reason == "codex_refused" and result.hint_md is None


def test_a_capped_day_falls_back_to_authored_hints_and_says_so(tmp_path):
    _paths, vault, repository = _setup(tmp_path, config="[hints]\nmax_daily_cost_usd = 0\nprice_per_million = 1.0\n")
    writer = WriterFake(provider_type="openrouter")
    result = _ask(vault, repository, writer=writer, chooser=ChooserFake())
    assert (result.kind, result.reason) == ("authored", "capped") and writer.calls == 0


def test_an_unpriced_metered_writer_is_refused_before_sending(tmp_path):
    _paths, vault, repository = _setup(tmp_path)
    writer = WriterFake(provider_type="openrouter")
    result = _ask(vault, repository, writer=writer, chooser=ChooserFake())
    assert result.reason == "unpriced" and writer.calls == 0


def test_a_metered_writer_inside_the_cap_writes_and_its_receipt_is_counted(tmp_path):
    paths, vault, repository = _setup(tmp_path, config="[hints]\nprice_per_million = 1.0\n")
    result = _ask(vault, repository, writer=WriterFake(provider_type="openrouter"),
                  chooser=ChooserFake(prefer("next_step@L3", 0.95)))
    assert result.status == S.READY and result.labels["origin"] == K.AI_WRITTEN
    [receipt] = receipts(paths.sqlite_path, "hint_writer")
    assert json.loads(receipt["budget_json"])["practice_index"]["cost_basis"] == "metered_estimate"
    assert S.hints_envelope(vault, repository).report()["metered_usd"] > 0


def test_a_chatgpt_plan_writer_is_estimated_only(tmp_path):
    # The day's metered budget is spent: the (metered) chooser falls back, and
    # with no authored hint left the fallback's next step is written on the plan.
    paths, vault, repository = _setup(tmp_path, config="[hints]\nmax_daily_cost_usd = 0\n", hints=[])
    result = _ask(vault, repository, writer=WriterFake(provider_type="chatgpt_plan"),
                  chooser=ChooserFake(prefer("next_step@L3", 0.95)))
    # A spent metered day does not stop the plan: it is never counted against the cap.
    assert result.status == S.READY and result.kind == "next_step" and result.chooser == "fallback"
    [receipt] = receipts(paths.sqlite_path, "hint_writer")
    assert json.loads(receipt["budget_json"])["practice_index"]["cost_basis"] == "estimated_only"
    assert S.hints_envelope(vault, repository).report()["metered_usd"] == pytest.approx(0.0, abs=1e-6)


# -- labels and the wording lint (G-H12) ---------------------------------------------------------


def test_every_kind_has_the_readers_plain_words_and_worked_help_is_marked():
    expected = {
        "approach_question": "a question about your approach", "discriminating": "a question that tells apart "
        "two explanations", "localize": "where it stops holding", "waypoint": "a goal to aim for",
        "subgoal_plan": "a plan for the rest", "next_step": "the next step", "error_specific": "check this part",
        "worked_parallel": "the same move on another example", "authored": "from the item",
        "continuation": "the next part, written for you", "worked_chunk": "a worked piece, from the goal back",
        "walkthrough": "the rest, worked through",
    }
    assert {name: kind.label for name, kind in K.KINDS.items()} == expected
    assert K.KINDS["discriminating"].label_at(3) == "a check that tells them apart"
    assert K.labels_for("approach_question", 1, origin=K.AI_WRITTEN, has_work=False)["kind"] == "your first move?"
    assert K.labels_for("waypoint", 3, origin=K.AI_WRITTEN, horizon_index=1)["horizon"] == "about two steps ahead"
    for level in (4, 5):
        assert K.labels_for(K.FALLBACK_ORDER[level][0], level, origin=K.AI_WRITTEN)["worked_help"] == "worked help ◌"
    assert K.labels_for("next_step", 3, origin=K.AI_WRITTEN)["worked_help"] is None
    # Worked help says so before it is taken: the picks carry the mark and the consequence.
    assert all(pick["worked_help"] == "worked help ◌" and pick["consequence"] for pick in K.worked_help_picks())


def test_the_wording_lint_rejects_judging_words_in_every_learner_facing_string():
    from learnloop.hints import service, writer

    strings: list[str] = [kind.label for kind in K.KINDS.values()]
    strings += [kind.label_level_3 for kind in K.KINDS.values() if kind.label_level_3]
    strings += list(K.HORIZON_LABELS.values()) + list(K.NO_SEPARATING_QUESTION.values())
    strings += [K.WITHHELD_MESSAGE, K.FIRST_MOVE_LABEL, K.WORKED_HELP_MARK]
    strings += [str(pick["label"]) for pick in K.worked_help_picks()]
    strings += [str(pick["consequence"]) for pick in K.worked_help_picks()]
    strings += [service._unavailable_message(reason) for reason in (
        "codex_refused", "capped", "unpriced", "no_option", "contract_failed", "no_authored_hint_left", None)]
    for text in strings:
        lowered = text.lower()
        for phrase in K.FORBIDDEN_WORDING:
            assert phrase not in lowered, (phrase, text)
    # The lint itself catches what it names.
    assert any(phrase in "honestly, you struggle here" for phrase in K.FORBIDDEN_WORDING)
    assert writer._INSTRUCTIONS.count("never judge them") == 1


# -- the job RPCs: never on the request path; shown when delivered ---------------------------


def test_the_request_is_a_job_and_the_read_that_returns_it_shows_it(tmp_path):
    import threading

    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    paths, _vault, _repository = _setup(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)

    def call(name, params):
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    gate = threading.Event()
    ctx.hint_writer_client = WriterFake(gate=gate)
    ctx.hint_chooser_client = ChooserFake(prefer("next_step@L3", 0.95))
    session = call("start_session", {"energy": "medium"})["sessionId"]
    job = call("practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                         "answerMd": WORK})
    assert (job["state"], job["result"]) == ("pending", None)
    # The serial loop answers other requests meanwhile (a draft flush).
    call("save_practice_draft", {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK,
                                 "submissionId": "k1"})
    assert call("practice.hint_job", {"jobId": job["jobId"]})["state"] == "pending"
    gate.set()
    assert ctx.hint_jobs.get(job["jobId"]).done.wait(30)
    [row] = assists(paths.sqlite_path)
    assert row["shown"] == 0 and row["counted_by"] == "server"  # prepared, not yet delivered
    read = call("practice.hint_job", {"jobId": job["jobId"]})
    assert read["state"] == "done" and read["result"]["status"] == "ready" and read["result"]["shown"] is True
    [row] = assists(paths.sqlite_path)
    assert row["shown"] == 1 and row["shown_at"]
    again = call("practice.hint_job", {"jobId": job["jobId"]})
    assert again["result"]["assistId"] == read["result"]["assistId"]  # idempotent
    assert len(assists(paths.sqlite_path)) == 1


def test_a_malformed_request_answers_its_job_with_a_validation_error(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.registry import METHOD_REGISTRY

    paths, _vault, _repository = _setup(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.hints_inline = True

    def call(name, params):
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    session = call("start_session", {"energy": "medium"})["sessionId"]
    with pytest.raises(SidecarError) as error:
        call("practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                       "request": "feedback", "answeredAssistId": "ha_missing"})
    assert error.value.code == "validation_error"


def test_a_job_of_another_vault_is_never_delivered_after_a_switch(tmp_path):
    import threading

    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.registry import METHOD_REGISTRY

    first, _v, _r = _setup(tmp_path / "a")
    second, _v2, _r2 = _setup(tmp_path / "b")
    ctx = SidecarContext()
    ctx.load(first.root)

    def call(name, params):
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    gate = threading.Event()
    ctx.hint_writer_client = WriterFake(gate=gate)
    ctx.hint_chooser_client = ChooserFake(prefer("next_step@L3", 0.95))
    session = call("start_session", {"energy": "medium"})["sessionId"]
    job = call("practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                         "answerMd": WORK})
    ctx.load(second.root)
    gate.set()
    assert ctx.hint_jobs.get(job["jobId"]).done.wait(30)
    with pytest.raises(SidecarError) as error:
        call("practice.hint_job", {"jobId": job["jobId"]})
    assert error.value.code == "not_found"
    assert [row["shown"] for row in assists(first.sqlite_path)] == [0]
    assert assists(second.sqlite_path) == []


def test_the_writers_receipts_are_labelled(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    _ask(vault, repository, chooser=ChooserFake(prefer("next_step@L3", 0.95)))
    [receipt] = receipts(paths.sqlite_path, "hint_writer")
    from learnloop.hints.writer import PROMPT_VERSION

    assert (receipt["judge"], receipt["question_set_version"]) == ("llm", PROMPT_VERSION) and receipt["state_hash"]
