#!/usr/bin/env python3
"""
word_orb_node.py — Main ROS2 node for the Word Orb API integration.

Provides:
  Services
    /word_orb/enrich   (WordEnrich)  — word string -> full enrichment
    /word_orb/ethics   (WordEthics)  — word string -> ethics/wisdom analysis
    /word_orb/lesson   (LessonGet)   — day int -> lesson content

  Topics (publishers)
    /word_orb/word_of_the_day    (WordData)   — periodic daily word
    /word_orb/lesson_of_the_day  (LessonData) — periodic daily lesson

  Parameters
    api_key            (string)  — Word Orb API key (empty = free tier)
    base_url           (string)  — API base URL (default: https://wordorb.ai)
    cache_ttl          (int)     — Cache TTL in seconds (default: 3600)
    default_language   (string)  — Default language code (default: en)
    default_track      (string)  — Default lesson track (default: learn)
    default_archetype  (string)  — Default archetype (default: explorer)
    publish_interval   (float)   — Seconds between daily publishes (default: 86400)
    daily_word         (string)  — Word to publish daily (default: courage)

MIT License — Lesson of the Day PBC
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import rclpy
from rclpy.node import Node
from builtin_interfaces.msg import Time

# Generated message / service types (built by rosidl)
from wordorb_ros2.msg import WordData, LessonData
from wordorb_ros2.srv import WordEnrich, WordEthics, LessonGet

# Our HTTP client (no external SDK)
from wordorb_ros2.word_orb_client import WordOrbClient


class WordOrbNode(Node):
    """ROS2 node bridging the Word Orb REST API to the ROS2 graph."""

    def __init__(self):
        super().__init__("word_orb_node")

        # ── Declare parameters ──────────────────────────────────────
        self.declare_parameter("api_key", "")
        self.declare_parameter("base_url", "https://wordorb.ai")
        self.declare_parameter("cache_ttl", 3600)
        self.declare_parameter("default_language", "en")
        self.declare_parameter("default_track", "learn")
        self.declare_parameter("default_archetype", "explorer")
        self.declare_parameter("publish_interval", 86400.0)
        self.declare_parameter("daily_word", "courage")

        # ── Read parameters ─────────────────────────────────────────
        api_key = self.get_parameter("api_key").get_parameter_value().string_value
        base_url = self.get_parameter("base_url").get_parameter_value().string_value
        cache_ttl = self.get_parameter("cache_ttl").get_parameter_value().integer_value
        default_lang = self.get_parameter("default_language").get_parameter_value().string_value
        self._default_track = self.get_parameter("default_track").get_parameter_value().string_value
        self._default_archetype = self.get_parameter("default_archetype").get_parameter_value().string_value
        publish_interval = self.get_parameter("publish_interval").get_parameter_value().double_value
        self._daily_word = self.get_parameter("daily_word").get_parameter_value().string_value

        # ── HTTP client ─────────────────────────────────────────────
        self._client = WordOrbClient(
            api_key=api_key,
            base_url=base_url,
            timeout=10,
            cache_ttl=cache_ttl,
            default_language=default_lang,
        )

        # ── Services ────────────────────────────────────────────────
        self.create_service(WordEnrich, "/word_orb/enrich", self._handle_enrich)
        self.create_service(WordEthics, "/word_orb/ethics", self._handle_ethics)
        self.create_service(LessonGet, "/word_orb/lesson", self._handle_lesson)

        # ── Publishers ──────────────────────────────────────────────
        self._word_pub = self.create_publisher(WordData, "/word_orb/word_of_the_day", 10)
        self._lesson_pub = self.create_publisher(LessonData, "/word_orb/lesson_of_the_day", 10)

        # ── Timer for periodic publishing ───────────────────────────
        self._timer = self.create_timer(publish_interval, self._publish_daily)

        # Publish once at startup
        self._publish_daily()

        self.get_logger().info(
            "Word Orb node started — base_url=%s, language=%s, interval=%.0fs",
            base_url,
            default_lang,
            publish_interval,
        )

    # ==================================================================
    # Service handlers
    # ==================================================================

    def _handle_enrich(
        self, request: WordEnrich.Request, response: WordEnrich.Response
    ) -> WordEnrich.Response:
        """Handle /word_orb/enrich service calls."""
        self.get_logger().info("Enrich request: word=%s lang=%s", request.word, request.language)

        data = self._client.get_word(request.word, request.language)

        if "_error" in data or "error" in data:
            response.success = False
            response.error_message = data.get("_error", data.get("error", "Unknown error"))
            return response

        response.success = True
        response.error_message = ""
        response.word = data.get("word", request.word)
        response.ipa = data.get("ipa", "")
        response.pos = data.get("pos", "")
        response.definition = data.get("def", "")
        response.etymology = data.get("etym", "")

        tones = data.get("tones", {})
        response.tone_child = tones.get("child", "")
        response.tone_teen = tones.get("teen", "")
        response.tone_adult = tones.get("adult", "")

        response.image_url = data.get("image_url", "")
        response.audio_url = data.get("audio_url", "")
        response.translations_json = json.dumps(data.get("langs", {}), ensure_ascii=False)

        return response

    def _handle_ethics(
        self, request: WordEthics.Request, response: WordEthics.Response
    ) -> WordEthics.Response:
        """Handle /word_orb/ethics service calls."""
        self.get_logger().info("Ethics request: word=%s lang=%s", request.word, request.language)

        data = self._client.get_ethics(request.word, request.language)

        if "_error" in data or "error" in data:
            response.success = False
            response.error_message = data.get("_error", data.get("error", "Unknown error"))
            return response

        response.success = True
        response.error_message = ""
        response.word = data.get("word", request.word)
        response.appears_in = data.get("appears_in", 0)
        response.related_words = data.get("related_words", [])
        response.lessons_json = json.dumps(data.get("lessons", []), ensure_ascii=False)

        return response

    def _handle_lesson(
        self, request: LessonGet.Request, response: LessonGet.Response
    ) -> LessonGet.Response:
        """Handle /word_orb/lesson service calls."""
        day = request.day
        track = request.track or self._default_track
        lang = request.language or self._client.default_language
        archetype = request.archetype or self._default_archetype

        self.get_logger().info(
            "Lesson request: day=%d track=%s lang=%s archetype=%s",
            day, track, lang, archetype,
        )

        data = self._client.get_lesson(day=day, track=track, language=lang, archetype=archetype)

        if "_error" in data or "error" in data:
            response.success = False
            response.error_message = data.get("_error", data.get("error", "Unknown error"))
            return response

        response.success = True
        response.error_message = ""
        response.day = data.get("day", day)
        response.track = data.get("track", track)
        response.title = data.get("title", "")
        response.theme = data.get("theme", "")
        response.age_group = data.get("age_group", "")
        response.language = data.get("language", lang)
        response.archetype = data.get("archetype", archetype)

        phases = data.get("phases", {})
        response.phase_hook = phases.get("hook", "")
        response.phase_story = phases.get("story", "")
        response.phase_wonder = phases.get("wonder", "")
        response.phase_action = phases.get("action", "")
        response.phase_wisdom = phases.get("wisdom", "")

        response.archetypes_available = json.dumps(
            data.get("archetypes_available", []), ensure_ascii=False
        )
        response.languages_available = json.dumps(
            data.get("languages_available", []), ensure_ascii=False
        )

        return response

    # ==================================================================
    # Periodic publishers
    # ==================================================================

    def _publish_daily(self):
        """Publish today's word and lesson on their respective topics."""
        self._publish_word_of_the_day()
        self._publish_lesson_of_the_day()

    def _publish_word_of_the_day(self):
        """Fetch and publish the daily word."""
        word_str = self._daily_word
        data = self._client.get_word(word_str)

        if "_error" in data or "error" in data:
            self.get_logger().warning(
                "Failed to fetch word_of_the_day (%s): %s",
                word_str,
                data.get("_error", data.get("error")),
            )
            return

        msg = WordData()
        msg.word = data.get("word", word_str)
        msg.ipa = data.get("ipa", "")
        msg.pos = data.get("pos", "")
        msg.definition = data.get("def", "")
        msg.etymology = data.get("etym", "")
        msg.language = self._client.default_language

        tones = data.get("tones", {})
        msg.tone_child = tones.get("child", "")
        msg.tone_teen = tones.get("teen", "")
        msg.tone_adult = tones.get("adult", "")

        msg.image_url = data.get("image_url", "")
        msg.audio_url = data.get("audio_url", "")
        msg.translations_json = json.dumps(data.get("langs", {}), ensure_ascii=False)

        msg.source = data.get("_source", "")
        msg.tier = data.get("_tier", "")
        msg.stamp = _now_stamp()

        self._word_pub.publish(msg)
        self.get_logger().info("Published word_of_the_day: %s", msg.word)

    def _publish_lesson_of_the_day(self):
        """Fetch and publish today's lesson."""
        data = self._client.get_lesson(day=0, track=self._default_track)

        if "_error" in data or "error" in data:
            self.get_logger().warning(
                "Failed to fetch lesson_of_the_day: %s",
                data.get("_error", data.get("error")),
            )
            return

        msg = LessonData()
        msg.day = data.get("day", 0)
        msg.track = data.get("track", self._default_track)
        msg.title = data.get("title", "")
        msg.theme = data.get("theme", "")
        msg.age_group = data.get("age_group", "")
        msg.language = data.get("language", self._client.default_language)
        msg.archetype = data.get("archetype", "")

        phases = data.get("phases", {})
        msg.phase_hook = phases.get("hook", "")
        msg.phase_story = phases.get("story", "")
        msg.phase_wonder = phases.get("wonder", "")
        msg.phase_action = phases.get("action", "")
        msg.phase_wisdom = phases.get("wisdom", "")

        msg.archetypes_available = json.dumps(
            data.get("archetypes_available", []), ensure_ascii=False
        )
        msg.languages_available = json.dumps(
            data.get("languages_available", []), ensure_ascii=False
        )

        msg.product = data.get("_product", "lesson_orb")
        msg.tier = data.get("_tier", "")
        msg.stamp = _now_stamp()

        self._lesson_pub.publish(msg)
        self.get_logger().info("Published lesson_of_the_day: day=%d — %s", msg.day, msg.title)


# ======================================================================
# Helpers
# ======================================================================

def _now_stamp() -> Time:
    """Return a builtin_interfaces/Time for right now (UTC)."""
    now = datetime.now(timezone.utc)
    t = Time()
    t.sec = int(now.timestamp())
    t.nanosec = int((now.timestamp() % 1) * 1e9)
    return t


def main(args=None):
    rclpy.init(args=args)
    node = WordOrbNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
