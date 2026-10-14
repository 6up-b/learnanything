"""The Decider's Tier 1 (mvp-0.22) composed with main at its landing.

The branch built Tier 1 as mvp-0.20 on e8d261405; main had since added UX
Phase 1 (automatic builds, the one-time OK at AI connection, books kept on
this computer (since retired), the per-request metered gate), the route rules in the grader
(main's own mvp-0.20, which deleted the separate proofs route check) and
value-of-information stopping (mvp-0.21). These pin how they compose: fakes
only, no network, no paid call.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import typing

import pytest

from learnloop.ai.decisions import ChoiceAnswer, DecisionResult
from learnloop.db.repositories import Repository

from tests.test_facet_span_support import LockProbe, SpanDecider, _span_vault
from tests.test_tier1_decider import _rows

SRC = Path(__file__).resolve().parents[1] / "src"


# -- 1. the deleted route check ------------------------------------------------------------------


def test_nothing_in_tier1_reads_the_deleted_route_check():
    """Main deleted ``attempts/proof_check.py`` and ``ai.routing.proof_check``;
    the branch's only references (a spend allowance, version pins) are gone."""

    from learnloop.ai.disclosures import JUDGE_ROUTES
    from learnloop.ai.review_spend import OUTPUT_ALLOWANCE
    from learnloop.ai.routing import AITask
    from learnloop.config.schema import AIRoutingConfig
    from learnloop.decider_judgments import CONTENT_TASKS, SERVING_TASKS

    assert importlib.util.find_spec("learnloop.attempts.proof_check") is None
    assert "proof_check" not in OUTPUT_ALLOWANCE
    assert "proof_check" not in typing.get_args(AITask)
    assert "proof_check" not in AIRoutingConfig.model_fields
    assert not [route for route, _judge, _consumer in JUDGE_ROUTES if "proof" in route]
    assert not [task for task in SERVING_TASKS + CONTENT_TASKS if "proof" in task]
    importers = [
        path.relative_to(SRC).as_posix() for path in SRC.rglob("*.py")
        if "attempts.proof_check" in path.read_text(encoding="utf-8")
        or "PROOF_ROUTE_CHECK_VERSIONS" in path.read_text(encoding="utf-8")
    ]
    assert importers == []


# -- version gates: main's mvp-0.20 is the route rules, never the Decider ------------------------


@pytest.mark.parametrize("version, moved", [
    ("mvp-0.19", False), ("mvp-0.20", False), ("mvp-0.21", False), ("mvp-0.22", True),
])
def test_tier1_judgments_move_only_at_mvp022(version, moved):
    from learnloop.config.schema import LearnLoopConfig
    from learnloop.decider_judgments import SERVING_TASKS, enabled

    config = LearnLoopConfig()
    config.algorithms.algorithm_version = version
    assert all(enabled(config, task) is moved for task in SERVING_TASKS)
    assert enabled(config, "facet_span_support")


def test_a_link_recorded_at_main_mvp020_or_mvp021_has_no_decider_authority(tmp_path):
    from types import SimpleNamespace

    from learnloop.db.stores.judgments import append_judgment
    from learnloop.substrate.recurrence_groups import _source_judgments

    repo = Repository(tmp_path / "state.sqlite")
    edges = []
    build = SimpleNamespace(citation_pairs={("a", "b"): [("cause_a", "cause_b", "episode_a", "episode_b")]},
                            edge=lambda *a, **kw: edges.append(kw))
    with repo.atomic():
        connection = repo.connection()
        for id, version in (("route_rules", "mvp-0.20"), ("voi", "mvp-0.21"), ("tier1", "mvp-0.22")):
            append_judgment(connection, id=id, task="same_cause", left_kind="attempt", left_id="a",
                            right_kind="attempt", right_id="b", judge="decider", judge_model="fake",
                            prompt_version="v1", input_hash=id, verdict="same",
                            rationale=json.dumps({"decider_route": "diagnosis_link_judgment",
                                                  "algorithm_version": version}))
        _source_judgments(build, connection)
    assert [edge["ref"] for edge in edges] == ["judgment:tier1"]


# -- 2. the facet chokepoint under UX Phase 1's automatic builds ---------------------------------


