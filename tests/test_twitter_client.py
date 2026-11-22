import pytest
import tweepy

from reddit_street_journal.twitter_client import TwitterClient


class FakeTweepyClient:
    def __init__(self, mentions=None, rate_limited=False):
        self.mentions = mentions or []
        self.rate_limited = rate_limited
        self.created = []
        self.searches = []

    def create_tweet(self, **kwargs):
        self.created.append(kwargs)

    def search_recent_tweets(self, **kwargs):
        self.searches.append(kwargs)
        if self.rate_limited:
            raise tweepy.TooManyRequests(FakeResponse())
        if not self.mentions:
            return {"meta": {"result_count": 0}}
        return {"data": self.mentions, "meta": {"result_count": len(self.mentions)}}


class FakeResponse:
    status_code = 429
    reason = "Too Many Requests"
    text = ""

    def json(self):
        return {}


def shout(text):
    return text.upper()


def test_post_sends_the_tweet(make_settings):
    fake = FakeTweepyClient()

    TwitterClient(make_settings(), client=fake).post("hello")

    assert fake.created == [{"text": "hello"}]


def test_post_refuses_text_over_the_limit(make_settings):
    fake = FakeTweepyClient()

    with pytest.raises(ValueError, match="281 characters"):
        TwitterClient(make_settings(), client=fake).post("x" * 281)

    assert fake.created == []


def test_reply_to_mentions_replies_to_each_new_tweet(make_settings):
    fake = FakeTweepyClient([{"id": 111, "text": "to the moon"}, {"id": 222, "text": "gm"}])

    replies = TwitterClient(make_settings(), client=fake).reply_to_mentions(shout)

    assert replies == 2
    assert fake.created == [
        {"text": "TO THE MOON", "in_reply_to_tweet_id": "111"},
        {"text": "GM", "in_reply_to_tweet_id": "222"},
    ]


def test_reply_to_mentions_never_answers_the_same_tweet_twice(make_settings):
    settings = make_settings()
    first_run = FakeTweepyClient([{"id": 111, "text": "to the moon"}])
    TwitterClient(settings, client=first_run).reply_to_mentions(shout)

    # A later run (a new process, in production) sees the old tweet and a new one.
    second_run = FakeTweepyClient([{"id": 111, "text": "to the moon"}, {"id": 222, "text": "gm"}])
    replies = TwitterClient(settings, client=second_run).reply_to_mentions(shout)

    assert replies == 1
    assert second_run.created == [{"text": "GM", "in_reply_to_tweet_id": "222"}]


def test_reply_to_mentions_excludes_the_bots_own_tweets(make_settings):
    fake = FakeTweepyClient()

    TwitterClient(make_settings(twitter_handle="WSB_Journal"), client=fake).reply_to_mentions(shout)

    assert fake.searches == [{"query": "@WSB_Journal -from:WSB_Journal", "max_results": 10}]


def test_reply_to_mentions_handles_no_results(make_settings):
    fake = FakeTweepyClient()

    assert TwitterClient(make_settings(), client=fake).reply_to_mentions(shout) == 0
    assert fake.created == []


def test_reply_to_mentions_truncates_long_replies(make_settings):
    fake = FakeTweepyClient([{"id": 111, "text": "hi"}])

    TwitterClient(make_settings(), client=fake).reply_to_mentions(lambda text: "x" * 500)

    assert len(fake.created[0]["text"]) == 280


def test_reply_to_mentions_backs_off_when_rate_limited(make_settings):
    fake = FakeTweepyClient(rate_limited=True)

    assert TwitterClient(make_settings(), client=fake).reply_to_mentions(shout) == 0
    assert fake.created == []
