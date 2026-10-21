"""
Step 4c: three 12-month scenarios instead of one forecast line.

The backtest (step 4b) showed no model forecasts this market reliably: carrying the
trend forward won in normal years and lost badly at the 2026 break, while "no change"
won at the break. So the dashboard shows outcomes under three stated assumptions:

  flat            prices stay at today's level          (best record during the break)
  trend_resumes   the 2023-2025 pace returns             (best record in normal years)
  break_continues the pace since just before the break carries on

v2, robust to one-month spikes (the monthly index moves several % on noise alone):
  - "today's level" = average of the last 3 months, not the last month
  - break pace (v3) = change from the average of Dec 2025 and Feb 2026 (the last clean
    months before the March break; Jan 2026 is skipped because it looks incomplete) to
    the Jul-Sep 2026 average, 7 months apart (centre Jan -> centre Aug), annualised.
    v2 used Oct-Dec 2025, which for villas mixed in the pre-break run-up (+6% Oct->Feb)
    and made "break continues" for villas come out at +0.5%.
  - trend pace = straight-line fit over the 36 months of 2023-2025 (stable already)

  python python/06_scenarios.py
Output: data/out/scenarios.csv, reports/04c_scenarios.md, reports/charts/scenarios_*.png
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

H = 12
TREND_WINDOW = ("2023-01-01", "2025-12-01")
PRE_BREAK = [pd.Timestamp("2025-12-01"), pd.Timestamp("2026-02-01")]
LATEST = ("2026-07-01", "2026-09-01")
MONTHS_BETWEEN = 7                     # centre of Dec-Feb (Jan 2026) to centre of Jul-Sep 2026 (Aug)
BREAK_START = pd.Timestamp("2026-03-01")
COLORS = {"flat": "#7f7f7f", "trend_resumes": "#2e75b6", "break_continues": "#c00000"}


def main():
    idx = pd.read_csv("data/out/price_index.csv", parse_dates=["month"])
    Path("reports/charts").mkdir(parents=True, exist_ok=True)
    rows = []
    table = ["| series | level now (3-month avg) | flat | trend resumes | break continues |",
             "|---|---|---|---|---|"]
    for sid, g in idx.groupby("series_id", sort=False):
        y = g.set_index("month")["index"].asfreq("MS")
        tw, pre, late = y[TREND_WINDOW[0]:TREND_WINDOW[1]], y.reindex(PRE_BREAK).dropna(), y[LATEST[0]:LATEST[1]]
        if len(tw) < 24 or len(pre) < 2 or len(late) < 3:
            table.append(f"| {sid} | not enough data in one of the windows | | | |")
            continue
        level = late.mean()
        slopes = {
            "flat": 0.0,
            "trend_resumes": float(np.polyfit(np.arange(len(tw)), np.log(tw.to_numpy()), 1)[0]),
            "break_continues": float(np.log(late.mean() / pre.mean()) / MONTHS_BETWEEN),
        }
        start = y.index[-1]
        future = pd.date_range(start + pd.offsets.MonthBegin(1), periods=H, freq="MS")
        pct = {}
        for name, s in slopes.items():
            path = level * np.exp(s * np.arange(1, H + 1))
            pct[name] = 100 * (path[-1] / level - 1)
            rows += [{"series_id": sid, "scenario": name, "month": m.date(), "index": round(v, 2)}
                     for m, v in zip(future, path)]
        table.append(f"| {sid} | {level:.1f} | {pct['flat']:+.1f}% | {pct['trend_resumes']:+.1f}% | {pct['break_continues']:+.1f}% |")

        hist = y[y.index >= "2021-01-01"]
        ma3 = hist.rolling(3).mean()
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(hist.index, hist.values, color="#1f4e79", alpha=0.3, lw=1, label="Index (monthly)")
        ax.plot(ma3.index, ma3.values, color="#1f4e79", lw=2, label="Index (3-month average)")
        for name, s in slopes.items():
            path = level * np.exp(s * np.arange(0, H + 1))
            ax.plot([start, *future], path, color=COLORS[name], ls="--", label=name.replace("_", " "))
        ax.axvline(BREAK_START, color="grey", ls=":", lw=1)
        ax.set_title(f"{sid}: 12-month scenarios (index, Jan 2020 = 100)")
        ax.legend(loc="upper left", fontsize=8)
        fig.tight_layout()
        fig.savefig(f"reports/charts/scenarios_{re.sub(r'[^a-z0-9]+', '_', sid.lower()).strip('_')}.png", dpi=120)
        plt.close(fig)

    pd.DataFrame(rows).to_csv("data/out/scenarios.csv", index=False)
    text = ("# Step 4c: 12-month scenarios\n\n"
            "Change over the next 12 months under each assumption, starting from the 3-month average level.\n\n"
            + "\n".join(table) +
            "\n\nThese are not predictions. Each shows what happens IF its assumption holds. "
            "The backtest (04b) is why no single line is presented as the forecast.\n")
    Path("reports/04c_scenarios.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
