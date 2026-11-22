"""Command-line entry point: ``python -m reddit_street_journal``."""

import argparse
import dataclasses
import logging
import sys

from dotenv import load_dotenv

from reddit_street_journal.config import ConfigError, Settings
from reddit_street_journal.pipeline import PublishError, run

logger = logging.getLogger("reddit_street_journal")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reddit_street_journal",
        description="Find the most-mentioned stock on a subreddit and publish a summary.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="read from Reddit and print the tweet, but store and publish nothing",
    )
    parser.add_argument("--subreddit", help="subreddit to scan (default: wallstreetbets)")
    parser.add_argument("--limit", type=int, help="number of hot posts to scan (default: 100)")
    args = parser.parse_args(argv)

    load_dotenv()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    settings = Settings.from_env()
    if args.subreddit:
        settings = dataclasses.replace(settings, subreddit=args.subreddit)
    if args.limit:
        settings = dataclasses.replace(settings, post_scan_limit=args.limit)

    try:
        tweet = run(settings, dry_run=args.dry_run)
    except ConfigError as error:
        logger.error("%s", error)
        return 2
    except PublishError as error:
        logger.error("%s", error)
        return 1

    if tweet:
        print(tweet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
