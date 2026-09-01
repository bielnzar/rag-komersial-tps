<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
    <!-- Top Header Bar -->
    <header class="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between sticky top-0 z-50 backdrop-blur-md">
      <div class="flex items-center gap-3">
        <button @click="goBackToChat" class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors">
          <span>← Kembali ke Obrolan</span>
        </button>
        <div class="h-4 w-px bg-slate-700"></div>
        <h1 class="text-base font-bold text-white flex items-center gap-2">
          <svg class="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
          Portal Admin & RAG Telemetry
        </h1>
      </div>
      
      <div class="flex items-center gap-2">
        <span class="flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-mono text-emerald-400 bg-emerald-950/60 rounded-md border border-emerald-800/80">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          UPDATE DALAM {{ countdown }}S
        </span>
        <span class="px-2.5 py-1 text-[11px] font-mono text-slate-400 bg-slate-900 rounded-md border border-slate-800">
          Endpoint: /administrator
        </span>
      </div>
    </header>

    <div class="max-w-7xl w-full mx-auto p-6 flex-1 flex flex-col">
      <!-- Tabs -->
      <div class="flex border-b border-slate-800 bg-slate-900/50 rounded-t-xl px-4 pt-2">
        <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
          :class="['px-5 py-3 font-semibold text-xs transition-colors border-b-2 tracking-wide uppercase', activeTab === tab.id ? 'border-teal-400 text-teal-400' : 'border-transparent text-slate-400 hover:text-slate-200']">
          {{ tab.name }}
        </button>
      </div>

      <!-- Main Content Box -->
      <div class="bg-slate-900/40 border border-t-0 border-slate-800 rounded-b-xl p-6 flex-1 shadow-2xl">
        
        <!-- TAB 1: TELEMETRI & TOKEN -->
        <div v-if="activeTab === 'telemetry'" class="space-y-6 animate-fade-in">
          <!-- Summary Cards -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="bg-slate-800/50 border border-slate-700/50 p-4 rounded-xl shadow-inner">
              <p class="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">Total Token (Gemini)</p>
              <h3 class="text-2xl font-bold text-blue-400">{{ metrics.gemini_tokens.toLocaleString() }}</h3>
            </div>
            <div class="bg-slate-800/50 border border-slate-700/50 p-4 rounded-xl shadow-inner">
              <p class="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">Total Token (Groq)</p>
              <h3 class="text-2xl font-bold text-orange-400">{{ metrics.groq_tokens.toLocaleString() }}</h3>
            </div>
            <div class="bg-slate-800/50 border border-slate-700/50 p-4 rounded-xl shadow-inner">
              <p class="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">Success Rate RAG</p>
              <h3 class="text-2xl font-bold text-emerald-400">{{ metrics.success_rate }}%</h3>
            </div>
            <div class="bg-slate-800/50 border border-slate-700/50 p-4 rounded-xl shadow-inner">
              <p class="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">Average Latency</p>
              <h3 class="text-2xl font-bold text-fuchsia-400">{{ metrics.avg_latency_ms }} ms</h3>
            </div>
          </div>

          <!-- Recent Logs Table -->
          <div class="bg-slate-800/30 border border-slate-700/50 rounded-xl overflow-hidden mt-6">
            <div class="px-4 py-3 bg-slate-800/80 border-b border-slate-700/50">
              <h3 class="text-sm font-semibold text-slate-200">Riwayat Eksekusi LLM Terakhir (DuckDB Audit)</h3>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-left text-sm text-slate-300">
                <thead class="bg-slate-800/40 text-slate-400 text-xs uppercase">
                  <tr>
                    <th class="px-4 py-3">Timestamp</th>
                    <th class="px-4 py-3">Agent</th>
                    <th class="px-4 py-3">Model</th>
                    <th class="px-4 py-3">Tokens</th>
                    <th class="px-4 py-3">Latency</th>
                    <th class="px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-700/50">
                  <tr v-for="(log, i) in recentLogs" :key="i" class="hover:bg-slate-700/20">
                    <td class="px-4 py-2">{{ new Date(log.timestamp).toLocaleTimeString() }}</td>
                    <td class="px-4 py-2 font-mono text-xs text-sky-300">{{ log.agent_name }}</td>
                    <td class="px-4 py-2">{{ log.model_name }}</td>
                    <td class="px-4 py-2">{{ log.total_tokens }}</td>
                    <td class="px-4 py-2">{{ log.latency_ms.toFixed(0) }}ms</td>
                    <td class="px-4 py-2">
                      <span :class="[
                        'px-2 py-1 rounded text-[10px] font-bold tracking-wider uppercase',
                        log.status === 'SUCCESS' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                      ]">{{ log.status }}</span>
                    </td>
                  </tr>
                  <tr v-if="recentLogs.length === 0">
                    <td colspan="6" class="px-4 py-4 text-center text-slate-500">Belum ada data log telemetri</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- TAB 2: API KEYS & STEP-BY-STEP CONFIG -->
        <div v-if="activeTab === 'keys'" class="space-y-6 animate-fade-in">
          <!-- KARTU KONFIGURASI MANDIRI PER-STEP -->
          <div class="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border border-teal-500/30 rounded-2xl p-6 shadow-2xl backdrop-blur-md mb-6">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-800">
              <div>
                <h3 class="text-base font-bold text-slate-100 flex items-center gap-2.5">
                  <span class="p-1.5 bg-teal-500/10 text-teal-400 rounded-lg border border-teal-500/20 text-xs">🤖</span>
                  Konfigurasi Mandiri Per-Tahapan (Provider, Model, & Kunci API)
                </h3>
                <p class="text-xs text-slate-400 mt-1">
                  Pilih <strong class="text-teal-300">Provider</strong>, pilih <strong class="text-teal-300">Model</strong>, lalu masukkan <strong class="text-teal-300">Kunci API Khusus</strong> untuk tiap step agar kuota tidak saling bentrok.
                </p>
              </div>
              <button 
                @click="saveStepConfigs" 
                :disabled="isSavingStepConfigs" 
                class="px-5 py-2.5 bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 disabled:opacity-50 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-teal-950/40 transition-all shrink-0 flex items-center gap-2 self-start md:self-auto"
              >
                <span>{{ isSavingStepConfigs ? 'Menyimpan...' : '💾 Simpan Konfigurasi Per-Step' }}</span>
              </button>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
              <!-- STEP 1: ROUTER -->
              <div class="bg-slate-950/80 border border-slate-800/90 rounded-2xl p-5 flex flex-col gap-4 shadow-lg">
                <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div class="flex items-center gap-2">
                    <span class="w-6 h-6 rounded-lg bg-sky-500/20 text-sky-400 border border-sky-500/30 flex items-center justify-center text-xs font-black">1</span>
                    <span class="text-xs font-bold text-slate-100 uppercase tracking-wider">STEP 1: Router Agent</span>
                  </div>
                  <span class="text-[10px] px-2 py-0.5 rounded bg-sky-950/60 text-sky-400 border border-sky-800/50 font-mono">Pilih Tabel</span>
                </div>

                <!-- 1. PILIH PROVIDER -->
                <div>
                  <label class="text-[10px] uppercase font-bold text-slate-400 block mb-1.5">1. Pilih Provider API:</label>
                  <div class="grid grid-cols-2 gap-2">
                    <button 
                      type="button" 
                      @click="setStepProvider('router', 'google_gemini')" 
                      :class="['py-1.5 px-3 rounded-lg text-xs font-bold transition-all border flex items-center justify-center gap-1.5', stepConfigs.router.provider === 'google_gemini' ? 'bg-sky-500/20 text-sky-300 border-sky-500/50' : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200']"
                    >
                      <span>Google Gemini</span>
                    </button>
                    <button 
                      type="button" 
                      @click="setStepProvider('router', 'groq')" 
                      :class="['py-1.5 px-3 rounded-lg text-xs font-bold transition-all border flex items-center justify-center gap-1.5', stepConfigs.router.provider === 'groq' ? 'bg-orange-500/20 text-orange-300 border-orange-500/50' : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200']"
                    >
                      <span>Groq Cloud</span>
                    </button>
                  </div>
                </div>

                <!-- 2. PILIH MODEL -->
                <div>
                  <label class="text-[10px] uppercase font-bold text-slate-400 block mb-1.5">2. Pilih Model AI:</label>
                  <select 
                    v-model="stepConfigs.router.model" 
                    class="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-sky-500 font-medium"
                  >
                    <option v-for="m in getModelsForProvider(stepConfigs.router.provider)" :key="m.id" :value="m.id">
                      {{ m.name }}
                    </option>
                  </select>
                </div>

                <!-- 3. LIST API KEYS KHUSUS STEP 1 -->
                <div class="flex-1 flex flex-col">
                  <div class="flex items-center justify-between mb-2">
                    <label class="text-[10px] uppercase font-bold text-slate-400">3. Kunci API Khusus Step 1:</label>
                    <span class="text-[10px] text-slate-500 font-mono">{{ stepConfigs.router.api_keys?.length || 0 }} Kunci</span>
                  </div>

                  <div class="space-y-2.5 flex-1 max-h-52 overflow-y-auto pr-1">
                    <div 
                      v-for="(k, i) in stepConfigs.router.api_keys" 
                      :key="'router_k'+i"
                      :class="['p-2.5 rounded-xl border text-xs flex flex-col gap-1.5', k.status === 'active' ? 'bg-sky-950/30 border-sky-500/50' : 'bg-slate-900/60 border-slate-800']"
                    >
                      <div class="flex items-center justify-between gap-1">
                        <input type="text" v-model="k.label" placeholder="Label Kunci" class="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[11px] text-slate-300 font-medium max-w-[110px]" />
                        <div class="flex items-center gap-1.5">
                          <span class="text-[9px] text-slate-500 font-mono">{{ k.usage || 0 }}x</span>
                          <button type="button" @click="setStepActiveKey('router', i)" :class="['px-2 py-0.5 rounded text-[9px] font-bold uppercase', k.status === 'active' ? 'bg-sky-400 text-slate-950' : 'bg-slate-800 text-slate-400 hover:text-slate-200']">
                            {{ k.status === 'active' ? 'AKTIF' : 'PASANG' }}
                          </button>
                          <button type="button" @click="deleteStepKey('router', i)" class="text-slate-500 hover:text-red-400 p-0.5">✕</button>
                        </div>
                      </div>
                      <input type="text" v-model="k.key" :placeholder="stepConfigs.router.provider === 'google_gemini' ? 'Masukkan Google Key (AIzaSy...)' : 'Masukkan Groq Key (gsk_...)'" class="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-[11px] font-mono text-slate-200 focus:outline-none focus:border-sky-500" />
                    </div>

                    <div v-if="!stepConfigs.router.api_keys || stepConfigs.router.api_keys.length === 0" class="text-center py-4 text-[11px] text-slate-500 border border-dashed border-slate-800 rounded-xl">
                      Belum ada kunci khusus. Menggunakan pool fallback.
                    </div>
                  </div>

                  <button type="button" @click="addStepKey('router')" class="w-full mt-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-sky-400 text-xs font-bold rounded-lg transition-colors">
                    + Tambah Kunci Step 1
                  </button>
                </div>
              </div>

              <!-- STEP 2: SQL GENERATOR -->
              <div class="bg-slate-950/80 border border-slate-800/90 rounded-2xl p-5 flex flex-col gap-4 shadow-lg">
                <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div class="flex items-center gap-2">
                    <span class="w-6 h-6 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center text-xs font-black">2</span>
                    <span class="text-xs font-bold text-slate-100 uppercase tracking-wider">STEP 2: SQL Generator</span>
                  </div>
                  <span class="text-[10px] px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/50 font-mono">Rakit SQL</span>
                </div>

                <!-- 1. PILIH PROVIDER -->
                <div>
                  <label class="text-[10px] uppercase font-bold text-slate-400 block mb-1.5">1. Pilih Provider API:</label>
                  <div class="grid grid-cols-2 gap-2">
                    <button 
                      type="button" 
                      @click="setStepProvider('sql_gen', 'google_gemini')" 
                      :class="['py-1.5 px-3 rounded-lg text-xs font-bold transition-all border flex items-center justify-center gap-1.5', stepConfigs.sql_gen.provider === 'google_gemini' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50' : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200']"
                    >
                      <span>Google Gemini</span>
                    </button>
                    <button 
                      type="button" 
                      @click="setStepProvider('sql_gen', 'groq')" 
                      :class="['py-1.5 px-3 rounded-lg text-xs font-bold transition-all border flex items-center justify-center gap-1.5', stepConfigs.sql_gen.provider === 'groq' ? 'bg-orange-500/20 text-orange-300 border-orange-500/50' : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200']"
                    >
                      <span>Groq Cloud</span>
                    </button>
                  </div>
                </div>

                <!-- 2. PILIH MODEL -->
                <div>
                  <label class="text-[10px] uppercase font-bold text-slate-400 block mb-1.5">2. Pilih Model AI:</label>
                  <select 
                    v-model="stepConfigs.sql_gen.model" 
                    class="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-emerald-500 font-medium"
                  >
                    <option v-for="m in getModelsForProvider(stepConfigs.sql_gen.provider)" :key="m.id" :value="m.id">
                      {{ m.name }}
                    </option>
                  </select>
                </div>

                <!-- 3. LIST API KEYS KHUSUS STEP 2 -->
                <div class="flex-1 flex flex-col">
                  <div class="flex items-center justify-between mb-2">
                    <label class="text-[10px] uppercase font-bold text-slate-400">3. Kunci API Khusus Step 2:</label>
                    <span class="text-[10px] text-slate-500 font-mono">{{ stepConfigs.sql_gen.api_keys?.length || 0 }} Kunci</span>
                  </div>

                  <div class="space-y-2.5 flex-1 max-h-52 overflow-y-auto pr-1">
                    <div 
                      v-for="(k, i) in stepConfigs.sql_gen.api_keys" 
                      :key="'sql_k'+i" 
                      :class="['p-2.5 rounded-xl border text-xs flex flex-col gap-1.5', k.status === 'active' ? 'bg-emerald-950/30 border-emerald-500/50' : 'bg-slate-900/60 border-slate-800']"
                    >
                      <div class="flex items-center justify-between gap-1">
                        <input type="text" v-model="k.label" placeholder="Label Kunci" class="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[11px] text-slate-300 font-medium max-w-[110px]" />
                        <div class="flex items-center gap-1.5">
                          <span class="text-[9px] text-slate-500 font-mono">{{ k.usage || 0 }}x</span>
                          <button type="button" @click="setStepActiveKey('sql_gen', i)" :class="['px-2 py-0.5 rounded text-[9px] font-bold uppercase', k.status === 'active' ? 'bg-emerald-400 text-slate-950' : 'bg-slate-800 text-slate-400 hover:text-slate-200']">
                            {{ k.status === 'active' ? 'AKTIF' : 'PASANG' }}
                          </button>
                          <button type="button" @click="deleteStepKey('sql_gen', i)" class="text-slate-500 hover:text-red-400 p-0.5">✕</button>
                        </div>
                      </div>
                      <input type="text" v-model="k.key" :placeholder="stepConfigs.sql_gen.provider === 'google_gemini' ? 'Masukkan Google Key (AIzaSy...)' : 'Masukkan Groq Key (gsk_...)'" class="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-[11px] font-mono text-slate-200 focus:outline-none focus:border-emerald-500" />
                    </div>

                    <div v-if="!stepConfigs.sql_gen.api_keys || stepConfigs.sql_gen.api_keys.length === 0" class="text-center py-4 text-[11px] text-slate-500 border border-dashed border-slate-800 rounded-xl">
                      Belum ada kunci khusus. Menggunakan pool fallback.
                    </div>
                  </div>

                  <button type="button" @click="addStepKey('sql_gen')" class="w-full mt-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-emerald-400 text-xs font-bold rounded-lg transition-colors">
                    + Tambah Kunci Step 2
                  </button>
                </div>
              </div>

              <!-- STEP 3: VIZ & ANALYST -->
              <div class="bg-slate-950/80 border border-slate-800/90 rounded-2xl p-5 flex flex-col gap-4 shadow-lg">
                <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div class="flex items-center gap-2">
                    <span class="w-6 h-6 rounded-lg bg-orange-500/20 text-orange-400 border border-orange-500/30 flex items-center justify-center text-xs font-black">3</span>
                    <span class="text-xs font-bold text-slate-100 uppercase tracking-wider">STEP 3: Viz & Analyst</span>
                  </div>
                  <span class="text-[10px] px-2 py-0.5 rounded bg-orange-950/60 text-orange-400 border border-orange-800/50 font-mono">Narasi & Grafik</span>
                </div>

                <!-- 1. PILIH PROVIDER -->
                <div>
                  <label class="text-[10px] uppercase font-bold text-slate-400 block mb-1.5">1. Pilih Provider API:</label>
                  <div class="grid grid-cols-2 gap-2">
                    <button 
                      type="button" 
                      @click="setStepProvider('viz_gen', 'google_gemini')" 
                      :class="['py-1.5 px-3 rounded-lg text-xs font-bold transition-all border flex items-center justify-center gap-1.5', stepConfigs.viz_gen.provider === 'google_gemini' ? 'bg-sky-500/20 text-sky-300 border-sky-500/50' : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200']"
                    >
                      <span>Google Gemini</span>
                    </button>
                    <button 
                      type="button" 
                      @click="setStepProvider('viz_gen', 'groq')" 
                      :class="['py-1.5 px-3 rounded-lg text-xs font-bold transition-all border flex items-center justify-center gap-1.5', stepConfigs.viz_gen.provider === 'groq' ? 'bg-orange-500/20 text-orange-300 border-orange-500/50' : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200']"
                    >
                      <span>Groq Cloud</span>
                    </button>
                  </div>
                </div>

                <!-- 2. PILIH MODEL -->
                <div>
                  <label class="text-[10px] uppercase font-bold text-slate-400 block mb-1.5">2. Pilih Model AI:</label>
                  <select 
                    v-model="stepConfigs.viz_gen.model" 
                    class="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-orange-500 font-medium"
                  >
                    <option v-for="m in getModelsForProvider(stepConfigs.viz_gen.provider)" :key="m.id" :value="m.id">
                      {{ m.name }}
                    </option>
                  </select>
                </div>

                <!-- 3. LIST API KEYS KHUSUS STEP 3 -->
                <div class="flex-1 flex flex-col">
                  <div class="flex items-center justify-between mb-2">
                    <label class="text-[10px] uppercase font-bold text-slate-400">3. Kunci API Khusus Step 3:</label>
                    <span class="text-[10px] text-slate-500 font-mono">{{ stepConfigs.viz_gen.api_keys?.length || 0 }} Kunci</span>
                  </div>

                  <div class="space-y-2.5 flex-1 max-h-52 overflow-y-auto pr-1">
                    <div 
                      v-for="(k, i) in stepConfigs.viz_gen.api_keys" 
                      :key="'viz_k'+i" 
                      :class="['p-2.5 rounded-xl border text-xs flex flex-col gap-1.5', k.status === 'active' ? 'bg-orange-950/30 border-orange-500/50' : 'bg-slate-900/60 border-slate-800']"
                    >
                      <div class="flex items-center justify-between gap-1">
                        <input type="text" v-model="k.label" placeholder="Label Kunci" class="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[11px] text-slate-300 font-medium max-w-[110px]" />
                        <div class="flex items-center gap-1.5">
                          <span class="text-[9px] text-slate-500 font-mono">{{ k.usage || 0 }}x</span>
                          <button type="button" @click="setStepActiveKey('viz_gen', i)" :class="['px-2 py-0.5 rounded text-[9px] font-bold uppercase', k.status === 'active' ? 'bg-orange-400 text-slate-950' : 'bg-slate-800 text-slate-400 hover:text-slate-200']">
                            {{ k.status === 'active' ? 'AKTIF' : 'PASANG' }}
                          </button>
                          <button type="button" @click="deleteStepKey('viz_gen', i)" class="text-slate-500 hover:text-red-400 p-0.5">✕</button>
                        </div>
                      </div>
                      <input type="text" v-model="k.key" :placeholder="stepConfigs.viz_gen.provider === 'google_gemini' ? 'Masukkan Google Key (AIzaSy...)' : 'Masukkan Groq Key (gsk_...)'" class="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-[11px] font-mono text-slate-200 focus:outline-none focus:border-orange-500" />
                    </div>

                    <div v-if="!stepConfigs.viz_gen.api_keys || stepConfigs.viz_gen.api_keys.length === 0" class="text-center py-4 text-[11px] text-slate-500 border border-dashed border-slate-800 rounded-xl">
                      Belum ada kunci khusus. Menggunakan pool fallback.
                    </div>
                  </div>

                  <button type="button" @click="addStepKey('viz_gen')" class="w-full mt-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-orange-400 text-xs font-bold rounded-lg transition-colors">
                    + Tambah Kunci Step 3
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- POOL KUNCI GLOBAL BACKUP -->
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 bg-slate-900/40 p-4 rounded-xl border border-slate-800/60">
            <div>
              <h3 class="text-sm font-bold text-slate-200">Kunci Cadangan / Global Pool Provider</h3>
              <p class="text-xs text-slate-400 mt-0.5">
                Kunci di bawah ini digunakan sebagai fallback jika salah satu tahapan tidak memiliki kunci khusus yang aktif.
              </p>
            </div>
            <button @click="saveApiKeys" :disabled="isSavingKeys" class="px-4 py-2 bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-slate-950 font-bold text-xs rounded-lg shadow-sm transition-all shrink-0 flex items-center gap-2">
              <span>{{ isSavingKeys ? 'Menyimpan...' : 'Simpan Kunci Pool Global' }}</span>
            </button>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- GOOGLE GEMINI POOL -->
            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col">
              <div class="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
                <h4 class="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg" class="w-4 h-4"/> 
                  Google Gemini API Keys
                </h4>
                <span class="text-[10px] font-semibold bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">
                  Total: {{ apiKeys.google_gemini ? apiKeys.google_gemini.length : 0 }}
                </span>
              </div>

              <div class="space-y-3.5 flex-1">
                <div 
                  v-for="(k, i) in apiKeys.google_gemini" 
                  :key="'gemini'+i" 
                  :class="[
                    'p-3.5 rounded-xl border transition-all flex flex-col gap-2',
                    k.status === 'active' ? 'bg-teal-950/20 border-teal-500/50' : 'bg-slate-900/60 border-slate-800'
                  ]"
                >
                  <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-bold text-slate-500">#{{ i+1 }}</span>
                      <input 
                        type="text" 
                        v-model="k.label" 
                        placeholder="Label Kunci" 
                        class="bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-xs text-slate-300 font-medium focus:outline-none focus:border-teal-500 max-w-[140px]"
                      />
                    </div>

                    <div class="flex items-center gap-2">
                      <span class="text-[10px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 font-mono">
                        {{ k.usage || 0 }}x dipanggil
                      </span>
                      
                      <!-- Radio Switch active status -->
                      <button 
                        @click="setActiveKey('google_gemini', i)"
                        type="button"
                        :class="[
                          'px-2.5 py-1 rounded text-[10px] font-bold tracking-wider uppercase transition-all flex items-center gap-1.5',
                          k.status === 'active' ? 'bg-teal-400 text-slate-950' : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
                        ]"
                      >
                        <span v-if="k.status === 'active'" class="w-1.5 h-1.5 rounded-full bg-slate-950"></span>
                        <span>{{ k.status === 'active' ? 'TERPASANG' : 'SET AKTIF' }}</span>
                      </button>

                      <button 
                        @click="deleteKey('google_gemini', i)" 
                        type="button" 
                        class="p-1 text-slate-500 hover:text-red-400 transition-colors"
                        title="Hapus Kunci Ini"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                      </button>
                    </div>
                  </div>

                  <input 
                    type="text" 
                    v-model="k.key" 
                    placeholder="Masukkan Google API Key (AIzaSy...)" 
                    class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>

                <div v-if="!apiKeys.google_gemini || apiKeys.google_gemini.length === 0" class="text-center py-6 text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
                  Belum ada kunci Google Gemini terdaftar.
                </div>
              </div>

              <button 
                @click="addKey('google_gemini')" 
                type="button"
                class="w-full mt-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-sky-400 text-xs font-bold rounded-xl transition-colors flex items-center justify-center gap-1.5"
              >
                <span>+ Tambah Kunci Gemini Baru</span>
              </button>
            </div>

            <!-- GROQ CLOUD POOL -->
            <div class="bg-slate-950/60 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col">
              <div class="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
                <h4 class="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <span class="text-orange-500 font-black">G</span> 
                  Groq Cloud API Keys
                </h4>
                <span class="text-[10px] font-semibold bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">
                  Total: {{ apiKeys.groq ? apiKeys.groq.length : 0 }}
                </span>
              </div>

              <div class="space-y-3.5 flex-1">
                <div 
                  v-for="(k, i) in apiKeys.groq" 
                  :key="'groq'+i" 
                  :class="[
                    'p-3.5 rounded-xl border transition-all flex flex-col gap-2',
                    k.status === 'active' ? 'bg-orange-950/20 border-orange-500/50 shadow-md shadow-orange-950/20' : 'bg-slate-900/60 border-slate-800'
                  ]"
                >
                  <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-bold text-slate-500">#{{ i+1 }}</span>
                      <input 
                        type="text" 
                        v-model="k.label" 
                        placeholder="Label Kunci (mis: Groq Utama)" 
                        class="bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-xs text-slate-300 font-semibold focus:outline-none focus:border-orange-500 max-w-[150px]"
                      />
                    </div>

                    <div class="flex items-center gap-2">
                      <span class="text-[10px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 font-mono">
                        {{ k.usage || 0 }}x dipanggil
                      </span>
                      
                      <!-- Radio Switch active status -->
                      <button 
                        @click="setActiveKey('groq', i)"
                        type="button"
                        :class="[
                          'px-2.5 py-1 rounded text-[10px] font-bold tracking-wider uppercase transition-all flex items-center gap-1.5',
                          k.status === 'active' ? 'bg-orange-400 text-slate-950' : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
                        ]"
                      >
                        <span v-if="k.status === 'active'" class="w-1.5 h-1.5 rounded-full bg-slate-950"></span>
                        <span>{{ k.status === 'active' ? 'TERPASANG' : 'SET AKTIF' }}</span>
                      </button>

                      <button 
                        @click="deleteKey('groq', i)" 
                        type="button" 
                        class="p-1 text-slate-500 hover:text-red-400 transition-colors"
                        title="Hapus Kunci Ini"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                      </button>
                    </div>
                  </div>

                  <input 
                    type="text" 
                    v-model="k.key" 
                    placeholder="Masukkan Groq API Key (gsk_...)" 
                    class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-orange-500 font-mono"
                  />
                </div>

                <div v-if="!apiKeys.groq || apiKeys.groq.length === 0" class="text-center py-6 text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
                  Belum ada kunci Groq Cloud terdaftar.
                </div>
              </div>

              <button 
                @click="addKey('groq')" 
                type="button"
                class="w-full mt-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-orange-400 text-xs font-bold rounded-xl transition-colors flex items-center justify-center gap-1.5"
              >
                <span>+ Tambah Kunci Groq Baru</span>
              </button>
            </div>
          </div>
        </div>

        <!-- TAB 3: SYSTEM HEALTH -->
        <div v-if="activeTab === 'health'" class="space-y-6 animate-fade-in">
          <div class="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-2xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center">
                <svg class="w-6 h-6 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
              </div>
              <div>
                <h3 class="text-base font-bold text-white">DuckDB Analytical Engine</h3>
                <p class="text-xs text-slate-400 font-mono">{{ health.database_path || 'Menghubungkan...' }}</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <button 
                @click="runReEtl" 
                :disabled="isRunningEtl"
                class="px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg transition-all flex items-center gap-2"
              >
                <span v-if="isRunningEtl" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                <span>{{ isRunningEtl ? 'Memproses Medallion ETL...' : '🔥 RE-ETL 9 FILE EXCEL' }}</span>
              </button>
              <div class="text-right">
                <span class="inline-block px-2.5 py-1 bg-emerald-500/10 text-emerald-400 text-[10px] font-bold uppercase rounded-md border border-emerald-500/20 tracking-wider mb-1">
                  {{ health.status === 'healthy' ? 'System Healthy' : 'Error' }}
                </span>
                <p class="text-lg font-bold text-slate-200">{{ health.database_size_mb || 0 }} MB</p>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div 
              v-for="(count, tableName) in health.tables" 
              :key="tableName" 
              @click="inspectTable(tableName)"
              class="bg-slate-900/80 border border-slate-800 p-4 rounded-xl hover:border-teal-500/50 hover:bg-slate-800/40 cursor-pointer transition-all flex flex-col justify-between group shadow-sm"
            >
              <div>
                <div class="flex items-center justify-between mb-1.5">
                  <p class="text-slate-300 text-xs font-bold font-mono tracking-wide truncate group-hover:text-teal-300" :title="tableName">{{ tableName }}</p>
                  <span class="text-[9px] bg-teal-950/80 text-teal-300 font-mono px-1.5 py-0.5 rounded border border-teal-800/60 font-semibold group-hover:bg-teal-500 group-hover:text-slate-950 transition-colors">
                    INTIP DATA ➔
                  </span>
                </div>
                <h3 class="text-lg font-bold text-teal-400 font-mono">{{ count.toLocaleString() }} Rows</h3>
              </div>
              <p class="text-[10px] text-slate-500 mt-2">Klik untuk melihat skema kolom & 20 baris pertama</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>

  <!-- TABLE DATA EXPLORER MODAL -->
  <div v-if="previewModal.isOpen" class="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4 md:p-6 animate-fade-in">
    <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-6xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
      <!-- Modal Header -->
      <div class="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center font-mono text-teal-400 font-bold text-xs">
            SQL
          </div>
          <div>
            <h3 class="text-base font-bold text-white flex items-center gap-2">
              Struktur & Sampel Data: <span class="text-teal-400 font-mono">{{ previewModal.tableName }}</span>
            </h3>
            <p class="text-xs text-slate-400">Menampilkan skema kolom (tipe data) & 20 baris data mentah dari DuckDB</p>
          </div>
        </div>
        <button @click="previewModal.isOpen = false" class="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors text-sm font-bold">
          ✕
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6 flex-1 overflow-y-auto space-y-6">
        <div v-if="previewModal.isLoading" class="py-16 text-center text-slate-400 font-mono text-xs flex flex-col items-center justify-center gap-2">
          <div class="w-6 h-6 border-2 border-teal-400 border-t-transparent rounded-full animate-spin"></div>
          <span>Membaca skema & data DuckDB...</span>
        </div>

        <template v-else>
          <!-- Section 1: Columns Schema -->
          <div>
            <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <span>📋 Skema Kolom & Tipe Data ({{ previewModal.columns.length }} Kolom)</span>
            </h4>
            <div class="flex flex-wrap gap-2 bg-slate-950/60 border border-slate-800 p-3 rounded-xl">
              <div 
                v-for="col in previewModal.columns" 
                :key="col.column_name" 
                class="px-2.5 py-1 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono flex items-center gap-1.5 shadow-sm"
              >
                <span class="font-bold text-teal-300">{{ col.column_name }}</span>
                <span class="text-slate-500 text-[10px] bg-slate-950 px-1 rounded">{{ col.column_type }}</span>
              </div>
            </div>
          </div>

          <!-- Section 2: Sample Rows Table -->
          <div>
            <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5">
              📊 Sampel Data Mentah (20 Baris Pertama)
            </h4>
            <div class="overflow-x-auto border border-slate-800 rounded-xl bg-slate-950/80 max-h-96">
              <table class="w-full text-left text-xs text-slate-300 font-mono whitespace-nowrap">
                <thead class="bg-slate-900 text-slate-400 uppercase sticky top-0 border-b border-slate-800">
                  <tr>
                    <th v-for="col in previewModal.columns" :key="col.column_name" class="px-3.5 py-2.5 border-r border-slate-800/60 font-semibold">
                      {{ col.column_name }}
                    </th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/40">
                  <tr v-for="(row, idx) in previewModal.sampleRows" :key="idx" class="hover:bg-slate-800/50 transition-colors">
                    <td v-for="col in previewModal.columns" :key="col.column_name" class="px-3.5 py-2 border-r border-slate-800/40 truncate max-w-[220px]" :title="String(row[col.column_name])">
                      <span v-if="row[col.column_name] === null" class="text-slate-600 italic">null</span>
                      <span v-else>{{ row[col.column_name] }}</span>
                    </td>
                  </tr>
                  <tr v-if="previewModal.sampleRows.length === 0">
                    <td :colspan="previewModal.columns.length || 1" class="px-4 py-8 text-center text-slate-400 font-mono text-xs italic">
                      ℹ️ Tabel <strong class="text-teal-300">{{ previewModal.tableName }}</strong> memiliki skema kolom lengkap tetapi belum berisi baris data (0 Baris).
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const countdown = ref(3);
let pollTimer = null;

