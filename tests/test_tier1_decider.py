"""Tier 1, the Decider migration (owner decision 2026-10-13): fakes only, no network.

Each moved judgment: the Decider decides (the argmax of its distribution, not
its separate choice field), the LLM runs only when the Decider is unavailable,
refused for spend or failing, and the judgment's switch restores the LLM path.
The facet span-support check is in ``test_facet_span_support``, the agreement
report in ``test_decider_agreement``; both use the doubles below.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from learnloop.ai.decisions import ChoiceAnswer, ChoiceQuestion, DecisionResult
from learnloop.ai.errors import AIProviderUnavailable
from learnloop.config.schema import LearnLoopConfig
from learnloop.db.repositories import Repository


class Decider:
    """A Decider double whose choice field disagrees with its probability argmax."""

    model = "fake/decider"
    provider_name = "fake"
    provider_type = "decider"
    settings = SimpleNamespace(price_per_million_input=0.02)

    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls: list = []

    def decide(self, state, questions, *, purpose):
        self.calls.append((state, questions, purpose))
        if self.error:
            raise self.error
        answers = {}
        for name, question in questions.items():
            assert isinstance(question, ChoiceQuestion)
            options = list(question.options)
            probabilities = {k: (0.8 if i == len(options) - 1 else 0.2 / (len(options) - 1))
                             for i, k in enumerate(options)}
            # Deliberately disagree with the probability argmax.
            answers[name] = ChoiceAnswer(options[0], probabilities)
        return DecisionResult(answers, self.model, 100, 0, 0.000002)


class FixedDecider(Decider):
    """Answers each question with ``choices[purpose]`` (or ``choices[name]``) at 0.9."""

    def __init__(self, choices):
        super().__init__()
        self.choices = choices

    def decide(self, state, questions, *, purpose):
        self.calls.append((purpose, state))
        answers = {}
        for name, question in questions.items():
            choice = self.choices.get(purpose, self.choices.get(name, next(iter(question.options))))
            assert choice in question.options
            n = len(question.options)
            answers[name] = ChoiceAnswer(choice, {k: (1.0 if n == 1 else 0.9) if k == choice else 0.1 / (n - 1)
                                                  for k in question.options})
        return DecisionResult(answers, self.model, 100, 0, 0.000002)


def _no_decider(*_args):
    raise AIProviderUnavailable("Decider unavailable")


def _config(**switches) -> LearnLoopConfig:
    config = LearnLoopConfig()
    config.algorithms.algorithm_version = "mvp-0.20"
    for name, value in switches.items():
        setattr(config.decider_routes, name, value)
    return config


def _rows(repository, task=None):
    with repository.connection() as connection:
        query = "SELECT * FROM judgment_ledger" + (" WHERE task = ?" if task else "") + " ORDER BY rowid"
        return [dict(row) for row in connection.execute(query, (task,) if task else ())]


# -- the shared decision ----------------------------------------------------------------------------


SERVING = ["learner_gap_judge", "learner_gap_kind", "misconception_match", "diagnosis_link_judgment",
           "field_question_classification", "contamination_leak_judgment", "contamination_reveal_judgment"]


@pytest.mark.parametrize("task", [*SERVING, "facet_span_support"])
@pytest.mark.parametrize("mode", ["decider", "unavailable", "failed", "refused", "disabled"])
def test_route_decision_fallback_and_switch(tmp_path, task, mode):
    from learnloop.ai.review_spend import ReviewSpend
    from learnloop.ai.spend import SpendCaps
    from learnloop.decider_judgments import decide, log_llm

    config = _config(**{task: mode != "disabled"})
    repo = Repository(tmp_path / "state.sqlite3")
    client = Decider(RuntimeError("failed") if mode == "failed" else None)
    calls = []

    def factory():
        calls.append(True)
        return None if mode == "unavailable" else client

    spend = ReviewSpend(SpendCaps(max_calls=0)) if mode == "refused" else None
    result = decide(root=tmp_path, config=config, repository=repo, task=task,
                    state={"input": "text"}, question=ChoiceQuestion("Choose", {"yes": None, "no": None}),
                    client_factory=factory, spend=spend)
    if mode == "decider":
        # The argmax decides, not the response's choice field.
        assert (result.status, result.choice, result.probabilities) == ("ok", "no", {"yes": 0.2, "no": 0.8})
    else:
        assert result.choice is None and result.status == mode
        log_llm(repo, result, choice="yes", model="fake/llm")
    rows = _rows(repo)
    if mode == "refused":
        assert not client.calls  # refused before anything is sent
    if mode == "disabled":
        assert not calls and [row["judge"] for row in rows] == ["llm"]
    else:
        assert rows[0]["judge"] == "decider"
        assert rows[0]["verdict"] == ("no" if mode == "decider" else mode)
        assert json.loads(rows[0]["rationale"])["status"] == result.status
    assert all(row["input_hash"] == result.input_hash for row in rows)


def test_serving_judgments_wait_for_the_successor_and_the_router_is_never_tier1():
    from learnloop.decider_judgments import enabled

    config = LearnLoopConfig()
    config.algorithms.algorithm_version = "mvp-0.19"
    assert not any(enabled(config, task) for task in SERVING)
    # The span-support check is a content path: its switch acts at every version.
    assert enabled(config, "facet_span_support")
    config.algorithms.algorithm_version = "mvp-0.20"
    assert all(enabled(config, task) for task in SERVING)
    assert not enabled(config, "router_decider") and not enabled(config, "llm_probability_decider")


def test_a_cancellation_is_never_a_fallback(tmp_path):
    from learnloop.ai.errors import AIInterrupted
    from learnloop.decider_judgments import decide

    repo = Repository(tmp_path / "state.sqlite3")
    with pytest.raises(AIInterrupted):
        decide(root=tmp_path, config=_config(), repository=repo, task="misconception_match", state="s",
               question=ChoiceQuestion("Choose", {"yes": None, "no": None}),
               client_factory=lambda: Decider(AIInterrupted("stop")))


def test_decider_receipt_and_spend_ignore_llm_output_budget(tmp_path):
    from learnloop.ai.execution import model_call, output_limit, report_call_usage
    from learnloop.ai.review_spend import ReviewSpend
    from learnloop.ai.spend import SpendCaps
    from learnloop.decider_judgments import decide

    config = _config()
    config.ai.output_tokens = 1234
    repo = Repository(tmp_path / "state.sqlite")

    class Receipted(FixedDecider):
        def decide(self, state, questions, *, purpose):
            assert output_limit() is None
            with model_call(self, purpose=purpose, prompt=state):
                result = super().decide(state, questions, purpose=purpose)
                report_call_usage({"input_tokens": 100, "output_tokens": 0, "cost": 0.000002,
                                   "resolved_model": self.model})
                return result

    client = Receipted({"misconception_match": "new"})
    spend = ReviewSpend(SpendCaps(), config=config)
    result = decide(root=tmp_path, config=config, repository=repo, task="misconception_match", state="belief",
                    question=ChoiceQuestion("Same or new?", {"same": None, "new": None}),
                    client_factory=lambda: client, spend=spend)
    assert result.choice == "new"
    assert spend.budget.used.calls == 1
    assert 100 <= spend.budget.used.total_tokens < config.ai.output_tokens
    assert spend.totals["tier1_decider"].input_tokens == 100
    with repo.connection() as c:
        row = c.execute("SELECT judge, output_budget_tokens, status, cost FROM model_call_receipts").fetchone()
    assert tuple(row) == ("decider", None, "completed", 0.000002)


# -- (b) the moved routes ----------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["decider", "unavailable", "disabled"])
def test_misconception_match(tmp_path, monkeypatch, mode):
    from learnloop import decider_judgments as tier1
    from learnloop.diagnosis import misconceptions as m
    from learnloop.diagnosis.ai_contracts import MisconceptionMatch
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault
    from tests.structured_ai import StructuredClientFake

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root, load_environment=False)
    vault.config.algorithms.algorithm_version = "mvp-0.20"
    vault.config.decider_routes.misconception_match = mode != "disabled"
    repo = Repository(paths.sqlite_path)
    decider = FixedDecider({"misconception_match": "candidate"})
    monkeypatch.setattr(tier1, "client_for", (lambda *a: decider) if mode != "unavailable" else _no_decider)

    class LLM(StructuredClientFake):
        model = "fake/llm"

        def __init__(self):
            self.calls = []

        def run_misconception_match(self, context):
            self.calls.append(context)
            return MisconceptionMatch(decision="new")

    llm = LLM()
    candidates = [SimpleNamespace(id="candidate", statement="same belief")]
    result = m._match_misconception("belief", candidates, llm, learning_object_id="lo", vault=vault, repository=repo)
    assert result == ("candidate" if mode == "decider" else None)
    assert len(llm.calls) == (0 if mode == "decider" else 1)
    assert len(decider.calls) == (1 if mode == "decider" else 0)
    judges = [(row["judge"], row["verdict"]) for row in _rows(repo, "misconception_match")]
    assert judges == {"decider": [("decider", "candidate")],
                      "unavailable": [("decider", "unavailable"), ("llm", "new")],
                      "disabled": []}[mode]


def test_misconception_match_without_a_model_asks_no_decider(tmp_path, monkeypatch):
    """Replay, the diagnosis worker and simulations pass no client: no model judgment, the Decider included."""

    from learnloop import decider_judgments as tier1
    from learnloop.diagnosis import misconceptions as m
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root, load_environment=False)
    repo = Repository(paths.sqlite_path)
    monkeypatch.setattr(tier1, "client_for", lambda *a: pytest.fail("no Decider without a model client"))
    candidates = [SimpleNamespace(id="candidate", statement="Same belief!")]
    assert m._match_misconception("same belief", candidates, None, learning_object_id="lo", vault=vault,
                                  repository=repo) == "candidate"
    assert not _rows(repo, "misconception_match")


def _gap_pair(tmp_path, config, caps=None):
    from learnloop.ai.review_spend import ReviewSpend
    from learnloop.ai.spend import SpendCaps
    from learnloop.diagnosis.text_gaps.judges import TextBudget
    from learnloop.matching.kinds import Subject
    from learnloop.matching.shortlist import CandidatePair

    tmp_path.mkdir(parents=True, exist_ok=True)
    vault = SimpleNamespace(root=tmp_path, config=config)
    repo = Repository(tmp_path / "state.sqlite")
    left = Subject(kind="learner_gap", id="a", text="A", content_hash="a", view={"name": "A"})
    right = Subject(kind="learning_object", id="b", text="B", content_hash="b", view={"name": "B"})
    budget = TextBudget(ReviewSpend(caps or SpendCaps(), config=config))
    return vault, repo, [CandidatePair(left, right, score=1, rank=1, model_id="fake")], budget


@pytest.mark.parametrize("mode", ["decider", "unavailable", "failed", "disabled"])
def test_gap_pairs(tmp_path, mode):
    from learnloop.diagnosis.text_gaps.kinds import SAME_PREREQUISITE
    from learnloop.diagnosis.text_gaps.pipeline import PipelineClients, _judge_all
    from tests.text_gap_fakes import GapLLMFake, always

    vault, repo, pairs, budget = _gap_pair(tmp_path, _config(learner_gap_judge=mode != "disabled"))
    llm = GapLLMFake(decide=always("same"))
    decider = Decider(RuntimeError("down") if mode == "failed" else None)
    clients = PipelineClients(judge=lambda: llm, decider=lambda: None if mode == "unavailable" else decider)
    result = _judge_all(repo, SAME_PREREQUISITE, pairs, vault=vault, budget=budget, clients=clients,
                        decider_on=False)
    authority = result.get("authority", "llm")
    # The Decider's argmax is the last option, "unsure"; the LLM says "same".
    assert result[authority]["b"] == ("unsure" if mode == "decider" else "same")
    assert len(llm.calls) == (0 if mode == "decider" else 1)
    rows = [(row["judge"], row["verdict"]) for row in _rows(repo, SAME_PREREQUISITE.task)]
    assert rows == {"decider": [("decider", "unsure")],
                    "unavailable": [("decider", "unavailable"), ("llm", "same")],
                    "failed": [("decider", "failed"), ("llm", "same")],
                    "disabled": [("llm", "same")]}[mode]
    if mode != "disabled":
        assert result["selected_judges"]["b"] == ("decider" if mode == "decider" else "llm")


def test_gap_pairs_reuse_the_deciders_verdict_and_defer_on_a_stopped_fallback(tmp_path):
    from learnloop.ai.spend import SpendCaps
    from learnloop.diagnosis.text_gaps.kinds import SAME_PREREQUISITE
    from learnloop.diagnosis.text_gaps.pipeline import PipelineClients, ReadingDeferred, _judge_all
    from tests.text_gap_fakes import GapLLMFake, always

    vault, repo, pairs, budget = _gap_pair(tmp_path / "first", _config())
    decider = Decider()
    clients = PipelineClients(judge=lambda: GapLLMFake(decide=always("same")), decider=lambda: decider)
    _judge_all(repo, SAME_PREREQUISITE, pairs, vault=vault, budget=budget, clients=clients, decider_on=False)
    again = _judge_all(repo, SAME_PREREQUISITE, pairs, vault=vault, budget=budget, clients=clients, decider_on=False)
    assert len(decider.calls) == 1 and again["selected"]["b"] == "unsure"  # reused, never paid twice

    # The Decider refused for spend falls back; the fallback refused too stops the reading (spend=True).
    vault, repo, pairs, budget = _gap_pair(tmp_path / "second", _config(), SpendCaps(max_calls=0))
    llm, refused = GapLLMFake(decide=always("same")), Decider()
    clients = PipelineClients(judge=lambda: llm, decider=lambda: refused)
    with pytest.raises(ReadingDeferred) as stopped:
        _judge_all(repo, SAME_PREREQUISITE, pairs, vault=vault, budget=budget, clients=clients, decider_on=False)
    assert stopped.value.spend and not llm.calls and not refused.calls
    assert [(row["judge"], row["verdict"]) for row in _rows(repo, SAME_PREREQUISITE.task)] == [("decider", "refused")]


@pytest.mark.parametrize("mode", ["decider", "unavailable", "disabled"])
def test_text_gap_kind_authority(tmp_path, mode):
    from tests.test_learner_text_gaps import EIGEN_GAP, _ask, _run, _vault
    from tests.text_gap_fakes import GapLLMFake, GapTutor, word_match

    toml = "[decider_routes]\nlearner_gap_kind = false\nlearner_gap_judge = false\n" if mode == "disabled" else ""
    root, repo = _vault(tmp_path, version="mvp-0.20", toml=toml)
    answer = _ask(root, repo, GapTutor(EIGEN_GAP))
    llm = GapLLMFake(decide=word_match("eigenvalues"))
    decider = FixedDecider({"learner_gap_kind": "none", "learner_gap_judge": "different"})
    row = _run(root, repo, answer["event_id"], llm=llm, decider=None if mode == "unavailable" else decider)
    # The tutor's reading says prerequisite; the Decider says none.
    assert row["kind"] == ("none" if mode == "decider" else "prerequisite")
    assert row["chooser"] == ("decider" if mode == "decider" else "context_model")


def test_text_gap_kind_is_reused_never_paid_for_twice(tmp_path):
    """A text whose kind the Decider answered is not asked again (as the predecessor's second opinion)."""

    from learnloop.diagnosis.text_gaps import tier1
    from learnloop.diagnosis.text_gaps.judges import TextBudget
    from learnloop.diagnosis.text_gaps.pipeline import PipelineClients
    from learnloop.diagnosis.text_gaps.sources import tutor_question_text
    from learnloop.vault.loader import load_vault
    from tests.test_learner_text_gaps import EIGEN_GAP, _ask, _vault
    from tests.text_gap_fakes import GapLLMFake, GapTutor

    root, repo = _vault(tmp_path, version="mvp-0.20")
    answer = _ask(root, repo, GapTutor(EIGEN_GAP))
    vault = load_vault(root)
    text = tutor_question_text(vault, repo, answer["event_id"])
    decider = FixedDecider({"learner_gap_kind": "misconception"})
    clients = PipelineClients(judge=lambda: GapLLMFake(), reader=lambda: GapLLMFake(), decider=lambda: decider)
    first = tier1.decide_kind(vault, repo, text, TextBudget.for_text(vault), clients, {}, lambda **_: None)
    again = tier1.decide_kind(vault, repo, text, TextBudget.for_text(vault), clients, {}, lambda **_: None)
    assert first[1].choice == again[1].choice == "misconception"
    assert first[1].judgment_id == again[1].judgment_id
    assert len(decider.calls) == 1
    (row,) = [row for row in _rows(repo, "learner_gap_kind") if row["judge"] == "decider"]
    assert json.loads(row["rationale"])["probabilities"]["misconception"] == pytest.approx(0.9)


@pytest.mark.parametrize("decider_mode", ["decider", "refused"])
def test_needed_is_the_deciders_and_its_refusal_falls_back(tmp_path, decider_mode):
    from learnloop.ai.spend import SpendLimitExceeded
    from learnloop.diagnosis.text_gaps import tier1
    from learnloop.diagnosis.text_gaps.contract import NEEDED_TASK
    from learnloop.diagnosis.text_gaps.pipeline import PipelineClients
    from tests.text_gap_fakes import GapLLMFake

    vault, repo, _pairs, budget = _gap_pair(tmp_path, _config())
    decider = FixedDecider({"learner_gap_judge": "no"}) if decider_mode == "decider" else Decider(
        SpendLimitExceeded("cap"))
    llm = GapLLMFake(needed="yes")
    needed = tier1.ask_needed(vault, repo, budget, context={"item": {"prompt": "p"}, "prerequisite": {"title": "t"}},
                              learning_object_id="lo", practice_item_id="pi",
                              clients=PipelineClients(judge=lambda: llm, decider=lambda: decider))
    if decider_mode == "decider":
        assert needed["selected"]["verdict"] == "no" and needed["selected"]["judge"] == "decider" and not llm.calls
    else:
        assert needed["selected"]["verdict"] == "yes" and needed["selected"]["judge"] == "llm"
        assert needed["decider"]["status"] == "refused"
    rows = [(row["judge"], row["verdict"]) for row in _rows(repo, NEEDED_TASK)]
    assert rows == ([("decider", "no")] if decider_mode == "decider" else [("decider", "refused"), ("llm", "yes")])


def test_the_gaps_report_skips_decider_failure_rows(tmp_path):
    from learnloop.db.stores.judgments import append_judgment
    from learnloop.diagnosis.text_gaps.contract import SAME_PREREQUISITE_TASK
    from learnloop.diagnosis.text_gaps.report import _pair_agreement

    repo = Repository(tmp_path / "state.sqlite")
    with repo.atomic():
        c = repo.connection()
        for judge, verdict in (("llm", "same"), ("decider", "unavailable")):
            append_judgment(c, task=SAME_PREREQUISITE_TASK, left_kind="learner_gap", left_id="a",
                            right_kind="learning_object", right_id="b", judge=judge, judge_model="m",
                            prompt_version="v", input_hash="h", verdict=verdict)
        assert _pair_agreement(c, SAME_PREREQUISITE_TASK)["pairs_judged_by_both"] == 0


@pytest.mark.parametrize("task", ["leak", "reveal"])
@pytest.mark.parametrize("mode", ["decider", "unavailable", "disabled"])
def test_contamination(tmp_path, monkeypatch, task, mode):
    from learnloop import decider_judgments as tier1
    from learnloop.ai.spend import SpendBudget, SpendCaps
    from learnloop.ops.contamination.detectors import Candidate
    from learnloop.ops.contamination.judge import OPERATIONS, JudgeRequest, run_judgments
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault
    from tests.test_contamination_report import Judge

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root, load_environment=False)
    vault.config.algorithms.algorithm_version = "mvp-0.20"
    setattr(vault.config.decider_routes, OPERATIONS[task], mode != "disabled")
    repo = Repository(paths.sqlite_path)
    decider = FixedDecider({OPERATIONS[task]: "clean"})
    monkeypatch.setattr(tier1, "client_for", (lambda *a: decider) if mode != "unavailable" else _no_decider)
    candidate = Candidate(detector="exam_leakage" if task == "leak" else "tutor_answer_leak",
                          left_kind="question_event", left_id="a", right_kind="practice_item", right_id="b",
                          context={"first": "text", "second": "text"}, subject_text="text", target_text="text")
    request = JudgeRequest(candidate, "Judge these two texts", "v1", "hash")
    llm = Judge("contaminated")
    run_judgments(repo, [request], client=llm, budget=SpendBudget(SpendCaps(max_total_tokens=100_000)),
                  settings={"model": llm.model, "provider": "fake"}, subscription=False, price_per_million=1,
                  run_id="r", on_saved=lambda r: None, vault=vault if mode != "disabled" else None)
    rows = _rows(repo)
    decided = {row["id"]: row for row in rows}[request.judgment_id]
    positive = "leak" if task == "leak" else "reveal"
    assert (decided["judge"], decided["verdict"]) == (("decider", "clean") if mode == "decider" else ("llm", positive))
    assert len(llm.calls) == (0 if mode == "decider" else 1)
    # One Decider row per check: the verdict under the request's own id, or a failure row beside the LLM's.
    assert [row["judge"] for row in rows] == {"decider": ["decider"], "unavailable": ["decider", "llm"],
                                              "disabled": ["llm"]}[mode]
    if mode == "decider":
        with repo.connection() as c:
            owners = {tuple(row) for row in c.execute("SELECT owner_kind, owner_id FROM model_call_receipts")}
        assert owners <= {("contamination_report", "r")}


