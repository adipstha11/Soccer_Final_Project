# Data quality report

Generated 2026-11-22 | data cut-off 2026-11-22

## 1. Totals

- match_level.csv: **4141 matches** (3909 EPL, 232 World Cup)
- goal_events.csv: **11721 goals** (11706 in regulation, 15 in extra time; shoot-out kicks excluded)
- team_interval_panel.csv: **49656 team-interval rows** (4138 matches x 2 teams x 6 intervals)
- primary sample (both formations + reconciled goal events): **4138 / 4141** matches
- goalless (0-0) matches retained: 256

## 2. Coverage by competition and season

| competition | season | expected_matches | matches_listed_by_source | completed_by_cutoff | matches_downloaded | matches_parsed | both_starting_formations | complete_goal_events | both_requirements (primary sample) | goals_total_all_periods | validated_regulation_goals_primary | goals_per_match_primary | pct_missing_formation | pct_goal_events_unreconciled | pct_missing_boxscore | pct_missing_prematch_odds | pct_missing_prematch_elo | formation_agreement_apif_pct | formation_agreement_statsbomb_pct | goals_with_active_formation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Premier League | 2016-17 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 1064 | 1064 | 2.800 | 0 | 0 | 97.110 | 0 | 100 | 95.500 |  | 0 |
| Premier League | 2017-18 | 380 | 380 | 380 | 380 | 380 | 379 | 380 | 379 | 1018 | 1017 | 2.683 | 0.260 | 0 | 0 | 0 | 100 | 97.900 |  | 0 |
| Premier League | 2018-19 | 380 | 380 | 380 | 380 | 380 | 378 | 380 | 378 | 1072 | 1066 | 2.820 | 0.530 | 0 | 0.260 | 0 | 100 | 94.500 |  | 0 |
| Premier League | 2019-20 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 1034 | 1034 | 2.721 | 0 | 0 | 1.050 | 0 | 100 | 97.600 |  | 0 |
| Premier League | 2020-21 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 1024 | 1024 | 2.695 | 0 | 0 | 2.110 | 0 | 100 | 96.300 |  | 0 |
| Premier League | 2021-22 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 1071 | 1071 | 2.818 | 0 | 0 | 7.370 | 0 | 100 | 96.100 |  | 0 |
| Premier League | 2022-23 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 1084 | 1084 | 2.853 | 0 | 0 | 22.370 | 0 | 100 | 93.900 |  | 0 |
| Premier League | 2023-24 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 1246 | 1246 | 3.279 | 0 | 0 | 2.630 | 0 | 100 | 96.800 |  | 0 |
| Premier League | 2024-25 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 1115 | 1115 | 2.934 | 0 | 0 | 3.160 | 0 | 100 | 98.700 |  | 0 |
| Premier League | 2025-26 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 380 | 1045 | 1045 | 2.750 | 0 | 0 | 0 | 0 | 100 | 97.100 |  | 0 |
| Premier League | 2026-27 |  | 109 | 109 | 109 | 109 | 109 | 109 | 109 | 299 | 299 | 2.743 | 0 | 0 | 0 | 8.260 | 100 |  |  | 0 |
| FIFA World Cup | 2018 | 64 | 64 | 64 | 64 | 64 | 64 | 64 | 64 | 169 | 166 | 2.594 | 0 | 0 | 0 | 100 | 0 | 95.300 | 56.200 | 169 |
| FIFA World Cup | 2022 | 64 | 64 | 64 | 64 | 64 | 64 | 64 | 64 | 172 | 168 | 2.625 | 0 | 0 | 0 | 100 | 0 | 87.500 | 70.300 | 172 |
| FIFA World Cup | 2026 | 104 | 104 | 104 | 104 | 104 | 104 | 104 | 104 | 308 | 300 | 2.885 | 0 | 0 | 0 | 100 | 0 | 98.800 |  | 0 |

## 3. Automated validation checks

51/51 checks pass. Checks marked (info) report counts.