const goBackToChat = () => {
  window.location.href = '/';
};

const activeTab = ref('telemetry');

const tabs = [
  { id: 'telemetry', name: 'Telemetri & Log Audit' },
  { id: 'keys', name: 'Kredensial API Keys' },
  { id: 'health', name: 'Kesehatan System' }
];

const metrics = ref({ gemini_tokens: 0, groq_tokens: 0, avg_latency_ms: 0, success_rate: 0, total_requests: 0 });
const recentLogs = ref([]);
const health = ref({ tables: {} });
const apiKeys = ref({ google_gemini: [], groq: [] });
const isSavingKeys = ref(false);
const isRunningEtl = ref(false);

// Step Configurations State (Provider, Model, & API Keys per-Step)
const stepConfigs = ref({
  router: { provider: 'google_gemini', model: 'gemini-3.5-flash-lite', api_keys: [] },
  sql_gen: { provider: 'google_gemini', model: 'gemini-3.6-flash', api_keys: [] },
  viz_gen: { provider: 'groq', model: 'openai/gpt-oss-20b', api_keys: [] }
});
const modelCatalog = ref({ google_gemini: [], groq: [] });
const poolKeys = ref({ google_gemini: [], groq: [] });
const isSavingStepConfigs = ref(false);

const getModelsForProvider = (provider) => {
  return modelCatalog.value[provider] || [];
};

