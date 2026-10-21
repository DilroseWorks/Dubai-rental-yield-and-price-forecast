"""
Step 1c: four questions the profile reports raised, answered with SQL.

  A. Rents: 95,027 exact duplicate rows (14%). Download mistake or real data?
  B. January 2026: the mirror has 13% fewer sales than the official file. Which days or types are missing?
  C. Mirror history: from which year is there enough data to model?
  D. Area names: how many rent areas match a sales area name exactly?

Run after 01_load_and_profile.py (it reads the raw_* tables in data/dubai_property.duckdb):
  python python/01c_diagnose.py
Writes reports/01c_diagnose.md.
"""
from pathlib import Path

import duckdb

con = duckdb.connect("data/dubai_property.duckdb")
out = ["# Step 1c diagnostics", ""]


def table(title, sql, note=""):
    res = con.execute(sql)
    head = [d[0] for d in res.description]
    rows = res.fetchall()
    out.extend([f"## {title}", ""] + ([note, ""] if note else []))
    out.append("| " + " | ".join(head) + " |")
    out.append("|" + "---|" * len(head))
    for r in rows:
        out.append("| " + " | ".join("" if v is None else f"{v:,}" if isinstance(v, int) else str(v) for v in r) + " |")
    out.append("")


# A. Rent duplicates. Group identical rows (ignoring which file they came from) and ask:
#    are the copies in the SAME file or spread ACROSS files?
#    Across files = our download overlapped. Same file = DLD itself lists identical rows,
#    e.g. one bulk registration of 50 identical labour-camp rooms.
rent_cols = [r[0] for r in con.execute("DESCRIBE raw_rents").fetchall() if r[0] != "filename"]
cols = ", ".join(f'"{c}"' for c in rent_cols)
table("A. Rent duplicates: where are the copies?", f"""
    WITH g AS (
        SELECT {cols}, count(*) AS copies, count(DISTINCT filename) AS n_files
        FROM raw_rents GROUP BY ALL HAVING count(*) > 1)
    SELECT CASE WHEN n_files > 1 THEN 'across files' ELSE 'same file' END AS where_copies_are,
           PROP_SUB_TYPE_EN AS sub_type,
           sum(copies - 1) AS extra_rows, count(*) AS duplicate_groups, max(copies) AS max_copies
    FROM g GROUP BY ALL ORDER BY extra_rows DESC LIMIT 15""",
    "Extra rows = rows you'd remove by de-duplicating.")

# B. January gap, day by day. If whole days are missing in the mirror, it lost a batch.
#    If every day is a little short, it filters differently.
table("B. January 2026 sales per day: official vs mirror", """
    WITH o AS (SELECT CAST(try_strptime(INSTANCE_DATE, '%Y-%m-%d %H:%M:%S') AS DATE) AS day, count(*) AS official
               FROM raw_sales_official GROUP BY 1),
         m AS (SELECT CAST(instance_date AS DATE) AS day, count(*) AS mirror
               FROM raw_sales_mirror WHERE usage_label = 'Residential' GROUP BY 1)
    SELECT day, official, mirror, official - coalesce(mirror, 0) AS missing_in_mirror
    FROM o LEFT JOIN m USING (day)
    WHERE day < DATE '2026-02-01' ORDER BY day""")

# C. History depth: rows per year in the mirror, residential, passing quality checks.
#    The forecast needs years with enough sales for a stable monthly median.
table("C. Mirror: residential sales per year (quality_flags = 0)", """
    SELECT year(CAST(instance_date AS DATE)) AS year, count(*) AS sales,
           round(100.0 * count(*) FILTER (WHERE reg_type_label = 'Off-Plan') / count(*), 1) AS pct_off_plan
    FROM raw_sales_mirror
    WHERE usage_label = 'Residential' AND quality_flags = '0'
    GROUP BY 1 HAVING year >= 2000 ORDER BY 1""")

# D. Area names: rents vs mirror sales, after trimming and upper-casing.
#    Every rent area that doesn't match can't get a yield until we map it.
table("D. Rent areas with no exact match in sales (top 25 by rent contracts)", """
    WITH s AS (SELECT DISTINCT upper(trim(area_name_en)) AS area FROM raw_sales_mirror),
         r AS (SELECT upper(trim(AREA_EN)) AS area, count(*) AS contracts FROM raw_rents GROUP BY 1)
    SELECT r.area AS rent_area, r.contracts
    FROM r LEFT JOIN s USING (area) WHERE s.area IS NULL
    ORDER BY contracts DESC LIMIT 25""")
total, matched = con.execute("""
    WITH s AS (SELECT DISTINCT upper(trim(area_name_en)) AS area FROM raw_sales_mirror)
    SELECT count(*), count(*) FILTER (WHERE area IN (SELECT area FROM s))
    FROM (SELECT upper(trim(AREA_EN)) AS area FROM raw_rents)""").fetchone()
out.append(f"Rent contracts whose area matches a sales area exactly: **{matched:,} of {total:,} ({100*matched/total:.1f}%)**")

Path("reports").mkdir(exist_ok=True)
Path("reports/01c_diagnose.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
