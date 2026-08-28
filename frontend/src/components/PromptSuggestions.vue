<template>
  <div class="my-6">
    <div class="flex items-center justify-between mb-3.5 px-1">
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
        class="card-interactive text-left p-4 rounded-xl group flex flex-col justify-between"
      >
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-[11px] font-semibold text-teal-400 bg-teal-950/60 px-2 py-0.5 rounded border border-teal-800/40">
              {{ item.tag }}
            </span>
            <span class="text-[10px] text-slate-500 font-mono">{{ item.tables }}</span>
          </div>
          <p class="text-xs sm:text-sm text-slate-200 group-hover:text-white font-medium leading-relaxed">
            "{{ item.query }}"
          </p>
        </div>
        
        <div class="flex items-center text-[11px] text-slate-400 mt-3 font-medium group-hover:text-teal-300">
          <span>Jalankan Analisis</span>
          <ArrowRight class="w-3.5 h-3.5 ml-auto transition-transform group-hover:translate-x-1" />
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
