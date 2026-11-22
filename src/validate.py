"""Automated integrity checks + coverage/quality reporting.

Checks never modify data: failures are reported (and raise in pytest).
Outputs:
  reports/validation_results.csv
  reports/coverage_by_competition_season.csv
  reports/formation_matchup_frequencies.csv
  reports/formation_frequencies.csv
  reports/data_quality_report.md
"""
from __future__ import annotations

import json
import re

import duckdb
import numpy as np
import pandas as pd

from . import config
from .build_datasets import formation_valid
from .parse_espn import interval_for

P = config.PROCESSED
VALID_SEASONS = {(s["competition"], s["season"]) for s in config.SEASONS}


def load():
    m = pd.read_csv(P / "match_level.csv", dtype={"season": str})
    g = pd.read_csv(P / "goal_events.csv", dtype={"season": str})
    p = pd.read_csv(P / "team_interval_panel.csv", dtype={"season": str}, low_memory=False)
    return m, g, p


def _res(name, bad, n, detail=""):
    return {"check": name, "passed": int(bad == 0), "n_violations": int(bad),
            "n_checked": int(n), "detail": detail}


def run_checks(m, g, p) -> pd.DataFrame:
    R = []
    prim = m[m.in_primary_sample == 1]
    gp = g[g.in_primary_sample == 1]

    R.append(_res("unique match_id", m.match_id.duplicated().sum(), len(m)))
    R.append(_res("unique goal_id", g.goal_id.duplicated().sum(), len(g)))
    R.append(_res("no duplicate fixtures (competition, season, home, away)",
                  int(m[m.competition == "Premier League"].duplicated(
                      ["season", "home_team", "away_team"]).sum()), len(m),
                  "World Cup pairings may legitimately repeat and are keyed by date"))
    full = [(c, s_) for (c, s_), n in config.EXPECTED_MATCHES.items() if n]
    bad_n = []
    for c, s_ in full:
        x = m[(m.competition == c) & (m.season == s_)]
        if len(x) != config.EXPECTED_MATCHES[(c, s_)]:
            bad_n.append(f"{c} {s_}: {len(x)}")
    R.append(_res("complete seasons have the expected number of distinct matches "
                  "(380 EPL; 64/64/104 WC)", len(bad_n), len(full), "; ".join(bad_n)))
    epl_full = m[(m.competition == "Premier League") & (m.season != "2026-27")]
    pairs_bad = (epl_full.groupby("season").apply(
        lambda x: x[["home_team", "away_team"]].drop_duplicates().shape[0] != 380)).sum()
    R.append(_res("each complete EPL season has 380 distinct home/away pairings",
                  int(pairs_bad), epl_full.season.nunique()))
    teams_ok = epl_full.groupby("season").apply(
        lambda x: pd.concat([x.home_team, x.away_team]).nunique() == 20 and
        (pd.concat([x.home_team, x.away_team]).value_counts() == 38).all())
    R.append(_res("each complete EPL season: 20 teams x 38 matches", int((~teams_ok).sum()),
                  len(teams_ok)))
    order_bad = 0
    for _, gg in g.groupby("match_id"):
        key = list(zip(gg.goal_period.map({"1H": 1, "2H": 2, "ET1": 3, "ET2": 4}),
                       gg.goal_minute, gg.stoppage_time_minute))
        order_bad += int(key != sorted(key) or list(gg.goal_seq) != list(range(1, len(gg) + 1)))
    R.append(_res("goal events in chronological order within each match", order_bad,
                  g.match_id.nunique()))
    def in_window(r):
        if r.competition == "Premier League":
            y = int(r.season[:4])          # 2019-20 ended 26 Jul 2020 (COVID)
            return f"{y}-07-01" <= r.match_date <= f"{y + 1}-08-31"
        return r.match_date[:4] == r.season
    R.append(_res("kickoff dates fall inside the season window",
                  int((~m.apply(in_window, axis=1)).sum()), len(m)))
    dup_ev = g.duplicated(["match_id", "espn_play_id"]).sum() + \
        g.duplicated(["match_id", "goal_period", "clock_display", "scoring_team",
                      "goal_type_raw", "home_score_after", "away_score_after"]).sum()
    R.append(_res("no duplicate goal events", dup_ev, len(g)))
    R.append(_res("unique panel_id", p.panel_id.duplicated().sum(), len(p)))

    forms = pd.concat([m.home_starting_formation, m.away_starting_formation]).dropna()
    R.append(_res("formation labels valid (d-d-.. summing to 10 outfielders)",
                  (~forms.map(formation_valid)).sum(), len(forms)))
    grp = pd.concat([m.home_formation_group, m.away_formation_group])
    other = sorted(set(pd.concat([m.home_starting_formation, m.away_starting_formation])
                       [grp.values == "other"]))
    R.append(_res("every valid formation label has an explicit group (info: 'other' labels)",
                  0, len(grp), f"{int((grp == 'other').sum())} team-matches in 'other': {other}"))
    R.append(_res("formation group present whenever formation valid",
                  int(((m.both_formations_available == 1) &
                       (m.home_formation_group.isna() | m.away_formation_group.isna())).sum()),
                  len(m)))
    bad_cs = (~pd.Series(list(zip(m.competition, m.season))).isin(VALID_SEASONS)).sum()
    R.append(_res("valid competition/season values", bad_cs, len(m)))
    R.append(_res("match dates within cut-off", (m.match_date > config.CUTOFF_DATE).sum(), len(m)))

    # timestamps
    lim = {"1H": (1, 45), "2H": (46, 90), "ET1": (91, 105), "ET2": (106, 120)}
    def ts_bad(r):
        lo, hi = lim.get(r.goal_period, (None, None))
        if lo is None:
            return True
        base, st = r.goal_minute, r.stoppage_time_minute
        if st > 0:
            return base != hi
        return not (lo <= base <= hi)
    tb = g.apply(ts_bad, axis=1)
    R.append(_res("goal minute consistent with period (stoppage only at 45/90/105/120)",
                  tb.sum(), len(g), "; ".join(g[tb].goal_id.head(10))))
    # stoppage-time parsing: notation re-derived from raw display
    def raw_to_notation(s):
        mm = re.match(r"^(\d+)'(?:\+(\d+)')?$", str(s))
        return None if not mm else (mm.group(1) + (f"+{mm.group(2)}" if mm.group(2) else ""))
    nb = (g.clock_display.map(raw_to_notation) != g.original_goal_time.astype(str)).sum()
    R.append(_res("stoppage-time notation preserved (e.g. 45+2, 90+4)", nb, len(g)))
    # team assignment
    ta = ((g.scoring_team != g.home_team) & (g.scoring_team != g.away_team)) | \
        (g.scoring_team == g.conceding_team) | g.scoring_team.isna()
    R.append(_res("goal assigned to exactly one participating team", ta.sum(), len(g)))
    og = g[g.own_goal_indicator == 1]
    R.append(_res("own goals credited to the opponent of the player's team (text check)",
                  (og.own_goal_text_check == 0).sum(), og.own_goal_text_check.notna().sum(),
                  f"{og.own_goal_text_check.isna().sum()} own goals without parseable text"))
    R.append(_res("penalty indicator <-> goal_type consistent",
                  ((g.penalty_indicator == 1) != (g.goal_type == "penalty")).sum()
                  - ((g.penalty_indicator == 1) & (g.own_goal_indicator == 1)).sum(), len(g)))
    R.append(_res("no shoot-out goals in goal_events",
                  (~g.goal_period.isin(["1H", "2H", "ET1", "ET2"])).sum(), len(g)))
    so = m[m.decided_by_shootout == 1]
    ev_tot = g.groupby("match_id").size()
    so_bad = (so.match_id.map(ev_tot).fillna(0) != so.total_goals_incl_extra_time).sum()
    R.append(_res("shoot-out matches: event goals == score excl. shoot-out", so_bad, len(so)))
    R.append(_res("regular-time scores exclude extra time and shoot-outs",
                  (m.total_goals > m.total_goals_incl_extra_time).sum(), len(m)))

    # final score reconstruction (primary sample)
    reg = gp[gp.in_regulation == 1]
    rh = reg[reg.scoring_side == "home"].groupby("match_id").size()
    ra = reg[reg.scoring_side == "away"].groupby("match_id").size()
    hh = reg[(reg.scoring_side == "home") & (reg.goal_period == "1H")].groupby("match_id").size()
    ha = reg[(reg.scoring_side == "away") & (reg.goal_period == "1H")].groupby("match_id").size()
    rec_bad = ((prim.match_id.map(rh).fillna(0) != prim.home_goals) |
               (prim.match_id.map(ra).fillna(0) != prim.away_goals)).sum()
    R.append(_res("regulation score reconstructed from goal events (primary sample)",
                  rec_bad, len(prim)))
    ht_bad = ((prim.match_id.map(hh).fillna(0) != prim.half_time_home_goals) |
              (prim.match_id.map(ha).fillna(0) != prim.half_time_away_goals)).sum()
    R.append(_res("half-time score reconstructed from goal events (primary sample)",
                  ht_bad, len(prim)))
    allrec = (m.goal_events_reconciled == 0).sum()
    R.append(_res("ALL matches: goal events reconcile with official score (info)",
                  allrec, len(m), "; ".join(m[m.goal_events_reconciled == 0].match_id.head(20))))
    lc = m[m.linescore_conflict == 1]
    R.append(_res("ESPN linescore conflicts resolved by an independent source (info)",
                  int((lc.goal_events_reconciled == 0).sum()), len(lc),
                  "; ".join(f"{r.match_id}: {r.score_source}" for r in lc.itertuples())))
    zero = (prim.total_goals == 0).sum()
    R.append(_res("0-0 matches retained (info: count)", 0, len(prim), f"{zero} goalless matches"))

    # independent source cross-checks
    fdm = m[m.fd_matched == 1]
    fd_bad = ((fdm.fd_FTHG != fdm.home_goals) | (fdm.fd_FTAG != fdm.away_goals)).sum()
    R.append(_res("EPL full-time score == football-data.co.uk", fd_bad, len(fdm),
                  "; ".join(fdm[(fdm.fd_FTHG != fdm.home_goals) |
                                (fdm.fd_FTAG != fdm.away_goals)].match_id.head(10))))
    fdh = fdm.dropna(subset=["fd_HTHG", "half_time_home_goals"])
    R.append(_res("EPL half-time score == football-data.co.uk",
                  ((fdh.fd_HTHG != fdh.half_time_home_goals) |
                   (fdh.fd_HTAG != fdh.half_time_away_goals)).sum(), len(fdh)))
    R.append(_res("football-data fixture date within 1 day of ESPN kickoff",
                  (fdm.fd_date_diff_days.abs() > 1).sum(), len(fdm)))
    sbm = m[m.sb_match_id.notna()]
    sb_bad = ((sbm.sb_home_goals_incl_et != sbm.home_goals_incl_extra_time) |
              (sbm.sb_away_goals_incl_et != sbm.away_goals_incl_extra_time)).sum()
    R.append(_res("WC 2018/22 goals (incl. ET) == StatsBomb", sb_bad, len(sbm)))

    # intervals
    rg = g[g.in_regulation == 1]
    recomputed = [interval_for(1 if pp == "1H" else 2, b, s) for pp, b, s in
                  zip(rg.goal_period, rg.goal_minute, rg.stoppage_time_minute)]
    R.append(_res("goal interval assignment (re-derived)",
                  (pd.Series(recomputed, index=rg.index) != rg.interval_number).sum(), len(rg)))
    R.append(_res("extra-time goals have no regulation interval",
                  g[g.in_regulation == 0].interval_number.notna().sum(),
                  (g.in_regulation == 0).sum()))
    st1 = rg[(rg.goal_period == "1H") & (rg.stoppage_time_minute > 0)]
    st2 = rg[(rg.goal_period == "2H") & (rg.stoppage_time_minute > 0)]
    R.append(_res("first-half stoppage goals in interval 3, second-half in 6",
                  (st1.interval_number != 3).sum() + (st2.interval_number != 6).sum(),
                  len(st1) + len(st2)))
    cnt = p.groupby("match_id").size()
    R.append(_res("12 panel rows per eligible match", (cnt != 12).sum(), len(cnt)))
    R.append(_res("panel covers exactly the primary-sample matches",
                  len(set(prim.match_id) ^ set(p.match_id)), len(prim)))
    per_team = p.groupby(["match_id", "team_id"]).interval_number.apply(
        lambda s: sorted(s) == [1, 2, 3, 4, 5, 6])
    R.append(_res("each team has intervals 1..6 once", (~per_team).sum(), len(per_team)))
    pg = p.groupby(["match_id", "home_indicator"]).goals_scored_in_interval.sum()
    exp_h = prim.set_index("match_id").home_goals
    exp_a = prim.set_index("match_id").away_goals
    bad_pg = sum(int(pg.get((mid, 1), -1) != exp_h[mid]) + int(pg.get((mid, 0), -1) != exp_a[mid])
                 for mid in prim.match_id)
    R.append(_res("panel goals sum to regulation score", bad_pg, 2 * len(prim)))
    R.append(_res("binary response == (count > 0)",
                  (p.scored_at_least_one_goal != (p.goals_scored_in_interval > 0).astype(int)).sum(),
                  len(p)))
    # mirror consistency: team's scored == opponent's conceded
    a = p.set_index(["match_id", "team_id", "interval_number"])
    b = p.set_index(["match_id", "opponent_id", "interval_number"])
    R.append(_res("panel mirror: scored(team) == conceded(opponent)",
                  (a.goals_scored_in_interval.sort_index().values !=
                   b.goals_conceded_in_interval.sort_index().values).sum(), len(p)))

    # leakage
    p_sorted = p.sort_values(["match_id", "team_id", "interval_number"])
    cum = p_sorted.groupby(["match_id", "team_id"]).goals_scored_in_interval.cumsum() - \
        p_sorted.goals_scored_in_interval
    cumc = p_sorted.groupby(["match_id", "team_id"]).goals_conceded_in_interval.cumsum() - \
        p_sorted.goals_conceded_in_interval
    R.append(_res("leakage: score diff at interval start uses only earlier intervals",
                  ((cum - cumc) != p_sorted.score_difference_at_interval_start).sum(), len(p)))
    tv = [c for c in p.columns if c.startswith("tv_") and c.endswith("_before_interval")]
    first = p[p.interval_number == 1]
    R.append(_res("leakage: time-varying counts are zero (or NaN if source incomplete) at kickoff",
                  int((first[tv].fillna(0) != 0).any(axis=1).sum()), len(first)))
    cf = [c for c in tv if any(k in c for k in ("shot_any", "shot_ot", "corner"))]
    inc = p.commentary_events_complete == 0
    R.append(_res("commentary-derived features NaN exactly when commentary incomplete",
                  int((p.loc[inc, cf].notna().any(axis=1)).sum() +
                      (p.loc[~inc, cf].isna().any(axis=1)).sum()), len(p),
                  f"{p.loc[inc, 'match_id'].nunique()} matches with incomplete commentary"))
    mono = p_sorted.groupby(["match_id", "team_id"])[tv].diff().lt(0).any(axis=1).sum()
    R.append(_res("leakage: time-varying counts non-decreasing", int(mono), len(p)))
    R.append(_res("leakage: no post-match columns in panel",
                  sum(c.startswith("post_") for c in p.columns), len(p.columns)))
    # pre-match rolling features recomputed independently in SQL
    # independent SQL re-implementation of the rolling rule: prior matches of
    # the same team in the same group, kickoff strictly earlier and within 365
    # days, most recent 10, mean of non-missing values.
    con = duckdb.connect()
    con.register("m", m)
    q = """
    WITH t AS (
      SELECT match_id, CAST(kickoff_utc AS TIMESTAMP) AS ts, home_team_id AS team,
             home_goals AS gf, post_home_possessionPct AS poss,
             CASE WHEN competition='Premier League' THEN 'EPL' ELSE 'WC'||season END AS grp,
             'home' AS side FROM m
      UNION ALL
      SELECT match_id, CAST(kickoff_utc AS TIMESTAMP), away_team_id, away_goals,
             post_away_possessionPct,
             CASE WHEN competition='Premier League' THEN 'EPL' ELSE 'WC'||season END,
             'away' FROM m),
    pairs AS (
      SELECT a.match_id, a.side, b.gf, b.poss,
             ROW_NUMBER() OVER (PARTITION BY a.match_id, a.side ORDER BY b.ts DESC, b.match_id DESC) AS rk
      FROM t a JOIN t b ON a.grp = b.grp AND a.team = b.team
                       AND b.ts < a.ts AND b.ts >= a.ts - INTERVAL 365 DAY)
    SELECT t.match_id, t.side, AVG(p.gf) AS sql_pre_gf, AVG(p.poss) AS sql_pre_poss,
           COUNT(p.gf) AS sql_n
    FROM t LEFT JOIN pairs p ON t.match_id = p.match_id AND t.side = p.side AND p.rk <= 10
    GROUP BY t.match_id, t.side"""
    s = con.execute(q).df()
    mm = m.set_index("match_id")
    for col, sqlc in (("gf", "sql_pre_gf"), ("possession", "sql_pre_poss")):
        pv = np.array([mm.at[i, f"pre_{sd}_{col}_last10"] for i, sd in zip(s.match_id, s.side)],
                      dtype=float)
        diff = ~np.isclose(s[sqlc].astype(float), pv, equal_nan=True)
        R.append(_res(f"leakage: pre-match rolling {col} == independent SQL (prior 10, <=365 days)",
                      int(diff.sum()), len(s)))
    pn = np.array([mm.at[i, f"pre_{sd}_n_prior_matches"] for i, sd in zip(s.match_id, s.side)])
    R.append(_res("leakage: rolling-window match counts == independent SQL",
                  int((pn != s.sql_n.values).sum()), len(s)))
    R.append(_res("leakage: a team's first match in group has no rolling history",
                  int(((m.pre_home_n_prior_matches == 0) & m.pre_home_gf_last10.notna()).sum() +
                      ((m.pre_away_n_prior_matches == 0) & m.pre_away_gf_last10.notna()).sum()),
                  2 * len(m)))
    sbp = p[p.season.isin(["2018", "2022"]) & (p.competition == "FIFA World Cup")]
    R.append(_res("WC18/22 panel rows have an active formation at interval start",
                  int(sbp.tv_active_formation_at_interval_start.isna().sum()), len(sbp)))
    return pd.DataFrame(R)


