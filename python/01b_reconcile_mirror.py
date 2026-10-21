"""
Step 1b: can we trust the mirror?

The 2004-2026 sales history comes from a third-party copy of DLD data on Hugging Face,
not from DLD directly. Before building on it, we compare its 2026 months against the
official 2026 export you downloaded from dubailand.gov.ae. If monthly counts and median
prices match closely, the mirror is a faithful copy. If not, we find out why now.

Run after 01_load_and_profile.py has created raw_sales_mirror and raw_sales_official:
  python python/01b_reconcile_mirror.py
Optional, if auto-detection picks the wrong columns (check reports/01_profile_sales_official.md):
  python python/01b_reconcile_mirror.py --date-col "Transaction Date" --amount-col "Amount"
"""
import argparse
import re
from pathlib import Path

import duckdb

FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%d-%m-%Y %H:%M:%S",
           "%d/%m/%Y", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y"]


def q(c):
    return '"' + c.replace('"', '""') + '"'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date-col")
    ap.add_argument("--amount-col")
    a = ap.parse_args()
    con = duckdb.connect("data/dubai_property.duckdb")

    cols = [r[0] for r in con.execute("DESCRIBE raw_sales_official").fetchall()]
    date_col = a.date_col or next(c for c in cols if re.search("date", c, re.I))
    amount_col = a.amount_col or next(c for c in cols if re.search(r"^(amount|actual_worth|trans.*value)", c, re.I))
    fmt = max(FORMATS, key=lambda f: con.execute(
        f"SELECT count(try_strptime(trim({q(date_col)}), '{f}')) FROM raw_sales_official").fetchone()[0])

    # Both sides: one row per month with a count and a median price.
    # The official export was filtered to Sales + Residential on the website,
    # so the mirror gets the same filter here.
    rows = con.execute(f"""
        WITH official AS (
            SELECT date_trunc('month', try_strptime(trim({q(date_col)}), '{fmt}')) AS month,
                   count(*) AS n, median(try_cast(replace({q(amount_col)}, ',', '') AS DOUBLE)) AS med
            FROM raw_sales_official GROUP BY 1),
        mirror AS (
            SELECT date_trunc('month', try_cast(instance_date AS DATE)) AS month,
                   count(*) AS n, median(try_cast(price_aed AS DOUBLE)) AS med
            FROM raw_sales_mirror
            WHERE usage_label = 'Residential' AND instance_date >= '2026-01-01'
            GROUP BY 1)
        SELECT strftime(month, '%Y-%m'), o.n, m.n,
               round(100.0 * (m.n - o.n) / o.n, 1),
               round(o.med)::BIGINT, round(m.med)::BIGINT
        FROM official o FULL JOIN mirror m USING (month)
        WHERE month >= DATE '2026-01-01' ORDER BY month
    """).fetchall()

    out = [f"Official file: date column = {date_col!r} ({fmt}), amount column = {amount_col!r}", "",
           "| month | official rows | mirror rows | count diff % | official median AED | mirror median AED |",
           "|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| " + " | ".join("" if v is None else f"{v:,}" if isinstance(v, (int, float)) else str(v) for v in r) + " |")
    out += ["", "Read it like this: full months should match within a few percent.",
            "The newest month in the mirror is partial (it stops mid-month), so ignore its gap."]
    # Written by Python (UTF-8), not by shell redirection: on Windows PowerShell,
    # "> file" saves UTF-16, which other tools then misread.
    Path("reports/01b_reconcile.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
