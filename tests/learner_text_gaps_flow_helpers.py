"""What other test files use from ``tests/test_learner_text_gaps_flow.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault
from tests.text_gap_fakes import GapLLMFake


EIGEN_GAP = LearnerGap(prerequisite_name="Eigenvalues", prerequisite_line="Scalars a matrix scales its eigenvectors by.",
                       kind="prerequisite")


def _at(minutes: float) -> FrozenClock:
    return FrozenClock(NOW + timedelta(minutes=minutes))


def _setup(tmp_path, *, version="mvp-0.16", toml="", name="vault"):
    paths = create_placement_vault(tmp_path / name, version=version)
    if toml:
        append_config_toml(paths.root, toml)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(load_vault(paths.root), repository, clock=FrozenClock(NOW))
    return paths.root, repository


def _clients(llm=None, decider=None, tutor=None) -> PipelineClients:
    llm = llm or GapLLMFake()
    return PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=(lambda: decider) if decider else None,
                           drafter=lambda: llm, tutor=(lambda: tutor) if tutor else None, embedder=None)
