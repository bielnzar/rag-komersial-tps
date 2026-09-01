<template>
  <aside 
    :class="[
      'fixed top-0 left-0 bottom-0 z-40 bg-slate-950/95 border-r border-slate-800/80 backdrop-blur-xl transition-all duration-300 flex flex-col justify-between shadow-2xl',
      isOpen ? 'w-64 translate-x-0' : 'w-0 -translate-x-full md:w-14 md:translate-x-0'
    ]"
  >
    <!-- Top Section: Header & New Chat Button -->
    <div class="p-3 space-y-2.5">
      <!-- Title Bar dengan Logo Pelindo Kecil -->
      <div class="flex items-center justify-between">
        <div v-if="isOpen" class="flex items-center gap-2 px-1">
          <img 
            :src="smallPelindoLogo" 
            alt="Logo Pelindo" 
            class="h-5 w-auto object-contain"
            @error="hasSmallLogoError = true"
            v-if="!hasSmallLogoError"
          />
          <Ship v-else class="w-4 h-4 text-teal-400 shrink-0" />
          <span class="font-bold text-xs text-slate-200 tracking-tight">Riwayat Sesi</span>
        </div>

        <!-- Single Toggle Button -->
        <button 
          @click="$emit('toggle-sidebar')"
          class="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 transition-colors mx-auto md:mx-0"
          :title="isOpen ? 'Tutup Sidebar' : 'Buka Sidebar'"
        >
          <PanelLeftClose v-if="isOpen" class="w-4 h-4" />
          <PanelLeftOpen v-else class="w-4 h-4" />
        </button>
      </div>

      <!-- New Chat Button -->
      <button
        @click="$emit('new-session')"
        :class="[
          'w-full py-2 px-3 rounded-xl bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 border border-teal-500/30 font-semibold text-xs transition-all flex items-center justify-center gap-2 shadow-sm',
          !isOpen && 'hidden md:flex md:p-2'
        ]"
        title="Buat Sesi Obrolan Baru"
      >
        <Plus class="w-3.5 h-3.5 text-teal-400 shrink-0" />
        <span v-if="isOpen">Chat Baru</span>
      </button>
    </div>

    <!-- Middle Section: Saved Session Threads List -->
    <div v-if="isOpen" class="flex-1 overflow-y-auto px-2.5 py-1 space-y-1 custom-scrollbar">
      <div v-if="sessions.length === 0" class="text-center py-10 px-2">
        <div class="inline-flex items-center justify-center p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 mb-2">
          <MessageSquare class="w-5 h-5 text-slate-600" />
        </div>
        <p class="text-[11px] font-medium text-slate-500 leading-relaxed">
          Belum ada riwayat sesi.<br />Silakan mulai pertanyaan baru.
        </p>
      </div>

      <div
        v-for="item in sessions"
        :key="item.session_id"
        @click="$emit('select-session', item.session_id)"
        :class="[
          'group relative p-2 rounded-xl border text-left cursor-pointer transition-all flex items-center justify-between gap-2',
          activeSessionId === item.session_id
            ? 'bg-slate-900 border-teal-500/50 text-slate-100 shadow-md'
            : 'bg-slate-950/40 hover:bg-slate-900/70 border-slate-900 text-slate-400 hover:text-slate-200'
        ]"
      >
        <div class="flex items-center gap-2 min-w-0 flex-1">
          <MessageSquare class="w-3.5 h-3.5 text-teal-400 shrink-0" />
          <div class="min-w-0 flex-1">
            <p class="text-[11px] font-medium truncate leading-tight">{{ item.title }}</p>
            <p class="text-[9px] text-slate-500 mt-0.5">{{ item.created_at }}</p>
          </div>
        </div>

        <!-- Delete Session Button on Hover -->
        <button
          @click.stop="$emit('delete-session', item.session_id)"
          class="opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-red-950/80 text-slate-500 hover:text-red-400 transition-all shrink-0"
          title="Hapus sesi ini"
        >
          <Trash2 class="w-3 h-3" />
        </button>
      </div>
    </div>

    <!-- Bottom Section: Active User Profile Card -->
    <div v-if="isOpen && currentUser" class="p-2.5 border-t border-slate-900 bg-slate-950/90 flex items-center justify-between">
      <div class="min-w-0 flex-1 pr-2">
        <p class="text-[11px] font-semibold text-slate-200 truncate">{{ currentUser.name }}</p>
        <div class="flex items-center gap-1.5 mt-0.5">
          <span class="inline-block px-1.5 py-0.2 text-[8px] font-bold uppercase tracking-wider rounded bg-slate-900 text-teal-300 border border-slate-800">
            {{ currentUser.role }}
          </span>
          <span class="text-[9px] text-slate-500 truncate">@{{ currentUser.username }}</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import { Ship, Plus, MessageSquare, Trash2, PanelLeftClose, PanelLeftOpen } from './Icons.js'

defineProps({
  isOpen: { type: Boolean, default: true },
  sessions: { type: Array, default: () => [] },
  activeSessionId: { type: String, default: '' },
  currentUser: { type: Object, default: () => null }
})

defineEmits(['toggle-sidebar', 'new-session', 'select-session', 'delete-session'])

const smallPelindoLogo = ref('/assets/Logo Pelindo.png')
const hasSmallLogoError = ref(false)
</script>
