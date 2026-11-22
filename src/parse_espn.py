"""Parse cached ESPN summary JSON into tidy source-level tables.

Outputs (pandas DataFrames, source-faithful, no imputation):
  matches   - one row per match (header, formations, linescores, box-score stats)
  goals     - one row per in-match goal from keyEvents (shoot-out kicks excluded)
  events    - time-stamped non-goal events used for time-varying features
              (shots, shots on target, corners, red cards, substitutions)
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import pandas as pd

from . import config

log = logging.getLogger(__name__)
RAW = config.RAW / "espn"

CLOCK_RE = re.compile(r"^\s*(\d+)'(?:\s*\+\s*(\d+)'?)?\s*$")
SCORE_TEXT_RE = re.compile(r"(?:Goal!|Own Goal by .*?\.)\s+(.+?)\s+(\d+),\s+(.+?)\s+(\d+)\.")

BOX_STATS = ["possessionPct", "totalShots", "shotsOnTarget", "wonCorners",
             "foulsCommitted", "yellowCards", "redCards", "offsides", "saves",
             "accuratePasses", "totalPasses", "accurateCrosses", "totalCrosses",
             "totalLongBalls", "accurateLongBalls", "totalTackles",
             "interceptions", "effectiveClearance", "penaltyKickGoals",
             "penaltyKickShots"]


def parse_clock(display: str | None) -> tuple[int | None, int | None]:
    """"45'+2'" -> (45, 2); "23'" -> (23, 0); unparseable -> (None, None)."""
    if not display:
        return None, None
    m = CLOCK_RE.match(display)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2) or 0)


def notation(base: int | None, stoppage: int | None) -> str | None:
    if base is None:
        return None
    return f"{base}+{stoppage}" if stoppage else f"{base}"


def interval_for(period: int, base: int, stoppage: int) -> int | None:
    """Assign a displayed match minute to one of six regulation intervals.

    Displayed minute m covers elapsed time [m-1, m). Boundaries:
      I1: 1-15  I2: 16-30  I3: 31-45 and 45+x   (period 1)
      I4: 46-60 I5: 61-75  I6: 76-90 and 90+x   (period 2)
    Period (not the minute) decides the half, so first-half stoppage (45+x)
    always lands in I3 and second-half stoppage (90+x) in I6. Periods >= 3
    (extra time, shoot-out) return None (outside the primary analysis)."""
    if period == 1:
        if stoppage or base > 45:
            return 3
        return 1 if base <= 15 else 2 if base <= 30 else 3
    if period == 2:
        if stoppage or base > 90:
            return 6
        if base <= 60:
            return 4          # includes rare base<=45 second-half stamps
        return 5 if base <= 75 else 6
    return None


def _team_side(team_id, home_id, away_id):
    if team_id == home_id:
        return "home"
    if team_id == away_id:
        return "away"
    return None


def _num(x):
    try:
        return float(str(x).replace("%", ""))
    except (TypeError, ValueError):
        return None


def parse_summary(d: dict, meta: dict):
    comp = d["header"]["competitions"][0]
    cps = {c["homeAway"]: c for c in comp["competitors"]}
    home, away = cps["home"], cps["away"]
    hid, aid = home["team"]["id"], away["team"]["id"]
    eid = meta["espn_event_id"]
    match_id = f"ESPN-{eid}"

    rost = {r.get("homeAway"): r for r in d.get("rosters", [])}

    def form(side):
        f = (rost.get(side) or {}).get("formation")
        return f if f else None

    def ls(c, i):
        l = c.get("linescores") or []
        if i < len(l):
            return _num(l[i].get("displayValue", l[i].get("value")))
        return None

    status = comp["status"]["type"]["name"]
    row = {
        "match_id": match_id,
        "espn_event_id": eid,
        "competition": meta["competition"],
        "season": meta["season"],
        "espn_season_name": meta.get("espn_season_name"),
        "kickoff_utc": meta["date_utc"],
        "status": status,
        "home_team_id": hid, "away_team_id": aid,
        "home_team": home["team"]["displayName"],
        "away_team": away["team"]["displayName"],
        "home_starting_formation": form("home"),
        "away_starting_formation": form("away"),
        "home_score_final_espn": _num(home.get("score")),
        "away_score_final_espn": _num(away.get("score")),
        "home_ls_p1": ls(home, 0), "away_ls_p1": ls(away, 0),
        "home_ls_p2": ls(home, 1), "away_ls_p2": ls(away, 1),
        "home_ls_et1": ls(home, 2), "away_ls_et1": ls(away, 2),
        "home_ls_et2": ls(home, 3), "away_ls_et2": ls(away, 3),
        "home_shootout": _num(home.get("shootoutScore")),
        "away_shootout": _num(away.get("shootoutScore")),
        "n_linescores": len(home.get("linescores") or []),
        "neutral_site": comp.get("neutralSite"),
        "venue": (d.get("gameInfo", {}).get("venue") or {}).get("fullName"),
        "attendance": d.get("gameInfo", {}).get("attendance"),
        "n_starters_home": sum(1 for p in (rost.get("home") or {}).get("roster", [])
                               if p.get("starter")),
        "n_starters_away": sum(1 for p in (rost.get("away") or {}).get("roster", [])
                               if p.get("starter")),
        "n_keyevents": len(d.get("keyEvents", [])),
        "n_commentary": len(d.get("commentary", [])),
        "comp_note": "; ".join(n.get("headline", "") for n in comp.get("notes", []) if n),
    }
    # box score (post-match)
    for t in d.get("boxscore", {}).get("teams", []):
        side = _team_side(t["team"]["id"], hid, aid)
        if not side:
            continue
        stats = {s["name"]: s.get("displayValue") for s in t.get("statistics", [])}
        vals = {k: _num(stats.get(k)) for k in BOX_STATS}
        # ESPN sometimes returns an all-zero placeholder box score; that is
        # missing data, not a match with zero passes.
        empty = not vals.get("totalPasses") and not vals.get("possessionPct")
        row[f"{side}_boxscore_available"] = int(not empty)
        for k in BOX_STATS:
            row[f"{side}_{k}"] = None if empty else vals[k]

    # ---------------- goals (keyEvents) ----------------
    goals = []
    events = []
    for k in d.get("keyEvents", []):
        ttext = (k.get("type") or {}).get("text") or ""
        period = (k.get("period") or {}).get("number")
        disp = (k.get("clock") or {}).get("displayValue")
        base, stp = parse_clock(disp)
        team_id = (k.get("team") or {}).get("id")
        side = _team_side(team_id, hid, aid)
        if ttext == "Halftime" and period == 1 and base is not None:
            row["h1_end_clock"] = disp
            row["h1_added_minutes_observed"] = stp
        if ttext == "End Regular Time" and base is not None:
            row["h2_end_clock"] = disp
            row["h2_added_minutes_observed"] = stp
        if ttext in ("End Match", "Full Time") and period == 2 and base is not None \
                and "h2_end_clock" not in row:
            row["h2_end_clock"] = disp
            row["h2_added_minutes_observed"] = stp
        if k.get("scoringPlay"):
            if k.get("shootout") or (period is not None and period >= 5):
                continue  # shoot-out kicks are never goals
            is_og = ttext.lower().startswith("own goal") or bool(k.get("ownGoal"))
            is_pen = "penalty" in ttext.lower()
            txt = k.get("text") or ""
            m = SCORE_TEXT_RE.search(txt)
            goals.append({
                "match_id": match_id, "espn_play_id": k.get("id"),
                "period": period, "clock_display": disp,
                "clock_seconds": (k.get("clock") or {}).get("value"),
                "goal_minute": base, "stoppage_time_minute": stp,
                "scoring_team_id": team_id, "scoring_side": side,
                "goal_type_raw": ttext, "penalty_indicator": int(is_pen),
                "own_goal_indicator": int(is_og), "text": txt,
                "text_score_a_team": m.group(1) if m else None,
                "text_score_a": int(m.group(2)) if m else None,
                "text_score_b_team": m.group(3) if m else None,
                "text_score_b": int(m.group(4)) if m else None,
            })
        elif ttext in ("Red Card",) or "second yellow" in ttext.lower() \
                or ttext == "Substitution":
            events.append({"match_id": match_id, "period": period,
                           "minute": base, "stoppage": stp, "team_id": team_id,
                           "side": side,
                           "event": "red_card" if ttext != "Substitution" else "substitution",
                           "source": "keyEvents", "raw_type": ttext})

    # ---------------- commentary (shots / corners) ----------------
    period = 1
    seen_play_ids = set()
    names = {side: [c["team"].get(k) for k in ("displayName", "shortDisplayName",
                                                 "name", "location", "abbreviation")
                    if c["team"].get(k)]
             for side, c in (("home", home), ("away", away))}
    pending = []  # commentary events whose team name did not match directly
    for c in d.get("commentary", []):
        txt = c.get("text") or ""
        play = c.get("play") or {}
        if play.get("period", {}).get("number"):
            period = play["period"]["number"]
        elif re.match(r"^(Second Half begins|Second half begins)", txt):
            period = 2
        elif re.match(r"^First Half Extra Time begins", txt):
            period = 3
        elif re.match(r"^Second Half Extra Time begins", txt):
            period = 4
        elif re.match(r"^Penalty Shootout begins", txt):
            period = 5
        base, stp = parse_clock((c.get("time") or {}).get("displayValue"))
        ev = classify_commentary(txt)
        if not ev or base is None:
            continue
        pid = play.get("id")
        if pid and pid in seen_play_ids:
            continue
        seen_play_ids.add(pid)
        team_name = ev[1]
        side = None
        ptid = (play.get("team") or {}).get("id")
        if ptid:
            side = _team_side(ptid, hid, aid)
        if side is None and team_name:
            side = match_team_name(team_name, names)
        rec = {"match_id": match_id, "period": period, "minute": base,
               "stoppage": stp, "team_id": {"home": hid, "away": aid}.get(side),
               "side": side, "event": ev[0], "source": "commentary_text",
               "raw_type": (play.get("type") or {}).get("text"),
               "commentary_team_name": team_name, "attribution": "direct"}
        if side is None:
            pending.append(rec)
        events.append(rec)
    # Resolve name variants (e.g. "Korea Republic" vs "South Korea") ONLY when
    # unambiguous: exactly one unmatched name and exactly one side with no
    # directly-matched commentary events.
    if pending:
        unmatched = {r["commentary_team_name"] for r in pending}
        matched_sides = {r["side"] for r in events
                         if r.get("source") == "commentary_text" and r["side"]}
        free = {"home", "away"} - matched_sides
        if len(unmatched) == 1 and len(free) == 1:
            side = free.pop()
            for r in pending:
                r["side"] = side
                r["team_id"] = {"home": hid, "away": aid}[side]
                r["attribution"] = "name_variant_resolved"
    return row, goals, events


SHOT_PATTERNS = [
    (re.compile(r"^Attempt saved\.\s+.+?\((.+?)\)"), "shot_on_target"),
    (re.compile(r"^Attempt missed\.\s+.+?\((.+?)\)"), "shot_off_target"),
    (re.compile(r"^Attempt blocked\.\s+.+?\((.+?)\)"), "shot_blocked"),
    (re.compile(r"^.+?\((.+?)\)\s+hits the (?:left post|right post|bar|crossbar)"), "shot_woodwork"),
    (re.compile(r"^Goal!\s+.+?\.\s+.+?\((.+?)\)"), "shot_goal"),
    (re.compile(r"^Penalty saved!\s+.+?\((.+?)\)"), "shot_on_target"),
    (re.compile(r"^Penalty missed!\s+.+?\((.+?)\)"), "shot_off_target"),
    (re.compile(r"^Corner,\s+(.+?)\.\s+Conceded"), "corner"),
]


def classify_commentary(txt: str):
    """Classify an Opta-style commentary line. Returns (event, team_name) or None.
    Uses the text rather than ESPN's play types so the same rule applies to all
    seasons (WC 2018 commentary has no typed plays)."""
    for rx, ev in SHOT_PATTERNS:
        m = rx.match(txt)
        if m:
            return ev, m.group(1).strip()
    return None


def _norm(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", "and")
    return re.sub(r"[^a-z0-9]", "", s)


def match_team_name(name: str, names: dict) -> str | None:
    """Return the side whose name aliases match `name`; None if no match or
    if both sides match (ambiguous)."""
    n = _norm(name)
    hits = set()
    for side, aliases in names.items():
        for full in aliases:
            f = _norm(full)
            if len(f) >= 3 and (n == f or (len(n) >= 4 and (n in f or f in n))):
                hits.add(side)
    return hits.pop() if len(hits) == 1 else None


def run(index_name: str = "espn_event_index.json"):
    index = json.loads((config.INTERIM / index_name).read_text())
    rows, goals, events, failures = [], [], [], []
    for meta in index:
        if not meta.get("in_scope"):
            continue
        p = (config.RAW / meta.get("raw_dir", "espn") / meta["espn_league"] / "summary"
             / f"{meta['espn_event_id']}.json")
        if not p.exists():
            failures.append({"espn_event_id": meta["espn_event_id"], "reason": "summary missing"})
            continue
        try:
            r, g, e = parse_summary(json.loads(p.read_text()), meta)
        except Exception as exc:
            failures.append({"espn_event_id": meta["espn_event_id"], "reason": repr(exc)})
            continue
        rows.append(r); goals.extend(g); events.extend(e)
    out = (pd.DataFrame(rows), pd.DataFrame(goals), pd.DataFrame(events),
           pd.DataFrame(failures, columns=["espn_event_id", "reason"]))
    log.info("parsed %d matches, %d goals, %d events, %d failures",
             len(out[0]), len(out[1]), len(out[2]), len(out[3]))
    return out
