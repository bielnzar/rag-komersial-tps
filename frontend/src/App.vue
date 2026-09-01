<template>
  <!-- 404 Not Found Page for invalid URLs like /akjsdklajds -->
  <div v-if="isNotFoundRoute" class="min-h-screen bg-slate-950 flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-slate-900/90 border border-slate-800 rounded-3xl p-8 text-center shadow-2xl backdrop-blur-xl animate-fade-in-up">
      <div class="inline-flex items-center justify-center p-4 rounded-2xl bg-red-950/40 border border-red-900/50 mb-4 text-red-400">
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
      </div>
      <h1 class="text-3xl font-extrabold text-white mb-2">404 - Halaman Tidak Ditemukan</h1>
      <p class="text-sm text-slate-400 mb-6 font-mono bg-slate-950/80 p-2.5 rounded-xl border border-slate-800 break-all">
        {{ currentPath }}
      </p>
      <p class="text-xs text-slate-400 mb-6">
        Jalur lokasi URL yang Anda masukkan tidak valid atau tidak diizinkan oleh sistem PT TPS.
      </p>
      <button @click="goHome" class="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-sm shadow-lg shadow-teal-500/20 transition-all hover:scale-[1.02]">
        ← Kembali ke Halaman Utama
      </button>
    </div>
  </div>

  <!-- Full-Page Hidden Admin Route (/administrator) -->
  <div v-else-if="isAdminRoute" class="min-h-screen bg-slate-950">
    <LoginModal v-if="!isLoggedIn" :is-admin-mode="true" @login-success="handleLoginSuccess" />
    <AdminDashboard v-else />
  </div>

  <!-- Standard Main Chat App Route (/) -->
  <div v-else class="min-h-screen flex flex-col justify-between bg-mesh relative overflow-x-hidden">
    <LoginModal v-if="!isLoggedIn" @login-success="handleLoginSuccess" />

    <!-- Sidebar History Component -->
    <SidebarHistory
      v-if="isLoggedIn"
      :is-open="isSidebarOpen"
      :sessions="sessions"
      :active-session-id="activeSessionId"
      :current-user="currentUser"
      @toggle-sidebar="isSidebarOpen = !isSidebarOpen"
      @new-session="handleNewSession"
      @select-session="handleSelectSession"
      @delete-session="handleDeleteSession"
    />

    <!-- Main Container Layout (bergeser saat sidebar terbuka di desktop) -->
    <div 
      :class="[
        'flex-1 flex flex-col justify-between transition-all duration-300',
        isLoggedIn && isSidebarOpen ? 'md:pl-64' : 'md:pl-14'
      ]"
    >
      <!-- Navbar Header -->
      <Navbar 
        :current-user="currentUser" 
        @reset-chat="handleNewSession" 
        @logout="handleLogout" 
        @toggle-sidebar="isSidebarOpen = !isSidebarOpen"
        @open-admin="showAdminDashboard = true"
      />

      <!-- Main Content Chat Area -->
      <main class="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-6 flex flex-col justify-between">
        <!-- Empty Hero State when no messages -->
        <div v-if="messages.length === 0" class="my-auto py-6 text-center animate-fade-in-up">
          <!-- Hero Logo Container (Clean & Glowing) -->
          <div class="inline-flex items-center justify-center p-3 sm:p-4 rounded-3xl bg-slate-900/80 border border-slate-700/50 mb-4 shadow-2xl backdrop-blur-md">
            <img 
              :src="logoUrl" 
              alt="Logo PT TPS" 
              class="h-12 sm:h-16 w-auto object-contain filter drop-shadow-[0_0_12px_rgba(20,184,166,0.25)]"
              @error="hasHeroLogoError = true"
              v-if="!hasHeroLogoError"
            />
            <Ship v-else class="w-10 h-10 text-teal-400" />
          </div>

          <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight mb-2">
            Selamat Datang di <span class="text-transparent bg-clip-text bg-gradient-to-r from-teal-300 via-cyan-300 to-blue-400">TPS Executive Intelligence Agent</span>
          </h2>
          <p class="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto leading-relaxed mb-5 font-medium">
            Sistem intelijen & analisis data operasional PT Terminal Petikemas Surabaya.
          </p>

          <!-- Prompt Suggestions Grid -->
          <PromptSuggestions @select-prompt="handleSelectPrompt" />
        </div>

        <!-- Messages History List -->
        <div v-else class="space-y-4 mb-6">
          <ChatMessage
            v-for="(msg, idx) in messages"
            :key="idx"
            :message="msg"
          />
          <div ref="scrollAnchor"></div>
        </div>
      </main>

      <!-- Floating Chat Input Bar -->
      <ChatInput
        :is-loading="isLoading"
        :selected-prompt="selectedPrompt"
        @send-query="handleSendQuery"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import Navbar from './components/Navbar.vue'
import SidebarHistory from './components/SidebarHistory.vue'
import LoginModal from './components/LoginModal.vue'
import PromptSuggestions from './components/PromptSuggestions.vue'
import ChatMessage from './components/ChatMessage.vue'
import ChatInput from './components/ChatInput.vue'
import AdminDashboard from './components/AdminDashboard.vue'
import { Ship } from './components/Icons.js'

