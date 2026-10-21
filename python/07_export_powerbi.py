"""
Step 5a: export dashboard-ready tables for Power BI into data/out/powerbi/.

Power BI could do these joins itself, but shaping the data here keeps the logic in
one tested place (SQL/Python) and the .pbix file simple: no heavy Power Query steps.

  python python/07_export_powerbi.py

Needs reference/area_names.csv in the project folder (DLD area -> name people use).
"""
from pathlib import Path

import duckdb
import pandas as pd

OUT = Path("data/out/powerbi")
OUT.mkdir(parents=True, exist_ok=True)
con = duckdb.connect("data/dubai_property.duckdb", read_only=True)

# 1. Monthly market activity (sales and new/renewed leases).
con.execute(f"""
    COPY (
        SELECT month::DATE AS month, reg_type, segment, count(*) AS sales,
               round(median(price_per_sqm)) AS median_aed_per_sqm
        FROM sales_clean WHERE month >= DATE '2015-01-01' GROUP BY ALL ORDER BY ALL
    ) TO '{OUT / "monthly_sales.csv"}' (HEADER)""")
con.execute(f"""
    COPY (
        SELECT month::DATE AS month, segment, version, count(*) AS contracts,
               round(median(rent_per_sqm)) AS median_rent_per_sqm,
               round(median(annual_rent)) AS median_annual_rent
        FROM rents_clean GROUP BY ALL ORDER BY ALL
    ) TO '{OUT / "monthly_rents.csv"}' (HEADER)""")

# 2. Community scorecard with readable names and an explicit "not enough data" flag,
#    so the dashboard never shows a blank that looks like 0%.
names = pd.read_csv("reference/area_names.csv")
score = con.execute("SELECT * FROM community_scorecard").df()
score = score.merge(names[["area", "community_name", "confidence"]], on="area", how="left")
score["community_name"] = score["community_name"].fillna(score["area"].str.title())
score["name_confidence"] = score.pop("confidence").fillna("unmapped")
score["momentum_status"] = score["price_yoy_6m_pct"].notna().map({True: "measured", False: "not enough repeat sales"})
score.to_csv(OUT / "community_scorecard.csv", index=False)

# 3. One long table of index lines: history, 3-month average, and the three scenarios.
#    In Power BI: line chart, x = month, y = value, legend = line.
idx = pd.read_csv("data/out/price_index.csv", parse_dates=["month"])
sc = pd.read_csv("data/out/scenarios.csv", parse_dates=["month"])
lines = []
for sid, g in idx.groupby("series_id"):
    g = g.sort_values("month")
    lines.append(pd.DataFrame({"series_id": sid, "month": g.month, "line": "index (monthly)", "value": g["index"]}))
    lines.append(pd.DataFrame({"series_id": sid, "month": g.month, "line": "index (3-month avg)",
                               "value": g["index"].rolling(3).mean()}))
for (sid, scen), g in sc.groupby(["series_id", "scenario"]):
    lines.append(pd.DataFrame({"series_id": sid, "month": g.month, "line": f"scenario: {scen.replace('_', ' ')}",
                               "value": g["index"]}))
lines = pd.concat(lines).dropna()
lines = lines[lines.month >= "2019-01-01"]
lines["value"] = lines["value"].round(2)
lines.to_csv(OUT / "index_lines.csv", index=False)

# 4. Scenario summary: % change after 12 months, one row per series and scenario.
last = sc.sort_values("month").groupby(["series_id", "scenario"]).tail(1)
level = idx[idx.month >= idx.month.max() - pd.DateOffset(months=2)].groupby("series_id")["index"].mean()
summ = last[["series_id", "scenario", "index"]].copy()
summ["change_12m_pct"] = (100 * (summ["index"] / summ["series_id"].map(level) - 1)).round(1) + 0.0  # +0.0 turns -0.0 into 0.0
summ["scenario"] = summ["scenario"].str.replace("_", " ")
summ.drop(columns="index").to_csv(OUT / "scenario_summary.csv", index=False)

# 5. Backtest summary: average % error by series, model, horizon, period.
bt = pd.read_csv("data/out/backtest_errors.csv")
bt = bt[bt.h.isin([3, 6, 12])]
bt["period"] = bt["break_window"].map({True: "2026 break", False: "normal"})
(bt.groupby(["series_id", "model", "h", "period"])["ape_pct"].mean().round(2)
   .reset_index().rename(columns={"h": "horizon_months", "ape_pct": "mape_pct"})
   .to_csv(OUT / "backtest_summary.csv", index=False))

for f in sorted(OUT.glob("*.csv")):
    print(f"{f.name}: {sum(1 for _ in open(f, encoding='utf-8')) - 1:,} rows")
