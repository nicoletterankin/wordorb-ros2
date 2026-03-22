# LessonData.msg — Daily lesson from the Word Orb Lesson Orb API
# Published on /word_orb/lesson_of_the_day

int32 day                     # Calendar day (1-365)
string track                  # Lesson track (learn, teach, grow, trivia)
string title                  # Lesson title
string theme                  # Lesson theme / subject area
string age_group              # Target age group (child, teen, adult, elder)
string language               # Language code (default: en)
string archetype              # Teaching archetype (explorer, scientist, etc.)

# Lesson phases
string phase_hook             # Opening hook — grabs attention
string phase_story            # Core narrative / story
string phase_wonder           # Deeper exploration / wonder
string phase_action           # Actionable exercise
string phase_wisdom           # Closing wisdom / takeaway

# Available options (JSON arrays)
string archetypes_available   # JSON array of available archetypes
string languages_available    # JSON array of available language codes

# Metadata
string product                # API product (lesson_orb)
string tier                   # API tier
builtin_interfaces/Time stamp # When this data was fetched
