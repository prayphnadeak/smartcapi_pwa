import numpy as np
import librosa
from typing import Optional
from app.core.logger import ml_logger

# Fungsi untuk mengekstrak 33 MFCC dari file wav audio
# Function to extract MFCC features from audio
def extract_mfcc_features(audio: np.ndarray, sr: int, n_mfcc: int = 33) -> np.ndarray:
    """
    Extract MFCC features from audio
    
    Args:
        audio: Audio data
        sr: Sample rate
        n_mfcc: Number of MFCC coefficients to extract
        
    Returns:
        MFCC features array
    """
    try:
        # Extract MFCC features
        mfccs = librosa.feature.mfcc(
            y=audio, 
            sr=sr, 
            n_mfcc=n_mfcc,
            n_fft=2048,
            hop_length=512,
            win_length=None,
            window='hann',
            center=True,
            pad_mode='constant'
        )
        
        # Apply delta and delta-delta features
        delta_mfccs = librosa.feature.delta(mfccs)
        delta2_mfccs = librosa.feature.delta(mfccs, order=2)
        
        # Combine features
        combined_features = np.vstack([mfccs, delta_mfccs, delta2_mfccs])
        
        # Compute mean and standard deviation
        mean_features = np.mean(combined_features, axis=1)
        std_features = np.std(combined_features, axis=1)
        
        # Concatenate mean and std
        final_features = np.concatenate([mean_features, std_features])
        
        return final_features
    except Exception as e:
        ml_logger.error(f"Error extracting MFCC features: {str(e)}")
        return np.array([])

# Function to extract mean of 33 MFCC features
def extract_33_mfcc_means(audio: np.ndarray, sr: int, n_mfcc: int = 33) -> np.ndarray:
    """
    Extract mean of 33 MFCC features from audio
    
    Args:
        audio: Audio data
        sr: Sample rate
        n_mfcc: Number of MFCC coefficients to extract
        
    Returns:
        Array of 33 MFCC mean values
    """
    try:
        # Extract MFCC features
        mfccs = librosa.feature.mfcc(
            y=audio, 
            sr=sr, 
            n_mfcc=n_mfcc,
            n_fft=2048,
            hop_length=512,
            window='hann',
            center=True,
            pad_mode='constant'
        )
        
        # Compute mean only
        mean_features = np.mean(mfccs, axis=1)
        
        return mean_features
    except Exception as e:
        ml_logger.error(f"Error extracting 33 MFCC means: {str(e)}")
        return np.array([])

# Function to extract spectral features from audio
def extract_spectral_features(audio: np.ndarray, sr: int) -> np.ndarray:
    """
    Extract spectral features from audio
    
    Args:
        audio: Audio data
        sr: Sample rate
        
    Returns:
        Spectral features array
    """
    try:
        # Compute spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(audio)
        
        # Compute mean and standard deviation
        features = []
        for feature in [spectral_centroids, spectral_rolloff, spectral_bandwidth, zero_crossing_rate]:
            features.append(np.mean(feature))
            features.append(np.std(feature))
        
        return np.array(features)
    except Exception as e:
        ml_logger.error(f"Error extracting spectral features: {str(e)}")
        return np.array([])

# Function to extract chroma features from audio
def extract_chroma_features(audio: np.ndarray, sr: int) -> np.ndarray:
    """
    Extract chroma features from audio
    
    Args:
        audio: Audio data
        sr: Sample rate
        
    Returns:
        Chroma features array
    """
    try:
        # Compute chroma features
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
        
        # Compute mean and standard deviation
        chroma_mean = np.mean(chroma, axis=1)
        chroma_std = np.std(chroma, axis=1)
        
        # Concatenate mean and std
        chroma_features = np.concatenate([chroma_mean, chroma_std])
        
        return chroma_features
    except Exception as e:
        ml_logger.error(f"Error extracting chroma features: {str(e)}")
        return np.array([])

# Function to extract all available features from audio
def extract_all_features(audio: np.ndarray, sr: int) -> np.ndarray:
    """
    Extract all features from audio
    
    Args:
        audio: Audio data
        sr: Sample rate
        
    Returns:
        Combined features array
    """
    try:
        # Extract all features
        mfcc_features = extract_mfcc_features(audio, sr)
        spectral_features = extract_spectral_features(audio, sr)
        chroma_features = extract_chroma_features(audio, sr)
        
        # Combine all features
        all_features = np.concatenate([mfcc_features, spectral_features, chroma_features])
        
        return all_features
    except Exception as e:
        ml_logger.error(f"Error extracting all features: {str(e)}")
        return np.array([])