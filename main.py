import asyncio
import logging
import threading
import time
import tempfile
import os
from pathlib import Path
from pydub import AudioSegment
from collections import deque
from dataclasses import dataclass
from typing import Optional

from music_selector import MusicSelector
from announcement_generator import AnnouncementGenerator
from voice_over_mixer import VoiceOverMixer
from audio_player import AudioPlayer

@dataclass
class PlaylistItem:
    """Represents an item in the radio playlist queue"""
    audio_path: str
    item_type: str  # 'intro', 'song', 'news'
    title: Optional[str] = None
    artist: Optional[str] = None
    cleanup_after: bool = False  # Whether to delete the file after playing

class AIDJApp:
    """Main AI DJ application with queue-based playlist management"""
    
    def __init__(self, music_folder: str, background_music_folder: str):
        self.music_folder = music_folder
        self.background_music_folder = background_music_folder
        
        # Initialize components
        self.music_selector = MusicSelector(music_folder)
        self.announcement_generator = AnnouncementGenerator()
        self.voice_mixer = VoiceOverMixer(background_music_folder)
        self.audio_player = AudioPlayer()
        
        # Queue-based playlist
        self.playlist_queue = deque()
        self.currently_playing = None
        
        # State management
        self.is_running = False
        self.songs_since_news = 0
        self.news_frequency = 3
        self.overlap_allowed = False  # Flag to indicate when next intro can start
        self.manual_dj_mode = False  # Flag for manual DJ takeover
        self.pause_after_song = False  # Flag to pause after current song
        
        # Timing constants
        self.crossfade_duration = 3000  # 3 second crossfade in milliseconds
        self.song_overlap_duration = 2.0  # 2 seconds of intro over song outro
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Add debug logging for audio issues
        logging.getLogger('voice_over_mixer').setLevel(logging.DEBUG)
        logging.getLogger('audio_player').setLevel(logging.DEBUG)
        
    async def start_radio(self):
        """Start the AI DJ radio station with queue-based playlist"""
        self.logger.info("Starting AI DJ Radio Station with queue-based playlist...")
        self.is_running = True
        
        try:
            # Start background tasks
            playlist_task = asyncio.create_task(self._maintain_playlist())
            playback_task = asyncio.create_task(self._process_playlist())
            keyboard_task = asyncio.create_task(self._keyboard_handler())
            
            # Wait for all tasks
            await asyncio.gather(playlist_task, playback_task, keyboard_task)
            
        except KeyboardInterrupt:
            self.logger.info("Received stop signal")
        except Exception as e:
            self.logger.error(f"Error in radio loop: {e}")
        finally:
            self.stop_radio()
    
    async def _keyboard_handler(self):
        """Handle keyboard commands for manual DJ control"""
        import msvcrt
        
        self.logger.info("Keyboard controls:")
        self.logger.info("  'p' - Pause AI DJ after current song")
        self.logger.info("  'r' - Resume AI DJ")
        self.logger.info("  's' - Show current status")
        self.logger.info("  'q' - Quit")
        
        while self.is_running:
            try:
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8').lower()
                    
                    if key == 'p':
                        await self._enable_manual_dj_mode()
                    elif key == 'r':
                        await self._disable_manual_dj_mode()
                    elif key == 's':
                        self._show_status()
                    elif key == 'q':
                        self.logger.info("Quit requested by user")
                        self.is_running = False
                        break
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.warning(f"Keyboard handler error: {e}")
                await asyncio.sleep(1.0)
    
    async def _enable_manual_dj_mode(self):
        """Enable manual DJ mode - pause after current song"""
        if self.manual_dj_mode:
            self.logger.info("Manual DJ mode already enabled")
            return
        
        self.pause_after_song = True
        self.logger.info("🎧 MANUAL DJ MODE: Will pause after current song finishes")
        self.logger.info("   You can then manually play music, talk, etc.")
        self.logger.info("   Press 'r' to resume AI DJ when ready")
    
    async def _disable_manual_dj_mode(self):
        """Disable manual DJ mode - resume AI DJ"""
        if not self.manual_dj_mode:
            self.logger.info("AI DJ is already running")
            return
        
        self.manual_dj_mode = False
        self.pause_after_song = False
        self.logger.info("🤖 AI DJ RESUMED: Taking control back from manual DJ")
        
        # If no audio is currently playing, start the next item immediately
        if not self.audio_player.is_audio_playing():
            self.logger.info("No audio playing - AI DJ will start immediately")
    
    def _show_status(self):
        """Show current AI DJ status"""
        if self.manual_dj_mode:
            status = "🎧 MANUAL DJ MODE (AI Paused)"
        elif self.pause_after_song:
            status = "⏸️ AI DJ (Will pause after current song)"
        else:
            status = "🤖 AI DJ (Active)"
        
        queue_length = len(self.playlist_queue)
        currently_playing = self.currently_playing.title if self.currently_playing else "Nothing"
        
        self.logger.info(f"Status: {status}")
        self.logger.info(f"Currently Playing: {currently_playing}")
        self.logger.info(f"Queue Length: {queue_length} items")
        self.logger.info(f"Audio Playing: {self.audio_player.is_audio_playing()}")
    
    async def _maintain_playlist(self):
        """Keep the playlist queue filled with upcoming content"""
        while self.is_running:
            try:
                # Don't add content if in manual DJ mode
                if self.manual_dj_mode:
                    await asyncio.sleep(3.0)
                    continue
                
                # Keep 3-5 items in the queue ahead of current playback
                while len(self.playlist_queue) < 4 and self.is_running and not self.manual_dj_mode:
                    await self._add_next_segment_to_queue()
                    
                # Check every few seconds
                await asyncio.sleep(3.0)
                
            except Exception as e:
                self.logger.error(f"Error maintaining playlist: {e}")
                await asyncio.sleep(5.0)
    
    async def _add_next_segment_to_queue(self):
        """Add the next intro + song pair to the queue"""
        try:
            # Select next song
            song_info = self.music_selector.get_random_song()
            self.logger.info(f"Queuing: {song_info['title']} by {song_info['artist']}")
            
            # Generate and create introduction
            should_play_news = self.songs_since_news >= self.news_frequency
            
            if should_play_news:
                self.logger.info("Generating news announcement...")
                intro_text = self.announcement_generator.generate_news_announcement(
                    song_info['title'], song_info['artist']
                )
                item_type = 'news'
                self.songs_since_news = 0
            else:
                intro_text = self.announcement_generator.generate_introduction(
                    song_info['title'], song_info['artist']
                )
                item_type = 'intro'
                self.songs_since_news += 1
            
            # Create mixed introduction
            intro_path = await self.voice_mixer.create_mixed_introduction(intro_text)
            
            # Verify intro file
            if not os.path.exists(intro_path) or os.path.getsize(intro_path) == 0:
                raise Exception(f"Introduction audio file invalid: {intro_path}")
            
            # Add intro to queue
            intro_item = PlaylistItem(
                audio_path=intro_path,
                item_type=item_type,
                title=f"Intro for {song_info['title']}",
                cleanup_after=True
            )
            self.playlist_queue.append(intro_item)
            
            # Add song to queue
            song_item = PlaylistItem(
                audio_path=song_info['file_path'],
                item_type='song',
                title=song_info['title'],
                artist=song_info['artist'],
                cleanup_after=False
            )
            self.playlist_queue.append(song_item)
            
            self.logger.info(f"Added intro + song to queue. Queue length: {len(self.playlist_queue)}")
            
        except Exception as e:
            self.logger.error(f"Error adding segment to queue: {e}")
    
    async def _process_playlist(self):
        """Process items from the playlist queue with professional transitions"""
        while self.is_running:
            try:
                # Check if we should pause for manual DJ
                if self.manual_dj_mode:
                    await asyncio.sleep(1.0)
                    continue
                
                if not self.playlist_queue:
                    await asyncio.sleep(0.5)
                    continue
                
                # Get next item
                next_item = self.playlist_queue.popleft()
                self.currently_playing = next_item
                
                # If this is an intro/news and the previous item was a song, wait for overlap permission
                if next_item.item_type in ['intro', 'news'] and self.audio_player.is_audio_playing():
                    # Wait for overlap to be allowed
                    while self.is_running and not self.overlap_allowed and self.audio_player.is_audio_playing():
                        await asyncio.sleep(0.1)
                
                await self._play_item_with_transitions(next_item)
                
                # Check if we should pause after this item (for manual DJ mode)
                if self.pause_after_song and next_item.item_type == 'song':
                    self.manual_dj_mode = True
                    self.pause_after_song = False
                    self.logger.info("🎧 MANUAL DJ MODE ACTIVATED")
                    self.logger.info("   AI DJ is now paused. You have control!")
                    self.logger.info("   Press 'r' to resume AI DJ when ready")
                
                # Reset overlap flag after each item
                self.overlap_allowed = False
                
            except Exception as e:
                self.logger.error(f"Error processing playlist: {e}")
                await asyncio.sleep(2.0)
    
    async def _play_item_with_transitions(self, item: PlaylistItem):
        """Play an item with appropriate transitions based on type"""
        self.logger.info(f"Playing {item.item_type}: {item.title}")
        
        # Start playback with crossfade
        if self.audio_player.is_audio_playing():
            self.logger.info(f"Crossfading to {item.item_type}")
            self.audio_player.play_next_audio_realtime_crossfade(
                item.audio_path, 
                self.crossfade_duration
            )
        else:
            self.logger.info(f"Starting {item.item_type} (no crossfade)")
            self.audio_player.play_next_audio_realtime_crossfade(
                item.audio_path, 
                0  # No crossfade needed
            )
        
        # Handle different transition types
        if item.item_type == 'song':
            await self._wait_for_song_with_overlap(item)
        else:  # intro or news
            await self._wait_for_complete_playback(item)
        
        # Cleanup if needed
        if item.cleanup_after:
            threading.Timer(5.0, lambda: self._cleanup_file(item.audio_path)).start()
    
    async def _wait_for_song_with_overlap(self, song_item: PlaylistItem):
        """Wait for song to play, but allow overlap for next intro"""
        try:
            # Get song duration
            song_audio = AudioSegment.from_mp3(song_item.audio_path)
            song_duration = len(song_audio) / 1000.0
            
            # Calculate when to allow next item to start (10 seconds before end)
            overlap_start_time = max(3.0, song_duration - self.song_overlap_duration)
            
            self.logger.info(f"Song duration: {song_duration:.1f}s, will allow overlap at {overlap_start_time:.1f}s")
            
            # Wait for the overlap point
            start_time = time.time()
            while self.is_running and self.audio_player.is_audio_playing():
                elapsed_time = time.time() - start_time
                
                if elapsed_time >= overlap_start_time:
                    self.logger.info(f"Song overlap point reached - allowing next intro")
                    self.overlap_allowed = True  # Signal that overlap can start
                    break  # Exit timing loop but continue waiting for song to finish
                
                await asyncio.sleep(0.1)
            
            # Wait for song to completely finish
            while self.is_running and self.audio_player.is_audio_playing():
                await asyncio.sleep(0.1)
            
            self.logger.info(f"Song finished: {song_item.title}")
                
        except Exception as e:
            self.logger.warning(f"Could not determine song timing: {e}, waiting for completion")
            await self._wait_for_complete_playback(song_item)
    
    async def _wait_for_complete_playback(self, item: PlaylistItem):
        """Wait for item to completely finish playing"""
        # Wait for playback to complete
        while self.is_running and self.audio_player.is_audio_playing():
            await asyncio.sleep(0.1)
        
        self.logger.info(f"Finished playing {item.item_type}: {item.title}")
    
    def _cleanup_file(self, file_path: str):
        """Clean up temporary files"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                self.logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            self.logger.warning(f"Could not clean up file {file_path}: {e}")
    
    def stop_radio(self):
        """Stop the radio station"""
        self.logger.info("Stopping AI DJ Radio Station...")
        self.is_running = False
        self.audio_player.stop_current_playback()
        
        # Clean up any queued temporary files
        for item in self.playlist_queue:
            if item.cleanup_after:
                self._cleanup_file(item.audio_path)
        
        self.playlist_queue.clear()

# Main execution
async def main():
    # Configuration
    MUSIC_FOLDER = "music"
    BACKGROUND_MUSIC_FOLDER = "background music"
    
    # Create AI DJ instance
    ai_dj = AIDJApp(MUSIC_FOLDER, BACKGROUND_MUSIC_FOLDER)
    
    try:
        await ai_dj.start_radio()
    except KeyboardInterrupt:
        print("\nShutting down AI DJ...")
        ai_dj.stop_radio()

if __name__ == "__main__":
    print("🎵 AI DJ Radio Station 🎵")
    print("Press Ctrl+C to stop")
    print("Keyboard Controls:")
    print("  'p' - Pause AI DJ after current song (Manual DJ mode)")
    print("  'r' - Resume AI DJ")
    print("  's' - Show status")
    print("  'q' - Quit")
    print("-" * 50)
    
    asyncio.run(main())
