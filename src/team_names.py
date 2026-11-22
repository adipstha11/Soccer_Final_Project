"""Explicit team-name normalisation maps (ESPN display name -> other sources).
Every ESPN team in scope must appear here; unmapped names raise instead of
being guessed."""

# ESPN -> football-data.co.uk (HomeTeam/AwayTeam columns)
ESPN_TO_FD = {
    "AFC Bournemouth": "Bournemouth", "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa", "Brentford": "Brentford",
    "Brighton & Hove Albion": "Brighton", "Burnley": "Burnley",
    "Chelsea": "Chelsea", "Coventry City": "Coventry",
    "Crystal Palace": "Crystal Palace", "Everton": "Everton", "Fulham": "Fulham",
    "Hull City": "Hull", "Ipswich Town": "Ipswich", "Leeds United": "Leeds",
    "Leicester City": "Leicester", "Liverpool": "Liverpool", "Luton Town": "Luton",
    "Manchester City": "Man City", "Manchester United": "Man United",
    "Newcastle United": "Newcastle", "Nottingham Forest": "Nott'm Forest",
    "Sheffield United": "Sheffield United", "Southampton": "Southampton",
    "Sunderland": "Sunderland", "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham", "Wolverhampton Wanderers": "Wolves",
    # historical seasons 2016-17 .. 2022-23
    "Cardiff City": "Cardiff", "Huddersfield Town": "Huddersfield",
    "Middlesbrough": "Middlesbrough", "Norwich City": "Norwich",
    "Stoke City": "Stoke", "Swansea City": "Swansea", "Watford": "Watford",
    "West Bromwich Albion": "West Brom",
}

# ESPN -> martj42 international_results names (identity unless listed)
ESPN_TO_INTL = {
    "Bosnia-Herzegovina": "Bosnia and Herzegovina", "Congo DR": "DR Congo",
    "Czechia": "Czech Republic", "Türkiye": "Turkey",
}

# ESPN -> StatsBomb names (identity for all WC 2018/2022 teams; verified
# programmatically in the pipeline: every ESPN WC 2018/2022 team name exists
# verbatim in StatsBomb matches).
ESPN_TO_SB: dict[str, str] = {}

# ESPN -> API-Football names as used in the Hugging Face dataset (national
# teams). Filled from observed values; identity otherwise.
ESPN_TO_APIF_NATIONAL = {
    "South Korea": "South Korea", "Bosnia-Herzegovina": "Bosnia & Herzegovina",
    "Congo DR": "Congo DR", "Czechia": "Czech Republic", "Türkiye": "Türkiye",
    "United States": "USA", "Ivory Coast": "Ivory Coast", "Curaçao": "Curacao",
    "Cape Verde": "Cape Verde Islands",
}


def to_fd(name: str) -> str:
    if name not in ESPN_TO_FD:
        raise KeyError(f"No football-data.co.uk mapping for ESPN team {name!r}")
    return ESPN_TO_FD[name]


def to_intl(name: str) -> str:
    return ESPN_TO_INTL.get(name, name)


def to_sb(name: str) -> str:
    return ESPN_TO_SB.get(name, name)
