"""Runtime configuration, read once from environment variables.

Nothing else in the package touches ``os.environ``; every module receives a
``Settings`` object instead. See ``.env.example`` for the full list of variables.
"""

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when required environment variables are missing."""


# Environment variable -> Settings attribute, grouped by when they are needed.
_REQUIRED_ALWAYS = {
    "REDDIT_CLIENT_ID": "reddit_client_id",
    "REDDIT_CLIENT_SECRET": "reddit_client_secret",
    "REDDIT_USER_AGENT": "reddit_user_agent",
}
_REQUIRED_FOR_LIVE_RUN = {
    "TWITTER_API_KEY": "twitter_api_key",
    "TWITTER_API_SECRET": "twitter_api_secret",
    "TWITTER_BEARER_TOKEN": "twitter_bearer_token",
    "TWITTER_ACCESS_TOKEN": "twitter_access_token",
    "TWITTER_ACCESS_TOKEN_SECRET": "twitter_access_token_secret",
    "CLOUD_HOST": "cloud_sql_instance",
    "DB_USER": "db_user",
    "DB_PASSWORD": "db_password",
    "DB_NAME": "db_name",
}


def _get(name: str) -> str | None:
    """Return an environment variable, treating blank values as unset."""
    return os.getenv(name, "").strip() or None


def _get_path(name: str) -> Path | None:
    value = _get(name)
    return Path(value) if value else None


@dataclass(frozen=True)
class Settings:
    # What to scan
    subreddit: str
    post_scan_limit: int

    # Reddit (username/password are optional; without them PRAW runs read-only)
    reddit_client_id: str | None
    reddit_client_secret: str | None
    reddit_user_agent: str | None
    reddit_username: str | None
    reddit_password: str | None

    # Twitter / X
    twitter_api_key: str | None
    twitter_api_secret: str | None
    twitter_bearer_token: str | None
    twitter_access_token: str | None
    twitter_access_token_secret: str | None
    twitter_handle: str
    twitter_mentions_max_results: int

    # OpenAI (optional; replies to @-mentions are skipped without a key)
    openai_api_key: str | None
    openai_model: str
    openai_character: str | None

    # Google Cloud SQL (MySQL)
    cloud_sql_instance: str | None
    db_user: str | None
    db_password: str | None
    db_name: str | None

    # Website publishing (optional; skipped unless both are set)
    website_repo_path: Path | None
    website_html_path: Path | None

    # Where the ticker cache and the replied-mentions ledger are kept
    state_dir: Path

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            subreddit=_get("SUBREDDIT") or "wallstreetbets",
            post_scan_limit=int(_get("POST_SCAN_LIMIT") or 100),
            reddit_client_id=_get("REDDIT_CLIENT_ID"),
            reddit_client_secret=_get("REDDIT_CLIENT_SECRET"),
            reddit_user_agent=_get("REDDIT_USER_AGENT"),
            reddit_username=_get("REDDIT_USERNAME"),
            reddit_password=_get("REDDIT_PASSWORD"),
            twitter_api_key=_get("TWITTER_API_KEY"),
            twitter_api_secret=_get("TWITTER_API_SECRET"),
            twitter_bearer_token=_get("TWITTER_BEARER_TOKEN"),
            twitter_access_token=_get("TWITTER_ACCESS_TOKEN"),
            twitter_access_token_secret=_get("TWITTER_ACCESS_TOKEN_SECRET"),
            twitter_handle=_get("TWITTER_HANDLE") or "WSB_Journal",
            twitter_mentions_max_results=int(_get("TWITTER_MAX_QUERY_RESULTS_FOR_MENTIONS") or 10),
            openai_api_key=_get("OPENAI_API_KEY"),
            openai_model=_get("OPENAI_MODEL") or "gpt-4o-mini",
            openai_character=_get("OPENAI_CHARACTER"),
            cloud_sql_instance=_get("CLOUD_HOST"),
            db_user=_get("DB_USER"),
            db_password=_get("DB_PASSWORD"),
            db_name=_get("DB_NAME"),
            website_repo_path=_get_path("WEBSITE_REPO_PATH"),
            # TWITTER_PATH is the variable's original name, still honoured.
            website_html_path=_get_path("WEBSITE_HTML_PATH") or _get_path("TWITTER_PATH"),
            state_dir=_get_path("STATE_DIR") or Path("state"),
        )

    def validate(self, *, dry_run: bool) -> None:
        """Fail fast, naming every missing variable at once.

        A dry run only reads from Reddit, so it needs far fewer credentials
        than a live run that also writes to Cloud SQL and posts to Twitter.
        """
        required = dict(_REQUIRED_ALWAYS)
        if not dry_run:
            required.update(_REQUIRED_FOR_LIVE_RUN)
        missing = [env for env, attr in required.items() if getattr(self, attr) is None]
        if missing:
            raise ConfigError(f"Missing required environment variables: {', '.join(missing)}")
