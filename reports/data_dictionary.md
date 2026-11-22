# Data dictionary

Generated 2026-11-22 from the processed files. Every column is listed with its role. **Roles decide which columns may be used as predictors** (section 6 of the brief).

| Role | Meaning | Allowed use |
|---|---|---|
| `ID` | identifier / join key - never a predictor | cluster / random-effect keys only |
| `RESPONSE` | outcome variable | outcome |
| `PRE` | pre-match predictor: known before kickoff, valid in every model | match Poisson/NB: yes | interval logistic/count: yes | survival: yes |
| `TV` | time-varying predictor: known at the START of the interval (panel only) | match-level: NO | interval models & survival: yes |
| `STRUCT` | structural design variable fixed at kickoff (formation, home, stage, interval) | yes (fixed at kickoff) |
| `EXPOSURE` | post-hoc exposure (minutes played in interval) - offset only, NEVER a predictor | log-offset in interval Poisson only |
| `POST` | post-match descriptive statistic - NEVER a predictor of goals in the same match | NO (descriptive only) |
| `QA` | validation / cross-source check field | NO |
| `PROV` | provenance / metadata | NO |

## Interval definition

ESPN reports the displayed minute (minute *m* = elapsed time [m-1, m)). Intervals are defined on the displayed minute and the period:

| # | label | half | displayed minutes | elapsed time |
|---|---|---|---|---|
| 1 | 0-15 | 1H | 1-15 | [0:00, 15:00) |
| 2 | 15-30 | 1H | 16-30 | [15:00, 30:00) |
| 3 | 30-45+ | 1H | 31-45 and 45+x | [30:00, end of 1H] |
| 4 | 45-60 | 2H | 46-60 | [45:00, 60:00) |
| 5 | 60-75 | 2H | 61-75 | [60:00, 75:00) |
| 6 | 75-90+ | 2H | 76-90 and 90+x | [75:00, end of 2H] |

The period (not the minute) decides the half, so first-half stoppage time always goes to interval 3 and second-half stoppage time to interval 6. Extra-time goals (ET1/ET2) are kept in `goal_events.csv` with `interval_number` = NA and are excluded from the panel. Shoot-out kicks are excluded everywhere.

## match_level.csv

