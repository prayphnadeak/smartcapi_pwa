<template>
  <div class="page-container">
    <div class="header">
      <h1 class="title">Database Wawancara</h1>
      <div class="header-actions">
        <div class="profile-section" @click="goToProfile" title="Lihat Profil">
          <button class="profile-icon-btn">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5ZM12 19.2C9.5 19.2 7.29 17.92 6 15.96C6.04 14.03 10 12.9 12 12.9C13.99 12.9 17.96 14.03 18 15.96C16.71 17.92 14.5 19.2 12 19.2Z"/>
            </svg>
          </button>
          <span class="profile-name">{{ currentUser?.name || 'Admin' }}</span>
        </div>
        <button class="export-btn" @click="exportCSV" title="Export CSV">Export CSV</button>
        <button class="clear-cache-btn" @click="clearCache" title="Hapus Cache Aplikasi">Clear Cache</button>

      </div>
    </div>

    <div v-if="accessDenied" class="access-denied">
      <p>⚠️ Anda tidak berhak mengakses halaman ini.</p>
    </div>

    <div v-else class="table-container">
      <table class="rekap-table">
        <thead>
          <tr>
            <th>No</th>
            <th>Mode Pendataan</th>
            <th>Nama</th>
            <th>Alamat</th>
            <th>Tempat Lahir</th>
            <th>Tanggal Lahir</th>
            <th>Usia</th>
            <th>Pendidikan</th>
            <th>Pekerjaan</th>
            <th>Hobi</th>
            <th>Nomor Telepon</th>
            <th>Alamat Email</th>
            <th>Enumerator</th>
            <th>Rekaman Wawancara</th>
            <th>Durasi Wawancara (detik)</th>
            <th>Tanggal Pendataan</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in rows" :key="row.id">
            <td data-label="No" class="no-col">{{ idx + 1 }}</td>
            <td data-label="Mode">{{ row.mode }}</td>
            <td data-label="Nama">{{ row.respondent?.full_name || row.respondent_name || '-' }}</td>
            <td data-label="Alamat">{{ row.respondent?.address || '-' }}</td>
            <td data-label="Tempat Lahir">{{ row.extracted_data?.['tempat_lahir'] || '-' }}</td>
            <td data-label="Tanggal Lahir">{{ row.extracted_data?.['tanggal_lahir'] || row.respondent?.birth_year || '-' }}</td>
            <td data-label="Usia">{{ row.extracted_data?.['usia'] || calculateAge(row.respondent?.birth_year) }}</td>
            <td data-label="Pendidikan">{{ row.extracted_data?.['pendidikan'] || row.respondent?.education || '-' }}</td>
            <td data-label="Pekerjaan">{{ row.extracted_data?.['pekerjaan'] || '-' }}</td>
            <td data-label="Hobi">{{ row.extracted_data?.['hobi'] || '-' }}</td>
            <td data-label="Nomor Telepon">{{ row.extracted_data?.['nomor_telepon'] || '-' }}</td>
            <td data-label="Alamat Email">{{ row.extracted_data?.['alamat_email'] || '-' }}</td>
            <td data-label="Enumerator">{{ row.enumerator_id }}</td>
            <td data-label="Rekaman" class="rekaman-col">
              <div v-if="row.has_recording" class="audio-controls">
                <button 
                  @click="playRecording(row)" 
                  class="audio-btn play-btn"
                  title="Play Audio"
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" class="audio-icon">
                    <path d="M8 5v14l11-7z"/>
                  </svg>
                </button>
              </div>
              <div v-else class="no-data">-</div>
            </td>
            <td data-label="Durasi Wawancara (detik)">{{ row.duration || 0 }}</td>
            <td data-label="Tanggal Pendataan">{{ formatDate(row.created_at) }}</td>
            <td data-label="Action" class="action-col">
              <button class="action-btn edit-btn" @click="onEdit(row)">Edit</button>
              <button class="action-btn delete-btn" @click="onDelete(row)">Delete</button>
              <button 
                class="action-btn intv-mfcc-btn" 
                @click="exportInterviewMfcc(row)" 
                :disabled="!row.has_recording"
                :title="(!row.has_recording) ? 'No recording available' : 'Export Interview MFCC'"
                :class="{ 'disabled': !row.has_recording }"
              >
                Intv MFCC
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Audio Player Modal -->
    <div v-if="showAudioPlayer" class="modal-overlay" @click.self="closeAudioPlayer">
      <div class="audio-player-modal">
        <div class="player-header">
          <h3>🎵 Rekaman Wawancara</h3>
          <button class="close-btn" @click="closeAudioPlayer">✕</button>
        </div>
        
        <div class="player-info">
          <p class="user-info">{{ currentAudioItem?.respondent?.full_name || currentAudioItem?.respondent_name || 'Responden' }}</p>
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
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store/auth';
import { api } from '../services/api';

