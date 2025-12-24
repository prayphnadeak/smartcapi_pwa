<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-title">Registrasi Akun</div>
      <p class="instruction">
        Mohon rekam suara anda dengan jelas untuk proses verifikasi. Ucapkan kalimat berikut:
      </p>

      <div class="sample-text" v-html="dynamicSampleText"></div>

      <div class="recorder-section">
        <div class="mic-button" @click="toggleRecording" :class="{ 'is-recording': isRecording }">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z" fill="white"/>
            <path d="M19 12H17C17 14.76 14.76 17 12 17C9.24 17 7 14.76 7 12H5C5 15.54 7.72 18.45 11 18.93V22H13V18.93C16.28 18.45 19 15.54 19 12Z" fill="white"/>
          </svg>
        </div>
        <div v-if="isRecording" class="duration-display">{{ formattedDuration }}</div>
        <p :class="['status-text', { 'success': recordingDone }]">{{ statusText }}</p>
      </div>

      <div class="form-buttons">
        <button type="button" class="btn-back" @click="goBack" :disabled="isUploading">
          BACK
        </button>
        <button type="submit" class="btn-next" @click="finishRegistration" :disabled="!recordingDone || isUploading">
          {{ isUploading ? 'UPLOADING...' : 'NEXT' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store/auth';
import { api } from '../services/api';

const router = useRouter();
const authStore = useAuthStore();

const isRecording = ref(false);
const recordingDone = ref(false);
const statusText = ref('Tekan untuk merekam');
const durationInSeconds = ref(0);
const timerInterval = ref(null);
const mediaRecorder = ref(null);
const audioChunks = ref([]);
const isUploading = ref(false);

// Audio Context & Nodes
const audioContext = ref(null);
const gainNode = ref(null);
const analyserNode = ref(null); // Or ScriptProcessor for RMS
const sourceNode = ref(null);
const destNode = ref(null); // MediaStreamDestination
const micVolume = ref(0);
const micGain = ref(1.0); // Default 1.0 (modified by slider)

// Placeholder user data, ideally fetch from store or API
const registrationData = { fullName: 'Pengguna Baru' }; 

const formattedDuration = computed(() => {
  const minutes = Math.floor(durationInSeconds.value / 60);
  const seconds = durationInSeconds.value % 60;
  const paddedMinutes = String(minutes).padStart(2, '0');
  const paddedSeconds = String(seconds).padStart(2, '0');
  return `${paddedMinutes}:${paddedSeconds}`;
});

const dynamicSampleText = computed(() => {
  const userName = registrationData.fullName || '[Nama Anda]';

  return `
    "<br><strong>[Ucapkan Salam]</strong>
    Nama saya <strong>[Sebutkan Nama Lengkap Anda]</strong>. Saya berasal dari [kota asal] dan saat ini berusia [usia
    Anda] tahun. Saya adalah seorang [jenis kelamin Anda], dan saya tinggal di [alamat
    lengkap Anda].
    <br>
    Saya menyelesaikan pendidikan terakhir saya di [nama institusi pendidikan], dengan
    gelar [gelar akademik]. Pendidikan ini telah memberikan saya pengetahuan dan
    keterampilan yang sangat berguna dalam berbagai aspek kehidupan.
    <br> Saat ini, saya bekerja sebagai [posisi pekerjaan Anda] di [nama
    perusahaan/organisasi tempat Anda bekerja]. Dalam pekerjaan saya, saya
    bertanggung jawab atas [deskripsi tugas utama Anda]. Pengalaman kerja ini telah
    mengajarkan saya banyak hal tentang profesionalisme, kerjasama tim, dan tanggung
    jawab.
    <br>
    Keluarga saya sangat mendukung segala aktivitas dan
    aspirasi saya, termasuk keinginan saya untuk menjadi petugas pendata dalam survei ini.
    <br> Alasan utama saya ingin menjadi petugas pendata dalam survei ini adalah karena saya percaya
    bahwa data yang akurat dan terpercaya sangat penting untuk pembangunan negara.
    Sebagai petugas pendata, saya akan memiliki kesempatan untuk berkontribusi
    langsung dalam pengumpulan data yang nantinya akan digunakan untuk merumuskan
    kebijakan-kebijakan penting.
    <br>Saya juga ingin terlibat lebih dalam dengan masyarakat dan membantu memastikan
    bahwa suara mereka terwakili dalam data yang dikumpulkan. Dengan bekerja sebagai
    petugas pendata, saya berharap bisa memberikan dampak positif bagi masyarakat secara keseluruhan.
    <br>Terima kasih atas kesempatan untuk memperkenalkan diri. Saya sangat berharap
    dapat berkontribusi sebagai petugas pendata dalam survei ini dan bekerja sama dengan tim yang
    berdedikasi untuk menciptakan data yang akurat dan bermanfaat.
    Salam hormat,
    <br><strong>[Sebutkan Nama Lengkap Anda]</strong>"
  `;
});

// Function to start audio recording
async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // --- Audio Pipeline Setup ---
    audioContext.value = new (window.AudioContext || window.webkitAudioContext)();
    sourceNode.value = audioContext.value.createMediaStreamSource(stream);
    
    // Gain Node (Volume Booster)
    gainNode.value = audioContext.value.createGain();
    gainNode.value.gain.value = micGain.value; // Set initial gain
    
    // Destination for MediaRecorder
    destNode.value = audioContext.value.createMediaStreamDestination();
    
    // Metering (ScriptProcessor to calculate RMS)
    const meterNode = audioContext.value.createScriptProcessor(4096, 1, 1);
    meterNode.onaudioprocess = (e) => {
        // Update gain dynamically if slider moves
        if (gainNode.value) {
            gainNode.value.gain.value = micGain.value;
        }

        const inputData = e.inputBuffer.getChannelData(0);
        let sum = 0;
        for (let i = 0; i < inputData.length; i++) {
            sum += inputData[i] * inputData[i];
        }
        const rms = Math.sqrt(sum / inputData.length);
        // Display volume (scale appropriately)
        micVolume.value = Math.min(100, Math.round(rms * 200 * (micGain.value > 1 ? 1 : 1.5))); 
    };

    // Connections: Source -> Gain -> Destination (for recording)
    sourceNode.value.connect(gainNode.value);
    gainNode.value.connect(destNode.value);
    
    // Connections: Gain -> Meter -> Destination (AudioContext physical out, muted/ignored)
    gainNode.value.connect(meterNode);
    meterNode.connect(audioContext.value.destination);
    
    // Use the potentially amplified stream for MediaRecorder
    mediaRecorder.value = new MediaRecorder(destNode.value.stream);
    audioChunks.value = [];

    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data);
      }
    };

    mediaRecorder.value.start();
    isRecording.value = true;
    recordingDone.value = false;
    statusText.value = 'Merekam... Tekan lagi untuk berhenti.';
    
    durationInSeconds.value = 0;
    timerInterval.value = setInterval(() => {
      durationInSeconds.value++;
    }, 1000);

  } catch (err) {
    console.error("Error accessing microphone:", err);
    alert("Gagal mengakses mikrofon. Pastikan izin diberikan.");
  }
}