| column | role | description |
|---|---|---|
| `match_id` | ID | Pipeline match key = 'ESPN-' + ESPN event id. Links all three tables. |
| `espn_event_id` | ID | Native ESPN event id. |
| `competition` | STRUCT | 'Premier League' or 'FIFA World Cup'. |
| `season` | STRUCT | EPL '2023-24'...'2026-27'; World Cup '2018','2022','2026'. Read as string. |
| `stage` | STRUCT | 'League' (EPL), 'Group' or 'Knockout' (WC; derived from group-stage end date). |
| `match_date` | STRUCT | Kickoff date in UTC (YYYY-MM-DD). |
| `kickoff_utc` | STRUCT | Kickoff timestamp, UTC, from ESPN. |
| `status` | PROV | ESPN final status: FULL_TIME, FINAL_AET (extra time), FINAL_PEN (shoot-out). |
| `home_team` | STRUCT | Home (or first-listed, for neutral WC venues) team, ESPN display name. |
| `away_team` | STRUCT | Away team, ESPN display name. |
| `home_team_id` | ID | ESPN team id (home). |
| `away_team_id` | ID | ESPN team id (away). |
| `home_starting_formation` | STRUCT | Home starting formation as published by ESPN (Opta-style label). Starting shape only. |
| `away_starting_formation` | STRUCT | Away starting formation (ESPN). |
| `formation_matchup` | STRUCT | Ordered matchup string. match_level: 'home vs away'; panel: 'team vs opponent'. |
| `formation_pair_unordered` | STRUCT | Alphabetically ordered pair 'A | B' (symmetric matchup, for total-goals models). |
| `both_formations_available` | QA | 1 if both labels exist and are valid. |
| `home_back_line` | STRUCT | Number of defenders in home formation (first digit). Provider-robust coarse descriptor. |
| `away_back_line` | STRUCT | Number of defenders in away formation. |
| `home_n_forwards` | STRUCT | Number of forwards (last digit) in home formation. |
| `away_n_forwards` | STRUCT | Number of forwards in away formation. |
| `back_line_matchup` | STRUCT | e.g. '4B vs 3B' (home vs away back lines). |
| `home_formation_group` | STRUCT | Home formation group (explicit map in build_datasets.FORMATION_GROUP; 'other' = unmapped label). Original string kept in home_starting_formation. |
| `away_formation_group` | STRUCT | Away formation group. |
| `formation_group_matchup` | STRUCT | Ordered group matchup (match_level: home vs away; panel: team vs opponent). |
| `formation_group_pair_unordered` | STRUCT | Unordered group pair 'A | B'. |
| `home_goals` | RESPONSE | Home goals in regulation (90 min + stoppage). Excludes extra time and shoot-outs. |
| `away_goals` | RESPONSE | Away goals in regulation. |
| `total_goals` | RESPONSE | home_goals + away_goals (regulation). |
| `half_time_home_goals` | RESPONSE | Home goals at half-time (first half incl. stoppage). Not a predictor for the full-match total. |
| `half_time_away_goals` | RESPONSE | Away goals at half-time. |
| `went_to_extra_time` | POST | 1 if the match went to extra time (WC knockouts). |
| `home_goals_incl_extra_time` | RESPONSE | Home goals incl. extra time, excl. shoot-out (secondary analyses). |
| `away_goals_incl_extra_time` | RESPONSE | Away goals incl. extra time, excl. shoot-out. |
| `total_goals_incl_extra_time` | RESPONSE | Total incl. extra time, excl. shoot-out. |
| `decided_by_shootout` | POST | 1 if decided by penalty shoot-out. |
| `home_shootout_goals` | POST | Shoot-out kicks scored (never counted as goals). |
| `away_shootout_goals` | POST | Shoot-out kicks scored (never counted as goals). |
| `neutral_site` | STRUCT | 1 = neutral venue. EPL: 0. WC: from martj42 fixture record (ESPN's flag is unreliable for WCs). |
| `neutral_site_source` | PROV | Source of neutral_site. |
| `home_is_host_country` | STRUCT | WC only: home side is the host nation of the venue. |
| `away_is_host_country` | STRUCT | WC only: away side is the host nation of the venue. |
| `venue` | PROV | Stadium name (ESPN). |
| `pre_odds_p_home_win` | PRE | EPL: implied P(home win) from football-data.co.uk market-average PRE-CLOSING odds (AvgH/AvgD/AvgA), normalised to remove overround. |
| `pre_odds_p_draw` | PRE | EPL: implied P(draw). |
| `pre_odds_p_away_win` | PRE | EPL: implied P(away win). |
| `pre_odds_p_over25` | PRE | EPL: implied P(over 2.5 goals) from Avg>2.5 / Avg<2.5 odds. Strong baseline for goal totals. |
| `pre_elo_home` | PRE | WC: home team Elo before the match (computed by this pipeline from martj42 results; World Football Elo method). |
| `pre_elo_away` | PRE | WC: away team pre-match Elo. |
| `pre_elo_diff_home_minus_away` | PRE | WC: pre_elo_home - pre_elo_away. |
| `pre_away_ga_last10` | PRE | away team's mean ga over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_away_gf_last10` | PRE | away team's mean gf over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_away_long_ball_share_last10` | PRE | away team's mean long_ball_share over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_away_n_prior_matches` | PRE | Number of prior matches (<=10) used for away team's rolling features. |
| `pre_away_passes_last10` | PRE | away team's mean passes over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_away_points_last10` | PRE | away team's mean points over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_away_possession_last10` | PRE | away team's mean possession over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_away_rest_days` | PRE | Days since away team's previous match in the same competition group (NaN if none within 365 days). |
| `pre_away_shots_comm_last10` | PRE | away team's mean shots_comm (attempts / on target, counted from ESPN commentary; available for all seasons) over its previous <=10 matches (same window rules as other rolling features). |
| `pre_away_shots_last10` | PRE | away team's mean shots over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_away_sot_comm_last10` | PRE | away team's mean sot_comm (attempts / on target, counted from ESPN commentary; available for all seasons) over its previous <=10 matches (same window rules as other rolling features). |
| `pre_away_sot_last10` | PRE | away team's mean sot over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_home_ga_last10` | PRE | home team's mean ga over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_home_gf_last10` | PRE | home team's mean gf over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_home_long_ball_share_last10` | PRE | home team's mean long_ball_share over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_home_n_prior_matches` | PRE | Number of prior matches (<=10) used for home team's rolling features. |
| `pre_home_passes_last10` | PRE | home team's mean passes over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_home_points_last10` | PRE | home team's mean points over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_home_possession_last10` | PRE | home team's mean possession over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_home_rest_days` | PRE | Days since home team's previous match in the same competition group (NaN if none within 365 days). |
| `pre_home_shots_comm_last10` | PRE | home team's mean shots_comm (attempts / on target, counted from ESPN commentary; available for all seasons) over its previous <=10 matches (same window rules as other rolling features). |
| `pre_home_shots_last10` | PRE | home team's mean shots over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `pre_home_sot_comm_last10` | PRE | home team's mean sot_comm (attempts / on target, counted from ESPN commentary; available for all seasons) over its previous <=10 matches (same window rules as other rolling features). |
| `pre_home_sot_last10` | PRE | home team's mean sot over its previous <=10 matches (EPL: previous EPL matches within 365 days, may span seasons, none for promoted clubs' first EPL match; WC: earlier matches in the same tournament only). Box-score based: missing for 2016-17. Style features (possession, passes, long_ball_share) are the leakage-safe way to measure tactical approach. |
| `post_away_accurateCrosses` | POST | away team full-match box-score statistic 'accurateCrosses' (ESPN). Post-match: descriptive only. |
| `post_away_accurateLongBalls` | POST | away team full-match box-score statistic 'accurateLongBalls' (ESPN). Post-match: descriptive only. |
| `post_away_accuratePasses` | POST | away team full-match box-score statistic 'accuratePasses' (ESPN). Post-match: descriptive only. |
| `post_away_effectiveClearance` | POST | away team full-match box-score statistic 'effectiveClearance' (ESPN). Post-match: descriptive only. |
| `post_away_foulsCommitted` | POST | away team full-match box-score statistic 'foulsCommitted' (ESPN). Post-match: descriptive only. |
| `post_away_interceptions` | POST | away team full-match box-score statistic 'interceptions' (ESPN). Post-match: descriptive only. |
| `post_away_long_ball_share` | POST | away team full-match box-score statistic 'long_ball_share' (ESPN). Post-match: descriptive only. |
| `post_away_n_tactical_shifts_sb` | POST | WC18/22: number of StatsBomb Tactical Shift events for away team (whole match). |
| `post_away_offsides` | POST | away team full-match box-score statistic 'offsides' (ESPN). Post-match: descriptive only. |
| `post_away_pass_accuracy` | POST | away team full-match box-score statistic 'pass_accuracy' (ESPN). Post-match: descriptive only. |
| `post_away_penaltyKickGoals` | POST | away team full-match box-score statistic 'penaltyKickGoals' (ESPN). Post-match: descriptive only. |
| `post_away_penaltyKickShots` | POST | away team full-match box-score statistic 'penaltyKickShots' (ESPN). Post-match: descriptive only. |
| `post_away_possessionPct` | POST | away team full-match box-score statistic 'possessionPct' (ESPN). Post-match: descriptive only. |
| `post_away_redCards` | POST | away team full-match box-score statistic 'redCards' (ESPN). Post-match: descriptive only. |
| `post_away_saves` | POST | away team full-match box-score statistic 'saves' (ESPN). Post-match: descriptive only. |
| `post_away_shotsOnTarget` | POST | away team full-match box-score statistic 'shotsOnTarget' (ESPN). Post-match: descriptive only. |
| `post_away_shots_commentary` | POST | away team full-match shots counted from ESPN commentary (available all seasons; NaN if commentary incomplete). Post-match: descriptive only. |
| `post_away_sot_commentary` | POST | away team full-match sot counted from ESPN commentary (available all seasons; NaN if commentary incomplete). Post-match: descriptive only. |
| `post_away_totalCrosses` | POST | away team full-match box-score statistic 'totalCrosses' (ESPN). Post-match: descriptive only. |
| `post_away_totalLongBalls` | POST | away team full-match box-score statistic 'totalLongBalls' (ESPN). Post-match: descriptive only. |
| `post_away_totalPasses` | POST | away team full-match box-score statistic 'totalPasses' (ESPN). Post-match: descriptive only. |
| `post_away_totalShots` | POST | away team full-match box-score statistic 'totalShots' (ESPN). Post-match: descriptive only. |
| `post_away_totalTackles` | POST | away team full-match box-score statistic 'totalTackles' (ESPN). Post-match: descriptive only. |
| `post_away_wonCorners` | POST | away team full-match box-score statistic 'wonCorners' (ESPN). Post-match: descriptive only. |
| `post_away_yellowCards` | POST | away team full-match box-score statistic 'yellowCards' (ESPN). Post-match: descriptive only. |
| `post_h1_added_minutes_observed` | POST | Observed added minutes at end of h1 (from ESPN half-end clock). |
| `post_h2_added_minutes_observed` | POST | Observed added minutes at end of h2 (from ESPN half-end clock). |
| `post_home_accurateCrosses` | POST | home team full-match box-score statistic 'accurateCrosses' (ESPN). Post-match: descriptive only. |
| `post_home_accurateLongBalls` | POST | home team full-match box-score statistic 'accurateLongBalls' (ESPN). Post-match: descriptive only. |
| `post_home_accuratePasses` | POST | home team full-match box-score statistic 'accuratePasses' (ESPN). Post-match: descriptive only. |
| `post_home_effectiveClearance` | POST | home team full-match box-score statistic 'effectiveClearance' (ESPN). Post-match: descriptive only. |
| `post_home_foulsCommitted` | POST | home team full-match box-score statistic 'foulsCommitted' (ESPN). Post-match: descriptive only. |
| `post_home_interceptions` | POST | home team full-match box-score statistic 'interceptions' (ESPN). Post-match: descriptive only. |
| `post_home_long_ball_share` | POST | home team full-match box-score statistic 'long_ball_share' (ESPN). Post-match: descriptive only. |
| `post_home_n_tactical_shifts_sb` | POST | WC18/22: number of StatsBomb Tactical Shift events for home team (whole match). |
| `post_home_offsides` | POST | home team full-match box-score statistic 'offsides' (ESPN). Post-match: descriptive only. |
| `post_home_pass_accuracy` | POST | home team full-match box-score statistic 'pass_accuracy' (ESPN). Post-match: descriptive only. |
| `post_home_penaltyKickGoals` | POST | home team full-match box-score statistic 'penaltyKickGoals' (ESPN). Post-match: descriptive only. |
| `post_home_penaltyKickShots` | POST | home team full-match box-score statistic 'penaltyKickShots' (ESPN). Post-match: descriptive only. |
| `post_home_possessionPct` | POST | home team full-match box-score statistic 'possessionPct' (ESPN). Post-match: descriptive only. |
| `post_home_redCards` | POST | home team full-match box-score statistic 'redCards' (ESPN). Post-match: descriptive only. |
| `post_home_saves` | POST | home team full-match box-score statistic 'saves' (ESPN). Post-match: descriptive only. |
| `post_home_shotsOnTarget` | POST | home team full-match box-score statistic 'shotsOnTarget' (ESPN). Post-match: descriptive only. |
| `post_home_shots_commentary` | POST | home team full-match shots counted from ESPN commentary (available all seasons; NaN if commentary incomplete). Post-match: descriptive only. |
| `post_home_sot_commentary` | POST | home team full-match sot counted from ESPN commentary (available all seasons; NaN if commentary incomplete). Post-match: descriptive only. |
| `post_home_totalCrosses` | POST | home team full-match box-score statistic 'totalCrosses' (ESPN). Post-match: descriptive only. |
| `post_home_totalLongBalls` | POST | home team full-match box-score statistic 'totalLongBalls' (ESPN). Post-match: descriptive only. |
| `post_home_totalPasses` | POST | home team full-match box-score statistic 'totalPasses' (ESPN). Post-match: descriptive only. |
| `post_home_totalShots` | POST | home team full-match box-score statistic 'totalShots' (ESPN). Post-match: descriptive only. |
| `post_home_totalTackles` | POST | home team full-match box-score statistic 'totalTackles' (ESPN). Post-match: descriptive only. |
| `post_home_wonCorners` | POST | home team full-match box-score statistic 'wonCorners' (ESPN). Post-match: descriptive only. |
| `post_home_yellowCards` | POST | home team full-match box-score statistic 'yellowCards' (ESPN). Post-match: descriptive only. |
| `goal_events_reconciled` | QA | 1 if goal events reproduce ESPN final score and (resolved) half scores. |
| `score_source` | PROV | Which source fields define the scores; flags ESPN linescore errors resolved by an independent source. |
| `linescore_conflict` | QA | 1 if ESPN per-period linescores disagreed with ESPN goal events. |
| `check_halves_match_linescores` | QA | Raw comparison of goal events to ESPN linescores (before adjudication). |
| `check_final_score_reconstructed` | QA | 1 if goal events sum to ESPN final score. |
| `n_goals_unattributed` | QA | Goal events without a team (should be 0). |
| `n_duplicate_goal_events_removed` | QA | Exact duplicate ESPN keyEvents (same period, clock, team, type and text) dropped for this match. |
| `n_goal_attribution_corrections` | QA | Own goals re-credited because ESPN's team credit contradicted ESPN's own text and the correction reproduces the final score. |
| `fd_matched` | QA | 1 if matched to a football-data.co.uk row (season+home+away, explicit name map). |
| `fd_odds_columns` | PROV | football-data.co.uk odds columns used: 'Avg' (market average, 2019-20+) or 'BbAv' (BetBrain average, to 2018-19). |
| `fd_date_diff_days` | QA | ESPN UTC date minus football-data date (days). |
| `fd_FTHG` | QA | football-data.co.uk full-time home goals (independent check). |
| `fd_FTAG` | QA | football-data.co.uk full-time away goals. |
| `fd_HTHG` | QA | football-data.co.uk half-time home goals. |
| `fd_HTAG` | QA | football-data.co.uk half-time away goals. |
| `elo_fixture_found` | QA | WC: 1 if the exact fixture was found in martj42 results (Elo taken from that row). |
| `apif_fixture_id` | ID | API-Football fixture id via the Hugging Face mirror (cross-check only). |
| `apif_home_formation` | QA | API-Football (HF mirror) home formation - cross-check only. |
| `apif_away_formation` | QA | API-Football away formation - cross-check only. |
| `formation_crosscheck_apif` | QA | 1 if both ESPN formations equal API-Football's. |
| `sb_match_id` | ID | StatsBomb match id (WC 2018/2022 only). |
| `sb_home_starting_formation` | QA | StatsBomb Starting XI formation (home), WC18/22. |
| `sb_away_starting_formation` | QA | StatsBomb Starting XI formation (away), WC18/22. |
| `formation_crosscheck_statsbomb` | QA | 1 if both ESPN formations equal StatsBomb's label (labels follow different conventions). |
| `sb_home_goals_incl_et` | QA | StatsBomb goal count for home side incl. ET. |
| `sb_away_goals_incl_et` | QA | StatsBomb goal count for away side incl. ET. |
| `commentary_shots_total` | QA | Number of attempts found in ESPN commentary (compare with post_*_totalShots). |
| `commentary_events_complete` | QA | 1 if ESPN commentary is complete enough to build time-varying shot/corner features; else those features are NaN. |
| `n_starters_home` | QA | Number of starters listed by ESPN (expect 11). |
| `n_starters_away` | QA | Number of starters listed by ESPN (expect 11). |
| `in_primary_sample` | QA | 1 if both formations valid AND goal events reconcile with official score. |
| `data_source` | PROV | Primary source of the row. |