def coverage(m, g, idx) -> pd.DataFrame:
    rows = []
    for spec in config.SEASONS:
        c, s = spec["competition"], spec["season"]
        ev = [e for e in idx if e["competition"] == c and e["season"] == s]
        comp = [e for e in ev if e["in_scope"]]
        mm = m[(m.competition == c) & (m.season == s)]
        gg = g[(g.competition == c) & (g.season == s)]
        prim = mm[mm.in_primary_sample == 1]
        n = len(mm)
        rows.append({
            "competition": c, "season": s,
            "expected_matches": config.EXPECTED_MATCHES.get((c, s)),
            "matches_listed_by_source": len(ev),
            "completed_by_cutoff": len(comp),
            "matches_downloaded": sum(e.get("summary_downloaded", False) for e in comp),
            "matches_parsed": n,
            "both_starting_formations": int(mm.both_formations_available.sum()),
            "complete_goal_events": int(mm.goal_events_reconciled.sum()),
            "both_requirements (primary sample)": len(prim),
            "goals_total_all_periods": len(gg),
            "validated_regulation_goals_primary": int(prim.total_goals.sum()),
            "goals_per_match_primary": round(prim.total_goals.mean(), 3) if len(prim) else None,
            "pct_missing_formation": round(100 * (1 - mm.both_formations_available.mean()), 2) if n else None,
            "pct_goal_events_unreconciled": round(100 * (1 - mm.goal_events_reconciled.mean()), 2) if n else None,
            "pct_missing_boxscore": round(100 * mm.post_home_possessionPct.isna().mean(), 2) if n else None,
            "pct_missing_prematch_odds": round(100 * mm.pre_odds_p_home_win.isna().mean(), 2) if n else None,
            "pct_missing_prematch_elo": round(100 * mm.pre_elo_home.isna().mean(), 2) if n else None,
            "formation_agreement_apif_pct": round(100 * mm.formation_crosscheck_apif.mean(), 1)
            if mm.formation_crosscheck_apif.notna().any() else None,
            "formation_agreement_statsbomb_pct": round(100 * mm.formation_crosscheck_statsbomb.mean(), 1)
            if mm.formation_crosscheck_statsbomb.notna().any() else None,
            "goals_with_active_formation": int(gg.active_formation_at_goal.notna().sum()),
        })
    return pd.DataFrame(rows)


