from types import SimpleNamespace

from reddit_street_journal.llm import DEFAULT_CHARACTER, ReplyGenerator


class FakeOpenAI:
    def __init__(self, reply):
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self._reply = reply

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        message = SimpleNamespace(content=self._reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_reply_uses_the_configured_model_and_character(make_settings):
    client = FakeOpenAI("  to the moon  ")
    settings = make_settings(openai_model="some-model", openai_character="You are a pirate.")

    reply = ReplyGenerator(settings, client=client).reply_to("is NVDA a buy?")

    assert reply == "to the moon"
    [request] = client.requests
    assert request["model"] == "some-model"
    assert request["messages"] == [
        {"role": "system", "content": "You are a pirate."},
        {"role": "user", "content": "Respond to this tweet: is NVDA a buy?"},
    ]


def test_a_default_character_is_used_when_none_is_configured(make_settings):
    client = FakeOpenAI("hi")

    ReplyGenerator(make_settings(openai_character=None), client=client).reply_to("hello")

    assert client.requests[0]["messages"][0]["content"] == DEFAULT_CHARACTER
