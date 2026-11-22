"""Turn the analysis into the text that gets published."""

from dataclasses import dataclass
from datetime import date

from reddit_street_journal.market_data import PriceChange, identify_season, next_season
from reddit_street_journal.tickers import Company

TWEET_LIMIT = 280
TRADING_DAYS = 7


@dataclass(frozen=True)
class TrendReport:
    as_of: date
    subreddit: str
    company: Company
    mentions: int
    price_change: PriceChange | None
    seasonal_returns: dict[str, float]


def compose_tweet(report: TrendReport) -> str:
    headline = [
        f"Top trending stock on r/{report.subreddit}",
        f"({report.as_of.isoformat()})",
        "",
        f"Stock: {report.company.display_name} ({report.company.ticker})",
        f"{report.mentions} mention{'' if report.mentions == 1 else 's'}",
    ]
    detail = _price_lines(report) + _seasonal_lines(report)

    # The headline is the point of the tweet. Detail lines are dropped from the
    # end until it fits, so a long company name can never make the post fail.
    while True:
        tweet = "\n".join(headline + ["", *detail] if detail else headline)
        if len(tweet) <= TWEET_LIMIT or not detail:
            return tweet
        detail.pop()


def _price_lines(report: TrendReport) -> list[str]:
    change = report.price_change
    if change is None:
        return []
    sign = "-" if change.absolute < 0 else "+"
    return [
        f"{sign}${abs(change.absolute):.2f} ({change.percent:+.2f}%) "
        f"over the past {TRADING_DAYS} trading days."
    ]


def _seasonal_lines(report: TrendReport) -> list[str]:
    returns = report.seasonal_returns
    current = identify_season(report.as_of)
    upcoming = next_season(current)
    if current not in returns or upcoming not in returns:
        return []  # not enough history, e.g. a recent IPO

    average = sum(returns.values()) / len(returns)
    versus_average = "better" if returns[current] > average else "worse"
    versus_current = "stronger" if returns[upcoming] > returns[current] else "weaker"
    return [
        f"Historically performs {versus_average} than its average in the {current}.",
        f"Next season ({upcoming}) tends to be {versus_current} than {current}.",
    ]
