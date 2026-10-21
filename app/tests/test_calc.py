import pandas as pd
import pytest

from calc import estimate_yield, scenario_series_for, scenario_values


def test_price_at_median_gives_community_yield():
    e = estimate_yield(gross_yield_pct=7.0, aed_per_sqm=15_000, size_sqm=80, price_aed=1_200_000)
    assert e.market_value == 1_200_000
    assert e.est_annual_rent == pytest.approx(84_000)
    assert e.gross_yield_pct == pytest.approx(7.0)
    assert e.net_yield_pct == pytest.approx(7.0)      # no costs entered
    assert e.price_vs_market_pct == pytest.approx(0.0)


def test_paying_more_lowers_yield():
    e = estimate_yield(7.0, 15_000, 80, 1_320_000)       # 10% above median
    assert e.price_vs_market_pct == pytest.approx(10.0)
    assert e.gross_yield_pct == pytest.approx(7.0 / 1.1)


def test_costs_reduce_net_not_gross():
    e = estimate_yield(7.0, 15_000, 80, 1_200_000, service_charge_per_sqm=15, vacancy_pct=5, other_costs_pct=5)
    rent = 84_000
    expected_net = rent * 0.95 - 15 * 80 - rent * 0.05
    assert e.gross_yield_pct == pytest.approx(7.0)
    assert e.net_yield_pct == pytest.approx(100 * expected_net / 1_200_000)


def test_bad_inputs_rejected():
    with pytest.raises(ValueError):
        estimate_yield(7.0, 15_000, 0, 1_000_000)


def test_scenario_series_mapping():
    assert scenario_series_for("MARSA DUBAI", "Flat") == "MARSA DUBAI / Ready / Flat"
    assert scenario_series_for("BUSINESS BAY", "Flat") == "DUBAI / Ready / Flat"
    assert scenario_series_for("MARSA DUBAI", "Villa") == "DUBAI / Ready / Villa"


def test_scenario_values_ordered_downside_first():
    sc = pd.DataFrame({"series_id": ["S"] * 3, "scenario": ["trend resumes", "flat", "break continues"],
                       "change_12m_pct": [10.0, 0.0, -10.0]})
    out = scenario_values(sc, "S", 1_000_000)
    assert list(out["scenario"]) == ["break continues", "flat", "trend resumes"]
    assert out["value_in_12m_aed"].tolist() == pytest.approx([900_000, 1_000_000, 1_100_000])
    with pytest.raises(KeyError):
        scenario_values(sc, "missing", 1)


# ---------------------------------------------------------------- map helpers and layout
from calc import count_words, mark_high_and_rising, signed_pct, yield_colours  # noqa: E402
from tile_layout import COLS, ROWS, TILES  # noqa: E402


def test_yield_bands():
    assert yield_colours(9.3)[0] == "#0B3C5D"
    assert yield_colours(8.5)[0] == "#0B3C5D"     # lower bound is inclusive
    assert yield_colours(4.0)[0] == "#E6EEF2"


def test_high_and_rising_uses_segment_average():
    s = pd.DataFrame({"gross_yield_pct": [9.0, 8.0, 5.0, 4.0], "price_yoy_6m_pct": [2.0, -1.0, 3.0, None]})
    assert mark_high_and_rising(s)["high_and_rising"].tolist() == [True, False, False, False]


def test_text_helpers():
    assert signed_pct(-9.9) == "−9.9%" and signed_pct(2.55, 0) == "+3%" and signed_pct(float("nan")) == "no data"
    assert count_words(12) == "Twelve"


def test_tiles_fit_the_grid_without_overlap():
    for seg in ("Flat", "Villa"):
        cells = [(c, r) for (s, _), (c, r, _) in TILES.items() if s == seg]
        assert len(cells) == len(set(cells)), f"two {seg} tiles share a cell"
        assert all(0 <= c < COLS and 0 <= r < ROWS for c, r in cells)


def test_every_community_in_the_data_has_a_tile():
    from pathlib import Path
    f = Path(__file__).parents[1] / "data" / "community_scorecard.csv"
    if not f.exists():
        pytest.skip("app/data not prepared")
    score = pd.read_csv(f)
    missing = [(r.segment, r.area) for r in score.itertuples() if (r.segment, r.area) not in TILES]
    assert not missing, f"add these to app/tile_layout.py: {missing}"


def test_backtest_table_reads_pipeline_model_names():
    # python/05_forecast.py writes lowercase names; the Power BI copy had them capitalised. Both must work.
    from calc import backtest_table
    rows = []
    for model, err in (("naive", 2.0), ("drift", 3.0), ("sarima", 2.5)):
        for period in ("normal", "2026 break"):
            for h in (3, 12):
                rows.append({"series_id": "S", "model": model, "horizon_months": h, "period": period, "mape_pct": err})
    lower = pd.DataFrame(rows)
    upper = lower.assign(model=lower["model"].map({"naive": "Naive", "drift": "Drift", "sarima": "SARIMA"}))
    for df in (lower, upper):
        t = backtest_table(df, "S")
        assert list(t.columns) == ["Naive", "Drift", "SARIMA"]
        assert t.shape == (4, 3) and t.notna().all().all()
