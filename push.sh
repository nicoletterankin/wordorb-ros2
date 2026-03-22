#!/bin/bash
cd "$(dirname "$0")"
git init
git add -A
git commit -m "Initial commit: wordorb_ros2 ROS2 package

ROS2 Humble package wrapping the Word Orb REST API (wordorb.ai).
Provides services for word enrichment, ethics analysis, and lesson
retrieval, plus topics for daily word and lesson content.

- 3 service definitions (WordEnrich, WordEthics, LessonGet)
- 2 message types (WordData, LessonData)
- Self-contained HTTP client (no external SDK)
- 162K words, 47 languages, 10 archetypes, 4 tracks
- TTL cache, graceful API failure handling
- Launch file with configurable parameters
- MIT License

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
git branch -M main
git remote add origin https://github.com/nicoletterankin/wordorb-ros2.git
git push -u origin main
