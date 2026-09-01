<template>
  <header class="card-executive sticky top-0 z-30 w-full border-b border-slate-800/80 px-3 sm:px-6 py-2.5">
    <div class="max-w-7xl mx-auto flex items-center justify-between gap-2">
      <!-- Left: Logo TPS Asli & Corporate Title -->
      <div class="flex items-center gap-3 min-w-0">
        <!-- Logo TPS Asli -->
        <div class="relative flex items-center justify-center h-9 px-2.5 py-1 rounded-xl bg-slate-900/90 border border-slate-700/60 shadow-sm shrink-0 overflow-hidden">
          <img 
            :src="logoUrl" 
            alt="Logo PT TPS" 
            class="h-6 sm:h-7 w-auto object-contain"
            @error="hasLogoError = true"
            v-if="!hasLogoError"
          />
          <div v-else class="flex items-center gap-1.5 whitespace-nowrap">
            <Ship class="w-4 h-4 text-teal-400" />
            <span class="font-bold text-xs text-slate-100 tracking-wider">PT TPS</span>
          </div>
        </div>

        <div class="h-5 w-px bg-slate-800 hidden lg:block shrink-0"></div>

        <!-- Corporate Title -->
        <div class="hidden lg:block min-w-0">
          <div class="flex items-center gap-2 whitespace-nowrap">
            <h1 class="font-bold text-sm text-slate-100 tracking-tight">
              PT Terminal Petikemas Surabaya
            </h1>
            <span class="px-2 py-0.5 text-[10px] font-semibold bg-slate-800 text-teal-300 rounded-md border border-slate-700">
              Executive AI
            </span>
          </div>
          <p class="text-[10px] text-slate-400 font-medium truncate">System Intelijen & Analisis Data Operasional</p>
        </div>
      </div>

      <!-- Right: Operational Badges, User Profile & Actions -->
      <div class="flex items-center gap-2 shrink-0">
        <!-- Engine Status -->
        <div class="hidden xl:flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-300 font-medium whitespace-nowrap">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <Database class="w-3.5 h-3.5 text-teal-400" />
          <span>DuckDB Engine</span>
        </div>

        <!-- User Role Badge -->
        <div v-if="currentUser" class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs font-semibold whitespace-nowrap">
          <UserCheck class="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span class="text-slate-200 hidden md:inline truncate max-w-[130px]">{{ currentUser.name }}</span>
          <span class="px-1.5 py-0.5 text-[9px] uppercase tracking-wider rounded bg-slate-800 text-teal-300 border border-slate-700 font-bold shrink-0">
            {{ currentUser.role }}
          </span>
        </div>


        <!-- Reset Button -->
        <button 
          @click="$emit('reset-chat')"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/90 hover:bg-slate-700/90 text-xs text-slate-200 border border-slate-700 transition-colors whitespace-nowrap"
          title="Mulai sesi analisis baru"
        >
          <RotateCcw class="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span class="hidden sm:inline">Reset Sesi</span>
        </button>

        <!-- Logout Button -->
        <button
          v-if="currentUser"
          @click="$emit('logout')"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-950/40 hover:bg-red-900/50 text-xs text-red-300 border border-red-800/60 transition-colors whitespace-nowrap"
          title="Keluar dari sistem"
        >
          <LogOut class="w-3.5 h-3.5 text-red-400 shrink-0" />
          <span class="hidden sm:inline">Keluar</span>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { Ship, Database, UserCheck, RotateCcw, LogOut } from './Icons.js'

defineProps({
  currentUser: { type: Object, default: () => null }
})

defineEmits(['reset-chat', 'logout'])

const logoUrl = ref('/assets/tps-logo.png')
const hasLogoError = ref(false)
</script>