| check | passed | n_violations | n_checked | detail |
|---|---|---|---|---|
| unique match_id | 1 | 0 | 4141 |  |
| unique goal_id | 1 | 0 | 11721 |  |
| no duplicate fixtures (competition, season, home, away) | 1 | 0 | 4141 | World Cup pairings may legitimately repeat and are keyed by date |
| complete seasons have the expected number of distinct matches (380 EPL; 64/64/104 WC) | 1 | 0 | 13 |  |
| each complete EPL season has 380 distinct home/away pairings | 1 | 0 | 10 |  |
| each complete EPL season: 20 teams x 38 matches | 1 | 0 | 10 |  |
| goal events in chronological order within each match | 1 | 0 | 3887 |  |
| kickoff dates fall inside the season window | 1 | 0 | 4141 |  |
| no duplicate goal events | 1 | 0 | 11721 |  |
| unique panel_id | 1 | 0 | 49656 |  |
| formation labels valid (d-d-.. summing to 10 outfielders) | 1 | 0 | 8276 |  |
| every valid formation label has an explicit group (info: 'other' labels) | 1 | 0 | 8282 | 2 team-matches in 'other': ['4-2-4-0'] |
| formation group present whenever formation valid | 1 | 0 | 4141 |  |
| valid competition/season values | 1 | 0 | 4141 |  |
| match dates within cut-off | 1 | 0 | 4141 |  |
| goal minute consistent with period (stoppage only at 45/90/105/120) | 1 | 0 | 11721 |  |
| stoppage-time notation preserved (e.g. 45+2, 90+4) | 1 | 0 | 11721 |  |
| goal assigned to exactly one participating team | 1 | 0 | 11721 |  |
| own goals credited to the opponent of the player's team (text check) | 1 | 0 | 409 | 1 own goals without parseable text |
| penalty indicator <-> goal_type consistent | 1 | 0 | 11721 |  |
| no shoot-out goals in goal_events | 1 | 0 | 11721 |  |
| shoot-out matches: event goals == score excl. shoot-out | 1 | 0 | 13 |  |
| regular-time scores exclude extra time and shoot-outs | 1 | 0 | 4141 |  |
| regulation score reconstructed from goal events (primary sample) | 1 | 0 | 4138 |  |
| half-time score reconstructed from goal events (primary sample) | 1 | 0 | 4138 |  |
| ALL matches: goal events reconcile with official score (info) | 1 | 0 | 4141 |  |
| ESPN linescore conflicts resolved by an independent source (info) | 1 | 0 | 6 | ESPN-498147: ESPN goal events; ESPN linescore error, split confirmed by StatsBomb; ESPN-498140: ESPN goal events; ESPN linescore error, split confirmed by StatsBomb; ESPN-480597: ESPN goal events; ESPN linescore error, split confirmed by football-data.co.uk; ESPN-740675: ESPN goal events; ESPN linescore error, split confirmed by football-data.co.uk; ESPN-740876: ESPN goal events; ESPN linescore error, split confirmed by football-data.co.uk; ESPN-740882: ESPN goal events; ESPN linescore error, split confirmed by football-data.co.uk |
| 0-0 matches retained (info: count) | 1 | 0 | 4138 | 256 goalless matches |
| EPL full-time score == football-data.co.uk | 1 | 0 | 3900 |  |
| EPL half-time score == football-data.co.uk | 1 | 0 | 3900 |  |
| football-data fixture date within 1 day of ESPN kickoff | 1 | 0 | 3900 |  |
| WC 2018/22 goals (incl. ET) == StatsBomb | 1 | 0 | 128 |  |
| goal interval assignment (re-derived) | 1 | 0 | 11706 |  |
| extra-time goals have no regulation interval | 1 | 0 | 15 |  |
| first-half stoppage goals in interval 3, second-half in 6 | 1 | 0 | 1130 |  |
| 12 panel rows per eligible match | 1 | 0 | 4138 |  |
| panel covers exactly the primary-sample matches | 1 | 0 | 4138 |  |
| each team has intervals 1..6 once | 1 | 0 | 8276 |  |
| panel goals sum to regulation score | 1 | 0 | 8276 |  |
| binary response == (count > 0) | 1 | 0 | 49656 |  |
| panel mirror: scored(team) == conceded(opponent) | 1 | 0 | 49656 |  |
| leakage: score diff at interval start uses only earlier intervals | 1 | 0 | 49656 |  |
| leakage: time-varying counts are zero (or NaN if source incomplete) at kickoff | 1 | 0 | 8276 |  |
| commentary-derived features NaN exactly when commentary incomplete | 1 | 0 | 49656 | 9 matches with incomplete commentary |
| leakage: time-varying counts non-decreasing | 1 | 0 | 49656 |  |
| leakage: no post-match columns in panel | 1 | 0 | 80 |  |
| leakage: pre-match rolling gf == independent SQL (prior 10, <=365 days) | 1 | 0 | 8282 |  |
| leakage: pre-match rolling possession == independent SQL (prior 10, <=365 days) | 1 | 0 | 8282 |  |
| leakage: rolling-window match counts == independent SQL | 1 | 0 | 8282 |  |
| leakage: a team's first match in group has no rolling history | 1 | 0 | 8282 |  |
| WC18/22 panel rows have an active formation at interval start | 1 | 0 | 1536 |  |

