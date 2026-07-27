"""One exact independence primitive, everywhere.

`spec_diagnostic_augmentation_v1.md` §8: *"`services/progression.py` already
treats a tight soft-kinship cluster as exactly one independent group. v1 §5.6's
promotion condition (b) needs precisely this... Call that implementation; do not
grow 'item fingerprint family' as a parallel notion. Six errors on six
near-clones of one item are one observation, everywhere, from one code path."*

The exact primitive is `canonical_projection.surface_group_id`, which collapses a
shared stimulus, a source-example family and a solution-template family before
falling back to the authored `surface_family` string. Four boundaries used to
compare the raw string instead, and each got the same class of thing wrong:

* **promotion** (`misconceptions._promotion_reason`) — promoted a DURABLE,
  learner-wide belief from what is really one observation;
* **probe exposure** (`probe_episodes.eligible_instruments`) — re-served a
  near-clone inside one episode as though it were a fresh surface;
* **probe completion** (`probe_episodes._surface_key`) — believed an episode had
  covered two surfaces when it had asked one question twice;
* **exam novelty** (`exam_pool`) — reserved a near-clone of an item the learner
  had already practised, which is the leakage a held-out pool exists to prevent.

Meas §3.A2's laddered stems are what make this reachable by construction rather
than by accident: a stem's parts share one stimulus BY DEFINITION, and each part
is a separate item free to carry its own `surface_family`.

Soft kinship (`familiarity.tight_kinship_clusters`) is deliberately NOT used
here. That is a strictly stronger notion with its own descoped spec item; this
file pins the exact-group correction only.
"""

from __future__ import annotations

import pytest

from learnloop.services.canonical_projection import surface_group_id
from learnloop.services.misconceptions import _independent_group_count, _promotion_reason
from learnloop.vault.models import PracticeItem


def _item(item_id: str, *, surface: str, stimulus: str | None = None, **fingerprint):
    fp = {"shared_stimulus_id": stimulus, **fingerprint}
    return PracticeItem.model_validate(
        {
            "id": item_id,
            "learning_object_id": "lo_1",
            "practice_mode": "constructed_response",
            "prompt": "p",
            "expected_answer": "a",
            "evidence_facets": ["f"],
            "surface_family": surface,
            "evidence_fingerprint": {k: v for k, v in fp.items() if v is not None},
            "created_at": "2026-07-26T00:00:00Z",
            "updated_at": "2026-07-26T00:00:00Z",
        }
    )


class _Vault:
    """The one attribute the counting helper reads."""

    def __init__(self, *items):
        self.practice_items = {item.id: item for item in items}


# ---------------------------------------------------------------------------
# The primitive itself
# ---------------------------------------------------------------------------


def test_a_shared_stimulus_outranks_differing_authored_family_names():
    """The laddered-stem case, at the primitive.

    Two parts of one stem carry different authored family strings and are still
    ONE observation. This is the exact input the old string comparison got wrong.
    """

    part_a = _item("pi_part_state", surface="svd_state", stimulus="stem_svd_1")
    part_b = _item("pi_part_execute", surface="svd_compute", stimulus="stem_svd_1")

    assert surface_group_id(part_a) == surface_group_id(part_b) == "stem_svd_1"
    assert part_a.surface_family != part_b.surface_family


def test_genuinely_unrelated_items_stay_distinct():
    a = _item("pi_a", surface="fam_a")
    b = _item("pi_b", surface="fam_b")

    assert surface_group_id(a) != surface_group_id(b)


# ---------------------------------------------------------------------------
# §5.6 arm (b): promotion to a durable belief
# ---------------------------------------------------------------------------


