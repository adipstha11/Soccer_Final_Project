# Football Tactical Analytics: formations, matchups and goal timing

This repository holds the data pipeline for the university statistics final project *"Predicting the Timing and Number of Goals in Football: The Role of Tactical Strategies and Formation Matchups in the Premier League and FIFA World Cup."*

It builds three linked, validated datasets from real match records, with no synthetic or imputed records. No models are fitted here yet.

📘 **New to the project?** Read **[docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md)** (the full explanation), then **[docs/TEAMMATE_SETUP.md](docs/TEAMMATE_SETUP.md)** (setup and loading data).

## Research questions

1. Do tactical (starting) formations predict goal counts?
2. Do formation matchups affect goal-scoring patterns?
3. Are certain formations associated with earlier or later goals?
4. Does attacking or tactical style improve predictive performance?
5. Do these relationships differ between the Premier League and the World Cup?

## Datasets (validated v2: 10 EPL seasons + partial 2026-27 + 3 World Cups)

| file | unit | rows |
|---|---|---|
| `data/processed/match_level.csv` | one completed match | 4,141 (4,138 fully usable) |
| `data/processed/goal_events.csv` | one in-match goal (shoot-out kicks excluded) | 11,721 (11,706 in regulation, 15 in extra time) |
| `data/processed/team_interval_panel.csv` | one team × match × 15-minute interval | 49,656 (= 4,138 × 12) |

The previous validated version (v1: 1,481 matches, EPL 2023-24 onward + World Cups) is preserved, with SHA-256 hashes, in `snapshots/baseline_v1_20261122/`. All match, goal and panel IDs are stable across versions.

Each file also has a `.parquet` copy. All three link on `match_id` (`ESPN-<event id>`). The panel's key is `(match_id, team_id, interval_number)`.

> **The processed datasets (`data/processed/`) are included in this repository.** Raw source caches (`data/raw/`, 1.7 GB, including ESPN raw JSON) are not, and the pipeline below rebuilds them. The tables derive largely from ESPN's unofficial public API, whose terms cover personal, non-commercial use. They are shared here for non-commercial academic coursework only; credit the sources listed below.

## Current validated coverage (data cut-off 2026-11-22)

| competition | season | matches (fully usable) | regulation goals (usable matches) |
|---|---|---|---|
| Premier League | 2016-17 | 380 | 1,064 |
| Premier League | 2017-18 | 380 (379) | 1,017 |
| Premier League | 2018-19 | 380 (378) | 1,066 |
| Premier League | 2019-20 | 380 | 1,034 |
| Premier League | 2020-21 | 380 | 1,024 |
| Premier League | 2021-22 | 380 | 1,071 |
| Premier League | 2022-23 | 380 | 1,084 |
| Premier League | 2023-24 | 380 | 1,246 |
| Premier League | 2024-25 | 380 | 1,115 |
| Premier League | 2025-26 | 380 | 1,045 |
| Premier League | 2026-27 (in progress) | 109 | 299 |
| FIFA World Cup | 2018 | 64 | 166 (+3 in extra time) |
| FIFA World Cup | 2022 | 64 | 168 (+4 in extra time) |
| FIFA World Cup | 2026 | 104 | 300 (+8 in extra time) |

Goal events reconcile with the official score in all 4,141 matches. Every EPL score agrees with football-data.co.uk. Three matches (one in 2017-18, two in 2018-19) have no ESPN formation label: they are flagged (`in_primary_sample = 0`) and excluded from the panel, never filled in. All 51 automated checks and 51 pytest tests pass (`reports/validation_results.csv`).

**v2 expansion (validated and promoted 2026-11-22).** EPL 2016-17 to 2022-23 was added from the same ESPN pipeline. It was built in `data/staging_v2/`, validated there, checked against the v1 baseline (`reports/baseline_preservation.csv`: no source-derived value changed; only rolling pre-match predictors changed, because earlier history now exists), and then promoted by `src/promote.py`. Details, coverage differences between eras and formation-matchup adequacy: [reports/historical_expansion_report.md](reports/historical_expansion_report.md).

## Sources and acknowledgements

| role | source | access |
|---|---|---|
| **Primary**: fixtures, starting formations, goal events, commentary-based shots/corners, red cards, substitutions, box scores | ESPN public site API, e.g. `https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary?event=704280` | no key; ESPN Terms of Use |
| In-match formation changes (WC 2018/2022); goal and formation cross-check | StatsBomb Open Data, https://github.com/statsbomb/open-data | no key; **"Data provided by StatsBomb"** |
| EPL pre-match odds; independent FT/HT score check | football-data.co.uk, https://www.football-data.co.uk/englandm.php | no key; credit the source |
| WC pre-match Elo (computed here); neutral-venue and host flags | martj42/international_results (CC0), https://github.com/martj42/international_results | no key |
| Formation cross-check only | eatpizzanot/soccer-dataset (CC-BY-4.0, API-Football-derived), https://huggingface.co/datasets/eatpizzanot/soccer-dataset | no key |

