from datetime import date

from reddit_street_journal.market_data import PriceChange
from reddit_street_journal.report import TWEET_LIMIT, TrendReport, compose_tweet
from reddit_street_journal.tickers import Company

NVIDIA = Company(name="nvidia", display_name="Nvidia", ticker="NVDA")
SEASONAL = {"Winter": 0.05, "Spring": 0.10, "Summer": 0.20, "Fall": 0.25}


def make_report(**overrides):
    values = {
        "as_of": date(2025, 10, 15),  # Fall
        "subreddit": "wallstreetbets",
        "company": NVIDIA,
        "mentions": 98,
        "price_change": PriceChange(absolute=-3.2, percent=-1.75),
        "seasonal_returns": SEASONAL,
    }
    values.update(overrides)
    return TrendReport(**values)


def test_compose_tweet_full_report():
    assert compose_tweet(make_report()) == (
        "Top trending stock on r/wallstreetbets\n"
        "(2025-10-15)\n"
        "\n"
        "Stock: Nvidia (NVDA)\n"
        "98 mentions\n"
        "\n"
        "-$3.20 (-1.75%) over the past 7 trading days.\n"
        "Historically performs better than its average in the Fall.\n"
        "Next season (Winter) tends to be weaker than Fall."
    )


def test_detail_is_dropped_before_a_long_company_name_breaks_the_limit():
    company = Company("x", "Alexandria Real Estate Equities and Associated Partners", "ARE")
    full_length = len(compose_tweet(make_report())) + len(company.display_name) - len("Nvidia")
    assert full_length > TWEET_LIMIT  # the scenario under test

    tweet = compose_tweet(make_report(company=company))

    assert len(tweet) <= TWEET_LIMIT
    assert "Stock: Alexandria Real Estate Equities and Associated Partners (ARE)" in tweet
    assert "98 mentions" in tweet
    assert "over the past 7 trading days." in tweet
    assert "Next season" not in tweet


def test_positive_change_is_signed_and_single_mention_is_singular():
    tweet = compose_tweet(
        make_report(mentions=1, price_change=PriceChange(absolute=12.5, percent=4.0))
    )
    assert "1 mention\n" in tweet
    assert "+$12.50 (+4.00%) over the past 7 trading days." in tweet


def test_seasonal_wording_follows_the_numbers():
    tweet = compose_tweet(make_report(as_of=date(2025, 1, 15)))  # Winter, the weakest season
    assert "performs worse than its average in the Winter." in tweet
    assert "Next season (Spring) tends to be stronger than Winter." in tweet


def test_missing_price_data_is_left_out_rather_than_reported_as_zero():
    tweet = compose_tweet(make_report(price_change=None, seasonal_returns={}))
    assert tweet == (
        "Top trending stock on r/wallstreetbets\n(2025-10-15)\n\nStock: Nvidia (NVDA)\n98 mentions"
    )


def test_seasonal_lines_need_both_the_current_and_the_next_season():
    tweet = compose_tweet(make_report(seasonal_returns={"Fall": 0.25, "Summer": 0.2}))
    assert "season" not in tweet.lower()
    assert "over the past 7 trading days." in tweet