## goal_events.csv

| column | role | description |
|---|---|---|
| `goal_id` | ID | match_id + '-G' + chronological goal number within match. |
| `match_id` | ID | Pipeline match key = 'ESPN-' + ESPN event id. Links all three tables. |
| `competition` | STRUCT | 'Premier League' or 'FIFA World Cup'. |
| `season` | STRUCT | EPL '2023-24'...'2026-27'; World Cup '2018','2022','2026'. Read as string. |
| `match_date` | STRUCT | Kickoff date in UTC (YYYY-MM-DD). |
| `goal_seq` | ID | Chronological goal order within match (1 = first goal). |
| `scoring_team` | STRUCT | Team credited with the goal (own goals credited to the benefiting team). |
| `conceding_team` | STRUCT | Team that conceded. |
| `scoring_team_id` | ID | ESPN team id credited with the goal. |
| `conceding_team_id` | ID | ESPN team id that conceded. |
| `scoring_side` | STRUCT | 'home' or 'away' side credited. |
| `goal_minute` | RESPONSE | Displayed match minute (base). 45+2 -> 45; 23' -> 23 (=elapsed 22:00-22:59). |
| `stoppage_time_minute` | RESPONSE | Added-time minute (45+2 -> 2; 0 if not in stoppage). |
| `original_goal_time` | RESPONSE | Exact source notation without quotes, e.g. '45+2', '90+4', '67'. |
| `clock_display` | PROV | Raw ESPN clock string, e.g. "90'+4'". |
| `goal_period` | STRUCT | 1H, 2H, ET1, ET2 (shoot-outs are excluded entirely). |
| `in_regulation` | STRUCT | 1 if 1H/2H (primary analysis). |
| `is_stoppage_time` | STRUCT | 1 if scored in added time. |
| `interval_number` | STRUCT | 1..6. Goals: interval of the goal (NA for extra time). |
| `goal_type` | STRUCT | own_goal, penalty, header, direct_free_kick, volley, other_shot (from ESPN type). |
| `goal_type_raw` | PROV | Raw ESPN type text, e.g. 'Penalty - Scored', 'Goal - Header', 'Own Goal'. |
| `penalty_indicator` | STRUCT | 1 = in-match penalty (shoot-out kicks are never included). |
| `own_goal_indicator` | STRUCT | 1 = own goal; credited to scoring_team (the beneficiary). |
| `home_team` | STRUCT | Home (or first-listed, for neutral WC venues) team, ESPN display name. |
| `away_team` | STRUCT | Away team, ESPN display name. |
| `home_starting_formation` | STRUCT | Home starting formation as published by ESPN (Opta-style label). Starting shape only. |
| `away_starting_formation` | STRUCT | Away starting formation (ESPN). |
| `scoring_team_starting_formation` | STRUCT | Scoring team's STARTING formation (ESPN) - not necessarily the shape at the time of the goal. |
| `opponent_starting_formation` | STRUCT | Opponent's starting formation (ESPN). |
| `active_formation_at_goal` | TV | WC 2018/22 only: scoring team's StatsBomb formation in force at the goal (latest Starting XI/Tactical Shift before the goal event). |
| `opponent_active_formation_at_goal` | TV | WC 2018/22 only: conceding team's StatsBomb formation at the goal. |
| `active_formation_source` | PROV | Source of active formation (StatsBomb) or empty. |
| `home_score_after` | POST | Home score immediately after this goal (incl. extra time ordering). |
| `away_score_after` | POST | Away score immediately after this goal. |
| `text_running_score_consistent` | QA | 1 if ESPN commentary running score equals reconstructed score. |
| `own_goal_text_check` | QA | Own goals: 1 if the player's team in ESPN text is the conceding team. |
| `goal_attribution_corrected` | QA | 1 if this own goal's team credit was corrected (see data_quality_report). |
| `sb_goal_minute` | QA | StatsBomb elapsed minute of the paired goal (pairing check). |
| `espn_play_id` | ID | Native ESPN play id of the goal. |
| `data_source` | PROV | Primary source of the row. |
| `in_primary_sample` | QA | 1 if both formations valid AND goal events reconcile with official score. |

