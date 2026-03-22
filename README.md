# wordorb_ros2

ROS2 package for the [Word Orb](https://wordorb.ai) vocabulary and lesson API. Gives any ROS2 robot access to 162,000+ words across 47 languages, daily lessons, assessments, and a knowledge graph — over standard ROS2 services and topics.

**Target distribution:** ROS2 Humble (Jazzy and Rolling also supported)

## What it does

| Interface | Name | Description |
|-----------|------|-------------|
| **Service** | `/word_orb/enrich` | Look up any word — returns IPA, definition, etymology, translations (47 languages), tone-adapted explanations (child/teen/adult), and media URLs |
| **Service** | `/word_orb/ethics` | Ethics/wisdom analysis — returns lessons where a word appears, related words, and contextual wisdom |
| **Service** | `/word_orb/lesson` | Retrieve a lesson by calendar day (1–365) — five narrative phases (hook, story, wonder, action, wisdom) across 10 teaching archetypes |
| **Topic** | `/word_orb/word_of_the_day` | Publishes a `WordData` message at a configurable interval |
| **Topic** | `/word_orb/lesson_of_the_day` | Publishes a `LessonData` message at a configurable interval |

## Quickstart

### 1. Clone into your workspace

```bash
cd ~/ros2_ws/src
git clone https://github.com/nicoletterankin/wordorb-ros2.git
```

### 2. Install dependencies

```bash
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
pip3 install requests
```

### 3. Build

```bash
cd ~/ros2_ws
colcon build --packages-select wordorb_ros2
source install/setup.bash
```

### 4. Get a free API key

```bash
curl -s -X POST https://wordorb.ai/api/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","name":"My Robot"}' | jq .key
```

Free tier: 500 calls/day, no credit card.

### 5. Launch

```bash
# With API key
ros2 launch wordorb_ros2 word_orb.launch.py api_key:=wo_your_key_here

# With custom language and faster publishing (every 60s for testing)
ros2 launch wordorb_ros2 word_orb.launch.py \
  api_key:=wo_your_key_here \
  default_language:=es \
  publish_interval:=60.0
```

### 6. Use the services

```bash
# Look up a word
ros2 service call /word_orb/enrich wordorb_ros2/srv/WordEnrich \
  "{word: 'courage', language: 'en'}"

# Get today's lesson
ros2 service call /word_orb/lesson wordorb_ros2/srv/LessonGet \
  "{day: 0, track: 'learn', language: 'en', archetype: 'explorer'}"

# Ethics analysis
ros2 service call /word_orb/ethics wordorb_ros2/srv/WordEthics \
  "{word: 'integrity', language: 'en'}"
```

### 7. Subscribe to topics

```bash
# Word of the day
ros2 topic echo /word_orb/word_of_the_day

# Lesson of the day
ros2 topic echo /word_orb/lesson_of_the_day
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | `""` | Word Orb API key. Empty = free tier (500/day). |
| `base_url` | string | `https://wordorb.ai` | API base URL |
| `cache_ttl` | int | `3600` | Seconds to cache API responses |
| `default_language` | string | `en` | Default language for lookups (47 available) |
| `default_track` | string | `learn` | Lesson track: learn, teach, grow, trivia |
| `default_archetype` | string | `explorer` | Teaching archetype (10 available) |
| `publish_interval` | float | `86400.0` | Seconds between daily publishes |
| `daily_word` | string | `courage` | Word to publish on the daily topic |

Set at runtime:

```bash
ros2 param set /word_orb_node default_language es
ros2 param set /word_orb_node publish_interval 120.0
```

## Message and service definitions

### WordData.msg

```
string word, ipa, pos, definition, etymology, language
string tone_child, tone_teen, tone_adult
string image_url, audio_url
string translations_json          # {"es":"coraje","fr":"courage",...}
string source, tier
builtin_interfaces/Time stamp
```

### LessonData.msg

```
int32 day
string track, title, theme, age_group, language, archetype
string phase_hook, phase_story, phase_wonder, phase_action, phase_wisdom
string archetypes_available, languages_available   # JSON arrays
string product, tier
builtin_interfaces/Time stamp
```

### WordEnrich.srv

```
string word, language
---
bool success, string error_message
string word, ipa, pos, definition, etymology
string tone_child, tone_teen, tone_adult
string image_url, audio_url, translations_json
```

### WordEthics.srv

```
string word, language
---
bool success, string error_message
string word
int32 appears_in
string[] related_words
string lessons_json
```

### LessonGet.srv

```
int32 day
string track, language, archetype
---
bool success, string error_message
int32 day
string track, title, theme, age_group, language, archetype
string phase_hook, phase_story, phase_wonder, phase_action, phase_wisdom
string archetypes_available, languages_available
```

## Supported languages (47)

en, es, fr, de, zh, ja, ar, hi, pt, sw, ko, it, ru, nl, sv, tr, th, vi, id, pl, cs, uk, el, he, ro, hu, da, fi, nb, ms, tl, bn, ta, te, mr, gu, kn, ml, pa, ur, fa, am, yo, zu, ha, ig, rw, so

## Teaching archetypes (10)

architect, diplomat, empath, explorer, macgyver, provider, rebel, scientist, strategist, survivor

## Lesson tracks (4)

- **learn** — Core vocabulary and knowledge
- **teach** — Pedagogy and explanation
- **grow** — Personal development
- **trivia** — Fun facts and curiosities

## Testing

```bash
# Run client tests (no ROS2 required)
WORDORB_API_KEY=wo_your_key python -m pytest test/ -v

# Run via colcon
colcon test --packages-select wordorb_ros2
colcon test-result --verbose
```

## Architecture

```
                    ┌─────────────────────────┐
                    │    wordorb.ai REST API   │
                    │  162K words / 47 langs   │
                    └────────────┬────────────┘
                                 │ HTTPS
                    ┌────────────▼────────────┐
                    │    WordOrbClient         │
                    │  (word_orb_client.py)    │
                    │  HTTP + TTL cache        │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    WordOrbNode           │
                    │  (word_orb_node.py)      │
                    ├─────────────────────────┤
                    │ Services:               │
                    │  /word_orb/enrich       │
                    │  /word_orb/ethics       │
                    │  /word_orb/lesson       │
                    ├─────────────────────────┤
                    │ Topics:                 │
                    │  /word_orb/word_of_day  │
                    │  /word_orb/lesson_of_day│
                    └─────────────────────────┘
```

## API

This package wraps the public Word Orb REST API at `https://wordorb.ai`. No local Python SDK is required — all HTTP calls are self-contained in `word_orb_client.py` using the `requests` library (with `urllib` fallback).

- **Docs:** https://wordorb.ai/docs
- **Playground:** https://wordorb.ai/playground
- **Pricing:** https://wordorb.ai/pricing
- **Status:** https://wordorb.ai/status

## License

MIT License. See [LICENSE](LICENSE).

Built by [Lesson of the Day PBC](https://lotdpbc.com).
