"""What other test files use from ``tests/test_learner_text_gaps.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients, process_learner_text
from learnloop.diagnosis.text_gaps.sources import tutor_question_text
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault
from tests.text_gap_fakes import GapLLMFake


EIGEN_GAP = LearnerGap(prerequisite_name="Eigenvalues", prerequisite_line="Scalars a matrix scales its eigenvectors by.",
                       kind="prerequisite")


def _vault(tmp_path, *, version: str = "mvp-0.16", toml: str = ""):
    paths = create_placement_vault(tmp_path / "vault", version=version)
    if toml:
        append_config_toml(paths.root, toml)
    return paths.root, Repository(paths.sqlite_path)


def _ask(root, repository, tutor, *, item="pi_diag_easy", question="What is an eigenvalue? I can't diagonalize."):
    vault = load_vault(root)
    return ask_question(vault, repository, tutor, context="practice", question_md=question,
                        practice_item_id=item, session_id="sess_1", clock=FrozenClock(NOW))


def _run(root, repository, event_id, *, llm=None, decider=None, tutor=None):
    llm = llm or GapLLMFake()
    clients = PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=(lambda: decider) if decider else None,
                              drafter=lambda: llm, tutor=(lambda: tutor) if tutor else None, embedder=None)
    text = tutor_question_text(load_vault(root), repository, event_id)
    return process_learner_text(root, repository, text, clients=clients, clock=FrozenClock(NOW))
