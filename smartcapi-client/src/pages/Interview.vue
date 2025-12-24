<template>
  <div>
    <div class="container interview-page">
      <button class="back-btn" @click="goBack">&lt;&lt; Kembali</button>

      <div class="form-title">Wawancara dengan Asistensi AI</div>

      <!-- AI Status Banner -->
      <center>
      <div v-if="realtimeMode" class="ai-status-banner" :class="aiStatus">
        <span v-if="aiStatus === 'preparing'"> Asisten AI sedang bersiap... (Memuat Model)</span>
        <span v-if="aiStatus === 'ready'"> Asisten AI siap membantu Anda!</span>
        <span v-if="aiStatus === 'error'">⚠️ Gagal terhubung ke Asisten AI.</span>
      </div>
      </center>
      <br></br>
      <form @submit.prevent="openSubmitDialog" class="interview-form">
        <div v-for="q in questions" :key="q.key" class="question-block">
          <label :for="q.key">{{ q.label }}</label>
          <div class="input-wrapper">
            <select
              v-if="q.type === 'select'"
              :id="q.key"
              v-model="manualForm[q.key]"
              class="form-input"
              @focus="handleInputFocus(q.key)"
            >
              <option disabled value="">Pilih Pendidikan</option>
              <option v-for="option in q.options" :key="option" :value="option">
                {{ option }}
              </option>
            </select>
            <input
              v-else
              :id="q.key"
              v-model="manualForm[q.key]"
              :type="q.type || 'text'"
              class="form-input"
              :placeholder="q.key === 'tanggal_lahir' ? 'dd/mm/yyyy' : ''"
              @blur="q.key === 'tanggal_lahir' ? handleDateBlur : null"
              @focus="handleInputFocus(q.key)"
            />
            
            <!-- Real-time Progress Spinner -->
            <div 
              v-if="currentQuestion && currentQuestion.variable_name === q.key && (silenceDetected || processingStatus !== 'Menunggu...')" 
              class="field-spinner"
              title="Memproses..."
            >
              <svg viewBox="0 0 50 50" class="spinner-svg">
                <circle cx="25" cy="25" r="20" fill="none" stroke="#e0e0e0" stroke-width="5"></circle>
                <circle 
                  cx="25" cy="25" r="20" 
                  fill="none" 
                  stroke="#007bff" 
                  stroke-width="5"
                  stroke-dasharray="126"
                  :stroke-dashoffset="126 - (126 * processingProgress / 100)"
                  transform="rotate(-90 25 25)"
                ></circle>
              </svg>
            </div>
          </div>
        </div>
      </form>

      <!-- Real-time Extraction UI Components -->
      <div v-if="realtimeMode" class="realtime-section">
        <!-- Current Question Display -->
        <!-- Current Question Display REMOVED as per user request (Opportunistic Mode) -->
        <!-- <div v-if="currentQuestion" class="current-question-card">
          <div class="question-header">
            <span class="question-number">Pertanyaan {{ currentQuestion.question_number }}</span>
            <span class="question-progress">{{ currentQuestionIndex + 1 }}/{{ totalQuestions }}</span>
          </div>
          <p class="question-text">{{ currentQuestion.question_text }}</p>
        </div> -->

        <!-- Silence Detection Indicator -->
        <div v-if="silenceDetected || processingStatus !== 'Menunggu...'" class="silence-indicator">
          <div class="spinner" v-if="silenceDetected"></div>
          <span>{{ processingStatus }}</span>
          <div class="progress-bar-container">
            <div class="progress-bar-fill" :style="{width: processingProgress + '%'}"></div>
          </div>
          <span class="progress-text">{{ processingProgress }}%</span>
        </div>

        <!-- Interview Progress Bar -->
        <div v-if="totalQuestions > 0" class="interview-progress">
          <div class="progress-info">
            <span>Progress Interview</span>
            <span class="progress-percentage">{{ Math.round((currentQuestionIndex / totalQuestions) * 100) }}%</span>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar-fill" :style="{width: (currentQuestionIndex / totalQuestions * 100) + '%'}"></div>
          </div>
        </div>

        <!-- Extracted Answers List REMOVED as per user request -->
        <!-- Just rely on auto-fill and top status bar -->



        <!-- Live Transcript -->
        <!-- Live Transcript (Hidden as per User Request)
        <div v-if="liveTranscript" class="live-transcript" style="margin-top: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #007bff;">
          <h4 style="margin: 0 0 0.5rem 0; color: #007bff; font-size: 0.9rem;">Transkrip Langsung</h4>
          <p style="margin: 0; font-style: italic; color: #555;">{{ liveTranscript }}</p>
        </div> 
        -->
      </div>

      <div class="bottom-action-bar">
        <button type="button" class="action-btn clear-btn" @click="handleClear">
          CLEAR DATA
        </button>
        
        <!-- Toggle removed as per request, always in Real-time mode -->
        
        <div class="mic-container">
          <div class="mic-button" :class="{ recording: isRecording }" @click="handleMic">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z" fill="white"/>
              <path d="M19 12H17C17 14.76 14.76 17 12 17C9.24 17 7 14.76 7 12H5C5 15.54 7.72 18.45 11 18.93V22H13V18.93C16.28 18.45 19 15.54 19 12Z" fill="white"/>
            </svg>
          </div>
          <div v-if="isRecording" class="duration-display">{{ formattedDuration }}</div>
        </div>
         
        <!-- New Process AI Button -->
        <!--
        <button type="button" class="action-btn process-btn" @click="handleFinishAndProcess" :disabled="isProcessing">
          {{ isProcessing ? 'Memproses...' : 'Proses AI' }}
        </button>
        -->
        <button type="button" class="action-btn submit-btn" @click="openSubmitDialog">
          SUBMIT
        </button>

      </div>

      <div v-if="showSubmitDialog" class="dialog-overlay">
        <div class="dialog-box">
          <p>Apakah Anda yakin ingin mengirim data wawancara ini?</p>
          <div class="dialog-actions">
            <button class="dialog-btn confirm-btn" @click="confirmSubmit">YA</button>
            <button class="dialog-btn cancel-btn" @click="cancelSubmit">TIDAK</button>
          </div>
        </div>
      </div>

      <!-- Sync Status Indicator (NEW) -->
      <div v-if="syncStatus" class="sync-status" :class="syncStatus">
        <span v-if="syncStatus === 'saving'">💾 Menyimpan data lokal...</span>
        <span v-if="syncStatus === 'saved'">✅ Data tersimpan lokal</span>
        <span v-if="syncStatus === 'syncing'">🔄 Mengirim ke server...</span>
        <span v-if="syncStatus === 'synced'">✅ Data berhasil tersinkronisasi</span>
        <span v-if="syncStatus === 'error'">⚠️ Gagal sinkronisasi (akan coba lagi)</span>
        <span v-if="syncStatus === 'processing'"> Sedang memproses AI...</span>
      </div>

      <!-- Mic Volume & Sensitivity (Diagnostics) -->
      <div class="mic-diagnostics" v-if="isRecording">
         <div class="volume-bar-container">
           <div class="volume-bar-label">Mic Volume</div>
           <div class="volume-bar-track">
             <div class="volume-bar-fill" :style="{ width: micVolume + '%', backgroundColor: micVolume > 10 ? '#28a745' : '#dc3545' }"></div>
           </div>
           <div class="volume-value">{{ micVolume }}%</div>
         </div>
         <div class="sensitivity-control">
            <label>Penguat Suara (Gain): {{ micGain }}x</label>
            <input type="range" min="1" max="5" step="0.5" v-model.number="micGain" class="slider">
         </div>
      </div>

      <!-- DEBUG OVERLAY (Temporary for Diagnosis) -->
      <div style="margin-top: 30px; padding: 10px; border: 2px dashed red; background: #fff0f0; font-size: 10px; font-family: monospace; word-break: break-all;">
        <strong>🔍 DIAGNOSTIC INFO (Screenshot ini jika error):</strong><br>
        WS Status: {{ wsConnected ? 'CONNECTED ✅' : 'DISCONNECTED ❌' }}<br>
        WS URL: {{ debugWsUrl }}<br>
        Realtime Mode: {{ realtimeMode }}<br>
        Last Error: {{ lastWsError }}<br>
        Screen: {{ windowWidth }}x{{ windowHeight }}<br>
        UA: {{ userAgent }}
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useInterviewStore } from '../store/interview';
import { useAuthStore } from '../store/auth';
import { api } from '../services/api';
import { generateUUID } from '../utils/uuid';