@pytest.mark.parametrize("mode", ["decider", "unavailable", "disabled", "oversized"])
def test_field_question_classification(tmp_path, monkeypatch, mode):
    from learnloop import decider_judgments as tier1
    from learnloop.ai.spend import SpendCaps, SpendEstimate
    from learnloop.field import decider as field_decider
    from learnloop.field.classification import classify_missing_questions
    from learnloop.field.decider import Classifier
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root, load_environment=False)
    vault.config.algorithms.algorithm_version = "mvp-0.20"
    vault.config.decider_routes.field_question_classification = mode != "disabled"
    if mode == "oversized":
        monkeypatch.setattr(field_decider, "MAX_QUESTIONS", 0)
    repo = Repository(paths.sqlite_path)
    event = repo.insert_question_event({"context": "library", "question_md": "What is the prerequisite?",
                                        "question_type": "prerequisite", "created_at": "2026-10-13T12:00:00Z"})
    decider = FixedDecider({"field_question_classification": "yes"})
    monkeypatch.setattr(tier1, "client_for", (lambda *a: decider) if mode != "unavailable" else _no_decider)
    classifier = Classifier(vault, repo, [{"id": "lo", "facets": []}], lambda row: json.dumps(row))
    calls = []

    def llm(row):
        calls.append(row)
        return {"question_type": "prerequisite", "lo_ids": [], "facets": []}

    def classify():
        return classify_missing_questions(
            repo, repo.question_events(), model="fake", classify=llm,
            estimate_per_question=SpendEstimate(calls=1, total_tokens=20, estimated_usd=0.001),
            caps=SpendCaps(), enabled=True, decider=classifier if mode != "disabled" else None)

    report = classify()
    assert report["status"] == "complete"
    assert len(calls) == (0 if mode == "decider" else 1)
    with repo.connection() as c:
        row = c.execute("SELECT lo_ids_json, model FROM question_classifications WHERE question_event_id = ?",
                        (event,)).fetchone()
    assert json.loads(row[0]) == (["lo"] if mode == "decider" else [])
    assert row[1] == ("fake/decider" if mode == "decider" else "fake")
    judges = [(row["judge"], row["right_id"]) for row in _rows(repo, "field_question_classification")]
    assert judges == {"decider": [("decider", "lo_ids:lo")],
                      "unavailable": [("decider", "lo_ids:lo"), ("llm", "lo_ids:lo"), ("llm", None)],
                      "disabled": [("llm", None)], "oversized": [("llm", None)]}[mode]
    counts = len(calls), len(decider.calls)
    repeated = classify()
    assert repeated["pending"] == repeated["classified"] == 0
    assert (len(calls), len(decider.calls)) == counts


