"""Interaction-only inputs: synthetic rows, temporary SQLite, no live AI."""
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from learnloop.ai.execution import model_call, report_call_usage
from learnloop.ai.spend import SpendCaps, SpendEstimate
from learnloop.db.repositories import Repository
from learnloop.field.classification import classify_missing_questions, load_cached_classifications
from learnloop.field.signals import (
    DAILY_SIGNAL_MASS_CAP, confusion_blocks_fast_track, derive_interaction_signals,
    enrich_attempts, input_hash, load_interaction_signals,
)
from learnloop.field.types import AttemptRow, ItemFeatures


def attempt(**changes):
    return replace(AttemptRow("a", ItemFeatures("item", "lo", "2026-01-01T12:00:00Z"), 1.0, 0.5), **changes)


def question(**changes):
    return dict(id="q", context="practice", question_md="Why?",
                question_type="prerequisite", facets_json='["f"]',
                created_at="2026-01-01T11:00:00Z", attempt_id="a") | changes


def derive(questions=(), attempts=(), readers=(), cache=()):
    return derive_interaction_signals(questions, readers, attempts, facet_to_lo={"f": "lo", "prereq": "lower"}, cached_classifications=cache)


def test_typed_questions_hint_depth_and_g13_pure_inputs():
    original = attempt(hints_used=2)
    rows = derive([question(seconds_into_attempt=0)], [original])
    assistance, q, hint = rows
    assert assistance.signal_type == "practice_assistance"
    assert assistance.effective_mass == 0
    assert (q.outcome, q.effective_mass, q.help_before_work) == (0, .15, True)
    assert hint.outcome == .3 and hint.effective_mass == 0
    enriched, = enrich_attempts([original], rows)
    assert enriched.help_before_work
    assert original == attempt(hints_used=2)  # frozen source record is untouched
    assert enriched.outcome == original.outcome and enriched.effective_mass == original.effective_mass


@pytest.mark.parametrize("timing,expected", [(None, False), (0, True), (.001, False), (20, False)])
def test_exact_zero_not_absence_means_before_work(timing, expected):
    signal, = derive([question(seconds_into_attempt=timing)])
    assert signal.help_before_work is expected


@pytest.mark.parametrize("kind", ["other", "verification"])
def test_curiosity_is_never_negative(kind):
    signal, = derive([question(question_type=kind, seconds_into_attempt=0)])
    assert signal.outcome is None and signal.effective_mass == 0
    assert not signal.help_before_work
    assert not confusion_blocks_fast_track([signal], lo_id="lo", as_of="2026-02-01")


def test_daily_cap_is_chronological_utc_and_per_lo():
    questions = [question(id=str(i), created_at=f"2026-01-01T1{i}:00:00Z") for i in range(4)]
    questions.append(question(id="other", facets_json='["prereq"]'))
    rows = derive(reversed(questions))
    assert sum(s.effective_mass for s in rows if s.lo_id == "lo") == pytest.approx(DAILY_SIGNAL_MASS_CAP)
    assert next(s for s in rows if s.lo_id == "lower").effective_mass == .15
    assert rows == derive(questions)
    assert derive([question(created_at="2026-01-02T01:00:00+02:00"),
                   question(id="q2", created_at="2026-01-01T23:30:00Z"),
                   question(id="q3", created_at="2026-01-02T00:00:00Z")])[-1].effective_mass == .15


def test_later_feedback_cannot_change_earlier_attempt_or_prediction():
    early = attempt()
    feedback = question(context="feedback", question_type="mechanism", created_at="2026-01-01T13:00:00Z", leak_suspected=True)
    rows = derive([feedback], [early])
    signal, = rows
    assert (signal.observed_at, signal.outcome, signal.effective_mass) == ("2026-01-01T13:00:00Z", .5, .1)
    assert enrich_attempts([early], rows) == (early,)
    future = replace(early, attempt_id="later", features=replace(early.features, observed_at="2026-01-02"))
    assert enrich_attempts([future], rows)[0].preceded_by_question


