"""Adaptive difficulty AD1: the reopened F11, fix round 3 (orchestrator)
(docs/reviews/adaptive-difficulty-ad1-codex-review.md, "Fix round 3").

The final Codex verify reopened F11: the held-out check of the frozen
identities ran once before the whole forecaster pair, so a source marked held
out while the first request ran still reached the next request, and a retry
after ``AIOutputTruncated`` still sent it. Every AD request now passes one
pre-send guard (``learnloop.adaptive_difficulty.sending``) that reads the
predicate afresh before each attempt and each physical request.

Each test but the control failed on da8c3f611 for the reason its docstring
names. Fakes only: no network, no paid call.
"""

from __future__ import annotations

from learnloop.ai.errors import AIOutputTruncated
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import AuditDecider, ForecastLLM, ad_plan_vault, ad_receipts, rows
from tests.test_ad1_codex_rereview_fixes import SENTINEL, _exercise, _hold_out, _served_with_history, _set_fields


class _HoldingOutLLM(ForecastLLM):
    """An LLM whose first request marks ``spans`` held out while it runs (then answers or truncates)."""

    def __init__(self, monkeypatch, spans, *, truncate: bool = False, **kwargs):
        super().__init__(**kwargs)
        self._monkeypatch, self._spans, self._truncate = monkeypatch, tuple(spans), truncate

    def complete(self, request):
        first = not self.prompts
        if first:
            _hold_out(self._monkeypatch, *self._spans)
        if first and self._truncate:
            self.prompts.append(request.prompt)
            raise AIOutputTruncated("finish_reason = length")
        return super().complete(request)


class _HoldingOutDecider(AuditDecider):
    """A Decider that marks ``spans`` held out while its request runs, or just before it is sent."""

    def __init__(self, monkeypatch, spans, *, before_send: bool = False, **kwargs):
        super().__init__(**kwargs)
        self._monkeypatch, self._spans, self._before_send = monkeypatch, tuple(spans), before_send

    def decide(self, state, questions, *, purpose, timeout_seconds=None):
        if self._before_send:
            _hold_out(self._monkeypatch, *self._spans)
            return super().decide(state, questions, purpose=purpose, timeout_seconds=timeout_seconds)
        result = super().decide(state, questions, purpose=purpose, timeout_seconds=timeout_seconds)
        _hold_out(self._monkeypatch, *self._spans)
        return result


def _forecast(paths, step, llm, decider):
    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation

    return {outcome.forecaster: outcome for outcome in forecast_presentation(
        load_vault(paths.root), Repository(paths.sqlite_path), step["presentation_id"],
        clients=Clients(llm=llm, decider=decider))}


def _model_calls(paths, owner_kind):
    return rows(paths.sqlite_path, "SELECT * FROM model_call_receipts WHERE owner_kind = ? AND parent_call_id IS NULL "
                                   "ORDER BY started_at, rowid", (owner_kind,))


def _judgments(paths, task):
    return rows(paths.sqlite_path, "SELECT * FROM judgment_ledger WHERE task = ? ORDER BY rowid", (task,))


# -- the verify's two reproductions -----------------------------------------------------------


def test_a_source_held_out_during_the_llm_request_refuses_the_decider_request(tmp_path, monkeypatch):
    """F11 reopened: protection was checked once before the pair, so the
    Decider request after an LLM request during which the history source was
    marked held out still carried the sentinel, and both outcomes were
    ``ok``. Now the Decider request is refused, the LLM's answer (which
    returned after the mark) is not recorded, and the request already sent
    keeps its model-call receipt."""

    paths, step = _served_with_history(tmp_path)
    llm = _HoldingOutLLM(monkeypatch, ["hist"], p_correct=0.4)
    decider = AuditDecider(p_yes=0.6)
    outcomes = _forecast(paths, step, llm, decider)
    assert len(llm.prompts) == 1 and SENTINEL in llm.prompts[0], "sent before the mark: legitimately"
    assert decider.calls == []
    assert {name: outcome.status for name, outcome in outcomes.items()} == {
        "llm_v3:llm": "protected", "llm_v3:decider": "protected"}
    assert [row for row in ad_receipts(paths.sqlite_path) if row["forecaster"].startswith("llm_v3")] == []
    assert _judgments(paths, "ad_item_forecast") == []
    assert len(_model_calls(paths, "ad_item_forecast")) == 1, "the sent request keeps its accounting"