@pytest.mark.parametrize("mode", ["decider", "unavailable", "disabled"])
def test_link_judgments(tmp_path, monkeypatch, mode):
    from learnloop import decider_judgments as tier1
    from learnloop.ai.review_spend import ReviewSpend, RouteInfo
    from learnloop.ai.spend import SpendCaps
    from learnloop.diagnosis.offline_review.decider_links import judge_links
    from learnloop.diagnosis.offline_review.judge import LinkJudgment, LinkVerdict

    config = _config(diagnosis_link_judgment=mode != "disabled")
    vault = SimpleNamespace(root=tmp_path, config=config)
    repo = Repository(tmp_path / "state.sqlite")
    decider = FixedDecider({"diagnosis_link_judgment": "different"})
    monkeypatch.setattr(tier1, "client_for", (lambda *a: decider) if mode != "unavailable" else _no_decider)
    spend = ReviewSpend(SpendCaps(), config=config)
    spend.routes["diagnosis_judge"] = RouteInfo("diagnosis_judge", "fake", "fake/llm", "subscription", None,
                                                "subscription")
    calls = []

    def llm():
        calls.append(True)
        return LinkJudgment(links=[LinkVerdict(label="L1", verdict="same", reason="same cause")])

    result, producers = judge_links(vault, repo, spend, "Current and earlier answers", {"L1": "earlier"}, "now", llm,
                                    llm_model="fake/llm")
    assert result.links[0].verdict == ("different" if mode == "decider" else "same")
    assert producers["L1"][0] == ("decider" if mode == "decider" else "llm")
    assert len(calls) == (0 if mode == "decider" else 1)
    rows = [(row["judge"], row["verdict"]) for row in _rows(repo, "diagnosis_link_judgment")]
    assert rows == {"decider": [("decider", "different")],
                    "unavailable": [("decider", "unavailable"), ("llm", "same")],
                    "disabled": []}[mode]


