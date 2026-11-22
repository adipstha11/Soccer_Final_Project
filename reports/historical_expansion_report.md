# Historical expansion report (v2)

Generated 2026-11-22. The baseline v1 (1,481 matches) is preserved in `snapshots/baseline_v1_20261122/` with SHA-256 hashes. This expansion adds EPL 2016-17 to 2022-23 from the same ESPN pipeline.

## 1. Per-season coverage

| Competition | Season | Era | Matches found | Valid formations | Valid goal events | Fully usable matches | Regulation goals |
|---|---|---|---|---|---|---|---|
| Premier League | 2016-17 | added (v2) | 380 | 380 | 380 | 380 | 1064 |
| Premier League | 2017-18 | added (v2) | 380 | 379 | 380 | 379 | 1017 |
| Premier League | 2018-19 | added (v2) | 380 | 378 | 380 | 378 | 1066 |
| Premier League | 2019-20 | added (v2) | 380 | 380 | 380 | 380 | 1034 |
| Premier League | 2020-21 | added (v2) | 380 | 380 | 380 | 380 | 1024 |
| Premier League | 2021-22 | added (v2) | 380 | 380 | 380 | 380 | 1071 |
| Premier League | 2022-23 | added (v2) | 380 | 380 | 380 | 380 | 1084 |
| Premier League | 2023-24 | baseline (v1) | 380 | 380 | 380 | 380 | 1246 |
| Premier League | 2024-25 | baseline (v1) | 380 | 380 | 380 | 380 | 1115 |
| Premier League | 2025-26 | baseline (v1) | 380 | 380 | 380 | 380 | 1045 |
| Premier League | 2026-27 | baseline (v1) | 109 | 109 | 109 | 109 | 299 |
| FIFA World Cup | 2018 | baseline (v1) | 64 | 64 | 64 | 64 | 166 |
| FIFA World Cup | 2022 | baseline (v1) | 64 | 64 | 64 | 64 | 168 |
| FIFA World Cup | 2026 | baseline (v1) | 104 | 104 | 104 | 104 | 300 |

## 2. Totals (verified, not theoretical)

- Verified matches: **4,141** (fully usable: 4,138); EPL 3,909 + World Cup 232.
- Validated goals: **11,721** (11,706 in regulation, 15 in WC extra time; shoot-out kicks excluded).
- Team-interval panel observations: **49,656** (= 4,138 matches x 12).
- Added in v2: 2,657 matches, 7,360 regulation goals, 31,884 panel rows.
- Targets in the brief: 4,141 matches / 49,692 panel rows. Achieved: 4,141 / 49,656.

## 3. Missing data and coverage differences: historical vs recent seasons

| Season | Box score missing % | Commentary incomplete % | Pre-match odds missing % | Score == football-data.co.uk % | Linescore conflicts resolved |
|---|---|---|---|---|---|
| 2016-17 | 97.100 | 0 | 0 | 100 | 0 |
| 2017-18 | 0 | 0.500 | 0 | 100 | 1 |
| 2018-19 | 0.300 | 1.600 | 0 | 100 | 0 |
| 2019-20 | 1.100 | 0 | 0 | 100 | 0 |
| 2020-21 | 2.100 | 0 | 0 | 100 | 0 |
| 2021-22 | 7.400 | 0.300 | 0 | 100 | 0 |
| 2022-23 | 22.400 | 0 | 0 | 100 | 0 |
| 2023-24 | 2.600 | 0 | 0 | 100 | 0 |
| 2024-25 | 3.200 | 0 | 0 | 100 | 0 |
| 2025-26 | 0 | 0.300 | 0 | 100 | 3 |
| 2026-27 | 0 | 0 | 8.300 | 100 | 0 |
| 2018 | 0 | 0 |  |  | 2 |
| 2022 | 0 | 0 |  |  | 0 |
| 2026 | 0 | 0 |  |  | 0 |

- **Box scores** (possession, passes, long balls, box-score shots): missing for 18.6% of added-season matches vs 1.8% of recent EPL matches. ESPN returns all-zero placeholders for **all of 2016-17** and for scattered later matches. These are recorded as missing, never 0. So possession/passing/long-ball style features cannot be computed for 2016-17. The rolling features for early 2017-18 use fewer matches (or none).
- **Shots for every season**: shots and shots on target are also counted from ESPN commentary (`post_*_shots_commentary`, `pre_*_shots_comm_last10`). Where both exist they were checked against the box score (tolerance max(4, 15%)). This makes shot-based tactical predictors available for all ten seasons.
- **Formations, goal minutes (incl. stoppage notation), penalties, own goals and starting XIs** are equally complete in historical and recent seasons.
- **Pre-match odds**: seasons up to 2018-19 use football-data.co.uk BetBrain averages (`BbAv*`), later seasons the market average (`Avg*`). The column used is recorded in `fd_odds_columns`.

