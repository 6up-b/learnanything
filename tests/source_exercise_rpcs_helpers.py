"""What more than one test file uses to stage a picked source exercise (a test file never imports another)."""

from __future__ import annotations


def proposal_row(repository, *, proposal_id, constraints, intent, exercise, caller="tutor"):
    """One stored practice proposal naming ``exercise``, as ``find_practice`` writes it."""

    from learnloop.db.stores.practice_index import insert_proposal

    with repository.connection() as connection:
        insert_proposal(connection, id=proposal_id, created_at="2026-10-12T08:59:00Z", origin="rpc",
                        query_id="q", query_text="eigenvalues", constraints=constraints, path="direct",
                        path_reason="test", signals={}, reranked=True, rerank_status="reranked",
                        rerank_model=None, proposed=[{**exercise, "rank": 1}], exclusions={}, manifest={},
                        algorithm_version="mvp-0.19", caller=caller, caller_ref="qe_1", intent=intent)
