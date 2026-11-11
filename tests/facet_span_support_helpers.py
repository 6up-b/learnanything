"""What other test files use from ``tests/test_facet_span_support.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.ai.decisions import ChoiceAnswer, DecisionResult

from tests.tier1_decider_helpers import Decider, _no_decider


class SpanDecider(Decider):
    def __init__(self, choice):
        super().__init__()
        self.choice = choice

    def decide(self, state, questions, *, purpose):
        self.calls.append(state)
        assert purpose == "facet_span_support" and len(questions) == 1
        options = next(iter(questions.values())).options
        probabilities = {k: 0.7 if k == self.choice else 0.1 for k in options}
        # The choice field says supports; only the argmax counts.
        return DecisionResult({"verdict": ChoiceAnswer("supports", probabilities)}, self.model, 100, 0, 0.000002)


def _span_vault(tmp_path, monkeypatch, client, *, role="primary_textbook", text="SVD expresses A = U Sigma V^T."):
    from learnloop import decider_judgments as tier1
    from tests.facet_identity_actions_helpers import _vault_with_duplicate
    from tests.facet_reword_confirm_helpers import _seed

    paths, _vault, repo = _vault_with_duplicate(tmp_path)
    citation = _seed(paths, repo, role, "cited", text=text)
    monkeypatch.setattr(tier1, "client_for", (lambda *a: client) if client is not None else _no_decider)
    return paths, repo, citation


class LockProbe(SpanDecider):
    """Records whether the vault mutation lock was held when the Decider was asked."""

    def __init__(self, choice, root):
        super().__init__(choice)
        self.root = root
        self.holders = []

    def decide(self, state, questions, *, purpose):
        from learnloop.vault_lock import read_lock_holder

        self.holders.append(read_lock_holder(self.root))
        return super().decide(state, questions, purpose=purpose)
