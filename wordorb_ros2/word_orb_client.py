#!/usr/bin/env python3
"""
word_orb_client.py — Self-contained HTTP client for the Word Orb REST API.

Wraps https://wordorb.ai/api/* endpoints. No external SDK dependency;
uses only the ``requests`` library (stdlib ``urllib.request`` as fallback).

MIT License — Lesson of the Day PBC
"""

from __future__ import annotations

import json
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    import requests

    _HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error

    _HAS_REQUESTS = False

logger = logging.getLogger("wordorb_ros2.client")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "https://wordorb.ai"
DEFAULT_TIMEOUT = 10  # seconds
DEFAULT_LANGUAGE = "en"
DEFAULT_TRACK = "learn"
DEFAULT_ARCHETYPE = "explorer"


# ---------------------------------------------------------------------------
# Simple in-memory TTL cache
# ---------------------------------------------------------------------------

class _Cache:
    """Trivial TTL cache keyed by arbitrary strings."""

    def __init__(self, ttl: int = 3600):
        self._store: Dict[str, tuple[float, Any]] = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts > self.ttl:
            del self._store[key]
            return None
        return value

    def put(self, key: str, value: Any) -> None:
        self._store[key] = (time.monotonic(), value)

    def clear(self) -> None:
        self._store.clear()


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class WordOrbClient:
    """Synchronous HTTP client for the Word Orb REST API."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        cache_ttl: int = 3600,
        default_language: str = DEFAULT_LANGUAGE,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_language = default_language
        self._cache = _Cache(ttl=cache_ttl)

        if _HAS_REQUESTS:
            self._session = requests.Session()
            if self.api_key:
                self._session.headers["Authorization"] = f"Bearer {self.api_key}"
            self._session.headers["User-Agent"] = "wordorb-ros2/1.0.0"
        else:
            self._session = None
            logger.warning(
                "requests library not found; falling back to urllib. "
                "Install requests for better performance: pip install requests"
            )

    # ------------------------------------------------------------------
    # Internal HTTP
    # ------------------------------------------------------------------

    def _get(self, path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Issue a GET request and return parsed JSON."""
        url = f"{self.base_url}{path}"

        # Build query string
        if params:
            filtered = {k: v for k, v in params.items() if v is not None and v != ""}
            if filtered:
                qs = "&".join(f"{k}={v}" for k, v in filtered.items())
                url = f"{url}?{qs}"

        # Check cache
        cached = self._cache.get(url)
        if cached is not None:
            logger.debug("Cache hit: %s", url)
            return cached

        logger.debug("GET %s", url)

        try:
            if _HAS_REQUESTS:
                resp = self._session.get(url, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
            else:
                req = urllib.request.Request(url)
                if self.api_key:
                    req.add_header("Authorization", f"Bearer {self.api_key}")
                req.add_header("User-Agent", "wordorb-ros2/1.0.0")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            logger.error("API request failed: %s — %s", url, exc)
            return {"_error": str(exc)}

        # Cache successful responses
        if "_error" not in data and "error" not in data:
            self._cache.put(url, data)

        return data

    # ------------------------------------------------------------------
    # Public API Methods
    # ------------------------------------------------------------------

    def get_word(self, word: str, language: str = "") -> Dict[str, Any]:
        """
        Look up a word.

        GET /api/word/{word}?lang={language}

        Returns the full enrichment payload: definition, IPA, etymology,
        translations, tone variants, media URLs.
        """
        lang = language or self.default_language
        params = {}
        if lang and lang != "en":
            params["lang"] = lang
        return self._get(f"/api/word/{word}", params)

    def get_lesson(
        self,
        day: int = 0,
        track: str = DEFAULT_TRACK,
        language: str = "",
        archetype: str = DEFAULT_ARCHETYPE,
    ) -> Dict[str, Any]:
        """
        Retrieve a lesson by calendar day.

        GET /api/lesson?day={day}&track={track}

        day=0 means today's lesson (derived from calendar date).
        """
        if day <= 0:
            day = _today_day_of_year()

        lang = language or self.default_language
        params: Dict[str, str] = {
            "day": str(day),
            "track": track,
        }
        # Language and archetype are part of the response selection
        # The API returns the default archetype; language filtering
        # is handled server-side when available.
        return self._get("/api/lesson", params)

    def get_quiz(
        self,
        day: int = 0,
        track: str = DEFAULT_TRACK,
    ) -> Dict[str, Any]:
        """
        Retrieve quiz / assessment for a given day.

        GET /api/quiz?day={day}&track={track}
        """
        if day <= 0:
            day = _today_day_of_year()
        return self._get("/api/quiz", {"day": str(day), "track": track})

    def get_graph(self, word: str) -> Dict[str, Any]:
        """
        Retrieve the knowledge graph for a word.

        GET /api/graph/word?word={word}

        Returns lessons where the word appears and related words.
        """
        return self._get("/api/graph/word", {"word": word})

    def get_stats(self) -> Dict[str, Any]:
        """
        Retrieve platform statistics.

        GET /api/stats
        """
        return self._get("/api/stats")

    def get_ethics(self, word: str, language: str = "") -> Dict[str, Any]:
        """
        Compose an ethics / wisdom analysis for a word.

        This is a compound operation:
        1. Fetch the knowledge graph for the word.
        2. For each lesson where the word appears, note the context.
        3. Return the graph data enriched with related words and lesson refs.

        The caller (the ROS2 node) can optionally fetch full lesson wisdom
        phases for deeper ethical context.
        """
        graph = self.get_graph(word)
        if "_error" in graph or "error" in graph:
            return graph

        # Enrich with word definition for context
        word_data = self.get_word(word, language)

        return {
            "word": word,
            "appears_in": graph.get("appears_in", 0),
            "related_words": graph.get("related_words", []),
            "lessons": graph.get("lessons", []),
            "definition": word_data.get("def", ""),
            "etymology": word_data.get("etym", ""),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today_day_of_year() -> int:
    """Return today's day-of-year (1-366)."""
    now = datetime.now(timezone.utc)
    return now.timetuple().tm_yday


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.DEBUG)

    key = sys.argv[1] if len(sys.argv) > 1 else ""
    client = WordOrbClient(api_key=key)

    print("\n=== Word: courage ===")
    w = client.get_word("courage")
    print(json.dumps(w, indent=2, ensure_ascii=False)[:800])

    print(f"\n=== Lesson: day {_today_day_of_year()} ===")
    les = client.get_lesson()
    print(json.dumps(les, indent=2, ensure_ascii=False)[:800])

    print("\n=== Graph: courage ===")
    g = client.get_graph("courage")
    print(json.dumps(g, indent=2, ensure_ascii=False)[:800])

    print("\n=== Stats ===")
    s = client.get_stats()
    print(json.dumps(s, indent=2, ensure_ascii=False)[:800])

    print("\n=== Ethics: courage ===")
    e = client.get_ethics("courage")
    print(json.dumps(e, indent=2, ensure_ascii=False)[:800])
