# SmartCAPI PWA

![SmartCAPI Logo](https://via.placeholder.com/150) <!-- Replace with actual logo URL if available -->

**SmartCAPI PWA** is a sophisticated Computer Assisted Personal Interviewing (CAPI) system designed as a Progressive Web App (PWA). It leverages advanced Artificial Intelligence (AI) to streamline field data collection, featuring offline capabilities, real-time audio transcription, and intelligent answer extraction.

## Key Features

*   **Offline-First Architecture**: Built on Vue.js and IndexedDB, ensuring full functionality even without an internet connection. Data syncs automatically when connectivity is restored.
*   **AI-Powered Interviewing**:
    *   **Real-time Transcription**: Uses OpenAI Whisper (via API or local worker) to transcribe interviews on the fly.
    *   **Intelligent Extraction**: Automatic answer extraction using GPT-4o-mini to populate questionnaire fields from natural conversation.
    *   **Speaker Diarization**: Smartly distinguishes between Enumerator and Respondent to focus processing only on relevant answers.
    *   **Hallucination Filtering**: Advanced filtering to remove non-speech noise and AI hallucinations.
*   **Audio Management**:
    *   High-quality compressed audio recording.
    *   Visual audio inputs (waveform/RMS).
    *   Secure storage and playback of interview recordings.
*   **Role-Based Access**: Dedicated workflows for Administrators and Enumerators.

## Tech Stack

### Client (Frontend)
*   **Framework**: [Vue.js 3](https://vuejs.org/) (Composition API)
*   **Build Tool**: [Vite](https://vitejs.dev/)
*   **State Management**: [Pinia](https://pinia.vuejs.org/)
*   **Routing**: [Vue Router](https://router.vuejs.org/)
*   **Styling**: Custom CSS (Responsive & Modern UI)
*   **Storage**: IndexedDB (Local) & LocalStorage (Auth)

### Server (Backend)
*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
*   **Database**: MySQL / MariaDB (SQLAlchemy)
*   **Async Task Queue**: Celery with Redis Broker
*   **AI Services**:
    *   **ASR**: OpenAI Whisper
    *   **LLM**: OpenAI GPT-4o-mini
    *   **ML**: Scikit-Learn (Random Forest) for Speaker ID

##Prerequisites

Before you begin, ensure you have the following installed:
*   [Node.js](https://nodejs.org/) (v16+)
*   [Python](https://www.python.org/) (v3.9+)
*   [Redis](https://redis.io/) (Running locally or via Docker)
*   [XAMPP](https://www.apachefriends.org/) (or any MySQL server)

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/StartCAPI-Project/smartcapi_pwa.git
cd smartcapi_pwa
```

### 2. Backend Setup
Navigate to the backend directory:
```bash
cd smartcapi-backend
```

Create a virtual environment and install dependencies:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

Configure environment variables:
Copy `.env.example` to `.env` and fill in your details (DB URL, OpenAI Key, Redis URL).
```bash
cp .env.example .env
```

Initialize the database:
```bash
# Ensure MySQL is running and the database 'smartcapi' exists
python run_server.py
```

### 3. Frontend Setup
Navigate to the client directory:
```bash
cd ../smartcapi-client
```

Install dependencies:
```bash
npm install
```

Configure environment variables:
Create `.env` file referencing your backend API URL.

## 🏃‍♂️ Usage

### Running the Backend
In the `smartcapi-backend` directory, start the API server and Celery workers.
*Tip: It's recommended to run these in separate terminals.*

**Terminal 1: API Server**
```bash
python run_server.py
```
**Terminal 2: Background Workers (Audio/AI Processing)**
```bash
python run_workers.py
```

### Running the Frontend
In the `smartcapi-client` directory:
```bash
npm run dev
```
Access the application at `http://localhost:5173`.

## 📁 Project Structure

```
smartcapi_pwa/
├── deploy/                     # Deployment Automation (CentOS Stream 9)
│   ├── deploy_backend.sh       # Backend Service Deployment
│   ├── deploy_frontend.sh      # Frontend Build & Nginx Configuration
│   ├── packager.py             # Deployment Artifact Packager
│   └── setup_remote.sh         # VPS Initialization (Deps, Redis, Nginx, FFmpeg)
├── docs/                       # Architectural Documentation
│   ├── database.dbml           # Database Schema (DBML Format)
│   └── *.puml                  # Sequence Diagrams (PlantUML)
├── smartcapi-backend/          # FastAPI Backend application
│   ├── app/
│   │   ├── api/v1/             # API Endpoints (Auth, Interview, Users, WS)
│   │   ├── core/               # Core Config (Env, Logger, Security, Redis)
│   │   ├── db/                 # Database Layer (SQLAlchemy Models)
│   │   ├── processing/         # Audio & AI Processing Pipeline
│   │   │   ├── audio/          # Audio Utils & Feature Extraction
│   │   │   ├── llm/            # LLM Prompts & Chains
│   │   │   ├── queues/         # Redis Queue Publishers
│   │   │   └── workers/        # Worker Logic (Audio, Whisper, LLM)
│   │   ├── schemas/            # Pydantic Schemas (Request/Response)
│   │   ├── services/           # Business Logic Services
│   │   │   ├── auth_service.py
│   │   │   ├── file_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── realtime_extraction.py
│   │   │   ├── whisper_service.py
│   │   │   └── ...
│   │   ├── workers/            # Independent Worker Processes (Merger, etc.)
│   │   └── main.py             # Application Entry Point
│   ├── scripts/                # Maintenance Scripts
│   ├── tests/                  # Integration & Unit Tests
│   ├── requirements.txt        # Python Dependencies
│   ├── run_server.py           # Dev Server Launcher (Uvicorn)
│   └── run_workers.py          # Worker Process Launcher
└── smartcapi-client/           # Vue 3 Frontend PWA
    ├── public/                 # Static Assets (Icons, Manifest)
    ├── src/
    │   ├── assets/             # CSS, Images, SVGs
    │   ├── components/         # Vue Components
    │   │   ├── Interview/      # Recorder, Chat, ManualForm
    │   │   ├── Layout/         # AppShell, Navbar, Notifications
    │   │   ├── Rekapitulasi/   # Data Tables & Exports
    │   │   └── ui/             # Shared UI Elements (Buttons, Inputs)
    │   ├── composables/        # Composition API Hooks
    │   │   ├── useAudioRecorder.js
    │   │   ├── useInterview.js
    │   │   ├── useOfflineDB.js
    │   │   ├── useWebSocket.js
    │   │   └── ...
    │   ├── pages/              # Route Views (Login, Register, Dashboard)
    │   ├── router/             # Vue Router Config
    │   ├── services/           # External Services
    │   │   ├── api.js          # Axios Client
    │   │   ├── auth.js         # Auth Management
    │   │   ├── syncService.js  # Offline Data Sync
    │   │   └── ws.js           # WebSocket Client
    │   ├── store/              # Pinia Global State
    │   │   ├── auth.js
    │   │   ├── interview.ts
    │   │   └── ...
    │   ├── utils/              # Utilities (UUID, Network Monitor)
    │   ├── App.vue             # Root Component
    │   └── main.ts             # App Entry Point
    ├── index.html              # PWA Entry Point
    └── vite.config.js          # Vite Configuration
```

## Administrator Credential for accessing PWA

* username : admincapi
* password : supercapi
* role     : managing users and database

## � Python Libraries & Dependencies

The backend is built with a robust set of Python libraries to handle API requests, AI processing, database management, and asynchronous tasks.

| Library | Function / Purpose |
| :--- | :--- |
| **fastapi** | High-performance web framework for building APIs with Python 3.9+. |
| **uvicorn** | ASGI web server implementation for Python. |
| **sqlalchemy** | SQL Toolkit and Object Relational Mapper (ORM) for database interactions. |
| **pydantic** | Data validation using Python type hints, ensuring data integrity. |
| **pydantic-settings** | Management of application settings and environment variables. |
| **python-jose** | JavaScript Object Signing and Encryption (JOSE) implementation for JWT handling. |
| **passlib** | Password hashing library (using bcrypt) for secure authentication. |
| **python-multipart** | Streaming multipart parser, essential for file uploads. |
| **openai** | Official client library for accessing OpenAI's API (GPT-4o, Whisper). |
| **httpx** | A next-generation HTTP client for Python, used for async API calls. |
| **faster-whisper** | Faster implementation of OpenAI's Whisper model for local speech-to-text. |
| **librosa** | Python package for music and audio analysis (feature extraction). |
| **soundfile** | Library for reading and writing sound files (WAV, FLAC, etc.). |
| **numpy** | The fundamental package for scientific computing with Python. |
| **scikit-learn** | Machine learning library used for speaker identification models. |
| **torch** | Open source machine learning framework (PyTorch), underlying engine for AI models. |
| **torchaudio** | Audio library for PyTorch, providing I/O and signal processing. |
| **celery** | Distributed task queue for handling background jobs (transcription, extraction). |
| **redis** | In-memory data structure store, used as the message broker for Celery. |
| **alembic** | Lightweight database migration tool for usage with SQLAlchemy. |
| **email-validator** | Robust email syntax validation library. |

## �📄 License
This project is proprietary. All rights reserved.

## 👥 Contributors
*   **Pray Putra Hasianro Nadeak** - Developer
*   **Irma Amalia Dewi**  Co-advisor
*   **Prof. Dr. Ir. Yoanes Bandung, S.T, M.T** - Advisor
  
All contributors come from ITB-Bandung Institute of Technology