def test_a_source_held_out_inside_a_truncated_attempt_refuses_the_retry(tmp_path, monkeypatch):
    """F11 reopened: the LLM's first attempt marks the source held out and
    raises ``AIOutputTruncated``; the permitted retry used to send the
    sentinel again, and the Decider after it. Both are now refused."""

    paths, step = _served_with_history(tmp_path)
    llm = _HoldingOutLLM(monkeypatch, ["hist"], truncate=True, p_correct=0.4)
    decider = AuditDecider(p_yes=0.6)
    outcomes = _forecast(paths, step, llm, decider)
    assert len(llm.prompts) == 1, "the truncation retry was refused"
    assert decider.calls == []
    assert {outcome.status for outcome in outcomes.values()} == {"protected"}
    assert [row for row in ad_receipts(paths.sqlite_path) if row["forecaster"].startswith("llm_v3")] == []
    calls = _model_calls(paths, "ad_item_forecast")
    assert [row["status"] for row in calls] == ["truncated"], "the truncated attempt keeps its accounting"


def test_a_source_held_out_just_before_the_physical_request_is_refused_by_the_request_gate(tmp_path, monkeypatch):
    """The guard is also the context's request gate: a mark that lands after
    the Decider request was admitted but before the transport sends it
    refuses that physical request (on da8c3f611 it was sent)."""

    paths, step = _served_with_history(tmp_path)
    llm = ForecastLLM(p_correct=0.4)
    decider = _HoldingOutDecider(monkeypatch, ["hist"], before_send=True, p_yes=0.6)
    outcomes = _forecast(paths, step, llm, decider)
    assert decider.calls == [], "the physical request never left"
    assert outcomes["llm_v3:decider"].status == "protected"
    assert outcomes["llm_v3:llm"].status == "ok", "the LLM forecast ran while nothing was protected"
    assert [row["forecaster"] for row in ad_receipts(paths.sqlite_path)
            if row["forecaster"].startswith("llm_v3")] == ["llm_v3:llm"]


# -- the feature audit's fallback ------------------------------------------------------------


def _audit_vault(tmp_path, config: str = ""):
    paths = ad_plan_vault(tmp_path, config=config)
    _set_fields(paths, "pi_m1a", prompt=f"{SENTINEL}: an exam question.", canonical_exercise=_exercise("audit"))
    return paths


