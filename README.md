# AI DJ Radio Station

An AI-powered radio DJ application that automatically selects music, generates introductions using AI, creates voice-overs, and plays them with smooth crossfading.

## Features

- **Automatic Music Selection**: Randomly selects MP3 files from your music library
- **AI-Generated Introductions**: Uses Ollama LLM to create engaging 40-word song introductions  
- **Voice-Over Creation**: Converts text to speech using Microsoft Edge TTS
- **Background Music Mixing**: Mixes voice-overs with background music at appropriate volumes
- **Crossfading**: Smooth transitions between introductions and songs
- **Continuous Playback**: Automatically prepares the next song while current one is playing

## Requirements

- Python 3.8+
- Ollama with `llamusic/llamusic:latest` model installed
- FFmpeg (for audio processing)

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install FFmpeg**:
   - Windows: Download from https://ffmpeg.org/ and add to PATH
   - Or use chocolatey: `choco install ffmpeg`

3. **Install and setup Ollama**:
   - Download from https://ollama.ai/
   - Install the model: `ollama pull llamusic/llamusic:latest`
   - Start Ollama service: `ollama serve`

## Usage

1. **Prepare your music folders**:
   - Put your MP3 songs in the `music/` folder
   - Put background music tracks in the `background music/` folder

2. **Run the AI DJ**:
   ```bash
   python main.py
   ```

3. **Stop the DJ**:
   - Press `Ctrl+C` to gracefully stop the radio station

## Configuration

Edit `config.py` to customize:
- Voice settings (choose different TTS voices)
- Audio mixing parameters
- Timing settings
- Ollama server settings

## How It Works

1. **Music Selection**: Randomly picks an MP3 from the music folder
2. **Metadata Extraction**: Reads song title and artist from MP3 tags
3. **AI Introduction**: Sends song info to Ollama to generate a 40-word DJ introduction
4. **Voice-Over Creation**: Uses Edge TTS to convert the introduction to speech
5. **Audio Mixing**: Combines voice-over with background music at 30% volume
6. **Playback**: Plays the introduction, then crossfades into the actual song
7. **Pre-loading**: While a song plays, the next song and introduction are prepared

## Troubleshooting

### "Import could not be resolved" errors
- Install all requirements: `pip install -r requirements.txt`
- Ensure FFmpeg is installed and in PATH

### Ollama connection issues
- Make sure Ollama is running: `ollama serve`
- Verify the model is installed: `ollama list`
- Check if `llamusic/llamusic:latest` model exists

### Audio playback issues
- Install/update audio drivers
- Try different audio formats
- Check file permissions on music folders

### TTS issues
- Ensure internet connection (Edge TTS requires online access)
- Try different voice models in config.py

## File Structure

```
AI DJ/
├── main.py                 # Main application entry point
├── music_selector.py       # Handles music file selection and metadata
├── announcement_generator.py # AI-powered introduction generation
├── voice_over_mixer.py     # TTS and audio mixing
├── audio_player.py         # Audio playback with crossfading
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── music/                 # Your MP3 music files
├── background music/      # Background music for voice-overs
└── README.md             # This file
```

## License

This project is open source. Feel free to modify and distribute.
