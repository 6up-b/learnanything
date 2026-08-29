"""Server-side quote re-anchoring (deterministic outranks model-reported).

The quote is the anchor authority; model-emitted char offsets are hints that
grading recomputes. Localization is never fatal: an unlocatable quote degrades
to a whole-answer anchor and the grade proceeds. These tests pin the resolver's
closed basis vocabulary and the exact live bug: a correct quote with miscounted
offsets used to reject the entire exam grade.
"""

from __future__ import annotations

from learnloop.attempts.ai_contracts import CriterionEvidence, ErrorAttribution, GradingProposal
from learnloop.attempts.grading import (
    ANCHOR_BASES,
    resolve_quote_anchor,
    validate_codex_grading_proposal,
)
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault


# --- resolver units ---------------------------------------------------------


def test_unique_exact_match_uses_exact_offsets():
    answer = "The zero vector is (0,0) because T(e)=0."
    quote = "T(e)=0"
    res = resolve_quote_anchor(answer, quote)
    assert res.basis == "quote_match_unique"
    assert answer[res.char_start : res.char_end] == quote


def test_multiple_occurrences_pick_nearest_to_hint():
    answer = "x = 2 so x = 2 again"
    res = resolve_quote_anchor(answer, "x = 2", hint_start=8)
    assert res.basis == "quote_match_hint_disambiguated"
    assert res.char_start == 9
    assert answer[res.char_start : res.char_end] == "x = 2"


def test_multiple_occurrences_without_hint_take_first():
    answer = "x = 2 so x = 2 again"
    res = resolve_quote_anchor(answer, "x = 2")
    assert res.basis == "quote_match_first"
    assert res.char_start == 0


def test_whitespace_run_mismatch_resolves_normalized():
    answer = "First line\n\n  x   =   2  \nend"
    res = resolve_quote_anchor(answer, "x = 2")
    assert res.basis == "quote_match_normalized"
    # The resolved span covers the original region, whitespace runs included.
    assert answer[res.char_start : res.char_end].split() == ["x", "=", "2"]


def test_nfc_mismatch_resolves_when_answer_is_nfc_normal():
    answer = "the projection onto é is trivial"  # composed é (NFC)
    quote = "onto é is"  # decomposed
    res = resolve_quote_anchor(answer, quote)
    assert res.basis == "quote_match_normalized"
    assert "é" in answer[res.char_start : res.char_end]


def test_latex_escaped_content_matches_exactly():
    answer = r"so $v \oplus w = T^{-1}(T(v)+T(w))$ holds"
    quote = r"$v \oplus w = T^{-1}(T(v)+T(w))$"
    res = resolve_quote_anchor(answer, quote)
    assert res.basis == "quote_match_unique"
    assert answer[res.char_start : res.char_end] == quote


def test_absent_quote_degrades_to_unanchored():
    res = resolve_quote_anchor("a completely different answer", "T(e)=0")
    assert res == resolve_quote_anchor("a completely different answer", "T(e)=0")
    assert res.basis == "unanchored_quote"
    assert res.char_start is None and res.char_end is None


def test_empty_inputs_are_unanchored():
    assert resolve_quote_anchor("", "q").basis == "unanchored_quote"
    assert resolve_quote_anchor("answer", "").basis == "unanchored_quote"


def test_resolver_is_deterministic():
    answer = "x = 2 so  x =  2 again"
    for _ in range(3):
        first = resolve_quote_anchor(answer, "x =  2", hint_start=5)
        second = resolve_quote_anchor(answer, "x =  2", hint_start=5)
        assert first == second


def test_bases_are_the_closed_vocabulary():
    assert set(ANCHOR_BASES) == {
        "quote_match_unique",
        "quote_match_hint_disambiguated",
        "quote_match_first",
        "quote_match_normalized",
        "unanchored_quote",
    }


# --- validator integration --------------------------------------------------


