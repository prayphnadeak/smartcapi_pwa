"""
Silence Detection Service for Real-time Audio Processing

This service detects silence periods in audio streams to trigger
automatic transcription and extraction.
"""

import numpy as np
import librosa
from typing import List, Tuple
from app.core.config import settings
from app.core.logger import ml_logger


class SilenceDetector:
    """
    Detects silence periods in audio streams
    """
    
    # Function to initialize SilenceDetector
    def __init__(
        self, 
        threshold: float = None,
        min_duration: float = None,
        sample_rate: int = None
    ):
        """
        Initialize silence detector
        
        Args:
            threshold: RMS energy threshold for silence (default from settings)
            min_duration: Minimum silence duration in seconds (default from settings)
            sample_rate: Audio sample rate (default from settings)
        """
        self.threshold = threshold or settings.SILENCE_THRESHOLD
        self.min_duration = min_duration or getattr(settings, 'SILENCE_MIN_DURATION', 1.5)
        self.sample_rate = sample_rate or settings.SAMPLE_RATE
        
        # State tracking
        self.silence_start_time = None
        self.is_in_silence = False
        self.total_silence_duration = 0.0
        
        ml_logger.info(
            f"SilenceDetector initialized: threshold={self.threshold}, "
            f"min_duration={self.min_duration}s"
        )
    
    # Function to reset detector state
    def reset(self):
        """Reset detector state"""
        self.silence_start_time = None
        self.is_in_silence = False
        self.total_silence_duration = 0.0
    
    # Function to calculate RMS energy
    def calculate_rms_energy(self, audio_data: np.ndarray) -> float:
        """
        Calculate RMS (Root Mean Square) energy of audio
        
        Args:
            audio_data: Audio samples as numpy array
            
        Returns:
            RMS energy value
        """
        try:
            # Calculate RMS energy
            rms = np.sqrt(np.mean(audio_data ** 2))
            return float(rms)
        except Exception as e:
            ml_logger.error(f"Error calculating RMS: {str(e)}")
            return 0.0
    
    # Function to check if audio is silence
    def is_silence(self, audio_data: np.ndarray) -> bool:
        """
        Check if audio data represents silence
        
        Args:
            audio_data: Audio samples as numpy array
            
        Returns:
            True if audio is silence, False otherwise
        """
        rms = self.calculate_rms_energy(audio_data)
        return rms < self.threshold
    
    # Function to process audio chunk
    def process_chunk(
        self, 
        audio_data: np.ndarray,
        chunk_duration: float
    ) -> Tuple[bool, float]:
        """
        Process an audio chunk and update silence state
        
        Args:
            audio_data: Audio samples as numpy array
            chunk_duration: Duration of the chunk in seconds
            
        Returns:
            Tuple of (silence_detected, silence_duration)
            - silence_detected: True if silence window exceeded min_duration
            - silence_duration: Current total silence duration
        """
        is_silent = self.is_silence(audio_data)
        
        if is_silent:
            if not self.is_in_silence:
                # Start of silence period
                self.is_in_silence = True
                self.silence_start_time = 0.0
                ml_logger.debug("Silence started")
            
            # Accumulate silence duration
            self.total_silence_duration += chunk_duration
            
            # Check if silence window exceeded
            if self.total_silence_duration >= self.min_duration:
                ml_logger.info(
                    f"Silence window detected: {self.total_silence_duration:.2f}s"
                )
                return True, self.total_silence_duration
        else:
            if self.is_in_silence:
                # End of silence period (but didn't reach threshold)
                ml_logger.debug(
                    f"Silence ended (too short): {self.total_silence_duration:.2f}s"
                )
                self.reset()
        
        return False, self.total_silence_duration
    
    # Function to process audio bytes
    def process_audio_bytes(
        self, 
        audio_bytes: bytes,
        chunk_duration: float = None
    ) -> Tuple[bool, float]:
        """
        Process audio from bytes
        
        Args:
            audio_bytes: Audio data as bytes
            chunk_duration: Duration of the chunk in seconds (auto-calculated if None)
            
        Returns:
            Tuple of (silence_detected, silence_duration)
        """
        try:
            # Convert bytes to numpy array
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
            
            # Normalize to [-1, 1]
            audio_data = audio_data / 32768.0
            
            # Calculate duration if not provided
            if chunk_duration is None:
                chunk_duration = len(audio_data) / self.sample_rate
            
            return self.process_chunk(audio_data, chunk_duration)
        except Exception as e:
            ml_logger.error(f"Error processing audio bytes: {str(e)}")
            return False, 0.0
    
    # Function to analyze audio file
    def analyze_audio_file(self, audio_path: str) -> List[Tuple[float, float]]:
        """
        Analyze an audio file and return all silence periods
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            List of (start_time, end_time) tuples for silence periods
        """
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Calculate RMS energy with frames
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.01 * sr)     # 10ms hop
            
            rms = librosa.feature.rms(
                y=audio, 
                frame_length=frame_length, 
                hop_length=hop_length
            )[0]
            
            # Convert frame indices to time
            times = librosa.frames_to_time(
                np.arange(len(rms)), 
                sr=sr, 
                hop_length=hop_length
            )
            
            # Find silence frames
            silence_frames = np.where(rms < self.threshold)[0]
            
            # Group consecutive silence frames
            silence_periods = []
            if len(silence_frames) > 0:
                start_frame = silence_frames[0]
                prev_frame = silence_frames[0]
                
                for frame in silence_frames[1:]:
                    if frame != prev_frame + 1:  # Not consecutive
                        start_time = times[start_frame]
                        end_time = times[prev_frame]
                        
                        # Check if duration exceeds minimum
                        if end_time - start_time >= self.min_duration:
                            silence_periods.append((start_time, end_time))
                        
                        start_frame = frame
                    
                    prev_frame = frame
                
                # Add the last period
                start_time = times[start_frame]
                end_time = times[prev_frame]
                
                if end_time - start_time >= self.min_duration:
                    silence_periods.append((start_time, end_time))
            
            ml_logger.info(f"Found {len(silence_periods)} silence periods in {audio_path}")
            return silence_periods
            
        except Exception as e:
            ml_logger.error(f"Error analyzing audio file: {str(e)}")
            return []


# Singleton instance
silence_detector = SilenceDetector()
