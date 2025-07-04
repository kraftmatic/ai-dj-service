# Music Directory

This directory contains the main music tracks that the AI DJ will play during the radio show.

## File Format
- **Supported formats**: MP3 files
- **Naming convention**: Any filename is supported (the system will extract metadata from ID3 tags)

## What Goes Here
Place your music collection in this folder. The AI DJ will:
- Randomly select songs from this directory
- Extract artist and title information from MP3 metadata
- Generate custom introductions for each song
- Play songs in full with professional crossfades

## Metadata Requirements
For best results, ensure your MP3 files have proper ID3 tags:
- **Title**: Song title
- **Artist**: Artist name
- **Album**: Album name (optional)

If metadata is missing, the system will fall back to using the filename.

## Example Files
The system works with any MP3 files, such as:
- `01. Artist Name - Song Title.mp3`
- `Nirvana - Smells Like Teen Spirit.mp3`
- `AllStar.mp3`

## Notes
- MP3 files are excluded from Git via `.gitignore`
- The AI DJ will not repeat songs until all songs have been played
- Add as many or as few songs as you like - the system adapts automatically
