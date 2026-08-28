<template>
  <div class="sticky bottom-0 z-20 w-full p-4 sm:p-6 bg-gradient-to-t from-slate-950 via-slate-950/95 to-transparent">
    <div class="max-w-4xl mx-auto">
      <!-- Concise & Dynamic Loading Indicator Bar -->
      <div v-if="isLoading" class="mb-3 px-3.5 py-2.5 rounded-xl card-executive border border-teal-500/30 flex items-center justify-between animate-fade-in-up">
        <div class="flex items-center gap-2.5 text-xs font-medium text-teal-300">
          <Loader2 class="w-3.5 h-3.5 animate-spin text-teal-400" />
          <span class="transition-all duration-300">{{ currentLoadingMsg }}</span>
        </div>
        <span class="text-[11px] text-slate-400 font-mono">Mohon tunggu sebentar...</span>
      </div>

      <!-- Main Command Palette Input Form -->
      <form @submit.prevent="handleSubmit" class="relative flex items-center">
        <input
          v-model="inputQuery"
          type="text"
          :disabled="isLoading"
          placeholder="Ketik pertanyaan analisis data komersial pelabuhan (cth: throughput domestik 2022)..."
          class="w-full pl-4 pr-24 py-3.5 sm:py-4 rounded-xl card-executive text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-teal-500/60 focus:border-teal-500/60 shadow-xl transition-all disabled:opacity-50"
        />

        <div class="absolute right-2 flex items-center gap-1.5">
          <button
            type="submit"
            :disabled="isLoading || !inputQuery.trim()"
            class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold text-xs transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-md shadow-teal-500/20"
          >
            <span>Kirim</span>
            <Send class="w-3.5 h-3.5" />
          </button>
        </div>
      </form>

      <!-- Footer Info -->
      <div class="flex items-center justify-between text-[11px] text-slate-500 mt-2.5 px-1 font-medium">
        <span>PT Terminal Petikemas Surabaya • Divisi Komersial</span>
        <span class="hidden sm:inline">Press <kbd class="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 font-mono text-[10px] text-slate-400">Enter</kbd> to send</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { Send, Loader2 } from './Icons.js'

const props = defineProps({
  isLoading: { type: Boolean, default: false },
  selectedPrompt: { type: String, default: '' }
})

const emit = defineEmits(['send-query'])
const inputQuery = ref('')

// Rotasi Pesan Loading Interaktif & Alami
const loadingMessages = [
  'Menganalisis pertanyaan Anda...',
  'Menghubungkan ke database DuckDB...',
  'Mengekstrak data komersial pelabuhan...',
  'Menyiapkan ringkasan & visualisasi grafik...'
]

const currentLoadingMsg = ref(loadingMessages[0])
let msgInterval = null

watch(() => props.isLoading, (val) => {
  if (val) {
    let idx = 0
    currentLoadingMsg.value = loadingMessages[0]
    msgInterval = setInterval(() => {
      idx = (idx + 1) % loadingMessages.length
      currentLoadingMsg.value = loadingMessages[idx]
    }, 1400)
  } else {
    if (msgInterval) clearInterval(msgInterval)
  }
})

onBeforeUnmount(() => {
  if (msgInterval) clearInterval(msgInterval)
})

const handleSubmit = () => {
  if (!inputQuery.value.trim() || props.isLoading) return
  emit('send-query', inputQuery.value.trim())
  inputQuery.value = ''
}

watch(() => props.selectedPrompt, (newVal) => {
  if (newVal) {
    inputQuery.value = newVal
  }
})
</script>