const router = useRouter();
const route = useRoute();
const interviewStore = useInterviewStore();
const authStore = useAuthStore();

const questions = [
  { key: 'nama', label: 'Nama Lengkap' },
  { key: 'tempat_lahir', label: 'Tempat Lahir' },
  { key: 'tanggal_lahir', label: 'Tanggal Lahir', type: 'text' },
  { key: 'usia', label: 'Usia', type: 'number' },
  { key: 'pendidikan', label: 'Pendidikan Terakhir', type: 'text' },
  { key: 'alamat', label: 'Alamat Lengkap' },
  { key: 'pekerjaan', label: 'Pekerjaan' },
  { key: 'hobi', label: 'Hobi' },
  { key: 'nomor_telepon', label: 'Nomor Telepon' },
  { key: 'alamat_email', label: 'Alamat Email', type: 'email' },
];


const manualForm = ref(Object.fromEntries(questions.map(q => [q.key, ""])));
const showSubmitDialog = ref(false);
const isRecording = ref(false);
const isProcessing = ref(false);
const timer = ref(null);
const durationInSeconds = ref(0);
const currentInterviewId = ref(null);
const isEditMode = ref(false);

// State baru untuk MediaRecorder
const mediaRecorder = ref(null);
const audioChunks = ref([]);
const audioBlob = ref(null);

// ===== STATE BARU UNTUK OFFLINE-FIRST =====
const syncStatus = ref(''); // saving, saved, syncing, synced, error, processing
const DB_NAME = 'smartcapi_local';
const STORE_NAME = 'transcripts';
// ===========================================

// ===== STATE BARU UNTUK REAL-TIME EXTRACTION =====
const realtimeMode = ref(true); // Default to true (LIVE)
const ws = ref(null); // WebSocket connection
const extractedAnswers = ref([]); // List of extracted answers
const currentQuestion = ref(null); // Current question being asked
const currentQuestionIndex = ref(0); // Current question index
const totalQuestions = ref(0); // Total number of questions
const silenceDetected = ref(false); // Silence detection indicator
const processingProgress = ref(0); // Processing progress (0-100)
const processingStatus = ref('Menunggu...'); // Status text
const wsConnected = ref(false); // WebSocket connection status
const aiStatus = ref('preparing'); // PREPARING, READY, ERROR
const micVolume = ref(0);
const micGain = ref(1.0); // Software gain multiplier
const liveTranscript = ref(""); // Real-time transcript buffer
// DEBUG STATE
const debugWsUrl = ref("");
const lastWsError = ref("None");
const windowWidth = ref(window.innerWidth);
const windowHeight = ref(window.innerHeight);
const userAgent = ref(navigator.userAgent);
// ================================================

onMounted(async () => {
  if (route.query.edit) {
    isEditMode.value = true;
    currentInterviewId.value = route.query.edit;
    await fetchInterviewData(currentInterviewId.value);
  } else {
    await createNewInterview();
  }
  connectWebSocket();
});

onUnmounted(() => {
  // Stop recording if active
  if (isRecording.value && mediaRecorder.value && mediaRecorder.value.state === 'recording') {
    mediaRecorder.value.stop();
    // Stop all tracks to release microphone
    if (mediaRecorder.value.stream) {
      mediaRecorder.value.stream.getTracks().forEach(track => track.stop());
    }
  }
  
  // Clear timer
  if (timer.value) {
    clearInterval(timer.value);
  }
  
  // Disconnect WebSocket
  disconnectWebSocket();
  
  console.log('Interview component unmounted, resources cleaned up');
});

