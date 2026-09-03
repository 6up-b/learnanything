from __future__ import annotations

import sys

import pytest

from learnloop.content.authoring.animation_media import (
    is_faststart,
    probe_duration_seconds,
    remux_faststart,
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


def test_remux_faststart_moves_moov_first_and_keeps_duration():
    raw = tiny_mp4(frames=12, fps=15)
    assert is_faststart(raw) is False

    remuxed = remux_faststart(raw)

    assert is_faststart(remuxed) is True
    assert remuxed != raw
    assert probe_duration_seconds(remuxed) == pytest.approx(0.8, abs=0.05)
    # Already-faststart input is returned as-is (idempotent, no re-encode).
    assert remux_faststart(remuxed) is remuxed


def test_remux_faststart_passes_garbage_through():
    assert remux_faststart(b"mp4-bytes") == b"mp4-bytes"


def test_remux_faststart_returns_input_when_pyav_missing(monkeypatch):
    raw = tiny_mp4()
    monkeypatch.setitem(sys.modules, "av", None)
    assert remux_faststart(raw) is raw


def test_concat_clips_joins_in_order_as_one_faststart_stream():
    from learnloop.content.authoring.animation_media import concat_clips

    clips = [tiny_mp4(frames=12, fps=15), tiny_mp4(frames=6, fps=15), tiny_mp4(frames=12, fps=15)]

    joined = concat_clips(clips, fps=30)

    assert is_faststart(joined) is True
    # 0.8 s + 0.4 s + 0.8 s of source timing, re-encoded at a uniform 30 fps.
    assert probe_duration_seconds(joined) == pytest.approx(2.0, abs=0.15)
    av = pytest.importorskip("av")
    import io

    with av.open(io.BytesIO(joined)) as container:
        streams = [stream.type for stream in container.streams]
        assert streams == ["video"]
        video = container.streams.video[0]
        assert (video.width, video.height) == (64, 48)


def test_concat_single_clip_is_just_a_faststart_remux():
    from learnloop.content.authoring.animation_media import concat_clips

    raw = tiny_mp4()
    single = concat_clips([raw])
    assert is_faststart(single) is True
    assert probe_duration_seconds(single) == pytest.approx(0.8, abs=0.05)
    with pytest.raises(ValueError):
        concat_clips([])


def _frame_times(data: bytes) -> list[float]:
    av = pytest.importorskip("av")
    import io

    with av.open(io.BytesIO(data)) as container:
        video = container.streams.video[0]
        return [float(frame.pts * frame.time_base) for frame in container.decode(video)]


def test_concat_clips_rebases_offset_clips_and_ignores_longer_audio_tracks():
    """A shot whose frames start at t=2 s, or whose audio outlives its video,
    must neither freeze the picture nor swallow the following shot."""

    from learnloop.content.authoring.animation_media import concat_clips

    offset_clip = tiny_mp4(frames=12, fps=15, start_seconds=2.0)
    audio_clip = tiny_mp4(frames=12, fps=15, audio_seconds=3.0)
    plain = tiny_mp4(frames=12, fps=15)

    joined = concat_clips([plain, offset_clip, audio_clip, plain])

    times = _frame_times(joined)
    assert len(times) == 48  # every frame of every clip survives
    gaps = [round(b - a, 3) for a, b in zip(times, times[1:])]
    assert max(gaps) == pytest.approx(1 / 15, abs=0.01)  # no frozen stretch
    assert probe_duration_seconds(joined) == pytest.approx(4 * 0.8, abs=0.15)


def test_concat_clips_defaults_to_the_source_frame_rate():
    from learnloop.content.authoring.animation_media import concat_clips

    av = pytest.importorskip("av")
    import io

    joined = concat_clips([tiny_mp4(frames=24, fps=24), tiny_mp4(frames=24, fps=24)])
    with av.open(io.BytesIO(joined)) as container:
        assert round(float(container.streams.video[0].average_rate)) == 24
    assert len(_frame_times(joined)) == 48