// ==========================================
// STATE MANAGEMENT
// ==========================================
const isLoggedIn = ref(false)
const currentUser = ref(null)
const isSidebarOpen = ref(true)
const currentPath = ref(window.location.pathname)
const isAdminRoute = ref(currentPath.value === '/administrator' || currentPath.value === '/administrator/')
const isHomeRoute = ref(currentPath.value === '/' || currentPath.value === '')
const isNotFoundRoute = ref(!isAdminRoute.value && !isHomeRoute.value)

const goHome = () => {
  window.location.href = '/'
}

const sessions = ref([])
const activeSessionId = ref('')
const messages = ref([])
const isLoading = ref(false)
const selectedPrompt = ref('')
const scrollAnchor = ref(null)
const logoUrl = ref('/assets/tps-logo.png')
const hasHeroLogoError = ref(false)

onMounted(async () => {
  if (isAdminRoute.value) {
    const adminToken = localStorage.getItem('tps_admin_token')
    const adminUser = localStorage.getItem('tps_admin_user')

    if (adminToken && adminUser) {
      try {
        currentUser.value = JSON.parse(adminUser)
        isLoggedIn.value = true
      } catch (e) {
        localStorage.removeItem('tps_admin_token')
        localStorage.removeItem('tps_admin_user')
        isLoggedIn.value = false
      }
    }
  } else {
    const token = localStorage.getItem('tps_token')
    const user = localStorage.getItem('tps_user')

    if (token && user) {
      try {
        currentUser.value = JSON.parse(user)
        isLoggedIn.value = true
        await fetchUserSessions()
      } catch (e) {
        handleLogout()
      }
    }
  }
})

const fetchUserSessions = async () => {
  const token = localStorage.getItem('tps_token')
  if (!token) return

  try {
    const res = await fetch('/api/v1/sessions', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    if (data.status === 'success') {
      sessions.value = data.sessions || []
    }
  } catch (e) {
    console.error('Error fetching sessions:', e)
  }
}

const handleLoginSuccess = async (userProfile) => {
  currentUser.value = userProfile
  isLoggedIn.value = true
  await fetchUserSessions()
}

const handleLogout = () => {
  if (isAdminRoute.value) {
    localStorage.removeItem('tps_admin_token')
    localStorage.removeItem('tps_admin_user')
  } else {
    localStorage.removeItem('tps_token')
    localStorage.removeItem('tps_user')
  }
  currentUser.value = null
  isLoggedIn.value = false
  messages.value = []
  sessions.value = []
  activeSessionId.value = ''
}

const handleNewSession = () => {
  activeSessionId.value = `sess_${currentUser.value?.username || 'user'}_${Date.now()}`
  messages.value = []
  selectedPrompt.value = ''
}

const handleSelectSession = async (sessionId) => {
  const token = localStorage.getItem('tps_token')
  if (!token) return

  activeSessionId.value = sessionId
  isLoading.value = true

  try {
    const res = await fetch(`/api/v1/sessions/${sessionId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    if (data.status === 'success') {
      messages.value = data.messages || []
      scrollToBottom()
    }
  } catch (e) {
    console.error('Error loading session messages:', e)
  } finally {
    isLoading.value = false
  }
}

const handleDeleteSession = async (sessionId) => {
  const token = localStorage.getItem('tps_token')
  if (!token) return

  try {
    await fetch(`/api/v1/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    sessions.value = sessions.value.filter(s => s.session_id !== sessionId)
    if (activeSessionId.value === sessionId) {
      handleNewSession()
    }
  } catch (e) {
    console.error('Error deleting session:', e)
  }
}

const scrollToBottom = async () => {
  await nextTick()
  scrollAnchor.value?.scrollIntoView({ behavior: 'smooth' })
}

const handleSelectPrompt = (promptText) => {
  selectedPrompt.value = promptText
}

const handleSendQuery = async (queryText) => {
  const userTimestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  const token = localStorage.getItem('tps_token')

  if (!token) {
    handleLogout()
    return
  }

  if (!activeSessionId.value) {
    activeSessionId.value = `sess_${currentUser.value?.username || 'user'}_${Date.now()}`
  }

  messages.value.push({
    role: 'user',
    content: queryText,
    timestamp: userTimestamp
  })
  scrollToBottom()

  isLoading.value = true

  try {
    const response = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        query: queryText,
        session_id: activeSessionId.value
      })
    })

    if (response.status === 401 || response.status === 403) {
      handleLogout()
      return
    }

    const data = await response.json()
    const botTimestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    if (data.status === 'success') {
      messages.value.push({
        role: 'assistant',
        userQuery: queryText,
        content: data.answer,
        sql: data.sql_executed,
        data: data.data,
        chartConfig: data.chart_config,
        timestamp: botTimestamp
      })
    } else {
      messages.value.push({
        role: 'assistant',
        userQuery: queryText,
        content: data.answer || 'Maaf, terjadi kesalahan saat memproses data.',
        error: data.error || 'Eksekusi query gagal.',
        timestamp: botTimestamp
      })
    }

    await fetchUserSessions()
  } catch (err) {
    const botTimestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    messages.value.push({
      role: 'assistant',
      userQuery: queryText,
      content: 'Maaf, tidak dapat terhubung ke server backend.',
      error: err.message,
      timestamp: botTimestamp
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}
</script>