The full audit of 16 candidate sources is in `data/processed/source_audit.csv`. It records HTTP status, fields verified, licence and why each source was used or rejected. API-Football, Sportmonks and football-data.org need keys; FBref blocks automated access; `nlbair/openplay` returns 404. **No credentials or payments were needed.**

## Reproduce

```bash
git clone <REPO_URL> football_tactical_project && cd football_tactical_project
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                       # optional; no keys needed

python -m src.run_pipeline --pilot 3       # pilot: 3 matches per competition-season
python -m src.run_pipeline                 # full: extract -> build -> validate -> reports (~10 min first run)
python -m src.run_pipeline --skip-extract  # rebuild from cached raw data only
pytest tests -q                            # unit + dataset-integrity tests
```

`src/config.py` includes all 14 competition-seasons; a full first run downloads about 4,100 match summaries (~25 min). Historical raw JSON is stored separately in `data/raw/espn_historical/`.

Safe rebuild (staging → validate → compare → promote):
```bash
PROCESSED_DIR=data/staging_v2 REPORTS_DIR=reports_staging_v2 ESPN_INDEX=espn_event_index_v2.json \
  python -m src.run_pipeline --skip-extract --baseline-snapshot snapshots/baseline_v1_20261122
python -m src.promote --staging data/staging_v2 --reports-staging reports_staging_v2 \
  --index espn_event_index_v2.json --snapshot snapshots/baseline_v1_20261122
```
`promote` refuses to overwrite `data/processed/` unless validation, the baseline comparison and pytest (run against the staging files) all pass.

How the pipeline behaves:
- It uses rate limiting (0.35 s between requests), retries with exponential backoff, and a write-once raw cache.
- Raw files in `data/raw/` are never overwritten. `--refresh-current-season` saves a new, dated football-data.co.uk snapshot next to the old one.
- Logs go to `logs/`.

## Project structure

```
docs/PROJECT_OVERVIEW.md   full project explanation for teammates
docs/TEAMMATE_SETUP.md     setup, loading data, branches, data-sharing rules
src/config.py              scope, paths, interval scheme
src/http_client.py         rate limiting, retries, write-once cache
src/extract_espn.py        ESPN scoreboards + match summaries
src/extract_statsbomb.py   StatsBomb WC 2018/2022 events (formations, tactical shifts, goals)
src/extract_aux.py         football-data.co.uk, martj42 results, Hugging Face mirror
src/parse_espn.py          raw JSON -> matches / goals / timed events (stoppage parsing, interval rule)
src/team_names.py          explicit team-name maps (unmapped names raise an error)
src/elo.py                 World Football Elo, pre-match ratings
src/build_datasets.py      merging, adjudication, pre-match and time-varying features, the three datasets
src/validate.py            automated checks, coverage, formation frequency tables
src/reports.py             data dictionary, quality report, feasibility report, source audit
src/compare_baseline.py, src/expansion_report.py, src/promote.py   v2 expansion: compare, report, promote
tests/                     pytest suite
reports/                   data dictionary, quality and feasibility reports, frequency tables
data/                      (local only, not in Git) raw/, interim/, processed/, staging_v2/
```

## Importing

**Python**
```python
import pandas as pd
m = pd.read_csv("data/processed/match_level.csv", dtype={"season": str})
g = pd.read_csv("data/processed/goal_events.csv", dtype={"season": str})
p = pd.read_csv("data/processed/team_interval_panel.csv", dtype={"season": str}, low_memory=False)
# or: pd.read_parquet("data/processed/team_interval_panel.parquet")
```

**R**
```r
library(readr)
m <- read_csv("data/processed/match_level.csv", col_types = cols(season = col_character()))
g <- read_csv("data/processed/goal_events.csv", col_types = cols(season = col_character()))
p <- read_csv("data/processed/team_interval_panel.csv", col_types = cols(season = col_character()),
              guess_max = 20000)
# or: arrow::read_parquet("data/processed/team_interval_panel.parquet")
p$starting_formation <- relevel(factor(p$starting_formation), ref = "4-2-3-1")
# e.g. glm(scored_at_least_one_goal ~ factor(interval_number) + starting_formation + ..., family = binomial, data = p)
# with cluster-robust SEs: sandwich::vcovCL(fit, cluster = ~ match_id)
```

