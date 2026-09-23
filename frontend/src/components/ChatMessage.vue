<template>
  <div
    class="flex gap-3.5 sm:gap-4.5 p-4 sm:p-5.5 rounded-2xl transition-all duration-200"
    :class="[
      message.role === 'user' 
        ? 'bg-[#121c32] border border-slate-700/60 ml-auto max-w-[85%] sm:max-w-[76%] shadow-card' 
        : 'bg-[#0e172a] border border-slate-800/80 w-full shadow-card'
    ]"
  >
    <!-- Avatar Icon -->
    <div
      class="w-8 h-8 sm:w-8.5 sm:h-8.5 rounded-xl flex items-center justify-center shrink-0 font-medium text-xs shadow-sm"
      :class="[
        message.role === 'user'
          ? 'bg-slate-800 text-slate-300 border border-slate-700'
          : 'bg-sky-950/80 text-sky-400 border border-sky-800/60'
      ]"
    >
      <User v-if="message.role === 'user'" class="w-4 h-4 text-slate-300" />
      <Ship v-else class="w-4.5 h-4.5 text-sky-400" />
    </div>

    <!-- Message Content Body -->
    <div class="flex-1 min-w-0">
      <!-- Role Header & Metadata -->
      <div class="flex items-center justify-between mb-2 pb-1 border-b border-slate-800/40">
        <div class="flex items-center gap-2.5">
          <span class="text-xs font-semibold tracking-tight" :class="message.role === 'user' ? 'text-slate-200' : 'text-sky-300'">
            {{ message.role === 'user' ? 'Pertanyaan Anda' : 'Asisten Komersial TPS' }}
          </span>
          <!-- Discreet quiet technical meta -->
          <span v-if="message.role === 'assistant' && message.is_cached" class="px-2 py-0.5 text-[10px] font-mono text-emerald-300 bg-emerald-950/60 rounded border border-emerald-800/60 flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            Cache (0 ms)
          </span>
          <span v-else-if="message.role === 'assistant'" class="px-2 py-0.5 text-[10px] font-mono text-slate-400 bg-slate-900 rounded border border-slate-800 flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-sky-400"></span>
            DuckDB OLAP
          </span>
        </div>
        <span class="text-[11px] text-slate-400 font-mono">{{ message.timestamp }}</span>
      </div>

      <!-- User Query Text / Assistant Narrative Answer (Editorial Typography) -->
      <div
        class="text-xs sm:text-[13px] text-slate-200 leading-relaxed font-sans narrative-reading"
        v-html="formattedContent"
      ></div>

      <!-- Assistant Extra Artifacts (SQL, ECharts, Raw Data) -->
      <template v-if="message.role === 'assistant'">
        <!-- SQL Accordion -->
        <SqlAccordion :sql="message.sql" />

        <!-- On-Demand Chart Trigger Action Bar (If Data Exists) -->
        <div v-if="message.data && message.data.length > 0" class="mt-3.5 flex flex-wrap items-center gap-2">
          <!-- Button 1: Toggle/Generate Chart -->
          <button
            v-if="!message.chartConfig"
            @click="handleGenerateChart"
            :disabled="isGeneratingChart"
            class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-sky-950/70 hover:bg-sky-900/80 border border-sky-800/70 text-xs font-medium text-sky-200 transition-colors shadow-sm disabled:opacity-50 cursor-pointer"
          >
            <Loader2 v-if="isGeneratingChart" class="w-3.5 h-3.5 animate-spin text-sky-300" />
            <BarChart3 v-else class="w-3.5 h-3.5 text-sky-400" />
            <span>{{ isGeneratingChart ? 'Merakit Visualisasi...' : 'Visualisasikan Grafik ECharts' }}</span>
          </button>

          <button
            v-else
            @click="showChart = !showChart"
            class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-medium text-slate-300 transition-colors cursor-pointer"
          >
            <BarChart3 class="w-3.5 h-3.5 text-sky-400" />
            <span>{{ showChart ? 'Sembunyikan Grafik' : 'Tampilkan Grafik' }}</span>
          </button>
        </div>

        <!-- ECharts Dynamic Chart View -->
        <EChartsViewer v-if="showChart" :chart-config="message.chartConfig" />

        <!-- Raw Data Table View with Multi-Format Export & Print -->
        <DataTableModal :data="message.data" :user-query="message.userQuery || ''" :narrative="message.content || ''" />

        <!-- Business Notice (when data empty or syntax notice) -->
        <div v-if="message.error" class="mt-3.5 p-3 rounded-xl bg-slate-900/90 border border-amber-500/30 text-xs text-slate-300 flex items-start gap-2.5">
          <AlertCircle class="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span class="font-semibold text-amber-300">Catatan Hasil Kueri:</span>
            <p class="mt-1 font-mono text-[11px] text-slate-300 leading-relaxed">{{ message.error }}</p>
          </div>
        </div>

        <!-- Interactive Suggestion Chips saat Data Kosong -->
        <div v-if="message.suggestions && message.suggestions.length > 0" class="mt-3.5 p-3 rounded-xl bg-[#0b1324] border border-slate-800">
          <p class="text-[11px] font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 rounded-full bg-sky-400"></span>
            Kueri Alternatif yang Tersedia:
          </p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="(chip, idx) in message.suggestions"
              :key="idx"
              @click="$emit('select-suggestion', chip)"
              class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-sky-500/50 text-xs font-normal text-slate-300 hover:text-white transition-colors cursor-pointer shadow-sm text-left"
            >
              <span class="text-sky-400">→</span>
              <span>{{ chip }}</span>
            </button>
          </div>
        </div>

        <!-- User Feedback Rating Action Bar -->
        <div v-if="!message.isStreaming && message.role === 'assistant'" class="mt-4 pt-3 border-t border-slate-800/60">
          <div v-if="!feedbackSubmitted" class="flex flex-wrap items-center gap-2.5">
            <span class="text-[11px] text-slate-400">Apakah jawaban ini akurat?</span>
            <button
              @click="submitRating('THUMBS_UP')"
              :disabled="isSubmittingFeedback"
              class="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 hover:text-white transition-colors cursor-pointer disabled:opacity-50"
              title="Jawaban Akurat & Membantu"
            >
              <span>👍</span>
              <span class="text-[11px] font-medium">Akurat</span>
            </button>
            <button
              @click="openDislikeDialog"
              :disabled="isSubmittingFeedback"
              class="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 hover:text-rose-300 transition-colors cursor-pointer disabled:opacity-50"
              title="Jawaban Kurang Sesuai"
            >
              <span>👎</span>
              <span class="text-[11px] font-medium">Kurang Sesuai</span>
            </button>
          </div>

          <!-- Rating Result Status -->
          <div v-else class="flex items-center gap-2 text-xs">
            <span v-if="submittedRating === 'THUMBS_UP'" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-950/50 border border-emerald-800/70 text-emerald-300 font-medium text-[11px]">
              <span>✓</span> Terima kasih, umpan balik Anda telah tercatat.
            </span>
            <span v-else class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300 font-medium text-[11px]">
              <span>✓</span> Catatan evaluasi telah dikirimkan ke administrator.
            </span>
          </div>

          <!-- Inline Box for Dislike Feedback Note -->
          <div v-if="showDislikeDialog" class="mt-2.5 p-3 bg-[#0b1324] border border-slate-700/80 rounded-xl shadow-lg space-y-2">
            <div class="flex items-center justify-between">
              <p class="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                <span>Evaluasi Kueri:</span> Apa yang perlu disesuaikan? (Opsional)
              </p>
              <button @click="showDislikeDialog = false" class="text-slate-400 hover:text-white text-xs cursor-pointer">✕</button>
            </div>
            <textarea
              v-model="feedbackNote"
              placeholder="Contoh: Tahun atau metrik TEUs kurang pas dengan konteks pertanyaan..."
              rows="2"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
            ></textarea>
            <div class="flex justify-end gap-2">
              <button
                @click="submitRating('THUMBS_DOWN', feedbackNote)"
                :disabled="isSubmittingFeedback"
                class="px-3 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded-md text-xs font-medium transition-colors cursor-pointer disabled:opacity-50"
              >
                {{ isSubmittingFeedback ? 'Mengirim...' : 'Kirim Catatan' }}
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { User, Bot, AlertCircle, BarChart3, Loader2 } from './Icons.js'
import SqlAccordion from './SqlAccordion.vue'
import EChartsViewer from './EChartsViewer.vue'
import DataTableModal from './DataTableModal.vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['select-suggestion'])

