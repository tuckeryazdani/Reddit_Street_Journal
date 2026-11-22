"""The pipeline: extract from Reddit, load to Cloud SQL, analyse, publish."""

import logging
from collections.abc import Callable
from datetime import date

import pandas as pd

from reddit_street_journal import market_data, storage, tickers, website
from reddit_street_journal.config import Settings
from reddit_street_journal.llm import ReplyGenerator
from reddit_street_journal.mentions import MentionMatcher, extract_mentions
from reddit_street_journal.reddit_client import RedditScraper
from reddit_street_journal.report import TRADING_DAYS, TrendReport, compose_tweet
from reddit_street_journal.tickers import Universe
from reddit_street_journal.twitter_client import TwitterClient

logger = logging.getLogger(__name__)


class PublishError(RuntimeError):
    """Raised after the run when one or more publishing steps failed."""


def analyze(
    mentions: pd.DataFrame,
    universe: Universe,
    subreddit: str,
    today: date,
    fetch_closes: Callable[[str], pd.Series],
) -> TrendReport:
    """Pick the most-mentioned company and gather its price statistics.

    ``fetch_closes`` maps a ticker to its closing-price history. It is a
    parameter so the analysis can be tested without calling Yahoo Finance.
    """
    counts = mentions["stock"].value_counts()
    # Ties are broken alphabetically so that the result is deterministic.
    top_stock, top_count = min(counts.items(), key=lambda item: (-item[1], item[0]))
    company = universe.companies[top_stock]

    # One request serves both statistics: the recent change is the tail of the
    # full history that the seasonal averages need anyway.
    closes = fetch_closes(company.ticker)
    return TrendReport(
        as_of=today,
        subreddit=subreddit,
        company=company,
        mentions=int(top_count),
        price_change=market_data.price_change(closes.tail(TRADING_DAYS)),
        seasonal_returns=market_data.seasonal_returns(closes),
    )


def run(settings: Settings, *, dry_run: bool = False) -> str | None:
    """Run the pipeline once and return the tweet, or None if nothing was mentioned.

    With ``dry_run`` the pipeline reads from Reddit and Yahoo Finance and builds
    the tweet, but writes nothing: no database load, no tweet, no website push.
    """
    settings.validate(dry_run=dry_run)
    today = date.today()

    universe = tickers.load_universe(settings.state_dir)
    scraper = RedditScraper(settings)
    comments = scraper.iter_comments(settings.subreddit, settings.post_scan_limit)
    mentions = pd.DataFrame(extract_mentions(comments, MentionMatcher(universe)))
    if mentions.empty:
        logger.warning("No stock mentions found in r/%s", settings.subreddit)
        return None
    logger.info(
        "Found %d mentions of %d companies. Top 5: %s",
        len(mentions),
        mentions["stock"].nunique(),
        mentions["stock"].value_counts().head(5).to_dict(),
    )

    if not dry_run:
        storage.load_mentions(mentions, storage.cloud_sql_engine(settings))

    report = analyze(mentions, universe, settings.subreddit, today, market_data.fetch_closes)
    tweet = compose_tweet(report)
    if dry_run:
        logger.info("Dry run: skipped the database load and all publishing")
        return tweet

    _publish(tweet, settings, today)
    return tweet


def _publish(tweet: str, settings: Settings, today: date) -> None:
    """Run every publishing step, even if an earlier one fails, then report failures."""
    twitter = TwitterClient(settings)
    steps: dict[str, Callable[[], object]] = {"post tweet": lambda: twitter.post(tweet)}

    if settings.openai_api_key:
        steps["reply to mentions"] = lambda: twitter.reply_to_mentions(
            ReplyGenerator(settings).reply_to
        )
    else:
        logger.info("OPENAI_API_KEY not set; not replying to mentions")

    if settings.website_repo_path and settings.website_html_path:
        steps["update website"] = lambda: website.publish(
            tweet, settings.website_repo_path, settings.website_html_path, today
        )
    else:
        logger.info("WEBSITE_REPO_PATH / WEBSITE_HTML_PATH not set; not updating the website")

    failed = []
    for name, step in steps.items():
        try:
            step()
        except Exception:
            # The destinations are independent: a Twitter outage should not
            # stop the website update, and vice versa.
            logger.exception("Publishing step failed: %s", name)
            failed.append(name)
    if failed:
        raise PublishError(f"Publishing steps failed: {', '.join(failed)}")