## 4. Conflicts found and how they were handled

**ESPN per-period linescores vs goal events (6 matches).** In each case ESPN's goal events reproduce ESPN's final score, while the per-period `linescores` field is wrong (all zeros, a value of -1, or goals assigned to the wrong half). The goal-event split was accepted only because an independent source confirmed it (football-data.co.uk HT/FT for EPL, StatsBomb period-level goals for WC). Raw data are untouched; the decision is recorded in `score_source` and `linescore_conflict`.

| match_id | competition | season | home_team | away_team | home_goals | away_goals | half_time_home_goals | half_time_away_goals | score_source |
|---|---|---|---|---|---|---|---|---|---|
| ESPN-498147 | FIFA World Cup | 2018 | Colombia | England | 1 | 1 | 0 | 0 | ESPN goal events; ESPN linescore error, split confirmed by StatsBomb |
| ESPN-498140 | FIFA World Cup | 2018 | Belgium | England | 2 | 0 | 1 | 0 | ESPN goal events; ESPN linescore error, split confirmed by StatsBomb |
| ESPN-480597 | Premier League | 2017-18 | Manchester City | Brighton & Hove Albion | 3 | 1 | 2 | 1 | ESPN goal events; ESPN linescore error, split confirmed by football-data.co.uk |
| ESPN-740675 | Premier League | 2025-26 | West Ham United | Brentford | 0 | 2 | 0 | 1 | ESPN goal events; ESPN linescore error, split confirmed by football-data.co.uk |
| ESPN-740876 | Premier League | 2025-26 | Aston Villa | Chelsea | 1 | 4 | 1 | 2 | ESPN goal events; ESPN linescore error, split confirmed by football-data.co.uk |
| ESPN-740882 | Premier League | 2025-26 | Manchester City | Nottingham Forest | 2 | 2 | 1 | 0 | ESPN goal events; ESPN linescore error, split confirmed by football-data.co.uk |

**Duplicate goal events (1 match(es), 4 rows dropped).** ESPN listed the same goal twice, with identical period, clock, team, type and text (which includes the running score). The duplicate copy is dropped. Matches: ESPN-450867.

**Own-goal credit contradicting ESPN's own text (1 goal(s)).** ESPN credited an own goal to the own-goal scorer's team, although its text says "Own Goal by <player>, <that team>". The goal was re-credited to the opponent because that reproduces ESPN's final score. Football-data.co.uk FT/HT scores agree. Matches: ESPN-450779.

**Matches without starting formations (3).** ESPN's roster has no formation label for these matches (players' position slots exist, but are not converted into a label). They stay in match_level.csv and goal_events.csv with `in_primary_sample = 0` and are excluded from the panel. API-Football labels, where present, are in `apif_*_formation` for sensitivity checks only. Matches: ESPN-480711, ESPN-513780, ESPN-513579.

**Empty ESPN box scores (517 matches).** ESPN returned all-zero placeholder statistics; these are set to missing (not zero). Goal events and formations for these matches are complete, so they stay in the sample; post-match statistics and the rolling style features that depend on them are NaN-aware.

| competition | season | matches_without_box_score |
|---|---|---|
| Premier League | 2016-17 | 369 |
| Premier League | 2018-19 | 1 |
| Premier League | 2019-20 | 4 |
| Premier League | 2020-21 | 8 |
| Premier League | 2021-22 | 28 |
| Premier League | 2022-23 | 85 |
| Premier League | 2023-24 | 10 |
| Premier League | 2024-25 | 12 |

