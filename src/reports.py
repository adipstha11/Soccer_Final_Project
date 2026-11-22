"""Generate reports/: data_dictionary.md, data_quality_report.md,
feasibility_assessment.md and data/processed/source_audit.csv.
Numbers are computed from the processed data at generation time."""
from __future__ import annotations

import datetime as dt
import re

import numpy as np
import pandas as pd

from . import config, validate

R, P = config.REPORTS, config.PROCESSED

# --------------------------------------------------------------------------
# variable roles
# --------------------------------------------------------------------------
ROLE_HELP = {
    "ID": "identifier / join key - never a predictor",
    "RESPONSE": "outcome variable",
    "PRE": "pre-match predictor: known before kickoff, valid in every model",
    "TV": "time-varying predictor: known at the START of the interval (panel only)",
    "STRUCT": "structural design variable fixed at kickoff (formation, home, stage, interval)",
    "EXPOSURE": "post-hoc exposure (minutes played in interval) - offset only, NEVER a predictor",
    "POST": "post-match descriptive statistic - NEVER a predictor of goals in the same match",
    "QA": "validation / cross-source check field",
    "PROV": "provenance / metadata",
}

EXACT = {
    # ids
    "match_id": ("ID", "Pipeline match key = 'ESPN-' + ESPN event id. Links all three tables."),
    "espn_event_id": ("ID", "Native ESPN event id."),
    "goal_id": ("ID", "match_id + '-G' + chronological goal number within match."),
    "panel_id": ("ID", "match_id-team_id-I<interval_number>."),
    "goal_seq": ("ID", "Chronological goal order within match (1 = first goal)."),
    "espn_play_id": ("ID", "Native ESPN play id of the goal."),
    "home_team_id": ("ID", "ESPN team id (home)."), "away_team_id": ("ID", "ESPN team id (away)."),
    "team_id": ("ID", "ESPN team id of the panel team."), "opponent_id": ("ID", "ESPN team id of opponent."),
    "scoring_team_id": ("ID", "ESPN team id credited with the goal."),
    "conceding_team_id": ("ID", "ESPN team id that conceded."),
    "sb_match_id": ("ID", "StatsBomb match id (WC 2018/2022 only)."),
    "apif_fixture_id": ("ID", "API-Football fixture id via the Hugging Face mirror (cross-check only)."),
    # descriptors / structure
    "competition": ("STRUCT", "'Premier League' or 'FIFA World Cup'."),
    "season": ("STRUCT", "EPL '2023-24'...'2026-27'; World Cup '2018','2022','2026'. Read as string."),
    "stage": ("STRUCT", "'League' (EPL), 'Group' or 'Knockout' (WC; derived from group-stage end date)."),
    "match_date": ("STRUCT", "Kickoff date in UTC (YYYY-MM-DD)."),
    "kickoff_utc": ("STRUCT", "Kickoff timestamp, UTC, from ESPN."),
    "status": ("PROV", "ESPN final status: FULL_TIME, FINAL_AET (extra time), FINAL_PEN (shoot-out)."),
    "home_team": ("STRUCT", "Home (or first-listed, for neutral WC venues) team, ESPN display name."),
    "away_team": ("STRUCT", "Away team, ESPN display name."),
    "team": ("STRUCT", "Panel team."), "opponent": ("STRUCT", "Panel opponent."),
    "home_starting_formation": ("STRUCT", "Home starting formation as published by ESPN (Opta-style label). Starting shape only."),
    "away_starting_formation": ("STRUCT", "Away starting formation (ESPN)."),
    "starting_formation": ("STRUCT", "Panel team's starting formation (ESPN)."),
    "opponent_starting_formation": ("STRUCT", "Opponent's starting formation (ESPN)."),
    "formation_matchup": ("STRUCT", "Ordered matchup string. match_level: 'home vs away'; panel: 'team vs opponent'."),
    "formation_pair_unordered": ("STRUCT", "Alphabetically ordered pair 'A | B' (symmetric matchup, for total-goals models)."),
    "both_formations_available": ("QA", "1 if both labels exist and are valid."),
    "home_back_line": ("STRUCT", "Number of defenders in home formation (first digit). Provider-robust coarse descriptor."),
    "away_back_line": ("STRUCT", "Number of defenders in away formation."),
    "home_n_forwards": ("STRUCT", "Number of forwards (last digit) in home formation."),
    "away_n_forwards": ("STRUCT", "Number of forwards in away formation."),
    "back_line_matchup": ("STRUCT", "e.g. '4B vs 3B' (home vs away back lines)."),
    "home_formation_group": ("STRUCT", "Home formation group (explicit map in build_datasets.FORMATION_GROUP; 'other' = unmapped label). Original string kept in home_starting_formation."),
    "away_formation_group": ("STRUCT", "Away formation group."),
    "formation_group_matchup": ("STRUCT", "Ordered group matchup (match_level: home vs away; panel: team vs opponent)."),
    "formation_group_pair_unordered": ("STRUCT", "Unordered group pair 'A | B'."),
    "starting_formation_group": ("STRUCT", "Panel team's formation group."),
    "opponent_formation_group": ("STRUCT", "Opponent's formation group."),
    "fd_odds_columns": ("PROV", "football-data.co.uk odds columns used: 'Avg' (market average, 2019-20+) or 'BbAv' (BetBrain average, to 2018-19)."),
    "back_line": ("STRUCT", "Panel team's back-line count."), "opponent_back_line": ("STRUCT", "Opponent back-line count."),
    "n_forwards": ("STRUCT", "Panel team's forward count."), "opponent_n_forwards": ("STRUCT", "Opponent forward count."),
    "home_indicator": ("STRUCT", "1 = panel team is ESPN 'home' side. At World Cups this is administrative; use with neutral_site/team_is_host_country."),
    "neutral_site": ("STRUCT", "1 = neutral venue. EPL: 0. WC: from martj42 fixture record (ESPN's flag is unreliable for WCs)."),
    "neutral_site_source": ("PROV", "Source of neutral_site."),
    "home_is_host_country": ("STRUCT", "WC only: home side is the host nation of the venue."),
    "away_is_host_country": ("STRUCT", "WC only: away side is the host nation of the venue."),
    "team_is_host_country": ("STRUCT", "WC only: panel team is playing in its own country."),
    "venue": ("PROV", "Stadium name (ESPN)."),
    # responses
    "home_goals": ("RESPONSE", "Home goals in regulation (90 min + stoppage). Excludes extra time and shoot-outs."),
    "away_goals": ("RESPONSE", "Away goals in regulation."),
    "total_goals": ("RESPONSE", "home_goals + away_goals (regulation)."),
    "half_time_home_goals": ("RESPONSE", "Home goals at half-time (first half incl. stoppage). Not a predictor for the full-match total."),
    "half_time_away_goals": ("RESPONSE", "Away goals at half-time."),
    "went_to_extra_time": ("POST", "1 if the match went to extra time (WC knockouts)."),
    "home_goals_incl_extra_time": ("RESPONSE", "Home goals incl. extra time, excl. shoot-out (secondary analyses)."),
    "away_goals_incl_extra_time": ("RESPONSE", "Away goals incl. extra time, excl. shoot-out."),
    "total_goals_incl_extra_time": ("RESPONSE", "Total incl. extra time, excl. shoot-out."),
    "decided_by_shootout": ("POST", "1 if decided by penalty shoot-out."),
    "home_shootout_goals": ("POST", "Shoot-out kicks scored (never counted as goals)."),
    "away_shootout_goals": ("POST", "Shoot-out kicks scored (never counted as goals)."),
    "goals_scored_in_interval": ("RESPONSE", "Count of goals the panel team scored in the interval (can exceed 1)."),
    "goals_conceded_in_interval": ("RESPONSE", "Count of goals conceded in the interval."),
    "scored_at_least_one_goal": ("RESPONSE", "Binary: 1 if goals_scored_in_interval >= 1."),
    "conceded_at_least_one_goal": ("RESPONSE", "Binary: 1 if goals_conceded_in_interval >= 1."),
    # pre-match
    "pre_odds_p_home_win": ("PRE", "EPL: implied P(home win) from football-data.co.uk market-average PRE-CLOSING odds (AvgH/AvgD/AvgA), normalised to remove overround."),
    "pre_odds_p_draw": ("PRE", "EPL: implied P(draw)."), "pre_odds_p_away_win": ("PRE", "EPL: implied P(away win)."),
    "pre_odds_p_over25": ("PRE", "EPL: implied P(over 2.5 goals) from Avg>2.5 / Avg<2.5 odds. Strong baseline for goal totals."),
    "pre_odds_p_team_win": ("PRE", "EPL: implied P(panel team wins)."),
    "pre_odds_p_opponent_win": ("PRE", "EPL: implied P(opponent wins)."),
    "pre_elo_home": ("PRE", "WC: home team Elo before the match (computed by this pipeline from martj42 results; World Football Elo method)."),
    "pre_elo_away": ("PRE", "WC: away team pre-match Elo."),
    "pre_elo_diff_home_minus_away": ("PRE", "WC: pre_elo_home - pre_elo_away."),
    "pre_elo_team": ("PRE", "WC: panel team pre-match Elo."), "pre_elo_opponent": ("PRE", "WC: opponent pre-match Elo."),
    "pre_team_n_prior_matches": ("PRE", "Number of prior matches (<=10) behind the team's rolling features."),
    "pre_opp_n_prior_matches": ("PRE", "Same for opponent."),
    # time-varying
    "match_minute": ("TV", "Elapsed minute at interval start (0,15,30,45,60,75)."),
    "score_difference_at_interval_start": ("TV", "Team goals minus opponent goals before the interval begins."),
    "goals_for_before_interval": ("TV", "Team goals scored before the interval."),
    "goals_against_before_interval": ("TV", "Team goals conceded before the interval."),
    "tv_man_advantage_at_interval_start": ("TV", "Opponent red cards minus own red cards before the interval (>0 = numerical advantage)."),
    "tv_active_formation_at_interval_start": ("TV", "WC 2018/22 only: team's StatsBomb formation in force at interval start (after any Tactical Shift). StatsBomb labels differ in convention from ESPN."),
    "tv_opp_active_formation_at_interval_start": ("TV", "WC 2018/22 only: opponent's StatsBomb formation in force at interval start."),
    # interval design
    "interval_number": ("STRUCT", "1..6. Goals: interval of the goal (NA for extra time)."),
    "interval_label": ("STRUCT", "0-15, 15-30, 30-45+, 45-60, 60-75, 75-90+."),
    "interval_start": ("STRUCT", "Elapsed-minute lower bound (inclusive)."),
    "interval_end": ("STRUCT", "Elapsed-minute nominal upper bound (exclusive; intervals 3 and 6 also include stoppage)."),
    "interval_includes_stoppage": ("STRUCT", "1 for intervals 3 and 6."),
    "exposure_observed_minutes": ("EXPOSURE", "15, or 15 + observed added time for intervals 3/6 (from ESPN half-end clock). Known only after the interval: use as log-offset, not as predictor."),
    # goals
    "scoring_team": ("STRUCT", "Team credited with the goal (own goals credited to the benefiting team)."),
    "conceding_team": ("STRUCT", "Team that conceded."),
    "scoring_side": ("STRUCT", "'home' or 'away' side credited."),
    "goal_minute": ("RESPONSE", "Displayed match minute (base). 45+2 -> 45; 23' -> 23 (=elapsed 22:00-22:59)."),
    "stoppage_time_minute": ("RESPONSE", "Added-time minute (45+2 -> 2; 0 if not in stoppage)."),
    "original_goal_time": ("RESPONSE", "Exact source notation without quotes, e.g. '45+2', '90+4', '67'."),
    "clock_display": ("PROV", "Raw ESPN clock string, e.g. \"90'+4'\"."),
    "goal_period": ("STRUCT", "1H, 2H, ET1, ET2 (shoot-outs are excluded entirely)."),
    "in_regulation": ("STRUCT", "1 if 1H/2H (primary analysis)."),
    "is_stoppage_time": ("STRUCT", "1 if scored in added time."),
    "goal_type": ("STRUCT", "own_goal, penalty, header, direct_free_kick, volley, other_shot (from ESPN type)."),
    "goal_type_raw": ("PROV", "Raw ESPN type text, e.g. 'Penalty - Scored', 'Goal - Header', 'Own Goal'."),
    "penalty_indicator": ("STRUCT", "1 = in-match penalty (shoot-out kicks are never included)."),
    "own_goal_indicator": ("STRUCT", "1 = own goal; credited to scoring_team (the beneficiary)."),
    "scoring_team_starting_formation": ("STRUCT", "Scoring team's STARTING formation (ESPN) - not necessarily the shape at the time of the goal."),
    "active_formation_at_goal": ("TV", "WC 2018/22 only: scoring team's StatsBomb formation in force at the goal (latest Starting XI/Tactical Shift before the goal event)."),
    "opponent_active_formation_at_goal": ("TV", "WC 2018/22 only: conceding team's StatsBomb formation at the goal."),
    "active_formation_source": ("PROV", "Source of active formation (StatsBomb) or empty."),
    "sb_goal_minute": ("QA", "StatsBomb elapsed minute of the paired goal (pairing check)."),
    "home_score_after": ("POST", "Home score immediately after this goal (incl. extra time ordering)."),
    "away_score_after": ("POST", "Away score immediately after this goal."),
    "text_running_score_consistent": ("QA", "1 if ESPN commentary running score equals reconstructed score."),
    "own_goal_text_check": ("QA", "Own goals: 1 if the player's team in ESPN text is the conceding team."),
    "in_primary_sample": ("QA", "1 if both formations valid AND goal events reconcile with official score."),
    # QA / provenance
    "goal_events_reconciled": ("QA", "1 if goal events reproduce ESPN final score and (resolved) half scores."),
    "score_source": ("PROV", "Which source fields define the scores; flags ESPN linescore errors resolved by an independent source."),
    "linescore_conflict": ("QA", "1 if ESPN per-period linescores disagreed with ESPN goal events."),
    "check_halves_match_linescores": ("QA", "Raw comparison of goal events to ESPN linescores (before adjudication)."),
    "check_final_score_reconstructed": ("QA", "1 if goal events sum to ESPN final score."),
    "n_duplicate_goal_events_removed": ("QA", "Exact duplicate ESPN keyEvents (same period, clock, team, type and text) dropped for this match."),
    "n_goal_attribution_corrections": ("QA", "Own goals re-credited because ESPN's team credit contradicted ESPN's own text and the correction reproduces the final score."),
    "goal_attribution_corrected": ("QA", "1 if this own goal's team credit was corrected (see data_quality_report)."),
    "n_goals_unattributed": ("QA", "Goal events without a team (should be 0)."),
    "fd_matched": ("QA", "1 if matched to a football-data.co.uk row (season+home+away, explicit name map)."),
    "fd_date_diff_days": ("QA", "ESPN UTC date minus football-data date (days)."),
    "fd_FTHG": ("QA", "football-data.co.uk full-time home goals (independent check)."),
    "fd_FTAG": ("QA", "football-data.co.uk full-time away goals."),
    "fd_HTHG": ("QA", "football-data.co.uk half-time home goals."),
    "fd_HTAG": ("QA", "football-data.co.uk half-time away goals."),
    "elo_fixture_found": ("QA", "WC: 1 if the exact fixture was found in martj42 results (Elo taken from that row)."),
    "apif_home_formation": ("QA", "API-Football (HF mirror) home formation - cross-check only."),
    "apif_away_formation": ("QA", "API-Football away formation - cross-check only."),
    "formation_crosscheck_apif": ("QA", "1 if both ESPN formations equal API-Football's."),
    "sb_home_starting_formation": ("QA", "StatsBomb Starting XI formation (home), WC18/22."),
    "sb_away_starting_formation": ("QA", "StatsBomb Starting XI formation (away), WC18/22."),
    "formation_crosscheck_statsbomb": ("QA", "1 if both ESPN formations equal StatsBomb's label (labels follow different conventions)."),
    "sb_home_goals_incl_et": ("QA", "StatsBomb goal count for home side incl. ET."),
    "sb_away_goals_incl_et": ("QA", "StatsBomb goal count for away side incl. ET."),
    "commentary_shots_total": ("QA", "Number of attempts found in ESPN commentary (compare with post_*_totalShots)."),
    "commentary_events_complete": ("QA", "1 if ESPN commentary is complete enough to build time-varying shot/corner features; else those features are NaN."),
    "n_starters_home": ("QA", "Number of starters listed by ESPN (expect 11)."),
    "n_starters_away": ("QA", "Number of starters listed by ESPN (expect 11)."),
    "data_source": ("PROV", "Primary source of the row."),
}