def test_prerequisite_mapping_not_item_fallback_and_leak_non_cold():
    early = attempt()
    rows = derive([question(facets_json='["prereq"]', leak_suspected=True)], [early])
    assert next(s for s in rows if s.signal_type == "prerequisite").lo_id == "lower"
    assert not enrich_attempts([early], rows)[0].features.cold
    assert derive([question(facets_json=None)], [early]) == ()


def test_cached_reader_classification_is_missing_only_and_not_backdated():
    reader = dict(id="r", kind="learner_question_asked", created_at="2026-01-01",
                  payload_json=json.dumps({"question_md": "How does this work?"}))
    cache = dict(id="c", question_event_id=None, interaction_event_id="r",
                 input_hash=input_hash(reader), question_type="mechanism",
                 facets_json='["f"]', lo_ids_json="[]", created_at="2026-01-03")
    rows = derive(readers=[reader], cache=[cache])
    assert rows[0].signal_type == "reader_confusion"
    assert rows[0].observed_at == "2026-01-03"
    assert not confusion_blocks_fast_track(rows, lo_id="lo", as_of="2026-01-02")
    assert confusion_blocks_fast_track(rows, lo_id="lo", as_of="2026-01-04")
    assert not confusion_blocks_fast_track(rows, lo_id="lo", as_of="2026-01-04", self_report_known=True)
    stale = dict(cache, input_hash="stale")
    assert derive(readers=[reader], cache=[stale]) == ()
    logged = question(question_type="other")
    cache = dict(cache, question_event_id="q", interaction_event_id=None, input_hash=input_hash(logged))
    assert derive([logged], cache=[cache])[0].signal_type == "other"


@pytest.fixture
def repository(tmp_path):
    return Repository(tmp_path / "state.sqlite")


def classify(repository, events, callback, **changes):
    kwargs = dict(model="fake-model", classify=callback,
                  estimate_per_question=SpendEstimate(calls=1, total_tokens=10, estimated_usd=.01),
                  caps=SpendCaps(), enabled=True)
    return classify_missing_questions(repository, events, **(kwargs | changes))


def answer(_):
    return {"question_type": "prerequisite", "facets": ["f"], "lo_ids": ["lo"]}


def test_missing_only_cache_resume_ledger_and_no_replay_calls(repository):
    calls = []
    def fake(row):
        calls.append(row)
        assert "answer_md" not in row
        return answer(row)
    missing = question(question_type=None, answer_md="Future tutor answer")
    report = classify(repository, [question(), missing], fake)
    assert report["classified"] == 1 and len(calls) == 1
    assert classify(repository, [missing], fake)["pending"] == 0
    with repository.connection() as connection:
        cache = load_cached_classifications(connection)
        assert connection.execute("SELECT count(*) FROM judgment_ledger").fetchone()[0] == 1
        before = tuple(connection.iterdump())
        assert derive([missing], cache=cache)
        assert derive([missing], cache=cache)
        assert tuple(connection.iterdump()) == before  # G13: every stored byte/value unchanged
    assert len(calls) == 1


@pytest.mark.parametrize("options,status", [
    ({"dry_run": True}, "dry_run"), ({"enabled": False}, "disabled"),
    ({"caps": SpendCaps(max_calls=0)}, "over_budget"),
    ({"cancelled": lambda: True}, "cancelled"),
    ({"estimate_per_question": SpendEstimate(calls=1)}, "over_budget"),
])
def test_no_calls_or_writes_when_not_admitted(repository, options, status):
    def forbidden(_):
        pytest.fail("model must not be constructed/called")
    with repository.connection() as connection:
        before = tuple(connection.iterdump())
    assert classify(repository, [question(question_type=None)], forbidden, **options)["status"] == status
    with repository.connection() as connection:
        assert tuple(connection.iterdump()) == before


def test_invalid_verdict_logged_not_cached(repository):
    raw = {"question_type": "nonsense", "facets": [], "lo_ids": []}
    result = classify(repository, [question(question_type=None)], lambda _: raw)
    assert result["invalid"] == 1
    with repository.connection() as connection:
        assert load_cached_classifications(connection) == ()
        assert json.loads(connection.execute("SELECT verdict FROM judgment_ledger").fetchone()[0]) == raw


