import os
import re
import json
import datetime
from typing import Dict, Any, List
from openai import OpenAI
from app.core.config import settings
from app.core.logger import ml_logger

# Improved Prompt Template (User Provided)
EXTRACTION_PROMPT_TEMPLATE = """
Anda adalah asisten AI yang ahli dalam mengekstrak informasi terstruktur dari transkrip wawancara CAPI (Computer Assisted Personal Interviewing).

TRANSKRIP WAWANCARA:
{transcript}

TANGGAL WAWANCARA:
{current_date}

TARGET FIELD:
{target_schema}

INSTRUKSI EKSTRAKSI:
1. Baca transkrip dengan teliti dan ekstrak HANYA informasi yang EKSPLISIT disebutkan oleh RESPONDEN
2. Abaikan pertanyaan dari pewawancara
3. Perhatikan bahwa label speaker (Enumerator/Respondent) mungkin tidak akurat atau berlabel "Unknown". Gunakan konteks percakapan untuk menentukan mana yang merupakan jawaban responden.
4. Jika informasi tidak jelas atau tidak disebutkan, kembalikan null untuk field tersebut
5. Konversi kata "kosong" menjadi "0" jika disebutkan sebelum atau sesudah bilangan/angka (Contoh: "kosong delapan" -> "08", "satu kosong" -> "10").
6. Format output HARUS valid JSON dengan field sesuai target_schema

ATURAN KHUSUS PER FIELD:
- nama: Ekstrak nama lengkap responden (BUKAN pewawancara). Hindari prefix "Bapak/Ibu" jika ada nama asli
- tempat_lahir: Nama kota/kabupaten tempat lahir
- tanggal_lahir: Format DD/MM/YYYY. Jika hanya menyebut tahun, gunakan 01/01/YYYY. Jika hanya tanggal tanpa bulan, gunakan DD/01/YYYY
- usia: HITUNG OTOMATIS: (Tanggal Wawancara - Tanggal Lahir) dengan pendekatan Last Birthday (ulang tahun terakhir). Jangan bulatkan ke atas.
- pendidikan: Jenjang terakhir (SD/SMP/SMA/D3/S1/S2/S3). Normalisasi ke format standar
- alamat: Alamat lengkap atau minimal kelurahan/kecamatan. Normalisasi: "jalan"->"Jl.", "kelurahan"->"Kel.", "kecamatan"->"Kec.", "kabupaten"->"Kab.", "lorong"->"Lr.", "nomor"->"No.", "provinsi"->"Prov."
- pekerjaan: Pekerjaan/profesi saat ini. JANGAN isi dengan "Survei" atau "Interview"
- hobi: Array of string, hobi atau kesukaan. Contoh: ["membaca", "olahraga"]
- nomor_telepon: Nomor HP format Indonesia (08xxx atau 628xxx)
- alamat_email: Email address valid

ATURAN KHUSUS DETEKSI FRASE (STRONG SIGNALS):
Jika speaker teridentifikasi sebagai RESPONDEN (atau konteks jelas responden), PRIORITASKAN kalimat berikut:
1. "nama lengkap saya..." / "nama lengkapnya..." / "nama lengkap saya adalah..." -> ISI FIELD 'nama' dengan kata-kata setelahnya.
2. "alamat lengkap saya..." / "alamat lengkap rumah saya..." / "alamat lengkap rumah ini..." / "kami tinggal di..." / "saya tinggal di..." -> ISI FIELD 'alamat' dengan deskripsi lokasi setelahnya SEPANJANG APAPUN alamat tersebut disebutkan.
3. "pekerjaan saya sehari-hari..." / "pekerjaannya..." / "pekerjaan saya saat ini..." -> ISI FIELD 'pekerjaan' dengan aktivitas yang disebutkan.
4. "hobi saya..." / "hobinya..." / "hobi saya itu..." -> ISI FIELD 'hobi' dengan daftar kegiatan setelahnya.
5. "nomor HP saya..." / "nomor teleponnya..." / "nomor HP nya..." / "nomor hapenya..." -> ISI FIELD 'nomor_telepon' dengan format NUMERIK/ANGKA ARAB (contoh: 081234567890).
6. KHUSUS FIELD EMAIL: "email saya..." / "alamat emailnya..." -> ISI FIELD 'email'. Lakukan konversi:
   - kata "at" ubah menjadi "@"
   - kata "underscore" ubah menjadi "_"
   - kata "dot" atau "titik" ubah menjadi "."
   - angka yang dieja (misal "satu") ubah menjadi angka arab ("1").

CONTOH EKSTRAKSI:
Transkrip: "Nama saya Budi Santoso, lahir di Jakarta tanggal 15 Agustus 1990. Sekarang saya berusia 34 tahun. Pendidikan terakhir S1. Tinggal di Jalan Sudirman No 10."
Output:
{{
  "nama": "Budi Santoso",
  "tempat_lahir": "Jakarta",
  "tanggal_lahir": "15/08/1990",
  "usia": "34",
  "pendidikan": "S1",
  "alamat": "Jalan Sudirman No 10",
  "pekerjaan": null,
  "hobi": [],
  "nomor_telepon": null,
  "alamat_email": null
}}



OUTPUT JSON:
Pastikan response Anda HANYA berisi valid JSON tanpa penjelasan tambahan.
"""