def _divergence_proposal(
    *,
    quote: str | None,
    char_start: int | None,
    char_end: int | None,
    target_ref: dict | None = None,
) -> GradingProposal:
    divergence: dict = {"anchor_kind": "span", "criterion_id": "correctness"}
    if quote is not None:
        divergence["quote"] = quote
    if char_start is not None:
        divergence["char_start"] = char_start
        divergence["char_end"] = char_end
    attribution = {
        "error_type": "incomplete_answer",
        "evidence": "The stated identity is wrong.",
        "resolution_status": "unresolved",
        "cause_scope": "unknown",
        "first_divergence": divergence,
    }
    if target_ref is not None:
        attribution["target_ref"] = target_ref
    return GradingProposal(
        diagnosis_md="The zero-vector comparison step diverges.",
        attempt_id="att",
        practice_item_id="pi_svd_define_001",
        rubric_score=0,
        criterion_evidence=[
            CriterionEvidence(
                criterion_id="correctness",
                points_awarded=0,
                evidence="Partial derivation only.",
            )
        ],
        error_attributions=[ErrorAttribution(**attribution)],
        grader_confidence=0.8,
    )


def _validate(tmp_path, proposal, learner_answer):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    item = vault.practice_items["pi_svd_define_001"]
    return validate_codex_grading_proposal(
        proposal,
        attempt_id="att",
        item=item,
        vault=vault,
        learner_answer_md=learner_answer,
    )


def test_wrong_model_offsets_with_correct_quote_grade_succeeds(tmp_path):
    """The live bug: a one-character miscount rejected the whole exam grade."""

    answer = "The identity is (0,0) since T(e)=0 must hold."
    quote = "T(e)=0"
    true_start = answer.index(quote)
    validated = _validate(
        tmp_path,
        _divergence_proposal(
            quote=quote, char_start=true_start + 1, char_end=true_start + 1 + len(quote)
        ),
        answer,
    )
    divergence = validated.error_attributions[0].first_divergence
    assert divergence["char_start"] == true_start
    assert divergence["char_end"] == true_start + len(quote)
    assert divergence["anchor_basis"] == "quote_match_unique"
    # The raw model miscount stays visible for the disagreement-rate audit.
    assert divergence["model_reported_char_start"] == true_start + 1


def test_correct_model_offsets_record_no_disagreement(tmp_path):
    answer = "The identity is (0,0) since T(e)=0 must hold."
    quote = "T(e)=0"
    start = answer.index(quote)
    validated = _validate(
        tmp_path,
        _divergence_proposal(quote=quote, char_start=start, char_end=start + len(quote)),
        answer,
    )
    divergence = validated.error_attributions[0].first_divergence
    assert divergence["char_start"] == start
    assert "model_reported_char_start" not in divergence
    assert divergence["anchor_basis"] == "quote_match_unique"


def test_null_offsets_are_resolved_server_side(tmp_path):
    answer = "The identity is (0,0) since T(e)=0 must hold."
    validated = _validate(
        tmp_path,
        _divergence_proposal(quote="T(e)=0", char_start=None, char_end=None),
        answer,
    )
    divergence = validated.error_attributions[0].first_divergence
    assert answer[divergence["char_start"] : divergence["char_end"]] == "T(e)=0"


def test_unlocatable_quote_degrades_to_whole_answer_not_rejection(tmp_path):
    answer = "A derivation that never states the hallucinated line."
    validated = _validate(
        tmp_path,
        _divergence_proposal(quote="T(e)=42", char_start=3, char_end=10),
        answer,
    )
    divergence = validated.error_attributions[0].first_divergence
    assert divergence["anchor_kind"] == "whole_answer"
    assert divergence["anchor_basis"] == "unanchored_quote"
    assert divergence["quote"] == "T(e)=42"  # kept for display
    assert "char_start" not in divergence and "char_end" not in divergence


def test_answer_span_target_offsets_are_recomputed_not_fatal(tmp_path):
    answer = "The identity is (0,0) since T(e)=0 must hold."
    quote = "T(e)=0"
    start = answer.index(quote)
    validated = _validate(
        tmp_path,
        _divergence_proposal(
            quote=quote,
            char_start=start,
            char_end=start + len(quote),
            target_ref={
                "kind": "answer_span",
                "quote": quote,
                "char_start": start + 2,
                "char_end": start + 2 + len(quote),
            },
        ),
        answer,
    )
    ref = validated.error_attributions[0].target_ref
    assert ref["char_start"] == start
    assert answer[ref["char_start"] : ref["char_end"]] == quote