const showChart = ref(true)
const isGeneratingChart = ref(false)

// State Feedback Pengguna (Tugas 2.3)
const feedbackSubmitted = ref(props.message.feedbackGiven || false)
const submittedRating = ref(props.message.feedbackRating || '')
const isSubmittingFeedback = ref(false)
const showDislikeDialog = ref(false)
const feedbackNote = ref('')

const openDislikeDialog = () => {
  showDislikeDialog.value = true
}

const submitRating = async (rating, note = '') => {
  if (isSubmittingFeedback.value) return
  isSubmittingFeedback.value = true

  try {
    const token = localStorage.getItem('tps_token')
    const sessionId = localStorage.getItem('tps_session_id') || props.message.sessionId || 'default_session'
    
    await fetch('/api/v1/feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        session_id: sessionId,
        query: props.message.userQuery || props.message.content || 'Kueri Pengguna',
        sql_executed: props.message.sql || null,
        rating: rating,
        feedback_note: note || null
      })
    })

    feedbackSubmitted.value = true
    submittedRating.value = rating
    showDislikeDialog.value = false
    props.message.feedbackGiven = true
    props.message.feedbackRating = rating
  } catch (err) {
    console.error('Gagal mengirim feedback pengguna:', err)
  } finally {
    isSubmittingFeedback.value = false
  }
}

