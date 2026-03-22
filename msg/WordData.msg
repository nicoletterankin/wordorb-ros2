# WordData.msg — Full word enrichment from the Word Orb API
# Published on /word_orb/word_of_the_day

string word                   # The word itself
string ipa                    # IPA pronunciation (e.g. /ˈkɜːrɪdʒ/)
string pos                    # Part of speech (noun, verb, etc.)
string definition             # Full definition
string etymology              # Word origin / etymology
string language               # Language code (default: en)

# Tone-adapted definitions
string tone_child             # Child-friendly explanation
string tone_teen              # Teen-appropriate explanation
string tone_adult             # Full adult definition

# Media URLs
string image_url              # Word illustration URL
string audio_url              # Pronunciation audio URL

# Translations (JSON-encoded key-value map: {"es":"coraje","fr":"courage",...})
string translations_json

# Metadata
string source                 # Data source (d1, cache, etc.)
string tier                   # API tier (free, starter, growth, enterprise)
builtin_interfaces/Time stamp # When this data was fetched
