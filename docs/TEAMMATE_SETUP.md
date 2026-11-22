# Teammate quick-start guide

This guide takes you from nothing to loading the data in Python or R. For what the project is about, read [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) first.

> **Analyse the validated v2 data in `data/processed/`** (4,141 matches / 11,721 goals / 49,656 panel rows; EPL 2016-17 to 2026-27 and three World Cups).
> v2 was validated and promoted on 2026-11-22. The previous v1 baseline is archived in `snapshots/baseline_v1_20261122/`.

---

## 1. Clone the repository

```bash
git clone <REPO_URL> football_tactical_project
cd football_tactical_project
```

Replace `<REPO_URL>` with the URL your teammate shares (GitHub → green **Code** button → copy HTTPS URL).

## 2. Python environment

Python 3.11 or newer is required; the project was built with 3.13.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

For analysis you will probably also want:

```bash
pip install statsmodels matplotlib jupyter
```

**R users:**

```r
install.packages(c("readr", "dplyr", "arrow", "sandwich", "lmtest", "MASS", "lme4"))
```

No API keys are needed. `.env.example` lists optional settings only. Never commit a `.env` file.

## 3. Get the processed datasets

The analysis needs only these three files, each also available as `.parquet`:

```
data/processed/match_level.csv
data/processed/goal_events.csv
data/processed/team_interval_panel.csv
```

**They are not in the Git repository.** They are derived from ESPN's public API, whose terms allow personal, non-commercial use, and we have not verified that redistributing ESPN-derived tables is allowed (see [section 9](#9-data-sharing-rules)). There are two ways to get them.

### Option A: rebuild them yourself (always allowed)

This downloads the public source data to your own machine and rebuilds the tables. It takes about 10 minutes on the first run and uses about 0.7 GB of raw cache for the baseline seasons.

```bash
source .venv/bin/activate
python -m src.run_pipeline --pilot 3   # quick smoke test: 3 matches per competition-season
python -m src.run_pipeline             # full build -> data/processed/ and reports/
```

> ⚠️ **While the v2 expansion is in progress**, the scope in `src/config.py` may already include the 2016-17 to 2022-23 seasons. In that case a full run also downloads those seasons (≈1 GB more, longer runtime) and builds the expanded tables. To reproduce exactly the v1 baseline, check out the baseline commit or tag once one exists, or ask the project lead. The baseline code is archived in `snapshots/baseline_v1_20261122/src/` on the lead's machine.

### Option B: get the files directly from the project lead

For coursework within the team, the project lead may hand you the processed CSVs privately, for example through a shared university drive. Put them in `data/processed/`. **Do not commit them to Git or post them publicly.**

Check that you have the right version:

```bash
wc -l data/processed/match_level.csv data/processed/goal_events.csv data/processed/team_interval_panel.csv
# expected (rows + 1 header line): 1482, 4355, 17773
```

On macOS, check the SHA-256 checksums against the lead's `SHA256SUMS` file:

```bash
shasum -a 256 data/processed/*.csv
```

## 4. Load the data

### Python

```python
import pandas as pd

m = pd.read_csv("data/processed/match_level.csv",        dtype={"season": str}, low_memory=False)
g = pd.read_csv("data/processed/goal_events.csv",        dtype={"season": str}, low_memory=False)
p = pd.read_csv("data/processed/team_interval_panel.csv", dtype={"season": str}, low_memory=False)
# Faster alternative: pd.read_parquet("data/processed/team_interval_panel.parquet")

print(len(m), len(g), len(p))   # 1481 4354 17772

# Example: join match-level strength onto goals
g2 = g.merge(m[["match_id", "pre_odds_p_over25", "pre_elo_diff_home_minus_away"]], on="match_id", how="left")
```

### R

```r
library(readr)
m <- read_csv("data/processed/match_level.csv",        col_types = cols(season = col_character()))
g <- read_csv("data/processed/goal_events.csv",        col_types = cols(season = col_character()))
p <- read_csv("data/processed/team_interval_panel.csv", col_types = cols(season = col_character()),
              guess_max = 20000)
# or: p <- arrow::read_parquet("data/processed/team_interval_panel.parquet")

p$starting_formation <- relevel(factor(p$starting_formation), ref = "4-2-3-1")
```

**Always read `season` as text.** Otherwise `"2018"` becomes a number while `"2023-24"` stays a string.

## 5. Understand the IDs

