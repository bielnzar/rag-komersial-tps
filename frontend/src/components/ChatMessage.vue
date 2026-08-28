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

      <!-- User Query Text / Assistant Narrative Answer (Markdown Formatted) -->
      <div
        class="text-xs sm:text-sm text-slate-200 leading-relaxed font-sans whitespace-pre-wrap"
        v-html="formattedContent"
      ></div>

      <!-- Assistant Extra Artifacts (SQL, ECharts, Raw Data) -->
      <template v-if="message.role === 'assistant'">
        <!-- SQL Accordion -->
        <SqlAccordion :sql="message.sql" />

        <!-- ECharts Dynamic Chart View -->
        <EChartsViewer :chart-config="message.chartConfig" />

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
import { computed } from 'vue'
import { User, Bot, AlertCircle } from './Icons.js'
import SqlAccordion from './SqlAccordion.vue'
import EChartsViewer from './EChartsViewer.vue'
import DataTableModal from './DataTableModal.vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const formattedContent = computed(() => {
  if (!props.message?.content) return ''
  let text = props.message.content

  // Escape HTML tags sederhana untuk keamanan
  text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  // Parse **bold text** menjadi <strong class="font-bold text-cyan-300">bold text</strong>
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-cyan-300">$1</strong>')

  // Parse *italic text* menjadi <em class="italic text-slate-300">italic text</em>
  text = text.replace(/\*(.*?)\*/g, '<em class="italic text-slate-300">$1</em>')

  return text
})
</script>
