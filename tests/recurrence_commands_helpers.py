"""What other test files use from ``tests/test_recurrence_commands.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.ai.spend import SpendCaps
from learnloop.diagnosis.recurrence.guard import BUILTIN_SUITE, run_guard

from tests.recurrence_fakes import M1_CAUSE_A, M1_CAUSE_B, M1_DIAGNOSER_B, JudgeFake, write_m1_run


CAPS = SpendCaps(max_candidates=100, max_pairs=100, max_retries=20, max_calls=100, max_total_tokens=500_000, max_estimated_usd=1.0)


def _judge_model(vault) -> str:
    from learnloop.diagnosis.recurrence.guard import configured_judge_model

    return configured_judge_model(vault) or "fake-model"


def _guard_judge(false_merge: str | None = None, *, model: str = "fake-model") -> JudgeFake:
    """Says ``different`` on every negative pair (``same`` on positives),
    except a planted false merge on the named case's statements."""

    negatives = {(case.statement_a, case.statement_b) for case in BUILTIN_SUITE if case.expected == "different"}
    # The planted M1 case (write_m1_run): authored A vs B, and A vs the diagnoser's B.
    negatives |= {(M1_CAUSE_A, M1_CAUSE_B), (M1_CAUSE_A, M1_DIAGNOSER_B)}
    target = next((case for case in BUILTIN_SUITE if case.case_id == false_merge), None)

    def decide(left: str, right: str) -> str:
        pair = {(left, right), (right, left)}
        if target is not None and pair & {(target.statement_a, target.statement_b)}:
            return "same"
        return "different" if pair & negatives else "same"

    return JudgeFake(decide, model=model)


def _pass_guard(tmp_path, vault, repository, *, judge=None, linked=False, name="m1-run", **kwargs):
    """The guard on the built-in suite plus one M1 run (the citation path checked)."""

    run_dir = tmp_path / name
    write_m1_run(run_dir, run_id=name, linked=linked)
    return run_guard(vault, repository, caps=CAPS, from_run=run_dir,
                     judge_client=judge or _guard_judge(model=_judge_model(vault)), **kwargs)
