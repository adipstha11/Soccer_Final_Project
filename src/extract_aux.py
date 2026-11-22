"""Auxiliary sources (all public, no credentials):

* football-data.co.uk EPL CSVs  - pre-match betting odds (team-strength proxy)
  and independent full-time / half-time scores for validation.
  https://www.football-data.co.uk/englandm.php  (free; please credit the site)
* martj42/international_results (CC0) - full international results history,
  used to compute pre-match national-team Elo ratings for World Cup matches.
  https://github.com/martj42/international_results
* eatpizzanot/soccer-dataset on Hugging Face (CC-BY-4.0; derived from
  API-Football) - independent formation labels for cross-validation only.
  https://huggingface.co/datasets/eatpizzanot/soccer-dataset
"""
from __future__ import annotations

import logging

from . import config
from .http_client import Client

log = logging.getLogger(__name__)

FD_URL = "https://www.football-data.co.uk/mmz4281/{code}/E0.csv"
INTL_URL = ("https://raw.githubusercontent.com/martj42/international_results/"
            "master/results.csv")
HF_URL = ("https://huggingface.co/datasets/eatpizzanot/soccer-dataset/"
          "resolve/main/{name}.parquet")


def run(client: Client, refresh_current: bool = False):
    paths = {}
    for spec in config.SEASONS:
        if "fd_code" in spec:
            p = config.RAW / "football_data_co_uk" / f"E0_{spec['fd_code']}.csv"
            # in-progress season: optionally take a NEW dated snapshot
            refresh = refresh_current and spec["season"] == "2026-27"
            paths[("fd", spec["season"])] = client.cached_file(
                FD_URL.format(code=spec["fd_code"]), p, refresh=refresh)
    paths["intl"] = client.cached_file(
        INTL_URL, config.RAW / "international_results" / "results.csv")
    for name in ("fixtures", "fixture_lineups", "teams", "leagues"):
        paths[("hf", name)] = client.cached_file(
            HF_URL.format(name=name), config.RAW / "hf_soccer_dataset" / f"{name}.parquet")
    return paths
