<template>
  <div
    class="flex gap-3 sm:gap-4 p-4 sm:p-6 rounded-2xl transition-all duration-200"
    :class="[
      message.role === 'user' 
        ? 'bg-slate-900/90 border border-slate-800 ml-auto max-w-[85%] sm:max-w-[78%] shadow-sm' 
        : 'card-executive border border-slate-800/90 w-full'
    ]"
  >
    <!-- Avatar Icon -->
    <div
      class="w-8 h-8 sm:w-9 sm:h-9 rounded-xl flex items-center justify-center shrink-0 font-semibold text-xs shadow-sm"
      :class="[
        message.role === 'user'
          ? 'bg-slate-800 text-cyan-400 border border-slate-700'
          : 'bg-teal-950 text-teal-300 border border-teal-800/50'
      ]"
    >
      <User v-if="message.role === 'user'" class="w-4 h-4" />
      <Bot v-else class="w-4.5 h-4.5" />
    </div>

    <!-- Message Content Body -->
    <div class="flex-1 min-w-0">
      <!-- Role Header & Timestamp -->
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold tracking-tight" :class="message.role === 'user' ? 'text-slate-200' : 'text-teal-300'">
            {{ message.role === 'user' ? 'Anda' : 'Asisten AI Komersial TPS' }}
          </span>
          <span v-if="message.role === 'assistant'" class="px-2 py-0.5 text-[10px] font-mono text-slate-400 bg-slate-900 rounded border border-slate-800">
            Self-Healing Active
          </span>
        </div>
        <span class="text-[11px] text-slate-500 font-mono">{{ message.timestamp }}</span>
      </div>

      <!-- User Query Text / Assistant Narrative Answer (Smart Structured Formatting) -->
      <div
        class="text-xs sm:text-sm text-slate-200 leading-relaxed font-sans"
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
            class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-teal-950/80 hover:bg-teal-900 border border-teal-800/80 text-xs font-medium text-teal-300 transition-all shadow-sm disabled:opacity-50 cursor-pointer"
          >
            <Loader2 v-if="isGeneratingChart" class="w-3.5 h-3.5 animate-spin text-teal-300" />
            <BarChart3 v-else class="w-3.5 h-3.5 text-teal-400" />
            <span>{{ isGeneratingChart ? 'Merakit ECharts...' : '📊 Visualisasikan Grafik' }}</span>
          </button>

          <button
            v-else
            @click="showChart = !showChart"
            class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 text-xs font-medium text-slate-300 transition-all cursor-pointer"
          >
            <BarChart3 class="w-3.5 h-3.5 text-cyan-400" />
            <span>{{ showChart ? '🙈 Sembunyikan Grafik' : '📊 Tampilkan Grafik' }}</span>
          </button>
        </div>

        <!-- ECharts Dynamic Chart View -->
        <EChartsViewer v-if="showChart" :chart-config="message.chartConfig" />

        <!-- Raw Data Table View -->
        <DataTableModal :data="message.data" />

        <!-- Error Message Notice -->
        <div v-if="message.error" class="mt-3.5 p-3.5 rounded-xl bg-amber-950/30 border border-amber-800/40 text-xs text-amber-200 flex items-start gap-2.5">
          <AlertCircle class="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span class="font-bold">Info Self-Healing / Umpan Balik System:</span>
            <p class="mt-1 font-mono text-[11px] opacity-90 leading-relaxed">{{ message.error }}</p>
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

const showChart = ref(true)
const isGeneratingChart = ref(false)

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

  // 5. Bold **text** -> <strong class="font-bold text-cyan-300">text</strong>
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-cyan-300">$1</strong>')

  // 6. Italic *text* -> <em class="italic text-slate-300">text</em>
  text = text.replace(/\*(.*?)\*/g, '<em class="italic text-slate-300">$1</em>')

  // 7. Styling Nomor List "1. ", "1.CMA", "1CMA" -> Badge Terstruktur Rapi dengan Spasi
  text = text.replace(/(?:^|(?<=\n))\s*(\d+)\.?(?=\s|[A-Z]|\*\*)/gm, '<span class="inline-flex items-center justify-center w-5 h-5 rounded-md bg-slate-900 border border-slate-700 text-teal-300 font-mono text-[11px] font-bold mr-2 my-0.5 shadow-sm">$1</span> ')

  // 8. Styling Sub-bullet "- " -> Point Bullet Cyan
  text = text.replace(/^\s*-\s+/gm, '<span class="inline-block w-1.5 h-1.5 rounded-full bg-cyan-400 mr-2 ml-4"></span>')

  // 9. Convert Newlines ke Spacing Div / BR
  text = text.replace(/\n\n/g, '<div class="h-2.5"></div>')
  text = text.replace(/\n/g, '<br />')

  return text
})
</script>
