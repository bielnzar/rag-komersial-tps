<template>
  <div v-if="data && data.length > 0" class="mt-3.5">
    <!-- Baris Tombol Aksi: Toggle Tabel & Dropdown Ekspor -->
    <div class="flex items-center gap-2 flex-wrap relative">
      <!-- Tombol 1: Buka/Tutup Tabel -->
      <button
        @click="isOpen = !isOpen"
        class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 text-xs font-medium text-slate-300 transition-colors cursor-pointer"
      >
        <Table class="w-3.5 h-3.5 text-teal-400" />
        <span>Tabel Data Mentah DuckDB ({{ data.length }} Baris)</span>
        <ChevronRight class="w-3.5 h-3.5 transition-transform duration-200" :class="{ 'rotate-90': isOpen }" />
      </button>

      <!-- Tombol 2: Dropdown Ekspor Multi-Format -->
      <div class="relative" ref="dropdownRef">
        <button
          @click="isDropdownOpen = !isDropdownOpen"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-xs font-medium text-teal-300 transition-all cursor-pointer shadow-sm hover:border-teal-500/50"
        >
          <Download class="w-3.5 h-3.5 text-teal-400" />
          <span>Ekspor Data</span>
          <ChevronDown class="w-3 h-3 text-slate-400 transition-transform duration-200" :class="{ 'rotate-180': isDropdownOpen }" />
        </button>

        <!-- Menu Dropdown Ekspor Popover -->
        <div
          v-if="isDropdownOpen"
          class="absolute left-0 mt-1.5 w-64 rounded-xl bg-slate-900/95 border border-slate-700/90 shadow-2xl p-1.5 z-30 backdrop-blur-md animate-fade-in divide-y divide-slate-800/60"
        >
          <div class="p-1 space-y-1">
            <!-- Opsi 1: Unduh Excel -->
            <button
              @click="downloadExcel"
              class="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left text-xs text-slate-200 hover:bg-slate-800/90 hover:text-teal-300 transition-colors cursor-pointer group"
            >
              <FileSpreadsheet class="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
              <div>
                <div class="font-semibold">Unduh Excel (.xls)</div>
                <div class="text-[10px] text-slate-400">Workbook terformat rapi siap pakai</div>
              </div>
            </button>

            <!-- Opsi 2: Unduh CSV -->
            <button
              @click="downloadCSV"
              class="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left text-xs text-slate-200 hover:bg-slate-800/90 hover:text-teal-300 transition-colors cursor-pointer group"
            >
              <FileText class="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
              <div>
                <div class="font-semibold">Unduh CSV (.csv)</div>
                <div class="text-[10px] text-slate-400">Standar tabular UTF-8 BOM untuk Excel & BI</div>
              </div>
            </button>
          </div>

          <div class="p-1 space-y-1">
            <!-- Opsi 3: Salin ke Clipboard -->
            <button
              @click="copyTableTSV"
              class="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left text-xs text-slate-200 hover:bg-slate-800/90 hover:text-teal-300 transition-colors cursor-pointer group"
            >
              <Copy class="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
              <div>
                <div class="font-semibold">Salin Tabel (TSV)</div>
                <div class="text-[10px] text-slate-400">Siap paste langsung ke Excel (Ctrl+V)</div>
              </div>
            </button>

            <!-- Opsi 4: Cetak / Simpan PDF Laporan -->
            <button
              @click="printReportPDF"
              class="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left text-xs text-slate-200 hover:bg-slate-800/90 hover:text-teal-300 transition-colors cursor-pointer group"
            >
              <Printer class="w-4 h-4 text-rose-400 group-hover:scale-110 transition-transform" />
              <div>
                <div class="font-semibold">Cetak / Simpan PDF</div>
                <div class="text-[10px] text-slate-400">Laporan formal A4 narasi & tabel</div>
              </div>
            </button>
          </div>
        </div>
      </div>

      <!-- Feedback Indikator Salin -->
      <transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 translate-y-1"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <span v-if="copiedMessage" class="text-[11px] text-teal-400 font-mono flex items-center gap-1 bg-teal-950/80 px-2 py-0.5 rounded border border-teal-800/60">
          <Check class="w-3 h-3 text-teal-400" />
          {{ copiedMessage }}
        </span>
      </transition>
    </div>

    <!-- Tampilan Tabel Collapsible -->
    <div v-show="isOpen" class="mt-2.5 card-executive rounded-xl overflow-hidden border border-slate-800">
      <!-- Toolbar Filter Cepat dalam Tabel -->
      <div v-if="data.length > 5" class="p-2.5 bg-slate-950/50 border-b border-slate-800 flex items-center justify-between gap-2">
        <span class="text-[11px] text-slate-400 font-mono">
          Menampilkan {{ filteredData.length }} dari {{ data.length }} baris data
        </span>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Filter data dalam tabel..."
          class="px-2.5 py-1 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500/70 w-44 sm:w-56"
        />
      </div>

      <!-- Wadah Tabel dengan Scroll Horizontal & Vertikal -->
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
            <tr
              v-for="(row, idx) in filteredData"
              :key="idx"
              class="hover:bg-slate-900/40 transition-colors"
            >
              <td v-for="col in headers" :key="col" class="px-4 py-2 whitespace-nowrap">
                <span v-if="row[col] === null || row[col] === undefined" class="text-slate-600 italic">null</span>
                <span v-else>{{ row[col] }}</span>
              </td>
            </tr>
            <tr v-if="filteredData.length === 0">
              <td :colspan="headers.length" class="px-4 py-6 text-center text-slate-500 italic">
                Tidak ada baris data yang cocok dengan filter pencarian.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import {
  Table,
  ChevronRight,
  ChevronDown,
  Download,
  Copy,
  Check,
  Printer,
  FileSpreadsheet,
  FileText
} from './Icons.js'