def _cited_reword_proposal(repo, citation):
    from tests.test_facet_identity_actions import SHARED
    from tests.test_facet_reword_confirm import _proposal, _support
    from tests.test_facet_rewords import NEW_CLAIM

    return _proposal(repo, {"id": SHARED, "claim": NEW_CLAIM, "meaning_support": _support(citation)})


def _apply_as_an_automatic_build(paths, repo, patch_id):
    """The automatic build's apply step: ``synthesize_study_map(apply=True,
    apply_gate=auto_apply_allowed)`` reaches ``_apply_and_wire_goal``."""

    from learnloop.content.synthesis.source_set_synthesis import StudyMapResult, _apply_and_wire_goal

    result = StudyMapResult(source_set_id="sset_quickadd_src", subject_id="subject", mode="auto",
                            manifest_hash="m", proposal_id=patch_id)
    _apply_and_wire_goal(paths.root, repo, result, brief={}, create_goal=False, clock=None)
    assert result.applied
    return result


@pytest.mark.parametrize("choice", ["supports", "does not support"])
def test_an_automatic_builds_apply_asks_the_span_check_before_the_vault_lock(tmp_path, monkeypatch, choice):
    from learnloop import decider_judgments as tier1
    from learnloop.content.facet_identity import actions
    from learnloop.vault.loader import load_vault
    from tests.test_facet_identity_actions import SHARED
    from tests.test_facet_rewords import NEW_CLAIM, _entry

    paths, repo, citation = _span_vault(tmp_path, monkeypatch, None)
    client = LockProbe(choice, paths.root)
    monkeypatch.setattr(tier1, "client_for", lambda *a: client)
    _apply_as_an_automatic_build(paths, repo, _cited_reword_proposal(repo, citation))
    assert client.holders == [None]  # asked once, with no vault lock held
    (check,) = _rows(repo, "facet_span_support")
    pending = actions.pending_reword_confirms(repo, load_vault(paths.root))
    if choice == "supports":
        assert _entry(paths, SHARED)["claim"] == NEW_CLAIM and pending == []
    else:
        (card,) = pending
        assert card["span_support"]["verdict"] == choice and card["span_support"]["judgment_id"] == check["id"]


def test_a_book_carrying_the_retired_keep_local_is_asked_like_any_other(tmp_path, monkeypatch):
    """The Decider landing guarded the span check with UX Phase 1's per-book
    ``keep_local``. The opt-out is retired (owner, 2026-10-13; the
    reading-hardening landing): the column is never consulted, so a reword
    citing a book that still carries it is asked about and, on ``supports``,
    applies like any other."""

    from learnloop.content.facet_identity import actions
    from learnloop.content.proposals.patches import apply_accepted_items
    from learnloop.vault.loader import load_vault
    from tests.test_facet_identity_actions import SHARED
    from tests.test_facet_rewords import NEW_CLAIM, _entry

    client = SpanDecider("supports")
    paths, repo, citation = _span_vault(tmp_path, monkeypatch, client)
    with repo.connection() as connection:
        connection.execute("UPDATE source_artifacts SET keep_local = 1 WHERE id = ?", ("src_cited",))
        connection.commit()
    assert repo.sources_with_retired_keep_local() == ["src_cited"]
    apply_accepted_items(paths.root, _cited_reword_proposal(repo, citation))
    assert len(client.calls) == 1
    assert _entry(paths, SHARED)["claim"] == NEW_CLAIM
    assert actions.pending_reword_confirms(repo, load_vault(paths.root)) == []
    (check,) = _rows(repo, "facet_span_support")
    assert check["verdict"] == "supports"
    assert "kept_on_this_computer" not in json.loads(check["rationale"] or "{}")


# -- 4. spend: UX's per-request metered gate admits and settles the Decider ----------------------


def _decider_http(choice):
    calls = []

    def http(method, url, headers, body, timeout):
        request = json.loads(body)
        calls.append(request)
        answers = {}
        for name, question in request["questions"].items():
            options = list(question["criteria"])
            probabilities = {option: (0.7 if option == choice else 0.1) for option in options}
            answers[name] = {"type": "choice", "choice": options[0], "probabilities": probabilities,
                             "confidence": 0.7}
        payload = {"id": "gen-dec-1", "model": request["model"] + "-20261006", "provider": "Perplexity",
                   "answers": answers, "usage": {"input_tokens": 400, "output_tokens": 3, "cost": 0.000008}}
        return 200, {}, json.dumps(payload).encode()

    return http, calls


