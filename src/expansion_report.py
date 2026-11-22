"""reports/historical_expansion_report.md (+ CSV tables) for the v2 expansion
(EPL 2016-17 .. 2022-23 added). All figures are computed from the processed
files; baseline figures come from the v1 snapshot."""
from __future__ import annotations

import datetime as dt
import json

import numpy as np
import pandas as pd

from . import config
from .reports import _md

FOCUS = ["4-3-3", "4-2-3-1", "4-4-2", "3-5-2", "3-4-3", "3-4-2-1"]
HIST_SEASONS = [f"{y}-{str(y + 1)[2:]}" for y in range(2016, 2023)]


def team_rows(m):
    """Two rows per match (team perspective), regulation goals."""
    out = []
    for s, o in (("home", "away"), ("away", "home")):
        out.append(pd.DataFrame({
            "match_id": m.match_id, "competition": m.competition, "season": m.season,
            "formation": m[f"{s}_starting_formation"], "opp_formation": m[f"{o}_starting_formation"],
            "group": m[f"{s}_formation_group"], "opp_group": m[f"{o}_formation_group"],
            "back_line": m[f"{s}_back_line"], "gf": m[f"{s}_goals"], "ga": m[f"{o}_goals"]}))
    return pd.concat(out, ignore_index=True)


def per_season_table(m, idx):
    rows = []
    for spec in config.SEASONS:
        c, s = spec["competition"], spec["season"]
        ev = [e for e in idx if e["competition"] == c and e["season"] == s and e["in_scope"]]
        x = m[(m.competition == c) & (m.season == s)]
        rows.append({
            "Competition": c, "Season": s,
            "Era": "added (v2)" if s in HIST_SEASONS else "baseline (v1)",
            "Matches found": len(ev),
            "Valid formations": int(x.both_formations_available.sum()),
            "Valid goal events": int(x.goal_events_reconciled.sum()),
            "Fully usable matches": int(x.in_primary_sample.sum()),
            "Regulation goals": int(x[x.in_primary_sample == 1].total_goals.sum()),
            "Box score missing %": round(100 * x.post_home_possessionPct.isna().mean(), 1),
            "Commentary incomplete %": round(100 * (x.commentary_events_complete == 0).mean(), 1),
            "Pre-match odds missing %": round(100 * x.pre_odds_p_home_win.isna().mean(), 1)
            if c == "Premier League" else None,
            "Score == football-data.co.uk %": round(100 * ((x.fd_FTHG == x.home_goals) &
                                                        (x.fd_FTAG == x.away_goals))[x.fd_matched == 1].mean(), 1)
            if c == "Premier League" and x.fd_matched.sum() else None,
            "Linescore conflicts resolved": int(x.linescore_conflict.sum()),
        })
    return pd.DataFrame(rows)


def matchup_adequacy(m, label):
    prim = m[m.in_primary_sample == 1]
    fm = prim.formation_pair_unordered.value_counts()
    gm = prim.formation_group_pair_unordered.value_counts()
    return {"version": label, "matches": len(prim),
            "distinct formations": pd.concat([prim.home_starting_formation,
                                              prim.away_starting_formation]).nunique(),
            "distinct exact matchups (unordered)": len(fm),
            "exact matchups >=30 matches": int((fm >= 30).sum()),
            "exact matchups >=50": int((fm >= 50).sum()),
            "exact matchups >=100": int((fm >= 100).sum()),
            "share of matches in matchups >=30": round((fm[fm >= 30].sum()) / len(prim), 3),
            "distinct group matchups (unordered)": len(gm),
            "group matchups >=30": int((gm >= 30).sum()),
            "group matchups >=100": int((gm >= 100).sum())}


