"""End-to-end pipeline.

  python -m src.run_pipeline --pilot 3      # 3 matches per competition-season
  python -m src.run_pipeline                # full extraction + build + validation
  python -m src.run_pipeline --skip-extract # rebuild from cached raw data only
"""
from __future__ import annotations

import argparse
import logging

from . import build_datasets, config, extract_aux, extract_espn, extract_statsbomb, validate
from .http_client import Client


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int, default=None)
    ap.add_argument("--skip-extract", action="store_true")
    ap.add_argument("--refresh-current-season", action="store_true",
                    help="take a new dated snapshot of the in-progress EPL odds CSV")
    ap.add_argument("--baseline-snapshot", default=None,
                    help="snapshot dir to compare baseline records against")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(config.LOGS / "pipeline.log"),
                                  logging.StreamHandler()])
    if not a.skip_extract:
        c = Client()
        extract_espn.run(c, pilot=a.pilot,
                         index_name=None if a.pilot else config.ESPN_INDEX)
        extract_statsbomb.run(c)
        extract_aux.run(c, refresh_current=a.refresh_current_season)
    index = "espn_event_index_pilot.json" if a.pilot else config.ESPN_INDEX
    build_datasets.run(index)
    if not a.pilot:
        checks, cov, *_ = validate.write_reports()
        from . import reports
        reports.write_all()
        if a.baseline_snapshot:
            from . import compare_baseline, expansion_report
            cmp = compare_baseline.compare(config.ROOT / a.baseline_snapshot, config.PROCESSED)
            cmp.to_csv(config.REPORTS / "baseline_preservation.csv", index=False)
            logging.info("baseline preservation: %s", cmp.status.value_counts().to_dict())
            expansion_report.write(a.baseline_snapshot)
        failed = checks[checks.passed == 0]
        logging.info("validation: %d checks, %d with violations", len(checks), len(failed))
        print(checks.to_string())
        print(cov.to_string())


if __name__ == "__main__":
    main()
