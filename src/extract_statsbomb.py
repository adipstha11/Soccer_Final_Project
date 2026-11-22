"""StatsBomb Open Data (https://github.com/statsbomb/open-data) for FIFA World
Cup 2018 (competition 43 / season 3) and 2022 (43 / 106).

Used ONLY for (a) in-match formation changes ("Tactical Shift" events) so that
`active_formation_at_goal` can be populated, and (b) independent cross-checks of
starting formations and goals. Raw event files are stored gzip-compressed
(lossless) under data/raw/statsbomb/ and never modified.

Licence: StatsBomb Public Data User Agreement - free for research with
attribution ("Data provided by StatsBomb").
"""
from __future__ import annotations

import logging

import pandas as pd

from . import config
from .http_client import Client

log = logging.getLogger(__name__)
BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
RAW = config.RAW / "statsbomb"


def fmt_formation(x) -> str | None:
    """StatsBomb stores formations as integers, e.g. 4231 -> '4-2-3-1'."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    return "-".join(str(int(x)))


def run(client: Client):
    matches, shifts, goals = [], [], []
    for spec in config.SEASONS:
        if "sb" not in spec:
            continue
        cid, sid = spec["sb"]
        ms = client.cached_json(f"{BASE}/matches/{cid}/{sid}.json",
                                RAW / "matches" / f"{cid}_{sid}.json")
        for m in ms:
            mid = m["match_id"]
            ev = client.cached_json(f"{BASE}/events/{mid}.json",
                                    RAW / "events" / f"{mid}.json.gz", gz=True)
            home = m["home_team"]["home_team_name"]
            away = m["away_team"]["away_team_name"]
            matches.append({"sb_match_id": mid, "season": spec["season"],
                            "match_date": m["match_date"], "sb_home": home,
                            "sb_away": away, "sb_home_score": m["home_score"],
                            "sb_away_score": m["away_score"]})
            for e in ev:
                t = e["type"]["name"]
                team = e.get("team", {}).get("name")
                if t in ("Starting XI", "Tactical Shift"):
                    shifts.append({"sb_match_id": mid, "team": team, "type": t,
                                   "period": e["period"], "minute": e["minute"],
                                   "second": e["second"], "index": e["index"],
                                   "formation": fmt_formation(
                                       e.get("tactics", {}).get("formation"))})
                is_goal = (t == "Shot" and e.get("shot", {}).get("outcome", {})
                           .get("name") == "Goal")
                if (is_goal or t == "Own Goal For") and e["period"] <= 4:
                    goals.append({"sb_match_id": mid, "team": team,
                                  "period": e["period"], "minute": e["minute"],
                                  "second": e["second"], "index": e["index"],
                                  "own_goal": int(t == "Own Goal For"),
                                  "penalty": int(e.get("shot", {}).get("type", {})
                                                 .get("name") == "Penalty")})
        log.info("StatsBomb WC %s: %d matches", spec["season"], len(ms))
    return pd.DataFrame(matches), pd.DataFrame(shifts), pd.DataFrame(goals)
