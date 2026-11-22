"""Build the three linked analysis datasets from parsed source tables.

  data/processed/match_level.csv         one row per completed match
  data/processed/goal_events.csv         one row per in-match goal (no shoot-outs)
  data/processed/team_interval_panel.csv one row per team x match x 15-min interval

Primary key links: match_id (all three); goal_id (goal events);
(match_id, team_id, interval_number) (panel).
"""
from __future__ import annotations

import json
import logging
import re

import numpy as np
import pandas as pd

from . import config, elo, parse_espn, team_names
from .extract_statsbomb import run as _sb_run  # noqa: F401  (documented dependency)

log = logging.getLogger(__name__)

PERIOD_LABEL = {1: "1H", 2: "2H", 3: "ET1", 4: "ET2"}
# digits separated by '-', optionally followed by ESPN's '-d' (diamond) suffix
# e.g. '3-4-3-d' (3-4-3 with a diamond midfield). The suffix is kept verbatim.
FORMATION_RE = r"^\d(?:-\d){1,4}(?:-d)?$"

# Group-stage end dates (UTC); later matches are knockout matches.
WC_GROUP_END = {"2018": "2018-06-28", "2022": "2022-12-02", "2026": "2026-06-28"}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _goal_type(raw: str, pen: int, og: int) -> str:
    if og:
        return "own_goal"
    if pen:
        return "penalty"
    r = raw.lower()
    if "header" in r:
        return "header"
    if "free-kick" in r or "free kick" in r:
        return "direct_free_kick"
    if "volley" in r:
        return "volley"
    return "other_shot"


def formation_valid(f) -> bool:
    if not isinstance(f, str) or not pd.Series([f]).str.match(FORMATION_RE).iloc[0]:
        return False
    return sum(int(x) for x in formation_digits(f).split("-")) == 10


def formation_digits(f: str) -> str:
    """Numeric part of a label: '3-4-3-d' -> '3-4-3'."""
    return re.sub(r"-d$", "", f)


# Explicit formation -> group map (original strings are always kept).
# Rationale: groups follow defensive structure and number of central strikers,
# the dimensions on which providers agree most; back-3 and back-5 labels are
# merged because the same shape is labelled 5-3-2 by one provider and 3-5-2 by
# another. Labels not listed map to "other" and are reported, never guessed.
FORMATION_GROUP = {
    "4-2-3-1": "4-2-3-1",
    **{f: "4-3-3 family" for f in ("4-3-3", "4-1-4-1", "4-5-1", "4-3-2-1", "4-1-2-3")},
    **{f: "4-4-2 family" for f in ("4-4-2", "4-4-1-1", "4-2-2-2", "4-1-3-2",
                                   "4-1-2-1-2", "4-3-1-2", "4-2-4")},
    **{f: "back-3/5, 1 or 3 forwards" for f in ("3-4-2-1", "3-4-3", "3-4-3-d", "5-4-1", "3-2-4-1",
                                                "3-5-1-1", "3-4-1-1-1", "5-2-3",
                                                "3-6-1", "5-2-2-1", "3-3-3-1", "3-1-4-1-1")},
    **{f: "back-3/5, 2 forwards" for f in ("3-5-2", "3-1-4-2", "3-4-1-2", "5-3-2",
                                           "5-2-1-2", "3-3-2-2", "3-1-3-1-2")},
}


def formation_group(f):
    if not formation_valid(f):
        return None
    return FORMATION_GROUP.get(f, "other")


def add_formation_groups(m: pd.DataFrame) -> pd.DataFrame:
    m = m.copy()
    for s_ in ("home", "away"):
        m[f"{s_}_formation_group"] = m[f"{s_}_starting_formation"].map(formation_group)
    ok = m.home_formation_group.notna() & m.away_formation_group.notna()
    m["formation_group_matchup"] = (m.home_formation_group + " vs " +
                                    m.away_formation_group).where(ok)
    m["formation_group_pair_unordered"] = [
        " | ".join(sorted([h, a])) if isinstance(h, str) and isinstance(a, str) else None
        for h, a in zip(m.home_formation_group, m.away_formation_group)]
    return m


# --------------------------------------------------------------------------
# goals
# --------------------------------------------------------------------------
def build_goals(m: pd.DataFrame, g: pd.DataFrame) -> pd.DataFrame:
    g = g.copy()
    g["_order"] = np.arange(len(g))
    g = g.sort_values(["match_id", "period", "goal_minute", "stoppage_time_minute",
                       "clock_seconds", "_order"], kind="stable")
    g["goal_seq"] = g.groupby("match_id").cumcount() + 1
    g["goal_id"] = g.match_id + "-G" + g.goal_seq.astype(str).str.zfill(2)
    mm = m.set_index("match_id")
    for c in ("competition", "season", "home_team", "away_team", "home_team_id",
              "away_team_id", "home_starting_formation", "away_starting_formation",
              "kickoff_utc"):
        g[c] = g.match_id.map(mm[c])
    home = g.scoring_side == "home"
    g["scoring_team"] = np.where(home, g.home_team, g.away_team)
    g["conceding_team"] = np.where(home, g.away_team, g.home_team)
    g["scoring_team_id"] = np.where(home, g.home_team_id, g.away_team_id)
    g["conceding_team_id"] = np.where(home, g.away_team_id, g.home_team_id)
    g["scoring_team_starting_formation"] = np.where(
        home, g.home_starting_formation, g.away_starting_formation)
    g["opponent_starting_formation"] = np.where(
        home, g.away_starting_formation, g.home_starting_formation)
    g.loc[g.scoring_side.isna(), ["scoring_team", "conceding_team",
                                  "scoring_team_starting_formation",
                                  "opponent_starting_formation"]] = None
    g["original_goal_time"] = [parse_espn.notation(b, s) for b, s in
                               zip(g.goal_minute, g.stoppage_time_minute)]
    g["goal_period"] = g.period.map(PERIOD_LABEL)
    g["in_regulation"] = g.period.isin([1, 2]).astype(int)
    g["is_stoppage_time"] = (g.stoppage_time_minute > 0).astype(int)
    g["interval_number"] = [parse_espn.interval_for(p, b, s) if p in (1, 2) else None
                            for p, b, s in zip(g.period, g.goal_minute,
                                               g.stoppage_time_minute)]
    g["interval_number"] = g.interval_number.astype("Int64")
    g["goal_type"] = [_goal_type(r, p, o) for r, p, o in
                      zip(g.goal_type_raw, g.penalty_indicator, g.own_goal_indicator)]
    # running score (all periods, chronological)
    g["home_score_after"] = (g.scoring_side == "home").astype(int).groupby(g.match_id).cumsum()
    g["away_score_after"] = (g.scoring_side == "away").astype(int).groupby(g.match_id).cumsum()
    # ESPN text running score check: "Goal! Home 1, Away 0." lists home first
    def _txt_ok(r):
        if pd.isna(r.text_score_a):
            return np.nan
        a = parse_espn._norm(str(r.text_score_a_team))
        h = parse_espn._norm(r.home_team)
        aw = parse_espn._norm(r.away_team)
        if a[:5] == h[:5] or a in h or h in a:
            return int(r.text_score_a == r.home_score_after and
                       r.text_score_b == r.away_score_after)
        if a[:5] == aw[:5] or a in aw or aw in a:
            return int(r.text_score_a == r.away_score_after and
                       r.text_score_b == r.home_score_after)
        return np.nan
    g["text_running_score_consistent"] = g.apply(_txt_ok, axis=1)
    # own goal: ESPN text "Own Goal by <player>, <player's team>." -> the
    # player's team must be the CONCEDING team (goal credited to the opponent)
    def _og_ok(r):
        if not r.own_goal_indicator:
            return np.nan
        mo = re.search(r"Own Goal by .+?,\s*(.+?)\.", r.text or "")
        if not mo:
            return np.nan
        t = parse_espn._norm(mo.group(1))
        c = parse_espn._norm(r.conceding_team or "")
        sc = parse_espn._norm(r.scoring_team or "")
        if t and (t in c or c in t or t[:5] == c[:5]):
            return 1
        if t and (t in sc or sc in t or t[:5] == sc[:5]):
            return 0
        return np.nan
    g["own_goal_text_check"] = g.apply(_og_ok, axis=1)
    g["match_date"] = g.kickoff_utc.str[:10]
    g["data_source"] = "ESPN site API (summary.keyEvents)"
    return g


