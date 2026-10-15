"""Method-explicit items landed on main as mvp-0.25: the compositions.

The branch rendered "Use {method} in your answer." from ``required_method``
on every surface it knew. Main gained surfaces since its base, and the
landing routes each through the same functions (``presented_prompt``,
``fit_presented_prompt``, ``answered_question``/``answered_prompt``):

* router R2a's ``LearnerStateCardV1``: past work shows its pinned contract's
  question with the frozen method's sentence, whole within the stem limit;
* RW3a's margin cues: "Open" shows the cited answer's question from its
  graded contract; "check me" keeps the sentence whole when it clips;
* the daily plan's item rows and the Reader's video pause points preview the
  question with the sentence whole.

And the one-time statement judgment is registered the way main registers its
Decider judgments: a Tier-1 content task (``decider_routes.
required_method_statement``), its Decider defaulting to the Tier-1 route's.
Fakes only; no network.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from learnloop.config.schema import DeciderProviderConfig, LearnLoopConfig
from learnloop.reader import reader_cues as RCU
from learnloop.router.card import STEM_LIMIT
from learnloop.vault.loader import load_vault
from learnloop.vault.models import RequiredMethod
from learnloop.vault.required_method import answered_prompt, answered_question, required_method_instruction

from tests.helpers import add_followup_item

METHOD = "singular value decomposition"
SENTENCE = required_method_instruction(METHOD)
LONG = "Let A be the 2 by 2 matrix with rows (3, 0) and (4, 5). " * 12


# -- the learner state card (router R2a) ---------------------------------------------------------


def _graded_under_method(env, attempt_id: str, item_id: str, *, prompt: str, method: str | None) -> str:
    """Grade ``attempt_id`` under a pinned contract that showed ``prompt`` and froze ``method``."""

    from learnloop.learner.assessment_contracts import snapshot_for_presentation
    from tests.test_router_card import LAST
    from tests.daily_plan_fakes import iso

    update = {"prompt": prompt}
    if method is not None:
        update["required_method"] = RequiredMethod(name=method, criterion_ids=["correctness"])
    item = env.vault.practice_items[item_id].model_copy(update=update)
    version_id = snapshot_for_presentation(env.repository, env.vault, item)
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id, grading_revision) VALUES (?, ?, 'correctness', 4, 1, ?, ?, 0)",
            (f"ge_{attempt_id}", attempt_id, iso(LAST), version_id),
        )
        connection.commit()
    return version_id


def test_the_card_shows_the_frozen_methods_sentence_whole_after_a_shortened_statement(tmp_path, monkeypatch):
    from tests.daily_plan_fakes import iso
    from tests.test_router_card import LAST, OWN_ANSWER, _attempt, _card, _card_world

    env = _card_world(tmp_path, monkeypatch)
    _attempt(env, "att_method", "pi_a", "lo_m1", iso(LAST), answer=OWN_ANSWER, correctness=1.0)
    _graded_under_method(env, "att_method", "pi_a", prompt=LONG, method=METHOD)
    _attempt(env, "att_short", "pi_b", "lo_m2", "2026-09-21T09:00:00Z", answer="e1, e2", correctness=1.0)
    _graded_under_method(env, "att_short", "pi_b", prompt="Name a basis.", method=METHOD)
    card = _card(env)
    work = {entry["attempt_id"]: entry for entry in card["json"]["recent_work"]}
    stem = work["att_method"]["stem"]
    # The statement is shortened; the instruction stays whole, within the card's limit.
    assert stem.endswith(" " + SENTENCE) and len(stem) <= STEM_LIMIT
    assert stem.startswith("Let A be the 2 by 2 matrix")
    assert work["att_short"]["stem"] == f"Name a basis. {SENTENCE}"
    assert f"question: {stem}" in card["text"]


def test_the_card_shows_no_sentence_for_a_contract_that_froze_no_method(tmp_path, monkeypatch):
    """The item gains a method after the answer: the pinned question shows
    none (the learner was never asked to use it)."""

    from tests.daily_plan_fakes import iso
    from tests.test_router_card import LAST, OLD_STEM, OWN_ANSWER, _attempt, _card, _card_world

    env = _card_world(tmp_path, monkeypatch)
    _attempt(env, "att_old", "pi_a", "lo_m1", iso(LAST), answer=OWN_ANSWER, correctness=1.0)
    _graded_under_method(env, "att_old", "pi_a", prompt=OLD_STEM, method=None)
    card = _card(env)
    work = {entry["attempt_id"]: entry for entry in card["json"]["recent_work"]}
    assert work["att_old"]["stem"] == OLD_STEM
    assert SENTENCE not in card["text"]


# -- RW3a: "Open" and "check me" ------------------------------------------------------------------


def _graded_attempt_under(repository, vault, *, attempt_id: str, prompt: str, method: str | None) -> None:
    from learnloop.learner.assessment_contracts import snapshot_for_presentation
    from tests.helpers import NOW_ISO
    from tests.test_reader_cues import _attempt

    _attempt(repository, attempt_id=attempt_id, answer="SVD is the eigendecomposition.")
    update = {"prompt": prompt}
    if method is not None:
        update["required_method"] = RequiredMethod(name=method, criterion_ids=["correctness"])
    item = vault.practice_items["pi_svd_define_001"].model_copy(update=update)
    version_id = snapshot_for_presentation(repository, vault, item)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id, grading_revision) VALUES (?, ?, 'correctness', 1, 1, ?, ?, 0)",
            (f"ge_{attempt_id}", attempt_id, NOW_ISO, version_id),
        )
        connection.commit()


def test_open_shows_the_answered_question_with_its_frozen_method_whole(tmp_path):
    from tests.test_reader_cues import _active_error, _cue_vault, _plan_and_cues

    _root, vault, repository = _cue_vault(tmp_path, error=False)
    _graded_attempt_under(repository, vault, attempt_id="att-method", prompt=LONG, method=METHOD)
    _active_error(repository, attempt_id="att-method")
    _plan, cues = _plan_and_cues(vault, repository)
    assert cues["marks"]
    for mark in cues["marks"]:
        prompt = mark["earlier"]["prompt"]
        assert prompt.endswith(" " + SENTENCE) and len(prompt) <= RCU.MAX_PROMPT_CHARS
        assert prompt.startswith("Let A be the 2 by 2 matrix")


def test_open_without_a_method_is_unchanged(tmp_path):
    """No method anywhere: the item's question as it is now, clipped as before."""

    from tests.test_reader_cues import _active_error, _cue_vault, _plan_and_cues

    _root, vault, repository = _cue_vault(tmp_path, error=False)
    _graded_attempt_under(repository, vault, attempt_id="att-plain", prompt="Define SVD.", method=None)
    _active_error(repository, attempt_id="att-plain")
    _plan, cues = _plan_and_cues(vault, repository)
    assert cues["marks"] and all(mark["earlier"]["prompt"] == "Define SVD." for mark in cues["marks"])


