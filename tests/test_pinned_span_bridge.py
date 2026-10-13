"""S4 (§10.3): "Explain this with my work" pins the learner's chosen spans."""
from __future__ import annotations

from learnloop.source_retrieval.tutor import PinnedSpanProvider
from learnloop.tutor.tutor_qa import ask_question
from tests.source_service_fakes import build_textbook_vault, loaded, set_item_answer, tool_tutor

ANSWER = "Swapping two rows of a matrix multiplies its determinant by -1, so the determinant changes sign."


def test_pinned_spans_pass_the_policys_filters(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    set_item_answer(paths, "pi_determinant_2", ANSWER)
    vault = loaded(paths)
    item = vault.practice_items["pi_determinant_2"]
    answer_span, definition_span, exercise_span = spans["ch5"][2], spans["ch5"][1], spans["exercises"][1]
    provider = PinnedSpanProvider([f"ext_text:{answer_span}", f"ext_text:{definition_span}",
                                   f"ext_text:{exercise_span}", "ext_text:missing"])
    pinned, manifest = provider(vault, repository, context="practice", question_md="Explain with my work",
                                learning_object_ids=["lo_matrices"], item=item)
    assert [span["span_id"] for span in pinned] == [definition_span]
    reasons = {entry["span_id"]: entry["reason"] for entry in manifest["dropped_pins"]}
    assert reasons[answer_span] == "it reproduces the answer to the item you are practising"
    assert reasons["missing"] == "no such passage"
    assert exercise_span in reasons
    reading, _ = provider(vault, repository, context="library", question_md="q", learning_object_ids=[], item=None)
    assert {span["span_id"] for span in reading} >= {answer_span, definition_span}
    cold, cold_manifest = PinnedSpanProvider([f"ext_text:{definition_span}"], cold=True)(
        vault, repository, context="practice", question_md="q", learning_object_ids=[], item=item)
    assert cold == [] and cold_manifest["policy"] == "cold_attempt"


def test_the_bridge_is_a_normal_tutor_question_with_the_draft(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    tutor = tool_tutor()
    definition_span = spans["ch5"][1]
    result = ask_question(loaded(paths), repository, tutor, context="practice",
                          question_md="Explain this with my work", practice_item_id="pi_eigen_1", session_id="s1",
                          source_span_provider=PinnedSpanProvider([f"ext_text:{definition_span}"]),
                          learner_draft_md="det(A - tI) = 0 so t = 2")
    prompt = tutor.prompts[0]
    assert "det(A - tI) = 0 so t = 2" in prompt and definition_span in prompt
    event = repository.question_event(result["event_id"])
    assert event["answer_status"] == "answered"
    assert event["source_context"]["source_retrieval"]["basis"] == "pinned"
