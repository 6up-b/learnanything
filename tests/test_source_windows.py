"""Local contextual retrieval P1: the shared window rule (sections, policy classes, splits, keys)."""
from __future__ import annotations

from learnloop.source_retrieval import windows as W


def _rows(*specs):
    return [(span, text, tuple(section), policy) for span, text, section, policy in specs]


def test_grouped_windows_respect_sections_policy_and_the_token_bound():
    long = "word " * 3000  # ~5,000 estimated tokens: alone above the window bound, so it is split
    rows = _rows(("s1", "Alpha text here.", ["Ch 1"], "teaching"), ("s2", "Beta text here.", ["Ch 1"], "teaching"),
                 ("s3", "Gamma solution text.", ["Ch 1"], "solution"), ("s4", "Delta text.", ["Ch 2"], "teaching"),
                 ("s5", long, ["Ch 2"], "teaching"), ("s6", "Epsilon exam text.", ["Ch 2"], "exam"))
    windows = W.build_windows("ext", rows, "grouped")
    assert [window.span_ids for window in windows] == [["s1", "s2"], ["s3"], ["s4"], ["s5"], ["s5"], ["s6"]]
    assert all(sum(member.tokens for member in window.members) <= W.WINDOW_TOKENS for window in windows)
    assert all(len({window.policy_class}) == 1 for window in windows)
    # Every block exactly once, in order.
    assert list(dict.fromkeys(span for window in windows for span in window.span_ids)) == [
        "s1", "s2", "s3", "s4", "s5", "s6"]
    singleton = W.build_windows("ext", rows, "singleton")
    assert [window.span_ids for window in singleton] == [["s1"], ["s2"], ["s3"], ["s4"], ["s5"], ["s5"], ["s6"]]


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


def test_every_window_holds_the_bound_cjk_and_unbroken_text_included():
    """Codex review F15: a 6,000-character CJK recipe (~6,000 estimated tokens)
    and an unbroken 60,000-byte input both end in windows of at most 4,096."""

    cjk = "\u7279\u5f81\u503c" * 2000  # 6,000 CJK characters, 18,000 UTF-8 bytes, no whitespace
    unbroken = "x" * 60_000
    spaced = ("word " * 9000).strip()
    for text in (cjk, unbroken, spaced):
        for variant in W.VARIANTS:
            windows = W.build_windows("ext", _rows(("s1", "Intro.", ["A"], "teaching"), ("s2", text, ["A"], "teaching")),
                                      variant)
            assert all(sum(member.tokens for member in window.members) <= W.WINDOW_TOKENS for window in windows)
            parts = [window.members[0] for window in windows if window.span_ids == ["s2"]]
            assert len(parts) > 1 and "".join(part.text for part in parts) == text
            assert [part.split[0] for part in parts] == list(range(len(parts)))
    # Whitespace is preferred over a hard cut where the part has any.
    parts = [w.members[0] for w in W.build_windows("ext", _rows(("s1", spaced, [], "teaching")), "grouped")]
    assert all(part.text.endswith("word") for part in parts[:-1])


def test_a_withheld_heading_never_reaches_a_teaching_descendant_and_marking_it_changes_its_keys(
        tmp_path, monkeypatch):
    """Codex review F1: a held-out section header reads as WITHHELD_HEADING in
    its teaching descendants' recipes, and the mark gives those windows new keys."""

    from tests.source_retrieval_fakes import build_retrieval_vault, loaded

    paths, repository = build_retrieval_vault(tmp_path / "vault")
    vault = loaded(paths)
    before = W.extraction_windows(vault, repository, "ext_book", "grouped")
    texts = " ".join(text for window in before for text in window.chunks)
    assert "Chapter 5 Eigenvalues" in texts
    real = W.policy_classes

    def heading_held_out(vault_, repository_, keys):
        classes = real(vault_, repository_, keys)
        return {key: ("exam" if key == ("ext_book", "s1") else value) for key, value in classes.items()}

    monkeypatch.setattr(W, "policy_classes", heading_held_out)
    after = W.extraction_windows(vault, repository, "ext_book", "grouped")
    texts = " ".join(text for window in after for text in window.chunks)
    assert "Chapter 5 Eigenvalues" not in texts and W.WITHHELD_HEADING in texts
    keys_before, keys_after = W.expected_keys("ls_x", before), W.expected_keys("ls_x", after)
    descendants = {"s2", "s3", "s4"}
    assert all(keys_before[span] != keys_after[span] for span in descendants)
    others = set(keys_before) - descendants
    assert others and all(keys_before[span] == keys_after[span] for span in others)
    # The batched path (one policy read for many extractions) redacts it too.
    batched = W.windows_by_extraction(vault, repository, ["ext_book"], ("grouped",))[("ext_book", "grouped")]
    assert W.expected_keys("ls_x", batched) == keys_after