class LLMService:
    # Function to initialize LLMService
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.system_prompt_path = "./app/processing/llm/prompts/system_prompt.txt"
        self.extract_prompt_path = "./app/processing/llm/prompts/extract_info.txt"
        self._load_prompts()
        self.DEFAULT_STRUCTURE = {
            "nama": None,
            "alamat": None,
            "tempat_lahir": None,
            "tanggal_lahir": None,
            "usia": None,
            "pendidikan": None,
            "pekerjaan": None,
            "hobi": [],
            "nomor_telepon": None,
            "alamat_email": None
        }
    
    # Function to load prompts
    def _load_prompts(self):
        """Load system and extraction prompts from files"""
        try:
            prompts_dir = os.path.dirname(self.system_prompt_path)
            os.makedirs(prompts_dir, exist_ok=True)
            
            # SYSTEM PROMPT 
            if os.path.exists(self.system_prompt_path):
                with open(self.system_prompt_path, 'r') as f:
                    self.system_prompt = f.read()
            else:
                self.system_prompt = """You are an information extraction assistant for SmartCAPI.""" # Simplified fallback
            
            # EXTRACTION PROMPT (Force Update for Opportunistic Model)
            # We want to overwrite or ensure it matches the new requirement
            self.extract_prompt = """
Below is an ASR transcription result of an interview segment. 
Your task is to extract ANY relevant information that matches the target schema.

TARGET SCHEMA:
{target_schema}

CRITICAL RULES:
1. ONE segment may contain MULTIPLE valid fields. Extract all of them.
2. If the transcript contains NO relevant information for the schema, return an empty JSON object `{}`.
3. Do NOT hallucinate. Only extract what is explicitly stated or strongly implied by the respondent.
4. For 'nama' (Name), extract full names.
5. For 'usia' (Age), if Year of Birth is mentioned (e.g. 1990), calculate age based on current year (2025).
6. Return purely the JSON object.

### PROCESS THIS INPUT ###
Transkrip: {transcript}
"""         
            # We don't save this dynamic prompt to file to avoid overwriting user customizations 
            # unless we decided to stick to a fixed file. 
            # For now, let's keep the file logic for system prompt but use dynamic for extract to ensure Schema injection works.

            ml_logger.info("Prompts loaded successfully")

        except Exception as e:
            ml_logger.error(f"Error loading prompts: {str(e)}")
            self.system_prompt = "Anda adalah asisten AI untuk SmartCAPI."

    # Function to extract information from transcript
    def extract_information(self, transcript: str, prompt: str = None, schema: List[str] = None) -> Dict[str, Any]:
        """
        Ekstraksi informasi dengan prompt yang lebih baik
        """
        try:
            # Handle empty transcript early
            if not transcript or not transcript.strip():
                return {}

            ml_logger.info(f"Extracting information (Length: {len(transcript)})")

            # Bersihkan transkrip dari noise
            cleaned_transcript = self.clean_transcript(transcript)
            
            # Build Schema Representation
            # If prompt is NOT None, we might skip this if the manual prompt doesn't need schema injection
            # But the user logic generally relies on TARGET_FIELD placeholder?
            # Existing code checked if schema: -> schema_str. 
            # The new template uses {target_schema}.
            
            target_schema_list = schema if schema else list(self.DEFAULT_STRUCTURE.keys())
            
            # Buat prompt
            current_date = datetime.datetime.now().strftime("%d/%m/%Y")
            
            if prompt is None:
                final_prompt = EXTRACTION_PROMPT_TEMPLATE.format(
                    transcript=cleaned_transcript,
                    target_schema=json.dumps(target_schema_list, ensure_ascii=False),
                    current_date=current_date
                )
            else:
                # Fallback to manual prompt if provided (legacy support)
                final_prompt = prompt.replace("{transcript}", cleaned_transcript)
                if schema and "{target_schema}" in final_prompt:
                     final_prompt = final_prompt.replace("{target_schema}", json.dumps(target_schema_list, ensure_ascii=False))
                # Try inject date if placeholder exists
                if "{current_date}" in final_prompt:
                    final_prompt = final_prompt.replace("{current_date}", current_date)

            # Call OpenAI GPT-4o-mini
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert data extraction assistant for CAPI interviews. Always respond with valid JSON only."},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=0.1,  # Lower temperature untuk konsistensi
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            
            extracted = {}
            try:
                extracted = json.loads(result_text)
            except json.JSONDecodeError:
                # Handle markdown code block if not handled by response_format (gpt usually gives pure json with that flag but just in case)
                if '```' in result_text:
                     # try to extract json block
                     match = re.search(r'```(?:json)?(.*?)```', result_text, re.DOTALL)
                     if match:
                         extracted = json.loads(match.group(1).strip())

            # Post-processing: Normalisasi format
            extracted = self.normalize_extracted_data(extracted)
            
            return extracted
            
        except Exception as e:
            ml_logger.error(f"LLM extraction failed: {e}")
            return {}

    def clean_transcript(self, transcript: str) -> str:
        """
        Bersihkan transkrip dari noise dan hallucination
        """
        if not transcript: return ""
        # Hapus repetisi berlebihan
        transcript = re.sub(r'(\b\w+\b)(\s+\1){3,}', r'\1', transcript)
        
        # Hapus karakter aneh (Keep basic punctuation)
        transcript = re.sub(r'[^\w\s\.,!?-]', '', transcript)
        
        # Normalize whitespace
        transcript = ' '.join(transcript.split())
        
        return transcript

    def normalize_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalisasi data hasil ekstraksi
        """
        if not data: return {}
        normalized = {}
        
        for key, value in data.items():
            if value is None or value == "":
                normalized[key] = None
                continue
            
            # Normalisasi pendidikan
            if key == 'pendidikan' and isinstance(value, str):
                value = value.upper()
                # Map variasi ke format standar
                mapping = {
                    'SEKOLAH DASAR': 'SD',
                    'SEKOLAH MENENGAH PERTAMA': 'SMP',
                    'SEKOLAH MENENGAH ATAS': 'SMA',
                    'SEKOLAH MENENGAH KEJURUAN': 'SMK',
                    'DIPLOMA': 'D3',
                    'SARJANA': 'S1',
                    'MAGISTER': 'S2',
                    'DOKTOR': 'S3'
                }
                value = mapping.get(value, value)
            
            # Normalisasi hobi ke array
            if key == 'hobi':
                if isinstance(value, str):
                    # Split by comma atau semicolon
                    value = [h.strip() for h in re.split(r'[,;]', value) if h.strip()]
                elif not isinstance(value, list):
                    value = []
            
            # Normalisasi nomor telepon
            if key == 'nomor_telepon' and isinstance(value, str):
                # Hapus karakter non-digit
                digits = re.sub(r'\D', '', value)
                # Format ke 08xxx
                if digits.startswith('628'):
                    value = '0' + digits[2:]
                else:
                    value = digits
            
            # Normalisasi tanggal
            if key == 'tanggal_lahir' and isinstance(value, str):
                # Pastikan format DD/MM/YYYY
                if '-' in value:
                    parts = value.split('-') # Check YYYY-MM-DD or DD-MM-YYYY
                    if len(parts) == 3:
                        if len(parts[0]) == 4:  # YYYY-MM-DD -> DD/MM/YYYY
                            value = f"{parts[2]}/{parts[1]}/{parts[0]}"
                        else:  # DD-MM-YYYY -> DD/MM/YYYY
                            value = '/'.join(parts)
            
            # Normalisasi Alamat (User Request)
            if key == 'alamat' and isinstance(value, str):
                replacements = {
                    r'\bdaerah\b': '', # Remove filler
                    r'\bjalan\b': 'Jl.',
                    r'\bkelurahan\b': 'Kel.',
                    r'\bkecamatan\b': 'Kec.',
                    r'\bkabupaten\b': 'Kab.',
                    r'\blorong\b': 'Lr.',
                    r'\bnomor\b': 'No.',
                    r'\bprovinsi\b': 'Prov.'
                }
                for pattern, replace in replacements.items():
                    value = re.sub(pattern, replace, value, flags=re.IGNORECASE)
            
            normalized[key] = value
        
        return normalized

    # Function to correct grammar of transcript
    def correct_grammar(self, text: str) -> str:
        """
        Correct grammar and punctuation of ASR text without changing meaning.
        Useful for cleaning up raw Whisper output before extraction.
        """
        try:
            if not text or len(text) < 5:
                return text

            prompt = f"""Perbaiki tata bahasa dan tanda baca dari teks berikut.
