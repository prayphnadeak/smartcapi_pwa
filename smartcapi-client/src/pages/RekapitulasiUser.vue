<template>
  <div class="page-container">
    <div class="header">
      <h1 class="title">Rekapitulasi User</h1>
      <div class="header-actions">
        <div class="profile-section" @click="goToProfile" title="Lihat Profil">
          <button class="profile-icon-btn">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5ZM12 19.2C9.5 19.2 7.29 17.92 6 15.96C6.04 14.03 10 12.9 12 12.9C13.99 12.9 17.96 14.03 18 15.96C16.71 17.92 14.5 19.2 12 19.2Z"/>
            </svg>
          </button>
          <span class="profile-name">{{ currentUser?.name || 'Admin' }}</span>
        </div>
        <button class="logout-btn" @click="logout" title="Logout">Logout</button>
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
            <th>Username</th>
            <th>Nama</th>
            <th>Email</th>
            <th>Nomor Telepon</th>
            <th>Jumlah Wawancara</th>
            <th>Rekaman</th>
            <th>Tanggal Pendaftaran</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in rows" :key="row.id">
            <td data-label="No" class="no-col">{{ idx + 1 }}</td>
            <td data-label="Username">{{ row.username }}</td>
            <td data-label="Nama">{{ row.full_name || '-' }}</td>
            <td data-label="Email">{{ row.email }}</td>
            <td data-label="Nomor Telepon">{{ row.phone || '-' }}</td>
            <td data-label="Jumlah Wawancara">{{ row.interview_count || 0 }}</td>
            <td data-label="Rekaman" class="rekaman-col">
              <div v-if="row.voice_sample_path" class="audio-controls">
                <button 
                  @click="openAudioPlayer(row)" 
                  class="audio-btn play-btn"
                  title="Play Audio"
                >
                  <img src="../assets/play.svg" alt="Play" class="audio-icon" />
                </button>
              </div>
              <div v-else class="no-data">-</div>
            </td>
            <td data-label="Tanggal Pendaftaran">{{ formatDate(row.created_at) }}</td>
            <td data-label="Action" class="action-col">
              <button class="action-btn edit-btn" @click="onEdit(row)">Edit</button>
              <button class="action-btn delete-btn" @click="onDelete(row)">Delete</button>
              <button class="action-btn mfcc-btn" @click="exportMfcc(row)" title="Export User MFCC">User MFCC</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal-overlay">
      <div class="modal-content">
        <h3>Edit User</h3>
        <form @submit.prevent="saveEdit">
          <div class="form-group">
            <label>Username</label>
            <input v-model="editForm.username" type="text" required />
          </div>
          <div class="form-group">
            <label>Nama Lengkap</label>
            <input v-model="editForm.full_name" type="text" />
          </div>
          <div class="form-group">
            <label>Email</label>
            <input v-model="editForm.email" type="email" required />
          </div>
          <div class="form-group">
            <label>Nomor Telepon</label>
            <input v-model="editForm.phone" type="tel" placeholder="Nomor Telepon" />
          </div>
          <div class="form-group">
            <label>Password (Kosongkan jika tidak ingin mengubah)</label>
            <input v-model="editForm.password" type="password" placeholder="Password baru" />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeEditModal">Batal</button>
            <button type="submit" class="btn-save">Simpan</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Audio Player Modal -->
    <div v-if="showAudioPlayer" class="modal-overlay" @click.self="closeAudioPlayer">
      <div class="audio-player-modal">
        <div class="player-header">
          <h3>🎵 Voice Recording</h3>
          <button class="close-btn" @click="closeAudioPlayer">✕</button>
        </div>
        
        <div class="player-info">
          <p class="user-info">{{ currentAudioUser?.full_name || currentAudioUser?.username }}</p>
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
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store/auth';
import { api } from '../services/api';

const router = useRouter();
const authStore = useAuthStore();
const accessDenied = ref(false);
const audioElement = ref(null);
const rows = ref([]);
const currentUser = ref(null);

// Edit Modal State
const showEditModal = ref(false);
const editForm = ref({
  id: null,
  username: '',
  full_name: '',
  email: '',
  phone: '',
  password: ''
});

// Audio Player State
const showAudioPlayer = ref(false);
const currentAudioUser = ref(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const audioDuration = ref(0);
const volume = ref(100);
const playbackSpeed = ref(1);

const timelineProgress = computed(() => {
  if (audioDuration.value === 0) return 0;
  return (currentTime.value / audioDuration.value) * 100;
});

onMounted(async () => {
  loadUsers();
});

onUnmounted(() => {
  if (audioElement.value) {
    audioElement.value.pause();
    audioElement.value = null;
  }
});

// Function to load users from API
async function loadUsers() {
  try {
    const token = authStore.userToken.value;
    if (!token) {
        router.push('/');
        return;
    }
    
    const response = await api.getUsers(token);
    rows.value = response.data;
    
  } catch (error) {
    console.error("Failed to fetch users:", error);
    if (error.response && error.response.status === 403) {
        accessDenied.value = true;
    }
  }
}

// Function to open audio player modal
function openAudioPlayer(row) {
  currentAudioUser.value = row;
  showAudioPlayer.value = true;
  
  const audioUrl = `/${row.voice_sample_path}`;
  
  if (audioElement.value) {
    audioElement.value.pause();
  }
  
  audioElement.value = new Audio(audioUrl);
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
    alert('Gagal memutar audio. Pastikan file ada dan server berjalan.');
  });
}

