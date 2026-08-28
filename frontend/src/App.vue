<template>
  <div class="min-h-screen flex flex-col justify-between bg-mesh">
    <!-- Navbar Header -->
    <Navbar @reset-chat="handleResetChat" />

    <!-- Main Content Chat Area -->
    <main class="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-6 flex flex-col justify-between">
      <!-- Empty Hero State when no messages -->
      <div v-if="messages.length === 0" class="my-auto py-8 text-center animate-fade-in-up">
        <!-- Hero Logo Container with Fallback -->
        <div class="inline-flex items-center justify-center p-3 sm:p-4 rounded-3xl bg-slate-900/90 border border-slate-700/60 mb-6 shadow-xl">
          <img 
            :src="logoUrl" 
            alt="Logo PT TPS" 
            class="h-16 sm:h-20 w-auto object-contain"
            @error="hasHeroLogoError = true"
            v-if="!hasHeroLogoError"
          />
          <Ship v-else class="w-10 h-10 text-teal-400" />
        </div>

        <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight mb-2">
          Selamat Datang di <span class="text-transparent bg-clip-text bg-gradient-to-r from-teal-300 via-cyan-300 to-blue-400">TPS Executive Intelligence Agent</span>
        </h2>
        <p class="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto leading-relaxed mb-6 font-medium">
          Sistem analisis data operasional & komersial PT Terminal Petikemas Surabaya.
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
</template>

<script setup>
import { ref, nextTick } from 'vue'
import Navbar from './components/Navbar.vue'
import PromptSuggestions from './components/PromptSuggestions.vue'
import ChatMessage from './components/ChatMessage.vue'
import ChatInput from './components/ChatInput.vue'
import { Ship } from './components/Icons.js'

const messages = ref([])
const isLoading = ref(false)
const selectedPrompt = ref('')
const scrollAnchor = ref(null)
const logoUrl = ref('/assets/tps-logo.png')
const hasHeroLogoError = ref(false)

const scrollToBottom = async () => {
  await nextTick()
  scrollAnchor.value?.scrollIntoView({ behavior: 'smooth' })
}

const handleSelectPrompt = (promptText) => {
  selectedPrompt.value = promptText
}

const handleResetChat = () => {
  messages.value = []
  selectedPrompt.value = ''
}

const handleSendQuery = async (queryText) => {
  const userTimestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  // Push User Message
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
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: queryText,
        user_id: 'user_komersial',
        role: 'commercial'
      })
    })

    if (!response.ok) {
      const errData = await response.json()
      throw new Error(errData.detail || 'Terjadi kesalahan pada server backend.')
    }

    const data = await response.json()
    const assistantTimestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    // Push Assistant Response Message
    messages.value.push({
      role: 'assistant',
      content: data.answer || 'Berhasil memproses query.',
      sql: data.sql_executed,
      chartConfig: data.chart_config,
      data: data.data,
      error: data.error,
      timestamp: assistantTimestamp
    })
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: 'Maaf, terjadi kendala saat menghubungi server AI.',
      error: err.message,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}
</script>
