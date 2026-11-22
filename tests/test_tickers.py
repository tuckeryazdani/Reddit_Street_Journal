import json
import os
import time

import pytest

from reddit_street_journal import tickers
from reddit_street_journal.tickers import (
    build_universe,
    clean_company_name,
    load_constituents,
    parse_constituents,
)

WIKIPEDIA_SAMPLE = """
<html><body>
<table id="constituents" class="wikitable">
  <tr><th>Symbol</th><th>Security</th><th>GICS Sector</th></tr>
  <tr><td><a href="#">MMM</a></td><td><a href="#">3M</a></td><td>Industrials</td></tr>
  <tr><td><a href="#">aapl</a>\n</td><td><a href="#">Apple Inc.</a></td><td>IT</td></tr>
  <tr><td>BRK.B</td><td>Berkshire Hathaway</td><td>Financials</td></tr>
</table>
</body></html>
"""


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Apple Inc.", "Apple"),
        ("Tesla, Inc.", "Tesla"),
        ("Alphabet Inc. (Class A)", "Alphabet"),
        ("Coca-Cola Company (The)", "Coca-Cola"),
        ("The Walt Disney Company", "Walt Disney"),
        ("Deere & Company", "Deere"),
        ("Arthur J. Gallagher & Co.", "Arthur J. Gallagher"),
        ("Linde plc", "Linde"),
        ("Chubb Limited", "Chubb"),
        ("Lilly (Eli)", "Lilly"),
        ("Nvidia", "Nvidia"),
        ("Micron Technology", "Micron Technology"),
        ("Costco", "Costco"),  # ends in "co" but that is not a suffix here
    ],
)
def test_clean_company_name(raw, expected):
    assert clean_company_name(raw) == expected


def test_parse_constituents_reads_ticker_and_name_columns():
    assert parse_constituents(WIKIPEDIA_SAMPLE) == [
        ("MMM", "3M"),
        ("AAPL", "Apple Inc."),
        ("BRK.B", "Berkshire Hathaway"),
    ]


def test_parse_constituents_rejects_a_page_without_the_table():
    with pytest.raises(ValueError, match="constituents table"):
        parse_constituents("<html><body><p>Nothing here</p></body></html>")


def test_universe_uses_cleaned_names_and_keeps_display_casing(universe):
    apple = universe.companies["apple"]
    assert (apple.display_name, apple.ticker) == ("Apple", "AAPL")
    assert universe.companies["mcdonald's"].display_name == "McDonald's"


def test_universe_collapses_share_classes_onto_the_first_listing(universe):
    assert universe.companies["google"].ticker == "GOOGL"
    assert universe.symbols["GOOG"] == universe.symbols["GOOGL"] == "google"
    assert "alphabet" not in universe.companies


def test_universe_excludes_ambiguous_names_but_keeps_their_tickers(universe):
    assert "target" not in universe.aliases
    assert "3m" not in universe.aliases
    assert universe.symbols["TGT"] == "target"
    assert universe.companies["target"].ticker == "TGT"


def test_aliases_for_tickers_outside_the_universe_are_ignored():
    universe = build_universe([("NVDA", "Nvidia")])
    assert universe.aliases == {"nvidia": "nvidia"}


def test_load_constituents_scrapes_once_then_serves_the_cache(tmp_path):
    cache = tmp_path / "state" / "constituents.json"
    calls = []

    def fetch():
        calls.append(1)
        return [("NVDA", "Nvidia")]

    assert load_constituents(cache, fetch) == [("NVDA", "Nvidia")]
    assert load_constituents(cache, fetch) == [("NVDA", "Nvidia")]
    assert len(calls) == 1
    assert json.loads(cache.read_text()) == [["NVDA", "Nvidia"]]


def test_load_constituents_refreshes_an_expired_cache(tmp_path):
    cache = tmp_path / "constituents.json"
    cache.write_text(json.dumps([["OLD", "Old Co"]]))
    _age(cache, days=8)

    assert load_constituents(cache, lambda: [("NEW", "New Co")]) == [("NEW", "New Co")]
    assert json.loads(cache.read_text()) == [["NEW", "New Co"]]


def test_load_constituents_falls_back_to_a_stale_cache_when_the_scrape_fails(tmp_path):
    cache = tmp_path / "constituents.json"
    cache.write_text(json.dumps([["OLD", "Old Co"]]))
    _age(cache, days=8)

    def failing_fetch():
        raise ConnectionError("Wikipedia is down")

    assert load_constituents(cache, failing_fetch) == [("OLD", "Old Co")]


def test_load_constituents_raises_when_the_scrape_fails_and_there_is_no_cache(tmp_path):
    def failing_fetch():
        raise ConnectionError("Wikipedia is down")

    with pytest.raises(ConnectionError):
        load_constituents(tmp_path / "constituents.json", failing_fetch)


def test_fetch_rejects_a_suspiciously_short_table(monkeypatch):
    class Response:
        text = WIKIPEDIA_SAMPLE

        def raise_for_status(self):
            pass

    monkeypatch.setattr(tickers.requests, "get", lambda *args, **kwargs: Response())

    with pytest.raises(ValueError, match="Only 3 constituents"):
        tickers.fetch_constituents()


def _age(path, days):
    old = time.time() - days * 24 * 60 * 60
    os.utime(path, (old, old))
