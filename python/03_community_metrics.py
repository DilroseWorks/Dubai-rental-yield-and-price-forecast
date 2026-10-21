"""
Step 3: compute yield and momentum per community, report them, export for Power BI.

  python python/03_community_metrics.py

Runs sql/04_community_metrics.sql, writes reports/03_community_metrics.md,
and exports CSVs to data/out/ (Power BI reads these in a later step).
"""
from pathlib import Path

import duckdb

con = duckdb.connect("data/dubai_property.duckdb")
con.execute(Path("sql/04_community_metrics.sql").read_text(encoding="utf-8"))
out = ["# Step 3: community yield and momentum", ""]


def table(title, sql, note=""):
    res = con.execute(sql)
    head = [d[0] for d in res.description]
    out.extend([f"## {title}", ""] + ([note, ""] if note else []))
    out.append("| " + " | ".join(head) + " |")
    out.append("|" + "---|" * len(head))
    for r in res.fetchall():
        out.append("| " + " | ".join(
            "" if v is None else f"{v:,.0f}" if isinstance(v, float) and abs(v) >= 1000
            else f"{v:,.2f}" if isinstance(v, float) else f"{v:,}" if isinstance(v, int)
            else str(v) for v in r) + " |")
    out.append("")


table("Coverage", """
    SELECT segment, count(*) AS communities_with_yield,
           sum(n_rents) AS new_leases_used, sum(n_sales) AS ready_sales_used
    FROM community_yield GROUP BY 1 ORDER BY 1""",
    "Communities need >= 50 new leases and >= 50 ready sales in qualifying size bands.")

for seg in ["Flat", "Villa"]:
    table(f"{seg}s: top 15 by gross yield", f"""
        SELECT area, gross_yield_pct, naive_yield_pct, price_yoy_6m_pct, price_yoy_12m_pct,
               volume_yoy_6m_pct, ready_aed_per_sqm_6m, n_rents, n_sales, rent_coverage_pct
        FROM community_scorecard WHERE segment = '{seg}'
        ORDER BY gross_yield_pct DESC LIMIT 15""")
    table(f"{seg}s: bottom 5 by gross yield", f"""
        SELECT area, gross_yield_pct, naive_yield_pct, price_yoy_6m_pct, n_rents, n_sales
        FROM community_scorecard WHERE segment = '{seg}'
        ORDER BY gross_yield_pct ASC LIMIT 5""")

table("Where the naive method is most wrong", """
    SELECT area, segment, gross_yield_pct, naive_yield_pct,
           round(naive_yield_pct - gross_yield_pct, 2) AS naive_minus_lfl
    FROM community_scorecard ORDER BY abs(naive_yield_pct - gross_yield_pct) DESC LIMIT 10""",
    "Naive = median rent / median price for the whole community, ignoring unit size.")

for seg in ["Flat", "Villa"]:
    table(f"Ready {seg.lower()}s: price momentum, all communities", f"""
        SELECT m.area,
               round(100*b.price_yoy_6m_same_project,1) AS same_project_yoy_6m_pct,
               round(100*m.price_yoy_6m,1)           AS raw_yoy_6m_pct,
               round(100*b.price_yoy_12m_same_project,1) AS same_project_yoy_12m_pct,
               round(100*m.volume_yoy_6m,1)          AS volume_yoy_6m_pct,
               b.projects_6m, m.n_6m, m.n_6m_ly
        FROM community_momentum m
        LEFT JOIN community_momentum_same_project b USING (area, segment, reg_type)
        WHERE m.reg_type = 'Ready' AND m.segment = '{seg}' AND m.price_yoy_6m IS NOT NULL
        ORDER BY same_project_yoy_6m_pct DESC NULLS LAST""",
        "same_project = each project compared with itself a year earlier (main measure). "
        "raw = all sales, which jumps when new projects start selling.")

table("Market-wide: same-project vs raw momentum (6m YoY)", """
    SELECT m.reg_type, m.segment, count(*) AS communities,
           round(100 * median(b.price_yoy_6m_same_project), 1) AS median_same_project_pct,
           round(100 * median(m.price_yoy_6m), 1) AS median_raw_pct,
           round(100.0 * count(*) FILTER (WHERE b.price_yoy_6m_same_project < 0) / NULLIF(count(b.price_yoy_6m_same_project), 0), 1) AS pct_falling_same_project
    FROM community_momentum m LEFT JOIN community_momentum_same_project b USING (area, segment, reg_type)
    WHERE m.price_yoy_6m IS NOT NULL GROUP BY ALL ORDER BY 1, 2""")

table("Rule 5 check: communities losing the most short leases", """
    SELECT * FROM rule5_check ORDER BY pct_dropped DESC LIMIT 15""",
    "Rule 5 now keeps 1- and 2-year leases. If pct_dropped varies a lot AND rent_sqm_dropped differs from rent_sqm_kept, rule 5 biases those communities.")

table("Area names: top projects per DLD area (for marketing-name mapping)", """
    SELECT * FROM area_top_projects ORDER BY area""")

Path("data/out").mkdir(parents=True, exist_ok=True)
for t in ["community_scorecard", "community_momentum", "community_momentum_same_project", "yield_cells"]:
    con.execute(f"COPY {t} TO 'data/out/{t}.csv' (HEADER)")
out.append("Exported to data/out/: community_scorecard.csv, community_momentum.csv, community_momentum_same_project.csv, yield_cells.csv")

Path("reports/03_community_metrics.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