def test_cancellation_preserves_paid_work_then_resume(repository):
    stopped = False
    def fake(row):
        nonlocal stopped
        stopped = True
        return answer(row)
    events = [question(id=str(i), question_type=None) for i in range(2)]
    report = classify(repository, events, fake, cancelled=lambda: stopped)
    assert report["classified"] == 1 and report["status"] == "cancelled"
    assert classify(repository, events, answer)["classified"] == 1


def test_hidden_physical_retry_blocked_before_network(repository):
    client = SimpleNamespace(provider_name="fake", model="fake")
    sent = []
    def fake(row):
        with model_call(client, purpose="field_question_classification"):
            for i in range(2):
                with model_call(client, purpose="chat_request"):
                    sent.append(i)
                    report_call_usage({"input_tokens": 20, "output_tokens": 5})
        return answer(row)
    report = classify(repository, [question(question_type=None)], fake)
    assert sent == [0] and report["status"] == "over_budget"
    assert report["charged"]["calls"] == 1
    assert report["charged"]["total_tokens"] == 25
    with repository.connection() as connection:
        assert connection.execute("SELECT count(*) FROM model_call_receipts").fetchone()[0] == 2


def test_late_classification_does_not_delay_logged_leak_or_help():
    q = question(question_type=None, hint_equivalent=True, leak_suspected=True, seconds_into_attempt=0)
    cache = dict(id="c", question_event_id="q", interaction_event_id=None,
                 input_hash=input_hash(q), question_type="other",
                 facets_json='["f"]', lo_ids_json="[]", created_at="2026-01-03")
    enriched, = enrich_attempts([attempt()], derive([q], [attempt()], cache=[cache]))
    assert not enriched.features.cold and enriched.help_before_work


@pytest.mark.parametrize("dry_run", [True, False])
def test_classification_cli_is_offline_lazy_bounded_and_resumable(repository, monkeypatch, dry_run):
    from typer.testing import CliRunner
    import typer
    from learnloop.cli import field_classification as cli

    root = repository.sqlite_path.parent
    (root / "learnloop.toml").write_text("")
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO question_events (id,context,question_md,created_at) VALUES (?,?,?,?)",
            ("q", "library", "A question", "2026-01-01"),
        )
    config = SimpleNamespace(
        field=SimpleNamespace(enabled=True, question_classification_enabled=True),
        ai=SimpleNamespace(routing=SimpleNamespace(field_question_classifier="fake"),
                           providers={"fake": SimpleNamespace(model="fake", type="openai_chat")}),
        storage=SimpleNamespace(sqlite_path="state.sqlite"),
    )
    loaded = SimpleNamespace(root=root, config=config, learning_objects={}, evidence_facets={})
    def load(path, *, load_environment):
        assert path == root and load_environment is False
        return loaded
    monkeypatch.setattr(cli, "load_vault", load)
    calls = []
    class Client:
        provider_name = "fake"
        model = "fake"
        def supports(self, _):
            return True
        def complete(self, request):
            calls.append(request)
            return request.result_model(question_type="other", lo_ids=[], facets=[])
    def resolve(*args, **kwargs):
        assert not dry_run
        assert args[2] == "field_question_classifier" and kwargs["allow_env"] is False
        return SimpleNamespace(client=Client(), runtime=SimpleNamespace(ready=True))
    monkeypatch.setattr(cli, "ready_client_for_task", resolve)
    app = typer.Typer()
    @app.callback()
    def root_command():
        pass
    cli.register_classification_command(app)
    args = ["classify-questions", "--vault", str(root), "--price-per-million", "1", "--json"]
    if dry_run:
        args.append("--dry-run")
    with repository.connection() as connection:
        before = tuple(connection.iterdump())
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["status"] == ("dry_run" if dry_run else "complete")
    if dry_run:
        assert calls == []
        with repository.connection() as connection:
            assert tuple(connection.iterdump()) == before
    else:
        assert len(calls) == 1 and calls[0].output_budget_tokens == 512
        assert CliRunner().invoke(app, args).exit_code == 0
        assert len(calls) == 1