const handleGenerateChart = async () => {
  if (isGeneratingChart.value || !props.message.data) return
  isGeneratingChart.value = true

  try {
    const token = localStorage.getItem('tps_token')
    const res = await fetch('/api/v1/visualize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        query: props.message.userQuery || props.message.content,
        data: props.message.data
      })
    })

    if (!res.ok) throw new Error('Gagal merakit grafik.')
    const json = await res.json()

    if (json.chart_config && Object.keys(json.chart_config).length > 0) {
      props.message.chartConfig = json.chart_config
      showChart.value = true
    }
  } catch (err) {
    console.error('Error visualisasi on-demand:', err)
  } finally {
    isGeneratingChart.value = false
  }
}

const formattedContent = computed(() => {
  if (!props.message?.content) return ''
  let text = props.message.content

  // 1. Normalisasi Titik Dua (:) sebelum nomor list (misal: "Service: 1." -> "Service:\n\n1.")
  text = text.replace(/:\s*(\d+\.\s+)/g, ':\n\n$1')

  // 2. Auto-Break Nomor List (misal: " 2. BEN Line" -> "\n\n2. BEN Line")
  text = text.replace(/(?<=[^\n])\s+(\d+\.\s+)/g, '\n\n$1')

  // 3. Normalisasi Sub-Item Titik Koma (misal: "; Service PAX" -> "\n   - Service PAX")
  text = text.replace(/;\s*(Service\s+)/gi, '\n   - $1')

  // 4. Escape HTML tags untuk keamanan
  text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  // 5. Bold **text** -> font-semibold text-white (Clean Editorial)
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>')

  // 6. Italic *text* -> text-slate-300
  text = text.replace(/\*(.*?)\*/g, '<em class="italic text-slate-300">$1</em>')

  // 7. Styling Nomor List "1. " -> Badge Rapi Elegan
  text = text.replace(/(?:^|(?<=\n))\s*(\d+)\.?(?=\s|[A-Z]|\*\*)/gm, '<span class="inline-flex items-center justify-center w-5 h-5 rounded bg-slate-800/90 border border-slate-700/80 text-slate-200 font-mono text-[11px] font-semibold mr-2 my-0.5">$1</span> ')

  // 8. Styling Sub-bullet "- " -> Point Bullet Sky Blue
  text = text.replace(/^\s*-\s+/gm, '<span class="inline-block w-1.5 h-1.5 rounded-full bg-sky-400 mr-2 ml-3"></span>')

  // 9. Convert Newlines ke Spacing Div / BR
  text = text.replace(/\n\n/g, '<div class="h-2"></div>')
  text = text.replace(/\n/g, '<br />')

  return text
})
</script>
