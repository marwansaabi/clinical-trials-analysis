"""Runs every query in sql/ against data/aact.duckdb and saves each result as a CSV in outputs/.

Each query to export is preceded by a comment line "-- @output: <name>".
Usage: python scripts/02_run_analysis.py
"""
import re
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


def main():
    OUT.mkdir(exist_ok=True)
    con = duckdb.connect(str(__import__("os").environ.get("AACT_DB", ROOT / "data" / "aact.duckdb")), read_only=True)
    con.execute((ROOT / "sql" / "00_views.sql").read_text())
    for sql_file in sorted((ROOT / "sql").glob("0[1-9]_*.sql")):
        text = sql_file.read_text()
        parts = re.split(r"^-- @output: (\w+)\s*$", text, flags=re.M)
        if parts[0].strip():
            con.execute(parts[0])  # setup statements (e.g. views) before the first output
        for name, query in zip(parts[1::2], parts[2::2]):
            df = con.sql(query.strip().rstrip(";")).df()
            df.to_csv(OUT / f"{name}.csv", index=False)
            print(f"{sql_file.name:20s} -> outputs/{name}.csv ({len(df)} rows)")
    con.close()


if __name__ == "__main__":
    main()