# Owner decision 2026-10-12 (Slice A §5 rule 6): a Codex classifier runs on the
# subscription without a physical-request bound; cost is estimated only.

def _classification_cli(repository, monkeypatch, *, profile_type, client=None):
    from typer.testing import CliRunner
    import typer
    from learnloop.cli import field_classification as cli

    root = repository.sqlite_path.parent
    (root / "learnloop.toml").write_text("")
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO question_events (id,context,question_md,created_at) VALUES (?,?,?,?)",
            ("q", "library", "A question", "2026-01-01"),
        )
    config = SimpleNamespace(
        field=SimpleNamespace(enabled=True, question_classification_enabled=True),
        ai=SimpleNamespace(routing=SimpleNamespace(field_question_classifier="route"),
                           providers={"route": SimpleNamespace(model="fake", type=profile_type)}),
        storage=SimpleNamespace(sqlite_path="state.sqlite"),
    )
    loaded = SimpleNamespace(root=root, config=config, learning_objects={}, evidence_facets={})
    monkeypatch.setattr(cli, "load_vault", lambda path, *, load_environment: loaded)

    def resolve(*args, **kwargs):
        if client is None:
            pytest.fail("no client may be constructed")
        assert args[2] == "field_question_classifier" and kwargs["allow_env"] is False
        return SimpleNamespace(client=client, runtime=SimpleNamespace(ready=True))

    monkeypatch.setattr(cli, "ready_client_for_task", resolve)
    app = typer.Typer()

    @app.callback()
    def root_command():
        pass

    cli.register_classification_command(app)

    def invoke(*extra):
        result = CliRunner().invoke(app, ["classify-questions", "--vault", str(root), "--json", *extra])
        return result.exit_code, json.loads(result.output)

    return invoke


class CodexClassifier:
    provider_name = "codex"
    provider_type = "codex_sdk"
    model = "fake-codex"

    def __init__(self, *, usage=True, physical_purpose="field_question_classification:sdk_turn"):
        self.usage, self.purpose, self.turns = usage, physical_purpose, 0

    def supports(self, capability):
        return capability == "structured_completion"

    def complete(self, request):
        for _ in range(2):  # a repair turn: unbounded on the subscription
            with model_call(self, purpose=self.purpose):
                self.turns += 1
                if self.usage:
                    report_call_usage({"input_tokens": 10, "output_tokens": 20})
        return request.result_model(question_type="other", lo_ids=[], facets=[])


def _classifier_receipts(repository):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT purpose, budget_json, usage_json FROM model_call_receipts "
            "WHERE owner_kind='field_question_classification' ORDER BY started_at, id"
        )]


def test_codex_classification_dry_run_estimates_without_price(repository, monkeypatch):
    invoke = _classification_cli(repository, monkeypatch, profile_type="codex_sdk")
    with repository.connection() as connection:
        before = tuple(connection.iterdump())
    code, report = invoke("--dry-run", "--max-tokens", "0", "--max-cost-usd", "0")
    assert code == 0, report
    assert report["status"] == "dry_run" and report["pending"] == 1
    assert report["billing"] == "subscription" and report["cost_basis"] == "estimated_only"
    assert report["physical_request_bound"] is False
    assert report["caps_in_force"]["not_enforced"] == ["max_total_tokens", "max_estimated_usd"]
    assert report["estimate"]["total_tokens"] > 0 and report["estimate"]["estimated_usd"] is None
    with repository.connection() as connection:
        assert tuple(connection.iterdump()) == before


