"""
Step 6a: copy the small dashboard tables into app/data/ so the Streamlit app can run
without the DuckDB file (which is too big for GitHub and never leaves your laptop).

  python python/07_export_powerbi.py      (if not run since the last data change)
  python python/08_prepare_app_data.py
"""
import shutil
from pathlib import Path

SRC, DST = Path("data/out/powerbi"), Path("app/data")
TABLES = ["community_scorecard", "index_lines", "scenario_summary", "backtest_summary", "monthly_sales",
          "monthly_rents"]
DST.mkdir(parents=True, exist_ok=True)
for t in TABLES:
    src = SRC / f"{t}.csv"
    if not src.exists():
        raise SystemExit(f"{src} not found. Run python/07_export_powerbi.py first.")
    shutil.copy(src, DST / src.name)
    print(f"copied {src.name} ({src.stat().st_size / 1024:.0f} KB)")
