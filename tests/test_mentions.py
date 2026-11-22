from datetime import datetime

import pytest

from reddit_street_journal.mentions import Comment, MentionMatcher, extract_mentions
from reddit_street_journal.tickers import build_universe


@pytest.mark.parametrize(
    "text",
    [
        # Real false positives from an audit of the original substring matcher.
        "Precious metals moving like crypto did before",
        "SLV getting into the artificial intelligence business",
        "we run everything on kubernetes",
        "all the youtubers are bullish",
    ],
)
def test_substrings_of_other_words_are_not_mentions(matcher, text):
    assert matcher.find(text) == set()


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Meta is printing", {"meta"}),
        ("NVIDIA to the moon", {"nvidia"}),
        ("loading up on nvidia, intel and uber.", {"nvidia", "intel", "uber"}),
        ("Meta's earnings were great", {"meta"}),
        ("(tesla)", {"tesla"}),
        ("I love McDonald's", {"mcdonald's"}),
    ],
)
def test_company_names_match_whole_words_in_any_case(matcher, text, expected):
    assert matcher.find(text) == expected


def test_legal_suffixes_are_not_needed_to_match(matcher):
    assert matcher.find("apple and tesla are both up") == {"apple", "tesla"}


def test_aliases_resolve_to_the_canonical_company(matcher):
    assert matcher.find("facebook is dead") == {"meta"}
    assert matcher.find("alphabet or google?") == {"google"}
    assert matcher.find("ford and berkshire") == {"ford motor", "berkshire hathaway"}


def test_longer_names_win_over_names_they_contain():
    universe = build_universe([("AXP", "American Express"), ("AMR", "American")])
    matcher = MentionMatcher(universe)
    assert matcher.find("american express beat earnings") == {"american express"}


def test_bare_tickers_match_only_in_upper_case(matcher):
    assert matcher.find("NVDA calls printing") == {"nvidia"}
    assert matcher.find("nvda calls printing") == set()


def test_share_classes_resolve_to_one_company(matcher):
    assert matcher.find("GOOG or GOOGL?") == {"google"}
    assert matcher.find("BRK.B is my retirement plan") == {"berkshire hathaway"}


def test_ticker_inside_a_longer_token_is_not_a_mention(matcher):
    assert matcher.find("XNVDAX and NVDA123") == set()


def test_tickers_that_are_common_words_need_a_cashtag(matcher):
    assert matcher.find("THE COST OF LIVING") == set()
    assert matcher.find("$COST is a buy") == {"costco"}


def test_short_tickers_need_a_cashtag(matcher):
    assert matcher.find("F in the chat") == set()
    assert matcher.find("$F is cheap") == {"ford motor"}


def test_cashtags_match_in_any_case(matcher):
    assert matcher.find("$tsla and $Nvda") == {"tesla", "nvidia"}


def test_dollar_amounts_and_unknown_cashtags_are_ignored(matcher):
    assert matcher.find("made $500 on $ZZZZ") == set()


def test_ambiguous_company_names_match_only_by_ticker(matcher):
    assert matcher.find("my price target is 3m shares") == set()
    assert matcher.find("TGT and MMM") == {"target", "3m"}


def test_empty_universe_matches_nothing():
    matcher = MentionMatcher(build_universe([]))
    assert matcher.find("NVDA nvidia $NVDA") == set()


def test_extract_mentions_counts_each_company_once_per_comment(matcher):
    comment = Comment(
        body="NVDA nvidia $NVDA, also tesla",
        author="someone",
        created_at=datetime(2025, 12, 26, 21, 27, 17),
        post_title="Daily thread",
    )
    quiet = Comment("nothing to see here", "other", datetime(2025, 12, 26), "Daily thread")

    mentions = extract_mentions([comment, quiet], matcher)

    assert [mention.stock for mention in mentions] == ["nvidia", "tesla"]
    assert all(mention.comment_body == comment.body for mention in mentions)
    assert mentions[0].author == "someone"
    assert mentions[0].created_at == comment.created_at
    assert mentions[0].post_title == "Daily thread"