def test_fake_codex_classification_records_estimated_only(repository, monkeypatch):
    client = CodexClassifier()
    invoke = _classification_cli(repository, monkeypatch, profile_type="codex_sdk", client=client)
    code, report = invoke("--max-tokens", "1", "--max-cost-usd", "0")
    assert code == 0, report
    assert report["status"] == "complete" and report["classified"] == 1
    assert client.turns == 2  # no physical-request bound
    assert report["charged"]["calls"] == 1 and report["charged"]["estimated_usd"] is None
    receipts = _classifier_receipts(repository)
    roots = [json.loads(r["budget_json"]) for r in receipts if r["budget_json"]]
    assert roots and all(b["cost_basis"] == "estimated_only" and b["billing"] == "subscription"
                         and b["physical_request_bound"] is False for b in roots)
    usage = [json.loads(r["usage_json"]) for r in receipts]
    assert usage and all(u["cost_basis"] == "estimated_only" and u["estimated_usd"] is None for u in usage)
    turns = [json.loads(r["usage_json"]) for r in receipts if r["purpose"].endswith(":sdk_turn")]
    assert [(u["estimated_total_tokens"], u["estimated_token_source"]) for u in turns] == [
        (30, "reported_usage"), (30, "reported_usage")]


def test_codex_classification_estimate_falls_back_to_planned_tokens(repository, monkeypatch):
    invoke = _classification_cli(repository, monkeypatch, profile_type="codex_sdk",
                                 client=CodexClassifier(usage=False))
    code, report = invoke("--price-per-million", "2")
    assert code == 0 and report["status"] == "complete", report
    usage = [json.loads(r["usage_json"]) for r in _classifier_receipts(repository)]
    planned = report["estimate"]["total_tokens"]
    assert usage and {u["estimated_token_source"] for u in usage} == {"input_plus_output_estimate"}
    assert all(u["estimated_total_tokens"] == planned for u in usage)
    assert all(u["estimated_usd"] == pytest.approx(planned * 2 / 1_000_000) for u in usage)


def test_codex_classification_still_stops_at_the_call_cap(repository, monkeypatch):
    client = CodexClassifier()
    invoke = _classification_cli(repository, monkeypatch, profile_type="codex_sdk", client=client)
    code, report = invoke("--max-calls", "0")
    assert code == 1 and report["status"] == "over_budget"
    assert client.turns == 0 and report["charged"]["calls"] == 0
    # The worker's per-question reservation also counts calls on the subscription.
    events = [question(id=str(i), question_type=None) for i in range(2)]
    stopped = classify(repository, events, answer, subscription=True,
                       caps=SpendCaps(max_calls=1, max_total_tokens=1, max_estimated_usd=0),
                       estimate_per_question=SpendEstimate(calls=1, total_tokens=10))
    assert stopped["status"] == "over_budget" and stopped["classified"] == 0


def test_metered_classifier_keeps_bound_unknown_price_refusal_and_token_cap(repository, monkeypatch):
    client = CodexClassifier(physical_purpose="chat_request")
    client.provider_type = "openai_chat"
    invoke = _classification_cli(repository, monkeypatch, profile_type="openai_chat", client=client)
    code, report = invoke()  # no price: refused before any client
    assert code == 1 and report["status"] == "over_budget" and client.turns == 0
    assert report["billing"] == "metered" and report["physical_request_bound"] is True
    code, report = invoke("--price-per-million", "1", "--max-tokens", "1")
    assert code == 1 and report["status"] == "over_budget" and client.turns == 0
    code, report = invoke("--price-per-million", "1")
    assert code == 1 and report["status"] == "over_budget"
    assert client.turns == 1  # the hidden second physical request never started


def test_codex_classifier_resolving_to_metered_client_is_refused(repository, monkeypatch):
    client = CodexClassifier()
    client.provider_type = "openrouter"
    invoke = _classification_cli(repository, monkeypatch, profile_type="codex_sdk", client=client)
    code, report = invoke()
    assert code == 1 and report["status"] == "invalid" and client.turns == 0


