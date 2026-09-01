<template>
  <div class="my-6">
    <div class="flex items-center justify-between mb-3 px-1">
      <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
        <Sparkles class="w-3.5 h-3.5 text-teal-400" />
        Rekomendasi Pertanyaan Analisis Komersial
      </p>
      <span class="text-[11px] text-slate-500 font-medium">Klik untuk mencoba</span>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <button
        v-for="(item, idx) in suggestions"
        :key="idx"
        @click="$emit('select-prompt', item.query)"
        class="card-interactive text-left p-4 rounded-2xl group flex flex-col justify-between min-h-[140px] border border-slate-800/80 hover:border-teal-500/50 bg-slate-900/60 hover:bg-slate-900/90 transition-all shadow-md"
      >
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-[10px] font-bold text-teal-300 bg-teal-950/80 px-2 py-0.5 rounded-md border border-teal-800/50 uppercase tracking-wider">
              {{ item.tag }}
            </span>
            <span class="text-[10px] text-slate-500 font-mono">{{ item.tables }}</span>
          </div>
          <p class="text-xs text-slate-200 group-hover:text-white font-medium leading-relaxed">
            "{{ item.query }}"
          </p>
        </div>
        
        <div class="flex items-center text-[11px] text-slate-400 mt-3 font-semibold group-hover:text-teal-300 transition-colors">
          <span>Jalankan Analisis</span>
          <ArrowRight class="w-3.5 h-3.5 ml-auto transition-transform group-hover:translate-x-1 text-teal-400" />
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { Sparkles, ArrowRight } from './Icons.js'

defineEmits(['select-prompt'])

const suggestions = [
  {
    tag: 'Throughput Container',
    query: 'Berapa total actual throughput container domestik pada tahun 2022?',
    tables: 'fakta_throughput'
  },
  {
    tag: 'Operasional Kapal',
    query: 'Tampilkan 3 Line Operator (LOP) dengan total TEUs terbanyak pada operasional kapal domestik',
    tables: 'fakta_vessel'
  },
  {
    tag: 'Market Share SL INT',
    query: 'Sebutkan 3 Line Operator (LOP) dengan total TEUs terbesar pada data market share sheet SL INT',
    tables: 'fakta_market_share'
  }
]
</script>
