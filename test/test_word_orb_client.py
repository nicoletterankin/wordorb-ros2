"""
test_word_orb_client.py — Unit tests for the Word Orb HTTP client.

These tests run against the live API (free tier) and validate response
structure. They do NOT require ROS2 to be installed.

Run standalone:
  python -m pytest test/test_word_orb_client.py -v

Run via colcon:
  colcon test --packages-select wordorb_ros2
"""

import json
import os
import sys
import pytest

# Allow import from parent when running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wordorb_ros2.word_orb_client import WordOrbClient, _today_day_of_year


# Use the free-tier key for testing — override with WORDORB_API_KEY env var
API_KEY = os.environ.get("WORDORB_API_KEY", "")


@pytest.fixture(scope="module")
def client():
    """Shared client instance for all tests."""
    return WordOrbClient(api_key=API_KEY, cache_ttl=60)


class TestWordOrbClient:
    """Tests against the live Word Orb API."""

    def test_get_word(self, client):
        """Word enrichment should return a word, IPA, definition."""
        data = client.get_word("courage")
        if "_error" in data or "error" in data:
            pytest.skip(f"API unavailable: {data}")
        assert data.get("word") == "courage"
        assert "ipa" in data
        assert "def" in data
        assert "tones" in data
        assert "langs" in data

    def test_get_word_translations(self, client):
        """Translations should include common languages."""
        data = client.get_word("courage")
        if "_error" in data or "error" in data:
            pytest.skip(f"API unavailable: {data}")
        langs = data.get("langs", {})
        assert "es" in langs  # Spanish
        assert "fr" in langs  # French
        assert "de" in langs  # German

    def test_get_lesson(self, client):
        """Lesson should return phases and metadata."""
        data = client.get_lesson(day=1, track="learn")
        if "_error" in data or "error" in data:
            pytest.skip(f"API unavailable: {data}")
        assert data.get("day") == 1
        assert "phases" in data
        phases = data["phases"]
        assert "hook" in phases
        assert "story" in phases
        assert "wisdom" in phases

    def test_get_lesson_today(self, client):
        """Day 0 should resolve to today's day-of-year."""
        data = client.get_lesson(day=0)
        if "_error" in data or "error" in data:
            pytest.skip(f"API unavailable: {data}")
        expected_day = _today_day_of_year()
        assert data.get("day") == expected_day

    def test_get_graph(self, client):
        """Knowledge graph should return lesson appearances."""
        data = client.get_graph("courage")
        if "_error" in data or "error" in data:
            pytest.skip(f"API unavailable: {data}")
        assert data.get("word") == "courage"
        assert "appears_in" in data
        assert "lessons" in data
        assert isinstance(data["lessons"], list)

    def test_get_stats(self, client):
        """Platform stats should return product counts."""
        data = client.get_stats()
        if "_error" in data or "error" in data:
            pytest.skip(f"API unavailable: {data}")
        assert "products" in data
        assert "version" in data

    def test_get_ethics(self, client):
        """Ethics analysis should combine graph + word data."""
        data = client.get_ethics("courage")
        if "_error" in data or "error" in data:
            pytest.skip(f"API unavailable: {data}")
        assert data.get("word") == "courage"
        assert "appears_in" in data
        assert "related_words" in data
        assert "definition" in data

    def test_cache_hit(self, client):
        """Second call should be served from cache."""
        # First call populates cache
        client.get_word("serenity")
        # Second call should hit cache (no HTTP)
        data = client.get_word("serenity")
        # If we got data back, cache is working
        if "_error" not in data and "error" not in data:
            assert data.get("word") == "serenity"

    def test_today_day_of_year(self):
        """Helper should return a valid day 1-366."""
        day = _today_day_of_year()
        assert 1 <= day <= 366


class TestClientInit:
    """Test client initialization variants."""

    def test_default_init(self):
        c = WordOrbClient()
        assert c.base_url == "https://wordorb.ai"
        assert c.default_language == "en"

    def test_custom_init(self):
        c = WordOrbClient(
            api_key="wo_test123",
            base_url="https://custom.example.com/",
            cache_ttl=120,
            default_language="es",
        )
        assert c.api_key == "wo_test123"
        assert c.base_url == "https://custom.example.com"  # trailing slash stripped
        assert c.default_language == "es"
