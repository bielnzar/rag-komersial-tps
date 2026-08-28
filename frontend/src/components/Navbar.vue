<template>
  <header class="card-executive sticky top-0 z-30 w-full border-b border-slate-800/80 px-4 py-3 sm:px-8">
    <div class="max-w-7xl mx-auto flex items-center justify-between">
      <!-- Left: Logo & Corporate Title -->
      <div class="flex items-center gap-3.5">
        <!-- Logo Image with Fallback -->
        <div class="relative flex items-center justify-center h-10 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-700/60 shadow-sm overflow-hidden">
          <img 
            :src="logoUrl" 
            alt="Logo PT TPS" 
            class="h-7 w-auto object-contain"
            @error="hasLogoError = true"
            v-if="!hasLogoError"
          />
          <div v-else class="flex items-center gap-2">
            <Ship class="w-5 h-5 text-teal-400" />
            <span class="font-bold text-sm text-slate-100 tracking-wider">TPS</span>
          </div>
        </div>

        <div class="h-6 w-px bg-slate-800 hidden sm:block"></div>

        <div>
          <div class="flex items-center gap-2">
            <h1 class="font-bold text-base sm:text-lg text-slate-100 tracking-tight">
              PT Terminal Petikemas Surabaya
            </h1>
            <span class="px-2 py-0.5 text-[10px] font-medium bg-slate-800 text-slate-300 rounded-md border border-slate-700">
              Commercial Analytics
            </span>
          </div>
          <p class="text-[11px] text-slate-400 font-medium">System Intelijen & Analisis Data Operasional</p>
        </div>
      </div>

      <!-- Right: Operational Badges & Reset -->
      <div class="flex items-center gap-3">
        <!-- Engine Status -->
        <div class="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-300 font-medium">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <Database class="w-3.5 h-3.5 text-teal-400" />
          <span>DuckDB Engine</span>
        </div>

        <!-- Role Badge -->
        <div class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-300 font-medium">
          <UserCheck class="w-3.5 h-3.5 text-cyan-400" />
          <span>Divisi Komersial</span>
        </div>

        <!-- Reset Button -->
        <button 
          @click="$emit('reset-chat')"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/90 hover:bg-slate-700/90 text-xs text-slate-200 border border-slate-700 transition-colors"
          title="Mulai sesi analisis baru"
        >
          <RotateCcw class="w-3.5 h-3.5 text-slate-400" />
          <span>Reset Sesi</span>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { Ship, Database, UserCheck, RotateCcw } from './Icons.js'

defineEmits(['reset-chat'])
const logoUrl = ref('/assets/tps-logo.png')
const hasLogoError = ref(false)
</script>