def test_two_parts_of_one_stem_do_not_promote_a_durable_belief():
    """The harmful write this correction prevents.

    A durable misconception is a learner-wide claim. Promoting one from a single
    stimulus is precisely "six errors on six near-clones of one item are one
    observation" inverted, and A2 made it reachable by design.
    """

    vault = _Vault(
        _item("pi_part_state", surface="svd_state", stimulus="stem_svd_1"),
        _item("pi_part_execute", surface="svd_compute", stimulus="stem_svd_1"),
    )
    candidate = {
        "item_ids": ["pi_part_state", "pi_part_execute"],
        # The legacy denormalization still says two — and is not consulted.
        "surface_families": ["svd_state", "svd_compute"],
    }

    assert _independent_group_count(vault, candidate) == 1
    assert _promotion_reason(vault, candidate, None) is None


def test_two_genuinely_independent_items_still_promote():
    """The correction tightens the boundary; it must not close it."""

    vault = _Vault(_item("pi_a", surface="fam_a"), _item("pi_b", surface="fam_b"))
    candidate = {"item_ids": ["pi_a", "pi_b"], "surface_families": ["fam_a", "fam_b"]}

    assert _independent_group_count(vault, candidate) == 2
    assert _promotion_reason(vault, candidate, None) == "independent_surface"


def test_the_stored_surface_families_list_is_not_trusted():
    """Groups are RECOMPUTED, not read.

    `surface_families` is a legacy denormalization written by several producers.
    Trusting it would leave the promotion boundary exactly as trustworthy as its
    least careful writer, so the arm ignores it even when it disagrees loudly.
    """

    vault = _Vault(_item("pi_only", surface="fam_a"))
    candidate = {"item_ids": ["pi_only"], "surface_families": ["a", "b", "c", "d"]}

    assert _promotion_reason(vault, candidate, None) is None


@pytest.mark.parametrize(
    "candidate",
    [
        {"item_ids": [], "surface_families": ["a", "b"]},
        {"item_ids": ["pi_gone", "pi_b"], "surface_families": ["a", "b"]},
        {"surface_families": ["a", "b"]},
    ],
    ids=["no-item-ids", "unresolvable-item", "item-ids-absent"],
)
def test_unverifiable_provenance_fails_closed(candidate):
    """A candidate whose provenance cannot be checked is not evidence.

    Returning a partial count would let a candidate whose history is half-missing
    look independent on the surviving half. The conservative direction here is
    the one that declines to write a durable belief about the learner.
    """

    vault = _Vault(_item("pi_b", surface="fam_b"))

    assert _independent_group_count(vault, candidate) == 0
    assert _promotion_reason(vault, candidate, None) is None


# ---------------------------------------------------------------------------
# The other three boundaries read the same primitive
# ---------------------------------------------------------------------------


def test_probe_completion_keys_on_the_group_not_the_authored_string():
    from learnloop.services.probe_episodes import _surface_key

    vault = _Vault(
        _item("pi_part_state", surface="svd_state", stimulus="stem_svd_1"),
        _item("pi_part_execute", surface="svd_compute", stimulus="stem_svd_1"),
    )

    assert _surface_key(vault, "pi_part_state") == _surface_key(vault, "pi_part_execute")


def test_an_unknown_probe_item_stays_distinct_rather_than_collapsing():
    """Opposite conservative direction from promotion, deliberately.

    There, an unknown item must not manufacture independence. Here, an unknown
    item that collapsed into some other group would make an episode look MORE
    covered than it is, so distinct-by-default is the safe reading.
    """

    from learnloop.services.probe_episodes import _surface_key

    vault = _Vault()

    assert _surface_key(vault, "pi_missing") == "pi_missing"


def test_exam_practiced_surfaces_are_groups():
    from learnloop.services.exam_pool import _practiced_surface_families

    vault = _Vault(
        _item("pi_part_state", surface="svd_state", stimulus="stem_svd_1"),
        _item("pi_part_execute", surface="svd_compute", stimulus="stem_svd_1"),
    )

    practiced = _practiced_surface_families(vault, {"pi_part_state"})

    # Practising one part marks the whole stimulus as seen, so its sibling can
    # no longer read as a novel surface in a held-out exam.
    assert practiced == {"stem_svd_1"}
    assert surface_group_id(vault.practice_items["pi_part_execute"]) in practiced
