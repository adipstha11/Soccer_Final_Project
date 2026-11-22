"""Compare a (staging) build with the baseline snapshot for the baseline records.

Rules
  * every baseline match_id / goal_id / panel_id must still exist;
  * for baseline records, every column that exists in both versions must be
    identical, EXCEPT rolling pre-match predictors (pre_*_last10,
    pre_*_n_prior_matches, pre_*_rest_days), which legitimately change because
    earlier EPL seasons now provide history; these are reported as
    EXPECTED_CHANGE with counts;
  * anything else that differs is FAIL.
Writes <REPORTS>/baseline_preservation.csv.
"""
from __future__ import annotations

import argparse
import re

import numpy as np
import pandas as pd

from . import config

ROLLING = re.compile(r"^pre_(home|away|team|opp)_.*(last10|n_prior_matches|rest_days)$")


def _same(a: pd.Series, b: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
        return pd.Series(np.isclose(a.astype(float), b.astype(float), equal_nan=True,
                                    rtol=1e-9, atol=1e-9), index=a.index)
    return (a.astype(str) == b.astype(str)) | (a.isna() & b.isna())


def compare(snapshot, new_dir):
    rows = []
    specs = [("match_level.csv", "match_id"), ("goal_events.csv", "goal_id"),
             ("team_interval_panel.csv", "panel_id")]
    for fname, key in specs:
        old = pd.read_csv(snapshot / "processed" / fname, dtype={"season": str}, low_memory=False)
        new = pd.read_csv(new_dir / fname, dtype={"season": str}, low_memory=False)
        missing = set(old[key]) - set(new[key])
        rows.append({"file": fname, "column": f"<{key} retained>", "n_baseline": len(old),
                     "n_changed": len(missing),
                     "status": "PASS" if not missing else "FAIL"})
        o = old.set_index(key)
        n = new.set_index(key).loc[o.index.intersection(new.set_index(key).index)]
        o = o.loc[n.index]
        for c in o.columns:
            if c not in n.columns:
                rows.append({"file": fname, "column": c, "n_baseline": len(o),
                             "n_changed": len(o), "status": "FAIL (column dropped)"})
                continue
            diff = int((~_same(o[c], n[c])).sum())
            if diff == 0:
                status = "PASS"
            elif ROLLING.match(c):
                status = "EXPECTED_CHANGE"
            else:
                status = "FAIL"
            rows.append({"file": fname, "column": c, "n_baseline": len(o),
                         "n_changed": diff, "status": status})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    a = ap.parse_args()
    df = compare(config.ROOT / a.snapshot, config.PROCESSED)
    df.to_csv(config.REPORTS / "baseline_preservation.csv", index=False)
    print(df[df.status != "PASS"].to_string())
    print(df.status.value_counts().to_string())


if __name__ == "__main__":
    main()
