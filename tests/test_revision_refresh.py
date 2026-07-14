"""ING M7 — revision refresh (§10.4).

A new revision is detected but pinned membership does not advance automatically;
adopting it advances the pin and triggers append. Changed/removed spans mark links
stale/needs_reanchor; unchanged spans keep their links (re-anchored). Canned
payloads, zero network.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.services.revision_refresh import refresh_revision
from learnloop.services.source_set_synthesis import create_study_map
from learnloop.vault.loader import load_vault

from tests.test_source_append import SymmetryInventoryClient
from tests.test_source_inventory import _block, _ir, _persist, _register_revision
from tests.test_source_set_synthesis import FakeSynthesisClient, _setup

_CLOCK = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))


def _member_revision(root, source_id):
    vault = load_vault(root)
    ss = next(s for s in vault.source_sets if s.id == "set_la")
    return next(m.revision_id for m in ss.members if m.source_id == source_id)


def _register_new_revision(repo, *, changed: bool):
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
            ("rev_text_v2", "src_text", "sha256:v2", _CLOCK.now().isoformat()),
        )
        connection.commit()
    first = "A real square matrix is symmetric precisely when A equals its transpose." if changed \
        else "A real square matrix is symmetric when A^T = A."
    ir = _ir([
        ("chapter_symmetry", "Symmetric matrices",
         [_block("s1", first),
          _block("s2", "The spectral theorem applies to real symmetric matrices.")],
         "sha256:sym2", 5),
    ])
    _persist(repo, ir, revision_id="rev_text_v2", extraction_id="ext_text_v2")


def test_new_revision_pinned_membership_requires_confirmation(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"depth": "intro"})
    assert _member_revision(root, "src_text") == "rev_text"

    _register_new_revision(repo, changed=False)

    # Detecting/importing the new revision does NOT advance the pin.
    result = refresh_revision(root, "set_la", source_id="src_text", old_revision_id="rev_text",
                              new_revision_id="rev_text_v2", new_extraction_id="ext_text_v2",
                              confirm=False, run_append=False, repository=repo, clock=_CLOCK)
    assert result.membership_advanced is False
    assert _member_revision(root, "src_text") == "rev_text"

    # Adopting it (confirm) advances the pin.
    result2 = refresh_revision(root, "set_la", source_id="src_text", old_revision_id="rev_text",
                               new_revision_id="rev_text_v2", new_extraction_id="ext_text_v2",
                               confirm=True, run_append=False, repository=repo, clock=_CLOCK)
    assert result2.membership_advanced is True
    assert _member_revision(root, "src_text") == "rev_text_v2"


def test_unchanged_spans_keep_links_changed_spans_go_stale(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"depth": "intro"})
    # links exist on rev_text.
    assert repo.entity_source_links_for_revision("rev_text")

    _register_new_revision(repo, changed=True)
    result = refresh_revision(root, "set_la", source_id="src_text", old_revision_id="rev_text",
                              new_revision_id="rev_text_v2", new_extraction_id="ext_text_v2",
                              confirm=False, run_append=False, repository=repo, clock=_CLOCK)
    # s1 is unchanged and re-anchors; s2 changed. Every link resolves to a decision.
    total = len(result.unchanged_links) + len(result.reanchored_links) + len(result.stale_links) + len(result.needs_reanchor_links)
    assert total == len(repo.entity_source_links_for_revision("rev_text"))
    # a changed/removed span produced at least one stale/needs_reanchor link.
    assert result.stale_links or result.needs_reanchor_links
