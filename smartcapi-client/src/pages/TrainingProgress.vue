<template>
  <div class="training-page">
    <div class="training-container">
      <div class="training-header">
        <h2>Memproses Suara Anda</h2>
        <p>Mohon tunggu sebentar, kami sedang melatih sistem untuk mengenali suara Anda.</p>
      </div>

      <div class="progress-section">
        <div class="progress-bar-container">
          <div class="progress-bar" :style="{ width: progress + '%' }"></div>
        </div>
        <div class="progress-info">
          <span class="percentage">{{ progress }}%</span>
          <span class="status-message">{{ statusMessage }}</span>
        </div>
      </div>

      <div class="steps-container">
        <div class="step" :class="{ active: progress >= 10, completed: progress > 20 }">
          <div class="step-icon">1</div>
          <div class="step-text">Ekstraksi Fitur</div>
        </div>
        <div class="step" :class="{ active: progress >= 20, completed: progress > 40 }">
          <div class="step-icon">2</div>
          <div class="step-text">Persiapan Data</div>
        </div>
        <div class="step" :class="{ active: progress >= 40, completed: progress > 80 }">
          <div class="step-icon">3</div>
          <div class="step-text">Pelatihan Model</div>
        </div>
        <div class="step" :class="{ active: progress >= 80, completed: progress >= 100 }">
          <div class="step-icon">4</div>
          <div class="step-text">Finalisasi</div>
        </div>
      </div>

      <div class="action-buttons">
        <button 
          v-if="isCompleted" 
          class="btn-continue" 
          @click="goToDashboard"
        >
          LANJUT KE DASHBOARD
        </button>
        <div v-else class="loading-spinner"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store/auth';
import { api } from '../services/api';

const router = useRouter();
const authStore = useAuthStore();

const progress = ref(0);
const statusMessage = ref('Menyiapkan...');
const isCompleted = ref(false);
const pollInterval = ref(null);

// Function to check training progress
async function checkProgress() {
  try {
    const token = authStore.userToken.value;
    
    // Use the api service instead of direct fetch with hardcoded URL
    const response = await api.getTrainingProgress(token);
    
    if (response.status === 200) {
      const data = response.data;
      progress.value = data.progress;
      statusMessage.value = data.message;
      
      if (data.status === 'completed' || data.progress >= 100) {
        progress.value = 100;
        isCompleted.value = true;
        statusMessage.value = "Pelatihan Selesai!";
        clearInterval(pollInterval.value);
      } else if (data.status === 'error') {
        statusMessage.value = "Terjadi kesalahan: " + data.message;
        clearInterval(pollInterval.value);
        alert("Terjadi kesalahan saat pelatihan model.");
      }
    }
  } catch (error) {
    console.error("Error checking progress:", error);
    // Don't alert on every poll error to avoid spamming the user
    // but maybe stop polling if it's a 401 or persistent error
  }
}

// Function to navigate to dashboard
function goToDashboard() {
  router.push('/rekapitulasi');
}

onMounted(() => {
  // Start polling
  checkProgress();
  pollInterval.value = setInterval(checkProgress, 1000);
});

onUnmounted(() => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value);
  }
});
</script>

<style scoped>
.training-page {
  min-height: 100vh;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.training-container {
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 500px;
  text-align: center;
}

.training-header h2 {
  color: #1976d2;
  margin-bottom: 10px;
}

.training-header p {
  color: #666;
  margin-bottom: 30px;
}

.progress-section {
  margin-bottom: 40px;
}

.progress-bar-container {
  height: 10px;
  background: #e0e0e0;
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #1976d2, #64b5f6);
  transition: width 0.5s ease;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  font-weight: 600;
  color: #333;
}

.steps-container {
  display: flex;
  justify-content: space-between;
  margin-bottom: 40px;
  position: relative;
}

.steps-container::before {
  content: '';
  position: absolute;
  top: 15px;
  left: 0;
  right: 0;
  height: 2px;
  background: #e0e0e0;
  z-index: 0;
}

.step {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 25%;
}

.step-icon {
  width: 30px;
  height: 30px;
  background: #e0e0e0;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
  font-weight: bold;
  margin-bottom: 8px;
  transition: all 0.3s;
}

.step.active .step-icon {
  background: #1976d2;
  box-shadow: 0 0 0 4px rgba(25, 118, 210, 0.2);
}

.step.completed .step-icon {
  background: #4caf50;
}

.step-text {
  font-size: 0.75rem;
  color: #999;
  font-weight: 500;
}

.step.active .step-text {
  color: #1976d2;
  font-weight: 700;
}

.action-buttons {
  height: 50px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.btn-continue {
  background: #4caf50;
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 25px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 6px rgba(76, 175, 80, 0.2);
}

.btn-continue:hover {
  background: #43a047;
  transform: translateY(-2px);
  box-shadow: 0 6px 8px rgba(76, 175, 80, 0.3);
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #1976d2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
