<template>
  <div v-if="data && data.length > 0" class="mt-3.5">
    <button
      @click="isOpen = !isOpen"
      class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 text-xs font-medium text-slate-300 transition-colors"
    >
      <Table class="w-3.5 h-3.5 text-teal-400" />
      <span>Tabel Data Mentah DuckDB ({{ data.length }} Baris)</span>
      <ChevronRight class="w-3.5 h-3.5 transition-transform duration-200" :class="{ 'rotate-90': isOpen }" />
    </button>

    <!-- Collapsible Table View -->
    <div v-show="isOpen" class="mt-2.5 card-executive rounded-xl overflow-hidden border border-slate-800">
      <div class="max-h-72 overflow-x-auto overflow-y-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-900/90 text-teal-300 font-mono border-b border-slate-800 sticky top-0 z-10">
              <th v-for="col in headers" :key="col" class="px-4 py-2.5 font-semibold whitespace-nowrap">
                {{ col }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800/50 text-slate-300 font-mono">
            <tr v-for="(row, idx) in data" :key="idx" class="hover:bg-slate-900/40 transition-colors">
              <td v-for="col in headers" :key="col" class="px-4 py-2.5 whitespace-nowrap">
                <span v-if="row[col] === null || row[col] === undefined" class="text-slate-600 italic">null</span>
                <span v-else>{{ row[col] }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Table, ChevronRight } from './Icons.js'

const props = defineProps({
  data: { type: Array, default: () => [] }
})

const isOpen = ref(false)

const headers = computed(() => {
  if (!props.data || props.data.length === 0) return []
  return Object.keys(props.data[0])
})
</script>