| ID | Format | Example | Meaning |
|---|---|---|---|
| `match_id` | `ESPN-<event id>` | `ESPN-704291` | One match. Joins all three tables. Look a match up at `https://www.espn.com/soccer/match/_/gameId/704291`. |
| `espn_event_id` | integer | `704291` | ESPN's native ID. |
| `goal_id` | `<match_id>-G<nn>` | `ESPN-704291-G03` | The 3rd goal of that match, in time order (`goal_seq`). |
| `panel_id` | `<match_id>-<team_id>-I<k>` | `ESPN-633794-655-I4` | Team 655 (Saudi Arabia), interval 4 of that match. |
| `team_id` | ESPN team id | `331` | Stable across seasons within a competition. Use it for team random effects. |

Panel key: `(match_id, team_id, interval_number)`. Each match has exactly 12 panel rows.

## 6. Which CSV for which analysis

| Analysis | File | Response | Notes |
|---|---|---|---|
| Total goals ~ formation matchup (Q2) | `match_level.csv` | `total_goals` | One row per match. Use `formation_pair_unordered`. |
| Team goals ~ own formation (Q1) | `match_level.csv`, reshaped to 2 rows per match | `home_goals` / `away_goals` | Or sum the panel by `(match_id, team_id)`. |
| Goal-minute distributions, time to first goal (Q3) | `goal_events.csv` | `goal_minute` | Filter `in_regulation == 1`. Goalless matches are absent here, so get them from match_level. |
| Scoring probability per 15 minutes (Q3, Q4) | `team_interval_panel.csv` | `scored_at_least_one_goal` | Cluster SEs by `match_id`. |
| Interval goal counts | `team_interval_panel.csv` | `goals_scored_in_interval` | Offset `log(exposure_observed_minutes)`. |
| EPL vs WC (Q5) | any; filter or interact on `competition` | | WC: use `neutral_site`, not `home_indicator`. |

**Leakage rule:** never use `post_*`, `QA`, `PROV` or `exposure_*` columns as predictors. Role tags for every column are in [`reports/data_dictionary.md`](../reports/data_dictionary.md).

## 7. Run the tests

```bash
source .venv/bin/activate
pytest tests -q
```

Use `pytest tests`, not plain `pytest`. A plain run also collects the archived copy of the tests under `snapshots/` (if present) and fails with an "import file mismatch".

After the v2 promotion (2026-11-22), the result is **51 passed** against `data/processed/`. The earlier "42 passed, 1 error" came from running the in-progress v2 code against v1 data, and is resolved.

## 8. Work on your own branch

Never commit directly to `main`.

```bash
git checkout main
git pull
git checkout -b analysis/<your-name>-<topic>       # e.g. analysis/sam-eda
# ... work ...
git add notebooks/eda.ipynb                        # add specific files, not "git add ."
git commit -m "EDA: goal distributions by competition"
git push -u origin analysis/<your-name>-<topic>
```

Then open a Pull Request on GitHub for review.

Suggested layout for analysis work, so it doesn't collide with the data pipeline:

```
analysis/       notebooks and scripts (Python or R)
figures/        exported plots (small PNG/PDF only)
```

**Never commit:**

- `data/raw/`, `data/interim/`, `data/processed/`, `data/staging_v2/`;
- `snapshots/`, `logs/`, `.env`, `.venv/`;
- large files.

Before committing, check with `git status` that you are adding only your own code, notes and figures.

## 9. Data-sharing rules

| Source | Can it be in the public repo? | What to do |
|---|---|---|
| ESPN raw JSON (`data/raw/espn*`) | **No.** ESPN Terms of Use: personal, non-commercial. | Rebuild locally (Option A). |
| ESPN-derived tables (`data/processed/`, `data/interim/`, `data/staging_v2/`) | **Not verified, so treat as no.** | Rebuild locally, or share privately within the team (Option B). |
| StatsBomb Open Data | Free for research with attribution. | Credit "Data provided by StatsBomb" in the report. |
| football-data.co.uk | Free to use. | Credit football-data.co.uk. |
| martj42/international_results | CC0 (public domain). | Credit as a courtesy. |
| Hugging Face `eatpizzanot/soccer-dataset` | CC-BY-4.0. | Credit the dataset (and API-Football). |
| Aggregated tables in `reports/` | Summary counts, no raw records. | Fine to include in the course report. |

## 10. Getting help

- What a column means → [`reports/data_dictionary.md`](../reports/data_dictionary.md)
- Data quality, conflicts and missingness → [`reports/data_quality_report.md`](../reports/data_quality_report.md)
- What is answerable, recommended models → [`reports/feasibility_assessment.md`](../reports/feasibility_assessment.md)
- Big picture → [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