const setStepProvider = (stepKey, newProvider) => {
  if (!stepConfigs.value[stepKey]) return;
  stepConfigs.value[stepKey].provider = newProvider;
  
  // Set default model for the new provider
  const available = getModelsForProvider(newProvider);
  if (available.length > 0) {
    stepConfigs.value[stepKey].model = available[0].id;
  }
};

const addStepKey = (stepKey) => {
  if (!stepConfigs.value[stepKey]) return;
  if (!stepConfigs.value[stepKey].api_keys) stepConfigs.value[stepKey].api_keys = [];
  const count = stepConfigs.value[stepKey].api_keys.length + 1;
  const isGoogle = stepConfigs.value[stepKey].provider === 'google_gemini';
  const label = isGoogle ? `Gemini Key ${count}` : `Groq Key ${count}`;
  const initialStatus = stepConfigs.value[stepKey].api_keys.length === 0 ? 'active' : 'inactive';
  stepConfigs.value[stepKey].api_keys.push({
    label,
    key: '',
    status: initialStatus,
    usage: 0
  });
};

const deleteStepKey = (stepKey, index) => {
  if (!stepConfigs.value[stepKey]?.api_keys) return;
  const wasActive = stepConfigs.value[stepKey].api_keys[index].status === 'active';
  stepConfigs.value[stepKey].api_keys.splice(index, 1);
  if (wasActive && stepConfigs.value[stepKey].api_keys.length > 0) {
    stepConfigs.value[stepKey].api_keys[0].status = 'active';
  }
};