// Function to create a new interview session
async function createNewInterview() {
  try {
    const token = authStore.userToken.value;
    const interviewData = {
      mode: "ai",
      respondent_data: {
        full_name: "New Respondent",
        birth_year: null,
        education: null,
        address: null
      }
    };
    const response = await api.createInterview(interviewData, token);
    currentInterviewId.value = response.data.id;
    console.log("Created new interview with ID:", currentInterviewId.value);
  } catch (error) {
    console.error("Failed to create new interview:", error);
    // Fallback or alert? If we can't create, WS will fail.
  }
}

// Function to fetch interview data by ID
async function fetchInterviewData(id) {
  try {
    const token = authStore.userToken.value;
    const response = await api.getInterview(id, token);
    const data = response.data;

    // Populate form from respondent data
    if (data.respondent) {
        manualForm.value.nama = data.respondent.full_name;
        manualForm.value.pendidikan = data.respondent.education;
        manualForm.value.alamat = data.respondent.address;
        
        // Calculate age if birth_year exists
        if (data.respondent.birth_year) {
            const currentYear = new Date().getFullYear();
            manualForm.value.usia = currentYear - data.respondent.birth_year;
        }
    }
    
    // Populate form from extracted_answers
    if (data.extracted_answers && data.extracted_answers.length > 0) {
        data.extracted_answers.forEach(answer => {
            if (answer.question && answer.question.variable_name) {
                const key = answer.question.variable_name;
                if (manualForm.value.hasOwnProperty(key)) {
                    manualForm.value[key] = answer.answer_text;
                }
            }
        });
    }
    
    // If audio exists, we might want to show it or allow re-recording
    if (data.raw_audio_path) {
        // For now, just indicate that audio exists if needed, or leave as is
        // If user records new audio, it will overwrite
    }
  } catch (error) {
    console.error("Failed to fetch interview", error);
    alert("Gagal mengambil data wawancara.");
  }
}

const formattedDuration = computed(() => {
  const minutes = Math.floor(durationInSeconds.value / 60);
  const seconds = durationInSeconds.value % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
});

// Function to navigate back to rekapitulasi page
function goBack() {
  router.push('/rekapitulasi');
}

// Function to open the submission confirmation dialog
function openSubmitDialog() {
  showSubmitDialog.value = true;
}

// ===== FUNGSI BARU: INIT INDEXEDDB =====
// Function to initialize IndexedDB for offline storage
function initDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const objectStore = db.createObjectStore(STORE_NAME, { keyPath: 'uuid' });
        objectStore.createIndex('sync_status', 'sync_status', { unique: false });
        objectStore.createIndex('timestamp', 'timestamp', { unique: false });
        objectStore.createIndex('interview_id', 'interview_id', { unique: false });
        console.log('📦 IndexedDB initialized');
      }
    };
  });
}

// ===== FUNGSI BARU: SIMPAN KE INDEXEDDB =====
// Function to save interview data to IndexedDB
async function saveToIndexedDB(interviewData) {
  try {
    syncStatus.value = 'saving';
    
    // Wrap DB operation in a promise
    const dbOp = new Promise(async (resolve, reject) => {
        try {
            const db = await initDB();
            const tx = db.transaction(STORE_NAME, 'readwrite');
            const store = tx.objectStore(STORE_NAME);
            
            const record = {
                ...interviewData,
                uuid: generateUUID(), // Use custom UUID generator
                sync_status: 'pending',
                timestamp: new Date().toISOString(),
                last_modified: new Date().toISOString()
            };
            
            const request = store.put(record);
            
            request.onsuccess = () => {
                resolve(record);
            };
            
            request.onerror = () => {
                reject(request.error);
            };
            
            tx.onabort = () => reject(new Error('Transaction aborted'));
            tx.onerror = () => reject(tx.error);
            
        } catch (e) {
            reject(e);
        }
    });
    
    // Create timeout promise
    const timeout = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Timeout saving to local storage (5s)')), 5000)
    );
    
    // Race them
    const record = await Promise.race([dbOp, timeout]);
    
    syncStatus.value = 'saved';
    console.log('✅ Data saved to IndexedDB:', record.uuid);
    setTimeout(() => syncStatus.value = '', 3000); // Clear after 3s
    return record;

  } catch (error) {
    syncStatus.value = 'error';
    console.error('❌ IndexedDB error:', error);
    // Alert user but don't blocking flow entirely if possible, 
    // but here we throw so caller knows it failed.
    // Alert removed to prevent blocking UI on mobile. Fallback to server is automatic.
    console.warn("Warning: Gagal menyimpan data lokal (Timeout/Error). Akan mencoba memproses ke server langsung.");
    // Return mock record to allow flow to continue to server sync if online
    return { uuid: 'temp-' + Date.now(), ...interviewData };
  }
}

// ===== FUNGSI BARU: KONVERSI BLOB KE BASE64 =====
// Function to convert Blob to Base64 string
function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

// ===== FUNGSI BARU: REQUEST BACKGROUND SYNC =====
// Function to register background sync for offline data
async function requestBackgroundSync() {
  if ('serviceWorker' in navigator && 'sync' in self.registration) {
    try {
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register('transcript-sync');
      console.log('🔄 Background sync registered');
    } catch (error) {
      console.error('❌ Background sync registration failed:', error);
    }
  }
}

// Function to process AI extraction manually
async function processAI() {
  if (!audioBlob.value) return;
  
  isProcessing.value = true;
  syncStatus.value = 'processing';
  
  try {
    const token = authStore.userToken.value;
    
    // 1. Create Interview if not exists
    if (!currentInterviewId.value) {
      const interviewData = {
        mode: "ai",
        respondent_data: {
          full_name: manualForm.value.nama || "New Respondent",
          birth_year: null,
          education: null,
          address: null
        }
      };
      const response = await api.createInterview(interviewData, token);
      currentInterviewId.value = response.data.id;
    }
    
    // 2. Upload Audio
    await api.uploadAudio(currentInterviewId.value, audioBlob.value, token);
    
    // 3. Process Audio
    const processResponse = await api.processAudio(currentInterviewId.value, token);
    const extractedInfo = processResponse.data.extracted_info;
    
    // 4. Populate Form
    if (extractedInfo) {
      Object.keys(extractedInfo).forEach(key => {
        if (manualForm.value.hasOwnProperty(key) && extractedInfo[key]) {
          manualForm.value[key] = extractedInfo[key];
        }
      });
    }
    
    syncStatus.value = 'synced';
    setTimeout(() => syncStatus.value = '', 3000);
    alert('Proses AI selesai! Silakan periksa data yang terisi.');
    
  } catch (error) {
    console.error("Error processing AI:", error);
    syncStatus.value = 'error';
    alert('Gagal memproses AI. Silakan coba lagi atau isi manual.');
  } finally {
    isProcessing.value = false;
  }
}

