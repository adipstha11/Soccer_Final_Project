"""Extract ESPN public site-API scoreboards and match summaries.

Endpoints (unofficial, public, no key):
  {BASE}/{league}/scoreboard?dates=YYYYMMDD
  {BASE}/{league}/summary?event={id}
Raw JSON is cached under data/raw/espn/{league}/... and never overwritten.
"""
from __future__ import annotations

import datetime as dt
import json
import logging

from . import config
from .http_client import Client

log = logging.getLogger(__name__)
RAW = config.RAW / "espn"


def _all_final(d: dict) -> bool:
    evs = d.get("events", [])
    return all(e["status"]["type"]["completed"] or
               e["status"]["type"]["name"] in ("STATUS_POSTPONED", "STATUS_CANCELED",
                                               "STATUS_ABANDONED")
               for e in evs)


def scoreboard(client: Client, league: str, day: str, raw: str = "espn") -> dict:
    """day = YYYYMMDD. Cached only when every listed match is completed/cancelled
    and the day is before the cut-off (so in-progress days get re-fetched)."""
    path = config.RAW / raw / league / "scoreboard" / f"{day}.json"
    cutoff = config.CUTOFF_DATE.replace("-", "")
    return client.cached_json(
        f"{config.ESPN_BASE}/{league}/scoreboard", path, params={"dates": day},
        cache_if=lambda d: day < cutoff and _all_final(d))


def season_days(client: Client, spec: dict) -> list[str]:
    if "window" in spec:
        a, b = (dt.date.fromisoformat(x) for x in spec["window"])
        return [(a + dt.timedelta(days=i)).strftime("%Y%m%d")
                for i in range((b - a).days + 1)]
    seed = scoreboard(client, spec["espn"], spec["seed"], spec.get("raw", "espn"))
    cal = seed["leagues"][0]["calendar"]
    days = sorted({c[:10].replace("-", "") for c in cal if isinstance(c, str)})
    cutoff = config.CUTOFF_DATE.replace("-", "")
    return [d for d in days if d <= cutoff]


def list_events(client: Client, spec: dict) -> list[dict]:
    """Return one record per unique ESPN event in the season (any status)."""
    out: dict[str, dict] = {}
    for day in season_days(client, spec):
        d = scoreboard(client, spec["espn"], day, spec.get("raw", "espn"))
        season_name = d.get("leagues", [{}])[0].get("season", {}).get("displayName")
        for e in d.get("events", []):
            out.setdefault(e["id"], {
                "espn_event_id": e["id"],
                "competition": spec["competition"],
                "season": spec["season"],
                "espn_league": spec["espn"],
                "raw_dir": spec.get("raw", "espn"),
                "espn_season_name": season_name,
                "date_utc": e["date"],
                "status": e["status"]["type"]["name"],
                "completed": bool(e["status"]["type"]["completed"]),
                "name": e.get("name"),
            })
    log.info("%s %s: %d events listed", spec["competition"], spec["season"], len(out))
    return list(out.values())


def summary(client: Client, league: str, event_id: str, raw: str = "espn") -> dict:
    path = config.RAW / raw / league / "summary" / f"{event_id}.json"

    def final(d):
        try:
            return d["header"]["competitions"][0]["status"]["type"]["completed"]
        except Exception:
            return False
    return client.cached_json(f"{config.ESPN_BASE}/{league}/summary", path,
                              params={"event": event_id}, cache_if=final)


def run(client: Client, pilot: int | None = None, seasons: list[str] | None = None,
        index_name: str | None = None) -> list[dict]:
    """Extract all scoped seasons (or only `seasons`). Writes the event index."""
    index = []
    for spec in config.SEASONS:
        if seasons and spec["season"] not in seasons:
            continue
        events = list_events(client, spec)
        done = [e for e in events if e["status"] in config.COMPLETED_STATUSES
                and e["date_utc"][:10] <= config.CUTOFF_DATE]
        if pilot:
            done = done[:pilot]
        for i, e in enumerate(done):
            try:
                summary(client, spec["espn"], e["espn_event_id"], spec.get("raw", "espn"))
                e["summary_downloaded"] = True
            except Exception as exc:  # keep going; record failure
                log.warning("summary failed %s: %s", e["espn_event_id"], exc)
                e["summary_downloaded"] = False
            if i % 50 == 0:
                log.info("  %s %s summaries %d/%d", spec["competition"],
                         spec["season"], i, len(done))
        for e in events:
            e.setdefault("summary_downloaded", False)
            e["in_scope"] = e in done
        index.extend(events)
    name = index_name or ("espn_event_index_pilot.json" if pilot else "espn_event_index.json")
    (config.INTERIM / name).write_text(json.dumps(index, indent=1))
    return index
