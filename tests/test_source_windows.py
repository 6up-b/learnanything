"""Local contextual retrieval P1: the shared window rule (sections, policy classes, splits, keys)."""
from __future__ import annotations

from learnloop.source_retrieval import windows as W


def _rows(*specs):
    return [(span, text, tuple(section), policy) for span, text, section, policy in specs]


def test_grouped_windows_respect_sections_policy_and_the_token_bound():
    long = "word " * 3000  # ~5,000 estimated tokens: alone above the window bound, below the split bound
    rows = _rows(("s1", "Alpha text here.", ["Ch 1"], "teaching"), ("s2", "Beta text here.", ["Ch 1"], "teaching"),
                 ("s3", "Gamma solution text.", ["Ch 1"], "solution"), ("s4", "Delta text.", ["Ch 2"], "teaching"),
                 ("s5", long, ["Ch 2"], "teaching"), ("s6", "Epsilon exam text.", ["Ch 2"], "exam"))
    windows = W.build_windows("ext", rows, "grouped")
    assert [window.span_ids for window in windows] == [["s1", "s2"], ["s3"], ["s4"], ["s5"], ["s6"]]
    assert all(len({window.policy_class}) == 1 for window in windows)
    # Every block exactly once, in order.
    assert [span for window in windows for span in window.span_ids] == ["s1", "s2", "s3", "s4", "s5", "s6"]
    singleton = W.build_windows("ext", rows, "singleton")
    assert [window.span_ids for window in singleton] == [["s1"], ["s2"], ["s3"], ["s4"], ["s5"], ["s6"]]


def test_an_oversized_block_is_split_by_offsets_and_averaged_by_tokens():
    huge = "token " * 9000  # ~18,000 estimated tokens: three parts
    windows = W.build_windows("ext", _rows(("s1", huge, [], "teaching")), "grouped")
    assert len(windows) >= 3 and all(window.members[0].split is not None for window in windows)
    assert "".join(window.members[0].text for window in windows) == huge
    keys = W.expected_keys("hs_x", windows)
    assert list(keys) == ["s1"] and len(keys["s1"]) == len(windows)
    mean = W.mean_vector([[1.0, 0.0], [0.0, 1.0]], [3, 1])
    assert mean == [0.75, 0.25]


def test_a_new_exam_mark_changes_the_affected_windows_keys_only():
    base = _rows(("s1", "Alpha.", ["A"], "teaching"), ("s2", "Beta.", ["A"], "teaching"),
                 ("s3", "Gamma.", ["B"], "teaching"))
    marked = _rows(("s1", "Alpha.", ["A"], "teaching"), ("s2", "Beta.", ["A"], "exam"),
                   ("s3", "Gamma.", ["B"], "teaching"))
    before = W.expected_keys("ls_x", W.build_windows("ext", base, "grouped"))
    after = W.expected_keys("ls_x", W.build_windows("ext", marked, "grouped"))
    assert before["s3"] == after["s3"]  # another section's window is unaffected
    assert before["s1"] != after["s1"] and before["s2"] != after["s2"]
    # Another space never shares a key.
    assert W.expected_keys("ls_y", W.build_windows("ext", base, "grouped"))["s3"] != before["s3"]