const props = defineProps({
  data: { type: Array, default: () => [] },
  userQuery: { type: String, default: '' },
  narrative: { type: String, default: '' }
})

const isOpen = ref(false)
const isDropdownOpen = ref(false)
const dropdownRef = ref(null)
const copiedMessage = ref('')
const searchQuery = ref('')

const headers = computed(() => {
  if (!props.data || props.data.length === 0) return []
  return Object.keys(props.data[0])
})

const filteredData = computed(() => {
  if (!searchQuery.value.trim()) return props.data
  const q = searchQuery.value.toLowerCase().trim()
  return props.data.filter(row => {
    return Object.values(row).some(val =>
      val !== null && val !== undefined && String(val).toLowerCase().includes(q)
    )
  })
})

// Tutup dropdown jika klik di luar area
const handleClickOutside = (e) => {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    isDropdownOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

const showToast = (msg) => {
  copiedMessage.value = msg
  setTimeout(() => {
    copiedMessage.value = ''
  }, 2500)
}

// 📄 OPSI 1: UNDUH CSV (UTF-8 BOM agar rapi di Microsoft Excel)
const downloadCSV = () => {
  if (!props.data || props.data.length === 0) return
  isDropdownOpen.value = false

  const cols = headers.value
  const csvRows = [cols.join(',')]

  for (const row of props.data) {
    const values = cols.map(c => {
      const val = row[c] === null || row[c] === undefined ? '' : String(row[c])
      return `"${val.replace(/"/g, '""')}"`
    })
    csvRows.push(values.join(','))
  }

  // \uFEFF adalah UTF-8 BOM untuk memastikan Excel Windows membaca delimiter secara otomatis
  const blob = new Blob(['\uFEFF' + csvRows.join('\r\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `tps_data_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
  showToast('✓ CSV Terunduh')
}

// 📊 OPSI 2: UNDUH EXCEL (.xls Workbook terformat)
const downloadExcel = () => {
  if (!props.data || props.data.length === 0) return
  isDropdownOpen.value = false

  const cols = headers.value
  let tableHtml = `
    <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
    <head>
      <meta charset="utf-8">
      <!--[if gte mso 9]>
      <xml>
        <x:ExcelWorkbook>
          <x:ExcelWorksheets>
            <x:ExcelWorksheet>
              <x:Name>Data Komersial TPS</x:Name>
              <x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions>
            </x:ExcelWorksheet>
          </x:ExcelWorksheets>
        </x:ExcelWorkbook>
      </xml>
      <![endif]-->
      <style>
        th { background-color: #0f766e; color: #ffffff; font-weight: bold; border: 1px solid #0d9488; padding: 6px; }
        td { border: 1px solid #cbd5e1; padding: 5px; font-family: Calibri, sans-serif; }
      </style>
    </head>
    <body>
      <table>
        <thead>
          <tr>${cols.map(c => `<th>${c}</th>`).join('')}</tr>
        </thead>
        <tbody>
  `

  for (const row of props.data) {
    tableHtml += '<tr>'
    for (const c of cols) {
      const val = row[c] === null || row[c] === undefined ? '' : row[c]
      const isNum = typeof val === 'number'
      tableHtml += `<td ${isNum ? 'style="mso-number-format:General;"' : ''}>${val}</td>`
    }
    tableHtml += '</tr>'
  }

  tableHtml += `
        </tbody>
      </table>
    </body>
    </html>
  `

  const blob = new Blob([tableHtml], { type: 'application/vnd.ms-excel;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `tps_komersial_${new Date().toISOString().slice(0, 10)}.xls`
  a.click()
  URL.revokeObjectURL(url)
  showToast('✓ Excel Terunduh')
}

// 📋 OPSI 3: SALIN TABEL TSV (Siap Paste di Excel)
const copyTableTSV = async () => {
  if (!props.data || props.data.length === 0) return
  isDropdownOpen.value = false

  const cols = headers.value
  const tsvLines = [cols.join('\t')]

  for (const row of props.data) {
    const vals = cols.map(c => {
      const v = row[c] === null || row[c] === undefined ? '' : String(row[c])
      return v.replace(/[\t\r\n]/g, ' ')
    })
    tsvLines.push(vals.join('\t'))
  }

  try {
    await navigator.clipboard.writeText(tsvLines.join('\n'))
    showToast('✓ Tersalin! Siap paste ke Excel')
  } catch (err) {
    console.error('Gagal menyalin:', err)
  }
}

// 🖨️ OPSI 4: CETAK / SIMPAN PDF LAPORAN FORMAL
const printReportPDF = () => {
  if (!props.data || props.data.length === 0) return
  isDropdownOpen.value = false

  const cols = headers.value
  const printWin = window.open('', '_blank', 'width=900,height=950')
  if (!printWin) {
    alert('Popup diblokir oleh browser. Harap izinkan popup untuk mencetak laporan.')
    return
  }

  const cleanNarrative = props.narrative
    ? props.narrative
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>')
    : ''

  printWin.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Laporan Analisis Data Komersial - PT Terminal Petikemas Surabaya</title>
      <style>
        @page { size: A4; margin: 15mm; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; color: #0f172a; margin: 0; padding: 20px; font-size: 11pt; }
        .header { border-bottom: 3px solid #0f766e; padding-bottom: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-end; }
        .company { font-size: 18pt; font-weight: bold; color: #0f766e; letter-spacing: -0.5px; }
        .sub-company { font-size: 9.5pt; color: #475569; margin-top: 2px; }
        .doc-meta { font-size: 8.5pt; color: #64748b; text-align: right; }
        .section-title { font-size: 10pt; font-weight: bold; color: #334155; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 18px; margin-bottom: 6px; }
        .query-box { background: #f1f5f9; border-left: 4px solid #0f766e; padding: 10px 14px; font-size: 10.5pt; font-style: italic; color: #1e293b; margin-bottom: 16px; border-radius: 4px; }
        .narrative-box { font-size: 10pt; line-height: 1.6; color: #334155; margin-bottom: 20px; text-align: justify; }
        table { width: 100%; border-collapse: collapse; font-size: 9pt; margin-top: 8px; }
        th { background-color: #0f766e; color: #ffffff; font-weight: bold; text-align: left; padding: 7px 9px; border: 1px solid #0f766e; }
        td { padding: 6px 9px; border: 1px solid #cbd5e1; }
        tr:nth-child(even) { background-color: #f8fafc; }
        .footer { margin-top: 36px; border-top: 1px solid #e2e8f0; padding-top: 10px; font-size: 8pt; color: #94a3b8; display: flex; justify-content: space-between; }
        @media print {
          body { padding: 0; }
          button { display: none; }
        }
      </style>
    </head>
    <body>
      <div class="header">
        <div>
          <div class="company">PT TERMINAL PETIKEMAS SURABAYA</div>
          <div class="sub-company">Enterprise Commercial Data Analytics Assistant Report</div>
        </div>
        <div class="doc-meta">
          <div><strong>Tanggal Cetak:</strong> ${new Date().toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' })}</div>
          <div><strong>Waktu:</strong> ${new Date().toLocaleTimeString('id-ID')} WIB</div>
        </div>
      </div>

      ${props.userQuery ? `
        <div class="section-title">Pertanyaan Analisis Pengguna:</div>
        <div class="query-box">"${props.userQuery}"</div>
      ` : ''}

      ${cleanNarrative ? `
        <div class="section-title">Ringkasan Narasi Eksekutif:</div>
        <div class="narrative-box">${cleanNarrative}</div>
      ` : ''}

      <div class="section-title">Tabel Hasil Kueri Database (${props.data.length} Baris Data):</div>
      <table>
        <thead>
          <tr>${cols.map(c => `<th>${c}</th>`).join('')}</tr>
        </thead>
        <tbody>
          ${props.data.map(row => `
            <tr>
              ${cols.map(c => `<td>${row[c] !== null && row[c] !== undefined ? row[c] : '-'}</td>`).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>

      <div class="footer">
        <span>Laporan Resmi Dihasilkan oleh TPS Enterprise AI Assistant</span>
        <span>Dokumen Internal PT Terminal Petikemas Surabaya</span>
      </div>
    </body>
    </html>
  `)
  printWin.document.close()
  printWin.focus()
  setTimeout(() => {
    printWin.print()
  }, 400)
}
</script>
