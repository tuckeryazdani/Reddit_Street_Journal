"""Post to Twitter/X and reply to tweets that mention the bot."""

import logging
from collections.abc import Callable

import tweepy

from reddit_street_journal.config import Settings
from reddit_street_journal.report import TWEET_LIMIT

logger = logging.getLogger(__name__)

REPLIED_LEDGER = "replied_mentions.txt"


class TwitterClient:
    def __init__(self, settings: Settings, client: tweepy.Client | None = None) -> None:
        self._client = client or tweepy.Client(
            bearer_token=settings.twitter_bearer_token,
            consumer_key=settings.twitter_api_key,
            consumer_secret=settings.twitter_api_secret,
            access_token=settings.twitter_access_token,
            access_token_secret=settings.twitter_access_token_secret,
            return_type=dict,
        )
        self._handle = settings.twitter_handle
        self._max_results = settings.twitter_mentions_max_results
        self._ledger_path = settings.state_dir / REPLIED_LEDGER

    def post(self, text: str) -> None:
        if len(text) > TWEET_LIMIT:
            raise ValueError(f"Tweet is {len(text)} characters; the limit is {TWEET_LIMIT}")
        self._client.create_tweet(text=text)
        logger.info("Posted tweet (%d characters)", len(text))

    def reply_to_mentions(self, generate_reply: Callable[[str], str]) -> int:
        """Reply once to each recent tweet that mentions the bot. Returns the reply count.

        Tweet ids that have been answered are appended to a ledger file, so a
        tweet is never answered twice across runs. Mount ``STATE_DIR`` as a
        volume when running in a container, or the ledger is lost with it.
        """
        already_replied = self._read_ledger()
        try:
            response = self._client.search_recent_tweets(
                # Exclude the bot's own tweets so it can never reply to itself.
                query=f"@{self._handle} -from:{self._handle}",
                max_results=self._max_results,
            )
        except tweepy.TooManyRequests:
            logger.warning("Twitter rate limit reached; skipping mentions this run")
            return 0

        replies = 0
        for tweet in response.get("data") or []:
            tweet_id = str(tweet["id"])
            if tweet_id in already_replied:
                continue
            reply = generate_reply(tweet["text"])[:TWEET_LIMIT]
            self._client.create_tweet(text=reply, in_reply_to_tweet_id=tweet_id)
            # Recorded immediately, so a crash on a later tweet cannot cause a
            # duplicate reply to this one on the next run.
            self._record_reply(tweet_id)
            replies += 1

        logger.info("Replied to %d new mention(s)", replies)
        return replies

    def _read_ledger(self) -> set[str]:
        if not self._ledger_path.exists():
            return set()
        return set(self._ledger_path.read_text(encoding="utf-8").split())

    def _record_reply(self, tweet_id: str) -> None:
        self._ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self._ledger_path.open("a", encoding="utf-8") as ledger:
            ledger.write(tweet_id + "\n")
