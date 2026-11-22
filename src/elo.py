"""Pre-match national-team Elo computed from the CC0 martj42 results file using
the World Football Elo method (eloratings.net):

  R_new = R_old + K * G * (W - We)
  We = 1 / (10^(-dr/400) + 1), dr includes +100 for a non-neutral home side
  G = 1 (|gd|<=1), 1.5 (|gd|=2), (11+|gd|)/8 (|gd|>=3)
  K = 60 World Cup finals, 50 continental finals, 40 qualifiers / Nations
      League / major tournaments, 30 other tournaments, 20 friendlies.

All teams start at 1500 in 1872; ~150 years of burn-in make the seed
irrelevant for 2018-2026. Ratings are taken *before* any match on the target
date (no same-day information), so they are valid pre-match predictors. This is
a DERIVED variable computed by this pipeline, not a published rating.
"""
from __future__ import annotations

from collections import defaultdict

import pandas as pd

CONTINENTAL = ("UEFA Euro", "Copa América", "African Cup of Nations",
               "AFC Asian Cup", "Gold Cup", "CONCACAF Championship",
               "Oceania Nations Cup", "Confederations Cup")


def k_factor(t: str) -> int:
    if t == "FIFA World Cup":
        return 60
    if "qualification" in t.lower():
        return 40
    if any(t.startswith(c) for c in CONTINENTAL):
        return 50
    if "Nations League" in t:
        return 40
    if t == "Friendly":
        return 20
    return 30


def g_mult(gd: int) -> float:
    gd = abs(gd)
    return 1.0 if gd <= 1 else 1.5 if gd == 2 else (11 + gd) / 8


def compute(results: pd.DataFrame) -> pd.DataFrame:
    """Return one row per historical match with pre-match ratings."""
    r = results.dropna(subset=["home_score", "away_score"]).copy()
    r["date"] = pd.to_datetime(r["date"])
    r = r.sort_values("date", kind="stable").reset_index(drop=True)
    rating = defaultdict(lambda: 1500.0)
    pre_h, pre_a = [], []
    # process day by day so all same-day matches use start-of-day ratings
    for _, day in r.groupby("date", sort=True):
        upd = defaultdict(float)
        for i, m in day.iterrows():
            h, a = m.home_team, m.away_team
            rh, ra = rating[h], rating[a]
            pre_h.append((i, rh)); pre_a.append((i, ra))
            neutral = str(m.neutral).upper() == "TRUE"
            dr = rh - ra + (0 if neutral else 100)
            we = 1 / (10 ** (-dr / 400) + 1)
            gd = int(m.home_score) - int(m.away_score)
            w = 1.0 if gd > 0 else 0.5 if gd == 0 else 0.0
            delta = k_factor(m.tournament) * g_mult(gd) * (w - we)
            upd[h] += delta; upd[a] -= delta
        for t, dlt in upd.items():
            rating[t] += dlt
    r["elo_pre_home"] = pd.Series(dict(pre_h))
    r["elo_pre_away"] = pd.Series(dict(pre_a))
    return r


def rating_before(elo_hist: pd.DataFrame, team: str, date) -> float | None:
    """Rating of `team` at the start of `date` (from its last match before)."""
    date = pd.Timestamp(date)
    h = elo_hist[(elo_hist.home_team == team) & (elo_hist.date >= date)]
    a = elo_hist[(elo_hist.away_team == team) & (elo_hist.date >= date)]
    # first match on/after date gives the pre-match (start-of-day) rating
    cands = []
    if len(h):
        cands.append((h.date.iloc[0], h.elo_pre_home.iloc[0]))
    if len(a):
        cands.append((a.date.iloc[0], a.elo_pre_away.iloc[0]))
    if not cands:
        return None
    return float(min(cands, key=lambda x: x[0])[1])
