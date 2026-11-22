"""Read comments from Reddit."""

import logging
from collections.abc import Iterator
from datetime import UTC, datetime

import praw

from reddit_street_journal.config import Settings
from reddit_street_journal.mentions import Comment

logger = logging.getLogger(__name__)


class RedditScraper:
    def __init__(self, settings: Settings, client: praw.Reddit | None = None) -> None:
        self._reddit = client or praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
            username=settings.reddit_username,
            password=settings.reddit_password,
            check_for_updates=False,  # no call to PyPI on every scheduled run
        )

    def iter_comments(self, subreddit: str, post_limit: int) -> Iterator[Comment]:
        """Yield every loaded comment on the subreddit's current hot posts."""
        for submission in self._reddit.subreddit(subreddit).hot(limit=post_limit):
            # limit=0 drops the "load more comments" stubs instead of fetching
            # them, which keeps a run to one request per post.
            submission.comments.replace_more(limit=0)
            for comment in submission.comments.list():
                yield Comment(
                    body=comment.body,
                    author=str(comment.author),
                    created_at=_naive_utc(comment.created_utc),
                    post_title=submission.title,
                )


def _naive_utc(timestamp: float) -> datetime:
    """Epoch seconds -> UTC datetime without tzinfo, as MySQL DATETIME stores it."""
    return datetime.fromtimestamp(timestamp, tz=UTC).replace(tzinfo=None)