@pytest.mark.parametrize("limit_usd", [1.0, 0.0])
def test_inside_an_automatic_builds_request_gate_the_span_check_is_admitted_and_settled(
        tmp_path, monkeypatch, limit_usd):
    """The gate (UX Phase 1, unchanged) admits the Decider's one physical
    request like any metered request and settles its reported cost; a refusal
    is the check's ``refused``: the reword waits, the build goes on."""

    from learnloop import decider_judgments as tier1
    from learnloop.ai.execution import gate_model_requests
    from learnloop.ai.providers.decider import DeciderProviderClient
    from learnloop.config.schema import openrouter_decider_provider
    from learnloop.content.facet_identity import actions
    from learnloop.content.pipeline.add_source import _request_gate
    from learnloop.vault.loader import load_vault
    from tests.test_facet_identity_actions import SHARED
    from tests.test_facet_rewords import NEW_CLAIM, _entry

    paths, repo, citation = _span_vault(tmp_path, monkeypatch, None)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    http, calls = _decider_http("supports")
    client = DeciderProviderClient("openrouter_decider", openrouter_decider_provider(), http=http)
    monkeypatch.setattr(tier1, "client_for", lambda *a: client)
    config = load_vault(paths.root).config
    gate = _request_gate(config, limit_usd, 16_000)
    with gate_model_requests(gate):
        _apply_as_an_automatic_build(paths, repo, _cited_reword_proposal(repo, citation))
    (check,) = _rows(repo, "facet_span_support")
    pending = actions.pending_reword_confirms(repo, load_vault(paths.root))
    if limit_usd:
        assert len(calls) == 1 and gate.admitted == 1 and gate.refusal is None
        assert gate.spent_usd == pytest.approx(0.000008)  # the reported cost replaced the reservation
        assert check["verdict"] == "supports" and pending == []
        assert _entry(paths, SHARED)["claim"] == NEW_CLAIM
        with repo.connection() as connection:
            receipts = connection.execute(
                "SELECT owner_kind, output_budget_tokens, status, cost FROM model_call_receipts "
                "WHERE owner_kind = 'facet_span_support'").fetchall()
        # The Decider's receipt, exempt from the LLM output budget.
        assert [tuple(row) for row in receipts] == [("facet_span_support", None, "completed", 0.000008)]
    else:
        assert calls == [] and gate.admitted == 0 and gate.refusal["reason"] == "limit"
        assert check["verdict"] == "refused"
        (card,) = pending
        assert card["span_support"]["verdict"] is None


# -- 3. disclosures and the one-time OK name the same recipient ----------------------------------


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)


def _connection(root, monkeypatch):
    import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.handlers import first_run
    from learnloop_sidecar.registry import METHOD_REGISTRY

    from tests.ux_phase1_support import route

    monkeypatch.setattr(first_run, "authoring_route_for", lambda vault: route())
    ctx = SidecarContext()
    ctx.load(root)
    spec = METHOD_REGISTRY["get_ai_connection"]
    return spec.handler(ctx, spec.params_model.model_validate({}))


def test_the_one_ok_and_settings_name_perplexity_through_openrouter(tmp_path, monkeypatch, isolated_config):
    from learnloop.ai.disclosures import judge_route_disclosures
    from learnloop.vault.loader import load_vault

    from tests.ux_phase1_support import fresh_library

    root = fresh_library(tmp_path)
    payload = _connection(root, monkeypatch)
    base = ("LearnLoop sends passages of the books you add, and your answers, to Codex (your ChatGPT account) "
            "to write questions and give feedback.")
    note = payload["deciderNote"]
    assert note.startswith("With an OpenRouter key, LearnLoop also asks Perplexity, through OpenRouter,")
    assert "your answers and questions" in note and "book passages" in note
    assert payload["whatLeaves"] == f"{base} {note}"
    settings = {entry["route"]: entry["disclosure"] for entry in judge_route_disclosures(load_vault(root).config)}
    for route in ("tier1_decider", "learner_gap_decider"):
        assert "OpenRouter, which forwards it to Perplexity" in settings[route]


