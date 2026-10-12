import math

import pytest

from learnloop.numeric import (
    beta_mean,
    beta_quantile,
    clamp,
    empirical_quantile,
    percentiles,
    regularized_incomplete_beta,
    sigmoid,
    student_t_quantile,
)


def test_clamp_bounds() -> None:
    assert clamp(1.5) == 1.0
    assert clamp(-0.5) == 0.0
    assert clamp(0.4) == 0.4
    assert clamp(7.0, low=2.0, high=5.0) == 5.0


def test_sigmoid_symmetry_and_bounds() -> None:
    assert sigmoid(0.0) == 0.5
    assert sigmoid(2.0) == pytest.approx(1.0 - sigmoid(-2.0))
    assert 0.0 < sigmoid(-30.0) < 1e-12
    assert sigmoid(800.0) == 1.0  # no overflow
    assert sigmoid(-800.0) == pytest.approx(0.0)


def test_empirical_quantile_single_element() -> None:
    assert empirical_quantile([3.0], 0.0) == 3.0
    assert empirical_quantile([3.0], 0.5) == 3.0
    assert empirical_quantile([3.0], 1.0) == 3.0


def test_empirical_quantile_odd_n() -> None:
    values = [3.0, 1.0, 2.0]
    assert empirical_quantile(values, 0.5) == 2.0
    assert empirical_quantile(values, 0.0) == 1.0
    assert empirical_quantile(values, 1.0) == 3.0


def test_empirical_quantile_even_n_interpolates() -> None:
    values = [1.0, 2.0, 3.0, 4.0]
    assert empirical_quantile(values, 0.5) == pytest.approx(2.5)
    # numpy.percentile([1,2,3,4], 85, method="linear") == 3.55
    assert empirical_quantile(values, 0.85) == pytest.approx(3.55)


def test_empirical_quantile_unsorted_input() -> None:
    assert empirical_quantile([9.0, 1.0, 5.0, 7.0, 3.0], 0.75) == pytest.approx(7.0)


def test_empirical_quantile_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):
        empirical_quantile([], 0.5)
    with pytest.raises(ValueError):
        empirical_quantile([1.0], 1.5)


def test_percentiles_defaults_and_empty() -> None:
    assert percentiles([]) == {}
    result = percentiles([float(i) for i in range(1, 101)])
    assert result[0.50] == pytest.approx(50.5)
    assert result[0.90] == pytest.approx(90.1)
    assert set(result) == {0.10, 0.25, 0.50, 0.75, 0.90}


def test_percentiles_custom_qs() -> None:
    result = percentiles([1.0, 2.0, 3.0, 4.0], qs=(0.5,))
    assert result == {0.5: pytest.approx(2.5)}
    assert not math.isnan(result[0.5])


def test_regularized_incomplete_beta_matches_uniform_cdf() -> None:
    # Beta(1,1) is uniform: I_x(1,1) == x.
    for x in (0.0, 0.1, 0.25, 0.5, 0.9, 1.0):
        assert regularized_incomplete_beta(x, 1.0, 1.0) == pytest.approx(x, abs=1e-9)
    # Symmetric Beta(2,2) has median 0.5 and is monotone.
    assert regularized_incomplete_beta(0.5, 2.0, 2.0) == pytest.approx(0.5, abs=1e-9)
    assert regularized_incomplete_beta(0.2, 2.0, 2.0) < 0.5


def test_beta_mean() -> None:
    assert beta_mean(1.0, 1.0) == pytest.approx(0.5)
    assert beta_mean(9.0, 1.0) == pytest.approx(0.9)


def test_beta_quantile_uniform() -> None:
    # Beta(1,1) inverse-CDF is the identity: the 25th percentile is 0.25.
    assert beta_quantile(0.25, 1.0, 1.0) == pytest.approx(0.25, abs=1e-6)
    assert beta_quantile(0.5, 1.0, 1.0) == pytest.approx(0.5, abs=1e-6)


def test_beta_quantile_high_evidence_tracks_mean() -> None:
    # A high-evidence posterior concentrates: its 25th-percentile lower bound sits
    # just under the mean, unlike a flat 5-trial estimate.
    alpha, beta = 90.0, 10.0
    mean = beta_mean(alpha, beta)  # 0.9
    lb = beta_quantile(0.25, alpha, beta)
    assert lb == pytest.approx(mean, abs=0.03)
    assert lb < mean
    # A thin 5-trial estimate (alpha=5, beta=1, mean ~0.83) is far more cautious:
    # its lower bound sits well under the mean despite the high point estimate.
    thin_lb = beta_quantile(0.25, 5.0, 1.0)
    assert thin_lb < beta_mean(5.0, 1.0) - 0.05
    # and the high-evidence lb clears 0.83 while the thin lb does not.
    assert lb > 0.83
    assert thin_lb < 0.83


def test_beta_quantile_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):
        beta_quantile(1.5, 1.0, 1.0)
    with pytest.raises(ValueError):
        beta_quantile(0.5, 0.0, 1.0)


@pytest.mark.parametrize(("df", "expected"), [
    # Two-sided 95% critical values (R: qt(.975, df); scipy.stats.t.ppf).
    (1, 12.7062047361747), (2, 4.30265272974946), (3, 3.18244630528371),
    (5, 2.57058183563631), (19, 2.09302405440831), (36, 2.02809400098045),
    (1000, 1.96233908082641),
])
def test_student_t_quantile_matches_tables(df, expected) -> None:
    assert student_t_quantile(0.975, df) == pytest.approx(expected, abs=1e-9)
    assert student_t_quantile(0.025, df) == pytest.approx(-expected, abs=1e-9)


def test_student_t_quantile_approaches_the_normal_and_rejects_bad_inputs() -> None:
    assert student_t_quantile(0.5, 4) == 0.0
    assert student_t_quantile(0.975, 1e7) == pytest.approx(1.959963984540054, abs=1e-6)
    for p, df in ((0.0, 3), (1.0, 3), (0.5, 0), (0.9, math.inf), (0.9, math.nan)):
        with pytest.raises(ValueError):
            student_t_quantile(p, df)