def test_only_new_authoritative_decider_links_reach_recurrence(tmp_path):
    from learnloop.db.stores.judgments import append_judgment
    from learnloop.substrate.recurrence_groups import _source_judgments

    repo = Repository(tmp_path / "state.sqlite")
    edges = []
    build = SimpleNamespace(citation_pairs={("a", "b"): [("cause_a", "cause_b", "episode_a", "episode_b")]},
                            edge=lambda *a, **kw: edges.append(kw))
    with repo.atomic():
        c = repo.connection()
        for id, metadata in (
            ("shadow", {}),
            ("old", {"decider_route": "diagnosis_link_judgment", "algorithm_version": "mvp-0.19"}),
            ("authoritative", {"decider_route": "diagnosis_link_judgment", "algorithm_version": "mvp-0.20"}),
        ):
            append_judgment(c, id=id, task="same_cause", left_kind="attempt", left_id="a",
                            right_kind="attempt", right_id="b", judge="decider", judge_model="fake",
                            prompt_version="v1", input_hash=id, verdict="same", rationale=json.dumps(metadata))
        _source_judgments(build, c)
    assert len(edges) == 1
    assert edges[0]["ref"] == "judgment:authoritative"


# -- review fixes ------------------------------------------------------------------------------------


class TiedDecider(Decider):
    """Its two first options share the top probability (and its choice field names the first)."""

    def decide(self, state, questions, *, purpose):
        self.calls.append((state, questions, purpose))
        answers = {}
        for name, question in questions.items():
            options = list(question.options)
            probabilities = {k: (0.5 if i < 2 else 0.0) for i, k in enumerate(options)}
            answers[name] = ChoiceAnswer(options[0], probabilities)
        return DecisionResult(answers, self.model, 100, 0, 0.000002)


