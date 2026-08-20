"""Meas §D1 ``measurement_rank`` — plan item 3.4.

"The number of independent dimensions the item pool can actually resolve, against
the number of facets declared." Independence is behavioural (standing constraint
11): a facet's measurement signature is the set of observation units that can see
it — criterion signatures (correlation group, else criterion id) plus observing
practice items. Identical signatures are ONE dimension; an empty signature is
none at all. Coverage here is the counting rule, the explicit deficit split, and
that publishing the rank merges nothing.
"""

from __future__ import annotations

from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.learner.identifiability import (
    ProposalView,
    analyze_identifiability,
    build_registry_view,
    declared_facets,
    graph_identifiability_report,
    measurement_rank,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW
from tests.test_identifiability_doctor import _build_registry_vault


def _view(**kwargs) -> ProposalView:
    return ProposalView(**kwargs)


def test_rank_equals_dimensions_when_signatures_are_distinct():
    """Three facets, three distinct observing criteria — full rank, zero deficit."""

    view = _view(
        facet_repairs={"fa": ("r1",), "fb": ("r2",), "fc": ("r3",)},
        criterion_targets=[
            {"criterion_id": "c1", "correlation_group": "g1", "facet": "fa", "capability": "retrieval"},
            {"criterion_id": "c2", "correlation_group": "g2", "facet": "fb", "capability": "retrieval"},
            {"criterion_id": "c3", "correlation_group": "g3", "facet": "fc", "capability": "retrieval"},
        ],
    )
    rank = measurement_rank(view)
    assert rank.facets_declared == 3
    assert rank.independent_dimensions == 3
    assert rank.deficit == 0
    assert rank.deficit_from_collapse == 0
    assert rank.deficit_from_unobserved == 0
    assert rank.collapsed_groups == ()
    assert rank.rank_ratio == 1.0


def test_two_facets_sharing_an_observing_signature_are_one_dimension():
    """The §D1 criterion: nothing in the pool moves one without moving the other."""

    view = _view(
        facet_repairs={"fa": ("r",), "fb": ("r",), "fc": ("rx",)},
        criterion_targets=[
            # fa and fb are observed by exactly the same correlation group.
            {"criterion_id": "c1", "correlation_group": "g1", "facet": "fa", "capability": "retrieval"},
            {"criterion_id": "c1", "correlation_group": "g1", "facet": "fb", "capability": "retrieval"},
            {"criterion_id": "c2", "correlation_group": "g2", "facet": "fc", "capability": "retrieval"},
        ],
    )
    rank = measurement_rank(view)
    assert rank.facets_declared == 3
    assert rank.independent_dimensions == 2       # not 3
    assert rank.deficit == 1
    assert rank.deficit_from_collapse == 1
    assert rank.deficit_from_unobserved == 0
    assert rank.collapsed_groups == (("fa", "fb"),)


def test_partial_overlap_is_still_two_dimensions():
    """Sharing *a* criterion is not sharing a signature — only identity collapses."""

    view = _view(
        facet_repairs={"fa": (), "fb": ()},
        criterion_targets=[
            {"criterion_id": "c1", "correlation_group": "g1", "facet": "fa", "capability": "retrieval"},
            {"criterion_id": "c1", "correlation_group": "g1", "facet": "fb", "capability": "retrieval"},
            # One extra criterion sees fb alone, so evidence can separate them.
            {"criterion_id": "c2", "correlation_group": "g2", "facet": "fb", "capability": "retrieval"},
        ],
    )
    rank = measurement_rank(view)
    assert rank.independent_dimensions == 2
    assert rank.deficit == 0
    assert rank.collapsed_groups == ()


def test_unobserved_facet_contributes_no_dimension_and_the_deficit_is_split():
    """A declared facet nothing observes is uninstrumented (§D2), not synonymous."""

    view = _view(
        facet_repairs={"fa": (), "fb": (), "fdark": (), "fdarker": ()},
        criterion_targets=[
            {"criterion_id": "c1", "correlation_group": "g1", "facet": "fa", "capability": "retrieval"},
            {"criterion_id": "c1", "correlation_group": "g1", "facet": "fb", "capability": "retrieval"},
        ],
    )
    rank = measurement_rank(view)
    assert rank.facets_declared == 4
    assert rank.independent_dimensions == 1
    # Stated outright, and split by cause rather than left to be subtracted.
    assert rank.deficit == 3
    assert rank.deficit_from_unobserved == 2
    assert rank.deficit_from_collapse == 1
    assert rank.deficit == rank.deficit_from_unobserved + rank.deficit_from_collapse
    assert rank.unobserved_facets == ("fdark", "fdarker")
    assert rank.collapsed_groups == (("fa", "fb"),)
    assert rank.rank_ratio == 0.25


def test_item_pool_observations_are_measurement_dimensions():
    """§D1 is about what the *item pool* can resolve, not only rubric criteria.

    An item observing {a, b} and nothing else means a and b always move together:
    one dimension. A second item that observes b alone separates them.
    """

    shared = _view(
        facet_repairs={"fa": (), "fb": ()},
        item_observations={"pi_1": ("fa", "fb")},
    )
    rank = measurement_rank(shared)
    assert rank.independent_dimensions == 1
    assert rank.collapsed_groups == (("fa", "fb"),)

    separated = _view(
        facet_repairs={"fa": (), "fb": ()},
        item_observations={"pi_1": ("fa", "fb"), "pi_2": ("fb",)},
    )
    assert measurement_rank(separated).independent_dimensions == 2
    assert measurement_rank(separated).deficit == 0


def test_criteria_and_items_are_distinct_observation_units():
    """A criterion named ``x`` and an item named ``x`` must not alias each other."""

    view = _view(
        facet_repairs={"fa": (), "fb": ()},
        criterion_targets=[
            {"criterion_id": "shared", "correlation_group": "shared", "facet": "fa", "capability": "retrieval"},
        ],
        item_observations={"shared": ("fb",)},
    )
    assert measurement_rank(view).independent_dimensions == 2


def test_declared_facets_covers_every_standing_obligation():
    """Registry entries, recipe components, criterion targets and observed facets."""

    view = _view(
        facet_repairs={"registry_only": ()},
        recipe_components=[{"facet": "recipe_only", "capability": "coordination"}],
        criterion_targets=[
            {"criterion_id": "c1", "correlation_group": "g1", "facet": "criterion_only", "capability": "retrieval"},
        ],
        item_observations={"pi_1": ("item_only",)},
    )
    assert declared_facets(view) == {"registry_only", "recipe_only", "criterion_only", "item_only"}
    rank = measurement_rank(view)
    assert rank.facets_declared == 4
    # criterion_only and item_only are observed; the other two are not.
    assert rank.independent_dimensions == 2
    assert rank.unobserved_facets == ("recipe_only", "registry_only")


def test_empty_view_abstains_rather_than_dividing_by_zero():
    rank = measurement_rank(_view())
    assert rank.facets_declared == 0
    assert rank.independent_dimensions == 0
    assert rank.deficit == 0
    assert rank.rank_ratio is None


def test_as_dict_publishes_the_rank_and_the_deficit():
    view = _view(
        facet_repairs={"fa": (), "fb": (), "fdark": ()},
        item_observations={"pi_1": ("fa", "fb")},
    )
    payload = measurement_rank(view).as_dict()
    assert payload["measurement_rank"] == payload["independent_dimensions"] == 1
    assert payload["facets_declared"] == 3
    assert payload["deficit"] == 2
    assert payload["deficit_from_unobserved"] == 1
    assert payload["deficit_from_collapse"] == 1
    assert payload["rank_ratio"] == round(1 / 3, 6)
    assert payload["collapsed_groups"] == [["fa", "fb"]]
    assert payload["unobserved_facets"] == ["fdark"]


# -- the real registry view + the published report ----------------------------


def test_registry_view_rank_counts_items_and_criteria(tmp_path):
    """The doctor's own fixture: 2 facets, one observed by an item + a criterion."""

    paths = _build_registry_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    rank = measurement_rank(build_registry_view(vault, "linear-algebra"))
    assert rank.facets_declared == 2
    assert rank.independent_dimensions == 1
    assert rank.deficit == 1
    # facet_pick is required by the blueprint but observed by nothing at all.
    assert rank.unobserved_facets == ("facet_pick",)
    assert rank.deficit_from_collapse == 0
    assert rank.collapsed_groups == ()


def test_graph_identifiability_report_publishes_the_rank(tmp_path):
    paths = _build_registry_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))

    report = graph_identifiability_report(vault, repository, subject_id="linear-algebra")
    subject = report["subjects"][0]
    rank = subject["measurement_rank"]
    assert rank["independent_dimensions"] == 1
    assert rank["facets_declared"] == 2
    assert rank["deficit"] == 1
    assert report["totals"]["measurement_rank"] == {
        "facets_declared": 2,
        "independent_dimensions": 1,
        "deficit": 1,
    }