## 4. How often do the named formations appear? (team-matches, fully usable sample)

| formation | EPL 2016-17..2022-23 | EPL 2023-24..2026-27 | World Cup | total | share_of_team_matches |
|---|---|---|---|---|---|
| 4-3-3 | 1096 | 394 | 86 | 1576 | 0.190 |
| 4-2-3-1 | 1379 | 1268 | 152 | 2799 | 0.338 |
| 4-4-2 | 663 | 92 | 68 | 823 | 0.099 |
| 3-5-2 | 253 | 79 | 8 | 340 | 0.041 |
| 3-4-3 | 210 | 45 | 5 | 260 | 0.031 |
| 3-4-2-1 | 405 | 317 | 42 | 764 | 0.092 |

The formations are far from equally common. 4-2-3-1 alone is about a third of all team-matches, while 3-4-3 and 3-5-2 are rare. ESPN's use of labels also drifts over time: 3-4-3 appears mainly in 2016-17..2020-21, while 3-4-2-1 dominates later. This may be partly a labelling change rather than a tactical one.

Full table (top 20):

| formation | EPL 2016-17..2022-23 | EPL 2023-24..2026-27 | World Cup | total | share_of_team_matches |
|---|---|---|---|---|---|
| 4-2-3-1 | 1379 | 1268 | 152 | 2799 | 0.338 |
| 4-3-3 | 1096 | 394 | 86 | 1576 | 0.190 |
| 4-4-2 | 663 | 92 | 68 | 823 | 0.099 |
| 3-4-2-1 | 405 | 317 | 42 | 764 | 0.092 |
| 4-1-4-1 | 273 | 72 | 39 | 384 | 0.046 |
| 4-4-1-1 | 285 | 55 | 10 | 350 | 0.042 |
| 3-5-2 | 253 | 79 | 8 | 340 | 0.041 |
| 3-4-3 | 210 | 45 | 5 | 260 | 0.031 |
| 5-4-1 | 116 | 54 | 15 | 185 | 0.022 |
| 5-3-2 | 98 | 26 | 12 | 136 | 0.016 |
| 3-4-1-2 | 98 | 18 | 6 | 122 | 0.015 |
| 4-5-1 | 100 | 12 | 0 | 112 | 0.013 |
| 4-1-2-1-2 | 66 | 4 | 4 | 74 | 0.009 |
| 4-2-2-2 | 62 | 12 | 0 | 74 | 0.009 |
| 3-5-1-1 | 62 | 6 | 0 | 68 | 0.008 |
| 4-3-1-2 | 53 | 8 | 3 | 64 | 0.008 |
| 3-1-4-2 | 32 | 4 | 11 | 47 | 0.006 |
| 4-3-2-1 | 30 | 11 | 1 | 42 | 0.005 |
| 3-2-4-1 | 12 | 12 | 0 | 24 | 0.003 |
| 4-1-3-2 | 5 | 7 | 2 | 14 | 0.002 |

## 5. Average goals by starting formation (regulation, team perspective)

| formation | team_matches | goals_for_mean | goals_against_mean | match_total_mean |
|---|---|---|---|---|
| 4-2-3-1 | 2799 | 1.498 | 1.367 | 2.865 |
| 4-3-3 | 1576 | 1.701 | 1.211 | 2.912 |
| 4-4-2 | 823 | 1.228 | 1.478 | 2.706 |
| 3-4-2-1 | 764 | 1.428 | 1.478 | 2.906 |
| 4-1-4-1 | 384 | 1.289 | 1.505 | 2.794 |
| 4-4-1-1 | 350 | 1.126 | 1.623 | 2.749 |
| 3-5-2 | 340 | 1.079 | 1.576 | 2.656 |
| 3-4-3 | 260 | 1.281 | 1.419 | 2.700 |
| 5-4-1 | 185 | 0.984 | 1.859 | 2.843 |
| 5-3-2 | 136 | 0.765 | 1.860 | 2.625 |
| 3-4-1-2 | 122 | 1.270 | 1.393 | 2.664 |
| 4-5-1 | 112 | 0.830 | 1.741 | 2.571 |
| 4-1-2-1-2 | 74 | 1.297 | 1.311 | 2.608 |
| 4-2-2-2 | 74 | 1.514 | 1.324 | 2.838 |
| 3-5-1-1 | 68 | 1.162 | 1.750 | 2.912 |

