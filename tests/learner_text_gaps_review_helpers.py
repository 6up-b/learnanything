"""What other test files use from ``tests/test_learner_text_gaps_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from contextlib import closing
from datetime import timedelta

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import learner_gaps as store
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients, process_learner_text
from learnloop.diagnosis.text_gaps.sources import StuckText, tutor_question_text
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, append_config_toml, create_placement_vault
from tests.text_gap_fakes import GapLLMFake


EIGEN_GAP = LearnerGap(prerequisite_name="Eigenvalues", prerequisite_line="Scalars a matrix scales its eigenvectors by.",
                       kind="prerequisite")
EIGENVECTOR_GAP = LearnerGap(prerequisite_name="Eigenvectors", prerequisite_line="Vectors a matrix only scales.",
                             kind="prerequisite")
BELIEF = LearnerGap(belief_statement="Every matrix can be diagonalized.", kind="misconception")


def _at(minutes: float) -> FrozenClock:
    return FrozenClock(NOW + timedelta(minutes=minutes))


def _vault(tmp_path, *, version: str = "mvp-0.16", toml: str = "", sync: bool = False):
    paths = create_placement_vault(tmp_path / "vault", version=version)
    if toml:
        append_config_toml(paths.root, toml)
    repository = Repository(paths.sqlite_path)
    if sync:
        sync_vault_state(load_vault(paths.root), repository, clock=FrozenClock(NOW))
    return paths.root, repository


def _ask(root, repository, tutor, *, item="pi_diag_easy", question="What is an eigenvalue?", minutes=0.0):
    return ask_question(load_vault(root), repository, tutor, context="practice", question_md=question,
                        practice_item_id=item, session_id="sess_1", clock=_at(minutes))["event_id"]


def _clients(llm=None, *, decider=None, tutor=None) -> PipelineClients:
    llm = llm or GapLLMFake()
    return PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=(lambda: decider) if decider else None,
                           drafter=lambda: llm, tutor=(lambda: tutor) if tutor else None, embedder=None)


def _run(root, repository, event_id, llm, *, tutor=None, decider=None, minutes=0.0):
    text = tutor_question_text(load_vault(root), repository, event_id)
    return process_learner_text(root, repository, text, clients=_clients(llm, tutor=tutor, decider=decider),
                                clock=_at(minutes))


def _gaps(repository):
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return store.gaps(connection)


def _jobs(repository):
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return store.jobs(connection)


def _created_los(root):
    return sorted(lo for lo in load_vault(root).learning_objects if lo.startswith("lo_ltg_"))


def _fail_once(monkeypatch, module, name):
    original = getattr(module, name)
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError(f"{name} failed once")
        return original(*args, **kwargs)

    monkeypatch.setattr(module, name, flaky)
    return calls


class _StuckSource:
    """The stuck marker as a fake: ``stuck`` says whether the next answer is one."""

    def __init__(self, *, stuck: bool = False):
        self.stuck = stuck
        self.lookups: list[str] = []

    def stuck_texts(self, connection):
        raise AssertionError("recording an answer never scans every stuck answer")

    def stuck_text(self, connection, attempt_id):
        self.lookups.append(attempt_id)
        if not self.stuck:
            return None
        return StuckText(attempt_id=attempt_id, practice_item_id="pi_diag_easy", learning_object_id="lo_diag",
                         subject_id="linear-algebra", text="I don't get what an eigenvalue is", created_at=NOW_ISO)


def _self_graded(root, repository, *, minutes, points=0.0, item="pi_diag_easy", complete=False):
    """One recorded answer; ``complete`` also runs the doors' post-attempt pipeline."""

    from learnloop.attempts.post_attempt import run_post_attempt_pipeline

    grade = SelfGradeInput(criterion_points={"correctness": points}, confidence=2)
    result = complete_self_graded_attempt(
        load_vault(root), repository,
        AttemptDraft(practice_item_id=item, learner_answer_md="I don't get what an eigenvalue is", hints_used=0,
                     attempt_type="independent_attempt"),
        grade, clock=_at(minutes),
    )
    if complete:
        run_post_attempt_pipeline(load_vault(root), repository, result=result, self_grade=grade, clock=_at(minutes))
    return result
