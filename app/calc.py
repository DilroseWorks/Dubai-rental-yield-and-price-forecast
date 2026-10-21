"""Pure calculation helpers for the Streamlit app. No Streamlit imports, so they are unit-testable."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
TABLES = ["community_scorecard", "index_lines", "scenario_summary", "backtest_summary", "monthly_sales",
          "monthly_rents"]
SCENARIO_LABELS = {"break continues": "Downside: post-break fall continues",
                   "flat": "Base case: no change",
                   "trend resumes": "Upside: 2023–25 trend resumes"}


def load_data(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    missing = [t for t in TABLES if not (data_dir / f"{t}.csv").exists()]
    if missing:
        raise FileNotFoundError(f"Missing in {data_dir}: {missing}. Run python/08_prepare_app_data.py first.")
    d = {t: pd.read_csv(data_dir / f"{t}.csv") for t in TABLES}
    for t in ("index_lines", "monthly_sales", "monthly_rents"):
        d[t]["month"] = pd.to_datetime(d[t]["month"])
    return d


def scenario_series_for(area: str, segment: str) -> str:
    """Which price-index series the 12-month scenarios come from for a community.
    Only Dubai-wide Ready series (and Dubai Marina flats) have enough history for scenarios."""
    if area == "MARSA DUBAI" and segment == "Flat":
        return "MARSA DUBAI / Ready / Flat"
    return f"DUBAI / Ready / {segment}"


@dataclass
class YieldEstimate:
    market_value: float          # community median Ready price per sqm x size
    est_annual_rent: float       # gross yield x market value
    price_vs_market_pct: float   # how far the user's price is above/below the community median
    gross_yield_pct: float       # on the user's price
    net_yield_pct: float         # after the user's costs, on the user's price


def estimate_yield(gross_yield_pct: float, aed_per_sqm: float, size_sqm: float, price_aed: float,
                   service_charge_per_sqm: float = 0.0, vacancy_pct: float = 0.0,
                   other_costs_pct: float = 0.0) -> YieldEstimate:
    """Estimate rent from community medians, then yields on the price the user would actually pay.

    Rent = community gross yield x (community median price per sqm x size). Paying more than the
    community median for the same size does not raise the rent, so it lowers the user's yield.
    """
    if size_sqm <= 0 or price_aed <= 0:
        raise ValueError("size and price must be positive")
    market_value = aed_per_sqm * size_sqm
    rent = gross_yield_pct / 100 * market_value
    net_rent = rent * (1 - vacancy_pct / 100) - service_charge_per_sqm * size_sqm - rent * other_costs_pct / 100
    return YieldEstimate(
        market_value=market_value,
        est_annual_rent=rent,
        price_vs_market_pct=100 * (price_aed / market_value - 1),
        gross_yield_pct=100 * rent / price_aed,
        net_yield_pct=100 * net_rent / price_aed,
    )


def scenario_values(scenarios: pd.DataFrame, series_id: str, price_aed: float) -> pd.DataFrame:
    """Value of the property after 12 months under each scenario, ordered downside -> upside."""
    s = scenarios[scenarios["series_id"] == series_id].copy()
    if s.empty:
        raise KeyError(f"no scenarios for {series_id}")
    s["value_in_12m_aed"] = price_aed * (1 + s["change_12m_pct"] / 100)
    s["label"] = s["scenario"].map(SCENARIO_LABELS).fillna(s["scenario"])
    return s.sort_values("change_12m_pct")[["scenario", "label", "change_12m_pct", "value_in_12m_aed"]].reset_index(drop=True)


def data_as_of(index_lines: pd.DataFrame) -> pd.Timestamp:
    hist = index_lines[index_lines["line"].str.startswith("index")]
    return hist["month"].max()


# ---------------------------------------------------------------- headline numbers

@dataclass
class MarketKpis:
    sales_change_pct: float      # Apr-Sep this year vs the same months last year, all sales
    window_label: str            # e.g. "Apr–Sep 2026"
    index_latest: float          # Ready flat index, 3-month average, Jan 2020 = 100
    below_peak_pct: float        # latest 3-month average vs its highest value
    peak_month: pd.Timestamp
    new_lease_premium_pct: float  # new vs renewed flat leases, rent per sqm, latest month
    new_rent_per_sqm: float
    renewed_rent_per_sqm: float
    rents_month: pd.Timestamp


def market_kpis(d: dict[str, pd.DataFrame], series_id: str = "DUBAI / Ready / Flat") -> MarketKpis:
    sales = d["monthly_sales"]
    last = sales["month"].max()
    start = last - pd.DateOffset(months=5)
    this = sales[(sales["month"] >= start) & (sales["month"] <= last)]["sales"].sum()
    prev_start, prev_end = start - pd.DateOffset(years=1), last - pd.DateOffset(years=1)
    prev = sales[(sales["month"] >= prev_start) & (sales["month"] <= prev_end)]["sales"].sum()

    idx = d["index_lines"]
    avg = idx[(idx["series_id"] == series_id) & (idx["line"] == "index (3-month avg)")].dropna(subset=["value"])
    avg = avg.sort_values("month")
    peak = avg.loc[avg["value"].idxmax()]

    rents = d["monthly_rents"]
    flats = rents[rents["segment"] == "Flat"]
    rm = flats["month"].max()
    latest = flats[flats["month"] == rm].set_index("version")["median_rent_per_sqm"]

    return MarketKpis(
        sales_change_pct=100 * (this / prev - 1),
        window_label=f"{start:%b}–{last:%b %Y}",
        index_latest=float(avg["value"].iloc[-1]),
        below_peak_pct=100 * (avg["value"].iloc[-1] / peak["value"] - 1),
        peak_month=peak["month"],
        new_lease_premium_pct=100 * (latest["New"] / latest["Renewed"] - 1),
        new_rent_per_sqm=float(latest["New"]),
        renewed_rent_per_sqm=float(latest["Renewed"]),
        rents_month=rm,
    )


# ---------------------------------------------------------------- map and scatter helpers

# Gross-yield bands for the tile map: (lower bound, background, text colour). Same scale for flats
# and villas, so the two can be compared.
YIELD_BANDS = [
    (8.5, "#0B3C5D", "#FFFFFF"),
    (7.5, "#1F6F9B", "#FFFFFF"),
    (6.5, "#6FA8CB", "#0B1B26"),
    (5.5, "#B5D3E4", "#0B1B26"),
    (float("-inf"), "#E6EEF2", "#0B1B26"),
]


def yield_colours(gross_yield_pct: float) -> tuple[str, str]:
    for lower, bg, fg in YIELD_BANDS:
        if gross_yield_pct >= lower:
            return bg, fg
    raise ValueError(gross_yield_pct)


def mark_high_and_rising(score: pd.DataFrame) -> pd.DataFrame:
    """Flag communities with above-average yield (average of that segment) AND rising prices."""
    s = score.copy()
    avg = s["gross_yield_pct"].mean()
    s["high_and_rising"] = (s["gross_yield_pct"] > avg) & (s["price_yoy_6m_pct"] > 0)
    return s


_WORDS = ["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
          "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen"]


def count_words(n: int) -> str:
    return _WORDS[n] if 0 <= n < len(_WORDS) else str(n)


def signed_pct(x: float, decimals: int = 1) -> str:
    """+2.6% / −9.9% with a true minus sign."""
    if pd.isna(x):
        return "no data"
    sign = "+" if x > 0 else ("−" if x < 0 else "")
    return f"{sign}{abs(x):.{decimals}f}%"


MODEL_NAMES = {"Naive": "No change", "Drift": "Continue trend", "SARIMA": "SARIMA"}


def backtest_table(backtest: pd.DataFrame, series_id: str, horizons=(3, 12)) -> pd.DataFrame:
    """Average forecast error (MAPE, %) by period and horizon, one column per model."""
    b = backtest[(backtest["series_id"] == series_id) & (backtest["horizon_months"].isin(horizons))].copy()
    # The pipeline writes "naive" / "drift" / "sarima"; match names in any case.
    canonical = {m.lower(): m for m in MODEL_NAMES}
    b["model"] = b["model"].astype(str).str.strip().str.lower().map(canonical)
    b = b.dropna(subset=["model"])
    t = b.pivot_table(index=["period", "horizon_months"], columns="model", values="mape_pct", aggfunc="mean")
    t = t.reindex(columns=[m for m in MODEL_NAMES if m in t.columns])
    order = [(p, h) for p in ("normal", "2026 break") for h in horizons if (p, h) in t.index]
    return t.loc[order]
