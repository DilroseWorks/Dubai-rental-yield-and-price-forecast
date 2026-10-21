# Step 2 cleaning report

## Sales: exclusion waterfall

Each row is counted under the FIRST rule it fails.

| rule | rows | pct |
|---|---|---|
| 1 failed the mirror's quality checks | 28,495 | 2.1 |
| 2 not residential | 183,245 | 13.4 |
| 3 not a market sale (lease-to-own, developer registration...) | 54,896 | 4.0 |
| 4 not a flat or villa | 72,531 | 5.3 |
| 5 before 2010 (thin data, 2009 backlog) | 70,595 | 5.1 |
| 6 partial month (Oct 2026) | 1,025 | 0.1 |
| KEPT | 961,490 | 70.1 |

## Rents: exclusion waterfall

Before these rules, 95,027 identical copies were collapsed (685,015 raw rows → 589,988).

| rule | rows | pct |
|---|---|---|
| 1 not a flat or villa (labour camp, staff housing...) | 19,009 | 3.2 |
| 2 contract covers several properties | 9,230 | 1.6 |
| 3 no rent amount | 1 | 0.0 |
| 4 implausible size | 15,989 | 2.7 |
| 5 not a 1- or 2-year lease | 23,722 | 4.0 |
| 6 partial month (Oct 2026) | 43,134 | 7.3 |
| 7 extreme rent per sqm (bottom/top 1%) | 9,558 | 1.6 |
| KEPT | 469,345 | 79.6 |

## Sales: assumptions worth knowing

| units_with_no_sub_type_treated_as_flat | pct_of_clean |
|---|---|
| 0 | 0.0 |

## Sales: rows kept without a procedure name, by year

If these sit only in 2026, it's how the mirror ingests recent data, not a real category.

| yr | no_procedure | all_kept | pct |
|---|---|---|---|
| 2,026 | 17,816 | 102,325 | 17.4 |

## 2026 check: clean mirror vs official, Ready and Off-Plan

Within about 5% either way = the cleaned mirror is consistent with the official source.

| month | reg_type | official | mirror | diff_pct |
|---|---|---|---|---|
| 2026-01 | Off-Plan | 10,570 | 10,096 | -4.5 |
| 2026-01 | Ready | 3,870 | 3,691 | -4.6 |
| 2026-02 | Off-Plan | 10,018 | 10,336 | 3.2 |
| 2026-02 | Ready | 4,009 | 4,127 | 2.9 |
| 2026-03 | Off-Plan | 9,025 | 8,959 | -0.7 |
| 2026-03 | Ready | 2,542 | 2,528 | -0.6 |
| 2026-04 | Off-Plan | 9,412 | 9,334 | -0.8 |
| 2026-04 | Ready | 2,409 | 2,394 | -0.6 |
| 2026-05 | Off-Plan | 6,632 | 6,526 | -1.6 |
| 2026-05 | Ready | 1,967 | 1,942 | -1.3 |
| 2026-06 | Off-Plan | 9,059 | 8,988 | -0.8 |
| 2026-06 | Ready | 2,533 | 2,508 | -1.0 |
| 2026-07 | Off-Plan | 8,665 | 8,903 | 2.7 |
| 2026-07 | Ready | 3,044 | 2,923 | -4.0 |
| 2026-08 | Off-Plan | 7,368 | 7,412 | 0.6 |
| 2026-08 | Ready | 2,675 | 2,590 | -3.2 |
| 2026-09 | Off-Plan | 6,539 | 6,447 | -1.4 |
| 2026-09 | Ready | 2,645 | 2,621 | -0.9 |

## January check (mirror, clean sales)

About 100 = a normal January. Well below 100 only in 2026 = a mirror gap; low every year = seasonality.

