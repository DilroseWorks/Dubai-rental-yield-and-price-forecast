# Step 4b: forecast backtest and 12-month forecast

## SARIMA order per series (picked by AIC on pre-backtest data only)

| series | (p,d,q) | seasonal | trend | first origin |
|---|---|---|---|---|
| DUBAI / Ready / Flat | (1, 1, 0) | (0, 0, 0, 0) | n | 2018-01 |
| DUBAI / Ready / Villa | (0, 1, 1) | (0, 0, 0, 0) | n | 2018-01 |
| DUBAI / Off-Plan / Flat | (2, 1, 1) | (0, 0, 1, 12) | n | 2018-01 |
| DUBAI / Off-Plan / Villa | (1, 1, 0) | (0, 0, 0, 0) | n | 2021-08 |
| MARSA DUBAI / Ready / Flat | (0, 1, 1) | (0, 0, 0, 0) | n | 2018-01 |

## Backtest error, normal periods (MAPE %, lower is better)

Average % error of the forecast index level, over all origins whose target month is before Mar 2026.

| series | horizon | naive | drift | sarima | best |
|---|---|---|---|---|---|
| DUBAI / Off-Plan / Flat | 3m | 1.64 | 1.35 | 1.62 | drift |
| DUBAI / Off-Plan / Flat | 6m | 2.44 | 2.15 | 2.39 | drift |
| DUBAI / Off-Plan / Flat | 12m | 4.6 | 4.17 | 4.15 | sarima |
| DUBAI / Off-Plan / Villa | 3m | 3.15 | 2.04 | 3.52 | drift |
| DUBAI / Off-Plan / Villa | 6m | 5.64 | 3.46 | 6.15 | drift |
| DUBAI / Off-Plan / Villa | 12m | 11.56 | 6.18 | 12.21 | drift |
| DUBAI / Ready / Flat | 3m | 2.99 | 2.32 | 3.22 | drift |
| DUBAI / Ready / Flat | 6m | 5.75 | 3.9 | 5.8 | drift |
| DUBAI / Ready / Flat | 12m | 10.79 | 7.32 | 10.9 | drift |
| DUBAI / Ready / Villa | 3m | 4.32 | 3.22 | 5.9 | drift |
| DUBAI / Ready / Villa | 6m | 7.9 | 5.22 | 9.31 | drift |
| DUBAI / Ready / Villa | 12m | 14.07 | 8.95 | 15.51 | drift |
| MARSA DUBAI / Ready / Flat | 3m | 3.99 | 3.76 | 4.31 | drift |
| MARSA DUBAI / Ready / Flat | 6m | 6.62 | 5.86 | 6.87 | drift |
| MARSA DUBAI / Ready / Flat | 12m | 12.63 | 11.51 | 12.99 | drift |

## Backtest error, target months inside the 2026 break

Forecasts made before the break, judged on Mar to Sep 2026. Shows how every model copes with a shock it can't see coming.

| series | horizon | naive | drift | sarima | best |
|---|---|---|---|---|---|
| DUBAI / Off-Plan / Flat | 3m | 0.96 | 1.69 | 1.24 | naive |
| DUBAI / Off-Plan / Flat | 6m | 1.81 | 3.05 | 2.39 | naive |
| DUBAI / Off-Plan / Flat | 12m | 2.96 | 3.45 | 3.15 | naive |
| DUBAI / Off-Plan / Villa | 3m | 1.38 | 3.44 | 1.49 | naive |
| DUBAI / Off-Plan / Villa | 6m | 2.48 | 8.26 | 2.13 | sarima |
| DUBAI / Off-Plan / Villa | 12m | 2.39 | 11.21 | 2.4 | naive |
| DUBAI / Ready / Flat | 3m | 2.99 | 4.07 | 3.09 | naive |
| DUBAI / Ready / Flat | 6m | 4.31 | 8.34 | 4.47 | naive |
| DUBAI / Ready / Flat | 12m | 3.89 | 14.6 | 3.91 | naive |
| DUBAI / Ready / Villa | 3m | 5.23 | 6.41 | 4.86 | sarima |
| DUBAI / Ready / Villa | 6m | 6.34 | 8.82 | 6.23 | sarima |
| DUBAI / Ready / Villa | 12m | 6.69 | 8.78 | 8.54 | naive |
| MARSA DUBAI / Ready / Flat | 3m | 6.71 | 7.73 | 5.68 | sarima |
| MARSA DUBAI / Ready / Flat | 6m | 8.08 | 11.24 | 6.91 | sarima |
| MARSA DUBAI / Ready / Flat | 12m | 6.87 | 14.37 | 6.69 | sarima |

## How often SARIMA beat naive at 12 months

| series | origins | SARIMA better than naive (%) |
|---|---|---|
| DUBAI / Off-Plan / Flat | 32 | 62 |
| DUBAI / Off-Plan / Villa | 17 | 18 |
| DUBAI / Ready / Flat | 32 | 28 |
| DUBAI / Ready / Villa | 32 | 22 |
| MARSA DUBAI / Ready / Flat | 32 | 34 |

## 12-month forecast (SARIMA, from the last month of data)

| series | last month | index now | index in 12m | change % | 80% range of change % |
|---|---|---|---|---|---|
| DUBAI / Ready / Flat | 2026-09 | 146.5 | 144.1 | -1.7 | -11.0 to +8.7 |
| DUBAI / Ready / Villa | 2026-09 | 229.0 | 230.7 | +0.7 | -19.4 to +25.9 |
| DUBAI / Off-Plan / Flat | 2026-09 | 135.0 | 134.4 | -0.5 | -8.4 to +8.1 |
| DUBAI / Off-Plan / Villa | 2026-09 | 173.4 | 172.8 | -0.4 | -7.7 to +7.5 |
| MARSA DUBAI / Ready / Flat | 2026-09 | 162.7 | 163.1 | +0.2 | -12.8 to +15.2 |

Charts: reports/charts/*.png