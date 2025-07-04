# 🎵 AI DJ Radio Station - Quick Start Guide

## Before You Begin

You'll need these prerequisites:

1. **Ollama** with the `llamusic:latest` model
2. **FFmpeg** for audio processing
3. **Internet connection** for Edge TTS

## Quick Setup

### Option 1: Use the Launcher (Recommended)
1. Double-click `launcher.bat` 
2. Choose "1. Run Setup Check" to verify everything is working
3. Choose "3. Start AI DJ Radio" to begin

### Option 2: Command Line
```bash
# Check setup
python setup.py

# Run tests
python test.py

# Start the DJ
python main.py
```

### Option 3: VS Code Tasks
- Press `Ctrl+Shift+P` → "Tasks: Run Task"
- Choose from available tasks

## First Time Setup Steps

### 1. Install Ollama
- Download from https://ollama.ai/
- Install the model: `ollama pull llamusic:latest`
- Start the service: `ollama serve`

### 2. Install FFmpeg
- **Windows**: Download from https://ffmpeg.org/ and add to PATH
- **Or use Chocolatey**: `choco install ffmpeg`

### 3. Verify Music Files
- Your `music/` folder has MP3 files
- Your `background music/` folder has background tracks

### 4. Test Everything
Run `python setup.py` to verify all components are working.

## How to Use

### Starting the Radio
1. Make sure Ollama is running (`ollama serve`)
2. Run the AI DJ application
3. The radio will start automatically:
   - Select a random song
   - Generate an AI introduction
   - Create a voice-over with background music
   - Play the intro, then crossfade to the song
   - Prepare the next song while the current one plays

### Stopping the Radio
- Press `Ctrl+C` to gracefully stop

## Customization

### Change DJ Voices
Edit `config.py` and modify the `AVAILABLE_VOICES` list with your preferred Edge TTS voices.

### Adjust Audio Settings
In `config.py`, you can modify:
- `CROSSFADE_DURATION` - How long the crossfade between intro and song
- `BACKGROUND_MUSIC_VOLUME` - Volume level for background music during voice-overs
- Fade in/out durations

### Customize AI Introductions
The AI generates 40-word introductions. You can modify the prompt in `announcement_generator.py` to change the style, length, or tone.

## Troubleshooting

### Common Issues

**"Import could not be resolved"**
- Run `python -m pip install -r requirements.txt`

**Ollama connection errors**
- Make sure Ollama is running: `ollama serve`
- Verify the model exists: `ollama list`

**No audio playback**
- Check your audio drivers
- Try running as administrator
- Verify MP3 files are not corrupted

**TTS not working**
- Check internet connection
- Try different voices in config.py

### Getting Help

1. Run `python setup.py` to check your configuration
2. Run `python test.py` to test individual components
3. Check the console output for detailed error messages

## File Overview

- `main.py` - Main application
- `launcher.py` - Easy-to-use menu interface
- `setup.py` - Setup verification tool
- `test.py` - Component testing tool
- `config.py` - Configuration settings
- `*.bat` files - Windows shortcuts

## Have Fun!

Your AI DJ will automatically create a unique radio experience with personalized introductions for each song. Enjoy the automated radio station! 🎵
