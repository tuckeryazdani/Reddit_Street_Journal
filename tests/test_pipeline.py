from datetime import date, datetime

import pandas as pd
import pytest

from reddit_street_journal import pipeline
from reddit_street_journal.config import ConfigError
from reddit_street_journal.market_data import PriceChange
from reddit_street_journal.mentions import Comment


def mentions_frame(*stocks):
    return pd.DataFrame({"stock": list(stocks)})


def rising_closes(ticker):
    days = pd.date_range("2020-01-01", periods=1500, freq="D")
    return pd.Series(range(100, 1600), index=days, dtype=float)


def no_closes(ticker):
    return pd.Series(dtype=float)


def test_analyze_reports_the_most_mentioned_company(universe):
    mentions = mentions_frame("tesla", "nvidia", "nvidia", "apple", "nvidia")

    report = pipeline.analyze(
        mentions, universe, "wallstreetbets", date(2025, 10, 15), rising_closes
    )

    assert report.company.ticker == "NVDA"
    assert report.mentions == 3
    assert report.subreddit == "wallstreetbets"
    assert report.as_of == date(2025, 10, 15)
    # The last 7 closes are 1593..1599.
    assert report.price_change == PriceChange(absolute=6.0, percent=0.38)
    assert set(report.seasonal_returns) == {"Winter", "Spring", "Summer", "Fall"}


def test_analyze_breaks_ties_alphabetically(universe):
    mentions = mentions_frame("tesla", "apple", "tesla", "apple")

    report = pipeline.analyze(mentions, universe, "wallstreetbets", date(2025, 10, 15), no_closes)

    assert report.company.name == "apple"


def test_analyze_survives_missing_price_data(universe):
    report = pipeline.analyze(
        mentions_frame("nvidia"), universe, "wallstreetbets", date(2025, 10, 15), no_closes
    )

    assert report.price_change is None
    assert report.seasonal_returns == {}


class FakeScraper:
    comments = [
        Comment("NVDA to the moon", "alice", datetime(2025, 12, 26, 21, 0), "Daily thread"),
        Comment("nvidia and tesla", "bob", datetime(2025, 12, 26, 21, 5), "Daily thread"),
        Comment("precious metals only", "carol", datetime(2025, 12, 26, 21, 9), "Daily thread"),
    ]

    def __init__(self, settings):
        pass

    def iter_comments(self, subreddit, post_limit):
        return iter(self.comments)


@pytest.fixture
def offline_pipeline(monkeypatch, universe):
    """Replace every network dependency of ``run`` and record the side effects."""
    calls = []

    class RecordingTwitter:
        def __init__(self, settings):
            pass

        def post(self, text):
            calls.append(("tweet", text))

        def reply_to_mentions(self, generate_reply):
            calls.append(("replies",))

    monkeypatch.setattr(pipeline.tickers, "load_universe", lambda state_dir: universe)
    monkeypatch.setattr(pipeline, "RedditScraper", FakeScraper)
    monkeypatch.setattr(pipeline.market_data, "fetch_closes", rising_closes)
    monkeypatch.setattr(pipeline, "TwitterClient", RecordingTwitter)
    monkeypatch.setattr(pipeline, "ReplyGenerator", lambda settings: type("G", (), {"reply_to": 0}))
    monkeypatch.setattr(pipeline.storage, "cloud_sql_engine", lambda settings: "engine")
    monkeypatch.setattr(
        pipeline.storage,
        "load_mentions",
        lambda mentions, engine: calls.append(("load", sorted(mentions["stock"]))),
    )
    monkeypatch.setattr(
        pipeline.website,
        "publish",
        lambda tweet, repo, page, today: calls.append(("website", str(page))),
    )
    return calls


def test_dry_run_builds_the_tweet_without_side_effects(offline_pipeline, make_settings):
    # A dry run must work with nothing but Reddit credentials.
    settings = make_settings(twitter_api_key=None, db_password=None, cloud_sql_instance=None)

    tweet = pipeline.run(settings, dry_run=True)

    assert "Stock: Nvidia (NVDA)\n2 mentions" in tweet
    assert "+$6.00 (+0.38%) over the past 7 trading days." in tweet
    assert offline_pipeline == []


def test_live_run_loads_then_publishes_everywhere(offline_pipeline, make_settings, tmp_path):
    settings = make_settings(website_repo_path=tmp_path, website_html_path="index.html")

    tweet = pipeline.run(settings)

    assert offline_pipeline == [
        ("load", ["nvidia", "nvidia", "tesla"]),
        ("tweet", tweet),
        ("replies",),
        ("website", "index.html"),
    ]


def test_optional_destinations_are_skipped_when_not_configured(offline_pipeline, make_settings):
    pipeline.run(make_settings(openai_api_key=None))

    assert [call[0] for call in offline_pipeline] == ["load", "tweet"]


def test_one_failing_destination_does_not_block_the_others(
    offline_pipeline, make_settings, monkeypatch, tmp_path
):
    class BrokenTwitter:
        def __init__(self, settings):
            pass

        def post(self, text):
            raise ConnectionError("Twitter is down")

        def reply_to_mentions(self, generate_reply):
            raise ConnectionError("Twitter is down")

    monkeypatch.setattr(pipeline, "TwitterClient", BrokenTwitter)
    settings = make_settings(website_repo_path=tmp_path, website_html_path="index.html")

    with pytest.raises(pipeline.PublishError, match="post tweet, reply to mentions"):
        pipeline.run(settings)

    assert [call[0] for call in offline_pipeline] == ["load", "website"]


def test_no_mentions_means_nothing_is_stored_or_published(
    offline_pipeline, make_settings, monkeypatch
):
    monkeypatch.setattr(FakeScraper, "comments", [])

    assert pipeline.run(make_settings()) is None
    assert offline_pipeline == []


def test_live_run_refuses_to_start_with_missing_credentials(offline_pipeline, make_settings):
    settings = make_settings(twitter_api_key=None, db_password=None)

    with pytest.raises(ConfigError, match="TWITTER_API_KEY, DB_PASSWORD"):
        pipeline.run(settings)

    assert offline_pipeline == []
