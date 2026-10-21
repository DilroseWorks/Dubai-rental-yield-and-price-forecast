"""
Run any .sql file against the project database and print the result as a table.

  python python/run_query.py sql/check_2026_break.sql
"""
import sys

import duckdb

con = duckdb.connect("data/dubai_property.duckdb", read_only=True)
res = con.execute(open(sys.argv[1], encoding="utf-8").read())
head = [d[0] for d in res.description]
print("| " + " | ".join(head) + " |")
print("|" + "---|" * len(head))
for r in res.fetchall():
    print("| " + " | ".join("" if v is None else f"{v:,.0f}" if isinstance(v, float) and abs(v) >= 100
                            else f"{v:,.1f}" if isinstance(v, float) else str(v) for v in r) + " |")
