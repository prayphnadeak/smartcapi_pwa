<template>
  <div class="select-mode">
    <div class="logo-container">
      <img src="@/assets/smartcapi-logo.png" alt="SmartCAPI Logo" class="logo-img" />
    </div>
    <h2>Pilih Mode Admin</h2>
    <div class="button-container">
      <Button @click="choose('user')">Manajemen Pengguna</Button>
      <Button @click="choose('database')">Manajamen Data</Button>
    </div>
  </div>
</template>

<script setup>
import Button from '../components/ui/Button.vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../store/user';

// 1. Impor store interview
import { useInterviewStore } from '../store/interview';

const router = useRouter();
const userStore = useUserStore();
// 2. Inisialisasi store interview
const interviewStore = useInterviewStore();

// Function to handle mode selection
function choose(mode) {
  userStore.setInterviewMode(mode);

  interviewStore.startInterviewTimer();

  if (mode === 'user') {
    // Jika mode adalah 'manajemen pengguna', akan diarahkan ke rekapitulasi-user
    router.push('/rekapitulasi-user'); 
  } else {
    // Jika mode adalah 'manajamen data', akan diarahkan ke /interview-manual
    router.push('/database');
  }
}
</script>

<style scoped>
/* Style tidak perlu diubah */
.select-mode { 
  text-align: center; 
  margin-top: 2em;
  padding: 20px;
}
.logo-container {
  width: 100%;
  max-width: 400px;
  margin: 0 auto 2.5em auto;
}
.logo-img {
  width: 100%;
}
h2 {
  margin-bottom: 2em;
}
.button-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}
</style>