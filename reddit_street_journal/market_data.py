"""Price history from Yahoo Finance and the statistics derived from it."""

import logging
from dataclasses import dataclass
from datetime import date

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

SEASONS = ("Winter", "Spring", "Summer", "Fall")


@dataclass(frozen=True)
class PriceChange:
    absolute: float  # dollars
    percent: float


def yahoo_symbol(ticker: str) -> str:
    """Yahoo writes share classes with a dash: BRK.B -> BRK-B."""
    return ticker.replace(".", "-")


def fetch_closes(ticker: str) -> pd.Series:
    """Return the full daily closing-price history, or an empty series on failure.

    Yahoo Finance is an unofficial API that fails in many ways. Price data is
    garnish on the mention count, so a failure here should not sink the run.
    """
    try:
        history = yf.Ticker(yahoo_symbol(ticker)).history(period="max")
    except Exception:
        logger.warning("Could not fetch price history for %s", ticker, exc_info=True)
        return pd.Series(dtype=float)
    return history.get("Close", pd.Series(dtype=float)).dropna()


def price_change(closes: pd.Series) -> PriceChange | None:
    """Change from the first to the last close, or None if there are too few points."""
    if len(closes) < 2:
        return None
    first, last = float(closes.iloc[0]), float(closes.iloc[-1])
    return PriceChange(absolute=round(last - first, 2), percent=round((last / first - 1) * 100, 2))


def identify_season(day: date) -> str:
    """Return the season a date falls in (northern hemisphere, fixed equinox/solstice dates)."""
    month_day = (day.month, day.day)
    if (3, 20) <= month_day <= (6, 20):
        return "Spring"
    if (6, 21) <= month_day <= (9, 22):
        return "Summer"
    if (9, 23) <= month_day <= (12, 20):
        return "Fall"
    return "Winter"


def next_season(season: str) -> str:
    return SEASONS[(SEASONS.index(season) + 1) % len(SEASONS)]


def seasonal_returns(closes: pd.Series) -> dict[str, float]:
    """Average daily return (in percent) for each season, across the whole history.

    Returns are compared rather than price levels: a stock that has risen for
    twenty years has a higher average *price* in whichever season is most recent,
    which says nothing about seasonality.
    """
    daily_returns = closes.pct_change().dropna() * 100
    if daily_returns.empty:
        return {}
    by_season = daily_returns.groupby(daily_returns.index.map(identify_season)).mean()
    return {season: float(by_season[season]) for season in SEASONS if season in by_season}
