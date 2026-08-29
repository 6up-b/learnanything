from __future__ import annotations

from learnloop.diagnosis.probes import parse_misconception_label


def test_parse_misconception_label_registry_ulid():
    # A 26-char Crockford ULID suffix is a registry misconception id.
    suffix, is_registry = parse_misconception_label("misconception:01KWZVQW28SAP6EYDXZTZAH6ZS")
    assert suffix == "01KWZVQW28SAP6EYDXZTZAH6ZS"
    assert is_registry is True


def test_parse_misconception_label_legacy_error_type():
    # A non-ULID suffix is a legacy error-type-keyed hypothesis.
    suffix, is_registry = parse_misconception_label("misconception:conceptual_slip")
    assert suffix == "conceptual_slip"
    assert is_registry is False


def test_parse_misconception_label_rejects_wrong_length_and_alphabet():
    # 25 chars, and a ULID-length string containing the excluded letter I.
    assert parse_misconception_label("misconception:01KWZVQW28SAP6EYDXZTZAH6Z") == (
        "01KWZVQW28SAP6EYDXZTZAH6Z",
        False,
    )
    assert parse_misconception_label("misconception:01KWZVQW28SAP6EYDXZTZAH6ZI") == (
        "01KWZVQW28SAP6EYDXZTZAH6ZI",
        False,
    )


def test_parse_misconception_label_non_misconception_label():
    assert parse_misconception_label("facet_solid") == ("", False)
    assert parse_misconception_label("mastered") == ("", False)
