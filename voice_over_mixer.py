import asyncio
import edge_tts
import random
import logging
from pathlib import Path
from pydub import AudioSegment
from pydub.playback import play
import io
import tempfile
import os
import config

class VoiceOverMixer:
    """Creates voice-over using edge-tts and mixes with background music"""
    
    def __init__(self, background_music_folder: str):
        self.background_music_folder = Path(background_music_folder)
        self.logger = logging.getLogger(__name__)
        
        # Available voices - you can change these to your preference
        self.voices = [
            "en-US-AriaNeural",
            "en-US-DavisNeural", 
            "en-US-GuyNeural",
            "en-US-JennyNeural"
        ]
        
    async def create_mixed_introduction(self, text: str, output_path: str = None) -> str:
        """
        Create a mixed audio file with TTS voice-over and background music
        Returns path to the generated audio file
        """
        if output_path is None:
            output_path = tempfile.mktemp(suffix=".mp3")
        
        try:
            # Generate TTS audio
            tts_audio_path = await self._generate_tts(text)
            
            # Get random background music
            background_path = self._get_random_background()
            
            # Mix the audio
            mixed_path = self._mix_audio(tts_audio_path, background_path, output_path)
            
            # Clean up temporary TTS file
            if os.path.exists(tts_audio_path):
                os.remove(tts_audio_path)
            
            self.logger.info(f"Created mixed introduction: {mixed_path}")
            return mixed_path
            
        except Exception as e:
            self.logger.error(f"Failed to create mixed introduction: {e}")
            raise
    
    async def _generate_tts(self, text: str) -> str:
        """Generate TTS audio using edge-tts"""
        voice = random.choice(self.voices)
        output_path = tempfile.mktemp(suffix=".mp3")
        
        try:
            self.logger.info(f"Generating TTS with voice {voice}")
            self.logger.debug(f"TTS text: {text}")
            
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            
            # Verify the file was created and has content
            if not os.path.exists(output_path):
                raise Exception(f"TTS file not created: {output_path}")
            
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise Exception(f"TTS file is empty: {output_path}")
            
            self.logger.info(f"Generated TTS with voice {voice} - {file_size} bytes")
            return output_path
            
        except Exception as e:
            self.logger.error(f"TTS generation failed: {e}")
            # Try with a different voice as fallback
            fallback_voice = "en-US-AriaNeural"  # Most reliable voice
            if fallback_voice != voice:
                self.logger.info(f"Retrying TTS with fallback voice: {fallback_voice}")
                try:
                    communicate = edge_tts.Communicate(text, fallback_voice)
                    await communicate.save(output_path)
                    
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        self.logger.info(f"Fallback TTS successful with {fallback_voice}")
                        return output_path
                except Exception as fallback_error:
                    self.logger.error(f"Fallback TTS also failed: {fallback_error}")
            
            raise Exception(f"TTS generation failed for both primary and fallback voices: {e}")
    
    def _get_random_background(self) -> str:
        """Select random background music file"""
        bg_files = list(self.background_music_folder.glob("*.mp3"))
        
        if not bg_files:
            raise ValueError("No background music files found")
        
        selected = random.choice(bg_files)
        self.logger.info(f"Selected background music: {selected.name}")
        return str(selected)
    
    def _mix_audio(self, tts_path: str, background_path: str, output_path: str) -> str:
        """Mix TTS audio with background music and add buffers for smooth crossfades"""
        # Load audio files
        tts_audio = AudioSegment.from_mp3(tts_path)
        background_audio = AudioSegment.from_mp3(background_path)
        
        # Reduce background music volume to 30%
        background_audio = background_audio - 10  # Reduce by 10dB (roughly 30% volume)
        
        # Add configurable buffer duration before and after TTS for smooth crossfades
        buffer_duration = getattr(config, 'INTRO_BUFFER_DURATION', 3000)  # Default to 3 seconds
        total_duration = len(tts_audio) + (2 * buffer_duration)  # Buffer before + TTS + buffer after
        
        # Ensure background music is long enough for buffers + TTS
        if len(background_audio) < total_duration:
            # Loop background music if it's shorter than needed
            loops_needed = (total_duration // len(background_audio)) + 1
            background_audio = background_audio * loops_needed
        
        # Trim background to match total duration (buffer + TTS + buffer)
        background_audio = background_audio[:total_duration]
        
        # Add fade in/out to background music
        background_audio = background_audio.fade_in(500).fade_out(1000)
        
        # Overlay TTS on background music starting after the initial buffer
        # This leaves buffer_duration at start and end as background-only for crossfades
        mixed_audio = background_audio.overlay(tts_audio, position=buffer_duration)
        
        self.logger.info(f"Mixed audio with {buffer_duration}ms buffers (before/after) - total duration: {len(mixed_audio)}ms")
        self.logger.debug(f"Structure: {buffer_duration}ms buffer + {len(tts_audio)}ms TTS + {buffer_duration}ms buffer")
        
        # Export mixed audio
        mixed_audio.export(output_path, format="mp3")
        
        self.logger.info(f"Mixed audio exported to: {output_path}")
        return output_path
