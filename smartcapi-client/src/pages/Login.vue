<template>
  <div class="login-page">
    <div class="login-logo">
      <img src="@/assets/smartcapi-logo.png" alt="SmartCAPI Logo" class="logo-img" />
      <span class="logo-text">Smart Computer Assisted Personal Interviewing</span>
    </div>
    <div class="login-card">
      <form @submit.prevent="onLogin">
        <input v-model="username" type="text" placeholder="Username" required />
        <input v-model="password" type="password" placeholder="Password" required />
        <button type="submit" class="login-btn">Log in</button>
      </form>
      <div class="login-links">
        <span>Belum punya akun? Klik <a href="#" @click.prevent="goRegister">daftar</a></span>
        <span>Info selengkapnya <a href="#" @click.prevent="goAboutUs">di sini</a></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
// import store
import { useAuthStore } from '@/store/auth' // sesuaikan path jika berbeda

const router = useRouter()
const authStore = (typeof useAuthStore === 'function') ? useAuthStore() : null

const username = ref('')
const password = ref('')

// Function to handle login submission
async function onLogin() {
  if (!username.value || !password.value) {
    alert('Masukkan username dan password')
    return
  }

  if (!authStore) {
    alert('Auth store not initialized')
    return
  }

  const result = await authStore.loginWithCredentials(username.value, password.value)
  
  if (result.ok) {
    // Redirect based on role
    const role = result.user?.role || 'user'
    if (role === 'admin') {
      router.push('/admin-select')
    } else {
      router.push('/rekapitulasi')
    }
  } else {
    alert('Login gagal: ' + (result.error || 'Unknown error'))
  }
}

// Function to navigate to the registration page
function goRegister() {
  router.push('/register')
}
// Function to navigate to the About Us page
function goAboutUs() {
  router.push('/about-us')
}
</script>

<style scoped>
/* ... tetap seperti semula, tidak diubah ... */
.login-page {
  min-height: 100vh;
  background: #f6f8fa;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.login-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
  width: 100%;
  max-width: 400px;
}
.logo-img {
  width: 100%;
  margin-bottom: 16px;
}
.logo-text {
  font-size: 1.1rem;
  font-weight: bold;
  color: #222;
  font-family: 'Montserrat', Arial, Helvetica, sans-serif;
  text-align: center;
  line-height: 1.4;
}
.login-card {
  background: #ededed;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(48,52,54,0.04);
  padding: 2rem 2.3rem 1.3rem 2.3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 400px;
  box-sizing: border-box;
}
.login-card form {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 13px;
}
.login-card input[type="text"],
.login-card input[type="password"] {
  width: 100%;
  border: 1px solid #b7b7b7;
  border-radius: 5px;
  padding: 0.7em 1em;
  font-size: 1rem;
}
.login-btn {
  background: #2196f3;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 0.7em 0;
  font-size: 1.1em;
  font-weight: bold;
  cursor: pointer;
  margin-top: 10px;
  transition: filter 0.2s;
}
.login-btn:hover { filter: brightness(0.95); }
.login-links {
  margin-top: 8px;
  font-size: 0.98em;
  color: #222;
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: center;
}
.login-links a {
  color: #1565c0;
  text-decoration: underline;
  cursor: pointer;
  font-weight: bold;
}
</style>