"""Generate in-character replies to tweets with an OpenAI chat model."""

import logging

from openai import OpenAI

from reddit_street_journal.config import Settings

logger = logging.getLogger(__name__)

DEFAULT_CHARACTER = (
    "You are a regular on the r/wallstreetbets subreddit. "
    "Reply to tweets with one short, funny message in that community's voice."
)


class ReplyGenerator:
    def __init__(self, settings: Settings, client: OpenAI | None = None) -> None:
        # The SDK retries rate-limit and connection errors with exponential
        # backoff, so there is no retry loop here.
        self._client = client or OpenAI(api_key=settings.openai_api_key, max_retries=5)
        self._model = settings.openai_model
        self._character = settings.openai_character or DEFAULT_CHARACTER

    def reply_to(self, tweet_text: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": self._character},
                {"role": "user", "content": f"Respond to this tweet: {tweet_text}"},
            ],
            max_tokens=150,  # keeps replies tweet-sized
        )
        return response.choices[0].message.content.strip()
