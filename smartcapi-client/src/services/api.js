import axios from 'axios';

// BASE_URL sekarang menggunakan environment variable untuk fleksibilitas.
// Di development, ini akan menggunakan proxy yang dikonfigurasi di vite.config.js
const BASE_URL = `${import.meta.env.VITE_API_BASE_URL || '/api'}/v1`; 

export const api = {
  /**
   * Melakukan login pengguna.
   * @param {object} credentials - Berisi username dan password.
   * @returns {Promise} Axios promise yang berisi token.
   */
  login(credentials) {
    // Backend mengharapkan form-data (OAuth2PasswordRequestForm), bukan JSON
    const params = new URLSearchParams();
    params.append('username', credentials.username);
    params.append('password', credentials.password);
    
    return axios.post(`${BASE_URL}/auth/login`, params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
  },

  /**
   * Mendaftarkan pengguna baru.
   * @param {object} userData - Data dari form registrasi.
   */
  register(userData) {
    return axios.post(`${BASE_URL}/auth/register`, userData);
  },
  
  /**
   * Membuat wawancara baru.
   * @param {object} data - Data awal wawancara.
   * @param {string} token - Token autentikasi pengguna.
   */
  createInterview(data, token) {
    return axios.post(`${BASE_URL}/interviews/`, data, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Mengupload file audio untuk wawancara.
   * @param {number} id - ID wawancara.
   * @param {File} file - File audio.
   * @param {string} token - Token autentikasi pengguna.
   */
  uploadAudio(id, file, token) {
    const formData = new FormData();
    formData.append('audio_file', file);
    return axios.post(`${BASE_URL}/interviews/${id}/upload-audio`, formData, {
      headers: { 
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${token}` 
      }
    });
  },

  /**
   * Memproses audio wawancara (Diarization + STT + LLM).
   * @param {number} id - ID wawancara.
   * @param {string} token - Token autentikasi pengguna.
   */
  processAudio(id, token) {
    return axios.post(`${BASE_URL}/interviews/${id}/process-audio`, {}, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Mengupdate data wawancara.
   * @param {number} id - ID wawancara.
   * @param {object} data - Data yang akan diupdate.
   * @param {string} token - Token autentikasi pengguna.
   */
  updateInterview(id, data, token) {
    return axios.put(`${BASE_URL}/interviews/${id}`, data, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Mengambil semua data wawancara.
   * @param {string} token - Token autentikasi pengguna.
   */
  getInterviews(token) {
    return axios.get(`${BASE_URL}/interviews/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Mengambil detail wawancara berdasarkan ID.
   * @param {number} id - ID wawancara.
   * @param {string} token - Token autentikasi pengguna.
   */
  getInterview(id, token) {
    return axios.get(`${BASE_URL}/interviews/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Menghapus data wawancara berdasarkan ID.
   * @param {number} id - ID wawancara.
   * @param {string} token - Token autentikasi pengguna.
   */
  deleteInterview(id, token) {
    return axios.delete(`${BASE_URL}/interviews/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Mengambil profil pengguna berdasarkan ID.
   * @param {number} id - ID pengguna.
   * @param {string} token - Token autentikasi pengguna.
   */
  getUserProfile(id, token) {
    return axios.get(`${BASE_URL}/users/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Menambahkan sampel suara untuk training model.
   * @param {File} file - File audio.
   * @param {string} label - Label pembicara (misal: 'enumerator').
   * @param {string} token - Token autentikasi pengguna.
   */
  addVoiceSample(file, label, token) {
    const formData = new FormData();
    formData.append('audio_file', file);
    formData.append('speaker_label', label);
    return axios.post(`${BASE_URL}/training/add-voice-sample`, formData, {
      headers: { 
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${token}` 
      }
    });
  },

  /**
   * Mengupload sampel suara pengguna saat registrasi.
   * @param {File} file - File audio.
   * @param {string} token - Token autentikasi pengguna.
   */
  uploadVoiceSample(file, token) {
    const formData = new FormData();
    formData.append('voice_file', file, 'recording.wav');
    return axios.post(`${BASE_URL}/users/me/voice-sample`, formData, {
      headers: { 
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${token}` 
      }
    });
  },

  /**
   * Mengambil semua pengguna (Admin only).
   * @param {string} token - Token autentikasi pengguna.
   */
  getUsers(token) {
    return axios.get(`${BASE_URL}/users/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Menghapus pengguna berdasarkan ID (Admin only).
   * @param {number} id - ID pengguna.
   * @param {string} token - Token autentikasi pengguna.
   */
  deleteUser(id, token) {
    return axios.delete(`${BASE_URL}/users/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Mengupdate data pengguna (Admin only).
   * @param {number} id - ID pengguna.
   * @param {object} data - Data yang akan diupdate.
   * @param {string} token - Token autentikasi pengguna.
   */
  updateUser(id, data, token) {
    return axios.put(`${BASE_URL}/users/${id}`, data, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Upload audio file for an interview.
   * @param {number} interviewId - ID wawancara.
   * @param {Blob} audioBlob - Audio file blob.
   * @param {string} token - Token autentikasi pengguna.
   */
  uploadAudio(interviewId, audioBlob, token) {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'recording.webm');
    
    return axios.post(`${BASE_URL}/interviews/${interviewId}/upload-audio`, formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * Process audio file for an interview (transcription and extraction).
   * @param {number} interviewId - ID wawancara.
   * @param {string} token - Token autentikasi pengguna.
   */
  processAudio(interviewId, token) {
    return axios.post(`${BASE_URL}/interviews/${interviewId}/process-audio`, {}, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Get interview by ID.
   * @param {number} interviewId - ID wawancara.
   * @param {string} token - Token autentikasi pengguna.
   */
  getInterview(interviewId, token) {
    return axios.get(`${BASE_URL}/interviews/${interviewId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Get interview transcript.
   * @param {number} interviewId - ID wawancara.
   * @param {string} token - Token autentikasi pengguna.
   */
  getInterviewTranscript(interviewId, token) {
    return axios.get(`${BASE_URL}/interviews/${interviewId}/transcript`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Get interview audio recording as blob.
   * @param {number} interviewId - ID wawancara.
   * @param {string} token - Token autentikasi pengguna.
   */
  getInterviewAudio(interviewId, token) {
    return axios.get(`${BASE_URL}/interviews/${interviewId}/audio`, {
      headers: { 'Authorization': `Bearer ${token}` },
      responseType: 'blob'
    });
  },

  /**
   * Export MFCC data for a user's voice sample.
   * @param {number} userId - ID pengguna.
   * @param {string} token - Token autentikasi pengguna.
   */
  exportUserMfcc(userId, token) {
    return axios.get(`${BASE_URL}/users/${userId}/export-mfcc`, {
      headers: { 'Authorization': `Bearer ${token}` },
      responseType: 'blob' // Important for file download
    });
  },

  /**
   * Export MFCC data for an interview.
   * @param {number} interviewId - ID wawancara.
   * @param {string} token - Token autentikasi pengguna.
   */
  exportInterviewMfcc(interviewId, token) {
    return axios.get(`${BASE_URL}/interviews/${interviewId}/export-mfcc`, {
      headers: { 'Authorization': `Bearer ${token}` },
      responseType: 'blob' // Important for file download
    });
  },

  /**
   * Export MFCC data for all interviews of a user.
   * @param {number} userId - ID pengguna.
   * @param {string} token - Token autentikasi pengguna.
   */
  exportUserInterviewsMfcc(userId, token) {
    return axios.get(`${BASE_URL}/users/${userId}/export-interviews-mfcc`, {
      headers: { 'Authorization': `Bearer ${token}` },
      responseType: 'blob'
    });
  },

  /**
   * Get training progress for the current user.
   * @param {string} token - Token autentikasi pengguna.
   */
  getTrainingProgress(token) {
    return axios.get(`${BASE_URL}/training/progress`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  /**
   * Clear system logs (admin only).
   * @param {string} token - Token autentikasi pengguna.
   */
  clearSystemLogs(token) {
    return axios.delete(`${BASE_URL}/system/logs`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  }
};