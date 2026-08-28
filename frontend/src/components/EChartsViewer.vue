<template>
  <div v-if="chartConfig && Object.keys(chartConfig).length > 0" class="mt-4 card-executive p-4 sm:p-5 rounded-2xl border border-slate-800">
    <!-- Header Controls -->
    <div class="flex items-center justify-between mb-3.5 pb-2.5 border-b border-slate-800/80">
      <div class="flex items-center gap-2">
        <BarChart3 class="w-4 h-4 text-teal-400" />
        <h4 class="text-xs font-bold text-slate-200 uppercase tracking-wider">
          {{ chartConfig.title?.text || 'Visualisasi Grafik ECharts' }}
        </h4>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-if="chartInstance"
          @click="downloadImage"
          class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-[11px] font-medium text-slate-300 transition-colors border border-slate-700"
          title="Unduh Grafik sebagai Gambar"
        >
          <Download class="w-3.5 h-3.5 text-teal-400" />
          <span>Export PNG</span>
        </button>
      </div>
    </div>

    <!-- Chart Canvas Container -->
    <div ref="chartContainer" class="w-full h-72 sm:h-80"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { BarChart3, Download } from './Icons.js'

const props = defineProps({
  chartConfig: { type: Object, default: () => ({}) }
})

const chartContainer = ref(null)
let chartInstance = null

// Fungsi pembersih warna teks agar selalu kontras di latar belakang gelap
const sanitizeChartOption = (rawOption) => {
  if (!rawOption || typeof rawOption !== 'object') return {}
  try {
    const opt = JSON.parse(JSON.stringify(rawOption))

    const darkColors = ['#000', '#000000', '#333', '#333333', '#555', '#555555', '#666', '#666666']

    // Sanitasi Title
    if (opt.title && typeof opt.title === 'object') {
      if (!opt.title.textStyle) opt.title.textStyle = {}
      opt.title.textStyle.color = '#f8fafc'
    }

    // Sanitasi Sumbu X & Y
    const fixAxis = (axisObj) => {
      if (!axisObj) return
      const axes = Array.isArray(axisObj) ? axisObj : [axisObj]
      axes.forEach(axis => {
        if (!axis || typeof axis !== 'object') return
        if (!axis.axisLabel) axis.axisLabel = {}
        if (!axis.axisLabel.color || (typeof axis.axisLabel.color === 'string' && darkColors.includes(axis.axisLabel.color.toLowerCase()))) {
          axis.axisLabel.color = '#94a3b8'
        }
        if (axis.nameTextStyle) axis.nameTextStyle.color = '#cbd5e1'
      })
    }

    fixAxis(opt.xAxis)
    fixAxis(opt.yAxis)

    // Pastikan Series selalu memiliki Angka Label (Data Values) di atas batang
    if (opt.series) {
      const seriesList = Array.isArray(opt.series) ? opt.series : [opt.series]
      seriesList.forEach(s => {
        if (!s || typeof s !== 'object') return
        if (!s.label) s.label = {}
        s.label.show = true
        if (!s.label.position) s.label.position = 'top'
        s.label.color = '#38bdf8'
        s.label.fontWeight = 'bold'
        s.label.fontSize = 12
      })
    }

    // Pastikan Grid memiliki margin atas agar label angka tidak terpotong
    if (!opt.grid || typeof opt.grid !== 'object') opt.grid = {}
    opt.grid.top = opt.grid.top || '20%'
    opt.grid.containLabel = true

    return opt
  } catch (err) {
    console.error('Error sanitizing chart option:', err)
    return rawOption
  }
}

const initChart = async () => {
  await nextTick()
  if (!chartContainer.value || !props.chartConfig || Object.keys(props.chartConfig).length === 0) return

  const echarts = typeof window !== 'undefined' ? window.echarts : null

  if (!echarts) {
    console.warn('ECharts library belum dimuat dari CDN.')
    return
  }

  try {
    if (chartInstance) {
      chartInstance.dispose()
    }

    chartInstance = echarts.init(chartContainer.value, 'dark')

    const sanitizedOption = sanitizeChartOption(props.chartConfig)

    // Theme overrides untuk estetika maritim executive
    const mergedOption = {
      backgroundColor: 'transparent',
      textStyle: { fontFamily: 'Plus Jakarta Sans, sans-serif' },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        borderColor: '#0d9488',
        textStyle: { color: '#f8fafc' }
      },
      color: ['#14b8a6', '#38bdf8', '#6366f1', '#10b981', '#f59e0b', '#ec4899'],
      ...sanitizedOption
    }

    chartInstance.setOption(mergedOption)
  } catch (err) {
    console.error('Gagal menginisialisasi ECharts:', err)
  }
}

const handleResize = () => {
  try {
    chartInstance?.resize()
  } catch (e) {}
}

const downloadImage = () => {
  if (!chartInstance) return
  try {
    const url = chartInstance.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#0b0f19' })
    const a = document.createElement('a')
    a.href = url
    a.download = `TPS_Analytics_Chart_${Date.now()}.png`
    a.click()
  } catch (e) {
    console.error('Gagal unduh gambar grafik:', e)
  }
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    try { chartInstance.dispose() } catch (e) {}
  }
})

watch(() => props.chartConfig, () => {
  initChart()
}, { deep: true })
</script>