// Function to close audio player modal
function closeAudioPlayer() {
  if (audioElement.value) {
    audioElement.value.pause();
    audioElement.value = null;
  }
  showAudioPlayer.value = false;
  currentAudioUser.value = null;
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

// Function to create edit form data
function onEdit(row){
  editForm.value = {
    id: row.id,
    username: row.username,
    full_name: row.full_name,
    email: row.email,
    phone: row.phone,
    password: ''
  };
  showEditModal.value = true;
}

// Function to close edit modal
function closeEditModal() {
  showEditModal.value = false;
  editForm.value = { id: null, username: '', full_name: '', email: '', phone: '', password: '' };
}

// Function to save edited user data
async function saveEdit() {
  try {
    const token = authStore.userToken.value;
    const updateData = {
      username: editForm.value.username,
      full_name: editForm.value.full_name,
      email: editForm.value.email,
      phone: editForm.value.phone
    };
    
    if (editForm.value.password) {
      updateData.password = editForm.value.password;
    }
    
    await api.updateUser(editForm.value.id, updateData, token);
    alert('User berhasil diupdate!');
    closeEditModal();
    loadUsers();
  } catch (error) {
    console.error('Failed to update user:', error);
    alert('Gagal mengupdate user: ' + (error.response?.data?.detail || error.message));
  }
}

// Function to delete user
async function onDelete(row){
  if (confirm(`Apakah Anda yakin ingin menghapus data untuk user ${row.username}?`)) {
    try {
      const token = authStore.userToken.value;
      await api.deleteUser(row.id, token);
      alert('User berhasil dihapus!');
      loadUsers();
    } catch (error) {
      console.error('Failed to delete user:', error);
      alert('Gagal menghapus user: ' + (error.response?.data?.detail || error.message));
    }
  }
}

// Function to export MFCC for user
async function exportMfcc(row) {
  try {
    const token = authStore.userToken.value;
    const response = await api.exportUserMfcc(row.id, token);
    
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `mfcc_export_${row.username}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    console.error('Failed to export MFCC:', error);
    alert('Gagal mengekspor MFCC: ' + (error.response?.data?.detail || error.message));
  }
}

// Function to navigate to profile page
function goToProfile() {
  router.push('/profile');
}

// Function to logout user
function logout() {
  authStore.logout();
  router.push('/');
}
// Function to format date
function formatDate(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}
</script>

<style scoped>
.logout-btn {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.2s;
}

.logout-btn:hover {
  background-color: #d32f2f;
}

.page-container {
  max-width: 1200px;
  margin: 1rem auto;
  padding: 1rem;
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
}

.rekap-table {
  width: 100%;
  border-collapse: collapse;
  background-color: #fff;
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

.mfcc-btn {
  background-color: #28a745;
  color: white;
}

.mfcc-btn:hover {
  background-color: #218838;
}

/* Modal Styles */
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
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 25px;
  border-radius: 8px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #1976d2;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.btn-cancel {
  background: #e0e0e0;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.btn-save {
  background: #1976d2;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

/* Audio Player Modal Styles */
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
  background: rgba(255, 255, 255, 0.1);
  padding: 20px;
  border-radius: 12px;
}

.timeline-container {
  position: relative;
  margin-bottom: 10px;
}

.timeline {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.3);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

.timeline::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.timeline::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.time-display {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  margin-bottom: 20px;
  opacity: 0.9;
}

.control-buttons {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
}

.control-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 10px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.control-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.play-pause-btn {
  width: 60px;
  height: 60px;
  background: white;
  color: #667eea;
}

.play-pause-btn:hover {
  background: rgba(255, 255, 255, 0.9);
}

.volume-control {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.volume-slider {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.3);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
}

.volume-slider::-moz-range-thumb {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  border: none;
}

.volume-value {
  font-size: 0.9rem;
  min-width: 40px;
  text-align: right;
}

.speed-control {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
}

.speed-control label {
  font-size: 0.9rem;
}

.speed-select {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  outline: none;
}

.speed-select option {
  background: #667eea;
  color: white;
}

/* Responsive Styles for Mobile */
@media screen and (max-width: 768px) {
  .page-container {
    padding: 1rem;
    margin: 0;
    box-shadow: none;
  }
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  .title {
    font-size: 1.5rem;
  }
  .rekap-table thead {
    display: none;
  }
  .rekap-table tbody, .rekap-table tr, .rekap-table td {
    display: block;
    width: 100%
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
  }
  .rekap-table td:last-child {
    border-bottom: none;
  }
  .no-col, .rekaman-col, .action-col {
    width: auto;
    text-align: right;
  }
  .action-col {
    justify-content: flex-end;
    gap: 8px;
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