const router = useRouter();
const authStore = useAuthStore();
const accessDenied = ref(false);
const rows = ref([]);
const currentUser = ref(null);

// Audio Player State
const showAudioPlayer = ref(false);
const currentAudioItem = ref(null);
const audioElement = ref(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const audioDuration = ref(0);
const volume = ref(100);
const playbackSpeed = ref(1);
const currentAudioUrl = ref(null);

const API_BASE_URL = '/api/v1';

const timelineProgress = computed(() => {
  if (audioDuration.value === 0) return 0;
  return (currentTime.value / audioDuration.value) * 100;
});

onMounted(async () => {
  loadData();
});

onUnmounted(() => {
  if (audioElement.value) {
    audioElement.value.pause();
    audioElement.value = null;
  }
  if (currentAudioUrl.value) {
    URL.revokeObjectURL(currentAudioUrl.value);
    currentAudioUrl.value = null;
  }
});

// Function to fetch interview data from API
async function loadData() {
  try {
    const token = authStore.userToken.value;
    if (!token) {
        router.push('/');
        return;
    }
    
    const response = await api.getInterviews(token);
    rows.value = response.data;
    
  } catch (error) {
    console.error("Failed to fetch data:", error);
    if (error.response && error.response.status === 403) {
        accessDenied.value = true;
    }
  }
}

// Function to calculate age from birth year
function calculateAge(birthYear) {
    if (!birthYear) return '-';
    const currentYear = new Date().getFullYear();
    return currentYear - birthYear;
}

// Helper function to format date string
function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('id-ID');
}

