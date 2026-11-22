"""Promote a validated staging build to the published locations.

  python -m src.promote --staging data/staging_v2 --reports-staging reports_staging_v2 \
      --index espn_event_index_v2.json --snapshot snapshots/baseline_v1_20261122

Steps (aborts on any failure, nothing is overwritten before all pass):
  1. staging validation_results.csv must show 0 failed checks;
  2. pytest must pass against the staging outputs (PROCESSED_DIR/REPORTS_DIR);
  3. baseline-preservation report must show no changes to source-derived
     values of baseline records (see compare_baseline.py);
  4. the snapshot directory with the previous version must exist;
then files are copied into data/processed and reports/, and the staging
event index becomes data/interim/espn_event_index.json.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

from . import config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--staging", required=True)
    ap.add_argument("--reports-staging", required=True)
    ap.add_argument("--index", required=True)
    ap.add_argument("--snapshot", required=True)
    a = ap.parse_args()
    root = config.ROOT
    st, rst, snap = root / a.staging, root / a.reports_staging, root / a.snapshot
    if not (snap / "SHA256SUMS").exists():
        sys.exit(f"snapshot {snap} missing - refusing to promote")
    v = pd.read_csv(rst / "validation_results.csv")
    if (v.passed == 0).any():
        sys.exit("staging validation has failures:\n" + v[v.passed == 0].to_string())
    cmp = pd.read_csv(rst / "baseline_preservation.csv")
    if (cmp.status == "FAIL").any():
        sys.exit("baseline preservation failed:\n" + cmp[cmp.status == "FAIL"].to_string())
    env = dict(os.environ, PROCESSED_DIR=str(st), REPORTS_DIR=str(rst), ESPN_INDEX=a.index)
    r = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=root, env=env)
    if r.returncode != 0:
        sys.exit("pytest failed against staging - refusing to promote")
    for f in st.iterdir():
        shutil.copy2(f, root / "data" / "processed" / f.name)
    for f in rst.iterdir():
        shutil.copy2(f, root / "reports" / f.name)
    shutil.copy2(config.INTERIM / a.index, config.INTERIM / "espn_event_index.json")
    print("promoted", st, "->", root / "data" / "processed")


if __name__ == "__main__":
    main()