def test_a_revision_held_out_during_the_decider_request_refuses_the_llm_fallback(tmp_path, monkeypatch):
    """The same pattern in the feature audit: the revision's unit is marked
    held out while the Decider request runs (which leaves ``complexity``
    tied). The LLM fallback used to be sent the stem anyway, and both
    judges' answers were ledgered; now the fallback is refused and nothing
    built on either answer is recorded."""

    from learnloop.adaptive_difficulty.feature_audit import audit_revision

    paths = _audit_vault(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    tie = {"0": 0.3, "1": 0.3, "2": 0.2, "3": 0.1, "4": 0.1}
    decider = _HoldingOutDecider(monkeypatch, ["audit"], distributions={"complexity": tie})
    llm = ForecastLLM(audit={"complexity": "2"})
    outcome = audit_revision(vault, repository, vault.practice_items["pi_m1a"], decider_factory=lambda: decider,
                             llm_client=llm)
    assert len(decider.calls) == 1 and llm.prompts == []
    assert outcome.status == "protected" and outcome.answered == {}
    assert _judgments(paths, "ad_feature_audit") == []
    assert len(_model_calls(paths, "ad_feature_audit")) == 1, "the sent Decider request keeps its accounting"


def test_a_revision_held_out_inside_a_truncated_fallback_attempt_refuses_the_retry(tmp_path, monkeypatch):
    """The fallback's own retry: its first attempt marks the revision held
    out and truncates; the retry used to send the stem again and its answer
    was ledgered."""

    from learnloop.adaptive_difficulty.feature_audit import VOCABULARY, audit_revision

    paths = _audit_vault(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    llm = _HoldingOutLLM(monkeypatch, ["audit"], truncate=True,
                         audit={"complexity": "1", "transfer": "near", "scaffolding": "cue",
                                "span": "single_step", "response": "short_constructed"})
    outcome = audit_revision(vault, repository, vault.practice_items["pi_m1a"],
                             decider_factory=lambda: AuditDecider(error=RuntimeError("down")), llm_client=llm)
    assert len(llm.prompts) == 1, "the truncation retry was refused"
    assert outcome.status == "protected" and outcome.llm_status == "protected" and outcome.answered == {}
    ledger = _judgments(paths, "ad_feature_audit")
    assert [row["judge"] for row in ledger] == ["decider"] * 5, "only the Decider's failure, recorded before"
    assert not any(row["verdict"] in VOCABULARY[row["right_id"]] for row in ledger)


# -- the backfill ---------------------------------------------------------------------------


def test_a_unit_held_out_while_the_backfill_runs_refuses_its_later_forecasts(tmp_path, monkeypatch):
    """The backfill computes its predicate once and handed it to every
    forecast, which reused it: items whose unit was marked held out during
    the run were still sent. Each forecast now asks today's predicate."""

    from learnloop.adaptive_difficulty.backfill import backfill
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path)
    for item_id in ("pi_m1b", "pi_m1c"):
        _set_fields(paths, item_id, prompt=f"{SENTINEL} {item_id}", canonical_exercise=_exercise(item_id))
    llm = _HoldingOutLLM(monkeypatch, ["pi_m1b", "pi_m1c"], p_correct=0.5)
    result = backfill(load_vault(paths.root), Repository(paths.sqlite_path), audit=False, llm_v1=True,
                      reading=False, dry_run=False, clients=Clients(llm=llm))
    by_status = result["llm_v1"]["by_status"]
    assert set(by_status) == {"ok", "protected"} and by_status["protected"] == 2
    assert len(llm.prompts) == by_status["ok"] and not any(SENTINEL in prompt for prompt in llm.prompts)


# -- the control ----------------------------------------------------------------------------


def test_with_nothing_protected_the_pair_is_unchanged(tmp_path, monkeypatch):
    """Control (passes before and after): the predicate is read again before
    each request, and with nothing protected (protection unchanged mid-pair; an
    unrelated span held out mid-pair now expires the pair, the AD23 redesign's
    E2: tests/test_ad_epoch.py) both forecasts are sent exactly and recorded."""

    paths, step = _served_with_history(tmp_path)
    llm = _HoldingOutLLM(monkeypatch, [], p_correct=0.4)
    decider = AuditDecider(p_yes=0.6)
    outcomes = _forecast(paths, step, llm, decider)
    assert {name: (outcome.status, outcome.p) for name, outcome in outcomes.items()} == {
        "llm_v3:llm": ("ok", 0.4), "llm_v3:decider": ("ok", 0.6)}
    assert len(llm.prompts) == 1 and len(decider.calls) == 1
    assert SENTINEL in llm.prompts[0] and SENTINEL in decider.calls[0]["body"]
    receipts = [row for row in ad_receipts(paths.sqlite_path) if row["forecaster"].startswith("llm_v3")]
    assert sorted((row["forecaster"], row["status"]) for row in receipts) == [
        ("llm_v3:decider", "ok"), ("llm_v3:llm", "ok")]
    assert len(_judgments(paths, "ad_item_forecast")) == 2