def test_check_me_keeps_the_sentence_whole_when_it_clips(tmp_path):
    from learnloop.clock import FrozenClock
    from learnloop.vault.writer import upsert_practice_item
    from learnloop_sidecar.handlers.reader import check_me_proposal
    from tests.helpers import NOW
    from tests.test_reader_cues import _answered_cue, _cue_vault

    root, _vault, repository = _cue_vault(tmp_path, on_disk=True)
    add_followup_item(root)
    vault = load_vault(root)
    item = vault.practice_items["pi_svd_define_002"].model_copy(update={
        # The cue's query still finds it (its own words first).
        "prompt": vault.practice_items["pi_svd_define_002"].prompt + " " + LONG,
        "required_method": RequiredMethod(name=METHOD, criterion_ids=[
            vault.practice_items["pi_svd_define_002"].grading_rubric.criteria[0].id]),
    })
    upsert_practice_item(root, item, clock=FrozenClock(NOW))
    vault = load_vault(root)
    found = check_me_proposal(vault, repository, "ext1", _answered_cue())
    assert found["status"] == "found" and found["practice_item_id"] == "pi_svd_define_002"
    assert found["prompt"].endswith(" " + SENTENCE) and len(found["prompt"]) <= 220


# -- the daily plan's item rows ------------------------------------------------------------------


def test_a_plan_rows_preview_keeps_the_sentence_whole(tmp_path):
    from learnloop.daily_plan.view import PROMPT_PREVIEW_CHARS, _item_row
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    plain = vault.practice_items["pi_svd_define_001"]
    vault.practice_items["pi_long"] = plain.model_copy(update={
        "id": "pi_long", "prompt": LONG,
        "required_method": RequiredMethod(name=METHOD, criterion_ids=["correctness"]),
    })
    env = SimpleNamespace(vault=vault)

    def row(item_id: str) -> dict:
        planned = SimpleNamespace(practice_item_id=item_id, learning_object_id=plain.learning_object_id,
                                  lane="review", est_minutes=2.0, state="pending", origin="plan",
                                  served_at=None, done_at=None)
        return _item_row(env, planned)

    preview = row("pi_long")["prompt_preview"]
    assert preview.endswith(" " + SENTENCE) and len(preview) <= PROMPT_PREVIEW_CHARS
    # Without a method the preview is the statement's first characters, as before.
    assert row("pi_svd_define_001")["prompt_preview"] == plain.prompt[:PROMPT_PREVIEW_CHARS]


