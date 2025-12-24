import asyncio
import json
import traceback
import datetime
import re
import logging
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.core.logger import ml_logger
from app.core.redis_client import async_redis_client, RedisQueue, RedisChannel
from app.services.llm_service import llm_service
from app.services.question_manager import QuestionManager
from app.db.models import QuestionnaireQuestion, ExtractedAnswer, InterviewTranscript

# Reusing logic from realtime_extraction.py (modified for worker)
import re

# =========================================================
# 🛡️ SEMANTIC GUARDS CONFIGURATION
# =========================================================

FIELD_GUARDS = {
    "nama": "guard_nama",             # Adjusted key from "nama_lengkap" to "nama" based on DB schema usually
    "nama_lengkap": "guard_nama",     # Alias
    "tempat_lahir": "guard_tempat",
    "tanggal_lahir": "guard_tanggal",
    "usia": "guard_usia",
    "pendidikan": "guard_pendidikan",
    "alamat": "guard_alamat",
    "pekerjaan": "guard_pekerjaan",
    "hobi": "guard_hobi",
    "nomor_telepon": "guard_telepon",
    "email": "guard_email",
    "alamat_email": "guard_email"     # Alias
}

# --- GUARD FUNCTIONS ---

def guard_tanggal(value: str) -> bool:
    """
    Validasi tanggal dengan toleransi format
    """
    if not value or not isinstance(value, str):
        return False
    
    # Format yang diterima: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
    patterns = [
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'\d{1,2}-\d{1,2}-\d{4}',
        r'\d{4}-\d{1,2}-\d{1,2}'
    ]
    
    for pattern in patterns:
        if re.match(pattern, value):
            try:
                # Coba parse untuk validasi
                if '/' in value:
                    datetime.datetime.strptime(value, '%d/%m/%Y')
                elif value.count('-') == 2:
                    if len(value.split('-')[0]) == 4:
                        datetime.datetime.strptime(value, '%Y-%m-%d')
                    else:
                        datetime.datetime.strptime(value, '%d-%m-%Y')
                return True
            except:
                return False
    
    return False


def guard_usia(value: Any) -> bool:
    """Validasi usia (lebih toleran)"""
    try:
        age = int(value) if isinstance(value, str) else value
        return 0 <= age <= 120
    except:
        return False

def guard_telepon(value: str) -> bool:
    """Validasi nomor telepon Indonesia"""
    if not value or not isinstance(value, str):
        return False
    
    # Hapus karakter non-digit
    digits = re.sub(r'\D', '', value)
    
    # Format Indonesia: 08xx, 628xx, +628xx (10-13 digit)
    # Relaxed: Allow slightly shorter for user input error (9-14)
    return len(digits) >= 9 and len(digits) <= 14 and digits.startswith(('08', '628', '8'))

def guard_email(value: str) -> bool:
    """Validasi email"""
    if not value or not isinstance(value, str):
        return False
    
    # Skip jika "-" atau "tidak ada"
    if value.strip() in ['-', 'tidak ada', 'tidak', '']:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, value))

# Keep other guards? User provided guards for specific fields but left others out in prompt (guard_nama, etc.)
# "masukkan dan sesuaikan script di atas"
# The prompt implies replacing/updating. I should keep `guard_nama` etc if not replaced.
# The user snippet provided: `guard_tanggal`, `guard_usia`, `guard_nomor_telepon`, `guard_email`.
# I will KEEP the others (nama, tempat, pendidikan, alamat, pekerjaan, hobi) from previous implementation.

# ... (Previous implementation of other guards) ...
def guard_nama(value: str) -> bool:
    blacklist = {"uji", "tes", "test", "mic", "halo", "oke", "ok"}
    tokens = value.lower().split()
    if any(t in blacklist for t in tokens): return False
    if len(tokens) > 4: return False 
    return value.istitle() 

def guard_tempat(value: str) -> bool:
    if len(value.split()) > 3: return False
    blacklist = ["tidur", "rumah", "kerja", "kantor"]
    return not any(b in value.lower() for b in blacklist)

