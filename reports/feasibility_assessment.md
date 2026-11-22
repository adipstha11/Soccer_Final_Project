# Feasibility assessment

Generated 2026-11-22. Based on 4141 matches, 11721 goals and 49656 team-interval rows actually collected and validated.

## 1. Is the full research question answerable?

**Mostly yes, with three explicit qualifications.**

1. **Formation and goal counts (Q1, Q2):** answerable. Both starting formations and fully reconciled goal events exist for 4,138/4,141 in-scope matches.
2. **Formation and goal timing (Q3):** answerable using *starting* formations, through the interval panel and discrete-time survival. In-match formation changes are observed only for WC 2018/2022 (StatsBomb). For the EPL and WC 2026, use the phrase "starting formation" and do not describe it as the shape in force when a goal was scored.
   - For context, in WC 2018/22 teams averaged 1.40 StatsBomb Tactical Shifts per match, and the scoring team's active formation differed from its StatsBomb starting formation at 17% of goals. Starting formation is therefore a noisy proxy for the shape at the time of a goal.
3. **Tactical strategy (Q4):** only partially measurable. No source used here has a validated time-stamped measure of directness or possession. What can be measured:
   - **Pre-match style:** each team's rolling mean of possession %, passes, long-ball share (long balls / passes) and shots over its previous ≤10 matches. These are leakage-safe and are the recommended operationalisation of 'direct vs possession-based'.
   - **In-match, time-varying:** cumulative shots, shots on target, corners, red cards and substitutions before each interval (from ESPN commentary; validated against box-score totals).
   - **Post-match only:** full-match possession, passes, long balls, crosses. These are descriptive and must not be used to predict goals in the same match.
   - **Not available:** xG for most matches. football-data.co.uk added match xG only in 2026-27, and it is post-match.
4. **EPL vs World Cup (Q5):** answerable, but the World Cup side is small. See section 4.

Causal language is **not** justified. Formations are chosen in response to the opponent, expected game state and squad quality. Coefficients are adjusted associations, conditional on the pre-match strength controls.

## 2. Which seasons have reliable data

| competition | season | completed_by_cutoff | both_requirements (primary sample) | validated_regulation_goals_primary | goals_per_match_primary |
|---|---|---|---|---|---|
| Premier League | 2016-17 | 380 | 380 | 1064 | 2.800 |
| Premier League | 2017-18 | 380 | 379 | 1017 | 2.683 |
| Premier League | 2018-19 | 380 | 378 | 1066 | 2.820 |
| Premier League | 2019-20 | 380 | 380 | 1034 | 2.721 |
| Premier League | 2020-21 | 380 | 380 | 1024 | 2.695 |
| Premier League | 2021-22 | 380 | 380 | 1071 | 2.818 |
| Premier League | 2022-23 | 380 | 380 | 1084 | 2.853 |
| Premier League | 2023-24 | 380 | 380 | 1246 | 3.279 |
| Premier League | 2024-25 | 380 | 380 | 1115 | 2.934 |
| Premier League | 2025-26 | 380 | 380 | 1045 | 2.750 |
| Premier League | 2026-27 | 109 | 109 | 299 | 2.743 |
| FIFA World Cup | 2018 | 64 | 64 | 166 | 2.594 |
| FIFA World Cup | 2022 | 64 | 64 | 168 | 2.625 |
| FIFA World Cup | 2026 | 104 | 104 | 300 | 2.885 |

All 14 competition-seasons are covered. 12 are 100% usable. The rest lose only matches without ESPN formation labels (3 in total). 2026-27 is a partial season (matches to 22 Nov 2026), so include season fixed effects. Historical seasons differ in tactical-statistic coverage: 2016-17 has no ESPN box scores. See reports/historical_expansion_report.md.

## 3. Which formation matchups have adequate observations

There are 23 distinct formation labels and 171 distinct unordered matchups. Matchups with at least 30 matches: **29** overall (29 within EPL alone, 0 within World Cup alone). With at least 50 matches: 18; with at least 100: 10.

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

**Recommendations:**
- Use the five formation groups (`*_formation_group`: 4-2-3-1 / 4-3-3 family / 4-4-2 family / back-3/5 with 1 or 3 forwards / back-3/5 with 2 forwards) as the main factor. Or model the most common exact formations (4-2-3-1, 4-3-3, 4-4-2, 3-4-2-1, 4-1-4-1) and pool the rest.
- Or use the provider-robust coarse descriptors `back_line` (3/4/5 defenders) and `n_forwards`.
- Back-line matchups (home vs away):

| back_line_matchup | FIFA World Cup | Premier League |
|---|---|---|
| 3B vs 3B | 8 | 209 |
| 3B vs 4B | 24 | 503 |
| 3B vs 5B | 5 | 41 |
| 4B vs 3B | 26 | 580 |
| 4B vs 4B | 147 | 2320 |
| 4B vs 5B | 12 | 133 |
| 5B vs 3B | 1 | 27 |
| 5B vs 4B | 9 | 93 |