def test_computing_the_rank_triggers_no_merge(tmp_path):
    """§D1 review, never auto-merge: the analysis proposes, a human decides.

    Running the report without ``schedule_probes`` publishes the rank and leaves
    the generation-need and proposal tables untouched, even though the view has
    an unobserved facet and (in general) collapse candidates.
    """

    paths = _build_registry_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))

    report = graph_identifiability_report(vault, repository, subject_id="linear-algebra")
    assert report["subjects"][0]["measurement_rank"]["deficit"] == 1
    assert report["totals"]["scheduled_probes"] == 0
    assert repository.synthesis_generation_needs(subject_id="linear-algebra") == []
    with repository.connection() as connection:
        merges = connection.execute("SELECT COUNT(*) FROM facet_merges").fetchone()[0]
    assert merges == 0
    # The vault-side alias table (where a collapse would actually land) carries
    # no redirect either: the rank named a candidate and changed no vocabulary.
    aliases = load_vault(paths.root).facet_aliases
    assert {src: dst for src, dst in aliases.items() if src != dst} == {}


def test_rank_does_not_disturb_the_seven_checks(tmp_path):
    """The rank reads item observations; the checks deliberately do not.

    ``analyze_identifiability`` must produce the same findings whether or not the
    view carries the item pool, so publishing the rank cannot change what the
    doctor reports or schedules.
    """

    paths = _build_registry_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    view = build_registry_view(vault, "linear-algebra")
    assert view.item_observations                      # the pool is populated
    stripped = ProposalView(
        facet_repairs=view.facet_repairs,
        criterion_targets=view.criterion_targets,
        recipe_components=view.recipe_components,
        recipes=view.recipes,
        planted_profiles=view.planted_profiles,
        criterion_fingerprints=view.criterion_fingerprints,
    )
    assert [f.as_dict() for f in analyze_identifiability(view)] == [
        f.as_dict() for f in analyze_identifiability(stripped)
    ]


def test_rank_on_the_real_linear_algebra_fixture(tmp_path):
    """§5.8.2's measured result keeps both deficit causes explicit.

    The spec recorded 14/39 facets; the fixture has gained practice items since,
    including one composite coordinate-operations exercise that observes three
    facets together. The pool therefore has a large non-instrumentation deficit
    plus one truthful three-facet collapse candidate; rank analysis merges none.
    """

    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "linear_algebra"
    vault = load_vault(fixture)                        # read-only; never mutated
    view = build_registry_view(vault, None)
    rank = measurement_rank(view)
    assert rank.facets_declared == 39
    assert rank.independent_dimensions >= 14
    assert rank.deficit > 20
    assert rank.deficit == rank.deficit_from_unobserved + rank.deficit_from_collapse
    assert rank.deficit_from_unobserved > 20
    assert rank.deficit_from_collapse == 2
    assert len(rank.collapsed_groups) == 1
    (collapsed,) = rank.collapsed_groups
    assert len(collapsed) == 3
    assert tuple(sorted(view.item_observations["pi_exercise_01kyjb8p3e84wbn812gw8sdhxq"])) == collapsed
    assert rank.rank_ratio is not None and 0.3 < rank.rank_ratio < 0.5
