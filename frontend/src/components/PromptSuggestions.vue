<template>
  <div class="my-6">
    <!-- Header Rekomendasi Analisis -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 px-1">
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
          <Sparkles class="w-4 h-4" />
        </div>
        <div>
          <h3 class="text-xs sm:text-sm font-semibold text-slate-100 tracking-wide flex items-center gap-2">
            Rekomendasi Analisis Komersial
            <span class="text-[10px] font-medium text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/60 font-mono">
              9 Kueri Terverifikasi
            </span>
          </h3>
        </div>
      </div>
      <span class="text-[11px] text-slate-400 font-normal hidden sm:inline">
        Pilih skenario domain untuk memuat kueri data operasional
      </span>
    </div>

    <!-- Category Segmented Control Navigation -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-4">
      <button
        v-for="cat in categories"
        :key="cat.id"
        type="button"
        @click="activeCategory = cat.id"
        :class="[
          'flex items-center justify-between px-3.5 py-2.5 rounded-xl border text-left transition-all duration-150',
          activeCategory === cat.id
            ? 'bg-[#142038] border-sky-500/40 text-sky-200 shadow-sm'
            : 'bg-[#0b1324] border-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-[#0f1a30] hover:border-slate-700/80'
        ]"
      >
        <div class="flex items-center gap-2.5 min-w-0">
          <component :is="cat.icon" class="w-4 h-4 shrink-0" :class="activeCategory === cat.id ? 'text-sky-400' : 'text-slate-400'" />
          <span class="text-xs font-semibold truncate">{{ cat.name }}</span>
        </div>
        <div class="flex items-center gap-1.5 shrink-0 ml-2">
          <span class="text-[10px] px-1.5 py-0.5 rounded font-mono font-medium"
            :class="activeCategory === cat.id ? 'bg-sky-950/80 text-sky-300 border border-sky-800/40' : 'bg-slate-800/60 text-slate-400'"
          >
            {{ cat.items.length }}
          </span>
        </div>
      </button>
    </div>

    <!-- Current Category Context Banner -->
    <div class="mb-3.5 px-3 py-2 rounded-lg bg-[#0b1324]/80 border border-slate-800/70 flex items-center justify-between text-[11px] text-slate-400">
      <div class="flex items-center gap-2 truncate">
        <span class="font-medium text-slate-300">Cakupan Domain:</span>
        <span class="truncate text-slate-400">{{ currentCategory.description }}</span>
      </div>
      <span class="text-[10px] text-slate-400 font-mono shrink-0 ml-2">DuckDB Verified</span>
    </div>

    <!-- Interactive Query Cards Grid (Solid Industrial Cards) -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <button
        v-for="(item, idx) in currentCategory.items"
        :key="idx"
        type="button"
        @click="triggerPrompt(item.query)"
        class="card-interactive text-left p-4 rounded-xl group flex flex-col justify-between min-h-[155px]"
      >
        <div>
          <!-- Tag & Table Badges -->
          <div class="flex items-center justify-between gap-1 mb-2.5">
            <span class="text-[10px] font-semibold text-sky-300 bg-sky-950/70 px-2 py-0.5 rounded border border-sky-800/50 uppercase tracking-wide truncate">
              {{ item.tag }}
            </span>
            <span class="text-[10px] text-slate-400 font-mono shrink-0">{{ item.tables }}</span>
          </div>

          <!-- Query Prompt -->
          <p class="text-xs text-slate-200 group-hover:text-white font-medium leading-relaxed mb-2.5">
            "{{ item.query }}"
          </p>

          <!-- Metric Focus Pill -->
          <div class="text-[11px] text-slate-400 font-normal flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 rounded-full bg-sky-400"></span>
            <span>{{ item.metric }}</span>
          </div>
        </div>
        
        <!-- Action Footer -->
        <div class="flex items-center justify-between text-[11px] text-slate-400 mt-3 pt-2.5 border-t border-slate-800/60 group-hover:border-slate-700/60 transition-colors">
          <span class="font-medium text-slate-400 group-hover:text-sky-300 transition-colors">Jalankan Analisis</span>
          <div class="w-5 h-5 rounded bg-slate-800/80 group-hover:bg-sky-500/20 flex items-center justify-center transition-colors">
            <ArrowRight class="w-3 h-3 transition-transform group-hover:translate-x-0.5 text-slate-400 group-hover:text-sky-300" />
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Sparkles, ArrowRight, BarChart3, DollarSign, Ship } from './Icons.js'

