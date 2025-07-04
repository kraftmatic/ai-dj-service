import threading
import time
import logging
from pathlib import Path
from pydub import AudioSegment
from pydub.playback import play
import pygame
import os
import tempfile

class AudioPlayer:
    """Handles audio playback with crossfading capabilities"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_thread = None
        self.stop_playback = threading.Event()
        self.is_playing = False
        self.current_audio_path = None  # Track what's currently playing
        self.current_sound = None  # Track pygame Sound object
        self.current_channel = None  # Track pygame channel
        self.channel_id = 0  # Unique ID for tracking which channel is current
        
        # Initialize pygame mixer with more channels for overlapping
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024)
        pygame.mixer.init(channels=8)  # Allow up to 8 simultaneous sounds
        
    def play_with_crossfade(self, intro_path: str, song_path: str, crossfade_duration: int = 3000):
        """
        Play introduction followed by song with crossfade
        crossfade_duration in milliseconds
        """
        if self.is_playing:
            self.stop_current_playback()
        
        self.stop_playback.clear()
        self.current_thread = threading.Thread(
            target=self._play_sequence_seamless,
            args=(intro_path, song_path, crossfade_duration)
        )
        self.current_thread.daemon = True
        self.current_thread.start()
    
    def _play_sequence_seamless(self, intro_path: str, song_path: str, crossfade_duration: int):
        """Create and play a seamless sequence without replaying intro content"""
        try:
            self.is_playing = True
            self.logger.info(f"Playing introduction: {Path(intro_path).name}")
            
            # Load audio files
            intro_audio = AudioSegment.from_mp3(intro_path)
            song_audio = AudioSegment.from_mp3(song_path)
            
            # Create the complete sequence in memory
            if len(intro_audio) > crossfade_duration:
                # Split intro: main part + crossfade part
                intro_main = intro_audio[:-crossfade_duration]
                intro_crossfade = intro_audio[-crossfade_duration:]
            else:
                # If intro is very short, use smaller crossfade
                actual_crossfade = min(crossfade_duration, len(intro_audio) // 2)
                intro_main = intro_audio[:-actual_crossfade] if actual_crossfade > 0 else intro_audio
                intro_crossfade = intro_audio[-actual_crossfade:] if actual_crossfade > 0 else AudioSegment.empty()
                crossfade_duration = actual_crossfade
            
            # Create crossfade segment
            if len(intro_crossfade) > 0 and crossfade_duration > 0:
                self.logger.info(f"Creating crossfade transition ({crossfade_duration}ms)")
                song_beginning = song_audio[:crossfade_duration]
                
                # Apply fades
                intro_faded = intro_crossfade.fade_out(crossfade_duration)
                song_faded = song_beginning.fade_in(crossfade_duration)
                
                # Create crossfade by overlaying
                crossfade_segment = intro_faded.overlay(song_faded)
                
                # Combine: intro_main + crossfade + rest_of_song
                complete_sequence = intro_main + crossfade_segment + song_audio[crossfade_duration:]
            else:
                # No crossfade, just concatenate
                complete_sequence = intro_audio + song_audio
            
            self.logger.info(f"Playing complete sequence to song: {Path(song_path).name}")
            
            # Play the complete sequence
            self._play_audio_segment(complete_sequence)
            
            self.logger.info("Finished playing song")
            
        except Exception as e:
            self.logger.error(f"Error during playback: {e}")
        finally:
            self.is_playing = False
    
    def _play_audio_segment(self, audio_segment: AudioSegment):
        """Play an audio segment using pygame"""
        try:
            self.is_playing = True
            self.playback_start_time = time.time()
            
            # Export to temporary file for pygame
            import tempfile
            temp_file = tempfile.mktemp(suffix=".wav")
            audio_segment.export(temp_file, format="wav")
            
            # Load and play with pygame
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for playback to finish or stop signal
            while pygame.mixer.music.get_busy():
                if self.stop_playback.is_set():
                    # Fade out current audio for smooth transition
                    pygame.mixer.music.fadeout(1000)  # 1 second fade out
                    break
                time.sleep(0.1)
            
            # Clean up temp file
            try:
                os.remove(temp_file)
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Error playing audio segment: {e}")
        finally:
            self.is_playing = False
    
    def stop_current_playback(self):
        """Stop current playback"""
        self.logger.info("Stopping current playback")
        
        # Stop channel-based playback
        if self.current_channel and self.current_channel.get_busy():
            self.current_channel.stop()
        
        # Stop music-based playback (fallback)
        self.stop_playback.set()
        pygame.mixer.music.stop()
        
        if self.current_thread and self.current_thread.is_alive():
            self.current_thread.join(timeout=2)
        
        self.is_playing = False
    
    def get_song_duration(self, song_path: str) -> int:
        """Get duration of song in milliseconds"""
        try:
            audio = AudioSegment.from_mp3(song_path)
            return len(audio)
        except Exception as e:
            self.logger.error(f"Could not get duration for {song_path}: {e}")
            return 180000  # Default to 3 minutes
    
    def play_preloaded_audio(self, audio_segment: AudioSegment):
        """
        Play a pre-loaded audio segment for seamless transitions
        """
        if self.is_playing:
            self.stop_current_playback()
        
        self.stop_playback.clear()
        self.current_thread = threading.Thread(
            target=self._play_audio_segment,
            args=(audio_segment,)
        )
        self.current_thread.daemon = True
        self.current_thread.start()
    
    def get_current_playback_position(self):
        """
        Get the current playback position (approximate)
        Returns time in seconds since playback started
        """
        if hasattr(self, 'playback_start_time') and self.is_playing:
            return time.time() - self.playback_start_time
        return 0
    

    
    def play_next_audio(self, next_audio_path: str, crossfade_duration: int = 3000):
        """
        Create a true crossfade by mixing the end of current audio with start of next audio
        
        Args:
            next_audio_path: Path to the next audio file to play
            crossfade_duration: Duration of crossfade in milliseconds (default 3 seconds)
        """
        try:
            self.logger.info(f"Creating true crossfade to: {Path(next_audio_path).name}")
            
            # If nothing is currently playing, just play the new audio
            if not self.is_playing or not self.current_audio_path:
                self.logger.info("No current playback, starting new audio directly")
                self._play_single_audio(next_audio_path)
                return
            
            # Load both audio files
            current_audio = AudioSegment.from_mp3(self.current_audio_path)
            next_audio = AudioSegment.from_mp3(next_audio_path)
            
            # Get current playback position
            current_pos_ms = self.get_current_playback_position() * 1000
            
            # Create the crossfaded transition
            crossfaded_audio = self._create_true_crossfade(
                current_audio, next_audio, current_pos_ms, crossfade_duration
            )
            
            # Stop current playback and play crossfaded audio
            self.stop_current_playback()
            
            # Track new audio path
            self.current_audio_path = next_audio_path
            
            # Play the crossfaded sequence
            self.stop_playback.clear()
            self.current_thread = threading.Thread(
                target=self._play_audio_segment,
                args=(crossfaded_audio,)
            )
            self.current_thread.daemon = True
            self.current_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error creating true crossfade: {e}")
            # Fallback: just play the new audio
            self._play_single_audio(next_audio_path)
    
    def _create_true_crossfade(self, current_audio: AudioSegment, next_audio: AudioSegment, 
                              current_pos_ms: float, crossfade_duration: int) -> AudioSegment:
        """
        Create a true crossfade by mixing audio segments
        """
        try:
            self.logger.info(f"Mixing crossfade at position {current_pos_ms/1000:.1f}s")
            
            # Get remaining part of current audio from current position
            remaining_current = current_audio[int(current_pos_ms):]
            
            # If remaining audio is shorter than crossfade, use what we have
            actual_crossfade_duration = min(crossfade_duration, len(remaining_current))
            
            if actual_crossfade_duration <= 0:
                # No remaining audio to crossfade, just return next audio
                return next_audio
            
            # Get the crossfade portion of current audio (end part)
            if len(remaining_current) > actual_crossfade_duration:
                # Play some of remaining current, then crossfade the end
                pre_crossfade = remaining_current[:-actual_crossfade_duration]
                current_crossfade_part = remaining_current[-actual_crossfade_duration:]
            else:
                # All remaining audio will be crossfaded
                pre_crossfade = AudioSegment.empty()
                current_crossfade_part = remaining_current
                actual_crossfade_duration = len(remaining_current)
            
            # Get the beginning of next audio for crossfade
            next_crossfade_part = next_audio[:actual_crossfade_duration]
            next_remainder = next_audio[actual_crossfade_duration:]
            
            # Apply fades
            current_faded = current_crossfade_part.fade_out(actual_crossfade_duration)
            next_faded = next_crossfade_part.fade_in(actual_crossfade_duration)
            
            # Mix the crossfade parts
            if len(current_faded) > 0 and len(next_faded) > 0:
                # Ensure both parts are same length
                min_length = min(len(current_faded), len(next_faded))
                crossfade_mix = current_faded[:min_length].overlay(next_faded[:min_length])
            else:
                crossfade_mix = next_faded
            
            # Combine: pre_crossfade + crossfade_mix + remainder_of_next
            result = pre_crossfade + crossfade_mix + next_remainder
            
            self.logger.info(f"Created crossfaded audio: {len(result)/1000:.1f}s total")
            return result
            
        except Exception as e:
            self.logger.error(f"Error mixing crossfade: {e}")
            return next_audio  # Fallback to just next audio
    
    def play_next_audio_with_overlap(self, current_audio_path: str, next_audio_path: str, crossfade_duration: int = 3000):
        """
        Create a proper crossfade by pre-creating the overlapped audio
        This method requires knowing what's currently playing to create a true crossfade
        
        Args:
            current_audio_path: Path to currently playing audio (for creating the crossfade)
            next_audio_path: Path to the next audio file to play
            crossfade_duration: Duration of crossfade in milliseconds
        """
        try:
            self.logger.info(f"Creating overlapped crossfade: {Path(current_audio_path).name} → {Path(next_audio_path).name}")
            
            # Load both audio files
            current_audio = AudioSegment.from_mp3(current_audio_path)
            next_audio = AudioSegment.from_mp3(next_audio_path)
            
            # Get current playback position (approximate)
            current_position_ms = self.get_current_playback_position() * 1000
            
            # Calculate where to start the crossfade in the current audio
            crossfade_start = len(current_audio) - crossfade_duration
            if current_position_ms < crossfade_start:
                # We're not at the crossfade point yet, so take the remaining audio
                remaining_current = current_audio[int(current_position_ms):]
                
                # If remaining audio is longer than crossfade duration, trim it for the crossfade
                if len(remaining_current) > crossfade_duration:
                    crossfade_part = remaining_current[-crossfade_duration:].fade_out(crossfade_duration)
                    pre_crossfade = remaining_current[:-crossfade_duration]
                else:
                    crossfade_part = remaining_current.fade_out(len(remaining_current))
                    pre_crossfade = AudioSegment.empty()
            else:
                # We're already in crossfade territory
                remaining_duration = len(current_audio) - current_position_ms
                crossfade_part = current_audio[int(current_position_ms):].fade_out(int(remaining_duration))
                pre_crossfade = AudioSegment.empty()
            
            # Create fade-in for next audio
            next_beginning = next_audio[:crossfade_duration]
            next_rest = next_audio[crossfade_duration:]
            next_faded = next_beginning.fade_in(crossfade_duration)
            
            # Create the crossfaded segment by overlaying
            if len(crossfade_part) > 0:
                # Make sure both segments are the same length for overlay
                min_length = min(len(crossfade_part), len(next_faded))
                crossfade_segment = crossfade_part[:min_length].overlay(next_faded[:min_length])
                
                # Combine: pre-crossfade + crossfade + rest of next audio
                complete_sequence = pre_crossfade + crossfade_segment + next_rest
            else:
                # No crossfade possible, just use faded next audio
                complete_sequence = next_faded + next_rest
            
            # Stop current playback and play the crossfaded sequence
            self.stop_current_playback()
            
            self.stop_playback.clear()
            self.current_thread = threading.Thread(
                target=self._play_audio_segment,
                args=(complete_sequence,)
            )
            self.current_thread.daemon = True
            self.current_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error creating overlapped crossfade: {e}")
            # Fallback to simple transition
            self.play_next_audio(next_audio_path, crossfade_duration)
    
    def _play_single_audio(self, audio_path: str):
        """Play a single audio file using Sound for channel support"""
        import tempfile
        try:
            audio = AudioSegment.from_mp3(audio_path)
            
            if self.is_playing:
                self.stop_current_playback()
            
            # Convert to wav for pygame.mixer.Sound
            temp_file = tempfile.mktemp(suffix=".wav")
            audio.export(temp_file, format="wav")
            
            # Create Sound object and play on a channel
            sound = pygame.mixer.Sound(temp_file)
            channel = pygame.mixer.find_channel()
            channel.play(sound)
            
            # Track current playback
            self.current_audio_path = audio_path
            self.current_sound = sound
            self.current_channel = channel
            self.is_playing = True
            self.playback_start_time = time.time()
            self.channel_id += 1
            current_channel_id = self.channel_id
            
            # Monitor playback in background thread
            def monitor_playback():
                while channel.get_busy():
                    time.sleep(0.1)
                # Only set is_playing to False if this is still the current channel
                if self.channel_id == current_channel_id:
                    self.is_playing = False
                self._cleanup_file(temp_file)
            
            threading.Thread(target=monitor_playback, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error playing single audio: {e}")
    
    def play_next_audio_realtime_crossfade(self, next_audio_path: str, crossfade_duration: int = 3000):
        """
        Play next audio with a true real-time crossfade using pygame.mixer.Sound and channels.
        """
        import tempfile
        try:
            self.logger.info(f"Real-time crossfade to: {Path(next_audio_path).name}")
            
            # Load next audio and convert to wav for pygame.mixer.Sound
            next_audio = AudioSegment.from_mp3(next_audio_path)
            temp_file = tempfile.mktemp(suffix=".wav")
            next_audio.export(temp_file, format="wav")
            next_sound = pygame.mixer.Sound(temp_file)
            
            # If nothing is currently playing, just play the new audio directly
            if not self.is_playing or not self.current_channel or not self.current_channel.get_busy():
                self.logger.info("No current playback, starting new audio directly")
                # Play on a new channel
                next_channel = pygame.mixer.find_channel()
                next_channel.play(next_sound)
                
                # Update tracking
                self.current_sound = next_sound
                self.current_channel = next_channel
                self.current_audio_path = next_audio_path
                self.is_playing = True
                self.playback_start_time = time.time()
                self.channel_id += 1
                current_channel_id = self.channel_id
                
                # Monitor playback completion
                def monitor_playback():
                    while next_channel.get_busy():
                        time.sleep(0.1)
                    # Only set is_playing to False if this is still the current channel
                    if self.channel_id == current_channel_id:
                        self.is_playing = False
                    self._cleanup_file(temp_file)
                
                threading.Thread(target=monitor_playback, daemon=True).start()
                return
            
            # Get current channel before starting crossfade
            current_channel = self.current_channel
            
            # Start playing next audio on a new channel with volume 0
            next_channel = pygame.mixer.find_channel()
            next_channel.set_volume(0.0)
            next_channel.play(next_sound)
            
            # Execute crossfade
            self._execute_realtime_crossfade(current_channel, next_channel, crossfade_duration)
            
            # Update tracking to new audio
            self.current_sound = next_sound
            self.current_channel = next_channel
            self.current_audio_path = next_audio_path
            self.playback_start_time = time.time()
            self.channel_id += 1
            current_channel_id = self.channel_id
            
            # Schedule cleanup and monitor new playback
            def monitor_new_playback():
                while next_channel.get_busy():
                    time.sleep(0.1)
                # Only set is_playing to False if this is still the current channel
                if self.channel_id == current_channel_id:
                    self.is_playing = False
                self._cleanup_file(temp_file)
            
            threading.Thread(target=monitor_new_playback, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error in real-time crossfade: {e}")
            self._play_single_audio(next_audio_path)

    def _execute_realtime_crossfade(self, current_channel, next_channel, crossfade_duration: int):
        """
        Execute real-time crossfade by adjusting volumes of two simultaneously playing channels
        """
        try:
            self.logger.info(f"Executing real-time crossfade ({crossfade_duration}ms)")
            steps = 50
            step_duration = (crossfade_duration / 1000.0) / steps
            
            def crossfade_volumes():
                try:
                    for step in range(steps + 1):
                        # Check if channels are still active
                        current_active = current_channel and current_channel.get_busy()
                        next_active = next_channel and next_channel.get_busy()
                        
                        if not next_active:
                            self.logger.warning("Next channel stopped during crossfade")
                            break
                        
                        # Calculate volumes
                        current_volume = 1.0 - (step / steps) if current_active else 0.0
                        next_volume = step / steps
                        
                        # Apply volumes
                        if current_active:
                            current_channel.set_volume(current_volume)
                        if next_active:
                            next_channel.set_volume(next_volume)
                        
                        time.sleep(step_duration)
                    
                    # Ensure proper final state
                    if current_channel and current_channel.get_busy():
                        current_channel.stop()
                        self.logger.debug("Stopped current channel after crossfade")
                    
                    if next_channel and next_channel.get_busy():
                        next_channel.set_volume(1.0)
                        self.logger.debug("Set next channel to full volume")
                    
                except Exception as e:
                    self.logger.error(f"Error in crossfade thread: {e}")
            
            threading.Thread(target=crossfade_volumes, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error executing real-time crossfade: {e}")
            # Fallback: stop current and play next at full volume
            if current_channel:
                current_channel.stop()
            if next_channel:
                next_channel.set_volume(1.0)

    def wait_for_completion(self, timeout: float = None):
        """
        Wait for current audio to finish playing
        
        Args:
            timeout: Maximum time to wait in seconds (None for no limit)
            
        Returns:
            bool: True if audio finished naturally, False if timed out or stopped
        """
        start_time = time.time()
        
        while self.is_playing:
            if timeout and (time.time() - start_time) > timeout:
                self.logger.warning(f"Wait for completion timed out after {timeout}s")
                return False
            
            time.sleep(0.1)
        
        return True
    
    def is_audio_playing(self) -> bool:
        """Check if audio is currently playing"""
        return self.is_playing

    def _cleanup_file(self, file_path: str):
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                self.logger.debug(f"Cleaned up: {file_path}")
        except Exception as e:
            self.logger.warning(f"Could not clean up {file_path}: {e}")