PATTERNS = [
    (r"^pre_(home|away)_n_prior_matches$", "PRE", "Number of prior matches (<=10) used for {0} team's rolling features."),
    (r"^pre_(home|away)_rest_days$", "PRE", "Days since {0} team's previous match in the same competition group (NaN if none within 365 days)."),
    (r"^pre_(home|away)_(shots_comm|sot_comm)_last10$", "PRE",
     "{0} team's mean {1} (attempts / on target, counted from ESPN commentary; available for all seasons) over its previous <=10 matches (same window rules as other rolling features)."),
    (r"^pre_(home|away)_(\w+)_last10$", "PRE",
     "{0} team's mean {1} over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach."),
    (r"^pre_(team|opp)_(\w+)_last10$", "PRE", "Panel version of pre_<side>_{1}_last10 for the {0}."),
    (r"^tv_(own|opp)_(shot_any|shot_ot|corner|red|sub)_before_interval$", "TV",
     "Cumulative {0} {1} recorded before the interval begins (ESPN commentary / keyEvents). shot_any = all attempts; shot_ot = on target incl. goals; red = red cards incl. second yellows; sub = substitutions."),
    (r"^post_(home|away)_(shots|sot)_commentary$", "POST", "{0} team full-match {1} counted from ESPN commentary (available all seasons; NaN if commentary incomplete). Post-match: descriptive only."),
    (r"^post_(home|away)_n_tactical_shifts_sb$", "POST", "WC18/22: number of StatsBomb Tactical Shift events for {0} team (whole match)."),
    (r"^post_(h1|h2)_added_minutes_observed$", "POST", "Observed added minutes at end of {0} (from ESPN half-end clock)."),
    (r"^post_(home|away)_(\w+)$", "POST", "{0} team full-match box-score statistic '{1}' (ESPN). Post-match: descriptive only."),
]


