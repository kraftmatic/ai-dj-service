import random
import os
from pathlib import Path
from mutagen import File as MutagenFile
import logging

class MusicSelector:
    """Handles random selection of MP3 files from the music folder"""
    
    def __init__(self, music_folder: str):
        self.music_folder = Path(music_folder)
        self.played_songs = set()
        self.logger = logging.getLogger(__name__)
        
    def get_random_song(self) -> dict:
        """
        Select a random MP3 file from the music folder
        Returns dict with file path, title, and artist
        """
        mp3_files = list(self.music_folder.glob("*.mp3"))
        
        if not mp3_files:
            raise ValueError("No MP3 files found in music folder")
        
        # Filter out already played songs if possible
        available_songs = [f for f in mp3_files if f not in self.played_songs]
        
        # If all songs have been played, reset the played set
        if not available_songs:
            self.played_songs.clear()
            available_songs = mp3_files
            self.logger.info("All songs played, resetting playlist")
        
        selected_file = random.choice(available_songs)
        self.played_songs.add(selected_file)
        
        # Extract metadata
        song_info = self._extract_metadata(selected_file)
        song_info['file_path'] = str(selected_file)
        
        self.logger.info(f"Selected song: {song_info['title']} by {song_info['artist']}")
        return song_info
    
    def _extract_metadata(self, file_path: Path) -> dict:
        """Extract title and artist from MP3 metadata"""
        try:
            audio_file = MutagenFile(file_path)
            
            title = "Unknown Title"
            artist = "Unknown Artist"
            
            if audio_file is not None:
                # Try different tag formats
                if 'TIT2' in audio_file:  # ID3v2.4
                    title = str(audio_file['TIT2'][0])
                elif 'TITLE' in audio_file:  # Vorbis
                    title = str(audio_file['TITLE'][0])
                elif hasattr(audio_file, 'title') and audio_file.title:
                    title = str(audio_file.title[0])
                
                if 'TPE1' in audio_file:  # ID3v2.4
                    artist = str(audio_file['TPE1'][0])
                elif 'ARTIST' in audio_file:  # Vorbis
                    artist = str(audio_file['ARTIST'][0])
                elif hasattr(audio_file, 'artist') and audio_file.artist:
                    artist = str(audio_file.artist[0])
            
            # If no metadata found, use filename
            if title == "Unknown Title":
                title = file_path.stem
                
        except Exception as e:
            self.logger.warning(f"Could not extract metadata from {file_path}: {e}")
            title = file_path.stem
            artist = "Unknown Artist"
        
        return {
            'title': title,
            'artist': artist
        }