# -- answered_question: the pair answered_prompt renders -----------------------------------------


def test_answered_question_is_the_pair_answered_prompt_renders():
    from learnloop.vault.required_method import presented_prompt

    item = SimpleNamespace(prompt="Now.", required_method=None)
    frozen = {"prompt": "Then.", "required_method": {"name": METHOD, "criterion_ids": ["c"]}}
    plain = {"prompt": "Then.", "required_method": None}
    for subject, contract in ((item, frozen), (item, plain), (item, None), (None, frozen), (None, None)):
        statement, method = answered_question(subject, contract)
        expected = answered_prompt(subject, contract)
        assert (presented_prompt(statement, method) if (statement, method) != (None, None) else None) == expected
    assert answered_question(item, frozen) == ("Then.", frozen["required_method"])
    assert answered_question(item, plain) == ("Now.", None)


# -- the statement judgment, registered as a Tier-1 content task ---------------------------------


def test_the_statement_judgment_is_a_tier1_content_task_with_its_own_switch():
    from learnloop.decider_judgments import CONTENT_TASKS, enabled

    assert "required_method_statement" in CONTENT_TASKS
    config = LearnLoopConfig()
    # A content path: on at every version, off by its own switch.
    for version in ("mvp-0.9", "mvp-0.21", "mvp-0.25"):
        config.algorithms.algorithm_version = version
        assert enabled(config, "required_method_statement"), version
    config.decider_routes.required_method_statement = False
    assert not enabled(config, "required_method_statement")


def test_the_judges_decider_defaults_to_the_tier1_deciders_profile():
    from learnloop.config.schema import DEFAULT_DECIDER_PROVIDER
    from learnloop.content.proposals.method_phrasing import decider_profile_name

    config = LearnLoopConfig()
    vault = SimpleNamespace(config=config)
    assert decider_profile_name(vault) == DEFAULT_DECIDER_PROVIDER
    config.ai.providers["pplx"] = DeciderProviderConfig(api="perplexity")
    config.ai.routing.tier1_decider = "pplx"
    assert decider_profile_name(vault) == "pplx"
    # Its own route still wins.
    config.ai.providers["other"] = DeciderProviderConfig(api="perplexity")
    config.ai.routing.rubric_phrasing_judge = "other"
    assert decider_profile_name(vault) == "other"


def test_switched_off_the_llm_judge_decides_the_statement(tmp_path):
    from learnloop.content.proposals.method_statement_judge import resolve_statement_judge
    from tests.helpers import append_config_toml, create_basic_vault
    from tests.structured_ai import StructuredClientFake
    from tests.test_required_method_authority import StatementDecider

    class LLM(StructuredClientFake):
        provider_name = "llm-fake"
        model = "llm-fake-model"

    paths = create_basic_vault(tmp_path / "vault")
    decider = StatementDecider({"requires": 0.8, "allows": 0.15, "prohibits": 0.05})
    judge = resolve_statement_judge(load_vault(paths.root), clients={"decider": decider, "llm": LLM()},
                                    price_per_million=1.0)
    assert judge.kind == "decider"
    append_config_toml(paths.root, "[decider_routes]\nrequired_method_statement = false\n")
    judge = resolve_statement_judge(load_vault(paths.root), clients={"decider": decider, "llm": LLM()},
                                    price_per_million=1.0)
    assert judge.kind == "llm" and decider.calls == []


def test_the_tier1_disclosure_names_the_statement_judgment():
    from learnloop.ai.disclosures import judge_route_disclosures

    settings = {entry["route"]: entry["disclosure"] for entry in judge_route_disclosures(LearnLoopConfig())}
    assert "required_method_statement" in settings["tier1_decider"]
    assert "no learner text" in settings["tier1_decider"]
    assert json.dumps(settings)


# -- exam protection: the held-out leakage screen reads the question as presented ---------------


def test_the_leakage_screen_reads_the_rendered_question():
    from learnloop.content.authoring.practice_leakage import _payload_surfaces

    method = {"name": "cofactor expansion", "criterion_ids": ["m"]}
    surfaces = _payload_surfaces({"prompt": "Compute det(A).", "required_method": method, "expected_answer": "13"})
    assert surfaces.startswith("Compute det(A).\n\nUse cofactor expansion in your answer.")
    # Without a method the screened text is unchanged.
    assert _payload_surfaces({"prompt": "Compute det(A).", "expected_answer": "13"}) == "Compute det(A).\n13"