const emit = defineEmits(['select-prompt', 'run-prompt'])

const activeCategory = ref('operasional')

const categories = [
  {
    id: 'operasional',
    name: 'Operasional & Throughput',
    icon: BarChart3,
    description: 'Arus petikemas (Box/TEUs), kargo uncontainerized, & perbandingan RKAP',
    items: [
      {
        tag: 'Throughput Petikemas',
        query: 'Berapa total actual throughput container internasional dan domestik pada tahun 2024?',
        tables: 'fakta_throughput',
        metric: 'Satuan: TEUs & Box (Internasional & Domestik)'
      },
      {
        tag: 'Kargo Uncontainerized',
        query: 'Berapa total kegiatan uncontainerized (UC) tahun 2024?',
        tables: 'fakta_realisasi_uc',
        metric: 'Kegiatan Uncontainerized (Tonase & CBM)'
      },
      {
        tag: 'Rasio TEUs vs Box',
        query: 'Berapa perbandingan TEUs domestik dan internasional tahun 2024?',
        tables: 'fakta_overview_box',
        metric: 'Perbandingan Volume & Evaluasi RKAP'
      }
    ]
  },
  {
    id: 'finansial',
    name: 'Finansial & Tarif',
    icon: DollarSign,
    description: 'Pendapatan operasional komersial, ranking revenue operator, & keringanan biaya',
    items: [
      {
        tag: 'Total Revenue',
        query: 'Berapa total pendapatan komersial tahun 2023?',
        tables: 'fakta_komersial_dashboard',
        metric: 'Total Pendapatan (Miliar Rupiah)'
      },
      {
        tag: 'Top 5 Operator',
        query: 'Siapa 5 operator dengan revenue terbesar tahun 2024?',
        tables: 'fakta_komersial_dashboard',
        metric: 'Ranking Pendapatan Line Operator (LOP)'
      },
      {
        tag: 'Diskon & Restitusi',
        query: 'Tampilkan daftar permohonan diskon dan restitusi yang diajukan pelanggan',
        tables: 'fakta_rest_n_disc',
        metric: 'Status Pengajuan Keringanan Biaya'
      }
    ]
  },
  {
    id: 'pasar_rute',
    name: 'Pasar & Rute Pelayaran',
    icon: Ship,
    description: 'Market share liner pelayaran, kunjungan call rute kapal, & volume transhipment',
    items: [
      {
        tag: 'Market Share Liner',
        query: 'Siapa 3 operator dengan volume market share terbesar tahun 2023?',
        tables: 'fakta_market_share',
        metric: 'Pangsa Pasar Volume TEUs Internasional'
      },
      {
        tag: 'Rute & Call Kapal',
        query: 'Tampilkan rute dan total call kapal per operator tahun 2024',
        tables: 'fakta_vessel_service',
        metric: 'Frekuensi Kunjungan Rute Pelayaran'
      },
      {
        tag: 'Transhipment Hub',
        query: 'Berapa total revenue transhipment per operator tahun 2024?',
        tables: 'fakta_transhipment',
        metric: 'Pendapatan Vessel & Yard Transhipment'
      }
    ]
  }
]

const currentCategory = computed(() => {
  return categories.find(c => c.id === activeCategory.value) || categories[0]
})

const triggerPrompt = (queryText) => {
  emit('select-prompt', queryText)
  emit('run-prompt', queryText)
}
</script>