# --------------------------------------------------------------------------
# goal-event cleaning: exact duplicates and contradictory own-goal credit
# --------------------------------------------------------------------------
def clean_goal_events(g: pd.DataFrame, m: pd.DataFrame):
    """Two documented, source-internal corrections (raw files untouched):

    1. Exact duplicate keyEvents: ESPN sometimes lists the same goal twice with
       identical period, clock, team, type AND text (the text carries the
       running score, so two genuine goals cannot share it). The later copy is
       dropped and counted in n_duplicate_goal_events_removed.
    2. Own goals whose ESPN team credit contradicts ESPN's own text ("Own Goal
       by <player>, <player's team>" where <player's team> is the credited
       team). The goal is re-credited to the opponent ONLY if that makes the
       goal events reproduce ESPN's final score; it is flagged in
       goal_attribution_corrected. Independent football-data.co.uk scores are
       checked afterwards by the validation suite.
    """
    g = g.copy()
    key = ["match_id", "period", "clock_display", "scoring_team_id", "goal_type_raw", "text"]
    dup = g.duplicated(key, keep="first")
    m = m.copy()
    m["n_duplicate_goal_events_removed"] = m.match_id.map(
        g[dup].groupby("match_id").size()).fillna(0).astype(int)
    g = g[~dup].copy()
    g["goal_attribution_corrected"] = 0
    mm = m.set_index("match_id")
    for i, r in g[g.own_goal_indicator == 1].iterrows():
        mo = re.search(r"Own Goal by .+?,\s*(.+?)\.", r.text or "")
        if not mo or r.scoring_side not in ("home", "away"):
            continue
        t = parse_espn._norm(mo.group(1))
        credited = parse_espn._norm(mm.at[r.match_id, f"{r.scoring_side}_team"])
        if not (t and (t in credited or credited in t)):
            continue  # text consistent with credit
        other = "away" if r.scoring_side == "home" else "home"
        trial = g.loc[g.match_id == r.match_id, "scoring_side"].copy()
        trial.loc[i] = other
        fin = (int((trial == "home").sum()) == mm.at[r.match_id, "home_score_final_espn"] and
               int((trial == "away").sum()) == mm.at[r.match_id, "away_score_final_espn"])
        if fin:
            g.at[i, "scoring_side"] = other
            g.at[i, "scoring_team_id"] = mm.at[r.match_id, f"{other}_team_id"]
            g.at[i, "goal_attribution_corrected"] = 1
            log.warning("own goal re-credited from ESPN text: %s %s", r.match_id, r.clock_display)
    m["n_goal_attribution_corrections"] = m.match_id.map(
        g[g.goal_attribution_corrected == 1].groupby("match_id").size()).fillna(0).astype(int)
    log.info("duplicate goal events removed: %d; own-goal credits corrected: %d",
             int(dup.sum()), int(g.goal_attribution_corrected.sum()))
    return g, m


# --------------------------------------------------------------------------
# reconciliation of goal events with official scores
# --------------------------------------------------------------------------
def reconcile(m: pd.DataFrame, goals: pd.DataFrame) -> pd.DataFrame:
    m = m.copy()
    def cnt(mask, side):
        x = goals[mask & (goals.scoring_side == side)].groupby("match_id").size()
        return m.match_id.map(x).fillna(0).astype(int)
    for side in ("home", "away"):
        m[f"{side}_ev_p1"] = cnt(goals.period == 1, side)
        m[f"{side}_ev_p2"] = cnt(goals.period == 2, side)
        m[f"{side}_ev_et"] = cnt(goals.period.isin([3, 4]), side)
    m["n_goals_unattributed"] = m.match_id.map(
        goals[goals.scoring_side.isna()].groupby("match_id").size()).fillna(0).astype(int)
    has_ls = m.n_linescores >= 2
    ok_p1 = (m.home_ev_p1 == m.home_ls_p1) & (m.away_ev_p1 == m.away_ls_p1)
    ok_p2 = (m.home_ev_p2 == m.home_ls_p2) & (m.away_ev_p2 == m.away_ls_p2)
    tot_h = m.home_ev_p1 + m.home_ev_p2 + m.home_ev_et
    tot_a = m.away_ev_p1 + m.away_ev_p2 + m.away_ev_et
    ok_final = (tot_h == m.home_score_final_espn) & (tot_a == m.away_score_final_espn)
    m["check_halves_match_linescores"] = np.where(has_ls, (ok_p1 & ok_p2).astype(int), np.nan)
    m["check_final_score_reconstructed"] = ok_final.astype(int)
    m["goal_events_reconciled"] = (ok_final & (~has_ls | (ok_p1 & ok_p2))
                                   & (m.n_goals_unattributed == 0)).astype(int)
    return m


