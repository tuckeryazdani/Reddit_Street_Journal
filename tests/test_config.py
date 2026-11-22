from pathlib import Path

import pytest

from reddit_street_journal.config import ConfigError, Settings

REDDIT_ENV = {
    "REDDIT_CLIENT_ID": "id",
    "REDDIT_CLIENT_SECRET": "secret",
    "REDDIT_USER_AGENT": "agent",
}


@pytest.fixture
def clean_env(monkeypatch):
    """Run the test against an empty environment, whatever the developer has exported."""
    monkeypatch.setattr("os.environ", {})
    return monkeypatch


def test_defaults_apply_when_nothing_is_set(clean_env):
    settings = Settings.from_env()

    assert settings.subreddit == "wallstreetbets"
    assert settings.post_scan_limit == 100
    assert settings.twitter_handle == "WSB_Journal"
    assert settings.twitter_mentions_max_results == 10
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.state_dir == Path("state")
    assert settings.website_repo_path is None
    assert settings.reddit_client_id is None


def test_values_are_read_from_the_environment(clean_env):
    clean_env.setenv("SUBREDDIT", "stocks")
    clean_env.setenv("POST_SCAN_LIMIT", "25")
    clean_env.setenv("CLOUD_HOST", "project:region:instance")
    clean_env.setenv("WEBSITE_REPO_PATH", "/website")

    settings = Settings.from_env()

    assert settings.subreddit == "stocks"
    assert settings.post_scan_limit == 25
    assert settings.cloud_sql_instance == "project:region:instance"
    assert settings.website_repo_path == Path("/website")


def test_blank_values_count_as_unset(clean_env):
    clean_env.setenv("REDDIT_CLIENT_ID", "   ")
    clean_env.setenv("SUBREDDIT", "")

    settings = Settings.from_env()

    assert settings.reddit_client_id is None
    assert settings.subreddit == "wallstreetbets"


def test_legacy_twitter_path_is_still_honoured(clean_env):
    clean_env.setenv("TWITTER_PATH", "tweets.html")
    assert Settings.from_env().website_html_path == Path("tweets.html")

    clean_env.setenv("WEBSITE_HTML_PATH", "index.html")
    assert Settings.from_env().website_html_path == Path("index.html")


def test_dry_run_needs_only_reddit_credentials(clean_env):
    for name, value in REDDIT_ENV.items():
        clean_env.setenv(name, value)

    Settings.from_env().validate(dry_run=True)


def test_validate_names_every_missing_variable(clean_env):
    clean_env.setenv("REDDIT_CLIENT_ID", "id")

    with pytest.raises(ConfigError) as error:
        Settings.from_env().validate(dry_run=True)

    assert str(error.value) == (
        "Missing required environment variables: REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT"
    )


def test_live_run_also_needs_twitter_and_database_credentials(clean_env):
    for name, value in REDDIT_ENV.items():
        clean_env.setenv(name, value)

    with pytest.raises(ConfigError, match="TWITTER_API_KEY.*CLOUD_HOST.*DB_NAME"):
        Settings.from_env().validate(dry_run=False)