// Function to play the audio recording
async function playRecording(item) {
  if (!item.has_recording) {
    alert("Responden ini tidak memiliki data rekaman.");
    return;
  }
  
  try {
      const token = authStore.userToken.value;
      if (!token) {
         alert("Anda harus login.");
         return;
      }

      console.log(`Attempting to play audio for interview ${item.id}`);
      const response = await api.getInterviewAudio(item.id, token);
      
      if (!response.data || response.data.size === 0) {
          console.error("Received empty audio blob");
          alert("Data audio corup tatau kosong.");
          return;
      }

      console.log(`Audio blob received. Size: ${response.data.size}, Type: ${response.data.type}`);
      
      // Revoke previous URL if exists to prevent memory leaks
      if (currentAudioUrl.value) {
          URL.revokeObjectURL(currentAudioUrl.value);
      }
      
      const blob = new Blob([response.data], { type: 'audio/wav' });
      currentAudioUrl.value = URL.createObjectURL(blob);
      console.log(`Audio URL created: ${currentAudioUrl.value}`);

      currentAudioItem.value = item;
      showAudioPlayer.value = true;
      
      // Reset existing audio element if any
      if (audioElement.value) {
        audioElement.value.pause();
        audioElement.value = null;
      }
      
      // Create new Audio instance
      const audio = new Audio(currentAudioUrl.value);
      audioElement.value = audio;
      
      audio.volume = volume.value / 100;
      audio.playbackRate = playbackSpeed.value;
      
      // Attach event listeners
      audio.addEventListener('loadedmetadata', () => {
        console.log("Audio metadata loaded. Duration:", audio.duration);
        audioDuration.value = audio.duration;
      });
      
      audio.addEventListener('timeupdate', () => {
        currentTime.value = audio.currentTime;
      });
      
      audio.addEventListener('ended', () => {
        console.log("Audio playback ended");
        isPlaying.value = false;
        currentTime.value = 0;
      });
      
      audio.addEventListener('error', (e) => {
          console.error("Error during audio playback:", e);
          console.error("Audio error code:", audio.error ? audio.error.code : 'unknown');
          alert("Terjadi kesalahan saat memutar audio.");
      });
      
      // Attempt playback
      try {
          await audio.play();
          isPlaying.value = true;
          console.log("Audio playback started");
      } catch (err) {
        console.error('Error starting playback:', err);
        alert('Gagal memutar audio. Browser mungkin memblokir autoplay atau format tidak didukung.');
      }

  } catch (error) {
      console.error("Failed to fetch audio:", error);
      let errMsg = "Gagal memuat audio.";
      if (error.response) {
          errMsg += ` Status: ${error.response.status}.`;
          if (error.response.status === 404) errMsg += " File tidak ditemukan di server.";
          if (error.response.status === 401) errMsg += " Sesi habis, silakan login ulang.";
      } else {
          errMsg += ` Error: ${error.message}`;
      }
      alert(`${errMsg}\nID: ${item.id}`);
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

// Function to toggle play/pause state
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

// Function to seek audio position
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

// Helper function to format seconds to time string
function formatTime(seconds) {
  if (isNaN(seconds) || seconds === 0) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Function to handle edit action
function onEdit(row) {
    alert("Edit: " + row.id);
}

// Function to handle delete action
async function onDelete(row) {
    const name = row.respondent?.full_name || row.respondent_name || `ID ${row.id}`;
    if (confirm(`Yakin ingin menghapus data responden "${name}"?`)) {
        try {
            const token = authStore.userToken.value;
            await api.deleteInterview(row.id, token);
            alert('Data berhasil dihapus.');
            loadData(); // Refresh data after deletion
        } catch (error) {
            console.error("Gagal menghapus data:", error);
            alert("Gagal menghapus data.");
        }
    }
}

// Function to navigate to profile page
function goToProfile() {
  router.push('/profile');
}

// Function to export table data to CSV
function exportCSV() {
  if (!rows.value || rows.value.length === 0) {
    alert("Tidak ada data untuk diexport.");
    return;
  }

  // Define headers
  const headers = [
    "No", "Mode Pendataan", "Nama", "Alamat", "Tempat Lahir", 
    "Tanggal Lahir", "Usia", "Pendidikan", "Pekerjaan", "Hobi", 
    "Nomor Telepon", "Alamat Email", "Enumerator", "Durasi Wawancara (detik)", "Tanggal Pendataan"
  ];

  // Map rows to CSV data
  const csvRows = rows.value.map((row, index) => {
    return [
      index + 1,
      row.mode || '-',
      (row.respondent?.full_name || row.respondent_name || '-').replace(/,/g, ' '), // Handle commas
      (row.respondent?.address || '-').replace(/,/g, ' '),
      (row.extracted_data?.['tempat_lahir'] || '-').replace(/,/g, ' '),
      (row.extracted_data?.['tanggal_lahir'] || row.respondent?.birth_year || '-').replace(/,/g, ' '),
      (row.extracted_data?.['usia'] || calculateAge(row.respondent?.birth_year)).toString(),
      (row.extracted_data?.['pendidikan'] || row.respondent?.education || '-').replace(/,/g, ' '),
      (row.extracted_data?.['pekerjaan'] || '-').replace(/,/g, ' '),
      (row.extracted_data?.['hobi'] || '-').replace(/,/g, ' '),
      (row.extracted_data?.['nomor_telepon'] || '-').replace(/,/g, ' '),
      (row.extracted_data?.['alamat_email'] || '-').replace(/,/g, ' '),
      row.enumerator_id || '-',
      (row.duration || 0).toString(),
      formatDate(row.created_at)
    ].map(field => `"${field}"`).join(','); // Quote fields
  });

  // Combine headers and rows
  const csvContent = [headers.join(','), ...csvRows].join('\n');

  // Create blob and download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', 'database_wawancara.csv');
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}


// Function to export MFCC data for an interview
async function exportInterviewMfcc(row) {
  if (!row.has_recording) {
    alert("Interview ini tidak memiliki rekaman audio.");
    return;
  }

  try {
    const token = authStore.userToken.value;
    const response = await api.exportInterviewMfcc(row.id, token);
    
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `mfcc_export_interview_${row.id}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    console.error('Failed to export MFCC:', error);
    
    let errorMessage = 'Gagal mengekspor MFCC';
    
    if (error.response && error.response.data instanceof Blob) {
        try {
            const text = await error.response.data.text();
            const data = JSON.parse(text);
            if (data.detail) errorMessage += ': ' + data.detail;
        } catch (e) {
            errorMessage += ': ' + (error.response.statusText || error.message);
        }
    } else if (error.response?.data?.detail) {
        errorMessage += ': ' + error.response.data.detail;
    } else {
        errorMessage += ': ' + error.message;
    }

    alert(errorMessage);
  }
}

// Function to clear application cache (IndexedDB and Backend Logs)
async function clearCache() {
  if (!confirm('Apakah Anda yakin ingin menghapus cache aplikasi? Ini akan menghapus data offline browser DAN mengosongkan log system (backend) jika Anda Admin.')) {
    return;
  }

  // 1. Clear Backend System Logs
  try {
      const token = authStore.userToken.value;
      if (token) {
          await api.clearSystemLogs(token);
          console.log("System logs cleared successfully via API");
      }
  } catch (error) {
      console.warn("Gagal menghapus system logs (Warning: hanya Superuser yang bisa menghapus log backend):", error);
      // Continue to clear local cache anyway
  }

  // 2. Clear Browser Cache (IndexedDB)
  try {
    const DB_NAME = 'smartcapi_local';
    const req = indexedDB.deleteDatabase(DB_NAME);
    
    req.onsuccess = () => {
      console.log("IndexedDB deleted successfully");
      alert('Cache browser dan logs backend (bila admin) berhasil dibersihkan. Halaman akan dimuat ulang.');
      window.location.reload();
    };
    
    req.onerror = (e) => {
      console.error("Error deleting IndexedDB:", e);
      alert("Gagal menghapus cache database lokal.");
    };
    
    req.onblocked = () => {
      console.warn("Delete blocked");
      alert("Penghapusan cache terhalang. Tutup tab lain aplikasi ini dan coba lagi.");
    };

  } catch (error) {
    console.error("Gagal menghapus cache:", error);
    alert("Terjadi kesalahan saat menghapus cache.");
  }
}


</script>

<style scoped>
.page-container {
  max-width: 1200px;
  margin: 1rem auto;
  padding: 1rem;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  min-height: 100vh;
  aspect-ratio: 16/9;
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
  font-size: 1.5rem;
  margin: 0;
}

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
  font-size: 14px;
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
  width: 24px;
  height: 24px;
}

.access-denied {
  text-align: center;
  padding: 3rem;
  color: #d32f2f;
  font-size: 1.1rem;
  font-weight: 600;
  background-color: #ffebee;
  border-radius: 8px;
  margin-top: 2rem;
}

.table-container {
  margin-top: 1.5rem;
  overflow-x: auto;
  height: calc(100vh - 200px);
}

.rekap-table {
  width: 100%;
  border-collapse: collapse;
  background-color: #fff;
  font-size: 0.9rem;
}

.rekap-table th {
  background-color: #1976d2;
  color: white;
  padding: 12px 15px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
}

.rekap-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #e0e0e0;
  white-space: nowrap;
}

.rekap-table tbody tr:hover {
  background-color: #f5f5f5;
}



.no-col {
  width: 50px;
  text-align: center;
  font-weight: 600;
  color: #666;
}

.rekaman-col {
  text-align: center;
}

.audio-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.audio-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.audio-btn:hover {
  background-color: #f0f0f0;
  transform: scale(1.1);
}

.audio-icon {
  width: 28px;
  height: 28px;
  display: block;
}

.no-data {
  color: #999;
  font-weight: 500;
}

.action-col {
  text-align: center;
}

.action-btn {
  margin: 0 4px;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-btn {
  background-color: #ff9800;
  color: white;
}

.edit-btn:hover {
  background-color: #f57c00;
}

.delete-btn {
  background-color: #f44336;
  color: white;
}

.delete-btn:hover {
  background-color: #d32f2f;
}

.delete-btn:hover {
  background-color: #d32f2f;
}

.intv-mfcc-btn {
  background-color: #17a2b8;
  color: white;
}

.intv-mfcc-btn:hover {
  background-color: #138496;
}

.action-btn:disabled,
.action-btn.disabled {
  background-color: #ccc;
  cursor: not-allowed;
  opacity: 0.7;
}

.action-btn:disabled:hover,
.action-btn.disabled:hover {
  background-color: #ccc;
  transform: none;
}

.clear-cache-btn {
  background-color: #6c757d;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.2s;
}

.clear-cache-btn:hover {
  background-color: #5a6268;
}



.export-btn {
  background-color: #28a745;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.2s;
  margin-right: 10px;
}

.export-btn:hover {
  background-color: #218838;
}


/* Responsive Styles for Square Aspect Ratio */
@media screen and (orientation: portrait) and (min-width: 768px) and (max-width: 1024px) {
  .page-container {
    aspect-ratio: 1/1;
    max-width: 90vh;
    margin: 2rem auto;
  }
  
  .table-container {
    height: calc(90vh - 180px);
  }
}



/* Responsive Styles for Mobile */
@media screen and (max-width: 768px) {
  .page-container {
    padding: 1rem;
    margin: 0;
    box-shadow: none;
    height: auto;
    aspect-ratio: auto;
  }
  .header {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .title {
    font-size: 1.3rem;
    text-align: center;
    order: 1; /* Title at top */
  }
  .header-actions {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    gap: 8px;
    width: 100%;
    order: 2; /* Buttons row below title */
  }
  .export-btn,
  .clear-cache-btn {
    flex: 1;
    min-width: 80px;
    padding: 10px 12px;
    font-size: 13px;
    text-align: center;
  }
  .export-btn {
    order: 1; /* Export CSV first */
  }
  .clear-cache-btn {
    order: 2; /* Clear Cache second */
  }
  .profile-section {
    padding: 5px 8px;
    order: 3; /* Username last */
  }
  .profile-name {
    font-size: 12px;
  }
  .table-container {
    height: auto;
    overflow-x: visible;
  }
  .rekap-table thead {
    display: none;
  }
  .rekap-table tbody, .rekap-table tr, .rekap-table td {
    display: block;
    width: 100%;
  }
  .rekap-table tr {
    margin-bottom: 1rem;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  }
  .rekap-table td {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 15px;
    border-bottom: 1px solid #f0f0f0;
    text-align: right;
    white-space: normal;
  }
  .rekap-table td::before {
    content: attr(data-label);
    font-weight: 600;
    color: #333;
    text-align: left;
    padding-right: 1rem;
    flex: 1;
  }
  .rekap-table td:last-child {
    border-bottom: none;
  }
  .no-col, .rekaman-col, .action-col {
    width: auto;
    text-align: right;
  }
  .rekaman-col {
    justify-content: flex-end;
  }
  .audio-controls {
    justify-content: flex-end;
  }
  .audio-btn.play-btn {
    background-color: #28a745;
    color: white;
    border-radius: 50%;
    width: 36px;
    height: 36px;
    padding: 6px;
  }
  .audio-btn.play-btn svg {
    fill: white;
  }
  .action-col {
    justify-content: flex-end;
    gap: 8px;
    flex-wrap: wrap;
  }
  
  .audio-player-modal {
    width: 95%;
    padding: 20px;
  }
  
  .control-buttons {
    gap: 10px;
  }
  
  .play-pause-btn {
    width: 50px;
    height: 50px;
  }
}
</style>