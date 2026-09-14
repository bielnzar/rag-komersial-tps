<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fade-in">
    <div class="card-executive max-w-md w-full p-6 sm:p-8 rounded-3xl border border-slate-700/60 shadow-2xl bg-slate-900/95 relative overflow-hidden">
      <!-- Decorative Accent Blur -->
      <div class="absolute -top-12 -right-12 w-36 h-36 bg-teal-500/15 rounded-full blur-2xl pointer-events-none"></div>
      <div class="absolute -bottom-12 -left-12 w-36 h-36 bg-blue-500/15 rounded-full blur-2xl pointer-events-none"></div>

      <!-- Header Section dengan Logo TPS Asli -->
      <div class="text-center mb-6">
        <div class="inline-flex items-center justify-center p-3 sm:p-4 rounded-3xl bg-slate-950/90 border border-slate-700/60 mb-3 shadow-xl">
          <img 
            :src="logoUrl" 
            alt="Logo PT TPS" 
            class="h-12 sm:h-14 w-auto object-contain"
            @error="hasLogoError = true"
            v-if="!hasLogoError"
          />
          <div v-else class="flex items-center gap-2 px-2 py-1">
            <Ship class="w-8 h-8 text-teal-400" />
            <span class="font-extrabold text-lg text-slate-100 tracking-wider">PT TPS</span>
          </div>
        </div>

        <h2 class="text-xl sm:text-2xl font-extrabold tracking-tight text-slate-100">
          Portal Masuk Sistem AI
        </h2>
        <p class="text-xs text-slate-400 font-medium mt-1">
          PT Terminal Petikemas Surabaya — Single Unified Access
        </p>
      </div>

      <!-- Error Alert Message -->
      <div v-if="errorMessage" class="mb-5 p-3.5 rounded-xl bg-red-950/60 border border-red-800/60 text-red-200 text-xs flex items-start gap-2.5 animate-shake">
        <AlertCircle class="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
        <div class="font-medium">{{ errorMessage }}</div>
      </div>

      <!-- Unified Login Form -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1.5">Username Pengguna</label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <User class="w-4 h-4" />
            </div>
            <input
              type="text"
              v-model="username"
              required
              autocomplete="username"
              placeholder="Masukkan username Anda"
              class="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs font-medium focus:outline-none focus:border-teal-500 transition-colors"
            />
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1.5">Kata Sandi (Password)</label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <Lock class="w-4 h-4" />
            </div>
            <input
              :type="showPassword ? 'text' : 'password'"
              v-model="password"
              required
              autocomplete="current-password"
              placeholder="Masukkan kata sandi"
              class="w-full pl-9 pr-10 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs font-medium focus:outline-none focus:border-teal-500 transition-colors"
            />
            <button 
              type="button" 
              @click="showPassword = !showPassword"
              class="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300 transition-colors text-xs"
            >
              {{ showPassword ? 'Sembunyikan' : 'Lihat' }}
            </button>
          </div>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="isLoading"
          class="w-full py-3 rounded-xl font-bold text-xs shadow-lg transition-all flex items-center justify-center gap-2 bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-400 hover:to-cyan-500 text-slate-950 shadow-teal-500/20 disabled:opacity-60"
        >
          <Loader2 v-if="isLoading" class="w-4 h-4 animate-spin" />
          <ShieldCheck v-else class="w-4 h-4" />
          <span>{{ isLoading ? 'Memverifikasi Kredensial...' : 'Masuk ke Sistem' }}</span>
        </button>
      </form>

      <!-- Session Info Banner -->
      <div class="mt-6 pt-4 border-t border-slate-800/80 text-center">
        <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400">
          <span class="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse"></span>
          <span>Sesi aktif aman harian (maksimal 8 jam)</span>
        </div>
        <p class="text-[10px] text-slate-500 mt-2">
          Admin diarahkan ke Dashboard Manajemen, User diarahkan ke Chat AI.
        </p>
      </div>

      <!-- Security Footer Badge -->
      <div class="mt-3 text-center">
        <span class="text-[10px] font-medium text-slate-500 inline-flex items-center gap-1">
          <ShieldCheck class="w-3 h-3 text-teal-400" />
          Terenkripsi PBKDF2-HMAC-SHA256 & JWT PT TPS
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Ship, User, Lock, ShieldCheck, AlertCircle, Loader2 } from './Icons.js'

const emit = defineEmits(['login-success'])

const logoUrl = ref('/assets/tps-logo.png')
const hasLogoError = ref(false)

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  errorMessage.value = ''
  isLoading.value = true

  try {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value.trim(),
        password: password.value
      })
    })

    const data = await res.json()

    if (!res.ok) {
      errorMessage.value = data.detail || 'Gagal masuk. Periksa username dan password.'
      isLoading.value = false
      return
    }

    const todayStr = new Date().toISOString().split('T')[0]
    const nowTime = Date.now().toString()

    // Simpan token, user profile, dan timestamp sesi harian
    localStorage.setItem('tps_token', data.access_token)
    localStorage.setItem('tps_user', JSON.stringify(data.user))
    localStorage.setItem('tps_login_date', todayStr)
    localStorage.setItem('tps_login_time', nowTime)

    const currentPath = window.location.pathname

    if (data.user.role === 'admin') {
      // Simpan kredensial admin
      localStorage.setItem('tps_admin_token', data.access_token)
      localStorage.setItem('tps_admin_user', JSON.stringify(data.user))

      // Smart Redirect: jika bukan di /administrator, arahkan langsung
      if (currentPath !== '/administrator' && currentPath !== '/administrator/') {
        window.location.href = '/administrator'
        return
      }
    } else {
      // Peran User biasa: jika sedang membuka /administrator, arahkan ke halaman utama /
      if (currentPath === '/administrator' || currentPath === '/administrator/') {
        window.location.href = '/'
        return
      }
    }

    emit('login-success', data.user)
  } catch (err) {
    errorMessage.value = 'Gagal terhubung ke server otentikasi. Pastikan backend aktif.'
  } finally {
    isLoading.value = false
  }
}
</script>