def guard_pendidikan(value: str) -> bool:
    valid = {
        "sd", "smp", "sma",
        "d3", "diploma",
        "s1", "sarjana",
        "s2", "magister",
        "s3", "doktor",
        "tidak sekolah",
        "sm", "stm", "smk", "madrasah"
    }
    val = value.lower().strip()
    # Direct match
    if val in valid: return True
    # Substring match (e.g. "tamat SD")
    if any(v in val for v in valid): return True
    return False

def guard_alamat(value: str) -> bool:
    blacklist = {"tidur", "makan", "berenang", "jalan", "kerja", "hobi", "sehari-hari"}
    # Relaxed to 2 words min, but check if it contains at least one alphabetic char
    if len(value.split()) < 2: return False 
    if not any(c.isalpha() for c in value): return False
    return not any(b in value.lower() for b in blacklist)

def guard_pekerjaan(value: str) -> bool:
    blacklist = {"berenang", "jalan", "tidur", "makan", "nonton"}
    if value.lower() in blacklist: return False
    return len(value.split()) <= 30 # Relaxed to 30 words per user request

def guard_hobi(value: str) -> bool:
    blacklist = {"kantor", "kerja", "pabrik"}
    return value.lower() not in blacklist

# NOTE: `guard_telepon` renamed to match `FIELD_GUARDS` key 'guard_telepon' in previous, 
# but user provided `guard_nomor_telepon`. I should align mapping.
# User code: `guard_nomor_telepon`. My mapping uses `guard_telepon`.
# I will use `guard_telepon` name for the function implementation to match existing mapping.


# =========================================================

