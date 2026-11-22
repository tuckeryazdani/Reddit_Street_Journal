from dataclasses import fields
from pathlib import Path

import pytest

from reddit_street_journal.config import Settings
from reddit_street_journal.mentions import MentionMatcher
from reddit_street_journal.tickers import build_universe

# A slice of the S&P 500, in Wikipedia's formatting, chosen to cover the awkward
# cases: legal suffixes, share classes, ambiguous names and short tickers.
CONSTITUENTS = [
    ("NVDA", "Nvidia"),
    ("META", "Meta Platforms"),
    ("INTC", "Intel"),
    ("UBER", "Uber"),
    ("AAPL", "Apple Inc."),
    ("TSLA", "Tesla, Inc."),
    ("GOOGL", "Alphabet Inc. (Class A)"),
    ("GOOG", "Alphabet Inc. (Class C)"),
    ("TGT", "Target Corporation"),
    ("COST", "Costco"),
    ("F", "Ford Motor Company"),
    ("MMM", "3M"),
    ("BRK.B", "Berkshire Hathaway"),
    ("MCD", "McDonald's"),
    ("AXP", "American Express"),
]


@pytest.fixture
def universe():
    return build_universe(CONSTITUENTS)


@pytest.fixture
def matcher(universe):
    return MentionMatcher(universe)


@pytest.fixture
def make_settings(tmp_path):
    """Build a Settings object with every credential filled in with a placeholder."""

    def _make(**overrides):
        values = {field.name: f"test-{field.name}" for field in fields(Settings)}
        values.update(
            subreddit="wallstreetbets",
            post_scan_limit=5,
            twitter_handle="WSB_Journal",
            twitter_mentions_max_results=10,
            openai_model="test-model",
            website_repo_path=None,
            website_html_path=None,
            state_dir=Path(tmp_path) / "state",
        )
        values.update(overrides)
        return Settings(**values)

    return _make
