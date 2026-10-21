"""
Step 4a: build monthly price indexes that are not fooled by project mix.

Why: step 3 showed a community's median price per sqm jumps when a new, pricier
project starts selling, though no existing home changed value. A forecast trained
on those medians would learn jumps that never happened.

How (a "project fixed-effects" index):
  log(price per sqm) = project effect + month effect
The project effect soaks up "this project is expensive". What is left, the month
effect, is how prices moved for the same projects over time. Estimated by
alternating averages, which needs only numpy.

Series built:
  - Dubai-wide: Ready Flat, Off-Plan Flat, Ready Villa, Off-Plan Villa
  - The 10 communities with the most Ready flat sales (2023 to Sep 2026)

  python python/04_build_index.py
Output: data/out/price_index.csv, reports/04a_index.md
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

BASE_MONTH = "2020-01-01"     # index = 100 in this month
MIN_SALES_DUBAI = 30          # a month needs this many sales to get an index value
MIN_SALES_AREA = 15
MIN_MONTHS = 96               # 8 years: enough for a model to see yearly seasonality several times
N_COMMUNITIES = 10


def fixed_effects_index(df: pd.DataFrame, max_iter: int = 200, tol: float = 1e-7) -> pd.Series:
    """Month effects from log(price) = project effect + month effect."""
    y = np.log(df["price_per_sqm"].to_numpy())
    m_codes, months = pd.factorize(df["month"], sort=True)
    p_codes, _ = pd.factorize(df["project_key"])
    m_n = np.bincount(m_codes)
    p_n = np.bincount(p_codes)
    pe = np.zeros(p_n.size)
    me = np.zeros(m_n.size)
    for _ in range(max_iter):
        me_new = np.bincount(m_codes, weights=y - pe[p_codes]) / m_n
        pe = np.bincount(p_codes, weights=y - me_new[m_codes]) / p_n
        done = np.max(np.abs(me_new - me)) < tol
        me = me_new
        if done:
            break
    return pd.Series(me, index=pd.DatetimeIndex(months), name="effect"), pd.Series(m_n, index=pd.DatetimeIndex(months))


def contiguous_from(counts: pd.Series, min_n: int) -> pd.Timestamp | None:
    """First month after which EVERY month has at least min_n sales."""
    full = counts.reindex(pd.date_range(counts.index.min(), counts.index.max(), freq="MS"), fill_value=0)
    bad = full[full < min_n]
    start = full.index.min() if bad.empty else bad.index.max() + pd.offsets.MonthBegin(1)
    return start if start <= full.index.max() else None


def build(df, series_id, min_n, out_rows, notes):
    eff, n = fixed_effects_index(df)
    start = contiguous_from(n, min_n)
    if start is None:
        notes.append(f"| {series_id} | skipped: no stretch where every month has {min_n}+ sales |")
        return
    eff, n = eff[eff.index >= start], n[n.index >= start]
    months = len(eff)
    if months < MIN_MONTHS:
        notes.append(f"| {series_id} | skipped: only {months} usable months from {start:%Y-%m} |")
        return
    # Re-estimate on the usable window only, so thin early months can't distort it.
    df = df[df["month"] >= start]
    eff, n = fixed_effects_index(df)
    base = pd.Timestamp(BASE_MONTH) if pd.Timestamp(BASE_MONTH) in eff.index else eff.index[0]
    index = 100 * np.exp(eff - eff.loc[base])
    raw_median = df.groupby("month")["price_per_sqm"].median()
    for mth in index.index:
        out_rows.append({"series_id": series_id, "month": mth.date(), "index": round(index[mth], 3),
                         "raw_median_aed_sqm": round(raw_median[mth], 1), "sales": int(n[mth])})
    notes.append(f"| {series_id} | {start:%Y-%m} to {index.index.max():%Y-%m} ({months} months), "
                 f"base {base:%Y-%m} = 100, min {n.min()} sales/month |")


def main():
    con = duckdb.connect("data/dubai_property.duckdb", read_only=True)
    df = con.execute("""
        SELECT month, reg_type, segment, area, price_per_sqm,
               coalesce(project_name::VARCHAR, building_name::VARCHAR, area || ' (no project)') AS project_key
        FROM sales_clean WHERE price_per_sqm > 0
    """).df()
    df["month"] = pd.to_datetime(df["month"])
    # A missing key gets code -1 from pd.factorize, which numpy can't count.
    # Rows with no project, building or area share one "unknown" bucket instead.
    df["project_key"] = df["project_key"].fillna("unknown project")
    df = df.dropna(subset=["month", "price_per_sqm"])

    rows, notes = [], ["| series | result |", "|---|---|"]
    for reg in ["Ready", "Off-Plan"]:
        for seg in ["Flat", "Villa"]:
            build(df[(df.reg_type == reg) & (df.segment == seg)], f"DUBAI / {reg} / {seg}", MIN_SALES_DUBAI, rows, notes)

    rf = df[(df.reg_type == "Ready") & (df.segment == "Flat")]
    top = (rf[rf.month >= "2023-01-01"].groupby("area").size().sort_values(ascending=False).head(N_COMMUNITIES).index)
    for area in top:
        build(rf[rf.area == area], f"{area} / Ready / Flat", MIN_SALES_AREA, rows, notes)

    Path("data/out").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv("data/out/price_index.csv", index=False)
    Path("reports").mkdir(exist_ok=True)
    Path("reports/04a_index.md").write_text(
        "# Step 4a: price indexes\n\n" + "\n".join(notes) +
        "\n\nIndex = project-adjusted price per sqm, base month = 100. "
        "raw_median_aed_sqm is kept next to it for comparison.\n", encoding="utf-8")
    print("\n".join(notes))


if __name__ == "__main__":
    main()
