"""Find stock mentions in free text.

A substring test (``"meta" in body``) is the obvious first version and it is
wrong in an expensive way: it counts "metals" as Meta, "intelligence" as Intel
and "kubernetes" as Uber. This module matches whole words only, and asks for
more evidence the more ambiguous the token is:

* ``$TSLA`` - a cashtag is explicit, so it always counts, in any case.
* ``TSLA``  - a bare ticker counts only in upper case, only if it is three or
  more letters, and only if it is not also a word people shout (ALL, NOW, COST).
* ``tesla`` - a company name or alias counts in any case, on word boundaries.

Each company is counted at most once per comment.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from reddit_street_journal.tickers import Universe

MIN_BARE_TICKER_LENGTH = 3

# Tickers that are also ordinary words or forum jargon when written in capitals
# ("30 DTE", "PEG ratio", "company XYZ", "RTX 5090"). They still match as cashtags.
AMBIGUOUS_TICKERS = frozenset(
    {
        "ALL", "AMP", "APP", "ARE", "BALL", "BEN", "BRO", "CAT", "COO", "COP", "COST", "DAY",
        "DOC", "DOW", "DTE", "EXE", "FANG", "FAST", "FOX", "GEN", "HAS", "ICE", "IFF", "KEY",
        "KEYS", "LITE", "LOW", "MAR", "MAS", "MET", "MLM", "MSCI", "MTD", "NOW", "PEG", "PKG",
        "POOL", "PSA", "REG", "RTX", "TAP", "TECH", "TXT", "USB", "WELL", "XYZ", "YUM",
    }
)  # fmt: skip

_CASHTAG = re.compile(r"\$([A-Za-z]{1,5}(?:\.[A-Za-z])?)(?!\w)")


@dataclass(frozen=True)
class Comment:
    body: str
    author: str
    created_at: datetime
    post_title: str


@dataclass(frozen=True)
class Mention:
    """One company mentioned in one comment. Field names match the database columns."""

    stock: str
    comment_body: str
    author: str
    created_at: datetime
    post_title: str


def _whole_word(alternatives: Iterable[str], flags: int = 0) -> re.Pattern[str]:
    """Compile one pattern matching any of ``alternatives`` as a whole word.

    Longest first, so "american express" wins over a shorter name it contains.
    The lookarounds do the job of ``\\b`` but also behave for names that start
    or end with punctuation.
    """
    ordered = sorted(alternatives, key=len, reverse=True)
    if not ordered:
        return re.compile(r"(?!)")  # matches nothing
    return re.compile(r"(?<!\w)(?:" + "|".join(map(re.escape, ordered)) + r")(?!\w)", flags)


class MentionMatcher:
    def __init__(self, universe: Universe) -> None:
        self._aliases = universe.aliases
        self._symbols = universe.symbols
        self._name_pattern = _whole_word(universe.aliases, re.IGNORECASE)
        self._ticker_pattern = _whole_word(
            symbol
            for symbol in universe.symbols
            if len(symbol) >= MIN_BARE_TICKER_LENGTH and symbol not in AMBIGUOUS_TICKERS
        )

    def find(self, text: str) -> set[str]:
        """Return the canonical names of every company mentioned in ``text``."""
        found = set()
        for match in self._name_pattern.finditer(text):
            found.add(self._aliases.get(match.group().lower()))
        for match in self._ticker_pattern.finditer(text):
            found.add(self._symbols.get(match.group()))
        for match in _CASHTAG.finditer(text):
            found.add(self._symbols.get(match.group(1).upper()))
        found.discard(None)
        return found


def extract_mentions(comments: Iterable[Comment], matcher: MentionMatcher) -> list[Mention]:
    """Expand each comment into one ``Mention`` per company it talks about."""
    return [
        Mention(
            stock=stock,
            comment_body=comment.body,
            author=comment.author,
            created_at=comment.created_at,
            post_title=comment.post_title,
        )
        for comment in comments
        for stock in sorted(matcher.find(comment.body))
    ]