def formation_tables(m):
    prim = m[m.in_primary_sample == 1]
    team_forms = pd.concat([
        prim[["competition", "home_starting_formation"]].rename(columns={"home_starting_formation": "formation"}),
        prim[["competition", "away_starting_formation"]].rename(columns={"away_starting_formation": "formation"})])
    ff = team_forms.groupby(["formation", "competition"]).size().unstack(fill_value=0)
    ff["total"] = ff.sum(axis=1)
    ff = ff.sort_values("total", ascending=False)
    fm = prim.groupby(["formation_pair_unordered", "competition"]).size().unstack(fill_value=0)
    fm["total"] = fm.sum(axis=1)
    fm = fm.sort_values("total", ascending=False)
    return ff, fm


def write_reports():
    m, g, p = load()
    idx = json.loads((config.INTERIM / config.ESPN_INDEX).read_text())
    checks = run_checks(m, g, p)
    cov = coverage(m, g, idx)
    ff, fm = formation_tables(m)
    R = config.REPORTS
    checks.to_csv(R / "validation_results.csv", index=False)
    cov.to_csv(R / "coverage_by_competition_season.csv", index=False)
    ff.to_csv(R / "formation_frequencies.csv")
    fm.to_csv(R / "formation_matchup_frequencies.csv")
    return checks, cov, ff, fm, m, g, p