def test_a_tied_top_option_is_no_answer_and_hands_over(tmp_path):
    """Review F8: a tie for the top probability is no clear answer; the first option never wins it."""

    from learnloop.decider_judgments import FAILURE_VERDICTS, decide, decide_many, log_llm

    repo = Repository(tmp_path / "state.sqlite3")
    question = ChoiceQuestion("Choose", {"yes": None, "no": None, "unsure": None})
    result = decide(root=tmp_path, config=_config(), repository=repo, task="misconception_match", state="s",
                    question=question, client_factory=TiedDecider)
    assert (result.status, result.choice) == ("tied", None)
    assert result.probabilities == {"yes": 0.5, "no": 0.5, "unsure": 0.0}
    log_llm(repo, result, choice="no", model="fake/llm")
    assert [(row["judge"], row["verdict"]) for row in _rows(repo)] == [("decider", "tied"), ("llm", "no")]
    assert "tied" in FAILURE_VERDICTS


def test_a_tied_batch_question_has_no_choice(tmp_path, monkeypatch):
    from learnloop import decider_judgments as tier1

    monkeypatch.setattr(tier1, "client_for", lambda *a: TiedDecider())
    repo = Repository(tmp_path / "state.sqlite3")
    decisions = tier1.decide_many(root=tmp_path, config=_config(), repository=repo,
                                  task="field_question_classification", state="s",
                                  questions={"q": ChoiceQuestion("Choose", {"yes": None, "no": None})},
                                  left_kind="question_event", left_id="e")
    assert (decisions["q"].status, decisions["q"].choice) == ("tied", None)


def test_a_tied_gap_pair_goes_to_the_llm(tmp_path):
    from learnloop.diagnosis.text_gaps.kinds import SAME_PREREQUISITE
    from learnloop.diagnosis.text_gaps.pipeline import PipelineClients, _judge_all
    from tests.text_gap_fakes import GapLLMFake, always

    vault, repo, pairs, budget = _gap_pair(tmp_path, _config())
    llm = GapLLMFake(decide=always("different"))
    clients = PipelineClients(judge=lambda: llm, decider=lambda: TiedDecider())
    result = _judge_all(repo, SAME_PREREQUISITE, pairs, vault=vault, budget=budget, clients=clients,
                        decider_on=False)
    # same / different tie: no match is made on the first option; the LLM decides.
    assert result["selected"]["b"] == "different" and result["selected_judges"]["b"] == "llm"
    assert [(row["judge"], row["verdict"]) for row in _rows(repo, SAME_PREREQUISITE.task)] == [
        ("decider", "tied"), ("llm", "different")]
