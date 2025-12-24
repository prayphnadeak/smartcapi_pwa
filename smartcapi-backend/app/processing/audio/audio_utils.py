import os
import librosa
import numpy as np
import soundfile as sf
from typing import Tuple, Optional, List
from app.core.config import settings
from app.core.logger import ml_logger

# Function to load audio file with specified sample rate
def load_audio(audio_path: str, sr: int = None) -> Tuple[np.ndarray, int]:
    """
    Load audio file
    
    Args:
        audio_path: Path to the audio file
        sr: Target sample rate (default: use settings)
        
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    try:
        if sr is None:
            sr = settings.SAMPLE_RATE
        
        audio, sample_rate = librosa.load(audio_path, sr=sr)
        return audio, sample_rate
    except Exception as e:
        ml_logger.error(f"Error loading audio {audio_path}: {str(e)}")
        return np.array([]), sr or settings.SAMPLE_RATE

# Function to save audio data to a file
def save_audio(audio: np.ndarray, output_path: str, sr: int = None) -> bool:
    """
    Save audio to file
    
    Args:
        audio: Audio data
        output_path: Path to save the audio file
        sr: Sample rate (default: use settings)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if sr is None:
            sr = settings.SAMPLE_RATE
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save audio
        sf.write(output_path, audio, sr)
        return True
    except Exception as e:
        ml_logger.error(f"Error saving audio to {output_path}: {str(e)}")
        return False

# Function to split audio into chunks of specific duration
def split_audio(audio: np.ndarray, chunk_duration: float, sr: int = None) -> list:
    """
    Split audio into chunks of specified duration
    
    Args:
        audio: Audio data
        chunk_duration: Duration of each chunk in seconds
        sr: Sample rate (default: use settings)
        
    Returns:
        List of audio chunks
    """
    try:
        if sr is None:
            sr = settings.SAMPLE_RATE
        
        chunk_samples = int(chunk_duration * sr)
        chunks = []
        
        for i in range(0, len(audio), chunk_samples):
            chunk = audio[i:i+chunk_samples]
            if len(chunk) > 0:  # Skip empty chunks
                chunks.append(chunk)
        
        return chunks
    except Exception as e:
        ml_logger.error(f"Error splitting audio: {str(e)}")
        return []

# Function to normalize audio amplitude
def normalize_audio(audio: np.ndarray) -> np.ndarray:
    """
    Normalize audio to have maximum amplitude of 1
    
    Args:
        audio: Audio data
        
    Returns:
        Normalized audio data
    """
    try:
        if len(audio) == 0:
            return audio
        
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio
    except Exception as e:
        ml_logger.error(f"Error normalizing audio: {str(e)}")
        return audio

# Function to apply noise reduction to audio data
def apply_noise_reduction(audio: np.ndarray, sr: int = None) -> np.ndarray:
    """
    Apply simple noise reduction to audio
    
    Args:
        audio: Audio data
        sr: Sample rate (default: use settings)
        
    Returns:
        Audio with reduced noise
    """
    try:
        if sr is None:
            sr = settings.SAMPLE_RATE
        
        # Simple spectral subtraction noise reduction
        # This is a placeholder implementation
        # In a real application, you might use a more sophisticated method
        
        # Compute STFT
        stft = librosa.stft(audio)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise from the first 0.5 seconds
        noise_frames = int(0.5 * sr / 512)  # Assuming hop_length of 512
        if magnitude.shape[1] > noise_frames:
            noise_magnitude = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
            
            # Apply spectral subtraction
            alpha = 2.0  # Over-subtraction factor
            magnitude = magnitude - alpha * noise_magnitude
            magnitude = np.maximum(magnitude, 0.1 * np.mean(magnitude))  # Floor
        
        # Reconstruct audio
        stft_denoised = magnitude * np.exp(1j * phase)
        audio_denoised = librosa.istft(stft_denoised)
        
        return audio_denoised
    except Exception as e:
        ml_logger.error(f"Error applying noise reduction: {str(e)}")
        return audio

# Function to resample audio to a new sample rate
def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int = None) -> np.ndarray:
    """
    Resample audio to target sample rate
    
    Args:
        audio: Audio data
        orig_sr: Original sample rate
        target_sr: Target sample rate (default: use settings)
        
    Returns:
        Resampled audio data
    """
    try:
        if target_sr is None:
            target_sr = settings.SAMPLE_RATE
        
        if orig_sr == target_sr:
            return audio
        
        return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
    except Exception as e:
        ml_logger.error(f"Error resampling audio: {str(e)}")
        return audio

# Function to concatenate multiple audio segments
def concatenate_audio(audio_segments: List[np.ndarray]) -> np.ndarray:
    """
    Concatenate multiple audio segments
    
    Args:
        audio_segments: List of audio segments
        
    Returns:
        Concatenated audio
    """
    try:
        if not audio_segments:
            return np.array([])
        
        return np.concatenate(audio_segments)
    except Exception as e:
        ml_logger.error(f"Error concatenating audio: {str(e)}")
        return np.array([])

# Function to compute RMS amplitude of audio
def compute_rms(audio: np.ndarray) -> float:
    """
    Compute Root Mean Square (RMS) amplitude of audio
    """
    if len(audio) == 0:
        return 0.0
    return np.sqrt(np.mean(audio**2))