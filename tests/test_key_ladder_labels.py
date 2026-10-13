"""S1 (G6): the verifier ladder labels every answer key honestly (§7.3)."""
from __future__ import annotations

import pytest

from learnloop.content.authoring import pf_sandbox
from learnloop.content.authoring.source_exercise_import import run_key_ladder
from tests.pf_fakes import ALWAYS_TRUE_CHECK
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded, service_clients

needs_bwrap = pytest.mark.skipif(not pf_sandbox.sandbox_available(), reason="bubblewrap is not installed")
NEVER_CHECK = "def check(reference, answer):\n    return False\n"
BROKEN_CHECK = "def check(reference, answer)\n    return True\n"
STEM = "1. An eigenvalue t satisfies 3t + 5 = 20; solve 3x + 5 = 20 for x to find the eigenvalue."
SOLUTION = {"status": "found", "text": "1. Subtracting 5 gives 3x = 15, so the eigenvalue is x = 5.",
            "span_ids": ["t12"], "page": 30, "judgment_id": "ssm_x"}


@pytest.fixture
def env(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    return loaded(paths), repository


def _ladder(env, llm, *, stem=STEM, reference="5", solution=None, cited=""):
    vault, repository = env
    return run_key_ladder(vault, repository, subject_id="sei_test", stem=stem, reference=reference,
                          solution=solution, cited_quote=cited, clients=service_clients(llm))


def test_rung_one_the_books_solution_quote_verified_and_supported(env):
    result = _ladder(env, FakeServiceLLM(), solution=SOLUTION,
                     cited="Subtracting 5 gives 3x = 15, so the eigenvalue is x = 5.")
    assert (result.key_status, result.rung, result.verified) == ("book_solution", "book_solution", True)
    assert result.verification["book_solution"]["quote_found"] is True
    assert result.ledger_ids  # every verdict ledgered


def test_a_quote_not_in_the_passage_falls_to_the_panel(env, monkeypatch):
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    result = _ladder(env, FakeServiceLLM(), solution=SOLUTION, cited="the answer is plainly five here")
    assert result.rung == "panel"
    assert result.verification["book_solution"]["quote_found"] is False


def test_the_books_solution_contradicting_the_key_is_disputed(env):
    result = _ladder(env, FakeServiceLLM(), reference="7", solution=SOLUTION,
                     cited="Subtracting 5 gives 3x = 15, so the eigenvalue is x = 5.")
    assert (result.key_status, result.verification["disputed_by"]) == ("disputed", "book_solution")
    assert not result.verified


@needs_bwrap
def test_rung_two_panel_plus_sympy_is_checked(env):
    result = _ladder(env, FakeServiceLLM())
    assert result.key_status == "checked" and result.verified
    assert result.verification["panel"]["symbolic_status"] == "confirmed"


def test_a_numeric_key_without_a_sandbox_is_panel_agrees_unconfirmed(env, monkeypatch):
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    result = _ladder(env, FakeServiceLLM())
    assert result.key_status == "panel_agrees_unconfirmed" and not result.verified
    assert result.verification["panel"]["symbolic_status"] == "sandbox_unavailable"
    assert result.verification["panel"]["model_agree"] == 3


@needs_bwrap
def test_a_failed_sympy_run_is_panel_agrees_unconfirmed(env):
    result = _ladder(env, FakeServiceLLM(sympy_check=BROKEN_CHECK))
    assert result.key_status == "panel_agrees_unconfirmed"
    assert result.verification["panel"]["symbolic_status"] == "sandbox_error"


def test_no_check_written_is_panel_agrees_unconfirmed(env):
    llm = FakeServiceLLM()
    llm.sympy_check = ""  # the judge wrote no sympy check for a numeric answer
    result = _ladder(env, llm)
    assert result.key_status == "panel_agrees_unconfirmed"
    assert result.verification["panel"]["symbolic_status"] == "no_check_written"


@needs_bwrap
def test_a_degenerate_check_is_panel_agrees_unconfirmed(env):
    result = _ladder(env, FakeServiceLLM(sympy_check=ALWAYS_TRUE_CHECK))
    assert result.key_status == "panel_agrees_unconfirmed"
    assert result.verification["panel"]["symbolic_status"] == "degenerate_check"


@needs_bwrap
def test_a_symbolic_check_that_rejects_the_agreement_is_disputed(env):
    result = _ladder(env, FakeServiceLLM(sympy_check=NEVER_CHECK))
    assert (result.key_status, result.verification["disputed_by"]) == ("disputed", "symbolic_check")


def test_a_prose_key_with_agreeing_solves_is_panel_agrees(env):
    stem = "3. Explain why the determinant changes sign when two rows of a matrix are swapped."
    llm = FakeServiceLLM(panel_answers={"determinant changes sign": "the determinant is multiplied by -1"})
    result = _ladder(env, llm, stem=stem, reference="the determinant is multiplied by -1")
    assert (result.key_status, result.verified) == ("panel_agrees", True)
    assert result.verification["panel"]["symbolic_status"] == "not_applicable"


def test_a_panel_that_agrees_on_another_answer_disputes_the_key(env, monkeypatch):
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    result = _ladder(env, FakeServiceLLM(), reference="7")
    assert (result.key_status, result.verification["disputed_by"]) == ("disputed", "panel")
    assert result.verification["panel"]["panel_answer"] == "5"


def test_a_panel_that_cannot_agree_leaves_the_models_answer(env):
    stem = "Prove that every bounded monotone sequence converges."
    result = _ladder(env, FakeServiceLLM(), stem=stem, reference="by completeness")
    assert result.key_status == "model_answer" and not result.verified


def test_a_metered_route_without_a_price_is_skipped_and_labelled(env):
    llm = FakeServiceLLM()
    llm.provider_type = "openrouter"
    result = _ladder(env, llm)
    assert result.key_status == "model_answer" and result.rung == "skipped"
    assert "source_service.llm_price_per_million" in result.skip_reason


def test_the_daily_cap_skips_the_ladder(env):
    vault, repository = env
    vault.config.source_service.max_daily_cost_usd = 0.0
    result = run_key_ladder(vault, repository, subject_id="sei_cap", stem=STEM, reference="5", solution=None,
                            clients=service_clients(FakeServiceLLM()))
    assert result.key_status == "model_answer" and "daily cap" in result.skip_reason


# -- Live sanity run: worked-solution keys were disputed by a check that could not read them --
#
# An imported exercise's key is a worked solution (prose and LaTeX), not a bare
# expression. The ladder handed the whole key to the judge's sympy check, whose
# ``sympify(reference)`` raised and returned False, so correct keys with 6/6
# panel agreement were labelled "disputed". The sandbox now gets the key's
# "Final answer:" line when it has one (as PF passes its references), and a key
# the sandbox cannot read leaves the symbolic check unconfirmed, never rejected.

PARSING_CHECK = (
    "import sympy\n"
    "def check(reference, answer):\n"
    "    try:\n"
    "        return sympy.simplify(sympy.sympify(reference) - sympy.sympify(answer)) == 0\n"
    "    except Exception:\n"
    "        return False\n"
)
WORKED_KEY = "Subtract 5 from both sides, so $3x = 15$. Dividing by 3, the eigenvalue is $x = 5$."


class WorkedSolutionJudge(FakeServiceLLM):
    """The live judge: it reads the worked solution, accepts the solves, and
    writes a check that parses the reference it is given."""

    def _EquivalenceResult(self, request, context):
        from learnloop.content.authoring import pf_contracts as C

        return C.EquivalenceResult(answer_kind="symbolic", agreements=[True] * len(context["answers"]),
                                   sympy_check=PARSING_CHECK)


@needs_bwrap
def test_a_worked_solution_the_check_cannot_read_is_unconfirmed_not_disputed(env):
    result = _ladder(env, WorkedSolutionJudge(), reference=WORKED_KEY)
    assert result.key_status == "panel_agrees_unconfirmed" and not result.verified
    assert "disputed_by" not in result.verification
    panel = result.verification["panel"]
    assert (panel["symbolic_status"], panel["model_agree"]) == ("reference_unreadable", 3)
    assert panel["symbolic_reference"] == "whole_key"


@needs_bwrap
def test_a_worked_solution_with_a_final_answer_line_is_checked(env):
    result = _ladder(env, WorkedSolutionJudge(), reference=WORKED_KEY + "\n\nFinal answer: 5")
    assert (result.key_status, result.verified) == ("checked", True)
    panel = result.verification["panel"]
    assert (panel["symbolic_status"], panel["symbolic_reference"]) == ("confirmed", "final_answer_line")


@needs_bwrap
def test_a_readable_key_the_check_rejects_is_still_disputed(env):
    result = _ladder(env, WorkedSolutionJudge(), reference=WORKED_KEY + "\n\nFinal answer: 7")
    assert (result.key_status, result.verification["disputed_by"]) == ("disputed", "symbolic_check")
    assert result.verification["panel"]["symbolic_status"] == "rejected"