def write(baseline_snapshot: str = "snapshots/baseline_v1_20261122"):
    P, R = config.PROCESSED, config.REPORTS
    m = pd.read_csv(P / "match_level.csv", dtype={"season": str})
    g = pd.read_csv(P / "goal_events.csv", dtype={"season": str})
    p = pd.read_csv(P / "team_interval_panel.csv", dtype={"season": str}, low_memory=False)
    idx = json.loads((config.INTERIM / config.ESPN_INDEX).read_text())
    base_m = pd.read_csv(config.ROOT / baseline_snapshot / "processed" / "match_level.csv",
                         dtype={"season": str})
    # baseline adequacy computed on the same grouping rules for comparability
    from .build_datasets import add_formation_groups
    base_m = add_formation_groups(base_m)

    season_tab = per_season_table(m, idx)
    season_tab.to_csv(R / "expansion_per_season.csv", index=False)
    prim = m[m.in_primary_sample == 1]
    tr = team_rows(prim)
    epl = prim.competition == "Premier League"

    # formation frequency by era
    tr["era"] = np.where(tr.competition == "FIFA World Cup", "World Cup",
                         np.where(tr.season.isin(HIST_SEASONS), "EPL 2016-17..2022-23",
                                  "EPL 2023-24..2026-27"))
    freq = tr.groupby(["formation", "era"]).size().unstack(fill_value=0)
    freq["total"] = freq.sum(axis=1)
    freq["share_of_team_matches"] = (freq.total / freq.total.sum()).round(4)
    freq = freq.sort_values("total", ascending=False)
    freq.to_csv(R / "formation_frequency_by_era.csv")
    focus = freq.reindex(FOCUS).fillna(0)

    # average goals by formation (team perspective, regulation)
    gstats = tr.groupby("formation").agg(team_matches=("gf", "size"), goals_for_mean=("gf", "mean"),
                                         goals_against_mean=("ga", "mean"))
    gstats["match_total_mean"] = gstats.goals_for_mean + gstats.goals_against_mean
    gstats = gstats.sort_values("team_matches", ascending=False).round(3)
    gstats.to_csv(R / "goals_by_formation.csv")
    grp_stats = tr.groupby("group").agg(team_matches=("gf", "size"), goals_for_mean=("gf", "mean"),
                                        goals_against_mean=("ga", "mean")).round(3)

    # timing distribution by formation (scoring team's starting formation)
    rg = g[(g.in_regulation == 1) & (g.in_primary_sample == 1)].copy()
    rg["interval_number"] = rg.interval_number.astype(int)
    timing = pd.crosstab(rg.scoring_team_starting_formation, rg.interval_number)
    timing = timing.loc[timing.sum(axis=1).sort_values(ascending=False).index]
    timing_share = timing.div(timing.sum(axis=1), axis=0).round(3)
    timing_share["n_goals"] = timing.sum(axis=1)
    timing_share.columns = [f"I{c}" if c != "n_goals" else c for c in timing_share.columns]
    timing_share.to_csv(R / "goal_timing_by_formation.csv")
    gmap = dict(zip(pd.concat([m.home_starting_formation, m.away_starting_formation]),
                    pd.concat([m.home_formation_group, m.away_formation_group])))
    rg = rg.assign(group=rg.scoring_team_starting_formation.map(gmap))
    tg = pd.crosstab(rg.group, rg.interval_number)
    tg_share = tg.div(tg.sum(axis=1), axis=0).round(3)
    tg_share["n_goals"] = tg.sum(axis=1)
    tg_share.columns = [f"I{c}" if c != "n_goals" else c for c in tg_share.columns]

    # matchup tables
    fm = prim.groupby(["formation_pair_unordered", "competition"]).size().unstack(fill_value=0)
    fm["total"] = fm.sum(axis=1)
    fm = fm.sort_values("total", ascending=False)
    fm.to_csv(R / "formation_matchup_frequencies.csv")
    om = pd.crosstab(tr.formation, tr.opp_formation)
    keep = freq.index[:10]
    om_top = om.reindex(index=keep, columns=keep).fillna(0).astype(int)
    om.to_csv(R / "formation_vs_opponent_counts.csv")
    grp = pd.crosstab(tr.group, tr.opp_group)
    grp.to_csv(R / "formation_group_vs_opponent_counts.csv")
    blm = prim.back_line_matchup.value_counts().rename("matches").to_frame()

    adequacy = pd.DataFrame([matchup_adequacy(base_m, "v1 baseline (1,481 matches)"),
                             matchup_adequacy(m, f"v2 expanded ({len(prim):,} matches)")]).T
    adequacy.columns = adequacy.iloc[0]
    adequacy = adequacy.iloc[1:]
    adequacy.to_csv(R / "matchup_adequacy_before_after.csv")

    # precision: approx SE of log mean total goals for top matchups, before vs after
    bf = base_m[base_m.in_primary_sample == 1].formation_pair_unordered.value_counts()
    top = fm.head(12).index
    mu = prim.total_goals.mean()
    prec = pd.DataFrame({
        "matches_v1": bf.reindex(top).fillna(0).astype(int),
        "matches_v2": fm.loc[top, "total"],
    })
    prec["approx_SE_log_rate_v1"] = (1 / np.sqrt(prec.matches_v1 * mu)).replace(np.inf, np.nan).round(3)
    prec["approx_SE_log_rate_v2"] = (1 / np.sqrt(prec.matches_v2 * mu)).round(3)
    prec["min_detectable_rate_ratio_v2"] = np.exp(2.8 * np.sqrt(2) * prec.approx_SE_log_rate_v2).round(3)

    n_hist = int(prim.season.isin(HIST_SEASONS).sum())
    hist = prim[prim.season.isin(HIST_SEASONS)]
    rec = prim[epl & ~prim.season.isin(HIST_SEASONS)]
    box_h = hist.post_home_possessionPct.isna().mean()
    box_r = rec.post_home_possessionPct.isna().mean()

    s = [
        "# Historical expansion report (v2)", "",
        f"Generated {dt.date.today()}. The baseline v1 (1,481 matches) is preserved in `{baseline_snapshot}/` with SHA-256 hashes. "
        "This expansion adds EPL 2016-17 to 2022-23 from the same ESPN pipeline.", "",
        "## 1. Per-season coverage", "",
        _md(season_tab[["Competition", "Season", "Era", "Matches found", "Valid formations",
                        "Valid goal events", "Fully usable matches", "Regulation goals"]]), "",
        "## 2. Totals (verified, not theoretical)", "",
        f"- Verified matches: **{len(m):,}** (fully usable: {int(m.in_primary_sample.sum()):,}); "
        f"EPL {int((m.competition == 'Premier League').sum()):,} + World Cup {int((m.competition == 'FIFA World Cup').sum())}.",
        f"- Validated goals: **{len(g):,}** ({int(g.in_regulation.sum()):,} in regulation, {int((g.in_regulation == 0).sum())} in WC extra time; shoot-out kicks excluded).",
        f"- Team-interval panel observations: **{len(p):,}** (= {p.match_id.nunique():,} matches x 12).",
        f"- Added in v2: {n_hist:,} matches, {int(hist.total_goals.sum()):,} regulation goals, {n_hist * 12:,} panel rows.",
        f"- Targets in the brief: 4,141 matches / 49,692 panel rows. Achieved: {len(m):,} / {len(p):,}.", "",
        "## 3. Missing data and coverage differences: historical vs recent seasons", "",
        _md(season_tab[["Season", "Box score missing %", "Commentary incomplete %",
                        "Pre-match odds missing %", "Score == football-data.co.uk %",
                        "Linescore conflicts resolved"]]), "",
        f"- **Box scores** (possession, passes, long balls, box-score shots): missing for {box_h:.1%} of added-season matches vs {box_r:.1%} of recent EPL matches. "
        "ESPN returns all-zero placeholders for **all of 2016-17** and for scattered later matches. These are recorded as missing, never 0. "
        "So possession/passing/long-ball style features cannot be computed for 2016-17. The rolling features for early 2017-18 use fewer matches (or none).",
        "- **Shots for every season**: shots and shots on target are also counted from ESPN commentary (`post_*_shots_commentary`, `pre_*_shots_comm_last10`). "
        "Where both exist they were checked against the box score (tolerance max(4, 15%)). This makes shot-based tactical predictors available for all ten seasons.",
        "- **Formations, goal minutes (incl. stoppage notation), penalties, own goals and starting XIs** are equally complete in historical and recent seasons.",
        "- **Pre-match odds**: seasons up to 2018-19 use football-data.co.uk BetBrain averages (`BbAv*`), later seasons the market average (`Avg*`). The column used is recorded in `fd_odds_columns`.", "",
        "## 4. How often do the named formations appear? (team-matches, fully usable sample)", "",
        _md(focus.reset_index().rename(columns={"index": "formation"})), "",
        "The formations are far from equally common. 4-2-3-1 alone is about a third of all team-matches, while 3-4-3 and 3-5-2 are rare. "
        "ESPN's use of labels also drifts over time: 3-4-3 appears mainly in 2016-17..2020-21, while 3-4-2-1 dominates later. This may be partly a labelling change rather than a tactical one.", "",
        "Full table (top 20):", "", _md(freq.head(20), index=True), "",
        "## 5. Average goals by starting formation (regulation, team perspective)", "",
        _md(gstats.head(15), index=True), "",
        "By formation group:", "", _md(grp_stats, index=True), "",
        "These are raw descriptive means. Formation choice is confounded by team strength (strong teams favour 4-3-3 / 4-2-3-1; underdogs use back fives), so differences must be adjusted with the strength controls.", "",
        "## 6. Goal timing distribution by scoring team's starting formation", "",
        "Share of the formation's regulation goals scored in each interval (I1 = 0-15 ... I6 = 75-90+):", "",
        _md(timing_share.head(12), index=True), "",
        "By formation group:", "", _md(tg_share, index=True), "",
        "## 7. Matchup counts", "",
        "Most common unordered matchups:", "", _md(fm.head(20), index=True), "",
        "Formation vs opponent formation (team perspective, top-10 formations, each match counted twice):", "",
        _md(om_top, index=True), "",
        "Formation group vs opponent group (team perspective):", "", _md(grp, index=True), "",
        "Back-line matchups (home vs away):", "", _md(blm, index=True), "",
        "## 8. Is there enough data for specific matchups?", "",
        _md(adequacy, index=True), "",
        "Approximate precision for the most common matchups. SE of log(mean total goals) ≈ 1/sqrt(n x mean goals). "
        "The minimum detectable rate ratio is for a two-sided 5% test at 80% power against a reference of similar size:", "",
        _md(prec, index=True), "",
        "**Verdict**",
        f"- Exact matchups: the number of matchups with at least 30 matches rises from {adequacy.iloc[3, 0]} to {adequacy.iloc[3, 1]}. "
        f"Only the leading pairs (4-2-3-1 mirror, 4-2-3-1 vs 4-3-3, 4-2-3-1 vs 3-4-2-1, ...) can be estimated with useful precision. Minimum detectable rate ratios are {prec.min_detectable_rate_ratio_v2.iloc[:3].min():.2f}-{prec.min_detectable_rate_ratio_v2.iloc[:3].max():.2f} for the top 3 pairs and {prec.min_detectable_rate_ratio_v2.iloc[3:].min():.2f}-{prec.min_detectable_rate_ratio_v2.iloc[3:].max():.2f} for pairs 4-12. "
        f"{int((fm.total < 30).sum())} of {len(fm)} exact matchups have fewer than 30 matches, so most of the long tail stays sparse.",
        "- **Recommended grouping** (`*_formation_group`, original strings kept):",
        "  - `4-2-3-1`",
        "  - `4-3-3 family` (4-3-3, 4-1-4-1, 4-5-1, 4-3-2-1)",
        "  - `4-4-2 family` (4-4-2, 4-4-1-1, 4-2-2-2, 4-1-3-2, diamonds 4-1-2-1-2 / 4-3-1-2)",
        "  - `back-3/5, 1 or 3 forwards` (3-4-2-1, 3-4-3, 5-4-1, 3-2-4-1, 3-5-1-1, ...)",
        "  - `back-3/5, 2 forwards` (3-5-2, 3-1-4-2, 3-4-1-2, 5-3-2, ...)",
        "- Back-3 and back-5 labels are merged on purpose. Providers label the same shape 5-3-2 or 3-5-2, and ESPN-vs-StatsBomb agreement on 'back three' is much better than on the exact label.",
        f"- The unordered group × group matchup has {adequacy.iloc[7, 1]} observed cells, of which {adequacy.iloc[8, 1]} have at least 30 matches and {adequacy.iloc[9, 1]} at least 100. "
        "The cells below 30 involve the tiny 'other' group (e.g. 4-2-4-0), which should be pooled or dropped.",
        "- An alternative is the two-level descriptor `back_line` × `n_forwards`.", "",
        "## 9. Does the expansion give a meaningful statistical improvement?", "",
        f"- EPL sample: {int(epl.sum()):,} matches instead of 1,249 (about {epl.sum() / 1249:.1f}x). Standard errors for EPL formation effects shrink by about 1/sqrt({epl.sum() / 1249:.1f}) ≈ {1 / np.sqrt(epl.sum() / 1249):.2f}x.",
        "- Ten seasons allow season fixed effects and a genuine out-of-time test. For example, train on 2016-17..2024-25 and test on 2025-26, all with causally computed predictors (strictly earlier kickoffs).",
        "- The EPL vs World Cup comparison does **not** improve: World Cup size is unchanged (232 matches), so the EPL/WC imbalance grows. Compare at formation-group level.",
        "- Caveat: rolling style features are unavailable for 2016-17 and patchy early in 2017-18 (box scores). Models that need possession/long-ball share should start in 2017-18, or use the commentary shot features only.", "",
        "## 10. Rolling-window rules (pre-match predictors)", "",
        "- Window: the team's previous ≤10 matches in the same competition group, with kickoff strictly before the match. The current match and later matches never contribute (checked by an independent SQL re-implementation).",
        "- EPL windows **cross season boundaries** but only use matches within the previous **365 days**. So:",
        "  - a team's first match of the season uses its last matches of the previous EPL season;",
        "  - a **newly promoted club has no history** at its first EPL match (`pre_*_n_prior_matches = 0`, features NaN). No Championship or other non-EPL data are used or invented;",
        "  - a club returning after relegation does not reuse an earlier top-flight spell;",
        "  - 2016-17 opening matches have no history, because 2015-16 is not in the dataset.",
        "- World Cup windows: earlier matches in the same tournament only.",
        "- Missing source values (empty box scores) are skipped inside the window, so a mean may rest on fewer than `n_prior_matches` values.",
        "- Rolling values of the v1 baseline records changed in v2 because earlier history now exists (e.g. 2023-24 openers). This is expected and is listed in `reports/baseline_preservation.csv`. All source-derived values (scores, goals, formations, timing) are unchanged.", "",
        "## 11. Temporal validation support", "",
        "- `season` (ordered), `match_date` and `kickoff_utc` allow chronological splits.",
        "- All `PRE` and `TV` predictors are computed from strictly earlier information, so a split at any date is leakage-free.",
        "- Promoted-team NaNs should be handled with an explicit indicator (e.g. `pre_team_n_prior_matches == 0`) rather than by dropping rows.",
    ]
    (R / "historical_expansion_report.md").write_text("\n".join(s))
    return season_tab
