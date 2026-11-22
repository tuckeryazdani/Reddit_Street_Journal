"""Load mentions into the ``reddit_mentions`` table (MySQL on Google Cloud SQL)."""

import logging

import pandas as pd
import sqlalchemy as sa

from reddit_street_journal.config import Settings

logger = logging.getLogger(__name__)

metadata = sa.MetaData()

reddit_mentions = sa.Table(
    "reddit_mentions",
    metadata,
    sa.Column("stock", sa.Text),
    sa.Column("comment_body", sa.Text),
    sa.Column("author", sa.Text),
    sa.Column("created_at", sa.DateTime),  # UTC
    sa.Column("post_title", sa.Text),
)

COLUMNS = [column.name for column in reddit_mentions.columns]
# One company, mentioned by one author, in one comment. Reddit comment
# timestamps have one-second resolution, which is as close to a natural key as
# the table has.
MENTION_KEY = ["stock", "author", "created_at"]


def cloud_sql_engine(settings: Settings) -> sa.Engine:
    """Create an engine that connects through the Cloud SQL Python Connector."""
    # Imported here so that tests and dry runs do not need the Google libraries.
    from google.cloud.sql.connector import Connector

    connector = Connector()

    def connect():
        return connector.connect(
            settings.cloud_sql_instance,
            "pymysql",
            user=settings.db_user,
            password=settings.db_password,
            db=settings.db_name,
        )

    return sa.create_engine("mysql+pymysql://", creator=connect)


def load_mentions(mentions: pd.DataFrame, engine: sa.Engine) -> int:
    """Append mentions that are not already stored. Returns the number inserted.

    Every run re-reads the subreddit's hot posts, so most comments have been
    seen before. A blind append would store them again on each run; this load
    is idempotent, so the job can be re-run or scheduled more often safely.
    """
    batch = mentions[COLUMNS].drop_duplicates(subset=MENTION_KEY)
    metadata.create_all(engine)

    with engine.begin() as connection:
        # Only rows at least as new as the batch's oldest comment can collide.
        already_stored = pd.read_sql(
            sa.select(*(reddit_mentions.c[key] for key in MENTION_KEY))
            .where(reddit_mentions.c.created_at >= batch["created_at"].min().to_pydatetime())
            .distinct(),
            connection,
        )
        if not already_stored.empty:
            joined = batch.merge(already_stored, on=MENTION_KEY, how="left", indicator=True)
            batch = joined.loc[joined["_merge"] == "left_only", COLUMNS]

        batch.to_sql(reddit_mentions.name, connection, if_exists="append", index=False)

    logger.info(
        "Stored %d new mentions (%d already in the table)", len(batch), len(mentions) - len(batch)
    )
    return len(batch)
