"""Publish the tweet to the companion website.

The website is a static site in its own git repository. Each update is pushed
on a dated branch, so it reaches the live site through a pull request rather
than a direct commit to ``main``.
"""

import html
import logging
import subprocess
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

_INSERT_AFTER = "<body>"


def insert_tweet(page: str, tweet: str) -> str:
    """Return ``page`` with the tweet added as the first element of ``<body>``."""
    if _INSERT_AFTER not in page:
        raise ValueError("Could not find a <body> tag in the page")
    # Escaped because the text ends up inside someone else's HTML.
    body = html.escape(tweet).replace("\n", "<br>")
    block = f'\n\n<br><br> <blockquote class="twitter-tweet">{body}</blockquote>'
    index = page.index(_INSERT_AFTER) + len(_INSERT_AFTER)
    return page[:index] + block + page[index:]


def publish(tweet: str, repo_path: Path, html_path: Path, today: date) -> str:
    """Commit the tweet to a new branch of the website repo and push it.

    ``html_path`` may be absolute or relative to ``repo_path``. Returns the
    branch name. Any failing git command aborts the publish.
    """
    page_path = repo_path / html_path
    branch = f"bot-post-{today.isoformat()}"

    _git(repo_path, "checkout", "main")
    _git(repo_path, "pull", "origin", "main")
    _git(repo_path, "checkout", "-b", branch)

    page = page_path.read_text(encoding="utf-8")
    page_path.write_text(insert_tweet(page, tweet), encoding="utf-8")

    _git(repo_path, "add", str(page_path))
    _git(repo_path, "commit", "-m", f"Automated update for {today.isoformat()}")
    _git(repo_path, "push", "origin", branch)

    logger.info("Pushed %s; open a pull request to publish it", branch)
    return branch


def _git(repo_path: Path, *args: str) -> None:
    # Arguments are passed as a list (no shell), so nothing here is interpolated
    # into a command line.
    subprocess.run(["git", *args], cwd=repo_path, check=True)
