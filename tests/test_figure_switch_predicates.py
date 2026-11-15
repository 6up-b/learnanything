"""Each figure switch has one predicate, in ``learnloop.figure_admission``, and every switch under ``figures.enabled``
asks the parent itself.

The pre-build pass and the offer trigger read ``show_me_enabled`` and ``offers_enabled`` through those predicates, so a
goal or an offer is never admitted with figures off, whatever the child switch says. Before, they read the raw
setting and were right only because the pass runs with figures on; the matrix below shows the two reads agree on
every configuration the pass reaches, so nothing a vault computes changed.
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


@pytest.mark.parametrize(("figures", "show_me", "kept", "rule"), [
    (False, True, 0, None),  # figures off: nothing kept and no record, whatever show me says
    (True, False, 0, FR.FILTER_SHOW_ME_OFF),
    (True, True, 1, None),
])
def test_a_goal_candidate_is_kept_only_with_figures_and_show_me_on(tmp_path, figures, show_me, kept, rule):
    paths, repository, _vault = make_vault(tmp_path)
    set_config(paths, "figures", enabled=figures, show_me_enabled=show_me)
    vault = load_vault(paths.root)
    candidate = PF.Candidate("gap", "gap:g1", EXTRACTION, ["p3"], GOAL, "prefetch")
    assert len(PF.filter_candidates(env_for(vault, repository), [candidate], open_keys=set())) == kept
    assert [found["rule"] for found in _filter_records(repository)] == ([rule] if rule else [])
    assert FA.show_me_enabled(vault) is (figures and show_me)


@pytest.mark.parametrize(("figures", "prefetch", "show_me", "offers"), list(product((False, True), repeat=4)))
def test_where_a_pass_runs_the_predicates_read_what_the_raw_settings_read(figures, prefetch, show_me, offers):
    vault = _config(enabled=figures, prefetch_enabled=prefetch, show_me_enabled=show_me, offers_enabled=offers)
    # The pass (and its gap candidates and filters) runs only past this guard; the offer trigger only past
    # ``runs_here``, which asks the same switch.
    if PF.enabled(vault):
        assert FA.show_me_enabled(vault) is show_me
        assert FA.offers_enabled(vault) is offers
    else:
        assert not (figures and prefetch)
    ctx = SimpleNamespace(vault=vault, repository=object(), secondary=False, figure_prefetch_inline=True)
    assert PR.runs_here(ctx) is P.prefetch_switch(vault) is PF.enabled(vault)


@pytest.mark.parametrize("name", ["predictions_enabled", "region_enabled", "revisions_enabled"])
def test_the_feature_switches_sit_under_figures_enabled(name):
    predicate = getattr(FA, name)
    assert predicate(_config(enabled=True, **{name: True})) is True
    assert predicate(_config(enabled=True, **{name: False})) is False
    assert predicate(_config(enabled=False, **{name: True})) is False
    assert predicate(SimpleNamespace(config=SimpleNamespace(figures=None))) is False


def test_the_teachers_visuals_switch_is_the_teachers_alone_and_a_lesson_asks_all_three():
    from learnloop.teacher import visuals as TV

    def vault(visuals: bool, figures: bool, show_me: bool) -> SimpleNamespace:
        return SimpleNamespace(config=SimpleNamespace(teacher=SimpleNamespace(visuals=visuals), figures=SimpleNamespace(
            enabled=figures, show_me_enabled=show_me)))

    assert FA.teacher_visuals_enabled(vault(True, False, False)) is True
    assert FA.teacher_visuals_enabled(SimpleNamespace(config=SimpleNamespace(teacher=None))) is False
    for visuals, figures, show_me in product((False, True), repeat=3):
        assert TV.active(vault(visuals, figures, show_me)) is (visuals and figures and show_me)