def describe(col: str):
    if col in EXACT:
        return EXACT[col]
    for rx, role, txt in PATTERNS:
        mm = re.match(rx, col)
        if mm:
            return role, txt.format(*mm.groups())
    return None


MODEL_USE = {
    "ID": "cluster / random-effect keys only",
    "RESPONSE": "outcome",
    "PRE": "match Poisson/NB: yes | interval logistic/count: yes | survival: yes",
    "TV": "match-level: NO | interval models & survival: yes",
    "STRUCT": "yes (fixed at kickoff)",
    "EXPOSURE": "log-offset in interval Poisson only",
    "POST": "NO (descriptive only)",
    "QA": "NO",
    "PROV": "NO",
}


def data_dictionary(m, g, p) -> str:
    out = ["# Data dictionary", "",
           f"Generated {dt.date.today()} from the processed files. Every column is listed with its role. "
           "**Roles decide which columns may be used as predictors** (section 6 of the brief).", "",
           "| Role | Meaning | Allowed use |", "|---|---|---|"]
    for k, v in ROLE_HELP.items():
        out.append(f"| `{k}` | {v} | {MODEL_USE[k]} |")
    out += ["", "## Interval definition", "",
            "ESPN reports the displayed minute (minute *m* = elapsed time [m-1, m)). Intervals are defined on the displayed minute and the period:", "",
            "| # | label | half | displayed minutes | elapsed time |", "|---|---|---|---|---|",
            "| 1 | 0-15 | 1H | 1-15 | [0:00, 15:00) |",
            "| 2 | 15-30 | 1H | 16-30 | [15:00, 30:00) |",
            "| 3 | 30-45+ | 1H | 31-45 and 45+x | [30:00, end of 1H] |",
            "| 4 | 45-60 | 2H | 46-60 | [45:00, 60:00) |",
            "| 5 | 60-75 | 2H | 61-75 | [60:00, 75:00) |",
            "| 6 | 75-90+ | 2H | 76-90 and 90+x | [75:00, end of 2H] |", "",
            "The period (not the minute) decides the half, so first-half stoppage time always goes to interval 3 and second-half stoppage time to interval 6. Extra-time goals (ET1/ET2) are kept in `goal_events.csv` with `interval_number` = NA and are excluded from the panel. Shoot-out kicks are excluded everywhere.", ""]
    undocumented = []
    for name, df in (("match_level.csv", m), ("goal_events.csv", g), ("team_interval_panel.csv", p)):
        out += [f"## {name}", "", "| column | role | description |", "|---|---|---|"]
        for c in df.columns:
            d = describe(c)
            if d is None:
                undocumented.append(f"{name}:{c}")
                d = ("?", "UNDOCUMENTED")
            out.append(f"| `{c}` | {d[0]} | {d[1]} |")
        out.append("")
    if undocumented:
        out += ["## Undocumented columns", ""] + [f"- {u}" for u in undocumented]
    return "\n".join(out)


