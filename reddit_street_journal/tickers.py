"""The stock universe: S&P 500 constituents, scraped from Wikipedia and cached.

Wikipedia gives a ticker and a formal company name ("Apple Inc.", "Tesla, Inc.").
Nobody on Reddit writes those, so each company is expanded into the names people
actually type: the formal name with its legal suffix removed, plus a short list
of hand-picked aliases. Names that are also everyday words ("target", "block")
are excluded, because matching them would count far more noise than signal.
"""

import json
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
CACHE_FILENAME = "sp500_constituents.json"
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60
# The index has ~500 members. Far fewer rows means the page layout changed and
# the scrape should be treated as failed rather than silently shrinking the universe.
MIN_EXPECTED_CONSTITUENTS = 400

# Canonical names for companies better known by something other than their listing.
NAME_OVERRIDES = {"GOOGL": "Google", "GOOG": "Google", "META": "Meta"}

# Extra names people use, keyed by ticker.
EXTRA_ALIASES = {
    "AMD": ("amd",),
    "BAC": ("bofa",),
    "BRK.B": ("berkshire",),
    "CMG": ("chipotle",),
    "DELL": ("dell",),
    "DIS": ("disney",),
    "F": ("ford",),
    "GOOGL": ("alphabet",),
    "GS": ("goldman",),
    "HOOD": ("robinhood",),
    "JPM": ("jpmorgan", "jp morgan"),
    "LMT": ("lockheed",),
    "LULU": ("lululemon",),
    "MCD": ("mcdonalds",),
    "META": ("facebook",),
    "MU": ("micron",),
    "PLTR": ("palantir",),
    "RTX": ("raytheon",),
    "SCHW": ("schwab",),
    "TMUS": ("t-mobile",),
    "UNH": ("unitedhealth",),
    "XOM": ("exxon",),
}

# Company names that are also common words or mean something else on a trading
# forum ("price target", "the dow", "3m" as in three months, "ppl" as in people,
# and "reddit", which on Reddit nearly always means the site, not the stock).
# These companies are still matched by ticker.
AMBIGUOUS_NAMES = frozenset(
    {
        "3m",
        "ball",
        "best buy",
        "block",
        "coherent",
        "cooper",
        "dow",
        "flex",
        "fox",
        "hp",
        "msci",
        "nasdaq",
        "news",
        "pool",
        "ppl",
        "progressive",
        "reddit",
        "rtx",
        "southern",
        "target",
        "travelers",
        "waters",
        "williams",
        "workday",
    }
)

_PARENTHETICAL = re.compile(r"\s*\(.*?\)")
_LEADING_THE = re.compile(r"^the\s+", re.IGNORECASE)
_LEGAL_SUFFIX = re.compile(
    r"(?:\s+and|\s*&)?[\s,]+"
    r"(?:inc|incorporated|corp|corporation|company|companies|co|plc|ltd|limited)\.?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Company:
    name: str  # canonical lowercase key, as stored in the database: "apple"
    display_name: str  # "Apple"
    ticker: str  # primary listing: "AAPL"


@dataclass(frozen=True)
class Universe:
    companies: dict[str, Company]  # canonical name -> company
    aliases: dict[str, str]  # lowercase name people type -> canonical name
    symbols: dict[str, str]  # ticker symbol -> canonical name


def clean_company_name(raw: str) -> str:
    """Strip the legal boilerplate from a formal company name.

    >>> clean_company_name("Tesla, Inc.")
    'Tesla'
    >>> clean_company_name("Coca-Cola Company (The)")
    'Coca-Cola'
    """
    name = _PARENTHETICAL.sub("", raw).strip()
    name = _LEADING_THE.sub("", name)
    previous = None
    while previous != name:  # suffixes can stack: "Foo Holdings Co., Inc."
        previous = name
        name = _LEGAL_SUFFIX.sub("", name).strip()
    return name


def build_universe(constituents: list[tuple[str, str]]) -> Universe:
    """Turn (ticker, formal name) rows into the lookup tables the matcher needs."""
    companies: dict[str, Company] = {}
    aliases: dict[str, str] = {}
    symbols: dict[str, str] = {}

    for ticker, raw_name in constituents:
        display_name = NAME_OVERRIDES.get(ticker) or clean_company_name(raw_name)
        name = display_name.lower()
        # Share classes (GOOGL/GOOG, FOXA/FOX) collapse onto the first listing.
        companies.setdefault(name, Company(name, display_name, ticker))
        symbols[ticker] = name
        for alias in (name, *EXTRA_ALIASES.get(ticker, ())):
            if alias not in AMBIGUOUS_NAMES:
                aliases.setdefault(alias, name)

    return Universe(companies, aliases, symbols)


def parse_constituents(html: str) -> list[tuple[str, str]]:
    """Extract (ticker, company name) rows from the Wikipedia constituents table."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "constituents"}) or soup.find("table", {"class": "wikitable"})
    if table is None:
        raise ValueError("Could not find the S&P 500 constituents table")

    constituents = []
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if len(cells) >= 2:
            constituents.append((cells[0].text.strip().upper(), cells[1].text.strip()))
    return constituents


def fetch_constituents() -> list[tuple[str, str]]:
    response = requests.get(
        WIKIPEDIA_URL, headers={"User-Agent": "reddit-street-journal/1.0"}, timeout=30
    )
    response.raise_for_status()
    constituents = parse_constituents(response.text)
    if len(constituents) < MIN_EXPECTED_CONSTITUENTS:
        raise ValueError(f"Only {len(constituents)} constituents parsed; page layout changed?")
    return constituents


def load_constituents(
    cache_path: Path,
    fetch: Callable[[], list[tuple[str, str]]] = fetch_constituents,
    max_age_seconds: float = CACHE_TTL_SECONDS,
) -> list[tuple[str, str]]:
    """Return the constituents list, re-scraping at most once per ``max_age_seconds``.

    If the scrape fails and an expired cache exists, the stale copy is used: index
    membership changes a few times a year, so week-old data beats a failed run.
    """
    if cache_path.exists() and time.time() - cache_path.stat().st_mtime < max_age_seconds:
        return _read_cache(cache_path)

    try:
        constituents = fetch()
    except Exception:
        if not cache_path.exists():
            raise
        logger.warning("S&P 500 scrape failed; using the expired cache", exc_info=True)
        return _read_cache(cache_path)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(constituents), encoding="utf-8")
    logger.info("Scraped %d S&P 500 constituents from Wikipedia", len(constituents))
    return constituents


def load_universe(state_dir: Path) -> Universe:
    return build_universe(load_constituents(state_dir / CACHE_FILENAME))


def _read_cache(cache_path: Path) -> list[tuple[str, str]]:
    rows = json.loads(cache_path.read_text(encoding="utf-8"))
    return [(ticker, name) for ticker, name in rows]
