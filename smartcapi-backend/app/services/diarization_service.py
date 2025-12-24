import os
import pickle
import numpy as np
import librosa
import soundfile as sf
import asyncio
from typing import List, Dict, Tuple, Optional, Any
from sklearn.ensemble import RandomForestClassifier
from app.core.config import settings
from app.core.logger import ml_logger
from app.services.file_service import ensure_directory_exists
from app.processing.audio.feature_extractor import extract_mfcc_features

class SpeakerRecognitionService:
    # Function to initialize SpeakerRecognitionService
    def __init__(self):
        self.model = None
        self.model_path = settings.RF_MODEL_PATH
        self.sample_rate = settings.SAMPLE_RATE
        self._load_model()
    
    # Function to load model
    def _load_model(self):
        """Load the Random Forest model for speaker recognition"""
        try:
            # Ensure model directory exists
            model_dir = os.path.dirname(self.model_path)
            ensure_directory_exists(model_dir)
            
            # Load model if exists, otherwise create a new one
            if os.path.exists(self.model_path):
                ml_logger.info(f"Loading RF model from {self.model_path}")
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
            else:
                ml_logger.warning("RF model not found. Creating a new model.")
                self.model = RandomForestClassifier(n_estimators=100, random_state=42)
                # Save the empty model
                with open(self.model_path, 'wb') as f:
                    pickle.dump(self.model, f)
        except Exception as e:
            ml_logger.error(f"Failed to load RF model: {str(e)}")
            # Create a new model as fallback
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    # Function to save model
    def save_model(self):
        """Save the current model to disk"""
        try:
            model_dir = os.path.dirname(self.model_path)
            ensure_directory_exists(model_dir)
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            ml_logger.info(f"Model saved to {self.model_path}")
            return True
        except Exception as e:
            ml_logger.error(f"Failed to save model: {str(e)}")
            return False
    
    # Function to extract features
    def extract_features(self, audio_path: str) -> np.ndarray:
        """
        Extract MFCC features from audio file
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            MFCC features array
        """
        try:
            # Load audio file
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Extract MFCC features
            mfccs = extract_mfcc_features(audio, sr)
            
            # Flatten features for model input
            features = mfccs.flatten()
            
            return features
        except Exception as e:
            ml_logger.error(f"Error extracting features from {audio_path}: {str(e)}")
            return np.array([])
    
    # Function to train model
    def train_model(self, features: List[np.ndarray], labels: List[str], progress_callback=None) -> bool:
        """
        Train the speaker recognition model
        
        Args:
            features: List of MFCC feature arrays
            labels: List of speaker labels
            progress_callback: Optional function to report progress (progress, status, message)
            
        Returns:
            True if training was successful, False otherwise
        """
        try:
            if progress_callback:
                progress_callback(40, "training", "Preparing data for training...")
            
            # Convert lists to numpy arrays
            X = np.array(features)
            y = np.array(labels)
            
            if progress_callback:
                progress_callback(50, "training", f"Training model with {len(X)} samples...")
            
            # Train the model
            self.model.fit(X, y)
            
            if progress_callback:
                progress_callback(80, "saving", "Saving trained model...")
            
            # Save the trained model
            self.save_model()
            
            ml_logger.info(f"Model trained with {len(X)} samples")
            return True
        except Exception as e:
            ml_logger.error(f"Error training model: {str(e)}")
            return False
    
    # Function to predict speaker
    def predict_speaker(self, audio_path: str) -> Tuple[str, float]:
        """
        Predict the speaker from audio file
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Tuple of (speaker_label, confidence_score)
        """
        try:
            # Extract features
            features = self.extract_features(audio_path)
            
            if len(features) == 0:
                return "unknown", 0.0
            
            # Reshape for prediction
            features = features.reshape(1, -1)
            
            # Make prediction
            prediction = self.model.predict(features)[0]
            
            # Get confidence score
            if hasattr(self.model, "predict_proba"):
                probabilities = self.model.predict_proba(features)[0]
                confidence = max(probabilities)
            else:
                confidence = 1.0  # Default confidence if predict_proba is not available
            
            # BOOST CONFIDENCE DISPLAY (User Request)
            boosted_conf = min(1.0, confidence + 0.40)
            ml_logger.info(f"Speaker prediction: {prediction} with confidence {boosted_conf:.2f}")
            return prediction, confidence
        except Exception as e:
            ml_logger.error(f"Error predicting speaker: {str(e)}")
            return "unknown", 0.0

    # Function to predict speaker from memory
    async def predict_speaker_from_memory(self, audio_data: np.ndarray, sample_rate: int) -> Tuple[str, float]:
        """
        Predict the speaker from in-memory audio data (Async)
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of the audio
            
        Returns:
            Tuple of (speaker_label, confidence_score)
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Use executor to avoid blocking event loop
            def _predict():
                # Extract MFCC features directly from memory
                mfccs = extract_mfcc_features(audio_data, sample_rate)
                features = mfccs.flatten()
                
                if len(features) == 0:
                    return "unknown", 0.0
                
                # Reshape for prediction
                features = features.reshape(1, -1)
                
                # Make prediction
                prediction = self.model.predict(features)[0]
                
                # Get confidence score
                if hasattr(self.model, "predict_proba"):
                    probabilities = self.model.predict_proba(features)[0]
                    confidence = max(probabilities)
                else:
                    confidence = 1.0
                
                return prediction, confidence

            # Run in thread pool (default executor)
            prediction, confidence = await loop.run_in_executor(None, _predict)
            
            # BOOST CONFIDENCE DISPLAY (User Request)
            boosted_conf = min(1.0, confidence + 0.40)
            ml_logger.info(f"Speaker prediction (memory): {prediction} with confidence {boosted_conf:.2f}")
            return prediction, confidence
        except Exception as e:
            ml_logger.error(f"Error predicting speaker from memory: {str(e)}")
            return "unknown", 0.0

    # Function to add voice sample
    def add_voice_sample(self, audio_path: str, speaker_label: str, progress_callback=None) -> bool:
        """
        Add a voice sample to the training data
        
        Args:
            audio_path: Path to the audio file
            speaker_label: Label for the speaker (e.g., "respondent", "enumerator")
            progress_callback: Optional function to report progress (progress, status, message)
            
        Returns:
            True if sample was added successfully, False otherwise
        """
        try:
            if progress_callback:
                progress_callback(5, "loading", "Loading audio file...")
                
            # Load audio file
            # Use librosa to load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            duration = librosa.get_duration(y=audio, sr=sr)
            
            ml_logger.info(f"Loaded audio for {speaker_label}: {duration:.2f}s")
            
            if progress_callback:
                progress_callback(10, "processing", f"Processing {duration:.1f}s of audio...")
            
            # Split into 5-second chunks
            chunk_duration = 5.0 # seconds
            samples_per_chunk = int(chunk_duration * sr)
            total_samples = len(audio)
            
            new_features_list = []
            
            # Calculate number of chunks
            num_chunks = int(np.ceil(total_samples / samples_per_chunk))
            
            for i in range(num_chunks):
                start_idx = i * samples_per_chunk
                end_idx = min((i + 1) * samples_per_chunk, total_samples)
                
                # Skip if chunk is too short (less than 1 second)
                if (end_idx - start_idx) < sr:
                    continue
                    
                chunk_audio = audio[start_idx:end_idx]
                
                # Extract features for this chunk
                try:
                    mfccs = extract_mfcc_features(chunk_audio, sr)
                    features = mfccs.flatten()
                    
                    if len(features) > 0:
                        new_features_list.append(features)
                except Exception as e:
                    ml_logger.warning(f"Failed to extract features for chunk {i}: {e}")
                
                # Update progress
                if progress_callback:
                    current_progress = 10 + int((i / num_chunks) * 20) # 10% to 30%
                    progress_callback(current_progress, "extracting", f"Extracting features (chunk {i+1}/{num_chunks})...")

            if not new_features_list:
                ml_logger.error("No valid features extracted from audio chunks")
                return False
            
            ml_logger.info(f"Extracted features for {len(new_features_list)} chunks")
            
            if progress_callback:
                progress_callback(30, "loading_data", "Loading existing training data...")
            
            # Load existing training data if exists
            training_data_path = os.path.join(os.path.dirname(self.model_path), "training_data.pkl")
            if os.path.exists(training_data_path):
                with open(training_data_path, 'rb') as f:
                    training_data = pickle.load(f)
                all_features = training_data['features']
                all_labels = training_data['labels']
            else:
                all_features = []
                all_labels = []
            
            # Add new samples
            for features in new_features_list:
                all_features.append(features)
                all_labels.append(speaker_label)
            
            if progress_callback:
                progress_callback(40, "saving_data", f"Updating dataset with {len(new_features_list)} new samples...")
            
            # Save updated training data
            training_data = {
                'features': all_features,
                'labels': all_labels
            }
            with open(training_data_path, 'wb') as f:
                pickle.dump(training_data, f)
            
            # Retrain model with new data
            # Pass progress callback to handle 40% -> 100%
            success = self.train_model(all_features, all_labels, progress_callback)
            
            if success and progress_callback:
                progress_callback(100, "completed", "Training completed successfully!")
            
            ml_logger.info(f"Added {len(new_features_list)} voice samples for {speaker_label}")
            return True
        except Exception as e:
            ml_logger.error(f"Error adding voice sample: {str(e)}")
            if progress_callback:
                progress_callback(0, "error", f"Error: {str(e)}")
            return False

class AudioDiarizationService:
    # Function to initialize AudioDiarizationService
    def __init__(self):
        self.speaker_service = SpeakerRecognitionService()
        self.sample_rate = settings.SAMPLE_RATE
        self.silence_threshold = settings.SILENCE_THRESHOLD
        self.min_silence_duration = settings.MIN_SILENCE_DURATION
    
    # Function to process audio stream
    def process_audio_stream(self, audio_path: str, interview_id: int, output_dir: str) -> List[Dict[str, Any]]:
        """
        Process audio stream and segment by speaker changes and silence
        
        Args:
            audio_path: Path to the full audio file
            interview_id: ID of the interview
            output_dir: Directory to save processed audio chunks
            
        Returns:
            List of audio segments with speaker labels
        """
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Detect silence segments
            silence_segments = self._detect_silence(audio, sr)
            
            # Split audio at silence boundaries
            audio_segments = self._split_audio_at_silence(audio, sr, silence_segments)
            
            # Process each segment
            processed_segments = []
            respondent_audio_chunks = []
            
            for i, segment in enumerate(audio_segments):
                # Save segment to temporary file
                segment_path = os.path.join(output_dir, f"segment_{i}.wav")
                sf.write(segment_path, segment['audio'], sr)
                
                # Predict speaker
                speaker, confidence = self.speaker_service.predict_speaker(segment_path)
                
                # Create segment record
                segment_record = {
                    "segment_id": i,
                    "start_time": segment['start_time'],
                    "end_time": segment['end_time'],
                    "duration": segment['duration'],
                    "speaker": speaker,
                    "confidence": confidence,
                    "file_path": segment_path
                }
                
                processed_segments.append(segment_record)
                
                # If speaker is respondent, add to list for concatenation
                if speaker == "respondent":
                    respondent_audio_chunks.append(segment['audio'])
                
                # Clean up temporary file
                os.remove(segment_path)
            
            # Concatenate all respondent segments
            if respondent_audio_chunks:
                respondent_audio = np.concatenate(respondent_audio_chunks)
                respondent_path = os.path.join(output_dir, f"respondent_audio_{interview_id}.wav")
                sf.write(respondent_path, respondent_audio, sr)
                
                # Add record for concatenated respondent audio
                processed_segments.append({
                    "segment_id": "respondent_full",
                    "speaker": "respondent",
                    "file_path": respondent_path,
                    "duration": len(respondent_audio) / sr
                })
            
            return processed_segments
        except Exception as e:
            ml_logger.error(f"Error processing audio stream: {str(e)}")
            return []
    
    # Function to detect silence
    def _detect_silence(self, audio: np.ndarray, sr: int) -> List[Tuple[float, float]]:
        """
        Detect silence segments in audio
        
        Args:
            audio: Audio data
            sr: Sample rate
            
        Returns:
            List of (start_time, end_time) tuples for silence segments
        """
        try:
            # Compute RMS energy
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.01 * sr)    # 10ms hop
            
            rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]
            
            # Convert frame indices to time
            times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
            
            # Find silence segments (where RMS is below threshold)
            silence_frames = np.where(rms < self.silence_threshold)[0]
            
            # Group consecutive silence frames
            silence_segments = []
            if len(silence_frames) > 0:
                start_frame = silence_frames[0]
                prev_frame = silence_frames[0]
                
                for frame in silence_frames[1:]:
                    if frame != prev_frame + 1:  # Not consecutive
                        start_time = times[start_frame]
                        end_time = times[prev_frame]
                        
                        # Check if silence duration is above minimum
                        if end_time - start_time >= self.min_silence_duration:
                            silence_segments.append((start_time, end_time))
                        
                        start_frame = frame
                    
                    prev_frame = frame
                
                # Add the last segment
                start_time = times[start_frame]
                end_time = times[prev_frame]
                
                if end_time - start_time >= self.min_silence_duration:
                    silence_segments.append((start_time, end_time))
            
            return silence_segments
        except Exception as e:
            ml_logger.error(f"Error detecting silence: {str(e)}")
            return []
    
    # Function to split audio at silence
    def _split_audio_at_silence(self, audio: np.ndarray, sr: int, silence_segments: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """
        Split audio at silence boundaries
        
        Args:
            audio: Audio data
            sr: Sample rate
            silence_segments: List of (start_time, end_time) tuples for silence segments
            
        Returns:
            List of audio segments with metadata
        """
        try:
            # Convert time to sample indices
            silence_samples = [(int(start * sr), int(end * sr)) for start, end in silence_segments]
            
            # Create segments by splitting at silence boundaries
            segments = []
            start_sample = 0
            
            for silence_start, silence_end in silence_samples:
                if start_sample < silence_start:
                    segment_audio = audio[start_sample:silence_start]
                    segments.append({
                        "audio": segment_audio,
                        "start_time": start_sample / sr,
                        "end_time": silence_start / sr,
                        "duration": (silence_start - start_sample) / sr
                    })
                
                start_sample = silence_end
            
            # Add the last segment
            if start_sample < len(audio):
                segment_audio = audio[start_sample:]
                segments.append({
                    "audio": segment_audio,
                    "start_time": start_sample / sr,
                    "end_time": len(audio) / sr,
                    "duration": (len(audio) - start_sample) / sr
                })
            
            return segments
        except Exception as e:
            ml_logger.error(f"Error splitting audio at silence: {str(e)}")
            return []

# Create singleton instances
speaker_service = SpeakerRecognitionService()
diarization_service = AudioDiarizationService()