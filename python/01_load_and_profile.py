"""
Step 1: load the raw DLD files into DuckDB and profile them.

What it does
  1. Reads every CSV you downloaded for one dataset (sales or rents) as text,
     so nothing is silently mis-parsed on the way in.
  2. Saves an untouched copy as Parquet (data/raw/<name>.parquet): our "raw layer".
  3. Writes a profile report (reports/01_profile_<name>.md) answering:
     how many rows, which columns, which date range, any months missing,
     any duplicate rows or IDs, how empty each column is.

Usage (run from the project folder):
  python python/01_load_and_profile.py --name sales_mirror   --files "downloads/sales_mirror/*.parquet"
  python python/01_load_and_profile.py --name sales_official --files "downloads/sales_official_2026/*.csv"
  python python/01_load_and_profile.py --name rents          --files "downloads/rents/*.csv"
"""
import argparse
import re
from pathlib import Path

import duckdb

# Date formats seen in DLD exports. We try each one and keep the first that works.
DATE_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%d-%m-%Y %H:%M:%S",
                "%d/%m/%Y", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y"]


def q(col: str) -> str:
    """Quote a column name (DLD headers contain spaces, brackets and question marks)."""
    return '"' + col.replace('"', '""') + '"'


def pick_date_format(con, table: str, col: str) -> str:
    """Pick the ONE format that parses the most values in this column.
    One format per column (not per row) so 03-04-2024 can't be read as
    3 April in one row and 4 March in the next."""
    best, best_n = DATE_FORMATS[0], -1
    for f in DATE_FORMATS:
        n = con.execute(f"SELECT count(try_strptime(trim({q(col)}), '{f}')) FROM {table}").fetchone()[0]
        if n > best_n:
            best, best_n = f, n
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="sales or rents")
    ap.add_argument("--files", required=True, help='glob, e.g. "downloads/sales/*.csv"')
    args = ap.parse_args()

    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("reports").mkdir(exist_ok=True)
    con = duckdb.connect("data/dubai_property.duckdb")

    # all_varchar: read everything as text. Type conversion is a later, deliberate step.
    # union_by_name: if chunk files have columns in different orders, match by header.
    # filename: remember which file each row came from (needed to trace duplicates).
    if args.files.lower().endswith(".parquet"):
        # Parquet already carries types. We still cast everything to text so the
        # profile below treats every source the same way.
        source = f"(SELECT COLUMNS(* EXCLUDE (filename))::VARCHAR, filename FROM read_parquet('{args.files}', filename = true))"
    else:
        source = f"read_csv('{args.files}', all_varchar = true, union_by_name = true, filename = true, header = true)"
    con.execute(f"CREATE OR REPLACE TABLE raw_{args.name} AS SELECT * FROM {source}")
    t = f"raw_{args.name}"
    con.execute(f"COPY {t} TO 'data/raw/{args.name}.parquet' (FORMAT parquet)")

    cols = [r[0] for r in con.execute(f"DESCRIBE {t}").fetchall() if r[0] != "filename"]
    n_rows = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    n_files = con.execute(f"SELECT count(DISTINCT filename) FROM {t}").fetchone()[0]
    out = [f"# Profile: {args.name}", "",
           f"- Files read: **{n_files}**", f"- Rows: **{n_rows:,}**",
           f"- Columns: **{len(cols)}**", ""]

    # 1. Exact duplicate rows (same values in every column). Common when date-range
    #    exports overlap by a day.
    col_list = ", ".join(q(c) for c in cols)
    dup_rows = con.execute(
        f"SELECT count(*) - count(DISTINCT ({col_list})) FROM (SELECT {col_list} FROM {t})"
    ).fetchone()[0]
    out.append(f"- Exact duplicate rows: **{dup_rows:,}**")

    # 2. Duplicate IDs: an ID column should be unique per row.
    id_cols = [c for c in cols if re.search(r"(transaction|contract).*(id|number|no)", c, re.I)]
    for c in id_cols:
        d = con.execute(f"SELECT count(*) - count(DISTINCT {q(c)}), count(*) - count({q(c)}) FROM {t}").fetchone()
        out.append(f"- Column `{c}`: **{d[0]:,}** repeated values, **{d[1]:,}** empty")
    out.append("")

    # 3. Date columns: how many parse, what range, and are any months missing?
    date_cols = [c for c in cols if re.search(r"date", c, re.I)]
    for c in date_cols:
        fmt = pick_date_format(con, t, c)
        expr = f"try_strptime(trim({q(c)}), '{fmt}')"
        mn, mx, ok, filled = con.execute(
            f"SELECT min({expr}), max({expr}), count({expr}), count({q(c)}) FROM {t}").fetchone()
        out += [f"## Date column `{c}` (format used: `{fmt}`)",
                f"- Parsed: {ok:,} of {filled:,} non-empty values; range **{mn} to {mx}**"]
        bad = con.execute(f"SELECT {q(c)} FROM {t} WHERE {q(c)} IS NOT NULL AND {expr} IS NULL LIMIT 5").fetchall()
        if bad:
            out.append(f"- Examples that did NOT parse: {[b[0] for b in bad]}")
        monthly = con.execute(f"""
            WITH m AS (SELECT date_trunc('month', {expr}) AS month, count(*) AS n
                       FROM {t} WHERE {expr} IS NOT NULL GROUP BY 1),
                 s AS (SELECT unnest(generate_series(min(month), max(month), INTERVAL 1 MONTH)) AS month FROM m)
            SELECT s.month, coalesce(m.n, 0) FROM s LEFT JOIN m USING (month) ORDER BY 1
        """).fetchall()
        gaps = [str(m[0])[:7] for m in monthly if m[1] == 0]
        if len(gaps) <= 24:
            out.append(f"- Months with zero rows: {gaps if gaps else 'none'}")
        else:
            # Hundreds of empty months means a few junk dates stretch the range (e.g. 1925).
            out.append(f"- Months with zero rows: **{len(gaps)}** (first {gaps[0]}, last {gaps[-1]}). "
                       "A long list like this usually means a handful of junk dates, not missing data.")
        out.append("- Rows per month (last 24 months):")
        out.append("")
        out.append("| month | rows |\n|---|---|")
        out += [f"| {str(m[0])[:7]} | {m[1]:,} |" for m in monthly[-24:]]
        out.append("")

    # 4. Every column: how empty it is, how many distinct values, an example.
    out += ["## Columns", "", "| column | % empty | distinct | example |", "|---|---|---|---|"]
    for c in cols:
        pct, nd, ex = con.execute(f"""
            SELECT round(100.0 * count(*) FILTER (WHERE {q(c)} IS NULL OR trim({q(c)}) = '') / count(*), 1),
                   approx_count_distinct({q(c)}), any_value({q(c)})
            FROM {t}""").fetchone()
        ex = (str(ex)[:40] if ex is not None else "").replace("|", "/")
        out.append(f"| {c} | {pct} | {nd:,} | {ex} |")

    # 5. Categories: full value counts for low-cardinality columns (types, usage, rooms...).
    out += ["", "## Category values (columns with 2 to 40 distinct values)", ""]
    for c in cols:
        nd = con.execute(f"SELECT count(DISTINCT {q(c)}) FROM {t}").fetchone()[0]
        if 2 <= nd <= 40:
            vals = con.execute(f"SELECT {q(c)}, count(*) FROM {t} GROUP BY 1 ORDER BY 2 DESC").fetchall()
            out.append(f"**{c}**: " + ", ".join(f"{v} ({n:,})" for v, n in vals))
            out.append("")

    report = Path(f"reports/01_profile_{args.name}.md")
    report.write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out[:12]))
    print(f"\nFull report: {report}")


if __name__ == "__main__":
    main()
