<template>
  <div v-if="sql" class="mt-3.5 border border-slate-800 rounded-xl overflow-hidden bg-slate-950/80">
    <button
      @click="isOpen = !isOpen"
      class="w-full px-3.5 py-2.5 flex items-center justify-between bg-slate-900/90 hover:bg-slate-900 text-xs font-mono text-slate-300 transition-colors"
    >
      <div class="flex items-center gap-2">
        <Code2 class="w-3.5 h-3.5 text-teal-400" />
        <span class="font-semibold text-slate-200">DuckDB Executed Query</span>
        <span class="px-2 py-0.5 text-[10px] bg-teal-950/80 text-teal-300 rounded border border-teal-800/50">
          Sanitizer Passed
        </span>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click.stop="copySql"
          class="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[11px] text-slate-300 transition-colors border border-slate-700"
          title="Salin SQL"
        >
          <Check v-if="copied" class="w-3 h-3 text-emerald-400" />
          <Copy v-else class="w-3 h-3" />
          <span>{{ copied ? 'Tersalin' : 'Copy' }}</span>
        </button>
        <ChevronDown class="w-3.5 h-3.5 text-slate-400 transition-transform duration-200" :class="{ 'rotate-180': isOpen }" />
      </div>
    </button>

    <div v-show="isOpen" class="p-3.5 bg-slate-950 text-xs font-mono text-cyan-300 overflow-x-auto border-t border-slate-800/80">
      <pre class="leading-relaxed whitespace-pre-wrap"><code>{{ sql }}</code></pre>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Code2, ChevronDown, Copy, Check } from './Icons.js'

const props = defineProps({
  sql: { type: String, default: '' }
})

const isOpen = ref(false)
const copied = ref(false)

const copySql = () => {
  if (!props.sql) return
  navigator.clipboard.writeText(props.sql)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>