// Function to stop audio recording
function stopRecording() {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop();
    // Don't stop tracks immediately if we want to play back... but we have file.
    
    clearInterval(timerInterval.value);
    isRecording.value = false;
    recordingDone.value = true;
    statusText.value = 'Rekaman Selesai. Tekan NEXT untuk melanjutkan.';
    
    // Cleanup Web Audio
    if (audioContext.value) {
        audioContext.value.close();
    }
  }
}

// Function to toggle audio recording
function toggleRecording() {
  if (isRecording.value) {
    stopRecording();
  } else {
    startRecording();
  }
}

// Function to finish registration and upload voice sample
async function finishRegistration() {
  if (audioChunks.value.length === 0) {
    alert("Silakan rekam suara terlebih dahulu.");
    return;
  }

  const audioBlob = new Blob(audioChunks.value, { type: 'audio/wav' });
  const token = authStore.userToken.value;

  try {
    isUploading.value = true;
    await api.uploadVoiceSample(audioBlob, token);
    alert("Registrasi dan rekaman suara berhasil!");
    router.push('/training-progress');
  } catch (error) {
    console.error("Failed to upload voice sample:", error);
    alert("Gagal mengupload rekaman suara, tapi registrasi berhasil.");
    router.push('/training-progress');
  } finally {
    isUploading.value = false;
  }
}

