<template>
  <div>
    <div class="container interview-page">
      <button class="back-btn" @click="goBack">&lt;&lt; Kembali</button>

      <div class="form-title">Wawancara tanpa Asistensi AI</div>

      <form @submit.prevent="openSubmitDialog" class="interview-form">
        <div v-for="q in questions" :key="q.key" class="question-block">
          <label :for="q.key">{{ q.label }}</label>
          <select
            v-if="q.type === 'select'"
            :id="q.key"
            v-model="manualForm[q.key]"
            class="form-input"
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
          />
        </div>
      </form>

      <div class="bottom-action-bar">
        <button type="button" class="action-btn clear-btn" @click="handleClear">
          CLEAR DATA
        </button>
        <div class="duration-display">{{ displayedDuration }}</div>
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
        <span v-if="syncStatus === 'saving'">💾 Menyimpan data...</span>
        <span v-if="syncStatus === 'saved'">✅ Data tersimpan lokal</span>
        <span v-if="syncStatus === 'syncing'">🔄 Mengirim data...</span>
        <span v-if="syncStatus === 'synced'">✅ Data berhasil dikirim</span>
        <span v-if="syncStatus === 'error'">⚠️ Gagal mengirim (akan coba lagi)</span>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useInterviewStore } from '../store/interview';
import { useAuthStore } from '../store/auth';
import { api } from '../services/api';
import { generateUUID } from '../utils/uuid';

const router = useRouter();
const route = useRoute();
const interviewStore = useInterviewStore();
const authStore = useAuthStore();

const displayedDuration = ref('00:00');
let timerInterval = null;

// ===== STATE BARU UNTUK OFFLINE-FIRST =====
const syncStatus = ref(''); // saving, saved, syncing, synced, error
const DB_NAME = 'smartcapi_local';
const STORE_NAME = 'transcripts'; // Menggunakan store yang sama dengan Interview.vue
// ===========================================

const questions = [
  { key: 'nama', label: 'Nama Lengkap' },
  { key: 'tempat_lahir', label: 'Tempat Lahir' },
  { key: 'tanggal_lahir', label: 'Tanggal Lahir', type: 'date' },
  { key: 'usia', label: 'Usia', type: 'number' },
  { 
    key: 'pendidikan', 
    label: 'Pendidikan Terakhir', 
    type: 'select', 
    options: [
      "Tidak/Belum Bersekolah",
      "SD",
      "SMP",
      "SMA",
      "D3",
      "S1",
      "S2",
      "S3"
    ] 
  },
  { key: 'alamat', label: 'Alamat Lengkap' },
  { key: 'pekerjaan', label: 'Pekerjaan' },
  { key: 'hobi', label: 'Hobi' },
  { key: 'nomor_telepon', label: 'Nomor Telepon' },
  { key: 'alamat_email', label: 'Alamat Email', type: 'email' },
];

const manualForm = ref(Object.fromEntries(questions.map(q => [q.key, ""])));
const showSubmitDialog = ref(false);
const isEditMode = ref(false);
const currentInterviewId = ref(null);

onMounted(() => {
  timerInterval = setInterval(() => {
    const startTime = interviewStore.interviewStartTime;
    if (startTime > 0) {
      const now = Date.now();
      const elapsedSeconds = Math.round((now - startTime) / 1000);
      const minutes = Math.floor(elapsedSeconds / 60);
      const seconds = elapsedSeconds % 60;
      displayedDuration.value = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
  }, 1000);

  if (route.query.edit) {
    isEditMode.value = true;
    currentInterviewId.value = route.query.edit;
    fetchInterviewData(currentInterviewId.value);
  }
});

onUnmounted(() => {
  clearInterval(timerInterval);
});

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

  } catch (error) {
    console.error("Failed to fetch interview", error);
    alert("Gagal mengambil data wawancara.");
  }
}

watch(() => manualForm.value.tanggal_lahir, (newDate) => {
  if (newDate) {
    const birthDate = new Date(newDate);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDifference = today.getMonth() - birthDate.getMonth();
    if (monthDifference < 0 || (monthDifference === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    manualForm.value.usia = age >= 0 ? age : '';
  } else {
    manualForm.value.usia = '';
  }
});

// Function to navigate back to rekapitulasi
function goBack() {
  router.push('/rekapitulasi');
}

// Function to open submission confirmation dialog
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
      }
    };
  });
}

