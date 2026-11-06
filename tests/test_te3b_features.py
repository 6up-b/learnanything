"""Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): RO6's candidate features gain a ``lesson`` indicator, a features-version
change point.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from learnloop.algorithm_versions import LESSON_OFFERS_ALGORITHM_VERSION, LESSON_OPPORTUNITY_ALGORITHM_VERSION
from learnloop.daily_plan import lesson_offer as LO
from learnloop.router import lesson_suggestions as LS
from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import price as P
from learnloop.router_objective import value as V

from tests.test_ro4_value import EXACT, FIXED, _inputs, _logit

TAG = LESSON_OFFERS_ALGORITHM_VERSION
OLD = LESSON_OPPORTUNITY_ALGORITHM_VERSION

# --- RO6's features ---------------------------------------------------------------------------------------------


def test_ro6s_features_gain_the_lesson_indicator_and_the_version_is_a_change_point(tmp_path):
    from learnloop.router_objective import tail_data as TD
    from learnloop.vault.loader import load_vault

    from tests.helpers import create_basic_vault, set_algorithm_version

    belief = LT.Belief(session_load=0.5, days_to_go=0.0, pending_reports=0.0, mastery_p=0.5, mastery_var=0.1)
    lesson = LT.ActionView(ref="lesson_offer:lo", kind="lesson", minutes=15.0)
    block = LT.ActionView(ref="b", kind="review", minutes=10.0)
    old = LT.vector(belief, lesson, remembered=20.0)
    new = LT.vector(belief, lesson, remembered=20.0, features_version=LT.FEATURES_VERSION_LESSON)
    assert len(old) == len(LT.NAMES) and len(new) == len(LT.NAMES_LESSON) == len(LT.NAMES) + 1
    assert new[:-1] == old and new[-1] == 1.0
    assert LT.vector(belief, block, remembered=20.0, features_version=LT.FEATURES_VERSION_LESSON)[-1] == 0.0
    prior = LT.prior_fit(0.01, "g", features_version=LT.FEATURES_VERSION_LESSON)
    assert prior.names == LT.NAMES_LESSON and prior.value(new) == 0.0
    # The served features version is part of the generator version: switching it on is a change point, once.
    paths = create_basic_vault(tmp_path / "v")
    set_algorithm_version(paths, TAG)
    on = load_vault(paths.root).config
    assert TD.features_version(on) == LT.FEATURES_VERSION_LESSON
    set_algorithm_version(paths, OLD)
    off = load_vault(paths.root).config
    assert TD.features_version(off) == LT.FEATURES_VERSION
    trace = {"versions": {"objective": "o", "tail": "t", "terminal": "x", "horizon_days": 90.0, "llm_schema": "s"},
             "mixing": {"seeds": {}, "epsilon": 0.02}}
    assert (TD.generator(trace, TAG, active=LT.FEATURES_VERSION_LESSON)
            != TD.generator(trace, TAG, active=LT.FEATURES_VERSION))


