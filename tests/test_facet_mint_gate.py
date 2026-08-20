"""D2's facet-mint gate, as a pure function and wired at ingest (plan item 5.4).

Meas D2: a candidate facet earns an id only when it is separable from its nearest
existing neighbours AND implies a distinct repair; "otherwise it is registered as
an alias of the neighbour, not as a facet", with the failure typed.
"""

from __future__ import annotations

from typing import Any

from learnloop.content.synthesis.facet_mint_gate import (
    MINT_GATE,
    MintDisposition,
    MintReason,
    NeighbourKind,
    distinct_repair,
    judge_facet_mints,
    mint_diagnostic,
    separable,
    is_testable,
)


def _facet(
    facet_id: str,
    *,
    claim: str = "",
    signatures: list[str] | None = None,
    repairs: list[str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "id": facet_id,
        "claim": claim or f"claim for {facet_id}",
        "error_signatures": signatures if signatures is not None else [f"{facet_id} error"],
        "instructional_repairs": repairs if repairs is not None else [f"{facet_id} repair"],
    }
    payload.update(extra)
    return payload


# --- the two criteria -------------------------------------------------------


def test_separability_is_symmetric_so_a_subset_facet_is_a_collapse():
    broad = _facet("broad", signatures=["swaps the transpose", "drops the scale factor"])
    narrow = _facet("narrow", signatures=["swaps the transpose"])
    other = _facet("other", signatures=["forgets the softmax"])

    # Each owns a signature the other does not -> an item can be authored that
    # only one of them fails.
    assert separable(broad, other)
    # `narrow`'s signatures are a subset: every item that catches it catches
    # `broad` too, so no item distinguishes them.
    assert not separable(narrow, broad)
    assert not separable(broad, narrow)


def test_distinct_repair_and_testability_are_independent_criteria():
    left = _facet("left", repairs=["contrast Q and Q^T"])
    same = _facet("same", repairs=["contrast Q and Q^T"])
    other = _facet("other", repairs=["re-derive the scale factor"])

    assert distinct_repair(left, other)
    assert not distinct_repair(left, same)
    # Normalization is the shared one: casing/punctuation is not a distinction.
    assert not distinct_repair(left, _facet("cased", repairs=["Contrast Q and Q^T."]))
    assert is_testable(left, other)
    assert not is_testable(left, _facet("bare", signatures=[], repairs=[]))


# --- the gate ---------------------------------------------------------------


def test_a_separable_candidate_with_a_distinct_repair_is_minted():
    registered = [
        _facet(
            "registered_transpose",
            claim="Qx is the coordinate vector in the Q basis.",
            # A shared signature makes the pair NEIGHBOURS (observationally
            # entangled), which is what puts it in front of the harness at all.
            signatures=["swaps Q and Q transpose", "misreads the basis order"],
            repairs=["contrast Q and Q transpose"],
        )
    ]
    candidate = _facet(
        "candidate_scale",
        claim="Qx is the coordinate vector in the Q basis, up to scale.",
        # ... and an exclusive signature on each side makes them SEPARABLE.
        signatures=["swaps Q and Q transpose", "drops the normalising scale factor"],
        repairs=["re-derive the scale factor from the norm"],
    )

    report = judge_facet_mints([candidate], registered=registered)

    verdict = report.verdicts[0]
    assert verdict.neighbours[0].kind is NeighbourKind.SHARED_ERROR_SIGNATURE
    assert verdict.disposition is MintDisposition.MINT
    assert verdict.reason is MintReason.SEPARABLE_AND_DISTINCT_REPAIR
    assert verdict.minted_status == "reviewed"
    assert verdict.alias_of is None
    assert verdict.exclusive_repairs == ("re derive the scale factor from the norm",)
    assert mint_diagnostic(verdict) is None


def test_a_non_separable_candidate_becomes_an_alias_not_a_mint():
    registered = [
        _facet(
            "registered_transpose",
            signatures=["swaps Q and Q transpose", "drops the scale factor"],
            repairs=["contrast Q and Q transpose"],
        )
    ]
    # Subset signatures (no item separates them) but a genuinely different repair.
    candidate = _facet(
        "candidate_transpose_again",
        signatures=["swaps Q and Q transpose"],
        repairs=["walk through an explicit 2x2 example"],
    )

    report = judge_facet_mints([candidate], registered=registered)

    verdict = report.verdicts[0]
    assert verdict.disposition is MintDisposition.ALIAS
    assert verdict.reason is MintReason.NO_AUTHORABLE_DISCRIMINATING_ITEM
    assert verdict.alias_of == "registered_transpose"
    assert verdict.minted_status is None
    # The distinct repair is DEFERRED, not discarded: it is what review recovers by
    # splitting the alias back out once an instrument that separates them exists.
    assert verdict.exclusive_repairs == ("walk through an explicit 2x2 example",)
    assert report.aliases() == {"registered_transpose": ["candidate_transpose_again"]}
    diagnostic = mint_diagnostic(verdict)
    assert diagnostic["gate"] == MINT_GATE and diagnostic["severity"] == "review"
    assert "alias" in diagnostic["message"]


def test_same_repair_class_aliases_even_when_signatures_differ():
    registered = [
        _facet(
            "registered_scale",
            signatures=["drops the scale factor", "reuses the raw dot product"],
            repairs=["re-derive the scale factor"],
        )
    ]
    candidate = _facet(
        "candidate_scale_variant",
        signatures=["drops the scale factor", "normalises after the softmax"],
        repairs=["re-derive the scale factor"],
    )

    verdict = judge_facet_mints([candidate], registered=registered).verdicts[0]

    assert verdict.disposition is MintDisposition.ALIAS
    assert verdict.reason is MintReason.SAME_REPAIR_CLASS
    assert verdict.alias_of == "registered_scale"


def test_a_candidate_with_no_neighbour_mints_unconditionally():
    verdict = judge_facet_mints(
        [_facet("lonely", claim="Something entirely unrelated about eigenvalues.")],
        registered=[_facet("far", claim="A completely different statement about graphs.")],
    ).verdicts[0]

    assert verdict.disposition is MintDisposition.MINT
    assert verdict.reason is MintReason.NO_NEIGHBOUR
    assert verdict.neighbours == ()


def test_untestable_candidate_abstains_and_is_not_born_reviewed():
    """D2's defect is minting at ``status: reviewed``; the abstention arm stops that.

    Aliasing on ignorance would delete the missing-vocabulary record D2 asks for,
    so an untestable candidate is minted `proposed` and recorded instead.
    """

    registered = [_facet("registered_bare", claim="Identical claim.", signatures=[], repairs=[])]
    candidate = _facet("candidate_bare", claim="Identical claim.", signatures=[], repairs=[])

    verdict = judge_facet_mints([candidate], registered=registered).verdicts[0]

    assert verdict.disposition is MintDisposition.ABSTAIN
    assert verdict.reason is MintReason.INSUFFICIENT_PAYLOAD_TO_TEST
    assert verdict.minted_status == "proposed"
    assert verdict.alias_of is None
    assert verdict.neighbours[0].kind is NeighbourKind.SHARED_CLAIM
    diagnostic = mint_diagnostic(verdict)
    assert diagnostic["severity"] == "review"
    assert "proposed" in diagnostic["message"]


def test_every_typed_reason_is_reachable():
    """Guard: a new reason arm must arrive with a case that reaches it."""

    reached: set[MintReason] = set()
    registered = [
        _facet("r_sub", signatures=["a", "b"], repairs=["repair one"]),
        _facet("r_same", signatures=["c", "d"], repairs=["repair two"]),
        _facet("r_bare", claim="bare claim", signatures=[], repairs=[]),
    ]
    candidates = [
        _facet("c_lonely", claim="unrelated"),
        _facet("c_separable", signatures=["a", "z"], repairs=["repair three"]),
        _facet("c_subset", signatures=["a"], repairs=["repair four"]),
        _facet("c_same_repair", signatures=["c", "y"], repairs=["repair two"]),
        _facet("c_bare", claim="bare claim", signatures=[], repairs=[]),
    ]
    for verdict in judge_facet_mints(candidates, registered=registered).verdicts:
        reached.add(verdict.reason)
    assert reached == set(MintReason)


def test_aliases_never_chain_because_candidates_are_judged_in_order():
    """An `alias_of` always names a facet that will exist after the batch applies."""

    registered = [_facet("root", signatures=["shared", "root only"], repairs=["root repair"])]
    candidates = [
        _facet("first", signatures=["shared"], repairs=["first repair"]),
        _facet("second", signatures=["shared"], repairs=["second repair"]),
    ]

    report = judge_facet_mints(candidates, registered=registered)

    assert [v.alias_of for v in report.verdicts] == ["root", "root"]
    minted = {v.candidate_id for v in report.minted} | {"root"}
    assert all(v.alias_of in minted for v in report.aliased)


def test_counts_and_summary_cover_the_closed_vocabularies():
    report = judge_facet_mints([_facet("solo")])

    assert set(report.counts()) == {str(d) for d in MintDisposition}
    assert set(report.reason_counts()) == {str(r) for r in MintReason}
    assert report.summary()["candidate_count"] == 1


# --- wired at ingest --------------------------------------------------------


def test_ingest_aliases_a_collapsing_candidate_into_a_registered_facet(tmp_path):
    """The wiring test: alias-not-mint at ingest, against the live registry.

    A facet already in the registry subsumes the candidate ``source_set_synthesis``
    would have minted, so no facet row is emitted for it. Instead the registry
    facet earns an ``update`` row appending the candidate id as an alias, and every
    downstream reference (recipe component, criterion target) resolves to the
    survivor. Fails if the mint gate is unwired from ``_normalize``.
    """

    from learnloop.content.synthesis.source_set_synthesis import create_study_map
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths
    from learnloop.vault.yaml_io import write_yaml

    from tests.test_source_set_synthesis import _CLOCK, FakeSynthesisClient, _setup

    root, repo = _setup(tmp_path)
    # A registered facet whose error signatures SUBSUME the candidate's and whose
    # repair the candidate does not extend: one obligation, two ids.
    write_yaml(
        VaultPaths(root, load_vault(root).config).facets_path,
        {
            "schema_version": 2,
            "facets": [
                {
                    "id": "facet_symmetry_registered",
                    "claim": "A real square matrix is symmetric exactly when A^T = A.",
                    "error_signatures": [
                        "substitutes A^T A = I for A^T = A",
                        "asserts every square matrix is symmetric",
                    ],
                    "instructional_repairs": ["contrast symmetric and orthogonal matrices"],
                    "status": "reviewed",
                }
            ],
        },
    )

    result = create_study_map(
        root,
        "set_la",
        client=FakeSynthesisClient(),
        brief={"depth": "intro"},
        repository=repo,
        clock=_CLOCK,
        apply=True,
    )

    assert not any(d["severity"] == "hard_fail" for d in result.gate_diagnostics)
    aliased = [d for d in result.gate_diagnostics if d["gate"] == MINT_GATE]
    assert len(aliased) == 1
    assert "facet_symmetry_definition" in aliased[0]["message"]
    assert "same_repair_class" in aliased[0]["message"]
    # Only the separable facet was minted; the collapsing one earned no id.
    assert result.item_counts["facet"] == 2  # 1 mint + 1 alias-registering update

    vault = load_vault(root)
    assert "facet_symmetry_definition" not in vault.evidence_facets
    assert "facet_spectral_applicability" in vault.evidence_facets
    survivor = vault.evidence_facets["facet_symmetry_registered"]
    assert "facet_symmetry_definition" in survivor.aliases
    # The alias resolves, so evidence filed against the old id lands on the facet.
    assert vault.canonical_facet_id("facet_symmetry_definition") == "facet_symmetry_registered"
    # Downstream references were redirected, not left dangling.
    recipe = vault.learning_objects["lo_diagonalize_symmetric"].blueprints[0].recipes[0]
    assert [component.facet for component in recipe.all_of] == [
        "facet_symmetry_registered",
        "facet_spectral_applicability",
    ]
    item = vault.practice_items["pi_identify_symmetry"]
    assert item.grading_rubric.criteria[0].targets[0].facet == "facet_symmetry_registered"