def test_loader_logged_reader_mapping_not_current_span_provenance(repository, caplog):
    lo = SimpleNamespace(
        id="lo", subjects=["subject"], blueprints=[], updated_at="2025-01-01",
        provenance=SimpleNamespace(source_refs=[SimpleNamespace(extraction_id="ex", span_ids=["s"])]),
    )
    vault = SimpleNamespace(learning_objects={"lo": lo}, canonical_facet_id=lambda f: f)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO question_events (id,context,question_md,question_type,created_at,source_context_json) VALUES (?,?,?,?,?,?)",
            ("q", "reader", "Why?", "mechanism", "2026-01-01", json.dumps({"candidate_learning_object_ids": ["lo"]})),
        )
        connection.execute(
            "INSERT INTO interaction_events (id,kind,origin,created_at,payload_json) VALUES (?,?,?,?,?)",
            ("r", "learner_question_asked", "learner", "2026-01-02",
             json.dumps({"question_type": "clarification", "extraction_id": "ex", "span_id": "s"})),
        )
        before = tuple(connection.iterdump())
        with caplog.at_level("INFO", logger="learnloop.field.signals"):
            signals = load_interaction_signals(connection, vault, ())
        assert len(signals) == 1
        assert all(s.lo_id == "lo" and s.subject_id == "default" and s.signal_type == "reader_confusion" for s in signals)
        assert caplog.records[-1].interaction_unmapped == 1
        assert caplog.records[-1].interaction_questions == 2
        assert tuple(connection.iterdump()) == before
        # Neither old nor new updated_at makes mutable provenance historical.
        lo.updated_at = "2026-02-01"
        assert load_interaction_signals(connection, vault, ()) == signals


@pytest.mark.parametrize("linked,context,expected", [
    (True, "practice", True), (False, "practice", False),
    (True, "feedback", False), (False, "feedback", False),
])
def test_tied_assistance_requires_linked_practice_phase(linked, context, expected):
    original = attempt(hints_used=1)
    q = question(
        context=context, question_type="mechanism", created_at=original.observed_at,
        attempt_id="a" if linked else None, seconds_into_attempt=0,
        leak_suspected=True,
    )
    rows = derive([q], [original])
    enriched, = enrich_attempts([original], rows)
    assert enriched.help_before_work is expected
    assert enriched.features.cold is not expected
    assert enriched.preceded_by_question is expected
    hint = next(s for s in rows if s.signal_id == "hint:a")
    assert hint.outcome == (.3 if expected else .8)


def test_tied_paid_classification_does_not_backdate_help():
    original = attempt()
    q = question(question_type=None, created_at=original.observed_at, seconds_into_attempt=0)
    cache = dict(id="c", question_event_id="q", interaction_event_id=None,
                 input_hash=input_hash(q), question_type="strategy",
                 facets_json='["f"]', lo_ids_json='["lo"]', created_at="2026-01-03")
    rows = derive([q], [original], cache=[cache])
    assert all(s.observed_at == "2026-01-03" for s in rows)
    assert enrich_attempts([original], rows) == (original,)
    logged = dict(q, hint_equivalent=True, leak_suspected=True)
    cache["input_hash"] = input_hash(logged)
    rows = derive([logged], [original], cache=[cache])
    enriched, = enrich_attempts([original], rows)
    assert enriched.help_before_work and not enriched.features.cold
    assert next(s for s in rows if s.signal_type == "practice_assistance").observed_at == original.observed_at


def test_explicit_and_paid_targets_override_facet_membership():
    q = question(lo_ids_json='["historical"]')
    rows = derive([q])
    assert [s.lo_id for s in rows] == ["historical"]
    missing = question()
    cache = dict(id="c", question_event_id="q", interaction_event_id=None,
                 input_hash=input_hash(missing), question_type="prerequisite",
                 facets_json='["f"]', lo_ids_json='["paid"]', created_at="2026-01-03")
    rows = derive([missing], cache=[cache])
    assert [s.lo_id for s in rows] == ["paid"]
    assert rows[0].observed_at == cache["created_at"]


