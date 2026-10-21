"""
Step 4b: backtest forecasting models on the price indexes, then forecast 12 months.

Models
  naive   next 12 months = last value. The bar every model has to beat.
  drift   last value + average monthly change of the last 24 months.
  sarima  seasonal ARIMA on log(index). Order picked by AIC using ONLY data before
          the first backtest origin, so the choice can't peek at the test period.

Backtest (rolling origin)
  Every 3 months from Jan 2018 (or later, if a series starts later), fit on data up to
  the origin and forecast 12 months. Compare with what actually happened.
  Errors are reported at 3, 6 and 12 months ahead, separately for the "break"
  origins whose 12-month window lands in Mar to Sep 2026.

  python python/05_forecast.py
Output: data/out/forecast.csv, data/out/backtest_errors.csv,
        reports/04b_forecast.md, reports/charts/*.png
Runtime: several minutes (hundreds of SARIMA fits). Progress is printed.
"""
import itertools
import re
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")
H = 12
FIRST_ORIGIN = pd.Timestamp("2018-01-01")
MIN_TRAIN = 72               # months of history needed before a series' first origin
BREAK_START = pd.Timestamp("2026-03-01")
GRID = [((p, 1, q), s, t)
        for p, q in itertools.product([0, 1, 2], [0, 1])
        for s in [(0, 0, 0, 0), (1, 0, 0, 12), (0, 0, 1, 12)]
        for t in ["n", "c"]]


def fit(y, order, seasonal, trend):
    return SARIMAX(y, order=order, seasonal_order=seasonal, trend=trend,
                   enforce_stationarity=False, enforce_invertibility=False).fit(disp=False, maxiter=200)


def select_order(y):
    best, best_aic = None, np.inf
    for order, seasonal, trend in GRID:
        try:
            aic = fit(y, order, seasonal, trend).aic
        except Exception:
            continue
        if aic < best_aic:
            best, best_aic = (order, seasonal, trend), aic
    return best


