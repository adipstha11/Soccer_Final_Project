"""Integrity tests on the processed datasets (run after the pipeline)."""
import pandas as pd
import pytest

from src import config, validate
from src.reports import describe

pytestmark = pytest.mark.skipif(
    not (config.PROCESSED / "match_level.csv").exists(),
    reason="run `python -m src.run_pipeline` first")


@pytest.fixture(scope="module")
def data():
    return validate.load()


@pytest.fixture(scope="module")
def checks(data):
    return validate.run_checks(*data)


def test_all_validation_checks_pass(checks):
    failed = checks[checks.passed == 0]
    assert failed.empty, "\n" + failed.to_string()


def test_every_column_documented(data):
    for df in data:
        missing = [c for c in df.columns if describe(c) is None]
        assert not missing, missing


def test_no_post_match_or_response_leak_into_panel_predictors(data):
    _, _, p = data
    assert not [c for c in p.columns if c.startswith("post_")]


def test_world_cup_2022_final(data):
    """Argentina 3-3 France (a.e.t.), Argentina won 4-2 on penalties."""
    m, g, _ = data
    r = m[(m.season == "2022") & (m.home_team == "Argentina") & (m.away_team == "France")].iloc[0]
    assert (r.home_goals, r.away_goals) == (2, 2)                       # regulation
    assert (r.home_goals_incl_extra_time, r.away_goals_incl_extra_time) == (3, 3)
    assert (r.home_shootout_goals, r.away_shootout_goals) == (4, 2)
    gg = g[g.match_id == r.match_id]
    assert len(gg) == 6                                                # no shoot-out kicks
    assert gg.penalty_indicator.sum() == 3                             # Messi 23', Mbappe 80', 118'
    assert set(gg[gg.in_regulation == 0].goal_period) == {"ET2"}


def test_own_goal_credit(data):
    """Burnley 1-4 Chelsea (2023-24): Al Dakhil (Burnley) own goal -> Chelsea."""
    _, g, _ = data
    og = g[(g.season == "2023-24") & (g.own_goal_indicator == 1) &
           (g.home_team == "Burnley") & (g.away_team == "Chelsea")]
    assert len(og) == 1 and og.iloc[0].scoring_team == "Chelsea"


def test_stoppage_notation_examples(data):
    _, g, _ = data
    assert {"45+2", "90+4"} <= set(g.original_goal_time)


def test_goalless_matches_present(data):
    m, _, p = data
    zero = m[m.total_goals == 0]
    assert len(zero) > 0
    assert set(zero.match_id) <= set(p.match_id)


def test_panel_size(data):
    m, _, p = data
    assert len(p) == 12 * int(m.in_primary_sample.sum())


def test_duplicate_keyevents_removed(data):
    """Liverpool 2-2 West Ham (2016-17): ESPN lists each goal twice."""
    m, g, _ = data
    r = m[m.match_id == "ESPN-450867"].iloc[0]
    assert r.n_duplicate_goal_events_removed == 4
    assert (g.match_id == "ESPN-450867").sum() == 4 and r.home_goals == 2 and r.away_goals == 2


def test_own_goal_credit_corrected_from_text(data):
    """Stoke 1-1 Everton (2016-17): Shawcross (Stoke) own goal must count for Everton."""
    _, g, _ = data
    og = g[(g.match_id == "ESPN-450779") & (g.own_goal_indicator == 1)].iloc[0]
    assert og.scoring_team == "Everton" and og.goal_attribution_corrected == 1


def test_missing_formations_flagged_not_filled(data):
    m, _, p = data
    miss = m[m.both_formations_available == 0]
    assert len(miss) > 0
    assert (miss.home_starting_formation.isna() | miss.away_starting_formation.isna()).all()
    assert (miss.in_primary_sample == 0).all()
    assert not set(miss.match_id) & set(p.match_id)


def test_ten_complete_epl_seasons(data):
    m, _, _ = data
    epl = m[(m.competition == "Premier League") & (m.season != "2026-27")]
    assert epl.season.nunique() == 10
    assert (epl.groupby("season").size() == 380).all()


def test_promoted_team_has_no_history_at_first_epl_match(data):
    """Sheffield United were promoted for 2019-20 (not in EPL 2016-19)."""
    m, _, _ = data
    epl = m[m.competition == "Premier League"].sort_values("kickoff_utc")
    first = epl[(epl.home_team == "Sheffield United") | (epl.away_team == "Sheffield United")].iloc[0]
    side = "home" if first.home_team == "Sheffield United" else "away"
    assert first.season == "2019-20"
    assert first[f"pre_{side}_n_prior_matches"] == 0
    assert pd.isna(first[f"pre_{side}_gf_last10"])


def test_rolling_window_never_older_than_365_days(data):
    """Fulham: relegated 2018-19, back 2020-21, relegated 2020-21, back 2022-23.
    First match of 2022-23 must not use the 2020-21 spell (>365 days earlier)."""
    m, _, _ = data
    epl = m[(m.competition == "Premier League") & (m.season == "2022-23")].sort_values("kickoff_utc")
    first = epl[(epl.home_team == "Fulham") | (epl.away_team == "Fulham")].iloc[0]
    side = "home" if first.home_team == "Fulham" else "away"
    assert first[f"pre_{side}_n_prior_matches"] == 0