- A full matchup interaction (formation × opponent formation) is estimable only for the top few pairs, and in practice only within the EPL. Use regularisation or random effects for matchups.

## 4. Is the EPL vs World Cup comparison statistically reasonable?

- Sample sizes are very unequal: 3909 EPL vs 232 WC matches. That gives 2784 WC panel rows and about 634 regulation WC goals.
- Main effects (does goal rate differ by competition, and do the main formation effects differ?) are estimable through a competition × formation-family interaction.
- Competition × detailed-matchup interactions are **not** estimable with useful precision. No unordered matchup reaches 30 World Cup matches.
- The strength controls differ by competition: market odds for EPL, computed Elo for WC. Standardise within competition, or fit competition-specific models and compare coefficients.
- World Cup 'home' is mostly administrative (neutral venues). Use `neutral_site` and `team_is_host_country` rather than `home_indicator`.
- World Cup knockout matches cannot end level after extra time. The primary analysis uses regulation time; `stage` lets you check robustness.

## 5. Distributional facts relevant to model choice

- Total goals per match: variance/mean = 0.97 (EPL) and 1.17 (WC).
- Team goals per match: variance/mean = 1.14 (EPL) and 1.26 (WC).
- So overdispersion is mild in the EPL and moderate in the World Cup. Test it formally (Cameron–Trivedi or a likelihood-ratio Poisson vs NB), but expect Poisson to be adequate for EPL team goals.
- 9.7% of goals are scored in stoppage time. That is why intervals 3 and 6 are longer: observed mean exposure is 18.5 and 21.1 minutes. Use `log(exposure_observed_minutes)` as an offset in interval Poisson models, or include interval fixed effects.

Goal rate by interval (panel):

| competition | interval_number | mean_goals | p_score | rows |
|---|---|---|---|---|
| FIFA World Cup | 1 | 0.162 | 0.157 | 464 |
| FIFA World Cup | 2 | 0.140 | 0.136 | 464 |
| FIFA World Cup | 3 | 0.254 | 0.220 | 464 |
| FIFA World Cup | 4 | 0.244 | 0.216 | 464 |
| FIFA World Cup | 5 | 0.222 | 0.198 | 464 |
| FIFA World Cup | 6 | 0.345 | 0.284 | 464 |
| Premier League | 1 | 0.180 | 0.165 | 7812 |
| Premier League | 2 | 0.200 | 0.182 | 7812 |
| Premier League | 3 | 0.250 | 0.221 | 7812 |
| Premier League | 4 | 0.228 | 0.204 | 7812 |
| Premier League | 5 | 0.237 | 0.211 | 7812 |
| Premier League | 6 | 0.322 | 0.274 | 7812 |

## 6. Recommended models

| Question | Data | Model | Notes |
|---|---|---|---|
| Q1 team goals ~ own formation | team-level (two rows per match, built from match_level) | Poisson GLM (NB if LR test rejects) | controls: opponent formation, pre-match strength, home/neutral, season FE; cluster SEs by match |
| Q2 total goals ~ matchup | match_level | Poisson/NB on `total_goals` with `formation_pair_unordered` (top pairs + other) | `pre_odds_p_over25` is a strong baseline control for EPL |
| Q3 timing | team_interval_panel | logistic on `scored_at_least_one_goal`, interval FE × formation | equivalently a discrete-time hazard for the first goal: keep rows up to the first goal interval |
| Q3 counts | team_interval_panel | Poisson on `goals_scored_in_interval` + offset log(exposure) | allows more than one goal per interval |
| Q4 tactics | panel / team-level | add `pre_team_possession_last10`, `pre_team_long_ball_share_last10` and time-varying shots / red cards | time-varying covariates are mediators of game state; report models with and without them |
| Q5 EPL vs WC | pooled | competition × formation-family interaction | or separate models with a Wald test of coefficient equality |

**Dependence:** rows are clustered within match and team (12 panel rows per match). Use cluster-robust SEs by `match_id`, or mixed models with random intercepts for `team_id` (crossed with `match_id`) via `lme4::glmer` or `glmmTMB`.

## 7. Main limitations

- Formation labels are provider interpretations of the average starting shape (see the agreement figures in the quality report).
- No formation changes are recorded for the EPL or WC 2026.
- Goal times have minute resolution only; seconds are never invented.
- ESPN is an undocumented public API. Its terms restrict redistribution of the raw data, so cite it and do not republish the raw JSON.
- Pre-match strength proxies differ by competition (odds vs Elo).
- 2026-27 is a partial season and 9 of its matches still lack odds.