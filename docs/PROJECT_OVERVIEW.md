# Project overview

**Predicting the Timing and Number of Goals in Football: The Role of Tactical Strategies and Formation Matchups in the Premier League and FIFA World Cup**

University statistics final project. This document is written for a teammate who has never seen the project. It explains what we are studying, what data we have, how the data were built, and what still needs to be done. It does not require reading the code.

> **Status as of 2026-11-22**
> - **Current validated dataset (v2, promoted 2026-11-22):** 4,141 matches (4,138 fully usable), 11,721 goals, 49,656 team-interval rows. It covers EPL 2016-17 to 2025-26 (10 complete seasons), 2026-27 (partial) and the 2018, 2022 and 2026 World Cups. All 51 checks and 51 tests pass. See [section F.2](#f2-historical-expansion-v2-in-progress) and [`reports/historical_expansion_report.md`](../reports/historical_expansion_report.md).
> - **Previous baseline (v1):** 1,481 matches, 4,354 goals, 17,772 rows, archived in `snapshots/baseline_v1_20261122/`. **Several figures further down in this document (sections C–I) still describe v1.** The reports in `reports/` are the up-to-date source.

---

## Contents

- [A. Project overview](#a-project-overview)
- [B. Research questions](#b-research-questions)
- [C. Dataset description](#c-dataset-description)
- [D. Data sources](#d-data-sources)
- [E. Data collection and cleaning](#e-data-collection-and-cleaning)
- [F. Current dataset coverage](#f-current-dataset-coverage)
- [G. Variable dictionary](#g-variable-dictionary)
- [H. Proposed statistical methods](#h-proposed-statistical-methods)
- [I. Limitations](#i-limitations)
- [J. Next steps for teammates](#j-next-steps-for-teammates)

---

## A. Project overview

### Motivation

Goals are rare in football. A Premier League match averages roughly 2.7–3.3 goals, so a single goal often decides the result. Coaches spend a great deal of effort choosing a **formation**, the arrangement of the ten outfield players written as defenders–midfielders–forwards (e.g. `4-2-3-1`, `3-4-2-1`). Pundits routinely claim that some shapes are "attacking", others "defensive", and that certain shapes beat others. These claims are rarely tested statistically on a large, clean dataset.

### Main research question

> Do a team's starting formation, the formation matchup against the opponent and the team's tactical style help predict **how many** goals are scored and **when** they are scored, after controlling for team strength? Do these relationships differ between the Premier League and the World Cup?

### Why formations matter

- A formation fixes how many players start in each line, which changes the numbers in midfield, how wide the team is and how many players are near goal.
- The **matchup** matters as much as a team's own shape. For example, a back three against a front two leaves a spare defender, while a back three against a front three does not. So we model the pairing (`formation_matchup`), not only each team's formation.
- Formations are cheap to observe and are published before kickoff, so they are natural *pre-match* predictors.

### Why goal timing is interesting

Goals are not spread evenly over 90 minutes. In our baseline, the last interval (75'–90'+stoppage) has the highest scoring rate in both competitions. The first-half interval that includes stoppage time (30'–45'+) is also elevated. Timing matters for:

- **Game-state dynamics.** An early goal changes how both teams play for the rest of the match.
- **Tactical fatigue.** Some shapes, such as high-pressing ones, may concede more late.
- **Practical prediction**, for example in-play probabilities.

### What we are trying to predict

1. **Goal counts:** total goals in a match, or goals scored by one team, from pre-match information. (Poisson regression.)
2. **Goal timing:** whether a team scores in each 15-minute interval, from pre-match information plus what is known when that interval starts. (Logistic regression or a discrete-time hazard.)

This project **predicts and describes associations**. It does not identify causal effects of formations. See [Limitations](#i-limitations).

---

## B. Research questions

| # | Question | Main dataset | Main response |
|---|---|---|---|
| **Q1** | **Do tactical formations predict goal counts?** Does a team's starting formation predict how many goals it scores (and concedes), holding team strength fixed? | `match_level.csv` (reshaped to two team rows per match) | team goals |
| **Q2** | **Do formation matchups affect goal-scoring patterns?** Does the *combination* of the two teams' formations predict total goals beyond each formation alone? | `match_level.csv` | `total_goals` |
| **Q3** | **Are certain formations associated with earlier or later goals?** Does the probability of scoring in a given 15-minute interval depend on formation, and does that dependence change over the match (formation × interval)? | `team_interval_panel.csv`, `goal_events.csv` | `scored_at_least_one_goal`, `goal_minute` |
| **Q4** | **Does attacking style improve predictive performance?** Does adding measures of style improve out-of-sample prediction over formation and strength alone? Style here means pre-match possession, passing volume, long-ball share and shots, plus in-match shots, corners and red cards so far. | panel and match level | same as Q1–Q3; compare held-out log-likelihood / Brier score |
| **Q5** | **Do the relationships differ between the Premier League and World Cup?** Are formation effects the same in club league football and in a short international tournament played at neutral venues? | pooled | competition × formation-family interaction |

---

## C. Dataset description

There are three linked tables in `data/processed/`, each with a `.csv` and a `.parquet` copy. All three link on **`match_id`**.

```
match_level.csv          1 row per match            (1,481 rows)
      │  match_id
      ├──────────────── goal_events.csv            1 row per goal          (4,354 rows)
      │  match_id
      └──────────────── team_interval_panel.csv    1 row per team × 15-min interval (17,772 rows = 1,481 × 2 × 6)
```

### C.1 `match_level.csv`: one row per match

- **Contains:** competition, season, stage, date, teams, both **starting formations** and the matchup, formation descriptors (number of defenders, number of forwards), regulation and half-time scores, extra-time and shoot-out fields, neutral-venue and host flags, **pre-match strength** (betting-market probabilities for the EPL, computed Elo for the World Cup), **pre-match rolling style** averages (`pre_*_last10`), post-match box-score statistics (`post_*`, descriptive only), and cross-source QA columns.
- **Supports:** total-goal and team-goal analysis (Q1, Q2, Q5).

Example: two genuine rows, selected columns, copied directly from the file.

| match_id | competition | season | match_date | home_team | away_team | home_starting_formation | away_starting_formation | formation_matchup | home_goals | away_goals | total_goals | pre_odds_p_home_win | pre_elo_diff_home_minus_away |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ESPN-704291 | Premier League | 2024-25 | 2024-08-24 | Brighton & Hove Albion | Manchester United | 4-2-3-1 | 4-2-3-1 | 4-2-3-1 vs 4-2-3-1 | 2 | 1 | 3 | 0.384 | *(NA: EPL uses odds)* |
| ESPN-633794 | FIFA World Cup | 2022 | 2022-11-22 | Argentina | Saudi Arabia | 4-4-2 | 4-1-4-1 | 4-4-2 vs 4-1-4-1 | 1 | 2 | 3 | *(NA: WC uses Elo)* | 447.6 |

### C.2 `goal_events.csv`: one row per goal

- **Contains:** the goal's order in the match, scoring and conceding team, **exact goal minute** and stoppage minute, the original notation (`45+2`, `90+5`), period (1H/2H/ET1/ET2), interval number, goal type (penalty, own goal, header, other shot), both teams' starting formations, the **active formation at the time of the goal** (WC 2018/2022 only, from StatsBomb), and the running score after the goal.
- **Supports:** goal-timing analysis (Q3): distribution of goal minutes, time to first goal, timing by formation.
- Shoot-out kicks are **never** included. Extra-time goals (15) are included but flagged with `in_regulation = 0` and have no interval number.

Example: all goals from the two matches above.

| goal_id | scoring_team | goal_minute | stoppage_time_minute | original_goal_time | goal_period | interval_number | goal_type | scoring_team_starting_formation | opponent_starting_formation | active_formation_at_goal | home_score_after | away_score_after |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ESPN-704291-G01 | Brighton & Hove Albion | 32 | 0 | 32 | 1H | 3 | other_shot | 4-2-3-1 | 4-2-3-1 | *(NA: EPL)* | 1 | 0 |
| ESPN-704291-G02 | Manchester United | 60 | 0 | 60 | 2H | 4 | other_shot | 4-2-3-1 | 4-2-3-1 | *(NA: EPL)* | 1 | 1 |
| ESPN-704291-G03 | Brighton & Hove Albion | 90 | 5 | 90+5 | 2H | 6 | header | 4-2-3-1 | 4-2-3-1 | *(NA: EPL)* | 2 | 1 |
| ESPN-633794-G01 | Argentina | 10 | 0 | 10 | 1H | 1 | penalty | 4-4-2 | 4-1-4-1 | 4-4-2 | 1 | 0 |
| ESPN-633794-G02 | Saudi Arabia | 48 | 0 | 48 | 2H | 4 | other_shot | 4-1-4-1 | 4-4-2 | 4-4-1-1 | 1 | 1 |
| ESPN-633794-G03 | Saudi Arabia | 53 | 0 | 53 | 2H | 4 | other_shot | 4-1-4-1 | 4-4-2 | 4-4-1-1 | 1 | 2 |

Note the Brighton winner at **90+5**. It is stored as minute 90 plus 5 stoppage minutes and falls in interval 6. Note also that Saudi Arabia started in a 4-1-4-1 (ESPN), while StatsBomb records their active shape at both goals as 4-4-1-1. Starting formation and actual shape can differ.

### C.3 `team_interval_panel.csv`: one row per team per 15-minute interval

- **Contains:** for each match, both teams × 6 intervals. The columns are:
  - own and opponent starting formation, and the matchup;
  - home/neutral/host indicators;
  - **goals scored and conceded in the interval** (count and 0/1);
  - **score difference at the start of the interval**;
  - time-varying counts of shots, corners, red cards and substitutions *before* the interval (`tv_*`);
  - pre-match strength and style;
  - observed minutes in the interval, an exposure used for offsets only.
- **Supports:** interval-level regression (Q3, Q4).

| # | label | covers |
|---|---|---|
| 1 | 0-15 | minutes 1–15 |
| 2 | 15-30 | 16–30 |
| 3 | 30-45+ | 31–45 **plus first-half stoppage** |
| 4 | 45-60 | 46–60 |
| 5 | 60-75 | 61–75 |
| 6 | 75-90+ | 76–90 **plus second-half stoppage** |

Example: the 12 genuine panel rows for Argentina vs Saudi Arabia (WC 2022), selected columns.

| panel_id | team | interval_number | interval_label | starting_formation | opponent_starting_formation | goals_scored_in_interval | scored_at_least_one_goal | score_difference_at_interval_start | exposure_observed_minutes | home_indicator |
|---|---|---|---|---|---|---|---|---|---|---|
| ESPN-633794-202-I1 | Argentina | 1 | 0-15 | 4-4-2 | 4-1-4-1 | 1 | 1 | 0 | 15 | 1 |
| ESPN-633794-202-I2 | Argentina | 2 | 15-30 | 4-4-2 | 4-1-4-1 | 0 | 0 | 1 | 15 | 1 |
| ESPN-633794-202-I3 | Argentina | 3 | 30-45+ | 4-4-2 | 4-1-4-1 | 0 | 0 | 1 | 22 | 1 |
| ESPN-633794-202-I4 | Argentina | 4 | 45-60 | 4-4-2 | 4-1-4-1 | 0 | 0 | 1 | 15 | 1 |
| ESPN-633794-202-I5 | Argentina | 5 | 60-75 | 4-4-2 | 4-1-4-1 | 0 | 0 | -1 | 15 | 1 |
| ESPN-633794-202-I6 | Argentina | 6 | 75-90+ | 4-4-2 | 4-1-4-1 | 0 | 0 | -1 | 29 | 1 |
| ESPN-633794-655-I1 | Saudi Arabia | 1 | 0-15 | 4-1-4-1 | 4-4-2 | 0 | 0 | 0 | 15 | 0 |
| ESPN-633794-655-I2 | Saudi Arabia | 2 | 15-30 | 4-1-4-1 | 4-4-2 | 0 | 0 | -1 | 15 | 0 |
| ESPN-633794-655-I3 | Saudi Arabia | 3 | 30-45+ | 4-1-4-1 | 4-4-2 | 0 | 0 | -1 | 22 | 0 |
| ESPN-633794-655-I4 | Saudi Arabia | 4 | 45-60 | 4-1-4-1 | 4-4-2 | **2** | 1 | -1 | 15 | 0 |
| ESPN-633794-655-I5 | Saudi Arabia | 5 | 60-75 | 4-1-4-1 | 4-4-2 | 0 | 0 | 1 | 15 | 0 |
| ESPN-633794-655-I6 | Saudi Arabia | 6 | 75-90+ | 4-1-4-1 | 4-4-2 | 0 | 0 | 1 | 29 | 0 |

Saudi Arabia's two goals (48', 53') fall in the same interval. The count column is `2` and the binary column is `1`. Because the World Cup is played at neutral venues, `home_indicator` here only records which team ESPN lists first. Use `neutral_site` and `team_is_host_country` instead.

---

## D. Data sources

Every source is public and needs **no API key or payment**. The full audit of the 16 candidate sources is in [`data/processed/source_audit.csv`](../data/processed/source_audit.csv). For each source it records the HTTP status, the fields verified, the licence and why the source was used or rejected.

| Source | What it contributes | Link | Access and terms |
|---|---|---|---|
| **ESPN public site API** (primary) | Fixtures, final status, **starting formations**, **goal events with minute, stoppage notation, period, penalty and own-goal type**, commentary (shots, corners), red cards, substitutions, box-score statistics. All three datasets are built on ESPN match IDs. | `https://site.api.espn.com/apis/site/v2/sports/soccer/{eng.1\|fifa.world}/scoreboard?dates=YYYYMMDD` and `.../summary?event=ID` | Unofficial, **undocumented** public API. No key. It is subject to ESPN's Terms of Use (personal, non-commercial use). **The raw JSON must not be redistributed, and redistribution of ESPN-derived tables has not been verified as permitted.** See [TEAMMATE_SETUP.md](TEAMMATE_SETUP.md#9-data-sharing-rules). |
| **StatsBomb Open Data** | WC 2018 and 2022 only: **in-match formation changes** (Tactical Shift events), giving `active_formation_at_goal` and `tv_active_formation_at_interval_start`. Also an independent cross-check of goals (128/128 matches agree) and of starting formations. | https://github.com/statsbomb/open-data | Free for research under the StatsBomb Public Data User Agreement. **Attribution required: "Data provided by StatsBomb".** It has no EPL seasons in our scope and no WC 2026. |
| **football-data.co.uk** | EPL **pre-match betting odds**, converted to implied win/draw/loss and over-2.5-goals probabilities; we use these as the EPL team-strength control. Also an **independent full-time and half-time score check** for every EPL match. | https://www.football-data.co.uk/englandm.php (season files `mmz4281/{2324,…}/E0.csv`) | Free; credit football-data.co.uk. The 2026-27 file lags ESPN by 9 matches, which therefore have no odds. |
| **martj42/international_results** | Every international result since 1872. We use it to **compute pre-match World Football Elo ratings** for WC teams (the Elo is derived by our pipeline, not downloaded), and for neutral-venue and host-country flags. | https://github.com/martj42/international_results | CC0-1.0 (public domain). Credit is courteous. |
| **Hugging Face `eatpizzanot/soccer-dataset`** | **Formation cross-check only**: API-Football-derived lineups. ESPN agrees with it on 98.5% of team-matches. | https://huggingface.co/datasets/eatpizzanot/soccer-dataset | CC-BY-4.0. It has no goal timestamps, so it is not usable as a primary source. It may share an upstream provider with ESPN, so the agreement is a consistency check rather than independent validation. |

**Considered but not used.** API-Football, Sportmonks and football-data.org require keys or registration. FBref blocks automated requests (and we did not circumvent this). ClubElo returned a server error. `nlbair/openplay` does not exist (HTTP 404). The audit file gives the details.

---

## E. Data collection and cleaning

All steps are automated in `src/` and run with `python -m src.run_pipeline`.

1. **Downloading matches.** For each competition-season, ESPN's daily *scoreboard* endpoint is queried day by day. It returns HTTP 400 for date ranges, so it cannot be queried by range. This finds every event ID, and each completed match's *summary* JSON is then downloaded. Only matches completed on or before the cut-off (`CUTOFF_DATE = 2026-11-22`) are kept. Requests are spaced 0.35 s apart, with retries and exponential backoff. Raw responses go to a **write-once cache** in `data/raw/`, which is never overwritten, so builds are reproducible offline (`--skip-extract`).
2. **Formations.** Starting formations come from ESPN's `rosters[].formation`. Every label must be digits that sum to 10 outfield players. Coarse descriptors are derived from each label: `back_line` (first digit) and `n_forwards` (last digit). For WC 2018/22, StatsBomb Starting XI and Tactical Shift events give the shape in force at every minute.
3. **Goal timestamps.** ESPN `keyEvents` give the displayed minute, the stoppage notation (e.g. `90'+4'`), the period and the scoring team. The parser in `src/parse_espn.py` splits these into `goal_minute`, `stoppage_time_minute` and `original_goal_time` (e.g. `90+4`). Times have **minute resolution only; seconds are never invented.**
4. **Stoppage time.** Stoppage time is never folded into the next minute. A `45+2` goal is minute 45 plus 2 of first-half stoppage. **The period, not the minute, decides the half**: first-half stoppage goals go to interval 3 and second-half stoppage goals to interval 6. That is why intervals 3 and 6 are longer: their mean observed exposure is 19.2 and 22.5 minutes. 12% of goals are scored in stoppage time (524 of 4,354).
5. **Multiple goals in one match.** In `goal_events.csv` each goal is its own row, numbered by `goal_seq` (`goal_id = match_id-G01, G02, …`), with the running score after it. In the panel, goals in the same interval are summed into `goals_scored_in_interval`, and `scored_at_least_one_goal` is its 0/1 indicator.
6. **Own goals and penalties.** Own goals are credited to the benefiting team. All 163 own goals with parseable text were checked against ESPN's wording; there are 164 own goals in total. Penalties are flagged, and shoot-out kicks are excluded everywhere.
7. **Joining sources.** ESPN is the backbone, and every other source is matched onto ESPN matches:
   - **football-data.co.uk** is matched by an explicit team-name map (`src/team_names.py`; an unmapped name raises an error rather than being silently dropped) and a date within 1 day. 1,240 EPL matches are matched.
   - **StatsBomb** is matched on WC fixtures.
   - **martj42 results** are matched on the international fixtures.
   - **Hugging Face/API-Football lineups** are matched by fixture.
8. **Incomplete or conflicting records.**
   - **Linescore conflicts:** in 5 matches ESPN's per-half score field disagreed with its own goal events. The goal-event split was accepted only after an independent source confirmed it (football-data.co.uk or StatsBomb). The decision is recorded in `score_source`.
   - **Empty box scores:** 22 matches have all-zero placeholder box scores. These are set to **missing (NaN), not zero**. The matches stay in the sample because goals and formations are complete.
   - **Incomplete commentary:** in 1 match the commentary shot counts don't match the box score, so its time-varying shot/corner features are NaN.
   - **Missing odds:** the 9 most recent EPL matches are missing from football-data.co.uk, so their odds are NA.
   - No records are imputed or synthesised. A match enters the **primary sample** only if both formations exist *and* its goal events reconcile with the official score. In the baseline that is 1,481 / 1,481 matches.
9. **Validation.** `src/validate.py` runs automated checks; the baseline passes all 41 (`reports/validation_results.csv`). They include:
   - unique keys;
   - valid formation labels;
   - stoppage notation preserved;
   - regulation and half-time scores reconstructed from goal events;
   - EPL scores equal to football-data.co.uk;
   - WC goals equal to StatsBomb;
   - 12 panel rows per match;
   - panel goals summing to the score;
   - mirror consistency (my goals scored = opponent's goals conceded);
   - several **leakage checks**: pre-match rolling stats re-derived with an independent SQL window, time-varying counts zero at kickoff and non-decreasing, and no post-match columns in the panel.

   On top of these checks, `pytest` runs unit and dataset-integrity tests.

---

## F. Current dataset coverage

### F.1 Validated baseline (v1): use this for analysis

The counts below were read directly from `data/processed/*.csv` on 2026-11-22. The files are byte-identical (SHA-256) to the archived baseline in `snapshots/baseline_v1_20261122/`.

| File | Rows | Notes |
|---|---|---|
| `match_level.csv` | **1,481** | 1,249 EPL + 232 World Cup; 79 goalless matches retained |
| `goal_events.csv` | **4,354** | 4,339 in regulation + 15 in extra time; 524 in stoppage time; 315 penalties; 164 own goals |
| `team_interval_panel.csv` | **17,772** | = 1,481 matches × 2 teams × 6 intervals |

| Competition | Season | Matches | Regulation goals | Goals / match |
|---|---|---|---|---|
| Premier League | 2023-24 | 380 | 1,246 | 3.28 |
| Premier League | 2024-25 | 380 | 1,115 | 2.93 |
| Premier League | 2025-26 | 380 | 1,045 | 2.75 |
| Premier League | 2026-27 *(partial, to 22 Nov 2026)* | 109 | 299 | 2.74 |
| FIFA World Cup | 2018 | 64 | 166 (+3 ET) | 2.59 |
| FIFA World Cup | 2022 | 64 | 168 (+4 ET) | 2.63 |
| FIFA World Cup | 2026 | 104 | 300 (+8 ET) | 2.88 |

The 5 most common starting formations (team-matches) are 4-2-3-1 (1,420), 4-3-3 (480), 3-4-2-1 (359), 4-4-2 (160) and 4-1-4-1 (111). There are 21 distinct labels and 98 distinct unordered matchups; only 10 matchups have 30 or more matches. Full tables: [`reports/formation_frequencies.csv`](../reports/formation_frequencies.csv), [`reports/formation_matchup_frequencies.csv`](../reports/formation_matchup_frequencies.csv).

### F.2 Historical expansion (v2): IN PROGRESS

Another workstream is extending the EPL back to **2016-17** (10 complete seasons, 2016-17 to 2025-26, plus the partial 2026-27). The World Cups stay at 2018, 2022 and 2026. The expansion:

- writes to **`data/staging_v2/`** and **`reports_staging_v2/`** only;
- will replace `data/processed/` only after it passes **all** validation checks, the test suite and a baseline-preservation comparison (`src/promote.py`).

**Update (2026-11-22, after 14:48): v2 validated and promoted.** The 4 violations seen at 14:39 were resolved as follows (details in `reports/data_quality_report.md` §4):

- **Invalid formation labels:** these were ESPN's `3-4-3-d` (diamond) label, now accepted as valid, with the original string kept.
- **Goal events not reconciling / unresolved conflicts:** one match (ESPN-450867) had every goal listed twice in ESPN keyEvents. The exact duplicates were dropped and the count is recorded. In the other (ESPN-450779), ESPN credited an own goal to the wrong team, contradicting its own text. It was re-credited and flagged; the final score and football-data.co.uk agree.
- **Matches without formations:** 3 matches have no ESPN formation label. They are flagged and excluded from the panel, not filled in.

Final v2: 4,141 matches / 11,721 goals / 49,656 panel rows. 51/51 checks and 51/51 tests pass. `reports/baseline_preservation.csv` shows that no source-derived value of a v1 record changed (only rolling predictors did, because earlier history now exists).

---

## G. Variable dictionary

The complete column-by-column dictionary, with every column's role and allowed use, is in **[`reports/data_dictionary.md`](../reports/data_dictionary.md)**. The most important variables are listed below.

### Response variables

| Variable | Table | Type | Used for |
|---|---|---|---|
| `total_goals` | match_level | count (regulation only) | Q2 Poisson |
| `home_goals`, `away_goals` | match_level | count | Q1 (reshape to team rows) |
| `goals_scored_in_interval` | panel | count | interval Poisson (with exposure offset) |
| `scored_at_least_one_goal` | panel | 0/1 | Q3 logistic / hazard |
| `goal_minute` (+ `stoppage_time_minute`) | goal_events | minute | timing distributions |

### Pre-match predictors (`PRE` and `STRUCT`: valid in every model)

- **Formation:**
  - `starting_formation`, `opponent_starting_formation` (panel); `home_/away_starting_formation` (match);
  - `formation_matchup` (ordered), `formation_pair_unordered` (symmetric);
  - coarse descriptors: `back_line`, `n_forwards`, `back_line_matchup`.
- **Strength:**
  - EPL: `pre_odds_p_team_win`, `pre_odds_p_draw`, `pre_odds_p_over25`;
  - WC: `pre_elo_team`, `pre_elo_opponent`, `pre_elo_diff_home_minus_away`.
- **Style (rolling averages over the prior ≤10 matches):** `pre_team_possession_last10`, `pre_team_passes_last10`, `pre_team_long_ball_share_last10`, `pre_team_shots_last10`, plus goals for/against and points over the last 10.
- **Context:** `competition`, `season`, `stage`, `home_indicator`, `neutral_site`, `team_is_host_country`, `interval_number`.

### Time-varying predictors (`TV`: panel only, known at the *start* of the interval)

- `score_difference_at_interval_start`, `goals_for_before_interval`, `goals_against_before_interval`;
- `tv_own_/tv_opp_shot_any_before_interval`, `…_shot_ot_…`, `…_corner_…`, `…_red_…`, `…_sub_…`, `tv_man_advantage_at_interval_start`;
- `tv_active_formation_at_interval_start` (WC 2018/22 only).

### Post-match descriptive statistics (`POST`: never predictors)

All `post_*` columns in match_level (full-match possession, passes, shots, corners, cards, etc.). They are summaries of the match whose goals we are predicting, so using them would leak the outcome. They are useful for describing matches only.

### Exposure

`exposure_observed_minutes` is the number of minutes actually played in the interval, including stoppage time. Use it **only** as `log(exposure)` offset in interval Poisson models. It is known only after the interval ends, so it must not be used as a predictor.

### How information leakage is prevented

1. Every column carries a role tag (`PRE`, `TV`, `POST`, `EXPOSURE`, `RESPONSE`, `QA`, `PROV`, `ID`, `STRUCT`) in the data dictionary.
2. Rolling pre-match averages use **only earlier matches** (prior 10). This is checked against an independent SQL window computation, and a team's first match has no history (NA, not 0).
3. Time-varying features count only events **before** the interval starts. Validation checks that they are zero at kickoff and never decrease.
4. No `post_*` column appears in the panel (validated).
5. **Rule for the analysis:** never use `post_*`, `QA`, `PROV` or `exposure_*` columns as predictors. Don't use `half_time_*` goals to predict full-match goals. Don't use `goals_conceded_in_interval` to predict `goals_scored_in_interval` in the same interval.

---

## H. Proposed statistical methods

*The models are planned but not yet fitted.*

### Model 1: Poisson regression (goal counts: Q1, Q2)

- **Response:** team goals in regulation (two rows per match, built from `match_level`), or `total_goals` per match.
- **Model:** `log E[goals] = β₀ + formation effects + opponent-formation effects (+ matchup) + strength + home/neutral + season`.
- **Predictors:**
  - own and opponent formation: the 5 common labels plus "other", or `back_line` / `n_forwards`;
  - formation matchup (top pairs plus "other", or back-line matchup);
  - strength: `pre_odds_*` for the EPL, Elo difference for the WC, standardised within competition;
  - home / neutral / host;
  - season fixed effects;
  - optionally, pre-match style.
- **Dispersion check:** the baseline variance/mean ratio is about 1.0 for EPL team goals and about 1.26 for WC team goals. Test Poisson against negative binomial with a likelihood-ratio or Cameron–Trivedi test.

### Model 2: Logistic regression (goal timing: Q3, Q4)

- **Response:** `scored_at_least_one_goal` in each team-interval.
- **Model:** `logit P(score) = interval FE + formation + formation × interval + opponent formation + strength + TV covariates + season`.
- The **formation × interval** interaction directly tests whether some shapes score relatively earlier or later.
- **Variants:**
  - a discrete-time hazard for the **first goal**: keep each team's rows up to and including the interval of its first goal;
  - Poisson on `goals_scored_in_interval` with offset `log(exposure_observed_minutes)`, which allows two goals in one interval.
- **Q4:** fit nested models: formation + strength; then + pre-match style; then + time-varying game state. Compare them out-of-sample. The time-varying variables are partly *mediators* (game state), so report models both with and without them.

### Cross-cutting design choices

| Topic | Plan |
|---|---|
| **Formation interactions** | Too many labels for full interactions: 98 matchups, only 10 with ≥30 matches. Pool rare formations into "other", use formation families or back-line counts, or use regularisation / random effects for matchups. |
| **Team-strength controls** | Essential, because strong teams choose different formations *and* score more. The EPL uses betting-market probabilities (including `pre_odds_p_over25`, a strong baseline for total goals). The WC uses computed Elo. They are on different scales, so standardise within competition or fit competition-specific models. |
| **Season effects** | Season fixed effects. Scoring varies noticeably by season (3.28 in 2023-24 vs 2.75 in 2025-26). |
| **Competition comparison (Q5)** | Pooled model with a competition × formation-family interaction, or separate models with Wald tests of coefficient equality. Detailed matchups are not comparable across competitions, because no matchup reaches 30 WC matches. |
| **Clustered standard errors** | The 12 panel rows per match (and both team rows) are not independent. Use cluster-robust SEs by `match_id` (R: `sandwich::vcovCL(fit, cluster = ~match_id)`; Python: `statsmodels` `cov_type="cluster"`), or mixed models with random intercepts for team. |
| **Train / test by season** | Split by time, not at random, so the model never sees the future. Baseline example: train on 2023-24 and 2024-25, validate on 2025-26, test on 2026-27 (partial). For the World Cup, use leave-one-tournament-out. Once v2 is promoted, train on 2016-17 to 2022-23 and test on later seasons. Evaluate with held-out log-likelihood, Brier score (logistic) and calibration. |

---

## I. Limitations

1. **Starting formation vs the tactical shape in play.** Formation labels are a data provider's reading of the starting line-up, not an objective measurement. Teams shift shape in and out of possession. ESPN agrees with API-Football on 98.5% of team-matches, but with StatsBomb on only 79% (96% on number of defenders). Most disagreements are naming conventions, such as 3-4-2-1 vs 3-4-3.
2. **Missing formation-change data.** In-match changes are observed only for WC 2018 and 2022 (StatsBomb). There, teams averaged 1.4 tactical shifts per match, and the scorer's active formation differed from its starting formation at 17% of goals. For the EPL and WC 2026 we know only the starting formation, so results must say "starting formation".
3. **Historical differences in formation labels.** Labelling conventions and fashionable shapes change over time. In the *unvalidated* v2 staging data, 4-4-2 makes up about 12% of EPL team-matches in 2016-17 to 2022-23, against about 4% in 2023-24 onward. This matters most for the 2016-17+ expansion, so compare formation frequencies by era before pooling seasons, and include season effects.
4. **World Cup sample size.** 232 WC matches against 1,249 EPL matches. Only main effects and formation families are estimable for the WC.
5. **Different strength measures.** Betting odds (EPL) and computed Elo (WC) are not on the same scale, so cross-competition comparisons of strength-adjusted effects need care.
6. **Missing match statistics.**
   - 22 matches have empty box scores, so their rolling style features are partly NA.
   - There is no time-stamped xG.
   - 9 recent EPL matches lack odds.
   - In the v2 staging data, *all* of 2016-17 lacks box scores, so possession and passing style cannot be computed for that season.
7. **Observational data; no causal claims.** Coaches choose formations in response to the opponent, the expected game state, injuries and squad quality. Coefficients are adjusted associations, not the effect of switching formation.
8. **Other.** Goal times have minute resolution only. ESPN is an undocumented API and could change. WC "home" is mostly administrative. 2026-27 is a partial season.

---

## J. Next steps for teammates

These tasks have **not** been done yet. Use the validated v2 data in `data/processed/`.

1. **Exploratory data analysis.** Summary tables by competition and season, and missingness by column (use the role tags).
2. **Goal distributions.** Histograms of `total_goals` and team goals, compared with Poisson fits, and the variance/mean ratio by competition.
3. **Formation frequencies.** By competition and season. Decide the "top-k plus other" grouping or use back-line families.
4. **Formation-matchup counts.** Decide which matchups have enough data (e.g. ≥30 matches) to model separately.
5. **Goal timing by interval.** Scoring rate per interval, by competition and by formation family, and the distribution of `goal_minute`, including stoppage time.
6. **Model selection.** Poisson vs negative binomial. Choose the formation coding and interactions. Compare nested models with season-based held-out data.
7. **Regression diagnostics.** Dispersion, residuals by interval and season, calibration plots, influence, and sensitivity to excluding WC knockouts and the partial 2026-27 season.
8. **Final report and presentation.** Methods, results with clustered CIs, limitations (section I), and source acknowledgements (section D).

**Before you start:** read [TEAMMATE_SETUP.md](TEAMMATE_SETUP.md), and work on your own git branch.