**Commentary completeness.** Time-varying shot and corner counts come from ESPN commentary. For each match the commentary attempt count was compared with the box-score total (tolerance: max(4 shots, 15%)). 10 match(es) fail (ESPN-480711, ESPN-480597, ESPN-513805, ESPN-513790, ESPN-513793, ESPN-513794, ESPN-513795, ESPN-513796, ESPN-605885, ESPN-740855); their commentary-derived features are NaN, not 0. Red cards and substitutions come from keyEvents and are unaffected.

**ESPN neutral-site flag.** ESPN reports `neutralSite = False` for every World Cup match, so it is not used. `neutral_site` and host-country flags for World Cup matches come from the martj42 fixture record.

**football-data.co.uk 2026-27 lag.** 9 recent EPL matches are not yet in the football-data.co.uk file, so their pre-match odds are missing. Re-run with `--refresh-current-season` later to take a new dated snapshot.

## 5. Formation label agreement across providers

Formation labels are a provider's interpretation of the average shape, not an objective measurement.

- ESPN vs API-Football (Hugging Face mirror), team-level exact agreement: **98.0%** over 4004 matches. The two may share an upstream provider, so this is a consistency check rather than fully independent validation.
- ESPN vs StatsBomb (WC 2018/22), team-level exact agreement: **79.3%**; back-line (number of defenders) agreement **96.1%**. Most disagreements are naming conventions (3-4-2-1 vs 3-4-3, 5-3-2 vs 3-5-2, 4-2-3-1 vs 4-5-1).

| ESPN | StatsBomb | team_matches |
|---|---|---|
| 3-4-2-1 | 3-4-3 | 10 |
| 3-1-4-2 | 3-5-2 | 8 |
| 5-3-2 | 3-5-2 | 6 |
| 4-2-3-1 | 4-5-1 | 4 |
| 4-2-3-1 | 4-3-3 | 4 |
| 5-4-1 | 3-4-3 | 3 |
| 4-1-2-1-2 | 4-4-2 | 2 |
| 4-3-3 | 4-1-4-1 | 2 |
| 4-2-3-1 | 4-4-2 | 2 |
| 4-3-3 | 4-3-2-1 | 1 |
| 4-2-3-1 | 4-3-2-1 | 1 |
| 3-4-2-1 | 5-4-1 | 1 |
| 4-3-1-2 | 4-3-3 | 1 |
| 4-1-2-1-2 | 4-3-3 | 1 |
| 4-4-1-1 | 4-5-1 | 1 |

## 6. Formation frequencies (team-matches, primary sample)

| formation | FIFA World Cup | Premier League | total |
|---|---|---|---|
| 4-2-3-1 | 152 | 2647 | 2799 |
| 4-3-3 | 86 | 1490 | 1576 |
| 4-4-2 | 68 | 755 | 823 |
| 3-4-2-1 | 42 | 722 | 764 |
| 4-1-4-1 | 39 | 345 | 384 |
| 4-4-1-1 | 10 | 340 | 350 |
| 3-5-2 | 8 | 332 | 340 |
| 3-4-3 | 5 | 255 | 260 |
| 5-4-1 | 15 | 170 | 185 |
| 5-3-2 | 12 | 124 | 136 |
| 3-4-1-2 | 6 | 116 | 122 |
| 4-5-1 | 0 | 112 | 112 |
| 4-1-2-1-2 | 4 | 70 | 74 |
| 4-2-2-2 | 0 | 74 | 74 |
| 3-5-1-1 | 0 | 68 | 68 |
| 4-3-1-2 | 3 | 61 | 64 |
| 3-1-4-2 | 11 | 36 | 47 |
| 4-3-2-1 | 1 | 41 | 42 |
| 3-2-4-1 | 0 | 24 | 24 |
| 4-1-3-2 | 2 | 12 | 14 |
| 3-3-3-1 | 0 | 12 | 12 |
| 3-4-3-d | 0 | 4 | 4 |
| 4-2-4-0 | 0 | 2 | 2 |

## 7. Formation matchup frequencies (unordered pairs, primary sample)