// Function to confirm and submit interview data
async function confirmSubmit() {
  showSubmitDialog.value = false;

  const emptyFields = questions.filter(q => !manualForm.value[q.key] || !String(manualForm.value[q.key]).trim());
  if (emptyFields.length > 0) {
    if (!confirm('Beberapa field masih kosong. Apakah Anda yakin ingin melanjutkan?')) {
      return;
    }
  }

  const startTime = interviewStore.interviewStartTime;
  let totalDuration = 0;
  if (startTime > 0) {
    totalDuration = Math.round((Date.now() - startTime) / 1000);
  }

  const token = authStore.userToken.value;

  // ===== STEP 1: SIMPAN KE INDEXEDDB DULU (OFFLINE-FIRST) =====
  const interviewData = {
    ...manualForm.value,
    duration: totalDuration,
    mode: 'AI',
    has_recording: audioBlob.value ? '1' : '0',
    // Store Blob directly (more efficient than Base64 string for IndexedDB)
    audio_blob: audioBlob.value || null, 
    audio_filename: audioBlob.value ? `recording-${Date.now()}.webm` : null
  };

  try {
    const savedRecord = await saveToIndexedDB(interviewData);
    console.log('💾 Data saved locally with UUID:', savedRecord.uuid);
  } catch (error) {
    console.error('❌ Failed to save locally:', error);
    alert(`Gagal menyimpan data lokal: ${error.message || error}`);
    return;
  }

  // ===== STEP 2: KIRIM KE SERVER (JIKA ONLINE) =====
  if (navigator.onLine) {
    try {
      syncStatus.value = 'syncing';
      
      if (currentInterviewId.value) {
        // Update existing interview
        const currentYear = new Date().getFullYear();
        const birthYear = manualForm.value.usia ? currentYear - parseInt(manualForm.value.usia) : null;
        
        // Prepare rich extracted_data
        const richExtractedData = {};
        for (const [key, value] of Object.entries(manualForm.value)) {
            // Find if we have a transcript for this key in extractedAnswers
            const match = extractedAnswers.value.find(a => a.variable_name === key);
            if (match && match.transcript) {
                richExtractedData[key] = {
                    answer: value,
                    transcript: match.transcript
                };
            } else {
                richExtractedData[key] = value;
            }
        }

        await api.updateInterview(currentInterviewId.value, {
          mode: "ai",
          respondent_data: {
            full_name: manualForm.value.nama || "Respondent",
            birth_year: birthYear,
            education: manualForm.value.pendidikan || null,
            address: manualForm.value.alamat || null
          },
          duration: totalDuration,
          status: "completed",
          extracted_data: richExtractedData
        }, token);
      } else {
        // Create new interview with respondent_data
        const currentYear = new Date().getFullYear();
        const birthYear = manualForm.value.usia ? currentYear - parseInt(manualForm.value.usia) : null;
        
        // Prepare rich extracted_data
        const richExtractedData = {};
        for (const [key, value] of Object.entries(manualForm.value)) {
             // Find if we have a transcript for this key in extractedAnswers
            const match = extractedAnswers.value.find(a => a.variable_name === key);
            if (match && match.transcript) {
                richExtractedData[key] = {
                    answer: value,
                    transcript: match.transcript
                };
            } else {
                richExtractedData[key] = value;
            }
        }
        
        const response = await api.createInterview({
          mode: "ai",
          respondent_data: {
            full_name: manualForm.value.nama || "Respondent",
            birth_year: birthYear,
            education: manualForm.value.pendidikan || null,
            address: manualForm.value.alamat || null
          },
          duration: totalDuration,
          extracted_data: richExtractedData
        }, token);
        
        currentInterviewId.value = response.data.id;
        
        // If audio exists, upload it
        if (audioBlob.value) {
          await api.uploadAudio(response.data.id, audioBlob.value, token);
        }
      }

      
      syncStatus.value = 'synced';
      
      interviewStore.clearInterviewTimer();
      router.push('/rekapitulasi');
      
    } catch (error) {
      console.error("⚠️ Gagal mengirim ke server:", error);
      syncStatus.value = 'error';
      
      await requestBackgroundSync();
      
      interviewStore.clearInterviewTimer();
      router.push('/rekapitulasi');
    }
  } else {
    // ===== JIKA OFFLINE: LANGSUNG KE REKAPITULASI =====
    console.log('📴 Offline mode: Data saved locally');
    await requestBackgroundSync();
    
    interviewStore.clearInterviewTimer();
    router.push('/rekapitulasi');
  }
}

// Function to cancel submission
function cancelSubmit() {
  showSubmitDialog.value = false;
}

// Function to clear form data AND reset AI session
async function handleClear() {
  if (confirm('Yakin ingin menghapus semua data dan memulai ulang wawancara?')) {
    // 1. Reset Local Form Data
    Object.keys(manualForm.value).forEach(key => manualForm.value[key] = "");
    
    // 2. Reset Audio State
    audioBlob.value = null;
    audioChunks.value = [];
    isRecording.value = false;
    if (timer.value) clearInterval(timer.value);
    durationInSeconds.value = 0;
    
    // 3. Reset AI/Extraction State
    extractedAnswers.value = [];
    processingProgress.value = 0;
    processingStatus.value = "Menunggu...";
    currentQuestion.value = null;
    currentQuestionIndex.value = 0;
    
    // 4. Reset Session (Key Step)
    disconnectWebSocket();
    currentInterviewId.value = null; // Clear ID so we know it's gone
    
    try {
        console.log("🔄 Starting fresh interview session...");
        await createNewInterview(); // Get NEW ID from Backend
        console.log("✅ New session started:", currentInterviewId.value);
        
        // 5. Reconnect WS with new ID
        connectWebSocket(); 
        
    } catch (e) {
        console.error("Failed to reset interview:", e);
        alert("Gagal memulai ulang sesi. Silakan refresh halaman.");
    }
  }
}