def test_with_every_decider_route_off_the_one_ok_is_unchanged(tmp_path, monkeypatch, isolated_config):
    from tests.ux_phase1_support import fresh_library, set_config

    root = fresh_library(tmp_path)
    from learnloop.decider_judgments import CONTENT_TASKS, SERVING_TASKS

    set_config(root, {
        **{("decider_routes", task): False for task in SERVING_TASKS + CONTENT_TASKS},
        ("learner_text_gaps", "decider_enabled"): False,
    })
    payload = _connection(root, monkeypatch)
    assert payload["deciderNote"] is None
    assert payload["whatLeaves"] == (
        "LearnLoop sends passages of the books you add, and your answers, to Codex (your ChatGPT account) "
        "to write questions and give feedback."
    )


def test_below_mvp022_the_one_ok_names_only_the_routes_still_on(tmp_path, monkeypatch, isolated_config):
    """Below the successor no Tier-1 judgment sends learner text, but the
    learner-text gaps' Decider (any version) and the span check (content) do."""

    from tests.helpers import _set_algorithm_version_at
    from tests.ux_phase1_support import fresh_library, set_config

    root = fresh_library(tmp_path)
    _set_algorithm_version_at(root, "mvp-0.21")
    set_config(root, {("learner_text_gaps", "decider_enabled"): False})
    note = _connection(root, monkeypatch)["deciderNote"]
    assert note == ("With an OpenRouter key, LearnLoop also asks Perplexity, through OpenRouter, short questions "
                    "about the book passages behind a reworded skill.")


def test_the_tier1_disclosure_and_the_one_ok_use_one_recipient_for_a_direct_perplexity_route():
    from learnloop.ai.disclosures import judge_route_disclosures
    from learnloop.config.schema import DeciderProviderConfig, LearnLoopConfig
    from learnloop.decider_judgments import connection_note

    config = LearnLoopConfig()
    config.algorithms.algorithm_version = "mvp-0.22"
    config.ai.providers["pplx"] = DeciderProviderConfig(api="perplexity")
    config.ai.routing.tier1_decider = "pplx"
    config.ai.routing.learner_gap_decider = "pplx"
    assert connection_note(config).startswith("With a Perplexity key, LearnLoop also asks Perplexity,")
    settings = {entry["route"]: entry["disclosure"] for entry in judge_route_disclosures(config)}
    assert "Perplexity's Decisions API directly" in settings["tier1_decider"]


# -- 5. output budget: the Decider exempt, its fallbacks under the shared policy ------------------


def test_the_decider_requests_no_output_budget_and_a_fallback_route_keeps_the_shared_policy():
    from learnloop.ai.review_spend import admitted_output_limit
    from learnloop.config.schema import DEFAULT_OUTPUT_TOKENS, LearnLoopConfig

    config = LearnLoopConfig()
    # The fallbacks' routes (ai.output_tokens unless a route override says otherwise).
    for route in ("misconception_match", "learner_gap_judge", "diagnosis_judge", "contamination_judge",
                  "field_question_classifier"):
        assert admitted_output_limit(route, None, config) == DEFAULT_OUTPUT_TOKENS
    config.ai.route_output_tokens["contamination_judge"] = 2048
    assert admitted_output_limit("contamination_judge", None, config) == 2048


class _TiedDecider(SpanDecider):
    def decide(self, state, questions, *, purpose):
        self.calls.append(state)
        options = list(next(iter(questions.values())).options)
        probabilities = {k: (0.5 if i < 2 else 0.0) for i, k in enumerate(options)}
        return DecisionResult({"verdict": ChoiceAnswer(options[0], probabilities)}, self.model, 100, 0, 0.000002)


def test_a_tied_span_check_inside_an_automatic_build_waits_for_the_owner(tmp_path, monkeypatch):
    from learnloop import decider_judgments as tier1
    from learnloop.content.facet_identity import actions
    from learnloop.vault.loader import load_vault

    paths, repo, citation = _span_vault(tmp_path, monkeypatch, None)
    client = _TiedDecider("supports")
    monkeypatch.setattr(tier1, "client_for", lambda *a: client)
    _apply_as_an_automatic_build(paths, repo, _cited_reword_proposal(repo, citation))
    (check,) = _rows(repo, "facet_span_support")
    assert check["verdict"] == "tied"
    (card,) = actions.pending_reword_confirms(repo, load_vault(paths.root))
    assert card["span_support"]["verdict"] is None