| formation_pair_unordered | FIFA World Cup | Premier League | total |
|---|---|---|---|
| 4-2-3-1 \| 4-2-3-1 | 25 | 510 | 535 |
| 4-2-3-1 \| 4-3-3 | 27 | 477 | 504 |
| 3-4-2-1 \| 4-2-3-1 | 13 | 264 | 277 |
| 4-2-3-1 \| 4-4-2 | 24 | 220 | 244 |
| 4-3-3 \| 4-4-2 | 14 | 152 | 166 |
| 4-1-4-1 \| 4-2-3-1 | 14 | 135 | 149 |
| 4-3-3 \| 4-3-3 | 6 | 141 | 147 |
| 3-4-2-1 \| 4-3-3 | 10 | 110 | 120 |
| 4-2-3-1 \| 4-4-1-1 | 6 | 100 | 106 |
| 3-5-2 \| 4-2-3-1 | 0 | 106 | 106 |
| 4-3-3 \| 4-4-1-1 | 3 | 88 | 91 |
| 3-5-2 \| 4-3-3 | 3 | 75 | 78 |
| 4-2-3-1 \| 5-4-1 | 9 | 61 | 70 |
| 3-4-3 \| 4-2-3-1 | 1 | 66 | 67 |
| 4-1-4-1 \| 4-3-3 | 5 | 60 | 65 |
| 3-4-2-1 \| 4-4-2 | 5 | 57 | 62 |
| 3-4-2-1 \| 3-4-2-1 | 3 | 52 | 55 |
| 4-1-4-1 \| 4-4-2 | 6 | 47 | 53 |
| 4-4-2 \| 4-4-2 | 5 | 40 | 45 |
| 3-4-3 \| 4-3-3 | 3 | 41 | 44 |
| 4-3-3 \| 5-4-1 | 3 | 40 | 43 |
| 4-3-3 \| 5-3-2 | 3 | 35 | 38 |
| 4-2-3-1 \| 4-5-1 | 0 | 37 | 37 |
| 4-4-1-1 \| 4-4-2 | 0 | 36 | 36 |
| 4-3-3 \| 4-5-1 | 0 | 34 | 34 |
| 3-4-2-1 \| 3-5-2 | 1 | 32 | 33 |
| 3-4-1-2 \| 4-2-3-1 | 2 | 30 | 32 |
| 4-2-3-1 \| 5-3-2 | 1 | 30 | 31 |
| 3-4-3 \| 4-4-2 | 0 | 31 | 31 |
| 3-4-2-1 \| 4-4-1-1 | 0 | 26 | 26 |
| 3-5-2 \| 4-4-2 | 2 | 24 | 26 |
| 3-4-2-1 \| 5-3-2 | 1 | 21 | 22 |
| 4-1-4-1 \| 4-4-1-1 | 1 | 20 | 21 |
| 4-2-2-2 \| 4-2-3-1 | 0 | 21 | 21 |
| 3-4-2-1 \| 4-1-4-1 | 2 | 18 | 20 |
| 3-4-3 \| 3-5-2 | 0 | 20 | 20 |
| 3-4-1-2 \| 4-3-3 | 1 | 19 | 20 |
| 4-4-2 \| 5-4-1 | 0 | 19 | 19 |
| 3-4-2-1 \| 3-4-3 | 1 | 18 | 19 |
| 3-4-1-2 \| 4-4-2 | 0 | 19 | 19 |
| 4-2-3-1 \| 4-3-1-2 | 1 | 17 | 18 |
| 4-1-2-1-2 \| 4-2-3-1 | 2 | 15 | 17 |
| 4-1-2-1-2 \| 4-3-3 | 0 | 16 | 16 |
| 3-5-1-1 \| 4-2-3-1 | 0 | 15 | 15 |
| 3-4-1-2 \| 3-4-2-1 | 1 | 14 | 15 |
| 4-4-1-1 \| 4-4-1-1 | 0 | 15 | 15 |
| 3-5-1-1 \| 4-3-3 | 0 | 14 | 14 |
| 4-2-2-2 \| 4-3-3 | 0 | 14 | 14 |
| 4-2-3-1 \| 4-3-2-1 | 1 | 13 | 14 |
| 4-4-2 \| 5-3-2 | 3 | 10 | 13 |
| 4-4-2 \| 4-5-1 | 0 | 13 | 13 |
| 3-4-2-1 \| 5-4-1 | 0 | 13 | 13 |
| 3-4-2-1 \| 3-5-1-1 | 0 | 12 | 12 |
| 4-3-1-2 \| 4-3-3 | 0 | 12 | 12 |
| 4-1-4-1 \| 5-4-1 | 1 | 9 | 10 |
| 4-3-1-2 \| 4-4-2 | 1 | 9 | 10 |
| 3-5-2 \| 4-1-4-1 | 0 | 10 | 10 |
| 3-2-4-1 \| 4-2-3-1 | 0 | 10 | 10 |
| 3-3-3-1 \| 4-4-2 | 0 | 9 | 9 |
| 3-4-3 \| 4-1-4-1 | 0 | 9 | 9 |
| 3-4-3 \| 5-4-1 | 0 | 9 | 9 |
| 3-4-3 \| 3-4-3 | 0 | 9 | 9 |
| 3-5-2 \| 3-5-2 | 0 | 9 | 9 |
| 4-2-2-2 \| 4-4-2 | 0 | 9 | 9 |
| 3-5-2 \| 4-4-1-1 | 0 | 9 | 9 |
| 3-1-4-2 \| 4-3-3 | 2 | 6 | 8 |
| 3-1-4-2 \| 4-4-2 | 1 | 7 | 8 |
| 3-1-4-2 \| 3-4-2-1 | 2 | 6 | 8 |
| 3-4-1-2 \| 3-5-2 | 0 | 8 | 8 |
| 3-5-2 \| 4-1-2-1-2 | 1 | 7 | 8 |
| 3-4-2-1 \| 4-3-1-2 | 0 | 8 | 8 |
| 4-3-2-1 \| 4-3-3 | 0 | 8 | 8 |
| 4-1-4-1 \| 4-1-4-1 | 3 | 4 | 7 |
| 3-4-3 \| 3-5-1-1 | 0 | 7 | 7 |
| 3-1-4-2 \| 4-2-3-1 | 0 | 7 | 7 |
| 4-1-2-1-2 \| 4-4-2 | 1 | 5 | 6 |
| 3-5-1-1 \| 3-5-2 | 0 | 6 | 6 |
| 4-2-2-2 \| 4-4-1-1 | 0 | 6 | 6 |
| 3-4-3 \| 4-2-2-2 | 0 | 6 | 6 |
| 3-4-3 \| 5-3-2 | 0 | 6 | 6 |
| 3-4-3 \| 4-5-1 | 0 | 6 | 6 |
| 3-4-1-2 \| 5-3-2 | 2 | 4 | 6 |
| 3-5-2 \| 5-4-1 | 1 | 4 | 5 |
| 3-4-2-1 \| 4-1-2-1-2 | 0 | 5 | 5 |
| 4-1-2-1-2 \| 4-1-4-1 | 0 | 5 | 5 |
| 3-4-3 \| 4-4-1-1 | 0 | 5 | 5 |
| 4-1-4-1 \| 5-3-2 | 1 | 4 | 5 |
| 3-4-3 \| 4-1-2-1-2 | 0 | 5 | 5 |
| 3-4-1-2 \| 4-1-4-1 | 0 | 4 | 4 |
| 3-5-2 \| 5-3-2 | 0 | 4 | 4 |
| 3-1-4-2 \| 4-1-4-1 | 3 | 1 | 4 |
| 3-4-2-1 \| 4-3-2-1 | 0 | 4 | 4 |
| 3-2-4-1 \| 4-3-3 | 0 | 4 | 4 |
| 4-1-3-2 \| 4-2-3-1 | 1 | 3 | 4 |
| 4-1-4-1 \| 4-2-2-2 | 0 | 4 | 4 |
| 4-1-4-1 \| 4-3-2-1 | 0 | 4 | 4 |
| 4-2-2-2 \| 5-4-1 | 0 | 3 | 3 |
| 4-1-2-1-2 \| 4-5-1 | 0 | 3 | 3 |
| 4-1-4-1 \| 4-5-1 | 0 | 3 | 3 |
| 4-4-1-1 \| 4-5-1 | 0 | 3 | 3 |
| 3-1-4-2 \| 3-4-1-2 | 0 | 3 | 3 |
| 3-5-1-1 \| 4-4-1-1 | 0 | 3 | 3 |
| 3-4-1-2 \| 4-4-1-1 | 0 | 3 | 3 |
| 3-5-2 \| 4-2-2-2 | 0 | 3 | 3 |
| 3-4-2-1 \| 4-2-2-2 | 0 | 3 | 3 |
| 3-4-2-1 \| 4-5-1 | 0 | 3 | 3 |
| 3-4-3 \| 4-3-1-2 | 0 | 3 | 3 |
| 3-1-4-2 \| 5-4-1 | 1 | 1 | 2 |
| 4-3-2-1 \| 5-3-2 | 0 | 2 | 2 |
| 4-2-2-2 \| 4-5-1 | 0 | 2 | 2 |
| 3-4-1-2 \| 5-4-1 | 0 | 2 | 2 |
| 3-4-2-1 \| 4-1-3-2 | 0 | 2 | 2 |
| 3-2-4-1 \| 4-4-2 | 0 | 2 | 2 |
| 3-5-2 \| 4-5-1 | 0 | 2 | 2 |
| 4-3-2-1 \| 4-5-1 | 0 | 2 | 2 |
| 4-3-2-1 \| 4-4-2 | 0 | 2 | 2 |
| 3-4-1-2 \| 3-4-3 | 0 | 2 | 2 |
| 4-1-2-1-2 \| 4-1-2-1-2 | 0 | 2 | 2 |
| 3-5-1-1 \| 4-1-4-1 | 0 | 2 | 2 |
| 3-2-4-1 \| 5-4-1 | 0 | 2 | 2 |
| 3-5-1-1 \| 4-4-2 | 0 | 2 | 2 |
| 4-1-3-2 \| 5-4-1 | 0 | 2 | 2 |
| 4-4-1-1 \| 5-3-2 | 0 | 2 | 2 |
| 4-1-3-2 \| 4-4-2 | 1 | 1 | 2 |
| 4-4-1-1 \| 5-4-1 | 0 | 2 | 2 |
| 4-1-3-2 \| 4-3-3 | 0 | 2 | 2 |
| 3-1-4-2 \| 4-3-1-2 | 1 | 1 | 2 |
| 4-3-1-2 \| 5-3-2 | 0 | 2 | 2 |
| 3-1-4-2 \| 3-5-2 | 0 | 2 | 2 |
| 3-5-2 \| 4-3-1-2 | 0 | 2 | 2 |
| 4-1-4-1 \| 4-3-1-2 | 0 | 2 | 2 |
| 4-3-2-1 \| 5-4-1 | 0 | 1 | 1 |
| 4-3-2-1 \| 4-4-1-1 | 0 | 1 | 1 |
| 4-3-1-2 \| 4-5-1 | 0 | 1 | 1 |
| 3-2-4-1 \| 4-3-2-1 | 0 | 1 | 1 |
| 3-2-4-1 \| 5-3-2 | 0 | 1 | 1 |
| 3-2-4-1 \| 4-4-1-1 | 0 | 1 | 1 |
| 4-3-1-2 \| 4-4-1-1 | 0 | 1 | 1 |
| 3-2-4-1 \| 4-2-4-0 | 0 | 1 | 1 |
| 3-2-4-1 \| 3-4-3 | 0 | 1 | 1 |
| 3-2-4-1 \| 3-4-2-1 | 0 | 1 | 1 |
| 3-1-4-2 \| 5-3-2 | 1 | 0 | 1 |
| 3-1-4-2 \| 4-2-2-2 | 0 | 1 | 1 |
| 3-1-4-2 \| 3-4-3 | 0 | 1 | 1 |
| 3-3-3-1 \| 3-4-2-1 | 0 | 1 | 1 |
| 3-4-1-2 \| 4-1-2-1-2 | 0 | 1 | 1 |
| 3-3-3-1 \| 4-3-3 | 0 | 1 | 1 |
| 3-4-3-d \| 4-4-2 | 0 | 1 | 1 |
| 4-1-2-1-2 \| 4-4-1-1 | 0 | 1 | 1 |
| 4-1-2-1-2 \| 5-3-2 | 0 | 1 | 1 |
| 4-1-2-1-2 \| 5-4-1 | 0 | 1 | 1 |
| 3-5-1-1 \| 4-5-1 | 0 | 1 | 1 |
| 4-1-3-2 \| 4-4-1-1 | 0 | 1 | 1 |
| 4-1-3-2 \| 5-3-2 | 0 | 1 | 1 |
| 3-5-1-1 \| 4-3-2-1 | 0 | 1 | 1 |
| 3-5-1-1 \| 4-1-2-1-2 | 0 | 1 | 1 |
| 3-5-1-1 \| 3-5-1-1 | 0 | 1 | 1 |
| 3-4-3-d \| 5-4-1 | 0 | 1 | 1 |
| 3-4-3-d \| 3-5-1-1 | 0 | 1 | 1 |
| 4-3-1-2 \| 4-3-2-1 | 0 | 1 | 1 |
| 3-4-3 \| 4-3-2-1 | 0 | 1 | 1 |
| 4-2-2-2 \| 4-3-1-2 | 0 | 1 | 1 |
| 3-4-1-2 \| 4-5-1 | 0 | 1 | 1 |
| 3-4-1-2 \| 4-3-1-2 | 0 | 1 | 1 |
| 3-4-1-2 \| 4-2-2-2 | 0 | 1 | 1 |
| 3-4-1-2 \| 3-5-1-1 | 0 | 1 | 1 |
| 3-4-1-2 \| 3-4-3-d | 0 | 1 | 1 |
| 3-4-1-2 \| 3-4-1-2 | 0 | 1 | 1 |
| 3-3-3-1 \| 4-4-1-1 | 0 | 1 | 1 |
| 4-2-4-0 \| 4-4-1-1 | 0 | 1 | 1 |
| 4-5-1 \| 5-3-2 | 0 | 1 | 1 |

