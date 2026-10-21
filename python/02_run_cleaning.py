"""
Step 2: run the cleaning SQL and report what it did.

  python python/02_run_cleaning.py

Runs sql/02_sales_clean.sql and sql/03_rents_clean.sql against data/dubai_property.duckdb,
then writes reports/02_cleaning.md with:
  - an exclusion waterfall per dataset (how many rows each rule removed, and why)
  - the January check on the mirror (is every January short, or only 2026?)
  - last 12 months of sales by Ready/Off-Plan, and rents by segment and version
"""
from pathlib import Path

import duckdb

con = duckdb.connect("data/dubai_property.duckdb")
for f in ["sql/02_sales_clean.sql", "sql/03_rents_clean.sql"]:
    con.execute(Path(f).read_text(encoding="utf-8"))
    print(f"ran {f}")

out = ["# Step 2 cleaning report", ""]


def table(title, sql, note=""):
    res = con.execute(sql)
    head = [d[0] for d in res.description]
    out.extend([f"## {title}", ""] + ([note, ""] if note else []))
    out.append("| " + " | ".join(head) + " |")
    out.append("|" + "---|" * len(head))
    for r in res.fetchall():
        out.append("| " + " | ".join(
            "" if v is None else f"{v:,.0f}" if isinstance(v, float) and abs(v) >= 100
            else f"{v:,.1f}" if isinstance(v, float) else f"{v:,}" if isinstance(v, int)
            else str(v) for v in r) + " |")
    out.append("")


waterfall = """
    SELECT coalesce(exclude_reason, 'KEPT') AS rule, count(*) AS rows,
           round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
    FROM {t} GROUP BY 1 ORDER BY 1"""
table("Sales: exclusion waterfall", waterfall.format(t="sales_flagged"),
      "Each row is counted under the FIRST rule it fails.")
n_raw, n_collapsed = con.execute(
    "SELECT (SELECT count(*) FROM raw_rents), (SELECT count(*) FROM rents_flagged)").fetchone()
table("Rents: exclusion waterfall", waterfall.format(t="rents_flagged"),
      f"Before these rules, {n_raw - n_collapsed:,} identical copies were collapsed "
      f"({n_raw:,} raw rows → {n_collapsed:,}).")

table("Sales: assumptions worth knowing", """
    SELECT count(*) FILTER (WHERE sub_type_assumed_flat) AS units_with_no_sub_type_treated_as_flat,
           round(100.0 * count(*) FILTER (WHERE sub_type_assumed_flat) / count(*), 1) AS pct_of_clean
    FROM sales_clean""")

table("Sales: rows kept without a procedure name, by year", """
    SELECT year(month) AS yr, count(*) FILTER (WHERE procedure_missing) AS no_procedure,
           count(*) AS all_kept,
           round(100.0 * count(*) FILTER (WHERE procedure_missing) / count(*), 1) AS pct
    FROM sales_clean GROUP BY 1 HAVING count(*) FILTER (WHERE procedure_missing) > 0 ORDER BY 1""",
    "If these sit only in 2026, it's how the mirror ingests recent data, not a real category.")

# 2026 check against the OFFICIAL file, split Ready / Off-Plan, with the same
# filters translated to the official column names. Totals matched in step 1;
# this checks that the SPLIT survives cleaning too.
table("2026 check: clean mirror vs official, Ready and Off-Plan", """
    WITH o AS (
        SELECT date_trunc('month', try_strptime(INSTANCE_DATE, '%Y-%m-%d %H:%M:%S')) AS month,
               IS_OFFPLAN_EN AS reg_type, count(*) AS official
        FROM raw_sales_official
        WHERE PROCEDURE_EN IN ('Sale', 'Sell', 'Sell - Pre registration', 'Delayed Sell', 'Sale On Payment Plan')
          AND (PROP_SB_TYPE_EN IN ('Flat', 'Villa', 'Residential Flats', 'Residential / Villas',
                                   'Residential / Attached Villas', 'Stacked Townhouses'))
        GROUP BY ALL),
    m AS (SELECT month, reg_type, count(*) AS mirror FROM sales_clean
          WHERE month >= DATE '2026-01-01' GROUP BY ALL)
    SELECT strftime(month, '%Y-%m') AS month, reg_type, official, mirror,
           round(100.0 * (mirror - official) / official, 1) AS diff_pct
    FROM o JOIN m USING (month, reg_type) ORDER BY 1, 2""",
    "Within about 5% either way = the cleaned mirror is consistent with the official source.")

# January check: compare each January with the average of the December before
# and the February after. A short 2026 January only is a mirror gap;
# short Januaries every year would mean a seasonal pattern (or a recurring gap).
table("January check (mirror, clean sales)", """
    WITH m AS (SELECT month, count(*) AS n FROM sales_clean GROUP BY 1)
    SELECT strftime(j.month, '%Y-%m') AS january, j.n AS jan_sales,
           round((d.n + f.n) / 2.0) AS avg_dec_feb,
           round(100.0 * j.n / ((d.n + f.n) / 2.0)) AS jan_as_pct_of_neighbours
    FROM m j
    JOIN m d ON d.month = j.month - INTERVAL 1 MONTH
    JOIN m f ON f.month = j.month + INTERVAL 1 MONTH
    WHERE month(j.month) = 1 ORDER BY 1""",
    "About 100 = a normal January. Well below 100 only in 2026 = a mirror gap; low every year = seasonality.")

table("Sales, last 12 months: Ready vs Off-Plan", """
    SELECT strftime(month, '%Y-%m') AS month, reg_type, count(*) AS sales,
           median(price_aed) AS median_price_aed, median(price_per_sqm) AS median_aed_per_sqm,
           median(size_sqm) AS median_size_sqm
    FROM sales_clean WHERE month >= DATE '2025-10-01'
    GROUP BY ALL ORDER BY 1, 2""")

table("Rents (Jan to Sep 2026): by segment and version", """
    SELECT segment, version, count(*) AS contracts,
           median(annual_rent) AS median_annual_rent, median(rent_per_sqm) AS median_rent_per_sqm,
           median(size_sqm) AS median_size_sqm
    FROM rents_clean GROUP BY ALL ORDER BY 1, 2""")

Path("reports").mkdir(exist_ok=True)
Path("reports/02_cleaning.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