# --------------------------------------------------------------------------
# football-data.co.uk (EPL odds + independent score check)
# --------------------------------------------------------------------------
def load_fd() -> pd.DataFrame:
    frames = []
    for spec in config.SEASONS:
        if "fd_code" not in spec:
            continue
        p = config.RAW / "football_data_co_uk" / f"E0_{spec['fd_code']}.csv"
        snaps = sorted(p.parent.glob(f"E0_{spec['fd_code']}*.csv"))  # newest snapshot
        x = pd.read_csv(snaps[-1], encoding="latin-1").copy()
        x = x.dropna(subset=["HomeTeam", "AwayTeam"])
        # Market-average pre-match odds: 'Avg*' (from 2019-20) or BetBrain
        # 'BbAv*' (up to 2018-19). Both are pre-kickoff averages across bookmakers.
        if "AvgH" in x:
            src = "Avg"
        else:
            x = x.rename(columns={"BbAvH": "AvgH", "BbAvD": "AvgD", "BbAvA": "AvgA",
                                  "BbAv>2.5": "Avg>2.5", "BbAv<2.5": "Avg<2.5"})
            src = "BbAv (BetBrain average)"
        x["fd_odds_columns"] = src
        x["season"] = spec["season"]
        x["fd_file"] = snaps[-1].name
        frames.append(x)
    fd = pd.concat(frames, ignore_index=True)
    fd["fd_date"] = pd.to_datetime(fd.Date, dayfirst=True)
    return fd


def merge_fd(m: pd.DataFrame) -> pd.DataFrame:
    fd = load_fd()
    epl = m.competition == "Premier League"
    m = m.copy()
    m["_fd_home"] = np.where(epl, m.home_team.map(lambda n: team_names.ESPN_TO_FD.get(n)), None)
    m["_fd_away"] = np.where(epl, m.away_team.map(lambda n: team_names.ESPN_TO_FD.get(n)), None)
    unm = m[epl & (m._fd_home.isna() | m._fd_away.isna())]
    if len(unm):
        raise KeyError(f"unmapped EPL teams: {set(unm.home_team) | set(unm.away_team)}")
    dup = fd.duplicated(["season", "HomeTeam", "AwayTeam"], keep=False)
    if dup.any():
        raise ValueError("ambiguous football-data fixtures (duplicate season/home/away)")
    cols = {"HomeTeam": "_fd_home", "AwayTeam": "_fd_away", "fd_date": "fd_date",
            "FTHG": "fd_FTHG", "FTAG": "fd_FTAG", "HTHG": "fd_HTHG", "HTAG": "fd_HTAG",
            "AvgH": "fd_AvgH", "AvgD": "fd_AvgD", "AvgA": "fd_AvgA",
            "Avg>2.5": "fd_Avg_over25", "Avg<2.5": "fd_Avg_under25", "fd_file": "fd_file",
            "fd_odds_columns": "fd_odds_columns"}
    f = fd[["season"] + list(cols)].rename(columns=cols)
    m = m.merge(f, on=["season", "_fd_home", "_fd_away"], how="left")
    m["fd_matched"] = m.fd_date.notna().astype(int)
    kick = pd.to_datetime(m.kickoff_utc.str[:10])
    m["fd_date_diff_days"] = (kick - m.fd_date).dt.days
    # date sanity: same fixture should be within 1 day (UTC vs UK local)
    bad = m.fd_matched.eq(1) & m.fd_date_diff_days.abs().gt(1)
    m.loc[bad, "fd_match_flag"] = "date_mismatch>1d"
    # implied probabilities (overround removed by normalisation)
    inv = 1 / m[["fd_AvgH", "fd_AvgD", "fd_AvgA"]]
    s = inv.sum(axis=1)
    m["pre_odds_p_home_win"] = inv.fd_AvgH / s
    m["pre_odds_p_draw"] = inv.fd_AvgD / s
    m["pre_odds_p_away_win"] = inv.fd_AvgA / s
    io, iu = 1 / m.fd_Avg_over25, 1 / m.fd_Avg_under25
    m["pre_odds_p_over25"] = io / (io + iu)
    return m.drop(columns=["_fd_home", "_fd_away"])


# --------------------------------------------------------------------------
# Elo for World Cup matches (exact fixture lookup -> no leakage)
# --------------------------------------------------------------------------
def merge_elo(m: pd.DataFrame) -> pd.DataFrame:
    r = pd.read_csv(config.RAW / "international_results" / "results.csv")
    hist = elo.compute(r)
    wc = hist[hist.tournament == "FIFA World Cup"]
    m = m.copy()
    m["neutral_site_intl"] = None
    m["home_is_host_country"] = np.nan
    m["away_is_host_country"] = np.nan
    m["pre_elo_home"] = np.nan
    m["pre_elo_away"] = np.nan
    m["elo_fixture_found"] = np.nan
    for i, row in m[m.competition == "FIFA World Cup"].iterrows():
        h, a = team_names.to_intl(row.home_team), team_names.to_intl(row.away_team)
        d = pd.Timestamp(row.kickoff_utc[:10])
        c = wc[(wc.date >= d - pd.Timedelta(days=1)) & (wc.date <= d + pd.Timedelta(days=1))
               & (((wc.home_team == h) & (wc.away_team == a)) |
                  ((wc.home_team == a) & (wc.away_team == h)))]
        if len(c) != 1:
            m.at[i, "elo_fixture_found"] = 0
            continue
        c = c.iloc[0]
        if c.home_team == h:
            m.at[i, "pre_elo_home"], m.at[i, "pre_elo_away"] = c.elo_pre_home, c.elo_pre_away
        else:
            m.at[i, "pre_elo_home"], m.at[i, "pre_elo_away"] = c.elo_pre_away, c.elo_pre_home
        m.at[i, "elo_fixture_found"] = 1
        # venue facts from the same fixture record (ESPN's neutralSite flag is
        # False for every World Cup match, so it is not used)
        m.at[i, "neutral_site_intl"] = str(c.neutral).upper() == "TRUE"
        m.at[i, "home_is_host_country"] = int(c.country == h)
        m.at[i, "away_is_host_country"] = int(c.country == a)
    m["pre_elo_diff_home_minus_away"] = m.pre_elo_home - m.pre_elo_away
    epl = m.competition == "Premier League"
    m["neutral_site"] = np.where(epl, 0, m.neutral_site_intl.map(
        lambda x: np.nan if pd.isna(x) else int(bool(x))))
    m["neutral_site_source"] = np.where(
        epl, "league fixture at home club's stadium",
        "martj42 international_results (neutral flag)")
    for sd in ("home", "away"):
        m[f"{sd}_is_host_country"] = np.where(epl, np.nan, m[f"{sd}_is_host_country"])
    return m.drop(columns=["neutral_site_intl"])


