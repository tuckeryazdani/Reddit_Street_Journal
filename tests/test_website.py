import subprocess
from datetime import date

import pytest

from reddit_street_journal.website import insert_tweet, publish

PAGE = "<html>\n<body>\n<h1>The Reddit Street Journal</h1>\n</body>\n</html>\n"


def git(cwd, *args):
    result = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout


def test_insert_tweet_adds_the_block_at_the_top_of_the_body():
    page = insert_tweet(PAGE, "Stock: Nvidia\n98 mentions")

    assert page.startswith(
        '<html>\n<body>\n\n<br><br> <blockquote class="twitter-tweet">'
        "Stock: Nvidia<br>98 mentions</blockquote>\n<h1>"
    )
    assert page.endswith("</body>\n</html>\n")


def test_insert_tweet_puts_the_newest_tweet_first():
    page = insert_tweet(insert_tweet(PAGE, "older"), "newer")

    assert page.index("newer") < page.index("older")


def test_insert_tweet_escapes_html():
    page = insert_tweet(PAGE, "AT&T <script>alert(1)</script>")

    assert "AT&amp;T &lt;script&gt;" in page
    assert "<script>" not in page


def test_insert_tweet_requires_a_body_tag():
    with pytest.raises(ValueError, match="<body>"):
        insert_tweet("<html></html>", "tweet")


@pytest.fixture
def website_repo(tmp_path, monkeypatch):
    """A clone of a throwaway website repository, with its bare "origin" next to it."""
    for variable in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(variable, "Test Bot")
    for variable in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(variable, "bot@example.com")

    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "--bare", "--initial-branch=main", str(origin))
    repo = tmp_path / "website"
    git(tmp_path, "clone", str(origin), str(repo))
    git(repo, "checkout", "-b", "main")
    (repo / "index.html").write_text(PAGE, encoding="utf-8")
    git(repo, "add", "index.html")
    git(repo, "commit", "-m", "Initial page")
    git(repo, "push", "origin", "main")
    return repo, origin


def test_publish_pushes_the_update_on_a_dated_branch(website_repo):
    repo, origin = website_repo

    branch = publish("Stock: Nvidia", repo, "index.html", date(2025, 12, 27))

    assert branch == "bot-post-2025-12-27"
    pushed_page = git(origin, "show", "bot-post-2025-12-27:index.html")
    assert '<blockquote class="twitter-tweet">Stock: Nvidia</blockquote>' in pushed_page
    assert git(origin, "log", "-1", "--format=%s", branch).strip() == (
        "Automated update for 2025-12-27"
    )
    # main is untouched: the change is meant to arrive through a pull request.
    assert "twitter-tweet" not in git(origin, "show", "main:index.html")


def test_publish_stops_before_editing_if_the_branch_already_exists(website_repo):
    repo, _ = website_repo
    publish("first", repo, "index.html", date(2025, 12, 27))

    with pytest.raises(subprocess.CalledProcessError):
        publish("second", repo, "index.html", date(2025, 12, 27))

    assert "second" not in (repo / "index.html").read_text(encoding="utf-8")
