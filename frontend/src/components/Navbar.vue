<template>
  <header class="sticky top-0 z-30 w-full bg-[#0a1122]/95 border-b border-slate-800/80 backdrop-blur-md px-3 sm:px-6 py-2.5">
    <div class="max-w-7xl mx-auto flex items-center justify-between gap-3">
      <!-- Left: Logo TPS Asli & Corporate Title -->
      <div class="flex items-center gap-3.5 min-w-0">
        <!-- Logo TPS Asli Container -->
        <div class="relative flex items-center justify-center h-10 px-3 py-1.5 rounded-xl bg-white/[0.04] border border-white/10 shadow-sm shrink-0">
          <img 
            :src="logoUrl" 
            alt="Logo PT TPS" 
            class="h-7 w-auto object-contain"
            @error="hasLogoError = true"
            v-if="!hasLogoError"
          />
          <div v-else class="flex items-center gap-2 whitespace-nowrap">
            <Ship class="w-4 h-4 text-sky-400" />
            <span class="font-bold text-xs text-slate-100 tracking-wider">PT TPS</span>
          </div>
        </div>

        <div class="h-6 w-px bg-slate-800/80 hidden sm:block shrink-0"></div>

        <!-- Corporate Title -->
        <div class="hidden sm:block min-w-0">
          <div class="flex items-center gap-2 whitespace-nowrap">
            <h1 class="font-semibold text-sm text-slate-100 tracking-tight">
              PT Terminal Petikemas Surabaya
            </h1>
            <span class="px-2 py-0.5 text-[10px] font-medium tracking-wide bg-sky-950/70 text-sky-300 rounded border border-sky-800/50">
              Commercial Analytics
            </span>
          </div>
          <p class="text-[11px] text-slate-400 font-normal truncate">Executive Decision Support & Port Intelligence</p>
        </div>
      </div>

      <!-- Right: Operational Badges, User Profile & Actions -->
      <div class="flex items-center gap-2 sm:gap-2.5 shrink-0">
        <!-- OLAP Warehouse Connection Status -->
        <div class="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs text-slate-300 font-medium whitespace-nowrap">
          <span class="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
          <Database class="w-3.5 h-3.5 text-slate-400" />
          <span class="text-slate-300">DuckDB Warehouse</span>
        </div>

        <!-- User Role Profile Pill -->
        <div v-if="currentUser" class="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs font-medium whitespace-nowrap">
          <UserCheck class="w-3.5 h-3.5 text-sky-400 shrink-0" />
          <span class="text-slate-200 hidden md:inline truncate max-w-[130px] font-semibold">{{ currentUser.name }}</span>
          <span class="px-1.5 py-0.5 text-[9px] uppercase tracking-wider rounded bg-slate-800/90 text-slate-300 border border-slate-700/80 font-mono font-semibold shrink-0">
            {{ currentUser.role }}
          </span>
        </div>

        <!-- Admin Portal Link (Admin Only) -->
        <a 
          v-if="currentUser && currentUser.role === 'admin'"
          href="/administrator"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-medium transition-colors whitespace-nowrap"
          title="Masuk ke Portal Administrator"
        >
          <span>Portal Admin</span>
        </a>

        <!-- Reset Button -->
        <button 
          @click="$emit('reset-chat')"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs text-slate-300 hover:text-white border border-slate-800 transition-colors whitespace-nowrap"
          title="Mulai sesi analisis baru"
        >
          <RotateCcw class="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span class="hidden sm:inline">Reset Sesi</span>
        </button>

        <!-- Logout Button -->
        <button
          v-if="currentUser"
          @click="$emit('logout')"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-red-950/40 text-xs text-slate-400 hover:text-red-300 border border-slate-800 hover:border-red-900/50 transition-colors whitespace-nowrap"
          title="Keluar dari sistem"
        >
          <LogOut class="w-3.5 h-3.5 text-slate-400 hover:text-red-400 shrink-0" />
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