class LLMWorker:
    """Worker untuk ekstraksi data dengan LLM"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.question_manager = QuestionManager(self.db)
        self.llm = llm_service
        self.logger = logging.getLogger('ml')
        # Konfigurasi logger untuk menghindari emoji di Windows
        self._configure_logger()
        
        # Initialize guards mapping
        # We need to map field names (from schema) to actual function objects
        # The FIELD_GUARDS dictionary (global) maps 'nama' -> 'guard_nama' (string)
        # We need to resolve these strings to the functions we just defined
        self.guards = {}
        for field, func_name in FIELD_GUARDS.items():
            if func_name in globals():
                self.guards[field] = globals()[func_name]

    def _configure_logger(self):
        """Konfigurasi logger dengan encoding UTF-8"""
        for handler in self.logger.handlers:
            if hasattr(handler, 'stream'):
                try:
                    handler.stream.reconfigure(encoding='utf-8')
                except:
                    pass

    def semantic_filter(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter semantik yang lebih toleran dengan auto-correction
        """
        filtered = {}
        
        for field, value in extracted_data.items():
            if value is None or value == "" or value == []:
                continue
            
            # Normalize field name
            field_lower = field.lower()
            
            # Skip jika field tidak ada guard
            if field_lower not in self.guards:
                filtered[field] = value
                continue
            
            guard_func = self.guards[field_lower]
            guard_name = FIELD_GUARDS.get(field_lower, "unknown_guard")
            
            try:
                # Coba validasi dengan guard
                if guard_func(str(value)):
                    filtered[field] = value
                else:
                    # PERBAIKAN: Coba auto-correct untuk tanggal
                    if field_lower == 'tanggal_lahir':
                        corrected = self._auto_correct_date(str(value))
                        if corrected and guard_func(corrected):
                            self.logger.info(f"[AUTO-CORRECT] Field '{field}': '{value}' -> '{corrected}'")
                            filtered[field] = corrected
                        else:
                            self.logger.warning(f"[GUARD-BLOCKED] Field '{field}' Value '{value}' rejected by {guard_name}")
                    else:
                        self.logger.warning(f"[GUARD-BLOCKED] Field '{field}' Value '{value}' rejected by {guard_name}")
                        
            except Exception as e:
                self.logger.error(f"Guard error for {field}: {e}")
                continue
        
        return filtered

    def _auto_correct_date(self, date_str: str) -> str:
        """
        Auto-correct untuk format tanggal yang salah
        Contoh: '18/XX/2025' -> '18/01/1963' (dari konteks)
        """
        if not date_str:
            return None
        
        # Pattern: DD/XX/YYYY atau DD/MM/YYYY yang salah tahun
        match = re.match(r'(\d{1,2})/([A-Z]{2}|\d{1,2})/(\d{4})', date_str)
        if not match:
            return None
        
        day, month, year = match.groups()
        
        # Fix month jika XX atau invalid
        if month == 'XX' or not month.isdigit():
            month = '01'  # Default ke Januari
        
        # Fix year jika terlalu baru (birth year > 2010 tidak masuk akal untuk survey)
        if year.isdigit() and int(year) > 2010:
            # Ekstrak 2 digit terakhir dan asumsikan abad ke-20
            year = '19' + year[-2:]
        
        corrected = f"{day}/{month}/{year}"
        
        # Validasi final
        try:
            datetime.datetime.strptime(corrected, '%d/%m/%Y')
            return corrected
        except:
            return None

    def _save_result(self, interview_id: int, question_obj, transcript: str, 
                     value: Any, confidence: float = 1.0):
        """
        Simpan hasil ekstraksi dengan konversi tipe data yang benar
        """
        try:
            # We already passed the question object, no need to query by name again 
            # (Original user code queried by name, but we have the ID/Object from map)
            
            # PERBAIKAN: Konversi list menjadi JSON string untuk SQLite
            if isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            
            # Konversi tipe data lain jika perlu
            if isinstance(value, (dict, tuple)):
                value = json.dumps(value, ensure_ascii=False)
            
            # Pastikan value adalah string, int, float, atau None
            if not isinstance(value, (str, int, float, type(None))):
                value = str(value)
            
            # Use Question.id directly
            existing = self.db.query(ExtractedAnswer).filter(
                ExtractedAnswer.interview_id == interview_id,
                ExtractedAnswer.question_id == question_obj.id
            ).first()
            
            if existing:
                existing.answer_text = value
                existing.transcript = transcript
                existing.confidence_score = confidence
                existing.updated_at = datetime.datetime.utcnow()
                self.logger.info(f" -> Updated '{question_obj.variable_name}': '{value}'")
            else:
                new_answer = ExtractedAnswer(
                    interview_id=interview_id,
                    question_id=question_obj.id,
                    answer_text=value,
                    transcript=transcript,
                    confidence_score=confidence
                )
                self.db.add(new_answer)
                self.logger.info(f" -> Found '{question_obj.variable_name}': '{value}'")
            
            self.db.commit()
            
            # Update nama responden jika ada
            if question_obj.variable_name == 'nama':
                self._update_respondent_name(interview_id, value)
                
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to save {question_obj.variable_name}: {e}")
            raise e

    def _update_respondent_name(self, interview_id: int, name: str):
        """Update nama responden di tabel Interview"""
        try:
            from app.db.models import Interview # Import here to avoid circular
            interview = self.db.query(Interview).filter(
                Interview.id == interview_id
            ).first()
            
            if interview and interview.respondent:
                current_name = interview.respondent.full_name or ""
                
                # Heuristic: Priority to longer names
                if len(name) > len(current_name) or not current_name:
                    interview.respondent.full_name = name
                    self.db.commit()
                    self.logger.info(f"Auto-updated Respondent Name to '{name}' from LLM extraction")
                    
        except Exception as e:
            self.logger.error(f"Failed to update respondent name: {e}")
            self.db.rollback()

    async def process_extraction(self, data: Dict):
        """
        Proses ekstraksi dengan error handling yang lebih baik
        """
        try:
            interview_id = data.get('interview_id')
            transcript = data.get('text')
            
            if not interview_id or not transcript:
                return

            self.logger.info(f"Processing Opportunistic LLM extraction for interview {interview_id}")
            
            # 1. Fetch Target Schema
            # Reusing existing logic to fetch active questions
            all_questions = self.db.query(QuestionnaireQuestion).filter(
                QuestionnaireQuestion.is_active == True
            ).all()
            
            if not all_questions:
                self.logger.warning("No active questions found in DB.")
                return

            question_map = {q.variable_name.lower(): q for q in all_questions if q.variable_name}
            target_schema_list = list(question_map.keys())

            self.logger.info(f"Target Schema: {target_schema_list}")
            
            # Helper to resolve LLM keys to DB keys
            def resolve_db_key(llm_key, db_map):
                if not llm_key: return None
                k = llm_key.lower().strip()
                
                # Direct match
                if k in db_map: return k
                
                # Common aliases (LLM output -> DB Variable)
                aliases = {
                    'nama_lengkap': 'nama',
                    'fullname': 'nama',
                    'pendidikan': 'pendidikan', # Assuming DB might be 'pendidikan' or 'pendidikan_terakhir'
                    'pendidikan_terakhir': 'pendidikan', 
                    'pekerjaan_utama': 'pekerjaan',
                    'alamat_lengkap': 'alamat',
                    'no_hp': 'nomor_telepon',
                    'nomor_hp': 'nomor_telepon',
                    'phone': 'nomor_telepon',
                    'email': 'alamat_email',
                    'hobi_kesukaan': 'hobi'
                }
                
                # Try alias
                if k in aliases:
                    alias = aliases[k]
                    if alias in db_map: return alias
                    
                # Try reverse check: is 'k' a part of any db key?
                # e.g. llm 'pendidikan' -> db 'pendidikan_terakhir'
                for db_k in db_map:
                    if k in db_k or db_k in k:
                        # Safety check: don't match 'nama' to 'alamat' etc.
                        if db_k[0] == k[0]: 
                            return db_k
                            
                return None
            
            # 2. Extract
            # Call loop runner
            loop = asyncio.get_event_loop()
            extracted_data = await loop.run_in_executor(
                None, 
                lambda: self.llm.extract_information(transcript, schema=target_schema_list)
            )
            
            self.logger.info(f"Opportunistic Extraction Result: {extracted_data}")
            
            # 3. Filter semantik dengan auto-correction
            extracted_data = self.semantic_filter(extracted_data)
            
            # 4. Simpan hasil
            for field, value in extracted_data.items():
                if value is not None and value != "" and value != []:
                     # Resolve key to DB variable name
                    db_key = resolve_db_key(field, question_map)
                
                    if db_key and db_key in question_map:
                        question = question_map[db_key]
                        self._save_result(
                            interview_id=interview_id,
                            question_obj=question,
                            transcript=transcript,
                            value=value,
                            confidence=1.0
                        )
                        # PUBLISH Event
                        channel = RedisChannel.interview_updates(interview_id)
                        await async_redis_client.publish(channel, json.dumps({
                            "type": "answer_extracted",
                            "success": True,
                            "question_id": question.id,
                            "variable_name": question.variable_name,
                            "extracted_answer": value,
                            "confidence": 1.0,
                            "transcript": transcript
                        }))

            
        except Exception as e:
            self.logger.error(f"Extraction processing failed: {e}")
            self.logger.error(traceback.format_exc())
            self.db.rollback()

    # Legacy method kept just in case but likely unused now
    async def _extract_answer(self, transcript: str, question: QuestionnaireQuestion) -> dict:
        return {}

async def main():
    ml_logger.info("Starting LLM Worker...")
    worker = LLMWorker()
    
    try:
        await async_redis_client.ping()
        ml_logger.info("Connected to Redis.")
    except Exception as e:
        return

    while True:
        try:
            result = await async_redis_client.blpop(RedisQueue.LLM_EXTRACTION, timeout=1)
            if result:
                _, data_json = result
                await worker.process_extraction(json.loads(data_json))
        except Exception as e:
            ml_logger.error(f"LLM Worker Error: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
