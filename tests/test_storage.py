from datetime import datetime

import pandas as pd
import pytest
import sqlalchemy as sa

from reddit_street_journal.storage import COLUMNS, load_mentions, reddit_mentions


@pytest.fixture
def engine():
    # SQLite stands in for Cloud SQL: the load only uses portable SQLAlchemy.
    return sa.create_engine("sqlite://")


def mention(stock, author, minute):
    return {
        "stock": stock,
        "comment_body": f"{author} likes {stock}",
        "author": author,
        "created_at": datetime(2025, 12, 26, 21, minute, 0),
        "post_title": "Daily thread",
    }


def stored_rows(engine):
    return pd.read_sql(sa.select(reddit_mentions).order_by(reddit_mentions.c.created_at), engine)


def test_first_load_creates_the_table_and_inserts_everything(engine):
    batch = pd.DataFrame([mention("nvidia", "alice", 1), mention("tesla", "bob", 2)])

    assert load_mentions(batch, engine) == 2

    rows = stored_rows(engine)
    assert list(rows.columns) == COLUMNS
    assert rows["stock"].tolist() == ["nvidia", "tesla"]
    assert rows["created_at"].tolist() == batch["created_at"].tolist()


def test_reloading_the_same_batch_inserts_nothing(engine):
    batch = pd.DataFrame([mention("nvidia", "alice", 1), mention("tesla", "bob", 2)])
    load_mentions(batch, engine)

    assert load_mentions(batch, engine) == 0
    assert len(stored_rows(engine)) == 2


def test_overlapping_batch_inserts_only_the_new_rows(engine):
    load_mentions(pd.DataFrame([mention("nvidia", "alice", 1), mention("tesla", "bob", 2)]), engine)
    second_run = pd.DataFrame([mention("tesla", "bob", 2), mention("intel", "carol", 3)])

    assert load_mentions(second_run, engine) == 1
    assert stored_rows(engine)["stock"].tolist() == ["nvidia", "tesla", "intel"]


def test_same_comment_mentioning_two_stocks_is_two_rows(engine):
    batch = pd.DataFrame([mention("nvidia", "alice", 1), mention("tesla", "alice", 1)])

    assert load_mentions(batch, engine) == 2
    assert load_mentions(batch, engine) == 0


def test_duplicates_within_a_batch_are_collapsed(engine):
    batch = pd.DataFrame([mention("nvidia", "alice", 1), mention("nvidia", "alice", 1)])

    assert load_mentions(batch, engine) == 1


def test_batch_older_than_everything_stored_is_inserted(engine):
    load_mentions(pd.DataFrame([mention("nvidia", "alice", 30)]), engine)

    assert load_mentions(pd.DataFrame([mention("tesla", "bob", 5)]), engine) == 1
    assert len(stored_rows(engine)) == 2


def test_extra_columns_are_not_written(engine):
    batch = pd.DataFrame([mention("nvidia", "alice", 1)]).assign(debug="x")

    load_mentions(batch, engine)

    assert list(stored_rows(engine).columns) == COLUMNS
