"""What other test files use from ``tests/test_teacher_te2_probes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from learnloop.algorithm_versions import TEACHER_PROBES_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.followup_run.jobs import process_next_job
from learnloop.teacher import probes as PR
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault

from tests.structured_ai import StructuredClientFake
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients, plan_turn


TAG = TEACHER_PROBES_ALGORITHM_VERSION
T0 = datetime(2026, 11, 6, 15, 0, tzinfo=UTC)
READING = "treats the eigenvector as if it were the eigenvalue"


class ProbeAuthor(StructuredClientFake):
    """FG1's frontier author, faked: two criteria, one failing prediction per reading; counts its calls."""

    model = "fake-frontier"
    provider_name = "fake_author"
    # The subscription plan: a lesson probe is never written on a metered client (§24 row TE2, Codex review F5).
    provider_type = "chatgpt_plan"

    def __init__(self, *, prompt: str = "For the map [[3,0],[0,7]], name a vector it only stretches, and by how much.",
                 error: Exception | None = None) -> None:
        self.calls = 0
        self.contexts: list = []
        self.prompt = prompt
        self.error = error

    def run_followup_probe_authoring(self, context):
        from learnloop.diagnosis.ai_contracts import (
            FollowupProbeAuthored,
            FollowupProbeCriterion,
            FollowupProbeManipulation,
            FollowupProbePrediction,
        )

        self.calls += 1
        self.contexts.append(context)
        if self.error is not None:
            raise self.error
        refs = [row["hypothesis_ref"] for row in context.hypotheses]
        return FollowupProbeAuthored(
            prompt_md=f"On {context.learning_object_title}: {self.prompt} (#{self.calls})",
            expected_answer_md="ibis heron: (1, 0) by three",
            surface_suffix=f"lesson_{self.calls}",
            criteria=[FollowupProbeCriterion(id="names_vector", description="Names an eigenvector.", points=2),
                      FollowupProbeCriterion(id="names_factor", description="Names its eigenvalue.", points=2)],
            predictions=[FollowupProbePrediction(hypothesis_ref=ref, fails_criteria=[("names_factor", "names_vector")[i % 2]])
                         for i, ref in enumerate(refs)],
            intended_manipulations=[FollowupProbeManipulation(axis=axis, rationale="A fresh question.")
                                    for axis in ("surface_wording", "answer_contract", "rubric")],
        )


def probe_turn(context, *, readings=(READING,), p=0.4, node="n1", message="Before we start, one quick question."):
    turn = plan_turn(context)
    turn["message"] = message
    turn["requests"].append({"action": "serve_probe", "node": node, "readings": list(readings), "p": p})
    return turn


class _Lesson:
    def __init__(self, tmp_path, turns, *, version=TAG, config=None):
        from tests.ux_phase1_support import set_config

        self.paths, self.repository = build_teacher_vault(tmp_path / "vault", version=version)
        if config:
            set_config(self.paths.root, config)
        self.paths.root.joinpath("learnloop.toml")
        self.fake = TeacherFake(turns)
        self.author = ProbeAuthor()
        self.minute = 0
        self.view = S.open_lesson(self.vault(), self.repository, entry="learning_object",
                                  learning_object_ids=["lo_eigen"], clients=clients(self.fake), clock=self.clock())
        self.lesson_id = self.view["lesson_id"]

    def vault(self):
        return load_vault(self.paths.root)

    def clock(self):
        self.minute += 1
        return FrozenClock(T0 + timedelta(minutes=self.minute))

    def generate(self):
        outcomes = []
        while True:
            outcome = process_next_job(self.vault(), self.repository, owner="test",
                                       clients=SimpleNamespace(author=self.author), clock=self.clock())
            if outcome is None:
                return outcomes
            outcomes.append(outcome)

    def look(self):
        self.view = S.view_lesson(self.vault(), self.repository, self.lesson_id, clock=self.clock())
        return self.view

    def act(self, action, payload=None, *, turns=None, right=None):
        if turns is not None:
            self.fake.turns = list(turns)
        if right is not None:
            self.fake.full = right
        self.view = S.take_turn(self.vault(), self.repository, lesson_id=self.lesson_id, action=action,
                                payload=payload or {}, clients=clients(self.fake), clock=self.clock())
        return self.view

    def rows(self, sql, params=()):
        with self.repository.connection() as connection:
            return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _probe(lesson):
    from learnloop.db.stores import lessons as store

    with lesson.repository.connection() as connection:
        return PR.probes(store.turns(connection, lesson.lesson_id))[0]