# --------------------------------------------------------------------------
# source audit (observations recorded during this project, 2026-11-22)
# --------------------------------------------------------------------------
def source_audit(m) -> pd.DataFrame:
    n = len(m)
    rows = [
        dict(source="ESPN site API (public, undocumented)",
             url="https://site.api.espn.com/apis/site/v2/sports/soccer/{eng.1|fifa.world}/{scoreboard?dates=YYYYMMDD|summary?event=ID}",
             tested="scoreboard (single day; date ranges return HTTP 400), summary", http_status="200",
             access="No key", goal_timestamps="YES - keyEvents: minute, stoppage notation (e.g. 90'+4'), period, team, penalty/own-goal type; shoot-out kicks flagged separately",
             starting_formations=f"YES - rosters[].formation, both teams present in {int(m.both_formations_available.sum())}/{n} matches",
             formation_changes="NO (not recorded)",
             seasons_verified="EPL 2023-24, 2024-25, 2025-26 (380 each), 2026-27 (109 completed by 2026-11-22); WC 2018 (64), 2022 (64), 2026 (104)",
             licence="Unofficial API; ESPN Terms of Use (personal, non-commercial). Do not redistribute raw JSON.",
             rate_limits_pricing="Free; no documented limits. Pipeline uses 0.35 s spacing + retry/backoff.",
             downloaded=f"YES - {n} match summaries", used_for="PRIMARY source for all three datasets",
             notes="Per-period linescores wrong in 5 matches (resolved, see quality report); box score empty in a few 2023-25 EPL matches; neutralSite flag False for all WC matches (not used)."),
        dict(source="StatsBomb Open Data", url="https://github.com/statsbomb/open-data",
             tested="competitions.json, matches/43/{3,106}.json, events/{id}.json", http_status="200",
             access="No key", goal_timestamps="YES (minute+second, period)", starting_formations="YES (Starting XI tactics.formation)",
             formation_changes="YES (Tactical Shift events)",
             seasons_verified="FIFA World Cup 2018, 2022 (64 each). Premier League only 2003/04 and 2015/16 - not in scope. No WC 2026.",
             licence="StatsBomb Public Data User Agreement; free for research with attribution.",
             rate_limits_pricing="Free (GitHub raw).", downloaded="YES - 128 matches incl. full event files",
             used_for="active_formation_at_goal / at interval start (WC18/22); cross-check of goals (128/128 agree) and formations",
             notes="Formation naming convention differs from ESPN (e.g. 3-4-2-1 vs 3-4-3; 5-3-2 vs 3-5-2)."),
        dict(source="football-data.co.uk", url="https://www.football-data.co.uk/mmz4281/{2324,2425,2526,2627}/E0.csv",
             tested="E0.csv for 4 seasons", http_status="200", access="No key", goal_timestamps="NO (FT/HT only)",
             starting_formations="NO", formation_changes="NO", seasons_verified="EPL 2023-24..2025-26 complete; 2026-27 file had 100 rows on 2026-11-22",
             licence="Free to use; credit football-data.co.uk.", rate_limits_pricing="Free", downloaded="YES",
             used_for="EPL pre-match odds (team strength / expected goals); independent FT/HT score check",
             notes=f"{int(m.fd_matched.sum())} EPL matches matched by explicit name map; 2026-27 file lags ESPN by {int(((m.competition=='Premier League')&(m.fd_matched==0)).sum())} matches."),
        dict(source="martj42/international_results", url="https://github.com/martj42/international_results",
             tested="results.csv", http_status="200", access="No key", goal_timestamps="NO", starting_formations="NO",
             formation_changes="NO", seasons_verified="All internationals 1872-2026 incl. WC 2018/2022/2026",
             licence="CC0-1.0", rate_limits_pricing="Free", downloaded="YES",
             used_for="Computed pre-match Elo for WC matches; neutral-venue and host-country flags", notes="Elo is DERIVED by this pipeline."),
        dict(source="Global Soccer Dataset (eatpizzanot/soccer-dataset, Hugging Face)",
             url="https://huggingface.co/datasets/eatpizzanot/soccer-dataset", tested="fixtures, fixture_lineups, teams, leagues parquet",
             http_status="200", access="No key", goal_timestamps="NO (no event table in the release)",
             starting_formations="YES (API-Football-derived lineups.formation)", formation_changes="NO",
             seasons_verified="EPL through 2025-26; no 2026-27 lineups at download time; WC 2018/2022/2026 partial",
             licence="CC-BY-4.0 (cite API-Football, football-data.co.uk)", rate_limits_pricing="Free", downloaded="YES",
             used_for="Independent formation cross-check only",
             notes="Not usable as primary: lacks goal timestamps. High agreement with ESPN may partly reflect a shared upstream data provider."),
        dict(source="API-Football v3", url="https://v3.football.api-sports.io", tested="/status without key",
             http_status="403", access="API key required (RapidAPI / api-sports)", goal_timestamps="Documented (fixtures/events) - NOT verified",
             starting_formations="Documented (fixtures/lineups) - NOT verified", formation_changes="Not documented",
             seasons_verified="Not verified (no key)", licence="Commercial ToS",
             rate_limits_pricing="Per vendor docs: free plan ~100 requests/day; not verified", downloaded="NO",
             used_for="Not used", notes="~3 calls per match x 1,481 matches would exceed a free daily quota by far; ESPN made it unnecessary."),
        dict(source="Sportmonks v3", url="https://api.sportmonks.com/v3/football/fixtures", tested="fixtures without token",
             http_status="401", access="API token; EPL/WC on paid plans per docs", goal_timestamps="Documented - NOT verified",
             starting_formations="Documented - NOT verified", formation_changes="Not verified", seasons_verified="Not verified",
             licence="Commercial", rate_limits_pricing="Paid (not verified)", downloaded="NO", used_for="Not used", notes=""),
        dict(source="football-data.org v4", url="https://api.football-data.org/v4/competitions/PL/matches", tested="matches without token",
             http_status="403", access="Free token (registration)", goal_timestamps="Not verified", starting_formations="Not verified",
             formation_changes="Not verified", seasons_verified="Not verified", licence="ToS", rate_limits_pricing="Free tier with request limits (not verified)",
             downloaded="NO", used_for="Not used", notes="Would require user registration; not needed."),
        dict(source="FBref", url="https://fbref.com/en/comps/9/schedule/", tested="schedule page", http_status="403",
             access="Blocks automated requests", goal_timestamps="Not verified", starting_formations="Not verified",
             formation_changes="Not verified", seasons_verified="Not verified", licence="Sports Reference ToS restricts scraping",
             rate_limits_pricing="n/a", downloaded="NO", used_for="Not used", notes="Access control respected; not circumvented."),
        dict(source="Understat", url="https://understat.com/league/EPL/2024", tested="league page", http_status="200",
             access="Public web page", goal_timestamps="Shot-level minutes exist per site - NOT inspected", starting_formations="NO (not provided)",
             formation_changes="NO", seasons_verified="Not verified", licence="Site ToS", rate_limits_pricing="n/a", downloaded="NO",
             used_for="Not used", notes="Possible future source of time-stamped xG for EPL; would need a second merge."),
        dict(source="ClubElo API", url="http://api.clubelo.com/2024-08-16", tested="date & club endpoints", http_status="502",
             access="No key", goal_timestamps="NO", starting_formations="NO", formation_changes="NO", seasons_verified="Unavailable at test time",
             licence="Free", rate_limits_pricing="Free", downloaded="NO", used_for="Not used (server error)", notes="Replaced by betting-market probabilities for EPL."),
        dict(source="eloratings.net", url="https://www.eloratings.net/2022.tsv", tested="year files", http_status="200",
             access="Public", goal_timestamps="NO", starting_formations="NO", formation_changes="NO",
             seasons_verified="Year-end ratings only (no pre-match history)", licence="Site", rate_limits_pricing="Free", downloaded="NO",
             used_for="Plausibility reference only", notes="Pre-match Elo computed from martj42 instead."),
        dict(source="nlbair/openplay (GitHub)", url="https://github.com/nlbair/openplay", tested="repository page", http_status="404",
             access="n/a", goal_timestamps="n/a", starting_formations="n/a", formation_changes="n/a", seasons_verified="n/a",
             licence="n/a", rate_limits_pricing="n/a", downloaded="NO", used_for="Not used", notes="Repository does not exist (confirmed 404)."),
        dict(source="Wyscout public dataset (Pappalardo et al. 2019)", url="https://figshare.com/collections/Soccer_match_event_dataset/4415000",
             tested="not tested", http_status="", access="Public download", goal_timestamps="Not verified", starting_formations="Not verified",
             formation_changes="Not verified", seasons_verified="Known to cover 2017-18 club seasons and WC 2018 only (outside EPL scope) - not verified here",
             licence="CC-BY-4.0 (per publication)", rate_limits_pricing="Free", downloaded="NO", used_for="Not used",
             notes="Out of the requested EPL seasons; WC 2018 already covered by ESPN + StatsBomb."),
        dict(source="Kaggle datasets", url="https://www.kaggle.com", tested="not tested", http_status="", access="Kaggle account + API token",
             goal_timestamps="varies", starting_formations="varies", formation_changes="varies", seasons_verified="Not verified",
             licence="varies", rate_limits_pricing="Free", downloaded="NO", used_for="Not used", notes="Needs user credentials; provenance often unclear."),
        dict(source="Open Matchday", url="", tested="not tested", http_status="", access="Unknown", goal_timestamps="Not verified",
             starting_formations="Not verified", formation_changes="Not verified", seasons_verified="Not verified", licence="Unknown",
             rate_limits_pricing="Unknown", downloaded="NO", used_for="Not used", notes="No authoritative endpoint identified; not relied upon."),
    ]
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
def _md(df: pd.DataFrame, index=False) -> str:
    d = df.reset_index() if index else df
    cols = list(d.columns)
    d = d.map(lambda v: v.replace("|", "\\|") if isinstance(v, str) else v)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for r in d.itertuples(index=False):
        lines.append("| " + " | ".join("" if (isinstance(v, float) and np.isnan(v)) else
                                      (f"{v:.3f}" if isinstance(v, float) and not float(v).is_integer() else
                                       str(int(v)) if isinstance(v, float) else str(v)) for v in r) + " |")
    return "\n".join(lines)


