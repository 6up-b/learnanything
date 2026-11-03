"""The two switches of data capture (``[data_capture]``). A leaf: no store, no domain.

``receipts_on`` acts at every algorithm version: a receipt changes nothing served.
``serving_on`` is the successor's gate (``DATA_CAPTURE_VERSIONS``, the kill switch
``data_capture.serving``): off, or below the tag, serving and outcomes are mvp-0.43's.
"""

from __future__ import annotations

from typing import Any

from learnloop.algorithm_versions import DATA_CAPTURE_VERSIONS


def receipts_on(config: Any) -> bool:
    section = getattr(config, "data_capture", None)
    return bool(getattr(section, "receipts", False))


def serving_on(config: Any) -> bool:
    section = getattr(config, "data_capture", None)
    algorithms = getattr(config, "algorithms", None)
    return (
        bool(getattr(section, "serving", False))
        and getattr(algorithms, "algorithm_version", None) in DATA_CAPTURE_VERSIONS
    )


__all__ = ["receipts_on", "serving_on"]