// Helper to map backend variable names to frontend keys
function mapVariableToKey(variableName) {
  if (!variableName) return null;
  const lower = variableName.toLowerCase().trim();
  
  // Direct match
  if (manualForm.value.hasOwnProperty(lower)) return lower;

  // Snake case normalization (e.g. "Tempat Lahir" -> "tempat_lahir")
  const snake = lower.replace(/\s+/g, '_');
  if (manualForm.value.hasOwnProperty(snake)) return snake;

  // Specific mappings
  const mappings = {
    'email': 'alamat_email',
    'phone': 'nomor_telepon',
    'hp': 'nomor_telepon',
    'handphone': 'nomor_telepon',
    'telepon': 'nomor_telepon',
    'pendidikan_terakhir': 'pendidikan',
    'nama_lengkap': 'nama',
    'alamat_lengkap': 'alamat',
    'hobi_kesukaan': 'hobi'
  };
  
  if (mappings[snake]) return mappings[snake];
  if (mappings[lower]) return mappings[lower];

  return null;
}

// Function to finish recording and process with AI
async function handleFinishAndProcess() {
  if (isRecording.value) {
    stopRecording();
  }
  
  if (!currentInterviewId.value) {
    alert("Belum ada interview ID.");
    return;
  }
  
  if (!confirm("Apakah Anda yakin ingin menyelesaikan dan memproses data dengan AI?")) {
    return;
  }
  
  isProcessing.value = true;
  processingStatus.value = "Memproses batch..."; // Feedback UI
  
  try {
    const token = authStore.userToken.value;
    
    // Call process-audio (Backend will use the stream file we saved)
    const response = await api.processAudio(currentInterviewId.value, token);
    const data = response.data;
    
    // Fill the form
    if (data.extracted_info) {
       Object.keys(data.extracted_info).forEach(rawKey => {
         const key = mapVariableToKey(rawKey);
         if (key) {
           // Special handling for Select/Options
           if (key === 'pendidikan') {
              // Ensure match option value exactly
              const eduOpts = ["SD", "SMP", "SMA", "D3", "S1", "S2", "S3", "Tidak Sekolah"];
              const rawVal = data.extracted_info[rawKey];
              
              if (rawVal) {
                  const val = rawVal.toUpperCase();
                  // Try direct or fuzzy match
                  const match = eduOpts.find(opt => opt.toUpperCase() === val || opt.toUpperCase() === val.replace(/\./g, ''));
                  if (match) {
                     manualForm.value[key] = match;
                  } else {
                     // Fallback: just set it, select might show empty if no match
                     manualForm.value[key] = rawVal;
                  }
              }
           } else {
              manualForm.value[key] = data.extracted_info[rawKey];
           }
         }
       });
    }
    
    alert("Proses AI Batch Selesai! Data telah terisi.");
    
  } catch (error) {
    console.error("Batch processing failed:", error);
    alert("Gagal memproses batch: " + (error.response?.data?.detail || error.message));
  } finally {
    isProcessing.value = false;
    processingStatus.value = "Menunggu...";
  }
}

// Helper function to format date
function formatDateToDDMMYYYY(isoDate) {
  if (!isoDate || !isoDate.includes('-')) return isoDate;
  const [yyyy, mm, dd] = isoDate.split('-');
  return `${dd.padStart(2, '0')}/${mm.padStart(2, '0')}/${yyyy}`;
}

// Event handler for date input blur
function handleDateBlur(e) {
  const val = e.target.value;
  if (val.match(/^\d{4}-\d{2}-\d{2}$/)) {
    manualForm.value.tanggal_lahir = formatDateToDDMMYYYY(val);
  }
}

// Event handler for input focus to trigger current question update
function handleInputFocus(key) {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    console.log('Sending set_question for:', key);
    ws.value.send(JSON.stringify({
      type: 'set_question',
      variable_name: key,
      interview_id: currentInterviewId.value
    }));
    
    // Optimistic UI update for current question (optional, but good for feedback)
    // We wait for backend 'current_question' message usually, but this acts fast.
  }
}