JANGAN mengubah makna, nama orang, atau informasi penting.
Hanya perbaiki typo, kapitalisasi, dan struktur kalimat yang berantakan.
Outputkan HANYA teks yang diperbaiki tanpa basa-basi.

Teks Asli: "{text}"
Teks Perbaikan:"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful grammar checking assistant for Indonesian language."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            corrected = response.choices[0].message.content.strip()
            # If model returns empty or hallucinated weirdness, fallback to original
            if not corrected:
                return text
                
            return corrected

        except Exception as e:
            ml_logger.error(f"Error correcting grammar: {e}")
            return text

    # Function to correct diarization
    def correct_diarization(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Correct speaker diarization labels using LLM reasoning.
        
        Args:
            segments: List of dicts with keys 'speaker' and 'text'
            
        Returns:
            Dict with corrected segments
        """
        try:
            if not segments:
                return {"segments": []}
                
            # Format input for LLM
            input_text = json.dumps(segments, indent=2)
            
            prompt = f"""
Anda adalah sistem koreksi diarization untuk SmartCAPI.
Anda menerima transkripsi yang sudah memiliki label speaker, tetapi label tersebut dapat salah atau tidak berubah ketika penutur berganti.

Tugas Anda:
1. Identifikasi segmen yang kemungkinan salah diarization berdasarkan:
   - perubahan gaya bicara,
   - perubahan topik secara tiba-tiba,
   - perbedaan struktur kalimat,
   - frasa yang biasanya diucapkan oleh pewawancara (mis. “boleh dijelaskan”, “pertanyaan berikutnya”),
   - frasa yang biasanya diucapkan oleh responden (mis. jawaban personal, informasi biodata, opini pribadi).

2. Perbaiki label speaker hanya jika ada bukti kuat.
   Jangan mengarang speaker baru. Hanya gunakan:
   - "Enumerator"
   - "Respondent"

3. Jika masih ragu, tandai segmen tersebut dengan:
   "uncertain": true
   sehingga modul berikutnya dapat mengambil keputusan lanjutan.

4. Output dalam format JSON:
{{
  "segments": [
    {{
      "speaker_original": "...",
      "speaker_corrected": "Enumerator/Respondent/unknown",
      "text": "...",
      "reason": "<penjelasan singkat>",
      "confidence": 0.0 - 1.0,
      "uncertain": true/false
    }}
  ]
}}

5. Jangan menambah, menghapus, atau mengubah isi perkataan responden.
Lakukan penalaran internal secara diam-diam, berikan hanya hasil JSON.

Berikut input transkripsi:
{input_text}
"""
            ml_logger.info(f"Correcting diarization for {len(segments)} segments")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs strictly JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                ml_logger.error(f"Failed to parse diarization correction JSON: {content}")
                # Fallback: return original structure
                return {"segments": []}
                
        except Exception as e:
            ml_logger.error(f"Error correcting diarization: {str(e)}")
            return {"segments": []}

    # Function to normalize transcription (remove fillers, fix punctuation)
    def normalize_transcript(self, text: str) -> str:
        """
        Normalize transcription by removing fillers, correcting punctuation and capitalization,
        without changing the meaning or factual information.
        
        Args:
            text: Raw transcript text
            
        Returns:
            Normalized transcript text
        """
        try:
            if not text or len(text) < 10:
                return text
                
            prompt = f"""
Anda adalah modul Normalisasi Transkripsi untuk SmartCAPI.

Tugas Anda adalah membersihkan transkripsi Whisper tanpa mengubah makna perkataan responden.

PERATURAN KETAT:
1. Jangan menambah, menghapus, atau mengubah informasi faktual.
2. Jangan membuat interpretasi baru.
3. Hanya lakukan:
   - menghapus filler (eee, em, anu, hmm, gitu, apa namanya, ya ya, dll)
   - menghapus pengulangan kata yang tidak memberi makna
   - memperbaiki pemisahan kalimat
   - menambah tanda baca ringan
   - memperbaiki kapitalisasi
   - menggabungkan frasa yang Whisper potong menjadi terpisah
   - memperbaiki salah dengar yang jelas (contoh: “aku tua” menjadi “kuliah” bila konteks sangat kuat)
4. Jangan merapikan gaya bicara, hanya struktur minimal.
   Ini bukan rewrite gaya bahasa, hanya normalisasi teknis.

HASIL OUTPUT:
Berikan hasil dalam format JSON berikut:
{{
  "normalized_text": "<hasil_normalisasi>",
  "changes_made": ["..."],
  "confidence": 0.0 - 1.0
}}

Jika terdapat bagian yang Anda ragu untuk normalisasi, biarkan apa adanya dan tandai pada field "changes_made".

Lakukan seluruh penalaran internal secara diam-diam. Berikan hanya JSON final.

Berikut transkripsi Whisper:
"{text}"
"""
            ml_logger.info("Normalizing transcript...")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs strictly JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=3000, # Allow for long transcripts
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            try:
                result = json.loads(content)
                normalized = result.get("normalized_text", text)
                changes = result.get("changes_made", [])
                
                if changes:
                    ml_logger.info(f"Normalization changes ({len(changes)}): {changes[:3]}...")
                    
                return normalized
            except json.JSONDecodeError:
                ml_logger.error(f"Failed to parse normalization JSON: {content[:100]}...")
                return text
                
        except Exception as e:
            ml_logger.error(f"Error normalizing transcript: {str(e)}")
            return text

llm_service = LLMService()