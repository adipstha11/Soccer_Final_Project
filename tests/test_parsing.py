"""Unit tests for parsing rules (no network, no data files needed)."""
import pytest

from src.build_datasets import formation_valid
from src.elo import g_mult, k_factor
from src.parse_espn import classify_commentary, interval_for, notation, parse_clock


@pytest.mark.parametrize("raw,expected", [
    ("23'", (23, 0)), ("45'+2'", (45, 2)), ("90'+13'", (90, 13)),
    ("105'+1'", (105, 1)), ("1'", (1, 0)), ("", (None, None)), (None, (None, None)),
])
def test_parse_clock(raw, expected):
    assert parse_clock(raw) == expected


def test_notation_preserves_stoppage():
    assert notation(45, 2) == "45+2"
    assert notation(90, 4) == "90+4"
    assert notation(67, 0) == "67"


@pytest.mark.parametrize("period,base,stp,iv", [
    (1, 1, 0, 1), (1, 15, 0, 1), (1, 16, 0, 2), (1, 30, 0, 2), (1, 31, 0, 3),
    (1, 45, 0, 3), (1, 45, 5, 3),          # first-half stoppage -> interval 3
    (2, 46, 0, 4), (2, 60, 0, 4), (2, 61, 0, 5), (2, 75, 0, 5), (2, 76, 0, 6),
    (2, 90, 0, 6), (2, 90, 9, 6),          # second-half stoppage -> interval 6
    (3, 95, 0, None), (4, 118, 0, None),   # extra time excluded
])
def test_interval_boundaries(period, base, stp, iv):
    assert interval_for(period, base, stp) == iv


def test_intervals_partition_regulation_minutes():
    """Every regulation minute maps to exactly one interval, monotonically."""
    seen = [interval_for(1, m, 0) for m in range(1, 46)] + \
           [interval_for(2, m, 0) for m in range(46, 91)]
    assert seen == sorted(seen)
    assert set(seen) == {1, 2, 3, 4, 5, 6}
    assert all(seen.count(k) == 15 for k in range(1, 7))


@pytest.mark.parametrize("f,ok", [
    ("4-2-3-1", True), ("3-4-2-1", True), ("4-4-2", True), ("4-1-2-1-2", True),
    ("3-4-3-d", True), ("4-4-3-d", False), ("4-4-3", False), ("442", False),
    (None, False), ("", False),
])
def test_formation_valid(f, ok):
    assert formation_valid(f) == ok


def test_commentary_classifier():
    assert classify_commentary(
        "Attempt saved. Richarlison (Tottenham Hotspur) right footed shot") == \
        ("shot_on_target", "Tottenham Hotspur")
    assert classify_commentary("Corner, Leeds United. Conceded by Ryan Gravenberch.") == \
        ("corner", "Leeds United")
    assert classify_commentary("Foul by Sander Berge (Fulham).") is None


def test_elo_parameters():
    assert k_factor("FIFA World Cup") == 60
    assert k_factor("FIFA World Cup qualification") == 40
    assert k_factor("Friendly") == 20
    assert g_mult(1) == 1 and g_mult(2) == 1.5 and g_mult(3) == pytest.approx(14 / 8)