def test_loader_current_lo_edits_cannot_retarget_history(repository):
    lo = SimpleNamespace(
        id="lo", subjects=["today"], updated_at="2025-01-01",
        blueprints=[SimpleNamespace(facets=["f"])],
        provenance=SimpleNamespace(source_refs=[]),
    )
    vault = SimpleNamespace(learning_objects={"lo": lo}, canonical_facet_id=lambda f: f)
    historical = replace(attempt(), features=replace(attempt().features, subject_id="then"))
    with repository.connection() as connection:
        for id_, attempt_id, source in [
            ("linked", "a", {"candidate_learning_object_ids": ["lo"]}),
            ("logged", None, {"candidate_learning_object_ids": ["lo"]}),
            ("unmapped", None, {}),
        ]:
            connection.execute(
                "INSERT INTO question_events (id,context,question_md,question_type,created_at,"
                "attempt_id,facets_json,source_context_json) VALUES (?,?,?,?,?,?,?,?)",
                (id_, "reader", "Why?", "mechanism", "2026-01-01", attempt_id, '["f"]', json.dumps(source)),
            )
        connection.execute(
            "INSERT INTO interaction_events (id,kind,origin,created_at,payload_json) VALUES (?,?,?,?,?)",
            ("reader", "learner_question_asked", "learner", "2026-01-02",
             json.dumps({"question_type": "mechanism", "lo_ids": ["lo"], "learner_subject_id": "logged-subject"})),
        )
        before = load_interaction_signals(connection, vault, [historical])
        assert len(before) == 3
        assert {s.subject_id for s in before} == {"then", "default", "logged-subject"}
        # Adding another LO sharing the facet, retagging the existing LO's
        # subject and aliasing facets must not change old targets or their mass.
        vault.learning_objects["new"] = SimpleNamespace(
            id="new", subjects=["new-subject"], blueprints=[SimpleNamespace(facets=["f"])],
            updated_at="2025-01-01", provenance=lo.provenance,
        )
        lo.subjects = ["changed"]
        lo.blueprints = []
        vault.canonical_facet_id = lambda f: "renamed"
        assert load_interaction_signals(connection, vault, [historical]) == before
        vault.learning_objects.clear()
        assert load_interaction_signals(connection, vault, [historical]) == before


def test_loader_without_optional_classification_table_is_read_only(repository):
    with repository.connection() as connection:
        connection.execute("DROP TABLE question_classifications")
        connection.execute(
            "INSERT INTO question_events (id,context,question_md,question_type,created_at,source_context_json) VALUES (?,?,?,?,?,?)",
            ("q", "reader", "Why?", "mechanism", "2026-01-01",
             json.dumps({"candidate_learning_object_ids": ["historical"]})),
        )
        before = tuple(connection.iterdump())
        rows = load_interaction_signals(connection, SimpleNamespace(), ())
        assert [s.lo_id for s in rows] == ["historical"]
        assert tuple(connection.iterdump()) == before


def test_loader_paid_mapping_is_available_only_at_classification_time(repository):
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO question_events (id,context,question_md,question_type,created_at,facets_json) VALUES (?,?,?,?,?,?)",
            ("q", "reader", "Why?", "mechanism", "2026-01-01", '["f"]'),
        )
        cursor = connection.execute("SELECT * FROM question_events")
        raw = dict(zip([c[0] for c in cursor.description], cursor.fetchone(), strict=True))
        connection.execute(
            "INSERT INTO question_classifications "
            "(id,question_event_id,input_hash,question_type,facets_json,lo_ids_json,created_at,model,prompt_version) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            ("c", "q", input_hash(raw), "mechanism", '["f"]', '["paid"]', "2026-01-03", "fake", "test"),
        )
        before = tuple(connection.iterdump())
        rows = load_interaction_signals(connection, SimpleNamespace(), ())
        assert len(rows) == 1 and rows[0].lo_id == "paid"
        assert rows[0].observed_at == "2026-01-03"
        assert not confusion_blocks_fast_track(rows, lo_id="paid", as_of="2026-01-02")
        assert tuple(connection.iterdump()) == before


@pytest.mark.parametrize("flags", [
    {"leak_suspected": True}, {"answer_revealed": True},
    {"seconds_into_attempt": 0},
])
def test_tied_linked_practice_assistance_independent_flags(flags):
    original = attempt()
    rows = derive([question(created_at=original.observed_at, **flags)], [original])
    enriched, = enrich_attempts([original], rows)
    assert enriched.help_before_work is ("seconds_into_attempt" in flags)
    assert enriched.features.cold is ("seconds_into_attempt" in flags)
