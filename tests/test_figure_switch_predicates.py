"""Each figure switch has one predicate, in ``learnloop.figure_admission``, and every switch under ``figures.enabled``
asks the parent itself. A goal or an offer has no switch of its own: the pre-build pass and the offer trigger admit it
wherever figures (and figures ahead of need) are on.
"""

from __future__ import annotations

from itertools import product
from types import SimpleNamespace

import pytest

from learnloop import figure_admission as FA
from learnloop.db.connection import connect
from learnloop.figures import power as P
from learnloop.figures import prefetch as PF
from learnloop.figures import records as FR
from learnloop.vault.loader import load_vault
from learnloop_sidecar import prefetch_runtime as PR
from tests.figure_fixtures import EXTRACTION, set_config
from tests.figures_prefetch_helpers import env_for, make_vault, mains  # noqa: F401 - mains: autouse

GOAL = "slide p and watch the mass left of zero move"


def _config(**figures: bool) -> SimpleNamespace:
    return SimpleNamespace(config=SimpleNamespace(figures=SimpleNamespace(**figures), teacher=None))


def _filter_records(repository) -> list[dict]:
    with connect(repository.sqlite_path, read_only=True) as connection:
        return [dict(row) for row in connection.execute(
            "SELECT rule, facts_json FROM decision_records WHERE kind = ?", (FR.KIND_FILTER,))]


@pytest.mark.parametrize(("figures", "kept"), [(False, 0), (True, 1)])
def test_a_goal_candidate_is_kept_only_with_figures_on(tmp_path, figures, kept):
    paths, repository, _vault = make_vault(tmp_path)
    set_config(paths, "figures", enabled=figures)
    vault = load_vault(paths.root)
    candidate = PF.Candidate("gap", "gap:g1", EXTRACTION, ["p3"], GOAL, "prefetch")
    assert len(PF.filter_candidates(env_for(vault, repository), [candidate], open_keys=set())) == kept
    assert _filter_records(repository) == []


@pytest.mark.parametrize(("figures", "prefetch"), list(product((False, True), repeat=2)))
def test_a_pass_and_the_offer_trigger_run_only_with_figures_ahead_of_need_on(figures, prefetch):
    vault = _config(enabled=figures, prefetch_enabled=prefetch)
    assert PF.enabled(vault) is (figures and prefetch)
    ctx = SimpleNamespace(vault=vault, repository=object(), secondary=False, figure_prefetch_inline=True)
    assert PR.runs_here(ctx) is P.prefetch_switch(vault) is PF.enabled(vault)


def test_the_teachers_visuals_switch_is_the_teachers_alone_and_a_lesson_asks_both():
    from learnloop.teacher import visuals as TV

    def vault(visuals: bool, figures: bool) -> SimpleNamespace:
        return SimpleNamespace(config=SimpleNamespace(teacher=SimpleNamespace(visuals=visuals), figures=SimpleNamespace(
            enabled=figures)))

    assert FA.teacher_visuals_enabled(vault(True, False)) is True
    assert FA.teacher_visuals_enabled(SimpleNamespace(config=SimpleNamespace(teacher=None))) is False
    for visuals, figures in product((False, True), repeat=2):
        assert TV.active(vault(visuals, figures)) is (visuals and figures)