def quality_report(checks, cov, ff, fm, m, g, p) -> str:
    epl = m.competition == "Premier League"
    lc = m[m.linescore_conflict == 1]
    box_missing = m[m.post_home_possessionPct.isna()]
    s = [f"# Data quality report", "", f"Generated {dt.date.today()} | data cut-off {config.CUTOFF_DATE}", "",
         "## 1. Totals", "",
         f"- match_level.csv: **{len(m)} matches** ({int(epl.sum())} EPL, {int((~epl).sum())} World Cup)",
         f"- goal_events.csv: **{len(g)} goals** ({int(g.in_regulation.sum())} in regulation, {int((g.in_regulation == 0).sum())} in extra time; shoot-out kicks excluded)",
         f"- team_interval_panel.csv: **{len(p)} team-interval rows** ({p.match_id.nunique()} matches x 2 teams x 6 intervals)",
         f"- primary sample (both formations + reconciled goal events): **{int(m.in_primary_sample.sum())} / {len(m)}** matches",
         f"- goalless (0-0) matches retained: {int((m.total_goals == 0).sum())}", "",
         "## 2. Coverage by competition and season", "", _md(cov), "",
         "## 3. Automated validation checks", "",
         f"{int(checks.passed.sum())}/{len(checks)} checks pass. Checks marked (info) report counts.", "",
         _md(checks[["check", "passed", "n_violations", "n_checked", "detail"]]), "",
         "## 4. Conflicts found and how they were handled", "",
         f"**ESPN per-period linescores vs goal events ({len(lc)} matches).** In each case ESPN's goal events reproduce ESPN's final score, while the per-period `linescores` field is wrong (all zeros, a value of -1, or goals assigned to the wrong half). "
         "The goal-event split was accepted only because an independent source confirmed it (football-data.co.uk HT/FT for EPL, StatsBomb period-level goals for WC). Raw data are untouched; the decision is recorded in `score_source` and `linescore_conflict`.", "",
         _md(lc[["match_id", "competition", "season", "home_team", "away_team", "home_goals", "away_goals",
                 "half_time_home_goals", "half_time_away_goals", "score_source"]]), "",
         f"**Duplicate goal events ({int((m.n_duplicate_goal_events_removed > 0).sum())} match(es), {int(m.n_duplicate_goal_events_removed.sum())} rows dropped).** ESPN listed the same goal twice, with identical period, clock, team, type and text (which includes the running score). The duplicate copy is dropped. Matches: {', '.join(m[m.n_duplicate_goal_events_removed > 0].match_id)}.", "",
         f"**Own-goal credit contradicting ESPN's own text ({int(m.n_goal_attribution_corrections.sum())} goal(s)).** ESPN credited an own goal to the own-goal scorer's team, although its text says \"Own Goal by <player>, <that team>\". The goal was re-credited to the opponent because that reproduces ESPN's final score. Football-data.co.uk FT/HT scores agree. Matches: {', '.join(m[m.n_goal_attribution_corrections > 0].match_id)}.", "",
         f"**Matches without starting formations ({int((m.both_formations_available == 0).sum())}).** ESPN's roster has no formation label for these matches (players' position slots exist, but are not converted into a label). They stay in match_level.csv and goal_events.csv with `in_primary_sample = 0` and are excluded from the panel. API-Football labels, where present, are in `apif_*_formation` for sensitivity checks only. Matches: {', '.join(m[m.both_formations_available == 0].match_id)}.", "",
         f"**Empty ESPN box scores ({len(box_missing)} matches).** ESPN returned all-zero placeholder statistics; these are set to missing (not zero). Goal events and formations for these matches are complete, so they stay in the sample; post-match statistics and the rolling style features that depend on them are NaN-aware.", "",
         _md(box_missing.groupby(["competition", "season"]).size().rename("matches_without_box_score").reset_index()), "",
         f"**Commentary completeness.** Time-varying shot and corner counts come from ESPN commentary. For each match the commentary attempt count was compared with the box-score total (tolerance: max(4 shots, 15%)). {int((m.commentary_events_complete == 0).sum())} match(es) fail ({', '.join(m[m.commentary_events_complete == 0].match_id)}); their commentary-derived features are NaN, not 0. Red cards and substitutions come from keyEvents and are unaffected.", "",
         "**ESPN neutral-site flag.** ESPN reports `neutralSite = False` for every World Cup match, so it is not used. `neutral_site` and host-country flags for World Cup matches come from the martj42 fixture record.", "",
         f"**football-data.co.uk 2026-27 lag.** {int((epl & (m.fd_matched == 0)).sum())} recent EPL matches are not yet in the football-data.co.uk file, so their pre-match odds are missing. Re-run with `--refresh-current-season` later to take a new dated snapshot.", "",
         "## 5. Formation label agreement across providers", "",
         "Formation labels are a provider's interpretation of the average shape, not an objective measurement.", "",
         f"- ESPN vs API-Football (Hugging Face mirror), team-level exact agreement: **{_team_agree(m, 'apif'):.1%}** over {int(m.formation_crosscheck_apif.notna().sum())} matches. The two may share an upstream provider, so this is a consistency check rather than fully independent validation.",
         f"- ESPN vs StatsBomb (WC 2018/22), team-level exact agreement: **{_team_agree(m, 'sb'):.1%}**; back-line (number of defenders) agreement **{_backline_agree(m):.1%}**. Most disagreements are naming conventions (3-4-2-1 vs 3-4-3, 5-3-2 vs 3-5-2, 4-2-3-1 vs 4-5-1).", "",
         _md(_sb_disagreements(m).head(15)), "",
         "## 6. Formation frequencies (team-matches, primary sample)", "", _md(ff, index=True), "",
         "## 7. Formation matchup frequencies (unordered pairs, primary sample)", "",
         _md(fm, index=True), "",
         "## 8. Missingness of predictor families (panel rows)", "",
         _md((p.filter(regex="^(pre_|tv_)").isna().groupby(p.competition).mean() * 100).round(1).T, index=True), "",
         "Pre-match odds exist only for the EPL and pre-match Elo only for the World Cup, by design. A World Cup team's first match has no rolling history because only earlier matches in the same tournament are used. EPL rolling features are missing only for each team's first EPL match within the dataset.", ""]
    return "\n".join(s)


