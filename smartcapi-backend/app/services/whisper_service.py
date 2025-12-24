import os
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.logger import ml_logger

class WhisperService:
    # Function to initialize WhisperService
    def __init__(self):
        # Initialize Async OpenAI Client
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        ml_logger.info("Layanan Whisper diaktifkan")

    # Function to transcribe audio
    async def transcribe(self, audio_path: str, language: Optional[str] = None, initial_prompt: Optional[str] = None) -> dict:
        """
        Transcribe audio file using OpenAI Whisper
        
        Args:
            audio_path: Path to the audio file
            language: Optional language code (e.g., 'id' for Indonesian)
            initial_prompt: Optional context prompt to guide Whisper
            
        Returns:
            Dictionary containing transcription results (text, segments, etc.)
        """
        try:
            ml_logger.info(f"Mentranskripsikan ucapan: {audio_path}")
            
            # Use provided prompt or fallback
            prompt_to_use = initial_prompt or "Survei Uji Coba SmartCAPI"
            
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            with open(audio_path, "rb") as audio_file:
                # Call OpenAI Whisper API with verbose_json to get segments
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="id", # Force ID for consistency
                    prompt=prompt_to_use,
                    response_format="verbose_json"
                )

            # Extract data
            text = transcript.text.strip()
            # OpenAI v1 segments are objects with attributes (text, start, end)
            segments = transcript.segments 
            detected_language = transcript.language
            
            result = {
                "text": text,
                "segments": segments,
                "language": detected_language,
                "language_probability": 1.0 # API doesn't return prob in usually the same way, assume high confidence
            }
            
            # LANGUAGE FILTER (Optional logic from previous version)
            # OpenAI API 'language' parameter forces the language, so detected_language should be 'id'.
            # But if it auto-detects something else despite hint (rare), we can check.
            if detected_language and detected_language not in ["en", "id", "indonesian"]:
                 # 'indonesian' acts as 'id' sometimes in full names
                 pass

            # HALLUCINATION FILTER removed per user request
            # We pass the raw text and segments directly.
            
            valid_segments = segments
            filtered_text = text
            
            result["text"] = filtered_text
            result["segments"] = valid_segments
            
            if not filtered_text:
                ml_logger.info("Transcription result empty after filtering.")
            else:
                safe_text = filtered_text[:100].encode('ascii', 'ignore').decode('ascii')
                ml_logger.info(f"Transcription completed (OpenAI): {safe_text}...")
                
            return result

        except Exception as e:
            ml_logger.error(f"Error transcribing with OpenAI API: {str(e)}")
            return {"text": "", "language": None, "error": str(e)}

# Create a singleton instance
whisper_service = WhisperService()