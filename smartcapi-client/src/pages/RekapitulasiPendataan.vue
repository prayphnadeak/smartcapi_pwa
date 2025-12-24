<template>
  <div class="page-container">
    <div class="header">
      <h1 class="title">Rekapitulasi Pendataan</h1>
      <div class="header-actions">
        <button class="add-btn" @click="goToInterview">
          <span>+</span> Tambah Data Wawancara
        </button>
        
        <div class="profile-section" @click="goToProfile" title="Lihat Profil">
          <button class="profile-icon-btn">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5ZM12 19.2C9.5 19.2 7.29 17.92 6 15.96C6.04 14.03 10 12.9 12 12.9C13.99 12.9 17.96 14.03 18 15.96C16.71 17.92 14.5 19.2 12 19.2Z"/>
            </svg>
          </button>
          <span class="profile-name">{{ authStore.userName.value }}</span>
        </div>
      </div>
    </div>

    <div class="tabs-container">
      <button
        :class="['tab-btn', { active: activeTab === 'ai' }]"
        @click="activeTab = 'ai'">
        Mode AI
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'manual' }]"
        @click="activeTab = 'manual'">
        Mode Manual
      </button>
    </div>

    <div v-if="activeTab === 'ai'">
      <RekapitulasiTabelAI
        :data="aiData"
        :getStatusClass="getStatusClass"
        :formatStatus="formatStatus"
        :playRecording="playRecording"

        :handleEdit="handleEdit"
        :handleDelete="handleDelete"

      />
    </div>
    <div v-else-if="activeTab === 'manual'">
      <RekapitulasiTabelManual
        :data="manualData"
        :getStatusClass="getStatusClass"
        :formatStatus="formatStatus"
        :handleEdit="handleEdit"
        :handleDelete="handleDelete"
      />
    </div>
    <!-- Audio Player Modal -->
    <div v-if="showAudioPlayer" class="modal-overlay" @click.self="closeAudioPlayer">
      <div class="audio-player-modal">
        <div class="player-header">
          <h3>🎵 Rekaman Wawancara</h3>
          <button class="close-btn" @click="closeAudioPlayer">✕</button>
        </div>
        
        <div class="player-info">
          <p class="user-info">{{ currentAudioItem?.respondent_name || 'Responden' }}</p>
        </div>

        <div class="player-controls">
          <!-- Timeline -->
          <div class="timeline-container">
            <input 
              type="range" 
              class="timeline" 
              min="0" 
              :max="audioDuration" 
              v-model="currentTime"
              @input="seekAudio"
              step="0.1"
            />
            <div class="timeline-progress" :style="{ width: timelineProgress + '%' }"></div>
          </div>

          <!-- Time Display -->
          <div class="time-display">
            <span class="current-time">{{ formatTime(currentTime) }}</span>
            <span class="duration">{{ formatTime(audioDuration) }}</span>
          </div>

          <!-- Control Buttons -->
          <div class="control-buttons">
            <button @click="rewind10" class="control-btn" title="Rewind 10s">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11.99 5V1l-5 5 5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6h-2c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
                <text x="9" y="16" font-size="8" fill="currentColor">10</text>
              </svg>
            </button>

            <button @click="togglePlayPause" class="control-btn play-pause-btn">
              <svg v-if="!isPlaying" width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
              <svg v-else width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
              </svg>
            </button>

            <button @click="forward10" class="control-btn" title="Forward 10s">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 5V1l5 5-5 5V7c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6h2c0 4.42-3.58 8-8 8s-8-3.58-8-8 3.58-8 8-8z"/>
                <text x="9" y="16" font-size="8" fill="currentColor">10</text>
              </svg>
            </button>

            <button @click="stopAudio" class="control-btn" title="Stop">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M6 6h12v12H6z"/>
              </svg>
            </button>
          </div>

          <!-- Volume Control -->
          <div class="volume-control">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>
            </svg>
            <input 
              type="range" 
              class="volume-slider" 
              min="0" 
              max="100" 
              v-model="volume"
              @input="changeVolume"
            />
            <span class="volume-value">{{ volume }}%</span>
          </div>

          <!-- Playback Speed -->
          <div class="speed-control">
            <label>Speed:</label>
            <select v-model="playbackSpeed" @change="changeSpeed" class="speed-select">
              <option value="0.5">0.5x</option>
              <option value="0.75">0.75x</option>
              <option value="1">1x</option>
              <option value="1.25">1.25x</option>
              <option value="1.5">1.5x</option>
              <option value="2">2x</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="edit-modal">
        <div class="modal-header">
          <h3>Edit Data Wawancara</h3>
          <button class="close-btn" @click="closeEditModal">✕</button>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="saveEdit" class="edit-form">
            <div v-for="q in questions" :key="q.key" class="form-group">
              <label :for="q.key">{{ q.label }}</label>
              
              <input 
                v-if="q.type !== 'select' && q.type !== 'textarea'"
                :type="q.type" 
                :id="q.key" 
                v-model="editForm[q.key]"
                class="form-input"
              />
              
              <select 
                v-else-if="q.type === 'select'"
                :id="q.key" 
                v-model="editForm[q.key]"
                class="form-input"
              >
                <option value="">Pilih {{ q.label }}</option>
                <option v-for="opt in q.options" :key="opt" :value="opt">{{ opt }}</option>
              </select>
              
              <textarea 
                v-else-if="q.type === 'textarea'"
                :id="q.key" 
                v-model="editForm[q.key]"
                class="form-input"
                rows="3"
              ></textarea>
            </div>
            
            <div class="modal-actions">
              <button type="button" class="cancel-btn" @click="closeEditModal">Batal</button>
              <button type="submit" class="save-btn" :disabled="isSaving">
                {{ isSaving ? 'Menyimpan...' : 'Simpan Perubahan' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>


  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import RekapitulasiTabelAI from '../components/Rekapitulasi/RekapitulasiTabelAI.vue';
import RekapitulasiTabelManual from '../components/Rekapitulasi/RekapitulasiTabelManual.vue';
import { useAuthStore } from '../store/auth';
import { useInterviewStore } from '../store/interview';
import { api } from '../services/api';

const router = useRouter();
const authStore = useAuthStore();
const interviewStore = useInterviewStore();
const interviewData = ref([]);
const activeTab = ref('ai');

// Audio Player State
const showAudioPlayer = ref(false);
const currentAudioItem = ref(null);
const audioElement = ref(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const audioDuration = ref(0);
const volume = ref(100);
const playbackSpeed = ref(1);
const currentAudioUrl = ref(null); // INFO: Keep track of blob URL to revoke it later

const API_BASE_URL = '/api/v1';

// Edit Modal State
const showEditModal = ref(false);
const editForm = ref({});
const currentEditId = ref(null);
const isSaving = ref(false);





// Defining questions for edit form
const questions = [
  { key: 'nama', label: 'Nama Lengkap', type: 'text' },
  { key: 'tempat_lahir', label: 'Tempat Lahir', type: 'text' },
  { key: 'tanggal_lahir', label: 'Tanggal Lahir', type: 'date' },
  { key: 'usia', label: 'Usia', type: 'number' },
  { key: 'pendidikan', label: 'Pendidikan Terakhir', type: 'select', options: ['SD', 'SMP', 'SMA', 'D3', 'S1', 'S2', 'S3', 'Tidak Sekolah'] },
  { key: 'alamat', label: 'Alamat Lengkap', type: 'textarea' },
  { key: 'pekerjaan', label: 'Pekerjaan', type: 'text' },
  { key: 'hobi', label: 'Hobi', type: 'text' },
  { key: 'nomor_telepon', label: 'Nomor Telepon', type: 'tel' },
  { key: 'alamat_email', label: 'Alamat Email', type: 'email' },
];

const aiData = computed(() => {
  return interviewData.value.filter(item => {
    const mode = (item.mode || '').toLowerCase().trim();
    return mode === 'ai' || mode === 'dengan asistensi ai';
  });
});

const manualData = computed(() => {
  return interviewData.value.filter(item => {
    const mode = (item.mode || '').toLowerCase().trim();
    return mode === 'manual' || mode === 'tanpa asistensi ai';
  });
});

const timelineProgress = computed(() => {
  if (audioDuration.value === 0) return 0;
  return (currentTime.value / audioDuration.value) * 100;
});

// Function to fetch interview data from the API
async function fetchInterviews() {
  if (!authStore.isAuthenticated.value) {
    alert('Anda harus login untuk melihat rekapitulasi.');
    router.push('/');
    return;
  }
  
  // Show respondents' name on Rekapitulasi Pendataan page
  const token = authStore.userToken.value;
  try {
    const response = await api.getInterviews(token);
    interviewData.value = response.data;
    
    // Auto-switch tab if AI data is empty but manual data exists
    if (aiData.value.length === 0 && manualData.value.length > 0) {
        activeTab.value = 'manual';
    }
  } catch (error) {
    console.error('Error fetching interviews:', error);
  }
}

onMounted(() => {
  fetchInterviews();
  
  // Refresh data when window regains focus (e.g. returning from Database tab)
  window.addEventListener('focus', fetchInterviews);
});

onUnmounted(() => {
  window.removeEventListener('focus', fetchInterviews);
  
  if (audioElement.value) {
    audioElement.value.pause();
    audioElement.value = null;
  }
  if (currentAudioUrl.value) {
    URL.revokeObjectURL(currentAudioUrl.value);
    currentAudioUrl.value = null;
  }
});

// Function to play recording for a specific interview item
async function playRecording(item) {
  if (!item.has_recording && !item.recording_path) {
    alert("Responden ini tidak memiliki data rekaman.");
    return;
  }

  try {
      const token = authStore.userToken.value;
      if (!token) {
          alert("Anda harus login untuk memutar audio.");
          return;
      }

      const response = await api.getInterviewAudio(item.id, token);
      
      // Revoke previous URL if exists
      if (currentAudioUrl.value) {
          URL.revokeObjectURL(currentAudioUrl.value);
      }
      
      const blob = new Blob([response.data], { type: 'audio/wav' });
      currentAudioUrl.value = URL.createObjectURL(blob);
      
      currentAudioItem.value = item;
      showAudioPlayer.value = true;
      
      if (audioElement.value) {
        audioElement.value.pause();
      }
      
      audioElement.value = new Audio(currentAudioUrl.value);
      audioElement.value.volume = volume.value / 100;
      audioElement.value.playbackRate = playbackSpeed.value;
      
      audioElement.value.addEventListener('loadedmetadata', () => {
        audioDuration.value = audioElement.value.duration;
      });
      
      audioElement.value.addEventListener('timeupdate', () => {
        currentTime.value = audioElement.value.currentTime;
      });
      
      audioElement.value.addEventListener('ended', () => {
        isPlaying.value = false;
        currentTime.value = 0;
      });
      
      audioElement.value.play().then(() => {
        isPlaying.value = true;
      }).catch(err => {
        console.error('Error playing audio:', err);
        alert('Gagal memutar audio. Format audio mungkin tidak didukung browser.');
      });

  } catch (error) {
      console.error("Failed to fetch audio:", error);
      alert("Gagal memuat audio. Pastikan file ada dan Anda memiliki akses.");
  }
}

// Function to close the audio player modal
function closeAudioPlayer() {
  if (audioElement.value) {
    audioElement.value.pause();
    audioElement.value = null;
  }
  if (currentAudioUrl.value) {
    URL.revokeObjectURL(currentAudioUrl.value);
    currentAudioUrl.value = null;
  }
  showAudioPlayer.value = false;
  currentAudioItem.value = null;
  isPlaying.value = false;
  currentTime.value = 0;
  audioDuration.value = 0;
}

// Function to toggle between play and pause states
function togglePlayPause() {
  if (!audioElement.value) return;
  if (isPlaying.value) {
    audioElement.value.pause();
    isPlaying.value = false;
  } else {
    audioElement.value.play();
    isPlaying.value = true;
  }
}

// Function to stop audio playback
function stopAudio() {
  if (!audioElement.value) return;
  audioElement.value.pause();
  audioElement.value.currentTime = 0;
  currentTime.value = 0;
  isPlaying.value = false;
}

// Function to seek audio position based on slider input
function seekAudio() {
  if (!audioElement.value) return;
  audioElement.value.currentTime = currentTime.value;
}

// Function to rewind audio by 10 seconds
function rewind10() {
  if (!audioElement.value) return;
  audioElement.value.currentTime = Math.max(0, audioElement.value.currentTime - 10);
}

// Function to forward audio by 10 seconds
function forward10() {
  if (!audioElement.value) return;
  audioElement.value.currentTime = Math.min(audioDuration.value, audioElement.value.currentTime + 10);
}

// Function to change audio volume
function changeVolume() {
  if (!audioElement.value) return;
  audioElement.value.volume = volume.value / 100;
}

// Function to change playback speed
function changeSpeed() {
  if (!audioElement.value) return;
  audioElement.value.playbackRate = playbackSpeed.value;
}

// Helper function to format seconds into MM:SS
function formatTime(seconds) {
  if (isNaN(seconds) || seconds === 0) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Helper function to determine status badge class
function getStatusClass(status) {
  if (status === 'Submitted' || status === 'completed') return 'status-badge status-submitted';
  if (status === 'Pending' || status === 'pending' || status === 'active') return 'status-badge status-pending';
  return 'status-badge status-no-data';
}

// Helper function to format status text
function formatStatus(status) {
  if (!status) return '-';
  const s = status.toLowerCase();
  if (s === 'completed') return 'Selesai';
  if (s === 'active') return 'Aktif';
  return status;
}

// Function to handle edit button click and fetch details
async function handleEdit(item) {
  try {
    const response = await axios.get(`${API_BASE_URL}/interviews/${item.id}`, {
      headers: { 'Authorization': `Bearer ${authStore.userToken.value}` }
    });
    const data = response.data;
    
    currentEditId.value = item.id;
    editForm.value = {};
    
    if (data.extracted_answers && data.extracted_answers.length > 0) {
      data.extracted_answers.forEach(answer => {
        if (answer.question && answer.question.variable_name) {
          editForm.value[answer.question.variable_name] = answer.answer_text;
        }
      });
    }
    
    if (data.respondent) {
      if (!editForm.value.nama) editForm.value.nama = data.respondent.full_name;
      if (!editForm.value.pendidikan) editForm.value.pendidikan = data.respondent.education;
      if (!editForm.value.alamat) editForm.value.alamat = data.respondent.address;
      
      if (!editForm.value.usia && data.respondent.birth_year) {
         const currentYear = new Date().getFullYear();
         editForm.value.usia = currentYear - data.respondent.birth_year;
      }
    }
    
    showEditModal.value = true;
    
  } catch (error) {
    console.error("Failed to fetch interview details:", error);
    alert("Gagal mengambil detail data.");
  }
}

// Function to save edited interview data
async function saveEdit() {
  if (!currentEditId.value) return;
  
  isSaving.value = true;
  try {
    let birthYear = null;
    const currentYear = new Date().getFullYear();
    if (editForm.value.tanggal_lahir) {
      birthYear = new Date(editForm.value.tanggal_lahir).getFullYear();
    } else if (editForm.value.usia) {
      birthYear = currentYear - parseInt(editForm.value.usia);
    }

    const payload = {
      respondent_data: {
        full_name: editForm.value.nama,
        birth_year: birthYear,
        education: editForm.value.pendidikan,
        address: editForm.value.alamat
      },
      extracted_data: editForm.value
    };

    await axios.put(`${API_BASE_URL}/interviews/${currentEditId.value}`, payload, {
      headers: { 'Authorization': `Bearer ${authStore.userToken.value}` }
    });
    
    alert('Data berhasil diperbarui.');
    showEditModal.value = false;
    fetchInterviews();
    
  } catch (error) {
    console.error("Failed to update interview:", error);
    alert("Gagal menyimpan perubahan.");
  } finally {
    isSaving.value = false;
  }
}

// Function to close the edit modal
function closeEditModal() {
  showEditModal.value = false;
  editForm.value = {};
  currentEditId.value = null;
}

// Function to handle delete interview data
async function handleDelete(item) {
  if (confirm(`Yakin ingin menghapus data responden "${item.respondent_name}"?`)) {
    try {
      await axios.delete(`${API_BASE_URL}/interviews/${item.id}`, {
         headers: { 'Authorization': `Bearer ${authStore.userToken.value}` }
      });
      alert('Data berhasil dihapus.');
      fetchInterviews();
    } catch (error) {
      console.error("Gagal menghapus data:", error);
      alert("Gagal menghapus data.");
    }
  }
}

// Function to navigate to interview creation page
function goToInterview() {
  if (!authStore.isAuthenticated.value) {
    alert('Anda harus login untuk menambah data.');
    router.push('/login');
    return;
  }
  router.push('/select-mode');
}

// Function to navigate to user profile
function goToProfile() {
  if (!authStore.isAuthenticated.value) {
    alert('Anda harus login untuk melihat profil.');
    router.push('/login');
    return;
  }
  router.push('/profile');
}


</script>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.profile-section {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 20px;
  transition: background-color 0.2s;
}
.profile-section:hover {
  background-color: #f0f0f0;
}
.profile-name {
  font-weight: 600;
  color: #333;
  font-size: 15px;
}
.profile-icon-btn {
  background: none;
  border: none;
  color: #1976d2;
  padding: 5px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.profile-icon-btn svg {
  width: 28px;
  height: 28px;
}
.page-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 2rem;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  border-bottom: 1px solid #eee;
  padding-bottom: 1rem;
}
.title {
  color: #1976d2;
  font-size: 1.8rem;
}
.add-btn {
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 20px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}
.tab-btn {
  padding: 10px 20px;
  font-size: 16px;
  font-weight: 600;
  border: none;
  background-color: transparent;
  cursor: pointer;
  color: #888;
  border-bottom: 3px solid transparent;
  transition: all 0.2s ease-in-out;
}
.tab-btn:hover {
  color: #333;
}
.tab-btn.active {
  color: #1976d2;
  border-bottom-color: #1976d2;
}

/* Audio Player Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.audio-player-modal {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 30px;
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  color: white;
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.player-header h3 {
  margin: 0;
  font-size: 1.5rem;
  color: white;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 24px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.player-info {
  text-align: center;
  margin-bottom: 25px;
}

.user-info {
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
}

.player-controls {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.timeline-container {
  position: relative;
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
  cursor: pointer;
}

/* Transcript QA Styles */
.qa-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
    padding: 10px;
}

.qa-item {
    display: flex;
    flex-direction: column;
    gap: 5px;
    border-bottom: 1px solid #eee;
    padding-bottom: 15px;
}

.qa-item:last-child {
    border-bottom: none;
}

.enumerator-box, .respondent-box {
    display: flex;
    gap: 8px;
    line-height: 1.5;
}

.enumerator-box {
    color: #1976d2;
    font-weight: 500;
}

.respondent-box {
    color: #333;
    padding-left: 20px;
}

.role-label {
    font-weight: bold;
    min-width: 20px;
}

.text {
    flex: 1;
}

.timeline {
  position: absolute;
  top: -7px;
  left: 0;
  width: 100%;
  height: 20px;
  opacity: 0;
  cursor: pointer;
  z-index: 2;
}

.timeline-progress {
  height: 100%;
  background: #fff;
  border-radius: 3px;
  position: relative;
}

.timeline-progress::after {
  content: '';
  position: absolute;
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 12px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.time-display {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.9);
}

.control-buttons {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin: 10px 0;
}

.control-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.control-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.play-pause-btn {
  background: white;
  color: #667eea;
  width: 50px;
  height: 50px;
}

.volume-control {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.8);
}

.volume-slider {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  appearance: none;
  cursor: pointer;
}

.volume-slider::-webkit-slider-thumb {
  appearance: none;
  width: 12px;
  height: 12px;
  background: white;
  border-radius: 50%;
  cursor: pointer;
}

.volume-value {
  font-size: 0.8rem;
  width: 35px;
  text-align: right;
}

.speed-control {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

.speed-select {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
}

.speed-select option {
  background: #667eea;
  color: white;
}

/* Edit Modal Styles */
.edit-modal {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.modal-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #666;
  cursor: pointer;
}

.modal-body {
  overflow-y: auto;
  flex: 1;
  padding-right: 5px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #555;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-input:focus {
  outline: none;
  border-color: #1976d2;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.cancel-btn {
  padding: 8px 16px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  color: #666;
}

.save-btn {
  padding: 8px 16px;
  background: #1976d2;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: white;
}

.save-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* Transcript Modal Styles */
.transcript-modal {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

.transcript-content {
  white-space: pre-wrap;
  line-height: 1.6;
  color: #444;
  font-size: 1rem;
  font-family: 'Courier New', Courier, monospace;
}

.loading-spinner {
  text-align: center;
  padding: 20px;
  color: #666;
  font-style: italic;
}

/* ============================================
   PORTRAIT / MOBILE RESPONSIVE STYLES
   ============================================ */
@media screen and (max-width: 768px) {
  .page-container {
    margin: 0.5rem;
    padding: 1rem;
    border-radius: 0;
  }
  
  .header {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .title {
    font-size: 1.4rem;
    text-align: center;
    margin-bottom: 0;
    order: 2; /* Title in middle */
  }
  
  /* Use display: contents to flatten header-actions, 
     so its children become direct flex items of .header */
  .header-actions {
    display: contents;
  }
  
  .add-btn {
    width: 100%;
    justify-content: center;
    border-radius: 8px;
    padding: 14px 20px;
    font-size: 15px;
    order: 3; /* Button at bottom */
  }
  
  .profile-section {
    justify-content: center;
    order: 1; /* Profile at top */
  }
  
  .tabs-container {
    display: flex;
    justify-content: center;
  }
  
  .tab-btn {
    flex: 1;
    text-align: center;
    padding: 12px 10px;
    font-size: 14px;
  }
}

/* Extra small screens (phones in portrait) */
@media screen and (max-width: 480px) {
  .page-container {
    margin: 0;
    padding: 0.75rem;
  }
  
  .title {
    font-size: 1.2rem;
  }
  
  .add-btn {
    padding: 12px 16px;
    font-size: 14px;
  }
  
  .profile-name {
    font-size: 13px;
  }
}
</style>