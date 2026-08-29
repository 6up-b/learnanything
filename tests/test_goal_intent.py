from __future__ import annotations

from learnloop.content.synthesis.brief import validate_brief
from learnloop.goals.goal_intent import resolve_goal_quest
from learnloop.vault.models import Goal


def _goal(**overrides) -> Goal:
    data = {
        "id": "goal_complex_numbers",
        "title": "Complex-number practice",
        "facet_scope": {"concepts": ["complex_numbers"], "facets": []},
        "created_at": "2026-07-24T00:00:00Z",
        "updated_at": "2026-07-24T00:00:00Z",
    }
    data.update(overrides)
    return Goal.model_validate(data)


def test_explicit_learner_intent_wins_over_operational_goal():
    quest = resolve_goal_quest(
        _goal(
            intent_sentence="  I want to use complex numbers in signal processing.  ",
            creation_source="learner",
            exam={"enabled": True, "item_count": 20},
        )
    )

    assert quest is not None
    assert quest.sentence == "I want to use complex numbers in signal processing."
    assert quest.basis == "explicit_intent"


def test_exam_goal_supplies_narrower_quest_when_intent_is_blank():
    quest = resolve_goal_quest(
        _goal(
            title="Signals and systems final",
            creation_source="learner",
            exam={"enabled": True, "item_count": 20},
        )
    )

    assert quest is not None
    assert quest.sentence == "Do well on the exam goal “Signals and systems final”."
    assert quest.basis == "exam_goal"


def test_non_exam_learner_goal_supplies_problem_mastery_quest():
    quest = resolve_goal_quest(_goal(creation_source="learner"))

    assert quest is not None
    assert quest.sentence == "Be good at problems covered by the goal “Complex-number practice”."
    assert quest.basis == "practice_goal"


def test_source_ingestion_title_is_not_treated_as_learner_intent():
    assert resolve_goal_quest(_goal(creation_source="source_ingestion")) is None


def test_legacy_goal_preserves_title_as_quest():
    quest = resolve_goal_quest(_goal())

    assert quest is not None
    assert quest.sentence == "Complex-number practice"
    assert quest.basis == "legacy_title"


def test_study_map_brief_preserves_camel_case_learner_intent():
    brief = validate_brief(
        {
            "outcome": "exam_prep",
            "goalTitle": "Signals final",
            "intentSentence": "I want to understand signal processing.",
        }
    )

    assert brief["goal_title"] == "Signals final"
    assert brief["intent_sentence"] == "I want to understand signal processing."


def test_study_map_brief_preserves_scope_and_explicit_practice_timing():
    brief = validate_brief(
        {
            "outcome": "general_learning",
            "scope": "Treat this as a narrow adjunct; preserve the existing map.",
            "practiceItems": "upfront",
        }
    )

    assert brief["scope"] == "Treat this as a narrow adjunct; preserve the existing map."
    assert brief["practice_items"] == "upfront"


def test_narrow_adjunct_preset_expands_defaults_but_allows_explicit_edits():
    generated = validate_brief({"authoringPreset": "narrow_adjunct"})

    assert generated["authoring_preset"] == "narrow_adjunct"
    assert generated["outcome"] == "general_learning"
    assert generated["depth"] == "intro"
    assert generated["practice_items"] == "upfront"
    assert "at most one focused learning object" in generated["scope"]

    edited = validate_brief(
        {
            "authoringPreset": "narrow_adjunct",
            "depth": "standard",
            "practiceItems": "as_you_read",
            "scope": "Only add the elevator paradox.",
        }
    )
    assert edited["depth"] == "standard"
    assert edited["practice_items"] == "as_you_read"
    assert edited["scope"] == "Only add the elevator paradox."