## 8. Missingness of predictor families (panel rows)

| index | FIFA World Cup | Premier League |
|---|---|---|
| tv_own_shot_any_before_interval | 0 | 0.200 |
| tv_own_shot_ot_before_interval | 0 | 0.200 |
| tv_own_corner_before_interval | 0 | 0.200 |
| tv_own_red_before_interval | 0 | 0 |
| tv_own_sub_before_interval | 0 | 0 |
| tv_opp_shot_any_before_interval | 0 | 0.200 |
| tv_opp_shot_ot_before_interval | 0 | 0.200 |
| tv_opp_corner_before_interval | 0 | 0.200 |
| tv_opp_red_before_interval | 0 | 0 |
| tv_opp_sub_before_interval | 0 | 0 |
| tv_man_advantage_at_interval_start | 0 | 0 |
| pre_odds_p_team_win | 100 | 0.200 |
| pre_odds_p_draw | 100 | 0.200 |
| pre_odds_p_opponent_win | 100 | 0.200 |
| pre_odds_p_over25 | 100 | 0.200 |
| pre_elo_team | 0 | 100 |
| pre_elo_opponent | 0 | 100 |
| pre_team_gf_last10 | 24.100 | 0.600 |
| pre_opp_gf_last10 | 24.100 | 0.600 |
| pre_team_ga_last10 | 24.100 | 0.600 |
| pre_opp_ga_last10 | 24.100 | 0.600 |
| pre_team_points_last10 | 24.100 | 0.600 |
| pre_opp_points_last10 | 24.100 | 0.600 |
| pre_team_possession_last10 | 24.100 | 8.400 |
| pre_opp_possession_last10 | 24.100 | 8.400 |
| pre_team_passes_last10 | 24.100 | 8.400 |
| pre_opp_passes_last10 | 24.100 | 8.400 |
| pre_team_long_ball_share_last10 | 24.100 | 8.400 |
| pre_opp_long_ball_share_last10 | 24.100 | 8.400 |
| pre_team_shots_last10 | 24.100 | 8.400 |
| pre_opp_shots_last10 | 24.100 | 8.400 |
| pre_team_sot_last10 | 24.100 | 8.400 |
| pre_opp_sot_last10 | 24.100 | 8.400 |
| pre_team_shots_comm_last10 | 24.100 | 0.600 |
| pre_opp_shots_comm_last10 | 24.100 | 0.600 |
| pre_team_sot_comm_last10 | 24.100 | 0.600 |
| pre_opp_sot_comm_last10 | 24.100 | 0.600 |
| pre_team_n_prior_matches | 0 | 0 |
| pre_opp_n_prior_matches | 0 | 0 |
| tv_active_formation_at_interval_start | 44.800 | 100 |
| tv_opp_active_formation_at_interval_start | 44.800 | 100 |

Pre-match odds exist only for the EPL and pre-match Elo only for the World Cup, by design. A World Cup team's first match has no rolling history because only earlier matches in the same tournament are used. EPL rolling features are missing only for each team's first EPL match within the dataset.
