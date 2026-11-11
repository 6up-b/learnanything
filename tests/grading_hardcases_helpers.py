"""What other test files use from ``tests/test_grading_hardcases.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import ReviewFakeClient
from tests.helpers import create_basic_vault


OPENROUTER = (
    '[ai.providers.haiku]\ntype = "openrouter"\nmodel = "anthropic/claude-haiku-5.5"\n'
    'api_key_env = "OPENROUTER_API_KEY"\nresponse_format = "json_schema"\n'
)


class JudgeFake(ReviewFakeClient):
    """A grader that grades every criterion one way: ``generous`` gives full
    credit; ``strict`` marks everything down without locating an error."""

    def __init__(self, mode, **kwargs):
        super().__init__(model=f"{mode}-model", **kwargs)
        self.mode = mode

    def _pf_hardcase_grader(self, request, context):
        criteria = context["rubric"]["criteria"]
        full = self.mode == "generous"
        return request.result_model.model_validate({
            "local_analysis_md": "fake", "attempt_id": context["attempt_id"],
            "practice_item_id": context["practice_item_id"],
            "criterion_evidence": [
                {"criterion_id": c["id"], "points_awarded": float(c["points"]) if full else 0.0, "evidence": "fake"}
                for c in criteria
            ],
            "rubric_score": int(sum(c["points"] for c in criteria)) if full else 0,
            "grader_confidence": 0.8,
        })


def _vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    config = paths.root / "learnloop.toml"
    config.write_text(config.read_text(encoding="utf-8") + "\n" + OPENROUTER, encoding="utf-8")
    return load_vault(paths.root, load_environment=False)
