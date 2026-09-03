from __future__ import annotations

import sys

import pytest

from learnloop.content.authoring.animation_media import (
    is_faststart,
    probe_duration_seconds,
    top_level_atoms,
)
from tests.media_fakes import tiny_mp4


def test_probe_duration_reads_container_duration():
    assert probe_duration_seconds(tiny_mp4(frames=12, fps=15)) == pytest.approx(0.8, abs=0.05)


def test_probe_duration_is_none_for_garbage():
    assert probe_duration_seconds(b"mp4-bytes") is None
    assert probe_duration_seconds(b"") is None


def test_probe_duration_is_none_without_pyav(monkeypatch):
    clip = tiny_mp4()  # built before PyAV is hidden
    monkeypatch.setitem(sys.modules, "av", None)
    assert probe_duration_seconds(clip) is None


def test_top_level_atoms_and_faststart_detection():
    data = tiny_mp4()
    atoms = top_level_atoms(data)
    assert atoms[0] == "ftyp"
    assert "moov" in atoms and "mdat" in atoms
    # A freshly muxed mp4 writes moov after mdat; that is exactly the layout a
    # streaming player cannot start without seeking.
    assert atoms.index("mdat") < atoms.index("moov")
    assert is_faststart(data) is False
    assert is_faststart(b"mp4-bytes") is False
    assert top_level_atoms(b"") == []