By formation group:

| group | team_matches | goals_for_mean | goals_against_mean |
|---|---|---|---|
| 4-2-3-1 | 2799 | 1.498 | 1.367 |
| 4-3-3 family | 2114 | 1.570 | 1.302 |
| 4-4-2 family | 1399 | 1.224 | 1.497 |
| back-3/5, 1 or 3 forwards | 1317 | 1.344 | 1.522 |
| back-3/5, 2 forwards | 645 | 1.085 | 1.581 |
| other | 2 | 1.500 | 1.500 |

These are raw descriptive means. Formation choice is confounded by team strength (strong teams favour 4-3-3 / 4-2-3-1; underdogs use back fives), so differences must be adjusted with the strength controls.

## 6. Goal timing distribution by scoring team's starting formation

Share of the formation's regulation goals scored in each interval (I1 = 0-15 ... I6 = 75-90+):

| scoring_team_starting_formation | I1 | I2 | I3 | I4 | I5 | I6 | n_goals |
|---|---|---|---|---|---|---|---|
| 4-2-3-1 | 0.123 | 0.140 | 0.171 | 0.166 | 0.169 | 0.231 | 4193 |
| 4-3-3 | 0.121 | 0.142 | 0.193 | 0.165 | 0.158 | 0.222 | 2680 |
| 3-4-2-1 | 0.121 | 0.132 | 0.181 | 0.160 | 0.170 | 0.236 | 1091 |
| 4-4-2 | 0.149 | 0.136 | 0.187 | 0.148 | 0.166 | 0.214 | 1011 |
| 4-1-4-1 | 0.149 | 0.135 | 0.152 | 0.135 | 0.172 | 0.257 | 495 |
| 4-4-1-1 | 0.140 | 0.150 | 0.170 | 0.168 | 0.162 | 0.211 | 394 |
| 3-5-2 | 0.112 | 0.114 | 0.153 | 0.172 | 0.185 | 0.264 | 367 |
| 3-4-3 | 0.129 | 0.105 | 0.168 | 0.168 | 0.183 | 0.246 | 333 |
| 5-4-1 | 0.110 | 0.181 | 0.187 | 0.137 | 0.181 | 0.203 | 182 |
| 3-4-1-2 | 0.116 | 0.174 | 0.123 | 0.155 | 0.148 | 0.284 | 155 |
| 4-2-2-2 | 0.125 | 0.196 | 0.134 | 0.161 | 0.205 | 0.179 | 112 |
| 5-3-2 | 0.144 | 0.144 | 0.212 | 0.115 | 0.173 | 0.212 | 104 |

By formation group:

| group | I1 | I2 | I3 | I4 | I5 | I6 | n_goals |
|---|---|---|---|---|---|---|---|
| 4-2-3-1 | 0.123 | 0.140 | 0.171 | 0.166 | 0.169 | 0.231 | 4193 |
| 4-3-3 family | 0.124 | 0.139 | 0.186 | 0.161 | 0.162 | 0.229 | 3320 |
| 4-4-2 family | 0.146 | 0.145 | 0.177 | 0.154 | 0.164 | 0.214 | 1713 |
| back-3/5, 1 or 3 forwards | 0.123 | 0.135 | 0.178 | 0.163 | 0.175 | 0.227 | 1770 |
| back-3/5, 2 forwards | 0.116 | 0.130 | 0.163 | 0.161 | 0.169 | 0.261 | 700 |
| other | 0.667 | 0 | 0.333 | 0 | 0 | 0 | 3 |

## 7. Matchup counts

Most common unordered matchups:

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

Formation vs opponent formation (team perspective, top-10 formations, each match counted twice):