| january | jan_sales | avg_dec_feb | jan_as_pct_of_neighbours |
|---|---|---|---|
| 2011-01 | 1,917 | 1,580 | 121 |
| 2012-01 | 1,545 | 1,852 | 83.0 |
| 2013-01 | 2,942 | 2,835 | 104 |
| 2014-01 | 3,262 | 4,421 | 74.0 |
| 2015-01 | 2,778 | 3,028 | 92.0 |
| 2016-01 | 1,844 | 2,922 | 63.0 |
| 2017-01 | 3,048 | 2,673 | 114 |
| 2018-01 | 2,100 | 2,258 | 93.0 |
| 2019-01 | 1,594 | 2,035 | 78.0 |
| 2020-01 | 1,954 | 3,204 | 61.0 |
| 2021-01 | 2,333 | 2,531 | 92.0 |
| 2022-01 | 4,087 | 4,273 | 96.0 |
| 2023-01 | 7,498 | 7,170 | 105 |
| 2024-01 | 9,068 | 9,387 | 97.0 |
| 2025-01 | 10,570 | 12,654 | 84.0 |
| 2026-01 | 13,787 | 15,644 | 88.0 |

## Sales, last 12 months: Ready vs Off-Plan

| month | reg_type | sales | median_price_aed | median_aed_per_sqm | median_size_sqm |
|---|---|---|---|---|---|
| 2025-10 | Off-Plan | 12,371 | 1,362,850 | 19,119 | 73.6 |
| 2025-10 | Ready | 4,459 | 1,220,000 | 14,819 | 79.8 |
| 2025-11 | Off-Plan | 12,077 | 1,506,918 | 20,132 | 74.5 |
| 2025-11 | Ready | 4,132 | 1,280,000 | 15,412 | 84.7 |
| 2025-12 | Off-Plan | 12,859 | 1,402,584 | 20,042 | 74.1 |
| 2025-12 | Ready | 3,966 | 1,298,725 | 15,585 | 83.4 |
| 2026-01 | Off-Plan | 10,096 | 1,787,619 | 19,931 | 82.0 |
| 2026-01 | Ready | 3,691 | 1,310,000 | 15,443 | 84.5 |
| 2026-02 | Off-Plan | 10,336 | 1,587,000 | 19,613 | 78.1 |
| 2026-02 | Ready | 4,127 | 1,350,000 | 16,440 | 82.2 |
| 2026-03 | Off-Plan | 8,959 | 1,615,888 | 19,644 | 77.3 |
| 2026-03 | Ready | 2,528 | 1,200,000 | 15,284 | 82.0 |
| 2026-04 | Off-Plan | 9,334 | 1,650,075 | 20,738 | 76.3 |
| 2026-04 | Ready | 2,394 | 1,350,000 | 15,921 | 84.0 |
| 2026-05 | Off-Plan | 6,526 | 1,148,868 | 18,423 | 67.4 |
| 2026-05 | Ready | 1,942 | 1,200,000 | 14,958 | 77.6 |
| 2026-06 | Off-Plan | 8,988 | 1,095,626 | 18,672 | 63.0 |
| 2026-06 | Ready | 2,508 | 1,300,000 | 15,469 | 84.4 |
| 2026-07 | Off-Plan | 8,903 | 1,002,238 | 18,715 | 59.5 |
| 2026-07 | Ready | 2,923 | 1,275,000 | 15,063 | 84.8 |
| 2026-08 | Off-Plan | 7,412 | 1,100,000 | 18,712 | 63.7 |
| 2026-08 | Ready | 2,590 | 1,349,500 | 15,535 | 86.1 |
| 2026-09 | Off-Plan | 6,447 | 1,245,120 | 18,791 | 69.1 |
| 2026-09 | Ready | 2,621 | 1,350,000 | 15,376 | 85.2 |

## Rents (Jan to Sep 2026): by segment and version

| segment | version | contracts | median_annual_rent | median_rent_per_sqm | median_size_sqm |
|---|---|---|---|---|---|
| Flat | New | 177,287 | 70,000 | 1,000 | 74.4 |
| Flat | Renewed | 249,566 | 59,500 | 736 | 83.6 |
| Villa | New | 19,707 | 180,000 | 765 | 238 |
| Villa | Renewed | 22,785 | 168,000 | 632 | 271 |