## team_interval_panel.csv

| column | role | description |
|---|---|---|
| `panel_id` | ID | match_id-team_id-I<interval_number>. |
| `match_id` | ID | Pipeline match key = 'ESPN-' + ESPN event id. Links all three tables. |
| `competition` | STRUCT | 'Premier League' or 'FIFA World Cup'. |
| `season` | STRUCT | EPL '2023-24'...'2026-27'; World Cup '2018','2022','2026'. Read as string. |
| `match_date` | STRUCT | Kickoff date in UTC (YYYY-MM-DD). |
| `stage` | STRUCT | 'League' (EPL), 'Group' or 'Knockout' (WC; derived from group-stage end date). |
| `team` | STRUCT | Panel team. |
| `team_id` | ID | ESPN team id of the panel team. |
| `opponent` | STRUCT | Panel opponent. |
| `opponent_id` | ID | ESPN team id of opponent. |
| `home_indicator` | STRUCT | 1 = panel team is ESPN 'home' side. At World Cups this is administrative; use with neutral_site/team_is_host_country. |
| `neutral_site` | STRUCT | 1 = neutral venue. EPL: 0. WC: from martj42 fixture record (ESPN's flag is unreliable for WCs). |
| `team_is_host_country` | STRUCT | WC only: panel team is playing in its own country. |
| `interval_number` | STRUCT | 1..6. Goals: interval of the goal (NA for extra time). |
| `interval_label` | STRUCT | 0-15, 15-30, 30-45+, 45-60, 60-75, 75-90+. |
| `interval_start` | STRUCT | Elapsed-minute lower bound (inclusive). |
| `interval_end` | STRUCT | Elapsed-minute nominal upper bound (exclusive; intervals 3 and 6 also include stoppage). |
| `interval_includes_stoppage` | STRUCT | 1 for intervals 3 and 6. |
| `match_minute` | TV | Elapsed minute at interval start (0,15,30,45,60,75). |
| `starting_formation` | STRUCT | Panel team's starting formation (ESPN). |
| `opponent_starting_formation` | STRUCT | Opponent's starting formation (ESPN). |
| `formation_matchup` | STRUCT | Ordered matchup string. match_level: 'home vs away'; panel: 'team vs opponent'. |
| `starting_formation_group` | STRUCT | Panel team's formation group. |
| `opponent_formation_group` | STRUCT | Opponent's formation group. |
| `formation_group_matchup` | STRUCT | Ordered group matchup (match_level: home vs away; panel: team vs opponent). |
| `back_line` | STRUCT | Panel team's back-line count. |
| `opponent_back_line` | STRUCT | Opponent back-line count. |
| `n_forwards` | STRUCT | Panel team's forward count. |
| `opponent_n_forwards` | STRUCT | Opponent forward count. |
| `goals_scored_in_interval` | RESPONSE | Count of goals the panel team scored in the interval (can exceed 1). |
| `goals_conceded_in_interval` | RESPONSE | Count of goals conceded in the interval. |
| `scored_at_least_one_goal` | RESPONSE | Binary: 1 if goals_scored_in_interval >= 1. |
| `conceded_at_least_one_goal` | RESPONSE | Binary: 1 if goals_conceded_in_interval >= 1. |
| `score_difference_at_interval_start` | TV | Team goals minus opponent goals before the interval begins. |
| `goals_for_before_interval` | TV | Team goals scored before the interval. |
| `goals_against_before_interval` | TV | Team goals conceded before the interval. |
| `tv_own_shot_any_before_interval` | TV | Cumulative own shot_any recorded before the interval begins (ESPN commentary / keyEvents). shot_any = all attempts; shot_ot = on target incl. goals; red = red cards incl. second yellows; sub = substitutions. |
| `tv_own_shot_ot_before_interval` | TV | Cumulative own shot_ot recorded before the interval begins (ESPN commentary / keyEvents). shot_any = all attempts; shot_ot = on target incl. goals; red = red cards incl. second yellows; sub = substitutions. |
| `tv_own_corner_before_interval` | TV | Cumulative own corner recorded before the interval begins (ESPN commentary / keyEvents). shot_any = all attempts; shot_ot = on target incl. goals; red = red cards incl. second yellows; sub = substitutions. |
| `tv_own_red_before_interval` | TV | Cumulative own red recorded before the interval begins (ESPN commentary / keyEvents). shot_any = all attempts; shot_ot = on target incl. goals; red = red cards incl. second yellows; sub = substitutions. |
| `tv_own_sub_before_interval` | TV | Cumulative own sub recorded before the interval begins (ESPN commentary / keyEvents). shot_any = all attempts; shot_ot = on target incl. goals; red = red cards incl. second yellows; sub = substitutions. |
| `tv_opp_shot_any_before_interval` | TV | Cumulative opp shot_any recorded before the interval begins (ESPN commentary / keyEvents). shot_any = all attempts; shot_ot = on target incl. goals; red = red cards incl. second yellows; sub = substitutions. |
| `tv_opp_shot_ot_before_interval` | TV | Cumulative opp shot_ot recorded before the interval begins (ESPN commentary / keyEvents). shot_any = all attempts; shot_ot = on target incl. goals; red = red cards incl. second yellows; sub = substitutions. |
| `tv_opp_corner_before_interval` | TV | Cumulative opp corner recorded before the interval begins (ESPN commentary / keyEvents). shot_any = all attempts; shot_ot = on target incl. goals; red = red cards incl. second yellows; sub = substitutions. |
| `tv_opp_red_before_interval` | TV | Cumulative opp red recorded before the interval begins (ESPN commentary / keyEvents). shot_any = all attempts; shot_ot = on target incl. goals; red = red cards incl. second yellows; sub = substitutions. |
| `tv_opp_sub_before_interval` | TV | Cumulative opp sub recorded before the interval begins (ESPN commentary / keyEvents). shot_any = all attempts; shot_ot = on target incl. goals; red = red cards incl. second yellows; sub = substitutions. |
| `commentary_events_complete` | QA | 1 if ESPN commentary is complete enough to build time-varying shot/corner features; else those features are NaN. |
| `tv_man_advantage_at_interval_start` | TV | Opponent red cards minus own red cards before the interval (>0 = numerical advantage). |
| `exposure_observed_minutes` | EXPOSURE | 15, or 15 + observed added time for intervals 3/6 (from ESPN half-end clock). Known only after the interval: use as log-offset, not as predictor. |
| `pre_odds_p_team_win` | PRE | EPL: implied P(panel team wins). |
| `pre_odds_p_draw` | PRE | EPL: implied P(draw). |
| `pre_odds_p_opponent_win` | PRE | EPL: implied P(opponent wins). |
| `pre_odds_p_over25` | PRE | EPL: implied P(over 2.5 goals) from Avg>2.5 / Avg<2.5 odds. Strong baseline for goal totals. |
| `pre_elo_team` | PRE | WC: panel team pre-match Elo. |
| `pre_elo_opponent` | PRE | WC: opponent pre-match Elo. |
| `pre_team_gf_last10` | PRE | Panel version of pre_<side>_gf_last10 for the team. |
| `pre_opp_gf_last10` | PRE | Panel version of pre_<side>_gf_last10 for the opp. |
| `pre_team_ga_last10` | PRE | Panel version of pre_<side>_ga_last10 for the team. |
| `pre_opp_ga_last10` | PRE | Panel version of pre_<side>_ga_last10 for the opp. |
| `pre_team_points_last10` | PRE | Panel version of pre_<side>_points_last10 for the team. |
| `pre_opp_points_last10` | PRE | Panel version of pre_<side>_points_last10 for the opp. |
| `pre_team_possession_last10` | PRE | Panel version of pre_<side>_possession_last10 for the team. |
| `pre_opp_possession_last10` | PRE | Panel version of pre_<side>_possession_last10 for the opp. |
| `pre_team_passes_last10` | PRE | Panel version of pre_<side>_passes_last10 for the team. |
| `pre_opp_passes_last10` | PRE | Panel version of pre_<side>_passes_last10 for the opp. |
| `pre_team_long_ball_share_last10` | PRE | Panel version of pre_<side>_long_ball_share_last10 for the team. |
| `pre_opp_long_ball_share_last10` | PRE | Panel version of pre_<side>_long_ball_share_last10 for the opp. |
| `pre_team_shots_last10` | PRE | Panel version of pre_<side>_shots_last10 for the team. |
| `pre_opp_shots_last10` | PRE | Panel version of pre_<side>_shots_last10 for the opp. |
| `pre_team_sot_last10` | PRE | Panel version of pre_<side>_sot_last10 for the team. |
| `pre_opp_sot_last10` | PRE | Panel version of pre_<side>_sot_last10 for the opp. |
| `pre_team_shots_comm_last10` | PRE | Panel version of pre_<side>_shots_comm_last10 for the team. |
| `pre_opp_shots_comm_last10` | PRE | Panel version of pre_<side>_shots_comm_last10 for the opp. |
| `pre_team_sot_comm_last10` | PRE | Panel version of pre_<side>_sot_comm_last10 for the team. |
| `pre_opp_sot_comm_last10` | PRE | Panel version of pre_<side>_sot_comm_last10 for the opp. |
| `pre_team_n_prior_matches` | PRE | Number of prior matches (<=10) behind the team's rolling features. |
| `pre_opp_n_prior_matches` | PRE | Same for opponent. |
| `tv_active_formation_at_interval_start` | TV | WC 2018/22 only: team's StatsBomb formation in force at interval start (after any Tactical Shift). StatsBomb labels differ in convention from ESPN. |
| `tv_opp_active_formation_at_interval_start` | TV | WC 2018/22 only: opponent's StatsBomb formation in force at interval start. |
| `data_source` | PROV | Primary source of the row. |