const setStepActiveKey = (stepKey, index) => {
  if (!stepConfigs.value[stepKey]?.api_keys) return;
  stepConfigs.value[stepKey].api_keys.forEach((k, idx) => {
    k.status = idx === index ? 'active' : 'inactive';
  });
};

const fetchStepConfigs = async () => {
  try {
    const token = localStorage.getItem('tps_admin_token') || localStorage.getItem('tps_token');
    const res = await fetch('/api/v1/admin/step_configs', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    if (data.status === 'success') {
      stepConfigs.value = data.step_configs;
      modelCatalog.value = data.catalog;
      poolKeys.value = data.pool_keys;
    }
  } catch (e) {
    console.error('Gagal mengambil konfigurasi per-step:', e);
  }
};

const saveStepConfigs = async () => {
  isSavingStepConfigs.value = true;
  try {
    const token = localStorage.getItem('tps_admin_token') || localStorage.getItem('tps_token');
    const res = await fetch('/api/v1/admin/step_configs', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ step_configs: stepConfigs.value })
    });
    const data = await res.json();
    if (data.status === 'success') {
      alert('✅ ' + data.message);
      await fetchStepConfigs();
    } else {
      alert('❌ Gagal menyimpan: ' + (data.detail || 'Error server'));
    }
  } catch (e) {
    alert('❌ Terjadi kesalahan jaringan saat menyimpan konfigurasi per-step');
  } finally {
    isSavingStepConfigs.value = false;
  }
};