| formation | 4-2-3-1 | 4-3-3 | 4-4-2 | 3-4-2-1 | 4-1-4-1 | 4-4-1-1 | 3-5-2 | 3-4-3 | 5-4-1 | 5-3-2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 4-2-3-1 | 1070 | 504 | 244 | 277 | 149 | 106 | 106 | 67 | 70 | 31 |
| 4-3-3 | 504 | 294 | 166 | 120 | 65 | 91 | 78 | 44 | 43 | 38 |
| 4-4-2 | 244 | 166 | 90 | 62 | 53 | 36 | 26 | 31 | 19 | 13 |
| 3-4-2-1 | 277 | 120 | 62 | 110 | 20 | 26 | 33 | 19 | 13 | 22 |
| 4-1-4-1 | 149 | 65 | 53 | 20 | 14 | 21 | 10 | 9 | 10 | 5 |
| 4-4-1-1 | 106 | 91 | 36 | 26 | 21 | 30 | 9 | 5 | 2 | 2 |
| 3-5-2 | 106 | 78 | 26 | 33 | 10 | 9 | 18 | 20 | 5 | 4 |
| 3-4-3 | 67 | 44 | 31 | 19 | 9 | 5 | 20 | 18 | 9 | 6 |
| 5-4-1 | 70 | 43 | 19 | 13 | 10 | 2 | 5 | 9 | 0 | 0 |
| 5-3-2 | 31 | 38 | 13 | 22 | 5 | 2 | 4 | 6 | 0 | 0 |

Formation group vs opponent group (team perspective):

| group | 4-2-3-1 | 4-3-3 family | 4-4-2 family | back-3/5, 1 or 3 forwards | back-3/5, 2 forwards | other |
|---|---|---|---|---|---|---|
| 4-2-3-1 | 1070 | 704 | 410 | 439 | 176 | 0 |
| 4-3-3 family | 704 | 540 | 412 | 285 | 173 | 0 |
| 4-4-2 family | 410 | 412 | 270 | 203 | 103 | 1 |
| back-3/5, 1 or 3 forwards | 439 | 285 | 203 | 264 | 125 | 1 |
| back-3/5, 2 forwards | 176 | 173 | 103 | 125 | 68 | 0 |
| other | 0 | 0 | 1 | 1 | 0 | 0 |

Back-line matchups (home vs away):

| back_line_matchup | matches |
|---|---|
| 4B vs 4B | 2467 |
| 4B vs 3B | 606 |
| 3B vs 4B | 527 |
| 3B vs 3B | 217 |
| 4B vs 5B | 145 |
| 5B vs 4B | 102 |
| 3B vs 5B | 46 |
| 5B vs 3B | 28 |

## 8. Is there enough data for specific matchups?

| index | v1 baseline (1,481 matches) | v2 expanded (4,138 matches) |
|---|---|---|
| matches | 1481 | 4138 |
| distinct formations | 21 | 23 |
| distinct exact matchups (unordered) | 98 | 171 |
| exact matchups >=30 matches | 10 | 29 |
| exact matchups >=50 | 6 | 18 |
| exact matchups >=100 | 3 | 10 |
| share of matches in matchups >=30 | 0.734 | 0.797 |
| distinct group matchups (unordered) | 17 | 17 |
| group matchups >=30 | 11 | 15 |
| group matchups >=100 | 4 | 14 |

Approximate precision for the most common matchups. SE of log(mean total goals) ≈ 1/sqrt(n x mean goals). The minimum detectable rate ratio is for a two-sided 5% test at 80% power against a reference of similar size:

| formation_pair_unordered | matches_v1 | matches_v2 | approx_SE_log_rate_v1 | approx_SE_log_rate_v2 | min_detectable_rate_ratio_v2 |
|---|---|---|---|---|---|
| 4-2-3-1 \| 4-2-3-1 | 337 | 535 | 0.032 | 0.026 | 1.108 |
| 4-2-3-1 \| 4-3-3 | 225 | 504 | 0.040 | 0.026 | 1.108 |
| 3-4-2-1 \| 4-2-3-1 | 192 | 277 | 0.043 | 0.036 | 1.153 |
| 4-2-3-1 \| 4-4-2 | 70 | 244 | 0.071 | 0.038 | 1.162 |
| 4-3-3 \| 4-4-2 | 36 | 166 | 0.099 | 0.046 | 1.200 |
| 4-1-4-1 \| 4-2-3-1 | 54 | 149 | 0.081 | 0.049 | 1.214 |
| 4-3-3 \| 4-3-3 | 32 | 147 | 0.105 | 0.049 | 1.214 |
| 3-4-2-1 \| 4-3-3 | 57 | 120 | 0.079 | 0.054 | 1.238 |
| 4-2-3-1 \| 4-4-1-1 | 27 | 106 | 0.114 | 0.058 | 1.258 |
| 3-5-2 \| 4-2-3-1 | 43 | 106 | 0.091 | 0.058 | 1.258 |
| 4-3-3 \| 4-4-1-1 | 17 | 91 | 0.144 | 0.062 | 1.278 |
| 3-5-2 \| 4-3-3 | 20 | 78 | 0.133 | 0.067 | 1.304 |

