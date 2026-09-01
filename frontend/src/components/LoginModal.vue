<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fade-in">
    <div class="card-executive max-w-md w-full p-6 sm:p-8 rounded-3xl border border-slate-700/60 shadow-2xl bg-slate-900/95 relative overflow-hidden">
      <!-- Top Decorative Accent Blur -->
      <div class="absolute -top-12 -right-12 w-36 h-36 bg-teal-500/10 rounded-full blur-2xl pointer-events-none"></div>
      <div class="absolute -bottom-12 -left-12 w-36 h-36 bg-blue-500/10 rounded-full blur-2xl pointer-events-none"></div>

      <!-- Header Section dengan Logo TPS Asli -->
      <div class="text-center mb-6">
        <div class="inline-flex items-center justify-center p-3 sm:p-4 rounded-3xl bg-slate-950/90 border mb-3 shadow-xl" :class="isAdminMode ? 'border-red-700/60' : 'border-slate-700/60'">
          <img 
            :src="logoUrl" 
            alt="Logo PT TPS" 
            class="h-12 sm:h-14 w-auto object-contain"
            @error="hasLogoError = true"
            v-if="!hasLogoError"
          />
          <div v-else class="flex items-center gap-2 px-2 py-1">
            <Ship class="w-8 h-8" :class="isAdminMode ? 'text-red-400' : 'text-teal-400'" />
            <span class="font-extrabold text-lg text-slate-100 tracking-wider">PT TPS</span>
          </div>
        </div>

        <h2 class="text-xl sm:text-2xl font-extrabold tracking-tight" :class="isAdminMode ? 'text-red-300' : 'text-slate-100'">
          {{ isAdminMode ? 'Portal Login System Administrator' : 'Portal Keamanan PT TPS' }}
        </h2>
        <p class="text-xs text-slate-400 font-medium mt-1">
          {{ isAdminMode ? 'Pengelolaan API Key, Telemetri & Otomasi Sistem' : 'Executive Intelligence Agent — Terminal Petikemas Surabaya' }}
        </p>
      </div>

      <!-- Error Alert Message -->
      <div v-if="errorMessage" class="mb-5 p-3.5 rounded-xl bg-red-950/60 border border-red-800/60 text-red-200 text-xs flex items-start gap-2.5 animate-shake">
        <AlertCircle class="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
        <div class="font-medium">{{ errorMessage }}</div>
      </div>

      <!-- Login Form -->
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
              placeholder="Masukkan username"
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
              type="password"
              v-model="password"
              required
              placeholder="Masukkan password"
              class="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs font-medium focus:outline-none focus:border-teal-500 transition-colors"
            />
          </div>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="isLoading"
          :class="isAdminMode ? 'bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 shadow-red-500/20 text-white' : 'bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-400 hover:to-cyan-500 text-slate-950 shadow-teal-500/20'"
          class="w-full py-3 rounded-xl font-bold text-xs shadow-lg transition-all flex items-center justify-center gap-2"
        >
          <Loader2 v-if="isLoading" class="w-4 h-4 animate-spin" />
          <ShieldCheck v-else class="w-4 h-4" />
          <span>{{ isLoading ? 'Memverifikasi Identitas...' : (isAdminMode ? 'Masuk Portal Administrator' : 'Masuk ke Sistem AI') }}</span>
        </button>
      </form>

      <!-- Quick Demo Login Presets -->
      <div class="mt-6 pt-5 border-t border-slate-800/80">
        <p class="text-[11px] font-semibold text-slate-400 mb-2.5 text-center">
          Pilih Akun Demo Cepat (Auto-Fill):
        </p>
        <div class="grid grid-cols-2 gap-2 text-[11px]">
          <button
            v-if="isAdminMode"
            @click="quickFill('admin', 'admin123')"
            type="button"
            class="p-2 rounded-xl bg-slate-950 hover:bg-slate-800 border border-red-900/60 text-left transition-colors flex items-center gap-2 col-span-2"
          >
            <span class="text-red-400 font-bold">Admin (System Administrator)</span>
            <span class="text-[9px] text-slate-500 ml-auto">Full Admin</span>
          </button>
          <button
            @click="quickFill('executive', 'tps123')"
            type="button"
            class="p-2 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left transition-colors flex items-center gap-2"
          >
            <span class="text-amber-400 font-bold">Direksi</span>
            <span class="text-[9px] text-slate-500 ml-auto">Full</span>
          </button>
          <button
            v-if="!isAdminMode"
            @click="quickFill('komersial', 'tps123')"
            type="button"
            class="p-2 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left transition-colors flex items-center gap-2"
          >
            <span class="text-cyan-400 font-bold">Komersial</span>
            <span class="text-[9px] text-slate-500 ml-auto">Comm</span>
          </button>
          <button
            v-if="!isAdminMode"
            @click="quickFill('operasional', 'tps123')"
            type="button"
            class="p-2 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left transition-colors flex items-center gap-2"
          >
            <span class="text-emerald-400 font-bold">Operasional</span>
            <span class="text-[9px] text-slate-500 ml-auto">Ops</span>
          </button>
          <button
            v-if="!isAdminMode"
            @click="quickFill('guest', 'guest123')"
            type="button"
            class="p-2 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left transition-colors flex items-center gap-2"
          >
            <span class="text-purple-400 font-bold">Tamu</span>
            <span class="text-[9px] text-slate-500 ml-auto">Guest</span>
          </button>
        </div>
      </div>

      <!-- Security Footer Badge -->
      <div class="mt-4 text-center">
        <span class="text-[10px] font-medium text-slate-500 inline-flex items-center gap-1">
          <ShieldCheck class="w-3 h-3 text-teal-400" />
          Dilindungi JWT Kriptografi 256-bit & RBAC PT TPS
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Ship, User, Lock, ShieldCheck, AlertCircle, Loader2 } from './Icons.js'

const props = defineProps({
  isAdminMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['login-success'])

const logoUrl = ref('/assets/tps-logo.png')
const hasLogoError = ref(false)

const username = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

const quickFill = (u, p) => {
  username.value = u
  password.value = p
  errorMessage.value = ''
}

const handleLogin = async () => {
  errorMessage.value = ''
  isLoading.value = true

  try {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    })

    const data = await res.json()

    if (!res.ok) {
      errorMessage.value = data.detail || 'Gagal masuk. Periksa username dan password.'
      isLoading.value = false
      return
    }

    if (props.isAdminMode) {
      if (!['admin', 'executive'].includes(data.user.role)) {
        errorMessage.value = '⛔ Akses Ditolak: Hanya akun System Administrator / Executive yang diizinkan masuk ke portal ini.'
        isLoading.value = false
        return
      }
      localStorage.setItem('tps_admin_token', data.access_token)
      localStorage.setItem('tps_admin_user', JSON.stringify(data.user))
    } else {
      localStorage.setItem('tps_token', data.access_token)
      localStorage.setItem('tps_user', JSON.stringify(data.user))
    }

    emit('login-success', data.user)
  } catch (err) {
    errorMessage.value = 'Gagal terhubung ke server otentikasi. Pastikan backend aktif.'
  } finally {
    isLoading.value = false
  }
}
</script>
