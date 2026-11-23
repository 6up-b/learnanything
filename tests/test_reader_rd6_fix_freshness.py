"""RD6's fix round, the two freshness majors: what the lens concludes from coverage must hold for the library and the
sections as they are now. A section changed since a needed LO's rows were written there reads as unknown for it,
never as skippable (its rows are no longer read); an LO coverage tried and found nowhere is settled only against the
library it was tried in, so a reading added since is not called skippable before the LO is tried against it. Every
model is a fake."""
from __future__ import annotations

from learnloop.vault.loader import load_vault
from learnloop.source_retrieval import deliverable_path as DP
from tests.goal_lens_helpers import build_lens_vault, lens_context, levels, scoped_goal


def _earlier_row(repository, lo_id: str, section_id: str, *, like: str) -> None:
    """A judge's row for the LO on the section, written against an earlier version of it (a copy of its row on
    ``like`` with another section hash): ``SC.standing`` no longer reads it."""

    with repository.connection() as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(section_coverage)")]
        picked = ", ".join({"id": "id || ':earlier'", "section_id": "?", "section_hash": "'an earlier version'"}.get(c, c)
                           for c in columns)
        connection.execute(f"INSERT INTO section_coverage ({', '.join(columns)}) SELECT {picked} FROM section_coverage "
                           "WHERE learning_object_id = ? AND section_id = ? AND learner_override IS NULL",
                           (section_id, lo_id, like))
        connection.commit()


def _vault(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault")
    return paths, repository, scoped_goal(paths, repository)


def test_a_section_changed_since_a_needed_los_rows_is_unknown_for_it_never_skippable(tmp_path):
    paths, repository, goal_id = _vault(tmp_path)
    ctx = lens_context(paths)
    assert levels(ctx, goal_id, "ext_book")["ch_orth"]["level"] == "skippable"  # nothing needed treats it
    # The needed LO's rows on it were written against an earlier version: its only current row is another LO's
    # "not about".
    _earlier_row(repository, "lo_eigen", "ch_orth", like="ch_eigen")
    orth = levels(ctx, goal_id, "ext_book")["ch_orth"]
    assert (orth["level"], orth["mapping"], orth["reasonKey"], orth["dim"]) == ("partial", "partial", "partial_unsettled", False)


def test_an_lo_tried_and_found_nowhere_is_settled_only_against_that_library(tmp_path):
    from learnloop_sidecar.handlers import deliverables as handler
    from tests.source_retrieval_fakes import seed_source

    paths, repository = build_lens_vault(tmp_path / "vault", cover=("lo_eigen",))
    goal_id = scoped_goal(paths, repository)
    ctx = lens_context(paths)
    work = handler._work(ctx)
    keys = DP.attempt_keys(load_vault(paths.root), repository, ["lo_det"])
    with work.lock:  # as a coverage run that found no candidate for it leaves it
        work.covering[goal_id] = {"state": "done"}
        work.attempted[goal_id] = {("lo_det", keys["lo_det"])}
    assert levels(ctx, goal_id, "ext_book")["ch_det"]["level"] == "skippable"  # settled: nothing needed is there
    # A reading added since may hold it: no section is skippable until it is tried against the library as it is.
    seed_source(repository, source_id="src_more", revision_id="rev_more", extraction_id="ext_more",
                title="More determinants", units={"more_det": ("Determinants, again", [("The determinant again.", 1)])})
    det = levels(ctx, goal_id, "ext_book")["ch_det"]
    assert (det["level"], det["reasonKey"], det["dim"]) == ("partial", "partial_unsettled", False)