// Function to navigate back
function goBack() {
  if (isRecording.value) {
    stopRecording();
  }
  router.back();
}

onUnmounted(() => {
  if (timerInterval.value) {
    clearInterval(timerInterval.value);
  }
  if (isRecording.value && mediaRecorder.value) {
    stopRecording();
  }
});
</script>

<style scoped>
/* (Style dari kode sebelumnya tetap dipertahankan, tidak ada perubahan) */
.register-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.register-container {
  background: white;
  border-radius: 8px;
  padding: 30px 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  text-align: center;
}
.register-title {
  color: #1976d2;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 20px;
}
.sample-text {
  background: #e9ecef;
  padding: 1rem;
  border-radius: 8px;
  color: #333;
  margin-bottom: 2.5rem;
  font-weight: 500;
  text-align: left;
  font-style: normal;
  line-height: 1.6;
  
  /* 9:16 Aspect Ratio & Scroll */
  aspect-ratio: 9/16;
  overflow-y: auto;
  
  /* Scrollbar styling for Firefox */
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
}

/* Mini scrollbar styling for Webkit (Chrome, Safari, Edge) */
.sample-text::-webkit-scrollbar {
  width: 4px;
}

.sample-text::-webkit-scrollbar-track {
  background: transparent;
}

.sample-text::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.recorder-section {
  margin-bottom: 2.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.mic-button {
  width: 80px;
  height: 80px;
  background: #1976d2;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  outline: none;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}
.mic-button:hover {
  background: #1565c0;
  transform: scale(1.05);
}
.mic-button.is-recording {
  background: #dc3545;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7); }
  70% { box-shadow: 0 0 0 15px rgba(220, 53, 69, 0); }
  100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); }
}

/* ---- STYLE BARU UNTUK TAMPILAN DURASI ---- */
.duration-display {
  margin-top: 1rem;
  font-size: 1.25rem;
  font-weight: bold;
  color: #333;
  font-family: 'Courier New', Courier, monospace;
}
/* ---------------------------------------- */

.status-text {
  margin-top: 1rem; /* Sedikit disesuaikan agar tidak terlalu jauh */
  font-weight: 500;
  color: #666;
}
.status-text.success {
  color: #28a745;
  font-weight: bold;
}
.form-buttons {
  display: flex;
  gap: 15px;
  margin-top: 20px;
}
.btn-back,
.btn-next {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 25px;
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s;
  background: #1976d2;
  color: white;
}
.btn-back:hover,
.btn-next:hover:not(:disabled) {
  background: #1565c0;
}
.btn-next:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.mic-diagnostics {
  margin-top: 20px;
  background: #f8f9fa;
  padding: 15px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border: 1px solid #dee2e6;
}

.volume-bar-container {
  width: 100%;
}

.volume-bar-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
  display: flex;
  justify-content: space-between;
}

.volume-bar-track {
  width: 100%;
  height: 10px;
  background: #eee;
  border-radius: 5px;
  overflow: hidden;
}

.volume-bar-fill {
  height: 100%;
  background: #28a745;
  transition: width 0.1s ease;
}

.sensitivity-control {
  display: flex;
  flex-direction: column;
  gap: 5px;
  text-align: left;
}

.sensitivity-control label {
  font-size: 12px;
  font-weight: 600;
  color: #333;
}

.slider {
  width: 100%;
  cursor: pointer;
}
</style>