# --------------------------------------------------------------------------
# API-Football formations (Hugging Face mirror) - cross-validation only
# --------------------------------------------------------------------------
def merge_apif(m: pd.DataFrame) -> pd.DataFrame:
    hf = config.RAW / "hf_soccer_dataset"
    fx = pd.read_parquet(hf / "fixtures.parquet")
    ln = pd.read_parquet(hf / "fixture_lineups.parquet")
    tm = pd.read_parquet(hf / "teams.parquet")
    fx = fx[fx.league_id.isin([1, 78]) & fx.is_played].copy()
    fx["date"] = pd.to_datetime(fx.date_utc).dt.normalize()
    tname = tm.set_index("id").name
    tfd = tm.set_index("id").fd_name
    fx["home_name"] = fx.home_team_id.map(tname)
    fx["away_name"] = fx.away_team_id.map(tname)
    fx["home_fd"] = fx.home_team_id.map(tfd)
    fx["away_fd"] = fx.away_team_id.map(tfd)
    lf = ln.dropna(subset=["formation"]).drop_duplicates(["fixture_id", "team_id"])
    lf = lf.set_index(["fixture_id", "team_id"]).formation
    fx["apif_home_formation"] = [lf.get((f, t)) for f, t in zip(fx.id, fx.home_team_id)]
    fx["apif_away_formation"] = [lf.get((f, t)) for f, t in zip(fx.id, fx.away_team_id)]
    m = m.copy()
    m["apif_home_formation"] = None
    m["apif_away_formation"] = None
    m["apif_fixture_id"] = None
    for i, row in m.iterrows():
        d = pd.Timestamp(row.kickoff_utc[:10])
        near = fx[(fx.date - d).abs() <= pd.Timedelta(days=1)]
        if row.competition == "Premier League":
            h, a = team_names.ESPN_TO_FD[row.home_team], team_names.ESPN_TO_FD[row.away_team]
            c = near[(near.league_id == 1) & (near.home_fd == h) & (near.away_fd == a)]
        else:
            h = team_names.ESPN_TO_APIF_NATIONAL.get(row.home_team, row.home_team)
            a = team_names.ESPN_TO_APIF_NATIONAL.get(row.away_team, row.away_team)
            c = near[(near.league_id == 78) & (
                ((near.home_name == h) & (near.away_name == a)) |
                ((near.home_name == a) & (near.away_name == h)))]
        if len(c) != 1:
            continue  # unmatched or ambiguous -> left missing, never guessed
        c = c.iloc[0]
        swap = row.competition != "Premier League" and c.home_name != h
        m.at[i, "apif_fixture_id"] = int(c.api_football_id) if pd.notna(c.api_football_id) else None
        m.at[i, "apif_home_formation"] = c.apif_away_formation if swap else c.apif_home_formation
        m.at[i, "apif_away_formation"] = c.apif_home_formation if swap else c.apif_away_formation
    both = m.apif_home_formation.notna() & m.apif_away_formation.notna()
    agree = ((m.apif_home_formation == m.home_starting_formation) &
             (m.apif_away_formation == m.away_starting_formation))
    m["formation_crosscheck_apif"] = np.where(both, agree.astype(int), np.nan)
    return m


# --------------------------------------------------------------------------
# StatsBomb: active formations and goal cross-check (WC 2018 / 2022)
# --------------------------------------------------------------------------
def load_statsbomb():
    from .http_client import Client
    from . import extract_statsbomb
    return extract_statsbomb.run(Client(delay=0.2))  # served from raw cache


def merge_statsbomb(m: pd.DataFrame, goals: pd.DataFrame):
    sbm, shifts, sbg = load_statsbomb()
    sbm["date"] = pd.to_datetime(sbm.match_date)
    m = m.copy()
    m["sb_match_id"] = np.nan
    for i, row in m[m.season.isin(["2018", "2022"]) &
                    (m.competition == "FIFA World Cup")].iterrows():
        d = pd.Timestamp(row.kickoff_utc[:10])
        h, a = team_names.to_sb(row.home_team), team_names.to_sb(row.away_team)
        c = sbm[((sbm.date - d).abs() <= pd.Timedelta(days=1)) & (
            ((sbm.sb_home == h) & (sbm.sb_away == a)) |
            ((sbm.sb_home == a) & (sbm.sb_away == h)))]
        if len(c) == 1:
            m.at[i, "sb_match_id"] = c.sb_match_id.iloc[0]
    m["sb_match_id"] = m.sb_match_id.astype("Int64")

    start = shifts[shifts.type == "Starting XI"].set_index(["sb_match_id", "team"]).formation
    n_shift = shifts[shifts.type == "Tactical Shift"].groupby(["sb_match_id", "team"]).size()
    for side in ("home", "away"):
        key = list(zip(m.sb_match_id, m[f"{side}_team"].map(team_names.to_sb)))
        m[f"sb_{side}_starting_formation"] = [start.get(k) if pd.notna(k[0]) else None
                                              for k in key]
        m[f"post_{side}_n_tactical_shifts_sb"] = [
            (n_shift.get(k, 0) if pd.notna(k[0]) else np.nan) for k in key]
    has = m.sb_match_id.notna()
    agree = ((m.sb_home_starting_formation == m.home_starting_formation) &
             (m.sb_away_starting_formation == m.away_starting_formation))
    m["formation_crosscheck_statsbomb"] = np.where(has, agree.astype(int), np.nan)
    # goal counts cross-check (regulation + extra time)
    sbc = sbg.groupby(["sb_match_id", "team"]).size()
    for side in ("home", "away"):
        key = list(zip(m.sb_match_id, m[f"{side}_team"].map(team_names.to_sb)))
        m[f"sb_{side}_goals_incl_et"] = [sbc.get(k, 0) if pd.notna(k[0]) else np.nan
                                         for k in key]
    sbp = sbg.groupby(["sb_match_id", "team", "period"]).size()
    for side in ("home", "away"):
        key = list(zip(m.sb_match_id, m[f"{side}_team"].map(team_names.to_sb)))
        m[f"sb_{side}_goals_p1"] = [sbp.get((k[0], k[1], 1), 0) if pd.notna(k[0]) else np.nan
                                    for k in key]
        m[f"sb_{side}_goals_reg"] = [(sbp.get((k[0], k[1], 1), 0) + sbp.get((k[0], k[1], 2), 0))
                                     if pd.notna(k[0]) else np.nan for k in key]

    # ---- active formation at goal: pair ESPN goal with StatsBomb goal ----
    goals = goals.copy()
    goals["active_formation_at_goal"] = None
    goals["opponent_active_formation_at_goal"] = None
    goals["active_formation_source"] = None
    goals["sb_goal_minute"] = np.nan
    sbmid = m.set_index("match_id").sb_match_id
    for mid, gg in goals.groupby("match_id"):
        sid = sbmid.get(mid)
        if pd.isna(sid):
            continue
        sh = shifts[shifts.sb_match_id == sid].sort_values("index")
        used = set()
        for gi, r in gg.iterrows():
            if pd.isna(r.scoring_team):
                continue
            team = team_names.to_sb(r.scoring_team)
            opp = team_names.to_sb(r.conceding_team)
            target = r.goal_minute - 1 + r.stoppage_time_minute  # SB elapsed minute
            cands = sbg[(sbg.sb_match_id == sid) & (sbg.team == team) &
                        (sbg.period == r.period) & (~sbg.index.isin(used))]
            cands = cands[(cands.minute - target).abs() <= 2]
            if len(cands) == 0:
                continue
            c = cands.iloc[(cands.minute - target).abs().argsort().iloc[0]]
            used.add(c.name)
            def active(t):
                x = sh[(sh.team == t) & (sh["index"] < c["index"])]
                return x.formation.iloc[-1] if len(x) else None
            goals.at[gi, "active_formation_at_goal"] = active(team)
            goals.at[gi, "opponent_active_formation_at_goal"] = active(opp)
            goals.at[gi, "active_formation_source"] = "StatsBomb Open Data (Starting XI / Tactical Shift)"
            goals.at[gi, "sb_goal_minute"] = c.minute
    return m, goals, shifts


