"""Adaptive difficulty AD2+AD3, fix round 9: focused regressions beside the A8 contract test
(``tests/test_ad23_contract.py``, which is the guarantee).

* F20/F26/F27 (R1): an attempt whose ANSWERED revision is held out is filtered at the source, so
  nothing derived from it (minutes, the moderator window, history) reads it;
* F21 (R2): the commissioned request is revalidated before it is sent and refused when it quotes
  withheld material;
* F32 (R6): with the predicate unavailable the relatedness proposal prepares nothing, and SendGuard
  refuses whatever the job quotes.

Fakes only: no network, no model call, no paid call.
"""

from __future__ import annotations

from contextlib import closing

import pytest

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import COUPLED, ProposalLLM, ad23_vault, rows
from tests.test_ad23_contract import T0, _hold_out, _predicate_raises, _protect, _copy_item  # noqa: F401


def test_an_attempt_on_a_held_out_answered_revision_is_filtered_at_the_source(tmp_path, monkeypatch):
    """R1 (Codex verify F20, F26, F27): ``pi_hist``'s current revision is public, but one answer was
    given to an earlier revision cut from held-out material. The view's attempts leave that answer
    out, so the practice minutes and the LO's window cutoff never read it (failed before: the
    answer's 1,000 minutes and its time were read)."""

    from learnloop.adaptive_difficulty.material_view import material_view

    from tests.test_ad23_contract import _base

    paths = _base(tmp_path)
    _protect(paths)
    _hold_out(monkeypatch)
    view = material_view(load_vault(paths.root), Repository(paths.sqlite_path))
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        visible = view.attempts(connection)
        assert all(row.get("plan_presentation_id") != "pp_hist_r9" for row in visible)
        assert {row["practice_item_id"] for row in visible} == {"pi_hist"}  # its public, earlier answer
        assert max(view.practice_minutes(connection)) < 1000.0
        assert view.window_cutoff(connection, ["lo_m1"]) < "2026-10-12T08:00:00Z"
        assert view.presentation(connection, "pp_hist_r9") is None


def test_a_commissioned_request_quoting_withheld_material_is_refused_before_it_is_sent(tmp_path, monkeypatch):
    """R2: the send-time revalidation refuses a request that quotes a withheld item's stem, id, a
    facet or a surface family only withheld material names, and passes one that quotes none."""

    from learnloop.adaptive_difficulty.generation import CommissionedRequestGuard, ProtectedRequest

    from tests.test_ad23_contract import _base

    paths = _base(tmp_path)
    _protect(paths)
    _hold_out(monkeypatch)
    guard = CommissionedRequestGuard()
    seen = guard.vault_view(load_vault(paths.root), Repository(paths.sqlite_path))
    assert "pi_secret" not in seen.practice_items and "pi_p1" in seen.practice_items
    guard("A request about pi_p1 in fam_public, facet recall.")
    for leak in ("Write like SENTINEL_STEM_AX9: a held-out exam question about bases.", "item pi_secret",
                 "facet SENTINEL_FACET_AX9", "family SENTINEL_FAMILY_AX9",
                 "SENTINEL_HIST_AX9: the earlier held-out revision."):
        with pytest.raises(ProtectedRequest):
            guard(leak)


def test_with_the_predicate_unavailable_relatedness_prepares_nothing(tmp_path, monkeypatch):
    """R6 (Codex verify F32): learned coupling on and a usable route, predicate unavailable: the
    proposal returns ``unavailable`` before it prepares, claims or sends anything (failed before:
    it prepared the LO's units and could send)."""

    from learnloop.adaptive_difficulty import relatedness as R

    paths = ad23_vault(tmp_path, ad=COUPLED)
    _predicate_raises(monkeypatch)
    llm = ProposalLLM()
    outcome = R.propose_subject(load_vault(paths.root), Repository(paths.sqlite_path), "linear-algebra", client=llm)
    assert outcome.status == "unavailable" and llm.prompts == []
    assert rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM ad_relatedness_runs")[0]["n"] == 0


def test_send_guard_refuses_an_unavailable_predicate_whatever_the_job_quotes(tmp_path, monkeypatch):
    """R6 (Codex verify F32): a job quoting no item and no identity is refused too."""

    from learnloop.adaptive_difficulty.sending import ProtectedContent, SendGuard

    paths = ad23_vault(tmp_path)
    _predicate_raises(monkeypatch)
    guard = SendGuard(load_vault(paths.root), Repository(paths.sqlite_path))
    with pytest.raises(ProtectedContent, match="unavailable"):
        guard.check("the request")
