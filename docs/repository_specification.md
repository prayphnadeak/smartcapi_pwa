# Spesifikasi Repository SmartCAPI PWA

Dokumen ini menjelaskan arsitektur, teknologi, dan spesifikasi sistem untuk repository **SmartCAPI PWA**.

## 1. Ikhtisar Proyek (Project Overview)

**SmartCAPI PWA** adalah aplikasi survei berbasis web (Progressive Web App) yang dirancang untuk membantu surveyor (enumerator) melakukan wawancara lapangan secara efisien. Sistem ini memiliki kemampuan **Offline-First**, perekaman audio, dan fitur **AI (Artificial Intelligence)** untuk transkripsi dan ekstraksi jawaban otomatis secara real-time maupun batch.

## 2. Arsitektur Sistem

Sistem menggunakan arsitektur **Client-Server** dengan pola hybrid (REST API + WebSocket) dan pemrosesan latar belakang (Background Workers).

### Diagram Tingkat Tinggi
*   **Client (Frontend)**: Vue.js PWA yang berjalan di browser/HP enumerator.
*   **API Gateway (Backend)**: FastAPI server yang menangani request HTTP dan koneksi WebSocket.
*   **Message Broker**: Redis untuk komunikasi antarkomponen dan antrian tugas (Queue).
*   **Worker Nodes**: Service terpisah untuk tugas berat (Transkripsi Audio, Speaker Diarization, Ekstraksi LLM).
*   **Database**: MySQL/MariaDB untuk penyimpanan data utama.

## 3. Tech Stack

### Frontend (`smartcapi-client`)
*   **Framework**: Vue.js 3 (Composition API)
*   **Build Tool**: Vite
*   **State Management**: Pinia
*   **Routing**: Vue Router
*   **Styling**: CSS (Custom/Vanilla), responsive design.
*   **Storage**: IndexedDB (untuk penyimpanan offline data wawancara).
*   **Audio**: Web Audio API (MediaRecorder, ScriptProcessorNode) untuk perekaman dan visualisasi PCM 16kHz.

### Backend (`smartcapi-backend`)
*   **Framework**: FastAPI (Python)
*   **ORM**: SQLAlchemy
*   **Database**: MySQL (via XAMPP/MariaDB)
*   **Async/Queue**: Celery & Redis
*   **Real-time Communication**: WebSockets, Redis Pub/Sub

### AI & Machine Learning Services
*   **ASR (Automatic Speech Recognition)**:
    *   OpenAI Whisper API (`whisper-1`)
    *   Faster-Whisper (Local/Worker fallback)
*   **LLM (Large Language Model)**:
    *   OpenAI GPT-4o-mini (untuk ekstraksi informasi dan normalisasi teks).
*   **Speaker Diarization**:
    *   **VAD (Voice Activity Detection)**: Berbasis energi (RMS) dan Silence Threshold.
    *   **Speaker ID**: Random Forest Classifier (`sklearn`) menggunakan fitur MFCC.
    *   **Logic**: Membedakan Enumerator (User Login) vs Responden (Lainnya).

## 4. Fitur Utama

1.  **Manajemen Pengguna & Autentikasi**:
    *   Login berbasis token (JWT/Bearer).
    *   Role-based access (Administrator vs Enumerator).

2.  **Mode Wawancara**:
    *   **Mode Manual**: Pengisian formulir kuesioner standar.
    *   **Mode AI (Smart Mode)**: Perekaman wawancara dengan bantuan AI untuk mengisi formulir otomatis.

3.  **Pemrosesan Audio Cerdas**:
    *   **Real-time Transcription**: Transkripsi langsung saat wawancara berlangsung.
    *   **Real-time Extraction**: Mengisi field kuesioner secara otomatis begitu responden menjawab pertanyaan terkait.
    *   **Speaker Identification**: Memisahkan suara enumerator (diabaikan) dan responden (diproses).
    *   **Hallucination Filter**: Filter khusus untuk menghapus teks sampah/halusinasi dari model Whisper pada audio hening/bising.

4.  **Offline-First Capability**:
    *   Data disimpan lokal di IndexedDB saat offline.
    *   Sinkronisasi otomatis ke server saat kembali online.

## 5. Struktur Direktori

### Backend (`smartcapi-backend/`)
*   `app/api/`: Endpoint API (v1) dan WebSocket handlers.
*   `app/core/`: Konfigurasi sistem (`config.py`), logger, dan security.
*   `app/db/`: Model database SQLAlchemy dan koneksi DB.
*   `app/services/`: Logika bisnis utama (WhisperService, LLMService, DiarizationService).
*   `app/workers/`: Celery workers untuk pemrosesan background.
*   `app/processing/`: Utilitas pemrosesan audio (AudioUtils) dan ML models.
*   `app/storage/`: Folder penyimpanan file audio upload dan log.
*   `test_*.py`: Skrip pengujian unit/integrasi.

### Frontend (`smartcapi-client/`)
*   `src/components/`: Komponen Vue reusable.
*   `src/pages/`: Halaman aplikasi (Login, Interview, Dashboard).
*   `src/store/`: State management (AuthStore, InterviewStore).
*   `src/services/`: API client services.
*   `src/assets/`: Statik files (images, icons).

## 6. Variabel Lingkungan Penting (.env)

*   `DATABASE_URL`: Connection string database.
*   `OPENAI_API_KEY`: Key untuk akses layanan OpenAI.
*   `CELERY_BROKER_URL`: URL koneksi Redis.
*   `SILENCE_THRESHOLD`: Batas sensitivitas deteksi suara (VAD).
*   `WHISPER_MODEL_PATH`: Lokasi model Whisper (jika lokal).
*   `RF_MODEL_PATH`: Lokasi model Random Forest (Speaker ID).

## 7. Alur Kerja "Proses AI" (Batch)

1.  **Upload**: Audio lengkap diunggah ke server.
2.  **Preprocessing**: Konversi format audio.
3.  **Diarization**: Segmentasi audio berdasarkan pembicara (Enumerator/Responden).
4.  **Filtering**: Hapus segmen enumerator.
5.  **Transcription**: Transkripsi segmen responden menggunakan Whisper.
6.  **Extraction**: Kirim transkrip ke LLM dengan skema JSON kuesioner.
7.  **Result**: Kembalikan JSON terstruktur ke frontend untuk mengisi form.

---
*Dokumen ini diperbarui terakhir pada: Desember 2025*
