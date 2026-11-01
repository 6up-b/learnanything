"""Reader workbench RW6b part 1: the follow-ups' search is the sources spec's
(spec_reader_workbench_v1 §9.3 items 2-3; gates G35, G53; sources spec §8.3.3, §20).

The default search is ``propose_practice`` -> ``find_practice`` with the
injected valuer, system-initiated, over a real textbook vault and the fake
service LLM (the relevance judge is the only model call, faked):

* the exact filters ride on the stored proposal (``practice_index_proposals``);
* the session's attempted item is never proposed;
* a point-model (``item_point``) value never licenses a dated check, so the
  planner creates nothing from it.

Fakes only; no model call anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
import json

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.instructional import reader_followups as RF
from learnloop.instructional.wiring import find_practice_injections
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded


@dataclass
class _Estimate:
    minutes: float

    def as_dict(self):
        return {"minutes": self.minutes, "prior_source": "test"}


def estimator(item_id, mode, expected):
    return _Estimate(2.0)


def _attempt(paths, repository, item_id, *, points, hints=0):
    complete_self_graded_attempt(loaded(paths), repository,
                                 AttemptDraft(practice_item_id=item_id, learner_answer_md="x",
                                              attempt_type="independent_attempt", hints_used=hints),
                                 SelfGradeInput(criterion_points={"correct": points}, fatal_errors=[], confidence=3))


def test_the_default_search_is_find_practice_with_the_exact_filters_system_initiated(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    _attempt(paths, repository, "pi_determinant_2", points=4, hints=1)  # an assisted-only success
    vault = loaded(paths)
    llm = FakeServiceLLM()
    search = RF.default_search(vault, repository, injections=find_practice_injections(
        vault, estimator=estimator, screen_client=llm, judge_client=llm), rerank_client=llm)
    question = RF.Question(key="retention:facet_determinant", purpose=RF.PURPOSE_RETENTION,
                           learning_object_ids=["lo_matrices"], facet_ids=["facet_determinant"])
    constraints = RF.constraints_for(question, exclude_family_ids=["fam_revealed"])
    result = search(RF.query_for(vault, question), constraints, caller={"kind": RF.VIA, "ref": "rsd_test"})
    assert result["status"] == "ok" and result["intent"] == "retention"
    proposed = {entry.get("practice_item_id") for entry in result["items"]}
    assert "pi_determinant_2" not in proposed  # attempted: never a candidate
    with repository.connection() as connection:
        row = connection.execute("SELECT constraints_json, caller, caller_ref FROM practice_index_proposals "
                                 "WHERE id = ?", (result["proposal_id"],)).fetchone()
    stored = json.loads(row["constraints_json"])
    assert stored["unattempted_only"] is True and stored["exclude_revealed_families"] is True
    assert stored["exclude_family_ids"] == ["fam_revealed"]
    assert (row["caller"], row["caller_ref"]) == ("reader", "rsd_test")
    # Whatever the valuation said, only a licensing regime would be dated.
    picks = RF._chosen_checks(result)
    for _section, check in picks:
        assert check["licenses_system_check"] is True
    assert result["valuation"]["system_initiated"] is True