def _team_agree(m, src):
    if src == "apif":
        a = m[m.formation_crosscheck_apif.notna()]
        return pd.concat([a.home_starting_formation == a.apif_home_formation,
                          a.away_starting_formation == a.apif_away_formation]).mean()
    a = m[m.sb_match_id.notna()]
    return pd.concat([a.home_starting_formation == a.sb_home_starting_formation,
                      a.away_starting_formation == a.sb_away_starting_formation]).mean()


def _backline_agree(m):
    a = m[m.sb_match_id.notna()]
    return pd.concat([a.home_starting_formation.str[0] == a.sb_home_starting_formation.str[0],
                      a.away_starting_formation.str[0] == a.sb_away_starting_formation.str[0]]).mean()


def _sb_disagreements(m):
    a = m[m.sb_match_id.notna()]
    x = pd.concat([a[["home_starting_formation", "sb_home_starting_formation"]].set_axis(["ESPN", "StatsBomb"], axis=1),
                   a[["away_starting_formation", "sb_away_starting_formation"]].set_axis(["ESPN", "StatsBomb"], axis=1)])
    x = x[x.ESPN != x.StatsBomb]
    return x.value_counts().rename("team_matches").reset_index()


def feasibility(cov, ff, fm, m, g, p) -> str:
    epl = m.competition == "Premier League"
    def disp(x):
        return x.var() / x.mean()
    tg = {c: disp(m[m.competition == c].total_goals) for c in m.competition.unique()}
    team_g = pd.concat([m[["competition", "home_goals"]].set_axis(["c", "g"], axis=1),
                        m[["competition", "away_goals"]].set_axis(["c", "g"], axis=1)])
    td = team_g.groupby("c").g.apply(disp)
    rates = p.groupby(["competition", "interval_number"]).agg(
        mean_goals=("goals_scored_in_interval", "mean"),
        p_score=("scored_at_least_one_goal", "mean"),
        rows=("panel_id", "size")).round(3).reset_index()
    fm_t = fm.copy()
    adequate = {k: int((fm_t.total >= k).sum()) for k in (30, 50, 100)}
    epl_ad = int((fm_t["Premier League"] >= 30).sum())
    wc_ad = int((fm_t["FIFA World Cup"] >= 30).sum()) if "FIFA World Cup" in fm_t else 0
    top = fm_t[fm_t.total >= 30].reset_index()
    bl = m.groupby(["back_line_matchup", "competition"]).size().unstack(fill_value=0)
    shifts = m[["post_home_n_tactical_shifts_sb", "post_away_n_tactical_shifts_sb"]].stack()
    ga = g[g.active_formation_at_goal.notna()]
    sbstart = pd.concat([
        m[m.sb_match_id.notna()][["match_id", "home_team", "sb_home_starting_formation"]].set_axis(["match_id", "team", "f"], axis=1),
        m[m.sb_match_id.notna()][["match_id", "away_team", "sb_away_starting_formation"]].set_axis(["match_id", "team", "f"], axis=1)])
    sbs = sbstart.set_index(["match_id", "team"]).f
    changed = np.mean([a != sbs.get((mid, t)) for a, mid, t in
                       zip(ga.active_formation_at_goal, ga.match_id, ga.scoring_team)]) if len(ga) else np.nan
    n_wc = int((~epl).sum())
    s = [
        "# Feasibility assessment", "",
        f"Generated {dt.date.today()}. Based on {len(m)} matches, {len(g)} goals and {len(p)} team-interval rows actually collected and validated.", "",
        "## 1. Is the full research question answerable?", "",
        "**Mostly yes, with three explicit qualifications.**", "",
        f"1. **Formation and goal counts (Q1, Q2):** answerable. Both starting formations and fully reconciled goal events exist for {int(m.in_primary_sample.sum()):,}/{len(m):,} in-scope matches.",
        "2. **Formation and goal timing (Q3):** answerable using *starting* formations, through the interval panel and discrete-time survival. In-match formation changes are observed only for WC 2018/2022 (StatsBomb). For the EPL and WC 2026, use the phrase \"starting formation\" and do not describe it as the shape in force when a goal was scored.",
        f"   - For context, in WC 2018/22 teams averaged {shifts.mean():.2f} StatsBomb Tactical Shifts per match, and the scoring team's active formation differed from its StatsBomb starting formation at {changed:.0%} of goals. Starting formation is therefore a noisy proxy for the shape at the time of a goal.",
        "3. **Tactical strategy (Q4):** only partially measurable. No source used here has a validated time-stamped measure of directness or possession. What can be measured:",
        "   - **Pre-match style:** each team's rolling mean of possession %, passes, long-ball share (long balls / passes) and shots over its previous ≤10 matches. These are leakage-safe and are the recommended operationalisation of 'direct vs possession-based'.",
        "   - **In-match, time-varying:** cumulative shots, shots on target, corners, red cards and substitutions before each interval (from ESPN commentary; validated against box-score totals).",
        "   - **Post-match only:** full-match possession, passes, long balls, crosses. These are descriptive and must not be used to predict goals in the same match.",
        "   - **Not available:** xG for most matches. football-data.co.uk added match xG only in 2026-27, and it is post-match.",
        "4. **EPL vs World Cup (Q5):** answerable, but the World Cup side is small. See section 4.", "",
        "Causal language is **not** justified. Formations are chosen in response to the opponent, expected game state and squad quality. Coefficients are adjusted associations, conditional on the pre-match strength controls.", "",
        "## 2. Which seasons have reliable data", "",
        _md(cov[["competition", "season", "completed_by_cutoff", "both_requirements (primary sample)",
                 "validated_regulation_goals_primary", "goals_per_match_primary"]]), "",
        f"All {len(cov)} competition-seasons are covered. {int((cov['both_requirements (primary sample)'] == cov.completed_by_cutoff).sum())} are 100% usable. "
        f"The rest lose only matches without ESPN formation labels ({int((m.both_formations_available == 0).sum())} in total). "
        "2026-27 is a partial season (matches to 22 Nov 2026), so include season fixed effects. "
        "Historical seasons differ in tactical-statistic coverage: 2016-17 has no ESPN box scores. See reports/historical_expansion_report.md.", "",
        "## 3. Which formation matchups have adequate observations", "",
        f"There are {ff.shape[0]} distinct formation labels and {fm.shape[0]} distinct unordered matchups. Matchups with at least 30 matches: **{adequate[30]}** overall ({epl_ad} within EPL alone, {wc_ad} within World Cup alone). With at least 50 matches: {adequate[50]}; with at least 100: {adequate[100]}.", "",
        _md(top, index=False), "",
        "**Recommendations:**",
        "- Use the five formation groups (`*_formation_group`: 4-2-3-1 / 4-3-3 family / 4-4-2 family / back-3/5 with 1 or 3 forwards / back-3/5 with 2 forwards) as the main factor. Or model the most common exact formations (4-2-3-1, 4-3-3, 4-4-2, 3-4-2-1, 4-1-4-1) and pool the rest.",
        "- Or use the provider-robust coarse descriptors `back_line` (3/4/5 defenders) and `n_forwards`.",
        "- Back-line matchups (home vs away):", "", _md(bl, index=True), "",
        "- A full matchup interaction (formation × opponent formation) is estimable only for the top few pairs, and in practice only within the EPL. Use regularisation or random effects for matchups.", "",
        "## 4. Is the EPL vs World Cup comparison statistically reasonable?", "",
        f"- Sample sizes are very unequal: {int(epl.sum())} EPL vs {n_wc} WC matches. That gives {n_wc * 12} WC panel rows and about {int(g[(g.competition == 'FIFA World Cup') & (g.in_regulation == 1)].shape[0])} regulation WC goals.",
        "- Main effects (does goal rate differ by competition, and do the main formation effects differ?) are estimable through a competition × formation-family interaction.",
        "- Competition × detailed-matchup interactions are **not** estimable with useful precision. No unordered matchup reaches 30 World Cup matches.",
        "- The strength controls differ by competition: market odds for EPL, computed Elo for WC. Standardise within competition, or fit competition-specific models and compare coefficients.",
        "- World Cup 'home' is mostly administrative (neutral venues). Use `neutral_site` and `team_is_host_country` rather than `home_indicator`.",
        "- World Cup knockout matches cannot end level after extra time. The primary analysis uses regulation time; `stage` lets you check robustness.", "",
        "## 5. Distributional facts relevant to model choice", "",
        f"- Total goals per match: variance/mean = {tg.get('Premier League', np.nan):.2f} (EPL) and {tg.get('FIFA World Cup', np.nan):.2f} (WC).",
        f"- Team goals per match: variance/mean = {td.get('Premier League', np.nan):.2f} (EPL) and {td.get('FIFA World Cup', np.nan):.2f} (WC).",
        "- So overdispersion is mild in the EPL and moderate in the World Cup. Test it formally (Cameron–Trivedi or a likelihood-ratio Poisson vs NB), but expect Poisson to be adequate for EPL team goals.",
        f"- {g.is_stoppage_time.mean():.1%} of goals are scored in stoppage time. That is why intervals 3 and 6 are longer: observed mean exposure is {p[p.interval_number == 3].exposure_observed_minutes.mean():.1f} and {p[p.interval_number == 6].exposure_observed_minutes.mean():.1f} minutes. Use `log(exposure_observed_minutes)` as an offset in interval Poisson models, or include interval fixed effects.", "",
        "Goal rate by interval (panel):", "", _md(rates), "",
        "## 6. Recommended models", "",
        "| Question | Data | Model | Notes |", "|---|---|---|---|",
        "| Q1 team goals ~ own formation | team-level (two rows per match, built from match_level) | Poisson GLM (NB if LR test rejects) | controls: opponent formation, pre-match strength, home/neutral, season FE; cluster SEs by match |",
        "| Q2 total goals ~ matchup | match_level | Poisson/NB on `total_goals` with `formation_pair_unordered` (top pairs + other) | `pre_odds_p_over25` is a strong baseline control for EPL |",
        "| Q3 timing | team_interval_panel | logistic on `scored_at_least_one_goal`, interval FE × formation | equivalently a discrete-time hazard for the first goal: keep rows up to the first goal interval |",
        "| Q3 counts | team_interval_panel | Poisson on `goals_scored_in_interval` + offset log(exposure) | allows more than one goal per interval |",
        "| Q4 tactics | panel / team-level | add `pre_team_possession_last10`, `pre_team_long_ball_share_last10` and time-varying shots / red cards | time-varying covariates are mediators of game state; report models with and without them |",
        "| Q5 EPL vs WC | pooled | competition × formation-family interaction | or separate models with a Wald test of coefficient equality |", "",
        "**Dependence:** rows are clustered within match and team (12 panel rows per match). Use cluster-robust SEs by `match_id`, or mixed models with random intercepts for `team_id` (crossed with `match_id`) via `lme4::glmer` or `glmmTMB`.", "",
        "## 7. Main limitations", "",
        "- Formation labels are provider interpretations of the average starting shape (see the agreement figures in the quality report).",
        "- No formation changes are recorded for the EPL or WC 2026.",
        "- Goal times have minute resolution only; seconds are never invented.",
        "- ESPN is an undocumented public API. Its terms restrict redistribution of the raw data, so cite it and do not republish the raw JSON.",
        "- Pre-match strength proxies differ by competition (odds vs Elo).",
        f"- 2026-27 is a partial season and {int((epl & m.pre_odds_p_home_win.isna() & (m.season == '2026-27')).sum())} of its matches still lack odds.",
    ]
    return "\n".join(s)


def write_all():
    checks, cov, ff, fm, m, g, p = validate.write_reports()
    (R / "data_dictionary.md").write_text(data_dictionary(m, g, p))
    source_audit(m).to_csv(P / "source_audit.csv", index=False)
    (R / "data_quality_report.md").write_text(quality_report(checks, cov, ff, fm, m, g, p))
    (R / "feasibility_assessment.md").write_text(feasibility(cov, ff, fm, m, g, p))
    return checks
