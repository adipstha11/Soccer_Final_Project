"""Central configuration: paths, competition/season scope, and constants."""
from __future__ import annotations

import os
from pathlib import Path

try:  # optional .env support
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:  # pragma: no cover
    pass

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = Path(os.getenv("INTERIM_DIR", ROOT / "data" / "interim"))
# Outputs can be redirected (staging builds) via environment variables, so a
# rebuild can be validated before it replaces the published files.
PROCESSED = Path(os.getenv("PROCESSED_DIR", ROOT / "data" / "processed"))
REPORTS = Path(os.getenv("REPORTS_DIR", ROOT / "reports"))
LOGS = ROOT / "logs"
# ESPN event index used for builds (written by extract_espn.run)
ESPN_INDEX = os.getenv("ESPN_INDEX", "espn_event_index.json")
for _p in (RAW, INTERIM, PROCESSED, REPORTS, LOGS):
    _p.mkdir(parents=True, exist_ok=True)

# Data cut-off (inclusive): only matches completed on/before this date are used.
CUTOFF_DATE = os.getenv("CUTOFF_DATE", "2026-11-22")

# Polite rate limiting for public endpoints (seconds between requests).
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.35"))
USER_AGENT = os.getenv(
    "HTTP_USER_AGENT", "football-tactical-research/1.0 (university coursework)"
)

# Optional credentials (NOT required by this pipeline; documented in .env.example)
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
FOOTBALL_DATA_ORG_TOKEN = os.getenv("FOOTBALL_DATA_ORG_TOKEN")
SPORTMONKS_TOKEN = os.getenv("SPORTMONKS_TOKEN")

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

# competition, season label, ESPN league slug, seed date (YYYYMMDD) or explicit window
# Historical EPL seasons (expansion v2). Their raw ESPN JSON is stored
# separately under data/raw/espn_historical/ to keep the baseline raw cache intact.
HIST = "espn_historical"
SEASONS = [
    {"competition": "Premier League", "season": "2016-17", "espn": "eng.1",
     "seed": "20161001", "fd_code": "1617", "raw": HIST},
    {"competition": "Premier League", "season": "2017-18", "espn": "eng.1",
     "seed": "20171014", "fd_code": "1718", "raw": HIST},
    {"competition": "Premier League", "season": "2018-19", "espn": "eng.1",
     "seed": "20181020", "fd_code": "1819", "raw": HIST},
    {"competition": "Premier League", "season": "2019-20", "espn": "eng.1",
     "seed": "20191019", "fd_code": "1920", "raw": HIST},
    {"competition": "Premier League", "season": "2020-21", "espn": "eng.1",
     "seed": "20201024", "fd_code": "2021", "raw": HIST},
    {"competition": "Premier League", "season": "2021-22", "espn": "eng.1",
     "seed": "20211016", "fd_code": "2122", "raw": HIST},
    {"competition": "Premier League", "season": "2022-23", "espn": "eng.1",
     "seed": "20221015", "fd_code": "2223", "raw": HIST},
    {"competition": "Premier League", "season": "2023-24", "espn": "eng.1",
     "seed": "20230812", "fd_code": "2324"},
    {"competition": "Premier League", "season": "2024-25", "espn": "eng.1",
     "seed": "20240817", "fd_code": "2425"},
    {"competition": "Premier League", "season": "2025-26", "espn": "eng.1",
     "seed": "20250816", "fd_code": "2526"},
    {"competition": "Premier League", "season": "2026-27", "espn": "eng.1",
     "seed": "20261018", "fd_code": "2627"},
    {"competition": "FIFA World Cup", "season": "2018", "espn": "fifa.world",
     "window": ("2018-06-14", "2018-07-15"), "sb": (43, 3)},
    {"competition": "FIFA World Cup", "season": "2022", "espn": "fifa.world",
     "window": ("2022-11-20", "2022-12-18"), "sb": (43, 106)},
    {"competition": "FIFA World Cup", "season": "2026", "espn": "fifa.world",
     "window": ("2026-06-11", "2026-07-19")},
]

EXPECTED_MATCHES = {
    **{("Premier League", f"{y}-{str(y + 1)[2:]}"): 380 for y in range(2016, 2023)},
    ("Premier League", "2023-24"): 380,
    ("Premier League", "2024-25"): 380,
    ("Premier League", "2025-26"): 380,
    ("Premier League", "2026-27"): None,  # in progress
    ("FIFA World Cup", "2018"): 64,
    ("FIFA World Cup", "2022"): 64,
    ("FIFA World Cup", "2026"): 104,
}

COMPLETED_STATUSES = {"STATUS_FULL_TIME", "STATUS_FINAL_AET", "STATUS_FINAL_PEN",
                      "STATUS_FINAL"}

# Interval scheme (elapsed-minute boundaries; displayed minute m == elapsed [m-1, m))
INTERVALS = [
    # number, label, half, first displayed minute, last displayed minute (None = +stoppage)
    (1, "0-15", 1, 1, 15),
    (2, "15-30", 1, 16, 30),
    (3, "30-45+", 1, 31, None),
    (4, "45-60", 2, 46, 60),
    (5, "60-75", 2, 61, 75),
    (6, "75-90+", 2, 76, None),
]