**Verdict**
- Exact matchups: the number of matchups with at least 30 matches rises from 10 to 29. Only the leading pairs (4-2-3-1 mirror, 4-2-3-1 vs 4-3-3, 4-2-3-1 vs 3-4-2-1, ...) can be estimated with useful precision. Minimum detectable rate ratios are 1.11-1.15 for the top 3 pairs and 1.16-1.30 for pairs 4-12. 142 of 171 exact matchups have fewer than 30 matches, so most of the long tail stays sparse.
- **Recommended grouping** (`*_formation_group`, original strings kept):
  - `4-2-3-1`
  - `4-3-3 family` (4-3-3, 4-1-4-1, 4-5-1, 4-3-2-1)
  - `4-4-2 family` (4-4-2, 4-4-1-1, 4-2-2-2, 4-1-3-2, diamonds 4-1-2-1-2 / 4-3-1-2)
  - `back-3/5, 1 or 3 forwards` (3-4-2-1, 3-4-3, 5-4-1, 3-2-4-1, 3-5-1-1, ...)
  - `back-3/5, 2 forwards` (3-5-2, 3-1-4-2, 3-4-1-2, 5-3-2, ...)
- Back-3 and back-5 labels are merged on purpose. Providers label the same shape 5-3-2 or 3-5-2, and ESPN-vs-StatsBomb agreement on 'back three' is much better than on the exact label.
- The unordered group × group matchup has 17 observed cells, of which 15 have at least 30 matches and 14 at least 100. The cells below 30 involve the tiny 'other' group (e.g. 4-2-4-0), which should be pooled or dropped.
- An alternative is the two-level descriptor `back_line` × `n_forwards`.

## 9. Does the expansion give a meaningful statistical improvement?

- EPL sample: 3,906 matches instead of 1,249 (about 3.1x). Standard errors for EPL formation effects shrink by about 1/sqrt(3.1) ≈ 0.57x.
- Ten seasons allow season fixed effects and a genuine out-of-time test. For example, train on 2016-17..2024-25 and test on 2025-26, all with causally computed predictors (strictly earlier kickoffs).
- The EPL vs World Cup comparison does **not** improve: World Cup size is unchanged (232 matches), so the EPL/WC imbalance grows. Compare at formation-group level.
- Caveat: rolling style features are unavailable for 2016-17 and patchy early in 2017-18 (box scores). Models that need possession/long-ball share should start in 2017-18, or use the commentary shot features only.

## 10. Rolling-window rules (pre-match predictors)

- Window: the team's previous ≤10 matches in the same competition group, with kickoff strictly before the match. The current match and later matches never contribute (checked by an independent SQL re-implementation).
- EPL windows **cross season boundaries** but only use matches within the previous **365 days**. So:
  - a team's first match of the season uses its last matches of the previous EPL season;
  - a **newly promoted club has no history** at its first EPL match (`pre_*_n_prior_matches = 0`, features NaN). No Championship or other non-EPL data are used or invented;
  - a club returning after relegation does not reuse an earlier top-flight spell;
  - 2016-17 opening matches have no history, because 2015-16 is not in the dataset.
- World Cup windows: earlier matches in the same tournament only.
- Missing source values (empty box scores) are skipped inside the window, so a mean may rest on fewer than `n_prior_matches` values.
- Rolling values of the v1 baseline records changed in v2 because earlier history now exists (e.g. 2023-24 openers). This is expected and is listed in `reports/baseline_preservation.csv`. All source-derived values (scores, goals, formations, timing) are unchanged.

## 11. Temporal validation support

- `season` (ordered), `match_date` and `kickoff_utc` allow chronological splits.
- All `PRE` and `TV` predictors are computed from strictly earlier information, so a split at any date is leakage-free.
- Promoted-team NaNs should be handled with an explicit indicator (e.g. `pre_team_n_prior_matches == 0`) rather than by dropping rows.