// ===== FUNGSI BARU: WEBSOCKET REAL-TIME EXTRACTION =====
// Function to connect to WebSocket
function connectWebSocket() {
  aiStatus.value = 'preparing'; // Set to preparing when connecting
  
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    console.log('WebSocket already connected');
    aiStatus.value = 'ready';
    return;
  }

  // Use relative path for WebSocket to leverage Vite proxy
  // If on HTTPS, use wss, otherwise ws
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/interview`;
  debugWsUrl.value = wsUrl; // Update debug info
  
  console.log('Connecting to WebSocket:', wsUrl);
  try {
      ws.value = new WebSocket(wsUrl);
  } catch (err) {
      lastWsError.value = "Init Error: " + err.message;
      return;
  }

  ws.value.onopen = () => {
    console.log('✅ WebSocket connected');
    wsConnected.value = true;
    lastWsError.value = "Connected"; // Clear error
    aiStatus.value = 'ready'; // Ready when connected
    
    // Send initialization message
    const initMessage = {
      type: 'start_interview',
      user_id: authStore.userId.value || null,
      interview_id: currentInterviewId.value || null
    };
    console.log('Sending WS init:', initMessage);
    ws.value.send(JSON.stringify(initMessage));
  };

  ws.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  ws.value.onerror = (error) => {
    console.error('❌ WebSocket error:', error);
    wsConnected.value = false;
    lastWsError.value = "WS Error event triggered (Check Console)";
    aiStatus.value = 'error'; // Error state
  };

  ws.value.onclose = () => {
    console.log('WebSocket disconnected');
    wsConnected.value = false;
    // Only set to error if we weren't expecting a close, or we could handle reconnect
    if (aiStatus.value !== 'ready') { 
        aiStatus.value = 'error'; 
    }
  };
}

// Function to handle incoming WebSocket messages
function handleWebSocketMessage(data) {
  console.log('📨 WebSocket message:', data);

  switch(data.type) {
    case 'current_question':
      currentQuestion.value = data;
      break;

    case 'speaker_detected':
      // Show speaker detection feedback
      console.log(`Speaker: ${data.speaker}, Confidence: ${data.confidence}`);
      if (data.speaker === 'respondent') {
        processingStatus.value = 'Mendengarkan Responden...';
      } else if (data.speaker === 'enumerator') {
        processingStatus.value = 'Mendeteksi Suara Enumerator (Diabaikan)';
      } else {
        processingStatus.value = 'Mendengarkan...';
      }
      break;

    case 'silence_detected':
      silenceDetected.value = true;
      processingStatus.value = 'Hening terdeteksi, memproses...';
      processingProgress.value = 0;
      break;

    case 'transcription_started':
      processingStatus.value = 'Mentranskripsi...';
      processingProgress.value = data.progress || 30;
      break;
      
    case 'extraction_started':
      processingStatus.value = 'Mengekstrak jawaban...';
      processingProgress.value = data.progress || 60;
      break;

    case 'saving_to_database':
      processingStatus.value = 'Menyimpan...';
      processingProgress.value = data.progress || 90;
      break;

    case 'answer_extracted':
      if (data.success) {
        // Add to extracted answers list
        extractedAnswers.value.push({
          question_id: data.question_id,
          question_text: data.question_text,
          transcript: data.transcript,
          extracted_answer: data.extracted_answer,
          confidence: data.confidence
        });

        // Show success notification (optional, maybe too noisy)
        // processingStatus.value = `Info diekstrak: ${data.variable_name}`;
        
        // Auto-fill form field using variable_name if available
        let matchingKey = null;

        if (data.variable_name) {
             const key = mapVariableToKey(data.variable_name);
             if (key) {
               console.log(`Auto-filling ${key} with: ${data.extracted_answer}`);
               
               // Special handling for Select/Options
               if (key === 'pendidikan') {
                  const eduOpts = ["SD", "SMP", "SMA", "D3", "S1", "S2", "S3", "Tidak Sekolah"];
                  const val = String(data.extracted_answer).toUpperCase();
                  const match = eduOpts.find(opt => opt.toUpperCase() === val || opt.toUpperCase() === val.replace(/\./g, ''));
                  if (match) {
                     manualForm.value[key] = match;
                  } else {
                     manualForm.value[key] = data.extracted_answer;
                  }
               } else {
                   manualForm.value[key] = data.extracted_answer;
               }
             }
        }

        // Reset indicators
        silenceDetected.value = false;
        processingProgress.value = 0;
        processingStatus.value = 'Menunggu jawaban...';
      }
      break;

    case 'question_progress':
      currentQuestionIndex.value = data.current_index;
      totalQuestions.value = data.total_questions;
      
      if (data.is_complete) {
        console.log('✅ Interview complete!');
        disconnectWebSocket();
        alert('Wawancara Selesai!');
      }
      break;

    case 'interview_complete':
      alert('Semua pertanyaan telah selesai!');
      disconnectWebSocket();
      break;

    case 'error':
      console.error('WebSocket error:', data.message);
      alert(`Error: ${data.message}`);
      break;

    case 'transcript_partial':
      liveTranscript.value = data.text;
      processingStatus.value = 'Mendengarkan...';
      break;

    case 'transcript_finalized':
      liveTranscript.value = ""; 
      console.log("Finalized:", data.text);
      break;
      
    case 'new_question':
       console.log("Next question recommended:", data);
       break;
  }
}

// Function to disconnect WebSocket
function disconnectWebSocket() {
  if (ws.value) {
    ws.value.close();
    ws.value = null;
    wsConnected.value = false;
    // realtimeMode.value = false; // Don't disable realtime mode on disconnect, try to reconnect or stay in mode
  }
}

// Function to send audio chunk via WebSocket
function sendAudioChunk(audioData) {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(audioData);
  }
}

// Helper function to get confidence score class
function getConfidenceClass(confidence) {
  if (confidence >= 0.8) return 'high';
  if (confidence >= 0.6) return 'medium';
  return 'low';
}

// Function to toggle realtime mode
function toggleRealtimeMode() {
  realtimeMode.value = !realtimeMode.value;
  
  if (realtimeMode.value) {
    connectWebSocket();
  } else {
    disconnectWebSocket();
  }
}


// ======================================================

// ===== FUNGSI BARU: PCM AUDIO RECORDING =====
const audioContext = ref(null);
const processor = ref(null);
const inputSource = ref(null);

// Function to handle microphone toggle
async function handleMic() {
  if (isRecording.value) {
    stopRecording();
  } else {
    await startRecording();
  }
}

// Function to start audio recording
async function startRecording() {
  try {
    // Check for Secure Context (HTTPS or localhost)
    if (!window.isSecureContext) {
      alert('Akses mikrofon diblokir karena koneksi tidak aman (HTTP). Harap akses website menggunakan HTTPS untuk mengizinkan perekaman audio.');
      return;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('Browser Anda tidak mendukung perekaman audio atu akses ditolak. Pastikan Anda menggunakan HTTPS dan memberikan izin akses mikrofon.');
      return;
    }

    processingStatus.value = 'Mendengarkan...';

    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        channelCount: 1,
        sampleRate: 16000
      } 
    });
    
    audioBlob.value = null;
    audioChunks.value = [];
    
    // Initialize AudioContext
    audioContext.value = new (window.AudioContext || window.webkitAudioContext)({
      sampleRate: 16000 // Try to Force 16kHz
    });
    
    const actualSampleRate = audioContext.value.sampleRate;
    console.log(`🎤 AudioContext initialized at ${actualSampleRate}Hz (Target: 16000Hz)`);

    if (audioContext.value.state === 'suspended') {
      await audioContext.value.resume();
    }

    inputSource.value = audioContext.value.createMediaStreamSource(stream);
    
    // Create ScriptProcessor
    // bufferSize 4096 is good for 44.1/48k. For 16k it's 256ms.
    // If rate is 48k, 4096 is ~85ms.
    processor.value = audioContext.value.createScriptProcessor(4096, 1, 1);
    
    processor.value.onaudioprocess = (e) => {
      if (!isRecording.value) return;
      
      let inputData = e.inputBuffer.getChannelData(0);
      
      // Downsample if needed
      if (actualSampleRate !== 16000) {
        inputData = downsampleBuffer(inputData, actualSampleRate, 16000);
      }
      
      // Apply Software Gain (Volume Boost)
      if (micGain.value > 1.0) {
         for (let i = 0; i < inputData.length; i++) {
            inputData[i] = inputData[i] * micGain.value;
         }
      }
      
      // Calculate RMS for Visualizer
      let sum = 0;
      for (let i = 0; i < inputData.length; i++) {
        sum += inputData[i] * inputData[i];
      }
      const rms = Math.sqrt(sum / inputData.length);
      
      // Update UI bar (scaled 0-100, assuming max RMS is approx 0.5 for normal speech)
      micVolume.value = Math.min(100, Math.round(rms * 200));
      
      // Log occasionally
      if (Math.random() < 0.05) {
         // console.log(`🎤 Mic Input RMS: ${rms.toFixed(4)}`);
      }

      // Convert float32 to int16 PCM
      const pcmData = convertFloat32ToInt16(inputData);

      
      // Send to WebSocket if connected
      if (realtimeMode.value && wsConnected.value) {
        sendAudioChunk(pcmData);
      }
    };
    
    inputSource.value.connect(processor.value);
    processor.value.connect(audioContext.value.destination);
    
    isRecording.value = true;
    durationInSeconds.value = 0;
    timer.value = setInterval(() => durationInSeconds.value++, 1000);
    
    console.log(`✅ Recording started. Outputting 16000Hz PCM.`);
    
  } catch (err) {
    console.error("❌ Gagal mengakses mikrofon:", err);
    alert('Gagal mengakses mikrofon: ' + err.message);
    processingStatus.value = 'Menunggu...';
  }
}

// Function to stop audio recording
function stopRecording() {
  if (!isRecording.value) return;
  
  // Stop processor and context
  if (processor.value) {
    processor.value.disconnect();
    processor.value = null;
  }
  
  if (inputSource.value) {
    inputSource.value.disconnect();
    inputSource.value = null;
  }
  
  if (audioContext.value) {
    audioContext.value.close();
    audioContext.value = null;
  }
  
  // Stop all tracks
  // Note: we need to keep reference to stream if we want to stop tracks properly
  // But AudioContext takes ownership mostly. 
  // Ideally we should store stream in a ref too.
  
  clearInterval(timer.value);
  isRecording.value = false;
  processingStatus.value = 'Memproses...';
  
  console.log("✅ Recording stopped");
}

// ===== AUDIO UTILS =====
// Helper function to downsample audio buffer
function downsampleBuffer(buffer, inputSampleRate, outputSampleRate) {
  if (outputSampleRate === inputSampleRate) {
    return buffer;
  }
  
  if (outputSampleRate > inputSampleRate) {
    // Upsampling not supported/recommended for this use case
    console.warn("Upsampling not supported");
    return buffer;
  }
  
  const sampleRateRatio = inputSampleRate / outputSampleRate;
  const newLength = Math.round(buffer.length / sampleRateRatio);
  const result = new Float32Array(newLength);
  
  let offsetResult = 0;
  let offsetBuffer = 0;
  
  while (offsetResult < result.length) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
    
    // Simple averaging (boxcar filter) for downsampling to prevent aliasing
    let accum = 0, count = 0;
    for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
      accum += buffer[i];
      count++;
    }
    
    result[offsetResult] = count > 0 ? accum / count : 0;
    
    offsetResult++;
    offsetBuffer = nextOffsetBuffer;
  }
  
  return result;
}

// Helper function to convert Float32 to Int16
function convertFloat32ToInt16(buffer) {
  let l = buffer.length;
  let buf = new Int16Array(l);
  while (l--) {
    // Clamp to [-1, 1]
    let s = Math.max(-1, Math.min(1, buffer[l]));
    // Scale to 16-bit integer range
    buf[l] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  return buf.buffer;
}

// ... inside startRecording ...
// We need to inject the logic there. Since I am replacing the utils section mostly, I will check where startRecording IS in relation to this.
// Wait, replace_file_content replaces a BLOCK. I need to replace startRecording AND the utils or do it in two steps.
// The user provided code shows convertFloat32ToInt16 is at the bottom. startRecording is above.
// I'll update startRecording to USE the downsampler, and add the downsampler function.

// Actually, looking at the previous view_file, startRecording is lines 824-905.

</script>

<style scoped>
/* Style tidak berubah */
.back-btn { align-self: flex-start; margin-bottom: 20px; background-color: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 20px; font-weight: 600; cursor: pointer; transition: background-color 0.2s; }
.back-btn:hover { background-color: #0056b3; }
.interview-page { width: 100%; max-width: 400px; margin: 0 auto; padding: 20px; background: #ffffff; min-height: 100vh; box-sizing: border-box; position: relative; padding-bottom: 120px; display: flex; flex-direction: column; }
.form-title { text-align: center; color: #1155cc; font-size: 18px; font-weight: 600; margin-bottom: 30px; margin-top: 0; }
.interview-form { display: flex; flex-direction: column; gap: 20px; }
.question-block { display: flex; flex-direction: column; gap: 8px; }
label { font-weight: 500; color: #333; font-size: 14px; }
.form-input { padding: 12px 16px; border: none; border-radius: 8px; background: #f5f5f5; font-size: 14px; outline: none; transition: background-color 0.2s; }
.form-input:focus { background: #eeeeee; }
.bottom-action-bar { position: fixed; left: 0; right: 0; bottom: 0; background: #ffffff; padding: 20px; display: flex; justify-content: center; align-items: center; gap: 20px; box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1); z-index: 1000; }
.action-btn { padding: 12px 24px; border: none; border-radius: 25px; font-weight: 600; font-size: 12px; cursor: pointer; min-width: 80px; transition: all 0.2s; }
.clear-btn { background: #dc3545; color: white; }
.clear-btn:hover { background: #c82333; }
.submit-btn { background: #007bff; color: white; }
.submit-btn:hover { background: #0056b3; }
.process-btn { background: #28a745; color: white; }
.process-btn:hover { background: #218838; }
.process-btn:disabled { background: #6c757d; cursor: not-allowed; }
.mic-container { display: flex; flex-direction: column; justify-content: center; align-items: center; }
.mic-button { width: 60px; height: 60px; background: #007bff; border-radius: 50%; display: flex; justify-content: center; align-items: center; cursor: pointer; transition: all 0.2s; border: none; outline: none; }
.mic-button:hover { background: #0056b3; transform: scale(1.05); }
.mic-button:active { transform: scale(0.95); }
.mic-button.recording { background: #dc3545; }
.mic-button.recording:hover { background: #c82333; }
.duration-display { margin-top: 8px; font-size: 14px; font-weight: 600; color: #333; font-family: 'monospace'; position: absolute; bottom: 100px; }
@media (max-width: 480px) { .interview-page { max-width: 100vw; padding: 16px; padding-bottom: 120px; } .form-title { font-size: 16px; margin-bottom: 25px; } .bottom-action-bar { gap: 10px; padding: 16px; } .action-btn { min-width: 60px; padding: 10px 12px; font-size: 11px; } .mic-button { width: 50px; height: 50px; } .mic-button svg { width: 20px; height: 20px; } .duration-display { bottom: 90px; } }
.dialog-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.5); display: flex; justify-content: center; align-items: center; z-index: 2000; }
.dialog-box { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); text-align: center; max-width: 350px; width: 90%; }
.dialog-box p { font-size: 1.1rem; margin-bottom: 25px; color: #333; }
.dialog-actions { display: flex; justify-content: center; gap: 20px; }
.dialog-btn { padding: 12px 25px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; transition: background-color 0.2s, transform 0.1s; }
.dialog-btn:hover { transform: translateY(-2px); }
.confirm-btn { background-color: #28a745; color: white; }
.confirm-btn:hover { background-color: #218838; }
.cancel-btn { background-color: #dc3545; color: white; }
.cancel-btn:hover { background-color: #c82333; }

/* ===== STYLE BARU UNTUK SYNC STATUS ===== */
.sync-status {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 25px;
  font-size: 14px;
  font-weight: 600;
  z-index: 3000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.sync-status.saving,
.sync-status.syncing,
.sync-status.processing {
  background: #ffc107;
  color: #000;
}

.sync-status.saved,
.sync-status.synced {
  background: #28a745;
  color: white;
}

.sync-status.error {
  background: #dc3545;
  color: white;
}
/* ======================================== */

/* ===== STYLES FOR REAL-TIME EXTRACTION ===== */
.realtime-section {
  margin-top: 20px;
  margin-bottom: 20px;
}

.realtime-btn {
  background: #6c757d;
  color: white;
  font-size: 11px;
  padding: 10px 16px;
}

.realtime-btn.active {
  background: #dc3545;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.current-question-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.question-number {
  font-size: 12px;
  font-weight: 600;
  opacity: 0.9;
}

.question-progress {
  font-size: 14px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 12px;
}

.question-text {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
  line-height: 1.5;
}

.silence-indicator {
  background: #fff3cd;
  border: 2px solid #ffc107;
  padding: 16px;
  border-radius: 10px;
  margin-bottom: 20px;
  text-align: center;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #ffc107;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.progress-bar-container {
  background: #e9ecef;
  border-radius: 10px;
  height: 8px;
  overflow: hidden;
  margin: 10px 0;
}

.progress-bar-fill {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  height: 100%;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: #666;
  font-weight: 600;
}

.interview-progress {
  background: white;
  padding: 16px;
  border-radius: 10px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

@keyframes blink-animation {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(0.98); }
  100% { opacity: 1; transform: scale(1); }
}

.ai-status-banner {
  margin-bottom: 20px;
  padding: 12px 20px;
  border-radius: 12px;
  font-weight: 600;
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

.ai-status-banner.preparing {
  background-color: #fff3cd;
  color: #856404;
  border-left: 5px solid #ffeb3b;
  animation: blink-animation 1.5s infinite ease-in-out;
}

.ai-status-banner.ready {
  background-color: #d4edda;
  color: #155724;
  border-left: 5px solid #28a745;
}

.ai-status-banner.error {
  background-color: #f8d7da;
  color: #721c24;
  border-left: 5px solid #dc3545;
}

/* Add blinking to the processing indicator as well */
.silence-indicator {
  animation: blink-animation 2s infinite ease-in-out;
}

.current-question-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border-left: 6px solid #6c5ce7;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.progress-percentage {
  color: #667eea;
}

.extracted-answers {
  margin-top: 20px;
}

.extracted-answers h3 {
  font-size: 16px;
  font-weight: 700;
  color: #333;
  margin-bottom: 16px;
}

.answer-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}

.answer-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.answer-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.answer-header h4 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin: 0;
  flex: 1;
}

.confidence-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 12px;
  color: white;
}

.confidence-badge.high {
  background: #28a745;
}

.confidence-badge.medium {
  background: #ffc107;
  color: #000;
}

.confidence-badge.low {
  background: #dc3545;
}

.answer-card .transcript,
.answer-card .answer {
  font-size: 13px;
  line-height: 1.6;
  margin: 8px 0;
  color: #555;
}

.answer-card .transcript strong,
.answer-card .answer strong {
  color: #333;
  font-weight: 600;
}

/* ===== FIELD SPINNER STYLES ===== */
.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.input-wrapper .form-input {
  width: 100%;
  padding-right: 40px; /* Make space for spinner */
}

.field-spinner {
  position: absolute;
  right: 10px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s ease;
}

.spinner-svg {
  width: 100%;
  height: 100%;
  transform-origin: center;
  animation: spin 2s linear infinite;
}

@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}
/* ================================ */
</style>