def sb_active_at(shifts, sid, team, period, minute):
    """Active StatsBomb formation at (period, minute:00): the Starting XI plus
    any Tactical Shift strictly before that instant."""
    x = shifts[(shifts.sb_match_id == sid) & (shifts.team == team) &
               ((shifts.type == "Starting XI") | (shifts.period < period) |
                ((shifts.period == period) & (shifts.minute < minute)))]
    x = x.sort_values("index")
    return x.formation.iloc[-1] if len(x) else None


# --------------------------------------------------------------------------
# commentary completeness (governs commentary-derived time-varying features)
# --------------------------------------------------------------------------
def commentary_completeness(m: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """A match's commentary is 'complete' if its shot count is within
    max(4 shots, 15%) of the ESPN box-score total (WC 2018 commentary is untyped
    text and differs by up to 4 attempts); when the box score is missing,
    at least 10 attempts and 50 commentary lines are required. Otherwise the
    commentary-derived interval features are set to NaN (never to 0)."""
    m = m.copy()
    sh = events[(events.source == "commentary_text") & events.event.str.startswith("shot")
                & events.period.between(1, 4)]  # exclude shoot-out kicks (period 5)
    n = m.match_id.map(sh.groupby("match_id").size()).fillna(0)
    box = m.post_home_totalShots + m.post_away_totalShots
    ok_box = (n - box).abs() <= np.maximum(4, 0.15 * box)
    ok_nobox = (n >= 10) & (m.n_commentary >= 50)
    m["commentary_shots_total"] = n.astype(int)
    m["commentary_events_complete"] = np.where(box.notna(), ok_box, ok_nobox).astype(int)
    ot = sh[sh.event.isin(["shot_on_target", "shot_goal"])]
    for side in ("home", "away"):
        a = m.match_id.map(sh[sh.side == side].groupby("match_id").size()).fillna(0)
        b = m.match_id.map(ot[ot.side == side].groupby("match_id").size()).fillna(0)
        ok = m.commentary_events_complete == 1
        m[f"post_{side}_shots_commentary"] = a.where(ok)
        m[f"post_{side}_sot_commentary"] = b.where(ok)
    return m


# --------------------------------------------------------------------------
# adjudication of ESPN linescore errors (documented 2-of-3 rule)
# --------------------------------------------------------------------------
def adjudicate(m: pd.DataFrame) -> pd.DataFrame:
    """When ESPN per-period linescores disagree with ESPN goal events, accept
    the goal events ONLY if (a) they reproduce ESPN's final score and (b) an
    independent source confirms the per-half split (football-data.co.uk HT/FT
    for EPL; StatsBomb period-level goals for WC 2018/22). Otherwise the match
    stays unreconciled and is excluded from the primary sample."""
    m = m.copy()
    m["linescore_conflict"] = (m.check_halves_match_linescores == 0).astype(int)
    cand = ((m.goal_events_reconciled == 0) & (m.check_final_score_reconstructed == 1)
            & (m.n_goals_unattributed == 0))
    fd_ok = ((m.fd_matched == 1) & (m.fd_HTHG == m.home_ev_p1) & (m.fd_HTAG == m.away_ev_p1)
             & (m.fd_FTHG == m.home_ev_p1 + m.home_ev_p2)
             & (m.fd_FTAG == m.away_ev_p1 + m.away_ev_p2))
    sb_ok = (m.sb_match_id.notna() & (m.sb_home_goals_p1 == m.home_ev_p1)
             & (m.sb_away_goals_p1 == m.away_ev_p1)
             & (m.sb_home_goals_reg == m.home_ev_p1 + m.home_ev_p2)
             & (m.sb_away_goals_reg == m.away_ev_p1 + m.away_ev_p2))
    fix = cand & (fd_ok | sb_ok)
    m["score_source"] = "ESPN linescores (agree with ESPN goal events)"
    m.loc[m.linescore_conflict == 1, "score_source"] = "UNRESOLVED linescore/goal-event conflict"
    for sd in ("home", "away"):
        m.loc[fix, f"{sd}_goals"] = m.loc[fix, f"{sd}_ev_p1"] + m.loc[fix, f"{sd}_ev_p2"]
        m.loc[fix, f"half_time_{sd}_goals"] = m.loc[fix, f"{sd}_ev_p1"]
    m.loc[fix, "total_goals"] = m.loc[fix, "home_goals"] + m.loc[fix, "away_goals"]
    m.loc[fix & fd_ok, "score_source"] = ("ESPN goal events; ESPN linescore error, "
                                          "split confirmed by football-data.co.uk")
    m.loc[fix & ~fd_ok & sb_ok, "score_source"] = ("ESPN goal events; ESPN linescore error, "
                                                   "split confirmed by StatsBomb")
    m.loc[fix, "goal_events_reconciled"] = 1
    log.info("linescore conflicts: %d, resolved by independent source: %d",
             int(m.linescore_conflict.sum()), int(fix.sum()))
    return m


# --------------------------------------------------------------------------
# pre-match rolling team form & style (strictly prior matches)
# --------------------------------------------------------------------------
ROLL_FEATS = ["gf", "ga", "points", "possession", "passes", "long_ball_share",
              "shots", "sot", "shots_comm", "sot_comm"]
LOOKBACK_DAYS = 365


def team_match_long(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for side, opp in (("home", "away"), ("away", "home")):
        x = pd.DataFrame({
            "match_id": m.match_id, "kickoff_utc": m.kickoff_utc,
            "competition": m.competition, "season": m.season,
            "team_id": m[f"{side}_team_id"],
            "gf": m[f"{side}_goals"], "ga": m[f"{opp}_goals"],
            "possession": m[f"post_{side}_possessionPct"],
            "passes": m[f"post_{side}_totalPasses"],
            "long_ball_share": m[f"post_{side}_totalLongBalls"] / m[f"post_{side}_totalPasses"],
            "shots": m[f"post_{side}_totalShots"],
            "sot": m[f"post_{side}_shotsOnTarget"],
            "shots_comm": m[f"post_{side}_shots_commentary"],
            "sot_comm": m[f"post_{side}_sot_commentary"],
            "side": side,
        })
        x["points"] = np.select([x.gf > x.ga, x.gf == x.ga], [3, 1], 0)
        rows.append(x)
    return pd.concat(rows, ignore_index=True)


def rolling_prematch(m: pd.DataFrame, window: int = 10,
                     lookback_days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    """Mean of each feature over the team's previous <= `window` matches.

    * EPL: previous EPL matches in the dataset, crossing season boundaries,
      but only matches played within `lookback_days` before kickoff. A newly
      promoted club therefore has NO history at its first EPL match (no
      Championship data are used or invented), and a club returning after
      relegation does not reuse matches from an earlier top-flight spell.
    * World Cup: previous matches in the SAME tournament only.
    The current and later matches never contribute (strictly earlier kickoffs).
    Missing source values (e.g. empty box scores) are skipped, so a feature
    mean can rest on fewer matches than pre_*_n_prior_matches.
    """
    t = team_match_long(m)
    t["ts"] = pd.to_datetime(t.kickoff_utc)
    t = t.sort_values(["ts", "match_id"], kind="stable").reset_index(drop=True)
    t["grp"] = np.where(t.competition == "Premier League", "EPL",
                        "WC" + t.season.astype(str))
    out = {f"pre_{f}_last{window}": np.full(len(t), np.nan) for f in ROLL_FEATS}
    n_prior = np.zeros(len(t), dtype=int)
    rest = np.full(len(t), np.nan)
    lb = pd.Timedelta(days=lookback_days)
    for _, idx in t.groupby(["grp", "team_id"], sort=False).groups.items():
        sub = t.loc[idx].sort_values(["ts", "match_id"])
        ts = sub.ts.values
        vals = {f: sub[f].values.astype(float) for f in ROLL_FEATS}
        for j, row_i in enumerate(sub.index):
            prior = np.arange(j)
            prior = prior[(ts[prior] < ts[j]) & (ts[prior] >= ts[j] - lb)][-window:]
            n_prior[row_i] = len(prior)
            if len(prior):
                rest[row_i] = (ts[j] - ts[prior[-1]]) / np.timedelta64(1, "D")
                for f in ROLL_FEATS:
                    v = vals[f][prior]
                    v = v[~np.isnan(v)]
                    if len(v):
                        out[f"pre_{f}_last{window}"][row_i] = v.mean()
    for k, v in out.items():
        t[k] = v
    t["pre_n_prior_matches"] = n_prior
    t["pre_rest_days"] = rest
    keep = ["match_id", "side", "pre_n_prior_matches", "pre_rest_days"] + list(out)
    w = t[keep].pivot(index="match_id", columns="side")
    w.columns = [f"{c.replace('pre_', 'pre_' + s + '_', 1)}" for c, s in w.columns]
    return m.merge(w.reset_index(), on="match_id", how="left")


# --------------------------------------------------------------------------
# main builders
# --------------------------------------------------------------------------
def build_match_level(m: pd.DataFrame) -> pd.DataFrame:
    m = m.copy()
    m["match_date"] = m.kickoff_utc.str[:10]
    has_ls = m.n_linescores >= 2
    went_et = m.status.isin(["STATUS_FINAL_AET", "STATUS_FINAL_PEN"])
    m["went_to_extra_time"] = went_et.astype(int)
    m["decided_by_shootout"] = (m.status == "STATUS_FINAL_PEN").astype(int)
    # regulation (90 + stoppage) goals: official ESPN per-period linescores
    for s in ("home", "away"):
        m[f"{s}_goals"] = np.where(has_ls, m[f"{s}_ls_p1"] + m[f"{s}_ls_p2"],
                                   np.where(went_et, np.nan, m[f"{s}_score_final_espn"]))
        m[f"half_time_{s}_goals"] = np.where(has_ls, m[f"{s}_ls_p1"], np.nan)
        m[f"{s}_goals_incl_extra_time"] = m[f"{s}_score_final_espn"]
        m[f"{s}_shootout_goals"] = np.where(m.decided_by_shootout == 1,
                                            m[f"{s}_shootout"], np.nan)
    m["total_goals"] = m.home_goals + m.away_goals
    m["total_goals_incl_extra_time"] = m.home_goals_incl_extra_time + m.away_goals_incl_extra_time
    m["formation_matchup"] = m.home_starting_formation + " vs " + m.away_starting_formation
    m["formation_pair_unordered"] = [
        " | ".join(sorted([h, a])) if isinstance(h, str) and isinstance(a, str) else None
        for h, a in zip(m.home_starting_formation, m.away_starting_formation)]
    m["both_formations_available"] = (m.home_starting_formation.map(formation_valid) &
                                      m.away_starting_formation.map(formation_valid)).astype(int)
    # coarse, provider-robust formation descriptors (derived from the label)
    for s in ("home", "away"):
        f = m[f"{s}_starting_formation"].where(m[f"{s}_starting_formation"].map(formation_valid))
        fd_ = f.str.replace(r"-d$", "", regex=True)
        m[f"{s}_back_line"] = fd_.str.split("-").str[0].astype(float)
        m[f"{s}_n_forwards"] = fd_.str.split("-").str[-1].astype(float)
    m["back_line_matchup"] = (m.home_back_line.astype("Int64").astype(str) + "B vs " +
                              m.away_back_line.astype("Int64").astype(str) + "B").where(
        m.home_back_line.notna() & m.away_back_line.notna())
    m = add_formation_groups(m)
    if "stage" not in m:
        m["stage"] = np.where(m.competition == "Premier League", "League",
                              np.where(m.match_date <= m.season.map(WC_GROUP_END).fillna(""),
                                       "Group", "Knockout"))
    # rename post-match box-score stats
    ren = {f"{s}_{k}": f"post_{s}_{k}" for s in ("home", "away") for k in parse_espn.BOX_STATS}
    ren.update({"h1_added_minutes_observed": "post_h1_added_minutes_observed",
                "h2_added_minutes_observed": "post_h2_added_minutes_observed"})
    m = m.rename(columns=ren)
    for s in ("home", "away"):
        m[f"post_{s}_long_ball_share"] = m[f"post_{s}_totalLongBalls"] / m[f"post_{s}_totalPasses"]
        m[f"post_{s}_pass_accuracy"] = m[f"post_{s}_accuratePasses"] / m[f"post_{s}_totalPasses"]
    m["data_source"] = "ESPN site API (summary)"
    return m


def build_panel(m: pd.DataFrame, goals: pd.DataFrame, events: pd.DataFrame,
                shifts: pd.DataFrame | None) -> pd.DataFrame:
    elig = m[m.in_primary_sample == 1]
    reg = goals[goals.in_regulation == 1]
    ev = events[events.period.isin([1, 2])].copy()
    ev["interval_number"] = [parse_espn.interval_for(p, b, s) for p, b, s in
                             zip(ev.period, ev.minute, ev.stoppage)]
    ev["shot_any"] = ev.event.str.startswith("shot").astype(int)
    ev["shot_ot"] = ev.event.isin(["shot_on_target", "shot_goal"]).astype(int)
    ev["corner"] = (ev.event == "corner").astype(int)
    ev["red"] = (ev.event == "red_card").astype(int)
    ev["sub"] = (ev.event == "substitution").astype(int)
    agg = ev.groupby(["match_id", "side", "interval_number"])[
        ["shot_any", "shot_ot", "corner", "red", "sub"]].sum()
    gagg = reg.groupby(["match_id", "scoring_side", "interval_number"]).size()

    starts = {1: (1, 0), 2: (1, 15), 3: (1, 30), 4: (2, 45), 5: (2, 60), 6: (2, 75)}
    rows = []
    for r in elig.itertuples(index=False):
        rd = r._asdict()
        for side, opp in (("home", "away"), ("away", "home")):
            cum = {"gs": 0, "gc": 0}
            cum_ev = {f"{w}_{k}": 0 for w in ("own", "opp")
                      for k in ("shot_any", "shot_ot", "corner", "red", "sub")}
            for (num, label, half, lo, hi) in config.INTERVALS:
                gs = int(gagg.get((r.match_id, side, num), 0))
                gc = int(gagg.get((r.match_id, opp, num), 0))
                row = {
                    "match_id": r.match_id, "competition": r.competition,
                    "season": r.season, "match_date": r.match_date, "stage": r.stage,
                    "team": rd[f"{side}_team"], "team_id": rd[f"{side}_team_id"],
                    "opponent": rd[f"{opp}_team"], "opponent_id": rd[f"{opp}_team_id"],
                    "home_indicator": int(side == "home"),
                    "neutral_site": r.neutral_site,
                    "team_is_host_country": rd[f"{side}_is_host_country"],
                    "interval_number": num, "interval_label": label,
                    "interval_start": starts[num][1],
                    "interval_end": {1: 15, 2: 30, 3: 45, 4: 60, 5: 75, 6: 90}[num],
                    "interval_includes_stoppage": int(num in (3, 6)),
                    "match_minute": starts[num][1],
                    "starting_formation": rd[f"{side}_starting_formation"],
                    "opponent_starting_formation": rd[f"{opp}_starting_formation"],
                    "formation_matchup": f"{rd[f'{side}_starting_formation']} vs "
                                         f"{rd[f'{opp}_starting_formation']}",
                    "starting_formation_group": rd[f"{side}_formation_group"],
                    "opponent_formation_group": rd[f"{opp}_formation_group"],
                    "formation_group_matchup": f"{rd[f'{side}_formation_group']} vs "
                                               f"{rd[f'{opp}_formation_group']}",
                    "back_line": rd[f"{side}_back_line"],
                    "opponent_back_line": rd[f"{opp}_back_line"],
                    "n_forwards": rd[f"{side}_n_forwards"],
                    "opponent_n_forwards": rd[f"{opp}_n_forwards"],
                    "goals_scored_in_interval": gs,
                    "goals_conceded_in_interval": gc,
                    "scored_at_least_one_goal": int(gs > 0),
                    "conceded_at_least_one_goal": int(gc > 0),
                    # ---- time-varying, known at interval start ----
                    "score_difference_at_interval_start": cum["gs"] - cum["gc"],
                    "goals_for_before_interval": cum["gs"],
                    "goals_against_before_interval": cum["gc"],
                }
                for k, v in cum_ev.items():
                    from_commentary = k.split("_", 1)[1] in ("shot_any", "shot_ot", "corner")
                    row[f"tv_{k}_before_interval"] = (
                        np.nan if from_commentary and not r.commentary_events_complete else v)
                row["commentary_events_complete"] = r.commentary_events_complete
                row["tv_man_advantage_at_interval_start"] = cum_ev["opp_red"] - cum_ev["own_red"]
                # exposure (POST-HOC: use only as offset, never as predictor)
                add = rd.get("post_h1_added_minutes_observed") if num == 3 else \
                    rd.get("post_h2_added_minutes_observed") if num == 6 else 0
                if num in (3, 6):
                    row["exposure_observed_minutes"] = (
                        15 + add if add is not None and not pd.isna(add) else np.nan)
                else:
                    row["exposure_observed_minutes"] = 15
                # pre-match (team perspective)
                row["pre_odds_p_team_win"] = rd.get(f"pre_odds_p_{side}_win")
                row["pre_odds_p_draw"] = rd.get("pre_odds_p_draw")
                row["pre_odds_p_opponent_win"] = rd.get(f"pre_odds_p_{opp}_win")
                row["pre_odds_p_over25"] = rd.get("pre_odds_p_over25")
                row["pre_elo_team"] = rd.get(f"pre_elo_{side}")
                row["pre_elo_opponent"] = rd.get(f"pre_elo_{opp}")
                for f in ROLL_FEATS:
                    row[f"pre_team_{f}_last10"] = rd.get(f"pre_{side}_{f}_last10")
                    row[f"pre_opp_{f}_last10"] = rd.get(f"pre_{opp}_{f}_last10")
                row["pre_team_n_prior_matches"] = rd.get(f"pre_{side}_n_prior_matches")
                row["pre_opp_n_prior_matches"] = rd.get(f"pre_{opp}_n_prior_matches")
                # StatsBomb active formation at interval start (WC18/22 only)
                sid = rd.get("sb_match_id")
                if shifts is not None and sid is not None and not pd.isna(sid):
                    p, mi = starts[num]
                    row["tv_active_formation_at_interval_start"] = sb_active_at(
                        shifts, sid, team_names.to_sb(rd[f"{side}_team"]), p, mi)
                    row["tv_opp_active_formation_at_interval_start"] = sb_active_at(
                        shifts, sid, team_names.to_sb(rd[f"{opp}_team"]), p, mi)
                else:
                    row["tv_active_formation_at_interval_start"] = None
                    row["tv_opp_active_formation_at_interval_start"] = None
                row["data_source"] = ("ESPN site API (keyEvents, commentary); "
                                      "pre-match: football-data.co.uk odds / computed Elo")
                rows.append(row)
                # update cumulative AFTER writing the row (no leakage)
                cum["gs"] += gs; cum["gc"] += gc
                for k in ("shot_any", "shot_ot", "corner", "red", "sub"):
                    for w, s_ in (("own", side), ("opp", opp)):
                        cum_ev[f"{w}_{k}"] += int(agg[k].get((r.match_id, s_, num), 0))
    p = pd.DataFrame(rows)
    p.insert(0, "panel_id", p.match_id + "-" + p.team_id.astype(str) + "-I" +
             p.interval_number.astype(str))
    return p


GOAL_COLS = ["goal_id", "match_id", "competition", "season", "match_date",
             "goal_seq", "scoring_team", "conceding_team", "scoring_team_id",
             "conceding_team_id", "scoring_side", "goal_minute",
             "stoppage_time_minute", "original_goal_time", "clock_display",
             "goal_period", "in_regulation", "is_stoppage_time", "interval_number",
             "goal_type", "goal_type_raw", "penalty_indicator", "own_goal_indicator",
             "home_team", "away_team", "home_starting_formation",
             "away_starting_formation", "scoring_team_starting_formation",
             "opponent_starting_formation", "active_formation_at_goal",
             "opponent_active_formation_at_goal", "active_formation_source",
             "home_score_after", "away_score_after", "text_running_score_consistent",
             "own_goal_text_check", "goal_attribution_corrected", "sb_goal_minute",
             "espn_play_id", "data_source"]


def run(index_name: str | None = None):
    index_name = index_name or config.ESPN_INDEX
    m, g, e, fails = parse_espn.run(index_name)
    g, m = clean_goal_events(g, m)
    m = reconcile(m, g)
    m = build_match_level(m)
    m = merge_fd(m)
    m = merge_elo(m)
    m = merge_apif(m)
    goals = build_goals(m, g)
    m, goals, shifts = merge_statsbomb(m, goals)
    m = adjudicate(m)
    m = commentary_completeness(m, e)
    m = rolling_prematch(m)
    m["in_primary_sample"] = ((m.both_formations_available == 1) &
                              (m.goal_events_reconciled == 1)).astype(int)
    goals["in_primary_sample"] = goals.match_id.map(m.set_index("match_id").in_primary_sample)
    panel = build_panel(m, goals, e, shifts)

    # save interim tables (parsed, unmodified source values)
    config.INTERIM.mkdir(exist_ok=True, parents=True)
    e.to_parquet(config.INTERIM / "espn_timed_events.parquet")
    fails.to_csv(config.INTERIM / "parse_failures.csv", index=False)
    shifts.to_csv(config.INTERIM / "statsbomb_formation_events.csv", index=False)

    match_cols = [
        "match_id", "espn_event_id", "competition", "season", "stage", "match_date",
        "kickoff_utc", "status", "home_team", "away_team", "home_team_id", "away_team_id",
        "home_starting_formation", "away_starting_formation", "formation_matchup",
        "formation_pair_unordered", "both_formations_available",
        "home_back_line", "away_back_line", "home_n_forwards", "away_n_forwards",
        "back_line_matchup", "home_formation_group", "away_formation_group",
        "formation_group_matchup", "formation_group_pair_unordered",
        "home_goals", "away_goals", "total_goals",
        "half_time_home_goals", "half_time_away_goals",
        "went_to_extra_time", "home_goals_incl_extra_time", "away_goals_incl_extra_time",
        "total_goals_incl_extra_time", "decided_by_shootout", "home_shootout_goals",
        "away_shootout_goals", "neutral_site", "neutral_site_source",
        "home_is_host_country", "away_is_host_country", "venue",
        # pre-match predictors
        "pre_odds_p_home_win", "pre_odds_p_draw", "pre_odds_p_away_win", "pre_odds_p_over25",
        "pre_elo_home", "pre_elo_away", "pre_elo_diff_home_minus_away",
    ] + sorted([c for c in m.columns if c.startswith("pre_home_") or c.startswith("pre_away_")]) + [
        # post-match descriptive
    ] + sorted([c for c in m.columns if c.startswith("post_")]) + [
        # validation / provenance
        "goal_events_reconciled", "score_source", "linescore_conflict",
        "check_halves_match_linescores",
        "check_final_score_reconstructed", "n_goals_unattributed",
        "n_duplicate_goal_events_removed", "n_goal_attribution_corrections",
        "fd_matched", "fd_odds_columns", "fd_date_diff_days", "fd_FTHG", "fd_FTAG", "fd_HTHG", "fd_HTAG",
        "elo_fixture_found", "apif_fixture_id", "apif_home_formation", "apif_away_formation",
        "formation_crosscheck_apif", "sb_match_id", "sb_home_starting_formation",
        "sb_away_starting_formation", "formation_crosscheck_statsbomb",
        "sb_home_goals_incl_et", "sb_away_goals_incl_et",
        "commentary_shots_total", "commentary_events_complete",
        "n_starters_home", "n_starters_away", "in_primary_sample", "data_source",
    ]
    m = m.sort_values(["competition", "season", "kickoff_utc", "match_id"])
    goals = goals.sort_values(["competition", "season", "match_date", "match_id", "goal_seq"])
    goals_out = goals[GOAL_COLS + ["in_primary_sample"]]
    m[match_cols].to_csv(config.PROCESSED / "match_level.csv", index=False)
    goals_out.to_csv(config.PROCESSED / "goal_events.csv", index=False)
    panel.to_csv(config.PROCESSED / "team_interval_panel.csv", index=False)
    # parquet copies for fast loading
    m[match_cols].to_parquet(config.PROCESSED / "match_level.parquet", index=False)
    goals_out.to_parquet(config.PROCESSED / "goal_events.parquet", index=False)
    panel.to_parquet(config.PROCESSED / "team_interval_panel.parquet", index=False)
    log.info("match_level %d rows | goal_events %d rows | panel %d rows",
             len(m), len(goals_out), len(panel))
    return m[match_cols], goals_out, panel, fails
