"""
Real-time Extraction Service

Orchestrates transcription and extraction for real-time interview processing
"""

import os
import tempfile
import asyncio
import numpy as np
import soundfile as sf
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.db.models import QuestionnaireQuestion, Interview, ExtractedAnswer, InterviewTranscript
from app.services.whisper_service import whisper_service
from app.services.llm_service import llm_service
from app.core.logger import api_logger, ml_logger
import warnings

# Suppress FP16 warning on CPU
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")


class RealtimeExtractionService:
    """
    Orchestrates real-time transcription and answer extraction
    """
    
    # Function to initialize RealtimeExtractionService
    def __init__(self):
        """Initialize real-time extraction service"""
        self.whisper = whisper_service
        self.llm = llm_service
        api_logger.info("RealtimeExtractionService initialized")
    
    # Function to process audio chunks for a question
    async def process_question_audio(
        self,
        audio_chunks: List[bytes],
        question: QuestionnaireQuestion,
        interview_id: int,
        db: Session,
        sample_rate: int = 16000,
        progress_callback = None
    ) -> Dict:
        """
        Process audio chunks for a single question
        
        Args:
            audio_chunks: List of audio data chunks (bytes)
            question: Question being answered
            interview_id: Interview ID
            db: Database session
            sample_rate: Audio sample rate
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict with transcription and extraction results
        """
        try:
            if progress_callback:
                await progress_callback({
                    "type": "processing_started",
                    "question_id": question.id,
                    "question_text": question.question_text
                })
            
            # Step 1: Concatenate audio chunks
            api_logger.info(f"Concatenating {len(audio_chunks)} audio chunks")
            audio_data = self._concatenate_audio_chunks(audio_chunks)
            
            if len(audio_data) == 0:
                raise ValueError("No audio data to process")
            
            # Step 2: Save to temporary file
            duration = len(audio_data) / sample_rate
            api_logger.info(f"Processing audio: {duration:.2f}s")
            
            temp_audio_path = self._save_temp_audio(audio_data, sample_rate)
            
            try:
                # Step 3: Transcribe with Whisper
                if progress_callback:
                    await progress_callback({
                        "type": "transcription_started",
                        "progress": 30
                    })
                
                api_logger.info(f"Transcribing audio for question {question.id} with context prompt.")
                
                # Context Injection: Tell Whisper what the question was!
                # This drastically improves accuracy for short answers like "Dua" vs "Tua"
                context_prompt = f"Pertanyaan: {question.question_text}. Jawaban responden adalah:"
                
                transcription_result = await self.whisper.transcribe(
                    audio_path=temp_audio_path,
                    initial_prompt=context_prompt
                )
                transcript = transcription_result.get("text", "").strip()
                
                if not transcript:
                    # Instead of raising an error, just return a "no speech" result
                    # This prevents the frontend from showing an error popup for silence/noise
                    api_logger.info("Empty transcription result (likely silence or noise)")
                    return {
                        "success": False,
                        "error": "No speech detected",
                        "is_silence": True,  # Flag to indicate this isn't a system error
                        "question_id": question.id
                    }
                
                api_logger.info(f"Transcription: {transcript[:100]}...")
                
                if progress_callback:
                    await progress_callback({
                        "type": "transcription_completed",
                        "transcript": transcript,
                        "progress": 60
                    })
                
                # Step 3b: Grammar Correction (Optional but recommended)
                if progress_callback:
                    await progress_callback({
                        "type": "grammar_correction_started",
                        "progress": 65
                    })
                
                # Run grammar correction in executor
                loop = asyncio.get_event_loop()
                transcript = await loop.run_in_executor(None, lambda: self.llm.correct_grammar(transcript))
                
                api_logger.info(f"Corrected Transcript: {transcript[:100]}...")

                # Step 4: Extract answer with LLM
                if progress_callback:
                    await progress_callback({
                        "type": "extraction_started",
                        "progress": 70
                    })
                
                api_logger.info(f"Extracting answer for question {question.id}")
                extraction_result = await self._extract_answer_with_llm(
                    transcript=transcript,
                    question=question
                )
                
                extracted_answer = extraction_result.get("answer")
                confidence = extraction_result.get("confidence", 0.0)
                
                # SANITIZATION: If LLM rejected the answer (null) or confidence is low,
                # it likely means the transcript was hallucination/noise.
                # We should NOT show the user "Menteri kakang-kakang" etc.
                if not extracted_answer or confidence < 0.2:
                     api_logger.warning("Low confidence extraction, sanitizing transcript.")
                     # Original transcript is still useful for debugging logs above, but for DB we sanitize.
                     transcript = "[Suara tidak jelas / Noise]"
                     extracted_answer = "" # Default to empty string
                     confidence = 0.0
                else:
                    api_logger.info(f"Extracted answer: {extracted_answer[:100]}...")
                
                # Step 5: Save to database
                if progress_callback:
                    await progress_callback({
                        "type": "saving_to_database",
                        "progress": 90
                    })
                
                self._save_extracted_answer(
                    db=db,
                    interview_id=interview_id,
                    question=question,
                    transcript=transcript,
                    answer=extracted_answer,
                    confidence=confidence
                )
                
                # Step 6: Return result
                result = {
                    "success": True,
                    "question_id": question.id,
                    "question_text": question.question_text,
                    "variable_name": question.variable_name,  # Added for frontend mapping
                    "transcript": transcript,
                    "extracted_answer": extracted_answer,
                    "confidence": confidence
                }
                
                if progress_callback:
                    await progress_callback({
                        "type": "answer_extracted",
                        "progress": 100,
                        **result
                    })
                
                return result
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                    
        except Exception as e:
            api_logger.error(f"Error processing question audio: {str(e)}")
            
            error_result = {
                "success": False,
                "error": str(e),
                "question_id": question.id if question else None
            }
            
            if progress_callback:
                await progress_callback({
                    "type": "error",
                    "message": str(e),
                    **error_result
                })
            
            return error_result
    
    # Function to concatenate audio chunks
    def _concatenate_audio_chunks(self, audio_chunks: List[bytes]) -> np.ndarray:
        """
        Concatenate audio chunks into single array
        
        Args:
            audio_chunks: List of audio bytes
            
        Returns:
            Concatenated audio as numpy array
        """
        try:
            audio_arrays = []
            
            for chunk in audio_chunks:
                # Convert bytes to numpy array
                audio_array = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
                # Normalize to [-1, 1]
                audio_array = audio_array / 32768.0
                audio_arrays.append(audio_array)
            
            # Concatenate all arrays
            if audio_arrays:
                return np.concatenate(audio_arrays)
            else:
                return np.array([])
                
        except Exception as e:
            ml_logger.error(f"Error concatenating audio chunks: {str(e)}")
            return np.array([])
    
    # Function to save temporary audio file
    def _save_temp_audio(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """
        Save audio to temporary file
        
        Args:
            audio_data: Audio numpy array
            sample_rate: Sample rate
            
        Returns:
            Path to temporary file
        """
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=".wav",
                dir=tempfile.gettempdir()
            )
            temp_path = temp_file.name
            temp_file.close()
            
            # Save audio
            sf.write(temp_path, audio_data, sample_rate)
            
            return temp_path
            
        except Exception as e:
            ml_logger.error(f"Error saving temporary audio: {str(e)}")
            raise
    
    # Function to extract answer with LLM
    async def _extract_answer_with_llm(
        self,
        transcript: str,
        question: QuestionnaireQuestion
    ) -> Dict:
        """
        Extract answer from transcript using LLM
        
        Args:
            transcript: Transcribed text
            question: Question being answered
            
        Returns:
            Dict with extracted answer and confidence
        """
        try:
            # Keyword mapping for context enhancement
            KEYWORDS_MAPPING = {
                "nama": ["nama saya", "panggil saja", "nama lengkap", "saya adalah"],
                "tempat_lahir": ["lahir di", "asal dari", "kelahiran", "tempat lahir"],
                "tanggal_lahir": ["tanggal", "bulan", "tahun", "lahir pada"],
                "usia": ["umur saya", "usia saya", "tahun ini umur"],
                "pendidikan": ["lulusan", "sekolah di", "kuliah di", "tamat", "pendidikan terakhir"],
                "alamat": ["tinggal di", "alamat saya", "rumah saya", "domisili"],
                "pekerjaan": ["bekerja sebagai", "pekerjaan saya", "saya seorang", "sehari-hari"],
                "hobi": ["hobi saya", "suka melakukan", "kegemaran", "waktu luang"],
                "nomor_telepon": ["nomor hp", "nomor telepon", "bisa dihubungi di", "whatsapp"],
                "alamat_email": ["email saya", "alamat email", "surel"]
            }

            # Get keywords for current variable
            keywords = KEYWORDS_MAPPING.get(question.variable_name, [])
            keywords_str = ", ".join(f'"{k}"' for k in keywords)

            # Specific rules per variable
            specific_rule = ""
            if question.variable_name == "nama":
                specific_rule = "5. KHUSUS VARIABEL 'nama': Jawaban HARUS berupa nama orang. TOLAK jika berisi angka (2, 3, dll) atau kata asing aneh."
            elif question.variable_name == "usia":
                specific_rule = "5. KHUSUS VARIABEL 'usia': Jawaban HARUS berupa angka atau estimasi umur yang masuk akal."
            
            # Create prompt for LLM with Enhanced Few-Shot and Strict Noise Filtering
            prompt = f"""Anda adalah asisten ekstraksi data cerdas untuk wawancara personal (SmartCAPI).
Tugas Anda adalah mengekstrak jawaban yang TEPAT, AKURAT, dan RELEVAN dari transkrip audio berdasarkan pertanyaan spesifik yang diajukan.

ATURAN KRUSIAL (STRICT):
1. HANYA ekstrak jika transkrip berisi jawaban yang RELEVAN dengan "Pertanyaan".
2. Jika transkrip berisi omong kosong, suara tidak jelas, teks bahasa asing aneh (misal: "además", "jeszcze"), atau potongan kalimat yang tidak menjawab pertanyaan -> KEMBALIKAN "answer": null.
3. JANGAN MENGARANG JAWABAN. Jika tidak yakin, kembalikan null.
4. PERHATIKAN KOREKSI: Jika responden meralat (misal: "A, eh bukan, B"), ambil jawaban TERAKHIR (B).
{specific_rule}

### CONTOH FEW-SHOT (Contextual Learning) ###

Contoh 1 (Jawaban Jelas):
Pertanyaan: "Siapa nama lengkap Anda?" (Variabel: nama)
Transkrip: "Nama saya Budi Santoso."
Jawaban: {{"answer": "Budi Santoso", "confidence": 1.0, "reason": "Menyebutkan nama lengkap jelas"}}

Contoh 2 (Noise/Hallucination -> REJECT):
Pertanyaan: "Siapa nama lengkap Anda?" (Variabel: nama)
Transkrip: "además kan saya... video stuti" 
Jawaban: {{"answer": null, "confidence": 0.0, "reason": "Teks tidak masuk akal/bukan bahasa Indonesia yang benar"}}

Contoh 3 (Salah Konteks -> REJECT):
Pertanyaan: "Berapa usia Anda?" (Variabel: usia)
Transkrip: "Saya tinggal di Jakarta Selatan."
Jawaban: {{"answer": null, "confidence": 0.0, "reason": "Jawaban tidak nyambung dengan pertanyaan usia"}}

Contoh 4 (Jawaban Pendek Valid):
Pertanyaan: "Apakah Anda bekerja?" (Variabel: status_kerja)
Transkrip: "Tidak."
Jawaban: {{"answer": "Tidak", "confidence": 0.95, "reason": "Jawaban langsung"}}

Contoh 5 (Potongan Kalimat/Gumam -> REJECT):
Pertanyaan: "Apa pekerjaan Anda?" (Variabel: pekerjaan)
Transkrip: "...anu... hmm..."
Jawaban: {{"answer": null, "confidence": 0.0, "reason": "Hanya gumaman"}}

---

### TUGAS EKSTRAKSI ###

Informasi Target:
- Pertanyaan: "{question.question_text}"
- Tipe Data: {question.data_type}
- Variabel: {question.variable_name}

Transkrip Audio:
"{transcript}"

Instruksi Output:
Ekstrak jawaban dalam format JSON valid. 
JIKA TIDAK ADA JAWABAN RELEVAN, ISI "answer" DENGAN null (tanpa tanda kutip).

Format JSON:
{{
    "answer": "...",
    "confidence": 0.0-1.0,
    "reason": "..."
}}
"""
            
            # Call LLM service (Synchronous)
            # Use run_in_executor to avoid blocking the event loop for too long
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.llm.extract_information(
                    transcript=transcript,
                    prompt=prompt
                )
            )
            
            # Parse result
            # The LLM returns a dict with "answer", "confidence", "reason"
            answer = result.get("answer")
            if answer:
                answer = str(answer).strip()
            
            confidence = result.get("confidence", 0.8)  # Default confidence
            
            return {
                "answer": answer,
                "confidence": confidence
            }
            
        except Exception as e:
            api_logger.error(f"Error extracting answer with LLM: {str(e)}")
            return {
                "answer": transcript,  # Fallback to full transcript
                "confidence": 0.5
            }
    
    # Function to save extracted answer to database
    def _save_extracted_answer(
        self,
        db: Session,
        interview_id: int,
        question: QuestionnaireQuestion,
        transcript: str,
        answer: str,
        confidence: float
    ):
        """
        Save extracted answer to database and update transcript
        
        Args:
            db: Database session
            interview_id: Interview ID
            question: Question object
            transcript: Full transcript
            answer: Extracted answer
            confidence: Confidence score
        """
        try:
            # 1. Save ExtractedAnswer
            existing = db.query(ExtractedAnswer).filter(
                ExtractedAnswer.interview_id == interview_id,
                ExtractedAnswer.question_id == question.id
            ).first()
            
            if existing:
                # Update existing answer
                existing.answer_text = answer
                existing.confidence_score = confidence
                api_logger.info(f"Updated existing answer for question {question.id}")
            else:
                # Create new answer
                extracted_answer = ExtractedAnswer(
                    interview_id=interview_id,
                    question_id=question.id,
                    answer_text=answer,
                    confidence_score=confidence
                )
                db.add(extracted_answer)
                api_logger.info(f"Created new answer for question {question.id}")
            
            # SYNC RESPONDENT NAME IF VARIABLE IS 'nama'
            if question.variable_name == "nama" and answer:
                 # Fetch interview to get respondent
                 interview = db.query(Interview).filter(Interview.id == interview_id).first()
                 if interview and interview.respondent:
                     interview.respondent.full_name = answer
                     db.add(interview.respondent)
                     api_logger.info(f"Auto-updated Respondent Name to '{answer}' from Realtime Service")

            # 2. Update InterviewTranscript
            transcript_entry = db.query(InterviewTranscript).filter(
                InterviewTranscript.interview_id == interview_id
            ).first()
            
            # Format: "Q: [Question Text]\nA: [Transcript] (Extracted: [Answer])\n\n"
            formatted_entry = f"Q: {question.question_text}\nA: {transcript}\n(Extracted: {answer})\n\n"
            
            if transcript_entry:
                if transcript_entry.cleaned_transcript:
                    transcript_entry.cleaned_transcript += formatted_entry
                else:
                    transcript_entry.cleaned_transcript = formatted_entry
                
                # Also update raw if needed, or keep them in sync
                if transcript_entry.raw_transcript:
                    transcript_entry.raw_transcript += formatted_entry
                else:
                    transcript_entry.raw_transcript = formatted_entry
                    
                api_logger.info(f"Appended to existing transcript for interview {interview_id}")
            else:
                transcript_entry = InterviewTranscript(
                    interview_id=interview_id,
                    raw_transcript=formatted_entry,
                    cleaned_transcript=formatted_entry,
                    summary=""
                )
                db.add(transcript_entry)
                api_logger.info(f"Created new transcript for interview {interview_id}")
            
            db.commit()
            
        except Exception as e:
            api_logger.error(f"Error saving extracted answer: {str(e)}")
            db.rollback()
            raise


# Singleton instance
realtime_extraction_service = RealtimeExtractionService()
