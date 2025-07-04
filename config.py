# AI DJ Configuration

## Ollama Setup
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "llamusic/llamusic:latest"

## Audio Settings
CROSSFADE_DURATION = 3000  # milliseconds
BACKGROUND_MUSIC_VOLUME = 0.2  # 20% volume
INTRO_FADE_IN = 500  # milliseconds
INTRO_FADE_OUT = 1000  # milliseconds
INTRO_BUFFER_DURATION = 3000  # milliseconds - background music before/after TTS for smooth crossfades

## Voice Settings (Edge TTS)
# Available voices - choose your preferred DJ voices
AVAILABLE_VOICES = [
    "en-US-AriaNeural",      # Female, friendly
    "en-US-DavisNeural",     # Male, natural
    "en-US-GuyNeural",       # Male, warm
    "en-US-JennyNeural",     # Female, professional
    "en-US-JasonNeural",     # Male, energetic
    "en-US-NancyNeural"      # Female, expressive
]

## Timing Settings
SONG_PREP_BUFFER = 30  # seconds before song ends to start preparing next
MIN_PREP_TIME = 30     # minimum seconds to prepare next song
NEWS_FREQUENCY = 3     # play news announcement every N songs

## News Settings
NEWS_RSS_URL = "https://feedx.net/rss/ap.xml"
NEWS_CACHE_DURATION = 1800  # seconds (30 minutes) to cache news stories

## Folders
MUSIC_FOLDER = "music"
BACKGROUND_MUSIC_FOLDER = "background music"
TEMP_FOLDER = "temp"  # For temporary audio files
