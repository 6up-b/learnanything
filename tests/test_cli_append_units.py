"""D-12: ``learnloop synthesize`` appending without ``--new-revision`` sends
only the units no kept synthesis of the set has sent (K3.2's filter, for the CLI).

The CLI passed ``new_revision_ids=None``, so ``_append`` took every selected
revision: each run re-sent the whole set's inventories (the bootstrap's book
and every earlier append's) as "new".
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from typer.testing import CliRunner

from learnloop.content.synthesis.ai_contracts import AppendConflict, AppendReconciliation, SynthSpanRef
from learnloop.content.synthesis.source_append import append_source, units_not_yet_sent
from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_source_set

from tests.source_append_helpers import (
    FakeAppendClient,
    SymmetryInventoryClient,
    _CLOCK,
    _bootstrap_and_add,
    _first_new_span,
    _neighborhood_facet_id,
)
from tests.source_inventory_helpers import _block, _ir, _persist, _register_revision


def _cli(monkeypatch, root, client, *args):
    import learnloop.cli as cli_module
    from learnloop.cli import app

    ready = SimpleNamespace(ready=True, status="ready", message="")
    monkeypatch.setattr(cli_module, "_ready_provider_for_task", lambda *a, **k: ("codex", ready, client))
    result = CliRunner().invoke(app, ["synthesize", "set_la", "--json", "--vault", str(root), *args])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def _sent(context) -> set[tuple[str, str]]:
    return {(entry["revision_id"], entry["unit_id"]) for entry in context.new_inventories}


def _add_two_unit_member(root, repo) -> None:
    """A third member, ``rev_two``, with two inventoried units ``u_a`` and ``u_b``."""

    _register_revision(repo, source_id="src_two", revision_id="rev_two")
    ir = _ir([
        ("u_a", "Symmetric matrices, a third time", [_block("s1", "A matrix equal to its transpose is symmetric.")],
         "sha256:u_a", 1),
        ("u_b", "Symmetric matrices, once more", [_block("s2", "Symmetric means A^T = A for a square A.")],
         "sha256:u_b", 2),
    ])
    _persist(repo, ir, revision_id="rev_two", extraction_id="ext_two")
    for unit_id in ("u_a", "u_b"):
        run_unit_inventory(repo, "ext_two", unit_id, role="alternate_explanation", profile="combined",
                           client=SymmetryInventoryClient(), input_budget_tokens=20000, clock=_CLOCK)
    vault = load_vault(root)
    members = [
        {"source_id": m.source_id, "revision_id": m.revision_id, "default_role": m.default_role,
         "scope": [{"unit_id": s.unit_id} for s in m.scope], "priority": m.priority}
        for m in next(s for s in vault.source_sets if s.id == "set_la").members
    ]
    members.append({"source_id": "src_two", "revision_id": "rev_two", "default_role": "alternate_explanation",
                    "scope": [{"unit_id": "u_a"}, {"unit_id": "u_b"}], "priority": 1})
    upsert_source_set(root, {"id": "set_la", "subject_id": "linear-algebra", "title": "Linear Algebra",
                             "members": members}, clock=_CLOCK)


def test_the_cli_append_sends_only_the_member_no_synthesis_has_sent(tmp_path, monkeypatch):
    root, _repo = _bootstrap_and_add(tmp_path)  # rev_text bootstrapped and applied; rev_alt added since
    client = FakeAppendClient()

    _cli(monkeypatch, root, client)

    (context,) = client.calls
    assert _sent(context) == {("rev_alt", "chapter_symmetry_alt")}


def test_a_partly_sent_member_sends_only_its_new_units(tmp_path, monkeypatch):
    root, repo = _bootstrap_and_add(tmp_path)
    _add_two_unit_member(root, repo)
    client = FakeAppendClient()
    # A keep-ahead build appended rev_alt and u_a (K3.2's filter); u_b came later.
    append_source(root, "set_la", client=client, new_revision_ids=["rev_alt", "rev_two"],
                  new_unit_ids={"rev_two": ["u_a"]}, repository=repo, clock=_CLOCK)

    _cli(monkeypatch, root, client)

    assert _sent(client.calls[-1]) == {("rev_two", "u_b")}


def test_with_nothing_new_the_cli_sends_nothing_and_says_so(tmp_path, monkeypatch):
    root, _repo = _bootstrap_and_add(tmp_path)
    client = FakeAppendClient()
    _cli(monkeypatch, root, client)

    again = _cli(monkeypatch, root, client)

    assert len(client.calls) == 1
    assert again["nothingNew"] is True and "--new-revision" in again["message"]


def _conflict_only(context, _n):
    """A review-only answer (a source conflict), so nothing auto-applies."""

    ext, unit, span = _first_new_span(context)
    return AppendReconciliation(conflicts=[AppendConflict(
        client_item_id="c1", entity_type="facet", entity_id=_neighborhood_facet_id(context), statement="disagree",
        left=SynthSpanRef(extraction_id="ext_text", unit_id="chapter_symmetry", span_id="s1"),
        right=SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span))])


def test_a_wholly_rejected_append_leaves_its_units_new(tmp_path, monkeypatch):
    from learnloop.content.proposals.proposals import reject_items

    root, _repo = _bootstrap_and_add(tmp_path, add_role="primary_textbook")
    client = FakeAppendClient(builder=_conflict_only)
    first = _cli(monkeypatch, root, client)
    assert first["append"]["review_item_ids"]
    assert units_not_yet_sent(root, "set_la") == ([], {})

    reject_items(root, first["append"]["proposal_id"])

    # (Re-running that same manifest reuses the rejected run: ledger row D-16.)
    assert units_not_yet_sent(root, "set_la") == (["rev_alt"], {})


def test_a_pending_append_counts_as_sent(tmp_path, monkeypatch):
    """As a keep-ahead build counts its chapters once it builds them (K3.2):
    a proposal waiting for review is not re-sent."""

    root, _repo = _bootstrap_and_add(tmp_path, add_role="primary_textbook")
    client = FakeAppendClient(builder=_conflict_only)
    _cli(monkeypatch, root, client)

    again = _cli(monkeypatch, root, client)

    assert len(client.calls) == 1 and again["nothingNew"] is True


def test_a_named_revision_is_sent_whole_as_before(tmp_path, monkeypatch):
    root, _repo = _bootstrap_and_add(tmp_path)
    client = FakeAppendClient()

    _cli(monkeypatch, root, client, "--new-revision", "rev_text")

    assert _sent(client.calls[0]) == {("rev_text", "chapter_symmetry")}
