from datetime import date

import pandas as pd
import pytest

from reddit_street_journal import market_data
from reddit_street_journal.market_data import (
    PriceChange,
    identify_season,
    next_season,
    price_change,
    seasonal_returns,
    yahoo_symbol,
)


@pytest.mark.parametrize(
    ("day", "season"),
    [
        (date(2025, 1, 1), "Winter"),
        (date(2024, 2, 29), "Winter"),
        (date(2025, 3, 19), "Winter"),
        (date(2025, 3, 20), "Spring"),
        (date(2025, 6, 20), "Spring"),
        (date(2025, 6, 21), "Summer"),
        (date(2025, 9, 22), "Summer"),
        (date(2025, 9, 23), "Fall"),
        (date(2025, 12, 20), "Fall"),
        (date(2025, 12, 21), "Winter"),
        (date(2025, 12, 31), "Winter"),
    ],
)
def test_identify_season_boundaries(day, season):
    assert identify_season(day) == season


def test_next_season_wraps_around_the_year():
    assert next_season("Summer") == "Fall"
    assert next_season("Fall") == "Winter"


def test_yahoo_symbol_translates_share_classes():
    assert yahoo_symbol("BRK.B") == "BRK-B"
    assert yahoo_symbol("NVDA") == "NVDA"


def test_price_change_compares_first_and_last_close():
    closes = pd.Series([100.0, 90.0, 120.0, 110.0])
    assert price_change(closes) == PriceChange(absolute=10.0, percent=10.0)


def test_price_change_can_be_negative():
    assert price_change(pd.Series([200.0, 150.0])) == PriceChange(absolute=-50.0, percent=-25.0)


def test_price_change_needs_two_points():
    assert price_change(pd.Series([100.0])) is None
    assert price_change(pd.Series(dtype=float)) is None


def test_seasonal_returns_averages_daily_returns_by_season():
    # Two years of prices that gain 1% every winter day and are flat otherwise.
    days = pd.date_range("2023-01-01", "2024-12-31", freq="D", tz="America/New_York")
    growth = [1.01 if identify_season(day) == "Winter" else 1.0 for day in days]
    closes = pd.Series(growth, index=days).cumprod() * 100

    returns = seasonal_returns(closes)

    assert set(returns) == {"Winter", "Spring", "Summer", "Fall"}
    assert returns["Winter"] == pytest.approx(1.0)
    assert returns["Spring"] == pytest.approx(0.0, abs=1e-9)
    assert returns["Summer"] == pytest.approx(0.0, abs=1e-9)


def test_seasonal_returns_omits_seasons_with_no_history():
    days = pd.date_range("2025-07-01", "2025-07-31", freq="D")
    closes = pd.Series(range(100, 100 + len(days)), index=days, dtype=float)
    assert set(seasonal_returns(closes)) == {"Summer"}


def test_seasonal_returns_of_an_empty_history_is_empty():
    assert seasonal_returns(pd.Series(dtype=float)) == {}


def test_fetch_closes_returns_an_empty_series_when_yahoo_fails(monkeypatch):
    def broken_ticker(symbol):
        raise ConnectionError("Yahoo is down")

    monkeypatch.setattr(market_data.yf, "Ticker", broken_ticker)

    assert market_data.fetch_closes("NVDA").empty


def test_fetch_closes_requests_the_yahoo_symbol(monkeypatch):
    requested = []

    class FakeTicker:
        def __init__(self, symbol):
            requested.append(symbol)

        def history(self, period):
            return pd.DataFrame({"Close": [1.0, None, 2.0]})

    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)

    closes = market_data.fetch_closes("BRK.B")

    assert requested == ["BRK-B"]
    assert closes.tolist() == [1.0, 2.0]
