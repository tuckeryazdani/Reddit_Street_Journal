import pytest

from reddit_street_journal import __main__ as cli
from reddit_street_journal.config import ConfigError
from reddit_street_journal.pipeline import PublishError


@pytest.fixture
def fake_run(monkeypatch):
    """Replace the pipeline with a recorder, and isolate the CLI from the real environment."""
    calls = []
    outcome = {"result": "the tweet"}

    def run(settings, *, dry_run):
        calls.append((settings, dry_run))
        if isinstance(outcome["result"], Exception):
            raise outcome["result"]
        return outcome["result"]

    monkeypatch.setattr("os.environ", {})
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr(cli, "run", run)
    return calls, outcome


def test_prints_the_tweet_and_exits_zero(fake_run, capsys):
    calls, _ = fake_run

    assert cli.main([]) == 0

    assert capsys.readouterr().out == "the tweet\n"
    [(settings, dry_run)] = calls
    assert dry_run is False
    assert (settings.subreddit, settings.post_scan_limit) == ("wallstreetbets", 100)


def test_flags_override_the_environment(fake_run):
    calls, _ = fake_run

    cli.main(["--dry-run", "--subreddit", "stocks", "--limit", "5"])

    [(settings, dry_run)] = calls
    assert dry_run is True
    assert (settings.subreddit, settings.post_scan_limit) == ("stocks", 5)


def test_nothing_is_printed_when_there_were_no_mentions(fake_run, capsys):
    _, outcome = fake_run
    outcome["result"] = None

    assert cli.main([]) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("error", "exit_code"),
    [(ConfigError("Missing required environment variables: X"), 2), (PublishError("boom"), 1)],
)
def test_known_failures_become_exit_codes_not_tracebacks(fake_run, error, exit_code):
    _, outcome = fake_run
    outcome["result"] = error

    assert cli.main([]) == exit_code