const runReEtl = async () => {
  if (!confirm('Apakah Anda yakin ingin memproses ulang seluruh 9 file Excel ETL ke DuckDB?')) return;
  isRunningEtl.value = true;
  try {
    const token = localStorage.getItem('tps_admin_token') || localStorage.getItem('tps_token');
    const res = await fetch('/api/v1/admin/re_etl', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    if (data.status === 'success') {
      alert(data.message);
      fetchData();
    } else {
      alert('❌ Gagal Re-ETL: ' + (data.detail || 'Error server'));
    }
  } catch (e) {
    alert('❌ Terjadi kesalahan jaringan saat Re-ETL');
  } finally {
    isRunningEtl.value = false;
  }
};

const previewModal = ref({ isOpen: false, tableName: '', columns: [], sampleRows: [], isLoading: false });

const inspectTable = async (tableName) => {
  previewModal.value = { isOpen: true, tableName, columns: [], sampleRows: [], isLoading: true };
  try {
    const token = localStorage.getItem('tps_admin_token') || localStorage.getItem('tps_token');
    const res = await fetch(`/api/v1/admin/table_preview/${tableName}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    if (data.status === 'success') {
      previewModal.value.columns = data.columns;
      previewModal.value.sampleRows = data.sample_rows;
    }
  } catch (e) {
    console.error('Gagal mengambil preview tabel:', e);
  } finally {
    previewModal.value.isLoading = false;
  }
};

const fetchMetrics = async () => {
  try {
    const token = localStorage.getItem('tps_admin_token') || localStorage.getItem('tps_token');
    const resMetrics = await fetch('/api/v1/admin/metrics', { headers: { 'Authorization': `Bearer ${token}` } });
    const dataMetrics = await resMetrics.json();
    if (dataMetrics.status === 'success') {
      metrics.value = dataMetrics.metrics;
      recentLogs.value = dataMetrics.recent_logs;
    }
  } catch (e) {
    console.error("Gagal mengambil metrik:", e);
  }
};

const fetchHealth = async () => {
  try {
    const token = localStorage.getItem('tps_admin_token') || localStorage.getItem('tps_token');
    const resHealth = await fetch('/api/v1/data/status', { headers: { 'Authorization': `Bearer ${token}` } });
    const dataHealth = await resHealth.json();
    if (dataHealth.status === 'healthy') {
      health.value = dataHealth;
    }
  } catch (e) {
    console.error("Gagal mengambil status health:", e);
  }
};

const fetchKeys = async () => {
  try {
    const token = localStorage.getItem('tps_admin_token') || localStorage.getItem('tps_token');
    const resKeys = await fetch('/api/v1/admin/keys', { headers: { 'Authorization': `Bearer ${token}` } });
    const dataKeys = await resKeys.json();
    if (dataKeys.status === 'success') {
      apiKeys.value = dataKeys.data;
    }
  } catch (e) {
    console.error("Gagal mengambil kunci API:", e);
  }
};

const fetchData = async () => {
  await Promise.all([
    fetchMetrics(),
    fetchHealth(),
    fetchKeys(),
    fetchStepConfigs()
  ]);
};

const setActiveKey = (provider, index) => {
  if (!apiKeys.value[provider]) return;
  apiKeys.value[provider].forEach((item, idx) => {
    item.status = idx === index ? 'active' : 'inactive';
  });
};

const addKey = (provider) => {
  if (!apiKeys.value[provider]) apiKeys.value[provider] = [];
  const count = apiKeys.value[provider].length + 1;
  const defaultLabel = provider === 'google_gemini' ? `Gemini Key ${count}` : `Groq Key ${count}`;
  const initialStatus = apiKeys.value[provider].length === 0 ? 'active' : 'inactive';
  apiKeys.value[provider].push({
    label: defaultLabel,
    key: '',
    status: initialStatus,
    usage: 0
  });
};

const deleteKey = (provider, index) => {
  if (!apiKeys.value[provider]) return;
  const wasActive = apiKeys.value[provider][index].status === 'active';
  apiKeys.value[provider].splice(index, 1);
  if (wasActive && apiKeys.value[provider].length > 0) {
    apiKeys.value[provider][0].status = 'active';
  }
};

const saveApiKeys = async () => {
  isSavingKeys.value = true;
  try {
    const token = localStorage.getItem('tps_admin_token') || localStorage.getItem('tps_token');
    await fetch('/api/v1/admin/keys', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(apiKeys.value)
    });
    // Refresh to get masked keys back
    await fetchKeys();
    alert('✅ Kredensial API Keys berhasil disimpan dan diperbarui!');
  } catch (e) {
    alert('❌ Gagal menyimpan API keys');
  } finally {
    isSavingKeys.value = false;
  }
};

// 🛡️ ANTI-OVERWRITE AUTO-POLLING:
// Polling 3 detik hanya mengambil data live metrics/telemetri latar belakang.
// Tidak akan pernah menimpa form ketikan input stepConfigs atau apiKeys!
onMounted(() => {
  fetchData();
  pollTimer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      fetchMetrics();
      if (activeTab.value === 'health') {
        fetchHealth();
      }
      countdown.value = 3;
    }
  }, 1000);
});

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});
</script>