// ===== FUNGSI BARU: SIMPAN KE INDEXEDDB =====
// Function to save interview data to IndexedDB
async function saveToIndexedDB(interviewData) {
  try {
    syncStatus.value = 'saving';
    const db = await initDB();
    
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      
      const record = {
        ...interviewData,
        uuid: generateUUID(),
        sync_status: 'pending',
        timestamp: new Date().toISOString(),
        last_modified: new Date().toISOString()
      };
      
      const request = store.put(record);
      
      request.onsuccess = () => {
        syncStatus.value = 'saved';
        console.log('✅ Data saved to IndexedDB:', record.uuid);
        setTimeout(() => syncStatus.value = '', 3000);
        resolve(record);
      };
      
      request.onerror = () => {
        syncStatus.value = 'error';
        console.error('❌ Failed to save to IndexedDB:', request.error);
        reject(request.error);
      };
    });
  } catch (error) {
    syncStatus.value = 'error';
    console.error('❌ IndexedDB error:', error);
    throw error;
  }
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
  let durationInSeconds = 0;
  if (startTime > 0) {
    const endTime = Date.now();
    durationInSeconds = Math.round((endTime - startTime) / 1000);
  }

  // Calculate birth year from age or date
  const currentYear = new Date().getFullYear();
  let birthYear = null;
  
  if (manualForm.value.tanggal_lahir) {
    birthYear = new Date(manualForm.value.tanggal_lahir).getFullYear();
  } else if (manualForm.value.usia) {
    birthYear = currentYear - parseInt(manualForm.value.usia);
  }
  
  const submissionData = {
    mode: 'manual',
    respondent_data: {
      full_name: manualForm.value.nama || "Respondent",
      birth_year: birthYear,
      education: manualForm.value.pendidikan || null,
      address: manualForm.value.alamat || null
    },
    duration: durationInSeconds,
    extracted_data: JSON.parse(JSON.stringify(manualForm.value))  // Backend will handle this later
  };

  // Deep clone submissionData to ensure no Proxy objects are passed to IndexedDB
  const plainSubmissionData = JSON.parse(JSON.stringify(submissionData));

  // ===== STEP 1: SIMPAN KE INDEXEDDB DULU (OFFLINE-FIRST) =====
  try {
    const savedRecord = await saveToIndexedDB(plainSubmissionData);
    console.log('💾 Data saved locally with UUID:', savedRecord.uuid);
  } catch (error) {
    console.error('❌ Failed to save locally:', error);
    alert('Gagal menyimpan data lokal. Silakan coba lagi.');
    return;
  }

  // ===== STEP 2: KIRIM KE SERVER (JIKA ONLINE) =====
  if (navigator.onLine) {
    try {
      syncStatus.value = 'syncing';
      const token = authStore.userToken.value;
      
      if (isEditMode.value) {
          await api.updateInterview(currentInterviewId.value, submissionData, token);
      } else {
          await api.createInterview(submissionData, token);
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

// Function to handle form submission
function handleSubmit() {
  openSubmitDialog();
}

// Function to clear form data
function handleClear() {
  if (confirm('Yakin ingin menghapus semua data?')) {
    for (const key in manualForm.value) {
      manualForm.value[key] = "";
    }
  }
}
</script>

<style scoped>
/* Semua style dari Kode B2 dipertahankan */
.back-btn {
  align-self: flex-start;
  margin-bottom: 20px;
  background-color: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}
.back-btn:hover {
  background-color: #0056b3;
}

.interview-page {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
  background: #ffffff;
  min-height: 100vh;
  box-sizing: border-box;
  position: relative;
  padding-bottom: 120px;
  display: flex;
  flex-direction: column;
}

.form-title {
  text-align: center;
  color: #1155cc;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 30px;
  margin-top: 0;
}

.interview-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.question-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.form-input {
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  background: #f5f5f5;
  font-size: 14px;
  outline: none;
  transition: background-color 0.2s;
}

.form-input:focus {
  background: #eeeeee;
}

.bottom-action-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background: #ffffff;
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 60px;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.action-btn {
  padding: 12px 32px;
  border: none;
  border-radius: 25px;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  min-width: 120px;
  transition: all 0.2s;
}

.clear-btn {
  background: #dc3545;
  color: white;
}

.clear-btn:hover {
  background: #c82333;
}

.submit-btn {
  background: #007bff;
  color: white;
}

.submit-btn:hover {
  background: #0056b3;
}

.duration-display {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  min-width: 60px;
  text-align: center;
}

@media (max-width: 480px) {
  .interview-page {
    max-width: 100vw;
    padding: 16px;
    padding-bottom: 120px;
  }

  .form-title {
    font-size: 16px;
    margin-bottom: 25px;
  }

  .bottom-action-bar {
    gap: 40px;
    padding: 16px;
  }

  .action-btn {
    min-width: 100px;
    padding: 10px 24px;
    font-size: 11px;
  }
}

@media (max-width: 768px) and (orientation: landscape) {
  .interview-page {
    padding-bottom: 100px;
  }

  .bottom-action-bar {
    padding: 12px 20px;
  }
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.dialog-box {
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  text-align: center;
  max-width: 350px;
  width: 90%;
}

.dialog-box p {
  font-size: 1.1rem;
  margin-bottom: 25px;
  color: #333;
}

.dialog-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.dialog-btn {
  padding: 12px 25px;
  border: none;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
}

.dialog-btn:hover {
  transform: translateY(-2px);
}

.confirm-btn {
  background-color: #28a745;
  color: white;
}

.confirm-btn:hover {
  background-color: #218838;
}

.cancel-btn {
  background-color: #dc3545;
  color: white;
}

.cancel-btn:hover {
  background-color: #c82333;
}

/* Sync Status Styles */
.sync-status {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 10px 15px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  z-index: 3000;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
  animation: slideIn 0.3s ease-out;
}

.sync-status.saving { background: #fff3cd; color: #856404; }
.sync-status.saved { background: #d4edda; color: #155724; }
.sync-status.syncing { background: #cce5ff; color: #004085; }
.sync-status.synced { background: #d4edda; color: #155724; }
.sync-status.error { background: #f8d7da; color: #721c24; }

@keyframes slideIn {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>