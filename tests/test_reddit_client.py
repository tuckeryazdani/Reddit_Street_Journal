from datetime import datetime
from types import SimpleNamespace

from reddit_street_journal.mentions import Comment
from reddit_street_journal.reddit_client import RedditScraper


class FakeCommentForest:
    def __init__(self, comments):
        self._comments = comments
        self.replace_more_limit = None

    def replace_more(self, limit):
        self.replace_more_limit = limit

    def list(self):
        return self._comments


class FakeReddit:
    def __init__(self, submissions):
        self.submissions = submissions
        self.requested = []

    def subreddit(self, name):
        def hot(limit):
            self.requested.append((name, limit))
            return self.submissions[:limit]

        return SimpleNamespace(hot=hot)


def submission(title, *comments):
    return SimpleNamespace(title=title, comments=FakeCommentForest(list(comments)))


def comment(body, author, created_utc):
    return SimpleNamespace(body=body, author=author, created_utc=created_utc)


def test_iter_comments_yields_every_comment_on_the_hot_posts(make_settings):
    first = submission("Daily thread", comment("NVDA", "alice", 1_700_000_000.0))
    second = submission("Earnings", comment("tesla", "bob", 1_700_000_060.0))
    reddit = FakeReddit([first, second, submission("Not scanned")])

    comments = list(RedditScraper(make_settings(), client=reddit).iter_comments("stocks", 2))

    assert reddit.requested == [("stocks", 2)]
    assert comments == [
        Comment("NVDA", "alice", datetime(2023, 11, 14, 22, 13, 20), "Daily thread"),
        Comment("tesla", "bob", datetime(2023, 11, 14, 22, 14, 20), "Earnings"),
    ]


def test_timestamps_are_utc_whatever_the_local_timezone(make_settings):
    reddit = FakeReddit([submission("Daily thread", comment("NVDA", "alice", 0.0))])

    [result] = RedditScraper(make_settings(), client=reddit).iter_comments("stocks", 1)

    assert result.created_at == datetime(1970, 1, 1, 0, 0, 0)
    assert result.created_at.tzinfo is None  # MySQL DATETIME has no timezone


def test_load_more_stubs_are_dropped_not_fetched(make_settings):
    post = submission("Daily thread", comment("NVDA", "alice", 0.0))

    list(RedditScraper(make_settings(), client=FakeReddit([post])).iter_comments("stocks", 1))

    assert post.comments.replace_more_limit == 0


def test_deleted_authors_are_recorded_as_text(make_settings):
    reddit = FakeReddit([submission("Daily thread", comment("[deleted]", None, 0.0))])

    [result] = RedditScraper(make_settings(), client=reddit).iter_comments("stocks", 1)

    assert result.author == "None"