Read `season` as text: otherwise "2018" becomes a number and "2023-24" stays a string.

## Key definitions

- **Regulation goals** (`home_goals`, `away_goals`, `total_goals`) are 90 minutes plus stoppage. Extra-time goals are kept separately (`*_incl_extra_time`). Shoot-out kicks are never goals.
- **Own goals** are credited to the benefiting team. This was verified against ESPN's text ("Own Goal by X, *Team*") for all 409 own goals with parseable text (410 in total). One 2016-17 own goal that ESPN credited to the wrong team was re-credited from ESPN's own text, and the fix is flagged (`goal_attribution_corrected`).
- **Formation groups** (`*_formation_group`): 4-2-3-1 / 4-3-3 family / 4-4-2 family / back-3/5 with 1 or 3 forwards / back-3/5 with 2 forwards. The map is explicit in `build_datasets.FORMATION_GROUP`, and the original strings are kept. Use the groups for matchup interactions; exact matchups are sparse beyond the top ~15 pairs.
- **Rolling pre-match predictors** (`pre_*_last10`): previous ≤10 matches in the same competition, kickoff strictly earlier. EPL windows cross seasons but only within 365 days, so promoted clubs start with no history (no Championship data are invented). World Cup windows stay within the tournament.
- **Stoppage time** keeps its exact notation in `original_goal_time` (`45+2`, `90+4`). Goal times have minute resolution only; seconds are never invented.
- **Intervals**: `[0,15)`, `[15,30)`, `[30, end of 1H]`, `[45,60)`, `[60,75)`, `[75, end of 2H]`. They are based on the displayed minute plus the period, so first-half stoppage goes to interval 3 and second-half stoppage to interval 6. Extra time is excluded from the panel.
- **Formations** are *starting* formations from ESPN. The shape actually in force is observed only for WC 2018/2022 (`active_formation_at_goal`, `tv_active_formation_at_interval_start`, from StatsBomb).
- **Predictor roles**: every column is tagged in `reports/data_dictionary.md`.
  - `PRE`: pre-match predictors.
  - `TV`: known at interval start.
  - `POST`: post-match, descriptive only.
  - `EXPOSURE`: offset only.
  - `RESPONSE`: outcomes.
  - `QA` / `PROV`: validation and provenance.

  Columns prefixed `post_` must not be used to predict goals in the same match.

## Reports

- `reports/data_quality_report.md`: coverage, all checks, conflicts and how they were resolved, cross-provider formation agreement, missingness.
- `reports/feasibility_assessment.md`: what is answerable, adequate matchups, EPL vs WC, recommended models.
- `reports/data_dictionary.md`: every column, its role and its allowed use.
- `reports/historical_expansion_report.md`: v2 per-season coverage, era differences, formation frequencies, goals and timing by formation, matchup adequacy before vs after.
- `reports/baseline_preservation.csv`: column-by-column comparison of v1 records before and after expansion.
- `reports/*.csv`: validation results, coverage, formation and matchup frequencies.

## Limitations (summary)

Full discussion: [docs/PROJECT_OVERVIEW.md § I](docs/PROJECT_OVERVIEW.md#i-limitations).

1. Formation labels are a provider's interpretation of the starting shape. ESPN agrees with API-Football for 98% of team-matches (4,004 matches compared), but with StatsBomb for only 79% (96% on back-line count), mostly because of naming conventions. Label use also drifts across eras (e.g. 3-4-3 before about 2021 vs 3-4-2-1 later), so include season effects.
2. Formation changes are not observed for the EPL or WC 2026.
3. Tactical style is measured from pre-match rolling box-score averages (possession, passes, long-ball share) and in-match cumulative shots/corners. There is no time-stamped xG. ESPN has **no box scores for 2016-17**, and about 22% are missing in 2022-23, so possession and long-ball features are missing there. Commentary-based shot counts (`*_shots_comm*`) cover all seasons.
4. Pre-match strength is measured differently by competition: betting odds for the EPL, computed Elo for the World Cup.
5. The World Cup sample (232 matches, unchanged by the expansion) is too small to compare detailed formation matchups across competitions. Use formation groups.
6. 2026-27 is a partial season; 9 recent matches are not yet in football-data.co.uk, so they lack odds.
7. All effects are associations, not causal effects: formation choice responds to the opponent and the expected game state.

## Data terms

- **ESPN** data come from an unofficial public API under ESPN's Terms of Use (personal, non-commercial). Do not republish the raw JSON or the ESPN-derived tables in `data/`.
- **StatsBomb**: credit "Data provided by StatsBomb".
- **football-data.co.uk**, **martj42** and the **Hugging Face** dataset (CC-BY-4.0): credit the sources.