def forecasts(y, spec):
    """12-month forecasts (log scale) from each model, given history y."""
    last = y.iloc[-1]
    out = {"naive": np.repeat(last, H)}
    slope = (y.iloc[-1] - y.iloc[-25]) / 24 if len(y) > 25 else 0.0
    out["drift"] = last + slope * np.arange(1, H + 1)
    try:
        out["sarima"] = np.asarray(fit(y, *spec).forecast(H))
    except Exception:
        out["sarima"] = np.full(H, np.nan)
    return out


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def main():
    idx = pd.read_csv("data/out/price_index.csv", parse_dates=["month"])
    Path("reports/charts").mkdir(parents=True, exist_ok=True)
    err_rows, fc_rows, spec_rows = [], [], []

    for sid, g in idx.groupby("series_id", sort=False):
        y = np.log(g.set_index("month")["index"].asfreq("MS"))
        first_origin = max(FIRST_ORIGIN, y.index[0] + pd.DateOffset(months=MIN_TRAIN))
        spec = select_order(y[y.index < first_origin])
        if spec is None:
            print(f"{sid}: no SARIMA order could be fitted, skipped")
            continue
        spec_rows.append(f"| {sid} | {spec[0]} | {spec[1]} | {spec[2]} | {first_origin:%Y-%m} |")
        origins = pd.date_range(first_origin, y.index[-1] - pd.DateOffset(months=1), freq="3MS")
        print(f"{sid}: order {spec}, {len(origins)} backtest origins")

        # Backtest
        for origin in origins:
            train = y[y.index < origin]
            actual = y[y.index >= origin].iloc[:H]
            for model, f in forecasts(train, spec).items():
                for h in range(1, len(actual) + 1):
                    a, p = np.exp(actual.iloc[h - 1]), np.exp(f[h - 1])
                    err_rows.append({"series_id": sid, "origin": origin.date(), "model": model, "h": h,
                                     "target_month": actual.index[h - 1].date(),
                                     "ape_pct": 100 * abs(p - a) / a,
                                     "break_window": actual.index[h - 1] >= BREAK_START})

        # Final forecast from all data, with an 80% interval for SARIMA
        res = fit(y, *spec).get_forecast(H)
        mean, ci = res.predicted_mean, res.conf_int(alpha=0.2)
        future = pd.date_range(y.index[-1] + pd.offsets.MonthBegin(1), periods=H, freq="MS")
        for i, m in enumerate(future):
            fc_rows.append({"series_id": sid, "month": m.date(), "model": "sarima",
                            "index": np.exp(mean.iloc[i]), "lower80": np.exp(ci.iloc[i, 0]),
                            "upper80": np.exp(ci.iloc[i, 1])})
            fc_rows.append({"series_id": sid, "month": m.date(), "model": "naive",
                            "index": np.exp(y.iloc[-1]), "lower80": None, "upper80": None})

        # Chart
        hist = np.exp(y[y.index >= "2018-01-01"])
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(hist.index, hist.values, color="#1f4e79", label="Index (history)")
        ax.plot(future, np.exp(mean.values), color="#c55a11", label="SARIMA forecast")
        ax.fill_between(future, np.exp(ci.iloc[:, 0]), np.exp(ci.iloc[:, 1]), color="#c55a11", alpha=0.2, label="80% interval")
        ax.axhline(hist.iloc[-1], color="grey", ls="--", lw=1, label="Naive (flat)")
        ax.axvline(BREAK_START, color="grey", ls=":", lw=1)
        ax.set_title(f"{sid}: project-adjusted price index ({'base = 100'})")
        ax.legend(loc="upper left", fontsize=8)
        fig.tight_layout()
        fig.savefig(f"reports/charts/{slug(sid)}.png", dpi=120)
        plt.close(fig)

    err = pd.DataFrame(err_rows)
    fc = pd.DataFrame(fc_rows)
    err.to_csv("data/out/backtest_errors.csv", index=False)
    fc.to_csv("data/out/forecast.csv", index=False)

    # ---- Report ----
    out = ["# Step 4b: forecast backtest and 12-month forecast", "",
           "## SARIMA order per series (picked by AIC on pre-backtest data only)", "",
           "| series | (p,d,q) | seasonal | trend | first origin |", "|---|---|---|---|---|"] + spec_rows

    def mape_table(sub, title, note):
        t = (sub[sub.h.isin([3, 6, 12])].groupby(["series_id", "h", "model"])["ape_pct"].mean()
             .unstack("model").round(2))
        out.extend(["", f"## {title}", "", note, "",
                    "| series | horizon | naive | drift | sarima | best |", "|---|---|---|---|---|---|"])
        for (sid, h), r in t.iterrows():
            best = r.idxmin() if r.notna().any() else ""
            out.append(f"| {sid} | {h}m | {r.get('naive', np.nan)} | {r.get('drift', np.nan)} | {r.get('sarima', np.nan)} | {best} |")

    mape_table(err[~err.break_window], "Backtest error, normal periods (MAPE %, lower is better)",
               "Average % error of the forecast index level, over all origins whose target month is before Mar 2026.")
    mape_table(err[err.break_window], "Backtest error, target months inside the 2026 break",
               "Forecasts made before the break, judged on Mar to Sep 2026. Shows how every model copes with a shock it can't see coming.")

    # Win rate: share of origins where SARIMA's 12-month error is below naive's
    w = err[(err.h == 12)].pivot_table(index=["series_id", "origin"], columns="model", values="ape_pct")
    w = w.dropna()
    win = (w["sarima"] < w["naive"]).groupby("series_id").mean().mul(100).round(0)
    out.extend(["", "## How often SARIMA beat naive at 12 months", "",
                "| series | origins | SARIMA better than naive (%) |", "|---|---|---|"])
    for sid, v in win.items():
        out.append(f"| {sid} | {len(w.loc[sid])} | {v:.0f} |")

    # Final forecast summary
    out.extend(["", "## 12-month forecast (SARIMA, from the last month of data)", "",
                "| series | last month | index now | index in 12m | change % | 80% range of change % |",
                "|---|---|---|---|---|---|"])
    for sid, g in fc[fc.model == "sarima"].groupby("series_id", sort=False):
        now = idx[idx.series_id == sid].iloc[-1]
        last = g.iloc[-1]
        ch = 100 * (last["index"] / now["index"] - 1)
        lo, hi = 100 * (last["lower80"] / now["index"] - 1), 100 * (last["upper80"] / now["index"] - 1)
        out.append(f"| {sid} | {pd.Timestamp(now['month']):%Y-%m} | {now['index']:.1f} | {last['index']:.1f} | {ch:+.1f} | {lo:+.1f} to {hi:+.1f} |")
    out.extend(["", "Charts: reports/charts/*.png"])
    Path("reports/04b_forecast.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
